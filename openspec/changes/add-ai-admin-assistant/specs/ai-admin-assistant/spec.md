## ADDED Requirements

### Requirement: Admin Assistant accepts natural language questions
The system SHALL provide a `POST /api/v1/ai/ask` endpoint that accepts a natural language question from an authenticated administrator and returns a natural language answer based on business database data.

#### Scenario: Valid question returns answer
- **WHEN** an authenticated admin sends `{"question": "How many pets have been adopted this month?"}`
- **THEN** the system SHALL return a JSON response with `answer` (natural language), `sql` (the generated SQL), and `execution_ms` (query execution time)

#### Scenario: Unauthenticated request returns 401
- **WHEN** a request without a valid JWT token is sent to the endpoint
- **THEN** the system SHALL return HTTP 401 Unauthorized

#### Scenario: Non-admin user returns 403
- **WHEN** a request with a valid JWT token lacking the `ai:assistant` scope is sent to the endpoint
- **THEN** the system SHALL return HTTP 403 Forbidden

#### Scenario: Empty question returns 422
- **WHEN** an empty or whitespace-only question is sent
- **THEN** the system SHALL return HTTP 422 Unprocessable Entity

### Requirement: Assistant only executes SELECT queries
The system SHALL enforce that only SELECT SQL statements are executed against the business database. All non-read operations SHALL be rejected before execution.

#### Scenario: SELECT query executes successfully
- **WHEN** the LLM generates `SELECT COUNT(*) FROM pets WHERE adopted_at IS NOT NULL AND adopted_at >= date('now', '-30 days')`
- **THEN** the system SHALL execute the query and return results

#### Scenario: INSERT statement is rejected
- **WHEN** the LLM generates `INSERT INTO pets (name, species) VALUES ('Buddy', 'Dog')`
- **THEN** the system SHALL reject the statement and return an error response without executing

#### Scenario: DROP statement is rejected
- **WHEN** the LLM generates `DROP TABLE pets`
- **THEN** the system SHALL reject the statement and return an error response without executing

#### Scenario: ALTER statement is rejected
- **WHEN** the LLM generates `ALTER TABLE pets ADD COLUMN test TEXT`
- **THEN** the system SHALL reject the statement and return an error response without executing

#### Scenario: DELETE statement is rejected
- **WHEN** the LLM generates `DELETE FROM pets WHERE id = 1`
- **THEN** the system SHALL reject the statement and return an error response without executing

#### Scenario: UPDATE statement is rejected
- **WHEN** the LLM generates `UPDATE pets SET name = 'Max' WHERE id = 1`
- **THEN** the system SHALL reject the statement and return an error response without executing

#### Scenario: CREATE statement is rejected
- **WHEN** the LLM generates `CREATE TABLE test (id INT)`
- **THEN** the system SHALL reject the statement and return an error response without executing

#### Scenario: TRUNCATE statement is rejected
- **WHEN** the LLM generates `TRUNCATE TABLE pets`
- **THEN** the system SHALL reject the statement and return an error response without executing

#### Scenario: COPY statement is rejected
- **WHEN** the LLM generates `COPY pets TO '/tmp/pets.csv'`
- **THEN** the system SHALL reject the statement and return an error response without executing

#### Scenario: EXECUTE statement is rejected
- **WHEN** the LLM generates `EXECUTE sp_delete_pet(1)`
- **THEN** the system SHALL reject the statement and return an error response without executing

#### Scenario: GRANT statement is rejected
- **WHEN** the LLM generates `GRANT ALL ON pets TO admin`
- **THEN** the system SHALL reject the statement and return an error response without executing

### Requirement: SQL execution has configurable limits
The system SHALL enforce configurable limits on SQL execution to prevent resource exhaustion: maximum rows returned, execution timeout, maximum query length, and maximum JOIN depth.

#### Scenario: Query exceeds max rows
- **WHEN** a query would return more than the configured `max_rows` (default 1000)
- **THEN** the system SHALL truncate results to `max_rows` and include a warning in the response

#### Scenario: Query exceeds execution timeout
- **WHEN** a query runs longer than the configured `execution_timeout_ms` (default 30000)
- **THEN** the system SHALL cancel the query and return an error response with message "The database query timed out."

#### Scenario: Query exceeds max length
- **WHEN** the LLM generates SQL longer than the configured `max_query_length` (default 10000 characters)
- **THEN** the system SHALL reject the statement before execution and return an error response

#### Scenario: Query exceeds JOIN depth
- **WHEN** the LLM generates SQL with more JOIN clauses than the configured `max_join_depth` (default 5)
- **THEN** the system SHALL reject the statement before execution and return an error response

### Requirement: Assistant provides conversation history
The system SHALL provide a `GET /api/v1/ai/history` endpoint that returns the authenticated admin's recent interaction history.

#### Scenario: History returns last 20 interactions
- **WHEN** an authenticated admin requests their history
- **THEN** the system SHALL return the last 20 interactions ordered by most recent first

#### Scenario: History respects limit parameter
- **WHEN** an authenticated admin requests history with `?limit=5`
- **THEN** the system SHALL return at most 5 interactions

### Requirement: Assistant exposes database schema context
The system SHALL expose database table and column metadata to the LLM so it can generate accurate SQL without prior knowledge of the schema.

#### Scenario: Schema context is included in prompt
- **WHEN** the LLM prompt is constructed for a question
- **THEN** it SHALL include table names, column names, column types, and foreign key relationships from the business database

#### Scenario: Schema context excludes row data
- **WHEN** the database schema is retrieved
- **THEN** it SHALL include metadata only (table/column names and types) — NOT actual row data

### Requirement: Assistant provides clear error messages
The system SHALL return user-friendly error messages when the assistant cannot process a question, including: unparseable SQL generation, database connection failures, provider timeouts, query execution errors, and limit violations.

#### Scenario: Database timeout returns error
- **WHEN** a query exceeds the configured execution timeout
- **THEN** the system SHALL return an error response with message "The database query timed out. Please try a simpler question."

#### Scenario: LLM generates invalid SQL
- **WHEN** the LLM generates SQL that fails to parse (e.g., syntax error)
- **THEN** the system SHALL return an error response and log the raw SQL for debugging

#### Scenario: Provider unavailable returns error message
- **WHEN** the configured AI provider returns an error or times out
- **THEN** the system SHALL return an error response indicating the provider is unavailable

#### Scenario: Max rows limit hit returns warning
- **WHEN** a query result exceeds `max_rows`
- **THEN** the system SHALL return results truncated to `max_rows` with a warning message

### Requirement: Assistant supports follow-up questions
The system SHALL support follow-up questions by including the previous question, SQL, and answer in the AIExecutionContext conversation history.

#### Scenario: Follow-up question references previous context
- **WHEN** an admin asks "Which breed was most common?" after "How many pets have been adopted this month?"
- **THEN** the prompt SHALL include the context from the previous interaction
