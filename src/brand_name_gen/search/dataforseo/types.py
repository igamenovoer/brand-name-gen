from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class GoogleRankQuery(BaseModel):
    """Parameters for a Google organic ranking query (DataForSEO).

    Parameters
    ----------
    keyword : str
        Query keyword to search for (e.g., app or brand name).
    se_domain : str, default='google.com'
        Search engine domain.
    location_code : int, default=2840
        DataForSEO location code (``2840`` = United States).
    language_code : str, default='en'
        Interface language code.
    device : str, default='desktop'
        Device type (``'desktop'`` or ``'mobile'``).
    os : str, default='macos'
        Operating system identifier.
    depth : int, default=50
        Depth of results to fetch.
    similarity_threshold : float, default=0.9
        Title similarity threshold in ``[0, 1]`` used for filtering matches.
    """

    keyword: str
    se_domain: str = "google.com"
    location_code: int = 2840
    language_code: str = "en"
    device: str = "desktop"
    os: str = "macos"
    depth: int = 50
    similarity_threshold: float = 0.9


class OrganicItem(BaseModel):
    """Single organic result item.

    Parameters
    ----------
    rank_absolute : int | None, optional
        Absolute rank when available.
    title : str
        Page title.
    url : str | None, optional
        Result URL when present.
    """

    rank_absolute: Optional[int] = None
    title: str
    url: Optional[str] = None


class GoogleRankResult(BaseModel):
    """Structured results for a ranking query.

    Parameters
    ----------
    query : GoogleRankQuery
        Original query parameters.
    top_position : int | None, optional
        Absolute rank of the first matching item if any.
    matches : list[OrganicItem]
        Items whose titles match or are similar to the keyword.
    total_matches : int, default=0
        Number of matching items.
    check_url : str | None, optional
        Backend-provided URL that reproduces the check in a browser.
    """

    query: GoogleRankQuery
    top_position: Optional[int] = None
    matches: List[OrganicItem] = Field(default_factory=list)
    total_matches: int = 0
    check_url: Optional[str] = None


class DataForSEOError(Exception):
    """Base exception for DataForSEO-related errors."""


class CredentialsMissingError(DataForSEOError):
    """Raised when login/password are not configured."""


class UnauthorizedError(DataForSEOError):
    """Raised for HTTP 401 responses from the API."""


class ForbiddenError(DataForSEOError):
    """Raised for HTTP 403 responses from the API."""


class ApiResponseError(DataForSEOError):
    """Raised for other non-successful API responses."""
