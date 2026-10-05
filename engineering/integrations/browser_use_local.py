"""Explicit optional Browser Use + Ollama runner; outputs unverified context."""
from __future__ import annotations

import os
import asyncio
import re
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory, gettempdir

from engineering.integrations.local_http import IntegrationError, local_url


def browser_options(*, enabled: bool, domains: list[str]) -> dict:
    if enabled is not True:
        raise IntegrationError("Browser Use is disabled; enable it explicitly")
    if not domains or len(domains) > 20:
        raise IntegrationError("Supply 1-20 allowed hostnames")
    for domain in domains:
        if (not isinstance(domain, str) or len(domain) > 253
                or not re.fullmatch(r"[a-zA-Z0-9]+(?:[a-zA-Z0-9.-]*[a-zA-Z0-9])?", domain)
                or any(not label or len(label) > 63 or label.startswith("-")
                       or label.endswith("-") for label in domain.split("."))):
            raise IntegrationError("Hostnames required; wildcards, URLs and paths are rejected")
    return {"allowed_domains": list(dict.fromkeys(domains)), "headless": True,
            "use_cloud": False, "is_local": True, "keep_alive": False,
            "enable_default_extensions": False, "captcha_solver": False,
            "auto_download_pdfs": False, "accept_downloads": False,
            "cross_origin_iframes": False}


async def run_browser(task: str, *, enabled: bool, domains: list[str],
                      model: str = "qwen3:8b", ollama_url: str = "http://127.0.0.1:11434",
                      max_steps: int = 10) -> dict:
    options = browser_options(enabled=enabled, domains=domains)
    host = local_url(ollama_url)
    if not isinstance(task, str) or not task.strip() or len(task) > 10000:
        raise IntegrationError("task must contain 1-10000 characters")
    if type(max_steps) is not int or not 1 <= max_steps <= 30:
        raise IntegrationError("max_steps must be an integer from 1 to 30")
    if not isinstance(model, str) or not model.strip():
        raise IntegrationError("A local Ollama model is required")
    os.environ["ANONYMIZED_TELEMETRY"] = "false"
    os.environ["BROWSER_USE_CLOUD_SYNC"] = "false"
    try:
        from browser_use import Agent, BrowserSession, ChatOllama
    except ImportError:
        raise IntegrationError("Install the pinned optional Browser Use environment first") from None
    with TemporaryDirectory(prefix="engineer-os-browser-") as profile:
        browser = BrowserSession(**options, user_data_dir=profile,
                                 downloads_path=str(Path(profile) / "downloads"))
        artifacts = None
        try:
            agent = Agent(task=task, llm=ChatOllama(model=model, host=host, timeout=60,
                          client_params={"trust_env": False, "follow_redirects": False}),
                          browser_session=browser, use_vision=False,
                          file_system_path=str(Path(profile) / "files"))
            artifacts = Path(agent.agent_directory)
            history = await asyncio.wait_for(agent.run(max_steps=max_steps), timeout=300)
            return {"text": history.final_result(), "tool": "browser-use",
                    "status": "UNVERIFIED", "evidentiary_status": "NOT_EVIDENCE",
                    "acceptance_granted": False}
        except TimeoutError:
            raise IntegrationError("Local browser run timed out") from None
        except Exception:
            raise IntegrationError("Local browser/model run failed; engineering acceptance was not granted") from None
        finally:
            try:
                await asyncio.wait_for(browser.kill(), timeout=30)
            finally:
                # Pinned Agent creates screenshots in a separate temporary directory.
                # Only delete the captured directory created by this invocation.
                if (artifacts is not None and artifacts.parent.resolve() == Path(gettempdir()).resolve()
                        and artifacts.name.startswith("browser_use_agent_")):
                    shutil.rmtree(artifacts)
