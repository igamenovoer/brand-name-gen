# Task: Python API for Checking `.com` Domain Availability

Purpose: Provide a small, dependency-light Python module that programmatically verifies if `<brand>.com` is unregistered (authoritative via RDAP), with optional DNS probes, caching, and batch/asynchronous helpers.

See also: context/hints/howto-check-domain-availability-programmatically.md

## Goals & Non‑Goals
- Goals: Authoritative availability for `.com` using Verisign RDAP; simple API; robust timeouts/retries; optional DoH probes; unit-testable; CLI integration.
- Non‑Goals: Trademark clearance, registrar purchase flow, pricing, or multi‑TLD registrar integrations.

## Public API (Sync)
```
# src/brand_name_gen/domain_check.py

from enum import Enum
from pydantic import BaseModel, Field, field_validator

class Source(str, Enum):
    rdap_verisign = 'rdap:verisign'
    doh_google = 'doh:google'
    doh_cloudflare = 'doh:cloudflare'
    unknown = 'unknown'

class DomainAvailability(BaseModel):
    domain: str = Field(description='e.g., brand-name.com')
    available: bool | None = Field(description='True=free, False=registered, None=unknown (transient error)')
    rdap_status: int | None = Field(default=None, description='HTTP status from RDAP (404, 200, etc.)')
    authoritative: bool = Field(default=False, description='True when result is from RDAP')
    source: Source = Field(default=Source.unknown)
    note: str | None = None

    @field_validator('domain')
    @classmethod
    def _validate_domain(cls, v: str) -> str:
        if not v or '.' not in v:
            raise ValueError('domain must include a TLD, e.g., brand-name.com')
        return v

class DomainCheckError(Exception):
    ...

def normalize_brand_label(label: str) -> str:
    """Lowercase, keep [a-z0-9-], collapse dashes, trim; IDNA for non-ASCII."""

def is_com_available(brand: str, *, timeout_s: float = 5.0) -> DomainAvailability:
    """Authoritative RDAP check against Verisign. 404 => available, 200 => registered."""

def check_www_resolves(domain: str, *, provider: str = 'google', timeout_s: float = 5.0) -> bool:
    """Optional: DoH A-record probe for www.<domain>; returns True if it resolves."""

def check_many(labels: list[str], *, timeout_s: float = 5.0) -> dict[str, DomainAvailability]:
    """Batch sync helper; serial by default, can accept a session for efficiency."""
```

### Optional Service Class (follows coding guide)
```
# src/brand_name_gen/domain_checker.py
"""
Domain availability checking service.

Provides a stateful checker for `.com` availability using RDAP
with optional DNS probes. Follows project coding guide:
 - module-level docstring (NumPy style)
 - constructors take no arguments
 - use factory methods for initialization
 - member fields prefixed with m_ (service class only)
 - Pydantic for data models (no m_ on models)
"""

from typing import Optional, Dict, List
import requests

class DomainChecker:
    """
    Stateful service for domain availability checks.

    Parameters
    ----------
    (use factory methods instead of constructor parameters)

    Attributes
    ----------
    m_timeout_s : float or None
        Request timeout in seconds
    m_session : requests.Session or None
        Optional shared HTTP session
    m_rdap_base : str or None
        RDAP base URL (defaults to Verisign for `.com`)

    Examples
    --------
    >>> checker = DomainChecker.from_defaults()
    >>> result = checker.check_com("brand-name")
    >>> result.available
    True
    """

    def __init__(self) -> None:
        self.m_timeout_s: Optional[float] = None
        self.m_session: Optional[requests.Session] = None
        self.m_rdap_base: Optional[str] = None

    @property
    def timeout_s(self) -> Optional[float]:
        """float or None: Current timeout in seconds."""
        return self.m_timeout_s

    def set_timeout(self, timeout_s: float) -> None:
        """Set timeout value in seconds."""
        self.m_timeout_s = timeout_s

    @classmethod
    def from_defaults(cls) -> "DomainChecker":
        """
        Create a checker with sensible defaults.

        Returns
        -------
        DomainChecker
            Instance configured with default RDAP base and timeout
        """
        inst = cls()
        inst.m_timeout_s = 5.0
        inst.m_rdap_base = "https://rdap.verisign.com/com/v1/domain/{}"
        inst.m_session = requests.Session()
        return inst

    @classmethod
    def from_session(cls, session: requests.Session, *, timeout_s: float = 5.0, rdap_base: Optional[str] = None) -> "DomainChecker":
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
        url = (self.m_rdap_base or "https://rdap.verisign.com/com/v1/domain/{}").format(domain)
        s = self.m_session or requests
        r = s.get(url, timeout=self.m_timeout_s or 5.0)
        if r.status_code == 404:
            return DomainAvailability(domain=domain, available=True, rdap_status=404, authoritative=True, source=Source.rdap_verisign)
        if r.ok:
            return DomainAvailability(domain=domain, available=False, rdap_status=r.status_code, authoritative=True, source=Source.rdap_verisign)
        return DomainAvailability(domain=domain, available=None, rdap_status=r.status_code, authoritative=True, source=Source.rdap_verisign, note='transient')
```

