# indgroup

Format and strictly parse numbers with Indian lakh and crore grouping (`12,34,567`) and the
digit grouping of every Unicode CLDR locale: `1.234.567,89` in German, `1'234'567.89` in
Swiss German, a narrow no-break space in French, `1234` but `12.345` in Spanish. Exact for
`int`, `float` and `Decimal`, typed, zero dependencies.

## Install

```
pip install indgroup
```

## Usage

The Indian system groups the last three digits, then the rest in pairs, so a million reads
as `10,00,000` and a crore as `1,00,00,000`.

```python
from decimal import Decimal
from indgroup import format_indian, parse_indian

print(format_indian(1234567))
print(format_indian(-12596475))
print(format_indian(Decimal("1234567.50")))
print(format_indian(0.1))
print(format_indian(1234567, separator=" "))
print(repr(parse_indian("12,34,567")))
print(repr(parse_indian("-1,234.50")))
# 12,34,567
# -1,25,96,475
# 12,34,567.50
# 0.1
# 12 34 567
# 1234567
# Decimal('-1234.50')
```

Any locale, with the symbols and grouping CLDR records for it. `grouping` takes the
`useGrouping` vocabulary of `Intl.NumberFormat`: `auto` honours the locale's minimum
grouping digits, `min2` asks for at least two digits before the first separator, `always`
groups every number longer than a group, `off` never groups.

```python
from indgroup import format_number

print(format_number(1234567.89, "de"))
print(format_number(1234567.89, "de-CH"))
print(ascii(format_number(1234567.89, "fr")))
print(format_number(1234567, "hi"))
print(format_number(1234, "es"), format_number(12345, "es"))
print(format_number(1234, "es", grouping="always"))
print(format_number(1234, "en", grouping="min2"))
print(ascii(format_number(-5, "sv")))
# 1.234.567,89
# 1'234'567.89
# '1\u202f234\u202f567,89'
# 12,34,567
# 1234 12.345
# 1.234
# 1234
# '\u22125'
```

Nothing is rounded: a `Decimal` keeps every digit it has, trailing zeros included, and a
`float` is read through its shortest round-trip spelling, so `0.1` prints `0.1` and not the
binary value it stands for, and a whole float such as `5.0` prints `5`, as in Intl. Values
with more than a million integer digits are refused with `ValueError`.

Parsing is strict. It takes the locale's own minus, decimal and group symbols, ASCII digits
only, and groups exactly where the locale writes them, or none at all. A value without a
fraction comes back as `int`, one with a fraction as a `Decimal` with every digit kept, so
formatting the result gives the same text again; the one exception is `-0`, which reads back
as the `int` `0`. Surrounding spaces, tabs and line breaks are ignored, but a group symbol is
never taken for one, even when it is a no-break space.

```python
from indgroup import number_symbols, parse_number, resolve_locale

print(repr(parse_number("1.234.567,5", "de")))
print(repr(parse_number("12,34,567", "en-IN")))
for text in ["1,234,567", "1 234"]:
    try:
        parse_number(text, "en-IN")
    except ValueError:
        print("rejected", text)
print(number_symbols("en-IN"))
print(resolve_locale("pt_BR.UTF-8"), resolve_locale("zh-TW"), resolve_locale("iw"))
# Decimal('1234567.5')
# 1234567
# rejected 1,234,567
# rejected 1 234
# NumberSymbols(locale='en-IN', decimal='.', group=',', minus='-', primary=3, secondary=2, min_grouping=1)
# pt zh-Hant he
```

## Command line

```
$ indgroup 1234567 -1234.5
12,34,567
-1,234.5
$ indgroup -l de 1234567.89
1.234.567,89
$ indgroup --parse 12,34,567.50
1234567.50
```

Values come from the arguments or from stdin, one per line. `-l/--locale` picks the locale
(default `en-IN`), `-g/--grouping` the strategy, `-p/--parse` reads grouped values back,
`--locales` lists the locales. Put `--` before a negative value other than plain digits,
such as `-1e5` or `-1.234,5`.
Errors exit with status 2.

## API

| Name | What it does |
| --- | --- |
| `format_indian(value, *, separator=",")` | Indian lakh and crore grouping, any single separator |
| `parse_indian(text, *, separator=",")` | strict inverse of `format_indian`, `int` or `Decimal` |
| `format_number(value, locale, *, grouping="auto")` | the locale's symbols and grouping, no rounding |
| `parse_number(text, locale)` | strict inverse of `format_number` |
| `number_symbols(locale)` | the `NumberSymbols` a locale uses |
| `NumberSymbols` | frozen value: `locale`, `decimal`, `group`, `minus`, `primary`, `secondary`, `min_grouping` |
| `resolve_locale(locale)` | the CLDR locale a tag reads, or `LookupError` |
| `supported_locales()` | the 766 CLDR locales, sorted |
| `cldr_version()` | the CLDR release of the table, `48.0.0` |
| `Number` | `int \| float \| Decimal` |
| `Grouping` | `Literal["auto", "min2", "always", "off"]` |

Wrong types raise `TypeError`; NaN, infinities, unknown grouping values and malformed text
raise `ValueError`; an unknown language raises `LookupError` instead of silently reading
English.

## How it compares with `Intl.NumberFormat`

The 650 locales ICU ships, the four grouping strategies and a set of integers and decimals
are checked against `Intl.NumberFormat` of Node 24.18 (ICU 78.3, CLDR 48) with Latin digits.
They agree everywhere except Swiss French, where the ICU data writes an apostrophe while
CLDR 48 gives
`fr-CH` no group symbol of its own, so it inherits the narrow no-break space of `fr`. This
library follows CLDR. Other differences are by design:

- Digits are always Latin (`0` to `9`); the native digits some locales default to, such as
  Arabic-Indic, are out of scope.
- Values are never rounded; `Intl.NumberFormat` shows three fraction digits by default.
- Only the decimal pattern is used: no percent, currency, compact or scientific notation.

## Why

Python's `locale` module depends on what the operating system has installed, the `en_IN`
locale is absent on most systems, and `format(n, ",")` knows only groups of three. Babel
covers CLDR but is a large dependency that rounds to the pattern's fraction digits, and
the small packages that mention lakh and crore convert numbers to words or are tied to template
filters. This is a plain formatter and a strict parser with exact `Decimal` support.

## Development

```
pip install -r requirements-dev.txt
python scripts/fetch_upstream.py   # optional: the CLDR, ICU and Intl reference files
pwsh scripts/check.ps1
```

The table in `src/indgroup/_cldr.json` is derived by `scripts/build_table.py` from the CLDR
JSON packages. The reference files are not part of the repository; their tests skip while
they are absent. `INDGROUP_E2E=1` adds a test that builds, installs and drives the wheel.

## License

MIT, see [LICENSE](LICENSE). The number data is derived from the Unicode CLDR and ships
under the Unicode License v3, see [LICENSE-UNICODE](LICENSE-UNICODE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
