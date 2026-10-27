# indgroup 1.0.0 certification report

The 1.0.0 certification bar applied to indgroup. Nothing is on PyPI yet
(`https://pypi.org/pypi/indgroup/json` answered 404 on 2026-10-25, checked twice), so 1.0.0
is the first release and there is no upgrade path to check; the CHANGELOG still lists every
change against 0.2.0, the last tagged state of `main`.

Progress:
- [x] Branch `release/1.0.0` created from `main` (e5cecf8, version 0.2.0)
- [x] Baseline gates on 0.2.0
- [x] API review and 1.0.0 changes (item 1)
- [x] Errors, typing, docstrings and doctests (items 2 to 5)
- [x] Ground truth: CLDR, ICU and UTS #35 re-fetched, Intl.NumberFormat re-run (item 7)
- [x] Contract, fuzz and author mutation round (items 6, 9, 18)
- [x] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [x] Packaging, e2e, every Python (items 8, 10, 13, 14)
- [x] Gates (item 15)
- [x] PR #3 and trace guard CLEAN
- [x] QA round 1: five lenses reported, every finding fixed (see QA)
- [x] QA round 2: five lenses re-checked round 1, every new finding fixed (see QA)
- [x] QA round 3: lenses d and e re-checked round 2, every new finding fixed (see QA)
- [x] QA round 4: lens d re-checked round 3, its new finding fixed (see QA)
- [x] Suite, gates, packages and matrix re-verified at b63f709 (see Matrix, packaging and gates)
- [x] QA round 5: five fresh lenses at 9ef91df reported 13 findings, every one fixed in 3a01f33 (see QA)
- [x] QA round 6: lenses a, c and e re-checked round 5 and reported 5 findings, every one fixed in 8fea04c (see QA)
- [x] QA round 7: lens e re-checked round 6 and reported 3 findings, every one fixed in ec8a8e7 (see QA)
- [x] QA round 8: lens e re-checked round 7 and reported 2 findings, both fixed in a10bba6 (see QA)
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer reports PASS (item 16)

## Scorecard (author)

| # | Item | Result |
| --- | --- | --- |
| 1 | Public API reviewed for stability | PASS: the 11 names of 0.2.0 kept with their signatures, parameter names and defaults, pinned by `tests/test_contract_api.py`; every behaviour change in the CHANGELOG |
| 2 | `__all__` exact, no private imports in docs | PASS |
| 3 | Docstrings with runnable examples, doctests | PASS: every public function and `NumberSymbols` carries doctests, `Number` and `Grouping` are shown in the package docstring; README and GUIDE blocks run as tests |
| 4 | Typed end to end | PASS: `mypy --strict src tests`, `py.typed` shipped, typing checked from an external consumer in the e2e test |
| 5 | Typed, documented, bounded errors | PASS: `TypeError` for wrong types, `ValueError` for bad values, `LookupError` for locales without data, each documented per function; messages quote at most 40 characters of the input |
| 6 | Contract tests of every public name | PASS |
| 7 | Real ground truth | PASS: see Ground truth |
| 8 | Real e2e from the wheel | PASS: wheel built, installed in a throwaway venv, driven from an empty folder, typed from a consumer with `mypy --strict`, CLI run as `indgroup` and `python -m indgroup`; no PyPI release to upgrade from |
| 9 | Seeded fuzz, no crash, hang or blowup | PASS: three seeds over the formatters, the strict grammar of both parsers against an independent acceptor, and timed hostile shapes |
| 10 | Supported Pythons | PASS: CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2t (free-threaded); 3.8.20 and 3.9.25 are installed but below `requires-python`; no 3.13t is installed here |
| 11 | README and `twine check` | PASS: `twine check --strict` on wheel and sdist, absolute links, README examples run as tests, the Babel facts re-checked against Babel 2.18.0 (10 MB wheel, CLDR 47, `format_decimal(1234, locale="es")` gives `1.234`, three fraction digits unless `decimal_quantization=False`) |
| 12 | Dated CHANGELOG section | PASS: 1.0.0, 2026-10-26; 0.2.0 and 0.1.0 dated from their merge commits |
| 13 | pyproject 1.0.0, Production/Stable | PASS: classifiers for 3.10 to 3.14, `MIT AND Unicode-3.0`, both licence files, URLs, keywords, no runtime dependencies |
| 14 | sdist and wheel contents | PASS: see Matrix, packaging and gates |
| 15 | Gates each exit 0 | PASS: see Matrix, packaging and gates |
| 18 | Contracts bite (mutations) | PASS: 18 of 18 author mutations killed, see Mutation round |

## Defects found in 0.2.0 (reproduced on 2026-10-25)

- `format_number(Decimal("1E-3000000"), "en")` writes three million fraction digits: the
  integer digits are bounded but the fraction digits are not, so `Decimal("1E-999999999")`
  would build a gigabyte of text.
- Error messages quote the whole input: `parse_number("x" * 100000, "en")` raises a
  `ValueError` of 100,033 characters, `resolve_locale("a" * 100000)` one of 100,020.
- `indgroup --parse` with an integer of more than 4300 digits exits 2 with the
  `int` string conversion limit message, although `parse_number` reads it.
- `mypy --strict src tests` failed on two test annotations (`ruff format --check .`,
  `ruff check .` and `mypy --strict src` exited 0); fixed in the tests.

All four are fixed on this branch and listed in the CHANGELOG.

## Found during certification

- The timing test of the largest accepted values asserted wall-clock times under one
  second. On the laptop (CPython 3.14.6, CPU at 91 % from other work) the single
  `Decimal(int)` conversion of a 100,000-digit integer alone took 1.4 s of CPU time and
  2 to 4 s of wall time, against 0.1 s on the desktop, so the test failed although the
  library did nothing beyond that one conversion. The test now measures CPU time and
  compares each call with the bare conversion it cannot avoid on the same machine (at most
  three times it plus 0.2 s); the refusal of a 12-million-digit integer and the
  adversarial parser shapes keep their absolute CPU-time bounds.
- The test that rebuilds the CLDR table read `src/indgroup/_cldr.json` from the tree, so the
  sdist suite run against an installed wheel (sources removed) failed on every interpreter.
  It now reads the table of the imported package, which in that run is the wheel's own.

## Ground truth

Every reference file is fetched by `scripts/fetch_upstream.py` into the gitignored
`tests/upstream/`, which tracks only `MANIFEST.json` (URL, revision, size, sha256,
licence). The tests check each file against the manifest hash and skip while it is
absent. On 2026-10-25 (21:55 UTC) the four fetched files were downloaded again and their
sha256 matched the manifest:

| File | URL | sha256 |
| --- | --- | --- |
| CLDR 48.2.0 numbers | https://registry.npmjs.org/cldr-numbers-full/-/cldr-numbers-full-48.2.0.tgz | 2d17a1453c559a62112caeed52e0bcfe3cb8539c99d239ae7b7ed4d0827679d9 |
| CLDR 48.2.0 core | https://registry.npmjs.org/cldr-core/-/cldr-core-48.2.0.tgz | 5310e0c7a06c1feb83dc8e54c8584bbe0b9c2ea8320172a18d541986b124585d |
| ICU 78.3 grouper | https://raw.githubusercontent.com/unicode-org/icu/release-78.3/icu4c/source/i18n/number_grouping.cpp | 6e7fc28bd2b6a365bffcad868f9618d6537b2b266b30830ef367e56f0f83a9bc |
| UTS #35 Numbers, rev. 76 | https://www.unicode.org/reports/tr35/tr35-76/tr35-numbers.html | be7b81e517dcbc9185aa131132254c2745aec7adec898d12d303187ad31e65b6 |

- The two CLDR rows were 48.0.0 until QA round 5, which moved the table to 48.2.0 (fetched
  2026-10-27; npm published it on 2026-03-18). Derived from both releases, the tables differ
  in exactly one fact, the `fr-CH` group symbol (U+202F in 48.0.0, `'` in 48.2.0).
