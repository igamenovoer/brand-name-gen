"""
Component scoring helpers for uniqueness evaluation.

Each scorer takes provider outputs and/or MatchStats and computes
ComponentScore using weights and penalties from UniquenessConfig.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Sequence, Tuple

from .matcher import Matcher
from .types import ComponentScore, MatchStats, UniquenessConfig
from brand_name_gen.domain.domain_check import DomainAvailability


def _band_counts(matcher: Matcher, title: str, titled_pos: Sequence[Tuple[str, Optional[int]]]) -> Tuple[int, int, int, Optional[int]]:
    """Return counts in bands (>=95, >=90, >=80) and min top position among matches."""
    n95 = n90 = n80 = 0
    top_pos: Optional[int] = None
    for t, pos in titled_pos:
        sc = matcher.score_pair(title, t)
        if sc >= 80:
            if pos is not None:
                top_pos = pos if top_pos is None else min(top_pos, pos)
            n80 += 1
        if sc >= 90:
            n90 += 1
        if sc >= 95:
            n95 += 1
    return n95, n90, n80, top_pos


def score_domain(av: DomainAvailability, cfg: UniquenessConfig) -> ComponentScore:
    base = cfg.weights.get("domain", 25)
    score = base if av.available else max(0, base - 10)
    return ComponentScore(name="domain", score=score, details={"available": av.available, "rdap_status": av.rdap_status})


def score_appfollow(stats: MatchStats, titled_pos: Sequence[Tuple[str, Optional[int]]], title: str, matcher: Matcher, cfg: UniquenessConfig) -> ComponentScore:
    base = cfg.weights.get("appfollow", 25)
    n95, n90, n80, top_pos = _band_counts(matcher, title, titled_pos)
    # Penalties
    score = base
    score -= 8 * n95
    score -= 4 * (n90 - n95)
    score -= 2 * (n80 - n90)
    if top_pos is not None and top_pos <= 3:
        score -= 3
    return ComponentScore(name="appfollow", score=max(0, score), details={"n95": n95, "n90": n90, "n80": n80, "top_pos": top_pos})


def score_play(stats: MatchStats, titled_pos: Sequence[Tuple[str, Optional[int]]], title: str, matcher: Matcher, cfg: UniquenessConfig) -> ComponentScore:
    base = cfg.weights.get("play", 20)
    n95, n90, n80, top_pos = _band_counts(matcher, title, titled_pos)
    score = base
    score -= 6 * n95
    score -= 3 * (n90 - n95)
    score -= 1 * (n80 - n90)
    if top_pos is not None and top_pos <= 3:
        score -= 2
    return ComponentScore(name="play", score=max(0, score), details={"n95": n95, "n90": n90, "n80": n80, "top_pos": top_pos})


def score_google(stats: MatchStats, titled_pos: Sequence[Tuple[str, Optional[int]]], title: str, matcher: Matcher, cfg: UniquenessConfig) -> ComponentScore:
    base = cfg.weights.get("google", 30)
    n95, n90, n80, top_pos = _band_counts(matcher, title, titled_pos)
    score = base
    # Position penalties
    if top_pos is not None:
        if top_pos <= 3:
            score -= 20
        elif top_pos <= 10:
            score -= 10
        else:
            score -= 4
    # Band penalties (cap similar to plan)
    score -= min(10, 2 * n95)
    score -= min(5, 1 * (n90 - n95))
    score = max(0, score)
    return ComponentScore(name="google", score=score, details={"n95": n95, "n90": n90, "n80": n80, "top_pos": top_pos})

