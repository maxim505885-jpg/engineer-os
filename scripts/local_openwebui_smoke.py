from __future__ import annotations

import json

from engineering.core.contracts import EngineerTask, MaterialRef
from engineering.core.engineer_core import EngineerCore
from engineering.runtime.factory import build_openwebui_runtime_from_env


def main() -> int:
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
    runtime = build_openwebui_runtime_from_env()
    results = runtime.execute(state.planned)
    core.collect(state, results)

    engineering_status = core.final_status(state).value
    output = {
        "task_id": task.task_id,
        "runtime": "openwebui",
        "model": runtime.openwebui.client.config.model,
        "agent_results": [result.as_dict() for result in state.results],
        "engineering_status": engineering_status,
        "runtime_health": "PASSED" if state.results else "FAILED",
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))

    if not state.results:
        print("ENGINEER OS local Open WebUI runtime smoke FAILED: no agent results.")
        return 1

    print("ENGINEER OS local Open WebUI runtime smoke PASSED.")
    print(
        f"Engineering result status: {engineering_status} "
        "(this is not a transport/runtime health verdict)."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
