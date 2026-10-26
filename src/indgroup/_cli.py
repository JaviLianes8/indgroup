"""Command line: ``indgroup 1234567`` prints ``12,34,567``; ``-l de`` prints ``1.234.567``."""

from __future__ import annotations

import errno
import os
import re
import sys
from collections.abc import Sequence
from decimal import Decimal
from typing import NoReturn, TextIO, cast

from ._args import HELP, Args, UsageError, read_args
from ._bigint import to_decimal
from ._digits import SPACE
from ._locale import cldr_version, supported_locales
from ._number import Grouping, format_number, parse_number
from ._value import shown

__all__ = ["main"]

_BOM = chr(0xFEFF)
# Decimal's finite spellings in ASCII. The exponent is matched whole and its value capped
# below, so its length never matters: the 100,000-digit bound of the library decides.
_PLAIN = re.compile(r"([+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+))(?:[eE]([+-]?)([0-9]+))?")
_EXPONENT_CAP = "999999999"  # past any bound, and within what Decimal can hold


def _utf8(stream: TextIO | None, encoding: str = "utf-8", errors: str = "strict") -> None:
    # Pipes default to the legacy code page on Windows, which cannot carry U+202F and friends.
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is not None and stream is not None and not stream.isatty():
        reconfigure(encoding=encoding, errors=errors)


def _fail(message: str) -> NoReturn:
    # A stderr that is missing or whose reader left is treated as stdout is, so the status stays 2.
    _write(sys.stderr, f"indgroup: error: {message}\n")
    raise SystemExit(2)


def _read_values(stdin: TextIO) -> list[str]:
    # The same trimming as the parsers: a no-break space may be a group symbol, never padding.
    values = [line.strip(SPACE) for line in stdin]
    if values:
        values[0] = values[0].removeprefix(_BOM).strip(SPACE)
    return [value for value in values if value]


def _convert(value: str, args: Args) -> str:
    if args.parse:
        number = parse_number(value, args.locale)
        if isinstance(number, int):  # str(int) stops at 4300 digits and takes quadratic time
            number = to_decimal(number)
        return format(number, "f")
    match = _PLAIN.fullmatch(value.strip(SPACE))
    if match is None:
        raise ValueError(f"not a plain number: {shown(value)}")
    mantissa, sign, exponent = match.group(1, 2, 3)
    exponent = (exponent or "0").lstrip("0") or "0"
    if len(exponent) > len(_EXPONENT_CAP):
        exponent = _EXPONENT_CAP
    number = Decimal(f"{mantissa}e{sign or ''}{exponent}")
    return format_number(number, args.locale, grouping=cast(Grouping, args.grouping))


def _closed(error: OSError) -> bool:
    # Windows reports a reader that went away as EINVAL as often as EPIPE.
    return isinstance(error, BrokenPipeError) or (
        sys.platform == "win32" and error.errno == errno.EINVAL
    )


def _write(stdout: TextIO | None, text: str) -> int:
    """Write ``text``; 1, quietly, when the reader closed the pipe (``indgroup | head -1``)."""
    if stdout is None:  # started without a stdout: as if its reader had already gone
        return 1 if text else 0
    try:
        stdout.write(text)
        stdout.flush()
    except OSError as error:
        if not _closed(error):
            raise
        try:
            descriptor = stdout.fileno()
        except (OSError, ValueError):  # not a real file, such as a StringIO
            return 1
        # What is still buffered goes nowhere, so the exit flush cannot fail a second time.
        devnull = os.open(os.devnull, os.O_WRONLY)
        os.dup2(devnull, descriptor)
        os.close(devnull)
        return 1
    return 0


def main(
    argv: Sequence[str] | None = None, stdin: TextIO | None = None, stdout: TextIO | None = None
) -> int:
    """Run the command line and return its exit status: 0, or 1 if stdout's reader left.

    Bad arguments, an unknown locale, a value that cannot be read or stdin that is not
    UTF-8 print one line on stderr and exit with status 2 through ``SystemExit``. Without
    streams it reads ``sys.stdin`` and writes ``sys.stdout``, switching each one it uses
    to UTF-8 when it is a pipe, and ``sys.stderr`` too when it writes ``sys.stdout``.
    """
    from . import __version__

    # Python sets sys.stdin and sys.stdout to None when the process starts without them.
    source: TextIO | None = stdin
    if source is None:
        source = sys.stdin
        _utf8(source, "utf-8-sig")
    target: TextIO | None = stdout
    if target is None:
        target = sys.stdout
        _utf8(target)
        # A program that reads stdout as UTF-8 reads stderr the same way; never fail on it.
        _utf8(sys.stderr, errors="backslashreplace")
    try:
        args = read_args(list(sys.argv[1:] if argv is None else argv))
    except UsageError as error:
        _fail(str(error))
    if args.show == "help":
        return _write(target, HELP)
    if args.show == "version":
        return _write(target, f"indgroup {__version__} (CLDR {cldr_version()})\n")
    if args.locales:
        return _write(target, "\n".join(supported_locales()) + "\n")
    if not args.values and (source is None or source.isatty()):
        _fail("no values: pass VALUE arguments or pipe them on stdin")
    try:
        values = args.values or _read_values(source)
    except UnicodeDecodeError:
        _fail("stdin is not valid UTF-8")
    try:
        lines = [_convert(value, args) for value in values]
    except (LookupError, ValueError) as error:
        _fail(str(error))
    return _write(target, "".join(f"{line}\n" for line in lines))
