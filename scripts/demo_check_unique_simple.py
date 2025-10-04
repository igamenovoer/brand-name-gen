#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys


def run(cmd: list[str]) -> int:
    print("$", " ".join(cmd))
    return subprocess.call(cmd)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="Demo: uniqueness check (builtin matcher)")
    ap.add_argument("title", help="Brand/App title")
    ap.add_argument("--json", dest="as_json", action="store_true", help="Print JSON outputs")
    args = ap.parse_args(argv)

    j = ["--json"] if args.as_json else []

    print("[1/5] Domain (.com via RDAP)")
    rc = run(["brand-name-gen-cli", "check-www", args.title] + j)
    if rc != 0:
        return rc

    print("[2/5] AppFollow ASO suggests")
    rc = run(["brand-name-gen-cli", "check-android", "appfollow", args.title] + j)
    if rc != 0:
        return rc

    print("[3/5] Google Play web search (heuristic)")
    rc = run(["brand-name-gen-cli", "check-android", "playstore", args.title] + j)
    if rc != 0:
        return rc

    print("[4/5] Google SERP via DataForSEO")
    rc = run(["brand-name-gen-cli", "check-search-engine", "dataforseo", args.title] + j)
    if rc != 0:
        return rc

    print("[5/5] Aggregate → Uniqueness score (builtin matcher)")
    rc = run(["brand-name-gen-cli", "evaluate", "uniqueness", args.title, "--matcher", "builtin"] + j)
    return rc


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))

