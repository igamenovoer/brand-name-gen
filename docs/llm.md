# LLM Integration (LiteLLM)

## Overview
Use LiteLLM to call an OpenAI-compatible LLM hosted at a custom base URL to generate creative brand names.

## Install
```bash
pip install litellm
```

## Minimal Client
```python
from litellm import completion

def suggest_names(keywords: list[str], *, style: str | None = None, base_url: str = "", api_key: str | None = None) -> list[str]:
    prompt = f"Generate 10 short, creative brand names. Keywords: {', '.join(keywords)}. Style: {style or 'any'}. Output one per line."
    resp = completion(
        model="openai/gpt-4o-mini",  # adjust to your provider
        messages=[{"role": "user", "content": prompt}],
        api_base=base_url or None,
        api_key=api_key,
        max_tokens=300,
        temperature=0.9,
    )
    text = resp.choices[0].message["content"]
    return [l.strip() for l in text.splitlines() if l.strip()]
```

## Environment Variables
- `LLM_BASE_URL` — custom endpoint like `https://llm.example.com/v1`
- `LLM_API_KEY` — API key/token for the provider

## CLI Wiring (planned)
Future flag: `--use-llm` to route generation via the LLM client, using `LLM_BASE_URL`/`LLM_API_KEY`.

## References
- LiteLLM keys and base URL: https://docs.litellm.ai/docs/set_keys
- OpenAI-compatible base URL env: https://docs.litellm.ai/docs/set_keys

