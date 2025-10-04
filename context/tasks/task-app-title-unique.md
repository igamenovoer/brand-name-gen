# Task: Python API for Android App Title “Uniqueness” Checks (AppFollow + Play Store)

Purpose: Provide a small, typed Python module to assess whether an Android app title is “unique enough” using (1) AppFollow ASO suggestions and (2) Google Play web search heuristics. Align with our coding guide and existing CLI.

See also
- context/hints/howto-ensure-android-app-title-uniqueness.md
- context/hints/howto-use-appfollow-python.md

## Goals & Non‑Goals
- Goals: Typed API with Pydantic models; provider‑specific checks (AppFollow, Play); similarity rules; timeouts; clean errors; easy CLI integration.
- Non‑Goals: Guaranteed store ranking position; full ASO analytics; scraping robustness guarantees.

## Public API (Sync)
```
# src/brand_name_gen/title_check.py
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field

class Provider(str, Enum):
    appfollow = 'appfollow'
    playstore = 'playstore'

class Suggestion(BaseModel):
    pos: Optional[int] = Field(default=None)
    term: str

class TitleCheckResult(BaseModel):
    provider: Provider
    title: str
    country: Optional[str] = None     # AppFollow
    hl: Optional[str] = None          # Play
    gl: Optional[str] = None          # Play
    threshold: float
    suggestions: List[Suggestion]
    collisions: List[Suggestion]
    unique_enough: bool
    meta: dict = Field(default_factory=dict)  # e.g., {'play_url': '...', 'count': 10}

class TitleCheckError(Exception):
    ...

# Normalization & similarity utilities
def normalize_title(s: str) -> str: ...  # lower, strip, collapse non-alnum to space

def is_similar(a: str, b: str, *, threshold: float = 0.9) -> bool: ...  # SequenceMatcher

# Provider calls
def check_title_appfollow(
    title: str,
    *,
    country: str = 'us',
    threshold: float = 0.9,
    api_key: Optional[str] = None,       # fallback to env APPFOLLOW_API_KEY
    timeout_s: float = 30.0,
) -> TitleCheckResult: ...

def check_title_playstore(
    title: str,
    *,
    hl: str = 'en',
    gl: str = 'US',
    threshold: float = 0.9,
    timeout_s: float = 30.0,
    user_agent: Optional[str] = None,
) -> TitleCheckResult: ...

# Aggregation (optional convenience)
def check_title(
    title: str,
    *,
    providers: List[Provider] = [Provider.appfollow, Provider.playstore],
    country: str = 'us',
    hl: str = 'en',
    gl: str = 'US',
    threshold: float = 0.9,
    api_key: Optional[str] = None,
    timeout_s: float = 30.0,
) -> List[TitleCheckResult]: ...
```

## Service Class (follows coding guide)
```
# src/brand_name_gen/title_checker.py
"""Stateful checker for Android title uniqueness.

- No-arg constructor; factory methods
- m_ prefixed members (service class only)
- Pydantic models for results
"""
from typing import Optional, List
import requests
from brand_name_gen.title_check import (
    Provider, TitleCheckResult, check_title_appfollow, check_title_playstore
)

class AppTitleChecker:
    def __init__(self) -> None:
        self.m_session: Optional[requests.Session] = None
        self.m_timeout_s: Optional[float] = None
        self.m_user_agent: Optional[str] = None
        self.m_api_key: Optional[str] = None  # AppFollow

    @classmethod
    def from_defaults(cls) -> 'AppTitleChecker':
        inst = cls()
        inst.m_session = requests.Session()
        inst.m_timeout_s = 30.0
        inst.m_user_agent = (
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
            'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
        )
        return inst

    @classmethod
    def from_session(
        cls, session: requests.Session, *, timeout_s: float = 30.0, user_agent: Optional[str] = None
    ) -> 'AppTitleChecker':
        inst = cls()
        inst.m_session = session
        inst.m_timeout_s = timeout_s
        inst.m_user_agent = user_agent
        return inst

    def set_appfollow_api_key(self, api_key: str) -> None:
        self.m_api_key = api_key

    def check_appfollow(self, title: str, *, country: str = 'us', threshold: float = 0.9) -> TitleCheckResult:
        return check_title_appfollow(
            title, country=country, threshold=threshold,
            api_key=self.m_api_key, timeout_s=self.m_timeout_s or 30.0,
        )

    def check_playstore(self, title: str, *, hl: str = 'en', gl: str = 'US', threshold: float = 0.9) -> TitleCheckResult:
        return check_title_playstore(
            title, hl=hl, gl=gl, threshold=threshold,
            timeout_s=self.m_timeout_s or 30.0, user_agent=self.m_user_agent,
        )
```

## Behavior & Semantics
- Normalization: lower, collapse non-alphanumeric to spaces, trim; compute a compact version without spaces for looser substring checks.
- Collision rule: a suggestion is a collision if normalized terms are not exactly equal AND (compact_in in compact_term OR compact_term in compact_in OR similarity ≥ threshold).
- AppFollow
  - Endpoint: GET https://api.appfollow.io/api/v2/aso/suggests?term=<title>&country=<country>
  - Auth: header X-AppFollow-API-Token (api_key or env APPFOLLOW_API_KEY)
  - 401/403 → raise TitleCheckError; other non-2xx → raise TitleCheckError
