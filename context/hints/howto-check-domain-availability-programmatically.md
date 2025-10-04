## HEADER
- Purpose: Programmatically verify if `www.<brand>.com` is available (no registration), using free, authoritative sources
- Status: Active
- Date: 2025-10-04
- Dependencies: Internet access; Python optional for examples
- Target: Brand-name generator pipeline, CLI, backend services

# How to Check .com Domain Availability (Free, Programmatic)

Key idea: you do NOT need a paid registrar API. For .com, the registry (Verisign) exposes a public RDAP endpoint. If the apex domain `<brand>.com` is unregistered, RDAP returns HTTP 404. If registered, it returns HTTP 200 with JSON details. Checking `www.<brand>.com` specifically is unnecessary once you own the apex — you can always create `www` yourself.

## 1) Normalize the Brand → Domain
- Lowercase; keep `a–z`, `0–9`, and `-`; strip leading/trailing `-`.
- For non‑ASCII, encode with IDNA (Punycode): `idna.encode(label).decode()`.

## 2) Authoritative RDAP Check (Free)
- Endpoint (.com): `https://rdap.verisign.com/com/v1/domain/<domain>`
- Signal: `HTTP 404` → available; `HTTP 200` → registered.

Example (curl)
```
curl -i https://rdap.verisign.com/com/v1/domain/brand-name.com
# 404 Not Found  => available
# 200 OK         => registered
```

Python snippet
```
import requests, idna

def normalize(label: str) -> str:
    label = label.strip().lower().strip('-')
    # keep letters, digits, hyphen; convert spaces/others to hyphen
    import re
    label = re.sub(r"[^a-z0-9-]+", "-", label)
    label = re.sub(r"-+", "-", label).strip('-')
    # idna for non-ascii inputs
    if any(ord(c) > 127 for c in label):
        label = idna.encode(label).decode()
    return label

def is_com_available(brand: str) -> bool:
    domain = f"{normalize(brand)}.com"
    url = f"https://rdap.verisign.com/com/v1/domain/{domain}"
    resp = requests.get(url, timeout=10)
    if resp.status_code == 404:
        return True
    if resp.ok:
        return False
    # network or transient error: treat as unknown; caller may retry
    raise RuntimeError(f"RDAP error {resp.status_code}")

# Optional: check if www resolves (diagnostic only)
def www_resolves(domain: str) -> bool:
    # Google DoH JSON API (free)
    import requests
    q = f"https://dns.google/resolve?name=www.{domain}&type=A"
    r = requests.get(q, timeout=10).json()
    # Status 0=NOERROR, 3=NXDOMAIN
    return r.get("Status") == 0 and any(ans.get("data") for ans in r.get("Answer", []))
```

Usage
```
if is_com_available("brand-name"):
    print("brand-name.com is available. You can register it and create www.brand-name.com.")
else:
    print("Taken — pick another name or TLD.")
```

## 3) Why RDAP (vs WHOIS/DNS)?
- RDAP is the ICANN-standard, JSON/HTTP protocol from registries/registrars.
- Free and authoritative; Verisign is the .com registry. WHOIS is text‑based and inconsistent; DNS may return NXDOMAIN even for registered but undelegated domains.

## 4) Optional Fallback: DNS over HTTPS (Free)
Check delegation (NS records) for the apex; NXDOMAIN often implies unregistered, but RDAP is definitive.
```
curl 'https://dns.google/resolve?name=brand-name.com&type=NS'
# JSON Status: 3 => NXDOMAIN (likely unregistered), 0 => delegated
```

## 5) Rate Limits & Practical Tips
- RDAP is rate‑limited per IP; cache results in your pipeline, batch queries, and retry with backoff.
- Only query the apex (`<brand>.com`); `www.<brand>.com` depends on your DNS once registered.
- Consider checking key variants (`brandname.com`, hyphen/no‑hyphen) to avoid near‑collisions.

## References
- Verisign RDAP (.com/.net): https://www.verisign.com/en_US/domain-names/registration-data-access-protocol/index.xhtml
- ICANN RDAP/WHOIS overview: https://lookup.icann.org/
- Google DoH JSON API: https://developers.google.com/speed/public-dns/docs/doh/json
- Cloudflare DoH JSON API: https://developers.cloudflare.com/1.1.1.1/encryption/dns-over-https/make-api-requests/dns-json/

