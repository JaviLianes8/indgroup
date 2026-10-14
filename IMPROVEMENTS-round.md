# indgroup improvement round

Progress:
- [x] Brainstorm ranked improvements (this file)
- [x] Pin the ground truth: CLDR 48 number symbols and patterns, ICU 78.3 grouping rule, UTS #35 numbers
- [x] Locale table derived from CLDR, with the Unicode licence shipped
- [x] `format_number`, `parse_number`, `number_symbols`, locale resolution, grouping strategies
- [x] `format_indian` and `parse_indian` fixes: float input without drift, ASCII digits only, separator checks
- [x] Command line
- [ ] Contracts: CLDR table, Intl.NumberFormat output, README examples, installed wheel
- [ ] Docs and packaging: README, CHANGELOG, metadata, sdist contents
- [ ] Gates: ruff format, ruff check, mypy --strict, pytest
- [ ] Mutation run: removing guarded logic makes the suite fail
- [ ] Independent review findings fixed with regression tests
- [ ] Pull request opened, guard clean

## Starting point

`0.1.0` gives `format_indian(value, separator=)` and `parse_indian(text, separator=)`, for the
Indian lakh and crore grouping only. Probed:

- One convention. No other grouping size, no locale symbols: German `1.234.567,89`, French
  with a narrow no-break space (U+202F), Swiss `1'234'567.89`, Arabic decimal `٫` cannot be
  expressed. The separator argument swaps the group character but the decimal point is
  always `.`.
- No minimum grouping digits: CLDR says Spanish, Italian, Polish and European Portuguese leave
  four-digit numbers ungrouped (`1234` but `12.345`), and Ewe needs five digits before it
  groups.
- `float` is rejected, so a caller converts it first and may introduce binary drift
  (`Decimal(0.1)`); the shortest round-trip spelling (`repr`) is what Intl shows.
- The parser uses `\d`, which matches every Unicode decimal digit, so `parse_indian("١٢,٣٤٥")`
  is accepted though the formatter never writes it.
- `-` and `+` are accepted as separators, which makes `format_indian(-1234, separator="-")`
  ambiguous.

## Ranked improvements

1. **CLDR number data as the source of truth.** For each of the 766 locales of CLDR 48: the
   Latin-digit decimal and group symbols, the minus sign (with its bidi mark where CLDR has
   one), the primary and secondary grouping sizes read from the standard decimal pattern
   (`#,##0.###` is 3 and 3, `#,##,##0.###` is 3 and 2, `#,#0.###` is 2 and 2) and
   `minimumGroupingDigits`. Derived by a script from the CLDR JSON package into a compact
   table shipped with the package; the CLDR files stay in an ignored local folder. The
   Unicode licence ships with the wheel.
2. **`format_number(value, locale, grouping=)`** following the ICU grouping rule
   (`number_grouping.cpp`): separators at the primary size, then every secondary size, and
   only when the integer has at least `primary + minimumGroupingDigits` digits. `grouping`
   takes the `Intl.NumberFormat` `useGrouping` vocabulary: `auto`, `min2`, `always`, `off`.
   Output checked against `Intl.NumberFormat` of Node 24.18 (ICU 78.3, CLDR 48).
3. **Exact inputs.** `int`, `Decimal` and `float`; a float is read through its shortest
   round-trip spelling so `0.1` prints `0.1`, never `0.1000000000000000055511151231257827`.
   Fraction digits are kept as given, including trailing zeros and negative zero; no rounding
   happens anywhere. NaN and infinities raise. `bool` is refused.
4. **`parse_number(text, locale)`**, strict: the locale's own decimal, group and minus symbols,
   ASCII digits, groups exactly where that locale puts them (or no groups at all). Western
   grouping in `en-IN`, a regular space in French, a misplaced group: all `ValueError`.
   Returns `int` without a fraction, `Decimal` with one, so every formatted value round-trips.
5. **Locale resolution like ICU**, ported from the sibling library: BCP 47 or POSIX spelling,
   deprecated codes, CLDR parent locales, likely scripts; unknown languages raise
   `LookupError`. `resolve_locale`, `supported_locales`, `cldr_version`.
6. **`number_symbols(locale)`** returns a frozen `NumberSymbols` value so callers can see and
   reuse what the formatter uses.
7. **`format_indian` and `parse_indian` kept and fixed**: same output, float accepted without
   drift, ASCII digits only, signs and whitespace refused as separators.
8. **Typed API.** `Grouping` literal alias, `mypy --strict` clean, run-time checks with clear
   messages for the wrong types and unknown values.
9. **Command line.** `indgroup 1234567.89 -l de`, `indgroup --parse "12,34,567"`, values from
   arguments or stdin lines. It fits: shell reports and CSV clean-up want exactly this.
10. **Contracts.** The table equals a fresh derivation from CLDR; every locale matches
    `Intl.NumberFormat` (Latin digits) for a set of integers and decimals under each grouping
    strategy; README examples run; the installed wheel and its console script are driven from
    an empty folder.
11. **Docs and packaging.** README with executed examples and an API table, CHANGELOG,
    keywords, classifiers, licence expression, an sdist without planning notes or fetched
    files.

## Out of scope

- Native digits (Arabic-Indic, Devanagari and others): the table holds the Latin-digit
  symbols, which is what `Intl.NumberFormat` gives with `-u-nu-latn`.
- Rounding, significant digits, compact, percent and currency patterns.
- Lenient parsing (any space as a group, ASCII minus for a Unicode minus).
