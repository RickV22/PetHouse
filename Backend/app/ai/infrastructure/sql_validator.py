from sqlglot import exp, parse

from app.ai.domain.entities import ValidationResult
from app.ai.domain.interfaces import SQLValidator

_READ_ONLY_TYPES = (exp.Select, exp.Union, exp.Intersect, exp.Except)


class SqlglotSQLValidator(SQLValidator):
    def __init__(
        self,
        max_rows: int = 1000,
        execution_timeout_ms: int = 30000,
        max_query_length: int = 10000,
        max_join_depth: int = 5,
    ) -> None:
        self._max_rows = max_rows
        self._execution_timeout_ms = execution_timeout_ms
        self._max_query_length = max_query_length
        self._max_join_depth = max_join_depth

    def validate(self, sql: str) -> ValidationResult:
        if not sql or not sql.strip():
            return self._invalid(sql, "SQL statement is empty")

        if len(sql) > self._max_query_length:
            return self._invalid(
                sql,
                f"SQL exceeds maximum length of {self._max_query_length} characters "
                f"({len(sql)} characters provided)",
            )

        try:
            statements = parse(sql, dialect="postgres")
        except Exception as e:
            return self._invalid(sql, f"Failed to parse SQL: {e}")

        if not statements:
            return self._invalid(sql, "SQL statement could not be parsed")

        filtered = [s for s in statements if s is not None]

        if len(filtered) == 0:
            return self._invalid(sql, "SQL statement could not be parsed")

        if len(filtered) > 1:
            return self._invalid(
                sql,
                f"Multiple statements detected ({len(filtered)}). Only single SELECT queries are allowed",
            )

        tree = filtered[0]

        if isinstance(tree, exp.Command):
            return self._invalid(
                sql,
                f"Unsupported or unrecognized SQL command",
            )

        if not isinstance(tree, _READ_ONLY_TYPES):
            return self._invalid(
                sql,
                f"Only SELECT queries are allowed. Got: {tree.__class__.__name__}",
            )

        joins = list(tree.find_all(exp.Join))
        if len(joins) > self._max_join_depth:
            return self._invalid(
                sql,
                f"Query exceeds maximum JOIN depth of {self._max_join_depth} "
                f"({len(joins)} JOINs detected)",
            )

        return ValidationResult(
            is_valid=True,
            sql=sql,
            max_rows=self._max_rows,
            execution_timeout_ms=self._execution_timeout_ms,
        )

    def _invalid(self, sql: str, message: str) -> ValidationResult:
        return ValidationResult(is_valid=False, error=message, sql=sql)
