# API Reference

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

## brand_name_gen.android.title_check

### Models
- Suggestion
  - Fields: `pos: int | None`, `term: str`
- TitleCheckResult
  - Fields: `provider: Literal['appfollow','playstore']`, `title: str`, `country: str | None`, `hl: str | None`, `gl: str | None`, `threshold: float`, `suggestions: list[Suggestion]`, `collisions: list[Suggestion]`, `unique_enough: bool`, `meta: dict`

### Functions
```
normalize_title(s: str) -> str
is_similar(a: str, b: str, *, threshold: float = 0.9) -> bool

check_title_appfollow(
  title: str,
  *, country: str = 'us', threshold: float = 0.9,
  api_key: str | None = None, timeout_s: float = 30.0
) -> TitleCheckResult

check_title_playstore(
  title: str,
  *, hl: str = 'en', gl: str = 'US', threshold: float = 0.9,
  timeout_s: float = 30.0, user_agent: str | None = None
) -> TitleCheckResult

check_title(
  title: str,
  *, providers: list[Provider] | None = None,
  country: str = 'us', hl: str = 'en', gl: str = 'US',
  threshold: float = 0.9, api_key: str | None = None,
  timeout_s: float = 30.0
) -> list[TitleCheckResult]
```

Example
```python
from brand_name_gen.android.title_check import check_title_appfollow, check_title_playstore

af = check_title_appfollow("BrandName", country="us")
ps = check_title_playstore("BrandName", hl="en", gl="US")
print(af.unique_enough, ps.unique_enough)
```

---

## brand_name_gen.android.title_checker

### AppTitleChecker
Stateful service wrapper.

```
from brand_name_gen.android.title_checker import AppTitleChecker

checker = AppTitleChecker.from_defaults()
checker.set_appfollow_api_key("<token>")
af = checker.check_appfollow("BrandName", country="us")
ps = checker.check_playstore("BrandName", hl="en", gl="US")
```

---

## brand_name_gen.domain.domain_check

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
from brand_name_gen.domain.domain_check import is_com_available

res = is_com_available("brand-name")
print(res.available)
```

---

## brand_name_gen.domain.domain_checker

### DomainChecker
Stateful service with factory methods:
- `from_defaults()`
- `from_session(session, *, timeout_s=5.0, rdap_base=None)`

Method:
- `check_com(brand: str) -> DomainAvailability`

Example
```python
from brand_name_gen.domain.domain_checker import DomainChecker

checker = DomainChecker.from_defaults()
result = checker.check_com("brand-name")
```

---

## brand_name_gen.search.dataforseo

### Types
```
from brand_name_gen.search.dataforseo.types import (
  GoogleRankQuery, GoogleRankResult, OrganicItem,
  DataForSEOError, CredentialsMissingError, UnauthorizedError, ForbiddenError, ApiResponseError,
)
```

- GoogleRankQuery
  - Fields: `keyword: str`, `se_domain: str = 'google.com'`, `location_code: int = 2840`, `language_code: str = 'en'`, `device: str = 'desktop'`, `os: str = 'macos'`, `depth: int = 50`, `similarity_threshold: float = 0.9`
- GoogleRankResult
  - Fields: `query: GoogleRankQuery`, `top_position: int | None`, `matches: list[OrganicItem]`, `total_matches: int`, `check_url: str | None`

### Service
```
from brand_name_gen.search.dataforseo.google_rank import DataForSEORanker

ranker = DataForSEORanker.from_env()  # .env takes precedence over os.environ
res = ranker.run(GoogleRankQuery(keyword="hb-app"))
print(res.top_position, [m.title for m in res.matches[:3]])
```

Errors
- `CredentialsMissingError` when creds are not found
- `UnauthorizedError` for 401
- `ForbiddenError` for 403

Notes
- Credentials: `DATAFORSEO_LOGIN`, `DATAFORSEO_PASSWORD` (prefer `.env` in CWD)
- Consumes DataForSEO credits

---

## brand_name_gen.utils.env

```
from brand_name_gen.utils.env import load_env_from_dotenv, read_dotenv_value

load_env_from_dotenv()               # loads KEY=VALUE from .env into os.environ (no override)
token = read_dotenv_value("MY_KEY")  # read .env value without mutating env
```
