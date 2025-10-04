#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from typing import List
import json
import re

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn


def run(cmd: List[str]) -> int:
    return subprocess.call(cmd)


def main(argv: List[str]) -> int:
    ap = argparse.ArgumentParser(description="Demo: uniqueness check (builtin matcher)")
    ap.add_argument("title", help="Brand/App title")
    ap.add_argument("--json", dest="as_json", action="store_true", help="Print JSON outputs")
    args = ap.parse_args(argv)

    console = Console()
    console.print(Panel.fit(f"[bold]Uniqueness Demo[/bold]\nMatcher: [cyan]builtin[/cyan]\nTitle: [green]{args.title}[/green]", title="brand-name-gen"))

    j = ["--json"] if args.as_json else []

    steps = [
        ("Domain (.com via RDAP)", ["brand-name-gen-cli", "check-www", args.title] + j),
        ("AppFollow ASO suggests", ["brand-name-gen-cli", "check-android", "appfollow", args.title] + j),
        ("Google Play web search (heuristic)", ["brand-name-gen-cli", "check-android", "playstore", args.title] + j),
        ("Google SERP via DataForSEO", ["brand-name-gen-cli", "check-search-engine", "dataforseo", args.title] + j),
        ("Aggregate → Uniqueness score (builtin)", ["brand-name-gen-cli", "evaluate", "uniqueness", args.title, "--matcher", "builtin"] + j),
    ]

    with Progress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), console=console) as progress:
        final_score = None
        final_grade = None
        for i, (desc, cmd) in enumerate(steps):
            task = progress.add_task(desc, total=None)
            # For the last step, capture output to extract final score
            if i == len(steps) - 1:
                proc = subprocess.run(cmd, capture_output=True, text=True)
                stdout = proc.stdout
                if stdout:
                    # Echo original output to console for visibility
                    console.print(stdout.rstrip())
                    if args.as_json:
                        try:
                            obj = json.loads(stdout)
                            final_score = obj.get("overall_score")
                            final_grade = obj.get("grade")
                        except Exception:
                            pass
                    else:
                        m_score = re.search(r"overall_score:\s*(\d+)", stdout)
                        m_grade = re.search(r"grade:\s*(.+)", stdout)
                        if m_score:
                            final_score = m_score.group(1)
                        if m_grade:
                            final_grade = m_grade.group(1).strip()
                rc = proc.returncode
            else:
                rc = run(cmd)
            progress.remove_task(task)
            if rc != 0:
                console.print(f"[yellow]⚠ Step failed:[/yellow] {desc} — continuing (neutral in aggregation)")
            else:
                console.print(f"[green]✓[/green] {desc}")
    # Print a final one-line summary as the very last line
    if final_score is not None and final_grade is not None:
        print(f"Final score: {final_score} ({final_grade})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
