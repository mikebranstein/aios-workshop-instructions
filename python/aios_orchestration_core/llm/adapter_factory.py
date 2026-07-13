"""Adapter factory for creating LLM adapters with fallback logic."""

import logging
from typing import Optional

from aios_orchestration_core.llm.base import JudgmentLLMAdapter
from aios_orchestration_core.llm.copilot_sdk_adapter import CopilotSDKAdapter, CopilotAdapterConfig
from aios_orchestration_core.llm.copilot_runtime_client import CopilotRuntimeClient

logger = logging.getLogger(__name__)


def create_adapter(
    model: str = "copilot-standard",
    use_stub: bool = False,
    stub_class: Optional[type] = None,
) -> JudgmentLLMAdapter:
    """
    Create an LLM adapter. No silent fallbacks — fails closed on SDK unavailability.
    
    Args:
        model: Model hint to pass to the adapter
        use_stub: If True, use stub adapter; if False, require CopilotSDKAdapter
        stub_class: Custom stub class to use (required if use_stub=True)
    
    Returns:
        JudgmentLLMAdapter: Either CopilotSDKAdapter or StubLLMAdapter
    
    Raises:
        ValueError: If use_stub=True but stub_class not provided
        ImportError: If use_stub=False but Copilot SDK unavailable (fails closed)
        Exception: If use_stub=False but Copilot SDK initialization fails (fails closed)
    
    Note:
        This function fails closed. If Copilot SDK is required (use_stub=False) 
        and unavailable, it raises an error immediately. There are no silent fallbacks.
        Callers must explicitly use --stub to enable stub responses.
    """
    
    if use_stub:
        if stub_class is None:
            raise ValueError("stub_class is required when use_stub=True")
        logger.info(f"Using StubLLMAdapter (explicit --stub flag) with model={model}")
        return stub_class(model)
    
    # Copilot is required when use_stub=False
    # Fail closed if it's not available (do NOT fall back silently)
    try:
        client = _get_copilot_client()
        config = CopilotAdapterConfig(model_default=model)
        logger.info(f"Using CopilotSDKAdapter with model={model}")
        return CopilotSDKAdapter(client, config)
    except ImportError as e:
        logger.error(
            f"FAILED: Copilot SDK not available ({e}). "
            "To use Copilot, ensure the GitHub Copilot SDK is installed. "
            "To use stub (test mode only), pass --stub flag."
        )
        raise
    except Exception as e:
        logger.error(
            f"FAILED: Could not initialize Copilot adapter: {e}. "
            "Check SDK configuration and try again. "
            "To use stub (test mode only), pass --stub flag."
        )
        raise


def _get_copilot_client():
    """
    Get the Copilot SDK client. Fails closed if unavailable.
    
    Raises:
        ImportError: If Copilot SDK is not available or cannot be imported
    """
    try:
        # Ensure SDK package is importable, then return runtime wrapper.
        import copilot  # noqa: F401
        return CopilotRuntimeClient()
    except ImportError:
        raise ImportError(
            "GitHub Copilot SDK not found. Install with: pip install github-copilot-sdk"
        )
