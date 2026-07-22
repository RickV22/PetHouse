import json
from typing import Any, Dict

from app.ai.domain.entities import AIExecutionContext, AIResponse, QueryResult
from app.ai.domain.exceptions import SQLValidationError
from app.ai.domain.interfaces import AITool, MCPClient, SQLValidator


class SqlQueryTool(AITool):
    def __init__(
        self,
        sql_validator: SQLValidator,
        mcp_client: MCPClient,
    ) -> None:
        self._sql_validator = sql_validator
        self._mcp_client = mcp_client

    async def execute(
        self, context: AIExecutionContext, params: Dict[str, Any]
    ) -> AIResponse:
        sql = params.get("sql", "")
        if not sql:
            return AIResponse(
                content=json.dumps({
                    "error": "No SQL provided",
                    "columns": [],
                    "rows": [],
                    "row_count": 0,
                    "execution_ms": 0,
                })
            )

        validation = self._sql_validator.validate(sql)
        if not validation.is_valid:
            raise SQLValidationError(
                validation.error or "SQL validation failed"
            )

        result = await self._mcp_client.execute_query(sql)

        return AIResponse(
            content=json.dumps(
                {
                    "columns": result.columns,
                    "rows": [list(r) for r in result.rows],
                    "row_count": result.row_count,
                    "execution_ms": result.execution_ms,
                },
                default=str,
            )
        )

    def description(self) -> str:
        return (
            "Execute read-only SQL queries against the business database. "
            "Only SELECT statements are permitted; all write operations are blocked."
        )

    def parameters(self) -> Dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "sql": {
                    "type": "string",
                    "description": "The SQL SELECT statement to execute",
                },
            },
            "required": ["sql"],
        }
