"""The command line's standard streams are UTF-8 on a pipe, whatever the system encoding."""

from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path
from typing import cast

import pytest

import indgroup
from indgroup._cli import main as indgroup_main

NNBSP = "\u202f"
ON_WINDOWS = sys.platform == "win32"


def _legacy_env() -> dict[str, str]:
    # Python's own UTF-8 switches are turned off, so the pipes start in the system encoding
    # (the ANSI code page on Windows, ASCII under the C locale elsewhere).
    env = {
        name: value
        for name, value in os.environ.items()
        if name not in ("PYTHONIOENCODING", "PYTHONUTF8", "PYTHONLEGACYWINDOWSSTDIO")
    }
    env["PYTHONPATH"] = str(Path(indgroup.__file__).resolve().parents[1])
    env["PYTHONUTF8"] = "0"
    if not ON_WINDOWS:
        env.update(LC_ALL="C", PYTHONCOERCECLOCALE="0")
    return env


def _run(argv: list[str], stdin: bytes = b"") -> tuple[int, bytes, bytes]:
    done = subprocess.run(
        [sys.executable, "-m", "indgroup", *argv],
        input=stdin,
        capture_output=True,
        env=_legacy_env(),
        timeout=120,
        check=False,
    )
    # Text streams end lines with CRLF on Windows.
    return done.returncode, done.stdout.replace(b"\r\n", b"\n"), done.stderr.replace(b"\r\n", b"\n")


def _error(message: str) -> bytes:
    return f"indgroup: error: {message}\n".encode()


@pytest.mark.parametrize(
    ("argv", "stdin", "expected"),
    [
        (["-p", "-l", "fr"], f"1{NNBSP}234{NNBSP}567\n".encode(), (0, b"1234567\n", b"")),
        (["-l", "de"], b"\xef\xbb\xbf1234567\n", (0, b"1.234.567\n", b"")),
        (["-l", "de"], b"\xff1234\n", (2, b"", _error("stdin is not valid UTF-8"))),
    ],
)
def test_stdin_is_read_as_utf8_and_a_byte_order_mark_is_skipped(
    argv: list[str], stdin: bytes, expected: tuple[int, bytes, bytes]
) -> None:
    assert _run(argv, stdin) == expected


def test_stdout_is_written_as_utf8() -> None:
    grouped = f"1{NNBSP}234{NNBSP}567\n".encode()
    assert _run(["-l", "fr"], b"1234567\n") == (0, grouped, b"")
    assert _run(["-l", "fr", "1234567"]) == (0, grouped, b"")


@pytest.mark.parametrize("value", ["1x\u20ac", "\u00e9", "\u65e5\u672c"])
def test_errors_quote_a_value_read_from_stdin_as_utf8_text(value: str) -> None:
    stdin = f"{value}\n".encode()
    expected = _error(f"not a plain number: '{value}'")
    assert _run(["-l", "de"], stdin) == (2, b"", expected)


@pytest.mark.skipif(not ON_WINDOWS, reason="elsewhere arguments arrive as bytes in the C locale")
@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["-\u00e9", "1"], "unknown option '-\u00e9'"),
        (["-l", "de", "1x\u20ac"], "not a plain number: '1x\u20ac'"),
        (["-l", "\u65e5\u672c", "1"], "not a locale tag: '\u65e5\u672c'"),
    ],
)
def test_errors_quote_an_argument_as_utf8_text(argv: list[str], message: str) -> None:
    assert _run(argv) == (2, b"", _error(message))


def _legacy(data: bytes = b"") -> io.TextIOWrapper:
    return io.TextIOWrapper(io.BytesIO(data), encoding="cp1252", errors="backslashreplace")


def test_the_process_streams_are_left_utf8_with_stderr_still_escaping(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Python's own messages written later, a traceback for one, must not fail on stderr.
    monkeypatch.setattr(sys, "stdin", _legacy(b"\xef\xbb\xbf1234567\n"))
    monkeypatch.setattr(sys, "stdout", _legacy())
    monkeypatch.setattr(sys, "stderr", _legacy())
    assert indgroup_main(["-l", "de"]) == 0
    streams = [(stream.encoding, stream.errors) for stream in (sys.stdin, sys.stdout, sys.stderr)]
    assert streams == [("utf-8-sig", "strict"), ("utf-8", "strict"), ("utf-8", "backslashreplace")]
    sys.stderr.write("\udc80")
    sys.stderr.flush()
    assert cast(io.BytesIO, sys.stderr.buffer).getvalue() == b"\\udc80"
    sys.stdout.flush()
    assert cast(io.BytesIO, sys.stdout.buffer).getvalue().splitlines() == [b"1.234.567"]
