"""Output matches Intl.NumberFormat of Node 24.18 (ICU 78.3, CLDR 48) with Latin digits,
recorded in tests/upstream/intl-node.json by scripts/intl_reference.mjs.

ICU ships fewer locales than CLDR. Where Intl falls back to another locale (its resolved
locale is neither the requested tag nor the CLDR locale this library resolves to), the case
is skipped: CLDR is the source of truth and test_sources.py covers it.
"""

from __future__ import annotations

from decimal import Decimal
from typing import Any, cast

import pytest
from conftest import KNOWN_ICU_DIFFERENCES, intl_comparable, upstream_json

from indgroup import Grouping, format_number, parse_number

_KNOWN = KNOWN_ICU_DIFFERENCES
_comparable = intl_comparable


@pytest.fixture(scope="module")
def reference() -> Any:
    data = upstream_json("intl-node.json")
    assert (data["icu"], data["cldr"], data["unicode"]) == ("78.3", "48.0", "17.0")
    return data


def test_every_locale_value_and_grouping_matches_intl(reference: Any) -> None:
    compared: set[str] = set()
    cases = 0
    for tag, grouping, value, resolved, expected in reference["cases"]:
        if not _comparable(tag, resolved):
            continue
        got = format_number(Decimal(value), tag, grouping=cast(Grouping, grouping))
        if tag in _KNOWN:
            icu, cldr = _KNOWN[tag]
            expected = expected.replace(icu, cldr)
        assert got == expected, (tag, grouping, value)
        compared.add(tag)
        cases += 1
    assert (len(compared), cases) == (650, 60168)
    probes = {"en-IN", "hi", "es", "pl", "ee", "fr", "de-CH", "tok", "fa", "zh-TW", "iw"}
    assert probes <= compared


def test_every_intl_output_parses_back(reference: Any) -> None:
    for tag, _grouping, value, resolved, expected in reference["cases"]:
        if not _comparable(tag, resolved) or tag in _KNOWN:
            continue
        back = parse_number(expected, tag)
        assert Decimal(back) == Decimal(value), (tag, expected)
