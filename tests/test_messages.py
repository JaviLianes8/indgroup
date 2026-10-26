"""The exact text of error messages: where the quoting of the input is cut, and what NaN and
the infinities are called."""

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
def test_an_input_of_forty_characters_is_quoted_whole(
    call: Callable[[str], object], prefix: str
) -> None:
    text = "x" * 40
    with pytest.raises(ValueError) as raised:
        call(text)
    assert str(raised.value) == f"{prefix}{text!r}"


@pytest.mark.parametrize(("call", "prefix"), CALLS)
def test_an_input_of_forty_one_characters_is_cut_and_counted(
    call: Callable[[str], object], prefix: str
) -> None:
    with pytest.raises(ValueError) as raised:
        call("x" * 41)
    assert str(raised.value) == f"{prefix}{'x' * 40!r}... (41 characters)"


def test_the_cut_counts_characters_not_bytes() -> None:
    with pytest.raises(ValueError) as raised:
        parse_indian(chr(0x20AC) * 41)
    assert str(raised.value).endswith("... (41 characters)")


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


def test_number_symbols_quotes_the_tag_the_same_way() -> None:
    with pytest.raises(ValueError) as raised:
        number_symbols("a" * 40)
    assert str(raised.value) == f"not a locale tag: {'a' * 40!r}"