- The shipped table `src/indgroup/_cldr.json` is rebuilt from the two CLDR packages by
  `scripts/build_table.py` inside the suite and must equal the shipped file; every locale is
  then checked symbol by symbol against the CLDR JSON.
- The grouping rule is checked against ICU's `Grouper` source and the minimum grouping
  digits definition against the UTS #35 text.
- Independent oracle, recorded: `node scripts/intl_reference.mjs` with Node 24.18.0
  (ICU 78.3, CLDR 48.0, Unicode 17.0) writes 72,036 `Intl.NumberFormat` cases (every
  locale, four groupings, Latin digits). Re-run on 2026-10-25, the output was byte for
  byte the manifest hash `3bdad111b1e70cba476c92e96412b9177f957b75df8daef9cba874478ef54b62`. Since the table moved to CLDR 48.2.0
  in QA round 5, every case matches, Swiss French included: ICU 78.3's `fr_CH.txt`
  (tag `release-78.3`, fetched 2026-10-27) has `group{"'"}`, as CLDR 48.2.0 has.
- Independent oracle, live: `tests/test_oracle_intl.py` sends 6,000 random cases per seed
  (three seeds) to `scripts/intl_oracle.mjs` in the same test run and compares, then
  parses every Intl output back.

## Mutation round (author)

One mutation at a time in a copy of the tree, full suite with `pytest -x` (doctests
included) on the laptop, CPython 3.14.6, 2026-10-25. Every mutation was killed. Where a
doctest caught it first, the suite was run again without doctests to name the test file
that also catches it.

| # | Module | Mutation | First catcher | Catcher without doctests |
| --- | --- | --- | --- | --- |
| M1 | `_digits` | minimum grouping off by one (`<` to `<=`) | package doctest | `test_cli::test_formats_arguments_in_the_indian_convention_by_default` |
| M2 | `_grouping` | Indian sizes swapped (`(3, 2)` to `(2, 3)`) | `format_indian` doctest | `test_cli::test_parse_prints_integers_past_the_int_string_limit` |
| M3 | `_number` | `min2` no longer forces two digits | `test_docs::test_every_python_example_prints_its_comments` | same |
| M4 | `_number` | `always` leaves ungrouped locales ungrouped | `test_number::test_always_groups_by_thousands_without_a_grouping_pattern` | same |
| M5 | `_value` | a Decimal's trailing `.0` dropped like a float's | `test_grouping::test_round_trips_decimals[-0.0]` | same |
| M6 | `_value` | `bool` accepted as a number | `test_contract_api::test_wrong_types_raise_type_error` | same |
| M7 | `_value` | Decimal digit bound off by one (`>=` to `>`) | `test_hostile::test_the_digit_bound_is_exact_on_both_sides_of_the_point` | same |
| M8 | `_digits` | parser strips Unicode spaces, eating a no-break space group | `test_fuzz::test_parse_number_accepts_exactly_the_strict_grammar[11]` | same |
| M9 | `_locale` | `root` no longer names the root locale | `test_docs::test_every_python_example_prints_its_comments` | same |
| M10 | `_locale` | unknown locale raises `ValueError` instead of `LookupError` | `resolve_locale` doctest | `test_contract_api::test_unknown_locales_raise_lookup_error_and_not_value_error` |
| M11 | `_digits` | leading group may hold primary-size digits | `test_fuzz::test_parse_indian_accepts_exactly_the_strict_grammar[11]` | same |
| M12 | `_symbols` | decimal and group symbols swapped | package doctest | `test_cli::test_formats_arguments_in_the_indian_convention_by_default` |
| M13 | `_cli` | `--parse` prints through `str()` | `test_cli::test_parse_prints_plain_values` | same |
| M14 | `_value` | messages quote 4,000 characters instead of 40 | `test_hostile::test_error_messages_quote_at_most_forty_characters_of_the_input` | same |
| M15 | `_number` | `parse_number` accepts a leading `+` | `test_contract_api::test_bad_values_raise_value_error_and_nothing_else` | same |
| M16 | `_locale` | CLDR parent locales ignored | `resolve_locale` doctest | `test_intl::test_every_locale_value_and_grouping_matches_intl` |
| M17 | `_digits` | fraction digit bound dropped in parsing | `test_hostile::test_the_digit_bound_is_exact_on_both_sides_of_the_point` | same |
| M18 | `_value` | float read by its binary value instead of its shortest spelling | `format_number` doctest | `test_docs::test_every_python_example_prints_its_comments` |

## Matrix, packaging and gates

Run on this PC at 9ade550 on 2026-10-26 from a fresh clone of `release/1.0.0`, with the
fetched reference files copied in and Node 24.18.0 on the path:

- Wheel and sdist built with `python -m build`. For each interpreter a new venv got the wheel
  plus pytest; the sdist's test suite ran from the unpacked sdist with its `src` removed, so
  it imported the installed wheel, then the package doctests ran from site-packages.

| Python | sdist suite against the wheel | Doctests in site-packages |
| --- | --- | --- |
| 3.10.19 | 235 passed, 3 skipped | 10 passed |
| 3.11.5 | 235 passed, 3 skipped | 10 passed |
| 3.12.12 | 235 passed, 3 skipped | 10 passed |
| 3.13.2 | 235 passed, 3 skipped | 10 passed |
| 3.14.2 | 235 passed, 3 skipped | 10 passed |
| 3.14.2t | 235 passed, 3 skipped | 10 passed |

  The three skips are the installed-wheel test (needs `INDGROUP_E2E=1`) and the two checks
  that need a git checkout.
- Full suite in the clone with `INDGROUP_E2E=1` (doctests, the installed-wheel test with
  both CLI entry points, the live Intl oracle): exit 0. The same suite, without the e2e
  test, passed on the laptop with CPython 3.14.6.
- Gates in the clone: `ruff format --check .`, `ruff check .`, `mypy --strict src` and
  `mypy --strict src tests` each exit 0, `pytest` as above.
- `twine check --strict dist/*`: both PASSED.
- Wheel: the package modules, `_cldr.json`, `py.typed`, `__main__.py`, the entry point
  `indgroup = indgroup._cli:main`, and `LICENSE` plus `LICENSE-UNICODE` under
  `dist-info/licenses`. Nothing else.
- Sdist: sources, tests, scripts, README, GUIDE, CHANGELOG, CONTRIBUTING, both licences,
  `requirements-dev.txt` and `tests/upstream/MANIFEST.json`. The fetched third-party files,
  this report and the improvement notes are excluded.

### At b63f709 (after QA round 4)

`https://pypi.org/pypi/indgroup/json` still answered 404 on 2026-10-26. `python -m build` at
b63f709 gives the same files on two separate builds, so every run below tested one wheel
(sha256 `85ab5b8e7f743af21b7528fa28802ab2dc9094fd620212fb4fd6c09b56f0f681`) and one sdist
(`90fefd13cb943f35742dd140d590597b560f03275b44c52a255edeb4347c5985`).

- Elena's PC, CPython 3.14.2, `git archive` of b63f709 with the fetched reference files,
  `INDGROUP_E2E=1`: 402 passed, 10 skipped, exit 0 (installed-wheel test included). Skipped:
  the five closed-stream shell cases (no POSIX shell there), the two tree checks (no git
  checkout) and the live Intl oracle (its Node has ICU 78.2). Gates in the same tree:
  `ruff format --check .`, `ruff check .`, `mypy --strict src` and `mypy --strict src tests`
  each exit 0.
- This PC, the interpreter matrix of lens d's fifth check on this wheel, same method as
  above:

