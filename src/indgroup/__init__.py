"""Format and parse integers and decimals in the Indian lakh and crore digit grouping."""

from __future__ import annotations

from ._grouping import format_indian, parse_indian

__version__ = "0.1.0"

__all__ = ["format_indian", "parse_indian"]
