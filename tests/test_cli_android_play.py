from __future__ import annotations

import json
from typing import Any, Dict

from click.testing import CliRunner

import brand_name_gen.cli as cli_mod
from brand_name_gen.cli import cli


def test_check_android_playstore_json(monkeypatch: Any) -> None:
    # Minimal HTML with aria-labels including near matches
    html = '<div aria-label="BrandName"></div><div aria-label="Brand Name Planner"></div><div aria-label="Other"></div>'

    class _R:
        status_code = 200

        def __init__(self, text: str) -> None:
            self.text = text

        def json(self) -> Dict[str, Any]:  # pragma: no cover
            return {}

    def fake_get(url: str, headers: Dict[str, str], timeout: int) -> _R:  # type: ignore[override]
        assert "play.google.com" in url
        return _R(html)

    monkeypatch.setattr(cli_mod.requests, "get", fake_get)  # type: ignore[arg-type]
    runner = CliRunner()
    res = runner.invoke(cli, [
        "check-android",
        "playstore",
        "BrandName",
        "--hl",
        "en",
        "--gl",
        "US",
        "--threshold",
        "0.7",
        "--json",
    ])
    assert res.exit_code == 0
    payload = json.loads(res.output)
    assert payload["provider"] == "playstore:web_search"
    assert payload["unique_enough"] is False
    assert any(c["term"].startswith("Brand Name") for c in payload["collisions"])  # type: ignore[index]
