import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.domain.entities import (
    AIExecutionContext,
    AIRequest,
    AIResponse,
    DatabaseSchema,
    QueryResult,
    TableMetadata,
)


@pytest.fixture
def mock_schema_provider():
    provider = MagicMock()
    provider.get_database_schema = AsyncMock(
        return_value=DatabaseSchema(tables=[TableMetadata(name="pets")])
    )
    return provider


@pytest.fixture
def mock_prompt_template():
    template = MagicMock()
    template.render_sql_prompt = MagicMock(
        return_value="You are a SQL expert...\n\nQuestion: list all pets\nSQL:"
    )
    template.render_response_prompt = MagicMock(
        return_value="Given the question...\n\nAnswer:"
    )
    return template


@pytest.fixture
def mock_ai_provider():
    provider = MagicMock()
    provider.generate = AsyncMock(
        return_value=AIResponse(content="SELECT * FROM pets")
    )
    return provider


@pytest.fixture
def context():
    return AIExecutionContext(user_id="admin-1")


class TestPlanQuery:
    @pytest.mark.asyncio
    async def test_returns_planned_query(
        self, mock_schema_provider, mock_prompt_template, mock_ai_provider, context
    ):
        from app.ai.use_cases.query_planner import QueryPlanner

        planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=mock_prompt_template,
            ai_provider=mock_ai_provider,
        )
        result = await planner.plan_query("list all pets", context)

        assert result.sql == "SELECT * FROM pets"
        assert result.schema.tables[0].name == "pets"
        assert "You are a SQL expert" in result.prompt

    @pytest.mark.asyncio
    async def test_retrieves_schema(
        self, mock_schema_provider, mock_prompt_template, mock_ai_provider, context
    ):
        from app.ai.use_cases.query_planner import QueryPlanner

        planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=mock_prompt_template,
            ai_provider=mock_ai_provider,
        )
        await planner.plan_query("list all pets", context)

        mock_schema_provider.get_database_schema.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_sets_schema_on_context(
        self, mock_schema_provider, mock_prompt_template, mock_ai_provider, context
    ):
        from app.ai.use_cases.query_planner import QueryPlanner

        planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=mock_prompt_template,
            ai_provider=mock_ai_provider,
        )
        await planner.plan_query("list all pets", context)

        assert context.database_schema is not None
        assert context.database_schema.tables[0].name == "pets"

    @pytest.mark.asyncio
    async def test_renders_sql_prompt(
        self, mock_schema_provider, mock_prompt_template, mock_ai_provider, context
    ):
        from app.ai.use_cases.query_planner import QueryPlanner

        planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=mock_prompt_template,
            ai_provider=mock_ai_provider,
        )
        await planner.plan_query("list all pets", context)

        mock_prompt_template.render_sql_prompt.assert_called_once_with(
            question="list all pets",
            schema=mock_schema_provider.get_database_schema.return_value,
            context=context,
        )

    @pytest.mark.asyncio
    async def test_calls_ai_provider(
        self, mock_schema_provider, mock_prompt_template, mock_ai_provider, context
    ):
        from app.ai.use_cases.query_planner import QueryPlanner

        planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=mock_prompt_template,
            ai_provider=mock_ai_provider,
        )
        await planner.plan_query("list all pets", context)

        expected_prompt = mock_prompt_template.render_sql_prompt.return_value
        mock_ai_provider.generate.assert_awaited_once()
        call_args = mock_ai_provider.generate.call_args[0][0]
        assert isinstance(call_args, AIRequest)
        assert call_args.prompt == expected_prompt

    @pytest.mark.asyncio
    async def test_strips_sql_markdown_fences(
        self, mock_schema_provider, mock_prompt_template, context
    ):
        from app.ai.use_cases.query_planner import QueryPlanner

        provider = MagicMock()
        provider.generate = AsyncMock(
            return_value=AIResponse(content="```sql\nSELECT * FROM pets\n```")
        )
        planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=mock_prompt_template,
            ai_provider=provider,
        )
        result = await planner.plan_query("list all pets", context)

        assert result.sql == "SELECT * FROM pets"

    @pytest.mark.asyncio
    async def test_strips_plain_markdown_fences(
        self, mock_schema_provider, mock_prompt_template, context
    ):
        from app.ai.use_cases.query_planner import QueryPlanner

        provider = MagicMock()
        provider.generate = AsyncMock(
            return_value=AIResponse(content="```\nSELECT * FROM pets\n```")
        )
        planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=mock_prompt_template,
            ai_provider=provider,
        )
        result = await planner.plan_query("list all pets", context)

        assert result.sql == "SELECT * FROM pets"


