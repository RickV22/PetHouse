## ADDED Requirements

### Requirement: AI provider configuration is stored in YAML
The system SHALL read AI provider settings from a `config/ai.yaml` file. The configuration SHALL support environment variable substitution using `${VAR_NAME}` syntax.

#### Scenario: YAML configuration loads at startup
- **WHEN** the application starts
- **THEN** it SHALL read and parse `config/ai.yaml`

#### Scenario: Environment variables are resolved
- **WHEN** the configuration contains `${GROQ_API_KEY}`
- **THEN** the system SHALL resolve it from the environment variable `GROQ_API_KEY`

#### Scenario: Missing environment variable raises error
- **WHEN** the configuration references `${MISSING_VAR}` and the environment variable is not set
- **THEN** the system SHALL log the missing variable name and fail to start

### Requirement: Groq is the supported provider for this change
The system SHALL support Groq as the single AI provider. Provider-specific settings SHALL include api_key, model, temperature, and max_tokens.

#### Scenario: Groq provider configured with API key and model
- **WHEN** the YAML configuration specifies a `groq` provider block
- **THEN** it SHALL accept `api_key`, `model`, `temperature`, and `max_tokens` as settings

#### Scenario: Missing Groq API key fails at startup
- **WHEN** the YAML configuration is missing the Groq API key
- **THEN** the system SHALL log the error and fail to start

### Requirement: Provider health check verifies connectivity
The system SHALL provide a health check mechanism that verifies Groq API connectivity on startup and at configurable intervals.

#### Scenario: Health check passes on startup
- **WHEN** the application starts and Groq API responds successfully
- **THEN** the health check SHALL report healthy and allow the application to continue

#### Scenario: Health check failure logs warning
- **WHEN** the Groq API is unreachable during health check
- **THEN** the system SHALL log a warning but continue running (degraded mode)

### Requirement: SQL validator limits are configurable
The YAML configuration SHALL include SQL validator settings: max_rows, execution_timeout_ms, max_query_length, and max_join_depth.

#### Scenario: SQL validator configured in YAML
- **WHEN** the YAML configuration specifies a `sql_validator` block
- **THEN** it SHALL contain `max_rows`, `execution_timeout_ms`, `max_query_length`, and `max_join_depth` settings

#### Scenario: Missing SQL validator settings use defaults
- **WHEN** the YAML configuration omits `sql_validator` settings
- **THEN** the system SHALL use default values (max_rows=1000, execution_timeout_ms=30000, max_query_length=10000, max_join_depth=5)

### Requirement: MCP Toolbox connection is configurable
The YAML configuration SHALL include MCP Toolbox connection settings: toolbox_url, database type, and connection string.

#### Scenario: MCP configured with toolbox URL
- **WHEN** the YAML configuration specifies an `mcp` block
- **THEN** it SHALL contain `toolbox_url`, `database.type`, and `database.connection_string` settings

#### Scenario: MCP configuration validated at startup
- **WHEN** the MCP connection string is missing or malformed
- **THEN** the system SHALL log the error and fail to start

### Requirement: Audit retention is configurable
The YAML configuration SHALL include audit retention settings: enabled flag and retention_days.

#### Scenario: Audit retention configured in YAML
- **WHEN** the YAML configuration specifies an `audit` block
- **THEN** it SHALL contain `enabled` and `retention_days` settings

#### Scenario: Audit disabled via configuration
- **WHEN** `audit.enabled` is set to `false`
- **THEN** the system SHALL skip audit logging without errors
