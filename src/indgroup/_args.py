"""Command-line arguments, read the same way on every supported Python.

argparse is not used: whether it takes ``-1e5`` for an option changed in Python 3.14, and
its errors print a usage block and quote arguments whole.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from ._value import shown

__all__ = ["GROUPINGS", "HELP", "Args", "UsageError", "read_args"]

GROUPINGS = ("auto", "min2", "always", "off")

HELP = """\
usage: indgroup [-h] [--version] [--locales] [-l LOCALE] [-g GROUPING] [-p] [VALUE ...]

Group the digits of numbers the way a locale writes them (Unicode CLDR).

positional arguments:
  VALUE                the numbers, in order; without any, one per non-blank line of stdin

options:
  -h, --help           show this help and exit
  --version            show the package and CLDR versions and exit
  --locales            list the supported locales and exit
  -l, --locale LOCALE  BCP 47 or POSIX locale (default: en-IN)
  -g, --grouping GROUPING
                       auto, min2, always or off, as Intl.NumberFormat useGrouping
                       (default: auto)
  -p, --parse          read values grouped the locale's way and print them plain

An argument that starts with a minus followed by a digit or a point, such as -1e5, is a
value. Put -- before any other value that starts with a minus.
"""

_LONG = ("--help", "--version", "--locales", "--locale", "--grouping", "--parse")
_SHORT = {"-h": "--help", "-l": "--locale", "-g": "--grouping", "-p": "--parse"}
_NEGATIVE = re.compile(r"-\.?[0-9]")


class UsageError(Exception):
    """A command line that cannot be read; the message is one short line."""


@dataclass
class Args:
    """What the command line asks for."""

    values: list[str] = field(default_factory=list)
    locale: str = "en-IN"
    grouping: str = "auto"
    parse: bool = False
    locales: bool = False
    show: str = ""  # "help" or "version": print it and stop


def _option(text: str, arg: str) -> str:
    """The long name of an option, from its short name or a unique prefix of its long one."""
    if text in _SHORT:
        return _SHORT[text]
    if text in _LONG:
        return text
    matches = [name for name in _LONG if name.startswith(text)] if len(text) > 2 else []
    if len(matches) == 1:
        return matches[0]
    if matches:
        raise UsageError(f"ambiguous option {shown(text)}: {' or '.join(matches)}")
    raise UsageError(f"unknown option {shown(arg)}")


def _set(args: Args, name: str, value: str) -> None:
    if name == "--locale":
        args.locale = value
    elif value in GROUPINGS:
        args.grouping = value
    else:
        raise UsageError(f"--grouping must be one of {', '.join(GROUPINGS)}, not {shown(value)}")


def read_args(argv: list[str]) -> Args:
    """Read ``argv`` the way getopt-style tools do; raise ``UsageError`` when it cannot."""
    args = Args()
    pending = argv[::-1]  # popped from the end, so a cluster such as -pl can push back -l
    while pending:
        arg = pending.pop()
        if arg == "--":
            args.values.extend(reversed(pending))
            break
        if arg == "-" or not arg.startswith("-") or _NEGATIVE.match(arg):
            args.values.append(arg)
            continue
        if arg.startswith("--"):
            text, attached, value = arg.partition("=")
        else:  # "-lde", "-l=de", "-pl"
            text, value = arg[:2], arg[2:]
            attached = value[:1]
            value = value.removeprefix("=")
        name = _option(text, arg)
        if name in ("--locale", "--grouping"):
            if not attached:
                if not pending:
                    raise UsageError(f"{name} needs a value")
                value = pending.pop()
            _set(args, name, value)
        elif attached and text.startswith("--"):
            raise UsageError(f"{name} takes no value: {shown(arg)}")
        elif attached:
            if "-" + value[:1] not in _SHORT:
                raise UsageError(f"unknown option {shown('-' + value[:1])} in {shown(arg)}")
            pending.append("-" + value)
            attached = ""
        if name in ("--help", "--version"):
            args.show = name.removeprefix("--")
            return args
        args.parse = args.parse or name == "--parse"
        args.locales = args.locales or name == "--locales"
    return args
