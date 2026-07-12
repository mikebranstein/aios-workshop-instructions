import ast
import inspect
from pathlib import Path
import unittest

from aios_orchestration_core.runlog.models import TransitionLogEntry


class AdapterSourceContractTests(unittest.TestCase):
    def test_transition_log_entry_requires_adapter_source_with_no_default(self) -> None:
        signature = inspect.signature(TransitionLogEntry)
        self.assertIn("adapter_source", signature.parameters)
        self.assertIs(
            signature.parameters["adapter_source"].default,
            inspect._empty,
            "adapter_source must remain required with no default",
        )

    def test_all_transition_log_entries_have_adapter_source(self) -> None:
        repo_root = Path(__file__).resolve().parents[1]
        python_files = [
            path
            for path in repo_root.rglob("*.py")
            if "tests" not in path.parts and "__pycache__" not in path.parts
        ]

        missing = []
        for path in python_files:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue

                is_transition_ctor = False
                if isinstance(node.func, ast.Name) and node.func.id == "TransitionLogEntry":
                    is_transition_ctor = True
                if isinstance(node.func, ast.Attribute) and node.func.attr == "TransitionLogEntry":
                    is_transition_ctor = True

                if not is_transition_ctor:
                    continue

                has_kw = any(
                    kw.arg == "adapter_source" and kw.value is not None
                    for kw in node.keywords
                )
                if not has_kw:
                    missing.append(f"{path.relative_to(repo_root)}:{node.lineno}")

        self.assertEqual(
            missing,
            [],
            "TransitionLogEntry constructor calls missing explicit adapter_source:\n"
            + "\n".join(missing),
        )

    def test_all_transition_log_entry_calls_pass_adapter_source_explicitly(self) -> None:
        # Backward-compatible alias for prior test naming.
        self.test_all_transition_log_entries_have_adapter_source()


if __name__ == "__main__":
    unittest.main()
