## HEADER
- Title: DataForSEO SERP API Integration (SDK Design)
- Purpose: Provide a typed, testable SDK-style module to query Google rankings via DataForSEO and expose a clean Python API used by the CLI and other components
- Status: Proposal → Implement
- Date: 2025-10-04
- Owner: core
- Dependencies: requests, dataforseo-client (official SDK), pydantic; env: DATAFORSEO_LOGIN, DATAFORSEO_PASSWORD
- Links: context/hints/howto-use-dataforseo-google-serp-api.md; magic-context/instructions/search-proactively.md; magic-context/general/python-coding-guide.md; magic-context/instructions/strongly-typed.md; ROADMAP.md

# Task: Design SDK for DataForSEO Functionality

This document proposes the architecture, public API, models, and implementation plan for integrating DataForSEO’s SERP API (Google Organic Live Advanced) as a typed Python SDK inside the project. The goal is to consolidate the temporary scripts and the CLI command into a reusable, strongly-typed module with clear error handling and tests.

## Goals & Non‑Goals
- Goals
  - Strongly-typed Python API for Google Organic rankings via DataForSEO
  - Support both HTTP (requests) and official SDK backends behind a common interface
  - Clean credential handling with `.env` precedence over `os.environ`
  - Pydantic models for inputs/outputs; mypy-friendly code
  - Unit tests with mocked responses; no live calls in CI
  - CLI `check-search-engine dataforseo` uses this SDK (no endpoint code in CLI)
- Non‑Goals
  - Asynchronous variant (can be a follow‑up)
  - Full coverage of all DataForSEO endpoints; we focus on Google Organic Live Advanced + lookups (optional)

## Module Layout (src)
- `src/brand_name_gen/dataforseo/types.py`
  - Pydantic models for requests/responses and common structures
- `src/brand_name_gen/dataforseo/backends.py`
  - Backend protocol and implementations (RequestsBackend, SdkBackend)
- `src/brand_name_gen/dataforseo/google_rank.py`
  - Public SDK entry points; service class(es); match logic

## Public API (Proposed)
```
# src/brand_name_gen/dataforseo/types.py
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field

class GoogleRankQuery(BaseModel):
    keyword: str
    se_domain: str = "google.com"      # e.g., google.com, google.co.uk
    location_code: int = 2840           # must be a valid DataForSEO location_code
    language_code: str = "en"           # DataForSEO language_code
    device: str = "desktop"             # desktop | mobile
    os: str = "macos"                   # macos | windows | android | ios
    depth: int = 50                     # number of results to fetch
    similarity_threshold: float = 0.9

class OrganicItem(BaseModel):
    rank_absolute: Optional[int] = None
    title: str
    url: Optional[str] = None

class GoogleRankResult(BaseModel):
    query: GoogleRankQuery
    top_position: Optional[int] = None
    matches: List[OrganicItem] = Field(default_factory=list)
    total_matches: int = 0
    check_url: Optional[str] = None

class DataForSEOError(Exception):
    """Base error for DataForSEO integration."""

class CredentialsMissingError(DataForSEOError):
    """Raised when login/password are not configured."""

class UnauthorizedError(DataForSEOError):
    """401 Unauthorized."""

class ForbiddenError(DataForSEOError):
    """403 Forbidden."""

class ApiResponseError(DataForSEOError):
    """Other non-success HTTP/API errors."""
```

```
# src/brand_name_gen/dataforseo/backends.py
from __future__ import annotations
from typing import Protocol, Any, Dict

class SerpBackend(Protocol):
    def google_organic_live_advanced(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call Google Organic Live Advanced and return raw JSON dict."""

class RequestsBackend:
    # Uses requests + HTTPBasicAuth
    ...

class SdkBackend:
    # Uses dataforseo-client (official SDK)
    ...
```

