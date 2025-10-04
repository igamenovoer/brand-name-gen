"""
Android app title uniqueness checks (AppFollow + Play Store).

Moved from `brand_name_gen.title_check` into `brand_name_gen.android.title_check`.
Public API remains the same via shim re-exports for backward compatibility.
"""

from __future__ import annotations

import os
import re
import urllib.parse as up
from difflib import SequenceMatcher
from enum import Enum
from typing import Dict, List, Optional

import requests
from pydantic import BaseModel, Field


class Provider(str, Enum):
    """Supported providers for Android title uniqueness checks.

    Members
    -------
    appfollow
        Use AppFollow ASO suggestions API.
    playstore
        Scrape Google Play web search results (heuristic, HTML subject to change).
    """

    appfollow = "appfollow"
    playstore = "playstore"


class Suggestion(BaseModel):
    """Suggestion item returned by a provider.

    Parameters
    ----------
    pos : int | None, optional
        1-based position in the suggestion list when available.
    term : str
        Suggested search term or app title text.
    """

    pos: Optional[int] = Field(default=None)
    term: str


class TitleCheckResult(BaseModel):
    """Structured result of a title uniqueness check.

    Parameters
    ----------
    provider : Provider
        Which provider produced the result (``Provider.appfollow`` or ``Provider.playstore``).
    title : str
        Input title that was evaluated.
    country : str | None, optional
        Country code (lowercase, e.g., ``'us'``) for AppFollow. ``None`` for Play Store.
    hl : str | None, optional
        Play Store UI language (e.g., ``'en'``). ``None`` for AppFollow.
    gl : str | None, optional
        Play Store country code (e.g., ``'US'``). ``None`` for AppFollow.
    threshold : float
        Similarity ratio threshold in ``[0, 1]`` for heuristic matching.
    suggestions : list[Suggestion]
        Provider-sourced suggestions or result titles.
    collisions : list[Suggestion]
        Subset of suggestions considered too similar or containing/contained by the input.
    unique_enough : bool
        ``True`` when no collisions found under the configured threshold.
    meta : dict
        Provider-specific metadata (e.g., ``{"play_url": "..."}``).
    """

    provider: Provider
    title: str
    country: Optional[str] = None
    hl: Optional[str] = None
    gl: Optional[str] = None
    threshold: float
    suggestions: List[Suggestion]
    collisions: List[Suggestion]
    unique_enough: bool
    meta: Dict[str, object] = Field(default_factory=dict)


class TitleCheckError(Exception):
    """Raised when a provider request fails or input is invalid."""


def normalize_title(s: str) -> str:
    """Normalize a string for title comparison.

    Lowercases, replaces non-alphanumerics with single spaces, collapses whitespace.

    Parameters
    ----------
    s : str
        Raw title or term.

    Returns
    -------
    str
        Normalized representation suitable for similarity matching.
    """
    t = s.lower()
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    return re.sub(r"\s+", " ", t)


def is_similar(a: str, b: str, *, threshold: float = 0.9) -> bool:
    """Check if two titles are similar under a ratio threshold.

    Parameters
    ----------
    a, b : str
        Titles to compare.
    threshold : float, default=0.9
        Ratio threshold in ``[0, 1]``. Higher values require closer matches.

    Returns
    -------
    bool
        ``True`` if similarity ratio is greater than or equal to ``threshold``.
    """
    return SequenceMatcher(None, normalize_title(a), normalize_title(b)).ratio() >= threshold


def _compute_collisions(title: str, terms: List[str], *, threshold: float) -> List[Suggestion]:
    norm_in = normalize_title(title)
    compact_in = norm_in.replace(" ", "")
    out: List[Suggestion] = []
    for i, t in enumerate(terms, start=1):
        norm_t = normalize_title(t)
        if norm_t == norm_in:
            continue
        compact_t = norm_t.replace(" ", "")
        if compact_in in compact_t or compact_t in compact_in or is_similar(t, title, threshold=threshold):
            out.append(Suggestion(pos=i, term=t))
    return out


