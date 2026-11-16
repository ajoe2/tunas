# Contributing to tunas

## Development Setup

The project is managed with [`uv`](https://docs.astral.sh/uv/) and requires Python 3.12+.

```bash
git clone https://github.com/ajoe2/tunas
cd tunas
uv sync
```

CI runs these on push:

```bash
uv run pytest --cov=tunas           # offline tests, 95% coverage gate
uv run ruff check
uv run ruff format                  # CI runs with --check
uv run mypy src/tunas               # strict
uv run mkdocs serve                 # preview docs at http://localhost:8000
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
│   ├── enums.py                SDIF / Hy-Tek code enums
│   ├── geography.py            LSC, US state, and country enums
│   ├── event.py                Event enum
│   ├── exceptions.py           Error hierarchy
│   ├── models.py               Slotted domain dataclasses
│   ├── parser.py               read_cl2, read_hy3, MeetArchive, ParseReport, ParseWarning
│   ├── standards.py            Time-standards lookups
│   ├── _parser/                Record parsing engines (internal)
│   └── _data/                  Bundled standards JSON and SDIF spec
├── tests/                  Pytest suite (fully self-contained, no network)
│   ├── conftest.py             Shared record builders + fixtures
│   ├── unit/                   Value types, enums, models, standards (no file I/O)
│   ├── cl2/                    `read_cl2` records, I/O, diagnostics, golden meets
│   ├── hy3/                    `read_hy3` records, I/O, golden meet
│   └── data/                   Committed real `.cl2`/`.hy3` meets + golden expected JSON
├── scripts/                Developer tools (standards sheet converter)
├── docs/                   MkDocs markdown documentation source
└── .github/workflows/      CI (test.yml), docs (docs.yml), PyPI release (publish.yml)
```

## Testing

Every change needs tests. Real-world coverage comes from committed "golden" meet files in `tests/data/` compared against expected-state JSON; no network is needed.

Fixed-width record builders live in `tests/conftest.py` (`from conftest import ...`). Put new tests in `unit/`, `cl2/`, or `hy3/`.

### Regenerating Golden Files

`tests/data/build_expected*.py` are independent decoders that don't import `tunas`, so a parser regression can't silently rewrite the expected state. Re-run one only when a fixture's expected state legitimately changes, and review the diff:

```bash
uv run python tests/data/build_expected.py        # Reno (individual events)
uv run python tests/data/build_expected_aaa.py    # AAA (relays)
uv run python tests/data/build_expected_hy3.py    # PASA (.hy3)
```

## Documentation

Update docs with code changes. CI runs `mkdocs build --strict`, so broken links fail.

## Pull Requests

- Branch from `main` and keep PRs focused.
- All CI gates must pass.
- Add a `CHANGELOG.md` entry ([Keep a Changelog](https://keepachangelog.com/) format).

## Releasing (Maintainers)

Publishing uses PyPI Trusted Publishing (OIDC):

1. Bump `__version__` in `src/tunas/_version.py`.
2. Move unreleased `CHANGELOG.md` entries to a new version heading.
3. Create a GitHub Release matching the version tag (e.g. `v0.3.0`).

`publish.yml` verifies the tag, builds, runs `twine check`, and uploads to PyPI. `docs.yml` deploys the site to GitHub Pages.

PyPI's Trusted Publisher is registered for owner `ajoe2`, repo `tunas`, workflow `publish.yml`, environment `pypi`.
