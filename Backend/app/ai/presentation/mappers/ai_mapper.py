from typing import List

from app.ai.domain.entities import AIInteraction, AskResult
from app.ai.presentation.dto.ask_response import AskResponse
from app.ai.presentation.dto.history_item import HistoryItem
from app.ai.presentation.dto.history_response import HistoryResponse


def to_ask_response(result: AskResult) -> AskResponse:
    return AskResponse(
        answer=result.answer,
        generated_sql=result.generated_sql,
        execution_time_ms=result.execution_ms,
        provider=result.provider,
        model=result.model,
        conversation_id=result.interaction_id,
        created_at=result.created_at,
    )


def to_history_item(interaction: AIInteraction) -> HistoryItem:
    return HistoryItem(
        id=interaction.interaction_id,
        question=interaction.question,
        answer=interaction.response,
        generated_sql=interaction.generated_sql,
        execution_time_ms=interaction.execution_ms,
        provider=interaction.provider,
        created_at=interaction.created_at,
    )


def to_history_response(interactions: List[AIInteraction]) -> HistoryResponse:
    items = [to_history_item(i) for i in interactions]
    return HistoryResponse(items=items, count=len(items))
