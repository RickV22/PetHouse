import json
import os
import sys
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.domain.entities import (
    AIExecutionContext,
    AIInteraction,
    AIRequest,
    AIResponse,
    AskResult,
    DatabaseSchema,
    QueryResult,
    TableMetadata,
)
from app.ai.domain.interfaces import (
    AIProvider,
    AITool,
    MCPClient,
    PromptTemplate,
    SchemaProvider,
    SQLValidator,
    ConversationRepository,
)
from app.ai.use_cases.query_planner import QueryPlanner
from app.ai.use_cases.admin_assistant import AdminAssistantUseCase


@pytest.fixture
def real_sql_validator():
    from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

    return SqlglotSQLValidator(
        max_rows=1000,
        execution_timeout_ms=30000,
        max_query_length=10000,
        max_join_depth=5,
    )


@pytest.fixture
def real_prompt_template():
    from app.ai.infrastructure.prompt_templates import PromptTemplateImpl

    return PromptTemplateImpl(
        sql_generation_template="Schema:\n{schema}\n\nHistory:\n{history}\n\nQ: {question}\nSQL:",
        response_formatting_template="Question: {question}\nSQL: {sql}\nResults:\n{results}\nAnswer:",
    )


@pytest.fixture
def mock_mcp_client():
    client = MagicMock(spec=MCPClient)
    client.get_schema = AsyncMock(
        return_value=DatabaseSchema(
            tables=[TableMetadata(name="pets")]
        )
    )
    client.execute_query = AsyncMock(
        return_value=QueryResult(
            columns=["id", "name"],
            rows=[(1, "Buddy"), (2, "Max")],
            row_count=2,
            execution_ms=5,
        )
    )
    return client


@pytest.fixture
def mock_ai_provider():
    provider = MagicMock(spec=AIProvider)
    provider.generate = AsyncMock()
    return provider


@pytest.fixture
def mock_schema_provider():
    provider = MagicMock(spec=SchemaProvider)
    provider.get_database_schema = AsyncMock(
        return_value=DatabaseSchema(
            tables=[TableMetadata(name="pets")]
        )
    )
    return provider


@pytest.fixture
def mock_conversation_repository():
    repo = MagicMock(spec=ConversationRepository)
    repo.get_history = AsyncMock(return_value=[])
    repo.save = AsyncMock()
    return repo


@pytest.fixture
def real_sql_query_tool(real_sql_validator, mock_mcp_client):
    from app.ai.infrastructure.sql_query_tool import SqlQueryTool

    return SqlQueryTool(
        sql_validator=real_sql_validator,
        mcp_client=mock_mcp_client,
    )


