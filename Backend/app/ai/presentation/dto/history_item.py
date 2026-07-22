from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class HistoryItem(BaseModel):
    id: str
    question: str
    answer: Optional[str] = None
    generated_sql: Optional[str] = None
    execution_time_ms: Optional[int] = None
    provider: str
    created_at: datetime
