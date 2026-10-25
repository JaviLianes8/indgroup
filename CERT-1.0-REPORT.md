# indgroup 1.0.0 certification report

The 1.0.0 certification bar applied to indgroup. Nothing is on PyPI yet
(`https://pypi.org/pypi/indgroup/json` answered 404 on 2026-10-25), so 1.0.0 is the first
release and there is no upgrade path to check; the CHANGELOG still lists every change
against 0.2.0, the last tagged state of `main`.

Progress:
- [x] Branch `release/1.0.0` created from `main` (e5cecf8, version 0.2.0)
- [ ] Baseline gates on 0.2.0
- [ ] API review and 1.0.0 changes (item 1)
- [ ] Errors, typing, docstrings and doctests (items 2 to 5)
- [ ] Ground truth: CLDR, ICU and UTS #35 re-fetched, Intl.NumberFormat re-run (item 7)
- [ ] Contract, fuzz and author mutation round (items 6, 9, 18)
- [ ] Docs: README, GUIDE, CHANGELOG (items 11, 12)
- [ ] Packaging, e2e, every Python (items 8, 10, 13, 14)
- [ ] Gates (item 15)
- [ ] PR and trace guard
- [ ] Five QA lenses report PASS (item 19)
- [ ] Independent reviewer reports PASS (item 16)

## Defects found in 0.2.0 (reproduced on 2026-10-25)

- `format_number(Decimal("1E-3000000"), "en")` writes three million fraction digits: the
  integer digits are bounded but the fraction digits are not, so `Decimal("1E-999999999")`
  would build a gigabyte of text.
- Error messages quote the whole input: `parse_number("x" * 100000, "en")` raises a
  `ValueError` of 100,033 characters, `resolve_locale("a" * 100000)` one of 100,020.
- `indgroup --parse` with an integer of more than 4300 digits exits 2 with the
  `int` string conversion limit message, although `parse_number` reads it.
