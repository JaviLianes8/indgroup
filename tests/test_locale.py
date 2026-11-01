from __future__ import annotations

from decimal import Decimal

import pytest

from indgroup import (
    cldr_version,
    format_number,
    number_symbols,
    parse_number,
    resolve_locale,
    supported_locales,
)


def test_the_table_comes_from_cldr_48_2() -> None:
    assert cldr_version() == "48.2.0"
    locales = supported_locales()
    assert len(locales) == 766
    assert list(locales) == sorted(locales)
    assert {"und", "en", "en-IN", "hi", "fr-CH", "es-419", "zh-Hant"} <= set(locales)


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("en-IN", "en-IN"),
        ("EN_in", "en-IN"),
        ("pt_BR.UTF-8", "pt"),
        ("pt-FR", "pt-PT"),
        ("es-MX", "es-MX"),
        ("es-CO", "es-CO"),
        ("de-AT-1996", "de-AT"),
        ("de-CH-u-co-phonebk", "de-CH"),
        ("zh-TW", "zh-Hant"),
        ("zh-SG", "zh-Hans-SG"),
        ("sr-ME", "sr-Latn-ME"),
        ("sr_RS@latin", "sr-Latn"),
        ("iw", "he"),
        ("sh", "sr-Latn"),
        ("en-UK", "en-GB"),
        ("en-Latn-GB", "en-GB"),
        ("root", "und"),
        ("und", "und"),
    ],
)
def test_resolves_like_icu(tag: str, expected: str) -> None:
    assert resolve_locale(tag) == expected


def test_swiss_french_groups_with_an_apostrophe_since_cldr_48_2() -> None:
    # CLDR 48.2.0 gave fr_CH a group symbol of its own (fr_CH.xml, release-48-2); 48.0.0
    # inherited the narrow no-break space of fr. ICU 78.3, and so Node 24.18, has it too.
    assert number_symbols("fr-CH").group == "'"
    assert format_number(1234567.89, "fr-CH") == "1'234'567,89"
    assert parse_number("1'234'567,89", "fr-CH") == Decimal("1234567.89")
    assert number_symbols("fr").group == chr(0x202F)


def test_every_supported_locale_resolves_to_itself() -> None:
    for locale in supported_locales():
        assert resolve_locale(locale) == locale


def test_unknown_language_is_an_error() -> None:
    with pytest.raises(LookupError):
        resolve_locale("xx")


@pytest.mark.parametrize("tag", ["", "e", "en--US", "en-US!", "en-abc", "123"])
def test_malformed_tags_are_rejected(tag: str) -> None:
    with pytest.raises(ValueError):
        resolve_locale(tag)


def test_a_non_string_locale_is_a_type_error() -> None:
    with pytest.raises(TypeError):
        resolve_locale(None)  # type: ignore[arg-type]
