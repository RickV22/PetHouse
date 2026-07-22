## Context

PetHouse runs a FastAPI backend with SQLAlchemy ORM, JWT authentication, and dual-database support (SQLite dev / PostgreSQL prod). An existing Ollama chatbot provides basic conversational capability but is not integrated with business data.

The organization needs an enterprise AI platform that can grow across multiple domains: administrative queries, veterinary assistance, adoption analytics, report generation, and recommendations.

This design covers the platform foundation (`ai-platform-core`) and the first capability (`ai-admin-assistant`).

**Constraints:**
- Business layer must have zero dependency on FastAPI, Open WebUI, Groq, or MCP
- All external dependencies must be abstracted through interfaces
- Only authenticated administrators may access the assistant
- Database access from the AI layer must be read-only (SELECT only)
- Every AI interaction must be fully audited
- Provider configuration must be YAML-driven
- Audit tables must live in the existing PetHouse PostgreSQL database (no separate instance)
- Existing Ollama chatbot must remain untouched

## Goals / Non-Goals

**Goals:**
- Design a Clean Architecture AI Platform Core with abstract interfaces (AIProvider, MCPClient, AITool, SchemaProvider, PromptTemplate, ConversationRepository)
- Implement the Administrative AI Assistant as the first capability
- Introduce AIExecutionContext as the unified context object for all AI operations
- Introduce AITool as a generic extension point — SQL execution is the first tool implementation
- Introduce QueryPlanner as the application service coordinating NL-to-SQL flow
- Introduce PromptTemplate for externalized, versionable prompt management
- Enable NL-to-SQL translation for business queries (adoptions, registrations, vaccinations, etc.)
- Provide read-only MCP-based database access with strengthened SQL validation (configurable max rows, timeout, query length, JOIN depth)
- Implement full audit logging within the existing PetHouse PostgreSQL database
- Support Groq as the single AI provider for this change
- Integrate Open WebUI as the admin chat frontend
- Enforce admin-only access via JWT scope verification

**Non-Goals:**
- Replacing the existing Ollama chatbot
- Modifying existing FastAPI business endpoints or data models
- Implementing future AI capabilities (Veterinary Assistant, Analytics, Reports, Recommendations)
- Building a custom chat UI (Open WebUI handles this)
- Migrating existing data or schemas
- Providing write access to the business database
- Multi-provider support (Ollama, OpenAI, Anthropic — deferred to a future change)
- Provider fallback logic (deferred)
- Multi-agent orchestration (deferred)

## Decisions

### Architecture: Clean Architecture with 4 Layers

**Decision:** Organize the AI platform into Domain, Application, Infrastructure, and Presentation layers.

**Rationale:**
- Domain layer remains pure Python with zero framework dependencies — this is the most critical constraint
- Application layer orchestrates use cases through domain interfaces without knowing implementation details
- Infrastructure layer provides concrete implementations for AI providers, MCP, database access, audit logging
- Presentation layer (FastAPI routes, Open WebUI integration) is the only layer with framework coupling
- AITool provides a generic extension point so new capabilities (report generation, veterinary queries, document search) can be added without modifying the core assistant flow
- QueryPlanner encapsulates the NL-to-SQL planning logic, keeping the use case focused on orchestration
- PromptTemplate externalizes prompt text so prompts can evolve independently of provider code

```text
┌─────────────────────────────────────────────────────────────┐
│                    Presentation Layer                        │
│     FastAPI Routes · Open WebUI Integration                 │
│     JWT Auth Middleware · Request/Response DTOs              │
├─────────────────────────────────────────────────────────────┤
│                    Application Layer                         │
│     AdminAssistantUseCase · QueryPlanner                    │
│     SQLValidator · Response Formatting                      │
├─────────────────────────────────────────────────────────────┤
│                    Domain Layer                              │
│     AIProvider · MCPClient · AITool · ConversationRepo      │
│     PromptTemplate · SchemaProvider · AIExecutionContext    │
│     Entities (AIRequest, AIResponse, etc.)                   │
├─────────────────────────────────────────────────────────────┤
│                   Infrastructure Layer                       │
│     GroqProvider · MCPToolboxClient · SqlAITool             │
│     PostgresConversationRepo · YamlConfigProvider           │
│     GroqPromptTemplate                                      │
└─────────────────────────────────────────────────────────────┘
```

