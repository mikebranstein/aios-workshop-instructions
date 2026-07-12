import sqlite3
from pathlib import Path

from aios_orchestration_core.runlog.models import TransitionLogEntry


class TransitionLogStore:
    def __init__(self, sqlite_path: str):
        self.sqlite_path = Path(sqlite_path)
        self.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        conn = sqlite3.connect(self.sqlite_path)
        try:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS transition_log (
                    loop_id TEXT NOT NULL DEFAULT 'pm',
                    run_id TEXT NOT NULL,
                    issue_number INTEGER NOT NULL,
                    from_state TEXT NOT NULL,
                    to_state TEXT NOT NULL,
                    trigger_event TEXT NOT NULL,
                    reason_code TEXT NOT NULL,
                    reason_detail TEXT NOT NULL,
                    blocked_stage TEXT,
                    actor TEXT NOT NULL,
                    timestamp_utc TEXT NOT NULL
                )
                """
            )
            # Migration: add loop_id to databases created before this column existed.
            try:
                conn.execute(
                    "ALTER TABLE transition_log ADD COLUMN loop_id TEXT NOT NULL DEFAULT 'pm'"
                )
            except sqlite3.OperationalError:
                pass  # Column already present; nothing to do.
            conn.commit()
        finally:
            conn.close()

    def append(self, entry: TransitionLogEntry) -> None:
        conn = sqlite3.connect(self.sqlite_path)
        try:
            conn.execute(
                """
                INSERT INTO transition_log (
                    loop_id, run_id, issue_number, from_state, to_state, trigger_event,
                    reason_code, reason_detail, blocked_stage, actor, timestamp_utc
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.loop_id,
                    entry.run_id,
                    entry.issue_number,
                    entry.from_state,
                    entry.to_state,
                    entry.trigger_event,
                    entry.reason_code,
                    entry.reason_detail,
                    entry.blocked_stage,
                    entry.actor,
                    entry.timestamp_utc,
                ),
            )
            conn.commit()
        finally:
            conn.close()