| Python | sdist suite against the wheel | Doctests in site-packages |
| --- | --- | --- |
| 3.10.19 | 399 passed, 3 skipped | 10 passed |
| 3.11.5 | 399 passed, 3 skipped | 10 passed |
| 3.12.12 | 399 passed, 3 skipped | 10 passed |
| 3.13.2 | 399 passed, 3 skipped | 10 passed |
| 3.14.2 | 399 passed, 3 skipped | 10 passed |
| 3.14.2t | 399 passed, 3 skipped (re-run) | 10 passed |

  In that run 3.14.2t had 3 failures, all in the live Intl oracle: Node could not start
  (Windows status `0xC0000142`, DLL initialisation failed) while this PC was loaded by other
  work. Re-run in a new 3.14.2t venv with the same wheel and Node 24.18.0: the oracle files
  pass (5 passed), then the whole sdist suite (399 passed, 3 skipped) and the doctests
  (10 passed). A new full matrix by the author could not get a turn on this PC, which stayed
  above its load limit for the whole session.
- `twine check --strict`: wheel and sdist PASSED. Contents as listed above, plus the
  `_args.py` module of the new command-line reader and the new test files in the sdist.

## QA

### Round 1 (2026-10-26, at 593f945)

Five independent lenses (a: API and docs, b: correctness and ground truth, c: adversarial,
d: packaging and e2e, e: contract strength) reported 24 findings (lens c also sent an
evidence note that is not a defect). Every one is fixed; none is disputed. Behaviour fixes
got a contract test first: run against 593f945 (the new test files with the old `src` on the
path), 56 of the new cases failed, and all pass after the fix.

| Finding | Severity | Fix |
| --- | --- | --- |
| a-A1 | medium | README and GUIDE now promise what holds: text written by the formatters reads back to a value that formats to the same text, `-0` excepted; the non-canonical spellings the parser also takes are listed. Pinned by `test_parse_edges::test_text_written_by_the_formatters_reads_back_to_the_same_text` |
| a-A2 | low | GUIDE: at run time `Number` is the union `int \| float \| Decimal` and `Grouping` a `typing.Literal` |
| a-A3, c-C3, d-D3 | low | The command line no longer uses `argparse`: every error, argument errors included, is one line on stderr quoting at most 40 characters of an argument, status 2 (`test_cli_args::test_argument_errors_are_one_short_line`, 12 shapes including a 20,000-character `-g`, `--x...`, `--parse=...`, `-p...` and an ambiguous `--lo=...`) |
| a-A4 | low | GUIDE and CHANGELOG: a longer input is cut and its length given |
| a-A5 | low | CONTRIBUTING describes the real policy: pure unit tests, and the files that read the clock, the docs, git, Node or the reference files, or build a venv |
| a-A6 | low | CHANGELOG: 0.2.0 dated 2026-10-14 (e5cecf8), 0.1.0 dated 2026-10-12 (6f813fe) with an `### Added` heading |
| b-F1 | medium | `resolve_locale` applies CLDR's `nonlikelyScript` parent rule (UTS #35 rev. 76, fetched 2026-10-26): `ru-Latn`, `hi-Arab`, `de-Cyrl`, `fr-Arab` read `und`. The table now ships the likely script of all 350 languages. Where the likely script added for a region has no data (`ku-GE`), the plain chain is kept (`ku`), as before |
| b-F2 | low | A grouped integer may not start with `0` (`0,001`, `01,234`, `00,01,234` refused); ungrouped `007` still reads. The fuzz acceptor follows the same rule |
| b-F3 | low | Documented: the table is the 766 locales of the CLDR JSON packages; the CLDR 48 XML has one more locale with number data, `en_US_POSIX` (re-checked: of the 359 XML locales not named the same way in the table, only it and three variant locales the table holds in lower case carry `<numbers>`), and `en-US-POSIX` reads `en` here while Intl writes `-1234567.5` |
| b-F4 | low | Multi-valued region aliases follow the UTS #35 Territory Exception (likely region of the language and script, else the first): `en-200` reads `en-CZ`, `ar-NT` `ar-SA`, `kk-SU` `kk-KZ`, `nl-AN` `nl-CW`, `en-830` `en-JE`, `en-PC` `en-FM`, each the locale Intl of Node 24.18 resolves |
| b-F5 | low | README and GUIDE: 637 CLDR locales ICU ships under their own name plus 13 alias and fallback tags (re-counted from `intl-node.json`: 650 = 637 + 13) |
| c-C1 | medium | stdin lines are trimmed of ASCII spaces, tabs and line breaks only, like the parsers; arguments are trimmed the same way |
| c-C2, d-D2 | low | A reader that closes stdout early stops the command quietly with status 1 (stdout pointed at the null device); in-process and subprocess tests |
| d-D1 | medium | An argument that starts with a minus and a digit or a point is a value on every Python; the same tests pass on 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2t, by subprocess too |
| e-F1 | medium | `test_parse_edges::test_str_subclasses_*`: a `str` subclass that lies in `join`, `strip`, `partition`, `split`, `replace`, `lower`, `startswith`, `__eq__`, `__len__` and `__str__`, as text, locale, separator and grouping |
| e-F2 | medium | Case tests for the modifier, `root`, the variant and the script |
| e-F3 | medium | Private use and extensions: `ca-ES-x-valencia` reads `ca` |
| e-F4 | medium | Numeric regions: `de-756` reads `de-CH` and formats `1'234'567` |
| e-F5 | low | `abcd`, `abcdefghi` and nine-character subtags are pinned as `ValueError` |
| e-F6 | low | `12.`, `.5` and other values that are not plain numbers are pinned as CLI errors |
| e-F7 | low | `--locales` output is compared whole, final newline included |

Other changes made with these fixes, each in the CHANGELOG: a tag that names its language's
likely script reads the same locale as without it for every language (`ru-Cyrl-UA` reads
`ru-UA`, `ca-Latn-ES-valencia` reads `ca-ES-valencia`); `--help` and `--version` print to
the stream given to `main` and return 0; long options may still be shortened to a unique
prefix.

Mutation re-check, one mutant at a time in a copy of the tree, `pytest -x` (doctests
included) on Elena's PC, CPython 3.14.2: the 15 surviving mutants of lens e plus 9 against
this round's fixes. All 24 killed.

| # | Mutation | First catcher |
| --- | --- | --- |
| G8 | separator read through its own methods | `test_parse_edges::test_str_subclasses_are_read_by_their_value` |
| N7 | grouping not converted to a plain `str` | `test_parse_edges::test_str_subclasses_cannot_fake_a_valid_grouping_or_hide_their_length` |
| X5 | text stripped with its own `strip` | `test_parse_edges::test_str_subclasses_are_read_by_their_value` |
| X6 | locale split with its own `partition` | `test_parse_edges::test_str_subclasses_are_read_by_their_value` |
| X10 | `shown()` measures with the subclass `__len__` | `test_parse_edges::test_str_subclasses_cannot_fake_a_valid_grouping_or_hide_their_length` |
| L3 | POSIX modifier case-sensitive | `test_locale_rules::test_every_subtag_is_read_in_any_case[sr_RS@LATIN-sr-Latn]` |
| L8 | `ROOT` not recognised | `test_locale_rules::test_every_subtag_is_read_in_any_case[ROOT-und]` |
| L13 | variant case kept | `test_locale_rules::test_every_subtag_is_read_in_any_case[ca-ES-VALENCIA-ca-ES-valencia]` |
| L14 | script case kept | `test_locale_rules::test_every_subtag_is_read_in_any_case[zh-hant-TW-zh-Hant]` |
| L7 | subtags after a singleton read as variants | `test_locale_rules::test_subtags_after_an_extension_or_private_use_are_not_variants[ca-ES-x-valencia-ca]` |
| L6 | numeric regions not recognised | `test_locale_rules::test_a_region_with_several_replacements_takes_the_likely_one[en-200-en-CZ]` |
| L1 | four-letter language accepted | `test_locale_rules::test_subtags_of_the_wrong_length_are_value_errors[abcd]` |
| X13 | nine-character subtags accepted | `test_locale_rules::test_subtags_of_the_wrong_length_are_value_errors[de-CH-abcdefghi]` |
| C9 | CLI accepts `12.` | `test_cli_args::test_values_must_be_plain_numbers[12.]` |
| X2 | `--locales` drops its final newline | `test_cli::test_locales_lists_the_table` |
| R1 | `nonlikelyScript` rule dropped | `test_locale_rules::test_a_script_other_than_the_likely_one_falls_back_to_the_root[ru-Latn]` |
| R2 | first replacement region always taken | `test_locale_rules::test_a_region_with_several_replacements_takes_the_likely_one[kk-SU-kk-KZ]` |
| R3 | grouped integers may start with `0` again | `test_docs::test_every_python_example_prints_its_comments` |
| R4 | stdin stripped of every Unicode space | `test_cli_args::test_stdin_keeps_unicode_spaces_and_group_symbols` |
| R5 | only plain negative digits are values (the old argparse rule) | `test_cli_args::test_negative_values_need_no_double_dash` |
| R6 | a closed pipe raises | `test_cli_args::test_a_closed_pipe_stops_quietly_with_status_one` |
| R7 | the likely-script chain may end at the root | `test_locale_rules::test_the_likely_script_and_the_explicit_parents_keep_their_data[ku-GE-ku]` |
| R8 | arguments not trimmed | `test_cli_args::test_ascii_spaces_around_a_value_are_ignored_in_arguments_and_stdin` |
| R9 | long options cannot be shortened | `test_cli_args::test_argument_errors_name_the_problem` |

