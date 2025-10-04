# Call LLM via LiteLLM (Custom Base URL)

## HEADER
- **Purpose**: Use LiteLLM Python SDK to call an LLM behind a custom (OpenAI‑compatible) base URL to generate creative brand names.
- **Status**: Active
- **Date**: 2025-10-04
- **Dependencies**: Python 3.11+, `litellm` package, reachable LLM endpoint
- **Target**: Developers & AI assistants

## TL;DR
- Install: `pip install litellm`
- Call with custom base (one-off): pass `api_base=...` to `litellm.completion`.
- Or set env/global base: `OPENAI_BASE_URL=...` or `litellm.api_base = ...`.

## Steps
- Install dependency
  - PyPI: `pip install litellm`
  - Pixi (dev): add to `pyproject.toml` `[tool.pixi.pypi-dependencies]` then `pixi install`
- Configure endpoint (choose one)
  - Per-call: `completion(..., api_base="https://llm.example.com/v1", api_key="<key>")`
  - Global (OpenAI‑compatible): `export OPENAI_BASE_URL=https://llm.example.com/v1`
  - Global (LiteLLM): `import litellm; litellm.api_base = "https://llm.example.com/v1"`
- Minimal code (project‑ready)
  - Create `src/brand_name_gen/llm_client.py` (example):
    ```python
    from litellm import completion

    def suggest_names(keywords: list[str], *, style: str|None=None, base_url: str="", api_key: str|None=None):
        prompt = f"Generate 10 creative, short brand names. Keywords: {', '.join(keywords)}. Style: {style or 'any'}. Output one per line."
        resp = completion(
            model="openai/gpt-4o-mini",  # adjust to your provider/model
            messages=[{"role": "user", "content": prompt}],
            api_base=base_url or None,
            api_key=api_key,
            max_tokens=300,
            temperature=0.9,
        )
        return [l.strip() for l in resp.choices[0].message["content"].splitlines() if l.strip()]
    ```
- CLI wiring (optional)
  - Read `LLM_BASE_URL`/`LLM_API_KEY` envs in `cli.py`; call `suggest_names(.., base_url=os.getenv("LLM_BASE_URL",""), api_key=os.getenv("LLM_API_KEY"))`.

## Gotchas
- Include scheme in base URL: use `https://` or `http://` (missing protocol causes errors).
- Model naming: LiteLLM infers provider from prefix (e.g., `openai/…`, `anthropic/…`). For OpenAI‑compatible servers, `openai/<model>` usually works; otherwise route via a LiteLLM Proxy alias.
- Auth: pass `api_key=` or use provider‑specific env vars.

## References (official)
- Pass custom base per call (api_base): https://docs.litellm.ai/docs/set_keys
- Set global base via `litellm.api_base`: https://docs.litellm.ai/docs/set_keys
- OpenAI‑compatible env (`OPENAI_BASE_URL`): https://docs.litellm.ai/docs/set_keys
- Using LiteLLM Proxy with SDK / OpenAI SDK: https://docs.litellm.ai/docs/providers/bedrock_embedding
- Example with custom endpoints: https://docs.litellm.ai/docs/providers/hyperbolic

