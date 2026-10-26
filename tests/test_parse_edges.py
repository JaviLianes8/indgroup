"""Strict parsing at its edges, and str subclasses that try to change what is read."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

import pytest

from indgroup import (
    Grouping,
    Number,
    format_indian,
    format_number,
    number_symbols,
    parse_indian,
    parse_number,
    resolve_locale,
)

LEADING_ZERO_GROUPS: list[Callable[[], object]] = [
    lambda: parse_number("0,001", "en"),
    lambda: parse_number("0.001", "de"),
    lambda: parse_number("000,001", "en"),
    lambda: parse_number("0,000,000", "en"),
    lambda: parse_number("01,234", "en"),
    lambda: parse_number("-0,001", "en"),
    lambda: parse_number("0,00,001", "en-IN"),
    lambda: parse_number("0\u202f001", "fr"),
    lambda: parse_indian("00,01,234"),
    lambda: parse_indian("0,01,234"),
    lambda: parse_indian("+0,001"),
]


@pytest.mark.parametrize("call", LEADING_ZERO_GROUPS)
def test_a_grouped_integer_cannot_start_with_zero(call: Callable[[], object]) -> None:
    # The formatter never writes these, and "0,001" is likelier a misread decimal comma.
    with pytest.raises(ValueError, match="not a validly grouped integer"):
        call()


def test_ungrouped_leading_zeros_and_zero_itself_still_read() -> None:
    assert parse_number("0", "en") == 0 and parse_number("-0", "en") == 0
    assert parse_number("007", "en") == 7 and parse_indian("0123") == 123
    assert parse_number("0,5", "de") == Decimal("0.5")
    assert parse_number("1,000", "en") == 1000 and parse_indian("10,00,000") == 10**6


def test_text_written_by_the_formatters_reads_back_to_the_same_text() -> None:
    values: list[Number] = [0, 7, 1000, -1234567, 0.25, Decimal("0.001"), Decimal("-1234.50")]
    groupings: list[Grouping] = ["auto", "min2", "always", "off"]
    for value in values:
        for locale in ["en", "de", "es", "fr", "en-IN", "de-CH", "sv"]:
            for grouping in groupings:
                text = format_number(value, locale, grouping=grouping)
                assert format_number(parse_number(text, locale), locale, grouping=grouping) == text
        assert format_indian(parse_indian(format_indian(value))) == format_indian(value)


class Hostile(str):
    """A str whose methods all lie; only its value may be read."""

    __hash__ = str.__hash__

    def __eq__(self, other: object) -> bool:
        return True

    def __len__(self) -> int:
        return 0

    def __str__(self) -> str:
        return "999"

    def join(self, parts: object) -> str:
        return "X"

    def strip(self, chars: str | None = None) -> str:
        return "999"

    def partition(self, separator: str) -> tuple[str, str, str]:
        return ("de", "", "")

    def split(self, *args: object, **kwargs: object) -> list[str]:
        return ["de"]

    def replace(self, *args: object, **kwargs: object) -> str:
        return "de"

    def lower(self) -> str:
        return "de"

    def startswith(self, *args: object, **kwargs: object) -> bool:
        return True


def test_str_subclasses_are_read_by_their_value() -> None:
    assert parse_number(Hostile("1"), "en") == 1
    assert parse_number(Hostile("-1.234,5"), "de") == Decimal("-1234.5")
    assert parse_indian(Hostile("12,34,567")) == 1234567
    assert resolve_locale(Hostile("en")) == "en"
    assert format_number(1234.5, Hostile("en")) == "1,234.5"
    assert number_symbols(Hostile("en_IN.UTF-8")).locale == "en-IN"
    assert format_indian(1234567, separator=Hostile(",")) == "12,34,567"
    assert parse_indian("12,34,567", separator=Hostile(",")) == 1234567
    assert format_number(1234567, "en", grouping=Hostile("off")) == "1234567"  # type: ignore[arg-type]


def test_str_subclasses_cannot_fake_a_valid_grouping_or_hide_their_length() -> None:
    with pytest.raises(ValueError):
        format_number(1234567, "en", grouping=Hostile("bogus"))  # type: ignore[arg-type]
    with pytest.raises(ValueError) as raised:
        resolve_locale(Hostile("@" * 100_000))
    assert len(str(raised.value)) < 120 and "100000 characters" in str(raised.value)
    with pytest.raises(ValueError) as raised:
        parse_number(Hostile("x" * 100_000), "en")
    assert len(str(raised.value)) < 120 and "100000 characters" in str(raised.value)
