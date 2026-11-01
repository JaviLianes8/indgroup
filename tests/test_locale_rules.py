"""Locale tags: CLDR's parent rules, deprecated regions, case, and the edges of the syntax."""

from __future__ import annotations

from decimal import Decimal

import pytest

from indgroup import format_number, resolve_locale

# UTS #35 rev. 76, "Parent Locales" (https://www.unicode.org/reports/tr35/tr35-76/tr35.html):
# localeRules="nonlikelyScript" makes the root the parent of every lang_Script whose script
# is not the likely script of lang. The spec's own example is ru_Latn; the others follow
# from likelySubtags.json of CLDR 48 (ru, de and fr are Latin or Cyrillic, hi Devanagari).
NONLIKELY = ["ru-Latn", "ru-Latn-RU", "hi-Arab", "de-Cyrl", "fr-Arab", "en-Arab", "ml-Arab"]


@pytest.mark.parametrize("tag", NONLIKELY)
def test_a_script_other_than_the_likely_one_falls_back_to_the_root(tag: str) -> None:
    assert resolve_locale(tag) == "und"
    assert format_number(Decimal("-1234567.5"), tag) == "-1,234,567.5"


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("ru-Cyrl", "ru"),
        ("ru-Cyrl-UA", "ru-UA"),
        ("de-Latn-CH", "de-CH"),
        ("zh-Hans-TW", "zh"),
        ("hi-Latn-IN", "hi-Latn"),
        ("ca-Latn-ES-valencia", "ca-ES-valencia"),
        ("ku-Latn-GE", "ku"),
    ],
)
def test_the_likely_script_and_the_explicit_parents_keep_their_data(
    tag: str, expected: str
) -> None:
    assert resolve_locale(tag) == expected


def test_an_unknown_language_in_any_script_is_still_a_lookup_error() -> None:
    for tag in ["xx-Latn", "qaa-Cyrl-RU"]:
        with pytest.raises(LookupError):
            resolve_locale(tag)


# UTS #35 rev. 76, Annex C, "Territory Exception": a region code with several replacements
# becomes the likely region of the language (and script) when listed, else the first one.
# Intl.NumberFormat of Node 24.18 resolves every tag below to the same locale.
@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("en-200", "en-CZ"),
        ("ar-NT", "ar-SA"),
        ("kk-SU", "kk-KZ"),
        ("nl-AN", "nl-CW"),
        ("en-830", "en-JE"),
        ("en-PC", "en-FM"),
        ("sr-Latn-YU", "sr-Latn"),
    ],
)
def test_a_region_with_several_replacements_takes_the_likely_one(tag: str, expected: str) -> None:
    assert resolve_locale(tag) == expected


def test_czechoslovakia_reads_czech_english_data() -> None:
    assert format_number(Decimal("-1234567.5"), "en-200") == "-1\xa0234\xa0567,5"


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("sr_RS@LATIN", "sr-Latn"),
        ("sr_RS@Latin", "sr-Latn"),
        ("ROOT", "und"),
        ("Root", "und"),
        ("ca-ES-VALENCIA", "ca-ES-valencia"),
        ("zh-hant-TW", "zh-Hant"),
        ("ZH-HANT-tw", "zh-Hant"),
        ("SR-latn-me", "sr-Latn-ME"),
    ],
)
def test_every_subtag_is_read_in_any_case(tag: str, expected: str) -> None:
    assert resolve_locale(tag) == expected


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("ca-ES-x-valencia", "ca"),
        ("ca-ES-u-va-valencia", "ca"),
        ("de-CH-x-1996-u-nu-arab", "de-CH"),
    ],
)
def test_subtags_after_an_extension_or_private_use_are_not_variants(
    tag: str, expected: str
) -> None:
    assert resolve_locale(tag) == expected


@pytest.mark.parametrize(
    ("tag", "expected"),
    [("de-756", "de-CH"), ("fr-756", "fr-CH"), ("en-826", "en-GB"), ("es-484", "es-MX")],
)
def test_numeric_regions_are_regions(tag: str, expected: str) -> None:
    assert resolve_locale(tag) == expected


def test_a_numeric_region_reads_that_region_data() -> None:
    assert format_number(1234567, "de-756") == "1'234'567"


@pytest.mark.parametrize(
    "tag", ["abcd", "a", "abcdefghi", "de-CH-abcdefghi", "de-abcdefghi", "en-US-", "-en"]
)
def test_subtags_of_the_wrong_length_are_value_errors(tag: str) -> None:
    # RFC 5646 reserves four-letter language subtags; none has number data or a meaning.
    with pytest.raises(ValueError) as raised:
        resolve_locale(tag)
    assert type(raised.value) is ValueError


def test_subtags_after_the_region_are_not_held_to_the_variant_grammar() -> None:
    # GUIDE: subtags after the region are not held to the variant grammar of BCP 47.
    assert resolve_locale("en-US-abcd") == "en"
    assert resolve_locale("de-AT-abcd") == "de-AT"
