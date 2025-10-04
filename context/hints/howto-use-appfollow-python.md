# How to use AppFollow in Python (get API token + minimal calls)

This hint shows how to get an AppFollow API token (v2), store it safely, and make minimal Python HTTP calls. Snippets are intentionally concise.

## 1) Get your API token (v2)

- Who can create: Account Owner or Admin
- Where: AppFollow → API Dashboard
  - Direct link (when signed in): https://watch.appfollow.io/settings/api
- Steps:
  - “Add new token” → name it → choose permissions (Read/Write/Delete; optionally scope by workspace if available)
  - Copy the token immediately (it’s fully visible only on creation)
  - Keep it secret; revoke/rotate as needed

Notes
- Multiple tokens with different roles/permissions are supported
- Requests made with your tokens consume credits and are billed to your account

Sources
- API Management in AppFollow: https://docs.api.appfollow.io/reference/api-management-in-appfollow
- Authorization (v2): https://docs.api.appfollow.io/reference/authorization
- Support: API Dashboard: https://support.appfollow.io/hc/en-us/articles/14098838663057-API-Dashboard

## 2) Store the token locally (macOS + zsh)

Temporary (current shell):

```zsh
export APPFOLLOW_API_TOKEN="<paste-your-token>"
```

Persistent (append to ~/.zshrc):

```zsh
echo 'export APPFOLLOW_API_TOKEN="<paste-your-token>"' >> ~/.zshrc
source ~/.zshrc
```

## 3) Install a tiny HTTP client

- pip:

```bash
pip install requests
```

- In this repo with pixi:

```bash
pixi add requests
```

## 4) Minimal Python example

Header: use X-AppFollow-API-Token. Base path for v2 examples: https://api.appfollow.io/api/v2

```python
import os
import requests

API_TOKEN = os.getenv("APPFOLLOW_API_TOKEN")
if not API_TOKEN:
    raise RuntimeError("Set APPFOLLOW_API_TOKEN env var with your AppFollow token")

BASE_URL = "https://api.appfollow.io/api/v2"
headers = {
    "X-AppFollow-API-Token": API_TOKEN,
    "Accept": "application/json",
}

# Example: fetch reviews for an app by external ID (ext_id = App Store ID or Google Play package ID)
params = {"ext_id": "606870241", "limit": 10}  # replace with your app id and desired params
resp = requests.get(f"{BASE_URL}/reviews", headers=headers, params=params, timeout=30)

if resp.status_code == 401:
    raise RuntimeError("Unauthorized: check token value/permissions and workspace access")
resp.raise_for_status()

data = resp.json()
print(data)
```

Other common endpoints (replace path/params per docs):

```python
# Ratings history
requests.get(f"{BASE_URL}/meta/ratings_history", headers=headers, params={"ext_id": "606870241"})

# Rankings
requests.get(f"{BASE_URL}/meta/rankings", headers=headers, params={"ext_id": "606870241", "country": "US"})

# ASO keyword research
requests.get(f"{BASE_URL}/aso/suggests", headers=headers, params={"term": "budget planner", "store": "appstore", "country": "US"})
```

## 5) Practical tips and error handling

- 401/403: token missing, invalid, or lacks permissions/workspace access
- 429: rate/credit limits—retry with backoff or reduce request volume
- Timeout: set a sensible timeout (e.g., 30s) and add retries for robustness
- Security: never commit tokens to VCS; prefer env vars or a secrets manager

## 6) Quick reference

- Auth header: `X-AppFollow-API-Token: <your_token>`
- Base (v2 examples): `https://api.appfollow.io/api/v2`
- Token management: only visible on creation; revoke to disable
- Multiple tokens: separate by service/team, narrow permissions where possible

## Sources

- Authorization (v2): https://docs.api.appfollow.io/reference/authorization
- API Management in AppFollow: https://docs.api.appfollow.io/reference/api-management-in-appfollow
- Support: API Dashboard: https://support.appfollow.io/hc/en-us/articles/14098838663057-API-Dashboard
