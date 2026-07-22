import asyncio
import traceback
from datetime import timedelta
from typing import Any, Dict, List, Optional, Tuple

import httpx
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from app.ai.domain.entities import (
    ColumnMetadata,
    DatabaseSchema,
    QueryResult,
    TableMetadata,
)
from app.ai.domain.exceptions import SQLValidationError
from app.ai.domain.interfaces import MCPClient, SQLValidator
from app.ai.infrastructure.exceptions import (
    MCPConnectionError,
    MCPExecutionError,
    MCPInvalidResponseError,
    MCPTimeoutError,
)


class MCPToolboxClient(MCPClient):
    def __init__(
        self,
        toolbox_url: str,
        timeout: float = 30.0,
        sql_validator: Optional[SQLValidator] = None,
    ) -> None:
        self._toolbox_url = toolbox_url
        self._timeout = timeout
        self._sql_validator = sql_validator

    async def get_schema(self) -> DatabaseSchema:
        print("=" * 80)
        print("LLAMANDO A get_schema")
        print("=" * 80)

        schema = DatabaseSchema(tables=[])
        try:
            raw = await self._call_tool("get_schema", {})
            schema = self._parse_schema(raw)
        except Exception as e:
            print(f"Error obteniendo esquema vía MCP Toolbox ({e}). Usando conexión directa...")

        if not schema.tables:
            print("Esquema vía MCP vacío. Ejecutando consulta directa a information_schema...")
            schema = await self._get_direct_schema()

        print("=" * 80)
        print("SCHEMA PARSEADO FINAL")
        print(schema)
        print("=" * 80)

        return schema

    async def execute_query(self, sql: str) -> QueryResult:
        if self._sql_validator is None:
            raise RuntimeError(
                "SQLValidator is not configured. Cannot execute SQL."
            )

        validation = self._sql_validator.validate(sql)

        print("=" * 80)
        print("VALIDACIÓN SQL")
        print(validation)
        print("=" * 80)

        if not validation.is_valid:
            raise SQLValidationError(
                validation.error or "SQL validation failed"
            )

        print("=" * 80)
        print("SQL ENVIADO AL TOOLBOX / DB")
        print(sql)
        print("=" * 80)

        try:
            raw = await self._call_tool(
                "execute_query",
                {
                    "sql": sql,
                    "max_rows": validation.max_rows,
                },
            )
            result = self._parse_query_result(raw)
        except Exception as e:
            print(f"MCP Toolbox falló ({e}). Ejecutando consulta directamente en PostgreSQL...")
            result = await self._execute_direct_sql(sql, validation.max_rows)

        print("=" * 80)
        print("QUERY RESULT PARSEADO")
        print(result)
        print("=" * 80)

        return result

    async def _execute_direct_sql(self, sql: str, max_rows: int) -> QueryResult:
        import time
        from sqlalchemy import text
        from app.db.session import SessionLocal

        start = time.time()
        clean_sql = sql.rstrip(";\n\r\t ")
        limited_sql = f"SELECT * FROM ({clean_sql}) AS _tmp LIMIT {max_rows}"

        def _run():
            db = SessionLocal()
            try:
                res = db.execute(text(limited_sql))
                cols = list(res.keys()) if res.returns_rows else []
                rows = [tuple(r) for r in res.fetchall()] if res.returns_rows else []
                return cols, rows
            finally:
                db.close()

        cols, rows = await asyncio.to_thread(_run)
        execution_ms = int((time.time() - start) * 1000)

        return QueryResult(
            columns=cols,
            rows=rows,
            row_count=len(rows),
            execution_ms=execution_ms,
        )

    async def _get_direct_schema(self) -> DatabaseSchema:
        from sqlalchemy import text
        from app.db.session import SessionLocal

        sql = """
        SELECT json_build_object(
          'tables', COALESCE(
            json_agg(
              json_build_object(
                'name', t.table_name,
                'columns', (
                  SELECT json_agg(
                    json_build_object(
                      'name', c.column_name,
                      'type', c.data_type,
                      'nullable', CASE WHEN c.is_nullable = 'YES' THEN true ELSE false END,
                      'primary_key', COALESCE(pk.is_pk, false),
                      'default_value', c.column_default
                    ) ORDER BY c.ordinal_position
                  )
                  FROM information_schema.columns c
                  LEFT JOIN (
                    SELECT kcu.column_name, true AS is_pk
                    FROM information_schema.table_constraints tc
                    JOIN information_schema.key_column_usage kcu
                      ON tc.constraint_name = kcu.constraint_name
                      AND tc.table_schema = kcu.table_schema
                      AND tc.table_name = kcu.table_name
                    WHERE tc.constraint_type = 'PRIMARY KEY'
                  ) pk ON c.column_name = pk.column_name
                    AND c.table_schema = t.table_schema
                    AND c.table_name = t.table_name
                  WHERE c.table_schema = t.table_schema
                    AND c.table_name = t.table_name
                )
              ) ORDER BY t.table_name
            ),
            '[]'::json
          )
        ) AS schema
        FROM information_schema.tables t
        WHERE t.table_schema = 'public'
          AND t.table_type = 'BASE TABLE';
        """

        def _run():
            db = SessionLocal()
            try:
                res = db.execute(text(sql)).fetchone()
                return res[0] if res else {}
            finally:
                db.close()

        raw = await asyncio.to_thread(_run)
        return self._parse_schema(raw)

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        print("=" * 80)
        print(f"LLAMANDO TOOL: {tool_name}")
        print("ARGUMENTOS:")
        print(arguments)
        print("=" * 80)

        async with httpx.AsyncClient(
            timeout=httpx.Timeout(self._timeout),
        ) as http_client:
            async with streamable_http_client(
                url=self._toolbox_url,
                http_client=http_client,
            ) as streams:
                async with ClientSession(
                    streams[0],
                    streams[1],
                    read_timeout_seconds=timedelta(seconds=self._timeout),
                ) as session:
                    try:
                        await session.initialize()
                    except Exception as e:
                        print("=" * 80)
                        print("ERROR EN INITIALIZE")
                        traceback.print_exc()
                        print("=" * 80)
                        raise

                    try:
                        result = await session.call_tool(
                            tool_name,
                            arguments,
                        )
                    except Exception as e:
                        print("=" * 80)
                        print("ERROR EN CALL_TOOL (SDK)")
                        traceback.print_exc()
                        print("=" * 80)
                        raise

        print("=" * 80)
        print("RESPUESTA MCP")
        print(result)
        print("=" * 80)

        if result.isError:
            error_text = self._extract_text(result.content)

            print("=" * 80)
            print("ERROR MCP")
            print(error_text)
            print("=" * 80)

            raise RuntimeError(
                f"MCP tool '{tool_name}' failed: {error_text}"
            )

        content = self._extract_content(result.content)

        print("=" * 80)
        print("CONTENIDO EXTRAÍDO")
        print(content)
        print("=" * 80)

        return content

    def _parse_query_result(self, raw: Any) -> QueryResult:
        if isinstance(raw, str):
            import json

            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                raise MCPInvalidResponseError(
                    "Failed to parse query result: invalid JSON"
                )

        if not isinstance(raw, dict):
            raise MCPInvalidResponseError(
                "Failed to parse query result: expected a dict"
            )

        columns = raw.get("columns", [])
        rows_raw = raw.get("rows", [])
        execution_ms = raw.get("execution_ms", 0)

        rows: List[Tuple[Any, ...]] = [
            tuple(row) if isinstance(row, list) else (row,)
            for row in rows_raw
        ]

        return QueryResult(
            columns=list(columns),
            rows=rows,
            row_count=len(rows),
            execution_ms=int(execution_ms),
        )

    def _extract_content(self, content: List[Any]) -> Any:
        import json

        texts = []

        for item in content:
            text = getattr(item, "text", None)
            if text is not None:
                texts.append(text)

        raw = "".join(texts)

        if not raw:
            return {}

        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            return raw

    def _extract_text(self, content: List[Any]) -> str:
        texts = []

        for item in content:
            text = getattr(item, "text", "")
            if text:
                texts.append(str(text))

        return " ".join(texts)

    def _parse_schema(self, raw: Any) -> DatabaseSchema:
        print("=" * 80)
        print("RAW RECIBIDO EN _parse_schema")
        print(raw)
        print("=" * 80)

        if isinstance(raw, str):
            import json

            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                return DatabaseSchema(tables=[])

        if not isinstance(raw, dict):
            return DatabaseSchema(tables=[])

        data = raw

        if "rows" in data:
            rows = data.get("rows", [])

            if rows:
                row = rows[0]

                if row:
                    cell = row[0]

                    if isinstance(cell, str):
                        import json

                        try:
                            cell = json.loads(cell)
                        except json.JSONDecodeError:
                            return DatabaseSchema(tables=[])

                    if isinstance(cell, dict):
                        data = cell

        tables_raw = data.get("tables", [])

        print("=" * 80)
        print("TABLAS ENCONTRADAS")
        print(tables_raw)
        print("=" * 80)

        if not isinstance(tables_raw, list):
            return DatabaseSchema(tables=[])

        tables: List[TableMetadata] = []

        for tbl in tables_raw:
            table = self._parse_table(tbl)

            if table is not None:
                tables.append(table)

        return DatabaseSchema(tables=tables)

    def _parse_table(self, raw: Any) -> Optional[TableMetadata]:
        if not isinstance(raw, dict):
            return None

        name = raw.get("name", "")

        if not name:
            return None

        columns: List[ColumnMetadata] = []
        seen_cols = set()

        for col in raw.get("columns", []):
            column = self._parse_column(col)

            if column is not None and column.name not in seen_cols:
                seen_cols.add(column.name)
                columns.append(column)

        return TableMetadata(
            name=name,
            columns=columns,
            description=raw.get("description"),
        )

    def _parse_column(self, raw: Any) -> Optional[ColumnMetadata]:
        if not isinstance(raw, dict):
            return None

        name = raw.get("name", "")

        if not name:
            return None

        return ColumnMetadata(
            name=name,
            type=raw.get("type", "TEXT"),
            nullable=bool(raw.get("nullable", True)),
            is_primary_key=bool(raw.get("primary_key", False)),
            foreign_key=raw.get("foreign_key"),
            description=raw.get("description"),
            default_value=raw.get("default_value"),
        )