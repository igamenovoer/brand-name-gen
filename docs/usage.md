# Usage

## Installation
```bash
pip install brand-name-gen
```

## Command Line
```bash
# Generate names
brand-name-gen-cli generate eco solar --style modern --limit 5

# Check .com availability (and probe www)
brand-name-gen-cli check-www brand-name --json

# Android title checks (ASO)
# 1) AppFollow ASO suggestions (requires APPFOLLOW_API_KEY; .env auto-loaded)
brand-name-gen-cli check-android appfollow "Your Brand" --country us --json

# 2) Google Play web search (heuristic)
brand-name-gen-cli check-android playstore "Your Brand" --hl en --gl US --json

# Search engine ranking (DataForSEO)
# Requires DATAFORSEO_LOGIN and DATAFORSEO_PASSWORD (prefer .env in CWD)
brand-name-gen-cli check-search-engine dataforseo "Your Brand" \
  --se-domain google.com --location-code 2840 --language-code en \
  --device desktop --os macos --depth 50 --json
```

Output:
```
NeoxEcoLy
MetaEcoLy
QuantEcoLy
...
```

Options:
- `--style`: modern | classic | playful | professional
- `--limit`: maximum number of names to output (default 20)

## Python API
```python
from brand_name_gen import generate_names

names = generate_names(["eco", "solar"], style="modern", limit=5)
print(names)
```

### Check .com Domain Availability
```python
from brand_name_gen.domain.domain_check import is_com_available

res = is_com_available("brand-name")
print(res.domain, res.available)  # brand-name.com True/False/None
```

### .env for AppFollow (auto-loaded)
Create a `.env` in your project root with:
```
APPFOLLOW_API_KEY=your_appfollow_api_token
```
The CLI automatically loads `.env` on start (does not override existing environment variables).

### .env for DataForSEO (precedence for CLI command)
Create a `.env` in your project root with:
```
DATAFORSEO_LOGIN=your_login
DATAFORSEO_PASSWORD=your_password
```
The `check-search-engine dataforseo` command prefers `.env` values over OS environment
variables and will fall back to `os.environ` only if keys are absent in `.env`.

### Python API: DataForSEO SDK
```python
from brand_name_gen.search.dataforseo.types import GoogleRankQuery
from brand_name_gen.search.dataforseo.google_rank import DataForSEORanker

ranker = DataForSEORanker.from_env()
result = ranker.run(GoogleRankQuery(keyword="hb-app"))
print(result.top_position, len(result.matches))
```

### Module Map (refactor)
- `brand_name_gen/android/*`: Android title checks (AppFollow/Play)
- `brand_name_gen/domain/*`: Domain availability (.com via RDAP)
- `brand_name_gen/search/dataforseo/*`: Google ranking SDK (DataForSEO)
- `brand_name_gen/utils/*`: Shared utilities (e.g., .env helpers)

### Android Title Checks via Python API
```python
from brand_name_gen.android.title_check import check_title_appfollow, check_title_playstore

# AppFollow (requires APPFOLLOW_API_KEY in env)
af = check_title_appfollow("Your Brand", country="us")
print(af.unique_enough, [c.term for c in af.collisions])

# Play Store web search (heuristic)
ps = check_title_playstore("Your Brand", hl="en", gl="US")
print(ps.unique_enough, [c.term for c in ps.collisions])
```

## Configuration (YAML)
- The evaluator supports YAML configuration (processed with ruamel.yaml) to control matcher engine, component weights, and grade thresholds.
- Precedence:
  1) `brand-name-gen-config.yaml` in the current working directory
  2) `BRAND_NAME_GEN_CONFIG` environment variable (path to YAML)
  3) Built-in defaults (see `src/brand_name_gen/evaluate/defaults.py`)

Example YAML (`examples/brand-name-gen-config.yaml`):
```
# Which matcher to use: auto | rapidfuzz | builtin
matcher_engine: auto

# Component weights (should sum roughly to ~100)
weights:
  domain: 25
  appfollow: 25
  play: 20
  google: 30

# Grade thresholds for the final score
thresholds:
  distinct: 80
  likely: 60
  border: 40
```

To point to a custom path:
```
export BRAND_NAME_GEN_CONFIG=/path/to/brand-name-gen-config.yaml
```

The CLI `evaluate uniqueness` command automatically loads this config. You can still override the matcher via `--matcher`.

## Uniqueness Evaluation (CLI)
Run the evaluator (aggregates Domain/AppFollow/Play/Google) with optional matcher override:
```
brand-name-gen-cli evaluate uniqueness "Your Brand" --matcher auto
```

If any provider call fails (network/auth), the evaluator prints a warning and assigns a neutral component score (50% of that component's weight) to keep the evaluation running.

### Demo Tasks (with progress)
We provide demo tasks that print step-by-step progress using Rich:
```
pixi run -e dev demo-check-unique-simple "Your Brand"   # builtin matcher
pixi run -e dev demo-check-unique-advanced "Your Brand" # rapidfuzz matcher
```
Add `-- --json` to see JSON output from each step.
