"""Calendar Scheduling ReAct agent using LangGraph."""
from __future__ import annotations

import os
from typing import Any

from langchain_openai import ChatOpenAI
from langgraph.prebuilt import create_react_agent

from agent.instructions import SYSTEM_PROMPT
from agent.tools import TOOLS


def build_agent(model: str = "gpt-4o", temperature: float = 0) -> Any:
    """Build and return the LangGraph ReAct agent."""
    llm = ChatOpenAI(
        model=model,
        temperature=temperature,
        api_key=os.environ["OPENAI_API_KEY"],
    )
    return create_react_agent(
        model=llm,
        tools=TOOLS,
        prompt=SYSTEM_PROMPT,
    )


def run_agent(email_text: str, model: str = "gpt-4o") -> dict[str, Any]:
    """
    Run the calendar scheduling agent on an incoming email.

    Args:
        email_text: Raw email text (Subject/From/Body).
        model: OpenAI model to use.

    Returns:
        Dict with 'messages', 'tool_calls', and 'final_response'.
    """
    agent = build_agent(model=model)
    result = agent.invoke({"messages": [("user", email_text)]})

    # Extract tool call trajectory
    tool_calls = []
    for msg in result["messages"]:
        if hasattr(msg, "tool_calls") and msg.tool_calls:
            for tc in msg.tool_calls:
                tool_calls.append({"name": tc["name"], "args": tc["args"]})

    # Final AI response text
    final_response = result["messages"][-1].content

    return {
        "messages": result["messages"],
        "tool_calls": tool_calls,
        "final_response": final_response,
    }
