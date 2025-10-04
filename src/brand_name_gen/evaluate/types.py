"""
Types for brand name uniqueness evaluation.

Defines the configuration, locale specification, intermediate match
statistics, per-component scores, per-locale report, and the final
UniquenessReport returned by the evaluator.
"""

from __future__ import annotations

from typing import Dict, List, Literal, Optional

from pydantic import BaseModel


class LocaleSpec(BaseModel):
    """Locale parameters for providers.

    Parameters
    ----------
    country : str
        AppFollow country code (lowercase), e.g., 'us'
    hl : str
        Play locale code, e.g., 'en'
    gl : str
        Play country code, e.g., 'US'
    location_code : int
        DataForSEO location_code
    language_code : str
        DataForSEO language_code
    weight : float
        Locale importance weight used in aggregation when configured
    """

    country: str = "us"
    hl: str = "en"
    gl: str = "US"
    location_code: int = 2840
    language_code: str = "en"
    weight: float = 1.0


class UniquenessConfig(BaseModel):
    """Configuration for the evaluator.

    Parameters
    ----------
    matcher_engine : {'auto','rapidfuzz','builtin'}
        Select matching engine
    weights : dict
        Component weights that sum roughly to 100 (domain, appfollow, play, google)
    thresholds : dict
        Grade bin thresholds: distinct, likely, border
    """

    matcher_engine: Literal["auto", "rapidfuzz", "builtin"] = "auto"
    weights: Dict[str, int] = {"domain": 25, "appfollow": 25, "play": 20, "google": 30}
    thresholds: Dict[str, int] = {"distinct": 80, "likely": 60, "border": 40}


class MatchStats(BaseModel):
    """Aggregate stats for matches of a query against a list of candidates."""

    max_score: int
    n_95: int
    n_90: int
    n_80: int
    top_hit_pos: Optional[int] = None


class ComponentScore(BaseModel):
    """Score for a single component (domain/appfollow/play/google)."""

    name: str
    score: int
    details: Dict[str, object] = {}


class LocaleReport(BaseModel):
    """Per-locale component results and features."""

    locale: LocaleSpec
    components: Dict[str, ComponentScore]
    features: Dict[str, object]


class UniquenessReport(BaseModel):
    """Final report with total score, grade, and per-locale breakdown."""

    overall_score: int
    grade: Literal["Distinct", "Likely Unique", "Borderline", "Colliding"]
    components: Dict[str, int]
    locales: List[LocaleReport]
    explanations: List[str] = []

