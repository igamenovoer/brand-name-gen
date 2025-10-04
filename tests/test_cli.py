from __future__ import annotations

import json
from typing import Any, Dict

from click.testing import CliRunner

from brand_name_gen.cli import cli
import brand_name_gen.cli as cli_mod
import brand_name_gen.domain_check as dc


class _Resp:
    def __init__(self, status_code: int, json_data: Dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self._json = json_data or {}

    @property
    def ok(self) -> bool:  # emulate requests.Response.ok
        return 200 <= self.status_code < 400

    def json(self) -> Dict[str, Any]:
        return self._json


def test_cli_generate_basic() -> None:
    runner = CliRunner()
    res = runner.invoke(cli, ["generate", "eco", "solar", "--style", "modern", "--limit", "2"])
    assert res.exit_code == 0
    lines = [ln for ln in res.output.strip().splitlines() if ln]
    assert len(lines) == 2


def test_cli_check_www_available_json(monkeypatch: Any) -> None:
    def fake_get(url: str, timeout: float) -> _Resp:  # type: ignore[override]
        assert "/domain/brand-name.com" in url
        return _Resp(404)

    monkeypatch.setattr(dc.requests, "get", fake_get)  # type: ignore[arg-type]
    runner = CliRunner()
    res = runner.invoke(cli, ["check-www", "brand name", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["domain"] == "brand-name.com"
    assert data["available"] is True
    assert data["www_resolves"] is False


def test_cli_check_www_taken_with_probe_json(monkeypatch: Any) -> None:
    def fake_is_com_available(brand: str, *, timeout_s: float = 5.0):
        return dc.DomainAvailability(
            domain="openai.com",
            available=False,
            rdap_status=200,
            authoritative=True,
            source=dc.Source.rdap_verisign,
        )

    def fake_probe(domain: str, *, provider: str = "google", timeout_s: float = 5.0) -> bool:
        assert domain == "openai.com"
        return True

    # Patch the symbol used inside the CLI module
    monkeypatch.setattr(cli_mod, "is_com_available", fake_is_com_available)  # type: ignore[arg-type]
    monkeypatch.setattr(dc, "check_www_resolves", fake_probe)  # type: ignore[arg-type]

    runner = CliRunner()
    res = runner.invoke(cli, ["check-www", "OpenAI", "--json"])
    assert res.exit_code == 0
    data = json.loads(res.output)
    assert data["domain"] == "openai.com"
    assert data["available"] is False
    assert data["www_resolves"] is True


def test_cli_check_www_human_output_includes_all_fields(monkeypatch: Any) -> None:
    def fake_is_com_available(brand: str, *, timeout_s: float = 5.0):
        return dc.DomainAvailability(
            domain="brand-name.com",
            available=True,
            rdap_status=404,
            authoritative=True,
            source=dc.Source.rdap_verisign,
        )

    monkeypatch.setattr(cli_mod, "is_com_available", fake_is_com_available)  # type: ignore[arg-type]

    runner = CliRunner()
    res = runner.invoke(cli, ["check-www", "brand name"])  # no --json
    assert res.exit_code == 0
    out = res.output
    # Ensure all JSON keys are present in key: value form
    assert "domain: brand-name.com" in out
    assert "available: True" in out
    assert "rdap_status: 404" in out
    assert "authoritative: True" in out
    assert "source: rdap:verisign" in out
    assert "note: None" in out
    assert "www_resolves: False" in out
