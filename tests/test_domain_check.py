from __future__ import annotations

from typing import Any, Dict

import types

import brand_name_gen.domain_check as dc
from brand_name_gen.domain_checker import DomainChecker


class _Resp:
    def __init__(self, status_code: int, json_data: Dict[str, Any] | None = None) -> None:
        self.status_code = status_code
        self._json = json_data or {}

    @property
    def ok(self) -> bool:  # emulate requests.Response.ok
        return 200 <= self.status_code < 400

    def json(self) -> Dict[str, Any]:
        return self._json


def test_is_com_available_available(monkeypatch: Any) -> None:
    def fake_get(url: str, timeout: float) -> _Resp:  # type: ignore[override]
        assert url.endswith("nonexistent-brand.com")
        return _Resp(404)

    monkeypatch.setattr(dc.requests, "get", fake_get)  # type: ignore[arg-type]
    res = dc.is_com_available("nonexistent brand")
    assert res.available is True
    assert res.authoritative is True
    assert res.rdap_status == 404


def test_is_com_available_taken(monkeypatch: Any) -> None:
    def fake_get(url: str, timeout: float) -> _Resp:  # type: ignore[override]
        assert url.endswith("openai.com")
        return _Resp(200)

    monkeypatch.setattr(dc.requests, "get", fake_get)  # type: ignore[arg-type]
    res = dc.is_com_available("OpenAI")
    assert res.available is False
    assert res.authoritative is True
    assert res.rdap_status == 200


def test_check_www_resolves_via_google(monkeypatch: Any) -> None:
    payload = {"Status": 0, "Answer": [{"data": "93.184.216.34"}]}

    def fake_get(url: str, timeout: float) -> _Resp:  # type: ignore[override]
        assert "dns.google/resolve" in url
        return _Resp(200, payload)

    monkeypatch.setattr(dc.requests, "get", fake_get)  # type: ignore[arg-type]
    assert dc.check_www_resolves("example.com") is True


def test_domain_checker_from_defaults(monkeypatch: Any) -> None:
    checker = DomainChecker.from_defaults()

    # patch the session inside checker
    def fake_get(url: str, timeout: float) -> _Resp:  # type: ignore[override]
        assert "/domain/brand-name.com" in url
        return _Resp(404)

    # mypy: requests.Session.get signature is broader; we rely on duck typing here
    checker.m_session.get = types.MethodType(lambda self, url, timeout=5.0: fake_get(url, timeout), checker.m_session)  # type: ignore[assignment]

    res = checker.check_com("Brand Name")
    assert res.domain.endswith("brand-name.com")
    assert res.available is True

