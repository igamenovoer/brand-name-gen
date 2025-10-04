from __future__ import annotations

from typing import Any, Dict, Protocol

import requests
from requests.auth import HTTPBasicAuth

from .types import ApiResponseError, ForbiddenError, UnauthorizedError


class SerpBackend(Protocol):
    """Protocol for SERP backends used by the ranker.

    Implementations must call the DataForSEO endpoint and return the parsed JSON
    response object as a ``dict``.
    """

    def google_organic_live_advanced(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Call ``/v3/serp/google/organic/live/advanced`` with a single payload.

        Parameters
        ----------
        payload : dict
            Request body as expected by DataForSEO. The backend is responsible for
            any batching or list-wrapping required by the API.

        Returns
        -------
        dict
            Parsed JSON response.
        """
        ...


class RequestsBackend:
    """Requests-based implementation of :class:`SerpBackend`."""

    def __init__(self, login: str, password: str, *, timeout_s: float = 30.0) -> None:
        self._login = login
        self._password = password
        self._timeout_s = timeout_s

    def google_organic_live_advanced(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the DataForSEO Google Organic Live Advanced endpoint.

        Parameters
        ----------
        payload : dict
            Single-task request body.

        Returns
        -------
        dict
            Parsed response body.

        Raises
        ------
        UnauthorizedError
            For HTTP 401 responses.
        ForbiddenError
            For HTTP 403 responses.
        ApiResponseError
            For other non-successful responses.
        """
        url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
        auth = HTTPBasicAuth(self._login, self._password)
        resp = requests.post(url, json=[payload], auth=auth, timeout=self._timeout_s)
        if resp.status_code == 401:
            raise UnauthorizedError("DataForSEO unauthorized (401)")
        if resp.status_code == 403:
            raise ForbiddenError("DataForSEO forbidden (403)")
        try:
            resp.raise_for_status()
        except requests.HTTPError as e:  # pragma: no cover
            raise ApiResponseError(f"DataForSEO error: {e}") from e
        data = resp.json()
        return data if isinstance(data, dict) else {}


class SdkBackend:
    def __init__(self) -> None:  # pragma: no cover
        raise NotImplementedError
