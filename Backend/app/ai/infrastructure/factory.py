from app.ai.config.loader import AIConfig
from app.ai.domain.interfaces import AIProvider
from app.ai.infrastructure.groq_provider import GroqProvider


class ProviderFactory:
    @staticmethod
    def create(config: AIConfig) -> AIProvider:
        provider_name = config.provider

        if provider_name == "groq":
            return GroqProvider(
                api_key=config.groq.api_key,
                model=config.groq.model,
                temperature=config.groq.temperature,
                max_tokens=config.groq.max_tokens,
            )

        raise ValueError(f"Unsupported provider: '{provider_name}'")
