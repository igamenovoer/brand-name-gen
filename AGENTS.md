# Repository Guidelines

## Project Structure & Module Organization
- Source: `src/brand_name_gen/` (`core.py`, `cli.py`, `__init__.py`)
- Tests: `tests/` (pytest). Example: `tests/test_basic.py`
- Docs: `docs/` (MkDocs Material). Config: `mkdocs.yml`
- Context (AI workspace): `context/` (see `context/README.md`)
- CI/CD: `.github/workflows/` (CI, Docs, PyPI)
- Packaging: `pyproject.toml` (hatchling, src-layout)

## Build, Test, and Development Commands
- `pixi run test` – run unit tests (quiet)
- `pixi run test-cov` – run tests with coverage
- `pixi run lint` / `pixi run format` – Ruff check/format
- `pixi run typecheck` – mypy static types
- `pixi run quality` – lint + typecheck + tests
- `pixi run build` – build wheel/sdist (`dist/`)
- `pixi run docs-serve` – live docs server; `pixi run docs-deploy` to publish
- CLI quick check: `brand-name-gen-cli generate eco solar --style modern --limit 5`

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indentation, line length 100
- Tools: Ruff, mypy (configured in `pyproject.toml`)
- Names: modules/functions `snake_case`, classes `PascalCase`, constants `UPPER_CASE`
- Public API exposed via `brand_name_gen.__init__`

## Testing Guidelines
- Framework: pytest; place tests under `tests/`
- Name tests `test_*.py`; keep fast and isolated
- Run locally with `pixi run test` (or `PYTHONPATH=src pytest` if not using pixi)

## Commit & Pull Request Guidelines
- Prefer Conventional Commits: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`
- PRs must include: summary, scope, screenshots (if CLI output), and linked issues
- Update docs (`docs/`) and context notes (`context/logs/`, `context/plans/`) when behavior changes

## Security & Configuration Tips
- Publishing: set GitHub secret `PYPI_API_TOKEN` for `.github/workflows/publish-pypi.yml`
- Docs: enable GitHub Pages (gh-deploy uses `gh-pages` branch)

## Agent-Specific Instructions
- Use the `context/` directory for plans, logs, and decisions; start files with the HEADER block
- Keep changes minimal and focused; mirror edits in tests and docs where applicable
- When adding features, expose them via CLI (`project.scripts`) and document in `docs/usage.md`
