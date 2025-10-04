from __future__ import annotations

import json
from typing import Any, Dict, List

from brand_name_gen.search.dataforseo.google_rank import DataForSEORanker
from brand_name_gen.search.dataforseo.types import GoogleRankQuery
import brand_name_gen.search.dataforseo.backends as backends_mod


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


def test_ranker_run_success(monkeypatch: Any) -> None:
    items = [
        {"type": "organic", "rank_absolute": 2, "title": "Other"},
        {"type": "organic", "rank_absolute": 3, "title": "HB - Apps on Google Play", "url": "https://play.google.com/..."},
    ]
    data = _make_tasks(items)

    def fake_post(url: str, json: Any, auth: Any, timeout: float) -> _Resp:  # type: ignore[override]
        assert "organic/live/advanced" in url
        return _Resp(200, data)

    monkeypatch.setattr(backends_mod.requests, "post", fake_post)  # type: ignore[arg-type]

    ranker = DataForSEORanker()
    ranker.set_credentials("x", "y")
    query = GoogleRankQuery(keyword="hb-app", depth=50)
    res = ranker.run(query)
    assert res.top_position == 3
    assert res.total_matches >= 1
    assert res.check_url

