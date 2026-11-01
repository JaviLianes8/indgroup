"""The number table shipped with the package, derived from Unicode CLDR."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any

__all__ = ["table"]


@lru_cache(maxsize=1)
def table() -> dict[str, Any]:
    """The number table shipped with the package (see scripts/build_table.py)."""
    text = files("indgroup").joinpath("_cldr.json").read_text(encoding="ascii")
    loaded: dict[str, Any] = json.loads(text)
    return loaded
