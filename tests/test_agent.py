"""
End-to-end tests for the Calendar Scheduling agent.

Runs all 5 tasks, traces them to LangSmith, and evaluates with 3 metrics.

Usage:
    export OPENAI_API_KEY=sk-...
    export LANGCHAIN_API_KEY=ls__...
    export LANGCHAIN_TRACING_V2=true
    export LANGCHAIN_PROJECT=calendar-scheduling-agent
    pytest tests/test_agent.py -v
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.agent import run_agent
from agent.tools import clear_state, get_sent_emails
from evaluation.tasks import TASKS
from evaluation.evaluators import EVALUATORS


# ---------------------------------------------------------------------------
# LangSmith dataset upload (runs once at session start if LS is configured)
# ---------------------------------------------------------------------------

def _upload_dataset_if_needed() -> str | None:
    """Upload tasks as a LangSmith dataset and return dataset name, or None."""
    api_key = os.environ.get("LANGCHAIN_API_KEY")
    if not api_key:
        return None
    try:
        from langsmith import Client
        client = Client()
        dataset_name = "calendar-scheduling-agent-tasks"
        existing = list(client.list_datasets(dataset_name=dataset_name))
        if existing:
            return dataset_name
        dataset = client.create_dataset(dataset_name, description="Calendar scheduling eval tasks")
        client.create_examples(
            inputs=[{"email": t["email"]} for t in TASKS],
            outputs=[{
                "expected_tool_calls": t["expected_tool_calls"],
                "success_criteria": t["success_criteria"],
            } for t in TASKS],
            dataset_id=dataset.id,
        )
        return dataset_name
    except Exception as e:
        print(f"[LangSmith] Dataset upload skipped: {e}")
        return None


# ---------------------------------------------------------------------------
# Pytest fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def reset_state():
    """Reset mock tool state before each test."""
    clear_state()
    yield
    clear_state()


# ---------------------------------------------------------------------------
# Parametrized end-to-end tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("task", TASKS, ids=[t["id"] for t in TASKS])
def test_calendar_task(task: dict):
    """Run a single calendar scheduling task and assert all metrics pass."""
    if not os.environ.get("OPENAI_API_KEY"):
        pytest.skip("OPENAI_API_KEY not set")

    result = run_agent(task["email"])

    # --- Metric 1: Trajectory ---
    actual_names = [tc["name"] for tc in result["tool_calls"]]
    expected = task["expected_tool_calls"]
    for tool_name in expected:
        assert tool_name in actual_names, (
            f"[{task['id']}] Expected tool '{tool_name}' not called. "
            f"Got trajectory: {actual_names}"
        )

    # --- Metric 2: send_email is last ---
    assert actual_names, f"[{task['id']}] No tools were called"
    assert actual_names[-1] == "send_email", (
        f"[{task['id']}] send_email was not the last call. Got: {actual_names}"
    )

    # --- Metric 3: An email was actually sent ---
    sent = get_sent_emails()
    assert len(sent) >= 1, f"[{task['id']}] No email was sent via send_email tool"
    assert sent[-1].get("body"), f"[{task['id']}] Sent email body is empty"

    print(f"\n[{task['id']}] PASS")
    print(f"  Trajectory: {actual_names}")
    print(f"  Email to:   {sent[-1].get('to')}")
    print(f"  Subject:    {sent[-1].get('subject')}")


# ---------------------------------------------------------------------------
# LangSmith experiment run (optional, invoked manually)
# ---------------------------------------------------------------------------

def run_langsmith_experiment(model: str = "gpt-4o") -> None:
    """
    Run all tasks through LangSmith evaluate() for full experiment tracking.
    Call directly: python -c "from tests.test_agent import run_langsmith_experiment; run_langsmith_experiment()"
    """
    from langsmith import Client
    from langsmith.evaluation import evaluate

    dataset_name = _upload_dataset_if_needed()
    if not dataset_name:
        print("LangSmith not configured. Set LANGCHAIN_API_KEY.")
        return

    def target(inputs: dict) -> dict:
        clear_state()
        return run_agent(inputs["email"], model=model)

    results = evaluate(
        target,
        data=dataset_name,
        evaluators=EVALUATORS,
        experiment_prefix=f"calendar-{model}",
        num_repetitions=3,
    )
    print(f"Experiment complete. Results: {results.experiment_name}")
