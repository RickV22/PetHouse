from typing import List

from pydantic import BaseModel

from app.ai.presentation.dto.history_item import HistoryItem


class HistoryResponse(BaseModel):
    items: List[HistoryItem]
    count: int
