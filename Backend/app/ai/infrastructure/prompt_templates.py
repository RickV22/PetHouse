from typing import List, Optional

from app.ai.domain.entities import (
    AIExecutionContext,
    AIInteraction,
    DatabaseSchema,
    QueryResult,
    TableMetadata,
)
from app.ai.domain.interfaces import PromptTemplate


class PromptTemplateImpl(PromptTemplate):
    def __init__(
        self,
        sql_generation_template: str,
        response_formatting_template: str,
    ) -> None:
        self._sql_template = sql_generation_template
        self._response_template = response_formatting_template

    def render_sql_prompt(
        self, question: str, schema: DatabaseSchema, context: AIExecutionContext
    ) -> str:
        schema_str = self._format_schema(schema)
        history_str = self._format_history(context.conversation_history)

        return self._sql_template.format(
            schema=schema_str,
            question=question,
            history=history_str,
        )

    def render_response_prompt(
        self,
        question: str,
        sql: str,
        result: QueryResult,
        context: AIExecutionContext,
    ) -> str:
        results_str = self._format_results(result)

        return self._response_template.format(
            question=question,
            sql=sql,
            results=results_str,
        )

    def _format_schema(self, schema: DatabaseSchema) -> str:
        if not schema.tables:
            return "(no tables available)"

        parts: List[str] = []
        for table in schema.tables:
            cols = []
            for col in table.columns:
                c_str = f"{col.name} ({col.type}"
                if col.is_primary_key:
                    c_str += ", PK"
                if col.foreign_key:
                    c_str += f", FK->{col.foreign_key}"
                c_str += ")"
                cols.append(c_str)
            parts.append(f"Tabla `{table.name}`: {', '.join(cols)}")

        return "\n".join(parts)

    def _format_history(self, history: List[AIInteraction]) -> str:
        if not history:
            return ""

        # Solo incluir las últimas 3 interacciones para ahorrar consumo de tokens
        recent = history[-3:]
        parts: List[str] = ["## Conversaciones recientes"]
        for interaction in recent:
            parts.append(f"Pregunta: {interaction.question}")
            if interaction.generated_sql:
                parts.append(f"SQL: {interaction.generated_sql}")
            if interaction.response:
                resp = interaction.response[:150] + "..." if len(interaction.response) > 150 else interaction.response
                parts.append(f"Respuesta: {resp}")
            parts.append("")

        return "\n".join(parts).strip()

    def _format_results(self, result: QueryResult) -> str:
        if not result.columns and not result.rows:
            return "(empty results)"

        header = " | ".join(str(c) for c in result.columns)
        lines: List[str] = [f"Columns: {header}"]

        for row in result.rows[:15]:
            values = " | ".join(str(v) for v in row)
            lines.append(values)

        if len(result.rows) > 15:
            lines.append(f"... ({len(result.rows) - 15} filas más no mostradas en el prompt)")

        lines.append(
            f"{result.row_count} row(s) returned ({result.execution_ms}ms)"
        )

        return "\n".join(lines)
