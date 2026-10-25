"""Format and parse numbers with Indian lakh and crore grouping and every Unicode CLDR locale.

- ``format_indian`` and ``parse_indian`` write and read the Indian grouping (``12,34,567``)
  with any one-character separator.
- ``format_number`` and ``parse_number`` write and read a number the way a CLDR locale
  does; ``number_symbols``, ``resolve_locale``, ``supported_locales`` and ``cldr_version``
  describe the locale data.
- ``Number`` is the type of the values accepted, ``int | float | Decimal``, and
  ``Grouping`` the ``Literal`` type of the ``grouping`` argument of ``format_number``.

>>> from decimal import Decimal
>>> from typing import get_args
>>> from indgroup import Grouping, Number, format_number
>>> def amounts(values: list[Number], grouping: Grouping = "auto") -> list[str]:
...     return [format_number(value, "en-IN", grouping=grouping) for value in values]
>>> amounts([1234567, 0.5, Decimal("-1234.50")])
['12,34,567', '0.5', '-1,234.50']
>>> get_args(Grouping)
('auto', 'min2', 'always', 'off')
>>> isinstance(Decimal("1"), get_args(Number))
True
"""

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