Runs at 1f26d23 (the fix commit):

- Elena's PC, CPython 3.14.2, fresh clone with the fetched reference files and Node 24.18.0,
  `INDGROUP_E2E=1`: 349 passed, nothing skipped (installed-wheel test and live Intl oracle
  included).
- This PC, one venv per interpreter, Node 24.18.0 on the path: 348 passed and 1 skipped
  (the installed-wheel test) on 3.10.19, 3.11.5, 3.12.12, 3.13.2, 3.14.2 and 3.14.2t.
- Gates: `ruff format --check .`, `ruff check .`, `mypy --strict src` and
  `mypy --strict src tests` each exit 0.

### Round 2 (2026-10-26, at 910f764)

The five lenses re-checked every round 1 finding at 910f764 and found each one fixed (lens a:
A1 to A6, lens b: F1 to F5, lens c: C1 to C3, lens d: D1 to D3, lens e: F1 to F7 and its 15
earlier mutants, all killed). They reported ten new findings, two of them the same defect seen
by two lenses. Every one is fixed; none is disputed. Behaviour fixes got a contract test first:
run against 910f764 (the new test files with the old `src` on the path), 12 cases failed (the
long cluster, every missing or closed standard stream, and the message for `-p=x`), and all pass
after the fix. The tests for lens e's surviving mutants pin behaviour that 910f764 already had,
so they pass on it and were proven by the mutation run below instead.

| Finding | Severity | Fix |
| --- | --- | --- |
| a-A7 | low | GUIDE: text that is not a tag raises `ValueError` for a four-letter language subtag or any subtag longer than eight characters; subtags after the region are not held to BCP 47's variant grammar (`en-US-abcd` reads `en`), pinned by `test_locale_rules::test_subtags_after_the_region_are_not_held_to_the_variant_grammar`. Behaviour unchanged |
| b-N1 | low | README and GUIDE list the difference with Intl for a tag that spells out its language's likely script (`de-Latn-AT` reads `de-AT` here, as UTS #35 says; Intl reads `de`), re-checked on Node 24.18 (ICU 78.3): `-1.234.567,5` from Intl against `-1`, `234`, `567,5` joined by no-break spaces here. The `en_US_POSIX` difference now reads as the one place where Intl follows CLDR (its XML) and this library, built from the JSON packages, does not |
| c-N1 | low | A short-option cluster is read letter by letter with an index and copies the rest of the argument only once, for an option that takes it as its value: 400,000 flags in one argument cost about what 400,000 separate ones do (`test_cli_grammar::test_a_long_option_cluster_is_read_in_linear_time`, CPU time; before the fix the cluster took 1.83 s on this PC and the separate flags 0.28 s) |
| c-N2, d-D4 | low | Started without stdout, the command stops quietly with status 1, as when its reader leaves (exit 0 when there is nothing to write); without stdin and VALUE arguments it reports that there are no values, status 2; without stderr an error still exits with status 2. In-process tests with each stream set to `None`, and subprocess tests with `>&-` and `<&-` |
| e-N1 | medium | `test_cli_streams::test_a_reader_gone_before_the_first_write_gets_no_traceback`: one VALUE argument, `--locales`, `--version` and one stdin line, with the read end of the pipe closed before the command starts: status 1 and an empty stderr |
| e-N2 | medium | `test_cli_streams::test_other_write_errors_are_raised_not_taken_for_a_closed_pipe`: `EIO` and `ENOSPC` propagate as `OSError` |
| e-N3 | medium | `test_cli_grammar::test_values_after_a_double_dash_keep_their_order`: several values after `--`, negative ones and a second `--` included |
| e-N4 | low | `test_cli_grammar`: three-character prefixes (`--p`, `--v`, `--h`), a bad `-g` with `-p`, with `--locales` and in `-pg`, `-l=de`, `-g=off`, `-pl=de`, `--parse=l`, `-p=x`, `--locales` followed by other flags, and a lone `-`, which is a value |

Other changes made with these fixes, each in the CHANGELOG: a flag given a value inside a
cluster (`-p=x`) is refused with a message that names the flag, as `--parse=x` already was.

Mutation re-check, one mutant at a time in a copy of the tree, `pytest -x` (doctests included)
on Elena's PC, CPython 3.14.2: the 10 surviving mutants of lens e, rewritten for the new
reader where its code moved, plus 7 against this round's fixes. All 17 killed.

| # | Mutation | First catcher |
| --- | --- | --- |
| C10 | closed pipe: buffer not sent to the null device | `test_cli_streams::test_a_reader_gone_before_the_first_write_gets_no_traceback` |
| C11 | closed pipe: write not flushed | `test_cli_streams::test_a_reader_gone_before_the_first_write_gets_no_traceback` |
| C7 | every write error taken for a closed pipe | `test_cli_streams::test_other_write_errors_are_raised_not_taken_for_a_closed_pipe[5]` |
| A2 | values after `--` reversed | `test_cli_grammar::test_values_after_a_double_dash_keep_their_order` |
| A3 | three-character prefixes refused | `test_cli_grammar::test_any_unique_prefix_of_three_characters_names_an_option` |
| A6 | any grouping accepted | `test_cli_grammar::test_a_bad_grouping_is_refused_whatever_else_is_asked` |
| A7 | `-l=de` keeps the equals sign | `test_cli_grammar::test_a_short_option_takes_its_value_after_an_equals_sign` |
| A9 | `--parse=x` accepted | `test_cli_args::test_argument_errors_are_one_short_line` |
| A13 | a later flag clears `--locales` | `test_cli_grammar::test_locales_wins_over_other_flags_in_any_order` |
| A14 | a lone `-` is an option | `test_cli_grammar::test_a_lone_dash_is_a_value` |
| S1 | missing stdout reported as success | `test_cli_streams::test_a_missing_stdout_stops_quietly_with_status_one` |
| S2 | missing stdin not handled | `test_cli_streams::test_a_missing_stdin_is_no_input` |
| S3 | missing stderr not handled | `test_cli_streams::test_a_missing_stderr_still_exits_with_status_two` |
| A9b | `-p=x` accepted | `test_cli_grammar::test_flags_take_no_value` |
| Q1 | a cluster copies its rest for every letter | `test_cli_grammar::test_a_long_option_cluster_is_read_in_linear_time` |
| Q2 | an unknown letter inside a cluster not named | `test_cli_grammar::test_flags_take_no_value` |
| H1 | `-h` inside a cluster does not end the reading | `test_cli_args::test_help_and_version_print_to_stdout_and_exit_zero` |

Runs at f500369 (the fix commit):

- Elena's PC, CPython 3.14.2, the tree with the fetched reference files, `INDGROUP_E2E=1`:
  377 passed, 7 skipped (the installed-wheel test included). Skipped: the four closed-stream
  subprocess cases, which need a POSIX shell that PC does not have, and the live Intl oracle,
  because its Node has ICU 78.2.
