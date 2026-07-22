import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# Config loader
# ---------------------------------------------------------------------------

class TestConfigLoader:
    def setup_method(self):
        os.environ["GROQ_API_KEY"] = "test-key-123"
        os.environ["AI_DB_TYPE"] = "postgresql"
        os.environ["AI_DB_CONNECTION"] = "postgresql://u:p@h/db"

    def teardown_method(self):
        for k in ("GROQ_API_KEY", "AI_DB_TYPE", "AI_DB_CONNECTION",
                  "AUDIT_DB_HOST", "AUDIT_DB_USER", "AUDIT_DB_PASSWORD"):
            os.environ.pop(k, None)

    def test_load_config_success(self):
        from app.ai.config.loader import load_config

        cfg_path = os.path.normpath(
            os.path.join(os.path.dirname(__file__), "..", "config/ai.yaml")
        )
        cfg = load_config(cfg_path)
        assert cfg.provider == "groq"
        assert cfg.groq.api_key == "test-key-123"
        assert cfg.groq.model == "llama-3.3-70b-versatile"
        assert cfg.groq.temperature == 0.1
        assert cfg.groq.max_tokens == 4096
        assert cfg.mcp.toolbox_url == "http://mcp-toolbox:5000/mcp"
        assert cfg.mcp.database.connection_string == "postgresql://u:p@h/db"
        assert cfg.sql_validator.max_rows == 1000
        assert cfg.sql_validator.execution_timeout_ms == 30000
        assert cfg.audit.enabled is True
        assert cfg.audit.retention_days == 90
        assert "SELECT" in cfg.prompts.sql_generation
        assert "Answer:" in cfg.prompts.response_formatting

    def test_load_config_missing_key_fails(self):
        from app.ai.config.loader import load_config, _validate_config

        os.environ.pop("GROQ_API_KEY")
        raw = {
            "ai": {
                "provider": "groq",
                "groq": {"api_key": "${GROQ_API_KEY}"},
                "mcp": {
                    "toolbox_url": "http://mcp:5000/mcp",
                    "database": {"type": "pg", "connection_string": "pg://"},
                },
            }
        }
        with pytest.raises(ValueError, match="GROQ_API_KEY"):
            _validate_config(raw)

    def test_load_config_missing_file(self):
        from app.ai.config.loader import load_config

        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path.yaml")


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------

class TestExceptions:
    def test_exception_hierarchy(self):
        from app.ai.infrastructure.exceptions import (
            AIProviderAuthError,
            AIProviderConnectionError,
            AIProviderError,
            AIProviderRateLimitError,
            AIProviderTimeoutError,
        )

        assert issubclass(AIProviderAuthError, AIProviderError)
        assert issubclass(AIProviderRateLimitError, AIProviderError)
        assert issubclass(AIProviderTimeoutError, AIProviderError)
        assert issubclass(AIProviderConnectionError, AIProviderError)

    def test_exceptions_carry_message(self):
        from app.ai.infrastructure.exceptions import AIProviderError

        e = AIProviderError("test message")
        assert str(e) == "test message"


# ---------------------------------------------------------------------------
# GroqProvider
# ---------------------------------------------------------------------------

@pytest.fixture
def mock_groq_client():
    with patch("app.ai.infrastructure.groq_provider.AsyncGroq") as mock:
        client = MagicMock()
        mock.return_value = client
        yield client


