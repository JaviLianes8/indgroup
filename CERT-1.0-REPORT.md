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
| 12 | Dated CHANGELOG section | PASS: 1.0.0, 2026-10-25 |
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
