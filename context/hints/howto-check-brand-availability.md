## HEADER
- Purpose: Checklist and official channels to verify domain and mobile app identifier uniqueness for a new brand, with best practices and links
- Status: Active
- Date: 2025-10-04
- Dependencies: Internet access; optional Apple/Google developer accounts; registrar access
- Target: Founders, PMs, mobile engineers, DevOps

# Brand Availability (Domains + App IDs)

## Goals
- Secure a domain without conflict and with good defenses.
- Ensure iOS and Android app identifiers are unique and stable.
- Follow official, verifiable sources and proven practices.

## What To Check

1) Domains (availability, conflicts, security)
- Availability: search exact/variant names on a registrar; verify status via ICANN RDAP/WHOIS.
- Conflicts: scan for live sites using similar names, typos, hyphenations, plural/singular; consider key TLDs (.com, relevant ccTLDs, industry TLDs).
- Defensive: register the canonical domain plus 1–3 strategic TLDs or obvious typos; enable privacy and auto‑renew.
- Security: enable DNSSEC; serve HTTPS from day 1 (.app TLD enforces HTTPS via HSTS preload).

2) Trademarks (clearance)
- Search in launch markets before committing the name:
  - United States: USPTO Trademark Search.
  - European Union: EUIPO (TMview / eSearch Plus).
  - International view: WIPO Global Brand Database.
- Check identical/similar marks in overlapping Nice classes; consult counsel for comprehensive clearance/filing if investing materially.

3) Mobile app identifiers (must be unique and persistent)
- iOS (Apple):
  - Bundle ID is the unique app identifier; cannot be changed after a build upload. Use reverse‑DNS bound to your domain (e.g., `com.yourco.product`).
  - App name (store) max 30 chars; ensure uniqueness at submission time.
  - Quick checks:
    - Try registering an explicit Bundle ID in Certificates, Identifiers & Profiles (duplicates not allowed).
    - Optional probe: iTunes Lookup API (returns if a bundleId is live): `https://itunes.apple.com/lookup?bundleId=com.example.app`.
- Android (Google Play):
  - Package name (`applicationId`) is unique and permanent on Play; cannot be changed or re‑used once taken.
  - Quick checks:
    - Probe URL: `https://play.google.com/store/apps/details?id=com.example.app&hl=en&gl=US` (200 = exists; 404 = likely free; regional caveats apply). Definitive lock occurs when creating the app in Play Console.
 - Developer Verification (rolling out): includes “package name registration” linking IDs to verified identities—plan to register early.

### Android — App Title vs Package Name (Deep Dive)
- App title (store listing name)
  - Not globally unique; duplicates across developers are allowed, but avoid confusion/impersonation risks.
  - Must follow Metadata policy: title length ≤ 30 chars; avoid promotional or ranking terms (e.g., "best", "#1", "free"); avoid emoji/excessive punctuation; avoid ALL CAPS unless part of your brand.
  - Localized per language; keep consistent across locales and suitable for a general audience.
- Package name (`applicationId`)
  - Globally unique on Play; locks when you create the app in Play Console and cannot be changed later (renaming requires a new app).
  - Choose reverse‑DNS under a domain you control, e.g., `com.yourco.brandname`. Keep lowercase; segments start with a letter; only letters/digits (underscore technically permitted by Java but discouraged).
  - To be certain you can publish with your brand: create the app entry early in Play Console to reserve the `applicationId`, even if you don’t publish immediately.
- Programmatic checks (free, indicative)
  - Probe if a packageId exists: `https://play.google.com/store/apps/details?id=com.example.app&hl=en&gl=US` → HTTP 200 means exists; 404 likely not taken. Regional quirks and A/B pages can affect responses.
  - Search for title collisions: site search or Play search UI for your intended app title in your launch locales. Collisions won’t block submission but may impact discoverability and risk confusion.

Python snippet (indicative only)
```
import requests

def play_exists(package: str) -> bool:
    url = f"https://play.google.com/store/apps/details?id={package}&hl=en&gl=US"
    r = requests.get(url, timeout=10)
    return r.status_code == 200

# Example
print(play_exists("com.yourco.brandname"))
```

## Recommended Workflow
1) Shortlist 3–5 name candidates
- For each: domain + RDAP, quick web/social handle scan, USPTO/EUIPO/WIPO prelim searches.

2) Legal triage
- For go‑forward candidates, commission comprehensive clearance and consider filing (in launch markets) before public reveal.

3) Reserve and lock identifiers
- Domains: buy canonical + key TLDs; enable privacy, auto‑renew, DNSSEC.
- Apple: register explicit Bundle ID; create the app record in App Store Connect to lock ID + name.
- Google Play: create app in Play Console to lock package name; align with Developer Verification timelines.

4) Freeze in code/CI and docs
- iOS: set `PRODUCT_BUNDLE_IDENTIFIER` in Xcode/CI.
- Android: set `applicationId` in `app/build.gradle` and lock via CI.
- Document canonical IDs in repo docs/runbooks.

5) Monitor
- Keep auto‑renew on; set brand/TM watch alerts; periodically re‑scan for conflicts.

## Naming Conventions
- Reverse‑DNS from a domain you own: `com.yourco.product`.
- Keep stable; suffix variants carefully: `com.yourco.product.dev`, `com.yourco.product.beta`.
- Avoid trademarked/sensitive terms; keep readable and scalable for sub‑brands/locales.

## Android Submission Checklist (Brand‑specific)
- Title fits ≤ 30 chars, policy‑compliant language; no promotional or ranking terms; no emoji/excessive punctuation; consistent across locales.
- Package `applicationId` selected under an owned domain; create app in Play Console to reserve ID.
- Avoid user confusion: check for existing apps using identical/similar titles in your category/markets; adjust subtitle/short description to clarify.
- Align with Developer Verification timelines; register package name if prompted.

## Quick Commands (Indicative)
- RDAP/WHOIS: ICANN Lookup: https://lookup.icann.org/
- iOS probe: `curl 'https://itunes.apple.com/lookup?bundleId=com.example.app'`
- Play probe: `curl -I 'https://play.google.com/store/apps/details?id=com.example.app&hl=en&gl=US'`

Note: Probes are indicative. Definitive uniqueness is enforced by Apple Developer/App Store Connect and Google Play Console at creation time.

## Official Sources
- Apple — App information (Bundle ID immutability, 30‑char name):
  - https://developer.apple.com/help/app-store-connect/reference/app-information/
- Apple — Bundle IDs (overview/API context):
  - https://developer.apple.com/documentation/appstoreconnectapi/bundle-ids
- Google Play Console Help — Create and set up your app (unique, permanent package names):
  - https://support.google.com/googleplay/android-developer/answer/9859152
- Android Developer Verification (package name registration timeline):
  - https://developer.android.com/developer-verification/guides
- Play Console Help — Metadata policy (title length, language restrictions):
  - https://support.google.com/googleplay/android-developer/answer/9898842
- Play Console Help — Store listing best practices (title must be 30 chars or less):
  - https://support.google.com/googleplay/android-developer/answer/13393723
- ICANN — Registration Data Lookup (RDAP) and WHOIS overview:
  - https://lookup.icann.org/
  - https://www.icann.org/resources/pages/whois-rdds-2023-11-02-en
- USPTO — Search trademarks:
  - https://www.uspto.gov/trademarks/search
- EUIPO — Trade mark availability; TMview:
  - https://www.euipo.europa.eu/en/trade-marks/before-applying/availability
  - https://www.tmdn.org/tmview/
- WIPO — Global Brand Database:
  - https://www.wipo.int/en/web/global-brand-database