def check_title_appfollow(
    title: str,
    *,
    country: str = "us",
    threshold: float = 0.9,
    api_key: Optional[str] = None,
    timeout_s: float = 30.0,
) -> TitleCheckResult:
    """Check title uniqueness using AppFollow ASO suggestions.

    Requires an AppFollow API token (``APPFOLLOW_API_KEY``). Suggestions are compared
    against the input using substring and similarity heuristics.

    Parameters
    ----------
    title : str
        Title to evaluate.
    country : str, default='us'
        Two-letter country code (lowercase) used by AppFollow.
    threshold : float, default=0.9
        Similarity threshold in ``[0, 1]`` for collision detection.
    api_key : str | None, optional
        Overrides ``APPFOLLOW_API_KEY`` from the environment when provided.
    timeout_s : float, default=30.0
        HTTP request timeout in seconds.

    Returns
    -------
    TitleCheckResult
        Structured result containing suggestions and any detected collisions.

    Raises
    ------
    TitleCheckError
        If the API key is missing or the AppFollow request fails.

    Examples
    --------
    >>> from brand_name_gen.android.title_check import check_title_appfollow
    >>> res = check_title_appfollow("BrandName", country="us")
    >>> res.unique_enough
    True
    """
    token = api_key or os.getenv("APPFOLLOW_API_KEY")
    if not token:
        raise TitleCheckError("APPFOLLOW_API_KEY not set")

    base = "https://api.appfollow.io/api/v2/aso/suggests"
    headers = {"X-AppFollow-API-Token": token, "Accept": "application/json"}
    params: Dict[str, str] = {"term": title, "country": country.lower()}
    r = requests.get(base, headers=headers, params=params, timeout=timeout_s)
    if r.status_code in (401, 403):
        raise TitleCheckError("AppFollow unauthorized/forbidden: check API key and access")
    try:
        r.raise_for_status()
    except requests.HTTPError as e:  # pragma: no cover - network edge
        raise TitleCheckError(f"AppFollow error: {e}") from e
    data = r.json()
    terms: List[str] = []
    for it in data:
        if isinstance(it, dict):
            v = it.get("displayTerm") or it.get("term")
            if isinstance(v, str) and v:
                terms.append(v)
    suggestions = [Suggestion(pos=i + 1, term=t) for i, t in enumerate(terms)]
    collisions = _compute_collisions(title, terms, threshold=threshold)
    return TitleCheckResult(
        provider=Provider.appfollow,
        title=title,
        country=country,
        hl=None,
        gl=None,
        threshold=threshold,
        suggestions=suggestions,
        collisions=collisions,
        unique_enough=len(collisions) == 0,
        meta={},
    )


def check_title_playstore(
    title: str,
    *,
    hl: str = "en",
    gl: str = "US",
    threshold: float = 0.9,
    timeout_s: float = 30.0,
    user_agent: Optional[str] = None,
) -> TitleCheckResult:
    """Heuristically check title uniqueness via Google Play web search.

    Scrapes the Play Store search results page and extracts ``aria-label`` app titles,
    which are then compared to the input title using substring and similarity rules.

    Parameters
    ----------
    title : str
        Title to evaluate.
    hl : str, default='en'
        UI language (e.g., ``'en'``).
    gl : str, default='US'
        Country code (e.g., ``'US'``).
    threshold : float, default=0.9
        Similarity threshold in ``[0, 1]`` for collision detection.
    timeout_s : float, default=30.0
        HTTP request timeout in seconds.
    user_agent : str | None, optional
        Custom user agent string for the request.

    Returns
    -------
    TitleCheckResult
        Structured result including suggestions and collisions. ``meta['play_url']`` holds
        the search URL used.

    Raises
    ------
    TitleCheckError
        If the Play Store page cannot be fetched successfully.
    """
    q = up.quote(f'"{title}"')
    url = f"https://play.google.com/store/search?q={q}&c=apps&hl={hl}&gl={gl}"
    headers = {
        "User-Agent": user_agent
        or (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }
    r = requests.get(url, headers=headers, timeout=timeout_s)
    if r.status_code != 200:
        raise TitleCheckError(f"Play search error: HTTP {r.status_code}")
    html = r.text
    labels: List[str] = [m.group(1) for m in re.finditer(r'aria-label="([^"]+)"', html)]
    # Deduplicate while preserving order
    seen: set[str] = set()
    uniq_labels: List[str] = []
    for lab in labels:
        if lab not in seen:
            uniq_labels.append(lab)
            seen.add(lab)
    terms = uniq_labels[:100]
    suggestions = [Suggestion(pos=i + 1, term=t) for i, t in enumerate(terms)]
    collisions = _compute_collisions(title, terms, threshold=threshold)
    return TitleCheckResult(
        provider=Provider.playstore,
        title=title,
        country=None,
        hl=hl,
        gl=gl,
        threshold=threshold,
        suggestions=suggestions,
        collisions=collisions,
        unique_enough=len(collisions) == 0,
        meta={"play_url": url},
    )


def check_title(
    title: str,
    *,
    providers: List[Provider] | None = None,
    country: str = "us",
    hl: str = "en",
    gl: str = "US",
    threshold: float = 0.9,
    api_key: Optional[str] = None,
    timeout_s: float = 30.0,
) -> List[TitleCheckResult]:
    """Run title checks across one or more providers.

    Parameters
    ----------
    title : str
        Title to evaluate.
    providers : list[Provider] | None, optional
        Execution order of providers. Defaults to ``[Provider.appfollow, Provider.playstore]``.
    country : str, default='us'
        Country code for AppFollow.
    hl : str, default='en'
        UI language for Play Store.
    gl : str, default='US'
        Country code for Play Store.
    threshold : float, default=0.9
        Similarity threshold in ``[0, 1]`` used by both providers.
    api_key : str | None, optional
        AppFollow API key override.
    timeout_s : float, default=30.0
        HTTP request timeout (applies to both providers).

    Returns
    -------
    list[TitleCheckResult]
        A list of results in the same order as the executed providers.
    """
    order = providers or [Provider.appfollow, Provider.playstore]
    out: List[TitleCheckResult] = []
    for p in order:
        if p == Provider.appfollow:
            out.append(
                check_title_appfollow(
                    title,
                    country=country,
                    threshold=threshold,
                    api_key=api_key,
                    timeout_s=timeout_s,
                )
            )
        elif p == Provider.playstore:
            out.append(
                check_title_playstore(
                    title,
                    hl=hl,
                    gl=gl,
                    threshold=threshold,
                    timeout_s=timeout_s,
                    user_agent=None,
                )
            )
    return out
