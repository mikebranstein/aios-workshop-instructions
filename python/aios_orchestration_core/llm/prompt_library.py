import json
from pathlib import Path
from typing import Dict, Any


_PROMPTS_ROOT = Path(__file__).resolve().parent / "prompts"

_TASK_PROMPT_FILE_MAP = {
    "foundation_research": _PROMPTS_ROOT / "foundation" / "foundation_research.md",
    "foundation_gate": _PROMPTS_ROOT / "foundation" / "foundation_gate.md",
    "foundation_research_plan": _PROMPTS_ROOT / "foundation" / "foundation_research_plan.md",
    "foundation_research_worker": _PROMPTS_ROOT / "foundation" / "foundation_research_worker.md",
    "foundation_wiki_manager": _PROMPTS_ROOT / "wiki" / "wiki_manager.md",
    "wiki_manager": _PROMPTS_ROOT / "wiki" / "wiki_manager.md",
    "format_issue_comment": _PROMPTS_ROOT / "github" / "format_issue_comment.md",
}


def render_task_prompt(task_type: str, prompt_vars: Dict[str, Any]) -> str:
    template_path = _TASK_PROMPT_FILE_MAP.get(task_type)
    if template_path is None:
        return ""
    if not template_path.exists():
        raise FileNotFoundError(f"Prompt template not found for task_type={task_type}: {template_path}")

    template = template_path.read_text(encoding="utf-8")
    prompt_vars_json = json.dumps(prompt_vars, ensure_ascii=True)
    prompt_vars_pretty_json = json.dumps(prompt_vars, ensure_ascii=True, indent=2)
    return (
        template.replace("{{PROMPT_VARS_JSON}}", prompt_vars_json).replace(
            "{{PROMPT_VARS_PRETTY_JSON}}",
            prompt_vars_pretty_json,
        )
    ).strip()