### AI Provider Abstraction

**Decision:** Define an `AIProvider` interface in the domain layer. The first implementation provides a `GroqProvider` adapter. The interface is designed for future provider implementations in a separate change.

**Alternatives considered:**
- Direct SDK coupling: Rejected — locks the platform to Groq and violates abstracted architecture
- Adapter pattern: Chosen — GroqProvider adapts the Groq SDK to the AIProvider interface

```python
class AIProvider(ABC):
    async def generate(self, request: AIRequest) -> AIResponse: ...
```

### MCP Client Abstraction

**Decision:** Abstract MCP Toolbox interaction behind an `MCPClient` interface. The interface exposes schema introspection and read-only query execution.

**Rationale:** MCP Toolbox is not a standard part of the Python ecosystem — abstracting it allows swapping for a direct database connection or another tool in the future without changing use case logic.

```python
class MCPClient(ABC):
    async def get_schema(self) -> DatabaseSchema: ...
    async def execute_query(self, sql: str) -> QueryResult: ...
```

### Read-Only Enforcement

**Decision:** SQL validation happens at two levels:
1. **MCP Toolbox connection** — configured with a database user that has SELECT-only privileges at the database level
2. **Application-level SQLValidator** — parses the generated SQL and rejects all non-read operations before execution

**Rejected statements (comprehensive denylist):**
INSERT, UPDATE, DELETE, ALTER, DROP, CREATE, TRUNCATE, COPY, EXECUTE, CALL, DO, GRANT, REVOKE, VACUUM, ANALYZE

**Configurable limits enforced by the SQLValidator:**
- `max_rows` — maximum rows returned (default: 1000)
- `execution_timeout_ms` — maximum query execution time (default: 30000)
- `max_query_length` — maximum SQL text length (default: 10000)
- `max_join_depth` — maximum number of JOIN clauses (default: 5)

**Rationale:** Defense in depth. The database-level restriction is the primary safeguard; the application-level validator catches issues before they reach the database and provides a better user experience with clear error messages. Configurable limits prevent runaway queries and resource exhaustion.

### Audit Logging

**Decision:** Audit tables live inside the existing PetHouse PostgreSQL database, abstracted behind a `ConversationRepository` interface. No separate audit database instance is created.

**Rationale:** Using the existing database simplifies operations (single backup, single connection pool, no cross-DB orchestration). The `ai_interactions` table is append-only and segregated by schema prefix for clarity.

**Audit schema (new table in PetHouse database):**
```sql
CREATE TABLE ai_interactions (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id       VARCHAR(255) NOT NULL,
    question      TEXT NOT NULL,
    generated_sql TEXT,
    execution_ms  INTEGER,
    response      TEXT,
    provider      VARCHAR(50) NOT NULL,
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### AITool — Generic Extension Point

**Decision:** Introduce an `AITool` interface in the domain layer as a generic extension point. Each capability (SQL query, report generation, veterinary assistant, document search) becomes a separate `AITool` implementation.

**Rationale:** AITool decouples capability implementation from the assistant orchestration. The `AdminAssistantUseCase` discovers available tools and dispatches to the appropriate one. This prepares the platform for future capabilities without modifying the core flow.

```python
class AITool(ABC):
    @abstractmethod
    async def execute(self, context: AIExecutionContext, params: dict) -> AIResponse: ...

    @abstractmethod
    def description(self) -> str: ...

    @abstractmethod
    def parameters(self) -> dict: ...
```

The SQL query capability becomes a `SqlQueryTool` that implements `AITool`:
- `execute()` — retrieves schema, builds SQL prompt via PromptTemplate, calls AIProvider, validates SQL, executes via MCPClient, formats response
- `description()` — returns "Execute read-only SQL queries against the business database"
- `parameters()` — returns the JSON schema for the `question` parameter

### QueryPlanner — Application Service

**Decision:** Introduce `QueryPlanner` as an application-layer service that encapsulates the NL-to-SQL planning logic. The `AdminAssistantUseCase` delegates to `QueryPlanner` for prompt construction and SQL generation coordination.

**Rationale:** Keeping planning logic in QueryPlanner keeps the use case focused on orchestration and error handling. QueryPlanner is testable in isolation and can be reused by future capabilities (e.g., report generator).

```python
class QueryPlanner:
    def __init__(
        self,
        schema_provider: SchemaProvider,
        prompt_template: PromptTemplate,
        ai_provider: AIProvider,
        sql_validator: SQLValidator,
    ): ...

    async def plan_query(self, question: str, context: AIExecutionContext) -> PlannedQuery: ...

    async def format_response(self, question: str, sql: str, result: QueryResult, context: AIExecutionContext) -> str: ...
