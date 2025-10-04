#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from typing import List

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn


def run(cmd: List[str]) -> int:
    return subprocess.call(cmd)


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Demo: uniqueness check (rapidfuzz matcher)")
    ap.add_argument("title", help="Brand/App title")
    ap.add_argument("--json", dest="as_json", action="store_true", help="Print JSON outputs")
    args = ap.parse_args(argv)

    console = Console()
    console.print(Panel.fit(f"[bold]Uniqueness Demo[/bold]\nMatcher: [cyan]rapidfuzz[/cyan]\nTitle: [green]{args.title}[/green]", title="brand-name-gen"))

    j = ["--json"] if args.as_json else []

    steps = [
        ("Domain (.com via RDAP)", ["brand-name-gen-cli", "check-www", args.title] + j),
        ("AppFollow ASO suggests", ["brand-name-gen-cli", "check-android", "appfollow", args.title] + j),
        ("Google Play web search (heuristic)", ["brand-name-gen-cli", "check-android", "playstore", args.title] + j),
        ("Google SERP via DataForSEO", ["brand-name-gen-cli", "check-search-engine", "dataforseo", args.title] + j),
        ("Aggregate → Uniqueness score (rapidfuzz)", ["brand-name-gen-cli", "evaluate", "uniqueness", args.title, "--matcher", "rapidfuzz"] + j),
    ]

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        for desc, cmd in steps:
            task = progress.add_task(desc, total=None)
            rc = run(cmd)
            progress.remove_task(task)
            if rc != 0:
                console.print(f"[red]Step failed:[/red] {desc}")
                return rc
            console.print(f"[green]✓[/green] {desc}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
