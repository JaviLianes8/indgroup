from __future__ import annotations

import io

import pytest

from indgroup import __version__, supported_locales
from indgroup._cli import main


def run(*argv: str, stdin: str = "") -> tuple[int, str]:
    out = io.StringIO()
    status = main(list(argv), stdin=io.StringIO(stdin), stdout=out)
    return status, out.getvalue()


def fails(capsys: pytest.CaptureFixture[str], *argv: str, stdin: str = "") -> str:
    with pytest.raises(SystemExit) as raised:
        run(*argv, stdin=stdin)
    assert raised.value.code == 2
    return capsys.readouterr().err


def test_formats_arguments_in_the_indian_convention_by_default() -> None:
    assert run("1234567", "-1234.50", "1e6") == (0, "12,34,567\n-1,234.50\n10,00,000\n")


def test_locale_and_grouping_options() -> None:
    assert run("1234567.5", "-l", "de") == (0, "1.234.567,5\n")
    assert run("1234", "--locale", "es") == (0, "1234\n")
    assert run("1234", "-l", "es", "--grouping", "always") == (0, "1.234\n")
    assert run("1234567", "-g", "off") == (0, "1234567\n")


def test_parse_prints_plain_values() -> None:
    assert run("--parse", "12,34,567", "1,234.50") == (0, "1234567\n1234.50\n")
    assert run("-p", "-l", "de", "--", "-1.234,5") == (0, "-1234.5\n")


def test_values_from_stdin_skip_blank_lines_and_a_bom() -> None:
    assert run(stdin="\ufeff1234567\r\n\n  \n-5\n") == (0, "12,34,567\n-5\n")


def test_no_values_print_nothing() -> None:
    assert run() == (0, "")


def test_locales_lists_the_table() -> None:
    status, out = run("--locales")
    assert status == 0
    assert out.splitlines() == list(supported_locales())


def test_version(capsys: pytest.CaptureFixture[str]) -> None:
    with pytest.raises(SystemExit):
        run("--version")
    assert capsys.readouterr().out.strip() == f"indgroup {__version__} (CLDR 48.0.0)"


def test_bad_values_and_locales_exit_with_status_two(capsys: pytest.CaptureFixture[str]) -> None:
    assert "not a plain number" in fails(capsys, "12,345")
    assert "not a plain number" in fails(capsys, "1e99999")
    assert "no number data" in fails(capsys, "1", "-l", "xx")
    assert "not a validly grouped" in fails(capsys, "-p", "1,234,567")
    assert "invalid choice" in fails(capsys, "1", "-g", "sometimes")


def test_a_terminal_without_values_is_a_usage_error(capsys: pytest.CaptureFixture[str]) -> None:
    class Terminal(io.StringIO):
        def isatty(self) -> bool:
            return True

    with pytest.raises(SystemExit) as raised:
        main([], stdin=Terminal(), stdout=io.StringIO())
    assert raised.value.code == 2
    assert "no values" in capsys.readouterr().err


def test_invalid_utf8_on_stdin_is_reported(capsys: pytest.CaptureFixture[str]) -> None:
    raw = io.TextIOWrapper(io.BytesIO(b"\xff\xfe12\n"), encoding="utf-8")
    with pytest.raises(SystemExit) as raised:
        main([], stdin=raw, stdout=io.StringIO())
    assert raised.value.code == 2
    assert "not valid UTF-8" in capsys.readouterr().err
