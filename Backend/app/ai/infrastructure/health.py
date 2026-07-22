from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass
class HealthStatus:
    healthy: bool
    message: str
    checked_at: datetime


class GroqHealthCheck:
    def __init__(self, provider: "GroqProvider") -> None:  # noqa: F821
        self._provider = provider
        self._last_status: HealthStatus | None = None

    async def check(self) -> HealthStatus:
        from app.ai.infrastructure.groq_provider import GroqProvider

        now = datetime.now(timezone.utc)
        try:
            await self._provider.client.models.list()
            status = HealthStatus(
                healthy=True,
                message="Groq API is reachable",
                checked_at=now,
            )
        except Exception as e:
            status = HealthStatus(
                healthy=False,
                message=f"Groq API health check failed: {e}",
                checked_at=now,
            )

        self._last_status = status
        return status

    @property
    def last_status(self) -> HealthStatus | None:
        return self._last_status
