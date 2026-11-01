"""Locale canonicalization contracts from fetched CLDR vectors and handwritten tags."""

from __future__ import annotations

import pytest
from conftest import read_upstream

from indgroup import format_number, number_symbols, parse_number, resolve_locale


def _outcome(tag: str) -> str | type[Exception]:
    try:
        return resolve_locale(tag)
    except (ValueError, LookupError) as error:
        return type(error)


def test_official_canonicalization_pairs_select_the_same_number_bundle() -> None:
    # Source URL, revision, retrieval date and digest are in tests/upstream/MANIFEST.json.
    source = read_upstream("localeCanonicalization.txt").decode("utf-8")
    mismatches = []
    count = 0
    for line in source.splitlines():
        fields = line.split("#", 1)[0].strip()
        if not fields:
            continue
        original, canonical = (part.strip() for part in fields.split(";"))
        count += 1
        if _outcome(original) != _outcome(canonical):
            mismatches.append((original, canonical, _outcome(original), _outcome(canonical)))
    assert count == 1773
    assert mismatches == []


@pytest.mark.parametrize("tag", ["hye-arevmda", "HYE_AREVMDA", "arm-arevmda-fonipa"])
def test_language_aliases_cannot_discard_an_unsupported_language_variant(tag: str) -> None:
    # Handwritten cases combining the simple and compound alias rules.
    for call in (resolve_locale, number_symbols):
        with pytest.raises(LookupError):
            call(tag)
    with pytest.raises(LookupError):
        format_number(12345, tag)
    with pytest.raises(LookupError):
        parse_number("12345", tag)


@pytest.mark.parametrize("tag", ["aar-saaho", "AAR_SAAHO", "aar-fonipa-saaho"])
def test_a_simple_language_alias_exposes_a_specific_compound_alias(tag: str) -> None:
    assert resolve_locale(tag) == "ssy"


@pytest.mark.parametrize("tag", ["sh@cyrillic", "hbs@cyrillic", "SH@CYRILLIC"])
def test_posix_script_modifiers_still_override_simple_alias_defaults(tag: str) -> None:
    assert resolve_locale(tag) == "sr-Cyrl"
    assert resolve_locale("sh-Latn@cyrillic") == "sr-Latn"
    assert resolve_locale("zh-cmn-Hant@latin") == "zh-Hant"


@pytest.mark.parametrize("tag", ["el-polytoni", "EL_POLYTONI", "el-Grek-polytoni"])
def test_variant_aliases_select_the_canonical_bundle(tag: str) -> None:
    assert resolve_locale(tag) == "el-polyton"
    assert number_symbols(tag).locale == "el-polyton"


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("be-fonipa-tarask", "be-tarask"),
        ("be-Cyrl-tarask-fonipa", "be-tarask"),
        ("ca-ES-fonipa-valencia", "ca-ES-valencia"),
        ("ca-Latn-ES-valencia-fonipa", "ca-ES-valencia"),
        ("el-fonipa-polyton", "el-polyton"),
        ("el-Grek-polytoni-fonipa", "el-polyton"),
    ],
)
def test_supported_variant_subsets_precede_the_base_bundle(tag: str, expected: str) -> None:
    assert resolve_locale(tag) == expected
    assert number_symbols(tag).locale == expected


def test_variant_subset_lookup_does_not_enumerate_all_combinations() -> None:
    variants = "-".join(f"v{index:04d}" for index in range(1000))
    assert resolve_locale(f"be-{variants}-tarask") == "be-tarask"
