import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def validator():
    from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

    return SqlglotSQLValidator(
        max_rows=1000,
        execution_timeout_ms=30000,
        max_query_length=500,
        max_join_depth=3,
    )


# ---------------------------------------------------------------------------
# Valid SELECT queries
# ---------------------------------------------------------------------------

class TestValidSelects:
    def test_simple_select(self, validator):
        result = validator.validate("SELECT * FROM pets")
        assert result.is_valid is True
        assert result.error is None

    def test_select_with_where(self, validator):
        result = validator.validate(
            "SELECT name, species FROM pets WHERE adopted_at IS NOT NULL"
        )
        assert result.is_valid is True

    def test_select_with_count(self, validator):
        result = validator.validate(
            "SELECT COUNT(*) FROM pets WHERE adopted_at >= date('now', '-30 days')"
        )
        assert result.is_valid is True

    def test_select_with_join(self, validator):
        result = validator.validate(
            "SELECT p.name, u.email FROM pets p JOIN users u ON p.owner_id = u.id"
        )
        assert result.is_valid is True

    def test_select_with_multiple_joins(self, validator):
        result = validator.validate(
            "SELECT * FROM pets p "
            "JOIN users u ON p.owner_id = u.id "
            "JOIN adoptions a ON a.pet_id = p.id"
        )
        assert result.is_valid is True

    def test_select_with_order_and_limit(self, validator):
        result = validator.validate(
            "SELECT * FROM pets ORDER BY created_at DESC LIMIT 10"
        )
        assert result.is_valid is True

    def test_select_with_distinct(self, validator):
        result = validator.validate("SELECT DISTINCT species FROM pets")
        assert result.is_valid is True

    def test_select_with_subquery(self, validator):
        result = validator.validate(
            "SELECT * FROM (SELECT * FROM pets WHERE species = 'Dog') AS dogs"
        )
        assert result.is_valid is True

    def test_select_with_cte(self, validator):
        result = validator.validate(
            "WITH recent AS (SELECT * FROM pets WHERE adopted_at IS NOT NULL) "
            "SELECT COUNT(*) FROM recent"
        )
        assert result.is_valid is True

    def test_select_with_group_by(self, validator):
        result = validator.validate(
            "SELECT species, COUNT(*) FROM pets GROUP BY species"
        )
        assert result.is_valid is True

    def test_union_select(self, validator):
        result = validator.validate(
            "SELECT * FROM pets UNION SELECT * FROM archived_pets"
        )
        assert result.is_valid is True

    def test_select_with_for_update(self, validator):
        result = validator.validate("SELECT * FROM pets FOR UPDATE")
        assert result.is_valid is True

    def test_returned_limits(self, validator):
        result = validator.validate("SELECT 1")
        assert result.max_rows == 1000
        assert result.execution_timeout_ms == 30000
        assert result.sql == "SELECT 1"


# ---------------------------------------------------------------------------
# Rejected non-SELECT statements
# ---------------------------------------------------------------------------

class TestRejectedNonSelect:
    def test_insert_rejected(self, validator):
        result = validator.validate("INSERT INTO pets (name) VALUES ('Buddy')")
        assert result.is_valid is False
        assert "SELECT" in result.error

    def test_update_rejected(self, validator):
        result = validator.validate("UPDATE pets SET name = 'Max' WHERE id = 1")
        assert result.is_valid is False

    def test_delete_rejected(self, validator):
        result = validator.validate("DELETE FROM pets WHERE id = 1")
        assert result.is_valid is False

    def test_drop_rejected(self, validator):
        result = validator.validate("DROP TABLE pets")
        assert result.is_valid is False

    def test_alter_rejected(self, validator):
        result = validator.validate("ALTER TABLE pets ADD COLUMN test TEXT")
        assert result.is_valid is False

    def test_create_rejected(self, validator):
        result = validator.validate("CREATE TABLE test (id INT)")
        assert result.is_valid is False

    def test_truncate_rejected(self, validator):
        result = validator.validate("TRUNCATE pets")
        assert result.is_valid is False

    def test_copy_rejected(self, validator):
        result = validator.validate("COPY pets TO '/tmp/pets.csv'")
        assert result.is_valid is False

    def test_execute_rejected(self, validator):
        result = validator.validate("EXECUTE sp_delete_pet(1)")
        assert result.is_valid is False

    def test_call_rejected(self, validator):
        result = validator.validate("CALL sp_delete_pet(1)")
        assert result.is_valid is False

    def test_do_rejected(self, validator):
        result = validator.validate("DO $$ BEGIN NULL; END $$")
        assert result.is_valid is False

    def test_grant_rejected(self, validator):
        result = validator.validate("GRANT SELECT ON pets TO admin")
        assert result.is_valid is False

    def test_revoke_rejected(self, validator):
        result = validator.validate("REVOKE SELECT ON pets FROM admin")
        assert result.is_valid is False

    def test_vacuum_rejected(self, validator):
        result = validator.validate("VACUUM pets")
        assert result.is_valid is False

    def test_analyze_rejected(self, validator):
        result = validator.validate("ANALYZE pets")
        assert result.is_valid is False


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------

