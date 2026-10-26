# indgroup

[![Lianes8 Certified](https://lianes8studio.com/certified/lianes8-certified-badge.svg)](https://lianes8studio.com/certified)

Format and strictly parse numbers with Indian lakh and crore grouping (`12,34,567`) and the
digit grouping of the 766 Unicode CLDR locales with number data: `1.234.567,89` in German,
`1'234'567.89` in Swiss German, a narrow no-break space in French, `1234` but `12.345` in
Spanish. Exact for `int`, `float` and `Decimal`, typed, zero dependencies.

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
with more than 100,000 digits before or after the point are refused with `ValueError`, so
no input can make a call build text without end; the longest values take about a tenth of
a second, since long integers are converted in better than quadratic time.

Parsing is strict. It takes the locale's own minus, decimal and group symbols, ASCII digits
only, and groups exactly where the locale writes them, or none at all; a grouped number never
starts with a zero group, so `0,001` is refused rather than read as `1`. A value without a
fraction comes back as `int`, one with a fraction as a `Decimal` with every digit kept, so
text written by `format_number` reads back to a value that formats to the same text; the one
exception is `-0`, which reads back as the `int` `0`. The parser also takes spellings the
formatter does not write, which format back to the locale's own spelling: digits without
groups, groups the minimum grouping digits leave out (Spanish `1.234`), leading zeros in
ungrouped digits (`007`) and surrounding spaces, tabs and line breaks. A group symbol is never
taken for a space, even when it is a no-break space.

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

Values come from the arguments or from stdin, one per line. A value to format is ASCII
digits with an optional sign, decimal point and exponent (`1234.5`, `-.5`, `5.`, `1e6`),
with at most 100,000 digits on each side of the point once the exponent is applied.
`-l/--locale` picks the locale (default `en-IN`), `-g/--grouping` the strategy,
`-p/--parse` reads grouped values back, `--locales` lists the locales. An argument that starts with a minus followed by a digit or a
point, such as `-1e5` or `-1.234,5`, is a value on every Python version; put `--` before any
other value that starts with a minus. Errors print one line on stderr and exit with status 2.
On a pipe, stdin, stdout and stderr are UTF-8 on every system.

## API

| Name | What it does |
| --- | --- |
| `format_indian(value, *, separator=",")` | Indian lakh and crore grouping; the separator is one character other than a digit, a sign or `.` |
| `parse_indian(text, *, separator=",")` | strict inverse of `format_indian`, `int` or `Decimal` |
| `format_number(value, locale, *, grouping="auto")` | the locale's symbols and grouping, no rounding |
| `parse_number(text, locale)` | strict inverse of `format_number` |
| `number_symbols(locale)` | the `NumberSymbols` a locale uses |
| `NumberSymbols` | frozen value: `locale`, `decimal`, `group`, `minus`, `primary`, `secondary`, `min_grouping` |
| `resolve_locale(locale)` | the CLDR locale a tag reads, or `LookupError` |
| `supported_locales()` | the 766 CLDR locales, sorted |
| `cldr_version()` | the CLDR release of the table, `48.2.0` |
| `Number` | `int \| float \| Decimal` |
| `Grouping` | `Literal["auto", "min2", "always", "off"]` |

Wrong types raise `TypeError`; NaN, infinities, unknown grouping values, malformed text and
values past the digit bound raise `ValueError`; an unknown language raises `LookupError`
instead of silently reading English. Error messages quote at most 40 characters of the
input; a longer input is cut and its length given. The [GUIDE](https://github.com/JaviLianes8/indgroup/blob/main/GUIDE.md) covers every
rule in detail and the
[CHANGELOG](https://github.com/JaviLianes8/indgroup/blob/main/CHANGELOG.md) what changed in
each release.

## How it compares with `Intl.NumberFormat`

The 637 CLDR locales that ICU ships under their own name, 13 alias and fallback tags such as
`iw` and `de-AT-1996`, the four grouping strategies and a set of integers and decimals are
checked against `Intl.NumberFormat` of Node 24.18 (ICU 78.3, CLDR 48) with Latin digits.
They agree everywhere, Swiss French included: CLDR 48.2.0 gave `fr-CH` an apostrophe as its
group symbol, and ICU 78.3 carries it. This library follows CLDR in three places where Intl
does not:

- A tag in a script other than its language's likely one, such as `ru-Latn` or `hi-Arab`,
  reads the root locale, as CLDR's `nonlikelyScript` parent rule says; Intl reads `ru` and
  `hi`. The same holds for a tag whose region's likely script has no data: `ku-GE` is
  `ku-Cyrl-GE` in CLDR's likely subtags and reads the root, where Intl reads `ku`.
- The legacy tags CLDR replaces read their replacement, such as `zh-yue` (`yue`), `no-bok`
  (`nb`) and `i-lux` (`lb`); Intl refuses them with `RangeError`.
- A tag that spells out its language's likely script, such as `de-Latn-AT` or `en-Latn-IN`,
  reads `de-AT` and `en-IN`, as UTS #35 says the lookup starts without that script; Intl
  drops the region and reads `de` and `en`, so `de-Latn-AT` writes `-1.234.567,5` there.

One difference goes the other way, where Intl follows CLDR and this library does not. The
table holds the 766 locales of the CLDR JSON packages. CLDR's XML has one more with number
data, `en_US_POSIX` (no grouping), which the JSON leaves out, so `en-US-POSIX` reads `en`
here while Intl writes `-1234567.5`.

Other differences are by design:

- Digits are always Latin (`0` to `9`); the native digits some locales default to, such as
  Arabic-Indic, are out of scope.
- Values are never rounded; `Intl.NumberFormat` shows three fraction digits by default.
- Only the decimal pattern is used: no percent, currency, compact or scientific notation.

## Why

`format(n, ",")` knows only groups of three. Python's `locale` module formats with the
locale data of the operating system and switches it with `setlocale`, a setting shared by
the whole process. Babel is the complete CLDR toolkit (dates, currencies, plural rules)
and has a strict parser too, but it is a 10 MB wheel, and its `format_decimal` rounds to
the pattern's three fraction digits unless `decimal_quantization=False` is passed; Babel
2.18.0 (CLDR 47) also groups Spanish `1234` as `1.234`, where CLDR's minimum grouping
digits say `1234`. When only the digits matter, `indgroup` is a small, typed,
zero-dependency formatter and strict parser that never rounds and is checked against
`Intl.NumberFormat`.

## Development

```
pip install -r requirements-dev.txt
python scripts/fetch_upstream.py   # optional: the CLDR, ICU and Intl reference files
pwsh scripts/check.ps1
```

The table in `src/indgroup/_cldr.json` is derived by `scripts/build_table.py` from the CLDR
JSON packages. The reference files are not part of the repository; their tests skip while
they are absent, and the live `Intl.NumberFormat` comparison needs Node 24.18 (ICU 78.3).
`INDGROUP_E2E=1` adds a test that builds, installs and drives the wheel.

## License

MIT, see [LICENSE](https://github.com/JaviLianes8/indgroup/blob/main/LICENSE). The number
data is derived from the Unicode CLDR and ships under the Unicode License v3, see
[LICENSE-UNICODE](https://github.com/JaviLianes8/indgroup/blob/main/LICENSE-UNICODE).

## Links

- Website: https://lianes8studio.com
- GitHub: https://github.com/JaviLianes8
- LinkedIn: https://www.linkedin.com/in/jlianes/
