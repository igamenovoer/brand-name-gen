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

from pathlib import Path
from pprint import pprint

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.rule import Rule

from brand_name_gen.evaluate.config import load_uniqueness_config
from brand_name_gen.evaluate.evaluator import UniquenessEvaluator
from brand_name_gen.evaluate.matcher import BuiltinMatcher, RapidFuzzMatcher
from brand_name_gen.evaluate.types import LocaleSpec
from brand_name_gen.utils.env import load_env_from_dotenv


def print_report(report) -> None:
    """Pretty-print a UniquenessReport summary."""
    console = Console()
    table = Table(title="Uniqueness Summary", show_header=True, header_style="bold magenta")
    table.add_column("Metric", style="dim", width=20)
    table.add_column("Value")
    table.add_row("overall_score", str(report.overall_score))
    table.add_row("grade", report.grade)
    comp_table = Table(show_header=True, header_style="bold cyan")
    comp_table.add_column("Component")
    comp_table.add_column("Score", justify="right")
    for name, score in report.components.items():
        comp_table.add_row(name, str(score))
    console.print(table)
    console.print(comp_table)
    if report.explanations:
        console.print(Rule("Explanations"))
        for line in report.explanations:
            console.print(f"- {line}")


# 1) Choose a title to evaluate
console = Console()
console.print(Panel.fit("[bold]Uniqueness Evaluation Demo[/bold]", title="brand-name-gen"))

title = "Your Brand"
console.print(f"[bold]Title:[/bold] [green]{title}[/green]")

# 2) Locale (AppFollow/Play/DataForSEO parameters)
loc = LocaleSpec(country="us", hl="en", gl="US", location_code=2840, language_code="en")
console.print(f"[bold]Locale:[/bold] country={loc.country} hl={loc.hl} gl={loc.gl} location_code={loc.location_code} language_code={loc.language_code}")

# 3) Load env from .env (so AppFollow/DataForSEO creds are available)
console.print(Rule("Step 1/5: Load .env"))
env_found = Path(".env").is_file()
load_env_from_dotenv()
console.print("[green]✓[/green] .env loaded" if env_found else "[yellow]⚠[/yellow] no .env found (using OS env if present)")

# 4) Load configuration (YAML precedence). Override matcher if desired.
console.print(Rule("Step 2/5: Load YAML config (with precedence)"))
cfg = load_uniqueness_config(overrides={"matcher_engine": "auto"})
console.print(f"[green]✓[/green] matcher_engine=[cyan]{cfg.matcher_engine}[/cyan]")
console.print(f"weights={cfg.weights}")
console.print(f"thresholds={cfg.thresholds}")

# 5) Build evaluator and ensure matcher aligns with config
console.print(Rule("Step 3/5: Initialize evaluator and matcher"))
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
console.print("[green]✓[/green] Evaluator ready")

# 6) Evaluate and inspect the report
console.print(Rule("Step 4/5: Evaluate"))
report = evaluator.evaluate(title, [loc])
console.print("[green]✓[/green] Evaluation complete")

console.print(Rule("Step 5/5: Report"))
print_report(report)
