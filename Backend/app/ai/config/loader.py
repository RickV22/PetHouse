import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import yaml


ENV_VAR_PATTERN = re.compile(r"\$\{([^}]+)\}")


def _resolve_env_vars(value: Any) -> Any:
    if isinstance(value, str):
        def _replace(match: re.Match) -> str:
            var_name = match.group(1)
            return os.environ.get(var_name, match.group(0))
        return ENV_VAR_PATTERN.sub(_replace, value)
    if isinstance(value, dict):
        return {k: _resolve_env_vars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve_env_vars(item) for item in value]
    return value


@dataclass
class GroqConfig:
    api_key: str = ""
    model: str = "llama-3.3-70b-versatile"
    temperature: float = 0.1
    max_tokens: int = 4096


@dataclass
class HealthCheckConfig:
    enabled: bool = True
    interval_seconds: int = 60
    timeout_seconds: int = 10


@dataclass
class MCPDatabaseConfig:
    type: str = ""
    connection_string: str = ""


@dataclass
class MCPConfig:
    toolbox_url: str = ""
    database: MCPDatabaseConfig = field(default_factory=MCPDatabaseConfig)


@dataclass
class SQLValidatorConfig:
    max_rows: int = 1000
    execution_timeout_ms: int = 30000
    max_query_length: int = 10000
    max_join_depth: int = 5


@dataclass
class AuditConfig:
    enabled: bool = True
    retention_days: int = 90


@dataclass
class PromptsConfig:
    sql_generation: str = ""
    response_formatting: str = ""


@dataclass
class AIConfig:
    provider: str = ""
    max_question_length: int = 1000
    groq: GroqConfig = field(default_factory=GroqConfig)
    health_check: HealthCheckConfig = field(default_factory=HealthCheckConfig)
    mcp: MCPConfig = field(default_factory=MCPConfig)
    sql_validator: SQLValidatorConfig = field(default_factory=SQLValidatorConfig)
    audit: AuditConfig = field(default_factory=AuditConfig)
    prompts: PromptsConfig = field(default_factory=PromptsConfig)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIConfig":
        ai = data.get("ai", {})
        max_question_length = int(ai.get("max_question_length", 1000))
        groq_raw = ai.get("groq", {})
        groq = GroqConfig(
            api_key=groq_raw.get("api_key", ""),
            model=groq_raw.get("model", "llama-3.3-70b-versatile"),
            temperature=float(groq_raw.get("temperature", 0.1)),
            max_tokens=int(groq_raw.get("max_tokens", 4096)),
        )

        hc_raw = ai.get("health_check", {})
        health_check = HealthCheckConfig(
            enabled=bool(hc_raw.get("enabled", True)),
            interval_seconds=int(hc_raw.get("interval_seconds", 60)),
            timeout_seconds=int(hc_raw.get("timeout_seconds", 10)),
        )

        mcp_raw = ai.get("mcp", {})
        db_raw = mcp_raw.get("database", {})
        mcp = MCPConfig(
            toolbox_url=mcp_raw.get("toolbox_url", ""),
            database=MCPDatabaseConfig(
                type=db_raw.get("type", ""),
                connection_string=db_raw.get("connection_string", ""),
            ),
        )

        sv_raw = ai.get("sql_validator", {})
        sql_validator = SQLValidatorConfig(
            max_rows=int(sv_raw.get("max_rows", 1000)),
            execution_timeout_ms=int(sv_raw.get("execution_timeout_ms", 30000)),
            max_query_length=int(sv_raw.get("max_query_length", 10000)),
            max_join_depth=int(sv_raw.get("max_join_depth", 5)),
        )

        audit_raw = ai.get("audit", {})
        audit = AuditConfig(
            enabled=bool(audit_raw.get("enabled", True)),
            retention_days=int(audit_raw.get("retention_days", 90)),
        )

        prompts_raw = ai.get("prompts", {})
        prompts = PromptsConfig(
            sql_generation=prompts_raw.get("sql_generation", ""),
            response_formatting=prompts_raw.get("response_formatting", ""),
        )

        return cls(
            provider=ai.get("provider", ""),
            max_question_length=max_question_length,
            groq=groq,
            health_check=health_check,
            mcp=mcp,
            sql_validator=sql_validator,
            audit=audit,
            prompts=prompts,
        )


def _validate_config(raw: Dict[str, Any]) -> None:
    ai = raw.get("ai")
    if not ai:
        raise ValueError("Configuration missing required 'ai' section")

    provider = ai.get("provider")
    if not provider:
        raise ValueError("Configuration missing required 'ai.provider'")

    if provider not in ("groq",):
        raise ValueError(
            f"Unsupported provider '{provider}'. Supported: groq"
        )

    groq = ai.get("groq")
    if not groq:
        raise ValueError("Configuration missing required 'ai.groq' section")

    mcp = ai.get("mcp")
    if not mcp:
        raise ValueError("Configuration missing required 'ai.mcp' section")

    mcp_db = mcp.get("database")
    if not mcp_db or not mcp_db.get("connection_string"):
        raise ValueError(
            "Configuration missing required 'ai.mcp.database.connection_string'"
        )

    unresolved = _find_unresolved_vars(raw)
    if unresolved:
        raise ValueError(
            f"Unresolved environment variables: {', '.join(unresolved)}"
        )


def _find_unresolved_vars(value: Any) -> List[str]:
    found: List[str] = []

    def _walk(v: Any) -> None:
        if isinstance(v, str):
            for match in ENV_VAR_PATTERN.finditer(v):
                var = match.group(1)
                if var not in os.environ:
                    found.append(var)
        elif isinstance(v, dict):
            for item in v.values():
                _walk(item)
        elif isinstance(v, list):
            for item in v:
                _walk(item)

    _walk(value)
    return found


def load_config(path: Optional[str] = None) -> AIConfig:
    if path is None:
        path = os.environ.get("AI_CONFIG_PATH", "config/ai.yaml")

    if not os.path.exists(path):
        raise FileNotFoundError(
            f"AI configuration file not found at '{path}'. "
            f"Set AI_CONFIG_PATH environment variable or create config/ai.yaml."
        )

    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    if raw is None:
        raise ValueError(f"AI configuration file '{path}' is empty")

    _validate_config(raw)

    resolved = _resolve_env_vars(raw)

    return AIConfig.from_dict(resolved)
