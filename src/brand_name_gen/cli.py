"""
Click-based CLI for Brand Name Gen.

Provides subcommands for generating names and checking `.com` availability.
"""

from __future__ import annotations

import json
import os
import re
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple

import click
import requests
import urllib.parse as up

from .core import generate_names
from .domain_check import DomainAvailability, check_www_resolves, is_com_available


def _load_env_from_dotenv() -> None:
    """Load simple KEY=VALUE pairs from .env in CWD if present.

    Does not override existing environment variables.
    Supports basic lines like KEY=value, ignoring blanks and lines starting with '#'.
    Strips surrounding single/double quotes from values.
    """
    path = os.path.join(os.getcwd(), ".env")
    if not os.path.isfile(path):
        return
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                key = k.strip()
                val = v.strip().strip('"').strip("'")
                if key and key not in os.environ:
                    os.environ[key] = val
    except Exception:  # pragma: no cover - defensive
        # Silently ignore malformed .env
        return


@click.group(help="Brand Name Gen CLI")
def cli() -> None:
    """Root command group."""
    _load_env_from_dotenv()


@cli.command("generate", help="Generate brand name ideas from keywords")
@click.argument("keywords", nargs=-1, required=True)
@click.option(
    "--style",
    type=click.Choice(["modern", "classic", "playful", "professional"], case_sensitive=False),
    default=None,
    help="Optional naming style",
)
@click.option("--limit", type=int, default=20, show_default=True, help="Max results")
def cmd_generate(keywords: Tuple[str, ...], style: str | None, limit: int) -> None:
    """Generate names and print one per line."""
    names: List[str] = generate_names(list(keywords), style=style, limit=limit)
    for n in names:
        click.echo(n)


@cli.command("check-www", help="Check if www.<brand>.com is available")
@click.argument("brand", type=str, required=True)
@click.option(
    "--provider",
    type=click.Choice(["google", "cloudflare"], case_sensitive=False),
    default="google",
    show_default=True,
    help="DoH provider for optional www probe",
)
@click.option("--timeout", type=float, default=5.0, show_default=True, help="HTTP timeout (s)")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output JSON")
def cmd_check_www(brand: str, provider: str, timeout: float, as_json: bool) -> None:
    """Check `<brand>.com` via RDAP and optionally probe www via DoH."""
    result: DomainAvailability = is_com_available(brand, timeout_s=timeout)
    www_resolves: bool | None
    if result.available is False:
        www_resolves = check_www_resolves(result.domain, provider=provider, timeout_s=timeout)
    elif result.available is True:
        www_resolves = False
    else:
        www_resolves = None

    payload = result.model_dump(mode="json")
    payload["www_resolves"] = www_resolves
    if as_json:
        click.echo(json.dumps(payload))
        return
    # Print the same fields as JSON in a human-readable key: value format
    # Keep stable order
    click.echo(f"domain: {payload['domain']}")
    click.echo(f"available: {payload['available']}")
    click.echo(f"rdap_status: {payload['rdap_status']}")
    click.echo(f"authoritative: {payload['authoritative']}")
    click.echo(f"source: {payload['source']}")
    click.echo(f"note: {payload['note']}")
    click.echo(f"www_resolves: {payload['www_resolves']}")


if __name__ == "__main__":  # pragma: no cover
    cli()


def _norm_title(s: str) -> str:
    t = s.lower()
    t = re.sub(r"[^a-z0-9]+", " ", t).strip()
    return re.sub(r"\s+", " ", t)


def _similar(a: str, b: str, *, threshold: float = 0.9) -> bool:
    return SequenceMatcher(None, _norm_title(a), _norm_title(b)).ratio() >= threshold


@cli.group("check-android", help="Check Android app title uniqueness (providers: appfollow, playstore)")
def check_android() -> None:
    """Parent group for Android title checks."""


