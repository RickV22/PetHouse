import os
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.ai.domain.entities import (
    AIExecutionContext,
    AIInteraction,
    AIRequest,
    AIResponse,
    AskResult,
    ColumnMetadata,
    DatabaseSchema,
    PlannedQuery,
    QueryResult,
    TableMetadata,
    ValidationResult,
)


class TestAIRequest:
    def test_constructor_sets_prompt(self):
        req = AIRequest(prompt="SELECT 1")
        assert req.prompt == "SELECT 1"

    def test_default_system_prompt_is_none(self):
        req = AIRequest(prompt="SELECT 1")
        assert req.system_prompt is None

    def test_default_temperature_is_none(self):
        req = AIRequest(prompt="SELECT 1")
        assert req.temperature is None

    def test_default_max_tokens_is_none(self):
        req = AIRequest(prompt="SELECT 1")
        assert req.max_tokens is None

    def test_equality(self):
        a = AIRequest(prompt="test", system_prompt="sys", temperature=0.5, max_tokens=100)
        b = AIRequest(prompt="test", system_prompt="sys", temperature=0.5, max_tokens=100)
        assert a == b

    def test_inequality(self):
        a = AIRequest(prompt="test")
        b = AIRequest(prompt="other")
        assert a != b

    def test_serialization(self):
        req = AIRequest(prompt="test", system_prompt="sys", temperature=0.5, max_tokens=100)
        d = {"prompt": "test", "system_prompt": "sys", "temperature": 0.5, "max_tokens": 100}
        assert req.__dict__ == d


class TestAIResponse:
    def test_constructor_sets_content(self):
        resp = AIResponse(content="Hello")
        assert resp.content == "Hello"

    def test_default_finish_reason_is_none(self):
        resp = AIResponse(content="Hello")
        assert resp.finish_reason is None

    def test_default_usage_is_none(self):
        resp = AIResponse(content="Hello")
        assert resp.usage is None

    def test_equality(self):
        a = AIResponse(content="Hello", finish_reason="stop", usage={"tokens": 10})
        b = AIResponse(content="Hello", finish_reason="stop", usage={"tokens": 10})
        assert a == b

    def test_serialization(self):
        resp = AIResponse(content="Hello", finish_reason="stop", usage={"tokens": 10})
        d = {"content": "Hello", "finish_reason": "stop", "usage": {"tokens": 10}}
        assert resp.__dict__ == d


class TestColumnMetadata:
    def test_constructor_sets_name_and_type(self):
        col = ColumnMetadata(name="id", type="INTEGER")
        assert col.name == "id"
        assert col.type == "INTEGER"

    def test_defaults(self):
        col = ColumnMetadata(name="id", type="INTEGER")
        assert col.nullable is True
        assert col.is_primary_key is False
        assert col.foreign_key is None
        assert col.description is None
        assert col.default_value is None

    def test_all_fields(self):
        col = ColumnMetadata(
            name="email",
            type="VARCHAR",
            nullable=False,
            is_primary_key=False,
            foreign_key="users(id)",
            description="Email address",
            default_value="''",
        )
        assert col.foreign_key == "users(id)"
        assert col.description == "Email address"
        assert col.default_value == "''"

    def test_equality(self):
        a = ColumnMetadata(name="id", type="INTEGER", nullable=False, is_primary_key=True)
        b = ColumnMetadata(name="id", type="INTEGER", nullable=False, is_primary_key=True)
        assert a == b

    def test_serialization(self):
        col = ColumnMetadata(name="id", type="INTEGER")
        d = {
            "name": "id", "type": "INTEGER", "nullable": True,
            "is_primary_key": False, "foreign_key": None,
            "description": None, "default_value": None,
        }
        assert col.__dict__ == d


class TestTableMetadata:
    def test_constructor_sets_name(self):
        table = TableMetadata(name="pets")
        assert table.name == "pets"

    def test_default_columns_empty(self):
        table = TableMetadata(name="pets")
        assert table.columns == []

    def test_default_description_none(self):
        table = TableMetadata(name="pets")
        assert table.description is None

    def test_with_columns_and_description(self):
        col = ColumnMetadata(name="id", type="INTEGER")
        table = TableMetadata(name="pets", columns=[col], description="Pet records")
        assert len(table.columns) == 1
        assert table.columns[0].name == "id"
        assert table.description == "Pet records"

    def test_equality(self):
        a = TableMetadata(name="pets", columns=[], description="x")
        b = TableMetadata(name="pets", columns=[], description="x")
        assert a == b

    def test_field_immutability(self):
        table = TableMetadata(name="pets")
        table.name = "users"
        assert table.name == "users"