class TestFormatResponse:
    @pytest.mark.asyncio
    async def test_returns_formatted_response(
        self, mock_schema_provider, mock_prompt_template, mock_ai_provider, context
    ):
        from app.ai.use_cases.query_planner import QueryPlanner

        result = QueryResult(columns=["id"], rows=[(1,)], row_count=1)
        mock_ai_provider.generate.return_value = AIResponse(
            content="There is 1 pet."
        )
        planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=mock_prompt_template,
            ai_provider=mock_ai_provider,
        )
        answer = await planner.format_response(
            "How many pets?", "SELECT COUNT(*) FROM pets", result, context
        )

        assert answer == "There is 1 pet."

    @pytest.mark.asyncio
    async def test_renders_response_prompt(
        self, mock_schema_provider, mock_prompt_template, mock_ai_provider, context
    ):
        from app.ai.use_cases.query_planner import QueryPlanner

        result = QueryResult()
        planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=mock_prompt_template,
            ai_provider=mock_ai_provider,
        )
        await planner.format_response(
            "How many?", "SELECT 1", result, context
        )

        mock_prompt_template.render_response_prompt.assert_called_once_with(
            question="How many?",
            sql="SELECT 1",
            result=result,
            context=context,
        )

    @pytest.mark.asyncio
    async def test_passes_prompt_to_ai(
        self, mock_schema_provider, mock_prompt_template, mock_ai_provider, context
    ):
        from app.ai.use_cases.query_planner import QueryPlanner

        result = QueryResult()
        planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=mock_prompt_template,
            ai_provider=mock_ai_provider,
        )
        await planner.format_response(
            "How many?", "SELECT 1", result, context
        )

        expected_prompt = mock_prompt_template.render_response_prompt.return_value
        call_args = mock_ai_provider.generate.call_args[0][0]
        assert isinstance(call_args, AIRequest)
        assert call_args.prompt == expected_prompt


class TestEdgeCases:
    @pytest.mark.asyncio
    async def test_empty_ai_response(
        self, mock_schema_provider, mock_prompt_template, context
    ):
        from app.ai.use_cases.query_planner import QueryPlanner

        provider = MagicMock()
        provider.generate = AsyncMock(return_value=AIResponse(content=""))
        planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=mock_prompt_template,
            ai_provider=provider,
        )
        result = await planner.plan_query("test", context)

        assert result.sql == ""

    @pytest.mark.asyncio
    async def test_no_fences(
        self, mock_schema_provider, mock_prompt_template, context
    ):
        from app.ai.use_cases.query_planner import QueryPlanner

        provider = MagicMock()
        provider.generate = AsyncMock(
            return_value=AIResponse(content="SELECT * FROM pets")
        )
        planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=mock_prompt_template,
            ai_provider=provider,
        )
        result = await planner.plan_query("test", context)

        assert result.sql == "SELECT * FROM pets"

    @pytest.mark.asyncio
    async def test_ai_provider_error_propagates(
        self, mock_schema_provider, mock_prompt_template, context
    ):
        from app.ai.use_cases.query_planner import QueryPlanner

        provider = MagicMock()
        provider.generate = AsyncMock(side_effect=RuntimeError("API failed"))
        planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=mock_prompt_template,
            ai_provider=provider,
        )
        with pytest.raises(RuntimeError, match="API failed"):
            await planner.plan_query("test", context)

    @pytest.mark.asyncio
    async def test_schema_provider_error_propagates(
        self, mock_prompt_template, mock_ai_provider, context
    ):
        from app.ai.use_cases.query_planner import QueryPlanner

        provider = MagicMock()
        provider.get_database_schema = AsyncMock(
            side_effect=ConnectionError("MCP down")
        )
        planner = QueryPlanner(
            schema_provider=provider,
            prompt_template=mock_prompt_template,
            ai_provider=mock_ai_provider,
        )
        with pytest.raises(ConnectionError, match="MCP down"):
            await planner.plan_query("test", context)