@check_android.command("appfollow", help="Use AppFollow ASO suggests to check title uniqueness")
@click.argument("title", type=str, required=True)
@click.option("--country", default="us", show_default=True, help="2-letter country code (lowercase)")
@click.option("--threshold", type=float, default=0.9, show_default=True, help="Similarity threshold (0-1)")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output JSON")
def check_android_appfollow(title: str, country: str, threshold: float, as_json: bool) -> None:
    api_key = os.getenv("APPFOLLOW_API_KEY")
    if not api_key:
        raise click.ClickException("APPFOLLOW_API_KEY not set in environment")
    base = "https://api.appfollow.io/api/v2/aso/suggests"
    headers = {"X-AppFollow-API-Token": api_key, "Accept": "application/json"}
    params = {"term": title, "country": country.lower()}
    r = requests.get(base, headers=headers, params=params, timeout=30)
    if r.status_code in (401, 403):
        raise click.ClickException("AppFollow unauthorized/forbidden: check API key and workspace access")
    try:
        r.raise_for_status()
    except requests.HTTPError as e:  # pragma: no cover - network edge
        raise click.ClickException(f"AppFollow error: {e}")
    data = r.json()
    suggestions = [
        {"pos": it.get("pos"), "term": it.get("displayTerm") or it.get("term")}
        for it in data
        if isinstance(it, dict)
    ]
    payload: Dict[str, Any] = {
        "title": title,
        "country": country,
        "provider": "appfollow:aso_suggests",
        "suggestions": suggestions,
        "collisions": [],
        "threshold": threshold,
        "unique_enough": None,
    }
    norm_in = _norm_title(title)
    collisions: List[Dict[str, Any]] = []
    for s in suggestions:
        term_val = s.get("term")
        if not isinstance(term_val, str):
            continue
        norm_term = _norm_title(term_val)
        compact_in = norm_in.replace(" ", "")
        compact_term = norm_term.replace(" ", "")
        if norm_term != norm_in and (
            compact_in in compact_term or compact_term in compact_in or _similar(term_val, title, threshold=threshold)
        ):
            collisions.append(s)
    payload["collisions"] = collisions
    payload["unique_enough"] = len(collisions) == 0

    if as_json:
        click.echo(json.dumps(payload))
        return
    click.echo(f"title: {payload['title']}")
    click.echo(f"country: {payload['country']}")
    click.echo(f"provider: {payload['provider']}")
    click.echo(f"threshold: {payload['threshold']}")
    click.echo(f"unique_enough: {payload['unique_enough']}")
    click.echo("suggestions:")
    for s in payload["suggestions"]:
        click.echo(f"  - pos={s.get('pos')} term={s.get('term')}")
    click.echo("collisions:")
    for c in payload["collisions"]:
        click.echo(f"  - pos={c.get('pos')} term={c.get('term')}")


@check_android.command("playstore", help="Use Google Play web search to check title visibility")
@click.argument("title", type=str, required=True)
@click.option("--hl", default="en", show_default=True, help="Play locale code (e.g., en)")
@click.option("--gl", default="US", show_default=True, help="Play country code (e.g., US)")
@click.option("--threshold", type=float, default=0.9, show_default=True, help="Similarity threshold (0-1)")
@click.option("--json", "as_json", is_flag=True, default=False, help="Output JSON")
def check_android_playstore(title: str, hl: str, gl: str, threshold: float, as_json: bool) -> None:
    q = up.quote(f'"{title}"')
    url = f"https://play.google.com/store/search?q={q}&c=apps&hl={hl}&gl={gl}"
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
        )
    }
    r = requests.get(url, headers=headers, timeout=30)
    if r.status_code != 200:
        raise click.ClickException(f"Play search error: HTTP {r.status_code}")
    html = r.text
    labels: List[str] = []
    for m in re.finditer(r'aria-label="([^"]+)"', html):
        labels.append(m.group(1))
    seen: set[str] = set()
    uniq_labels: List[str] = []
    for lab in labels:
        if lab not in seen:
            uniq_labels.append(lab)
            seen.add(lab)
    terms = uniq_labels[:100]
    suggestions = [{"pos": i + 1, "term": t} for i, t in enumerate(terms)]
    payload: Dict[str, Any] = {
        "title": title,
        "country": "",
        "provider": "playstore:web_search",
        "suggestions": suggestions,
        "collisions": [],
        "threshold": threshold,
        "unique_enough": None,
        "play_url": url,
    }
    norm_in = _norm_title(title)
    collisions_ps: List[Dict[str, Any]] = []
    for s in suggestions:
        term_val = s.get("term")
        if not isinstance(term_val, str):
            continue
        norm_term = _norm_title(term_val)
        compact_in = norm_in.replace(" ", "")
        compact_term = norm_term.replace(" ", "")
        if norm_term != norm_in and (
            compact_in in compact_term or compact_term in compact_in or _similar(term_val, title, threshold=threshold)
        ):
            collisions_ps.append(s)
    payload["collisions"] = collisions_ps
    payload["unique_enough"] = len(collisions_ps) == 0

    if as_json:
        click.echo(json.dumps(payload))
        return
    click.echo(f"title: {payload['title']}")
    click.echo(f"provider: {payload['provider']}")
    click.echo(f"threshold: {payload['threshold']}")
    click.echo(f"unique_enough: {payload['unique_enough']}")
    click.echo(f"play_url: {payload['play_url']}")
    click.echo("suggestions:")
    for s in payload["suggestions"]:
        click.echo(f"  - pos={s.get('pos')} term={s.get('term')}")
    click.echo("collisions:")
    for c in payload["collisions"]:
        click.echo(f"  - pos={c.get('pos')} term={c.get('term')}")
