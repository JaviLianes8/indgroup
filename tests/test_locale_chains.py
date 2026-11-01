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
        "sv-ABC-aaland",
        "sv-aaland-ABC",
        "en-CMN-gb-oed",
        "zh-Abc-cmn-hant",
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


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("sv-aaland-valencia", "sv-AX"),
        ("en-gb-oed-valencia", "en-GB"),
        ("sv-aaland-abcde", "sv-AX"),
        ("sv-a1b-aaland", "sv-AX"),
        ("en-1ab-gb-oed", "en-GB"),
        ("zh-cmn-a1b-hant", "zh-Hant"),
        ("sv-1996-aaland", "sv-AX"),
        ("en-1abc-gb-oed", "en-GB"),
        ("zh-cmn-1606-hant", "zh-Hant"),
    ],
)
def test_only_three_letters_the_rules_leave_first_are_an_extended_language_subtag(
    tag: str, expected: str
) -> None:
    # A variant or a subtag with a digit left first by the rules, of three or four characters,
    # stays among the variants, so the replacement's script or region still fills the tag's
    # empty one.
    assert resolve_locale(tag) == expected


@pytest.mark.parametrize(("tag", "expected"), [("sv-1-aaland", "sv"), ("en-1-gb-oed", "en")])
def test_a_digit_singleton_ends_the_subtags_the_rules_may_match(tag: str, expected: str) -> None:
    # As with a letter singleton, what follows belongs to the extension, so no rule applies.
    assert resolve_locale(tag) == expected
    assert resolve_locale("zh-1-cmn-hant") == "zh"


@pytest.mark.parametrize("tag", ["es-419-aaland", "es-aaland-419"])
def test_the_tag_s_own_numeric_region_beats_the_region_a_rule_brings(tag: str) -> None:
    assert resolve_locale(tag) == "es-419"
    assert format_number(VALUE, tag) == "-1,234,567.5"
    assert resolve_locale("sv-419-aaland") == resolve_locale("sv-419") == "sv"


@pytest.mark.parametrize(("tag", "expected"), [("no-bok-bok", "nb"), ("zh-yue-yue", "yue")])
def test_a_rule_removes_every_occurrence_of_the_subtags_it_matched(tag: str, expected: str) -> None:
    assert resolve_locale(tag) == expected


def test_a_repeated_region_a_rule_matched_does_not_stay_behind() -> None:
    # en-gb-oed removes both GB and gb, so cmn is left first: an extended language subtag.
    with pytest.raises(ValueError, match="extended language subtags are not supported"):
        resolve_locale("en-GB-gb-oed-cmn")


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("sr-latn-aaland", "sr-Latn"),
        ("zh-hant-cmn-hans", "zh-Hant"),
        ("be-aaland-arevela-latn", "und"),
        ("sv-fi-aaland", "sv-FI"),
        ("sv-aaland-fi", "sv-FI"),
        ("es-aaland-mx", "es-MX"),
    ],
)
def test_a_lower_case_script_or_region_the_rules_leave_first_is_the_tag_s_own(
    tag: str, expected: str
) -> None:
    # Case does not matter, so the replacement's script or region still fills only an empty one.
    assert resolve_locale(tag) == expected
    assert format_number(VALUE, tag) == format_number(VALUE, expected)