```

### PromptTemplate — Externalized Prompt Management

**Decision:** Introduce `PromptTemplate` as a domain-layer abstraction. Prompt templates are NOT embedded inside providers. Instead, they are loaded from configuration and rendered at runtime.

**Rationale:** Externalized prompts can be versioned, tested, and improved without touching provider code. Templates support variables for schema context, question, conversation history, and execution results.

```python
class PromptTemplate(ABC):
    @abstractmethod
    def render_sql_prompt(self, question: str, schema: DatabaseSchema, context: AIExecutionContext) -> str: ...

    @abstractmethod
    def render_response_prompt(self, question: str, sql: str, result: QueryResult, context: AIExecutionContext) -> str: ...
```

### AIExecutionContext — Unified Context Object

**Decision:** Introduce `AIExecutionContext` as a domain entity that bundles all context for an AI operation.

**Rationale:** Passing a single context object through the pipeline eliminates parameter bloat and makes it easy to add new context fields without changing method signatures.

```python
@dataclass
class AIExecutionContext:
    user_id: str
    permissions: List[str]
    provider: str
    model: str
    database_schema: DatabaseSchema
    conversation_history: List[AIInteraction]
    config: AIConfig
    timestamp: datetime
```

### Schema Provider

**Decision:** Create a `SchemaProvider` interface that returns the database schema in a structured domain model.

**Rationale:** The MCP client returns raw schema data — the SchemaProvider transforms it into a domain-friendly `DatabaseSchema` object that the PromptTemplate can consume without depending on MCP types.

### Configuration: YAML-Based

**Decision:** All AI platform configuration lives in `config/ai.yaml`.

**Structure (single-provider for this change):**
```yaml
ai:
  provider: groq
  groq:
    api_key: ${GROQ_API_KEY}
    model: llama-3.3-70b-versatile
    temperature: 0.1
    max_tokens: 4096

  health_check:
    enabled: true
    interval_seconds: 60
    timeout_seconds: 10

  mcp:
    toolbox_url: http://mcp-toolbox:9090
    database:
      type: ${AI_DB_TYPE}
      connection_string: ${AI_DB_CONNECTION}

  sql_validator:
    max_rows: 1000
    execution_timeout_ms: 30000
    max_query_length: 10000
    max_join_depth: 5

  audit:
    enabled: true
    retention_days: 90

  prompts:
    sql_generation: |
      You are a SQL expert. Given the following database schema...
    response_formatting: |
      Given the original question, the SQL used, and the results...
```

**Rationale:** YAML is human-readable, supports environment variable substitution (via `${VAR}`), and can be reloaded at runtime without recompilation. Prompts are externalized in configuration for independent iteration.

### NL-to-SQL Pipeline Flow (via AITool + QueryPlanner)

**Decision:** Implement the pipeline through the AITool and QueryPlanner abstractions. The `AdminAssistantUseCase` selects the appropriate tool and delegates.

```text
1. Admin sends question via Open WebUI
       ↓
2. FastAPI receives request, extracts JWT claims
       ↓
3. Auth middleware validates admin scope (ai:assistant)
       ↓
4. AdminAssistantUseCase receives question + authenticated user
       ↓
5. AdminAssistantUseCase builds AIExecutionContext:
   - user_id, permissions
   - configured provider + model
   - current timestamp
   - recent conversation history
       ↓
6. AdminAssistantUseCase selects SqlQueryTool (from AITool registry)
       ↓
