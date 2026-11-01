"""Handwritten strict grammar cases for whitespace group separators."""

from __future__ import annotations

from decimal import Decimal

import pytest

from indgroup import format_indian, parse_indian


@pytest.mark.parametrize("separator", list(" \t\r\n"))
@pytest.mark.parametrize("edges", ["left", "right", "both"])
@pytest.mark.parametrize("text", ["1", "1{sep}000", "-1{sep}000.50", "+1{sep}000.50"])
def test_boundary_group_separators_are_never_padding(separator: str, edges: str, text: str) -> None:
    raw = text.format(sep=separator)
    if edges in ("left", "both"):
        raw = separator + raw
    if edges in ("right", "both"):
        raw += separator
    with pytest.raises(ValueError):
        parse_indian(raw, separator=separator)


@pytest.mark.parametrize("separator", list(" \t\r\n"))
def test_other_ascii_padding_surrounds_a_whitespace_grouped_value(separator: str) -> None:
    padding = " \t\r\n".replace(separator, "")
    value = Decimal("-1234.50")
    text = format_indian(value, separator=separator)
    parsed = parse_indian(padding + text + padding, separator=separator)
    assert parsed == value
    assert str(parsed) == "-1234.50"
