# How to use Tavily in Python

This hint shows the minimal, practical steps to call Tavily from Python: install the SDK, set your API key, and use the main methods (search, extract, crawl, map). Code snippets are concise on purpose.

## 1) Install

- pip:

```bash
pip install tavily-python
```

- In this repo with pixi:

```bash
pixi add tavily-python
```

## 2) Set API key

Export your key (replace the value with your own, starting with tvly-):

```bash
export TAVILY_API_KEY="tvly-xxxxxxxxxxxxxxxxxxxxxxxx"
```

## 3) Create a client

```python
import os
from tavily import TavilyClient

client = TavilyClient(os.getenv("TAVILY_API_KEY"))  # or TavilyClient("tvly-...")
```

## 4) Search (general)

```python
resp = client.search(
    "Euro 2024 host nation",
    search_depth="basic",      # "basic" | "advanced"
    max_results=5,
    include_domains=["wikipedia.org"],  # optional
    include_raw_content=False,  # set True if you want raw HTML
    include_images=False,
    topic="general",           # "general" | "news"
)

for i, r in enumerate(resp["results"], 1):
    print(f"{i}. {r['title']} -> {r['url']}")
```

### News search (time-bounded)

```python
resp_news = client.search(
    "AI regulation updates",
    topic="news",
    days=1,                 # only works when topic="news"
    search_depth="basic",
    max_results=10,
)
print(len(resp_news["results"]))
```

## 5) Extract page content

Use after search when you need full article text.

```python
urls = [r["url"] for r in resp["results"][:3]]
extraction = client.extract(urls)
for item in extraction["results"]:
    print(item["url"]) 
    print(item["content"][:400], "...\n")
```

## 6) Crawl a site

Discover internal pages from a root URL with simple constraints.

```python
crawl = client.crawl(
    "https://docs.tavily.com",
    instructions="Find pages on the Python SDK and quickstart",
    limit=30,        # total pages
    max_depth=2,     # link levels deep
    max_breadth=10,  # links per level
    # select_domains=["^docs\\.tavily\\.com$"],
    # select_paths=["/sdk/python/.*"],
)
print(len(crawl["results"]))
```

## 7) Map a site

Get a structured list/graph of URLs starting from a root.

```python
site_map = client.map(
    "https://docs.tavily.com",
    limit=20,
    max_depth=1,
)
for node in site_map["results"]:
    print(node["url"])
```

## Quick reference: common params

- search_depth: "basic" | "advanced" (depth of search)
- max_results: typical range 5–20
- topic: "general" or "news"
- days: only when topic="news" (bound by recent days)
- include_domains / exclude_domains: optional filters
- include_raw_content / include_images: payload controls

## Error handling tips

- Wrap calls with try/except to handle network/429 errors and retry with backoff.
- Keep include_raw_content=False unless you need HTML to reduce payload.

## Sources

- Quickstart (Python): https://docs.tavily.com/sdk/python/quick-start
- SDK Reference (Python): https://docs.tavily.com/sdk/python/reference
- API Reference: https://docs.tavily.com/documentation/api-reference/introduction
- PyPI: https://pypi.org/project/tavily-python/
- GitHub: https://github.com/tavily-ai/tavily-python
