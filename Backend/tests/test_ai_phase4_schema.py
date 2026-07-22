import asyncio
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# MCPToolboxClient — schema parsing (unit tests, no MCP server needed)
# ---------------------------------------------------------------------------

class TestMCPToolboxClientParsing:
    def _make_client(self):
        from app.ai.infrastructure.mcp_client import MCPToolboxClient

        return MCPToolboxClient(toolbox_url="http://localhost:5000/mcp")

    def test_parse_schema_empty(self):
        client = self._make_client()
        result = client._parse_schema({})
        assert len(result.tables) == 0

    def test_parse_schema_none(self):
        client = self._make_client()
        result = client._parse_schema(None)
        assert len(result.tables) == 0

    def test_parse_schema_string(self):
        client = self._make_client()
        result = client._parse_schema("{}")
        assert len(result.tables) == 0

    def test_parse_schema_invalid_json_string(self):
        client = self._make_client()
        result = client._parse_schema("not json")
        assert len(result.tables) == 0

    def test_parse_schema_single_table(self):
        client = self._make_client()
        raw = {
            "tables": [
                {
                    "name": "pets",
                    "description": "Pet records",
                    "columns": [
                        {
                            "name": "id",
                            "type": "INTEGER",
                            "nullable": False,
                            "primary_key": True,
                        },
                        {
                            "name": "name",
                            "type": "VARCHAR(255)",
                            "nullable": False,
                        },
                        {
                            "name": "species",
                            "type": "VARCHAR(100)",
                            "nullable": True,
                            "default_value": "'Dog'",
                        },
                        {
                            "name": "owner_id",
                            "type": "INTEGER",
                            "nullable": True,
                            "foreign_key": "users(id)",
                        },
                    ],
                },
            ],
        }
        result = client._parse_schema(raw)
        assert len(result.tables) == 1

        table = result.tables[0]
        assert table.name == "pets"
        assert table.description == "Pet records"
        assert len(table.columns) == 4

        col_id = table.columns[0]
        assert col_id.name == "id"
        assert col_id.type == "INTEGER"
        assert col_id.nullable is False
        assert col_id.is_primary_key is True
        assert col_id.foreign_key is None

        col_owner = table.columns[3]
        assert col_owner.name == "owner_id"
        assert col_owner.foreign_key == "users(id)"

        col_species = table.columns[2]
        assert col_species.default_value == "'Dog'"

    def test_parse_schema_multiple_tables(self):
        client = self._make_client()
        raw = {
            "tables": [
                {"name": "pets", "columns": [{"name": "id", "type": "INTEGER"}]},
                {"name": "users", "columns": [{"name": "id", "type": "INTEGER"}]},
            ],
        }
        result = client._parse_schema(raw)
        assert len(result.tables) == 2
        assert result.tables[0].name == "pets"
        assert result.tables[1].name == "users"

    def test_parse_table_no_name_returns_none(self):
        client = self._make_client()
        assert client._parse_table({}) is None
        assert client._parse_table({"name": ""}) is None
        assert client._parse_table(None) is None

    def test_parse_column_no_name_returns_none(self):
        client = self._make_client()
        assert client._parse_column({}) is None
        assert client._parse_column({"name": ""}) is None
        assert client._parse_column(None) is None

    def test_parse_column_defaults(self):
        client = self._make_client()
        col = client._parse_column({"name": "test_col"})
        assert col is not None
        assert col.name == "test_col"
        assert col.type == "TEXT"
        assert col.nullable is True
        assert col.is_primary_key is False
        assert col.foreign_key is None
        assert col.description is None
        assert col.default_value is None

    def test_extract_text_empty(self):
        client = self._make_client()
        assert client._extract_text([]) == ""

    def test_extract_text_with_items(self):
        client = self._make_client()
        item1 = MagicMock()
        item1.text = "hello"
        item2 = MagicMock()
        item2.text = "world"
        assert client._extract_text([item1, item2]) == "hello world"

    def test_extract_content_json(self):
        client = self._make_client()
        item = MagicMock()
        item.text = '{"tables": []}'
        result = client._extract_content([item])
        assert result == {"tables": []}

    def test_extract_content_plain_text(self):
        client = self._make_client()
        item = MagicMock()
        item.text = "plain text"
        result = client._extract_content([item])
        assert result == "plain text"

    def test_extract_content_empty(self):
        client = self._make_client()
        result = client._extract_content([])
        assert result == {}