class TestDatabaseSchema:
    def test_default_tables_empty(self):
        schema = DatabaseSchema()
        assert schema.tables == []

    def test_with_tables(self):
        table = TableMetadata(name="pets")
        schema = DatabaseSchema(tables=[table])
        assert len(schema.tables) == 1
        assert schema.tables[0].name == "pets"

    def test_equality(self):
        a = DatabaseSchema(tables=[TableMetadata(name="pets")])
        b = DatabaseSchema(tables=[TableMetadata(name="pets")])
        assert a == b

    def test_serialization(self):
        schema = DatabaseSchema()
        assert "tables" in schema.__dict__


class TestQueryResult:
    def test_defaults(self):
        result = QueryResult()
        assert result.columns == []
        assert result.rows == []
        assert result.row_count == 0
        assert result.execution_ms == 0

    def test_with_data(self):
        result = QueryResult(
            columns=["id", "name"],
            rows=[(1, "Buddy"), (2, "Max")],
            row_count=2,
            execution_ms=5,
        )
        assert result.columns == ["id", "name"]
        assert len(result.rows) == 2
        assert result.row_count == 2
        assert result.execution_ms == 5

    def test_equality(self):
        a = QueryResult(columns=["id"], rows=[(1,)], row_count=1, execution_ms=1)
        b = QueryResult(columns=["id"], rows=[(1,)], row_count=1, execution_ms=1)
        assert a == b

    def test_serialization(self):
        result = QueryResult(columns=["id"], rows=[(1,)], row_count=1, execution_ms=1)
        d = {"columns": ["id"], "rows": [(1,)], "row_count": 1, "execution_ms": 1}
        assert result.__dict__ == d


class TestAIInteraction:
    def test_constructor_sets_required_fields(self):
        now = datetime.now(timezone.utc)
        interaction = AIInteraction(
            interaction_id="abc-123",
            user_id="user-1",
            question="How many pets?",
            created_at=now,
        )
        assert interaction.interaction_id == "abc-123"
        assert interaction.user_id == "user-1"
        assert interaction.question == "How many pets?"
        assert interaction.created_at == now

    def test_optional_fields_default_to_none(self):
        interaction = AIInteraction(
            interaction_id="1", user_id="u1", question="q"
        )
        assert interaction.generated_sql is None
        assert interaction.execution_ms is None
        assert interaction.response is None
        assert interaction.created_at is None

    def test_provider_defaults_to_empty_string(self):
        interaction = AIInteraction(
            interaction_id="1", user_id="u1", question="q"
        )
        assert interaction.provider == ""

    def test_all_fields(self):
        now = datetime.now(timezone.utc)
        interaction = AIInteraction(
            interaction_id="1",
            user_id="u1",
            question="q",
            generated_sql="SELECT 1",
            execution_ms=42,
            response="answer",
            provider="groq",
            created_at=now,
        )
        assert interaction.generated_sql == "SELECT 1"
        assert interaction.execution_ms == 42
        assert interaction.response == "answer"
        assert interaction.provider == "groq"

    def test_equality(self):
        now = datetime.now(timezone.utc)
        a = AIInteraction(
            interaction_id="1", user_id="u1", question="q",
            generated_sql="SELECT 1", execution_ms=42, response="ans",
            provider="groq", created_at=now,
        )
        b = AIInteraction(
            interaction_id="1", user_id="u1", question="q",
            generated_sql="SELECT 1", execution_ms=42, response="ans",
            provider="groq", created_at=now,
        )
        assert a == b

    def test_serialization(self):
        now = datetime.now(timezone.utc)
        interaction = AIInteraction(
            interaction_id="1", user_id="u1", question="q",
            generated_sql="SELECT 1", execution_ms=42, response="ans",
            provider="groq", created_at=now,
        )
        d = interaction.__dict__
        assert d["interaction_id"] == "1"
        assert d["user_id"] == "u1"
        assert d["question"] == "q"
        assert d["generated_sql"] == "SELECT 1"
        assert d["execution_ms"] == 42
        assert d["response"] == "ans"
        assert d["provider"] == "groq"
        assert d["created_at"] == now


