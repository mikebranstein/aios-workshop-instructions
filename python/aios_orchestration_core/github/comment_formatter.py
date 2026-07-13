"""Issue-comment Markdown formatting.

Every GitHub issue comment posted by an orchestrator can be routed through a
`CommentFormatter` so bodies are rewritten into polished, consistent Markdown
before they are published.

Design guarantees:
- **Fail-open.** A comment is NEVER dropped or corrupted because formatting
  failed. If the LLM errors, times out, returns nothing, or returns something
  unusable, the original body is posted unchanged.
- **Opt-in.** Gateways default to `NullCommentFormatter` (identity), so nothing
  changes unless a formatter is explicitly wired in.
- **Killable.** The `AIOS_FORMAT_COMMENTS` environment variable can globally
  disable LLM formatting (set to `0`/`false`/`no`/`off`).
"""

import logging
import os
from typing import Optional, Protocol, runtime_checkable

logger = logging.getLogger(__name__)

FORMAT_ISSUE_COMMENT_TASK = "format_issue_comment"

_DISABLED_VALUES = {"0", "false", "no", "off"}


@runtime_checkable
class CommentFormatter(Protocol):
    """Transforms a raw issue-comment body into the body that gets posted."""

    def format(self, body: str) -> str:
        ...


class NullCommentFormatter:
    """Default no-op formatter: returns the body unchanged."""

    def format(self, body: str) -> str:
        return body


class LLMCommentFormatter:
    """Rewrites comment bodies into polished Markdown via an LLM adapter.

    Fails open: any error or unusable response yields the original body.
    """

    def __init__(self, adapter, model_hint: str = "") -> None:
        self._adapter = adapter
        self._model_hint = model_hint

    def format(self, body: str) -> str:
        if not body or not body.strip():
            return body
        try:
            result = self._adapter.invoke_json(
                FORMAT_ISSUE_COMMENT_TASK,
                {"raw_comment": body},
                self._model_hint,
            )
            payload = getattr(result, "payload", None) or {}
            formatted = payload.get("formatted_markdown")
            if isinstance(formatted, str) and formatted.strip():
                return formatted
            logger.warning(
                "Comment formatter returned no usable markdown; posting original body."
            )
        except Exception as exc:  # noqa: BLE001 - fail-open by design
            logger.warning(
                "Comment markdown formatting failed (%s); posting original body.", exc
            )
        return body


def formatting_enabled() -> bool:
    """Return False when AIOS_FORMAT_COMMENTS explicitly disables formatting."""
    value = os.environ.get("AIOS_FORMAT_COMMENTS")
    if value is None:
        return True
    return value.strip().lower() not in _DISABLED_VALUES


def build_comment_formatter(adapter, model_hint: str = "") -> CommentFormatter:
    """Build the appropriate formatter for an adapter.

    Returns a `NullCommentFormatter` when no adapter is supplied or when
    formatting is disabled via `AIOS_FORMAT_COMMENTS`; otherwise an
    `LLMCommentFormatter`.
    """
    if adapter is None or not formatting_enabled():
        return NullCommentFormatter()
    return LLMCommentFormatter(adapter, model_hint=model_hint)
