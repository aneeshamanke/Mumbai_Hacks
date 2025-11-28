"""Gemini + tool orchestration worker."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict

import google.generativeai as genai
from dotenv import load_dotenv
from shared.storage import pop_job, update_run
from shared.tools import (
    WebSearchTool,
    WeatherTool,
    CalculatorTool,
    TimeTool,
    StockPriceTool,
)

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), "../config/.env"))


@dataclass
class ToolOutput:
    tool_name: str
    content: str
    metadata: Dict[str, Any]


class AgentRouter:
    def __init__(self, tools, api_key):
        self.tools = {t.name: t for t in tools}
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.chat_history = []

    def route_and_execute(self, prompt: str) -> Dict[str, Any]:
        print(f"--- Processing Prompt: '{prompt}' ---")
        
        self.chat_history.append({"role": "User", "content": prompt})
        
        max_steps = 5
        scratchpad = []
        tool_outputs = []
        
        for step in range(max_steps):
            print(f"  [Step {step + 1}/{max_steps}] Thinking...")
            
            history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.chat_history[:-1]])
            scratchpad_text = "\n".join(scratchpad)
            
            tool_descriptions = "\n".join([f"- {t.name}: {t.description}" for t in self.tools.values()])
            
            system_prompt = f"""
You are a smart agent that solves problems using tools.
Available Tools:
{tool_descriptions}
- final_answer: Use this tool when you have the final answer for the user. Argument: The final response text.

Conversation History:
{history_text}

Current User Request: {prompt}

Previous Steps (Scratchpad):
{scratchpad_text}

Instructions:
1. Analyze the Request, History, and Previous Steps.
2. Decide the NEXT step: either use a tool to get more info, or provide the final answer.
3. Return ONLY a JSON object: {{"tool": "tool_name", "args": "argument_value"}}
"""
            
            try:
                response = self.model.generate_content(system_prompt)
                response_text = response.text.strip()
                
                # Robust JSON extraction
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')
                
                if start_idx != -1 and end_idx != -1:
                    json_str = response_text[start_idx : end_idx + 1]
                    decision = json.loads(json_str)
                else:
                    raise ValueError("No JSON object found in response")
                
                tool_name = decision.get("tool")
                tool_args = decision.get("args")
                
                print(f"    -> Decided to use: {tool_name} (Args: {tool_args})")

                if tool_name == "final_answer":
                    self.chat_history.append({"role": "Agent", "content": tool_args})
                    return {
                        "answer": tool_args,
                        "tool_outputs": tool_outputs
                    }

                if tool_name in self.tools:
                    tool = self.tools[tool_name]
                    result = tool.run(tool_args)
                    print(f"    -> Output: {result}")
                    
                    scratchpad.append(f"Action: Used {tool_name} with args '{tool_args}'")
                    scratchpad.append(f"Observation: {result}")
                    
                    tool_outputs.append(ToolOutput(
                        tool_name=tool_name,
                        content=str(result),
                        metadata={"args": tool_args}
                    ))
                else:
                    error_msg = f"Error: Tool '{tool_name}' not found."
                    print(f"    -> {error_msg}")
                    scratchpad.append(f"System Error: {error_msg}")

            except Exception as e:
                print(f"  [Agent] Error during step: {e}")
                scratchpad.append(f"System Error: {e}")
        
        fallback_response = "I tried to solve your request but ran out of steps. Please try again."
        self.chat_history.append({"role": "Agent", "content": fallback_response})
        return {
            "answer": fallback_response,
            "tool_outputs": tool_outputs
        }


class OrchestratorWorker:
    def __init__(self) -> None:
        self.gemini_key = os.getenv("GEMINI_API_KEY", "dummy-key")
        self.tools = [
            WebSearchTool(),
            WeatherTool(),
            CalculatorTool(),
            TimeTool(),
            StockPriceTool()
        ]
        self.agent = AgentRouter(self.tools, self.gemini_key)

    def run(self, job: Dict[str, Any]) -> Dict[str, Any]:
        """Main entrypoint for a prompt job."""
        run_id = job["run_id"]
        prompt = job["prompt"]
        update_run(run_id, status="in_progress")
        
        # Execute Agent Logic
        agent_result = self.agent.route_and_execute(prompt)
        final_answer = agent_result["answer"]
        tool_outputs = agent_result["tool_outputs"]

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
