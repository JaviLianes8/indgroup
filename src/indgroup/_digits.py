"""Digit grouping and strict reading of grouped digits, shared by every formatter."""

from __future__ import annotations

import re
from decimal import Decimal
from functools import lru_cache

from ._bigint import to_int
from ._value import DIGITS, MAX_DIGITS, shown, too_long

SPACE = " \t\r\n"  # trimmed around values; never a group symbol such as U+00A0


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
    # The formatter never writes a leading zero group, and "0,001" is more likely a
    # misread decimal comma than the number 1, so a grouped integer starts with 1 to 9.
    sep = re.escape(separator)
    return re.compile(
        rf"[1-9][0-9]{{0,{secondary - 1}}}(?:{sep}[0-9]{{{secondary}}})*{sep}[0-9]{{{primary}}}"
    )


def read_digits(part: str, separator: str, primary: int, secondary: int) -> str:
    """The plain digits of an integer part, ungrouped or grouped exactly as specified.

    Ungrouped digits may start with zeros (``007``); grouped ones may not (``0,007``).
    """
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
    every digit written.
    """
    if not isinstance(text, str):
        raise TypeError(f"text must be a str, not {type(text).__name__}")
    raw = str.__str__(text).strip(SPACE)  # not str.strip(): U+00A0 and U+202F are group symbols
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
        number = to_int(digits)  # int(str) stops at 4300 digits and takes quadratic time
        return -number if negative else number
    return Decimal(f"{'-' if negative else ''}{digits}.{fraction}")
