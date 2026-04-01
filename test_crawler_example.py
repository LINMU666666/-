import types

import pytest

import crawler_example


class _DummyResponse:
    def __init__(self, status_code: int = 200, text: str = "ok", content: bytes = b"ok"):
        self.status_code = status_code
        self.text = text
        self.content = content

    def raise_for_status(self) -> None:
        if not (200 <= self.status_code < 400):
            raise RuntimeError(f"status {self.status_code}")


def _mock_get(monkeypatch):
    calls = []

    def _fake_get(*args, **kwargs):
        calls.append({"args": args, "kwargs": kwargs})
        return _DummyResponse()

    monkeypatch.setattr(crawler_example, "requests", types.SimpleNamespace(get=_fake_get))
    return calls


def test_fetch_url_no_proxy(monkeypatch):
    calls = _mock_get(monkeypatch)
    crawler_example.fetch_url("https://example.com", disable_proxy=True)
    assert calls[0]["kwargs"]["proxies"] == {"http": None, "https": None}


def test_fetch_url_custom_proxy(monkeypatch):
    calls = _mock_get(monkeypatch)
    crawler_example.fetch_url("https://example.com", proxy="http://p:1")
    assert calls[0]["kwargs"]["proxies"] == {"http": "http://p:1", "https": "http://p:1"}


def test_fetch_url_verify_cert(monkeypatch):
    calls = _mock_get(monkeypatch)
    crawler_example.fetch_url("https://example.com", verify_cert="/tmp/ca.pem")
    assert calls[0]["kwargs"]["verify"] == "/tmp/ca.pem"


def test_fetch_url_default_uses_env_proxy(monkeypatch):
    calls = _mock_get(monkeypatch)
    crawler_example.fetch_url("https://example.com")
    # Default uses system proxy (None means requests reads env)
    assert calls[0]["kwargs"]["proxies"] is None
