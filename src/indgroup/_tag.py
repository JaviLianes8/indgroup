"""Reading a locale tag into the language, script, region and variants CLDR canonicalizes it to."""

from __future__ import annotations

import re
from functools import lru_cache

from ._table import table
from ._value import shown

__all__ = ["parse_tag"]

_SUBTAG = re.compile(r"[A-Za-z0-9]{1,8}")
_LANGUAGE = re.compile(r"[A-Za-z]{2,3}|[A-Za-z]{5,8}")

# glibc locale modifiers that name a script, as in "sr_RS@latin"; others such as "@euro"
# do not affect number symbols.
_MODIFIERS = {"latin": "Latn", "cyrillic": "Cyrl", "devanagari": "Deva"}

Rules = dict[str, list[tuple[frozenset[str], list[str]]]]


def _is_script(part: str) -> bool:
    return len(part) == 4 and part.isalpha()


def _is_region(part: str) -> bool:
    return (len(part) == 2 and part.isalpha()) or (len(part) == 3 and part.isdigit())


@lru_cache(maxsize=1)
def _rules() -> Rules:
    """CLDR's language aliases of several subtags, by their first subtag, the longest first."""
    tags: dict[str, str] = table()["tags"]
    rules: Rules = {}
    for key in sorted(tags, key=lambda key: (-key.count("-"), key)):
        first, *rest = key.split("-")
        rules.setdefault(first, []).append((frozenset(rest), tags[key].split("-")))
    return rules


def _legacy(subtags: list[str]) -> list[str]:
    """``subtags`` with CLDR's language aliases of several subtags applied.

    A rule matches when its first subtag is the language (``und`` matches any) and its other
    subtags all stand before the first extension. They are removed; the replacement's
    language takes the place of the tag's, and its script and region fill only what the tag
    leaves empty: ``zh-yue-HK`` is ``yue-HK``, ``sv-aaland`` is ``sv-AX``, ``sv-FI-aaland``
    is ``sv-FI``.
    """
    for _ in range(4):  # a replacement never matches a further rule; this is a guard
        lowered = [part.lower() for part in subtags]
        end = next((at for at in range(1, len(lowered)) if len(lowered[at]) == 1), len(lowered))
        present = set(lowered[1:end])
        found = [
            (first, need, replacement)
            for first in dict.fromkeys((lowered[0], "und"))
            for need, replacement in _rules().get(first, ())
            if need <= present
        ]
        if not found:
            break
        first, need, (language, *extra) = found[0]
        if language == "und" and first == "und":
            language = subtags[0]
        rest = [part for part in subtags[1:end] if part.lower() not in need]
        script = rest.pop(0) if rest and _is_script(rest[0]) else ""
        region = rest.pop(0) if rest and _is_region(rest[0]) else ""
        variants = []
        for part in extra:
            if _is_script(part):
                script = script or part
            elif _is_region(part):
                region = region or part
            else:
                variants.append(part)
        fields = [part for part in (script, region) if part]
        subtags = [language, *fields, *variants, *rest, *subtags[end:]]
    return subtags


def parse_tag(locale: str) -> tuple[str, str, str, list[str]]:
    """Language, script, region (empty when absent) and variants of a locale tag."""
    if not isinstance(locale, str):
        raise TypeError(f"locale must be a str, not {type(locale).__name__}")
    tag, _, modifier = str.__str__(locale).partition("@")
    subtags = tag.split(".", 1)[0].replace("_", "-").split("-")  # POSIX "es_ES.UTF-8"
    if not all(_SUBTAG.fullmatch(part) for part in subtags):
        raise ValueError(f"not a locale tag: {shown(locale)}")
    subtags = _legacy(subtags)
    if subtags[0].lower() == "root":
        subtags[0] = "und"
    if not _LANGUAGE.fullmatch(subtags[0]):
        raise ValueError(f"not a locale tag: {shown(locale)}")
    rest = subtags[1:]
    if rest and len(rest[0]) == 3 and rest[0].isalpha():
        raise ValueError(f"extended language subtags are not supported: {shown(locale)}")
    script = rest.pop(0).title() if rest and _is_script(rest[0]) else ""
    script = script or _MODIFIERS.get(modifier.lower(), "")  # a script in the tag wins
    region = rest.pop(0).upper() if rest and _is_region(rest[0]) else ""
    variants = []
    for part in rest:
        if len(part) == 1:  # extensions and private use do not select number data
            break
        variants.append(part.lower())
    alias = table()["aliases"].get(subtags[0].lower(), subtags[0].lower()).split("-")
    for extra in alias[1:]:
        if len(extra) == 4:
            script = script or extra
        else:
            region = region or extra  # a region in the tag wins: "swc-KE" is "sw-KE"
    return alias[0], script, _region(alias[0], script, region), variants


def _region(language: str, script: str, region: str) -> str:
    """``region`` with a deprecated code replaced, as UTS #35 canonicalization does.

    A code with several replacements (``SU``, ``200``) becomes the likely region of the
    language and script when it is one of them, else the first one listed.
    """
    regions: dict[str, str] = table()["regions"]
    choices = regions.get(region, region).split(" ")
    if len(choices) == 1:
        return choices[0]
    homes: dict[str, str] = table()["homes"]
    home = homes.get(f"{language}-{script}") or homes.get(language)
    return home if home in choices else choices[0]
