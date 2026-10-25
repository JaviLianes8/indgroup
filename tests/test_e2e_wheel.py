"""Build the wheel, install it in a throwaway venv and drive the installed package.

Slow and needs the build backend, so it runs only with INDGROUP_E2E=1. Set
INDGROUP_E2E_NO_SCRIPT=1 where policy blocks running the generated console script.
"""

from __future__ import annotations

import os
import subprocess
import sys
import venv
import zipfile
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

pytestmark = pytest.mark.skipif(
    os.environ.get("INDGROUP_E2E") != "1", reason="set INDGROUP_E2E=1 to build and install"
)

PROGRAM = r"""
import importlib.metadata, importlib.resources
from decimal import Decimal
import indgroup
from indgroup import (
    NumberSymbols, cldr_version, format_indian, format_number, number_symbols, parse_indian,
    parse_number, resolve_locale, supported_locales,
)

assert "site-packages" in indgroup.__file__, indgroup.__file__
assert importlib.metadata.version("indgroup") == indgroup.__version__
assert importlib.resources.files("indgroup").joinpath("py.typed").is_file()
meta = importlib.metadata.metadata("indgroup")
assert meta["License-Expression"] == "MIT AND Unicode-3.0", meta["License-Expression"]
assert cldr_version() == "48.0.0" and len(supported_locales()) == 766
assert format_indian(1234567) == "12,34,567"
assert format_indian(0.1) == "0.1"
assert parse_indian("12,34,567.50") == Decimal("1234567.50")
assert format_number(1234567.5, "de") == "1.234.567,5"
assert format_number(1234567, "fr") == "1" + chr(0x202F) + "234" + chr(0x202F) + "567"
assert format_number(1234, "es") == "1234" and format_number(12345, "es") == "12.345"
assert parse_number("-1.234,5", "de") == Decimal("-1234.5")
assert number_symbols("en-IN") == NumberSymbols("en-IN", ".", ",", "-", 3, 2, 1)
assert resolve_locale("pt-FR") == "pt-PT"
for bad in ("1,234,567",):
    try:
        parse_number(bad, "en-IN")
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
try:
    resolve_locale("xx")
except LookupError:
    pass
else:
    raise AssertionError("expected LookupError")
for call, kind in [
    (lambda: format_number(10**100_000, "en"), ValueError),
    (lambda: parse_number("1" * 100_001, "en"), ValueError),
    (lambda: format_number(1, "en", grouping=True), TypeError),
]:
    try:
        call()
    except kind as error:
        assert len(str(error)) < 120
    else:
        raise AssertionError(kind)
import pickle
assert pickle.loads(pickle.dumps(number_symbols("hi"))) == number_symbols("hi")
assert NumberSymbols.__module__ == "indgroup"
print("e2e ok")
"""

CONSUMER = """
from decimal import Decimal
from indgroup import Grouping, Number, format_number, parse_number

def show(value: Number, grouping: Grouping = "auto") -> str:
    return format_number(value, "en-IN", grouping=grouping)

back: int | Decimal = parse_number(show(Decimal("1234567.5")), "en-IN")
print(show(1), back)
"""


def _run(
    *cmd: str | Path, cwd: Path | None = None, stdin: bytes = b""
) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(
        [str(c) for c in cmd], cwd=cwd, input=stdin, capture_output=True, check=False
    )


def test_installed_wheel_end_to_end(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    built = _run(sys.executable, "-m", "build", "--outdir", dist, ROOT)
    assert built.returncode == 0, built.stderr
    (wheel,) = dist.glob("indgroup-*.whl")
    (sdist,) = dist.glob("indgroup-*.tar.gz")
    names = zipfile.ZipFile(wheel).namelist()
    for name in ("indgroup/py.typed", "indgroup/_cldr.json", "indgroup/__main__.py"):
        assert name in names, name
    licences = {name.rsplit("/", 1)[1] for name in names if "/licenses/" in name}
    assert licences == {"LICENSE", "LICENSE-UNICODE"}
    assert not any(name.startswith(("tests/", "scripts/")) for name in names)
    entry_points = next(name for name in names if name.endswith("entry_points.txt"))
    assert "indgroup = indgroup._cli:main" in zipfile.ZipFile(wheel).read(entry_points).decode()
    listing = _run(sys.executable, "-m", "tarfile", "-l", sdist).stdout.decode()
    assert "IMPROVEMENTS-round" not in listing
    for fetched in (".tgz", "number_grouping", "tr35", "intl-node"):
        assert fetched not in listing, fetched
    for kept in ("tests/upstream/MANIFEST.json", "scripts/fetch_upstream.py", "LICENSE-UNICODE"):
        assert kept in listing, kept

    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    installed = _run(python, "-m", "pip", "install", "-q", wheel)
    assert installed.returncode == 0, installed.stderr

    # Run from an empty folder so the source tree cannot shadow the install.
    work = tmp_path / "work"
    work.mkdir()
    result = _run(python, "-I", "-c", PROGRAM, cwd=work)
    assert result.returncode == 0, result.stderr
    assert result.stdout.decode().strip() == "e2e ok"

    consumer = work / "consumer.py"
    consumer.write_text(CONSUMER, encoding="utf-8")
    typed = _run(sys.executable, "-m", "mypy", "--strict", "--python-executable", python, consumer)
    assert typed.returncode == 0, typed.stdout
    assert _run(python, "-I", consumer).stdout.decode().split() == ["1", "1234567.5"]

    script = bindir / ("indgroup.exe" if sys.platform == "win32" else "indgroup")
    commands: list[list[str | Path]] = [[python, "-m", "indgroup"]]
    if os.environ.get("INDGROUP_E2E_NO_SCRIPT") != "1":
        commands.append([script])
    for command in commands:
        shown = _run(*command, "-l", "fr", cwd=work, stdin=b"1234567\n-0.5\n")
        assert shown.returncode == 0, shown.stderr
        expected = "1" + chr(0x202F) + "234" + chr(0x202F) + "567\n-0,5\n"
        assert shown.stdout.decode("utf-8").replace("\r\n", "\n") == expected
        failed = _run(*command, "1", "-l", "xx", cwd=work)
        assert failed.returncode == 2 and b"no number data" in failed.stderr
        digits = "9" * 5000
        parsed = _run(*command, "-p", cwd=work, stdin=digits.encode() + b"\n")
        assert parsed.returncode == 0 and parsed.stdout.decode().strip() == digits
