"""The shipped table and the grouping rule agree with the pinned upstream sources.

The sources live in tests/upstream (see MANIFEST.json); these tests skip while absent.
"""

from __future__ import annotations

import importlib.util
import io
import json
import re
import tarfile
from pathlib import Path
from types import ModuleType
from typing import Any

from conftest import read_upstream

from indgroup import number_symbols, supported_locales

ROOT = Path(__file__).resolve().parents[1]


def _build_script() -> ModuleType:
    spec = importlib.util.spec_from_file_location(
        "build_table", ROOT / "scripts" / "build_table.py"
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _cldr_numbers() -> dict[str, Any]:
    found: dict[str, Any] = {}
    body = read_upstream("cldr-numbers-full-48.0.0.tgz")
    with tarfile.open(fileobj=io.BytesIO(body)) as archive:
        for member in archive.getmembers():
            if member.name.endswith("/numbers.json"):
                handle = archive.extractfile(member)
                assert handle is not None
                locale = member.name.split("/")[2]
                found[locale] = json.load(handle)["main"][locale]["numbers"]
    return found


def test_the_shipped_table_is_a_fresh_derivation_from_cldr() -> None:
    read_upstream("cldr-core-48.0.0.tgz")
    read_upstream("cldr-numbers-full-48.0.0.tgz")
    script = _build_script()
    shipped = (ROOT / "src" / "indgroup" / "_cldr.json").read_text(encoding="ascii")
    assert script.render(script.derive()) == shipped


def test_every_locale_reads_its_own_cldr_symbols() -> None:
    numbers = _cldr_numbers()
    assert sorted(numbers) == list(supported_locales())
    for locale, data in numbers.items():
        symbols = data["symbols-numberSystem-latn"]
        found = number_symbols(locale)
        assert found.locale == locale
        assert (found.decimal, found.group, found.minus) == (
            symbols["decimal"],
            symbols["group"],
            symbols["minusSign"],
        )
        assert found.decimal != found.group, locale
        assert found.min_grouping == int(data["minimumGroupingDigits"])


def test_grouping_sizes_come_from_the_standard_pattern() -> None:
    numbers = _cldr_numbers()
    sizes = {"#,##0.###": (3, 3), "#,##,##0.###": (3, 2), "#,#0.###": (2, 2)}
    for locale, data in numbers.items():
        pattern = data["decimalFormats-numberSystem-latn"]["standard"]
        found = number_symbols(locale)
        assert (found.primary, found.secondary) == sizes[pattern], locale


def test_grouping_sizes_of_hand_written_patterns() -> None:
    # Written by hand to cover shapes CLDR 48 does not use.
    sizes = _build_script().grouping_sizes
    assert sizes("0.######") == (0, 0)
    assert sizes("#,##0.00;(#,##0.00)") == (3, 3)
    assert sizes("#,##,###,##0") == (3, 3)
    assert sizes("#,####,##0") == (3, 4)
    assert sizes("#,#,##0") == (3, 1)


def test_the_grouping_rule_matches_icu() -> None:
    source = read_upstream("icu-78.3-number_grouping.cpp").decode("utf-8")
    # ICU groups when the digits left of the first separator reach the minimum grouping.
    assert "value.getUpperDisplayMagnitude() - fGrouping1 + 1 >= fMinGrouping" in source
    assert "(position % fGrouping2) == 0" in source
    # min2 takes the larger of two and the locale minimum; always (aligned) uses one.
    assert re.search(r"uprv_max\(2, getMinGroupingForLocale\(locale\)\)", source)
    assert "return {-4, -4, 1, grouping};" in source
    assert "fGrouping1 == -4 ? static_cast<short>(3)" in source


def test_the_spec_defines_minimum_grouping_digits() -> None:
    page = read_upstream("tr35-numbers.html").decode("utf-8")
    assert "<th>48</th>" in page
    assert "minimumGroupingDigits" in page
