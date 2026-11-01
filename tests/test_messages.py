"""Input length metadata and the fixed descriptions of nonfinite values."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal

import pytest

from indgroup import (
    format_indian,
    format_number,
    number_symbols,
    parse_indian,
    parse_number,
    resolve_locale,
)

CALLS: list[tuple[Callable[[str], object], str]] = [
    (parse_indian, "not a validly grouped integer: "),
    (lambda text: parse_number(text, "de"), "not a validly grouped integer: "),
    (resolve_locale, "not a locale tag: "),
]


@pytest.mark.parametrize(("call", "prefix"), CALLS)
@pytest.mark.parametrize("length", [9, 40, 41, 100_000])
def test_errors_report_the_length_without_quoting_any_input(
    call: Callable[[str], object], prefix: str, length: int
) -> None:
    text = "x" * length
    with pytest.raises(ValueError) as raised:
        call(text)
    assert str(raised.value) == f"{prefix}({length} characters)"


def test_the_length_counts_characters_not_bytes() -> None:
    with pytest.raises(ValueError) as raised:
        parse_indian(chr(0x20AC) * 41)
    assert str(raised.value) == "not a validly grouped integer: (41 characters)"


def _message(call: Callable[..., object], *args: object) -> str:
    with pytest.raises(ValueError) as raised:
        call(*args)
    return str(raised.value)


@pytest.mark.parametrize("value", [float("nan"), -float("nan"), Decimal("NaN"), Decimal("sNaN")])
def test_nan_is_named_in_the_message(value: float | Decimal) -> None:
    for message in (_message(format_indian, value), _message(format_number, value, "en")):
        assert message == "value must be a finite number, not NaN"


@pytest.mark.parametrize(
    "value", [float("inf"), -float("inf"), Decimal("Infinity"), Decimal("-Infinity")]
)
def test_an_infinity_is_named_in_the_message(value: float | Decimal) -> None:
    for message in (_message(format_indian, value), _message(format_number, value, "en")):
        assert message == "value must be a finite number, not an infinity"


def test_number_symbols_reports_only_the_tag_length() -> None:
    with pytest.raises(ValueError) as raised:
        number_symbols("a" * 40)
    assert str(raised.value) == "not a locale tag: (40 characters)"
