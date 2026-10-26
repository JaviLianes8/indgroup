"""Seeded random cases checked live against Intl.NumberFormat of the installed Node.

The recorded reference of test_intl.py covers fixed values; this asks Node in the test run
for random locales, groupings and decimal strings. It needs Node with ICU 78.3 and CLDR 48
(Node 24.18) and skips otherwise, since another ICU writes other data.
"""

from __future__ import annotations

import json
import random
import shutil
import subprocess
from decimal import Decimal
from pathlib import Path
from typing import cast

import pytest
from conftest import intl_comparable
from generators import GROUPINGS, SEEDS, decimal_text, locales

from indgroup import Grouping, format_number, parse_number

ROOT = Path(__file__).resolve().parents[1]
CASES = 6000


def _intl(cases: list[list[str]]) -> list[list[str | None]]:
    node = shutil.which("node")
    if node is None:
        pytest.skip("Node is not installed")
    done = subprocess.run(
        [node, str(ROOT / "scripts" / "intl_oracle.mjs")],
        input=json.dumps(cases),
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    )
    answer = json.loads(done.stdout)
    if (answer["icu"], answer["cldr"]) != ("78.3", "48.0"):
        pytest.skip(f"Node has ICU {answer['icu']} and CLDR {answer['cldr']}, not 78.3 and 48.0")
    results: list[list[str | None]] = answer["results"]
    return results


@pytest.mark.parametrize("seed", SEEDS)
def test_random_values_match_intl_and_parse_back(seed: int) -> None:
    rng = random.Random(seed)
    tags = locales()
    cases = [[rng.choice(tags), rng.choice(GROUPINGS), decimal_text(rng)] for _ in range(CASES)]
    compared = 0
    for (tag, grouping, text), (resolved, expected) in zip(cases, _intl(cases), strict=True):
        if not intl_comparable(tag, resolved):
            continue
        assert expected is not None
        value = Decimal(text)
        got = format_number(value, tag, grouping=cast(Grouping, grouping))
        assert got == expected, (tag, grouping, text)
        back = parse_number(expected, tag)
        assert Decimal(back) == value, (tag, expected)
        compared += 1
    assert compared > CASES * 0.8
