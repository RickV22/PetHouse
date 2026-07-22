from datetime import datetime, timezone
from typing import Callable, List, Optional
from uuid import UUID

from sqlalchemy.orm import Session

from app.ai.domain.entities import AIInteraction
from app.ai.domain.interfaces import ConversationRepository
from app.models.ai_interaction_model import AIInteractionModel


class PostgresConversationRepository(ConversationRepository):
    def __init__(
        self,
        session_factory: Callable[[], Session],
        retention_days: int = 90,
    ) -> None:
        self._session_factory = session_factory
        self._retention_days = retention_days

    async def save(self, interaction: AIInteraction) -> None:
        model = AIInteractionModel(
            id=UUID(interaction.interaction_id),
            user_id=interaction.user_id,
            question=interaction.question,
            generated_sql=interaction.generated_sql,
            execution_ms=interaction.execution_ms,
            response=interaction.response,
            provider=interaction.provider,
            created_at=interaction.created_at
            or datetime.now(timezone.utc),
        )
        session = self._session_factory()
        try:
            session.add(model)
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    async def get_history(
        self, user_id: str, limit: int = 20
    ) -> List[AIInteraction]:
        session = self._session_factory()
        try:
            rows = (
                session.query(AIInteractionModel)
                .filter(AIInteractionModel.user_id == user_id)
                .order_by(AIInteractionModel.created_at.desc())
                .limit(limit)
                .all()
            )
            return [self._to_domain(row) for row in rows]
        finally:
            session.close()

    def prune(self) -> int:
        cutoff = _utc_now() - _days(self._retention_days)
        session = self._session_factory()
        try:
            deleted = (
                session.query(AIInteractionModel)
                .filter(AIInteractionModel.created_at < cutoff)
                .delete()
            )
            session.commit()
            return deleted
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def _to_domain(self, model: AIInteractionModel) -> AIInteraction:
        return AIInteraction(
            interaction_id=str(model.id),
            user_id=model.user_id,
            question=model.question,
            generated_sql=model.generated_sql,
            execution_ms=model.execution_ms,
            response=model.response,
            provider=model.provider,
            created_at=model.created_at,
        )


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _days(n: int) -> object:
    from datetime import timedelta
    return timedelta(days=n)
