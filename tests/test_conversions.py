"""Long integers convert in better than quadratic time, exactly, in both directions.

Python converts between int and Decimal (and str) in time quadratic in the number of
digits, so 100,000 digits took 0.2 s on a desktop and 0.9 s on a slow laptop. The growth
contract times each public path at 12,500 and 100,000 digits: eight times the digits cost
64 times as long when quadratic, about 20 times with the conversions this package uses.
"""

from __future__ import annotations

import random
import time
from collections.abc import Callable
from decimal import Decimal

import pytest

from indgroup import format_indian, format_number, parse_indian, parse_number
from indgroup._bigint import to_decimal, to_int
from indgroup._cli import main

SMALL, LARGE = 12_500, 100_000


def _cost(call: Callable[[], object], runs: int = 5) -> float:
    # The fastest of several runs: other work on a busy machine only ever adds time.
    best = float("inf")
    for _ in range(runs):
        started = time.perf_counter()
        call()
        best = min(best, time.perf_counter() - started)
    return best


def _growth(make: Callable[[int], Callable[[], object]]) -> float:
    small, large = make(SMALL), make(LARGE)
    return _cost(large) / max(_cost(small), 1e-6)


PATHS: dict[str, Callable[[int], Callable[[], object]]] = {
    "parse_indian plain": lambda n: (lambda text: lambda: parse_indian(text))("9" * n),
    "parse_indian grouped": lambda n: (lambda text: lambda: parse_indian(text))(
        format_indian(10**n - 1)
    ),
    "parse_number": lambda n: (lambda text: lambda: parse_number(text, "de"))("9" * n),
    "format_indian": lambda n: (lambda value: lambda: format_indian(value))(10**n - 1),
    "format_number": lambda n: (lambda value: lambda: format_number(value, "en"))(-(10**n) + 1),
}


@pytest.mark.parametrize("path", sorted(PATHS))
def test_long_integers_cost_far_less_than_quadratic_time(path: str) -> None:
    assert _growth(PATHS[path]) < 36, path


def test_the_cli_prints_a_long_parsed_integer_in_far_less_than_quadratic_time() -> None:
    import io

    def make(n: int) -> Callable[[], object]:
        text = "9" * n
        return lambda: main(["-p", text], stdin=io.StringIO(""), stdout=io.StringIO())

    assert _growth(make) < 36


def test_the_largest_values_take_well_under_a_second() -> None:
    # About 0.07 s on a desktop; the bound leaves room for a laptop five times slower.
    biggest = 10**LARGE - 1
    grouped = format_number(biggest, "en")
    for call in (
        lambda: parse_indian("9" * LARGE),
        lambda: format_indian(biggest),
        lambda: format_number(biggest, "en"),
        lambda: parse_number(grouped, "en"),
    ):
        assert _cost(call, runs=2) < 1


@pytest.mark.parametrize("digits", [1, 2, 799, 800, 801, 1927, 1928, 4300, 4301, 30_001])
def test_conversions_are_exact_at_every_size(digits: int) -> None:
    rng = random.Random(digits)
    for _ in range(3):
        text = str(rng.randint(1, 9)) + "".join(rng.choices("0123456789", k=digits - 1))
        reference = Decimal(text)
        number = to_int(text)
        assert Decimal(number) == reference
        assert to_int("000" + text) == number
        assert to_decimal(number) == reference and to_decimal(-number) == reference.copy_negate()
        assert to_decimal(number).as_tuple().exponent == 0


def test_conversions_of_zero_and_powers_of_two_and_ten() -> None:
    assert to_int("0") == 0 and to_int("0000") == 0
    assert to_decimal(0) == 0 and str(to_decimal(0)) == "0"
    for exponent in (8, 799 * 8, 800 * 8, 800 * 8 + 1, 50_000):
        assert to_decimal(2**exponent) == Decimal(2**exponent)
        assert to_decimal(2**exponent - 1) == Decimal(2**exponent - 1)
    for exponent in (1, 1927, 1928, 40_000):
        assert to_int("1" + "0" * exponent) == 10**exponent
        assert to_decimal(10**exponent) == Decimal(f"1E+{exponent}")
        assert to_int("9" * exponent) == 10**exponent - 1