- This PC, CPython 3.13.2 with Git's `sh` on the path: the four command-line test files,
  closed-stream cases included, pass.
- Gates: `ruff format --check .`, `ruff check .`, `mypy --strict src` and
  `mypy --strict src tests` each exit 0.

### Round 3 (2026-10-26, at d73aa87)

Lens d re-checked D4 and lens e re-checked N1 to N4 and its earlier mutants at d73aa87: all
fixed, all killed. Lens d also ran the suite on CPython 3.10.19, 3.11.5, 3.12.12, 3.13.2,
3.14.2 and 3.14.2t (374 tests, no failure) and on the laptop with 3.14.6 from the wheel and
the sdist, and found the wheel, the sdist and `twine check` clean. They reported four new
findings, all fixed in bd3960c; none is disputed. The behaviour fix (d-D5) got its contract
tests first: run against d73aa87 (the new test files with the old `src` on the path), 7 cases
failed, and all pass after the fix. The tests for lens e's surviving mutants pin behaviour
that d73aa87 already had, so they pass on it and were proven by the mutation run below.

| Finding | Severity | Fix |
| --- | --- | --- |
| d-D5 | low | On a pipe, `main` switches `sys.stderr` to UTF-8 along with `sys.stdout`, keeping Python's `backslashreplace` handler, so an error quoting `é`, `€` or CJK text comes out as UTF-8 instead of the legacy code page or escapes. `test_cli_encoding` runs the command by subprocess with `PYTHONIOENCODING` removed and `PYTHONUTF8=0` (and the C locale outside Windows): values from stdin and, on Windows, from the arguments, quoted in errors as UTF-8 text; an in-process test pins the encoding and error handler each stream is left with. GUIDE, README, the docstring of `main` and the CHANGELOG say so |
| e-E1 | medium | `test_cli_encoding::test_stdin_is_read_as_utf8_and_a_byte_order_mark_is_skipped` and `test_stdout_is_written_as_utf8`, in the same legacy environment: a value grouped with U+202F under `-p -l fr`, a line with a byte order mark, a line that is not UTF-8, and U+202F written by `-l fr` |
| e-E2 | low | `test_cli_grammar::test_help_and_version_end_the_reading_in_their_long_form_too`: `--help --nope`, `--help --version` and `--version --help` |
| e-E3 | low | `test_cli_grammar::test_an_option_value_is_taken_as_written`: `-l==de`, `-g==off`, `-l=` and `--locale=` followed by a value, `--locale=` alone, `-g=` and `--grouping=` followed by a value, and `--grouping`, `-g` and `--locale` with a padded value, each with its exact error line. GUIDE now states that an option's value is taken as written and that `--help` and `--version` end the reading. Behaviour unchanged |

Mutation re-check, one mutant at a time in a copy of the tree, the whole suite with
`INDGROUP_E2E=1` and `pytest -x` (doctests included), four at a time on Elena's PC, CPython
3.14.2: lens e's six survivors and two against this round's fix. All 8 killed.

| # | Mutation | First catcher |
| --- | --- | --- |
| Cn | stdin not switched to UTF-8 | `test_cli_encoding::test_stdin_is_read_as_utf8_and_a_byte_order_mark_is_skipped` |
| D5 | stderr not switched to UTF-8 | `test_cli_encoding::test_errors_quote_a_value_read_from_stdin_as_utf8_text` |
| D5b | stderr switched with the `strict` handler | `test_cli_encoding::test_the_process_streams_are_left_utf8_with_stderr_still_escaping` |
| S17 | a long `--help` or `--version` does not end the reading | `test_cli_grammar::test_help_and_version_end_the_reading_in_their_long_form_too` |
| S8 | a short option's value loses every leading `=` | `test_cli_grammar::test_an_option_value_is_taken_as_written` |
| S15 | `--locale=` takes the next argument | `test_cli_grammar::test_an_option_value_is_taken_as_written` |
| S31 | `-l=` takes the next argument | `test_cli_grammar::test_an_option_value_is_taken_as_written` |
| S35 | a separate long option value is trimmed | `test_cli_grammar::test_an_option_value_is_taken_as_written` |

Runs at bd3960c (the fix commit):

- Elena's PC, CPython 3.14.2, a fresh clone with the fetched reference files,
  `INDGROUP_E2E=1`: 399 passed, 7 skipped, exit 0 (the installed-wheel test included).
  Skipped: the four closed-stream subprocess cases, which need a POSIX shell that PC does not
  have, and the live Intl oracle, because its Node has ICU 78.2.
- This PC, CPython 3.13.2 with Git's `sh` on the path: the four command-line test files and
  `test_cli_encoding`, closed-stream cases included, pass. The interpreter matrix was not rerun
  this round: the change is one more `reconfigure` call on a standard stream, which every
  supported Python has.
- Gates: `ruff format --check .`, `ruff check .`, `mypy --strict src` and
  `mypy --strict src tests` each exit 0.

### Round 4 (2026-10-26, at 60bbdaa)

Lens d re-checked D5 at 60bbdaa: fixed. With `PYTHONIOENCODING`, `PYTHONUTF8` and
`PYTHONLEGACYWINDOWSSTDIO` removed, a fresh wheel venv on CPython 3.10.19, 3.11.5, 3.12.12,
3.13.2, 3.14.2 and 3.14.2t and an sdist venv on 3.13.2 all print the error line for `-é`,
`1x€` and CJK text as UTF-8 with status 2, while a wheel built from d73aa87 still gives the
legacy bytes. The installed suite (393 passed, 3 skipped) and the doctests pass on all six,
`twine check --strict` passes, and the wheel and sdist contents are clean. Of 29 robustness
probes, one found a new defect, fixed in 406d1ba; none is disputed. Its contract tests came
first: against 60bbdaa they failed (status 120 in four subprocess cases, a raised
`BrokenPipeError` in process), and all pass after the fix.

| Finding | Severity | Fix |
| --- | --- | --- |
| d-D5 | low | Confirmed fixed; nothing to change |
| d-D6 | low | When the reader of stderr had closed it, the error line could not be flushed and Python turned that into status 120 at exit, not the documented 2. `_fail` now writes the line through the same helper as stdout: on a closed pipe it points file descriptor 2 at the null device and the status stays 2. `test_cli_streams::test_a_stderr_reader_gone_before_the_error_still_gives_status_two` runs four failing commands (unknown locale, unknown option, a bad value and stdin that is not UTF-8) with the read end of stderr closed before they start; `test_a_closed_stderr_in_process_still_exits_with_status_two` covers a stderr whose write raises `BrokenPipeError`; `test_a_closed_standard_stream_gives_no_traceback` gains `2>&-`. GUIDE and CHANGELOG say so |

Runs at 406d1ba (the fix commit):

- Elena's PC, CPython 3.14.2, the tree with the fetched reference files, `INDGROUP_E2E=1`:
  402 passed, 10 skipped, no failure (the installed-wheel test included). Skipped: the five
  closed-stream shell cases, which need a POSIX shell that PC does not have, the two tree
  checks, which need a git checkout, and the live Intl oracle, because its Node has ICU 78.2.
- This PC, CPython 3.13.2 with Git's `sh` on the path: `test_cli_streams`, `test_cli_encoding`,
  `test_docs` and `test_contract` pass, closed-stream and tree cases included. The reviewer's
  repro now gives 2 three times out of three, in the shell pipeline and with `Popen`, and the
  stdout version still gives 1.
- Gates: `ruff format --check .`, `ruff check .`, `mypy --strict src` and
  `mypy --strict src tests` each exit 0.

### Round 5 (2026-10-27, at 9ef91df)

