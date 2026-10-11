from decimal import Decimal

import pytest

from indgroup import format_indian, parse_indian


def test_groups_a_seven_digit_integer() -> None:
    assert format_indian(1234567) == "12,34,567"


def test_groups_an_eight_digit_integer() -> None:
    assert format_indian(12596475) == "1,25,96,475"


def test_leaves_small_numbers_unchanged() -> None:
    assert format_indian(0) == "0"
    assert format_indian(7) == "7"
    assert format_indian(999) == "999"
    assert format_indian(1234) == "1,234"


def test_groups_only_the_integer_part_of_a_decimal() -> None:
    assert format_indian(Decimal("1234567.89")) == "12,34,567.89"


def test_keeps_trailing_zeros_of_a_decimal() -> None:
    assert format_indian(Decimal("1234.50")) == "1,234.50"


def test_formats_negative_numbers() -> None:
    assert format_indian(-1234567) == "-12,34,567"
    assert format_indian(Decimal("-1234.5")) == "-1,234.5"


def test_accepts_a_custom_separator() -> None:
    assert format_indian(1234567, separator=" ") == "12 34 567"


def test_rejects_a_bad_separator() -> None:
    with pytest.raises(ValueError):
        format_indian(1234567, separator="")
    with pytest.raises(ValueError):
        format_indian(1234567, separator=".")
    with pytest.raises(ValueError):
        format_indian(1234567, separator="5")


def test_rejects_bool_and_float() -> None:
    with pytest.raises(TypeError):
        format_indian(True)
    with pytest.raises(TypeError):
        format_indian(1.5)  # type: ignore[arg-type]


def test_rejects_non_finite_decimals() -> None:
    with pytest.raises(ValueError):
        format_indian(Decimal("NaN"))
    with pytest.raises(ValueError):
        format_indian(Decimal("Infinity"))


def test_parses_a_grouped_integer_to_int() -> None:
    result = parse_indian("12,34,567")
    assert result == 1234567
    assert isinstance(result, int)


def test_parses_a_grouped_decimal_to_decimal() -> None:
    result = parse_indian("12,34,567.89")
    assert result == Decimal("1234567.89")
    assert isinstance(result, Decimal)


def test_parses_ungrouped_digits() -> None:
    assert parse_indian("1234567") == 1234567


def test_parses_negative_values() -> None:
    assert parse_indian("-12,34,567") == -1234567
    assert parse_indian("-1,234.5") == Decimal("-1234.5")


def test_parses_with_a_custom_separator() -> None:
    assert parse_indian("12 34 567", separator=" ") == 1234567


def test_rejects_western_grouping() -> None:
    with pytest.raises(ValueError):
        parse_indian("1,234,567")


def test_rejects_malformed_input() -> None:
    for bad in ["", "abc", "12,,34", "12.34.56", "1,2,3", "12,345."]:
        with pytest.raises(ValueError):
            parse_indian(bad)


@pytest.mark.parametrize("value", [0, 5, 999, 1234, 1234567, 12596475, 100000000])
def test_round_trips_integers(value: int) -> None:
    assert parse_indian(format_indian(value)) == value


@pytest.mark.parametrize("text", ["0.00", "1234.50", "-9876543.21", "1234567.1"])
def test_round_trips_decimals(text: str) -> None:
    value = Decimal(text)
    assert parse_indian(format_indian(value)) == value
