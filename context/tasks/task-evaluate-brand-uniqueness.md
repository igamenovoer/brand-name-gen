## HEADER
- Title: Brand Name Uniqueness Evaluation (OOD + Dual-Mode Matching)
- Purpose: Object-oriented design and algorithm to produce an explainable 0–100 “uniqueness” score for a candidate brand/app title across app stores (AppFollow/Play), Google SERP (DataForSEO), and .com domain (RDAP)
- Status: Proposal → Implement
- Date: 2025-10-04
- Owner: core
- Dependencies: pydantic, requests; brand_name_gen.android.title_check; brand_name_gen.search.dataforseo.google_rank; brand_name_gen.domain.domain_check; optional rapidfuzz

# Design Overview
We use a layered OOD architecture with a pluggable matching engine. The pipeline is fetch → extract → match → score → aggregate → report.

- Providers (fetch raw signals)
  - AppFollowProvider → wraps `check_title_appfollow`
  - PlayProvider → wraps `check_title_playstore`
  - SerpProvider → wraps `DataForSEORanker.run`
  - DomainProvider → wraps `is_com_available` (and optional `check_www_resolves`)
- Matcher Engine (Dual-Mode)
  - `Matcher` interface with `score_pair(a,b) -> int (0..100)` and `stats(query, candidates) -> MatchStats`
  - `RapidFuzzMatcher` (preferred, fast and robust) and `BuiltinMatcher` (fallback based on SequenceMatcher + heuristics)
- Scorers
  - DomainScorer, AppFollowScorer, PlayScorer, GoogleScorer compute component scores from `MatchStats` and provider metadata
- Aggregation
  - LocalesAggregator (min or weighted average per component) and GradeBinner (Distinct/Likely/Borderline/Colliding)
- Orchestrator
  - `UniquenessEvaluator` coordinates end-to-end evaluation and returns `UniquenessReport`

# API Design (Python)
```
# src/brand_name_gen/evaluate/types.py
from typing import Literal, Optional, List, Dict
from pydantic import BaseModel

class LocaleSpec(BaseModel):
    country: str = "us"      # AppFollow
    hl: str = "en"           # Play
    gl: str = "US"           # Play
    location_code: int = 2840  # DataForSEO
    language_code: str = "en"  # DataForSEO
    weight: float = 1.0

class UniquenessConfig(BaseModel):
    matcher_engine: Literal['auto','rapidfuzz','builtin'] = 'auto'
    weights: Dict[str, int] = {"domain": 25, "appfollow": 25, "play": 20, "google": 30}
    thresholds: Dict[str, int] = {"distinct": 80, "likely": 60, "border": 40}
    # Optional fine-grained penalties can be added here.

class MatchStats(BaseModel):
    max_score: int
    n_95: int
    n_90: int
    n_80: int
    top_hit_pos: Optional[int] = None  # min position among matched candidates

class ComponentScore(BaseModel):
    name: str
    score: int
    details: Dict[str, object] = {}

class LocaleReport(BaseModel):
    locale: LocaleSpec
    components: Dict[str, ComponentScore]
    features: Dict[str, object]

class UniquenessReport(BaseModel):
    overall_score: int
    grade: Literal['Distinct','Likely Unique','Borderline','Colliding']
    components: Dict[str, int]
    locales: List[LocaleReport]
    explanations: List[str] = []
```

```
# src/brand_name_gen/evaluate/matcher.py
from typing import Sequence
from .types import MatchStats

class Matcher:
    def score_pair(self, a: str, b: str) -> int: ...  # 0..100
    def stats(self, query: str, candidates: Sequence[str]) -> MatchStats: ...

class RapidFuzzMatcher(Matcher): ...
class BuiltinMatcher(Matcher): ...
```

```
# src/brand_name_gen/evaluate/evaluator.py
from .types import UniquenessConfig, LocaleSpec, UniquenessReport
from .matcher import Matcher
from typing import Optional

class UniquenessEvaluator:
    """Stateful evaluator following project coding guide (service class).

    - No-arg constructor; configure via factory methods
    - Member variables prefixed with `m_`
    - Strongly typed methods; NumPy-style docstrings
    """

    def __init__(self) -> None:
        self.m_matcher: Optional[Matcher] = None
        self.m_config: Optional[UniquenessConfig] = None

    @classmethod
    def from_defaults(cls) -> "UniquenessEvaluator": ...  # resolve matcher from config 'auto'

    @classmethod
    def from_matcher(cls, matcher: Matcher, *, config: UniquenessConfig) -> "UniquenessEvaluator": ...

    @property
    def config(self) -> Optional[UniquenessConfig]: ...  # read-only accessor

    def set_config(self, config: UniquenessConfig) -> None: ...
    def set_matcher(self, matcher: Matcher) -> None: ...

    def evaluate(self, title: str, locales: list[LocaleSpec] | None = None) -> UniquenessReport: ...
```

