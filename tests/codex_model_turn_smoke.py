import os

from engineering.core.codex_runtime import CodexAppServerClient, CodexServerConfig


def main() -> None:
    client = CodexAppServerClient(
        CodexServerConfig(
            cwd=os.getcwd(),
            sandbox="read-only",
            approval_policy="never",
            timeout_seconds=60.0,
        )
    )
    try:
        client.start()
        thread_result = client.request(
            "thread/start",
            {
                "cwd": os.getcwd(),
                "sandbox": "read-only",
                "approvalPolicy": "never",
            },
        )
        thread_id = (
            thread_result.get("thread", {}).get("id")
            or thread_result.get("threadId")
        )
        if not thread_id:
            raise RuntimeError(f"No thread id: {thread_result!r}")

        turn_result = client.request(
            "turn/start",
            {
                "threadId": thread_id,
                "input": [
                    {
                        "type": "text",
                        "text": (
                            "Return exactly one short sentence confirming that "
                            "ENGINEER OS reached the Codex model turn. Do not modify files."
                        ),
                    }
                ],
                "sandboxPolicy": {"type": "readOnly"},
            },
        )
        turn_id = turn_result.get("turn", {}).get("id") or turn_result.get("turnId")
        if not turn_id:
            raise RuntimeError(f"No turn id: {turn_result!r}")

        text, final_turn = client._collect_turn(thread_id, turn_id)
        status = final_turn.get("status")
        if status != "completed":
            raise RuntimeError(f"Codex turn did not complete: status={status!r}, turn={final_turn!r}")
        if not text.strip():
            raise RuntimeError("Codex turn completed without an agent message")

        print(f"CODEX_MODEL_TURN_SMOKE_OK status={status} text={text.strip()!r}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
