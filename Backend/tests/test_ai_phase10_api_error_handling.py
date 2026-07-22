import os
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.config.loader import AIConfig
from app.ai.domain.entities import AskResult
from app.ai.infrastructure.exceptions import (
    AIProviderAuthError,
    AIProviderConnectionError,
    AIProviderRateLimitError,
    AIProviderTimeoutError,
    MCPConnectionError,
    MCPExecutionError,
    MCPInvalidResponseError,
    MCPTimeoutError,
)
from app.ai.presentation.dependencies.ai_dependencies import (
    _load_config,
    get_admin_assistant_use_case,
)
from app.auth.jwt_handler import create_access_token, get_current_user
from app.main import app

client = TestClient(app)

TOKEN = create_access_token({"sub": "1"})


def _mock_config() -> AIConfig:
    return AIConfig(max_question_length=1000)


def _mock_user(has_permission: bool = True):
    user = MagicMock()
    user.id = 1
    user.role_id = 1
    perm = MagicMock()
    perm.name = "ai:assistant"
    user.role.permissions = [perm] if has_permission else []
    return user


@pytest.fixture(autouse=True)
def _clear_overrides():
    app.dependency_overrides.clear()
    yield
    app.dependency_overrides.clear()


def _setup(use_case=None):
    app.dependency_overrides[_load_config] = lambda: _mock_config()
    app.dependency_overrides[get_current_user] = lambda: _mock_user(has_permission=True)
    if use_case is not None:
        app.dependency_overrides[get_admin_assistant_use_case] = lambda: use_case


class TestAPIErrorHandling:
    def _make_use_case(self, side_effect):
        use_case = MagicMock()
        use_case.ask = AsyncMock(side_effect=side_effect)
        return use_case

    def test_provider_timeout_returns_408(self):
        use_case = self._make_use_case(
            AIProviderTimeoutError("Provider timed out")
        )
        _setup(use_case)

        resp = client.post(
            "/api/v1/ai/ask",
            json={"question": "How many pets?"},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 408
        assert "timed out" in resp.json()["detail"]

    def test_provider_auth_error_returns_401(self):
        use_case = self._make_use_case(
            AIProviderAuthError("Invalid API key")
        )
        _setup(use_case)

        resp = client.post(
            "/api/v1/ai/ask",
            json={"question": "How many pets?"},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 401
        assert "authentication" in resp.json()["detail"].lower()

    def test_provider_rate_limit_returns_502(self):
        use_case = self._make_use_case(
            AIProviderRateLimitError("Rate limit exceeded")
        )
        _setup(use_case)

        resp = client.post(
            "/api/v1/ai/ask",
            json={"question": "How many pets?"},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 502

    def test_provider_connection_error_returns_502(self):
        use_case = self._make_use_case(
            AIProviderConnectionError("Connection refused")
        )
        _setup(use_case)

        resp = client.post(
            "/api/v1/ai/ask",
            json={"question": "How many pets?"},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 502

    def test_mcp_timeout_returns_504(self):
        use_case = self._make_use_case(
            MCPTimeoutError("MCP query timed out")
        )
        _setup(use_case)

        resp = client.post(
            "/api/v1/ai/ask",
            json={"question": "How many pets?"},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 504

    def test_mcp_connection_error_returns_504(self):
        use_case = self._make_use_case(
            MCPConnectionError("MCP unavailable")
        )
        _setup(use_case)

        resp = client.post(
            "/api/v1/ai/ask",
            json={"question": "How many pets?"},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 504

    def test_mcp_execution_error_returns_502(self):
        use_case = self._make_use_case(
            MCPExecutionError("Query execution failed")
        )
        _setup(use_case)

        resp = client.post(
            "/api/v1/ai/ask",
            json={"question": "How many pets?"},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 502

    def test_mcp_invalid_response_returns_502(self):
        use_case = self._make_use_case(
            MCPInvalidResponseError("Invalid response format")
        )
        _setup(use_case)

        resp = client.post(
            "/api/v1/ai/ask",
            json={"question": "How many pets?"},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 502

    def test_runtime_error_returns_502(self):
        use_case = self._make_use_case(
            RuntimeError("Something went wrong")
        )
        _setup(use_case)

        resp = client.post(
            "/api/v1/ai/ask",
            json={"question": "How many pets?"},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 502

    def test_unexpected_exception_returns_500(self):
        use_case = self._make_use_case(
            Exception("Unexpected failure")
        )
        _setup(use_case)

        resp = client.post(
            "/api/v1/ai/ask",
            json={"question": "How many pets?"},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 500
        assert "Unexpected server error" in resp.json()["detail"]

    def test_history_generic_error_returns_500(self):
        use_case = MagicMock()
        use_case.get_history = AsyncMock(
            side_effect=Exception("DB error")
        )
        _setup(use_case)

        resp = client.get(
            "/api/v1/ai/history",
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 500
        assert "Unexpected server error" in resp.json()["detail"]
