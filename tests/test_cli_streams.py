"""The command line with standard streams that are missing, closed or failing."""

from __future__ import annotations

import errno
import io
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import indgroup
from indgroup._cli import main

NO_VALUES = b"indgroup: error: no values: pass VALUE arguments or pipe them on stdin"
SHELL = shutil.which("sh")


def _python(*argv: str) -> list[str]:
    return [sys.executable, "-m", "indgroup", *argv]


def _env() -> dict[str, str]:
    home = str(Path(indgroup.__file__).resolve().parents[1])
    return {**os.environ, "PYTHONPATH": home, "PYTHONIOENCODING": "utf-8"}


@pytest.mark.parametrize("argv", [["1234567"], ["--help"], ["--version"], ["--locales"]])
def test_a_missing_stdout_stops_quietly_with_status_one(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    # Python sets sys.stdout to None when the process starts without file descriptor 1.
    monkeypatch.setattr(sys, "stdout", None)
    assert main(argv, stdin=io.StringIO()) == 1
    assert capsys.readouterr().err == ""


def test_a_missing_stdout_with_nothing_to_write_is_success(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(sys, "stdout", None)
    assert main([], stdin=io.StringIO("\n\n")) == 0


def test_a_missing_stdin_is_no_input(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setattr(sys, "stdin", None)
    with pytest.raises(SystemExit) as raised:
        main([], stdout=io.StringIO())
    assert raised.value.code == 2
    assert capsys.readouterr().err == NO_VALUES.decode() + "\n"
    out = io.StringIO()
    assert main(["-l", "de", "1234567"], stdout=out) == 0
    assert out.getvalue() == "1.234.567\n"


def test_a_missing_stderr_still_exits_with_status_two(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(sys, "stderr", None)
    with pytest.raises(SystemExit) as raised:
        main(["--nope"], stdin=io.StringIO(), stdout=io.StringIO())
    assert raised.value.code == 2


@pytest.mark.skipif(SHELL is None, reason="needs a POSIX shell to start with a stream closed")
@pytest.mark.parametrize(
    ("argv", "redirect", "expected"),
    [
        (["5"], ">&-", (1, b"", b"")),
        (["--locales"], ">&-", (1, b"", b"")),
        ([], "<&-", (2, b"", NO_VALUES)),
        (["-l", "de", "1234567"], "<&-", (0, b"1.234.567", b"")),
        (["-l", "zz", "1"], "2>&-", (2, b"", b"")),
    ],
)
def test_a_closed_standard_stream_gives_no_traceback(
    argv: list[str], redirect: str, expected: tuple[int, bytes, bytes]
) -> None:
    assert SHELL is not None
    script = f'exec "$0" -m indgroup "$@" {redirect}'
    command = [SHELL, "-c", script, sys.executable, *argv]
    done = subprocess.run(command, capture_output=True, env=_env(), timeout=120, check=False)
    assert (done.returncode, done.stdout.strip(), done.stderr.strip()) == expected


@pytest.mark.parametrize(
    ("argv", "stdin"),
    [(["1234567"], b""), (["--locales"], b""), (["--version"], b""), (["-l", "en"], b"1\n")],
)
def test_a_reader_gone_before_the_first_write_gets_no_traceback(
    argv: list[str], stdin: bytes
) -> None:
    # The read end is closed before the command starts, so its first write fails.
    read, write = os.pipe()
    os.close(read)
    try:
        done = subprocess.run(
            _python(*argv),
            input=stdin,
            stdout=write,
            stderr=subprocess.PIPE,
            env=_env(),
            timeout=120,
            check=False,
        )
    finally:
        os.close(write)
    assert (done.returncode, done.stderr) == (1, b"")


class _Failing(io.StringIO):
    def __init__(self, code: int) -> None:
        super().__init__()
        self.code = code

    def write(self, text: str) -> int:
        raise OSError(self.code, os.strerror(self.code))


@pytest.mark.parametrize("code", [errno.EIO, errno.ENOSPC])
def test_other_write_errors_are_raised_not_taken_for_a_closed_pipe(code: int) -> None:
    with pytest.raises(OSError) as raised:
        main(["1"], stdin=io.StringIO(), stdout=_Failing(code))
    assert raised.value.errno == code
    assert not isinstance(raised.value, BrokenPipeError)


@pytest.mark.parametrize(
    ("argv", "stdin"),
    [(["-l", "zz", "1"], b""), (["--nope"], b""), (["-l", "en"], b"abc\n"), ([], b"\xff\n")],
)
def test_a_stderr_reader_gone_before_the_error_still_gives_status_two(
    argv: list[str], stdin: bytes
) -> None:
    # Without care, Python turns the failed flush of the error line into status 120 at exit.
    read, write = os.pipe()
    os.close(read)
    try:
        done = subprocess.run(
            _python(*argv),
            input=stdin,
            stdout=subprocess.PIPE,
            stderr=write,
            env=_env(),
            timeout=120,
            check=False,
        )
    finally:
        os.close(write)
    assert (done.returncode, done.stdout) == (2, b"")


def test_a_closed_stderr_in_process_still_exits_with_status_two(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _Gone(io.StringIO):
        def write(self, text: str) -> int:
            raise BrokenPipeError(errno.EPIPE, os.strerror(errno.EPIPE))

    monkeypatch.setattr(sys, "stderr", _Gone())
    with pytest.raises(SystemExit) as raised:
        main(["--nope"], stdin=io.StringIO(), stdout=io.StringIO())
    assert raised.value.code == 2
