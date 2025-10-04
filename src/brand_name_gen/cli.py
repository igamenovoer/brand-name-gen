from __future__ import annotations

import argparse
import sys
from typing import List

from .core import generate_names


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="brand-name-gen",
        description="Generate unique, memorable brand name ideas from keywords.",
    )
    parser.add_argument("keywords", nargs="+", help="Seed keywords, e.g. eco solar clean")
    parser.add_argument(
        "--style",
        choices=["modern", "classic", "playful", "professional"],
        help="Optional naming style",
    )
    parser.add_argument("--limit", type=int, default=20, help="Max results to output")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    ns = parse_args(argv)
    names: List[str] = generate_names(ns.keywords, style=ns.style, limit=ns.limit)
    for n in names:
        print(n)
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main(sys.argv[1:]))

