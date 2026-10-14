"""Locale-aware formatting and strict parsing of numbers with CLDR grouping."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal, get_args

from ._digits import group_digits, read_number
from ._symbols import number_symbols
from ._value import Number, split_value

Grouping = Literal["auto", "min2", "always", "off"]

_GROUPINGS: tuple[str, ...] = get_args(Grouping)


def format_number(value: Number, locale: str, *, grouping: Grouping = "auto") -> str:
    """Render ``value`` the way ``locale`` writes it, with Latin digits and no rounding.

    ``grouping`` follows the ``useGrouping`` option of ``Intl.NumberFormat``: ``auto`` uses
    the locale's minimum grouping digits (Spanish writes ``1234`` but ``12.345``), ``min2``
    requires at least two digits before the first separator, ``always`` groups every number
    longer than a group, ``off`` never groups.
    """
    if not isinstance(grouping, str) or grouping not in _GROUPINGS:
        raise ValueError(f"grouping must be one of {', '.join(_GROUPINGS)}, not {grouping!r}")
    symbols = number_symbols(locale)
    negative, integer, fraction = split_value(value)
    primary, secondary, minimum = symbols.primary, symbols.secondary, symbols.min_grouping
    if grouping == "off":
        primary = 0
    elif grouping == "always":
        minimum = 1
        if primary == 0:  # ICU groups by thousands when the pattern has no grouping
            primary = secondary = 3
    elif grouping == "min2":
        minimum = max(2, minimum)
    text = group_digits(integer, symbols.group, primary, secondary, minimum)
    if fraction:
        text = f"{text}{symbols.decimal}{fraction}"
    return f"{symbols.minus}{text}" if negative else text


def parse_number(text: str, locale: str) -> int | Decimal:
    """Read back a number written the way ``locale`` writes it.

    Strict: the locale's own minus sign, decimal and group symbols, ASCII digits, and groups
    exactly where the locale puts them, or no groups at all. A value without a fraction is
    an ``int``, one with a fraction a ``Decimal`` keeping every digit. Anything else raises
    ``ValueError``.
    """
    symbols = number_symbols(locale)
    sizes = (symbols.primary, symbols.secondary)
    return read_number(text, symbols.decimal, symbols.group, sizes, symbols.minus)
