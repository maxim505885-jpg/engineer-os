from __future__ import annotations

import json

from engineering.core.contracts import AgentStatus, EngineerTask, MaterialRef
from engineering.core.engineer_core import EngineerCore
from engineering.runtime.factory import build_openwebui_runtime_from_env


def evaluate_smoke(runtime, *, model: str | None = None) -> dict:
    task = EngineerTask(
        task_id="local-openwebui-smoke",
        tz="Проверить только реальный локальный runtime. Не делать инженерных выводов без исходных материалов.",
        materials=(
            MaterialRef(
                id="local-smoke-evidence",
                kind="test",
                name="Local Open WebUI runtime smoke test",
            ),
        ),
        requested_checks=("inspection",),
    )

    core = EngineerCore()
    state = core.plan(task)
    results = runtime.execute(state.planned)
    core.collect(state, results)

    engineering_status = core.final_status(state).value
    output = {
        "task_id": task.task_id,
        "runtime": "openwebui",
        "model": model,
        "agent_results": [result.as_dict() for result in state.results],
        "engineering_status": engineering_status if engineering_status not in {"ACCEPTED", "ACCEPTED_ALTERNATIVE", "PASS"} else "UNCERTAINTY",
        "runtime_health": "PASSED" if len(state.results) == len(state.planned) and all(
            result.status in {AgentStatus.UNCERTAINTY, AgentStatus.BLOCK}
            for result in state.results) else "FAILED",
    }
    return output


def main() -> int:
    try:
        runtime = build_openwebui_runtime_from_env()
        output = evaluate_smoke(runtime, model=runtime.openwebui.client.config.model)
    except Exception as exc:
        print(json.dumps({"runtime_health": "FAILED", "reason": type(exc).__name__}))
        return 1
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if output["runtime_health"] != "PASSED":
        print("ENGINEER OS local runtime smoke FAILED: incomplete or inappropriate results.")
        return 1
    print("ENGINEER OS runtime smoke PASSED; engineering acceptance was not tested.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
