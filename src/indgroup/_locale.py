"""Locale lookup in the number table derived from Unicode CLDR."""

from __future__ import annotations

from ._table import table
from ._tag import parse_tag
from ._value import shown

__all__ = ["cldr_version", "resolve_locale", "supported_locales"]


def cldr_version() -> str:
    """The CLDR release the number table was derived from.

    >>> cldr_version()
    '48.2.0'
    """
    return str(table()["cldr"])


def supported_locales() -> tuple[str, ...]:
    """Every CLDR locale with number data, sorted; ``und`` is the root locale.

    >>> locales = supported_locales()
    >>> len(locales), "en-IN" in locales, "und" in locales
    (766, True, True)
    """
    return tuple(sorted(table()["locales"]))


def _parent(tag: str) -> str:
    """The CLDR parent of a locale without data; the empty string past the language."""
    data = table()
    parent = data["parents"].get(tag)  # CLDR JSON names the root locale "und"
    if parent is not None:
        return str(parent)
    # CLDR's nonlikelyScript rule: "ru-Latn" falls back to the root, never to "ru".
    language, _, script = tag.partition("-")
    likely = data["scripts"].get(language)
    if likely is not None and len(script) == 4 and script.isalpha() and script != likely:
        return "und"
    return tag.rpartition("-")[0]


def _walk(tag: str) -> str | None:
    """The first locale with data on the CLDR fallback chain of ``tag``."""
    locales = table()["locales"]
    while tag:
        if tag in locales:
            return tag
        tag = _parent(tag)
    return None


def resolve_locale(locale: str) -> str:
    """The CLDR locale whose number symbols ``locale`` uses.

    Accepts BCP 47 (``pt-BR``) and POSIX (``pt_BR.UTF-8``, ``sr_RS@latin``) spellings in any
    case; a script in the tag wins over a POSIX modifier. Deprecated codes are replaced
    (``iw`` is ``he``, ``sh`` is ``sr-Latn``, ``UK`` is ``GB``, ``200`` is ``CZ`` or ``SK``), so
    are CLDR's legacy tags of several subtags (``zh-yue`` is ``yue``, ``no-bok`` is ``nb``,
    ``i-lux`` is ``lb``), and the likely script is added where a region's differs from the
    language's (``zh-TW`` is ``zh-Hant-TW``, ``ku-GE`` is ``ku-Cyrl-GE``). A locale without
    data of its own falls back through the CLDR parent locales, then by dropping subtags
    (``pt-FR`` reads ``pt-PT``, ``de-AT-1996`` reads ``de-AT``); a language in a script other
    than its likely one falls back to the root (``ru-Latn`` and ``ku-Cyrl-GE`` read ``und``),
    as CLDR's nonlikelyScript rule says. ``und`` and ``root`` name the root locale.

    Raises ``LookupError`` when no language with data is reached, so an unknown language
    never reads another language's symbols silently (``hy-arevmda``, Western Armenian, has
    none); ``TypeError`` for a non-``str``; and ``ValueError`` for text that is not a tag: an
    empty subtag, one longer than eight characters or not made of ASCII letters and digits,
    a language subtag that is not two, three or five to eight letters, or a three-letter
    extended language subtag CLDR does not replace (``en-abc``, ``be-abc-aaland``, where the
    legacy rule removes only ``aaland``). Subtags after the script or
    region are read as variants without checking their grammar (``en-Latn-abc`` reads ``en``).

    >>> resolve_locale("pt_BR.UTF-8"), resolve_locale("zh-TW"), resolve_locale("iw")
    ('pt', 'zh-Hant', 'he')
    >>> resolve_locale("pt-FR")
    'pt-PT'
    >>> resolve_locale("xx")
    Traceback (most recent call last):
    ...
    LookupError: no number data for locale 'xx'
    """
    language, script, region, variants = parse_tag(locale)
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
        if variants and f"{base}-{'-'.join(variants)}" in data["locales"]:
            return f"{base}-{'-'.join(variants)}"
    elif not script and default:
        likely = data["scripts"].get(f"{language}-{region}", default)
        tagged = "-".join(part for part in (language, likely, region) if part)
        if likely != default:
            # As its full form does: "ku-GE" is "ku-Cyrl-GE", which reads the root.
            found = _walk(tagged)
        elif tagged in data["locales"]:
            found = tagged
    found = found or _walk(base)
    if found is None:
        raise LookupError(f"no number data for locale {shown(locale)}")
    return found
