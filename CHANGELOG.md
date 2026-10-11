# Changelog

All notable changes to this project are documented here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0]

- Add `format_indian` to render integers and decimals with Indian lakh and crore
  grouping, with a configurable separator and support for negatives.
- Add `parse_indian` to read a grouped value back to an `int` or `Decimal`,
  rejecting Western grouping and malformed input.
