from __future__ import annotations

from decimal import Decimal

import pytest

from indgroup import NumberSymbols, format_number, number_symbols, parse_number

NNBSP = "\u202f"
NBSP = "\u00a0"


def test_formats_with_each_locale_symbols() -> None:
    assert format_number(1234567.5, "en") == "1,234,567.5"
    assert format_number(1234567.5, "de") == "1.234.567,5"
    assert format_number(1234567.5, "fr") == f"1{NNBSP}234{NNBSP}567,5"
    assert format_number(1234567.5, "de-CH") == "1'234'567.5"
    assert format_number(1234567.5, "ru") == f"1{NBSP}234{NBSP}567,5"
    assert format_number(1234567, "en-IN") == "12,34,567"
    assert format_number(1234567, "hi") == "12,34,567"


def test_minimum_grouping_digits_leave_short_numbers_ungrouped() -> None:
    assert format_number(1234, "es") == "1234"
    assert format_number(12345, "es") == "12.345"
    assert format_number(-1234, "pl") == "-1234"
    assert format_number(1234, "ee") == "1234"
    assert format_number(12345, "ee") == "12345"
    assert format_number(123456, "ee") == "123,456"


def test_grouping_strategies_follow_intl() -> None:
    assert format_number(1234, "es", grouping="always") == "1.234"
    assert format_number(1234, "en", grouping="min2") == "1234"
    assert format_number(12345, "en", grouping="min2") == "12,345"
    assert format_number(12345, "ee", grouping="min2") == "12345"
    assert format_number(1234567, "en", grouping="off") == "1234567"


def test_always_groups_by_thousands_without_a_grouping_pattern(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    plain = NumberSymbols("xx", ".", ",", "-", 0, 0, 1)
    monkeypatch.setattr("indgroup._number.number_symbols", lambda locale: plain)
    assert format_number(1234567, "xx") == "1234567"
    assert format_number(1234567, "xx", grouping="always") == "1,234,567"


def test_minus_signs_come_from_the_locale() -> None:
    assert format_number(-5, "sv") == "\u22125"
    assert format_number(-5, "fa") == "\u200e\u22125"
    assert format_number(Decimal("-0.0"), "en") == "-0.0"


def test_keeps_every_fraction_digit_without_rounding() -> None:
    assert format_number(Decimal("1234.5000"), "de") == "1.234,5000"
    assert format_number(Decimal("0.1234567890123456789"), "en") == "0.1234567890123456789"
    assert format_number(0.1 + 0.2, "en") == "0.30000000000000004"
    assert format_number(Decimal("1E+5"), "en") == "100,000"


def test_rejects_unknown_grouping_and_bad_values() -> None:
    for grouping in ["yes", "", True]:
        with pytest.raises(ValueError):
            format_number(1, "en", grouping=grouping)  # type: ignore[arg-type]
    with pytest.raises(TypeError):
        format_number(False, "en")
    with pytest.raises(ValueError):
        format_number(float("inf"), "en")
    with pytest.raises(LookupError):
        format_number(1, "xx")


def test_parses_the_locale_spelling() -> None:
    assert parse_number("1.234.567,5", "de") == Decimal("1234567.5")
    assert parse_number(f"-1{NNBSP}234", "fr") == -1234
    assert parse_number("\u22121\u00a0234", "sv") == -1234
    assert parse_number("12,34,567", "en-IN") == 1234567
    assert parse_number("1234", "es") == 1234
    assert parse_number("1.234", "es") == 1234


def test_parse_is_strict() -> None:
    bad = [
        ("1,234,567", "en-IN"),
        ("1 234", "fr"),
        ("1.234,5", "en"),
        ("-5", "sv"),
        ("1.23.456", "de"),
        ("12,34", "en"),
        ("1,234.", "en"),
        ("", "en"),
    ]
    for text, locale in bad:
        with pytest.raises(ValueError):
            parse_number(text, locale)


def test_parse_returns_int_or_decimal() -> None:
    assert type(parse_number("1,234", "en")) is int
    assert type(parse_number("1,234.0", "en")) is Decimal


@pytest.mark.parametrize("locale", ["en", "de", "fr", "es", "en-IN", "fa", "de-CH", "tok", "ee"])
@pytest.mark.parametrize("text", ["0", "-7", "1234", "-12345678", "1234567.890", "-0.5"])
def test_round_trips_through_every_grouping(locale: str, text: str) -> None:
    value = Decimal(text)
    for grouping in ("auto", "min2", "always", "off"):
        shown = format_number(value, locale, grouping=grouping)
        assert str(Decimal(parse_number(shown, locale))) == str(value)


def test_number_symbols_describe_the_locale() -> None:
    assert number_symbols("en-IN") == NumberSymbols("en-IN", ".", ",", "-", 3, 2, 1)
    assert number_symbols("es_ES.UTF-8") == NumberSymbols("es", ",", ".", "-", 3, 3, 2)
    assert number_symbols("tok").primary == 2
    with pytest.raises(AttributeError):
        number_symbols("en").group = " "  # type: ignore[misc]


def test_subclasses_cannot_change_the_digits() -> None:
    class Shown(int):
        def __repr__(self) -> str:
            return "shown"

        __str__ = __repr__

    class Drifting(float):
        def __repr__(self) -> str:
            return "0.30000000000000004"

    assert format_number(Shown(1234), "en") == "1,234"
    assert format_number(Drifting(0.3), "en") == "0.3"
