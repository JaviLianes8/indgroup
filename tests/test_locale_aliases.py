"""Locale tags CLDR rewrites before the lookup: aliases of several subtags, aliases that carry a
region, extended language subtags, likely scripts without data and the order of the fields.

The aliases come from languageAlias in supplemental/aliases.json of the CLDR 48.2.0 JSON
(cldr-core); the expected locales are what the shipped table holds for each replacement.
"""

from __future__ import annotations

from decimal import Decimal

import pytest

from indgroup import format_number, resolve_locale

VALUE = Decimal("-1234567.5")


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("zh-yue", "yue"),
        ("zh-yue-HK", "yue"),
        ("ZH_YUE_hk", "yue"),
        ("zh-cmn", "zh"),
        ("zh-cmn-Hans", "zh-Hans"),
        ("zh-cmn-Hant", "zh-Hant"),
        ("zh-cmn-Hans-SG", "zh-Hans-SG"),
        ("zh-guoyu", "zh"),
        ("no-bok", "nb"),
        ("no-nyn", "nn"),
        ("no-bokmal", "nb"),
        ("no-nynorsk", "nn"),
        ("i-lux", "lb"),
        ("art-lojban", "jbo"),
        ("i-default", "en"),
        ("sv-aaland", "sv-AX"),
        ("sv-FI-aaland", "sv-FI"),
        ("en-GB-oed", "en-GB"),
        ("zh-yue-u-nu-latn", "yue"),
    ],
)
def test_aliases_of_several_subtags_read_their_replacement(tag: str, expected: str) -> None:
    assert resolve_locale(tag) == expected
    assert format_number(VALUE, tag) == format_number(VALUE, expected)


@pytest.mark.parametrize(
    "tag", ["hy-arevmda", "zh-hakka", "zh-xiang", "zh-min-nan", "i-klingon", "sgn-BR", "sgn-BE-FR"]
)
def test_an_alias_to_a_language_without_data_is_a_lookup_error(tag: str) -> None:
    # hy-arevmda is Western Armenian (hyw), zh-hakka Hakka (hak): neither has number data,
    # so neither may read Armenian or Chinese symbols.
    with pytest.raises(LookupError):
        resolve_locale(tag)


def test_a_replacement_of_und_names_the_root_and_the_tag_keeps_its_fields() -> None:
    # i-enochian is und-x-i-enochian: the root, not the language "i".
    assert resolve_locale("i-enochian") == "und"
    # The replacement's script and region fill only what the tag leaves empty.
    assert resolve_locale("zh-cmn-Hant-Hans") == "zh-Hant"
    assert resolve_locale("zh-cmn-Hant-SG") == resolve_locale("zh-Hant-SG")


def test_an_alias_inside_an_extension_is_not_applied() -> None:
    assert resolve_locale("zh-x-yue") == "zh"
    assert resolve_locale("hy-x-arevmda") == "hy"


@pytest.mark.parametrize("tag", ["en-abc", "zh-abc-HK", "ar-aao", "en-abc-US"])
def test_other_extended_language_subtags_are_value_errors(tag: str) -> None:
    with pytest.raises(ValueError, match="extended language subtags are not supported"):
        resolve_locale(tag)


def test_a_three_letter_subtag_after_the_script_is_an_unchecked_variant() -> None:
    assert resolve_locale("en-Latn-abc") == "en"


@pytest.mark.parametrize(
    ("tag", "expected", "text"),
    [
        ("swc-KE", "sw-KE", "-1,234,567.5"),
        ("swc", "sw-CD", "-1.234.567,5"),
        ("prs-IR", "fa", chr(0x200E) + chr(0x2212) + "1,234,567.5"),
        ("cnr-BA", "sr-Cyrl-BA", "-1.234.567,5"),
        ("cnr", "sr-Latn-ME", "-1.234.567,5"),
    ],
)
def test_the_region_of_the_tag_wins_over_the_region_of_an_alias(
    tag: str, expected: str, text: str
) -> None:
    assert resolve_locale(tag) == expected
    assert format_number(VALUE, tag) == text


@pytest.mark.parametrize(
    ("short", "maximal"),
    [
        ("ku-GE", "ku-Cyrl-GE"),
        ("ku-AM", "ku-Cyrl-AM"),
        ("ku-AZ", "ku-Cyrl-AZ"),
        ("ku-TM", "ku-Cyrl-TM"),
        ("ky-CN", "ky-Arab-CN"),
        ("ky-TR", "ky-Latn-TR"),
        ("tg-PK", "tg-Arab-PK"),
        ("ug-KZ", "ug-Cyrl-KZ"),
        ("ug-MN", "ug-Cyrl-MN"),
        ("lzz-GE", "lzz-Geor-GE"),
    ],
)
def test_a_tag_reads_what_its_likely_script_reads_even_without_data(
    short: str, maximal: str
) -> None:
    # CLDR 48 likelySubtags adds the script; ku-Cyrl, ky-Arab, ky-Latn, tg-Arab, ug-Cyrl and
    # lzz-Geor have no data and are not the language's likely script, so the nonlikelyScript
    # rule gives the root.
    assert resolve_locale(short) == resolve_locale(maximal) == "und"
    assert format_number(VALUE, short) == format_number(VALUE, maximal) == "-1,234,567.5"


@pytest.mark.parametrize(
    ("tag", "expected"),
    [("uz-Arab@latin", "uz-Arab"), ("sr-Cyrl@latin", "sr-Cyrl"), ("hi-Latn@devanagari", "hi-Latn")],
)
def test_an_explicit_script_wins_over_a_posix_modifier(tag: str, expected: str) -> None:
    assert resolve_locale(tag) == expected
    assert format_number(VALUE, tag) == format_number(VALUE, expected)
    assert resolve_locale("uz@latin") == "uz-Latn" and resolve_locale("uz_AF@cyrillic") == "uz-Cyrl"


@pytest.mark.parametrize(
    "tag",
    [
        "en-Latn-US-abcdefghi",
        "en-US-1996-",
        "en-US-x-abcdefghij",
        "en-US-1996-abcdefghi",
        "en-US-u-nu-",
        "de-CH-1996-fonipa-abcdefghi",
        "en-Latn-US-1996-",
    ],
)
def test_a_bad_subtag_late_in_the_tag_is_a_value_error(tag: str) -> None:
    with pytest.raises(ValueError, match="not a locale tag"):
        resolve_locale(tag)
    with pytest.raises(ValueError, match="not a locale tag"):
        format_number(1234567, tag)
