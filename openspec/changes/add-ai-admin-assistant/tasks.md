## Phase 1: Foundation (COMPLETED)

- [x] 1.1 Create `app/ai/` package with Clean Architecture directory structure: `domain/`, `application/`, `infrastructure/`, `presentation/`
- [x] 1.2 Create `config/ai.yaml` with provider, MCP, and audit database configuration sections using environment variable placeholders
- [x] 1.3 Add required Python dependencies to `requirements.txt` (groq, mcp, pyyaml, asyncpg, httpx)
- [x] 1.4 Implement YAML configuration loader with environment variable resolution and startup validation
- [x] 1.5 Create dependency injection container skeleton

## Phase 2: Domain Layer

- [x] 2.1 Define domain entities as framework-free dataclasses: `AIRequest`, `AIResponse`, `DatabaseSchema`, `QueryResult`, `AIInteraction`
- [x] 2.2 Define `AIExecutionContext` entity with fields: user_id, permissions, provider, model, database_schema, conversation_history, config, timestamp
- [x] 2.3 Define `AIProvider` abstract interface with `generate` method
- [x] 2.4 Define `MCPClient` abstract interface with `get_schema` and `execute_query` methods
- [x] 2.5 Define `AITool` abstract interface with `execute`, `description`, and `parameters` methods
- [x] 2.6 Define `PromptTemplate` abstract interface with `render_sql_prompt` and `render_response_prompt` methods
- [x] 2.7 Define `SchemaProvider` abstract interface with `get_database_schema` method
- [x] 2.8 Define `ConversationRepository` abstract interface with `save` and `get_history` methods
- [x] 2.9 Verify all domain interfaces have zero imports from FastAPI, Open WebUI, Groq, MCP, or SQLAlchemy

## Phase 3: Groq Provider

- [x] 3.1 Implement `GroqProvider` adapter conforming to `AIProvider` interface
- [x] 3.2 Implement Groq-specific error mapping (timeout, rate limit, auth failure)
- [x] 3.3 Implement provider health check that verifies Groq API connectivity
- [x] 3.4 Implement provider factory that instantiates GroqProvider from YAML configuration
- [x] 3.5 Register GroqProvider in dependency injection container

## Phase 4: MCP Integration

- [x] 4.1 Implement `MCPToolboxClient` with `get_schema` method (retrieves table/column metadata only, no row data)
- [x] 4.2 Implement `MCPToolboxClient` with `execute_query` method (read-only SQL execution)
- [x] 4.3 Implement `SchemaProvider` that wraps MCP schema data into domain `DatabaseSchema` entity
- [x] 4.4 Implement `SQLValidator` that rejects all non-read statements: INSERT, UPDATE, DELETE, ALTER, DROP, CREATE, TRUNCATE, COPY, EXECUTE, CALL, DO, GRANT, REVOKE, VACUUM, ANALYZE
- [x] 4.5 Implement configurable limits in `SQLValidator`: max_rows (default 1000), execution_timeout_ms (default 30000), max_query_length (default 10000), max_join_depth (default 5)

## Phase 5: Audit Repository

- [ ] 5.1 Create Alembic migration for `ai_interactions` table in the existing PetHouse database (id UUID, user_id, question, generated_sql, execution_ms, response, provider, created_at)
- [ ] 5.2 Implement `PostgresConversationRepository` with `save` method (append-only)
- [ ] 5.3 Implement `PostgresConversationRepository` with `get_history` method (filter by user_id, ordered by created_at DESC, configurable limit)
- [ ] 5.4 Implement audit log retention/pruning logic with configurable TTL (default 90 days)

## Phase 6: Application Use Cases

- [x] 6.1 Implement `PromptTemplate` with SQL generation prompt rendering using config-loaded templates
- [x] 6.2 Implement `PromptTemplate` with response formatting prompt rendering
- [x] 6.3 Implement `QueryPlanner` application service that coordinates schema retrieval, prompt construction, and LLM SQL generation
- [x] 6.4 Implement `SqlQueryTool` (first AITool implementation) that executes the full NL-to-SQL pipeline
- [x] 6.5 Implement `AdminAssistantUseCase` that builds AIExecutionContext, selects SqlQueryTool, executes, and saves audit log
- [x] 6.6 Implement follow-up question context support (previous Q/A included in AIExecutionContext history)

## Phase 7: FastAPI Presentation

- [x] 7.1 Implement `POST /api/v1/ai/ask` endpoint accepting question and returning answer, SQL, and execution time
- [x] 7.2 Implement `GET /api/v1/ai/history` endpoint returning admin's interaction history with optional limit parameter
- [x] 7.3 Implement JWT auth middleware checking `ai:assistant` scope on AI endpoints
- [x] 7.4 Add input validation (reject empty questions, enforce max length)
- [x] 7.5 Wire dependency injection for all layers at application startup

## Phase 8: Docker / Open WebUI / MCP

- [ ] 8.1 Add Open WebUI service to `compose.yaml`
- [ ] 8.2 Add MCP Toolbox service to `compose.yaml`
- [ ] 8.3 Configure MCP Toolbox with READ-ONLY database user credentials
- [ ] 8.4 Configure Open WebUI to use FastAPI AI endpoints for the admin assistant
- [ ] 8.5 Update environment variable templates with AI platform settings
- [ ] 8.6 Implement graceful shutdown (close MCP connections, DB pools)

## Phase 9: Angular Assistant

- [ ] 9.1 Add AI Assistant panel component to the Angular frontend
- [ ] 9.2 Implement chat-style UI with question input and answer display
- [ ] 9.3 Integrate with `POST /api/v1/ai/ask` endpoint
- [ ] 9.4 Display generated SQL and execution time alongside the answer
- [ ] 9.5 Add conversation history panel using `GET /api/v1/ai/history`

## Phase 10: Testing

- [ ] 10.1 Write unit tests for domain entities (no framework dependencies)
- [ ] 10.2 Write unit tests for `SQLValidator` (all rejected statements + configurable limits)
- [ ] 10.3 Write unit tests for `PromptTemplate` rendering
- [ ] 10.4 Write unit tests for `QueryPlanner` with mock dependencies
- [ ] 10.5 Write integration tests for full pipeline with mock provider + test database
- [ ] 10.6 Write API tests for auth enforcement (401 without token, 403 without scope)
- [ ] 10.7 Write API tests for error scenarios (empty question, provider failure, invalid SQL, timeout)
