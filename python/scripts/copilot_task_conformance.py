import argparse
import json
from datetime import datetime, timezone

from aios_orchestration_core.llm.adapter_factory import create_adapter
from aios_orchestration_core.llm.schema_validation import validate_json_schema
from aios_orchestration_core.llm.task_tools import TASK_TOOL_MAP


def build_prompt_vars(task_type: str, trial: int):
    return {
        "task_type": task_type,
        "trial": trial,
        "issue": 1000 + trial,
        "summary": "Evaluate using the declared tool schema only.",
        "context": {
            "priority": "high",
            "risk": "medium",
            "signals": ["usage", "customer_feedback"],
        },
        "noise": {
            "should_ignore": True,
            "arbitrary_text": "Do not output plain text, only tool args.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="copilot-standard")
    parser.add_argument("--trials", type=int, default=1)
    parser.add_argument("--task", action="append", help="Task type to run (repeatable)")
    args = parser.parse_args()

    tasks = args.task or sorted(TASK_TOOL_MAP.keys())

    print(f"CONFORMANCE_START utc={datetime.now(timezone.utc).isoformat()}")
    print(f"MODEL={args.model}")
    print(f"TRIALS={args.trials}")
    print(f"TASKS={tasks}")

    adapter = create_adapter(model=args.model, use_stub=False)

    total = 0
    success = 0
    failures = []

    for task_type in tasks:
        schema = TASK_TOOL_MAP[task_type].parameters_schema
        for trial in range(1, args.trials + 1):
            total += 1
            prompt_vars = build_prompt_vars(task_type, trial)
            print(f"RUN task={task_type} trial={trial}")
            try:
                result = adapter.invoke_json(task_type, prompt_vars)
                errors = validate_json_schema(result.payload, schema)
                print("PAYLOAD=" + json.dumps(result.payload, ensure_ascii=True))
                print("MODEL_USED=" + str(result.model))
                print("REQUEST_ID=" + str(result.request_id))
                if errors:
                    print("RESULT=SCHEMA_INVALID")
                    print("VALIDATION_ERRORS=" + "; ".join(errors))
                    failures.append((task_type, trial, "schema_invalid", "; ".join(errors)))
                else:
                    print("RESULT=SCHEMA_VALID")
                    success += 1
            except Exception as ex:
                print("RESULT=EXCEPTION")
                print(f"ERROR_CLASS={type(ex).__name__}")
                print(f"ERROR_DETAIL={ex}")
                failures.append((task_type, trial, type(ex).__name__, str(ex)))

    print(f"SUMMARY total={total} success={success} failed={len(failures)}")
    if failures:
        for task_type, trial, err_cls, detail in failures:
            print(f"FAIL task={task_type} trial={trial} class={err_cls} detail={detail}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