7. SqlQueryTool.execute(context, {"question": question}):
   a. SchemaProvider.get_schema()  → retrieves DB metadata via MCP
   b. QueryPlanner.plan_query(question, context):
      - PromptTemplate.render_sql_prompt(question, schema, context)
      - AIProvider.generate(sql_prompt)  → receives SQL
      - SQLValidator.validate(sql)  → strict validation + limits
   c. MCPClient.execute_query(sql)  → runs SQL against business DB
   d. QueryPlanner.format_response(question, sql, result, context):
      - PromptTemplate.render_response_prompt(question, sql, result, context)
      - AIProvider.generate(response_prompt)  → natural language answer
   e. ConversationRepository.save(interaction)  → logs to audit table
       ↓
8. Formatted response returned to Open WebUI
```

## Architecture Diagrams

### Container Diagram (C4 Level 2)

```text
┌─────────────────────┐     ┌──────────────────────────────────────┐
│   Open Web UI        │────▶│   FastAPI (AI Module)               │
│   (Admin Chat UI)    │     │   /api/v1/ai/ask                    │
└─────────────────────┘     │   /api/v1/ai/history                 │
                            └──────────┬───────────────────────────┘
                                       │
                     ┌─────────────────┼──────────────────────┐
                     ▼                 ▼                       ▼
        ┌──────────────────┐ ┌─────────────────┐ ┌────────────────────────┐
        │   Groq API        │ │   MCP Toolbox   │ │  PetHouse PostgreSQL  │
        │   (LLM Provider)  │ │   (DB Gateway)  │ │  ├─ business tables   │
        └──────────────────┘ └────────┬────────┘ │  └─ ai_interactions   │
                                      │          └────────────────────────┘
                                      ▼
                           ┌──────────────────┐
                           │  PetHouse DB     │
                           │ (SQLite / PG)    │
                           │  READ ONLY       │
                           └──────────────────┘
