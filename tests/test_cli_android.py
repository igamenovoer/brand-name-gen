from __future__ import annotations

import json
from typing import Any, Dict, List

from click.testing import CliRunner

import brand_name_gen.cli as cli_mod
from brand_name_gen.cli import cli


class _Resp:
    def __init__(self, status_code: int, data: List[Dict[str, Any]]) -> None:
        self.status_code = status_code
        self._data = data

    def json(self) -> List[Dict[str, Any]]:
        return self._data

    def raise_for_status(self) -> None:
        if not (200 <= self.status_code < 400):
            raise Exception(f"HTTP {self.status_code}")


def test_check_android_appfollow_json(monkeypatch: Any) -> None:
    # Fake AppFollow suggests response
    data = [
        {"pos": 1, "displayTerm": "brandname"},
        {"pos": 2, "displayTerm": "brand name"},  # near match
        {"pos": 3, "displayTerm": "brandname app"},  # near match
        {"pos": 4, "displayTerm": "other app"},
    ]

    def fake_get(url: str, headers: Dict[str, str], params: Dict[str, str], timeout: int) -> _Resp:  # type: ignore[override]
        assert "aso/suggests" in url
        assert headers.get("X-AppFollow-API-Token") == "K"
        assert params.get("term") == "BrandName"
        assert params.get("country") == "us"
        return _Resp(200, data)

    monkeypatch.setenv("APPFOLLOW_API_KEY", "K")
    monkeypatch.setattr(cli_mod.requests, "get", fake_get)  # type: ignore[arg-type]

    runner = CliRunner()
    res = runner.invoke(cli, ["check-android", "appfollow", "BrandName", "--country", "us", "--json"])
    assert res.exit_code == 0
    payload = json.loads(res.output)
    assert payload["provider"] == "appfollow:aso_suggests"
    assert payload["country"] == "us"
    assert payload["unique_enough"] is False
    assert len(payload["collisions"]) >= 1


def test_check_android_missing_key(monkeypatch: Any) -> None:
    monkeypatch.delenv("APPFOLLOW_API_KEY", raising=False)
    runner = CliRunner()
    with runner.isolated_filesystem():
        res = runner.invoke(cli, ["check-android", "appfollow", "BrandName", "--json"])
        assert res.exit_code != 0
        assert "APPFOLLOW_API_KEY" in res.output


def test_check_android_uses_dotenv(monkeypatch: Any) -> None:
    # Ensure no env var is set
    monkeypatch.delenv("APPFOLLOW_API_KEY", raising=False)

    # Fake network
    data = [{"pos": 1, "displayTerm": "brandname"}]

    def fake_get(url: str, headers: Dict[str, str], params: Dict[str, str], timeout: int):  # type: ignore[override]
        assert headers.get("X-AppFollow-API-Token") == "DOTENVKEY"
        class _R:
            status_code = 200
            def json(self):  # noqa: D401
                return data
            def raise_for_status(self) -> None:
                return None
        return _R()

    monkeypatch.setattr(cli_mod.requests, "get", fake_get)  # type: ignore[arg-type]

    runner = CliRunner()
    with runner.isolated_filesystem():
        # Create .env in CWD for the CLI to load
        with open(".env", "w", encoding="utf-8") as f:
            f.write("APPFOLLOW_API_KEY=DOTENVKEY\n")
        res = runner.invoke(cli, ["check-android", "appfollow", "BrandName", "--country", "us", "--json"])
        assert res.exit_code == 0
        payload = json.loads(res.output)
        assert payload["provider"] == "appfollow:aso_suggests"
