"""Reading a locale tag into the language, script, region and variants CLDR canonicalizes it to."""

from __future__ import annotations

import re
from functools import lru_cache

from ._table import table
from ._value import input_size

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
    """Simple, compound and variant aliases, indexed by their first subtag."""
    tags: dict[str, str] = {
        **table()["aliases"],
        **table()["tags"],
        **{f"und-{key}": f"und-{value}" for key, value in table()["variants"].items()},
    }
    rules: Rules = {}
    for key in sorted(tags, key=lambda key: (-key.count("-"), key)):
        first, *rest = key.split("-")
        rules.setdefault(first, []).append((frozenset(rest), tags[key].split("-")))
    return rules


def _priority(
    first: str, need: frozenset[str]
) -> tuple[int, bool, bool, bool, bool, str, tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    # UTS #35 Annex C: most fields first, then presence of L/S/R/V, then code-point order.
    script = tuple(sorted(part for part in need if _is_script(part)))
    region = tuple(sorted(part for part in need if _is_region(part)))
    variants = tuple(sorted(need.difference(script, region)))
    return (
        -(len(need) + (first != "und")),
        first == "und",
        not script,
        not region,
        not variants,
        first,
        script,
        region,
        variants,
    )


def _legacy(subtags: list[str], modifier: str) -> list[str]:
    """``subtags`` with CLDR's language aliases of several subtags applied.

    A rule matches when its first subtag is the language (``und`` matches any) and its other
    subtags all stand before the first extension. Every occurrence of them is removed and the
    replacement's language takes the place of the tag's. What the tag has left is read as a
    tag: its own extended language, script and region stay first, a variant or a subtag with a
    digit is neither an extended language nor a script, the replacements' script and region
    fill only what it leaves empty and their variants follow its own: ``zh-yue-HK`` is
    ``yue-HK``, ``sv-aaland`` is ``sv-AX``, ``sv-FI-aaland`` is ``sv-FI``, ``be-arevela-Latn``
    is ``be-Latn`` and ``be-abc-aaland`` is ``be-abc-AX``, which ``parse_tag`` refuses. As in
    UTS #35, the rules apply until none matches, so a replacement can match a further rule:
    ``zh-cmn-yue`` is ``zh-yue``, then ``yue``. Since the tag's own subtags and the
    replacements' are kept apart until the end, a chain of rules reads like one rule.
    """
    end = next((at for at in range(1, len(subtags)) if len(subtags[at]) == 1), len(subtags))
    language, own = subtags[0], subtags[1:end]
    added: list[str] = []  # the replacements' subtags after their language
    # Each rule changes the language or consumes matched subtags; CLDR's aliases are acyclic.
    data = table()
    for _ in range(len(data["aliases"]) + len(data["tags"]) + len(data["variants"]) + 1):
        present = {part.lower() for part in (*own, *added)}
        found = [
            (first, need, replacement)
            for first in dict.fromkeys((language.lower(), "und"))
            for need, replacement in _rules().get(first, ())
            if need <= present
        ]
        if not found:
            break
        first, need, (replaced, *extra) = min(found, key=lambda rule: _priority(rule[0], rule[1]))
        if replaced != "und" or first != "und":
            language = replaced
        if not need and modifier:
            # A POSIX modifier overrides a simple alias's default script, as before.
            extra = [part for part in extra if not _is_script(part)]
        own = [part for part in own if part.lower() not in need]
        added = [part for part in added if part.lower() not in need] + extra
    extended = [own.pop(0)] if own and len(own[0]) == 3 and own[0].isalpha() else []
    script = own.pop(0) if own and _is_script(own[0]) else ""
    region = own.pop(0) if own and _is_region(own[0]) else ""
    variants = []
    for part in added:
        if _is_script(part):
            script = script or part
        elif _is_region(part):
            region = region or part
        else:
            variants.append(part)
    fields = [part for part in (script, region) if part]
    return [language, *extended, *fields, *own, *variants, *subtags[end:]]


def parse_tag(locale: str) -> tuple[str, str, str, list[str]]:
    """Language, script, region (empty when absent) and variants of a locale tag."""
    if not issubclass(type(locale), str):
        raise TypeError("locale must be a str")
    tag, _, modifier = str.__str__(locale).partition("@")
    subtags = tag.split(".", 1)[0].replace("_", "-").split("-")  # POSIX "es_ES.UTF-8"
    if not all(_SUBTAG.fullmatch(part) for part in subtags):
        raise ValueError(f"not a locale tag: {input_size(locale)}")
    modifier_script = _MODIFIERS.get(modifier.lower(), "")
    subtags = _legacy(subtags, modifier_script)
    if subtags[0].lower() == "root":
        subtags[0] = "und"
    if not _LANGUAGE.fullmatch(subtags[0]):
        raise ValueError(f"not a locale tag: {input_size(locale)}")
    rest = subtags[1:]
    if rest and len(rest[0]) == 3 and rest[0].isalpha():
        raise ValueError(f"extended language subtags are not supported: {input_size(locale)}")
    script = rest.pop(0).title() if rest and _is_script(rest[0]) else ""
    script = script or modifier_script  # a script in the tag wins
    region = rest.pop(0).upper() if rest and _is_region(rest[0]) else ""
    variants = []
    for part in rest:
        if len(part) == 1:  # extensions and private use do not select number data
            break
        variants.append(part.lower())
    language = subtags[0].lower()
    return language, script, _region(language, script, region), variants


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
