from __future__ import annotations

import json
from typing import Any, Dict, List

from click.testing import CliRunner

import brand_name_gen.search.dataforseo.backends as backends_mod
from brand_name_gen.cli import cli


class _Resp:
    def __init__(self, status_code: int, data: Dict[str, Any]) -> None:
        self.status_code = status_code
        self._data = data

    def json(self) -> Dict[str, Any]:
        return self._data

    def raise_for_status(self) -> None:
        if not (200 <= self.status_code < 400):
            raise Exception(f"HTTP {self.status_code}")


def _make_tasks(items: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {"tasks": [{"result": [{"items": items, "check_url": "https://google.com"}]}]}


def test_check_search_engine_dataforseo_json(monkeypatch: Any) -> None:
    # Fake DataForSEO response with organic items
    items = [
        {"type": "organic", "rank_absolute": 3, "title": "Other"},
        {"type": "organic", "rank_absolute": 4, "title": "HB - Apps on Google Play", "url": "https://play.google.com/..."},
        {"type": "organic", "rank_absolute": 8, "title": "hb app store"},
    ]
    data = _make_tasks(items)

    def fake_post(url: str, json: Any, auth: Any, timeout: float) -> _Resp:  # type: ignore[override]
        # Ensure endpoint and payload basics
        assert "organic/live/advanced" in url
        assert isinstance(json, list) and json[0].get("keyword") == "hb-app"
        # Ensure auth object carries credentials from .env precedence
        assert getattr(auth, "username", None) == "DOTENV_LOGIN"
        assert getattr(auth, "password", None) == "DOTENV_PASSWORD"
        return _Resp(200, data)

    # Patch requests.post used within the RequestsBackend implementation
    monkeypatch.setattr(backends_mod.requests, "post", fake_post)  # type: ignore[arg-type]
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Prepare .env with creds that should take precedence over OS env
        with open(".env", "w", encoding="utf-8") as f:
            f.write("DATAFORSEO_LOGIN=DOTENV_LOGIN\nDATAFORSEO_PASSWORD=DOTENV_PASSWORD\n")
        # Also set OS env to different values to verify precedence
        monkeypatch.setenv("DATAFORSEO_LOGIN", "ENV_LOGIN")
        monkeypatch.setenv("DATAFORSEO_PASSWORD", "ENV_PASSWORD")

        res = runner.invoke(
            cli,
            [
                "check-search-engine",
                "dataforseo",
                "hb-app",
                "--location-code",
                "2840",
                "--language-code",
                "en",
                "--depth",
                "50",
                "--json",
            ],
        )
        assert res.exit_code == 0
        payload = json.loads(res.output)
        assert payload["keyword"] == "hb-app"
        assert payload["top_position"] == 4
        assert payload["total_matches"] >= 1
        assert payload["check_url"]


def test_check_search_engine_dataforseo_missing_creds(monkeypatch: Any) -> None:
    runner = CliRunner()
    with runner.isolated_filesystem():
        # Ensure no environment creds leak in
        monkeypatch.delenv("DATAFORSEO_LOGIN", raising=False)
        monkeypatch.delenv("DATAFORSEO_USERNAME", raising=False)
        monkeypatch.delenv("DATAFORSEO_EMAIL", raising=False)
        monkeypatch.delenv("DATAFORSEO_PASSWORD", raising=False)
        monkeypatch.delenv("DATAFORSEO_PASS", raising=False)
        res = runner.invoke(cli, ["check-search-engine", "dataforseo", "hb-app", "--json"])
        assert res.exit_code != 0
        assert "DATAFORSEO_LOGIN" in res.output
