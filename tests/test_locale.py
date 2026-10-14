from __future__ import annotations

import pytest

from indgroup import cldr_version, resolve_locale, supported_locales


def test_the_table_comes_from_cldr_48() -> None:
    assert cldr_version() == "48.0.0"
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


def test_every_supported_locale_resolves_to_itself() -> None:
    for locale in supported_locales():
        assert resolve_locale(locale) == locale


def test_unknown_language_is_an_error() -> None:
    with pytest.raises(LookupError):
        resolve_locale("xx")


@pytest.mark.parametrize("tag", ["", "e", "en--US", "en-US!", "zh-cmn-Hant", "123"])
def test_malformed_tags_are_rejected(tag: str) -> None:
    with pytest.raises(ValueError):
        resolve_locale(tag)


def test_a_non_string_locale_is_a_type_error() -> None:
    with pytest.raises(TypeError):
        resolve_locale(None)  # type: ignore[arg-type]
