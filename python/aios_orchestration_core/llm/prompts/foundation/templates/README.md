# Foundation Orchestration Templates

This folder contains template specifications and examples for the Foundation Orchestration system.

## Files

- **`foundation_adr_format_contract.md`** — The authoritative contract for all generated ADRs
  - Specifies the exact 9-section format that every ADR must conform to
  - Used by `adr_generator.py` when creating ADRs
  - Referenced by the foundation gate when validating ADRs

## Usage

### For LLM Prompts
The `adr_generator.md` prompt references this contract when instructing the LLM how to format ADRs.

### For Code
The foundation gate validation logic should read and enforce this contract when validating generated ADRs.

### For Developers
Read `foundation_adr_format_contract.md` to understand what format ADRs must have.

