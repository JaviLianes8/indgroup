"""Locale lookup in the number table derived from Unicode CLDR."""

from __future__ import annotations

import json
import re
from functools import lru_cache
from importlib.resources import files
from typing import Any

from ._value import shown

__all__ = ["cldr_version", "resolve_locale", "supported_locales", "table"]

_SUBTAG = re.compile(r"[A-Za-z0-9]{1,8}")
_LANGUAGE = re.compile(r"[A-Za-z]{2,3}|[A-Za-z]{5,8}")


@lru_cache(maxsize=1)
def table() -> dict[str, Any]:
    """The number table shipped with the package (see scripts/build_table.py)."""
    text = files("indgroup").joinpath("_cldr.json").read_text(encoding="ascii")
    loaded: dict[str, Any] = json.loads(text)
    return loaded


def cldr_version() -> str:
    """The CLDR release the number table was derived from.

    >>> cldr_version()
    '48.0.0'
    """
    return str(table()["cldr"])


def supported_locales() -> tuple[str, ...]:
    """Every CLDR locale with number data, sorted; ``und`` is the root locale.

    >>> locales = supported_locales()
    >>> len(locales), "en-IN" in locales, "und" in locales
    (766, True, True)
    """
    return tuple(sorted(table()["locales"]))


# glibc locale modifiers that name a script, as in "sr_RS@latin"; others such as "@euro"
# do not affect number symbols.
_MODIFIERS = {"latin": "Latn", "cyrillic": "Cyrl", "devanagari": "Deva"}


def _parse(locale: str) -> tuple[str, str, str, list[str]]:
    """Language, script, region (empty when absent) and variants of a locale tag."""
    if not isinstance(locale, str):
        raise TypeError(f"locale must be a str, not {type(locale).__name__}")
    tag, _, modifier = str.__str__(locale).partition("@")
    subtags = tag.split(".", 1)[0].replace("_", "-").split("-")  # POSIX "es_ES.UTF-8"
    if subtags[0].lower() == "root":
        subtags[0] = "und"
    if not all(_SUBTAG.fullmatch(part) for part in subtags) or not _LANGUAGE.fullmatch(subtags[0]):
        raise ValueError(f"not a locale tag: {shown(locale)}")
    rest = subtags[1:]
    if rest and len(rest[0]) == 3 and rest[0].isalpha():
        raise ValueError(f"extended language subtags are not supported: {shown(locale)}")
    script = rest.pop(0).title() if rest and len(rest[0]) == 4 and rest[0].isalpha() else ""
    script = script or _MODIFIERS.get(modifier.lower(), "")
    region = ""
    if rest and (
        (len(rest[0]) == 2 and rest[0].isalpha()) or (len(rest[0]) == 3 and rest[0].isdigit())
    ):
        region = rest.pop(0).upper()
    variants = []
    for part in rest:
        if len(part) == 1:  # extensions and private use do not select number data
            break
        variants.append(part.lower())
    data = table()
    region = data["regions"].get(region, region)
    alias = data["aliases"].get(subtags[0].lower(), subtags[0].lower()).split("-")
    for extra in alias[1:]:
        if len(extra) == 4:
            script = script or extra
        else:
            region = region or extra
    return alias[0], script, region, variants


def _walk(tag: str) -> str | None:
    """The first locale with data on the CLDR fallback chain of ``tag``."""
    data = table()
    while tag:
        if tag in data["locales"]:
            return tag
        parent = data["parents"].get(tag)  # CLDR JSON names the root locale "und"
        tag = parent if parent is not None else tag.rpartition("-")[0]
    return None


def resolve_locale(locale: str) -> str:
    """The CLDR locale whose number symbols ``locale`` uses.

    Accepts BCP 47 (``pt-BR``) and POSIX (``pt_BR.UTF-8``, ``sr_RS@latin``) spellings in any
    case. Deprecated codes are replaced (``iw`` is ``he``, ``sh`` is ``sr-Latn``, ``UK`` is
    ``GB``), and where a language is written in several scripts the likely one is added
    (``zh-TW`` is ``zh-Hant-TW``, ``zh-SG`` is ``zh-Hans-SG``). A locale without data of its
    own falls back through the CLDR parent locales, then by dropping subtags (``pt-FR`` reads
    ``pt-PT``, ``de-AT-1996`` reads ``de-AT``). ``und`` and ``root`` name the root locale.
    Raises ``LookupError`` when no language with data is reached, so an unknown language
    never reads another language's symbols silently, ``ValueError`` for text that is not a
    locale tag and ``TypeError`` for a non-``str``.

    >>> resolve_locale("pt_BR.UTF-8"), resolve_locale("zh-TW"), resolve_locale("iw")
    ('pt', 'zh-Hant', 'he')
    >>> resolve_locale("pt-FR")
    'pt-PT'
    >>> resolve_locale("xx")
    Traceback (most recent call last):
    ...
    LookupError: no number data for locale 'xx'
    """
    language, script, region, variants = _parse(locale)
    data = table()
    base = "-".join(part for part in (language, script, region) if part)
    if variants and f"{base}-{'-'.join(variants)}" in data["locales"]:
        return f"{base}-{'-'.join(variants)}"
    if base in data["locales"]:
        return base
    found = None
    default = data["scripts"].get(language)
    if script and script == default:  # "en-Latn-GB" is "en-GB": CLDR omits default scripts
        base = "-".join(part for part in (language, region) if part)
    elif not script and default:
        likely = data["scripts"].get(f"{language}-{region}", default)
        tagged = "-".join(part for part in (language, likely, region) if part)
        if likely != default:
            found = _walk(tagged)
        elif tagged in data["locales"]:
            found = tagged
    found = found or _walk(base)
    if found is None:
        raise LookupError(f"no number data for locale {shown(locale)}")
    return found
