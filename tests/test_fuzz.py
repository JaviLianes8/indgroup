"""Seeded property tests: round trips, and strict parsing against an independent acceptor."""

from __future__ import annotations

import random
from decimal import Decimal

import pytest
from generators import GROUPINGS, SEEDS, SPACES, hostile_text, locales, symbols_of, value

from indgroup import (
    format_indian,
    format_number,
    parse_indian,
    parse_number,
    resolve_locale,
    supported_locales,
)

ASCII = set("0123456789")


def _digits(text: str) -> bool:
    return bool(text) and set(text) <= ASCII


def _integer(text: str, group: str, primary: int, secondary: int) -> str | None:
    """The digits of an integer part written plain or grouped exactly; written from the
    README rule (group sizes counted from the right), not from the library's regex."""
    if _digits(text):
        return text
    chunks = text.split(group)
    if primary == 0 or len(chunks) < 2 or not all(_digits(chunk) for chunk in chunks):
        return None
    if len(chunks[-1]) != primary or not 1 <= len(chunks[0]) <= secondary:
        return None
    if any(len(chunk) != secondary for chunk in chunks[1:-1]):
        return None
    return "".join(chunks)


def _accept(
    text: str, decimal: str, group: str, sizes: tuple[int, int], signs: list[str]
) -> object:
    """What a strict parse must return for ``text``, or None when it must refuse it."""
    raw = text.strip(SPACES)
    negative = False
    for sign in signs:
        if raw.startswith(sign):
            negative, raw = sign == signs[0], raw[len(sign) :]
            break
    integer, point, fraction = raw.partition(decimal)
    digits = _integer(integer, group, *sizes)
    if digits is None or (point and not _digits(fraction)):
        return None
    if not point:
        return -int(digits) if negative else int(digits)
    return Decimal(f"{'-' if negative else ''}{digits}.{fraction}")


def _outcome(parse: object, *args: object) -> object:
    try:
        return parse(*args)  # type: ignore[operator]
    except ValueError as error:
        assert len(str(error)) < 200, error
        return None


def _parse_indian_with(text: str, separator: str) -> object:
    return parse_indian(text, separator=separator)


@pytest.mark.parametrize("seed", SEEDS)
def test_formatted_values_parse_back_and_format_the_same(seed: int) -> None:
    rng = random.Random(seed)
    tags = locales()
    for _ in range(4000):
        tag, grouping, number = rng.choice(tags), rng.choice(GROUPINGS), value(rng)
        shown = format_number(number, tag, grouping=grouping)
        back = parse_number(shown, tag)
        exact = Decimal(repr(number)) if isinstance(number, float) else Decimal(number)
        assert back == exact, (tag, grouping, number, shown)
        if shown != symbols_of(tag).minus + "0":  # -0 reads back as the int 0
            assert format_number(back, tag, grouping=grouping) == shown, (tag, number)


@pytest.mark.parametrize("seed", SEEDS)
def test_parse_number_accepts_exactly_the_strict_grammar(seed: int) -> None:
    rng = random.Random(seed)
    tags = locales()
    accepted = 0
    for _ in range(20000):
        tag = rng.choice(tags)
        symbols = symbols_of(tag)
        text = hostile_text(rng, symbols)
        sizes = (symbols.primary, symbols.secondary)
        expected = _accept(text, symbols.decimal, symbols.group, sizes, [symbols.minus])
        got = _outcome(parse_number, text, tag)
        assert got == expected and type(got) is type(expected), (tag, text)
        accepted += got is not None
    assert accepted > 1000


@pytest.mark.parametrize("seed", SEEDS)
def test_parse_indian_accepts_exactly_the_strict_grammar(seed: int) -> None:
    rng = random.Random(seed)
    symbols = symbols_of("en-IN")
    for _ in range(20000):
        separator = rng.choice([",", " ", "'", "_", chr(0x202F)])
        text = hostile_text(rng, symbols).replace(",", separator)
        expected = _accept(text, ".", separator, (3, 2), ["-", "+"])
        got = _outcome(_parse_indian_with, text, separator)
        assert got == expected and type(got) is type(expected), (separator, text)


@pytest.mark.parametrize("seed", SEEDS)
def test_format_indian_round_trips_with_any_separator(seed: int) -> None:
    rng = random.Random(seed)
    for _ in range(5000):
        number = value(rng)
        separator = chr(rng.choice([0x2C, 0x20, 0x27, 0x5F, 0xA0, 0x202F, 0x66C, 0x3001]))
        shown = format_indian(number, separator=separator)
        back = parse_indian(shown, separator=separator)
        exact = Decimal(repr(number)) if isinstance(number, float) else Decimal(number)
        assert back == exact, (number, separator, shown)


@pytest.mark.parametrize("seed", SEEDS)
def test_resolve_locale_returns_a_supported_locale_or_a_typed_error(seed: int) -> None:
    rng = random.Random(seed)
    known = set(supported_locales())
    parts = ["en", "zh", "sr", "pt", "und", "root", "Hant", "Latn", "IN", "419", "TW", "UK"]
    parts += ["1996", "u", "co", "x", "posix", "abcdefgh", "a", "", "@latin", ".UTF-8", "xx"]
    resolved = 0
    for _ in range(20000):
        tag = rng.choice("-_").join(rng.choices(parts, k=rng.randint(1, 5)))
        try:
            found = resolve_locale(tag)
        except (ValueError, LookupError) as error:
            assert len(str(error)) < 200
            continue
        assert found in known, tag
        assert resolve_locale(found) == found
        resolved += 1
    assert resolved > 1000
