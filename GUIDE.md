# indgroup guide

The behaviour of every public name in detail. Each Python block below runs as a test: a
comment line after a `print` holds what it prints.

## Indian grouping

`format_indian(value, *, separator=",")` groups the last three digits of the integer part,
then the rest in pairs: `1,000` is a thousand, `1,00,000` a lakh, `1,00,00,000` a crore.
The fraction is never grouped. The separator is any one character except a digit (in any
script), `+`, `-` and `.`. `parse_indian(text, *, separator=",")` is its strict inverse and
also accepts a leading `+`.

```python
from decimal import Decimal
from indgroup import format_indian, parse_indian

for value in [999, 1000, 100000, 10**7, Decimal("-12345678.900")]:
    print(format_indian(value))
print(format_indian(10**9, separator="_"))
print(repr(parse_indian("+1,00,000")), repr(parse_indian("10000000")))
# 999
# 1,000
# 1,00,000
# 1,00,00,000
# -1,23,45,678.900
# 1_00_00_00_000
# 100000 10000000
```

## Any CLDR locale

`format_number(value, locale, *, grouping="auto")` reads the decimal, group and minus
symbols, the grouping sizes of the standard decimal pattern and the minimum grouping digits
that Unicode CLDR 48 records for the locale's Latin digits. `number_symbols(locale)` returns
them as a frozen `NumberSymbols`.

`grouping` takes the `useGrouping` values of `Intl.NumberFormat`:

| Value | Groups when |
| --- | --- |
| `"auto"` | at least `min_grouping` digits stand left of the first separator (the default) |
| `"min2"` | at least two, or `min_grouping` if larger |
| `"always"` | the integer part is longer than the first group; a locale whose pattern has no grouping groups by thousands, as ICU does |
| `"off"` | never |

```python
from indgroup import format_number, number_symbols

for grouping in ["auto", "min2", "always", "off"]:
    print(
        grouping,
        format_number(1234, "es", grouping=grouping),
        format_number(12345, "es", grouping=grouping),
    )
print(number_symbols("es"))
# auto 1234 12.345
# min2 1234 12.345
# always 1.234 12.345
# off 1234 12345
# NumberSymbols(locale='es', decimal=',', group='.', minus='-', primary=3, secondary=3, min_grouping=2)
```

Digits are always ASCII `0` to `9`. Some locales use other characters for the symbols: a
narrow no-break space (U+202F) or a no-break space (U+00A0) as the group, U+2212 as the minus
sign, and for Persian a left-to-right mark before it.

## Locale tags

`resolve_locale(locale)` names the CLDR locale whose data a tag reads; `format_number`,
`parse_number` and `number_symbols` all go through it.

- BCP 47 (`pt-BR`) and POSIX (`pt_BR.UTF-8`, `sr_RS@latin`) spellings, in any case.
- Deprecated codes are replaced (`iw` is `he`, `sh` is `sr-Latn`, `UK` is `GB`).
- A language written in several scripts gets its likely script (`zh-TW` reads
  `zh-Hant`, `sr-ME` reads `sr-Latn-ME`).
- A locale without data of its own falls back through the CLDR parent locales, then by
  dropping subtags (`pt-FR` reads `pt-PT`, `de-AT-1996` reads `de-AT`). Unicode extensions
  such as `-u-nu-arab` and private use do not change anything.
- `und` and `root` are the root locale. An unknown language raises `LookupError` rather than
  reading another language's data; text that is not a tag raises `ValueError`.

`supported_locales()` lists the 766 CLDR locales with number data and `cldr_version()` the
CLDR release, `48.0.0`.

```python
from indgroup import resolve_locale

for tag in ["en_IN.UTF-8", "zh-SG", "sr_RS@latin", "de-CH-u-nu-arab", "root"]:
    print(tag, resolve_locale(tag))
for tag in ["xx", "en--US"]:
    try:
        resolve_locale(tag)
    except (LookupError, ValueError) as error:
        print(type(error).__name__)
# en_IN.UTF-8 en-IN
# zh-SG zh-Hans-SG
# sr_RS@latin sr-Latn
# de-CH-u-nu-arab de-CH
# root und
# LookupError
# ValueError
```

## Exact values

