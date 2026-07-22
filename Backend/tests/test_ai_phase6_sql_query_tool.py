import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.domain.entities import AIExecutionContext, QueryResult


@pytest.fixture
def mock_sql_validator():
    validator = MagicMock()
    validator.validate = MagicMock()
    return validator


@pytest.fixture
def mock_mcp_client():
    client = MagicMock()
    client.execute_query = AsyncMock()
    return client


@pytest.fixture
def context():
    return AIExecutionContext(user_id="admin-1")


class TestSqlQueryTool:
    def _make_tool(self, sql_validator=None, mcp_client=None):
        from app.ai.infrastructure.sql_query_tool import SqlQueryTool

        if sql_validator is None:
            sql_validator = MagicMock()
            sql_validator.validate = MagicMock()
        if mcp_client is None:
            mcp_client = MagicMock()
            mcp_client.execute_query = AsyncMock()
        return SqlQueryTool(
            sql_validator=sql_validator,
            mcp_client=mcp_client,
        )

    @pytest.mark.asyncio
    async def test_execute_success(
        self, mock_sql_validator, mock_mcp_client, context
    ):
        from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

        validator = SqlglotSQLValidator()
        mock_mcp_client.execute_query.return_value = QueryResult(
            columns=["id", "name"],
            rows=[(1, "Buddy"), (2, "Whiskers")],
            row_count=2,
            execution_ms=5,
        )

        tool = self._make_tool(sql_validator=validator, mcp_client=mock_mcp_client)
        result = await tool.execute(context, {"sql": "SELECT * FROM pets"})

        assert isinstance(result.content, str)
        data = json.loads(result.content)
        assert data["columns"] == ["id", "name"]
        assert data["rows"] == [[1, "Buddy"], [2, "Whiskers"]]
        assert data["row_count"] == 2
        assert data["execution_ms"] == 5

    @pytest.mark.asyncio
    async def test_validation_failure_raises_error(
        self, mock_sql_validator, mock_mcp_client, context
    ):
        from app.ai.domain.exceptions import SQLValidationError
        from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

        validator = SqlglotSQLValidator()
        tool = self._make_tool(sql_validator=validator, mcp_client=mock_mcp_client)

        with pytest.raises(SQLValidationError, match="SELECT"):
            await tool.execute(context, {"sql": "DROP TABLE pets"})

        mock_mcp_client.execute_query.assert_not_called()

    @pytest.mark.asyncio
    async def test_empty_sql_returns_error_json(
        self, mock_sql_validator, mock_mcp_client, context
    ):
        tool = self._make_tool(
            sql_validator=mock_sql_validator,
            mcp_client=mock_mcp_client,
        )
        result = await tool.execute(context, {"sql": ""})

        data = json.loads(result.content)
        assert data["error"] == "No SQL provided"

        mock_sql_validator.validate.assert_not_called()
        mock_mcp_client.execute_query.assert_not_called()

    @pytest.mark.asyncio
    async def test_missing_sql_param_returns_error_json(
        self, mock_sql_validator, mock_mcp_client, context
    ):
        tool = self._make_tool(
            sql_validator=mock_sql_validator,
            mcp_client=mock_mcp_client,
        )
        result = await tool.execute(context, {})

        data = json.loads(result.content)
        assert data["error"] == "No SQL provided"

    @pytest.mark.asyncio
    async def test_execution_error_propagates(
        self, mock_sql_validator, mock_mcp_client, context
    ):
        from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

        validator = SqlglotSQLValidator()
        mock_mcp_client.execute_query.side_effect = RuntimeError("MCP failed")

        tool = self._make_tool(sql_validator=validator, mcp_client=mock_mcp_client)
        with pytest.raises(RuntimeError, match="MCP failed"):
            await tool.execute(context, {"sql": "SELECT 1"})

    @pytest.mark.asyncio
    async def test_delegates_to_mcp_client(
        self, mock_sql_validator, mock_mcp_client, context
    ):
        from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

        validator = SqlglotSQLValidator()
        mock_mcp_client.execute_query.return_value = QueryResult()

        tool = self._make_tool(sql_validator=validator, mcp_client=mock_mcp_client)
        await tool.execute(context, {"sql": "SELECT * FROM pets"})

        mock_mcp_client.execute_query.assert_awaited_once_with("SELECT * FROM pets")


class TestSqlQueryToolMetadata:
    def _make_tool(self):
        from app.ai.infrastructure.sql_query_tool import SqlQueryTool

        return SqlQueryTool(
            sql_validator=MagicMock(),
            mcp_client=MagicMock(),
        )

    def test_description(self):
        tool = self._make_tool()
        desc = tool.description()
        assert "read-only" in desc.lower()
        assert "SELECT" in desc

    def test_parameters(self):
        tool = self._make_tool()
        params = tool.parameters()
        assert params["type"] == "object"
        assert "sql" in params["properties"]
        assert params["properties"]["sql"]["type"] == "string"
        assert "required" in params
        assert "sql" in params["required"]
