"""Gemini + tool orchestration worker (skeleton)."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict

from shared.storage import pop_job, update_run


@dataclass
class ToolOutput:
    tool_name: str
    content: str
    metadata: Dict[str, Any]

class OrchestratorWorker:
    def __init__(self) -> None:
        self.gemini_key = os.getenv("GEMINI_API_KEY", "dummy-key")

    def run(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Main entrypoint for a prompt job."""
        run_id = job["run_id"]
        prompt = job["prompt"]
        update_run(run_id, status="in_progress")
        tool_outputs = [
            self._call_gemini(prompt),
            self._mock_search(prompt),
        ]
        final_answer = self._combine(tool_outputs)
        result = {
            "run_id": run_id,
            "prompt": prompt,
            "tools": [output.__dict__ for output in tool_outputs],
            "answer": final_answer,
            "latency_ms": job.get("latency_ms", 0),
        }
        self._persist_run(result)
        update_run(
            run_id,
            status="awaiting_votes",
            provisional_answer=final_answer,
            evidence=[output.__dict__ for output in tool_outputs],
        )
        return result

    def _call_gemini(self, prompt: str) -> ToolOutput:
        """Placeholder Gemini Flash call."""
        content = f"[Gemini Flash mock answer for prompt: {prompt[:80]}...]"
        metadata = {"model": "gemini-1.5-flash", "latency_ms": 1200}
        return ToolOutput(tool_name="gemini_flash", content=content, metadata=metadata)

    def _mock_search(self, prompt: str) -> ToolOutput:
        """Mock web search output."""
        content = f"[Search results summary for prompt keywords: {prompt[:80]}]"
        metadata = {"engine": "mock-search", "latency_ms": 400}
        return ToolOutput(tool_name="web_search", content=content, metadata=metadata)

    def _combine(self, tool_outputs: list[ToolOutput]) -> str:
        """Toy aggregator for tool outputs."""
        summary = "\n".join(f"{output.tool_name}: {output.content}" for output in tool_outputs)
        return f"Combined agent answer:\n{summary}"

    def _persist_run(self, result: Dict[str, Any]) -> None:
        """Persist run artifacts (local JSON for MVP)."""
        logs_dir = os.getenv("LOG_DIR", "./logs")
        os.makedirs(logs_dir, exist_ok=True)
        filepath = os.path.join(logs_dir, f"{result['run_id']}.json")
        with open(filepath, "w", encoding="utf-8") as fh:
            json.dump(result, fh, indent=2)
        print(f"[orchestrator] wrote artifacts -> {filepath}")


def poll_queue() -> Dict[str, Any] | None:
    """Pull job from shared JSON queue; sleep when empty."""
    job = pop_job()
    if job:
        return job
    time.sleep(1)
    return None


def main() -> None:
    worker = OrchestratorWorker()
    while True:
        job = poll_queue()
        if not job:
            continue
        result = worker.run(job)
        print(f"[orchestrator] completed run_id={result['run_id']}")


if __name__ == "__main__":
    main()
