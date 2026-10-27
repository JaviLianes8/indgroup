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
that Unicode CLDR 48.2 records for the locale's Latin digits. `number_symbols(locale)` returns
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

- BCP 47 (`pt-BR`) and POSIX (`pt_BR.UTF-8`, `sr_RS@latin`) spellings, in any case. A
  script in the tag wins over a POSIX modifier: `uz-Arab@latin` reads `uz-Arab`.
- Deprecated codes are replaced (`iw` is `he`, `sh` is `sr-Latn`, `UK` is `GB`, `756` is
  `CH`). A region code with several replacements takes the language's likely region when it
  is one of them, else the first one listed, as UTS #35 says (`en-200` reads `en-CZ`,
  `ar-NT` reads `ar-SA`). A language code whose replacement carries a region gives it only
  to a tag without one: `swc` reads `sw-CD`, but `swc-KE` reads `sw-KE`.
- The legacy tags of several subtags that CLDR replaces read their replacement, with the
  tag's own script and region kept: `zh-yue-HK` is `yue-HK`, `zh-cmn-Hant` is `zh-Hant`,
  `no-bok` is `nb`, `i-lux` is `lb`, `art-lojban` is `jbo`, `sv-aaland` is `sv-AX`. The
  rules apply until none matches, as UTS #35 says: `zh-cmn-yue` is `zh-yue`, then `yue`.
  They match only the subtags before the first extension, whether its singleton is a letter
  or a digit: in `sv-1-aaland`, `aaland` belongs to the extension, so the tag reads `sv`.
  A rule removes every occurrence of the subtags it matched (`no-bok-bok` is `nb`), and what
  the tag has left is read as a tag: its own script and region win wherever they stand in it
  (`es-aaland-419` is `es-419`), and the replacement's variants follow the tag's own. A variant
  or a subtag with a digit that the rules leave first is neither an extended language subtag
  nor a script: `sv-aaland-valencia`, `sv-a1b-aaland` and `sv-1996-aaland` are `sv-AX`.
  So `be-arevela-Latn` is `be-Latn` (the root), and a chain of rules reads what one rule
  does: `be-arevela-hepburn-heploc-Latn` is `be-Latn-alalc97`, the root as well.
  Where the replacement has no number data the tag raises `LookupError`, as any unknown
  language does: `hy-arevmda` is Western Armenian (`hyw`) and `zh-hakka` is Hakka (`hak`), so neither
  reads Armenian or Chinese.
- A tag without a script gets its likely one, from the region where it differs (`zh-TW`
  reads `zh-Hant`, `sr-ME` reads `sr-Latn-ME`), and then reads what that full form reads.
  Where the script has no data, that is the root, by the rule of the next point: `ku-GE` is
  `ku-Cyrl-GE`, and `ky-CN`, `tg-PK` and `ug-KZ` likewise read `und`. A tag that names its
  language's likely script gets no other: `ku-Latn-GE` reads `ku`, and `ky-Cyrl-CN` reads `ky`.
- A locale without data of its own falls back through the CLDR parent locales, then by
  dropping subtags (`pt-FR` reads `pt-PT`, `de-AT-1996` reads `de-AT`). A language in a script
  other than its likely one falls back to the root, as CLDR's `nonlikelyScript` rule says
  (`ru-Latn` and `hi-Arab` read `und`, not `ru` and `hi`). Unicode extensions such as
  `-u-nu-arab` and private use (`-x-...`) do not change anything.
- `und` and `root` are the root locale. An unknown language raises `LookupError` rather than
  reading another language's data. Text that is not a tag raises `ValueError`: an empty
  subtag, a subtag longer than eight characters or with characters other than ASCII letters
  and digits, in any position, a language subtag that is not two, three or five to eight
  letters, and an extended language subtag (three letters right after the language) other
  than those of the legacy tags above, such as `en-abc` or `zh-abc-HK`. That holds after the
  legacy rules: one that removes other subtags leaves the extended language subtag where it
  was, so `be-abc-aaland`, `en-abc-gb-oed` and `ja-aaland-abc` (`ja-abc` with the region
  `AX`) raise `ValueError` as `be-abc` does, in any case (`sv-ABC-aaland` too). Subtags
  after the script or region are read as variants without checking BCP 47's variant grammar:
  `en-US-abcd` and `en-Latn-abc` read `en`.

`supported_locales()` lists the 766 locales of the CLDR 48.2 JSON packages, every one with
number data, and `cldr_version()` the CLDR release, `48.2.0`. CLDR's XML has one more locale
with number data, `en_US_POSIX`, which the JSON packages leave out: `en-US-POSIX` reads `en`.

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
  in parsing, so that no input can make a call build text without end. Long integers are
  converted to and from decimal digits in better than quadratic time, so the longest
  values take about a tenth of a second on a desktop, well under a second.

## Strict parsing

`parse_number(text, locale)` and `parse_indian(text)` accept exactly:

1. optional spaces, tabs, carriage returns and line feeds (never a group symbol, even a
   no-break space);
2. an optional minus, the locale's own (`parse_indian` also takes `+`);
3. ASCII digits, either ungrouped (leading zeros allowed, as in `007`) or grouped exactly
   where the formatter puts separators, whatever the minimum grouping digits (so `1.234`
   and `1234` both read in Spanish), with a first group that does not start with `0`
   (`0,001` is refused rather than read as `1`);
4. optionally the decimal symbol followed by at least one digit;
5. optional trailing spaces as in step 1.

