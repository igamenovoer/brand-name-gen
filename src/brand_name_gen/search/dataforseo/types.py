from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class GoogleRankQuery(BaseModel):
    keyword: str
    se_domain: str = "google.com"
    location_code: int = 2840
    language_code: str = "en"
    device: str = "desktop"
    os: str = "macos"
    depth: int = 50
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
    ...


class CredentialsMissingError(DataForSEOError):
    ...


class UnauthorizedError(DataForSEOError):
    ...


class ForbiddenError(DataForSEOError):
    ...


class ApiResponseError(DataForSEOError):
    ...