- Play Store (heuristic)
  - URL: https://play.google.com/store/search?q="<title>"&c=apps&hl=<hl>&gl=<gl>
  - Parse aria-label="..." as candidate visible labels; dedupe; truncate (e.g., 100).
  - 200 OK required; else raise TitleCheckError.

## Dependencies
- Required: pydantic>=2, requests
- Optional: httpx (async), cachetools (TTL cache) — optional extras only.

## Code Sketch (Sync)
```
import os, re, requests, urllib.parse as up
from difflib import SequenceMatcher
from pydantic import BaseModel
from .title_check import Provider, Suggestion, TitleCheckResult, TitleCheckError

UA = (
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) '
    'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36'
)

def normalize_title(s: str) -> str:
    s = s.lower()
    s = re.sub(r'[^a-z0-9]+', ' ', s).strip()
    return re.sub(r'\s+', ' ', s)

def is_similar(a: str, b: str, *, threshold: float = 0.9) -> bool:
    return SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio() >= threshold

def _collisions(title: str, terms: list[str], *, threshold: float) -> list[Suggestion]:
    ni = normalize_title(title)
    compact_in = ni.replace(' ', '')
    out: list[Suggestion] = []
    for idx, t in enumerate(terms, start=1):
        nt = normalize_title(t)
        if nt == ni:
            continue
        compact_t = nt.replace(' ', '')
        if compact_in in compact_t or compact_t in compact_in or is_similar(t, title, threshold=threshold):
            out.append(Suggestion(pos=idx, term=t))
    return out

def check_title_appfollow(title: str, *, country: str = 'us', threshold: float = 0.9,
                          api_key: str | None = None, timeout_s: float = 30.0) -> TitleCheckResult:
    api_key = api_key or os.getenv('APPFOLLOW_API_KEY')
    if not api_key:
        raise TitleCheckError('APPFOLLOW_API_KEY not set')
    base = 'https://api.appfollow.io/api/v2/aso/suggests'
    h = {'X-AppFollow-API-Token': api_key, 'Accept': 'application/json'}
    p = {'term': title, 'country': country.lower()}
    r = requests.get(base, headers=h, params=p, timeout=timeout_s)
    if r.status_code in (401, 403):
        raise TitleCheckError('AppFollow unauthorized/forbidden')
    r.raise_for_status()
    data = r.json()
    terms = [(it.get('displayTerm') or it.get('term')) for it in data if isinstance(it, dict)]
    suggestions = [Suggestion(pos=i+1, term=t) for i, t in enumerate(terms) if t]
    collisions = _collisions(title, [s.term for s in suggestions], threshold=threshold)
    return TitleCheckResult(
        provider=Provider.appfollow, title=title, country=country,
        hl=None, gl=None, threshold=threshold,
        suggestions=suggestions, collisions=collisions,
        unique_enough=len(collisions) == 0, meta={},
    )

def check_title_playstore(title: str, *, hl: str = 'en', gl: str = 'US', threshold: float = 0.9,
                          timeout_s: float = 30.0, user_agent: str | None = None) -> TitleCheckResult:
    ua = user_agent or UA
    q = up.quote(f'"{title}"')
    url = f'https://play.google.com/store/search?q={q}&c=apps&hl={hl}&gl={gl}'
    h = {'User-Agent': ua}
    r = requests.get(url, headers=h, timeout=timeout_s)
    if r.status_code != 200:
        raise TitleCheckError(f'Play search error: HTTP {r.status_code}')
    html = r.text
    terms: list[str] = [m.group(1) for m in re.finditer(r'aria-label="([^"]+)"', html)]
    seen: set[str] = set(); uniq: list[str] = []
    for t in terms:
        if t not in seen:
            uniq.append(t); seen.add(t)
    uniq = uniq[:100]
    suggestions = [Suggestion(pos=i+1, term=t) for i, t in enumerate(uniq)]
    collisions = _collisions(title, [s.term for s in suggestions], threshold=threshold)
    return TitleCheckResult(
        provider=Provider.playstore, title=title, country=None,
        hl=hl, gl=gl, threshold=threshold,
        suggestions=suggestions, collisions=collisions,
        unique_enough=len(collisions) == 0, meta={'play_url': url},
    )
```

## Async (Optional)
- Mirror sync API via httpx.AsyncClient; preserve models and signatures with `async` suffix.

## Tests
- Unit: mock `requests.get` for both providers; supply sample JSON/HTML.
- Cases: exact match; near match (spacing/hyphen variants); threshold behavior; HTTP errors; missing APPFOLLOW_API_KEY.
- No network in tests; put sample HTML/JSON fixtures under tests/fixtures/.

## CLI Integration
- Already wired: `check-android appfollow` and `check-android playstore` use the same normalization and collision rules.
- Future: add a combined CLI that calls both and prints a summary.

## Acceptance Criteria
- Given a unique title, both providers return `unique_enough=True` with empty collisions.
- Given a near-collision title (e.g., “BrandName” vs “Brand Name Planner”), collisions list is non-empty.
- AppFollow errors without API key; Play errors on non-200.
- Models validate with Pydantic and mypy passes.

## Future Extensions
- Add caching with TTL to avoid repeated calls during batch checks.
- Add provider for Play API alternative (if official endpoints become available).
- Add result scoring (degree of uniqueness) and per-locale aggregation.
