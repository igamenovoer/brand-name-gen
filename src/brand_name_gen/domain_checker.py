"""
Domain availability checking service.

This module defines a stateful service class for checking `.com` domain
availability using RDAP. It follows the project's Python coding guide:

- Module-level docstring (NumPy style)
- Constructors take no arguments; use factory methods for initialization
- Member variables are prefixed with ``m_``
- Pydantic models are used for data (no ``m_`` on data fields)

Classes
-------
DomainChecker
    Stateful service with configurable timeout and session

Examples
--------
>>> from brand_name_gen.domain_checker import DomainChecker
>>> checker = DomainChecker.from_defaults()
>>> res = checker.check_com("brand-name")
>>> isinstance(res.available, (bool, type(None)))
True
"""

from __future__ import annotations

from typing import Optional

import requests

from brand_name_gen.domain_check import (
    DomainAvailability,
    Source,
    normalize_brand_label,
)


class DomainChecker:
    """
    Stateful service for domain availability checks via RDAP.

    Attributes
    ----------
    m_timeout_s : float or None
        Request timeout (seconds)
    m_session : requests.Session or None
        Optional shared HTTP session
    m_rdap_base : str or None
        RDAP base URL format string for `.com`
    """

    def __init__(self) -> None:
        """Initialize an empty instance; use factory methods to configure."""
        self.m_timeout_s: Optional[float] = None
        self.m_session: Optional[requests.Session] = None
        self.m_rdap_base: Optional[str] = None

    @property
    def timeout_s(self) -> Optional[float]:
        """float or None: Current timeout setting in seconds."""
        return self.m_timeout_s

    def set_timeout(self, timeout_s: float) -> None:
        """Set timeout value in seconds.

        Parameters
        ----------
        timeout_s : float
            Timeout for future HTTP requests
        """

        self.m_timeout_s = timeout_s

    @classmethod
    def from_defaults(cls) -> "DomainChecker":
        """
        Create a checker with sensible defaults.

        Returns
        -------
        DomainChecker
            Instance configured with a Session, default RDAP base, and timeout
        """

        inst = cls()
        inst.m_timeout_s = 5.0
        inst.m_rdap_base = "https://rdap.verisign.com/com/v1/domain/{}"
        inst.m_session = requests.Session()
        return inst

    @classmethod
    def from_session(
        cls, session: requests.Session, *, timeout_s: float = 5.0, rdap_base: Optional[str] = None
    ) -> "DomainChecker":
        """
        Create a checker bound to an existing requests.Session.

        Parameters
        ----------
        session : requests.Session
            Pre-configured HTTP session
        timeout_s : float, optional
            Request timeout (default 5.0)
        rdap_base : str, optional
            RDAP base URL format string with one `{}` placeholder
        """

        inst = cls()
        inst.m_timeout_s = timeout_s
        inst.m_rdap_base = rdap_base or "https://rdap.verisign.com/com/v1/domain/{}"
        inst.m_session = session
        return inst

    def check_com(self, brand: str) -> DomainAvailability:
        """
        Check `.com` availability for a brand label via RDAP.

        Parameters
        ----------
        brand : str
            Brand label (before `.com`)

        Returns
        -------
        DomainAvailability
            Pydantic model describing result
        """

        label = normalize_brand_label(brand)
        domain = f"{label}.com"
        base = self.m_rdap_base or "https://rdap.verisign.com/com/v1/domain/{}"
        url = base.format(domain)
        sess = self.m_session or requests
        timeout = self.m_timeout_s or 5.0
        resp = sess.get(url, timeout=timeout)
        if resp.status_code == 404:
            return DomainAvailability(
                domain=domain,
                available=True,
                rdap_status=404,
                authoritative=True,
                source=Source.rdap_verisign,
            )
        if resp.ok:
            return DomainAvailability(
                domain=domain,
                available=False,
                rdap_status=resp.status_code,
                authoritative=True,
                source=Source.rdap_verisign,
            )
        return DomainAvailability(
            domain=domain,
            available=None,
            rdap_status=resp.status_code,
            authoritative=True,
            source=Source.rdap_verisign,
            note="transient",
        )

