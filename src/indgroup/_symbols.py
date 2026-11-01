"""The number symbols and grouping sizes of a CLDR locale."""

from __future__ import annotations

from dataclasses import dataclass

from ._locale import resolve_locale
from ._table import table


@dataclass(frozen=True)
class NumberSymbols:
    """How a locale writes a number with Latin digits, as recorded in Unicode CLDR.

    ``primary`` is the size of the rightmost group and ``secondary`` the size of the groups
    to its left (3 and 3 for ``1,234,567``, 3 and 2 for the Indian ``12,34,567``); zero
    means the locale does not group. ``min_grouping`` is CLDR's minimumGroupingDigits: the
    number of digits that must stand left of the first separator before any is written.
    ``locale`` is the CLDR locale the data was read from. The value is frozen, compares by
    its fields and pickles as ``indgroup.NumberSymbols``.

    >>> symbols = number_symbols("hi")
    >>> symbols.group, symbols.primary, symbols.secondary
    (',', 3, 2)
    >>> symbols == NumberSymbols("hi", ".", ",", "-", 3, 2, 1)
    True
    """

    locale: str
    decimal: str
    group: str
    minus: str
    primary: int
    secondary: int
    min_grouping: int


NumberSymbols.__module__ = "indgroup"  # its public home, for pickles and reprs of the class


def number_symbols(locale: str) -> NumberSymbols:
    """The symbols and grouping sizes ``locale`` uses, after :func:`resolve_locale`.

    Raises what :func:`resolve_locale` raises: ``TypeError``, ``ValueError`` for a malformed
    tag and ``LookupError`` for a locale without number data.

    >>> swiss = number_symbols("de-CH")
    >>> swiss.locale, swiss.decimal, swiss.group, swiss.minus
    ('de-CH', '.', "'", '-')
    >>> number_symbols("es_ES.UTF-8").min_grouping
    2
    """
    resolved = resolve_locale(locale)
    data = table()
    profile = data["profiles"][data["locales"][resolved]]
    decimal, group, minus, primary, secondary, minimum = profile
    return NumberSymbols(resolved, decimal, group, minus, primary, secondary, minimum)
