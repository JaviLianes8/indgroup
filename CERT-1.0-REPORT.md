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
| CLDR 48.0.0 numbers | https://registry.npmjs.org/cldr-numbers-full/-/cldr-numbers-full-48.0.0.tgz | d3d12515b0f6f7c4b5f82586b52b16164a0cffbf4d45a9f2bd894380a96b1cb3 |
| CLDR 48.0.0 core | https://registry.npmjs.org/cldr-core/-/cldr-core-48.0.0.tgz | 3b739a175e47e50905050a34612584fd5590c9352b11f36e3498eacff1c9aa94 |
| ICU 78.3 grouper | https://raw.githubusercontent.com/unicode-org/icu/release-78.3/icu4c/source/i18n/number_grouping.cpp | 6e7fc28bd2b6a365bffcad868f9618d6537b2b266b30830ef367e56f0f83a9bc |
| UTS #35 Numbers, rev. 76 | https://www.unicode.org/reports/tr35/tr35-76/tr35-numbers.html | be7b81e517dcbc9185aa131132254c2745aec7adec898d12d303187ad31e65b6 |

- The shipped table `src/indgroup/_cldr.json` is rebuilt from the two CLDR packages by
  `scripts/build_table.py` inside the suite and must equal the shipped file; every locale is
  then checked symbol by symbol against the CLDR JSON.
- The grouping rule is checked against ICU's `Grouper` source and the minimum grouping
  digits definition against the UTS #35 text.
- Independent oracle, recorded: `node scripts/intl_reference.mjs` with Node 24.18.0
  (ICU 78.3, CLDR 48.0, Unicode 17.0) writes 72,036 `Intl.NumberFormat` cases (every
  locale, four groupings, Latin digits). Re-run on 2026-10-25, the output was byte for
  byte the manifest hash `3bdad111b1e70cba476c92e96412b9177f957b75df8daef9cba874478ef54b62`. All cases match except the documented
  Swiss French group symbol, where ICU's own data differs from the CLDR JSON.
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

Runs on the fix:

- Elena's PC, CPython 3.14.2, the tree with the fetched reference files, `INDGROUP_E2E=1`:
  377 passed, 7 skipped (the installed-wheel test included). Skipped: the four closed-stream
  subprocess cases, which need a POSIX shell that PC does not have, and the live Intl oracle,
  because its Node has ICU 78.2.
- This PC, CPython 3.13.2 with Git's `sh` on the path: the four command-line test files,
  closed-stream cases included, pass.
- Gates: `ruff format --check .`, `ruff check .`, `mypy --strict src` and
  `mypy --strict src tests` each exit 0.

### Disputed findings

None.
