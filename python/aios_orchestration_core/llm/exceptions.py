class LLMAdapterError(RuntimeError):
    """Base error for LLM adapter failures."""


class CapabilityProbeFailed(LLMAdapterError):
    """Raised when forced tool-call capability is unavailable."""


class ForcedToolCallMissing(LLMAdapterError):
    """Raised when model response does not contain the required tool call."""


class ToolSchemaValidationError(LLMAdapterError):
    """Raised when tool payload fails schema validation."""
