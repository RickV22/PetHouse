from typing import Optional

from groq import AsyncGroq
from groq import (
    APIConnectionError as GroqConnectionError,
    APIStatusError as GroqStatusError,
    APITimeoutError as GroqTimeoutError,
    RateLimitError as GroqRateLimitError,
)

from app.ai.domain.entities import AIRequest, AIResponse
from app.ai.domain.interfaces import AIProvider
from app.ai.infrastructure.exceptions import (
    AIProviderAuthError,
    AIProviderConnectionError,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderTimeoutError,
)


class GroqProvider(AIProvider):
    def __init__(
        self,
        api_key: str,
        model: str = "llama-3.3-70b-versatile",
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> None:
        self._client = AsyncGroq(api_key=api_key)
        self._model = model
        self._temperature = temperature
        self._max_tokens = max_tokens

    async def generate(self, request: AIRequest) -> AIResponse:
        temperature = request.temperature if request.temperature is not None else self._temperature
        max_tokens = request.max_tokens if request.max_tokens is not None else self._max_tokens

        messages = []
        if request.system_prompt:
            messages.append({"role": "system", "content": request.system_prompt})
        messages.append({"role": "user", "content": request.prompt})

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
        except GroqRateLimitError as e:
            raise AIProviderRateLimitError(str(e)) from e
        except GroqTimeoutError as e:
            raise AIProviderTimeoutError(str(e)) from e
        except GroqConnectionError as e:
            raise AIProviderConnectionError(str(e)) from e
        except GroqStatusError as e:
            if e.status_code in (413, 429) or "rate_limit" in str(e).lower() or "tokens" in str(e).lower():
                raise AIProviderRateLimitError(str(e)) from e
            if e.status_code == 401:
                raise AIProviderAuthError(str(e)) from e
            raise AIProviderError(str(e)) from e

        choice = response.choices[0]
        usage = None
        if response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

        return AIResponse(
            content=choice.message.content or "",
            finish_reason=choice.finish_reason,
            usage=usage,
        )

    @property
    def model(self) -> str:
        return self._model

    @property
    def client(self) -> AsyncGroq:
        return self._client
