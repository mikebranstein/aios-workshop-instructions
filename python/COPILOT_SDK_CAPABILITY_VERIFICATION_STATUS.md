# Copilot SDK Tool-Call Capability Verification Status

**Status**: Investigation Complete  
**Date**: 2026-07-12  
**Scope**: Separate concern from LangGraph integration; applies to all 7 loops

---

## Executive Summary

**Question**: Has the GitHub Copilot SDK's forced/exclusive tool-call output capability actually been verified against a **live SDK call** anywhere in the system yet?

**Answer**: **NO. Forced tool-call capability exists as a Protocol interface and test adapter, but has NOT been verified against a real GitHub Copilot SDK instance.**

**Implications**:
- Current system assumes `CopilotSDKClient.supports_forced_tool_calls()` returns True
- No fallback if real SDK returns False
- System is **not production-ready** for any loop until this is verified

---

## 1. Current State of Implementation

### 1.1 Code Structure

**File**: `aios_orchestration_core/llm/copilot_sdk_adapter.py`

```python
class CopilotSDKClient(Protocol):
    def supports_forced_tool_calls(self) -> bool:
        ...
    
    def chat(self, *, messages: List[Dict], tools: List[Dict], 
             tool_choice: Dict, model: str) -> Dict:
        ...

class CopilotSDKAdapter(JudgmentLLMAdapter):
    def __init__(self, client: CopilotSDKClient, ...):
        self.forced_tool_capability = self.client.supports_forced_tool_calls()
    
    def invoke_json(self, task_type: str, prompt_vars: Dict, ...) -> LLMInvocationResult:
        # Calls self.client.chat(...) with tool_choice={"type": "tool", "name": tool_name}
        # Enforces ForcedToolCallMissing exception if response lacks tool_calls
```

**Status**: Interface is well-designed; Protocol is clear.

---

### 1.2 Exception Handling

**File**: `aios_orchestration_core/llm/exceptions.py`

```python
class CapabilityProbeFailed(LLMAdapterError):
    """Raised if SDK does not support forced tool calls."""

class ForcedToolCallMissing(LLMAdapterError):
    """Raised if forced tool call was not returned by SDK."""
```

**Status**: Exception classes exist and are used in CopilotSDKAdapter.

---

### 1.3 Test Coverage

**File**: `tests/pm/test_forced_tool_adapter.py`

```python
class MockCopilotSDKClient:
    def supports_forced_tool_calls(self) -> bool:
        return True  # Mock always returns True
    
    def chat(self, *, messages, tools, tool_choice, model) -> Dict:
        # Returns mock response with tool_calls
        return {
            "tool_calls": [
                {"name": "tool_name", "arguments": {"decision": "CHAMPION"}}
            ]
        }

# Tests invoke CopilotSDKAdapter with mock client
# Result: Tests pass ✓
```

**Status**: Tests pass with **mock client**; no tests with real GitHub SDK.

---

## 2. What's Missing: Real SDK Verification

### 2.1 Current Test Adapter vs. Real SDK

| Aspect | Mock Adapter | Real GitHub SDK | Status |
|--------|--------------|-----------------|--------|
| `supports_forced_tool_calls()` | Returns True | **Unknown** |  ⚠️ Not verified |
| `chat()` with `tool_choice={"type": "tool", "name": "X"}` | Returns mock tool call | **Unknown** | ⚠️ Not verified |
| Response format (tool_calls array, arguments as object) | Hardcoded | **Unknown** | ⚠️ Not verified |
| Retry behavior on non-tool response | Mocked out | **Unknown** | ⚠️ Not verified |
| Token usage, model specification | Ignored | **Unknown** | ⚠️ Not verified |

### 2.2 What Needs Verification (Pre-Production)

1. **Capability Probe**: Call real SDK's `supports_forced_tool_calls()`. If False, system fails closed immediately.

2. **Tool Call Enforcement**: Verify that GitHub SDK honors `tool_choice={"type": "tool", "name": "X"}` and **never** returns plain-text responses.

