import json
import uuid
from datetime import datetime, timezone
from typing import List

from app.ai.domain.entities import (
    AIExecutionContext,
    AIInteraction,
    AIResponse,
    AskResult,
    QueryResult,
)
from app.ai.domain.interfaces import (
    AITool,
    ConversationRepository,
    PromptTemplate,
)
from app.ai.use_cases.query_planner import QueryPlanner


class AdminAssistantUseCase:
    def __init__(
        self,
        query_planner: QueryPlanner,
        sql_query_tool: AITool,
        prompt_template: PromptTemplate,
        conversation_repository: ConversationRepository,
        provider: str = "",
        model: str = "",
        permissions: List[str] | None = None,
        max_history: int = 20,
    ) -> None:
        self._query_planner = query_planner
        self._sql_query_tool = sql_query_tool
        self._prompt_template = prompt_template
        self._conversation_repository = conversation_repository
        self._provider = provider
        self._model = model
        self._permissions = permissions or []
        self._max_history = max_history

    async def ask(self, question: str, user_id: str) -> AskResult:

        print("PASO 1 - Obteniendo historial")
        history = await self._conversation_repository.get_history(
            user_id, limit=self._max_history
        )

        print("PASO 2 - Creando contexto")
        context = AIExecutionContext(
            user_id=user_id,
            permissions=self._permissions,
            provider=self._provider,
            model=self._model,
            conversation_history=history,
            timestamp=datetime.now(timezone.utc),
        )

        print("PASO 3 - Planificando consulta")
        planned = await self._query_planner.plan_query(question, context)

        print("PASO 4 - Ejecutando SQL")
        tool_response = await self._sql_query_tool.execute(
            context,
            {"sql": planned.sql},
        )

        print("PASO 5 - Parseando resultado")
        query_result = self._parse_query_result(tool_response)

        print("PASO 6 - Formateando respuesta")
        answer = await self._query_planner.format_response(
            question,
            planned.sql,
            query_result,
            context,
        )

        is_greeting_sql = "SELECT 'greeting'" in planned.sql
        final_sql = None if is_greeting_sql else planned.sql
        final_execution_ms = None if is_greeting_sql else query_result.execution_ms

        now = datetime.now(timezone.utc)
        interaction = AIInteraction(
            interaction_id=str(uuid.uuid4()),
            user_id=user_id,
            question=question,
            generated_sql=final_sql,
            execution_ms=final_execution_ms,
            response=answer,
            provider=self._provider,
            created_at=now,
        )

        print("PASO 7 - Guardando interacción")
        await self._conversation_repository.save(interaction)

        print("PASO 8 - Finalizado")

        return AskResult(
            answer=answer,
            generated_sql=final_sql,
            execution_ms=final_execution_ms,
            provider=self._provider,
            model=self._model,
            interaction_id=interaction.interaction_id,
            created_at=now,
        )

  
    def _parse_query_result(self, response: AIResponse) -> QueryResult:
        data = json.loads(response.content)
        if "error" in data and data["error"]:
            raise RuntimeError(data["error"])

        rows_raw = data.get("rows", [])
        rows = [tuple(r) if isinstance(r, list) else (r,) for r in rows_raw]

        return QueryResult(
            columns=data.get("columns", []),
            rows=rows,
            row_count=data.get("row_count", 0),
            execution_ms=data.get("execution_ms", 0),
        )

    async def get_history(
        self, user_id: str, limit: int = 20
    ) -> List[AIInteraction]:
        capped = min(limit, self._max_history)
        return await self._conversation_repository.get_history(
            user_id, limit=capped
        )
