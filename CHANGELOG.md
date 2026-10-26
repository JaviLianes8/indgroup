# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.0] - 2026-10-26

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
- Error messages quote at most 40 characters of the input; a longer input is cut and its
  length given. Before, they quoted it whole, so a megabyte of text gave a megabyte of
  message.
- `NumberSymbols` reports `indgroup` as its module, so pickles name the public path.
- Subclasses of `str` passed as text, locale, separator or grouping are read by their value,
  as subclasses of the numeric types already were.
- `parse_number` and `parse_indian` refuse a grouped integer whose first group starts with
  `0`, such as `0,001`, `01,234` or `00,01,234`: the formatters never write one, and `0,001`
  is more likely a misread decimal comma than the number 1. Ungrouped leading zeros (`007`)
  still read.
- `resolve_locale` applies CLDR's `nonlikelyScript` parent rule: a tag in a script other than
  its language's likely one falls back to the root locale (`ru-Latn`, `hi-Arab` and
  `de-Cyrl` read `und`), where 0.2.0 dropped the script and read `ru`, `hi` and `de`.
- A deprecated region code with several replacements is replaced as UTS #35 says, by the
  language's likely region when listed, else the first one: `en-200` reads `en-CZ`,
  `ar-NT` reads `ar-SA`, `kk-SU` reads `kk-KZ`. 0.2.0 left such codes alone.
- A tag that names its language's likely script reads the same locale as without it for
  every language, not only those written in several scripts: `ru-Cyrl-UA` reads `ru-UA`
  and `ca-Latn-ES-valencia` reads `ca-ES-valencia`.
- The command line reads its arguments without `argparse`, so it behaves the same on every
  Python version. An argument that starts with a minus followed by a digit or a point, such
  as `-1e5` or `-1.234,5`, is a value; before, Python 3.10 to 3.13 took it for an unknown
  option unless `--` came first, and 3.14 did not. Every error, argument errors included,
  prints one line on stderr (no usage block) quoting at most 40 characters of an argument,
  and still exits with status 2. `--help` and `--version` print to the stream given to
  `main` and return 0. Short options may be clustered (`-pl de`, `-plde`, `-l=de`), in time
  linear in the length of the argument, and a flag given a value (`-p=x`, `--parse=x`) is an
  error that names the flag.
- The command line trims only spaces, tabs and line breaks around a value read from stdin,
  as the parsers do: a no-break space or other Unicode space at either end of a line is part
  of the value, so a stray group symbol is refused instead of dropped. Arguments are trimmed
  the same way, so ` 5 ` formats as on stdin.
- On a pipe, the command line writes stderr as UTF-8, as it already read stdin and wrote
  stdout, keeping Python's backslash escapes for text UTF-8 cannot carry. Before, on Windows,
  an error quoting a non-ASCII argument came out in the legacy code page (`é` as the byte
  `0xE9`) or as `\u` escapes for characters that code page lacks, so a program reading
  both streams as UTF-8 failed on the error line.

### Fixed

- `indgroup --parse` printed nothing and failed with Python's `int` string conversion limit
  for integers of more than 4300 digits.
- A zero with a large exponent, such as `Decimal("0E+1000000")`, was refused as too long.
- `python -m indgroup` no longer runs the command when the module is merely imported.
- When the reader of its output closes the pipe early (`indgroup < values.txt | head -1`),
  the command stops quietly with status 1 instead of printing a `BrokenPipeError` traceback.
- Started without a stdout, stdin or stderr (closed with `>&-` or `<&-`, or by a parent that
  passes no standard handles), the command printed an `AttributeError` traceback. Without
  stdout it now stops quietly with status 1, as when its reader leaves; without stdin and
  VALUE arguments it reports that there are no values; without stderr an error still exits
  with status 2.

### Added

- A GUIDE with every rule, the doctests of every public name, and tests that pin the
  signatures and errors, compare random values live with `Intl.NumberFormat`, check strict
  parsing against an independent acceptor and time hostile input.

## [0.2.0] - 2026-10-14

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

## [0.1.0] - 2026-10-12

### Added

- Add `format_indian` to render integers and decimals with Indian lakh and crore
  grouping, with a configurable separator and support for negatives.
- Add `parse_indian` to read a grouped value back to an `int` or `Decimal`,
  rejecting Western grouping and malformed input.
