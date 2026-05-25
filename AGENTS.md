## Tooling & Commands

This project uses **`uv`** with **Python 3.12** for dependency and environment management. 

> ⚠️ **Important:** Avoid using bare `pip` or `python` commands. Always prefix with `uv`.

### Common Commands
* **Start the App:** `uv run main.py`
* **Add a Dependency:** `uv add <package>` *(Use `--dev` for development tools)*
* **Sync the Environment:** `uv sync`
* **Run a Tool or Script:** `uv run <command>`

---

## Documentation

Update the documentation immediately following any code changes to ensure it remains accurate and up to date.

---

## Testing

Every new feature must include accompanying test scripts to verify the correctness of the implementation. No code should be deployed without test coverage.