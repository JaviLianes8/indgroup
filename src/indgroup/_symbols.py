"""The number symbols and grouping sizes of a CLDR locale."""

from __future__ import annotations

from dataclasses import dataclass

from ._locale import resolve_locale, table


@dataclass(frozen=True)
class NumberSymbols:
    """How a locale writes a number with Latin digits, as recorded in Unicode CLDR.

    ``primary`` is the size of the rightmost group and ``secondary`` the size of the groups
    to its left (3 and 3 for ``1,234,567``, 3 and 2 for the Indian ``12,34,567``); zero
    means the locale does not group. ``min_grouping`` is CLDR's minimumGroupingDigits: the
    number of digits that must stand left of the first separator before any is written.
    """

    locale: str
    decimal: str
    group: str
    minus: str
    primary: int
    secondary: int
    min_grouping: int


def number_symbols(locale: str) -> NumberSymbols:
    """The symbols and grouping sizes ``locale`` uses, after :func:`resolve_locale`."""
    resolved = resolve_locale(locale)
    data = table()
    profile = data["profiles"][data["locales"][resolved]]
    decimal, group, minus, primary, secondary, minimum = profile
    return NumberSymbols(resolved, decimal, group, minus, primary, secondary, minimum)
