"""
Domain availability checking utilities.

This module provides strongly-typed helpers to verify if a `.com` domain
is registered using the authoritative RDAP service from the registry
(Verisign). It also exposes an optional DNS-over-HTTPS (DoH) probe for
diagnostics. Data models use Pydantic and follow the project's coding guide.

Classes
-------
DomainAvailability
    Result model describing domain availability, source, and status

Enums
-----
Source
    Origin of information (rdap:verisign, doh providers, unknown)

Functions
---------
normalize_brand_label
    Convert free-form brand text to a valid domain label
is_com_available
    Authoritatively check `<brand>.com` availability via RDAP
check_www_resolves
    Optional DoH probe for `www.<domain>` A record
check_many
    Batch helper to check multiple labels serially

Examples
--------
>>> from brand_name_gen.domain_check import is_com_available
>>> r = is_com_available("brand-name")
>>> r.available in (True, False, None)
True
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
    """Information source for availability results."""

    rdap_verisign = "rdap:verisign"
    doh_google = "doh:google"
    doh_cloudflare = "doh:cloudflare"
    unknown = "unknown"


class DomainAvailability(BaseModel):
    """Structured result for domain availability.

    Parameters
    ----------
    domain : str
        Fully qualified domain (e.g., ``brand-name.com``)
    available : bool or None
        True when unregistered, False when registered, None if unknown
    rdap_status : int or None
        HTTP status code returned by RDAP (404, 200, etc.)
    authoritative : bool
        True when the result is derived from RDAP (authoritative)
    source : Source
        Data source identifier
    note : str or None
        Optional human-friendly context
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
    def _validate_domain(cls, v: str) -> str:  # noqa: D401 - simple validation
        """Validate domain contains a TLD separator."""
        if not v or "." not in v:
            raise ValueError("domain must include a TLD, e.g., brand-name.com")
        return v


class DomainCheckError(Exception):
    """Raised when domain checking encounters an unrecoverable error."""


def normalize_brand_label(label: str) -> str:
    """Normalize free-form brand text into a DNS label.

    This performs lowercase conversion, replaces non-alphanumeric characters with
    hyphens, collapses duplicate hyphens, strips leading/trailing hyphens, and
    applies IDNA (Punycode) if non-ASCII remains.

    Parameters
    ----------
    label : str
        Input brand text (e.g., ``"Café Brand"``)

    Returns
    -------
    str
        Normalized label suitable for the left-hand side of a domain

    Raises
    ------
    DomainCheckError
        If normalization yields an empty label
    """

    s = re.sub(r"[^A-Za-z0-9-]+", "-", label.strip().lower())
    s = re.sub(r"-+", "-", s).strip("-")
    if not s:
        raise DomainCheckError("empty label after normalization")
    # If any non-ASCII remains, encode using IDNA (safe if ASCII too)
    try:
        s.encode("ascii")
    except UnicodeEncodeError:
        s = idna.encode(s).decode()
    return s


def _rdap_check(domain: str, *, timeout_s: float) -> DomainAvailability:
    """Query Verisign RDAP for a `.com` domain and interpret the response.

    Parameters
    ----------
    domain : str
        FQDN to check (e.g., ``brand-name.com``)
    timeout_s : float
        Request timeout in seconds

    Returns
    -------
    DomainAvailability
        Availability result based on RDAP response
    """

    url = RDAP_COM.format(domain)
    for attempt in (0, 1):  # one retry on transient errors
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
    """Check if `<brand>.com` is unregistered using RDAP.

    Parameters
    ----------
    brand : str
        Brand label (free-form) to normalize and check
    timeout_s : float, optional
        HTTP timeout, by default 5.0 seconds

    Returns
    -------
    DomainAvailability
        Result model with availability and metadata
    """

    label = normalize_brand_label(brand)
    domain = f"{label}.com"
    return _rdap_check(domain, timeout_s=timeout_s)


def check_www_resolves(domain: str, *, provider: str = "google", timeout_s: float = 5.0) -> bool:
    """Probe whether `www.<domain>` has an A record via DoH.

    This is diagnostic only and must not override RDAP conclusions.

    Parameters
    ----------
    domain : str
        FQDN without the `www.` prefix (e.g., ``brand-name.com``)
    provider : {'google', 'cloudflare'}, optional
        DoH provider to query (default 'google')
    timeout_s : float, optional
        HTTP timeout (default 5.0 seconds)

    Returns
    -------
    bool
        True if query returns status 0 (NOERROR) with A record answers
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
    """Batch check multiple brand labels serially.

    Parameters
    ----------
    labels : list of str
        Brand labels to normalize and query
    timeout_s : float, optional
        Per-request timeout (default 5.0 seconds)

    Returns
    -------
    dict
        Mapping from original label to DomainAvailability
    """

    results: Dict[str, DomainAvailability] = {}
    for raw in labels:
        results[raw] = is_com_available(raw, timeout_s=timeout_s)
    return results

