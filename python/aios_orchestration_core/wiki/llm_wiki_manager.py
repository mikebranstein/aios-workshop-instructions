import re
from dataclasses import dataclass
from typing import Protocol, Sequence

from aios_orchestration_core.llm.base import JudgmentLLMAdapter


class WikiManagerGateway(Protocol):
    def get_wiki_snapshot(self, limit: int = 50, excerpt_chars: int = 1200) -> list[dict]: ...
    def apply_wiki_manager_changes(
        self,
        *,
        page_path: str,
        page_content: str,
        page_moves: Sequence[dict],
        index_issue_number: int,
        index_summary: str,
        commit_message: str,
    ) -> bool: ...


@dataclass(frozen=True)
class WikiManagerPolicy:
    target_root: str = "foundation/"
    prefer_update_when_overlap_high: bool = True
    required_sections: tuple[str, ...] = (
        "Summary",
        "Decision",
        "Alternatives Considered",
        "Evidence",
        "Risks and Mitigations",
        "Traceability",
    )
    content_index_file: str = "Content-Index.md"
    reorganize_when_needed: bool = True


def normalize_wiki_page_path(value: str, default_path: str) -> str:
    path = (value or "").strip().replace("\\", "/")
    path = re.sub(r"/+", "/", path).strip("/")
    if not path:
        path = default_path
    if not path:
        return ""
    if not path.lower().endswith(".md"):
        path = f"{path}.md"
    # Slugify the filename stem so spaces / special chars never end up in links.
    parts = path.rsplit("/", 1)
    stem_with_ext = parts[-1]
    stem, _, _ = stem_with_ext.partition(".")
    safe_stem = re.sub(r"[^a-z0-9]+", "-", stem.lower()).strip("-") or slugify(stem)
    safe_name = f"{safe_stem}.md"
    path = f"{parts[0]}/{safe_name}" if len(parts) == 2 else safe_name
    # Redirect to default if the result collides with a system-managed filename.
    _SYSTEM_NAMES = {"home.md", "content-index.md", "_sidebar.md", "_footer.md"}
    if safe_name.lower() in _SYSTEM_NAMES:
        path = default_path
        if not path:
            return ""
        if not path.lower().endswith(".md"):
            path = f"{path}.md"
    return path


def slugify(value: str, fallback: str = "research", max_len: int | None = None) -> str:
    lowered = (value or "").strip().lower()
    cleaned = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    result = cleaned or fallback
    if max_len and len(result) > max_len:
        result = result[:max_len].rstrip("-")
    return result


class LLMWikiManager:
    def __init__(self, policy: WikiManagerPolicy | None = None):
        self.policy = policy or WikiManagerPolicy()

    def apply_llm_plan(
        self,
        *,
        gateway: WikiManagerGateway,
        adapter: JudgmentLLMAdapter,
        task_type: str,
        prompt_vars: dict,
        default_page_path: str,
        fallback_page_content: str,
        index_issue_number: int,
        default_index_summary: str,
        commit_message: str,
    ) -> str:
        payload_vars = dict(prompt_vars)
        payload_vars["existing_wiki_pages"] = gateway.get_wiki_snapshot(limit=50, excerpt_chars=1200)
        payload_vars["proposed_default_path"] = default_page_path
        payload_vars["wiki_manager_policy"] = {
            "prefer_update_when_overlap_high": self.policy.prefer_update_when_overlap_high,
            "target_root": self.policy.target_root,
            "required_sections": list(self.policy.required_sections),
            "content_index_file": self.policy.content_index_file,
            "reorganize_when_needed": self.policy.reorganize_when_needed,
        }

        result = adapter.invoke_json(task_type, payload_vars)
        payload = result.payload or {}
        page_path = normalize_wiki_page_path(payload.get("page_path", default_page_path), default_page_path)
        page_content = payload.get("page_content")
        if not isinstance(page_content, str) or not page_content.strip():
            page_content = fallback_page_content

        normalized_moves = []
        for move in payload.get("page_moves") or []:
            if not isinstance(move, dict):
                continue
            from_path = normalize_wiki_page_path(str(move.get("from_path", "")), "")
            to_path = normalize_wiki_page_path(str(move.get("to_path", "")), "")
            if from_path and to_path and from_path != to_path:
                normalized_moves.append({"from_path": from_path, "to_path": to_path})

        index_summary = payload.get("content_index_summary")
        if not isinstance(index_summary, str) or not index_summary.strip():
            index_summary = default_index_summary

        gateway.apply_wiki_manager_changes(
            page_path=page_path,
            page_content=page_content,
            page_moves=normalized_moves,
            index_issue_number=index_issue_number,
            index_summary=index_summary,
            commit_message=commit_message,
        )
        return page_path
