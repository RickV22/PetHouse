import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String, Text, Uuid

from app.db.base import Base


class AIInteractionModel(Base):
    __tablename__ = "ai_interactions"

    id = Column(
        Uuid(),
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id = Column(String(255), nullable=False, index=True)
    question = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=True)
    execution_ms = Column(Integer, nullable=True)
    response = Column(Text, nullable=True)
    provider = Column(String(50), nullable=False)
    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
