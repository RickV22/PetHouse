from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class AIRequest:
    prompt: str
    system_prompt: Optional[str] = None
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None


@dataclass
class AIResponse:
    content: str
    finish_reason: Optional[str] = None
    usage: Optional[Dict[str, int]] = None


@dataclass
class ColumnMetadata:
    name: str
    type: str
    nullable: bool = True
    is_primary_key: bool = False
    foreign_key: Optional[str] = None
    description: Optional[str] = None
    default_value: Optional[str] = None


@dataclass
class TableMetadata:
    name: str
    columns: List[ColumnMetadata] = field(default_factory=list)
    description: Optional[str] = None


@dataclass
class DatabaseSchema:
    tables: List[TableMetadata] = field(default_factory=list)


@dataclass
class QueryResult:
    columns: List[str] = field(default_factory=list)
    rows: List[Tuple[Any, ...]] = field(default_factory=list)
    row_count: int = 0
    execution_ms: int = 0


@dataclass
class AIInteraction:
    interaction_id: str
    user_id: str
    question: str
    generated_sql: Optional[str] = None
    execution_ms: Optional[int] = None
    response: Optional[str] = None
    provider: str = ""
    created_at: Optional[datetime] = None


@dataclass
class ValidationResult:
    is_valid: bool
    error: Optional[str] = None
    sql: str = ""
    max_rows: int = 1000
    execution_timeout_ms: int = 30000


@dataclass
class PlannedQuery:
    sql: str
    schema: DatabaseSchema
    prompt: str


@dataclass
class AIExecutionContext:
    user_id: str
    permissions: List[str] = field(default_factory=list)
    provider: str = ""
    model: str = ""
    database_schema: Optional[DatabaseSchema] = None
    conversation_history: List[AIInteraction] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    timestamp: Optional[datetime] = None


@dataclass
class AskResult:
    answer: str
    generated_sql: str
    execution_ms: int
    provider: str
    model: str
    interaction_id: str
    created_at: datetime
