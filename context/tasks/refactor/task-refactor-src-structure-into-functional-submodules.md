## What to Refactor

Restructure `src/brand_name_gen/` into clear functional submodules with cohesive responsibilities and typed public APIs. Consolidate helpers, remove cross‑cutting logic from CLI, and preserve backward compatibility via re‑exports.

Scope:
- Android ASO checks: `title_check.py`, `title_checker.py`
- Domain availability: `domain_check.py`, `domain_checker.py`
- Search engine ranking: `dataforseo/*` (new SDK modules already added)
- CLI `.env` utilities and HTTP glue currently sitting in `cli.py`
- Public API surface in `brand_name_gen.__init__`

## Why Refactor
- Improve maintainability and discoverability by grouping related code
- Enforce separation of concerns (SDK/service vs CLI)
- Strengthen typing and documentation per project guides
- Enable incremental growth (e.g., add Bing/YouTube rankers, more app stores)
- Simplify testing with module‑level boundaries (mocks at one seam)

## How to Refactor

1) Create subpackages
- `src/brand_name_gen/android/`
  - `title_check.py` (moved)
  - `title_checker.py` (moved)
  - `__init__.py` re‑exports
- `src/brand_name_gen/domain/`
  - `domain_check.py` (moved)
  - `domain_checker.py` (moved)
  - `__init__.py` re‑exports
- `src/brand_name_gen/search/`
  - `dataforseo/` (current SDK: `types.py`, `backends.py`, `google_rank.py`)
  - future: `bing/`, `youtube/`
- `src/brand_name_gen/utils/`
  - `env.py` (shared .env readers and precedence helpers)
  - `http.py` (future request/session helpers if needed)

2) Move files and adjust imports
- Update internal imports across modules and CLI
- Add `__init__.py` files to subpackages with explicit `__all__`

3) Preserve backward compatibility
- Re‑export key symbols at package root `brand_name_gen/__init__.py` (e.g., `generate_names`, `check_title_appfollow`, `check_title_playstore`, `is_com_available`)
- Option A (preferred): Keep original import paths working via root re‑exports only
- Option B (if needed): Add thin shims at old locations importing from new modules, marked deprecated

4) Refactor CLI to use SDK/services only
- Replace inline HTTP logic with calls to service/SDK modules (already done for DataForSEO)
- Centralize `.env` precedence logic in `utils/env.py` and import in CLI + SDKs

5) Update docs and tests
- Docs: update import paths; add a short “Module Map” section
- Tests: keep green by relying on root re‑exports; update targeted import paths only if necessary

6) Quality gates
- Run `pixi run quality` (ruff + mypy + tests)
- Verify no circular imports and public API stability

## Impact Analysis

Potential Risks
- Broken imports in downstream code or examples
- Subtle typing regressions if symbols aren’t re‑exported consistently
- CLI coupling to utils if not carefully isolated

Mitigations
- Provide root‑level re‑exports and keep names stable
- Add deprecated shim modules only if needed; mark with clear docstrings
- CI: run tests and mypy; check docs build

Runtime Behavior
- No functional changes; pure structural refactor with improved boundaries

## Expected Outcome
- A clean package layout by responsibility:
  - `brand_name_gen/android/*` for ASO checks
  - `brand_name_gen/domain/*` for RDAP/domain
  - `brand_name_gen/search/dataforseo/*` for ranking SDK
  - `brand_name_gen/utils/*` for shared helpers
- CLI remains thin and stable; API usage clearer and more discoverable

## Before/After Examples

Imports (library users)
```python
# Before
from brand_name_gen.title_check import check_title_appfollow, check_title_playstore
from brand_name_gen.domain_check import is_com_available

# After (preferred: stable via root re-exports)
from brand_name_gen import check_title_appfollow, check_title_playstore, is_com_available

# Or explicit submodules for clarity
from brand_name_gen.android.title_check import check_title_appfollow, check_title_playstore
from brand_name_gen.domain.domain_check import is_com_available
```

CLI glue (before vs after)
```python
# Before (inline HTTP in CLI command)
r = requests.post(url, json=[payload], auth=auth, timeout=timeout)

# After (service SDK)
from brand_name_gen.search.dataforseo.google_rank import DataForSEORanker
from brand_name_gen.search.dataforseo.types import GoogleRankQuery

ranker = DataForSEORanker.from_env()
res = ranker.run(GoogleRankQuery(keyword="hb-app"))
```

Shared .env access (centralized)
```python
# utils/env.py
def read_dotenv_value(key: str) -> str | None: ...

# usage in CLI/SDK modules
from brand_name_gen.utils.env import read_dotenv_value
```

## References
- Project guides: `magic-context/general/python-coding-guide.md`, `magic-context/instructions/strongly-typed.md`
- DataForSEO SDK docs (Context7): /dataforseo/pythonclient, /websites/docs_dataforseo_com-v3
- Current modules to move: `src/brand_name_gen/title_check.py`, `src/brand_name_gen/title_checker.py`, `src/brand_name_gen/domain_check.py`, `src/brand_name_gen/domain_checker.py`, `src/brand_name_gen/dataforseo/*`

