# Architecture

This document describes how `tunas` is organized, the design decisions behind
the public API, and what is intentionally out of scope. It also includes
publishing instructions so a release can be cut by hand.

## What `tunas` is (and isn't)

`tunas` is a **data-access library** for USA Swimming meet results. It reads
`.cl2` files (the Hy-Tek SDIF v3 export format used across USA Swimming) into
clean Python objects, ships a few high-value convenience helpers, and bundles
USA Swimming time standards so qualifying-time lookups work out of the box.

The library is deliberately small. It is **not** an analysis framework, a
relay-optimization tool, a meet-management system, or a web scraper. The
intent is to give downstream developers a solid, well-typed, well-tested base
to build *their* tools on.

### Target user

A Python developer building a swim-analytics or coach-tool application who
wants:

- A first-class object model for swim meet data (no `dict`-of-`dict`s).
- A parser that handles the long tail of real-world `.cl2` quirks without
  crashing.
- Bundled qualifying-time standards so the application doesn't have to ship
  its own.
- A library that gets out of the way: no global state, no surprise I/O, no
  required dependencies.

### In scope for v1 (0.1.0)

- `.cl2` parsing — every SDIF v3 record type, including relay events and
  splits.
- Domain model — `Meet`, `Club`, `Swimmer`, `MeetResult`,
  `IndividualMeetResult`, `RelayMeetResult`, `RelayLeg`, `Split`,
  `SwimmerContact`.
- Value types — `Time`, `Event`, and a full set of SDIF enums.
- Convenience query methods on `Swimmer`, `Meet`, and `Club`.
- Time-standards lookup with bundled USA Swimming standards data.
- Lenient parsing with a detailed `ParseReport`; opt-in `strict=True` mode.
- Full type hints (`py.typed`).

### Explicitly out of scope for v1

- **Relay generation algorithms.** Parsing relay *results* is in scope;
  optimizing relay rosters is not.
- **Writing `.cl2` files.** Read-only for v1. SDIF-compliant emit (checksums,
  fixed-width formatting) is deferred until a real user need surfaces.
- **Web scraping.** No connectors to pacswim.org or other meet-result
  archives. Users bring their own files.
- **Visualization, CSV/JSON export helpers.** Examples appear in the
  [cookbook](cookbook.md) but no built-in functions ship in v1.

## Repository layout

```
tunas/
├── pyproject.toml          Project metadata; hatchling build backend
├── README.md               PyPI long-description
├── LICENSE                 MIT
├── CHANGELOG.md            Keep a Changelog style
├── src/tunas/              Source (src-layout)
│   ├── __init__.py             Public API re-exports
│   ├── py.typed                PEP 561 marker
│   ├── _version.py             Single source of truth for __version__
│   ├── time.py                 Time value type
│   ├── enums.py                Small SDIF enums
│   ├── geography.py            Large enums (LSC, State, Country)
│   ├── event.py                Event enum + helpers
│   ├── exceptions.py           Error hierarchy
│   ├── models.py               Meet / Club / Swimmer / result dataclasses
│   ├── parser.py               read_cl2 + ParseReport
│   ├── standards.py            Time-standards lookup
│   ├── _parser/                Per-record handlers (internal)
│   └── _data/                  Bundled package data
│       ├── standards-2025-2028.json
│       └── sdif-v3.txt             Verbatim copy of the SDIF v3 spec
├── tests/                  Pytest suite + .cl2 fixtures
├── scripts/                Developer-only utilities (e.g., xlsx→json converter)
├── docs/                   This documentation
└── .github/workflows/      CI (lint + type-check + tests)
```

The library uses the **src-layout** rather than a flat layout. This means the
package is only importable after install, which protects against accidentally
testing the working-tree copy when the installed wheel is what you actually
ship.

## Design decisions

### Parser: lenient by default, exhaustive `ParseReport`

`.cl2` files in the wild contain encoding errors, malformed swimmer IDs,
unparseable times, and ambiguous club records — usually because they were
hand-edited by a meet director or exported from buggy versions of Hy-Tek
Meet Manager. A library that raises on the first error is unusable on real
data.

`read_cl2` therefore defaults to `strict=False`. Malformed records are
**skipped** and a `ParseWarning` is appended to the returned `ParseReport`,
so callers can inspect or `assert not report.warnings` if they want
strictness without modifying behavior. Users who want hard failures pass
`strict=True`.

See [parsing.md](parsing.md) for the exhaustive list of edge cases handled.

### Domain model: dataclasses with computed views

Every domain class is a dataclass. Value types (`Time`, `Split`,
`SwimmerContact`, `ParseWarning`) are **frozen**; aggregates (`Meet`,
`Club`, `Swimmer`, `IndividualMeetResult`, `RelayMeetResult`) are mutable so
the parser can populate them incrementally as it reads.

There is **one source of truth** for results:

- `Meet.individual_results: list[IndividualMeetResult]`
- `Meet.relay_results: list[RelayMeetResult]`

