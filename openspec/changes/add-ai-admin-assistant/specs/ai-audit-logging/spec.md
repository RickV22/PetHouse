## ADDED Requirements

### Requirement: Every AI interaction is logged to the existing PetHouse database
The system SHALL persist every AI interaction to the `ai_interactions` table in the existing PetHouse PostgreSQL database. The audit record SHALL include: user_id, question, generated_sql, execution_ms, response, provider, and created_at.

#### Scenario: Successful interaction is logged
- **WHEN** an admin completes a successful AI assistant query
- **THEN** the full interaction SHALL be written to the `ai_interactions` table with all required fields populated

#### Scenario: Failed interaction is logged
- **WHEN** an AI assistant query fails (e.g., invalid SQL, provider timeout)
- **THEN** the interaction SHALL be logged with the error details in the response field and NULL or empty for generated_sql and execution_ms as appropriate

#### Scenario: Audit record contains all required fields
- **WHEN** inspecting an audit log entry
- **THEN** it SHALL contain: id (UUID), user_id, question, generated_sql, execution_ms, response, provider, created_at (TIMESTAMP WITH TIME ZONE)

### Requirement: Audit logs are immutable
The system SHALL NOT provide any API or mechanism to modify or delete audit log entries. Audit data is append-only.

#### Scenario: No audit update endpoint exists
- **WHEN** examining the AI module API surface
- **THEN** there SHALL be no PUT, PATCH, or DELETE endpoint for audit log entries

#### Scenario: No audit delete endpoint exists
- **WHEN** examining the AI module API surface
- **THEN** there SHALL be no endpoint to delete audit log entries

### Requirement: Audit logs support querying by admin
The system SHALL provide the ConversationRepository `get_history` method that returns interactions filtered by user_id, ordered by most recent first, with configurable limit.

#### Scenario: History filtered by user
- **WHEN** querying history for a specific user
- **THEN** only that user's interactions SHALL be returned

#### Scenario: History respects ordering
- **WHEN** querying history
- **THEN** results SHALL be ordered by created_at descending

#### Scenario: History respects limit
- **WHEN** querying history with a limit of 10
- **THEN** at most 10 records SHALL be returned

### Requirement: Audit data is TTL-managed
The system SHALL support configurable retention period for audit logs. Logs older than the retention period MAY be pruned automatically.

#### Scenario: Configurable retention policy exists
- **WHEN** inspecting the audit configuration
- **THEN** it SHALL contain a `retention_days` setting

#### Scenario: Pruning does not affect current data
- **WHEN** audit log pruning runs
- **THEN** it SHALL only delete records older than the retention period without affecting recent interactions
