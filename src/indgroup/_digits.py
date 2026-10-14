"""Digit grouping and strict reading of grouped digits, shared by every formatter."""

from __future__ import annotations

import re
from decimal import Decimal
from functools import lru_cache

from ._value import DIGITS


def group_digits(digits: str, separator: str, primary: int, secondary: int, minimum: int) -> str:
    """Insert ``separator`` into a run of digits the way ICU's grouper does.

    The first separator sits ``primary`` digits from the right, the next ones every
    ``secondary`` digits, and nothing is grouped unless at least ``minimum`` digits stand to
    the left of the first separator. A primary size of zero means no grouping.
    """
    if primary <= 0 or len(digits) - primary < minimum:
        return digits
    groups = [digits[-primary:]]
    rest = digits[:-primary]
    while rest:
        groups.append(rest[-secondary:])
        rest = rest[:-secondary]
    return separator.join(reversed(groups))


@lru_cache(maxsize=64)
def _grouped(separator: str, primary: int, secondary: int) -> re.Pattern[str]:
    sep = re.escape(separator)
    return re.compile(
        rf"[0-9]{{1,{secondary}}}(?:{sep}[0-9]{{{secondary}}})*{sep}[0-9]{{{primary}}}"
    )


def read_digits(part: str, separator: str, primary: int, secondary: int) -> str:
    """The plain digits of an integer part written ungrouped or grouped exactly as specified."""
    if DIGITS.fullmatch(part):
        return part
    if primary > 0 and _grouped(separator, primary, secondary).fullmatch(part):
        return part.replace(separator, "")
    raise ValueError(f"not a validly grouped integer: {part!r}")


def read_number(
    text: str, decimal: str, separator: str, sizes: tuple[int, int], minus: str, plus: str = ""
) -> int | Decimal:
    """Parse ``text`` strictly: an optional sign, grouped digits, an optional fraction.

    A value without a fraction is an ``int``, one with a fraction a ``Decimal`` that keeps
    every digit written, so formatting it again gives the same text.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, not {type(text).__name__}")
    raw = text.strip()
    negative = raw.startswith(minus)
    if negative:
        raw = raw[len(minus) :]
    elif plus and raw.startswith(plus):
        raw = raw[len(plus) :]
    integer, point, fraction = raw.partition(decimal)
    digits = read_digits(integer, separator, *sizes)
    if point and not DIGITS.fullmatch(fraction):
        raise ValueError(f"not a valid fractional part: {fraction!r}")
    if not point:
        number = int(digits)
        return -number if negative else number
    return Decimal(f"{'-' if negative else ''}{digits}.{fraction}")
