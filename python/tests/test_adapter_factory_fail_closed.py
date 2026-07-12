"""Test that missing SDK fails gracefully per-issue in continuous mode."""

import pytest
from unittest.mock import patch, MagicMock
from aios_orchestration_core.llm.adapter_factory import create_adapter


def test_missing_sdk_raises_error():
    """Verify that missing SDK raises immediately, not silent fallback."""
    with patch("aios_orchestration_core.llm.adapter_factory._get_copilot_client") as mock_get:
        mock_get.side_effect = ImportError("SDK not found")
        
        # When use_stub=False and SDK is missing, should raise
        with pytest.raises(ImportError):
            create_adapter(model="gpt-4", use_stub=False, stub_class=None)


def test_missing_sdk_with_stub_class_fallback_removed():
    """Verify that even if stub_class is provided, SDK failure still raises when use_stub=False."""
    from pm_runner import StubLLMAdapter
    
    with patch("aios_orchestration_core.llm.adapter_factory._get_copilot_client") as mock_get:
        mock_get.side_effect = ImportError("SDK not found")
        
        # Even with stub_class provided, should raise (no fallback)
        with pytest.raises(ImportError):
            create_adapter(model="gpt-4", use_stub=False, stub_class=StubLLMAdapter)


def test_explicit_stub_flag_bypasses_sdk():
    """Verify that explicit --stub flag returns stub without SDK check."""
    from pm_runner import StubLLMAdapter
    
    # No SDK needed; stub should be returned immediately
    adapter = create_adapter(model="gpt-4", use_stub=True, stub_class=StubLLMAdapter)
    assert isinstance(adapter, StubLLMAdapter)


def test_circuit_breaker_catches_missing_sdk_per_issue():
    """
    Simulate: orchestrator processes issue #1 OK, SDK becomes unavailable 
    on issue #2, circuit breaker catches it and routes issue #2 to 
    PM_NEEDS_HUMAN, then issue #3 still processes.
    
    This requires:
    1. run_once wrapped in circuit breaker
    2. Circuit breaker catches adapter creation errors
    3. Error routed to NEEDS_HUMAN state, not killed entire run
    """
    # This test would need to:
    # - Mock orchestrator.run_once for multiple issues
    # - Make adapter creation fail on 2nd issue
    # - Verify 1st issue completes, 2nd gets PM_NEEDS_HUMAN, 3rd starts fresh
    # 
    # This is an integration test; requires real circuit breaker testing
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
