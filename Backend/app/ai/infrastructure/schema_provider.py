from app.ai.domain.entities import DatabaseSchema
from app.ai.domain.interfaces import MCPClient, SchemaProvider


class MCPSchemaProvider(SchemaProvider):
    def __init__(self, mcp_client: MCPClient) -> None:
        self._mcp_client = mcp_client

    async def get_database_schema(self) -> DatabaseSchema:
        return await self._mcp_client.get_schema()
