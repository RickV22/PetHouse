from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class AskResponse(BaseModel):
    answer: str
    generated_sql: Optional[str] = None
    execution_time_ms: Optional[int] = None
    provider: str
    model: str
    conversation_id: str
    created_at: datetime
