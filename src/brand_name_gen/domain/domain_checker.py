"""
Stateful service for `.com` domain availability checks via RDAP.

Implementation moved here from `brand_name_gen.domain_checker`.
"""

from __future__ import annotations

from typing import Optional

import requests

from .domain_check import DomainAvailability, Source, normalize_brand_label


class DomainChecker:
    def __init__(self) -> None:
        self.m_timeout_s: Optional[float] = None
        self.m_session: Optional[requests.Session] = None
        self.m_rdap_base: Optional[str] = None

    @property
    def timeout_s(self) -> Optional[float]:
        return self.m_timeout_s

    def set_timeout(self, timeout_s: float) -> None:
        self.m_timeout_s = timeout_s

    @classmethod
    def from_defaults(cls) -> "DomainChecker":
        inst = cls()
        inst.m_timeout_s = 5.0
        inst.m_rdap_base = "https://rdap.verisign.com/com/v1/domain/{}"
        inst.m_session = requests.Session()
        return inst

    @classmethod
    def from_session(
        cls, session: requests.Session, *, timeout_s: float = 5.0, rdap_base: Optional[str] = None
    ) -> "DomainChecker":
        inst = cls()
        inst.m_timeout_s = timeout_s
        inst.m_rdap_base = rdap_base or "https://rdap.verisign.com/com/v1/domain/{}"
        inst.m_session = session
        return inst

    def check_com(self, brand: str) -> DomainAvailability:
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