```
# src/brand_name_gen/dataforseo/google_rank.py
from __future__ import annotations
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
from .types import GoogleRankQuery, GoogleRankResult, OrganicItem,
    DataForSEOError, CredentialsMissingError, UnauthorizedError, ForbiddenError, ApiResponseError
from .backends import SerpBackend, RequestsBackend, SdkBackend

class DataForSEORanker:
    """Stateful service for Google ranking checks (follows m_ convention)."""

    def __init__(self) -> None:
        self.m_backend: Optional[SerpBackend] = None
        self.m_login: Optional[str] = None
        self.m_password: Optional[str] = None
        self.m_timeout_s: Optional[float] = None

    @classmethod
    def from_env(cls) -> "DataForSEORanker":
        inst = cls()
        # Precedence: .env in CWD > os.environ (resolved here, not mutating env)
        # Reuse a shared helper for .env lookup to match CLI behavior
        from brand_name_gen.cli import _read_dotenv_value  # small internal util reuse
        login = _read_dotenv_value("DATAFORSEO_LOGIN") or _read_dotenv_value("DATAFORSEO_USERNAME") or _read_dotenv_value("DATAFORSEO_EMAIL")
        password = _read_dotenv_value("DATAFORSEO_PASSWORD") or _read_dotenv_value("DATAFORSEO_PASS")
        import os
        inst.m_login = login or os.getenv("DATAFORSEO_LOGIN") or os.getenv("DATAFORSEO_USERNAME") or os.getenv("DATAFORSEO_EMAIL")
        inst.m_password = password or os.getenv("DATAFORSEO_PASSWORD") or os.getenv("DATAFORSEO_PASS")
        inst.m_timeout_s = 30.0
        inst.m_backend = RequestsBackend()
        return inst

    def set_backend(self, backend: SerpBackend) -> None:
        self.m_backend = backend

    def set_timeout(self, timeout_s: float) -> None:
        self.m_timeout_s = timeout_s

    def set_credentials(self, login: str, password: str) -> None:
        self.m_login = login
        self.m_password = password

    def run(self, query: GoogleRankQuery) -> GoogleRankResult:
        if not self.m_login or not self.m_password:
            raise CredentialsMissingError("DATAFORSEO_LOGIN/PASSWORD not configured")
        if not self.m_backend:
            self.m_backend = RequestsBackend()
        payload: Dict[str, Any] = {
            "keyword": query.keyword,
            "se_domain": query.se_domain,
            "location_code": query.location_code,
            "language_code": query.language_code,
            "device": query.device,
            "os": query.os,
            "depth": query.depth,
        }
        raw = self.m_backend.google_organic_live_advanced(payload)
        organic, check_url = _extract_organic_and_check_url(raw)
        matches = _find_matches(query.keyword, organic, threshold=query.similarity_threshold)
        top = matches[0].rank_absolute if matches else None
        return GoogleRankResult(
            query=query,
            top_position=top,
            matches=matches,
            total_matches=len(matches),
            check_url=check_url,
        )

def _extract_organic_and_check_url(data: Dict[str, Any]) -> tuple[list[Dict[str, Any]], Optional[str]]:
    tasks = data.get("tasks", []) or []
    if not tasks:
        return [], None
    results = tasks[0].get("result", []) or []
    if not results:
        return [], None
    items = results[0].get("items", []) or []
    check_url = results[0].get("check_url")
    organic = [it for it in items if isinstance(it, dict) and it.get("type") == "organic"]
    return organic, check_url

def _find_matches(keyword: str, organic: list[Dict[str, Any]], *, threshold: float) -> list[OrganicItem]:
    import re
    from difflib import SequenceMatcher

    def norm(s: str) -> str:
        s = s.lower(); s = re.sub(r"[^a-z0-9]+", " ", s).strip()
        return re.sub(r"\s+", " ", s)

    def similar(a: str, b: str) -> bool:
        return SequenceMatcher(None, norm(a), norm(b)).ratio() >= threshold

    out: list[OrganicItem] = []
    for it in organic:
        title = it.get("title") or ""
        if not isinstance(title, str) or not title:
            continue
        url = it.get("url") if isinstance(it.get("url"), str) else None
        rank_abs = it.get("rank_absolute") if isinstance(it.get("rank_absolute"), int) else None
        if norm(keyword) in norm(title) or similar(title, keyword):
            out.append(OrganicItem(rank_absolute=rank_abs, title=title, url=url))
    out.sort(key=lambda m: m.rank_absolute if isinstance(m.rank_absolute, int) else 10**9)
    return out
```

## CLI Integration (Refactor Plan)
- Replace inline HTTP call in `check-search-engine dataforseo` with calls to `DataForSEORanker`.
- Keep the same flags; construct `GoogleRankQuery` and print `GoogleRankResult`.
- Preserve current `.env` > env precedence via `from_env()`.

## Error Handling
- Map HTTP 401 → `UnauthorizedError`, 403 → `ForbiddenError`, others → `ApiResponseError`.
- Raise `CredentialsMissingError` when creds absent.
- CLI should surface messages and non‑zero exit codes accordingly.

## Tests
- Unit tests (pytest) under `tests/`:
  - `test_dataforseo_requests_backend.py` — mock `requests.post`, cover success + 401/403 + non‑2xx
  - `test_dataforseo_ranker.py` — verify `.env` precedence, mapping to models, match logic, top_position
  - Optional: `test_dataforseo_sdk_backend.py` — mock SDK client class; ensure parity
- No live calls in CI; use canned JSON fixtures.

## Documentation
- Add section “Google Ranking Checks” in `docs/usage.md` and `docs/api.md`:
  - How to set env creds (.env priority)
  - Example: build `GoogleRankQuery`, run `DataForSEORanker.from_env().run(query)`
  - Mention credits/cost, location/language lookup links

## Environment & Security
- Required: `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD`
- Never commit credentials; `.env` is gitignored
- Be explicit in docs about credit consumption and rate limits

## Phased Implementation Plan
1) Types + Requests backend + Ranker (sync)
2) Refactor CLI to use SDK
3) Tests for success/error paths; mypy + ruff pass
4) Docs update (usage + API)
5) Optional: SDK backend implementation (parity tests), locations/languages helpers

## Acceptance Criteria
- `DataForSEORanker.from_env().run(query)` returns `GoogleRankResult` with `top_position`, `matches[]`, and `check_url`
- CLI `check-search-engine dataforseo` uses the SDK and produces identical JSON to the current behavior
- Missing creds → clear error; 401/403 → mapped exceptions; tests cover these
- Mypy passes, tests green, docs updated

## Risks & Mitigations
- API shape drift: keep backend adapters thin; add unit tests with recorded samples
- Cost/rate limits: emphasize depth control in docs; consider backoff if needed
- HTML changes not applicable (we rely on DataForSEO)

