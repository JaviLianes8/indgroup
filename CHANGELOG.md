# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-25

The first stable release. The public API is the eleven names of 0.2.0 with their
signatures, parameter names and defaults unchanged: `format_indian`, `parse_indian`,
`format_number`, `parse_number`, `number_symbols`, `NumberSymbols`, `resolve_locale`,
`supported_locales`, `cldr_version`, `Number` and `Grouping`. The number data is CLDR 48.0.0
for all 766 locales. From here on, a change to any of them, or to the exceptions they raise,
needs a new major version.

### Changed

- The digit bound is now 100,000 digits before the point and 100,000 after it, checked in
  formatting and in parsing (`ValueError`). 0.2.0 allowed a million integer digits, which took
  seconds to convert between `int` and `Decimal`, and bounded neither the fraction nor the
  digits read by the parsers, so `Decimal("1E-999999999")` built a gigabyte of text.
- A `grouping` that is not a `str` raises `TypeError` instead of `ValueError`, like every
  other argument of the wrong type.
- Error messages quote at most 40 characters of the input, followed by its length. Before,
  they quoted it whole, so a megabyte of text gave a megabyte of message.
- `NumberSymbols` reports `indgroup` as its module, so pickles name the public path.
- Subclasses of `str` passed as text, locale, separator or grouping are read by their value,
  as subclasses of the numeric types already were.

### Fixed

- `indgroup --parse` printed nothing and failed with Python's `int` string conversion limit
  for integers of more than 4300 digits.
- A zero with a large exponent, such as `Decimal("0E+1000000")`, was refused as too long.
- `python -m indgroup` no longer runs the command when the module is merely imported.

### Added

- A GUIDE with every rule, the doctests of every public name, and tests that pin the
  signatures and errors, compare random values live with `Intl.NumberFormat`, check strict
  parsing against an independent acceptor and time hostile input.

## [0.2.0]

### Added

- `format_number` writes a number the way a locale does, from the number data of all 766
  locales of Unicode CLDR 48: decimal, group and minus symbols, primary and secondary
  grouping sizes, and minimum grouping digits (Spanish `1234` but `12.345`). `grouping`
  takes the `useGrouping` vocabulary of `Intl.NumberFormat`: `auto`, `min2`, `always`, `off`.
- `parse_number`, its strict inverse.
- `number_symbols` and the frozen `NumberSymbols` value it returns.
- `resolve_locale`, `supported_locales` and `cldr_version`. Tags may be BCP 47 or POSIX;
  deprecated codes, likely scripts and CLDR parent locales are honoured, and an unknown
  language raises `LookupError`.
- `Number` and `Grouping` type aliases.
- An `indgroup` command and `python -m indgroup`.
- The Unicode License v3 ships with the package for the derived CLDR data.

### Changed

- `format_indian` accepts `float`, read through its shortest round-trip spelling so no
  binary drift shows (`0.1` prints `0.1`, `5.0` prints `5`). Before, a float raised
  `TypeError`.
- Values with more than a million integer digits raise `ValueError`; below that, any length
  works, past the 4300-digit limit of `int` string conversion.
- Parsing strips only ASCII spaces, tabs and line breaks around the text, never a group
  symbol such as a no-break space.
- `parse_indian` accepts ASCII digits only. Before, any Unicode decimal digit passed, so
  `parse_indian` read Arabic-Indic digits the formatter never writes.
- The separator may not be `+` or `-`, which made signed output ambiguous, and must be a
  `str` (`TypeError` otherwise).

## [0.1.0]

- Add `format_indian` to render integers and decimals with Indian lakh and crore
  grouping, with a configurable separator and support for negatives.
- Add `parse_indian` to read a grouped value back to an `int` or `Decimal`,
  rejecting Western grouping and malformed input.