# Coding Guide Alignment
- Service classes (evaluator, providers, scorers, matchers):
  - No-arg constructors; configure via `from_*` factories and `set_*` methods
  - Member state uses `m_` prefix (e.g., `m_matcher`, `m_config`)
  - Provide read-only `@property` accessors where appropriate
- Data models (`pydantic`):
  - No `m_` prefixes; typed fields for API I/O
- Documentation:
  - Use NumPy-style docstrings at module/class/method levels
- Typing & quality:
  - Strong typing throughout; mypy-friendly; ruff-clean

# Dual-Mode Matching Strategy
- Config option: `UniquenessConfig.matcher_engine = 'auto'|'rapidfuzz'|'builtin'`
  - auto: use RapidFuzz if available, else Builtin
  - rapidfuzz: require RapidFuzz (error if missing)
  - builtin: force fallback (no RapidFuzz)

- RapidFuzzMatcher (examples)
  - WRatio / token_set_ratio / partial_ratio via `rapidfuzz.fuzz`
  - Bulk: `rapidfuzz.process.extract` / `process.cdist` to compute `n_80/n_90/n_95` and `max_score`

- BuiltinMatcher (heuristics)
  - SequenceMatcher ratio on normalized strings
  - Compact substring checks (remove spaces/hyphens)
  - Token-sort approximation (sorted token strings)

# Scoring Model (0–100)
Default weights: domain 25, appfollow 25, play 20, google 30
- Domain: +25 if `.com` available, else +15 baseline (tunable)
- AppFollow/Play: start full; subtract penalties by banded matches (≥95, 90–94, 80–89) and by top position (≤3 extra)
- Google: penalize by top matched position (≤3 heavy, 4–10 moderate, >10 mild) and by banded exact/near counts
- Locales: per-component minimum (conservative) or weighted average using `LocaleSpec.weight`
- Grade bins: ≥80 Distinct; 60–79 Likely; 40–59 Borderline; <40 Colliding

# Algorithm (Pseudocode)
```
# Orchestrator

def evaluate(title, locales, cfg):
    matcher = resolve_matcher(cfg.matcher_engine)
    locs = locales or [default_locale()]
    per_locale_reports = []

    for loc in locs:
        # Providers
        dom = domain_provider.check(title)
        af = appfollow_provider.fetch(title, country=loc.country)
        ps = play_provider.fetch(title, hl=loc.hl, gl=loc.gl)
        serp = serp_provider.fetch(title, loc.location_code, loc.language_code)

        # Candidates (text + position)
        af_titles = [(s.term, s.pos) for s in af.suggestions]
        ps_titles = [(s.term, s.pos) for s in ps.suggestions]
        serp_titles = [(m.title, m.rank_absolute) for m in serp.matches]

        # Match stats
        af_stats = matcher.stats(title, [t for t,_ in af_titles])
        ps_stats = matcher.stats(title, [t for t,_ in ps_titles])
        serp_stats = matcher.stats(title, [t for t,_ in serp_titles])

        # Component scores
        sc_domain = score_domain(dom, cfg)
        sc_af = score_appfollow(af_stats, af_titles, cfg)
        sc_ps = score_play(ps_stats, ps_titles, cfg)
        sc_google = score_google(serp_stats, serp_titles, cfg)

        per_locale_reports.append(LocaleReport(
            locale=loc,
            components={
                'domain': sc_domain,
                'appfollow': sc_af,
                'play': sc_ps,
                'google': sc_google,
            },
            features={
                'af': af_stats.model_dump(),
                'ps': ps_stats.model_dump(),
                'serp': serp_stats.model_dump(),
            },
        ))

    combined = aggregate_components(per_locale_reports, cfg)  # min or weighted average
    total = sum(combined.values())
    grade = bin_grade(total, cfg.thresholds)
    return UniquenessReport(
        overall_score=total,
        grade=grade,
        components=combined,
        locales=per_locale_reports,
        explanations=build_explanations(per_locale_reports),
    )
```

# CLI Sketch
```
brand-name-gen-cli evaluate uniqueness "Brand Name" \
  --country us --hl en --gl US \
  --location-code 2840 --language-code en \
  --matcher auto --json
```

# Testing
- Parametrize across `matcher_engine in {'builtin','rapidfuzz'}`
- Mock providers; assert grade equality and allow ±5 score delta across engines
- Unit tests for each scorer and aggregator

# Notes
- RapidFuzz is optional and preferred; Builtin requires no extra dependencies
- Keep normalization consistent; document default thresholds and allow overrides in `UniquenessConfig`
