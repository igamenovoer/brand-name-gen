"""
Domain availability checking utilities (RDAP + DoH helpers).

Implementation moved here from `brand_name_gen.domain_check` to the
functional subpackage `brand_name_gen.domain`.
"""

from __future__ import annotations

from enum import Enum
import random
import re
import time
from typing import Dict, List, Optional

import idna
import requests
from pydantic import BaseModel, Field, field_validator

RDAP_COM: str = "https://rdap.verisign.com/com/v1/domain/{}"


class Source(str, Enum):
    """Source of information for domain availability.

    Members
    -------
    rdap_verisign
        Authoritative Verisign RDAP endpoint for .com.
    doh_google
        DNS-over-HTTPS (Google) used for optional ``www`` probe.
    doh_cloudflare
        DNS-over-HTTPS (Cloudflare) used for optional ``www`` probe.
    unknown
        Fallback or unspecified.
    """

    rdap_verisign = "rdap:verisign"
    doh_google = "doh:google"
    doh_cloudflare = "doh:cloudflare"
    unknown = "unknown"


class DomainAvailability(BaseModel):
    """Availability status for a single domain name.

    Parameters
    ----------
    domain : str
        Fully-qualified domain (e.g., ``'brand-name.com'``).
    available : bool | None, optional
        ``True`` if available, ``False`` if registered, ``None`` if unknown/transient.
    rdap_status : int | None, optional
        HTTP status code returned by RDAP when authoritative.
    authoritative : bool, default=False
        Indicates the status derives from RDAP (authoritative) rather than heuristics.
    source : Source, default=Source.unknown
        Endpoint/provider that produced the data.
    note : str | None, optional
        Additional diagnostic note (e.g., ``"transient"``).
    """

    domain: str = Field(description="e.g., brand-name.com")
    available: Optional[bool] = Field(
        default=None, description="True=free, False=registered, None=unknown"
    )
    rdap_status: Optional[int] = Field(default=None, description="RDAP HTTP status code")
    authoritative: bool = Field(default=False, description="True when from RDAP")
    source: Source = Field(default=Source.unknown)
    note: Optional[str] = None

    @field_validator("domain")
    @classmethod
    def _validate_domain(cls, v: str) -> str:
        if not v or "." not in v:
            raise ValueError("domain must include a TLD, e.g., brand-name.com")
        return v


class DomainCheckError(Exception):
    """Raised for invalid input or normalization errors."""


def normalize_brand_label(label: str) -> str:
    """Normalize a brand string into a DNS label.

    Lowercases, keeps ``a–z``, ``0–9`` and ``-``, replaces other characters with ``-``,
    collapses duplicates and trims edges. Uses IDNA (Punycode) if non-ASCII remains.

    Parameters
    ----------
    label : str
        Raw brand text.

    Returns
    -------
    str
        Normalized DNS-compatible label (ASCII or Punycode).

    Raises
    ------
    DomainCheckError
        If the label becomes empty after normalization.
    """
    s = re.sub(r"[^A-Za-z0-9-]+", "-", label.strip().lower())
    s = re.sub(r"-+", "-", s).strip("-")
    if not s:
        raise DomainCheckError("empty label after normalization")
    try:
        s.encode("ascii")
    except UnicodeEncodeError:
        s = idna.encode(s).decode()
    return s


def _rdap_check(domain: str, *, timeout_s: float) -> DomainAvailability:
    url = RDAP_COM.format(domain)
    for attempt in (0, 1):
        resp = requests.get(url, timeout=timeout_s)
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
        if resp.status_code in (429, 500, 502, 503, 504) and attempt == 0:
            wait = 0.5 + random.random() * 0.5
            time.sleep(wait)
            continue
        return DomainAvailability(
            domain=domain,
            available=None,
            rdap_status=resp.status_code,
            authoritative=True,
            source=Source.rdap_verisign,
            note="transient",
        )
    return DomainAvailability(
        domain=domain,
        available=None,
        rdap_status=None,
        authoritative=False,
        source=Source.unknown,
        note="unreachable",
    )


def is_com_available(brand: str, *, timeout_s: float = 5.0) -> DomainAvailability:
    """Check whether ``<brand>.com`` is registered using RDAP.

    Parameters
    ----------
    brand : str
        Brand string to be normalized into a label.
    timeout_s : float, default=5.0
        RDAP request timeout in seconds.

    Returns
    -------
    DomainAvailability
        Authoritative result based on Verisign RDAP status.
    """
    label = normalize_brand_label(brand)
    domain = f"{label}.com"
    return _rdap_check(domain, timeout_s=timeout_s)


def check_www_resolves(domain: str, *, provider: str = "google", timeout_s: float = 5.0) -> bool:
    """Probe whether ``www.<domain>`` has an A record via DoH.

    Diagnostic-only helper; availability is determined by RDAP, not DNS.

    Parameters
    ----------
    domain : str
        Fully-qualified domain name (e.g., ``'brand-name.com'``).
    provider : {'google', 'cloudflare'}, default='google'
        DNS-over-HTTPS provider to query.
    timeout_s : float, default=5.0
        HTTP timeout in seconds.

    Returns
    -------
    bool
        ``True`` if at least one A record is present; otherwise ``False``.

    Raises
    ------
    ValueError
        If ``provider`` is not one of ``'google'`` or ``'cloudflare'``.
    """
    host = f"www.{domain}"
    if provider == "google":
        url = f"https://dns.google/resolve?name={host}&type=A"
        data = requests.get(url, timeout=timeout_s).json()
        status = int(data.get("Status", -1))
        answers = data.get("Answer", [])
        return status == 0 and any(a.get("data") for a in answers)
    if provider == "cloudflare":
        url = f"https://cloudflare-dns.com/dns-query?name={host}&type=A"
        headers = {"Accept": "application/dns-json"}
        data = requests.get(url, headers=headers, timeout=timeout_s).json()
        status = int(data.get("Status", -1))
        answers = data.get("Answer", [])
        return status == 0 and any(a.get("data") for a in answers)
    raise ValueError("provider must be 'google' or 'cloudflare'")


def check_many(labels: List[str], *, timeout_s: float = 5.0) -> Dict[str, DomainAvailability]:
    """Batch-check multiple brand strings for .com availability.

    Parameters
    ----------
    labels : list[str]
        List of brand strings; each is normalized to a DNS label.
    timeout_s : float, default=5.0
        RDAP timeout in seconds (applied per item).

    Returns
    -------
    dict[str, DomainAvailability]
        Mapping from original input label to the corresponding availability result.
    """
    results: Dict[str, DomainAvailability] = {}
    for raw in labels:
        results[raw] = is_com_available(raw, timeout_s=timeout_s)
    return results
