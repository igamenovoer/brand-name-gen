# How to use DataForSEO to fetch Google-like SERP rankings

This hint shows how to use DataForSEO SERP API to programmatically retrieve Google Search results in ranked order (positions), with controls for location, language, device, and depth. It also covers verifying results, extracting the top URLs, and optionally piping them to an extraction layer like Tavily/Firecrawl.

> What you’ll get: structured JSON with result positions (rank_absolute/rank_group) that closely match a real Google SERP for the specified parameters (no personalization). This is the recommended, compliant alternative to DIY scraping.

## Prerequisites
- DataForSEO account and API credentials (HTTP Basic Auth: login/password)
- Endpoints: “Live” for immediate requests, or “Task” flow for queued jobs
- Pick the Google “Organic” endpoint; use “advanced” for full SERP features

Key docs
- Overview: https://docs.dataforseo.com/v3/serp-overview/
- Google SERP overview: https://docs.dataforseo.com/v3/serp-google-overview/
- Google Organic (live/advanced): https://docs.dataforseo.com/v3/serp-google-organic-overview/
- Product page: https://dataforseo.com/apis/serp-api/google-serp-api

## Python SDKs (official clients)
- DataForSEO official Python client: `dataforseo-client`
  - PyPI: https://pypi.org/project/dataforseo-client/
  - GitHub: https://github.com/dataforseo/PythonClient
  - Install:
    ```bash
    pip install dataforseo-client
    ```
  - Notes: This client is generated from DataForSEO’s OpenAPI spec. Class and method names are subject to SDK versions; see the README/examples in the repo for exact usage. Typical flow is to configure Basic Auth, build the payload list, and call the Google Organic Live Advanced endpoint through the corresponding API class.

- Tavily Python client (for downstream extraction): `tavily-python`
  - PyPI/GitHub: https://github.com/tavily-ai/tavily-python
  - Install:
    ```bash
    pip install tavily-python
    ```
  - Notes: Useful to extract LLM-ready content from the ranked URLs you obtain from DataForSEO.

## Core concepts
- rank_absolute: the global position across all SERP elements (preferred for ordering)
- rank_group: position within a group of similar elements
- se_domain: Google domain (e.g., google.com, google.co.uk)
- location_code / language_code: geo/language targeting; lookup via dedicated endpoints
- device / os: desktop (windows, macos) or mobile (android, ios)
- depth: how many results DataForSEO should collect (e.g., 50, 100)
- check_url: a verification URL you can open in an Incognito window to visually confirm parity

Limitations
- No user-specific personalization/history. Layout can change; parity is approximate to your parameters.

## Look up locations and languages

Use DataForSEO’s “Locations” and “Languages” endpoints to find IDs/codes. Example (cURL):

```bash
curl -u '<LOGIN>:<PASSWORD>' \
  -H 'Content-Type: application/json' \
  -d '[{"country_code":"US","city":"Seattle"}]' \
  'https://api.dataforseo.com/v3/serp/google/locations'
```

```bash
curl -u '<LOGIN>:<PASSWORD>' \
  -H 'Content-Type: application/json' \
  -d '[{"language_name":"English"}]' \
  'https://api.dataforseo.com/v3/serp/google/languages'
```

Extract `location_code` and `language_code` from the response, then reuse in your SERP calls.

## Get ranked Google results (Live Advanced)

Minimal cURL (replace placeholders):

```bash
curl -u '<LOGIN>:<PASSWORD>' \
  -H 'Content-Type: application/json' \
  -d '[
    {
      "keyword": "best solar panels 2025",
      "se_domain": "google.com",
      "location_code": 2840,            
      "language_code": "en",
      "device": "desktop",
      "os": "macos",
      "depth": 50
    }
  ]' \
  'https://api.dataforseo.com/v3/serp/google/organic/live/advanced'
```

Python (requests):

