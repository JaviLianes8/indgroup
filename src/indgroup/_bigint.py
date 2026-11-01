"""Exact conversions between long ints and decimal digits, in better than quadratic time.

CPython converts between ``int`` and ``Decimal`` one digit block at a time against the whole
number, which takes quadratic time: 100,000 digits took 0.2 s on a desktop and 0.9 s on a
slow laptop. Here the number is split in halves of whole bytes, and the halves are joined or
separated with ``Decimal`` multiplication and division, which libmpdec does in close to
linear time for long operands.
"""

from __future__ import annotations

import decimal
from decimal import Decimal

__all__ = ["to_decimal", "to_int"]

# Pieces of at most this many bytes (about 1,900 digits) go through Python's own conversion,
# which is fast at that size and stays under the 4,300-digit limit of int and str.
_PIECE = 800


def _exact() -> decimal.Context:
    # A fresh context per call: a shared one would share its flags between threads.
    traps = [decimal.Inexact, decimal.Rounded, decimal.InvalidOperation, decimal.Overflow]
    return decimal.Context(
        prec=decimal.MAX_PREC, Emax=decimal.MAX_EMAX, Emin=decimal.MIN_EMIN, traps=traps
    )


def to_decimal(number: int) -> Decimal:
    """``Decimal(number)``, with exponent 0, for an int of any length."""
    if number < 0:
        return _exact().minus(to_decimal(-number))  # not -x: that rounds to the current context
    raw = number.to_bytes((number.bit_length() + 7) // 8, "big")
    context = _exact()
    powers: dict[int, Decimal] = {}

    def join(start: int, stop: int) -> Decimal:
        if stop - start <= _PIECE:
            return Decimal(int.from_bytes(raw[start:stop], "big"))
        middle = stop - (stop - start) // 2
        width = stop - middle
        if width not in powers:
            powers[width] = context.power(Decimal(256), width)
        high = context.multiply(join(start, middle), powers[width])
        return context.add(high, join(middle, stop))

    return join(0, len(raw))


def to_int(digits: str) -> int:
    """``int(digits)`` for a string of ASCII digits of any length, leading zeros allowed."""
    number = Decimal(digits)
    context = _exact()
    powers: dict[int, Decimal] = {}

    def split(value: Decimal, width: int) -> bytes:
        """The ``width`` big-endian bytes of ``value``, which is below ``256 ** width``."""
        if width <= _PIECE:
            return int(value).to_bytes(width, "big")
        low = width // 2
        if low not in powers:
            powers[low] = context.power(Decimal(256), low)
        high, rest = context.divmod(value, powers[low])
        return split(high, width - low) + split(rest, low)

    # One byte holds log(256) / log(10), about 2.41 digits; 5 / 12 bytes a digit is enough.
    return int.from_bytes(split(number, len(digits) * 5 // 12 + 1), "big")
