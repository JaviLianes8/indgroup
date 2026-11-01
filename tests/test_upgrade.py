"""Upgrade the actual PyPI 0.2.0 release in place to the built stable wheel."""

from __future__ import annotations

import os
import sys
import venv
from pathlib import Path

import pytest
from test_e2e_wheel import PROGRAM, ROOT, _run

pytestmark = pytest.mark.skipif(
    os.environ.get("INDGROUP_E2E_PYPI") != "1", reason="set INDGROUP_E2E_PYPI=1 for PyPI upgrade"
)

BASELINE = r"""
import inspect, json, pickle
from decimal import Decimal
from pathlib import Path
from typing import get_args
import indgroup as lib

assert "site-packages" in lib.__file__, lib.__file__
snapshot = {}
for name in lib.__all__:
    value = getattr(lib, name)
    if inspect.isfunction(value):
        snapshot[name] = str(inspect.signature(value))
    elif name in ("Number", "Grouping"):
        snapshot[name] = [str(item) for item in get_args(value)]
    else:
        snapshot[name] = list(inspect.signature(value).parameters)
assert len(snapshot) == 11
assert lib.format_indian(Decimal("1234567.50")) == "12,34,567.50"
assert lib.parse_indian("12,34,567.50") == Decimal("1234567.50")
assert lib.format_number(1234567.5, "de") == "1.234.567,5"
assert lib.parse_number("1.234.567,5", "de") == Decimal("1234567.5")
assert len(lib.supported_locales()) == 766
symbols = lib.number_symbols("en-IN")
if lib.__version__ == "0.2.0":
    Path("api.json").write_text(json.dumps(snapshot), encoding="utf-8")
    Path("symbols.pickle").write_bytes(pickle.dumps(symbols))
    assert lib.cldr_version() == "48.0.0"
    assert lib.number_symbols("fr-CH").group == chr(0x202F)
    assert lib.resolve_locale("ru-Latn") == "ru"
    assert lib.resolve_locale("ku-GE") == "ku"
    assert lib.parse_indian("0,001") == 1
    try:
        lib.format_number(1, "en", grouping=True)
    except ValueError:
        pass
    else:
        raise AssertionError("expected the 0.2.0 error family")
else:
    assert lib.__version__ == "1.0.0"
    assert snapshot == json.loads(Path("api.json").read_text(encoding="utf-8"))
    assert pickle.loads(Path("symbols.pickle").read_bytes()) == symbols
    assert lib.cldr_version() == "48.2.0"
    assert lib.number_symbols("fr-CH").group == "'"
    assert lib.resolve_locale("ru-Latn") == "und"
    assert lib.resolve_locale("ku-GE") == "und"
    try:
        lib.parse_indian("0,001")
    except ValueError:
        pass
    else:
        raise AssertionError("expected the documented strict grouping change")
    try:
        lib.format_number(1, "en", grouping=True)
    except TypeError:
        pass
    else:
        raise AssertionError("expected the documented grouping error change")
print(lib.__version__)
"""


def test_pypi_release_upgrades_in_place(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    built = _run(sys.executable, "-m", "build", "--wheel", "--outdir", dist, ROOT)
    assert built.returncode == 0, built.stderr
    (wheel,) = dist.glob("indgroup-*.whl")
    env_dir = tmp_path / "venv"
    venv.create(env_dir, with_pip=True)
    bindir = env_dir / ("Scripts" if sys.platform == "win32" else "bin")
    python = bindir / "python"
    installed = _run(
        python, "-m", "pip", "install", "--index-url", "https://pypi.org/simple", "indgroup==0.2.0"
    )
    assert installed.returncode == 0, installed.stderr
    work = tmp_path / "consumer"
    work.mkdir()
    before = _run(python, "-I", "-c", BASELINE, cwd=work)
    assert before.returncode == 0, before.stderr
    assert before.stdout.strip() == b"0.2.0"
    script = bindir / ("indgroup.exe" if sys.platform == "win32" else "indgroup")
    for command in ([script], [python, "-I", "-m", "indgroup"]):
        shown = _run(*command, "1234567.5", "-l", "de", cwd=work)
        assert shown.returncode == 0 and shown.stdout.strip() == b"1.234.567,5", shown.stderr
    upgraded = _run(python, "-m", "pip", "install", "--upgrade", wheel)
    assert upgraded.returncode == 0, upgraded.stderr
    after = _run(python, "-I", "-c", BASELINE, cwd=work)
    assert after.returncode == 0, after.stderr
    assert after.stdout.strip() == b"1.0.0"
    consumer = _run(python, "-I", "-c", PROGRAM, cwd=work)
    assert consumer.returncode == 0 and consumer.stdout.strip() == b"e2e ok", consumer.stderr
    for command in ([script], [python, "-I", "-m", "indgroup"]):
        parsed = _run(*command, "--parse", "1.234.567,5", "-l", "de", cwd=work)
        assert parsed.returncode == 0 and parsed.stdout.strip() == b"1234567.5", parsed.stderr
