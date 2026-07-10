"""AI layer exceptions."""

from __future__ import annotations

from models.common import PlatformError


class AIError(PlatformError):
    """Base exception for AI layer errors."""

    def __init__(self, message: str, *, code: str = "ai_error") -> None:
        super().__init__(message, code=code)


class AgentNotFoundError(AIError):
    """Raised when a requested agent is not registered."""

    def __init__(self, agent_id: str) -> None:
        super().__init__(f"Agent not found: {agent_id}", code="agent_not_found")
        self.agent_id = agent_id


class AgentRegistrationError(AIError):
    """Raised when agent registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="agent_registration_error")


class AgentStateError(AIError):
    """Raised when an invalid agent state transition is attempted."""

    def __init__(self, agent_id: str, current_state: str, operation: str) -> None:
        super().__init__(
            f"Cannot {operation} agent '{agent_id}' in state '{current_state}'",
            code="agent_state_error",
        )
        self.agent_id = agent_id
        self.current_state = current_state
        self.operation = operation


class PromptNotFoundError(AIError):
    """Raised when a requested prompt is not registered."""

    def __init__(self, prompt_id: str) -> None:
        super().__init__(f"Prompt not found: {prompt_id}", code="prompt_not_found")
        self.prompt_id = prompt_id


class PromptRegistrationError(AIError):
    """Raised when prompt registration fails."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="prompt_registration_error")


class LLMProviderNotFoundError(AIError):
    """Raised when a requested LLM provider is not registered."""

    def __init__(self, provider_id: str) -> None:
        super().__init__(f"LLM provider not found: {provider_id}", code="llm_provider_not_found")
        self.provider_id = provider_id


class LLMProviderError(AIError):
    """Raised when LLM provider operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="llm_provider_error")


class ReasoningError(AIError):
    """Raised when reasoning operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="reasoning_error")


class OrchestrationError(AIError):
    """Raised when AI orchestration operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="orchestration_error")


class MemoryStoreError(AIError):
    """Raised when memory store operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="memory_store_error")


class AIEvaluationError(AIError):
    """Raised when AI evaluation operations fail."""

    def __init__(self, message: str) -> None:
        super().__init__(message, code="ai_evaluation_error")
