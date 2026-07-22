from abc import ABC, abstractmethod
from typing import Any, Dict, List

from app.ai.domain.entities import (
    AIExecutionContext,
    AIInteraction,
    AIRequest,
    AIResponse,
    DatabaseSchema,
    QueryResult,
    ValidationResult,
)


class AIProvider(ABC):
    @abstractmethod
    async def generate(self, request: AIRequest) -> AIResponse:
        ...


class MCPClient(ABC):
    @abstractmethod
    async def get_schema(self) -> DatabaseSchema:
        ...

    @abstractmethod
    async def execute_query(self, sql: str) -> QueryResult:
        ...


class PromptTemplate(ABC):
    @abstractmethod
    def render_sql_prompt(
        self, question: str, schema: DatabaseSchema, context: AIExecutionContext
    ) -> str:
        ...

    @abstractmethod
    def render_response_prompt(
        self, question: str, sql: str, result: QueryResult, context: AIExecutionContext
    ) -> str:
        ...


class AITool(ABC):
    @abstractmethod
    async def execute(self, context: AIExecutionContext, params: Dict[str, Any]) -> AIResponse:
        ...

    @abstractmethod
    def description(self) -> str:
        ...

    @abstractmethod
    def parameters(self) -> Dict[str, Any]:
        ...


class SchemaProvider(ABC):
    @abstractmethod
    async def get_database_schema(self) -> DatabaseSchema:
        ...


class SQLValidator(ABC):
    @abstractmethod
    def validate(self, sql: str) -> ValidationResult:
        ...


class ConversationRepository(ABC):
    @abstractmethod
    async def save(self, interaction: AIInteraction) -> None:
        ...

    @abstractmethod
    async def get_history(
        self, user_id: str, limit: int = 20
    ) -> List[AIInteraction]:
        ...
