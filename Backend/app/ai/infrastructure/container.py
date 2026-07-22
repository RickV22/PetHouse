from typing import Any, Dict, Optional


class Container:
    _instances: Dict[str, Any] = {}

    def register(self, key: str, instance: Any) -> None:
        self._instances[key] = instance

    def resolve(self, key: str) -> Any:
        instance = self._instances.get(key)
        if instance is None:
            raise KeyError(f"No implementation registered for '{key}'")
        return instance

    def has(self, key: str) -> bool:
        return key in self._instances

    def clear(self) -> None:
        self._instances.clear()


container = Container()
