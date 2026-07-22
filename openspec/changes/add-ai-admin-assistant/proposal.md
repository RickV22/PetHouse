## Why

PetHouse needs an enterprise-grade AI platform that goes beyond the existing basic Ollama chatbot. Administrators currently lack a natural language interface to query business data — they must write raw SQL or rely on developers for simple questions like adoption counts or vaccination statuses. This creates bottlenecks, reduces self-service capability, and limits data-driven decision making.

## What Changes

- **New AI Platform module** — A reusable, Clean Architecture-based AI core capable of supporting multiple future AI features (Veterinary Assistant, Adoption Analytics, Report Generation, Recommendation Engine)
- **Administrative AI Assistant** — First implementation allowing admins to ask natural language questions and receive SQL-generated answers
- **Open WebUI integration** — Chat interface layer for the admin assistant
- **Groq integration** — Primary AI provider for NL-to-SQL and response generation (single provider for this change)
- **MCP Toolbox integration** — Read-only database schema and query execution tooling
- **MCP Client interface** — Abstracted MCP interaction for testability and future provider swapping
- **AI audit tables** — Audit logging within the existing PetHouse PostgreSQL database (no separate instance)
- **AITool extension system** — Generic plugin interface where SQL execution is the first tool implementation
- **QueryPlanner** — Application service that coordinates schema retrieval, prompt construction, and LLM interaction
- **PromptTemplate management** — Externalized prompt templates not embedded in provider code
- **YAML-based configuration system** — Single-provider (Groq) configuration with provider health check
- **Admin-only authentication gate** — JWT-authorized access control for the assistant
- **Full audit trail** — Every interaction logged: user, question, generated SQL, execution time, response, provider, timestamp

**Not changing:**
- Existing Ollama chatbot remains untouched
- No modifications to existing business logic or API contracts
- No changes to current database schema (pet_house.db)

## Capabilities

### New Capabilities
- `ai-platform-core`: Reusable Clean Architecture AI platform with abstract interfaces for AIProvider, MCPClient, AITool, SchemaProvider, PromptTemplate, ConversationRepository, and AIExecutionContext — the foundation for all future AI capabilities
- `ai-admin-assistant`: Administrative AI Assistant that accepts natural language questions, translates them to read-only SQL queries via the AITool system against the business database, and returns formatted answers via Open WebUI
- `ai-audit-logging`: Persistent audit trail stored in the existing PetHouse PostgreSQL database for every AI interaction
- `ai-provider-configuration`: YAML-driven Groq provider configuration with startup validation and health check
- `ai-prompts`: Externalized PromptTemplate management for SQL generation and response formatting, designed for future extensibility

### Modified Capabilities
- None (no existing specs require modification)

## Impact

| Area | Impact |
|------|--------|
| **Backend** | New Python module `app/ai/` following Clean Architecture layers (domain, application, infrastructure, presentation) |
| **Database** | New `ai_interactions` table in the existing PetHouse PostgreSQL database; read-only MCP connection to existing SQLite/PostgreSQL business database |
| **Configuration** | New `config/ai.yaml` for Groq provider settings, MCP connection, and audit configuration |
| **Docker Compose** | New services: Open WebUI, MCP Toolbox container |
| **Authentication** | New permission scope `ai:assistant` for admin-only access |
| **Existing Systems** | No changes to existing Ollama chatbot, Angular frontend, SvelteKit frontend, or business API |

## Future Work (post-this-change)

The following capabilities are deferred to separate OpenSpec changes:
- Multi-provider support (Ollama, OpenAI, Anthropic)
- Provider fallback logic
- Multi-agent orchestration
- Provider hot-swapping at runtime
