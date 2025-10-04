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
from brand_name_gen.domain_check import is_com_available

res = is_com_available("brand-name")
print(res.domain, res.available)  # brand-name.com True/False/None
```

### .env for AppFollow (auto-loaded)
Create a `.env` in your project root with:
```
APPFOLLOW_API_KEY=your_appfollow_api_token
```
The CLI automatically loads `.env` on start (does not override existing environment variables).

### Android Title Checks via Python API
```python
from brand_name_gen.title_check import check_title_appfollow, check_title_playstore

# AppFollow (requires APPFOLLOW_API_KEY in env)
af = check_title_appfollow("Your Brand", country="us")
print(af.unique_enough, [c.term for c in af.collisions])

# Play Store web search (heuristic)
ps = check_title_playstore("Your Brand", hl="en", gl="US")
print(ps.unique_enough, [c.term for c in ps.collisions])
```
