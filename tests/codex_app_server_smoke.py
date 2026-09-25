import os

from engineering.core.codex_runtime import CodexAppServerClient, CodexServerConfig


def main() -> None:
    config = CodexServerConfig(
        cwd=os.getcwd(),
        sandbox="read-only",
        approval_policy="never",
        timeout_seconds=60.0,
    )
    client = CodexAppServerClient(config)
    try:
        client.start()
        result = client.request(
            "thread/start",
            {
                "cwd": os.getcwd(),
                "sandbox": "read-only",
                "approvalPolicy": "never",
            },
        )
        thread = result.get("thread", {})
        thread_id = thread.get("id") or result.get("threadId")
        if not thread_id:
            raise RuntimeError(f"Codex app-server returned no thread id: {result!r}")
        print(f"CODEX_APP_SERVER_SMOKE_OK thread_id={thread_id}")
    finally:
        client.close()


if __name__ == "__main__":
    main()
