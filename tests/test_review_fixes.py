"""Regressions for the findings of the independent review of the 0.2.0 round."""

from __future__ import annotations

import time
from decimal import Context, Decimal

import pytest

from indgroup import format_indian, format_number, parse_indian, parse_number
from indgroup._value import MAX_DIGITS


def test_grouping_a_long_number_takes_linear_time() -> None:
    # A quadratic loop needs several seconds for a million digits; a linear one, milliseconds.
    started = time.perf_counter()
    text = format_number(Decimal(f"1E+{MAX_DIGITS - 1}"), "en")
    assert time.perf_counter() - started < 1.5
    assert text.startswith("1,000,") and text.endswith(",000")
    assert text.count(",") == MAX_DIGITS // 3


def test_numbers_past_python_int_string_limit_round_trip() -> None:
    value = 10**5000 + 7
    shown = format_number(value, "en-IN")
    assert parse_number(shown, "en-IN") == value
    assert parse_indian(format_indian(value)) == value
    assert format_number(Decimal("1E+5000"), "de").count(".") == 5000 // 3


def test_values_beyond_the_digit_bound_are_refused() -> None:
    with pytest.raises(ValueError):
        format_number(Decimal(f"1E+{MAX_DIGITS}"), "en")
    assert len(format_number(Decimal(f"1E+{MAX_DIGITS - 1}"), "en", grouping="off")) == MAX_DIGITS


def test_negative_zero_reads_back_as_zero() -> None:
    assert format_number(Decimal("-0"), "en") == "-0"
    assert parse_number("-0", "en") == 0
    assert str(parse_number("-0.0", "en")) == "-0.0"


def test_group_symbols_are_not_stripped_as_whitespace() -> None:
    for text in ["1\u202f234\u202f", "\u202f1234", "\u00a01\u202f234"]:
        with pytest.raises(ValueError):
            parse_number(text, "fr")
    assert parse_number(" \t1\u202f234\r\n", "fr") == 1234


def test_decimal_subclasses_cannot_change_the_digits() -> None:
    class Shown(Decimal):
        def __format__(self, spec: str, context: Context | None = None, /) -> str:
            return "9999999"

        def is_finite(self) -> bool:
            return True

    assert format_number(Shown("1"), "en") == "1"
    assert format_indian(Shown("12345")) == "12,345"
    with pytest.raises(ValueError):
        format_number(Shown("NaN"), "en")


def test_whole_floats_print_without_a_fraction_like_intl() -> None:
    assert format_number(5.0, "en") == "5"
    assert format_number(1e15, "en") == "1,000,000,000,000,000"
    assert format_number(-0.0, "en") == "-0"
    assert format_number(2.50, "de") == "2,5"
