"""Locale-aware formatting and strict parsing of numbers with CLDR grouping."""

from __future__ import annotations

from decimal import Decimal
from typing import Literal, cast, get_args

from ._digits import group_digits, read_number
from ._symbols import number_symbols
from ._value import Number, shown, split_value

# The useGrouping values of Intl.NumberFormat, documented in the package docstring.
Grouping = Literal["auto", "min2", "always", "off"]

_GROUPINGS: tuple[str, ...] = get_args(Grouping)


def format_number(value: Number, locale: str, *, grouping: Grouping = "auto") -> str:
    """Render ``value`` the way ``locale`` writes it, with Latin digits and no rounding.

    ``grouping`` follows the ``useGrouping`` option of ``Intl.NumberFormat``: ``auto`` uses
    the locale's minimum grouping digits (Spanish writes ``1234`` but ``12.345``), ``min2``
    requires at least two digits before the first separator, ``always`` groups every number
    longer than a group, ``off`` never groups.

    Raises ``TypeError`` for a value of another type (``bool`` included) or a non-``str``
    locale or grouping; ``ValueError`` for an unknown grouping, a malformed locale tag, NaN,
    an infinity, or more than 100,000 digits on either side of the point; ``LookupError``
    for a locale with no number data (see :func:`resolve_locale`).

    >>> format_number(1234567.89, "de")
    '1.234.567,89'
    >>> format_number(1234567, "en-IN")
    '12,34,567'
    >>> format_number(1234, "es"), format_number(1234, "es", grouping="always")
    ('1234', '1.234')
    >>> format_number(-1234567, "fr").split(chr(0x202F))  # narrow no-break spaces
    ['-1', '234', '567']
    """
    if not isinstance(grouping, str):
        raise TypeError(f"grouping must be a str, not {type(grouping).__name__}")
    grouping = cast(Grouping, str.__str__(grouping))  # a str subclass cannot fake a match
    if grouping not in _GROUPINGS:
        choices = ", ".join(_GROUPINGS)
        raise ValueError(f"grouping must be one of {choices}, not {shown(grouping)}")
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
    an ``int``, one with a fraction a ``Decimal`` keeping every digit. Spaces, tabs and line
    breaks around the text are ignored, a group symbol never. Anything else raises
    ``ValueError``, as do more than 100,000 digits on either side of the point; a
    non-``str`` raises ``TypeError`` and a locale without data ``LookupError``.

    >>> parse_number("1.234.567,89", "de")
    Decimal('1234567.89')
    >>> parse_number("12,34,567", "en-IN")
    1234567
    >>> parse_number("1,234,567", "en-IN")
    Traceback (most recent call last):
    ...
    ValueError: not a validly grouped integer: '1,234,567'
    """
    symbols = number_symbols(locale)
    sizes = (symbols.primary, symbols.secondary)
    return read_number(text, symbols.decimal, symbols.group, sizes, symbols.minus)
