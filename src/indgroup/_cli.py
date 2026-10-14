"""Command line: ``indgroup 1234567`` prints ``12,34,567``; ``-l de`` prints ``1.234.567``."""

from __future__ import annotations

import argparse
import re
import sys
from collections.abc import Sequence
from decimal import Decimal
from typing import TextIO, cast

from ._locale import cldr_version, supported_locales
from ._number import Grouping, format_number, parse_number

__all__ = ["main"]

_BOM = chr(0xFEFF)
_PLAIN = re.compile(r"[+-]?[0-9]+(?:\.[0-9]+)?(?:[eE][+-]?[0-9]{1,4})?")


def _parser() -> argparse.ArgumentParser:
    from . import __version__

    parser = argparse.ArgumentParser(
        prog="indgroup",
        description="Group the digits of numbers the way a locale writes them (Unicode CLDR).",
        epilog="Without VALUE arguments the values are read from stdin, one per non-blank line."
        " Put -- before negative values other than plain digits, such as -1e5 or -1.234,5.",
    )
    parser.add_argument("values", nargs="*", metavar="VALUE", help="the numbers, in order")
    parser.add_argument("-l", "--locale", default="en-IN", help="BCP 47 locale (default: en-IN)")
    parser.add_argument(
        "-g",
        "--grouping",
        default="auto",
        choices=["auto", "min2", "always", "off"],
        help="when to group, as Intl.NumberFormat useGrouping (default: auto)",
    )
    parser.add_argument(
        "-p",
        "--parse",
        action="store_true",
        help="read grouped values written in the locale and print them plain",
    )
    parser.add_argument(
        "--locales", action="store_true", help="list the supported locales and exit"
    )
    parser.add_argument(
        "--version", action="version", version=f"indgroup {__version__} (CLDR {cldr_version()})"
    )
    return parser


def _utf8(stream: TextIO, encoding: str = "utf-8") -> None:
    # Pipes default to the legacy code page on Windows, which cannot carry U+202F and friends.
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None and not stream.isatty():
        reconfigure(encoding=encoding)


def _read_values(stdin: TextIO) -> list[str]:
    values = [line.strip() for line in stdin]
    if values:
        values[0] = values[0].removeprefix(_BOM).strip()
    return [value for value in values if value]


def _convert(value: str, args: argparse.Namespace) -> str:
    if args.parse:
        number = parse_number(value, args.locale)
        return str(number) if isinstance(number, int) else format(number, "f")
    if not _PLAIN.fullmatch(value):
        raise ValueError(f"not a plain number: {value!r}")
    return format_number(Decimal(value), args.locale, grouping=cast(Grouping, args.grouping))


def main(
    argv: Sequence[str] | None = None, stdin: TextIO | None = None, stdout: TextIO | None = None
) -> int:
    """Run the command line and return 0.

    Bad arguments, an unknown locale, a value that cannot be read or stdin that is not
    UTF-8 exit with status 2 through ``SystemExit``. Without streams it reads ``sys.stdin``
    and writes ``sys.stdout``, switching them to UTF-8 when they are pipes.
    """
    if stdin is None:
        stdin = sys.stdin
        _utf8(stdin, "utf-8-sig")
    if stdout is None:
        stdout = sys.stdout
        _utf8(stdout)
    parser = _parser()
    args = parser.parse_args(argv)
    if args.locales:
        stdout.write("\n".join(supported_locales()) + "\n")
        return 0
    if not args.values and stdin.isatty():
        parser.error("no values: pass VALUE arguments or pipe them on stdin")
    try:
        values = args.values or _read_values(stdin)
    except UnicodeDecodeError:
        parser.exit(2, "indgroup: error: stdin is not valid UTF-8\n")
    try:
        lines = [_convert(value, args) for value in values]
    except (LookupError, ValueError) as error:
        parser.exit(2, f"indgroup: error: {error}\n")
    stdout.write("".join(f"{line}\n" for line in lines))
    return 0