Values are `int`, `float` or `Decimal` (`bool` is refused). Nothing is rounded.

- A `Decimal` is written with all its digits and its exponent applied: `Decimal("1.50")`
  keeps its zero, `Decimal("1E+3")` is `1000`, `Decimal("-0")` is `-0`.
- A `float` is read through its shortest round-trip spelling, so `0.1` is `0.1`, and a
  whole float has no fraction, as in Intl: `5.0` is `5`.
- An `int` of any size up to the bound below, past Python's 4,300-digit limit for `str`.
- Subclasses of `int`, `float`, `Decimal` and `str` are read by their value: their methods
  are never called.
- More than 100,000 digits before or after the point raise `ValueError`, in formatting and
  in parsing: converting between `int` and `Decimal` takes quadratic time, and this bound
  keeps every call well under a second.

## Strict parsing

`parse_number(text, locale)` and `parse_indian(text)` accept exactly:

1. optional spaces, tabs, carriage returns and line feeds (never a group symbol, even a
   no-break space);
2. an optional minus, the locale's own (`parse_indian` also takes `+`);
3. ASCII digits, either ungrouped or grouped exactly where the formatter puts separators,
   whatever the minimum grouping digits (so `1.234` and `1234` both read in Spanish);
4. optionally the decimal symbol followed by at least one digit;
5. optional trailing spaces as in step 1.

A value with no decimal symbol returns an `int`; one with it a `Decimal` keeping every
digit written, so formatting it again gives the same text. `-0` is the one exception: it
reads back as the `int` `0`, while `-0.0` stays `Decimal("-0.0")`.

```python
from indgroup import parse_number

for text, locale in [
    ("1.234", "es"),
    ("1234", "es"),
    ("-1" + chr(0x202F) + "234,50", "fr"),
    ("-0", "en"),
]:
    print(repr(parse_number(text, locale)))
for text, locale in [("1,234,567", "en-IN"), ("1 234", "fr"), ("1,234.", "en"), ("-5", "sv")]:
    try:
        parse_number(text, locale)
    except ValueError as error:
        print(error)
# 1234
# 1234
# Decimal('-1234.50')
# 0
# not a validly grouped integer: '1,234,567'
# not a validly grouped integer: '1 234'
# not a valid fractional part: ''
# not a validly grouped integer: '-5'
```

## Types

The package ships `py.typed` and passes `mypy --strict`. `Number` is `int | float | Decimal`,
the values the formatters accept, and `Grouping` is
`Literal["auto", "min2", "always", "off"]`, so a type checker rejects any other grouping.
Both are for annotating your own code; at run time they are the plain `typing` objects.

## Errors

| Exception | Raised for |
| --- | --- |
| `TypeError` | a value that is not an `int`, `float` or `Decimal`, a `bool`, or a text, locale, separator or grouping that is not a `str` |
| `ValueError` | NaN, infinities, more than 100,000 digits on a side, a bad separator, an unknown grouping, malformed text, a malformed locale tag |
| `LookupError` | a locale tag whose language has no CLDR number data |

Messages quote at most 40 characters of the input, followed by its length.

## Command line

`indgroup VALUE...` (or `python -m indgroup`) formats plain numbers such as `1234.5` or
`1e6`; `-p/--parse` reads grouped values back and prints them plain. Without values it reads
stdin, one value per non-blank line, as UTF-8 (a byte order mark is skipped). `-l/--locale`
picks the locale (default `en-IN`), `-g/--grouping` the strategy, `--locales` lists the
locales and `--version` shows the package and CLDR versions. Errors print one line on stderr
and exit with status 2.

## Data and its sources

The table in the package is derived from the CLDR 48.0.0 JSON packages by
`scripts/build_table.py`, and the tests check that a fresh derivation gives the shipped file
byte for byte. The grouping rule follows ICU's `number_grouping.cpp` (release 78.3). Output
is compared with `Intl.NumberFormat` of Node 24.18 (ICU 78.3, CLDR 48): the recorded
reference covers the 650 locales ICU ships in four groupings, and a live run compares random
values. They agree everywhere except `fr-CH`, where ICU's data writes an apostrophe and CLDR
48 inherits the narrow no-break space of `fr`; this library follows CLDR.
