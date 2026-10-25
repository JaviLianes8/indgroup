from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

UPSTREAM = Path(__file__).resolve().parent / "upstream"


def read_upstream(name: str) -> bytes:
    """Return a third-party reference file.

    The files are not committed: `python scripts/fetch_upstream.py` fetches them. Their
    tests skip while a file is absent and fail if it differs from the manifest.
    """
    path = UPSTREAM / name
    if not path.is_file():
        pytest.skip(f"{name} is not fetched; run python scripts/fetch_upstream.py")
    entry = json.loads((UPSTREAM / "MANIFEST.json").read_text(encoding="utf-8"))[name]
    body = path.read_bytes()
    assert hashlib.sha256(body).hexdigest() == entry["sha256"], f"{name} differs from MANIFEST"
    return body


def upstream_json(name: str) -> Any:
    return json.loads(read_upstream(name).decode("utf-8"))


# ICU's own data writes an apostrophe for Swiss French; the CLDR 48 JSON has no group of
# its own for fr-CH and inherits the narrow no-break space of fr. CLDR wins here.
KNOWN_ICU_DIFFERENCES = {"fr-CH": ("'", chr(0x202F))}


def intl_comparable(tag: str, resolved: str | None) -> bool:
    """Whether Intl formatted ``tag`` with the locale this library reads for it.

    ICU ships fewer locales than CLDR: where Intl falls back to another locale (its resolved
    locale is neither the requested tag nor the CLDR locale this library resolves to), the
    case says nothing about this library and is left out.
    """
    from indgroup import resolve_locale

    if resolved is None:
        return False
    plain = tag.lower().split("-u-")[0]
    try:
        ours = resolve_locale(tag).lower()
    except LookupError:
        return False
    return resolved.lower() in (plain, ours)
