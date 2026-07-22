import os
import sys
from datetime import datetime, timezone
from typing import List

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.domain.entities import (
    AIExecutionContext,
    AIInteraction,
    ColumnMetadata,
    DatabaseSchema,
    QueryResult,
    TableMetadata,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def schema():
    return DatabaseSchema(
        tables=[
            TableMetadata(
                name="pets",
                description="Pet records",
                columns=[
                    ColumnMetadata(
                        name="id",
                        type="INTEGER",
                        nullable=False,
                        is_primary_key=True,
                    ),
                    ColumnMetadata(
                        name="name",
                        type="VARCHAR(255)",
                        nullable=False,
                    ),
                    ColumnMetadata(
                        name="species",
                        type="VARCHAR(100)",
                        nullable=True,
                        default_value="'Dog'",
                    ),
                    ColumnMetadata(
                        name="owner_id",
                        type="INTEGER",
                        nullable=True,
                        foreign_key="users(id)",
                    ),
                ],
            ),
            TableMetadata(
                name="users",
                description=None,
                columns=[
                    ColumnMetadata(
                        name="id",
                        type="INTEGER",
                        nullable=False,
                        is_primary_key=True,
                    ),
                    ColumnMetadata(
                        name="email",
                        type="VARCHAR(255)",
                        nullable=False,
                    ),
                ],
            ),
        ]
    )


@pytest.fixture
def empty_schema():
    return DatabaseSchema(tables=[])


@pytest.fixture
def context():
    return AIExecutionContext(
        user_id="admin-1",
        conversation_history=[],
        timestamp=datetime(2026, 7, 21, 12, 0, 0, tzinfo=timezone.utc),
    )


@pytest.fixture
def context_with_history():
    return AIExecutionContext(
        user_id="admin-1",
        conversation_history=[
            AIInteraction(
                interaction_id="1",
                user_id="admin-1",
                question="Show me all dogs",
                generated_sql="SELECT * FROM pets WHERE species = 'Dog'",
                response="There are 5 dogs in the shelter.",
                provider="groq",
                created_at=datetime(2026, 7, 21, 11, 0, 0, tzinfo=timezone.utc),
            ),
            AIInteraction(
                interaction_id="2",
                user_id="admin-1",
                question="How many are adopted?",
                generated_sql="SELECT COUNT(*) FROM pets WHERE adopted_at IS NOT NULL",
                response="3 dogs have been adopted.",
                provider="groq",
                created_at=datetime(2026, 7, 21, 11, 5, 0, tzinfo=timezone.utc),
            ),
        ],
    )


@pytest.fixture
def query_result():
    return QueryResult(
        columns=["id", "name", "species"],
        rows=[(1, "Buddy", "Dog"), (2, "Whiskers", "Cat")],
        row_count=2,
        execution_ms=5,
    )


@pytest.fixture
def empty_result():
    return QueryResult()


# ---------------------------------------------------------------------------
# SQL prompt rendering
# ---------------------------------------------------------------------------


class TestRenderSqlPrompt:
    def _make_prompt(self, sql_template: str = "", response_template: str = ""):
        from app.ai.infrastructure.prompt_templates import PromptTemplateImpl

        return PromptTemplateImpl(
            sql_generation_template=sql_template,
            response_formatting_template=response_template,
        )

    def test_renders_schema_and_question(self, schema, context):
        prompt = self._make_prompt(
            sql_template="Schema:\n{schema}\n\nQ: {question}\nSQL:"
        )
        result = prompt.render_sql_prompt("List all pets", schema, context)

        assert "Table: pets" in result
        assert "Description: Pet records" in result
        assert "- id (INTEGER, PK, NOT NULL)" in result
        assert "- name (VARCHAR(255), NOT NULL)" in result
        assert "- species (VARCHAR(100), nullable, default: 'Dog')" in result
        assert "- owner_id (INTEGER, nullable, FK → users(id))" in result
        assert "Table: users" in result
        assert "- email (VARCHAR(255), NOT NULL)" in result
        assert "Q: List all pets" in result
        assert "SQL:" in result

    def test_with_conversation_history(self, schema, context_with_history):
        prompt = self._make_prompt(
            sql_template="{history}\n\n{schema}\n\n{question}\nSQL:"
        )
        result = prompt.render_sql_prompt(
            "List all cats", schema, context_with_history
        )

        assert "## Previous conversation" in result
        assert "Question: Show me all dogs" in result
        assert "SQL: SELECT * FROM pets WHERE species = 'Dog'" in result
        assert "Answer: There are 5 dogs in the shelter." in result
        assert "Question: How many are adopted?" in result
        assert "List all cats" in result

    def test_without_history(self, schema, context):
        prompt = self._make_prompt(
            sql_template="{history}\n\n{schema}\n\nQ: {question}\nSQL:"
        )
        result = prompt.render_sql_prompt("List all pets", schema, context)

        assert result.startswith("\n\n")
        assert "## Previous conversation" not in result

    def test_empty_schema(self, empty_schema, context):
        prompt = self._make_prompt(
            sql_template="Schema: {schema}\nQ: {question}\nSQL:"
        )
        result = prompt.render_sql_prompt("List pets", empty_schema, context)

        assert "(no tables available)" in result

    def test_no_history_placeholder(self, schema, context_with_history):
        prompt = self._make_prompt(
            sql_template="{schema}\n\nQ: {question}\nSQL:"
        )
        result = prompt.render_sql_prompt(
            "List cats", schema, context_with_history
        )

        assert "## Previous conversation" not in result
        assert "Table: pets" in result

    def test_custom_template(self, schema, context):
        prompt = self._make_prompt(
            sql_template="CUSTOM: {question} | TABLES: {schema}"
        )
        result = prompt.render_sql_prompt("Count pets", schema, context)

        assert result.startswith("CUSTOM: Count pets | TABLES: Table: pets")


# ---------------------------------------------------------------------------
# Response prompt rendering
# ---------------------------------------------------------------------------


class TestRenderResponsePrompt:
    def _make_prompt(self, sql_template: str = "", response_template: str = ""):
        from app.ai.infrastructure.prompt_templates import PromptTemplateImpl

        return PromptTemplateImpl(
            sql_generation_template=sql_template,
            response_formatting_template=response_template,
        )

    def test_renders_question_sql_and_results(self, query_result, context):
        prompt = self._make_prompt(
            response_template="{question}\nSQL: {sql}\nResults:\n{results}"
        )
        result = prompt.render_response_prompt(
            "List all pets",
            "SELECT * FROM pets",
            query_result,
            context,
        )

        assert "List all pets" in result
        assert "SELECT * FROM pets" in result
        assert "Columns: id | name | species" in result
        assert "1 | Buddy | Dog" in result
        assert "2 | Whiskers | Cat" in result
        assert "2 row(s) returned (5ms)" in result

    def test_empty_result(self, empty_result, context):
        prompt = self._make_prompt(
            response_template="Results: {results}"
        )
        result = prompt.render_response_prompt(
            "Q", "SELECT 1", empty_result, context
        )

        assert "(empty results)" in result

    def test_custom_template(self, query_result, context):
        prompt = self._make_prompt(
            response_template="ANSWER: {question} SQL: {sql} DATA: {results}"
        )
        result = prompt.render_response_prompt(
            "Test", "SELECT 1", query_result, context
        )

        assert result.startswith("ANSWER: Test SQL: SELECT 1 DATA: Columns:")


# ---------------------------------------------------------------------------
# Integration with real config
# ---------------------------------------------------------------------------


class TestIntegrationWithConfig:
    @pytest.fixture(autouse=True)
    def _set_config_path(self):
        os.environ.setdefault("GROQ_API_KEY", "sk-test")
        os.environ.setdefault("AI_DB_TYPE", "postgresql")
        os.environ.setdefault("AI_DB_CONNECTION", "postgresql://test:test@localhost/test")
        config_path = os.path.join(
            os.path.dirname(__file__), "..", "config", "ai.yaml"
        )
        os.environ["AI_CONFIG_PATH"] = config_path

    def test_sql_prompt_from_config(self, schema, context_with_history):
        from app.ai.config.loader import load_config
        from app.ai.infrastructure.prompt_templates import PromptTemplateImpl

        config = load_config()
        prompt = PromptTemplateImpl(
            sql_generation_template=config.prompts.sql_generation,
            response_formatting_template=config.prompts.response_formatting,
        )

        result = prompt.render_sql_prompt(
            "Show me all dogs",
            schema,
            context_with_history,
        )

        assert "Show me all dogs" in result
        assert "Table: pets" in result
        assert "- name (VARCHAR(255), NOT NULL)" in result
        assert "## Previous conversation" in result
        assert "Question: Show me all dogs" in result
        assert "SQL:" in result

    def test_response_prompt_from_config(self, query_result, context):
        from app.ai.config.loader import load_config
        from app.ai.infrastructure.prompt_templates import PromptTemplateImpl

        config = load_config()
        prompt = PromptTemplateImpl(
            sql_generation_template=config.prompts.sql_generation,
            response_formatting_template=config.prompts.response_formatting,
        )

        result = prompt.render_response_prompt(
            "Show me all dogs",
            "SELECT * FROM pets",
            query_result,
            context,
        )

        assert "Show me all dogs" in result
        assert "SELECT * FROM pets" in result
        assert "1 | Buddy | Dog" in result
        assert "2 row(s) returned" in result


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def _make_prompt(self, sql_template: str = "", response_template: str = ""):
        from app.ai.infrastructure.prompt_templates import PromptTemplateImpl

        return PromptTemplateImpl(
            sql_generation_template=sql_template,
            response_formatting_template=response_template,
        )

    def test_empty_question(self, schema, context):
        prompt = self._make_prompt(sql_template="{question}")
        result = prompt.render_sql_prompt("", schema, context)
        assert result == ""

    def test_schema_with_no_columns(self, context):
        schema = DatabaseSchema(
            tables=[TableMetadata(name="empty_table", columns=[])]
        )
        prompt = self._make_prompt(sql_template="{schema}")
        result = prompt.render_sql_prompt("test", schema, context)

        assert "Table: empty_table" in result
        assert "Columns:" in result

    def test_schema_with_nullable_column_no_default(self, context):
        schema = DatabaseSchema(
            tables=[
                TableMetadata(
                    name="t",
                    columns=[
                        ColumnMetadata(
                            name="col", type="TEXT", nullable=True
                        ),
                    ],
                )
            ]
        )
        prompt = self._make_prompt(sql_template="{schema}")
        result = prompt.render_sql_prompt("test", schema, context)

        assert "- col (TEXT, nullable)" in result

    def test_history_with_partial_data(self, context):
        context.conversation_history = [
            AIInteraction(
                interaction_id="1",
                user_id="admin-1",
                question="Hello",
                generated_sql=None,
                response="Hi",
                provider="groq",
                created_at=None,
            ),
        ]
        schema = DatabaseSchema(tables=[])
        prompt = self._make_prompt(sql_template="{history}")
        result = prompt.render_sql_prompt("test", schema, context)

        assert "## Previous conversation" in result
        assert "Question: Hello" in result
        assert "SQL:" not in result
        assert "Answer: Hi" in result

    def test_single_interaction_history(self, context):
        context.conversation_history = [
            AIInteraction(
                interaction_id="1",
                user_id="admin-1",
                question="Show me all dogs",
                generated_sql="SELECT * FROM pets WHERE species = 'Dog'",
                response="There are 5 dogs.",
                provider="groq",
            ),
        ]
        schema = DatabaseSchema(tables=[])
        prompt = self._make_prompt(sql_template="{history}")
        result = prompt.render_sql_prompt("test", schema, context)

        assert "## Previous conversation" in result
        assert "Question: Show me all dogs" in result
        assert "SQL: SELECT * FROM pets WHERE species = 'Dog'" in result
        assert "Answer: There are 5 dogs." in result
        assert result.count("Question:") == 1

    def test_results_with_single_column_no_rows(self, context):
        result = QueryResult(
            columns=["count"],
            rows=[],
            row_count=0,
            execution_ms=0,
        )
        prompt = self._make_prompt(response_template="{results}")
        rendered = prompt.render_response_prompt("q", "sql", result, context)

        assert "Columns: count" in rendered
        assert "0 row(s) returned (0ms)" in rendered
