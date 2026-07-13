from pathlib import Path
import tempfile


_RUNLOG_ROOT = Path(tempfile.gettempdir()) / "aios-orchestrator-runlogs"


def default_runlog_dir(loop_name: str) -> Path:
    return _RUNLOG_ROOT / loop_name
