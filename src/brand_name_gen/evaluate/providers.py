"""
Provider wrappers for uniqueness evaluation.

Each provider is a thin class that calls existing module-level functions
and returns typed models from those modules.
"""

from __future__ import annotations

from typing import Optional

from brand_name_gen.android.title_check import (
    TitleCheckResult as AndroidTitleCheckResult,
    check_title_appfollow,
    check_title_playstore,
)
from brand_name_gen.domain.domain_check import DomainAvailability, is_com_available
from brand_name_gen.search.dataforseo.google_rank import DataForSEORanker
from brand_name_gen.search.dataforseo.types import GoogleRankQuery, GoogleRankResult


class AppFollowProvider:
    def fetch(self, title: str, *, country: str = "us", threshold: float = 0.9) -> AndroidTitleCheckResult:
        return check_title_appfollow(title, country=country, threshold=threshold)


class PlayProvider:
    def fetch(self, title: str, *, hl: str = "en", gl: str = "US", threshold: float = 0.9) -> AndroidTitleCheckResult:
        return check_title_playstore(title, hl=hl, gl=gl, threshold=threshold)


class SerpProvider:
    def __init__(self) -> None:
        self._ranker = DataForSEORanker.from_env()

    def fetch(self, title: str, *, location_code: int, language_code: str) -> GoogleRankResult:
        q = GoogleRankQuery(keyword=title, location_code=location_code, language_code=language_code)
        return self._ranker.run(q)


class DomainProvider:
    def check(self, title: str) -> DomainAvailability:
        return is_com_available(title)

