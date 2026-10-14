"""Derive the package number table, src/indgroup/_cldr.json, from the CLDR JSON packages.

The CLDR packages are fetched into tests/upstream by scripts/fetch_upstream.py and are not
part of the repository. The table keeps only facts: for every locale the Latin-digit decimal,
group and minus symbols, the grouping sizes of the standard decimal pattern and the minimum
grouping digits; plus the parent locales, the likely script of a language and region where
a language has several, and the language and region codes CLDR replaces.

    python scripts/build_table.py
"""

from __future__ import annotations

import json
import re
import sys
import tarfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
UPSTREAM = ROOT / "tests" / "upstream"
TARGET = ROOT / "src" / "indgroup" / "_cldr.json"
VERSION = "48.0.0"

LANGUAGE = re.compile(r"[a-z]{2,3}")
REGION = re.compile(r"[A-Z]{2}|\d{3}")
TAG = re.compile(r"[a-z]{2,3}(-[A-Z][a-z]{3})?(-([A-Z]{2}|\d{3}))?")


def _members(path: Path) -> dict[str, Any]:
    """Every JSON member of a CLDR npm tarball, keyed by its path inside ``package/``."""
    found: dict[str, Any] = {}
    with tarfile.open(path) as archive:
        for member in archive.getmembers():
            if member.isfile() and member.name.endswith(".json"):
                handle = archive.extractfile(member)
                assert handle is not None
                found[member.name.removeprefix("package/")] = json.load(handle)
    return found


def grouping_sizes(pattern: str) -> tuple[int, int]:
    """Primary and secondary grouping sizes of a decimal pattern; (0, 0) when it has none.

    The primary size counts the digits after the last comma of the integer part, the
    secondary size those between the last two commas, defaulting to the primary size.
    """
    positive = pattern.split(";", 1)[0]
    integer = re.sub(r"[^#0-9,]", "", positive.split(".", 1)[0])
    groups = integer.split(",")
    if len(groups) < 2:
        return 0, 0
    primary = len(groups[-1])
    secondary = len(groups[-2]) if len(groups) > 2 else primary
    return primary, secondary


def derive(upstream: Path = UPSTREAM) -> dict[str, Any]:
    """The number table as a JSON-ready dict, derived from the two CLDR tarballs."""
    numbers = _members(upstream / f"cldr-numbers-full-{VERSION}.tgz")
    core = _members(upstream / f"cldr-core-{VERSION}.tgz")
    pool: dict[tuple[str, str, str, int, int, int], int] = {}
    locales: dict[str, int] = {}
    for name, body in sorted(numbers.items()):
        if not name.endswith("/numbers.json"):
            continue
        locale = name.split("/")[1]
        data = body["main"][locale]["numbers"]
        symbols = data["symbols-numberSystem-latn"]
        pattern = data["decimalFormats-numberSystem-latn"]["standard"]
        primary, secondary = grouping_sizes(pattern)
        row = (
            symbols["decimal"],
            symbols["group"],
            symbols["minusSign"],
            primary,
            secondary,
            int(data["minimumGroupingDigits"]),
        )
        locales[locale] = pool.setdefault(row, len(pool))
    supplemental = core["supplemental/parentLocales.json"]["supplemental"]["parentLocales"]
    likely = core["supplemental/likelySubtags.json"]["supplemental"]["likelySubtags"]
    aliases = core["supplemental/aliases.json"]["supplemental"]["metadata"]["alias"]
    return {
        "cldr": VERSION,
        "profiles": [list(row) for row in pool],
        "locales": locales,
        "parents": dict(sorted(supplemental["parentLocale"].items())),
        "scripts": _likely_scripts(locales, likely),
        "aliases": _language_aliases(locales, aliases["languageAlias"]),
        "regions": _region_aliases(aliases["territoryAlias"]),
    }


def _likely_scripts(locales: dict[str, int], likely: dict[str, str]) -> dict[str, str]:
    """The likely script of each language written in several, and of its regions that differ.

    Only languages with locales in more than one script need it: that is what makes
    ``zh-TW`` read the Traditional Chinese data and ``sr-ME`` reach ``sr-Latn-ME``.
    """
    multi = {name.split("-")[0] for name in locales if _script(name)}
    found: dict[str, str] = {}
    for key, value in sorted(likely.items()):
        parts = key.split("-")
        if parts[0] not in multi or not 1 <= len(parts) <= 2:
            continue
        if len(parts) == 2 and not REGION.fullmatch(parts[1]):
            continue
        default = likely.get(parts[0], "").split("-")
        script = value.split("-")[1]
        if len(parts) == 1 or (len(default) > 1 and script != default[1]):
            found[key] = script
    return found


def _script(name: str) -> bool:
    parts = name.split("-")
    return len(parts) > 1 and len(parts[1]) == 4


def _language_aliases(locales: dict[str, int], table: dict[str, Any]) -> dict[str, str]:
    """Language codes CLDR replaces, mapped to a replacement whose language has data."""
    languages = {name.split("-")[0] for name in locales}
    found: dict[str, str] = {}
    for key, entry in sorted(table.items()):
        target = entry["_replacement"]
        if LANGUAGE.fullmatch(key) and TAG.fullmatch(target) and target.split("-")[0] in languages:
            found[key] = target
    return found


def _region_aliases(table: dict[str, Any]) -> dict[str, str]:
    """Region codes CLDR replaces by exactly one other region (``UK`` is ``GB``)."""
    return {
        key: entry["_replacement"]
        for key, entry in sorted(table.items())
        if REGION.fullmatch(key) and REGION.fullmatch(entry["_replacement"])
    }


def render(table: dict[str, Any]) -> str:
    return json.dumps(table, ensure_ascii=True, separators=(",", ":"), sort_keys=True) + "\n"


def main() -> int:
    TARGET.write_text(render(derive()), encoding="ascii", newline="\n")
    print(f"wrote {TARGET.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