class TestFullSuccessPath:
    @pytest.mark.asyncio
    async def test_complete_pipeline_returns_ask_result(
        self, real_sql_validator, real_prompt_template,
        mock_ai_provider, mock_schema_provider,
        mock_mcp_client, mock_conversation_repository,
        real_sql_query_tool,
    ):
        mock_ai_provider.generate.side_effect = [
            AIResponse(content="SELECT * FROM pets"),
            AIResponse(content="There are 2 pets in the shelter."),
        ]

        query_planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=real_prompt_template,
            ai_provider=mock_ai_provider,
        )

        use_case = AdminAssistantUseCase(
            query_planner=query_planner,
            sql_query_tool=real_sql_query_tool,
            prompt_template=real_prompt_template,
            conversation_repository=mock_conversation_repository,
            provider="groq",
            model="llama-3.3-70b-versatile",
            permissions=["ai:assistant"],
        )

        result = await use_case.ask("List all pets", "admin-1")

        assert isinstance(result, AskResult)
        assert result.answer == "There are 2 pets in the shelter."
        assert result.generated_sql == "SELECT * FROM pets"
        assert result.execution_ms >= 0
        assert result.provider == "groq"
        assert result.model == "llama-3.3-70b-versatile"
        assert result.interaction_id is not None
        assert result.created_at is not None

    @pytest.mark.asyncio
    async def test_validates_sql_with_real_validator(
        self, real_sql_validator, real_prompt_template,
        mock_ai_provider, mock_schema_provider,
        mock_mcp_client, mock_conversation_repository,
    ):
        mock_ai_provider.generate.side_effect = [
            AIResponse(content="SELECT * FROM pets"),
            AIResponse(content="SQL is valid."),
        ]

        from app.ai.infrastructure.sql_query_tool import SqlQueryTool
        sql_tool = SqlQueryTool(
            sql_validator=real_sql_validator,
            mcp_client=mock_mcp_client,
        )

        query_planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=real_prompt_template,
            ai_provider=mock_ai_provider,
        )

        use_case = AdminAssistantUseCase(
            query_planner=query_planner,
            sql_query_tool=sql_tool,
            prompt_template=real_prompt_template,
            conversation_repository=mock_conversation_repository,
        )

        result = await use_case.ask("List all pets", "admin-1")
        assert result.generated_sql == "SELECT * FROM pets"

    @pytest.mark.asyncio
    async def test_saves_interaction_to_repository(
        self, real_sql_validator, real_prompt_template,
        mock_ai_provider, mock_schema_provider,
        mock_mcp_client, mock_conversation_repository,
        real_sql_query_tool,
    ):
        mock_ai_provider.generate.side_effect = [
            AIResponse(content="SELECT * FROM pets"),
            AIResponse(content="All pets listed."),
        ]

        query_planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=real_prompt_template,
            ai_provider=mock_ai_provider,
        )

        use_case = AdminAssistantUseCase(
            query_planner=query_planner,
            sql_query_tool=real_sql_query_tool,
            prompt_template=real_prompt_template,
            conversation_repository=mock_conversation_repository,
        )

        await use_case.ask("List all pets", "admin-1")

        mock_conversation_repository.save.assert_awaited_once()
        interaction = mock_conversation_repository.save.call_args[0][0]
        assert isinstance(interaction, AIInteraction)
        assert interaction.user_id == "admin-1"
        assert interaction.question == "List all pets"
        assert interaction.generated_sql == "SELECT * FROM pets"

    @pytest.mark.asyncio
    async def test_follow_up_uses_conversation_history(
        self, real_sql_validator, real_prompt_template,
        mock_ai_provider, mock_schema_provider,
        mock_mcp_client, mock_conversation_repository,
        real_sql_query_tool,
    ):
        mock_ai_provider.generate.side_effect = [
            AIResponse(content="SELECT * FROM pets"),
            AIResponse(content="All pets listed."),
        ]

        query_planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=real_prompt_template,
            ai_provider=mock_ai_provider,
        )

        use_case = AdminAssistantUseCase(
            query_planner=query_planner,
            sql_query_tool=real_sql_query_tool,
            prompt_template=real_prompt_template,
            conversation_repository=mock_conversation_repository,
            max_history=5,
        )

        await use_case.ask("List all pets", "admin-1")
        mock_conversation_repository.get_history.assert_awaited_with("admin-1", limit=5)

        saved = mock_conversation_repository.save.call_args[0][0]
        mock_conversation_repository.get_history.return_value = [saved]

        mock_ai_provider.generate.side_effect = [
            AIResponse(content="SELECT COUNT(*) FROM pets"),
            AIResponse(content="Count completed."),
        ]

        result2 = await use_case.ask("How many?", "admin-1")
        assert result2.generated_sql == "SELECT COUNT(*) FROM pets"


class TestProviderFailure:
    @pytest.mark.asyncio
    async def test_provider_timeout(
        self, mock_schema_provider, real_prompt_template,
        mock_conversation_repository, real_sql_query_tool,
    ):
        mock_ai_provider = MagicMock(spec=AIProvider)
        mock_ai_provider.generate = AsyncMock(
            side_effect=TimeoutError("Groq timed out")
        )

        query_planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=real_prompt_template,
            ai_provider=mock_ai_provider,
        )

        use_case = AdminAssistantUseCase(
            query_planner=query_planner,
            sql_query_tool=real_sql_query_tool,
            prompt_template=real_prompt_template,
            conversation_repository=mock_conversation_repository,
        )

        with pytest.raises(TimeoutError, match="Groq timed out"):
            await use_case.ask("List all pets", "admin-1")

    @pytest.mark.asyncio
    async def test_provider_unavailable(
        self, mock_schema_provider, real_prompt_template,
        mock_conversation_repository, real_sql_query_tool,
    ):
        mock_ai_provider = MagicMock(spec=AIProvider)
        mock_ai_provider.generate = AsyncMock(
            side_effect=ConnectionError("Groq unavailable")
        )

        query_planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=real_prompt_template,
            ai_provider=mock_ai_provider,
        )

        use_case = AdminAssistantUseCase(
            query_planner=query_planner,
            sql_query_tool=real_sql_query_tool,
            prompt_template=real_prompt_template,
            conversation_repository=mock_conversation_repository,
        )

        with pytest.raises(ConnectionError, match="Groq unavailable"):
            await use_case.ask("List all pets", "admin-1")


