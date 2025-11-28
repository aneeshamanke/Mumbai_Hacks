"""Gemini + tool orchestration worker."""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass
from typing import Any, Dict

import google.generativeai as genai
from dotenv import load_dotenv

# Add project root to path
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shared.storage import pop_job, update_run
from shared.tools import (
    TavilySearchTool,
    WeatherTool,
    CalculatorTool,
    TimeTool,
    StockPriceTool,
    WikipediaTool,
    NewsTool
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
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.chat_history = []

    def _expand_query(self, prompt: str) -> str:
        expansion_prompt = f"""
        You are an expert at refining user queries for search engines and tools.
        Rewrite the following user prompt to be more specific, detailed, and optimized for an autonomous agent to solve.
        
        CRITICAL INSTRUCTION:
        - If the prompt is already specific and clear (e.g., "What is the weather in Tokyo?", "Stock price of Apple"), return it EXACTLY as is. Do not rewrite it.
        - Only expand if the prompt is vague (e.g., "cricket news", "latest tech trends").
        - SAFETY CHECK: If the user asks for something harmful, illegal, or unethical (e.g., making weapons, hate speech), return a refusal message starting with "I cannot fulfill this request because...". Do NOT expand harmful queries.
        
        Do not add any conversational filler. Return ONLY the refined prompt.

        User Prompt: {prompt}
        """
        try:
            response = self.model.generate_content(expansion_prompt)
            expanded_prompt = response.text.strip()
            print(f"  [Query Expansion] Original: '{prompt}' -> Expanded: '{expanded_prompt}'")
            return expanded_prompt
        except Exception as e:
            print(f"  [Query Expansion] Failed: {e}")
            return prompt

    def route_and_execute(self, prompt: str, max_steps: int = 20, persona: str = "You are a smart agent that solves problems using tools.") -> Dict[str, Any]:
        
        # Expand the query first
        expanded_prompt = self._expand_query(prompt)
        print(f"--- Processing Prompt: '{expanded_prompt}' ---")
        
        self.chat_history.append({"role": "User", "content": expanded_prompt})
        
        scratchpad = []
        tool_outputs = []
        
        for step in range(max_steps):
            # --- Loop Detection ---
            # Check if the exact same tool and arguments have been used recently
            if len(tool_outputs) >= 2:
                last_tool = tool_outputs[-1].tool_name
                last_args = tool_outputs[-1].metadata.get('args')
                prev_tool = tool_outputs[-2].tool_name
                prev_args = tool_outputs[-2].metadata.get('args')
                
                if last_tool == prev_tool and last_args == prev_args:
                     print(f"  [Loop Detected] Same tool call repeated: {last_tool}({last_args})")
                     # Force the agent to try something else by appending a system message
                     self.chat_history.append({
                         "role": "system",
                         "content": f"SYSTEM ALERT: You just called {last_tool} with {last_args} twice in a row. STOP doing this. Try a DIFFERENT tool or a DIFFERENT query immediately."
                     })
            
            # Check if we are stuck in a search loop (many search calls with no answer)
            search_count = sum(1 for h in tool_outputs if h.tool_name in ['web_search', 'get_news', 'wikipedia'])
            if search_count > 5 and step > 8:
                 self.chat_history.append({
                     "role": "system",
                     "content": "SYSTEM ALERT: You have performed many searches but haven't found the answer. Stop searching blindly. Analyze what you have found so far. If you are stuck, admit it or try a completely different approach."
                 })
            # ----------------------

            print(f"  [Step {step + 1}/{max_steps}] Thinking...")
            
            history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in self.chat_history[:-1]])
            scratchpad_text = "\n".join(scratchpad)
            
            # Generate tool descriptions from Pydantic schemas
            tool_descriptions = []
            for t in self.tools.values():
                schema = t.args_schema.model_json_schema()
                # Simplified schema representation for the prompt
                args_desc = ", ".join([f"{k}: {v.get('description', '')} ({v.get('type', 'any')})" for k, v in schema.get('properties', {}).items()])
                tool_descriptions.append(f"- {t.name}: {t.description} Arguments: {{{args_desc}}}")
            
            tool_desc_str = "\n".join(tool_descriptions)
            
            system_prompt = f"""
{persona}

Available Tools:
{tool_desc_str}
- final_answer: Use this tool when you have the final answer for the user. Arguments: {{text: The final response text}}

IMPORTANT:
- **EFFICIENCY**: If the user asks a question that you can answer directly with your internal knowledge (e.g., general facts, coding help, jokes, simple math), use the `final_answer` tool IMMEDIATELY. Do NOT use other tools unless necessary.
- Your final answer (via the final_answer tool) should be a natural language summary, unless the user explicitly asks for a structured format (like JSON).
- Do not just dump data; explain it to the user.
- **Use Markdown tables** when comparing multiple items (e.g., weather in two cities, stock prices).
- Use **bold headings** to organize long answers.
- Keep the layout clean, professional, and easy to read.
- When using information from tools (web_search, get_news, wikipedia), YOU MUST INCLUDE THE SOURCE LINKS/URLS in your final answer.
- Format citations as: [Source Name](URL) or simply (URL).
- If a tool provides a URL, make sure it ends up in the final answer so the user can validate it.

SAFETY & CONDUCT:
- You are a helpful and harmless AI assistant.
- If the user asks for help with a harmful, illegal, or unethical activity, REFUSE the request politely but firmly.
- Do not be preachy or judgmental. Simply state that you cannot assist with that specific request.
- Example Refusal: "I cannot provide instructions on how to make a bomb as that is dangerous and illegal."
- Do NOT provide "educational" or "theoretical" information for harmful topics if it could be used for harm.

Conversation History:
{history_text}

Current User Request: {expanded_prompt}

Previous Steps (Scratchpad):
{scratchpad_text}

Instructions:
1. Analyze the Request, History, and Previous Steps.
2. Formulate a "Thought" about what to do next.
3. Decide the NEXT step: either use a tool to get more info, or provide the final answer.
4. Return ONLY a JSON object with the following structure:
{{
  "thought": "Your reasoning here...",
  "tool": "tool_name",
  "args": {{ "arg_name": "value" }}
}}

IMPORTANT:
- Your final answer (via the final_answer tool) should be a natural language summary, unless the user explicitly asks for a structured format (like JSON).
- Do not just dump data; explain it to the user.
- **Use Markdown tables** when comparing multiple items (e.g., weather in two cities, stock prices).
- Use **bold headings** to organize long answers.
- Keep the layout clean, professional, and easy to read.
"""
            
            # Retry loop for model generation and parsing
            max_retries = 3
            for attempt in range(max_retries):
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
                    
                    thought = decision.get("thought", "No thought provided.")
                    tool_name = decision.get("tool")
                    tool_args = decision.get("args")
                    
                    print(f"    [Thought] {thought}")
                    print(f"    -> Decided to use: {tool_name} (Args: {tool_args})")
                    
                    break # Success, exit retry loop
                    
                except Exception as e:
                    print(f"    [Attempt {attempt+1}/{max_retries}] Error parsing response: {e}")
                    if attempt == max_retries - 1:
                        tool_name = None # Failed after retries
            
            if not tool_name:
                error_msg = "Failed to generate valid JSON action after retries."
                print(f"    -> {error_msg}")
                scratchpad.append(f"System Error: {error_msg}")
                continue

            if tool_name == "final_answer":
                # Handle final_answer args which might be a dict or string
                answer_text = tool_args.get("text") if isinstance(tool_args, dict) else str(tool_args)
                self.chat_history.append({"role": "Agent", "content": answer_text})
                return {
                    "answer": answer_text,
                    "tool_outputs": tool_outputs
                }

            if tool_name in self.tools:
                tool = self.tools[tool_name]
                # Pass args directly, let the tool validate
                result = tool.run(tool_args)
                print(f"    -> Output: {result}")
                
                scratchpad.append(f"Thought: {thought}")
                scratchpad.append(f"Action: Used {tool_name} with args '{tool_args}'")
                scratchpad.append(f"Observation: {result}")
                
                tool_outputs.append(ToolOutput(
                    tool_name=tool_name,
                    content=str(result),
                    metadata={"args": tool_args, "thought": thought}
                ))
            else:
                error_msg = f"Error: Tool '{tool_name}' not found."
                print(f"    -> {error_msg}")
                scratchpad.append(f"System Error: {error_msg}")
        
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
            TavilySearchTool(),
            WeatherTool(),
            CalculatorTool(),
            TimeTool(),
            StockPriceTool(),
            WikipediaTool(),
            NewsTool()
        ]
        self.agent = AgentRouter(self.tools, self.gemini_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

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
