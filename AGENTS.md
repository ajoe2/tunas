# Agent Guide

`tunas` is a Python 3.12 library (src-layout, managed with `uv`) that parses SDIF `.cl2` and Hy-Tek `.hy3` swim files. Always run tools through `uv run`, never bare `pip`/`python`. [CONTRIBUTING.md](CONTRIBUTING.md) has the project layout and release steps.

## Commands
- **Sync:** `uv sync` (add a dependency with `uv add <package>`, `--dev` for tooling)
- **Test:** `uv run pytest` (CI: `uv run pytest --cov=tunas`, 95% gate)
- **Lint / format:** `uv run ruff check .` and `uv run ruff format .`
- **Type check:** `uv run mypy src/tunas` (strict)
- **Docs:** `uv run mkdocs build --strict`

## Rules
- Every change needs tests; run all of the checks above before shipping.
- Update the docs (`README.md`, `docs/`, public docstrings that feed the API reference) with any code change.
