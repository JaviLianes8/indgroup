# Contributing

Thanks for taking the time. This project keeps a small, predictable shape.

## Setup

```
pip install -r requirements-dev.txt
```

## Before you open a pull request

- Keep public API in `src/indgroup/__init__.py`; internals live in `_`-prefixed modules.
- Add a test for the behaviour you change. Unit tests are pure: no clock, no network, no
  files beyond the package's own data. A few test files reach further on purpose: the
  timing tests read the clock, the docs tests read README and GUIDE and run `git`, the CLI
  tests start `python -m indgroup`, the source and Intl tests read the fetched reference
  files and run Node (they skip while a file or Node is absent), and the wheel test
  (`INDGROUP_E2E=1`) builds the package and installs it into a throwaway venv.
- Run `scripts/check.ps1` (format, lint, types, tests) and make sure it passes.
- One logical change per commit, imperative subject line.

Open an issue first if the change is large or shifts the public API.