Five fresh lenses (a to e, same lenses as round 1) re-ran the bar at 9ef91df and reported 13
findings: a: 3, b: 3, c: 1, d: 1, e: 5. Lens a's F1 and lens d's D1 are the same defect. None
is disputed. All are fixed in 3a01f33. The contract tests came first. Run against the
sources of 9ef91df, the final `test_locale_aliases`, `test_cli_values`, `test_messages` and
`test_locale` give 47 failures and 90 passes; the passes include lens e's contracts, which pin
behaviour 9ef91df already had and fail only on its mutants (table below). The growth contract
of `test_conversions` measured ratios of 49 to 62 against its bound of 36 on 9ef91df (a copy
of the test without the import of the new module). All of them pass after the fix, where the
same ratios are 13 to 25.

| Finding | Severity | Fix |
| --- | --- | --- |
| a-F1, d-D1 | low | The command line takes every finite plain spelling of a number in ASCII: `.5`, `-.5`, `5.`, `+.25` and exponents of any length. The exponent is capped at nine digits before it reaches `Decimal`, so the library's 100,000-digit bound decides and gives its own error: `1e99999` prints 100,000 digits, `1e100000` and `1e` followed by 100,000 nines are `more than 100,000 digits`, and `0e99999999999999999999` prints `0`. `1,234`, `1_000`, `0x10`, `Infinity`, full-width and Arabic-Indic digits are still not plain numbers. `--help`, README and GUIDE state the grammar. Tests: `test_cli_values` (formats, bound, refusals, a 2-million-digit exponent read in under a second); `test_cli` and `test_cli_args` updated where they pinned the old refusals |
| a-F2 | low | GUIDE (tag rules and Errors table) and the `resolve_locale` docstring list every `ValueError` case, the extended language subtag included, and say that subtags after the script or region are read as variants without a grammar check, so `en-Latn-abc` reads `en` like `en-US-abcd`. Tests: `test_locale_aliases::test_other_extended_language_subtags_are_value_errors` and `test_a_three_letter_subtag_after_the_script_is_an_unchecked_variant` |
| a-F3 | low | The package docstring and the README API table say the separator is one character other than a digit, a sign or `.` |
| b-F1 | medium | The table is rebuilt from CLDR 48.2.0 (`cldr-numbers-full` and `cldr-core` from npm, sha256 in Ground truth). Derived by the same script, 48.0.0 and 48.2.0 differ in one fact, the `fr-CH` group symbol. `fr-CH` now writes and reads `1'234'567,89`, so the recorded Intl reference and the live oracle match on every compared case with no exception list (`KNOWN_ICU_DIFFERENCES` is gone). `cldr_version()` is `48.2.0`; README, GUIDE, CHANGELOG and the manifest say so. Tests: `test_locale::test_swiss_french_groups_with_an_apostrophe_since_cldr_48_2`, `test_intl` (now with `fr-CH` among its probes and parsed back), `test_sources` against the 48.2.0 files |
| b-F2 | low | The table carries CLDR's 65 language aliases of several subtags (`tags`), and the new `_tag` module applies them as UTS #35 does: a rule matches when its first subtag is the language (`und` for any) and its other subtags stand before the first extension; the replacement's script and region fill only what the tag leaves empty. `zh-yue-HK` reads `yue`, `zh-cmn-Hant` `zh-Hant`, `no-bok` `nb`, `i-lux` `lb`, `art-lojban` `jbo`, `i-default` `en`, `sv-aaland` `sv-AX`, `sv-FI-aaland` `sv-FI`, `i-enochian` `und`. An alias whose replacement has no data raises `LookupError`: `hy-arevmda`, `zh-hakka`, `zh-xiang`, `zh-min-nan`, `i-klingon`, `sgn-BR`, `sgn-BE-FR`. Tests: `test_locale_aliases` (three tests) |
| b-F3 | low | A tag without a script reads what its full form reads. The table now holds the likely script of every language and region where it differs (373 entries, 6 more), not only for languages with locales in several scripts, and the lookup no longer turns a root result into the language. `ku-GE`, `ku-AM`, `ku-AZ`, `ku-TM`, `ky-CN`, `ky-TR`, `tg-PK`, `ug-KZ`, `ug-MN` and `lzz-GE` read `und`, like their full forms; the last three were found by the wider table. README (Intl comparison) and GUIDE state it. Tests: `test_locale_aliases::test_a_tag_reads_what_its_likely_script_reads_even_without_data` (10 cases, resolution and output); `test_locale_rules` no longer pins `ku-GE` as `ku` |
| c-F1 | medium | New `_bigint` module: `to_int` splits the digits' `Decimal` by powers of 256 with exact `Decimal` division, and `to_decimal` joins the int's bytes with exact `Decimal` multiplication, both in a fresh context at `MAX_PREC`, with pieces of 800 bytes left to Python. `read_number`, `split_value` and `--parse` use them. On this PC (CPython 3.13.2), 100,000 digits now take 0.069 s to parse and 0.032 s to format, against 0.19 s and 0.10 s. The README and GUIDE claims match those figures. Tests: `test_conversions` (growth from 12,500 to 100,000 digits under 36 times for five public paths and the CLI, the largest values under a second each, exactness at the piece edges, the 4,300-digit limit and powers of 2 and 10) |
| e-F1 | medium | `test_locale_aliases::test_the_region_of_the_tag_wins_over_the_region_of_an_alias`: `swc-KE` is `sw-KE` (`-1,234,567.5`), `swc` is `sw-CD`, `prs-IR` is `fa`, `cnr-BA` is `sr-Cyrl-BA`, `cnr` is `sr-Latn-ME`, resolution and output |
| e-F2 | medium | `test_locale_aliases::test_a_bad_subtag_late_in_the_tag_is_a_value_error`: a bad subtag in the fourth or fifth position, after a variant, after `-x-`, and an empty trailing subtag, through `resolve_locale` and `format_number` |
| e-F3 | low | `test_locale_aliases::test_an_explicit_script_wins_over_a_posix_modifier` (`uz-Arab@latin`, `sr-Cyrl@latin`, `hi-Latn@devanagari`); GUIDE states the rule |
| e-F4 | low | `test_messages`: exactly 40 characters are quoted whole and 41 are cut with `... (41 characters)`, for `parse_indian`, `parse_number`, `resolve_locale` and `number_symbols`; the count is of characters, not bytes |
| e-F5 | low | `test_messages`: the message names NaN for float NaN, negative NaN, `Decimal("NaN")` and `Decimal("sNaN")`, and an infinity for both float and both `Decimal` infinities, through both formatters |

Mutation check of the fixes, one mutant at a time on this PC (CPython 3.13.2, bytecode
writing off), running the new and changed test files with `-x`. The five survivors of lens e
are now killed, and so are 13 mutants of the new code. Two of those 13 (an `und` replacement
and a tag's script against a replacement's) survived at first and gained the contract
`test_a_replacement_of_und_names_the_root_and_the_tag_keeps_its_fields`.

| Mutant | First catcher |
| --- | --- |
| e-F1: `region = region or extra` to `region = extra` | `test_locale_aliases::test_the_region_of_the_tag_wins_over_the_region_of_an_alias[swc-KE...]` |
| e-F2: subtag check on `subtags[:3]` only | `test_locale_aliases::test_a_bad_subtag_late_in_the_tag_is_a_value_error[en-Latn-US-abcdefghi]` |
| e-F3: the modifier wins over the tag's script | `test_locale_aliases::test_an_explicit_script_wins_over_a_posix_modifier[uz-Arab@latin...]` |
| e-F4: `len(text) <= _SHOWN` to `<` | `test_messages::test_an_input_of_forty_characters_is_quoted_whole[parse_indian...]` |
| e-F5: NaN called an infinity | `test_messages::test_nan_is_named_in_the_message[nan0]` |
| an `und` replacement keeps the tag's first subtag | `test_locale_aliases::test_a_replacement_of_und_names_the_root_and_the_tag_keeps_its_fields` |
| the replacement's region overrides the tag's | `test_locale_aliases::test_aliases_of_several_subtags_read_their_replacement[sv-FI-aaland-sv-FI]` |
| the replacement's script overrides the tag's | `test_locale_aliases::test_a_replacement_of_und_names_the_root_and_the_tag_keeps_its_fields` |
| `und` rules never tried | `test_locale_aliases::test_aliases_of_several_subtags_read_their_replacement[sv-aaland-sv-AX]` |
| aliases matched inside extensions | `test_locale_aliases::test_an_alias_inside_an_extension_is_not_applied` |
| exponent cap removed | `test_cli_values::test_every_plain_decimal_spelling_formats[argv6-...]` |
| `.5` and `5.` refused again | `test_cli_values::test_every_plain_decimal_spelling_formats[argv0-...]` |
| a root result of the likely script turned into the language | `test_locale_aliases::test_a_tag_reads_what_its_likely_script_reads_even_without_data[ku-GE...]` |
| `to_int` halves swapped | `test_conversions::test_conversions_are_exact_at_every_size[1927]` |
| `to_decimal` drops a byte | `test_conversions::test_conversions_are_exact_at_every_size[1927]` |
| `to_decimal` negates in the caller's context | `test_conversions::test_long_integers_cost_far_less_than_quadratic_time[format_number]` |
| `split_value` back to `Decimal(value)` | `test_conversions::test_long_integers_cost_far_less_than_quadratic_time[format_indian]` |
| `read_number` back to `int(Decimal(digits))` | `test_conversions::test_long_integers_cost_far_less_than_quadratic_time[parse_indian grouped]` |