class TestSqlValidationFailure:
    @pytest.mark.asyncio
    async def test_invalid_sql_rejected_by_validator(
        self, real_sql_validator, real_prompt_template,
        mock_ai_provider, mock_schema_provider,
        mock_mcp_client, mock_conversation_repository,
    ):
        mock_ai_provider.generate.return_value = AIResponse(
            content="DROP TABLE pets"
        )

        from app.ai.infrastructure.sql_query_tool import SqlQueryTool
        from app.ai.domain.exceptions import SQLValidationError

        sql_tool = SqlQueryTool(
            sql_validator=real_sql_validator,
            mcp_client=mock_mcp_client,
        )

        query_planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=real_prompt_template,
            ai_provider=mock_ai_provider,
        )

        use_case = AdminAssistantUseCase(
            query_planner=query_planner,
            sql_query_tool=sql_tool,
            prompt_template=real_prompt_template,
            conversation_repository=mock_conversation_repository,
        )

        with pytest.raises(SQLValidationError) as exc:
            await use_case.ask("Delete all pets", "admin-1")
        assert "DROP" in str(exc.value) or "SELECT" in str(exc.value)


class TestMCPFailure:
    @pytest.mark.asyncio
    async def test_mcp_timeout(
        self, real_sql_validator, real_prompt_template,
        mock_ai_provider, mock_schema_provider,
        mock_conversation_repository,
    ):
        mock_mcp_client = MagicMock(spec=MCPClient)
        mock_mcp_client.get_schema = AsyncMock(
            return_value=DatabaseSchema(tables=[TableMetadata(name="pets")])
        )
        mock_mcp_client.execute_query = AsyncMock(
            side_effect=TimeoutError("MCP query timed out")
        )

        from app.ai.infrastructure.sql_query_tool import SqlQueryTool
        sql_tool = SqlQueryTool(
            sql_validator=real_sql_validator,
            mcp_client=mock_mcp_client,
        )

        mock_ai_provider.generate.side_effect = [
            AIResponse(content="SELECT * FROM pets"),
            AIResponse(content="Query executed."),
        ]

        query_planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=real_prompt_template,
            ai_provider=mock_ai_provider,
        )

        use_case = AdminAssistantUseCase(
            query_planner=query_planner,
            sql_query_tool=sql_tool,
            prompt_template=real_prompt_template,
            conversation_repository=mock_conversation_repository,
        )

        with pytest.raises(TimeoutError, match="MCP query timed out"):
            await use_case.ask("List all pets", "admin-1")

    @pytest.mark.asyncio
    async def test_mcp_unavailable(
        self, real_sql_validator, real_prompt_template,
        mock_ai_provider, mock_conversation_repository,
    ):
        failing_schema_provider = MagicMock(spec=SchemaProvider)
        failing_schema_provider.get_database_schema = AsyncMock(
            side_effect=ConnectionError("MCP unavailable")
        )

        query_planner = QueryPlanner(
            schema_provider=failing_schema_provider,
            prompt_template=real_prompt_template,
            ai_provider=mock_ai_provider,
        )

        use_case = AdminAssistantUseCase(
            query_planner=query_planner,
            sql_query_tool=MagicMock(spec=AITool),
            prompt_template=real_prompt_template,
            conversation_repository=mock_conversation_repository,
        )

        with pytest.raises(ConnectionError, match="MCP unavailable"):
            await use_case.ask("List all pets", "admin-1")


class TestRepositoryFailure:
    @pytest.mark.asyncio
    async def test_get_history_failure_propagates(
        self, real_sql_validator, real_prompt_template,
        mock_ai_provider, mock_schema_provider,
        real_sql_query_tool,
    ):
        repo = MagicMock(spec=ConversationRepository)
        repo.get_history = AsyncMock(
            side_effect=RuntimeError("Database connection lost")
        )
        repo.save = AsyncMock()

        mock_ai_provider.generate.side_effect = [
            AIResponse(content="SELECT * FROM pets"),
            AIResponse(content="Answer."),
        ]

        query_planner = QueryPlanner(
            schema_provider=mock_schema_provider,
            prompt_template=real_prompt_template,
            ai_provider=mock_ai_provider,
        )

        use_case = AdminAssistantUseCase(
            query_planner=query_planner,
            sql_query_tool=real_sql_query_tool,
            prompt_template=real_prompt_template,
            conversation_repository=repo,
        )

        with pytest.raises(RuntimeError, match="Database connection lost"):
            await use_case.ask("List all pets", "admin-1")