```

### Key Interfaces (Domain Layer)

```text
┌──────────────────────────────────────────────────────────────────┐
│                         Domain Layer                             │
│                                                                  │
│  ┌──────────────┐  ┌─────────────────┐  ┌───────────────────┐   │
│  │ AIProvider    │  │ MCPClient        │  │ AITool            │   │
│  │ ──────────── │  │ ──────────────── │  │ ───────────────── │   │
│  │ +generate()  │  │ +get_schema()    │  │ +execute()        │   │
│  └──────────────┘  │ +execute_query() │  │ +description()    │   │
│                    └─────────────────┘  │ +parameters()     │   │
│  ┌──────────────────┐  ┌──────────────┐ └───────────────────┘   │
│  │ PromptTemplate    │  │ SchemaProvider│                         │
│  │ ─────────────────│  │ ─────────────│                         │
│  │ +render_sql()    │  │ +get_schema()│                         │
│  │ +render_resp()   │  └──────────────┘                         │
│  └──────────────────┘                                            │
│  ┌─────────────────────────────────┐  ┌──────────────────────┐   │
│  │ ConversationRepository          │  │ AIExecutionContext    │   │
│  │ ─────────────────────────────── │  │ (value object)       │   │
│  │ +save(interaction)              │  └──────────────────────┘   │
│  │ +get_history(user_id, limit)    │                              │
│  └─────────────────────────────────┘                              │
│  Entities: AIRequest, AIResponse, DatabaseSchema, QueryResult,   │
│  AIInteraction, ColumnMetadata, TableMetadata                     │
└──────────────────────────────────────────────────────────────────┘
```

## Risks / Trade-offs

| Risk | Mitigation |
|------|------------|
| Prompt injection leads to malicious SQL generation | Comprehensive SQL validator denylist + MCP database user with SELECT-only privileges + configurable limits on rows, timeout, query length, JOIN depth |
| Groq API latency or downtime | Configurable timeout per request; health check monitoring; error returned to user with clear message (fallback deferred to future change) |
| LLM hallucinates incorrect SQL | Return generated SQL to admin for transparency; "retry with feedback" loop; temperature set to 0.1 for deterministic output |
| MCP Toolbox becomes a single point of failure | MCPClient interface allows fallback to direct database connection with read-only credentials in a future change |
| Sensitive data leaked via prompt context | SchemaProvider limits exposed metadata to table/column names and types — no row data in schema context |
| Admin JWT token compromised | Token revocation support; short TTL tokens; IP-based rate limiting on AI endpoints |
| Audit table grows unbounded within PetHouse DB | TTL-based retention policy (configurable, default 90 days); monthly cleanup job |
| Configuration drift between environments | YAML config validated at startup with descriptive failure messages; health check verifies Groq connectivity |
| AITool abstraction adds complexity for single tool | Kept simple — SqlQueryTool is the only implementation; new tools added via separate change |

## Implementation Roadmap

The implementation is organized into 10 independently implementable phases.

### Phase 1: Foundation (COMPLETED)
- Package structure with Clean Architecture layers
- `config/ai.yaml` with Groq provider, MCP, and audit configuration
- YAML configuration loader with environment variable resolution and startup validation
- Dependency injection container skeleton
- Python dependencies (groq, httpx, mcp, asyncpg)

### Phase 2: Domain Layer
- Domain entities: AIRequest, AIResponse, DatabaseSchema, QueryResult, AIInteraction, AIExecutionContext
- Domain interfaces: AIProvider, MCPClient, AITool, PromptTemplate, SchemaProvider, ConversationRepository
- All entities are framework-free dataclasses with zero external imports

### Phase 3: Groq Provider
- Implement `GroqProvider` adapter conforming to `AIProvider` interface
- Implement provider health check
- Implement provider factory instantiation from YAML config
- Groq-specific error mapping

### Phase 4: MCP Integration
- Implement `MCPToolboxClient` with schema introspection (table/column metadata only, no row data)
- Implement `MCPToolboxClient` with read-only SQL execution
- Implement `SchemaProvider` wrapping MCP schema data into domain `DatabaseSchema`
- Implement `SQLValidator` with comprehensive denylist and configurable limits (max_rows, timeout, query_length, join_depth)

### Phase 5: Audit Repository
- Create Alembic migration for `ai_interactions` table in existing PetHouse database
- Implement `PostgresConversationRepository` with `save` and `get_history`
- Implement append-only enforcement (no update/delete endpoints)
- Implement TTL-based retention pruning

### Phase 6: Application Use Cases
- Implement `PromptTemplate` with SQL generation and response formatting templates loaded from config
- Implement `QueryPlanner` coordinating schema retrieval, prompt construction, and LLM interaction
- Implement `SqlQueryTool` (first AITool implementation)
- Implement `AdminAssistantUseCase` orchestrating tool selection, execution, and audit logging
- Implement `AIExecutionContext` construction from request context

### Phase 7: FastAPI Presentation
- Add `POST /api/v1/ai/ask` endpoint (admin-only, accepts question, returns answer + SQL + execution time)
- Add `GET /api/v1/ai/history` endpoint (returns admin's interaction history with limit param)
- Implement JWT auth middleware checking `ai:assistant` scope
- Add request validation (reject empty questions, enforce max length)
- Wire dependency injection for all layers

### Phase 8: Docker / Open WebUI / MCP
- Add Open WebUI service to `compose.yaml`
- Add MCP Toolbox service to `compose.yaml`
- Configure MCP Toolbox with READ-ONLY database user credentials
- Configure Open WebUI to point at FastAPI AI endpoints
- Update environment variable templates

### Phase 9: Angular Assistant
- Add AI Assistant panel to the existing Angular frontend
- Integrate with `POST /api/v1/ai/ask` endpoint
- Display question, SQL, answer, and execution time
- Show conversation history panel

### Phase 10: Testing
- Unit tests for domain entities and interfaces
- Unit tests for SQLValidator (all rejected statements + configurable limits)
- Unit tests for PromptTemplate rendering
- Unit tests for QueryPlanner with mock dependencies
- Integration tests for full pipeline with mock provider + test database
- API tests for auth enforcement (401, 403, 422)
- API tests for error scenarios (empty question, provider failure, invalid SQL, timeout)

### Rollback Strategy
- AI module is additive — no changes to existing code paths
- Rollback: remove `app/ai/` module, revert Docker Compose additions, drop `ai_interactions` table
- No impact on existing PetHouse operations

## Open Questions

1. Should the audit log include the raw prompt sent to the LLM for debugging prompt quality? (Yes — remove PII before storage)
2. What is the refresh strategy for database schema caching in the SchemaProvider? (Cache per session with TTL, invalidate on explicit request)
3. Should future AITool implementations share the same AIProvider instance or get dedicated instances? (Shared instance with per-tool model configuration)
4. Should PromptTemplate support Jinja2 or similar for template rendering, or plain Python string formatting? (Jinja2 for flexibility — add dependency)