Runs at 3a01f33 (the fix commit), on this PC:

- CPython 3.13.2, the tree with the fetched reference files (CLDR 48.2.0 in place of
  48.0.0) and Node 24.18.0 for the live oracle: 538 passed, 1 skipped (the opt-in
  installed-wheel test), doctests included.
- Gates: `ruff format --check .`, `ruff check .`, `mypy --strict src` and
  `mypy --strict src tests` each exit 0. No source file is over 200 lines.
- CPython 3.11.5: a probe of the new behaviour (aliases, likely scripts, a 100,000-digit
  round trip, the CLI grammar) passes. The interpreter matrix was not rerun: every machine
  stayed busy with other work for this session (`recurso.sh ver`), so it is left to lens
  d's re-check. The new code uses only what 3.10 has (`int.to_bytes` with a positional byte
  order, `decimal.MAX_PREC`, builtin generics at run time).

### Round 6 (2026-10-27, at 1e6503a)

Lenses a, c and e re-checked round 5 at 1e6503a. Every round 5 finding they re-ran is fixed
(lens a: F1 to F3; lens c: F1, with 100,000 digits now 66.7 ms to parse and 29.5 ms to
format on a desktop; lens e: F1 to F5, each old mutant killed). They reported 5 new findings:
a: 1, c: 1, e: 3. None is disputed. All are fixed in 8fea04c, the contract tests first.

| Finding | Severity | Fix |
| --- | --- | --- |
| a-N1 | low | Docs only; the behaviour already matched CLDR. The CHANGELOG no longer says a tag that names its language's likely script reads the same locale as without it: it is looked up without that script, and since its script is known, the region's likely script is not added, so `ku-Latn-GE` reads `ku` while `ku-GE` (`ku-Cyrl-GE`) reads the root. README and GUIDE give the same reason, and the GUIDE likely-script rule names `ku-Latn-GE` and `ky-Cyrl-CN`. Test: `test_locale_aliases::test_a_named_likely_script_skips_the_region_s_likely_script` |
| c-N1 | medium | A regression from 9ef91df: on a 32-bit CPython, whose `decimal.MAX_EMAX` is 425,000,000, an exponent past that crashed the command line with `InvalidOperation` and status 1. `_cli._convert` now clamps the exponent to 100,000 plus the length of the mantissa plus 2 instead of capping it at nine digits. Past that clamp the value is zero or past the digit bound whatever the exponent, so no result changes (12,000 seeded spellings near and past the bound give the same output or error as the old cap on 64-bit), and the exponent stays far inside every build's limit. On the 32-bit CPython 3.13.11 of lens c, `1e500000000`, `1e999999999`, `1e99999999999`, `1e-99999999999`, `+.590E-896824052` and `80E-156207682318855` now exit 2 with one line, by argv and by stdin, and `0e99999999999` prints `0`. CHANGELOG states it. Test: `test_cli_values::test_a_huge_exponent_stays_within_the_limits_of_a_32_bit_build`, which swaps in a `Decimal` with the 32-bit exponent limit: 5 failures on 1e6503a, all pass after |
| e-N1 | medium | `test_number::test_int_subclass_methods_are_never_called`: an int subclass whose `to_bytes`, `bit_length`, `__neg__` and `__lt__` lie formats like the plain int through `format_indian` and `format_number`, short, negative and past 4,300 digits |
| e-N2 | low | `test_cli_values::test_every_plain_decimal_spelling_formats`: exponents of ten or more characters, mostly leading zeros, unsigned, `+` and `-` (`1e0000000005`, `1e+0000000003`, `7E00000000000000000002`, `25e-0000000001`, `-4E-00000000002`) |
| e-N3 | low | The comment was false and the loop stopped after four rules. UTS #35 applies the alias rules until none matches, and a tag with more legacy variants needed more passes: `ca-ES-arevela-bokmal-lojban-nynorsk-saaho-xiang-valencia` read `ca` instead of `ca-ES-valencia`. `_tag._legacy` now loops until no rule matches. A rule removes the subtags it matched and no replacement brings them all back, so each rule applies at most once, and the bound of one pass per rule is only a guard. The docstring, GUIDE and CHANGELOG say the rules chain (`zh-cmn-yue` is `zh-yue`, then `yue`). Test: `test_locale_aliases::test_the_rules_apply_until_none_matches` (`zh-cmn-yue`, `zh-guoyu-yue`, `zh-cmn-Hant-gan`, `zh-cmn-GB-hakka` and the six-rule chain): it fails on 1e6503a and passes after |

Mutation check, one mutant at a time on this PC (CPython 3.13.2, bytecode writing off):

| Mutant | First catcher |
| --- | --- |
| e-N1: `to_decimal(int.__int__(value))` to `to_decimal(value)` | `test_number::test_int_subclass_methods_are_never_called` |
| e-N2: exponent leading zeros no longer stripped | `test_cli_values::test_every_plain_decimal_spelling_formats[argv8-...]` |
| e-N3: legacy rules applied once (`range(1)`) | `test_locale_aliases::test_the_rules_apply_until_none_matches` |
| e-N3: legacy rules applied at most four times (the 1e6503a loop) | `test_locale_aliases::test_the_rules_apply_until_none_matches` |
| c-N1: the 1e6503a nine-digit cap | `test_cli_values::test_a_huge_exponent_stays_within_the_limits_of_a_32_bit_build[1e500000000-...]` |

Runs at 8fea04c:

- Gates on this PC: `ruff format --check .`, `ruff check .`, `mypy --strict src` and
  `mypy --strict src tests` each exit 0. No source file is over 200 lines.
- Full suite on Elena's PC (CPython 3.14, a clean venv on a copy of the tracked files, a turn
  taken): every test passed, doctests included, and 18 skipped there (no Node, no git
  checkout, no POSIX shell, the opt-in installed-wheel test, no fetched reference files).
- CPython 3.13.2 on this PC, with Node 24.18 and the fetched reference files: the doctests,
  the changed test files and the files Elena skipped (`test_cli_streams`, `test_docs`,
  `test_oracle_intl`, `test_intl`, `test_sources`) pass.
