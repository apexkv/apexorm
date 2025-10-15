# Repository Guidelines

## Project Structure & Module Organization
- `apexorm/`: package root. Entry in `apexorm/__init__.py` (ApexORM, DB binding, migration).
- `apexorm/models/`: ORM internals — `__init__.py` (Model, ModelMeta), `manager.py` (Manager), `queryset.py` (QuerySet/Q), `fields.py`, `relations.py`, `m2m.py`.
- `apexorm/connection/`: database adapters (`SQLiteDB`, `MysqlDB`, `PostgresDB`).
- `test/`: pytest suite (`test_*.py`, `conftest.py`).
- `pyproject.toml`: Python 3.11+, setuptools build config.

## Build, Test, and Development Commands
- Install in editable mode: `python -m pip install -e .` (optionally `-e .[argon2,bcrypt]`).
- Run all tests (quiet): `pytest -q`.
- Filter tests by keyword: `pytest -k relations`.
- Show failures verbosely: `pytest -vv`.

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indentation; add type hints where practical.
- Names: modules/files `snake_case.py`; classes `PascalCase`; methods/vars `snake_case`.
- Strings: prefer double quotes; docstrings use triple double quotes.
- Keep the public API minimal; do not alter unrelated behavior when fixing bugs.
- Follow patterns in `apexorm/models/__init__.py`, `apexorm/models/queryset.py`, and tests.

## Testing Guidelines
- Framework: pytest. Tests live in `test/` and are named `test_*.py`.
- Use fixtures from `test/conftest.py` (notably `orm` using `SQLiteDB(tmp_path)`).
- Add tests alongside similar ones (e.g., extend `test_crud_and_queryset.py`).
- Aim for idempotent tests; DB is reset by fixtures. Cover new branches and edge cases.

## Commit & Pull Request Guidelines
- Commits: concise, imperative subject (≤72 chars). Example: `queryset: support iendswith lookup`.
- Include a brief body for non-trivial changes: rationale and impact.
- PRs: clear description, link issues, list behavior changes, and test coverage notes. Include reproduction steps for bug fixes.

## Security & Configuration Tips
- Prefer `SQLiteDB` for local development. Avoid hardcoding credentials in tests.
- For external DBs, use env vars and the project `DB` helpers to build connection strings.

## Agent-Specific Notes
- This AGENTS.md applies to the repository root and all subdirectories.
- If conflicting AGENTS.md files appear in nested folders, the deeper file takes precedence.
- Direct instructions from maintainers (issues/PRs) override general guidance here.