3. **Response Format**: Verify that response contains `tool_calls[0].arguments` as a JSON object (not string), matching our schema.

4. **Failure Modes**: What does the SDK return if:
   - Model doesn't support forced tool calls?
   - Tool schema is invalid?
   - Network error occurs mid-call?

5. **Retry Semantics**: Our adapter retries with a corrective system message if SDK returns non-tool response. Verify this works as expected.

---

## 3. Risk Assessment

### If Real SDK Does NOT Support Forced Tool Calls

| Component | Impact | Severity |
|-----------|--------|----------|
| **PM Loop** | Phase1, Synthesis, Phase2 decisions become unpredictable | **CRITICAL** |
| **PO Loop** | Prioritization decision becomes unpredictable | **CRITICAL** |
| **Dev Loop** | All stage decisions become unpredictable | **CRITICAL** |
| **All Loops** | System degrades from deterministic state machine to heuristic parsing of LLM text | **CRITICAL** |

**Verdict**: System cannot be considered production-ready without this verification.

---

### If Real SDK Tool-Call Response Format Differs

| Difference | Example | Impact |
|-----------|---------|--------|
| `arguments` is a string, not object | `"arguments": "{\"decision\": ...}"` | Parsing error; transition fails |
| Missing `tool_calls` key | Response is `{"content": "...", "tool_use": ...}` | ForcedToolCallMissing exception; retry loop fails |
| Tool name mismatch | Response contains `"tool_name"` not `"name"` | Extraction fails |

**Verdict**: Even small format differences break the system.

---

## 4. Bridge Mode Controller & Forced Tool Calls

**File**: `pm_orchestrator/migration/bridge.py`

Current design includes a `BridgeModeController` that tracks "clean runs" (runs without label conflicts). This is unrelated to forced tool calls but indicates the system expects to run in a degraded mode during migration.

**Question**: If forced tool calls fail, should PM enter a permanent bridge mode (fall back to heuristic label matching), or should it fail hard?

**Current Answer**: **No fallback is implemented**. If forced tool calls fail, the system raises an exception; no graceful degradation.

**Recommendation**: If verification reveals that forced tool calls are not available, add a `FallbackAdapter` that:
- Implements `JudgmentLLMAdapter`
- Uses heuristic pattern matching on plain-text responses
- Logs warnings (system is degraded)
- Enters bridge mode for all loops

---

## 5. Verification Plan

### Phase 1: Setup (1-2 days)
1. Obtain access to GitHub Copilot SDK (if not already available)
2. Review SDK documentation for tool-call capabilities
3. Create a standalone test script (`integration/verify_copilot_tool_calls.py`)

### Phase 2: Probe (1 day)
```python
from github_copilot_sdk import CopilotClient  # Hypothetical import

client = CopilotClient(token="...")
capability = client.supports_forced_tool_calls()

if not capability:
    print("ERROR: Forced tool calls not supported")
    sys.exit(1)
else:
    print("✓ Forced tool calls supported")
```

### Phase 3: Integration Test (2-3 days)
```python
# Call real SDK with real task (e.g., PM Phase1 decision)
adapter = CopilotSDKAdapter(client, config)
result = adapter.invoke_json(
    task_type="pm_phase1",
    prompt_vars={"context": "..."},
    model="copilot-standard"
)
# Verify result.payload contains expected decision field
# Verify result.model == "copilot-standard"
# Verify no exceptions raised
```

### Phase 4: Stress Test (2-3 days)
- Run 50+ real SDK calls with different task types (PM, PO, Dev phases)
- Verify 100% success rate with forced tool calls
- Capture response times, token usage
- Document any failures or unexpected behaviors

### Phase 5: Fallback Implementation (if needed) (3-5 days)
- If verification fails, implement FallbackAdapter
- Add bridge mode flag to all loops
- Update documentation

### Timeline
**Total**: 9-15 days before declaring system production-ready

---

## 6. Current Status of Forced Tool Call Handling