class TestEdgeCases:
    def test_empty_string(self, validator):
        result = validator.validate("")
        assert result.is_valid is False
        assert "empty" in result.error.lower()

    def test_whitespace_only(self, validator):
        result = validator.validate("   ")
        assert result.is_valid is False

    def test_none(self, validator):
        result = validator.validate(None)
        assert result.is_valid is False

    def test_multiple_statements_rejected(self, validator):
        result = validator.validate(
            "SELECT * FROM pets; SELECT * FROM users"
        )
        assert result.is_valid is False
        assert "Multiple" in result.error

    def test_select_then_insert_rejected(self, validator):
        result = validator.validate(
            "SELECT * FROM pets; INSERT INTO pets (name) VALUES ('X')"
        )
        assert result.is_valid is False

    def test_gibberish_rejected(self, validator):
        result = validator.validate("this is not sql at all")
        assert result.is_valid is False


# ---------------------------------------------------------------------------
# Configurable limits
# ---------------------------------------------------------------------------

class TestLimits:
    def test_max_query_length_exceeded(self, validator):
        sql = "SELECT " + "x" * 500
        result = validator.validate(sql)
        assert result.is_valid is False
        assert "maximum length" in result.error.lower()

    def test_max_query_length_respected(self, validator):
        sql = "SELECT " + "x" * 5
        result = validator.validate(sql)
        assert result.is_valid is True

    def test_max_join_depth_exceeded(self):
        from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

        v = SqlglotSQLValidator(max_join_depth=2)
        sql = (
            "SELECT * FROM t1 "
            "JOIN t2 ON t1.id = t2.id "
            "JOIN t3 ON t2.id = t3.id "
            "JOIN t4 ON t3.id = t4.id"
        )
        result = v.validate(sql)
        assert result.is_valid is False
        assert "JOIN" in result.error

    def test_max_join_depth_respected(self):
        from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

        v = SqlglotSQLValidator(max_join_depth=5)
        sql = (
            "SELECT * FROM t1 "
            "JOIN t2 ON t1.id = t2.id "
            "JOIN t3 ON t2.id = t3.id"
        )
        result = v.validate(sql)
        assert result.is_valid is True

    def test_custom_max_rows_returned(self):
        from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

        v = SqlglotSQLValidator(max_rows=500)
        result = v.validate("SELECT 1")
        assert result.max_rows == 500

    def test_custom_timeout_returned(self):
        from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

        v = SqlglotSQLValidator(execution_timeout_ms=15000)
        result = v.validate("SELECT 1")
        assert result.execution_timeout_ms == 15000

    def test_default_limits(self):
        from app.ai.infrastructure.sql_validator import SqlglotSQLValidator

        v = SqlglotSQLValidator()
        result = v.validate("SELECT 1")
        assert result.max_rows == 1000
        assert result.execution_timeout_ms == 30000


# ---------------------------------------------------------------------------
# Domain entity
# ---------------------------------------------------------------------------

class TestValidationResultEntity:
    def test_default_values(self):
        from app.ai.domain.entities import ValidationResult

        r = ValidationResult(is_valid=True)
        assert r.error is None
        assert r.sql == ""
        assert r.max_rows == 1000
        assert r.execution_timeout_ms == 30000

    def test_invalid_result(self):
        from app.ai.domain.entities import ValidationResult

        r = ValidationResult(is_valid=False, error="bad sql", sql="DROP TABLE pets")
        assert r.is_valid is False
        assert r.error == "bad sql"
        assert r.sql == "DROP TABLE pets"
