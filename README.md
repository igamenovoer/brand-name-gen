# Brand Name Generator

Generate unique, memorable brand names from seed keywords. Includes a simple Python API and a CLI for quick use.

## Overview

This project aims to create an intelligent brand name generator that can produce memorable, catchy, and market-appropriate brand names for various industries and products.

## Features (Planned)

- **Industry-specific generation**: Generate names tailored to specific industries (tech, fashion, food, etc.)
- **Style variations**: Create names in different styles (modern, classic, playful, professional)
- **Availability checking**: Verify domain availability and trademark conflicts
- **Multi-language support**: Generate names in different languages
- **Semantic analysis**: Ensure generated names convey appropriate meanings and emotions
- **Export functionality**: Export generated names in various formats

## Getting Started

Install from PyPI (after first release):
```
pip install brand-name-gen
```

CLI (pixi or system shell):
```
# Generate names
brand-name-gen-cli generate eco solar --style modern --limit 5

# Check .com availability (RDAP) and probe www
brand-name-gen-cli check-www brand-name --json

# Android title checks (ASO)
# AppFollow (requires APPFOLLOW_API_KEY; .env auto-loaded)
brand-name-gen-cli check-android appfollow "Your Brand" --country us --json
# Google Play web search (heuristic)
brand-name-gen-cli check-android playstore "Your Brand" --hl en --gl US --json

# Search engine ranking (DataForSEO)
# Requires DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD (prefer .env in project root)
brand-name-gen-cli check-search-engine dataforseo "Your Brand" --se-domain google.com --location-code 2840 --language-code en --device desktop --os macos --depth 50 --json

# Uniqueness score (aggregates Domain/AppFollow/Play/Google)
brand-name-gen-cli evaluate uniqueness "Your Brand" --matcher auto

# Demos (with progress)
# These print step-by-step progress using Rich and keep going even if a step fails.
# Simple (builtin matcher)
pixi run -e dev demo-check-unique-simple "Your Brand"
# Advanced (RapidFuzz matcher)
pixi run -e dev demo-check-unique-advanced "Your Brand"
# Optional: show JSON output from each step
pixi run -e dev demo-check-unique-advanced "Your Brand" -- --json
```

Python API:
```python
from brand_name_gen import generate_names

print(generate_names(["eco", "solar"], style="modern", limit=5))
```

Domain availability (.com) via RDAP:
```python
from brand_name_gen.domain.domain_check import is_com_available

res = is_com_available("brand-name")
print(res.domain, res.available)  # brand-name.com True/False/None
```

Android title checks:
```python
from brand_name_gen.android.title_check import check_title_appfollow, check_title_playstore

# AppFollow (set APPFOLLOW_API_KEY in environment or .env)
af = check_title_appfollow("Your Brand", country="us")
print(af.unique_enough, [c.term for c in af.collisions])

# Google Play web search (heuristic)
ps = check_title_playstore("Your Brand", hl="en", gl="US")
print(ps.unique_enough, [c.term for c in ps.collisions])
```

Tip: create a .env with `APPFOLLOW_API_KEY=...` in the project root; the CLI auto-loads it.

For DataForSEO, also add:
```
DATAFORSEO_LOGIN=your_login
DATAFORSEO_PASSWORD=your_password
```
The CLI prefers values from `.env` and falls back to `os.environ`.

YAML configuration (optional): place `brand-name-gen-config.yaml` in your project root (or set `BRAND_NAME_GEN_CONFIG=/path/to/file`) to control matcher engine, component weights, and grade thresholds. See `examples/brand-name-gen-config.yaml` for a commented template. The evaluator loads YAML automatically.

Provider failures: if any provider call fails (network/auth), the evaluator assigns a neutral component score (50% of that component's weight) and includes a warning in the report, rather than aborting.

Python SDK (DataForSEO):
```python
from brand_name_gen.search.dataforseo.types import GoogleRankQuery
from brand_name_gen.search.dataforseo.google_rank import DataForSEORanker

ranker = DataForSEORanker.from_env()
res = ranker.run(GoogleRankQuery(keyword="hb-app"))
print(res.top_position, [m.title for m in res.matches[:5]])
```

## Technology Stack

*To be determined based on requirements*

## Contributing

*Guidelines to be established*

## License

MIT
