"""The 1.0 promise of every public name: signatures, types returned, errors raised."""

from __future__ import annotations

import dataclasses
import inspect
import pickle
from decimal import Decimal
from typing import get_args

import pytest

import indgroup
from indgroup import (
    Grouping,
    Number,
    NumberSymbols,
    cldr_version,
    format_indian,
    format_number,
    number_symbols,
    parse_indian,
    parse_number,
    resolve_locale,
    supported_locales,
)

P = inspect.Parameter
SIGNATURES = {
    "format_indian": [
        ("value", P.POSITIONAL_OR_KEYWORD, P.empty),
        ("separator", P.KEYWORD_ONLY, ","),
    ],
    "parse_indian": [
        ("text", P.POSITIONAL_OR_KEYWORD, P.empty),
        ("separator", P.KEYWORD_ONLY, ","),
    ],
    "format_number": [
        ("value", P.POSITIONAL_OR_KEYWORD, P.empty),
        ("locale", P.POSITIONAL_OR_KEYWORD, P.empty),
        ("grouping", P.KEYWORD_ONLY, "auto"),
    ],
    "parse_number": [
        ("text", P.POSITIONAL_OR_KEYWORD, P.empty),
        ("locale", P.POSITIONAL_OR_KEYWORD, P.empty),
    ],
    "number_symbols": [("locale", P.POSITIONAL_OR_KEYWORD, P.empty)],
    "resolve_locale": [("locale", P.POSITIONAL_OR_KEYWORD, P.empty)],
    "supported_locales": [],
    "cldr_version": [],
}
RETURNS = {
    "format_indian": "str",
    "parse_indian": "int | Decimal",
    "format_number": "str",
    "parse_number": "int | Decimal",
    "number_symbols": "NumberSymbols",
    "resolve_locale": "str",
    "supported_locales": "tuple[str, ...]",
    "cldr_version": "str",
}


@pytest.mark.parametrize("name", sorted(SIGNATURES))
def test_function_signatures_are_pinned(name: str) -> None:
    signature = inspect.signature(getattr(indgroup, name))
    found = [(p.name, p.kind, p.default) for p in signature.parameters.values()]
    assert found == SIGNATURES[name]
    assert signature.return_annotation == RETURNS[name]
    assert getattr(indgroup, name).__module__.startswith("indgroup.")


def test_the_type_aliases_are_pinned() -> None:
    assert get_args(Grouping) == ("auto", "min2", "always", "off")
    assert get_args(Number) == (int, float, Decimal)


def test_number_symbols_is_a_frozen_value_in_the_package_namespace() -> None:
    fields = [(f.name, f.type) for f in dataclasses.fields(NumberSymbols)]
    assert fields == [
        ("locale", "str"),
        ("decimal", "str"),
        ("group", "str"),
        ("minus", "str"),
        ("primary", "int"),
        ("secondary", "int"),
        ("min_grouping", "int"),
    ]
    symbols = number_symbols("en-IN")
    assert NumberSymbols.__module__ == "indgroup"
    assert pickle.loads(pickle.dumps(symbols)) == symbols
    assert hash(symbols) == hash(NumberSymbols("en-IN", ".", ",", "-", 3, 2, 1))
    with pytest.raises(dataclasses.FrozenInstanceError):
        symbols.minus = "+"  # type: ignore[misc]


def test_return_types() -> None:
    assert type(format_indian(1)) is str and type(format_number(1, "en")) is str
    assert type(parse_indian("1")) is int and type(parse_indian("1.0")) is Decimal
    assert type(parse_number("1", "en")) is int and type(parse_number("1.0", "en")) is Decimal
    assert type(resolve_locale("en")) is str and type(cldr_version()) is str
    locales = supported_locales()
    assert type(locales) is tuple and all(type(name) is str for name in locales)


WRONG_TYPES = [
    lambda: format_indian("1"),  # type: ignore[arg-type]
    lambda: format_indian(True),
    lambda: format_indian(None),  # type: ignore[arg-type]
    lambda: format_indian(1, separator=44),  # type: ignore[arg-type]
    lambda: parse_indian(b"1"),  # type: ignore[arg-type]
    lambda: parse_indian("1", separator=None),  # type: ignore[arg-type]
    lambda: format_number("1", "en"),  # type: ignore[arg-type]
    lambda: format_number(False, "en"),
    lambda: format_number(1, b"en"),  # type: ignore[arg-type]
    lambda: format_number(1, "en", grouping=None),  # type: ignore[arg-type]
    lambda: parse_number(1, "en"),  # type: ignore[arg-type]
    lambda: parse_number("1", None),  # type: ignore[arg-type]
    lambda: number_symbols(1),  # type: ignore[arg-type]
    lambda: resolve_locale(["en"]),  # type: ignore[arg-type]
]
BAD_VALUES = [
    lambda: format_indian(float("nan")),
    lambda: format_indian(Decimal("-Infinity")),
    lambda: format_indian(1, separator=""),
    lambda: format_indian(1, separator="."),
    lambda: parse_indian("1,234,567"),
    lambda: parse_indian("1", separator="-"),
    lambda: format_number(1, "en", grouping="never"),  # type: ignore[arg-type]
    lambda: format_number(1, "en_"),
    lambda: parse_number("1.234,5", "en"),
    lambda: parse_number("+1", "en"),
    lambda: resolve_locale("zh-abc"),
    lambda: resolve_locale(""),
]
UNKNOWN_LOCALES = [
    lambda: resolve_locale("xx"),
    lambda: number_symbols("qaa"),
    lambda: format_number(1, "tlh"),
    lambda: parse_number("1", "zz-Latn"),
]


@pytest.mark.parametrize("call", WRONG_TYPES)
def test_wrong_types_raise_type_error(call: object) -> None:
    with pytest.raises(TypeError):
        call()  # type: ignore[operator]


@pytest.mark.parametrize("call", BAD_VALUES)
def test_bad_values_raise_value_error_and_nothing_else(call: object) -> None:
    with pytest.raises(ValueError) as raised:
        call()  # type: ignore[operator]
    assert type(raised.value) is ValueError


@pytest.mark.parametrize("call", UNKNOWN_LOCALES)
def test_unknown_locales_raise_lookup_error_and_not_value_error(call: object) -> None:
    with pytest.raises(LookupError) as raised:
        call()  # type: ignore[operator]
    assert type(raised.value) is LookupError
