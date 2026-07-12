from pathlib import Path
from typing import List, Optional

from aios_orchestration_core.runlog.models import TransitionLogEntry


class TransitionLogStore:
    """In-memory transition log with stdout and markdown export.
    
    Stores all transitions in RAM, prints to stdout on each append,
    and exports to markdown file on demand.
    """

    def __init__(self, markdown_path: Optional[str] = None):
        """Initialize store.
        
        Args:
            markdown_path: Optional path to write markdown export.
                          If None, markdown export is skipped.
        """
        self.entries: List[TransitionLogEntry] = []
        self.markdown_path = Path(markdown_path) if markdown_path else None
        if self.markdown_path:
            self.markdown_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry: TransitionLogEntry) -> None:
        """Append a transition entry, print to stdout, and update markdown."""
        self.entries.append(entry)
        print(entry.to_stdout())
        if self.markdown_path:
            self._update_markdown()

    def _update_markdown(self) -> None:
        """Write all entries to markdown file in table format."""
        if not self.markdown_path:
            return

        lines = [
            "# Orchestration Transitions Log",
            "",
            "## Summary",
            f"- Total transitions: {len(self.entries)}",
            f"- Last updated: {self.entries[-1].timestamp_utc if self.entries else 'N/A'}",
            "",
            "## Transition Details",
            "",
            "| Loop | Run ID | Issue | From State | To State | Event | Reason | Timestamp |",
            "|------|--------|-------|-----------|----------|-------|--------|----------|",
        ]

        for entry in self.entries:
            lines.append(entry.to_markdown_row())

        self.markdown_path.write_text("\n".join(lines) + "\n")

    def all(self) -> List[TransitionLogEntry]:
        """Return all stored transitions."""
        return list(self.entries)

    def by_loop(self, loop_id: str) -> List[TransitionLogEntry]:
        """Return transitions for a specific loop."""
        return [e for e in self.entries if e.loop_id == loop_id]

    def by_issue(self, issue_number: int) -> List[TransitionLogEntry]:
        """Return transitions for a specific issue."""
        return [e for e in self.entries if e.issue_number == issue_number]

    def export_markdown(self, path: str) -> None:
        """Export current transitions to a markdown file."""
        old_path = self.markdown_path
        self.markdown_path = Path(path)
        self.markdown_path.parent.mkdir(parents=True, exist_ok=True)
        self._update_markdown()
        self.markdown_path = old_path
