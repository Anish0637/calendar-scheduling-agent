"""Evaluators for the Calendar Scheduling agent using LangSmith."""
from __future__ import annotations

from typing import Any

from langchain_openai import ChatOpenAI
from langsmith.schemas import Example, Run


# ---------------------------------------------------------------------------
# Trajectory evaluator
# ---------------------------------------------------------------------------

def evaluate_trajectory(run: Run, example: Example) -> dict[str, Any]:
    """
    Check that the agent's tool-call trajectory matches the expected sequence.
    Returns a score between 0.0 and 1.0.
    """
    expected: list[str] = example.outputs.get("expected_tool_calls", [])
    actual_calls: list[dict] = run.outputs.get("tool_calls", [])
    actual_names = [tc["name"] for tc in actual_calls]

    if not expected:
        return {"key": "trajectory_match", "score": 1.0, "comment": "No expected trajectory defined"}

    matches = sum(1 for name in expected if name in actual_names)
    score = matches / len(expected)

    # Also check ordering
    in_order = True
    last_idx = -1
    for name in expected:
        try:
            idx = actual_names.index(name)
            if idx <= last_idx:
                in_order = False
                break
            last_idx = idx
        except ValueError:
            in_order = False
            break

    return {
        "key": "trajectory_match",
        "score": score * (1.0 if in_order else 0.8),
        "comment": (
            f"Expected {expected}, got {actual_names}. "
            f"Order correct: {in_order}. Match: {score:.0%}"
        ),
    }


# ---------------------------------------------------------------------------
# LLM-as-judge evaluator
# ---------------------------------------------------------------------------

def evaluate_response_quality(run: Run, example: Example) -> dict[str, Any]:
    """
    Use GPT-4o as a judge to assess whether the final email response
    satisfies the task's success criteria.
    """
    import os
    criteria: str = example.outputs.get("success_criteria", "")
    final_response: str = run.outputs.get("final_response", "")

    if not criteria or not final_response:
        return {"key": "response_quality", "score": 0.0, "comment": "Missing criteria or response"}

    llm = ChatOpenAI(model="gpt-4o", temperature=0, api_key=os.environ["OPENAI_API_KEY"])
    prompt = (
        f"You are an evaluator. Assess whether the following email response satisfies ALL of the success criteria.\n\n"
        f"Success Criteria:\n{criteria}\n\n"
        f"Email Response:\n{final_response}\n\n"
        f"Reply with ONLY a JSON object: {{\"pass\": true/false, \"reason\": \"...\"}}"
    )
    result = llm.invoke(prompt)
    text = result.content.strip()

    try:
        import json
        parsed = json.loads(text)
        passed = bool(parsed.get("pass", False))
        reason = parsed.get("reason", "")
    except Exception:
        passed = "true" in text.lower()
        reason = text

    return {
        "key": "response_quality",
        "score": 1.0 if passed else 0.0,
        "comment": reason,
    }


# ---------------------------------------------------------------------------
# send_email called check
# ---------------------------------------------------------------------------

def evaluate_send_email_called(run: Run, example: Example) -> dict[str, Any]:
    """Verify that send_email was called as the final tool."""
    actual_calls: list[dict] = run.outputs.get("tool_calls", [])
    names = [tc["name"] for tc in actual_calls]
    called = "send_email" in names
    is_last = names and names[-1] == "send_email"
    return {
        "key": "send_email_called",
        "score": 1.0 if (called and is_last) else (0.5 if called else 0.0),
        "comment": f"send_email called: {called}, as last step: {is_last}. Trajectory: {names}",
    }


EVALUATORS = [evaluate_trajectory, evaluate_response_quality, evaluate_send_email_called]