# ---------------------------------------------------------------------------
# MCPToolboxClient — integration with mocked MCP session
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_mcp_session():
    with patch("app.ai.infrastructure.mcp_client.streamable_http_client") as mock_transport, \
         patch("app.ai.infrastructure.mcp_client.ClientSession") as mock_session_cls:

        mock_session = MagicMock()
        mock_session.initialize = AsyncMock()
        mock_session.call_tool = AsyncMock()
        mock_session_cls.return_value.__aenter__.return_value = mock_session

        streams = (MagicMock(), MagicMock(), MagicMock())
        mock_transport.return_value.__aenter__.return_value = streams

        yield mock_session


class TestMCPToolboxClientIntegration:
    @pytest.mark.asyncio
    async def test_get_schema_success(self, mock_mcp_session):
        from app.ai.infrastructure.mcp_client import MCPToolboxClient

        mock_mcp_session.call_tool.return_value = MagicMock(
            isError=False,
            content=[MagicMock(text='{"tables": [{"name": "pets", "columns": [{"name": "id", "type": "INTEGER"}]}]}')],
        )

        client = MCPToolboxClient(toolbox_url="http://mcp:5000/mcp")
        schema = await client.get_schema()

        assert len(schema.tables) == 1
        assert schema.tables[0].name == "pets"
        assert schema.tables[0].columns[0].name == "id"

    @pytest.mark.asyncio
    async def test_get_schema_tool_error(self, mock_mcp_session):
        from app.ai.infrastructure.mcp_client import MCPToolboxClient

        mock_mcp_session.call_tool.return_value = MagicMock(
            isError=True,
            content=[MagicMock(text="connection refused")],
        )

        client = MCPToolboxClient(toolbox_url="http://mcp:5000/mcp")
        with pytest.raises(RuntimeError, match="get_schema"):
            await client.get_schema()

    @pytest.mark.asyncio
    async def test_execute_query_success(self, mock_mcp_session):
        from app.ai.infrastructure.mcp_client import MCPToolboxClient
        from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

        mock_mcp_session.call_tool.return_value = MagicMock(
            isError=False,
            content=[MagicMock(
                text='{"columns": ["id", "name"], "rows": [[1, "Buddy"], [2, "Whiskers"]], "execution_ms": 5}'
            )],
        )

        validator = SqlglotSQLValidator()
        client = MCPToolboxClient(
            toolbox_url="http://mcp:5000/mcp",
            sql_validator=validator,
        )
        result = await client.execute_query("SELECT id, name FROM pets")

        assert result.columns == ["id", "name"]
        assert result.row_count == 2
        assert list(result.rows[0]) == [1, "Buddy"]
        assert list(result.rows[1]) == [2, "Whiskers"]
        assert result.execution_ms == 5

    @pytest.mark.asyncio
    async def test_execute_query_validation_failure(self):
        from app.ai.infrastructure.mcp_client import MCPToolboxClient
        from app.ai.domain.exceptions import SQLValidationError
        from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

        validator = SqlglotSQLValidator()
        client = MCPToolboxClient(
            toolbox_url="http://mcp:5000/mcp",
            sql_validator=validator,
        )
        with pytest.raises(SQLValidationError, match="SELECT"):
            await client.execute_query("DROP TABLE pets")

    @pytest.mark.asyncio
    async def test_execute_query_no_validator(self):
        from app.ai.infrastructure.mcp_client import MCPToolboxClient

        client = MCPToolboxClient(toolbox_url="http://mcp:5000/mcp")
        with pytest.raises(RuntimeError, match="SQLValidator"):
            await client.execute_query("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_query_mcp_error(self, mock_mcp_session):
        from app.ai.infrastructure.mcp_client import MCPToolboxClient
        from app.ai.infrastructure.exceptions import MCPExecutionError
        from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

        mock_mcp_session.call_tool.return_value = MagicMock(
            isError=True,
            content=[MagicMock(text="execution error: timeout")],
        )

        validator = SqlglotSQLValidator()
        client = MCPToolboxClient(
            toolbox_url="http://mcp:5000/mcp",
            sql_validator=validator,
        )
        with pytest.raises(MCPExecutionError, match="execute_query"):
            await client.execute_query("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_query_timeout(self, mock_mcp_session):
        from app.ai.infrastructure.mcp_client import MCPToolboxClient
        from app.ai.infrastructure.exceptions import MCPTimeoutError
        from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

        mock_mcp_session.call_tool.side_effect = asyncio.TimeoutError()

        validator = SqlglotSQLValidator()
        client = MCPToolboxClient(
            toolbox_url="http://mcp:5000/mcp",
            sql_validator=validator,
        )
        with pytest.raises(MCPTimeoutError):
            await client.execute_query("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_query_connection_failure(self, mock_mcp_session):
        from app.ai.infrastructure.mcp_client import MCPToolboxClient
        from app.ai.infrastructure.exceptions import MCPConnectionError
        from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

        mock_mcp_session.call_tool.side_effect = ConnectionError("connection refused")

        validator = SqlglotSQLValidator()
        client = MCPToolboxClient(
            toolbox_url="http://mcp:5000/mcp",
            sql_validator=validator,
        )
        with pytest.raises(MCPConnectionError, match="connection refused"):
            await client.execute_query("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_query_invalid_response(self, mock_mcp_session):
        from app.ai.infrastructure.mcp_client import MCPToolboxClient
        from app.ai.infrastructure.exceptions import MCPInvalidResponseError
        from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

        mock_mcp_session.call_tool.return_value = MagicMock(
            isError=False,
            content=[MagicMock(text="not valid json")],
        )

        validator = SqlglotSQLValidator()
        client = MCPToolboxClient(
            toolbox_url="http://mcp:5000/mcp",
            sql_validator=validator,
        )
        with pytest.raises(MCPInvalidResponseError):
            await client.execute_query("SELECT 1")

    @pytest.mark.asyncio
    async def test_execute_query_passes_limits(self, mock_mcp_session):
        from app.ai.infrastructure.mcp_client import MCPToolboxClient
        from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

        mock_mcp_session.call_tool.return_value = MagicMock(
            isError=False,
            content=[MagicMock(
                text='{"columns": ["id"], "rows": [[1]]}'
            )],
        )

        validator = SqlglotSQLValidator(max_rows=500, execution_timeout_ms=15000)
        client = MCPToolboxClient(
            toolbox_url="http://mcp:5000/mcp",
            sql_validator=validator,
        )
        await client.execute_query("SELECT 1")

        call_kwargs = mock_mcp_session.call_tool.call_args
        args = call_kwargs[0]
        assert args[0] == "execute_query"
        assert args[1]["max_rows"] == 500
        assert args[1]["execution_timeout_ms"] == 15000


# ---------------------------------------------------------------------------
# MCPSchemaProvider
# ---------------------------------------------------------------------------

class TestMCPSchemaProvider:
    @pytest.mark.asyncio
    async def test_get_database_schema_delegates(self):
        from app.ai.domain.entities import DatabaseSchema, TableMetadata
        from app.ai.infrastructure.schema_provider import MCPSchemaProvider

        mock_client = MagicMock()
        expected = DatabaseSchema(tables=[TableMetadata(name="test")])
        mock_client.get_schema = AsyncMock(return_value=expected)

        provider = MCPSchemaProvider(mock_client)
        result = await provider.get_database_schema()

        assert result == expected
        mock_client.get_schema.assert_awaited_once()
