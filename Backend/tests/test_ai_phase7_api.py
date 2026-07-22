import os
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.config.loader import AIConfig
from app.ai.domain.entities import AIInteraction, AskResult
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


def _override_config() -> None:
    app.dependency_overrides[_load_config] = lambda: _mock_config()


def _override_auth(has_permission: bool = True) -> None:
    app.dependency_overrides[get_current_user] = lambda: _mock_user(
        has_permission
    )


def _override_use_case(
    answer: str = "There are 3 pets.",
    sql: str = "SELECT COUNT(*) FROM pets",
) -> None:
    use_case = MagicMock()
    use_case.ask = AsyncMock(
        return_value=AskResult(
            answer=answer,
            generated_sql=sql,
            execution_ms=42,
            provider="groq",
            model="llama-3.3-70b-versatile",
            interaction_id="11111111-1111-1111-1111-111111111111",
            created_at=datetime.now(timezone.utc),
        )
    )
    app.dependency_overrides[get_admin_assistant_use_case] = (
        lambda: use_case
    )


class TestAuth:
    def test_missing_jwt_returns_401(self):
        resp = client.post(
            "/api/v1/ai/ask", json={"question": "test"}
        )
        assert resp.status_code == 401

    def test_invalid_jwt_returns_401(self):
        resp = client.post(
            "/api/v1/ai/ask",
            json={"question": "test"},
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 401

    def test_missing_ai_assistant_permission_returns_403(self):
        _override_config()
        _override_auth(has_permission=False)

        resp = client.post(
            "/api/v1/ai/ask",
            json={"question": "test"},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 403
        data = resp.json()
        assert "ai:assistant" in data["detail"].lower()


class TestValidation:
    def test_empty_question_returns_400(self):
        _override_config()
        _override_auth()
        _override_use_case()

        resp = client.post(
            "/api/v1/ai/ask",
            json={"question": ""},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 400

    def test_whitespace_only_question_returns_400(self):
        _override_config()
        _override_auth()
        _override_use_case()

        resp = client.post(
            "/api/v1/ai/ask",
            json={"question": "   "},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 400

    def test_question_exceeds_max_length_returns_400(self):
        app.dependency_overrides[_load_config] = lambda: AIConfig(
            max_question_length=10
        )
        _override_auth()
        _override_use_case()

        resp = client.post(
            "/api/v1/ai/ask",
            json={"question": "This question is way too long"},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 400


class TestSuccess:
    def test_returns_ask_response_fields(self):
        _override_config()
        _override_auth()
        _override_use_case()

        resp = client.post(
            "/api/v1/ai/ask",
            json={"question": "How many pets?"},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["answer"] == "There are 3 pets."
        assert data["generated_sql"] == "SELECT COUNT(*) FROM pets"
        assert data["execution_time_ms"] == 42
        assert data["provider"] == "groq"
        assert data["model"] == "llama-3.3-70b-versatile"
        assert data["conversation_id"] == "11111111-1111-1111-1111-111111111111"
        assert "created_at" in data

    def test_passes_question_to_use_case(self):
        _override_config()
        _override_auth()
        use_case = MagicMock()
        use_case.ask = AsyncMock(
            return_value=AskResult(
                answer="",
                generated_sql="",
                execution_ms=0,
                provider="groq",
                model="llama-3.3-70b-versatile",
                interaction_id="id",
                created_at=datetime.now(timezone.utc),
            )
        )
        app.dependency_overrides[get_admin_assistant_use_case] = (
            lambda: use_case
        )

        resp = client.post(
            "/api/v1/ai/ask",
            json={"question": "How many pets?"},
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 200
        use_case.ask.assert_awaited_once_with("How many pets?", "1")


def _make_interaction(
    idx: int,
    question: str = "test",
    answer: str = "answer",
) -> AIInteraction:
    return AIInteraction(
        interaction_id=f"id-{idx:04d}",
        user_id="1",
        question=question,
        generated_sql=f"SELECT {idx}",
        execution_ms=idx * 10,
        response=answer,
        provider="groq",
        created_at=datetime.now(timezone.utc),
    )


class TestHistoryAuth:
    def test_missing_jwt_returns_401(self):
        resp = client.get("/api/v1/ai/history")
        assert resp.status_code == 401

    def test_invalid_jwt_returns_401(self):
        resp = client.get(
            "/api/v1/ai/history",
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 401

    def test_missing_ai_assistant_permission_returns_403(self):
        _override_auth(has_permission=False)

        resp = client.get(
            "/api/v1/ai/history",
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 403
        data = resp.json()
        assert "ai:assistant" in data["detail"].lower()


class TestHistory:
    def test_empty_history_returns_empty_list(self):
        _override_auth()
        use_case = MagicMock()
        use_case.get_history = AsyncMock(return_value=[])
        app.dependency_overrides[get_admin_assistant_use_case] = (
            lambda: use_case
        )

        resp = client.get(
            "/api/v1/ai/history",
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["items"] == []
        assert data["count"] == 0

    def test_populated_history_returns_items(self):
        _override_auth()
        interactions = [
            _make_interaction(1, question="q1", answer="a1"),
            _make_interaction(2, question="q2", answer="a2"),
        ]
        use_case = MagicMock()
        use_case.get_history = AsyncMock(return_value=interactions)
        app.dependency_overrides[get_admin_assistant_use_case] = (
            lambda: use_case
        )

        resp = client.get(
            "/api/v1/ai/history",
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 2
        assert len(data["items"]) == 2
        assert data["items"][0]["id"] == "id-0001"
        assert data["items"][0]["question"] == "q1"
        assert data["items"][0]["answer"] == "a1"
        assert data["items"][0]["generated_sql"] == "SELECT 1"
        assert data["items"][0]["execution_time_ms"] == 10
        assert data["items"][0]["provider"] == "groq"
        assert data["items"][1]["id"] == "id-0002"

    def test_respects_limit_parameter(self):
        _override_auth()
        use_case = MagicMock()
        use_case.get_history = AsyncMock(return_value=[])
        app.dependency_overrides[get_admin_assistant_use_case] = (
            lambda: use_case
        )

        client.get(
            "/api/v1/ai/history?limit=5",
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        use_case.get_history.assert_awaited_once_with("1", limit=5)

    def test_default_limit_is_20(self):
        _override_auth()
        use_case = MagicMock()
        use_case.get_history = AsyncMock(return_value=[])
        app.dependency_overrides[get_admin_assistant_use_case] = (
            lambda: use_case
        )

        client.get(
            "/api/v1/ai/history",
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        use_case.get_history.assert_awaited_once_with("1", limit=20)

    def test_invalid_limit_returns_422(self):
        _override_auth()
        use_case = MagicMock()
        app.dependency_overrides[get_admin_assistant_use_case] = (
            lambda: use_case
        )

        resp = client.get(
            "/api/v1/ai/history?limit=0",
            headers={"Authorization": f"Bearer {TOKEN}"},
        )
        assert resp.status_code == 422
