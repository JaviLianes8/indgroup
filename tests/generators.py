"""Seeded random inputs shared by the property, fuzz and oracle tests."""

from __future__ import annotations

import random
from decimal import Decimal

from indgroup import Grouping, NumberSymbols, number_symbols, supported_locales

SEEDS = [11, 2026, 48]
GROUPINGS: list[Grouping] = ["auto", "min2", "always", "off"]
SPACES = " \t\r\n"


def locales() -> list[str]:
    """Every CLDR locale but the root."""
    return [locale for locale in supported_locales() if locale != "und"]


def decimal_text(rng: random.Random, max_integer: int = 40, max_fraction: int = 12) -> str:
    """A plain decimal string with no leading zeros: optional minus, digits, optional fraction."""
    length = rng.choice([1, 1, 2, 3, 4, 5, 6, 7, 8, 9, rng.randint(1, max_integer)])
    integer = str(rng.randint(1, 9)) + "".join(rng.choices("0123456789", k=length - 1))
    if rng.random() < 0.15:
        integer = "0"
    text = ("-" if rng.random() < 0.3 else "") + integer
    if rng.random() < 0.4:
        text += "." + "".join(rng.choices("0123456789", k=rng.randint(1, max_fraction)))
    return text


def value(rng: random.Random) -> int | float | Decimal:
    """An int, a float or a Decimal, each written in several shapes."""
    kind = rng.random()
    if kind < 0.35:
        return int(Decimal(decimal_text(rng).split(".")[0]))
    if kind < 0.55:
        return rng.choice(
            [rng.uniform(-1e9, 1e9), rng.random(), float(rng.randint(-(10**15), 10**15))]
        )
    text = decimal_text(rng)
    if rng.random() < 0.2:
        text += f"E{rng.randint(-20, 20):+d}"
    return Decimal(text)


def hostile_text(rng: random.Random, symbols: NumberSymbols, length: int = 24) -> str:
    """Text made of the locale's own symbols, digits, spaces and a few strangers."""
    pool = [
        *"0123456789" * 3,
        symbols.decimal,
        symbols.group,
        symbols.group,
        symbols.minus,
        *SPACES,
        "+",
        "-",
        ".",
        ",",
        "'",
        chr(0x00A0),
        chr(0x202F),
        chr(0x2212),
        chr(0x0663),
        chr(0xFF11),
        "e",
        "\x00",
        "\ud800",
    ]
    return "".join(rng.choices(pool, k=rng.randint(0, length)))


def symbols_of(locale: str) -> NumberSymbols:
    return number_symbols(locale)
