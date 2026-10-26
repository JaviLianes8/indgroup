"""Huge, malformed and hostile input: typed errors, short messages, bounded time."""

from __future__ import annotations

import contextlib
import io
import time
from collections.abc import Callable
from decimal import Decimal
from functools import partial

import pytest

from indgroup import (
    format_indian,
    format_number,
    number_symbols,
    parse_indian,
    parse_number,
    resolve_locale,
)
from indgroup._cli import main
from indgroup._value import MAX_DIGITS

HUGE = "9" * 1_000_000 + "x"


def _message(call: Callable[[], object], kind: type[Exception] = ValueError) -> str:
    with pytest.raises(kind) as raised:
        call()
    text = str(raised.value)
    assert len(text) < 120, text[:200]
    return text


def test_error_messages_quote_at_most_forty_characters_of_the_input() -> None:
    assert "1000001 characters" in _message(lambda: parse_number(HUGE, "en"))
    assert "1000001 characters" in _message(lambda: parse_indian(HUGE))
    _message(lambda: parse_number("1." + HUGE, "en"))
    _message(lambda: parse_indian("1," + HUGE))
    _message(lambda: resolve_locale("a" * 1_000_000))
    _message(lambda: resolve_locale("en-" + "a" * 1_000_000))
    _message(lambda: resolve_locale("zz-" + "-".join(["abcde"] * 100_000)), LookupError)
    _message(lambda: resolve_locale("zz-" + "b" * 8), LookupError)
    _message(lambda: format_number(1, "en", grouping="x" * 1_000_000))  # type: ignore[arg-type]
    _message(lambda: format_number(Decimal("sNaN"), "en"))
    _message(lambda: format_number(Decimal(f"1E+{10**9}"), "en"))
    _message(lambda: number_symbols("x" * 1_000_000))
    assert _message(lambda: parse_number("1,23", "en")) == ("not a validly grouped integer: '1,23'")


def test_the_cli_reports_huge_values_in_one_short_line(capsys: pytest.CaptureFixture[str]) -> None:
    for argv in (["--", HUGE], ["-p", HUGE], ["-l", "q" * 100_000, "1"]):
        with pytest.raises(SystemExit) as raised:
            main(argv, stdin=io.StringIO(""), stdout=io.StringIO())
        assert raised.value.code == 2
        error = capsys.readouterr().err
        assert error.count("\n") == 1 and len(error) < 150, error[:200]


def test_the_digit_bound_is_exact_on_both_sides_of_the_point() -> None:
    edge = "9" * MAX_DIGITS
    assert len(format_number(int(Decimal(edge)), "en", grouping="off")) == MAX_DIGITS
    assert len(format_number(Decimal("0." + edge), "en")) == MAX_DIGITS + 2
    assert len(format_indian(Decimal(f"1E+{MAX_DIGITS - 1}"))) > MAX_DIGITS
    assert parse_number(edge, "en") == 10**MAX_DIGITS - 1
    assert parse_number("1" + ",000" * (MAX_DIGITS // 3), "en") == 10 ** (MAX_DIGITS - 1)
    assert parse_number("0." + edge, "en") == Decimal("0." + edge)
    too_many = [
        lambda: format_number(10**MAX_DIGITS, "en"),
        lambda: format_number(-(10**MAX_DIGITS), "en"),
        lambda: format_number(Decimal(f"1E+{MAX_DIGITS}"), "en"),
        lambda: format_number(Decimal(f"1E-{MAX_DIGITS + 1}"), "en"),
        lambda: format_indian(Decimal("0." + edge + "1")),
        lambda: parse_number(edge + "9", "en"),
        lambda: parse_number("1" + ",000" * (MAX_DIGITS // 3 + 1), "en"),
        lambda: parse_number("0." + edge + "9", "en"),
        lambda: parse_indian(edge + "9"),
    ]
    for call in too_many:
        assert "more than 100,000 digits" in _message(call)


def test_zero_with_any_exponent_is_zero() -> None:
    assert format_number(Decimal("0E+999999999"), "en") == "0"
    assert format_number(Decimal("-0E+5"), "de") == "-0"
    assert format_indian(Decimal("0E-3")) == "0.000"


def _seconds(call: Callable[[], object]) -> float:
    # CPU time of this process, so other work on a busy machine does not count.
    started = time.process_time()
    with contextlib.suppress(ValueError):
        call()
    return time.process_time() - started


def test_the_largest_values_cost_no_more_than_their_one_conversion() -> None:
    # Python's own conversion of a 100,000-digit int to Decimal and back is quadratic; the
    # package's conversions are faster, and nothing else may cost much next to them.
    biggest = 10**MAX_DIGITS - 1
    grouped = format_indian(biggest)
    to_decimal = _seconds(lambda: Decimal(biggest))
    to_int = _seconds(lambda: int(Decimal(str(Decimal(biggest)))))
    assert _seconds(lambda: format_number(biggest, "en-IN")) < 3 * to_decimal + 0.2
    assert _seconds(lambda: parse_indian(grouped)) < 3 * to_int + 0.2
    huge = 1 << 40_000_000
    assert _seconds(lambda: format_number(huge, "en")) < 0.5  # refused before any conversion


@pytest.mark.parametrize(
    "text",
    [
        "1" + ",23" * 400_000 + ",4567",
        "12" + ",34" * 400_000 + "x",
        "1" * 2_000_000 + ".",
        "-" * 2_000_000,
        "1." + "2" * 2_000_000 + "x",
        " " * 2_000_000 + "1",
        "1" + ",234" * 400_000 + ",23",
    ],
    ids=[
        "indian-tail",
        "pairs-then-junk",
        "long-digits",
        "signs",
        "long-fraction",
        "spaces",
        "thousands",
    ],
)
def test_adversarial_shapes_are_refused_in_linear_time(text: str) -> None:
    assert _seconds(lambda: parse_indian(text)) < 1
    assert _seconds(lambda: parse_number(text, "en")) < 1


def test_lone_surrogates_and_nul_are_plain_value_errors() -> None:
    for text in ["\ud8001", "1\x00", "1,2\udfff3"]:
        _message(partial(parse_number, text, "en"))
        _message(partial(parse_indian, text))
    _message(lambda: resolve_locale("en-\ud800"))
    _message(lambda: format_indian(1, separator="\ud800\ud800"))
    assert format_indian(1234, separator="\ud800") == "1\ud800234"
