"""Calendar Scheduling agent using OpenAI tool-calling loop directly."""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
except ImportError:
    pass

from openai import OpenAI

from agent.instructions import SYSTEM_PROMPT
from agent.tools import TOOLS, get_cal, schedule_cal, send_email

_TOOL_MAP = {
    "get_cal": lambda args: get_cal.invoke(args),
    "schedule_cal": lambda args: schedule_cal.invoke(args),
    "send_email": lambda args: send_email.invoke(args),
}


def _openai_tools() -> list[dict]:
    result = []
    for t in TOOLS:
        schema = t.args_schema.model_json_schema() if t.args_schema else {"type": "object", "properties": {}}
        result.append({
            "type": "function",
            "function": {
                "name": t.name,
                "description": t.description,
                "parameters": schema,
            },
        })
    return result


def run_agent(email_text: str, model: str = "gpt-4o") -> dict[str, Any]:
    """Run the calendar scheduling agent on an incoming email."""
    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    tools_schema = _openai_tools()
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": email_text},
    ]
    trajectory: list[dict] = []

    for _ in range(10):
        response = client.chat.completions.create(
            model=model, messages=messages, tools=tools_schema, tool_choice="auto"
        )
        msg = response.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))

        if not msg.tool_calls:
            return {"tool_calls": trajectory, "final_response": msg.content or ""}

        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments)
            trajectory.append({"name": name, "args": args})
            fn = _TOOL_MAP.get(name)
            tool_result = fn(args) if fn else {"error": f"Unknown tool: {name}"}
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(tool_result)})

    return {"tool_calls": trajectory, "final_response": "Max iterations reached"}
