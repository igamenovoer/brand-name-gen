"""
Click-based CLI for Brand Name Gen.

Provides subcommands for generating names and checking `.com` availability.
"""

from __future__ import annotations

import json
from typing import List, Tuple

import click

from .core import generate_names
from .domain_check import DomainAvailability, check_www_resolves, is_com_available


@click.group(help="Brand Name Gen CLI")
def cli() -> None:
    """Root command group."""


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
