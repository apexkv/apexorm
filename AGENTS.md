# Repository Guidelines

## Project Structure & Module Organization
- `apexorm/`: package root. Core entry in `apexorm/__init__.py` (ApexORM, DB binding, migration).
- `apexorm/models/`: ORM internals — `__init__.py` (Model, ModelMeta), `manager.py` (Manager), `queryset.py` (QuerySet/Q), `fields.py`, `relations.py`, `m2m.py`.
- `apexorm/connection/`: simple DB adapters (`SQLiteDB`, `MysqlDB`, `PostgresDB`).
- `test/`: pytest suite (`test_*.py`, `conftest.py`).
- `pyproject.toml`: Python 3.11+, setuptools build.

## Build, Test, and Development Commands
- Create env and install (editable): `python -m pip install -e .` (optionally `-e .[argon2,bcrypt]`).
- Run all tests (quiet): `pytest -q`.
- Filter tests: `pytest -k relations`.
- Show failures verbosely: `pytest -vv`.

## Coding Style & Naming Conventions
- Python 3.11+, 4‑space indentation, type hints where practical.
- Names: modules/files `snake_case.py`; classes `PascalCase`; methods/vars `snake_case`.
- Strings: prefer double quotes; docstrings use triple double quotes.
- Keep public API minimal; don’t alter unrelated behavior when fixing a bug.
- Follow existing patterns in `models/__init__.py`, `queryset.py`, and tests.

## Testing Guidelines
- Framework: pytest. Tests live in `test/` and are named `test_*.py`.
- Use fixtures from `test/conftest.py` (notably `orm` with `SQLiteDB(tmp_path)`).
- Add tests alongside similar ones (e.g., extend `test_crud_and_queryset.py`).
- Aim to cover new branches/edge cases; ensure idempotent tests (DB is reset by fixtures).

## Commit & Pull Request Guidelines
- Commits: concise, imperative subject (≤72 chars). Example: `queryset: support iendswith lookup`.
- Include a brief body explaining rationale and impact when non-trivial.
- PRs: clear description, reference issues, list behavior changes, and test coverage notes. Include reproduction steps for bug fixes.

## Security & Configuration Tips
- Prefer `SQLiteDB` for local dev; avoid hardcoding credentials in tests.
- For external DBs, use env vars and project `DB` helpers to build connection strings.
