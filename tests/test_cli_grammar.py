"""The option grammar of the command line, edge by edge."""

from __future__ import annotations

import io
import time

import pytest

from indgroup import __version__, supported_locales
from indgroup._cli import main

LOCALES = "\n".join(supported_locales()) + "\n"


def run(*argv: str, stdin: str = "") -> tuple[int, str]:
    out = io.StringIO()
    status = main(list(argv), stdin=io.StringIO(stdin), stdout=out)
    return status, out.getvalue()


def error_of(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    with pytest.raises(SystemExit) as raised:
        run(*argv)
    assert raised.value.code == 2
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err.count("\n") == 1
    return captured.err


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["--", "1", "-2", "3"], "1\n-2\n3\n"),
        (["-l", "en", "--", "3", "-1e5", "1", "--"], None),
        (["7", "-l", "de", "--", "1234", "-5", "2"], "7\n1.234\n-5\n2\n"),
    ],
)
def test_values_after_a_double_dash_keep_their_order(
    capsys: pytest.CaptureFixture[str], argv: list[str], expected: str | None
) -> None:
    if expected is None:  # a second "--" is a value, and not a number
        assert "not a plain number: '--'" in error_of(capsys, *argv)
    else:
        assert run(*argv) == (0, expected)


def test_any_unique_prefix_of_three_characters_names_an_option() -> None:
    assert run("--p", "12,34,567") == (0, "1234567\n")
    assert run("--v") == (0, f"indgroup {__version__} (CLDR 48.0.0)\n")
    assert run("--h")[1].startswith("usage: indgroup ")


@pytest.mark.parametrize(
    "argv", [["-p", "-g", "bogus", "12,34,567"], ["--locales", "-g", "bogus"], ["-pg", "bogus"]]
)
def test_a_bad_grouping_is_refused_whatever_else_is_asked(
    capsys: pytest.CaptureFixture[str], argv: list[str]
) -> None:
    assert "--grouping must be one of auto, min2, always, off" in error_of(capsys, *argv)


def test_a_short_option_takes_its_value_after_an_equals_sign() -> None:
    assert run("-l=de", "1234567") == (0, "1.234.567\n")
    assert run("-g=off", "-l", "de", "1234567") == (0, "1234567\n")
    assert run("-pl=de", "1.234") == (0, "1234\n")


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["--parse=l", "de", "1.234"], "--parse takes no value: '--parse=l'"),
        (["--locales=", "1"], "--locales takes no value"),
        (["-p=x", "1"], "--parse takes no value: '-p=x'"),
        (["-px", "1"], "unknown option '-x' in '-px'"),
        (["-xp", "1"], "unknown option '-xp'"),
    ],
)
def test_flags_take_no_value(
    capsys: pytest.CaptureFixture[str], argv: list[str], message: str
) -> None:
    assert message in error_of(capsys, *argv)


def test_locales_wins_over_other_flags_in_any_order() -> None:
    assert run("--locales", "-p") == (0, LOCALES)
    assert run("-p", "--locales", "-l", "de") == (0, LOCALES)


def test_a_lone_dash_is_a_value(capsys: pytest.CaptureFixture[str]) -> None:
    assert run("--locales", "-") == (0, LOCALES)
    assert run("-", "--version") == (0, f"indgroup {__version__} (CLDR 48.0.0)\n")
    assert "not a plain number: '-'" in error_of(capsys, "-")


def test_a_short_option_cluster_is_read_in_order() -> None:
    assert run("-ppl", "de", "1.234") == (0, "1234\n")
    assert run("-plde", "1.234") == (0, "1234\n")
    assert run("-ph", "--nope")[1].startswith("usage: indgroup ")


def test_help_and_version_end_the_reading_in_their_long_form_too() -> None:
    status, out = run("--help", "--nope")
    assert status == 0 and out.startswith("usage: indgroup ")
    assert run("--help", "--version")[1].startswith("usage: indgroup ")
    assert run("--version", "--help") == (0, f"indgroup {__version__} (CLDR 48.0.0)\n")


GROUPING = "--grouping must be one of auto, min2, always, off, not "


@pytest.mark.parametrize(
    ("argv", "message"),
    [
        (["-l==de", "1234567"], "not a locale tag: '=de'"),
        (["-g==off", "1234567"], GROUPING + "'=off'"),
        (["-l=", "de", "1234567"], "not a plain number: 'de'"),
        (["--locale=", "de", "1234567"], "not a plain number: 'de'"),
        (["--locale=", "1234567"], "not a locale tag: ''"),
        (["-g=", "off", "1234567"], GROUPING + "''"),
        (["--grouping=", "off", "1234567"], GROUPING + "''"),
        (["--grouping", " off", "1234567"], GROUPING + "' off'"),
        (["-g", " off", "1234567"], GROUPING + "' off'"),
        (["--locale", " de", "1234567"], "not a locale tag: ' de'"),
    ],
)
def test_an_option_value_is_taken_as_written(
    capsys: pytest.CaptureFixture[str], argv: list[str], message: str
) -> None:
    # One equals sign joins an option to its value; an empty value stays empty, and
    # nothing else is trimmed or taken from the next argument.
    assert error_of(capsys, *argv) == f"indgroup: error: {message}\n"


def _seconds(argv: list[str]) -> float:
    # CPU time of this process, so other work on a busy machine does not count.
    started = time.process_time()
    assert run(*argv) == (0, "1\n")
    return time.process_time() - started


def test_a_long_option_cluster_is_read_in_linear_time() -> None:
    # The same 400,000 flags as one argument and as separate ones cost about the same.
    size = 400_000
    separate = _seconds(["-p"] * size + ["1"])
    assert _seconds(["-" + "p" * size, "1"]) < 3 * separate + 0.2