Everything else — `Swimmer.meets`, `Swimmer.clubs`, `Swimmer.current_club`,
`Club.swimmers`, `Meet.swimmers`, etc. — is a computed `@property` derived
from those two lists. This eliminates the multi-list synchronization bug
class that plagued the original tunas codebase.

See [models.md](models.md) for every dataclass and its fields.

### `Time`: a single-int value type

`Time` stores `centiseconds: int` internally and exposes `minute`, `second`,
`hundredth`, `total_seconds`, and `centiseconds` as computed properties.
This makes ordering, hashing, addition, and subtraction trivial — and
correct, which the original codebase's separate min/sec/hundredth fields
were not.

### `Event`: a hand-rolled enum

`Event` is a 90+ member enum with `(distance, stroke, course)` tuple values.
Hand-rolling rather than generating provides IDE autocomplete
(`Event.FREE_100_SCY.<tab>`), is statically discoverable, and lets us add
helper classmethods like `Event.find(distance, stroke, course)` cleanly.

### Time standards: bundled data, no setup

The library ships USA Swimming time standards as a single JSON file under
`src/tunas/_data/standards-2025-2028.json`. The first call to
`qualifies_for(...)`, `standard_time(...)`, or `all_qualified(...)` lazily
loads and caches the file via `importlib.resources`. From the library
user's perspective there is no setup — just call the function.

When USA Swimming publishes new standards, a new release ships the updated
JSON. Users get the new cutoffs by upgrading the library:

```
pip install --upgrade tunas
```

See [standards.md](standards.md) for the schema and the quad-versioning
policy.

### Zero runtime dependencies

`tunas` uses only the Python standard library at runtime. This keeps install
times fast, dependency-resolution simple, and makes the library safe to add
to any project regardless of its existing pin file. Dev-time dependencies
(`pytest`, `ruff`, `mypy`, `openpyxl` for the standards converter script)
live in the `[dependency-groups.dev]` section of `pyproject.toml` and are
not installed by end users.

### Pythonic API: properties over `get_x()` / `set_x()`

Every public attribute is exposed as a property, not via getter/setter
methods. Type hints flow through cleanly to IDEs and type-checkers. Mutable
fields are mutated directly — there is no encapsulation game being played.

## Phasing of this initial release

The library is being built in four phases:

1. **Scaffold + documentation** (this commit). Repository structure,
   `pyproject.toml`, and the full `docs/` tree. **No library code.** The
   user reviews these docs as the API contract.
2. **Implementation.** Build `enums.py` → `geography.py` → `time.py` →
   `event.py` → `exceptions.py` → `models.py` → `_parser/*` → `parser.py` →
   `standards.py` and wire up `__init__.py` re-exports.
3. **Tests.** Comprehensive pytest suite — every module, every record-type
   handler, every documented edge case. Coverage target: ≥ 95%.
4. **Publish prep.** Build the wheel, smoke-test in a clean venv, document
   manual publishing steps. The user publishes to PyPI by hand.

## Publishing

`tunas` is published to PyPI **manually**. There is no automated publish
workflow.

### One-time setup

1. Create a PyPI account at https://pypi.org and (optionally) a TestPyPI
   account at https://test.pypi.org.
2. Create an API token under *Account settings → API tokens*. Scope it to
   the `tunas` project once the first release is up; for the very first
   release scope it to the whole account.
3. Store the token where `uv publish` can find it. The simplest option is:
   ```
   export UV_PUBLISH_TOKEN=pypi-xxxxx
   ```

### Per-release steps

From the repository root, on a clean working tree:

```
# 1. Bump the version
$EDITOR src/tunas/_version.py     # set __version__ = "X.Y.Z"
$EDITOR pyproject.toml            # set version = "X.Y.Z"
$EDITOR CHANGELOG.md              # move Unreleased entries under [X.Y.Z]

# 2. Sanity check
uv sync
uv run ruff check && uv run ruff format --check
uv run mypy src/tunas
uv run pytest --cov=tunas --cov-fail-under=95

# 3. Build the wheel + sdist
rm -rf dist/
uv build

# 4. Verify the build
uv run --with twine twine check dist/*

# 5. (Optional but recommended) Smoke-test in a clean venv
python -m venv /tmp/v
/tmp/v/bin/pip install dist/*.whl
/tmp/v/bin/python -c "from tunas import read_cl2, qualifies_for; print('ok')"
rm -rf /tmp/v

# 6. (Optional) Dry-run on TestPyPI first
uv publish --publish-url https://test.pypi.org/legacy/

# 7. Publish to PyPI
uv publish

# 8. Tag the release and push
git tag vX.Y.Z
git push --tags
```

### Notes

- Always **bump the version** in both `pyproject.toml` and
  `src/tunas/_version.py`. PyPI rejects re-uploads of the same version, so a
  mismatch will surface immediately.
- The `dist/` directory should be cleaned before each build to avoid
  accidentally uploading stale artifacts.
- If `uv publish` reports the project name is taken, the fallback is
  `tunas-swim` — update `pyproject.toml`, `README.md`, and the `docs/` install
  instructions, then rebuild.
