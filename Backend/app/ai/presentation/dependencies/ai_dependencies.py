from functools import lru_cache

from fastapi import Depends, HTTPException, status

from app.ai.config.loader import AIConfig, load_config
from app.ai.domain.interfaces import (
    AIProvider,
    ConversationRepository,
    MCPClient,
    PromptTemplate,
    SchemaProvider,
    SQLValidator,
)
from app.ai.infrastructure.container import container
from app.ai.infrastructure.factory import ProviderFactory
from app.ai.infrastructure.groq_provider import GroqProvider
from app.ai.infrastructure.mcp_client import MCPToolboxClient
from app.ai.infrastructure.prompt_templates import PromptTemplateImpl
from app.ai.infrastructure.repositories import PostgresConversationRepository
from app.ai.infrastructure.schema_provider import MCPSchemaProvider
from app.ai.infrastructure.sql_query_tool import SqlQueryTool
from app.ai.infrastructure.sql_validator import SqlglotSQLValidator
from app.ai.use_cases.admin_assistant import AdminAssistantUseCase
from app.ai.use_cases.query_planner import QueryPlanner
from app.auth.jwt_handler import get_current_user
from app.db.session import SessionLocal
from app.models.user_model import User


@lru_cache
def _load_config() -> AIConfig:
    return load_config()


def _wire() -> AdminAssistantUseCase:
    if container.has("admin_assistant_use_case"):
        return container.resolve("admin_assistant_use_case")

    config = _load_config()

    sql_validator: SQLValidator = SqlglotSQLValidator(
        max_rows=config.sql_validator.max_rows,
        execution_timeout_ms=config.sql_validator.execution_timeout_ms,
        max_query_length=config.sql_validator.max_query_length,
        max_join_depth=config.sql_validator.max_join_depth,
    )
    container.register("sql_validator", sql_validator)

    mcp_client: MCPClient = MCPToolboxClient(
        toolbox_url=config.mcp.toolbox_url,
        sql_validator=sql_validator,
    )
    container.register("mcp_client", mcp_client)

    schema_provider: SchemaProvider = MCPSchemaProvider(mcp_client=mcp_client)
    container.register("schema_provider", schema_provider)

    prompt_template: PromptTemplate = PromptTemplateImpl(
        sql_generation_template=config.prompts.sql_generation,
        response_formatting_template=config.prompts.response_formatting,
    )
    container.register("prompt_template", prompt_template)

    ai_provider: AIProvider = ProviderFactory.create(config)
    container.register("ai_provider", ai_provider)

    model = config.groq.model if hasattr(config.groq, "model") else ""
    if isinstance(ai_provider, GroqProvider):
        model = ai_provider.model

    conversation_repository: ConversationRepository = (
        PostgresConversationRepository(
            session_factory=SessionLocal,
            retention_days=config.audit.retention_days,
        )
    )
    container.register("conversation_repository", conversation_repository)

    query_planner: QueryPlanner = QueryPlanner(
        schema_provider=schema_provider,
        prompt_template=prompt_template,
        ai_provider=ai_provider,
    )
    container.register("query_planner", query_planner)

    sql_query_tool: SqlQueryTool = SqlQueryTool(
        sql_validator=sql_validator,
        mcp_client=mcp_client,
    )
    container.register("sql_query_tool", sql_query_tool)

    use_case = AdminAssistantUseCase(
        query_planner=query_planner,
        sql_query_tool=sql_query_tool,
        prompt_template=prompt_template,
        conversation_repository=conversation_repository,
        provider=config.provider,
        model=model,
    )
    container.register("admin_assistant_use_case", use_case)

    return use_case


def get_admin_assistant_use_case() -> AdminAssistantUseCase:
    return _wire()


def require_ai_assistant(
    current_user: User = Depends(get_current_user),
) -> User:
    if current_user.role_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing ai:assistant permission",
        )
    role = current_user.role
    if role is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing ai:assistant permission",
        )
    permissions = role.permissions
    has_scope = any(p.name == "ai:assistant" for p in permissions)
    if not has_scope:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing ai:assistant permission",
        )
    return current_user
