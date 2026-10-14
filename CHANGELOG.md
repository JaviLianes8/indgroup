# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
  binary drift shows (`0.1` prints `0.1`). Before, a float raised `TypeError`.
- `parse_indian` accepts ASCII digits only. Before, any Unicode decimal digit passed, so
  `parse_indian` read Arabic-Indic digits the formatter never writes.
- The separator may not be `+` or `-`, which made signed output ambiguous, and must be a
  `str` (`TypeError` otherwise).

## [0.1.0]

- Add `format_indian` to render integers and decimals with Indian lakh and crore
  grouping, with a configurable separator and support for negatives.
- Add `parse_indian` to read a grouped value back to an `int` or `Decimal`,
  rejecting Western grouping and malformed input.
