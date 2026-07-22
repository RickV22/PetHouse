class AIProviderError(Exception):
    pass


class AIProviderAuthError(AIProviderError):
    pass


class AIProviderRateLimitError(AIProviderError):
    pass


class AIProviderTimeoutError(AIProviderError):
    pass


class AIProviderConnectionError(AIProviderError):
    pass


class MCPError(Exception):
    pass


class MCPConnectionError(MCPError):
    pass


class MCPTimeoutError(MCPError):
    pass


class MCPExecutionError(MCPError):
    pass


class MCPInvalidResponseError(MCPError):
    pass
