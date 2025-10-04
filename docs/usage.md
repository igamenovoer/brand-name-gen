# Usage

## HEADER
- **Purpose**: Provide installation and usage instructions for CLI and Python API
- **Status**: Active
- **Date**: 2025-10-04
- **Dependencies**: None
- **Target**: End users

## Installation
```bash
pip install brand-name-gen
```

## Command Line
```bash
brand-name-gen eco solar --style modern --limit 5
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