- The 32-bit CPython 3.13.11 (lens c's interpreter): the CLI cases of c-N1 above.

### Round 7 (2026-10-27, at d95a548)

Lens e re-checked round 6 at d95a548. Its three round 6 findings are fixed: each re-applied
mutant is killed. It ran 20 new mutants on `_cli._convert` and `_tag._legacy`: 12 killed, 5
proven equivalent, 3 surviving and not equivalent, reported as 3 findings. None is disputed.
All three are missing contracts, not behaviour bugs: the code already gave the right result,
so no source file and no documented behaviour changes, and the CHANGELOG has nothing to add.
The new tests are in ec8a8e7.

| Finding | Severity | Fix |
| --- | --- | --- |
| e-N1-K03 | low | `test_cli_values::test_values_past_the_digit_bound_say_so` gains `.0001e100005`, `-.001e100004` and `+.001e100003`: leading fractional zeros put them past the bound only through an exponent past 100,002, so they pin that the exponent clamp counts the mantissa's length. Each exits 2 with the integer-part error |
| e-N2-K10 | low | `test_cli_values::test_values_at_the_digit_bound_written_with_an_exponent_as_long_as_the_bound`: `1e-100000`, `0.001e100002`, `0.1e100000` and `-.1e100000` exit 0 and print exactly 100,000 digits in the fraction or the integer part, ungrouped and grouped |
| e-N3-L02 | low | `test_locale_aliases::test_the_rules_apply_until_none_matches` pins the longest visible chain, nine rules (`ca-ES-aaland-arevela-arevmda-bokmal-hakka-lojban-nynorsk-saaho-xiang-valencia` reads `ca-ES-valencia`), and a seven-rule chain before be's own variant (`be-arevela-arevmda-bokmal-hakka-lojban-nynorsk-saaho-tarask` reads `be-tarask`) |

Mutation check, one mutant at a time on this PC (CPython 3.13.2, bytecode writing off),
running the changed test file:

| Mutant | First catcher |
| --- | --- |
| e-N1-K03: `bound = str(MAX_DIGITS + 2)` | `test_cli_values::test_values_past_the_digit_bound_say_so[.0001e100005-integer part]` |
| e-N2-K10: `len(exponent) >= len(bound)` | `test_cli_values::test_values_at_the_digit_bound_written_with_an_exponent_as_long_as_the_bound[1e-100000]` |
| e-N3-L02: legacy rules applied at most six times (`range(6)`) | `test_locale_aliases::test_the_rules_apply_until_none_matches` |
| e-N3-L02: at most seven times (`range(7)`) | `test_locale_aliases::test_the_rules_apply_until_none_matches` |
| e-N3-L02: at most eight times (`range(8)`) | `test_locale_aliases::test_the_rules_apply_until_none_matches` |

Runs at ec8a8e7:

- Gates on this PC: `ruff format --check .`, `ruff check .`, `mypy --strict src` and
  `mypy --strict src tests` each exit 0. No source file is over 200 lines.
- Full suite on Elena's PC (CPython 3.14.2, a clean venv on a fresh clone of the pushed
  branch, a turn taken): exit 0, every test passed, doctests included, and 16 skipped there
  (no Node, no POSIX shell, the opt-in installed-wheel test, no fetched reference files).
- CPython 3.13.2 on this PC: the two changed test files pass.

### Round 8 (2026-10-27, at 1e103c2)

Lens e re-checked round 7 at 1e103c2. Its three round 7 findings are fixed: each re-applied
mutant is killed, locally and in the full suite. It ran 10 new mutants on `_cli._convert` and
`_tag._legacy`: 8 killed, 1 proven equivalent and 1 surviving and not equivalent, which it
reported with a second, related finding. None is disputed. Both are behaviour bugs in how
`_tag._legacy` rebuilt the tag between two rules, fixed in a10bba6 with the contract tests
first; the CHANGELOG and GUIDE state the new behaviour.

| Finding | Severity | Fix |
| --- | --- | --- |
| e-N4-M09 | low | Each rule used to rebuild the tag with the replacement's variants in front of the subtags the tag had left, so the next rule read the tag's own script or region as a variant: `be-arevela-Latn` read `und` (`be-Latn`) but `be-arevela-hepburn-heploc-Latn` read `be`, and `ja-arevela-abc` raised `ValueError` but `ja-hepburn-heploc-abc` read `ja`. `_legacy` now keeps the tag's own subtags and the replacements' apart until no rule matches, then reads what the tag has left as a tag (its own script and region first) and adds the replacements' script and region where it has none and their variants after its own. A chain of rules now reads what one rule does, in any order. On the lens's 2,432 probe tags, 340 change: 300 now raise `ValueError` (the extended language subtag of e-N5-X01) and 40 chains now read their single-rule result (`be-arevela-hepburn-heploc-Latn` reads `und`, `sv-aaland-arevela-US` reads `sv`, `zh-arevela-aaland-US` reads `zh-Hant`); Node 24.18 with ICU 78.3 rejects all 340 with `RangeError`, so only tags BCP 47 calls ill-formed change. Tests: `test_locale_chains::test_a_chain_of_rules_reads_what_one_rule_reads`, `test_the_script_the_rules_uncover_is_the_tag_s_script` (both fail on 1e103c2) and `test_the_order_of_the_legacy_subtags_does_not_matter` |
| e-N5-X01 | low | An extended language subtag was accepted when a legacy rule matched later in the tag, because the rule's region or variant landed in front of it: `be-abc-aaland` read `be`, `sv-abc-aaland` read `sv-AX`, `en-abc-gb-oed` read `en-GB`, `ja-abc-hepburn-heploc` read `ja`. The fix of e-N4-M09 keeps a three-letter subtag that follows the language once the rules have removed theirs in that place, so `parse_tag` refuses it as it refuses `be-abc`; one a rule consumes (`zh-yue-HK`, `zh-cmn-yue`, `zh-min-nan`) is still read. The same holds for one the rules uncover: `ja-aaland-abc` is `ja-abc` with the region `AX` and now raises `ValueError` as `ja-arevela-abc` did. Tests: the four tags of the finding join `test_locale_aliases::test_other_extended_language_subtags_are_value_errors`, and `test_locale_chains::test_an_extended_language_subtag_the_rules_leave_is_a_value_error` and `test_an_extended_language_subtag_a_rule_consumes_is_read` pin the rest; the new cases fail on 1e103c2 |

Mutation check, one mutant at a time on this PC (CPython 3.13.2, bytecode writing off),
running the changed test files:

| Mutant | First catcher |
| --- | --- |
| e-N5-X01: no slot for the extended language subtag (`extended = []`) | `test_locale_chains::test_an_extended_language_subtag_the_rules_leave_is_a_value_error[ja-aaland-abc]` |
| e-N5-X01: the extended language subtag placed after the script and region | `test_locale_chains::test_an_extended_language_subtag_the_rules_leave_is_a_value_error[ja-aaland-abc]` |
| e-N4-M09: the replacements merged into the tag after each rule (the 1e103c2 model) | `test_locale_aliases::test_a_replacement_of_und_names_the_root_and_the_tag_keeps_its_fields` |
| e-N4-M09: the script the rules uncover ignored | `test_locale_chains::test_the_script_the_rules_uncover_is_the_tag_s_script` |
| e-N4-M09 analogue: the replacements' variants before the tag's own | equivalent, see below |

The last mutant only swaps the order of two kinds of variant, so it changes a result only for
a tag that has both, that is two or more variants. `resolve_locale` looks a variant up only as
the whole joined list (`base-v1-v2`), and every CLDR 48.2 locale with a variant has exactly
one (`be-tarask`, `ca-ES-valencia`, `el-polyton`), so such a tag falls back to its base either
way. Run on the lens's 2,432 probe tags, the mutant and a10bba6 give 0 differences in
`resolve_locale` and `format_number`.

Runs at a10bba6:

- Gates on this PC: `ruff format --check .`, `ruff check .`, `mypy --strict src` and
  `mypy --strict src tests` each exit 0. No source file is over 200 lines.
- Full suite on Elena's PC (CPython 3.14, a clean venv on a fresh clone of the pushed branch,
  a turn taken): exit 0, 591 passed, doctests included, and 16 skipped there (no Node with
  ICU 78.3, no POSIX shell, the opt-in installed-wheel test, no fetched reference files).
- CPython 3.13.2 on this PC, with Node 24.18 (ICU 78.3) and the fetched reference files:
  `test_sources`, `test_oracle_intl`, `test_intl`, `test_docs` and the two changed test files
  pass with no skip (130 passed).

### Disputed findings

None.