## Public API (Async optional)
```
# src/brand_name_gen/domain_check_async.py (optional)

async def is_com_available_async(brand: str, *, timeout_s: float = 5.0) -> DomainAvailability: ...
async def check_many_async(labels: list[str], *, timeout_s: float = 5.0, concurrency: int = 10) -> dict[str, DomainAvailability]: ...
```

## Behavior & Semantics
- RDAP (.com) endpoint: `https://rdap.verisign.com/com/v1/domain/<domain>`.
  - HTTP 404 => available=True, authoritative=True, source='rdap:verisign'.
  - HTTP 200 => available=False, authoritative=True.
  - Other (e.g., 429/5xx) => available=None; raise DomainCheckError only if caller requests strict mode.
- DoH fallback (diagnostic only): `https://dns.google/resolve?name=<name>&type=NS` or Cloudflare `https://cloudflare-dns.com/dns-query?name=<name>&type=NS` with `Accept: application/dns-json`.
  - Use only to add context when RDAP is unreachable; never contradict RDAP.
- Normalization: implement per hint; convert spaces to `-`, collapse dashes, strip leading/trailing `-`, IDNA encode when needed.
- Timeouts & Retries: default 5s timeout; one retry with exponential backoff (e.g., 0.5s, jitter) for 429/5xx; respect `Retry-After` if present.
- Caching (optional): in‑memory TTL cache keyed by domain (e.g., 10–60 minutes) to limit RDAP calls; make cache pluggable.
 - Coding guide compliance: service classes use `m_` members, constructor without args, factory classmethods (`from_defaults`, `from_session`); Pydantic models use regular field names.

## Minimal Dependencies
- Required: `pydantic>=2`, `requests`, `idna`.
- Optional: `httpx` (async), `cachetools` (TTLCache). Keep optional to avoid forcing users.

## Code Sketch (Sync)
```
import re, time, random, requests, idna
from enum import Enum
from pydantic import BaseModel

RDAP_COM = "https://rdap.verisign.com/com/v1/domain/{}"

class Source(str, Enum):
    rdap_verisign = 'rdap:verisign'
    doh_google = 'doh:google'
    doh_cloudflare = 'doh:cloudflare'
    unknown = 'unknown'

class DomainAvailability(BaseModel):
    domain: str
    available: bool | None
    rdap_status: int | None = None
    authoritative: bool = False
    source: Source = Source.unknown
    note: str | None = None

class DomainCheckError(Exception):
    pass

def normalize_brand_label(label: str) -> str:
    s = re.sub(r"[^A-Za-z0-9-]+", "-", label.strip().lower())
    s = re.sub(r"-+", "-", s).strip('-')
    if not s:
        raise DomainCheckError("empty label after normalization")
    # IDNA for non-ascii (label may already be ascii; safe to try)
    try:
        s.encode('ascii')
    except UnicodeEncodeError:
        s = idna.encode(s).decode()
    return s

def _rdap_check(domain: str, timeout_s: float) -> DomainAvailability:
    url = RDAP_COM.format(domain)
    for attempt in (0, 1):
        r = requests.get(url, timeout=timeout_s)
        if r.status_code == 404:
            return DomainAvailability(domain=domain, available=True, rdap_status=404, authoritative=True, source=Source.rdap_verisign)
        if r.ok:
            return DomainAvailability(domain=domain, available=False, rdap_status=r.status_code, authoritative=True, source=Source.rdap_verisign)
        if r.status_code in (429, 500, 502, 503, 504) and attempt == 0:
            wait = 0.5 + random.random() * 0.5
            time.sleep(wait)
            continue
        return DomainAvailability(domain=domain, available=None, rdap_status=r.status_code, authoritative=True, source=Source.rdap_verisign, note='transient')
    return DomainAvailability(domain=domain, available=None, rdap_status=None, authoritative=False, source=Source.unknown, note='unreachable')

def is_com_available(brand: str, *, timeout_s: float = 5.0) -> DomainAvailability:
    label = normalize_brand_label(brand)
    domain = f"{label}.com"
    return _rdap_check(domain, timeout_s)
```

## Documentation Requirements
- Add module-level docstrings (NumPy style) to `domain_check.py` and `domain_checker.py` describing purpose, classes/functions, and examples.
- Add NumPy-style docstrings for all public functions/methods and Pydantic models.


## CLI Integration
- Add flag `--check-domain <brand>` to `brand-name-gen` CLI.
  - Outputs JSON or human text with `DomainAvailability` fields.
  - Optionally `--doh` to probe `www.<domain>` resolution for diagnostics.

## Tests
- Unit tests with `responses` (mock RDAP 404/200/429) and deterministic backoff (patch sleep).
- Normalization tests: non-ASCII (IDNA), spaces, punctuation, long labels, leading/trailing hyphens.
- CLI test: exit code 0 + parse JSON output.

## Acceptance Criteria
- Given a non-existent `.com` domain, API returns `available=True`, `authoritative=True`, `rdap_status=404`.
- Given a known registered domain, API returns `available=False`, `authoritative=True`, `rdap_status=200`.
- Transient errors surface as `available=None` and do not crash callers.
- Normalization is predictable and documented.

## Future Extensions
- Support additional gTLDs/ccTLDs by mapping RDAP base URLs.
- Async batch mode with concurrency; external cache adapters (Redis, diskcache).
- Integrate into LLM name generator to filter/score candidates by availability.