A value with no decimal symbol returns an `int`; one with it a `Decimal` keeping every
digit written. So text written by `format_number` or `format_indian` reads back to a value
that formats to the same text with the same locale and grouping. `-0` is the one exception:
it reads back as the `int` `0`, while `-0.0` stays `Decimal("-0.0")`. Text the formatter
would not write (no groups, groups the minimum grouping digits leave out, leading zeros,
`parse_indian`'s `+`, surrounding spaces) reads too, and formats back to the canonical
spelling: `parse_number("1.234", "es")` is `1234`, which formats as `1234`.

```python
from indgroup import parse_number

for text, locale in [
    ("1.234", "es"),
    ("1234", "es"),
    ("-1" + chr(0x202F) + "234,50", "fr"),
    ("-0", "en"),
]:
    print(repr(parse_number(text, locale)))
for text, locale in [
    ("1,234,567", "en-IN"),
    ("1 234", "fr"),
    ("1,234.", "en"),
    ("-5", "sv"),
    ("0,001", "en"),
]:
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
# not a validly grouped integer: '0,001'
```

## Types

The package ships `py.typed` and passes `mypy --strict`. `Number` is `int | float | Decimal`,
the values the formatters accept, and `Grouping` is
`Literal["auto", "min2", "always", "off"]`, so a type checker rejects any other grouping.
Both are for annotating your own code. At run time `Number` is the union
`int | float | Decimal` and `Grouping` a `typing.Literal`; `typing.get_args` lists the
members of each.

## Errors

| Exception | Raised for |
| --- | --- |
| `TypeError` | a value that is not an `int`, `float` or `Decimal`, a `bool`, or a text, locale, separator or grouping that is not a `str` |
| `ValueError` | NaN, infinities, more than 100,000 digits on a side, a bad separator, an unknown grouping, malformed text, a malformed locale tag (an extended language subtag CLDR does not replace included) |
| `LookupError` | a locale tag whose language has no CLDR number data |

Messages quote at most 40 characters of the input. A longer input is cut to its first 40
characters, followed by `...` and its length, such as `(100000 characters)`.

## Command line

`indgroup VALUE...` (or `python -m indgroup`) formats plain numbers: ASCII digits with an
optional sign (`+` or `-`), an optional decimal point with digits on either side or both
(`1234.5`, `-.5`, `5.`) and an optional exponent (`1e6`, `2.5E-3`), of any length. Once the
exponent is applied, the library's bound decides: at most 100,000 digits on each side of
the point, so `1e99999` prints and `1e100000` is refused as too long. Anything else, such
as `1,234`, `1_000`, `0x10` or `Infinity`, is not a plain number. `-p/--parse` reads
grouped values back and prints them plain. Without values
it reads stdin, one value per line, as UTF-8 (a byte order mark is skipped). Spaces, tabs
and line breaks around a value are ignored, in arguments and on stdin alike, and lines that
hold nothing else are skipped; any other character, a no-break space included, is part of
the value, as in `parse_number`. `-l/--locale` picks the locale (default `en-IN`),
`-g/--grouping` the strategy, `--locales` lists the locales, `--version` shows the package
and CLDR versions and `-h/--help` the options. Long options may be shortened to any unique
prefix (`--pars`). An option's value is taken as written: one `=` may join it to the option
(`-l=de`, `--locale=de`), so `-l==de` asks for the locale `=de` and `--locale=` for an empty
one, and nothing around it is trimmed. `-h/--help` and `--version` end the reading of the
arguments, so whichever comes first is shown and anything after it is ignored.

An argument that starts with a minus followed by a digit or a point (`-1e5`, `-1.234,5`)
is a value, the same on every Python version; put `--` before any other value that starts
with a minus. Errors, argument errors included, print one line on stderr, quoting at most
40 characters of an argument, and exit with status 2. On a pipe, stdin, stdout and stderr
are UTF-8 whatever the system encoding (the legacy code page on Windows), so a program that
reads the output of `indgroup` as UTF-8 can read its errors the same way. When the reader
of stdout closes it early, as `indgroup < values.txt | head -1` does, the command stops
quietly with status 1, and the same when it starts with stdout closed (`indgroup 5 >&-`).
Started with stdin closed and no VALUE arguments, it reports that there are no values, with
status 2. An error still exits with status 2 when the reader of stderr has closed it, or when
the command starts with stderr closed (`indgroup -l zz 1 2>&-`); the error line is then lost.

## Data and its sources

The table in the package is derived from the CLDR 48.2.0 JSON packages by
`scripts/build_table.py`, and the tests check that a fresh derivation gives the shipped file
byte for byte. The grouping rule follows ICU's `number_grouping.cpp` (release 78.3). Output
is compared with `Intl.NumberFormat` of Node 24.18 (ICU 78.3, CLDR 48): the recorded
reference covers the 637 CLDR locales that ICU ships under their own name and 13 alias and
fallback tags (such as `iw`, `en-UK` and `de-AT-1996`) in four groupings, and a live run
compares random values. They agree everywhere, `fr-CH` included: CLDR 48.2.0 gave it an
apostrophe as its group symbol, where 48.0.0 inherited the narrow no-break space of `fr`, and
ICU 78.3 carries the apostrophe. This library follows CLDR where Intl does not: it applies the
`nonlikelyScript` rule (`ru-Latn` and `ku-GE` read the root, Intl reads `ru` and `ku`), and
reads the legacy tags CLDR replaces (`zh-yue`, `no-bok`, `i-lux`), which Intl refuses. A tag
that spells out its language's likely script, such as `de-Latn-AT`, reads `de-AT` here:
UTS #35 starts the lookup of such a tag without its script, and adds no likely script for
the region, so `ku-Latn-GE` reads `ku` while `ku-GE` reads the root. Intl drops the region
and reads `de`. One difference goes the other way: Intl follows CLDR's XML, which gives
`en_US_POSIX` number data of its own, while this table comes from the CLDR JSON packages,
which leave it out, so `en-US-POSIX` reads `en`.
