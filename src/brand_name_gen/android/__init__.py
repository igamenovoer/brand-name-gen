from __future__ import annotations

from .title_check import (
    Provider,
    Suggestion,
    TitleCheckError,
    TitleCheckResult,
    check_title,
    check_title_appfollow,
    check_title_playstore,
    is_similar,
    normalize_title,
)
from .title_checker import AppTitleChecker

__all__ = [
    "Provider",
    "Suggestion",
    "TitleCheckError",
    "TitleCheckResult",
    "check_title",
    "check_title_appfollow",
    "check_title_playstore",
    "is_similar",
    "normalize_title",
    "AppTitleChecker",
]

