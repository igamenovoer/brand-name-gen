"""
Stateful service for Android app title uniqueness checks.

Moved from `brand_name_gen.title_checker` to `brand_name_gen.android.title_checker`.
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
    """Stateful Android title uniqueness checker.

    Provides convenience wrappers around the stateless functions in
    ``brand_name_gen.android.title_check`` with configurable session, timeouts,
    user-agent, and AppFollow credentials.

    Attributes
    ----------
    m_session : requests.Session | None
        Optional HTTP session used by provider calls.
    m_timeout_s : float | None
        Default HTTP timeout (seconds) for provider requests.
    m_user_agent : str | None
        Optional user agent for Play Store requests.
    m_api_key : str | None
        AppFollow API key used by ``check_appfollow`` when set.
    """

    def __init__(self) -> None:
        self.m_session: Optional[requests.Session] = None
        self.m_timeout_s: Optional[float] = None
        self.m_user_agent: Optional[str] = None
        self.m_api_key: Optional[str] = None

    @classmethod
    def from_defaults(cls) -> "AppTitleChecker":
        """Construct an instance with reasonable defaults.

        Returns
        -------
        AppTitleChecker
            Instance configured with a ``requests.Session``, 30s timeout and a
            desktop Chrome user agent for Play Store.
        """
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
        """Construct an instance bound to a pre-existing session.

        Parameters
        ----------
        session : requests.Session
            Session used for outbound HTTP requests.
        timeout_s : float, default=30.0
            Default HTTP timeout in seconds.
        user_agent : str | None, optional
            Custom user agent for Play Store checks.

        Returns
        -------
        AppTitleChecker
            Configured checker instance.
        """
        inst = cls()
        inst.m_session = session
        inst.m_timeout_s = timeout_s
        inst.m_user_agent = user_agent
        return inst

    def set_appfollow_api_key(self, api_key: str) -> None:
        """Set the AppFollow API token used by ``check_appfollow``.

        Parameters
        ----------
        api_key : str
            AppFollow API token (equivalent to ``APPFOLLOW_API_KEY`` env var).
        """
        self.m_api_key = api_key

    def check_appfollow(self, title: str, *, country: str = "us", threshold: float = 0.9) -> TitleCheckResult:
        """Run an AppFollow title check using instance defaults.

        Parameters
        ----------
        title : str
            Title to evaluate.
        country : str, default='us'
            Two-letter lowercase country code.
        threshold : float, default=0.9
            Similarity threshold in ``[0, 1]`` for collision detection.

        Returns
        -------
        TitleCheckResult
            Structured result from the AppFollow provider.
        """
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
        """Run a Play Store title check using instance defaults.

        Parameters
        ----------
        title : str
            Title to evaluate.
        hl : str, default='en'
            Play Store UI language.
        gl : str, default='US'
            Play Store country code.
        threshold : float, default=0.9
            Similarity threshold in ``[0, 1]`` for collision detection.

        Returns
        -------
        TitleCheckResult
            Structured result from the Play Store provider.
        """
        return check_title_playstore(
            title,
            hl=hl,
            gl=gl,
            threshold=threshold,
            timeout_s=self.m_timeout_s or 30.0,
            user_agent=self.m_user_agent,
        )
