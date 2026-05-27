# Contributing to tunas

Thank you for helping improve `tunas`! This guide covers development setup, testing requirements, and the release process.

## Development Setup

The project is managed with [`uv`](https://docs.astral.sh/uv/) and requires Python 3.12+.

```bash
git clone https://github.com/ajoe2/tunas
cd tunas
uv sync            # Set up virtual environment and install all dependencies
```

Run tools via `uv run` to use the project environment. CI enforces these gates on push:

```bash
uv run pytest                       # Run full offline test suite
uv run pytest --cov=tunas           # Run with the 95% coverage gate
uv run ruff check                   # Lint codebase
uv run ruff format                  # Auto-format code (CI runs with --check)
uv run mypy src/tunas               # Strict type-check
uv run mkdocs serve                 # Preview documentation locally at http://localhost:8000
```

## Project Layout

```
tunas/
├── pyproject.toml          Project metadata and build config (Hatchling)
├── README.md               PyPI long-description
├── LICENSE                 MIT License
├── CHANGELOG.md            Semantic version changelog
├── mkdocs.yml              MkDocs (Material) site configuration
├── src/tunas/              Source package (src-layout)
│   ├── __init__.py             Public API exports
│   ├── py.typed                PEP 561 type-marker
│   ├── _version.py             Package version
│   ├── time.py                 Time value type
│   ├── enums.py                SDIF enums
│   ├── geography.py            LSC, US state, and country enums
│   ├── event.py                Event enum and helper properties
│   ├── exceptions.py           Error hierarchy
│   ├── models.py               Slotted domain dataclasses
│   ├── parser.py               read_cl2, read_hy3, MeetArchive, ParseReport, ParseWarning
│   ├── standards.py            Time-standards lookups
│   ├── _parser/                Per-record parsing logic (internal)
│   └── _data/                  Bundled package data (JSON standards, spec doc)
├── tests/                  Pytest suite (fully self-contained, no network)
│   ├── conftest.py             Shared record builders + fixtures
│   ├── unit/                   Value types, enums, models, standards (no file I/O)
│   ├── cl2/                    `read_cl2` records, I/O, parallelism, diagnostics, golden meets
│   ├── hy3/                    `read_hy3` records, I/O, golden meet
│   └── data/                   Committed real `.cl2`/`.hy3` meets + golden expected JSON
├── scripts/                Developer tools (e.g., standard sheets parser)
├── docs/                   MkDocs markdown documentation source
└── .github/workflows/      CI (test.yml) and PyPI release (publish.yml)
```

## Testing

Every change must include test coverage. The test suite is fully offline, comparing committed "golden" meet files under `tests/data/` against expected-state JSON.

Shared fixed-width record builders live in `tests/conftest.py` (`from conftest import ...`). Place new tests in the folder matching their coverage (`unit/`, `cl2/`, or `hy3/`).

### Regenerating Golden Files

The scripts under `tests/data/build_expected*.py` are independent reference decoders that read raw columns directly without importing `tunas`. This ensures regressions are caught rather than silently accepted. Only re-run them when a fixture's expected state legitimately changes, and carefully verify the diff:

```bash
uv run python tests/data/build_expected.py        # Reno (individual events)
uv run python tests/data/build_expected_aaa.py    # AAA (relays)
uv run python tests/data/build_expected_hy3.py    # PASA (.hy3)
```

## Documentation

Update documentation alongside code changes. CI builds the docs using `mkdocs build --strict`; broken links or references will fail the build.

## Pull Requests

- Branch from `main` and keep PRs focused.
- Ensure all linting, formatting, type-checking, and coverage-gated tests pass.
- Add a `CHANGELOG.md` entry under the appropriate section following the [Keep a Changelog](https://keepachangelog.com/) format.

## Releasing (Maintainers)

Publishing is automated via PyPI Trusted Publishing (OIDC):

1. Bump `__version__` in `src/tunas/_version.py`.
2. Move unreleased `CHANGELOG.md` entries to a new version heading.
3. Create a GitHub Release matching the version tag (e.g. `v0.3.0`).

The `publish` workflow verifies the tag, builds the package, runs `twine check`, and uploads to PyPI. The `docs` workflow deploys the documentation site to GitHub Pages.
