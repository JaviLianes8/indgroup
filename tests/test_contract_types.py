"""Handwritten contracts for hostile attributes and rejected type metadata."""

from __future__ import annotations

from collections.abc import Callable
from decimal import Decimal
from typing import cast

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


def _raise(*args: object) -> object:
    raise RuntimeError("instance hook executed")


@pytest.mark.parametrize("base", [int, float, Decimal])
@pytest.mark.parametrize("hook", ["__getattribute__", "__class__"])
def test_numeric_subclasses_are_read_without_attribute_hooks(base: type[Number], hook: str) -> None:
    attributes = {hook: property(_raise) if hook == "__class__" else _raise}
    value = cast(Number, type("Amount", (base,), attributes)(1234))
    assert format_indian(value) == "1,234"
    assert format_number(value, "en") == "1,234"


@pytest.mark.parametrize("hook", ["__getattribute__", "__class__"])
def test_string_subclasses_are_read_without_attribute_hooks(hook: str) -> None:
    attributes = {hook: property(_raise) if hook == "__class__" else _raise}
    text = type("Text", (str,), attributes)
    assert parse_indian(text("1,234")) == 1234
    assert parse_number(text("1,234"), text("en")) == 1234
    assert resolve_locale(text("en")) == "en"
    assert number_symbols(text("en")).locale == "en"
    assert format_indian(1234, separator=text(" ")) == "1 234"
    assert format_number(1234, text("en"), grouping=text("off")) == "1234"


CALLS: list[Callable[[object], object]] = [
    lambda value: format_indian(cast(Number, value)),
    lambda value: format_number(cast(Number, value), "en"),
    lambda value: parse_indian(cast(str, value)),
    lambda value: parse_number(cast(str, value), "en"),
    lambda value: resolve_locale(cast(str, value)),
    lambda value: number_symbols(cast(str, value)),
    lambda value: format_number(1, cast(str, value)),
    lambda value: parse_number("1", cast(str, value)),
    lambda value: format_number(1, "en", grouping=cast(Grouping, value)),
    lambda value: format_indian(1, separator=cast(str, value)),
    lambda value: parse_indian("1", separator=cast(str, value)),
]


@pytest.mark.parametrize("call", CALLS)
@pytest.mark.parametrize("hook", ["__getattribute__", "__class__"])
def test_wrong_types_are_rejected_without_attribute_hooks(
    call: Callable[[object], object], hook: str
) -> None:
    attributes = {hook: property(_raise) if hook == "__class__" else _raise}
    with pytest.raises(TypeError):
        call(type("Wrong", (), attributes)())


@pytest.mark.parametrize("call", CALLS)
@pytest.mark.parametrize(
    "name", ["T" * 100_000, "Bad\nforged log entry\x1b[31m"], ids=["huge", "log"]
)
def test_type_names_cannot_expand_or_inject_error_messages(
    call: Callable[[object], object], name: str
) -> None:
    with pytest.raises(TypeError) as raised:
        call(type(name, (), {})())
    message = str(raised.value)
    assert len(message) < 120
    assert "\n" not in message and "\x1b" not in message


@pytest.mark.parametrize("call", CALLS)
def test_type_metadata_is_not_read_through_a_metaclass(call: Callable[[object], object]) -> None:
    class Meta(type):
        def __getattribute__(cls, name: str) -> object:
            raise RuntimeError("metaclass hook executed")

    with pytest.raises(TypeError):
        call(Meta("Wrong", (), {})())
