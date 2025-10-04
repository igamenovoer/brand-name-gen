"""
Evaluate the uniqueness of a brand/app title using the Python API.

This manual script demonstrates how to:
- Configure (via YAML or overrides) and run the UniquenessEvaluator
- Set a locale (AppFollow/Play/DataForSEO params)
- Inspect the resulting UniquenessReport

Notes
-----
- The evaluator aggregates Domain (.com via RDAP), AppFollow (ASO suggests),
  Play (heuristic labels), and Google SERP (DataForSEO) into a 0–100 score.
- If any online provider fails (network/auth), the evaluator assigns a
  neutral score (50% of that component's weight) and adds a warning.
- YAML precedence: brand-name-gen-config.yaml in CWD > env BRAND_NAME_GEN_CONFIG > defaults.
  See examples/brand-name-gen-config.yaml for a commented template.
- Environment variables (.env):
  - APPFOLLOW_API_KEY (for AppFollow)
  - DATAFORSEO_LOGIN / DATAFORSEO_PASSWORD (for SERP)
"""

from pprint import pprint

from brand_name_gen.evaluate.config import load_uniqueness_config
from brand_name_gen.evaluate.evaluator import UniquenessEvaluator
from brand_name_gen.evaluate.matcher import BuiltinMatcher, RapidFuzzMatcher
from brand_name_gen.evaluate.types import LocaleSpec
from brand_name_gen.utils.env import load_env_from_dotenv


def print_report(report) -> None:
    """Pretty-print a UniquenessReport summary."""

    print("overall_score:", report.overall_score)
    print("grade:", report.grade)
    print("components:")
    for name, score in report.components.items():
        print(f"  - {name}: {score}")
    if report.explanations:
        print("explanations:")
        for line in report.explanations:
            print("  -", line)


# 1) Choose a title to evaluate
title = "Your Brand"

# 2) Locale (AppFollow/Play/DataForSEO parameters)
loc = LocaleSpec(country="us", hl="en", gl="US", location_code=2840, language_code="en")

# 3) Load env from .env (so AppFollow/DataForSEO creds are available)
load_env_from_dotenv()

# 4) Load configuration (YAML precedence). Override matcher if desired.
cfg = load_uniqueness_config(overrides={"matcher_engine": "auto"})

# 5) Build evaluator and ensure matcher aligns with config
evaluator = UniquenessEvaluator.from_defaults()
evaluator.set_config(cfg)
if cfg.matcher_engine == "rapidfuzz":
    evaluator.set_matcher(RapidFuzzMatcher())
elif cfg.matcher_engine == "builtin":
    evaluator.set_matcher(BuiltinMatcher())
else:  # auto
    try:
        evaluator.set_matcher(RapidFuzzMatcher())
    except Exception:
        evaluator.set_matcher(BuiltinMatcher())

# 6) Evaluate and inspect the report
report = evaluator.evaluate(title, [loc])
print_report(report)
