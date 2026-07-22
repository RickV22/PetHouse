import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.domain.entities import (
    AIExecutionContext,
    AIInteraction,
    AIResponse,
    AskResult,
    PlannedQuery,
    QueryResult,
)


@pytest.fixture
def mock_query_planner():
    planner = MagicMock()
    planner.plan_query = AsyncMock(
        return_value=PlannedQuery(
            sql="SELECT * FROM pets",
            schema=MagicMock(),
            prompt="You are a SQL expert...",
        )
    )
    planner.format_response = AsyncMock(
        return_value="There are 3 pets in the shelter."
    )
    return planner


@pytest.fixture
def mock_sql_query_tool():
    tool = MagicMock()
    tool.execute = AsyncMock(
        return_value=AIResponse(
            content=json.dumps({
                "columns": ["id", "name"],
                "rows": [[1, "Buddy"], [2, "Whiskers"], [3, "Max"]],
                "row_count": 3,
                "execution_ms": 5,
            })
        )
    )
    return tool


@pytest.fixture
def mock_prompt_template():
    return MagicMock()


@pytest.fixture
def mock_conversation_repository():
    repo = MagicMock()
    repo.get_history = AsyncMock(return_value=[])
    repo.save = AsyncMock()
    return repo


class TestAdminAssistantUseCase:
    def _make_use_case(
        self,
        query_planner=None,
        sql_query_tool=None,
        prompt_template=None,
        conversation_repository=None,
    ):
        from app.ai.use_cases.admin_assistant import AdminAssistantUseCase

        return AdminAssistantUseCase(
            query_planner=query_planner or MagicMock(),
            sql_query_tool=sql_query_tool or MagicMock(),
            prompt_template=prompt_template or MagicMock(),
            conversation_repository=conversation_repository or MagicMock(),
            provider="groq",
            model="llama-3.3-70b-versatile",
            permissions=["ai:assistant"],
        )

    @pytest.mark.asyncio
    async def test_returns_ai_response(
        self,
        mock_query_planner,
        mock_sql_query_tool,
        mock_prompt_template,
        mock_conversation_repository,
    ):
        use_case = self._make_use_case(
            query_planner=mock_query_planner,
            sql_query_tool=mock_sql_query_tool,
            prompt_template=mock_prompt_template,
            conversation_repository=mock_conversation_repository,
        )
        result = await use_case.ask("How many pets?", "admin-1")

        assert isinstance(result, AskResult)
        assert result.answer == "There are 3 pets in the shelter."
        assert result.generated_sql == "SELECT * FROM pets"
        assert result.execution_ms == 5
        assert result.provider == "groq"
        assert result.model == "llama-3.3-70b-versatile"
        assert result.interaction_id is not None
        assert result.created_at is not None

    @pytest.mark.asyncio
    async def test_retrieves_conversation_history(
        self,
        mock_query_planner,
        mock_sql_query_tool,
        mock_prompt_template,
        mock_conversation_repository,
    ):
        use_case = self._make_use_case(
            query_planner=mock_query_planner,
            sql_query_tool=mock_sql_query_tool,
            prompt_template=mock_prompt_template,
            conversation_repository=mock_conversation_repository,
        )
        await use_case.ask("How many pets?", "admin-1")

        mock_conversation_repository.get_history.assert_awaited_once_with(
            "admin-1", limit=20
        )

    @pytest.mark.asyncio
    async def test_builds_context_with_history(
        self,
        mock_query_planner,
        mock_sql_query_tool,
        mock_prompt_template,
        mock_conversation_repository,
    ):
        expected_history = [
            AIInteraction(
                interaction_id="prev-1",
                user_id="admin-1",
                question="test",
                provider="groq",
            )
        ]
        mock_conversation_repository.get_history.return_value = expected_history

        use_case = self._make_use_case(
            query_planner=mock_query_planner,
            sql_query_tool=mock_sql_query_tool,
            prompt_template=mock_prompt_template,
            conversation_repository=mock_conversation_repository,
        )
        await use_case.ask("How many pets?", "admin-1")

        context_arg = mock_query_planner.plan_query.call_args[0][1]
        assert isinstance(context_arg, AIExecutionContext)
        assert context_arg.user_id == "admin-1"
        assert context_arg.provider == "groq"
        assert context_arg.model == "llama-3.3-70b-versatile"
        assert context_arg.permissions == ["ai:assistant"]
        assert context_arg.conversation_history == expected_history
        assert context_arg.timestamp is not None

    @pytest.mark.asyncio
    async def test_plans_query_with_question(
        self,
        mock_query_planner,
        mock_sql_query_tool,
        mock_prompt_template,
        mock_conversation_repository,
    ):
        use_case = self._make_use_case(
            query_planner=mock_query_planner,
            sql_query_tool=mock_sql_query_tool,
            prompt_template=mock_prompt_template,
            conversation_repository=mock_conversation_repository,
        )
        await use_case.ask("How many pets?", "admin-1")

        mock_query_planner.plan_query.assert_awaited_once()
        question_arg = mock_query_planner.plan_query.call_args[0][0]
        assert question_arg == "How many pets?"

    @pytest.mark.asyncio
    async def test_passes_sql_to_tool(
        self,
        mock_query_planner,
        mock_sql_query_tool,
        mock_prompt_template,
        mock_conversation_repository,
    ):
        mock_query_planner.plan_query.return_value = PlannedQuery(
            sql="SELECT COUNT(*) FROM pets",
            schema=MagicMock(),
            prompt="prompt",
        )

        use_case = self._make_use_case(
            query_planner=mock_query_planner,
            sql_query_tool=mock_sql_query_tool,
            prompt_template=mock_prompt_template,
            conversation_repository=mock_conversation_repository,
        )
        await use_case.ask("Count?", "admin-1")

        mock_sql_query_tool.execute.assert_awaited_once()
        params_arg = mock_sql_query_tool.execute.call_args[0][1]
        assert params_arg == {"sql": "SELECT COUNT(*) FROM pets"}

    @pytest.mark.asyncio
    async def test_formats_response(
        self,
        mock_query_planner,
        mock_sql_query_tool,
        mock_prompt_template,
        mock_conversation_repository,
    ):
        use_case = self._make_use_case(
            query_planner=mock_query_planner,
            sql_query_tool=mock_sql_query_tool,
            prompt_template=mock_prompt_template,
            conversation_repository=mock_conversation_repository,
        )
        await use_case.ask("How many pets?", "admin-1")

        mock_query_planner.format_response.assert_awaited_once()
        call_args = mock_query_planner.format_response.call_args[0]
        assert call_args[0] == "How many pets?"
        assert call_args[1] == "SELECT * FROM pets"
        assert isinstance(call_args[2], QueryResult)
        assert call_args[2].row_count == 3

    @pytest.mark.asyncio
    async def test_saves_interaction(
        self,
        mock_query_planner,
        mock_sql_query_tool,
        mock_prompt_template,
        mock_conversation_repository,
    ):
        use_case = self._make_use_case(
            query_planner=mock_query_planner,
            sql_query_tool=mock_sql_query_tool,
            prompt_template=mock_prompt_template,
            conversation_repository=mock_conversation_repository,
        )
        await use_case.ask("How many pets?", "admin-1")

        mock_conversation_repository.save.assert_awaited_once()
        interaction = mock_conversation_repository.save.call_args[0][0]
        assert isinstance(interaction, AIInteraction)
        assert interaction.user_id == "admin-1"
        assert interaction.question == "How many pets?"
        assert interaction.generated_sql == "SELECT * FROM pets"
        assert interaction.execution_ms == 5
        assert interaction.response == "There are 3 pets in the shelter."
        assert interaction.provider == "groq"
        assert interaction.created_at is not None

    @pytest.mark.asyncio
    async def test_saves_interaction_on_tool_error(
        self,
        mock_query_planner,
        mock_sql_query_tool,
        mock_prompt_template,
        mock_conversation_repository,
    ):
        mock_sql_query_tool.execute.side_effect = RuntimeError("MCP failed")

        use_case = self._make_use_case(
            query_planner=mock_query_planner,
            sql_query_tool=mock_sql_query_tool,
            prompt_template=mock_prompt_template,
            conversation_repository=mock_conversation_repository,
        )
        with pytest.raises(RuntimeError, match="MCP failed"):
            await use_case.ask("How many?", "admin-1")

        mock_conversation_repository.save.assert_not_called()


    @pytest.mark.asyncio
    async def test_passes_max_history_to_repository(
        self,
        mock_query_planner,
        mock_sql_query_tool,
        mock_prompt_template,
        mock_conversation_repository,
    ):
        from app.ai.use_cases.admin_assistant import AdminAssistantUseCase

        use_case = AdminAssistantUseCase(
            query_planner=mock_query_planner,
            sql_query_tool=mock_sql_query_tool,
            prompt_template=mock_prompt_template,
            conversation_repository=mock_conversation_repository,
            provider="groq",
            model="llama-3.3-70b-versatile",
            max_history=5,
        )
        await use_case.ask("Hello?", "admin-1")

        mock_conversation_repository.get_history.assert_awaited_once_with(
            "admin-1", limit=5
        )

    @pytest.mark.asyncio
    async def test_default_max_history_is_20(
        self,
        mock_query_planner,
        mock_sql_query_tool,
        mock_prompt_template,
        mock_conversation_repository,
    ):
        from app.ai.use_cases.admin_assistant import AdminAssistantUseCase

        use_case = AdminAssistantUseCase(
            query_planner=mock_query_planner,
            sql_query_tool=mock_sql_query_tool,
            prompt_template=mock_prompt_template,
            conversation_repository=mock_conversation_repository,
        )
        await use_case.ask("Hello?", "admin-1")

        mock_conversation_repository.get_history.assert_awaited_once_with(
            "admin-1", limit=20
        )


class TestAdminAssistantUseCaseDefaults:
    def test_default_permissions_empty(self):
        from app.ai.use_cases.admin_assistant import AdminAssistantUseCase

        use_case = AdminAssistantUseCase(
            query_planner=MagicMock(),
            sql_query_tool=MagicMock(),
            prompt_template=MagicMock(),
            conversation_repository=MagicMock(),
        )
        assert use_case._permissions == []