class TestGroqProvider:
    def test_instantiation(self):
        from app.ai.infrastructure.groq_provider import GroqProvider

        provider = GroqProvider(api_key="test", model="llama3")
        assert provider.model == "llama3"

    @pytest.mark.asyncio
    async def test_generate_success(self, mock_groq_client):
        from app.ai.domain.entities import AIRequest
        from app.ai.infrastructure.groq_provider import GroqProvider

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "SELECT 1"
        mock_response.choices[0].finish_reason = "stop"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        mock_groq_client.chat.completions.create = AsyncMock(return_value=mock_response)

        provider = GroqProvider(api_key="test", model="llama3")
        result = await provider.generate(AIRequest(prompt="say hi"))

        assert result.content == "SELECT 1"
        assert result.finish_reason == "stop"
        assert result.usage == {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15}

    @pytest.mark.asyncio
    async def test_generate_with_system_prompt(self, mock_groq_client):
        from app.ai.domain.entities import AIRequest
        from app.ai.infrastructure.groq_provider import GroqProvider

        mock_groq_client.chat.completions.create = AsyncMock(
            return_value=MagicMock(
                choices=[MagicMock(message=MagicMock(content="ok", finish_reason="stop"))],
                usage=None,
            )
        )

        provider = GroqProvider(api_key="test")
        await provider.generate(AIRequest(prompt="hi", system_prompt="be concise"))

        call_kwargs = mock_groq_client.chat.completions.create.call_args
        messages = call_kwargs[1]["messages"]
        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "be concise"
        assert messages[1]["role"] == "user"

    @pytest.mark.asyncio
    async def test_generate_rate_limit_error(self, mock_groq_client):
        from app.ai.domain.entities import AIRequest
        from app.ai.infrastructure.exceptions import AIProviderRateLimitError
        from app.ai.infrastructure.groq_provider import GroqProvider
        from groq import RateLimitError

        mock_groq_client.chat.completions.create = AsyncMock(
            side_effect=RateLimitError("rate limited", response=MagicMock(), body=None)
        )

        provider = GroqProvider(api_key="test")
        with pytest.raises(AIProviderRateLimitError):
            await provider.generate(AIRequest(prompt="hi"))

    @pytest.mark.asyncio
    async def test_generate_auth_error(self, mock_groq_client):
        from app.ai.domain.entities import AIRequest
        from app.ai.infrastructure.exceptions import AIProviderAuthError
        from app.ai.infrastructure.groq_provider import GroqProvider
        from groq import APIStatusError

        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_groq_client.chat.completions.create = AsyncMock(
            side_effect=APIStatusError("unauthorized", response=mock_response, body=None)
        )

        provider = GroqProvider(api_key="bad-key")
        with pytest.raises(AIProviderAuthError):
            await provider.generate(AIRequest(prompt="hi"))

    @pytest.mark.asyncio
    async def test_generate_timeout_error(self, mock_groq_client):
        from app.ai.domain.entities import AIRequest
        from app.ai.infrastructure.exceptions import AIProviderTimeoutError
        from app.ai.infrastructure.groq_provider import GroqProvider
        from groq import APITimeoutError

        mock_groq_client.chat.completions.create = AsyncMock(
            side_effect=APITimeoutError("timed out")
        )

        provider = GroqProvider(api_key="test")
        with pytest.raises(AIProviderTimeoutError):
            await provider.generate(AIRequest(prompt="hi"))

    @pytest.mark.asyncio
    async def test_generate_connection_error(self, mock_groq_client):
        from app.ai.domain.entities import AIRequest
        from app.ai.infrastructure.exceptions import AIProviderConnectionError
        from app.ai.infrastructure.groq_provider import GroqProvider
        from groq import APIConnectionError

        mock_request = MagicMock()
        mock_groq_client.chat.completions.create = AsyncMock(
            side_effect=APIConnectionError(message="connection failed", request=mock_request)
        )

        provider = GroqProvider(api_key="test")
        with pytest.raises(AIProviderConnectionError):
            await provider.generate(AIRequest(prompt="hi"))

    @pytest.mark.asyncio
    async def test_request_overrides_defaults(self, mock_groq_client):
        from app.ai.domain.entities import AIRequest
        from app.ai.infrastructure.groq_provider import GroqProvider

        mock_groq_client.chat.completions.create = AsyncMock(
            return_value=MagicMock(
                choices=[MagicMock(message=MagicMock(content="x", finish_reason="stop"))],
                usage=None,
            )
        )

        provider = GroqProvider(api_key="test", temperature=0.5, max_tokens=100)
        await provider.generate(AIRequest(prompt="hi", temperature=0.9, max_tokens=200))

        call_kwargs = mock_groq_client.chat.completions.create.call_args
        assert call_kwargs[1]["temperature"] == 0.9
        assert call_kwargs[1]["max_tokens"] == 200


# ---------------------------------------------------------------------------
# ProviderFactory
# ---------------------------------------------------------------------------

class TestProviderFactory:
    def test_create_groq(self):
        from app.ai.config.loader import AIConfig, GroqConfig
        from app.ai.infrastructure.factory import ProviderFactory
        from app.ai.infrastructure.groq_provider import GroqProvider

        config = AIConfig(
            provider="groq",
            groq=GroqConfig(api_key="test", model="llama3", temperature=0.5, max_tokens=2048),
        )
        provider = ProviderFactory.create(config)
        assert isinstance(provider, GroqProvider)
        assert provider.model == "llama3"

    def test_create_unsupported_provider(self):
        from app.ai.config.loader import AIConfig
        from app.ai.infrastructure.factory import ProviderFactory

        config = AIConfig(provider="ollama")
        with pytest.raises(ValueError, match="ollama"):
            ProviderFactory.create(config)


# ---------------------------------------------------------------------------
# Health check
# ---------------------------------------------------------------------------

class TestGroqHealthCheck:
    @pytest.mark.asyncio
    async def test_health_check_success(self):
        from app.ai.infrastructure.groq_provider import GroqProvider
        from app.ai.infrastructure.health import GroqHealthCheck

        provider = GroqProvider(api_key="test")
        provider._client.models.list = AsyncMock(return_value=None)

        hc = GroqHealthCheck(provider)
        status = await hc.check()

        assert status.healthy is True
        assert "reachable" in status.message

    @pytest.mark.asyncio
    async def test_health_check_failure(self):
        from app.ai.infrastructure.groq_provider import GroqProvider
        from app.ai.infrastructure.health import GroqHealthCheck

        provider = GroqProvider(api_key="test")
        provider._client.models.list = AsyncMock(side_effect=Exception("API down"))

        hc = GroqHealthCheck(provider)
        status = await hc.check()

        assert status.healthy is False
        assert "API down" in status.message

    @pytest.mark.asyncio
    async def test_health_check_tracks_last_status(self):
        from app.ai.infrastructure.groq_provider import GroqProvider
        from app.ai.infrastructure.health import GroqHealthCheck

        provider = GroqProvider(api_key="test")
        provider._client.models.list = AsyncMock(return_value=None)

        hc = GroqHealthCheck(provider)
        assert hc.last_status is None
        await hc.check()
        assert hc.last_status is not None
        assert hc.last_status.healthy is True


# ---------------------------------------------------------------------------
# Dependency injection container
# ---------------------------------------------------------------------------

class TestContainer:
    def test_register_and_resolve(self):
        from app.ai.infrastructure.container import Container

        c = Container()
        c.register("ai.provider", "groq")
        assert c.resolve("ai.provider") == "groq"

    def test_resolve_unregistered_raises(self):
        from app.ai.infrastructure.container import Container

        c = Container()
        with pytest.raises(KeyError):
            c.resolve("nonexistent")

    def test_clear(self):
        from app.ai.infrastructure.container import Container

        c = Container()
        c.register("x", 1)
        c.clear()
        assert c.has("x") is False

    def test_global_container(self):
        from app.ai.infrastructure.container import container

        container.clear()
        container.register("test", 42)
        assert container.resolve("test") == 42
