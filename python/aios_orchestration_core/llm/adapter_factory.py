"""Adapter factory for creating LLM adapters with fallback logic."""

import logging
from typing import Optional

from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.llm.copilot_sdk_adapter import CopilotSDKAdapter, CopilotAdapterConfig

logger = logging.getLogger(__name__)


def create_adapter(
    model: str = "gpt-4",
    use_stub: bool = False,
    stub_class: Optional[type] = None,
) -> JudgmentLLMAdapter:
    """
    Create an LLM adapter with fallback logic.
    
    Args:
        model: Model hint to pass to the adapter
        use_stub: If True, use stub adapter; if False, try Copilot then fall back to stub
        stub_class: Custom stub class to use (required if use_stub=True or on fallback)
    
    Returns:
        JudgmentLLMAdapter: Either CopilotSDKAdapter or StubLLMAdapter
    
    Note:
        When use_stub=False (default), this attempts to use CopilotSDKAdapter.
        If the Copilot SDK is not available, it falls back to StubLLMAdapter with a warning.
        The stub_class parameter must be provided by the caller (typically from the runner script).
    """
    
    if use_stub:
        if stub_class is None:
            raise ValueError("stub_class is required when use_stub=True")
        return stub_class(model)
    
    # Try to create Copilot adapter
    try:
        # Try to get the Copilot SDK client
        # This would typically come from the GitHub Copilot extension or SDK
        client = _get_copilot_client()
        config = CopilotAdapterConfig(model_default=model)
        logger.info(f"Using CopilotSDKAdapter with model={model}")
        return CopilotSDKAdapter(client, config)
    except ImportError as e:
        logger.warning(
            f"Copilot SDK not available ({e}). Falling back to StubLLMAdapter. "
            "To use Copilot, ensure the GitHub Copilot SDK is installed."
        )
        if stub_class is None:
            raise ValueError(
                "Copilot SDK unavailable and no fallback stub_class provided. "
                "Pass stub_class to create_adapter() or use --stub flag."
            )
        logger.warning("Using StubLLMAdapter - LLM calls will return stub responses")
        return stub_class(model)
    except Exception as e:
        logger.warning(
            f"Failed to initialize Copilot adapter: {e}. "
            "Falling back to StubLLMAdapter."
        )
        if stub_class is None:
            raise ValueError(
                f"Failed to initialize Copilot adapter ({e}) and no fallback stub_class provided. "
                "Pass stub_class to create_adapter() or use --stub flag."
            )
        logger.warning("Using StubLLMAdapter - LLM calls will return stub responses")
        return stub_class(model)


def _get_copilot_client():
    """
    Get the Copilot SDK client.
    
    Raises:
        ImportError: If Copilot SDK is not available
    """
    try:
        # Try importing from GitHub Copilot SDK
        # This is a placeholder - adjust import based on actual SDK availability
        from github_copilot_sdk import CopilotClient
        
        # Initialize with default configuration
        client = CopilotClient()
        return client
    except ImportError:
        raise ImportError(
            "GitHub Copilot SDK not found. Install with: pip install github-copilot-sdk"
        )