```python
import requests
from requests.auth import HTTPBasicAuth

auth = HTTPBasicAuth("<LOGIN>", "<PASSWORD>")
url = "https://api.dataforseo.com/v3/serp/google/organic/live/advanced"
payload = [{
    "keyword": "best solar panels 2025",
    "se_domain": "google.com",
    "location_code": 2840,  # example; look up via Locations API
    "language_code": "en",
    "device": "desktop",
    "os": "macos",
    "depth": 50
}]

resp = requests.post(url, json=payload, auth=auth, timeout=30)
resp.raise_for_status()
data = resp.json()

# Navigate: tasks -> result -> items
tasks = data.get("tasks", [])
if not tasks: raise RuntimeError("No tasks in response")
results = tasks[0].get("result", [])
items = results[0].get("items", []) if results else []

# Filter organic and sort by absolute rank
organic = [it for it in items if it.get("type") == "organic"]
organic_sorted = sorted(organic, key=lambda it: it.get("rank_absolute", 10**9))

top10 = [(it.get("rank_absolute"), it.get("title"), it.get("url")) for it in organic_sorted[:10]]
for pos, title, url_ in top10:
    print(pos, title, url_)

# Optional: verify visually (open in Incognito)
check_url = results[0].get("check_url") if results else None
print("Verify:", check_url)
```

Notes
- Use “regular” vs “advanced”: advanced captures richer SERP features and can interleave elements.
- Prefer `rank_absolute` for your final ordering. Some workflows also keep `rank_group` for per-feature analysis.

### Usage example: official DataForSEO Python client (SDK)
The SDK wraps auth, request models, and responses for you. Minimal example for Google Organic Live Advanced:

```python
from dataforseo_client import Configuration, ApiClient, SerpApi
from dataforseo_client.models.serp_google_organic_live_advanced_request_info import (
  SerpGoogleOrganicLiveAdvancedRequestInfo,
)

# Configure Basic Auth
cfg = Configuration(username="<LOGIN>", password="<PASSWORD>")

with ApiClient(cfg) as api_client:
  serp_api = SerpApi(api_client)
  req = SerpGoogleOrganicLiveAdvancedRequestInfo(
    keyword="best solar panels 2025",
    location_code=2840,
    language_code="en",
    # Optional extras
    # device="desktop",  # if supported by your SDK version/model
    # os="macos",
    # calculate_rectangles=True,
  )
  api_response = serp_api.google_organic_live_advanced([req])

  # Inspect api_response for tasks/result/items depending on SDK version
  # print(api_response)
```

Source: DataForSEO PythonClient docs (Context7 mirror) — Google Organic Live Advanced example
https://github.com/dataforseo/pythonclient/blob/master/docs/serp_api.md#_snippet_45

## Approximating a user’s context
- Choose the correct `se_domain` (e.g., google.co.uk), `location_code`, and `language_code`.
- Set `device`/`os` (mobile vs desktop) to match your target audience.
- Remember: individual personalization/history cannot be mirrored.

## Optional: screenshots and AI summary
- Screenshot endpoint: helpful to confirm layout/state for a query.
- AI Summary endpoint: summarizes the SERP contents for quick insights (where supported).

## Pipe ranked URLs into an extraction layer (hybrid)
If you need clean, LLM-ready content:
1) Use DataForSEO to get a Google-ordered list of URLs.
2) Feed the top N URLs into an extractor (e.g., Tavily Extract or Firecrawl scrape) for content.

Pseudo-code (Python):

```python
# after obtaining organic_sorted
urls = [it[2] for it in top10]

# Tavily example (conceptual)
# tvly_client = TavilyClient(api_key=...)
# extracted = [tvly_client.extract(url=u) for u in urls]

# Firecrawl example (conceptual)
# fc = FirecrawlClient(api_key=...)
# extracted = [fc.scrape_url(u, formats=["markdown"]) for u in urls]
```

## Troubleshooting & tips
- If results look off, double-check `location_code` and `language_code`.
- Increase `depth` to capture more results (costs more credits).
- Some SERP features may push organic results down; always sort by `rank_absolute`.
- Rate/price: consult your plan; Live endpoints return immediately but consume credits per call.

## References
- DataForSEO SERP overview: https://docs.dataforseo.com/v3/serp-overview/
- Google SERP overview: https://docs.dataforseo.com/v3/serp-google-overview/
- Google Organic (Live/Advanced): https://docs.dataforseo.com/v3/serp-google-organic-overview/
- Locations: https://docs.dataforseo.com/v3/serp-google-locations/
- Languages: https://docs.dataforseo.com/v3/serp-google-languages/
- Product page: https://dataforseo.com/apis/serp-api/google-serp-api
