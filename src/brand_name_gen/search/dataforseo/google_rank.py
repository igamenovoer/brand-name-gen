from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from .. import dataforseo as _pkg  # type: ignore  # namespace import fallback if needed
from .backends import RequestsBackend, SerpBackend
from .types import CredentialsMissingError, GoogleRankQuery, GoogleRankResult, OrganicItem
from ...utils.env import read_dotenv_value
import os
import re
from difflib import SequenceMatcher


class DataForSEORanker:
    """Service wrapper for DataForSEO Google organic ranking.

    Reads credentials from the environment or a local ``.env`` file and executes the
    ``google/organic/live/advanced`` endpoint using the configured backend.
    """

    def __init__(self) -> None:
        self.m_backend: Optional[SerpBackend] = None
        self.m_login: Optional[str] = None
        self.m_password: Optional[str] = None
        self.m_timeout_s: Optional[float] = None

    @classmethod
    def from_env(cls) -> "DataForSEORanker":
        """Create an instance with credentials loaded from ``.env``/``os.environ``.

        Environment keys (``.env`` takes precedence):
        ``DATAFORSEO_LOGIN``/``DATAFORSEO_USERNAME``/``DATAFORSEO_EMAIL`` and
        ``DATAFORSEO_PASSWORD``/``DATAFORSEO_PASS``.

        Returns
        -------
        DataForSEORanker
            Configured ranker instance with a 30s default timeout.
        """
        inst = cls()
        login = read_dotenv_value("DATAFORSEO_LOGIN") or read_dotenv_value("DATAFORSEO_USERNAME") or read_dotenv_value("DATAFORSEO_EMAIL")
        password = read_dotenv_value("DATAFORSEO_PASSWORD") or read_dotenv_value("DATAFORSEO_PASS")
        inst.m_login = login or os.getenv("DATAFORSEO_LOGIN") or os.getenv("DATAFORSEO_USERNAME") or os.getenv("DATAFORSEO_EMAIL")
        inst.m_password = password or os.getenv("DATAFORSEO_PASSWORD") or os.getenv("DATAFORSEO_PASS")
        inst.m_timeout_s = 30.0
        inst.m_backend = None
        return inst

    def set_backend(self, backend: SerpBackend) -> None:
        """Inject a custom SERP backend implementation.

        Parameters
        ----------
        backend : SerpBackend
            Object implementing the SERP API call (e.g., :class:`RequestsBackend`).
        """
        self.m_backend = backend

    def set_timeout(self, timeout_s: float) -> None:
        """Set the default HTTP timeout in seconds."""
        self.m_timeout_s = timeout_s

    def set_credentials(self, login: str, password: str) -> None:
        """Set login and password explicitly.

        Parameters
        ----------
        login : str
            DataForSEO login/username/email.
        password : str
            DataForSEO password.
        """
        self.m_login = login
        self.m_password = password

    def run(self, query: GoogleRankQuery) -> GoogleRankResult:
        """Execute a ranking request and compute matches.

        Parameters
        ----------
        query : GoogleRankQuery
            Query parameters including keyword and similarity threshold.

        Returns
        -------
        GoogleRankResult
            Structured result including top position, matches and a ``check_url``.

        Raises
        ------
        CredentialsMissingError
            If credentials are not configured.
        ApiResponseError
            If the API response is not successful (may also raise subclass errors).
        """
        if not self.m_login or not self.m_password:
            raise CredentialsMissingError("DATAFORSEO_LOGIN/PASSWORD not configured")
        backend = self.m_backend or RequestsBackend(
            self.m_login, self.m_password, timeout_s=self.m_timeout_s or 30.0
        )
        payload: Dict[str, Any] = {
            "keyword": query.keyword,
            "se_domain": query.se_domain,
            "location_code": query.location_code,
            "language_code": query.language_code,
            "device": query.device,
            "os": query.os,
            "depth": query.depth,
        }
        raw = backend.google_organic_live_advanced(payload)
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


def _extract_organic_and_check_url(data: Dict[str, Any]) -> Tuple[List[Dict[str, Any]], Optional[str]]:
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


def _find_matches(keyword: str, organic: List[Dict[str, Any]], *, threshold: float) -> List[OrganicItem]:
    def norm(s: str) -> str:
        s2 = s.lower()
        s2 = re.sub(r"[^a-z0-9]+", " ", s2).strip()
        return re.sub(r"\s+", " ", s2)

    def similar(a: str, b: str) -> bool:
        return SequenceMatcher(None, norm(a), norm(b)).ratio() >= threshold

    out: List[OrganicItem] = []
    for it in organic:
        title = it.get("title") or ""
        if not isinstance(title, str) or not title:
            continue
        url_val = it.get("url") if isinstance(it.get("url"), str) else None
        rank_abs = it.get("rank_absolute") if isinstance(it.get("rank_absolute"), int) else None
        if norm(keyword) in norm(title) or similar(title, keyword):
            out.append(OrganicItem(rank_absolute=rank_abs, title=title, url=url_val))
    out.sort(key=lambda m: m.rank_absolute if isinstance(m.rank_absolute, int) else 10**9)
    return out
