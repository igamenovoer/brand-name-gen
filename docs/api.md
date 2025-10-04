# API Reference

## HEADER
- **Purpose**: Document the public Python API
- **Status**: Active
- **Date**: 2025-10-04
- **Dependencies**: None
- **Target**: Developers

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

