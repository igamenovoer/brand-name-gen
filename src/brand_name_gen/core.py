from __future__ import annotations

from typing import Iterable, List

__all__ = ["generate_names"]


_PREFIXES: tuple[str, ...] = (
    "neo",
    "meta",
    "quant",
    "hyper",
    "blue",
    "bright",
    "clear",
    "ever",
    "true",
)

_SUFFIXES: tuple[str, ...] = (
    "ly",
    "ify",
    "io",
    "ster",
    "scape",
    "verse",
    "labs",
    "works",
    "forge",
)

_STYLE_INFIX: dict[str, str] = {
    "modern": "x",
    "classic": "a",
    "playful": "oo",
    "professional": "pro",
}


def _slugify(word: str) -> str:
    return "".join(ch for ch in word.lower() if ch.isalnum())


def generate_names(
    keywords: Iterable[str],
    *,
    style: str | None = None,
    limit: int = 20,
) -> List[str]:
    """Generate a list of brand name ideas.

    Parameters
    - keywords: iterable of seed words (e.g., ["solar", "green"]).
    - style: optional style hint among {modern, classic, playful, professional}.
    - limit: maximum number of names to return.

    Returns a list of unique, title-cased brand name candidates.
    """
    seeds = [_slugify(k) for k in keywords if k and _slugify(k)]
    if not seeds:
        return []

    infix = _STYLE_INFIX.get(style or "", "")

    results: list[str] = []
    seen: set[str] = set()

    # Combine prefixes, seeds, infix, and suffixes
    for pref in _PREFIXES:
        for seed in seeds:
            base = f"{pref}{infix}{seed}" if infix else f"{pref}{seed}"
            for suf in _SUFFIXES:
                name = f"{base}{suf}"
                title = name.title()
                if title not in seen:
                    results.append(title)
                    seen.add(title)
                    if len(results) >= limit:
                        return results

    # Fallback simple combinations if limit not reached
    for seed in seeds:
        for suf in _SUFFIXES:
            title = f"{seed}{suf}".title()
            if title not in seen:
                results.append(title)
                seen.add(title)
                if len(results) >= limit:
                    return results

    return results