class TestAIExecutionContext:
    def test_constructor_sets_user_id(self):
        ctx = AIExecutionContext(user_id="admin-1")
        assert ctx.user_id == "admin-1"

    def test_default_permissions_empty(self):
        ctx = AIExecutionContext(user_id="admin-1")
        assert ctx.permissions == []

    def test_default_provider_and_model_empty(self):
        ctx = AIExecutionContext(user_id="admin-1")
        assert ctx.provider == ""
        assert ctx.model == ""

    def test_default_database_schema_none(self):
        ctx = AIExecutionContext(user_id="admin-1")
        assert ctx.database_schema is None

    def test_default_conversation_history_empty(self):
        ctx = AIExecutionContext(user_id="admin-1")
        assert ctx.conversation_history == []

    def test_default_config_empty(self):
        ctx = AIExecutionContext(user_id="admin-1")
        assert ctx.config == {}

    def test_default_timestamp_none(self):
        ctx = AIExecutionContext(user_id="admin-1")
        assert ctx.timestamp is None

    def test_all_fields(self):
        now = datetime.now(timezone.utc)
        schema = DatabaseSchema()
        history = [AIInteraction(interaction_id="1", user_id="u1", question="q")]
        ctx = AIExecutionContext(
            user_id="admin-1",
            permissions=["ai:assistant"],
            provider="groq",
            model="llama-3.3-70b-versatile",
            database_schema=schema,
            conversation_history=history,
            config={"key": "value"},
            timestamp=now,
        )
        assert ctx.permissions == ["ai:assistant"]
        assert ctx.provider == "groq"
        assert ctx.model == "llama-3.3-70b-versatile"
        assert ctx.database_schema is schema
        assert ctx.conversation_history == history
        assert ctx.config == {"key": "value"}
        assert ctx.timestamp == now

    def test_equality(self):
        a = AIExecutionContext(user_id="admin-1", permissions=["ai:assistant"])
        b = AIExecutionContext(user_id="admin-1", permissions=["ai:assistant"])
        assert a == b

    def test_serialization(self):
        ctx = AIExecutionContext(user_id="admin-1")
        d = ctx.__dict__
        assert d["user_id"] == "admin-1"


class TestValidationResult:
    def test_constructor_sets_is_valid(self):
        r = ValidationResult(is_valid=True)
        assert r.is_valid is True

    def test_default_values(self):
        r = ValidationResult(is_valid=True)
        assert r.error is None
        assert r.sql == ""
        assert r.max_rows == 1000
        assert r.execution_timeout_ms == 30000

    def test_invalid_result(self):
        r = ValidationResult(is_valid=False, error="bad sql", sql="DROP TABLE pets")
        assert r.is_valid is False
        assert r.error == "bad sql"
        assert r.sql == "DROP TABLE pets"

    def test_custom_limits(self):
        r = ValidationResult(is_valid=True, max_rows=500, execution_timeout_ms=15000)
        assert r.max_rows == 500
        assert r.execution_timeout_ms == 15000

    def test_equality(self):
        a = ValidationResult(is_valid=True, sql="SELECT 1", max_rows=1000, execution_timeout_ms=30000)
        b = ValidationResult(is_valid=True, sql="SELECT 1", max_rows=1000, execution_timeout_ms=30000)
        assert a == b


class TestPlannedQuery:
    def test_constructor_sets_all_fields(self):
        schema = DatabaseSchema()
        pq = PlannedQuery(sql="SELECT 1", schema=schema, prompt="test prompt")
        assert pq.sql == "SELECT 1"
        assert pq.schema is schema
        assert pq.prompt == "test prompt"

    def test_equality(self):
        schema = DatabaseSchema()
        a = PlannedQuery(sql="SELECT 1", schema=schema, prompt="test")
        b = PlannedQuery(sql="SELECT 1", schema=schema, prompt="test")
        assert a == b

    def test_serialization(self):
        schema = DatabaseSchema()
        pq = PlannedQuery(sql="SELECT 1", schema=schema, prompt="test")
        d = pq.__dict__
        assert d["sql"] == "SELECT 1"
        assert d["schema"] is schema
        assert d["prompt"] == "test"


class TestAskResult:
    def test_constructor_sets_all_fields(self):
        now = datetime.now(timezone.utc)
        result = AskResult(
            answer="There are 3 pets.",
            generated_sql="SELECT COUNT(*) FROM pets",
            execution_ms=42,
            provider="groq",
            model="llama-3.3-70b-versatile",
            interaction_id="abc-123",
            created_at=now,
        )
        assert result.answer == "There are 3 pets."
        assert result.generated_sql == "SELECT COUNT(*) FROM pets"
        assert result.execution_ms == 42
        assert result.provider == "groq"
        assert result.model == "llama-3.3-70b-versatile"
        assert result.interaction_id == "abc-123"
        assert result.created_at == now

    def test_equality(self):
        now = datetime.now(timezone.utc)
        a = AskResult(
            answer="a", generated_sql="s", execution_ms=1,
            provider="p", model="m", interaction_id="i", created_at=now,
        )
        b = AskResult(
            answer="a", generated_sql="s", execution_ms=1,
            provider="p", model="m", interaction_id="i", created_at=now,
        )
        assert a == b

    def test_serialization(self):
        now = datetime.now(timezone.utc)
        result = AskResult(
            answer="a", generated_sql="s", execution_ms=1,
            provider="p", model="m", interaction_id="i", created_at=now,
        )
        d = result.__dict__
        assert d["answer"] == "a"
        assert d["interaction_id"] == "i"
        assert d["created_at"] == now
