"""Digit grouping and strict reading of grouped digits, shared by every formatter."""

from __future__ import annotations

import re
from decimal import Decimal
from functools import lru_cache

from ._value import DIGITS, MAX_DIGITS, shown, too_long

_SPACE = " \t\r\n"


def group_digits(digits: str, separator: str, primary: int, secondary: int, minimum: int) -> str:
    """Insert ``separator`` into a run of digits the way ICU's grouper does.

    The first separator sits ``primary`` digits from the right, the next ones every
    ``secondary`` digits, and nothing is grouped unless at least ``minimum`` digits stand to
    the left of the first separator. A primary size of zero means no grouping.
    """
    if primary <= 0 or len(digits) - primary < minimum:
        return digits
    head = digits[:-primary]
    first = len(head) % secondary or secondary
    groups = [head[:first]]
    groups += [head[start : start + secondary] for start in range(first, len(head), secondary)]
    return separator.join([*groups, digits[-primary:]])


@lru_cache(maxsize=64)
def _grouped(separator: str, primary: int, secondary: int) -> re.Pattern[str]:
    sep = re.escape(separator)
    return re.compile(
        rf"[0-9]{{1,{secondary}}}(?:{sep}[0-9]{{{secondary}}})*{sep}[0-9]{{{primary}}}"
    )


def read_digits(part: str, separator: str, primary: int, secondary: int) -> str:
    """The plain digits of an integer part written ungrouped or grouped exactly as specified."""
    if DIGITS.fullmatch(part):
        digits = part
    elif primary > 0 and _grouped(separator, primary, secondary).fullmatch(part):
        digits = part.replace(separator, "")
    else:
        raise ValueError(f"not a validly grouped integer: {shown(part)}")
    if len(digits) > MAX_DIGITS:
        raise too_long("integer part")
    return digits


def read_number(
    text: str, decimal: str, separator: str, sizes: tuple[int, int], minus: str, plus: str = ""
) -> int | Decimal:
    """Parse ``text`` strictly: an optional sign, grouped digits, an optional fraction.

    A value without a fraction is an ``int``, one with a fraction a ``Decimal`` that keeps
    every digit written, so formatting it again gives the same text.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, not {type(text).__name__}")
    raw = str.__str__(text).strip(_SPACE)  # not str.strip(): U+00A0 and U+202F are group symbols
    negative = raw.startswith(minus)
    if negative:
        raw = raw[len(minus) :]
    elif plus and raw.startswith(plus):
        raw = raw[len(plus) :]
    integer, point, fraction = raw.partition(decimal)
    digits = read_digits(integer, separator, *sizes)
    if point and not DIGITS.fullmatch(fraction):
        raise ValueError(f"not a valid fractional part: {shown(fraction)}")
    if len(fraction) > MAX_DIGITS:
        raise too_long("fraction")
    if not point:
        number = int(Decimal(digits))  # int(str) stops at 4300 digits
        return -number if negative else number
    return Decimal(f"{'-' if negative else ''}{digits}.{fraction}")
