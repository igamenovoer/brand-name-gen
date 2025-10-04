"""
Matching engines for brand name similarity.

Provides a dual-mode strategy:
- RapidFuzzMatcher (preferred if available)
- BuiltinMatcher (SequenceMatcher + heuristics)
"""

from __future__ import annotations

import re
from difflib import SequenceMatcher
from typing import List, Sequence

from .types import MatchStats


class Matcher:
    """Interface for matching engines."""

    def score_pair(self, a: str, b: str) -> int:  # pragma: no cover - interface
        raise NotImplementedError

    def stats(self, query: str, candidates: Sequence[str]) -> MatchStats:  # pragma: no cover - interface
        raise NotImplementedError


def _norm(s: str) -> str:
    t = s.lower()
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    return re.sub(r"\s+", " ", t)


def _compact(s: str) -> str:
    return _norm(s).replace(" ", "")


def _token_sort_key(s: str) -> str:
    toks = _norm(s).split()
    return " ".join(sorted(toks))


class BuiltinMatcher(Matcher):
    """Fallback matcher using SequenceMatcher and heuristics."""

    def score_pair(self, a: str, b: str) -> int:
        return int(100 * SequenceMatcher(None, _norm(a), _norm(b)).ratio())

    def stats(self, query: str, candidates: Sequence[str]) -> MatchStats:
        n80 = n90 = n95 = 0
        max_score = 0
        for c in candidates:
            sc = self.score_pair(query, c)
            # Heuristic boosts for compact substring or token-sort equality
            if sc < 90 and (_compact(query) in _compact(c) or _compact(c) in _compact(query)):
                sc = max(sc, 90)
            if sc < 90 and _token_sort_key(query) == _token_sort_key(c):
                sc = max(sc, 88)
            max_score = max(max_score, sc)
            if sc >= 95:
                n95 += 1
            if sc >= 90:
                n90 += 1
            if sc >= 80:
                n80 += 1
        return MatchStats(max_score=max_score, n_95=n95, n_90=n90, n_80=n80, top_hit_pos=None)


class RapidFuzzMatcher(Matcher):
    """Matcher backed by RapidFuzz if available."""

    def __init__(self) -> None:
        try:
            from rapidfuzz import fuzz, utils  # type: ignore
        except Exception as e:  # pragma: no cover - import path
            raise RuntimeError("rapidfuzz is not installed") from e
        self._fuzz = fuzz
        self._utils = utils

    def score_pair(self, a: str, b: str) -> int:
        return int(self._fuzz.WRatio(a, b, processor=self._utils.default_process))

    def stats(self, query: str, candidates: Sequence[str]) -> MatchStats:
        n80 = n90 = n95 = 0
        max_score = 0
        for c in candidates:
            sc = int(self._fuzz.WRatio(query, c, processor=self._utils.default_process))
            max_score = max(max_score, sc)
            if sc >= 95:
                n95 += 1
            if sc >= 90:
                n90 += 1
            if sc >= 80:
                n80 += 1
        return MatchStats(max_score=max_score, n_95=n95, n_90=n90, n_80=n80, top_hit_pos=None)

