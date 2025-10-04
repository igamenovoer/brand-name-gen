## HEADER
- Purpose: Practical workflow and checks to make an Android (Google Play) app title effectively unique and discoverable, with automation examples
- Status: Active
- Date: 2025-10-04
- Dependencies: Internet; optional Tavily API key (`tavily-python`)
- Target: PMs, ASO specialists, mobile engineers

# How to Make Your Android App Title Unique (Google Play)

Reality check: Google Play does not enforce globally unique app titles. Treat uniqueness as a product/ASO requirement. Your goals are (a) no exact matches and (b) no confusingly similar titles in your category and locales, while staying policy‑compliant.

## Policy Constraints (must pass)
- App title length ≤ 30 characters
- No emojis, excessive punctuation, ALL CAPS (unless part of brand)
- No promotional/ranking terms (e.g., “best”, “#1”, “free”)
- References (official):
  - Metadata policy: https://support.google.com/googleplay/android-developer/answer/9898842
  - Store listing best practices: https://support.google.com/googleplay/android-developer/answer/13393723

## Workflow
1) Define scope
- Canonical title (≤ 30 chars), category, and target locales (e.g., en-US, de-DE, fr-FR).

2) Manual searches (exact + variants)
- Play search URL (per locale):
  - `https://play.google.com/store/search?q="Your%20App%20Title"&c=apps&hl=en&gl=US`
- Web search (site operator):
  - `site:play.google.com/store/apps "Your App Title"`
- Check variants: hyphen/no‑hyphen, singular/plural, spacing changes, common misspellings, transliterations.

3) Automated web scan (Tavily)
```python
from __future__ import annotations
import os, re
from difflib import SequenceMatcher
from tavily import TavilyClient

def norm(s: str) -> str:
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", " ", s).strip()
    return re.sub(r"\s+", " ", s)

def similar(a: str, b: str, *, threshold: float = 0.9) -> bool:
    return SequenceMatcher(None, norm(a), norm(b)).ratio() >= threshold

def find_conflicts(title: str, max_results: int = 15) -> dict:
    tv = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])  # set env first
    query = f'site:play.google.com/store/apps "{title}"'
    res = tv.search(query, max_results=max_results)
    hits = []
    for r in res.get("results", []):
        t = r.get("title", "")
        if norm(t) == norm(title) or similar(t, title):
            hits.append({"title": t, "url": r.get("url")})
    return {"query": query, "conflicts": hits, "unique": len(hits) == 0}

# Example
# print(find_conflicts("BrandName"))
```

4) Decision rules (suggested)
- Unique if: no exact matches and no “very close” titles (normalized or similarity ≥ 0.9) in your category/locales.
- If collisions exist: prefer a more distinctive core title; or add a short, policy‑compliant descriptor (e.g., “BrandName — Budget Planner”) while staying ≤ 30 chars.
- Validate localization: repeat for key locales and transliterations.

5) Lock identifiers and monitor
- Reserve unique `applicationId` by creating the app in Play Console (package name is globally unique and permanent).
- Re‑scan before submission and periodically (e.g., monthly) to catch new conflicts.

## Notes
- Title uniqueness is not enforced by Play, but discoverability and legal clarity matter. Pair these checks with trademark clearance in launch markets (USPTO/EUIPO/WIPO).
- Avoid scraping Play HTML directly; prefer web search (site operator) or APIs like Tavily for resilience.

