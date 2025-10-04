from __future__ import annotations

import json
from typing import Any, Dict, List

import brand_name_gen.title_check as tc


class _Resp:
    def __init__(self, status_code: int, data: Any = None, text: str = "") -> None:
        self.status_code = status_code
        self._data = data
        self.text = text

    def json(self) -> Any:
        return self._data

    def raise_for_status(self) -> None:
        if not (200 <= self.status_code < 400):
            raise Exception(f"HTTP {self.status_code}")


def test_normalize_and_similarity() -> None:
    assert tc.normalize_title("Brand Name") == "brand name"
    assert tc.is_similar("BrandName", "brand name") is True
    assert tc.is_similar("Foo", "Bar") is False


def test_check_title_appfollow_success(monkeypatch: Any) -> None:
    data = [
        {"pos": 1, "displayTerm": "brandname"},
        {"pos": 2, "displayTerm": "brand name"},
        {"pos": 3, "term": "other app"},
    ]

    def fake_get(url: str, headers: Dict[str, str], params: Dict[str, str], timeout: float) -> _Resp:  # type: ignore[override]
        assert "aso/suggests" in url
        assert headers.get("X-AppFollow-API-Token") == "TOK"
        assert params.get("term") == "BrandName"
        return _Resp(200, data)

    monkeypatch.setenv("APPFOLLOW_API_KEY", "TOK")
    monkeypatch.setattr(tc.requests, "get", fake_get)  # type: ignore[arg-type]

    res = tc.check_title_appfollow("BrandName", country="us", threshold=0.9)
    assert res.provider == tc.Provider.appfollow
    assert res.title == "BrandName"
    assert any(c.term.startswith("brand name") for c in res.collisions)


def test_check_title_appfollow_missing_key(monkeypatch: Any) -> None:
    monkeypatch.delenv("APPFOLLOW_API_KEY", raising=False)
    try:
        tc.check_title_appfollow("BrandName")
    except tc.TitleCheckError as e:  # noqa: SIM105
        assert "APPFOLLOW_API_KEY" in str(e)
    else:  # pragma: no cover
        raise AssertionError("expected TitleCheckError")


def test_check_title_playstore_success(monkeypatch: Any) -> None:
    html = '<div aria-label="BrandName"></div><div aria-label="Brand Name Planner"></div>'

    def fake_get(url: str, headers: Dict[str, str], timeout: float) -> _Resp:  # type: ignore[override]
        assert "play.google.com" in url
        return _Resp(200, text=html)

    monkeypatch.setattr(tc.requests, "get", fake_get)  # type: ignore[arg-type]
    res = tc.check_title_playstore("BrandName", hl="en", gl="US")
    assert res.provider == tc.Provider.playstore
    assert res.meta["play_url"]
    assert any(c.term.lower().startswith("brand name") for c in res.collisions)


def test_check_title_aggregate(monkeypatch: Any) -> None:
    # AppFollow mock
    af_data = [{"displayTerm": "Brand Name"}]

    def fake_get_af(url: str, headers: Dict[str, str], params: Dict[str, str], timeout: float) -> _Resp:  # type: ignore[override]
        return _Resp(200, af_data)

    # Play mock
    html = '<div aria-label="Brand Name"></div>'

    def fake_get_ps(url: str, headers: Dict[str, str], timeout: float) -> _Resp:  # type: ignore[override]
        return _Resp(200, text=html)

    # Patch sequencing by switching implementations when called
    call_idx = {"i": 0}

    def fake_get_switch(*args: Any, **kwargs: Any) -> _Resp:
        if call_idx["i"] == 0:
            call_idx["i"] += 1
            return fake_get_af(*args, **kwargs)
        return fake_get_ps(*args, **kwargs)

    monkeypatch.setenv("APPFOLLOW_API_KEY", "TOK")
    monkeypatch.setattr(tc.requests, "get", fake_get_switch)  # type: ignore[arg-type]

    out = tc.check_title("BrandName")
    assert len(out) == 2
    assert {r.provider for r in out} == {tc.Provider.appfollow, tc.Provider.playstore}

