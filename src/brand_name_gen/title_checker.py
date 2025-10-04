"""
Stateful service for Android app title uniqueness checks.

This service wraps the provider-specific functions in `title_check`
and exposes a stateful API following the project's coding guide:

- No-arg constructor; use factory methods to create instances
- Member variables prefixed with `m_`
- Pydantic models for results
"""

from __future__ import annotations

from typing import Optional

import requests

from .title_check import (
    TitleCheckResult,
    check_title_appfollow,
    check_title_playstore,
)


class AppTitleChecker:
    """
    Stateful Android title uniqueness checker.

    Attributes
    ----------
    m_session : requests.Session or None
        Optional shared HTTP session (reserved for future use)
    m_timeout_s : float or None
        Default timeout in seconds
    m_user_agent : str or None
        Default User-Agent for Play requests
    m_api_key : str or None
        AppFollow API token override
    """

    def __init__(self) -> None:
        self.m_session: Optional[requests.Session] = None
        self.m_timeout_s: Optional[float] = None
        self.m_user_agent: Optional[str] = None
        self.m_api_key: Optional[str] = None

    @classmethod
    def from_defaults(cls) -> "AppTitleChecker":
        """Create a checker with sensible defaults."""

        inst = cls()
        inst.m_session = requests.Session()
        inst.m_timeout_s = 30.0
        inst.m_user_agent = (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
        return inst

    @classmethod
    def from_session(
        cls, session: requests.Session, *, timeout_s: float = 30.0, user_agent: Optional[str] = None
    ) -> "AppTitleChecker":
        """Create a checker bound to an existing HTTP session."""

        inst = cls()
        inst.m_session = session
        inst.m_timeout_s = timeout_s
        inst.m_user_agent = user_agent
        return inst

    def set_appfollow_api_key(self, api_key: str) -> None:
        """Set AppFollow API key for subsequent calls."""

        self.m_api_key = api_key

    def check_appfollow(self, title: str, *, country: str = "us", threshold: float = 0.9) -> TitleCheckResult:
        """Check title using AppFollow ASO suggests."""

        return check_title_appfollow(
            title,
            country=country,
            threshold=threshold,
            api_key=self.m_api_key,
            timeout_s=self.m_timeout_s or 30.0,
        )

    def check_playstore(
        self, title: str, *, hl: str = "en", gl: str = "US", threshold: float = 0.9
    ) -> TitleCheckResult:
        """Check title using Google Play web search (heuristic)."""

        return check_title_playstore(
            title,
            hl=hl,
            gl=gl,
            threshold=threshold,
            timeout_s=self.m_timeout_s or 30.0,
            user_agent=self.m_user_agent,
        )

