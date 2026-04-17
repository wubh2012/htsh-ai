from contextlib import asynccontextmanager
from pathlib import Path
import sys

import pytest


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))

import services.ai_client as ai_client_module
from services.ai_client import AIClient


class FakeCursor:
    def __init__(self, row):
        self.row = row

    async def fetchone(self):
        return self.row


class FakeDB:
    def __init__(self, row):
        self.row = row
        self.queries = []

    async def execute(self, query, params=()):
        self.queries.append((query, params))
        return FakeCursor(self.row)


def make_fake_get_db(row):
    @asynccontextmanager
    async def _fake_get_db():
        yield FakeDB(row)

    return _fake_get_db


@pytest.mark.anyio
async def test_ai_client_loads_enabled_config_from_database(monkeypatch):
    row = {
        "provider": "deepseek-test",
        "api_key": "sk-test",
        "endpoint": "https://api.deepseek.com",
        "model": "deepseek-chat",
        "enabled": True,
    }
    monkeypatch.setattr(ai_client_module, "get_db", make_fake_get_db(row))

    client = AIClient()
    await client._ensure_config_loaded()

    assert client.provider == "deepseek-test"
    assert client.api_key == "sk-test"
    assert client.endpoint == "https://api.deepseek.com"
    assert client.model == "deepseek-chat"


@pytest.mark.anyio
async def test_ai_client_raises_for_incomplete_database_config(monkeypatch):
    row = {
        "provider": "broken-config",
        "api_key": "",
        "endpoint": "https://example.com/v1/chat/completions",
        "model": "test-model",
        "enabled": True,
    }
    monkeypatch.setattr(ai_client_module, "get_db", make_fake_get_db(row))

    client = AIClient()

    with pytest.raises(ValueError, match="缺少必要字段: api_key"):
        await client._ensure_config_loaded()


def test_normalize_endpoint_keeps_full_path_and_supports_base_url():
    client = AIClient(api_key="sk", endpoint="https://api.deepseek.com", model="deepseek-chat")
    assert client._normalize_endpoint() == "https://api.deepseek.com/chat/completions"

    client.endpoint = "https://api.openai.com/v1/chat/completions"
    assert client._normalize_endpoint() == "https://api.openai.com/v1/chat/completions"

    client.endpoint = "https://example.com/v1?foo=bar"
    assert client._normalize_endpoint() == "https://example.com/v1/chat/completions?foo=bar"
