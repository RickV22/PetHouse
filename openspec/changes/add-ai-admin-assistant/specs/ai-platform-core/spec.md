## ADDED Requirements

### Requirement: AI Platform Core defines domain interfaces
The platform SHALL provide abstract interfaces in the domain layer for: AIProvider, MCPClient, AITool, PromptTemplate, SchemaProvider, ConversationRepository, and AIExecutionContext. These interfaces SHALL contain zero dependencies on FastAPI, Open WebUI, Groq, MCP, SQLAlchemy, or any infrastructure library.

#### Scenario: Domain interfaces exist without framework imports
- **WHEN** inspecting the domain layer module
- **THEN** it SHALL NOT import from fastapi, openwebui, groq, mcp, sqlalchemy, httpx, or any infrastructure library

#### Scenario: AIProvider interface defines generate method
- **WHEN** examining the AIProvider interface
- **THEN** it SHALL declare an async `generate` method accepting an AIRequest and returning an AIResponse

#### Scenario: MCPClient interface defines schema and query methods
- **WHEN** examining the MCPClient interface
- **THEN** it SHALL declare `get_schema` returning a DatabaseSchema and `execute_query` accepting a SQL string and returning a QueryResult

#### Scenario: AITool interface defines execute, description, and parameters
- **WHEN** examining the AITool interface
- **THEN** it SHALL declare `execute` accepting AIExecutionContext and a params dict returning AIResponse, `description` returning a string, and `parameters` returning a dict

#### Scenario: PromptTemplate interface defines render methods
- **WHEN** examining the PromptTemplate interface
- **THEN** it SHALL declare `render_sql_prompt` accepting a question, DatabaseSchema, and AIExecutionContext, and `render_response_prompt` accepting a question, SQL string, QueryResult, and AIExecutionContext

#### Scenario: SchemaProvider interface defines schema method
- **WHEN** examining the SchemaProvider interface
- **THEN** it SHALL declare `get_database_schema` returning a DatabaseSchema

#### Scenario: ConversationRepository interface defines save and history methods
- **WHEN** examining the ConversationRepository interface
- **THEN** it SHALL declare `save` accepting an AIInteraction and `get_history` accepting a user ID and optional limit

### Requirement: Domain entities are framework-free data classes
The platform SHALL define AIRequest, AIResponse, DatabaseSchema, QueryResult, AIInteraction, and AIExecutionContext as plain data classes in the domain layer with no framework inheritance or decorators.

#### Scenario: Domain entities are pure Python classes
- **WHEN** inspecting AIRequest, AIResponse, DatabaseSchema, QueryResult, AIInteraction, or AIExecutionContext
- **THEN** each SHALL be a dataclass without inheriting from any framework-specific base class

#### Scenario: AIInteraction contains all audit fields
- **WHEN** inspecting the AIInteraction entity
- **THEN** it SHALL contain fields for: interaction_id, user_id, question, generated_sql, execution_ms, response, provider, and created_at

#### Scenario: AIExecutionContext contains all context fields
- **WHEN** inspecting the AIExecutionContext entity
- **THEN** it SHALL contain fields for: user_id, permissions, provider, model, database_schema, conversation_history, config, and timestamp

### Requirement: Dependency injection wires implementations to interfaces
The platform SHALL use dependency injection to bind interface implementations at startup. The binding SHALL be driven by YAML configuration.

#### Scenario: Groq provider injected as AIProvider implementation
- **WHEN** the YAML configuration specifies Groq as the provider
- **THEN** the application SHALL instantiate and inject GroqProvider as the AIProvider implementation

#### Scenario: Invalid provider name raises startup error
- **WHEN** the YAML configuration specifies a provider name not matching any registered implementation
- **THEN** the application SHALL raise a configuration validation error at startup

### Requirement: Configuration is validated at startup
The platform SHALL validate the YAML configuration file at startup and fail fast with descriptive error messages for missing or invalid settings.

#### Scenario: Missing API key triggers startup failure
- **WHEN** the YAML configuration is missing a required API key for Groq
- **THEN** the application SHALL log the specific missing key and exit with a non-zero status code

#### Scenario: Invalid provider URL triggers startup failure
- **WHEN** a provider URL is malformed in the YAML configuration
- **THEN** the application SHALL log the specific invalid URL and exit with a non-zero status code

### Requirement: AITool is the generic extension point for capabilities
The platform SHALL route all AI capability execution through the AITool interface. The first implementation SHALL provide a SqlQueryTool. Future capabilities SHALL be added as new AITool implementations without modifying existing tools or the core use case.

#### Scenario: SqlQueryTool executes the full NL-to-SQL pipeline
- **WHEN** SqlQueryTool.execute is called with a question and AIExecutionContext
- **THEN** it SHALL retrieve schema, build prompt, call AIProvider, validate SQL, execute via MCPClient, format response, and return an AIResponse

#### Scenario: AITool registry allows tool discovery
- **WHEN** the AdminAssistantUseCase starts
- **THEN** it SHALL discover available AITool implementations registered in the container

#### Scenario: New tool added without modifying existing code
- **WHEN** a new AITool implementation is registered in the container
- **THEN** it SHALL be discoverable without modifying AdminAssistantUseCase or SqlQueryTool
