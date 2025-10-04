# Domain Availability (.com)

## Overview
Check if `<brand>.com` is registered using Verisign RDAP (authoritative) and optionally probe `www.<brand>.com` via DNS-over-HTTPS (diagnostic). This is free and requires no registrar API.

## TL;DR
- RDAP 404 → available; 200 → registered
- Query apex only (`brand-name.com`); `www` is under your control once registered

## Quick Check (curl)
```bash
# Available → 404
curl -i https://rdap.verisign.com/com/v1/domain/brand-name.com

# Registered → 200
curl -i https://rdap.verisign.com/com/v1/domain/openai.com
```

## Python API
```python
from brand_name_gen.domain_check import is_com_available, check_www_resolves

result = is_com_available("brand-name")
print(result.model_dump())  # {'domain': 'brand-name.com', 'available': True, ...}

# Optional diagnostic (DNS)
if result.available is False:
    print(check_www_resolves(result.domain))  # True if www resolves
```

## Normalization Rules
- Lowercase; keep `a–z`, `0–9`, `-`
- Replace other chars with `-`, collapse, trim
- Use IDNA (Punycode) for non-ASCII

## Notes
- Rate limits apply; batch and cache results
- Treat transient errors as unknown; retry with backoff

## References
- Verisign RDAP (.com/.net): https://www.verisign.com/en_US/domain-names/registration-data-access-protocol/index.xhtml
- ICANN Lookup: https://lookup.icann.org/
- Google DoH JSON API: https://developers.google.com/speed/public-dns/docs/doh/json

