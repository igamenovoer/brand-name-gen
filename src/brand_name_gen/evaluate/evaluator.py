"""
UniquenessEvaluator orchestrates providers, matching, scoring, and aggregation.

Follows the project's service-class guide: no-arg constructor, m_-prefixed
members, factory methods, strong typing, and NumPy-style docstrings.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from .matcher import BuiltinMatcher, Matcher, RapidFuzzMatcher
from .providers import AppFollowProvider, DomainProvider, PlayProvider, SerpProvider
from .scoring import score_appfollow, score_domain, score_google, score_play
from .types import (
    ComponentScore,
    LocaleReport,
    LocaleSpec,
    UniquenessConfig,
    UniquenessReport,
)


class UniquenessEvaluator:
    """
    Stateful evaluator for brand name uniqueness.

    Attributes
    ----------
    m_matcher : Matcher or None
        Matching engine (RapidFuzz or Builtin)
    m_config : UniquenessConfig or None
        Scoring and matching configuration
    """

    def __init__(self) -> None:
        self.m_matcher: Optional[Matcher] = None
        self.m_config: Optional[UniquenessConfig] = None
        self._af = AppFollowProvider()
        self._ps = PlayProvider()
        self._serp = SerpProvider()
        self._dom = DomainProvider()

    @property
    def config(self) -> Optional[UniquenessConfig]:
        return self.m_config

    def set_config(self, config: UniquenessConfig) -> None:
        self.m_config = config

    def set_matcher(self, matcher: Matcher) -> None:
        self.m_matcher = matcher

    @classmethod
    def from_defaults(cls) -> "UniquenessEvaluator":
        inst = cls()
        cfg = UniquenessConfig()
        inst.m_config = cfg
        inst.m_matcher = _resolve_matcher(cfg.matcher_engine)
        return inst

    @classmethod
    def from_matcher(cls, matcher: Matcher, *, config: UniquenessConfig) -> "UniquenessEvaluator":
        inst = cls()
        inst.m_matcher = matcher
        inst.m_config = config
        return inst

    def evaluate(self, title: str, locales: List[LocaleSpec] | None = None) -> UniquenessReport:
        if not self.m_config:
            self.m_config = UniquenessConfig()
        if not self.m_matcher:
            self.m_matcher = _resolve_matcher(self.m_config.matcher_engine)
        matcher = self.m_matcher
        cfg = self.m_config
        locs = locales or [LocaleSpec()]

        per_locale: List[LocaleReport] = []
        for loc in locs:
            dom = self._dom.check(title)
            af = self._af.fetch(title, country=loc.country)
            ps = self._ps.fetch(title, hl=loc.hl, gl=loc.gl)
            serp = self._serp.fetch(title, location_code=loc.location_code, language_code=loc.language_code)

            af_titles = [(s.term, s.pos) for s in af.suggestions]
            ps_titles = [(s.term, s.pos) for s in ps.suggestions]
            serp_titles = [(m.title, m.rank_absolute) for m in serp.matches]

            # Stats can be reused for features; per-component penalties use band_counts with positions
            af_stats = matcher.stats(title, [t for t, _ in af_titles])
            ps_stats = matcher.stats(title, [t for t, _ in ps_titles])
            serp_stats = matcher.stats(title, [t for t, _ in serp_titles])

            sc_domain = score_domain(dom, cfg)
            sc_af = score_appfollow(af_stats, af_titles, title, matcher, cfg)
            sc_ps = score_play(ps_stats, ps_titles, title, matcher, cfg)
            sc_google = score_google(serp_stats, serp_titles, title, matcher, cfg)

            per_locale.append(
                LocaleReport(
                    locale=loc,
                    components={
                        "domain": sc_domain,
                        "appfollow": sc_af,
                        "play": sc_ps,
                        "google": sc_google,
                    },
                    features={
                        "af": af_stats.model_dump(),
                        "ps": ps_stats.model_dump(),
                        "serp": serp_stats.model_dump(),
                        "serp_check_url": getattr(serp, "check_url", None),
                    },
                )
            )

        combined = _aggregate_components(per_locale, cfg)
        total = int(sum(combined.values()))
        grade = _bin_grade(total, cfg.thresholds)
        explanations = _build_explanations(per_locale)
        return UniquenessReport(overall_score=total, grade=grade, components=combined, locales=per_locale, explanations=explanations)


def _resolve_matcher(engine: str) -> Matcher:
    if engine == "rapidfuzz":
        return RapidFuzzMatcher()
    if engine == "builtin":
        return BuiltinMatcher()
    # auto
    try:
        return RapidFuzzMatcher()
    except Exception:
        return BuiltinMatcher()


def _aggregate_components(per_locale: List[LocaleReport], cfg: UniquenessConfig) -> Dict[str, int]:
    # Conservative: per-component minimum across locales
    names = list(cfg.weights.keys())
    combined: Dict[str, int] = {}
    for name in names:
        vals: List[int] = []
        for rep in per_locale:
            cs = rep.components.get(name)
            if cs is not None:
                vals.append(int(cs.score))
        combined[name] = min(vals) if vals else 0
    return combined


def _bin_grade(total: int, thr: Dict[str, int]) -> str:
    if total >= thr.get("distinct", 80):
        return "Distinct"
    if total >= thr.get("likely", 60):
        return "Likely Unique"
    if total >= thr.get("border", 40):
        return "Borderline"
    return "Colliding"


def _build_explanations(reports: List[LocaleReport]) -> List[str]:
    out: List[str] = []
    for rep in reports:
        check_url = rep.features.get("serp_check_url")
        if check_url:
            out.append(f"SERP verification URL ({rep.locale.language_code}-{rep.locale.location_code}): {check_url}")
    return out