### What Works (Tested)
- ✓ CopilotSDKAdapter Protocol interface is sound
- ✓ ForcedToolCallMissing exception is raised correctly in mock tests
- ✓ Tool schema validation works as intended
- ✓ Retry logic on non-tool response is implemented

### What's Unknown (Untested)
- ⚠️ Real GitHub SDK supports forced tool calls
- ⚠️ Real SDK response format matches expected structure
- ⚠️ Retry loop works against real SDK (not mock)
- ⚠️ Token usage and performance under real conditions

---

## 7. Existing Fallback Infrastructure (Partial)

### What Exists
1. **Exception classes**: `CapabilityProbeFailed`, `ForcedToolCallMissing` (defined but `CapabilityProbeFailed` not actively used)
2. **Bridge mode controller**: PM has `BridgeModeController` for label migration; could extend to tool-call failures
3. **Heuristic parsing**: Individual nodes (e.g., Phase1) have decision mappings; could be extracted to a fallback adapter

### What's Missing
1. **Capability probe at startup**: No explicit check that forced tool calls are available before running any loop
2. **Fallback decision parser**: No heuristic that extracts decisions from plain-text responses
3. **Graceful degradation flag**: No system-wide way to enable fallback mode

### Recommendation
Implement a **pre-flight capability check** at orchestrator startup:
```python
def check_forced_tool_capability(client: CopilotSDKClient) -> bool:
    """Fail closed if forced tool calls not available."""
    if not client.supports_forced_tool_calls():
        raise CapabilityProbeFailed(
            "GitHub Copilot SDK does not support forced tool calls. "
            "This system requires deterministic tool-call responses."
        )
    return True

# In orchestrator.__init__():
check_forced_tool_capability(self.copilot_client)
```

---

## 8. Recommendation for LangGraph Integration

**Question**: Should LangGraph integration wait for Copilot SDK verification?

**Answer**: **NO, but with a caveat.**

**Rationale**:
- LangGraph is an orchestration layer; it doesn't depend on SDK capability
- SDK verification is orthogonal to graph composition
- We can design the graph with the assumption that forced tool calls work, then verify separately

**Caveat**:
- Before **deploying any loop to production**, forced tool calls must be verified for that loop
- The verification should be done in parallel with graph integration
- PM loop graph integration can proceed; SDK verification must follow before any production use

---

## 9. Action Items (Independent of LangGraph)

### Immediate (Before Design Approval)
- [ ] Locate GitHub Copilot SDK documentation or contact SDK team
- [ ] Confirm whether `supports_forced_tool_calls()` capability exists in current SDK
- [ ] Identify SDK authentication / access mechanism

### Short-term (Parallel to LangGraph Integration)
- [ ] Write standalone integration test script
- [ ] Run verification probe against real SDK
- [ ] Document verification results in a new COPILOT_SDK_VERIFICATION_RESULTS.md file

### Medium-term (Post-Verification)
- [ ] If verification passes: Add pre-flight check to orchestrators
- [ ] If verification fails: Implement FallbackAdapter + bridge mode across all loops

### Long-term
- [ ] Monitor GitHub SDK for changes; update system if forced tool calls become unavailable
- [ ] Document failure modes and recovery procedures in runbooks

---

## 10. Conclusion

**Current State**: Forced tool-call infrastructure is **well-designed but unverified**.

**Production Readiness**: System is **NOT production-ready** for any loop until forced tool calls are verified against the real GitHub Copilot SDK.

**Path Forward**: 
1. ✓ Proceed with LangGraph integration for PM (orchestration layer is orthogonal)
2. ⚠️ In parallel, run forced tool-call verification against real SDK
3. ✓ If verification passes: Proceed with confidence
4. ⚠️ If verification fails: Implement fallback adapter before any production deployment

**Risk Mitigation**: Implement pre-flight capability check in all orchestrators to fail fast if forced tool calls are not available.

---

**Document Version**: 1.0  
**Date**: 2026-07-12  
**Assigned To**: SDK Integration Team  
**Priority**: HIGH (blocking production deployment of any loop)
