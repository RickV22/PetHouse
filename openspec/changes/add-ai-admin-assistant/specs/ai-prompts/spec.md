## ADDED Requirements

### Requirement: PromptTemplate abstracts prompt construction
The system SHALL provide a `PromptTemplate` interface in the domain layer that externalizes prompt text from provider code. Templates SHALL be loaded from YAML configuration and rendered at runtime.

#### Scenario: PromptTemplate interface defines render methods
- **WHEN** examining the PromptTemplate interface
- **THEN** it SHALL declare `render_sql_prompt` accepting a question, DatabaseSchema, and AIExecutionContext, and `render_response_prompt` accepting a question, SQL string, QueryResult, and AIExecutionContext

#### Scenario: Prompt templates are loaded from config
- **WHEN** the application starts
- **THEN** the SQL generation and response formatting prompt templates SHALL be loaded from `config/ai.yaml`

#### Scenario: Templates support variable substitution
- **WHEN** a template contains `{schema}`, `{question}`, or `{history}` placeholders
- **THEN** the PromptTemplate SHALL replace them with the corresponding runtime values

### Requirement: SQL generation prompt guides accurate SQL output
The SQL generation prompt SHALL instruct the LLM to generate PostgreSQL-compatible SELECT queries based on the provided schema context. The prompt SHALL include: available tables and columns with types, foreign key relationships, and instructions to return only SELECT statements.

#### Scenario: SQL prompt includes schema context
- **WHEN** rendering the SQL generation prompt
- **THEN** it SHALL include all table names, column names, column types, primary keys, and foreign key relationships

#### Scenario: SQL prompt includes query constraints
- **WHEN** rendering the SQL generation prompt
- **THEN** it SHALL instruct the LLM to only generate SELECT statements and to avoid any non-read operations

#### Scenario: SQL prompt follows expected format
- **WHEN** the SQL generation prompt is rendered
- **THEN** the LLM SHALL receive clear instructions about the expected output format (SQL only, no markdown, no explanation)

### Requirement: Response formatting prompt produces natural language answers
The response formatting prompt SHALL instruct the LLM to convert SQL query results into natural language answers suitable for administrators.

#### Scenario: Response prompt includes query context
- **WHEN** rendering the response formatting prompt
- **THEN** it SHALL include the original question, the generated SQL, and the query results

#### Scenario: Response prompt produces concise answers
- **WHEN** the response formatting prompt is rendered
- **THEN** it SHALL instruct the LLM to produce concise, administrator-friendly answers without technical details unless asked

#### Scenario: Response prompt supports empty results
- **WHEN** a query returns zero rows
- **THEN** the response prompt SHALL produce an answer like "No results found for your query."

### Requirement: Prompts are extensible for future capabilities
The PromptTemplate interface SHALL support adding new prompt types without modifying existing prompt implementations. New capabilities SHALL add new render methods or new template configuration entries.

#### Scenario: New prompt type added without breaking existing prompts
- **WHEN** a future capability requires a new prompt type
- **THEN** it SHALL be added as a new render method in the PromptTemplate interface without modifying the existing `render_sql_prompt` or `render_response_prompt` methods

#### Scenario: Prompt text updated via configuration
- **WHEN** the prompt text in `config/ai.yaml` is updated
- **THEN** the new prompt text SHALL be used on the next application restart without code changes
