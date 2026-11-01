"""The values the command line formats: every finite plain spelling a Decimal takes, in ASCII,
bounded by the library's 100,000 digits rather than by the length of the exponent."""

from __future__ import annotations

import decimal
import io
import re
import time

import pytest

from indgroup import _cli
from indgroup._args import HELP
from indgroup._cli import main


def run(*argv: str) -> tuple[int, str]:
    out = io.StringIO()
    status = main(list(argv), stdin=io.StringIO(""), stdout=out)
    return status, out.getvalue()


def error_of(capsys: pytest.CaptureFixture[str], *argv: str) -> str:
    with pytest.raises(SystemExit) as raised:
        run(*argv)
    assert raised.value.code == 2
    error = capsys.readouterr().err
    assert error.count("\n") == 1 and len(error) < 150, error[:200]
    return error


@pytest.mark.parametrize(
    ("argv", "expected"),
    [
        (["-l", "en", ".5"], "0.5\n"),
        (["-l", "en", "-.5"], "-0.5\n"),
        (["-l", "en", "--", ".5", "5.", "+.25"], "0.5\n5\n0.25\n"),
        (["-l", "de", "-1.e3"], "-1.000\n"),
        (["1e0005"], "1,00,000\n"),
        (["1E+3", "1e-3", "-0.5E1"], "1,000\n0.001\n-5\n"),
        (["0e99999999999999999999"], "0\n"),
        (["-0e-0"], "-0\n"),
        (["1e0000000005", "1e+0000000003", "7E00000000000000000002"], "1,00,000\n1,000\n700\n"),
        (["--", "25e-0000000001", "-4E-00000000002"], "2.5\n-0.04\n"),
    ],
)
def test_every_plain_decimal_spelling_formats(argv: list[str], expected: str) -> None:
    assert run(*argv) == (0, expected)


def test_the_exponent_is_bounded_by_the_digits_it_makes() -> None:
    status, out = run("-l", "en", "-g", "off", "1e10000")
    assert (status, out) == (0, "1" + "0" * 10_000 + "\n")
    status, out = run("-l", "en", "-g", "off", "1e99999")
    assert (status, len(out)) == (0, 100_001)
    status, out = run("-l", "en", "-g", "off", "1e-99999")
    assert (status, len(out)) == (0, 100_002)


@pytest.mark.parametrize(
    ("value", "part"),
    [
        ("1e100000", "integer part"),
        ("1e99999999999999999999", "integer part"),
        pytest.param("1e" + "9" * 100_000, "integer part", id="exponent-of-100000-digits"),
        ("1e-100001", "fraction"),
        ("-1e-" + "9" * 30, "fraction"),
        ("0e-100001", "fraction"),
        # Leading fractional zeros put these past the bound only through an exponent past
        # MAX_DIGITS + 2, so the exponent clamp must leave room for the mantissa's length.
        (".0001e100005", "integer part"),
        ("-.001e100004", "integer part"),
        ("+.001e100003", "integer part"),
    ],
)
def test_values_past_the_digit_bound_say_so(
    capsys: pytest.CaptureFixture[str], value: str, part: str
) -> None:
    assert f"more than 100,000 digits in its {part}" in error_of(capsys, "--", value)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("1e-100000", "0." + "0" * 99_999 + "1\n"),
        ("0.001e100002", "1" + "0" * 99_999 + "\n"),
        ("0.1e100000", "1" + "0" * 99_999 + "\n"),
        ("-.1e100000", "-1" + "0" * 99_999 + "\n"),
    ],
    ids=["1e-100000", "0.001e100002", "0.1e100000", "-.1e100000"],
)
def test_values_at_the_digit_bound_written_with_an_exponent_as_long_as_the_bound(
    value: str, expected: str
) -> None:
    assert run("-l", "en", "-g", "off", "--", value) == (0, expected)
    status, out = run("-l", "en", "--", value)
    assert status == 0 and out.replace(",", "") == expected


def _decimal_of_a_32_bit_build(text: str) -> decimal.Decimal:
    # libmpdec on a 32-bit build refuses an exponent past 425,000,000 with InvalidOperation.
    exponent = re.search(r"[eE]([+-]?[0-9]+)$", text)
    if exponent is not None and abs(int(exponent.group(1))) > 425_000_000:
        raise decimal.InvalidOperation([decimal.InvalidOperation])
    return decimal.Decimal(text)


@pytest.mark.parametrize(
    ("value", "part"),
    [
        ("1e500000000", "integer part"),
        ("1e999999999", "integer part"),
        ("1e-99999999999", "fraction"),
        ("+.590E-896824052", "fraction"),
        ("80E-156207682318855", "fraction"),
    ],
)
def test_a_huge_exponent_stays_within_the_limits_of_a_32_bit_build(
    capsys: pytest.CaptureFixture[str], monkeypatch: pytest.MonkeyPatch, value: str, part: str
) -> None:
    monkeypatch.setattr(_cli, "Decimal", _decimal_of_a_32_bit_build)
    assert f"more than 100,000 digits in its {part}" in error_of(capsys, "--", value)
    assert run("--", "0e99999999999", "-0e999999999") == (0, "0\n-0\n")


@pytest.mark.parametrize(
    "value",
    [
        *["1e", ".", "e5", "-.", "1.2.3", "0x10", "1_000", "+-1", "", "1 000", "Infinity"],
        *["NaN", chr(0xFF11), "1e+-5", "1e5.0", chr(0x0661), "1" + chr(0x00A0) + "000"],
    ],
)
def test_anything_else_is_not_a_plain_number(
    capsys: pytest.CaptureFixture[str], value: str
) -> None:
    assert "not a plain number" in error_of(capsys, "--", value)


def test_a_huge_exponent_is_read_in_linear_time(capsys: pytest.CaptureFixture[str]) -> None:
    for value in ["1e" + "0" * 2_000_000 + "x", "1e" + "0" * 2_000_000 + "5"]:
        started = time.perf_counter()
        status = 0
        try:
            status = run("--", value)[0]
        except SystemExit as raised:
            status = int(str(raised.code))
        assert time.perf_counter() - started < 1
        assert status in (0, 2)
    capsys.readouterr()


def test_help_states_the_value_grammar() -> None:
    assert ".5" in HELP and "1e6" in HELP and "exponent" in HELP
