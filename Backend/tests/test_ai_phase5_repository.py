import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Callable

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.domain.entities import AIInteraction
from app.db.base import Base
from app.models.ai_interaction_model import AIInteractionModel


_COUNTER = 0


def _unique_id() -> str:
    global _COUNTER
    _COUNTER += 1
    return f"00000000-0000-0000-0000-{_COUNTER:012d}"


@pytest.fixture
def session_factory() -> Callable[[], Session]:
    engine = create_engine("sqlite://", echo=False)
    Base.metadata.create_all(bind=engine)
    factory = sessionmaker(bind=engine)
    return factory


@pytest.fixture
def repo(session_factory):
    from app.ai.infrastructure.repositories import PostgresConversationRepository

    return PostgresConversationRepository(
        session_factory=session_factory, retention_days=90
    )


def _interaction(
    user_id: str = "admin-1",
    question: str = "test",
    sql: str = "SELECT 1",
    response: str = "answer",
    execution_ms: int = 5,
    days_ago: int = 0,
) -> AIInteraction:
    return AIInteraction(
        interaction_id=_unique_id(),
        user_id=user_id,
        question=question,
        generated_sql=sql,
        execution_ms=execution_ms,
        response=response,
        provider="groq",
        created_at=datetime.now(timezone.utc) - timedelta(days=days_ago),
    )


class TestSave:
    @pytest.mark.asyncio
    async def test_saves_interaction(self, repo):
        interaction = _interaction()
        await repo.save(interaction)

        history = await repo.get_history("admin-1")
        assert len(history) == 1
        assert history[0].question == "test"

    @pytest.mark.asyncio
    async def test_saves_multiple_interactions(self, repo):
        await repo.save(_interaction(question="q1"))
        await repo.save(_interaction(question="q2"))

        history = await repo.get_history("admin-1")
        assert len(history) == 2

    @pytest.mark.asyncio
    async def test_saves_assigns_created_at_when_none(self, repo):
        interaction = AIInteraction(
            interaction_id=_unique_id(),
            user_id="admin-1",
            question="test",
            generated_sql="SELECT 1",
            provider="groq",
            created_at=None,
        )
        await repo.save(interaction)

        history = await repo.get_history("admin-1")
        assert len(history) == 1
        assert history[0].created_at is not None


class TestGetHistory:
    @pytest.mark.asyncio
    async def test_returns_empty_when_no_history(self, repo):
        history = await repo.get_history("unknown")
        assert history == []

    @pytest.mark.asyncio
    async def test_returns_only_requested_user(self, repo):
        await repo.save(_interaction(user_id="admin-1"))
        await repo.save(_interaction(user_id="admin-2"))

        history = await repo.get_history("admin-1")
        assert len(history) == 1
        assert history[0].user_id == "admin-1"

    @pytest.mark.asyncio
    async def test_orders_by_created_at_desc(self, repo):
        await repo.save(_interaction(question="old", days_ago=10))
        await repo.save(_interaction(question="recent", days_ago=1))
        await repo.save(_interaction(question="middle", days_ago=5))

        history = await repo.get_history("admin-1")
        assert [h.question for h in history] == ["recent", "middle", "old"]

    @pytest.mark.asyncio
    async def test_respects_limit(self, repo):
        for i in range(5):
            await repo.save(_interaction(question=f"q{i}", days_ago=i))

        history = await repo.get_history("admin-1", limit=3)
        assert len(history) == 3

    @pytest.mark.asyncio
    async def test_default_limit_is_20(self, repo):
        for i in range(25):
            await repo.save(_interaction(question=f"q{i}", days_ago=i))

        history = await repo.get_history("admin-1")
        assert len(history) == 20

    @pytest.mark.asyncio
    async def test_maps_all_fields(self, repo):
        now = datetime.now(timezone.utc)
        interaction = AIInteraction(
            interaction_id="11111111-1111-1111-1111-111111111111",
            user_id="admin-1",
            question="How many pets?",
            generated_sql="SELECT COUNT(*) FROM pets",
            execution_ms=42,
            response="There are 10 pets.",
            provider="groq",
            created_at=now,
        )
        await repo.save(interaction)

        history = await repo.get_history("admin-1")
        assert len(history) == 1
        result = history[0]
        assert result.interaction_id == "11111111-1111-1111-1111-111111111111"
        assert result.user_id == "admin-1"
        assert result.question == "How many pets?"
        assert result.generated_sql == "SELECT COUNT(*) FROM pets"
        assert result.execution_ms == 42
        assert result.response == "There are 10 pets."
        assert result.provider == "groq"
        assert result.created_at.replace(tzinfo=None) == now.replace(tzinfo=None)


class TestPrune:
    @pytest.mark.asyncio
    async def test_prunes_old_records(self, session_factory):
        from app.ai.infrastructure.repositories import PostgresConversationRepository

        repo = PostgresConversationRepository(
            session_factory=session_factory, retention_days=30
        )
        await repo.save(_interaction(question="old", days_ago=60))
        await repo.save(_interaction(question="recent", days_ago=10))

        deleted = repo.prune()

        assert deleted == 1
        history = await repo.get_history("admin-1")
        assert len(history) == 1
        assert history[0].question == "recent"

    @pytest.mark.asyncio
    async def test_prune_keeps_recent_records(self, session_factory):
        from app.ai.infrastructure.repositories import PostgresConversationRepository

        repo = PostgresConversationRepository(
            session_factory=session_factory, retention_days=30
        )
        await repo.save(_interaction(question="recent", days_ago=1))

        deleted = repo.prune()

        assert deleted == 0
        history = await repo.get_history("admin-1")
        assert len(history) == 1
