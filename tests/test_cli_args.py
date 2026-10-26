"""The command line reads its arguments and reports errors the same way on every Python."""

from __future__ import annotations

import io
import os
import subprocess
import sys
from pathlib import Path

import pytest

import indgroup
from indgroup import __version__, parse_number, supported_locales
from indgroup._cli import main

LONG = "A" * 20_000


def _python(*argv: str) -> list[str]:
    return [sys.executable, "-m", "indgroup", *argv]


def _env() -> dict[str, str]:
    # The folder holding the package under test: the source tree or an installed wheel.
    home = str(Path(indgroup.__file__).resolve().parents[1])
    return {**os.environ, "PYTHONPATH": home, "PYTHONIOENCODING": "utf-8"}


def run(*argv: str, stdin: str = "") -> tuple[int, str]:
    out = io.StringIO()
    status = main(list(argv), stdin=io.StringIO(stdin), stdout=out)
    return status, out.getvalue()


def error_of(capsys: pytest.CaptureFixture[str], *argv: str, stdin: str = "") -> str:
    """The whole of stderr for a command that must exit with status 2."""
    with pytest.raises(SystemExit) as raised:
        run(*argv, stdin=stdin)
    assert raised.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == ""
    return captured.err


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["-1e5"], "-1,00,000\n"),
        (["-l", "en", "-1.5e3"], "-1,500\n"),
        (["-p", "-0.5"], "-0.5\n"),
        (["-p", "-l", "de", "-1.234,5"], "-1234.5\n"),
        (["-p", "-1,00,000"], "-100000\n"),
        (["7", "-1e5", "-l", "de"], "7\n-100.000\n"),
        (["--", "-1e5"], "-1,00,000\n"),
    ],
)
def test_negative_values_need_no_double_dash(argv: list[str], expected: str) -> None:
    assert run(*argv) == (0, expected)


def test_a_negative_value_is_the_same_by_subprocess() -> None:
    done = subprocess.run(_python("-l", "en", "-1e5"), capture_output=True, env=_env(), check=False)
    assert (done.returncode, done.stdout.decode().strip(), done.stderr) == (0, "-100,000", b"")


@pytest.mark.parametrize(
    "argv",
    [
        ["-g", "bogus", "1"],
        ["-g", LONG, "1"],
        ["--nope", "1"],
        ["--x" + LONG, "1"],
        ["--parse=" + LONG],
        ["-p" + LONG],
        ["--lo=" + LONG],
        ["--locales=yes"],
        ["-l"],
        ["1", "--grouping"],
        ["-x"],
        ["- 5"],
    ],
)
def test_argument_errors_are_one_short_line(
    capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    error = error_of(capsys, *argv)
    assert error.startswith("indgroup: error: ")
    assert error.count("\n") == 1 and error.endswith("\n"), error[:300]
    assert len(error) < 150, error[:300]


def test_argument_errors_name_the_problem(capsys: pytest.CaptureFixture[str]) -> None:
    assert "auto, min2, always, off" in error_of(capsys, "-g", "sometimes", "1")
    assert "'--nope'" in error_of(capsys, "--nope", "1")
    assert "20003 characters" in error_of(capsys, "--x" + LONG)
    assert "--locale" in error_of(capsys, "-l")
    assert "ambiguous" in error_of(capsys, "--loca", "de")
    assert "not a plain number: '-1.2.3'" in error_of(capsys, "-1.2.3")


def test_abbreviated_and_attached_options() -> None:
    assert run("--locale", "de", "1234567") == (0, "1.234.567\n")
    assert run("--locale=de", "--group=off", "1234567") == (0, "1234567\n")
    assert run("-lde", "-goff", "1234567") == (0, "1234567\n")
    assert run("-pl", "de", "1.234") == (0, "1234\n")
    assert run("--pars", "12,34,567") == (0, "1234567\n")


def test_help_and_version_print_to_stdout_and_exit_zero() -> None:
    status, out = run("--help")
    assert status == 0 and out.startswith("usage: indgroup ")
    for option in ("--locale", "--grouping", "--parse", "--locales", "--version"):
        assert option in out
    assert run("-h", "--nope") == (0, out)
    assert run("--version") == (0, f"indgroup {__version__} (CLDR 48.2.0)\n")


def test_locales_ends_with_a_newline() -> None:
    assert run("--locales") == (0, "\n".join(supported_locales()) + "\n")


@pytest.mark.parametrize("value", ["1.2.3", ".", "1e", "e5", "0x10", "1_000", "+-1", ""])
def test_values_must_be_plain_numbers(capsys: pytest.CaptureFixture[str], value: str) -> None:
    assert "not a plain number" in error_of(capsys, "--", value)


def test_ascii_spaces_around_a_value_are_ignored_in_arguments_and_stdin() -> None:
    assert run(" 5 ", "\t-7\r\n") == (0, "5\n-7\n")
    assert run(stdin=" 5 \n\t-7\t\n") == (0, "5\n-7\n")
    assert run("-p", "-l", "fr", stdin=" 1\u202f234 \n") == (0, "1234\n")


@pytest.mark.parametrize(
    "line", ["1\u202f234\u202f", "\u20031\u202f234", "\xa01\u202f234", "1\u202f234\u2028"]
)
def test_stdin_keeps_unicode_spaces_and_group_symbols(
    capsys: pytest.CaptureFixture[str], line: str
) -> None:
    # The same rule as parse_number: only ASCII spaces, tabs and line breaks are trimmed.
    assert "not a validly grouped integer" in error_of(capsys, "-p", "-l", "fr", stdin=line + "\n")
    with pytest.raises(ValueError):
        parse_number(line, "fr")


def test_a_line_of_unicode_space_is_a_value_not_a_blank(capsys: pytest.CaptureFixture[str]) -> None:
    assert "not a plain number" in error_of(capsys, stdin="1\n\xa0\n")


class _ClosedPipe(io.StringIO):
    def write(self, text: str) -> int:
        raise BrokenPipeError(32, "Broken pipe")


def test_a_closed_pipe_stops_quietly_with_status_one(capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["1234567"], stdin=io.StringIO(), stdout=_ClosedPipe()) == 1
    assert capsys.readouterr().err == ""


def test_a_reader_that_closes_early_gets_no_traceback() -> None:
    process = subprocess.Popen(
        _python("-l", "en"),
        env=_env(),
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert process.stdin and process.stdout and process.stderr
    process.stdin.write(b"1234567\n" * 300_000)
    process.stdin.close()
    assert process.stdout.readline().strip() == b"1,234,567"
    process.stdout.close()
    error = process.stderr.read()
    assert process.wait(timeout=120) == 1
    assert error == b""
