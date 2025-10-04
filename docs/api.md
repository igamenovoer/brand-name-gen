# API Reference

## HEADER
- **Purpose**: Document the public Python API
- **Status**: Active
- **Date**: 2025-10-04
- **Dependencies**: None
- **Target**: Developers

## brand_name_gen.generate_names
```
generate_names(keywords: Iterable[str], *, style: str | None = None, limit: int = 20) -> list[str]
```

Generate a list of unique, title-cased brand name ideas.

Parameters:
- `keywords`: seed words like ["eco", "solar"]
- `style`: one of modern | classic | playful | professional (optional)
- `limit`: maximum number of results to return

Returns:
- List of strings (brand name suggestions)

---

## brand_name_gen.domain_check

### DomainAvailability (Pydantic model)
Fields: `domain: str`, `available: bool | None`, `rdap_status: int | None`, `authoritative: bool`, `source: str`, `note: str | None`.

### is_com_available(brand: str, *, timeout_s: float = 5.0) -> DomainAvailability
Normalize `brand` and query Verisign RDAP. 404 => available; 200 => registered.

### check_www_resolves(domain: str, *, provider: str = 'google', timeout_s: float = 5.0) -> bool
DNS-over-HTTPS probe for `www.<domain>` A record. Diagnostic only.

### check_many(labels: list[str], *, timeout_s: float = 5.0) -> dict[str, DomainAvailability]
Batch helper to check multiple labels serially.

Example
```python
from brand_name_gen.domain_check import is_com_available

res = is_com_available("brand-name")
print(res.available)
```

---

## brand_name_gen.domain_checker

### DomainChecker
Stateful service with factory methods:
- `from_defaults()`
- `from_session(session, *, timeout_s=5.0, rdap_base=None)`

Method:
- `check_com(brand: str) -> DomainAvailability`

Example
```python
from brand_name_gen.domain_checker import DomainChecker

checker = DomainChecker.from_defaults()
result = checker.check_com("brand-name")
```
