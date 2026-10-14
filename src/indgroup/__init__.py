"""Format and parse numbers with Indian lakh and crore grouping and every Unicode CLDR locale."""

from __future__ import annotations

from ._grouping import format_indian, parse_indian
from ._locale import cldr_version, resolve_locale, supported_locales
from ._number import Grouping, format_number, parse_number
from ._symbols import NumberSymbols, number_symbols
from ._value import Number

__version__ = "0.2.0"

__all__ = [
    "Grouping",
    "Number",
    "NumberSymbols",
    "cldr_version",
    "format_indian",
    "format_number",
    "number_symbols",
    "parse_indian",
    "parse_number",
    "resolve_locale",
    "supported_locales",
]
