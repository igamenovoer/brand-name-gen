"""
Stateful service for `.com` domain availability checks via RDAP.

Implementation moved here from `brand_name_gen.domain_checker`.
"""

from __future__ import annotations

from typing import Optional

import requests

from .domain_check import DomainAvailability, Source, normalize_brand_label


class DomainChecker:
    """Stateful service for ``.com`` availability via RDAP.

    Wraps the RDAP probing logic with configurable session, timeout and base URL.

    Attributes
    ----------
    m_timeout_s : float | None
        Request timeout in seconds.
    m_session : requests.Session | None
        HTTP session used to perform RDAP calls.
    m_rdap_base : str | None
        RDAP URL template (e.g., ``"https://rdap.verisign.com/com/v1/domain/{}"``).
    """

    def __init__(self) -> None:
        self.m_timeout_s: Optional[float] = None
        self.m_session: Optional[requests.Session] = None
        self.m_rdap_base: Optional[str] = None

    @property
    def timeout_s(self) -> Optional[float]:
        return self.m_timeout_s

    def set_timeout(self, timeout_s: float) -> None:
        """Set the default RDAP timeout.

        Parameters
        ----------
        timeout_s : float
            Timeout in seconds used for subsequent requests.
        """
        self.m_timeout_s = timeout_s

    @classmethod
    def from_defaults(cls) -> "DomainChecker":
        """Construct a checker with sane defaults.

        Returns
        -------
        DomainChecker
            Instance using a new ``requests.Session``, 5s timeout and Verisign RDAP.
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
        """Construct a checker bound to a given session.

        Parameters
        ----------
        session : requests.Session
            Session used for RDAP requests.
        timeout_s : float, default=5.0
            Default RDAP timeout in seconds.
        rdap_base : str | None, optional
            RDAP URL template. Defaults to Verisign's endpoint for ``.com``.

        Returns
        -------
        DomainChecker
            Configured instance.
        """
        inst = cls()
        inst.m_timeout_s = timeout_s
        inst.m_rdap_base = rdap_base or "https://rdap.verisign.com/com/v1/domain/{}"
        inst.m_session = session
        return inst

    def check_com(self, brand: str) -> DomainAvailability:
        """Check whether ``<brand>.com`` is registered.

        Parameters
        ----------
        brand : str
            Brand string normalized into a DNS label.

        Returns
        -------
        DomainAvailability
            Authoritative availability based on RDAP response.
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
