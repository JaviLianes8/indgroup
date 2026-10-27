"""Chains of CLDR's legacy tag rules read the tag the rules leave, whatever their number or order.

A rule removes the subtags it matched. What the tag has left is read as a tag of its own, and
the replacements' script and region fill only what it leaves empty while their variants come
after its own. The rules are those of languageAlias in supplemental/aliases.json of the CLDR
48.2.0 JSON (cldr-core); the tags are written by hand.
"""

from __future__ import annotations

import itertools
from decimal import Decimal

import pytest

from indgroup import format_number, resolve_locale

VALUE = Decimal("-1234567.5")
RULES = ["aaland", "arevela", "hepburn-heploc", "bokmal", "gb-oed"]
UND = "hepburn-heploc-aaland-arevela-arevmda-bokmal-hakka-lojban-nynorsk-saaho-xiang"


def _read(tag: str) -> str:
    try:
        return f"{resolve_locale(tag)} {format_number(VALUE, tag)}"
    except (LookupError, ValueError) as error:
        return type(error).__name__


@pytest.mark.parametrize(
    ("chain", "single"),
    [
        ("be-arevela-hepburn-heploc-Latn", "be-arevela-Latn"),
        ("be-arevela-hepburn-heploc-Latn", "be-hepburn-heploc-Latn"),
        ("be-aaland-hepburn-heploc-Latn", "be-aaland-Latn"),
        ("be-hepburn-heploc-arevela-Latn", "be-arevela-Latn"),
        ("ja-hepburn-heploc-abc", "ja-arevela-abc"),
        ("be-abc-hepburn-heploc", "be-abc"),
        ("sv-hepburn-heploc-aaland-FI", "sv-aaland-FI"),
        ("ca-hepburn-heploc-arevela-ES-valencia", "ca-ES-valencia-alalc97"),
    ],
)
def test_a_chain_of_rules_reads_what_one_rule_reads(chain: str, single: str) -> None:
    assert _read(chain) == _read(single)


def test_the_script_the_rules_uncover_is_the_tag_s_script() -> None:
    # be-Latn is a script other than be's likely one, so it reads the root.
    for tag in [
        "be-arevela-Latn",
        "be-arevela-hepburn-heploc-Latn",
        "be-aaland-hepburn-heploc-Latn",
    ]:
        assert resolve_locale(tag) == "und"
        assert format_number(VALUE, tag) == format_number(VALUE, "und")


@pytest.mark.parametrize("head", ["be", "sv", "ca-ES", "ja", "be-abc", "en"])
@pytest.mark.parametrize("tail", ["", "Latn", "FI", "valencia", "abc", "x-abc"])
def test_the_order_of_the_legacy_subtags_does_not_matter(head: str, tail: str) -> None:
    for count in (1, 2, 3):
        for rules in itertools.combinations(RULES, count):
            read = {
                _read("-".join(part for part in (head, *order, tail) if part))
                for order in itertools.permutations(rules)
            }
            assert len(read) == 1, (head, rules, tail, read)


@pytest.mark.parametrize(
    "tag",
    [
        "be-abc-hepburn-heploc",
        "ja-aaland-abc",
        "ja-hepburn-heploc-abc",
        "sv-abc-FI-aaland",
    ],
)
def test_an_extended_language_subtag_the_rules_leave_is_a_value_error(tag: str) -> None:
    with pytest.raises(ValueError, match="extended language subtags are not supported"):
        resolve_locale(tag)
    with pytest.raises(ValueError, match="extended language subtags are not supported"):
        format_number(VALUE, tag)


@pytest.mark.parametrize(
    ("tag", "expected"),
    [("zh-yue-HK", "yue"), ("zh-cmn-yue", "yue"), ("zh-HK-yue", "yue"), ("zh-min-nan", None)],
)
def test_an_extended_language_subtag_a_rule_consumes_is_read(
    tag: str, expected: str | None
) -> None:
    if expected is None:
        with pytest.raises(LookupError):
            resolve_locale(tag)
    else:
        assert resolve_locale(tag) == expected


@pytest.mark.parametrize("tag", ["en-gb-oed-aaland", "en-aaland-gb-oed", "en-GB-oed-aaland"])
def test_the_region_of_the_first_rule_applied_wins(tag: str) -> None:
    # en-gb-oed, a rule of en, applies before und-aaland: its GB stays and aaland's AX is
    # dropped, wherever the subtags stand.
    assert resolve_locale(tag) == "en-GB"


@pytest.mark.parametrize("tag", ["zh-cmn-Hant-419", "zh-419-cmn-hant", "zh-Hant-419-cmn"])
def test_a_numeric_region_the_rules_leave_is_not_an_extended_language_subtag(tag: str) -> None:
    # The rule brings the script and leaves 419 first: a region, so Hant still fills the script.
    assert resolve_locale(tag) == "zh-Hant"


@pytest.mark.parametrize(
    ("tag", "expected", "text"),
    [
        (f"sv-{UND}-FI", "sv-FI", "\u22121\xa0234\xa0567,5"),
        (f"en-gb-oed-{UND}-FI", "en-FI", "-1\xa0234\xa0567,5"),
        (f"i-default-gb-oed-{UND}-FI", "en-FI", "-1\xa0234\xa0567,5"),
    ],
)
def test_the_longest_chains_read_the_region_after_them(tag: str, expected: str, text: str) -> None:
    # Ten, eleven and twelve rules: i-default, en-gb-oed and the ten rules of und. The tag's own
    # region wins wherever it stands, so the effect of every rule before it shows.
    assert resolve_locale(tag) == expected
    assert format_number(VALUE, tag) == text
