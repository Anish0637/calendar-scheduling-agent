"""Evaluation tasks for the Calendar Scheduling agent."""
from __future__ import annotations

# Each task has:
#   email:                 the incoming email text
#   expected_tool_calls:   ordered list of tool names the agent should call
#   success_criteria:      rubric for LLM-as-judge on the final email response

TASKS = [
    {
        "id": "cal_001",
        "description": "Schedule vendor meeting — valid Tuesday slot",
        "email": (
            "Subject: Product Demo Request\n"
            "From: vendor@acmesales.com\n\n"
            "Hi Harrison,\n\n"
            "We'd love to give you a 30-minute demo of our new product. "
            "Would Tuesday March 11 work for you? We're flexible on time.\n\n"
            "Best, Vendor Team"
        ),
        "expected_tool_calls": ["get_cal", "schedule_cal", "send_email"],
        "success_criteria": (
            "The email confirms a meeting scheduled on Tuesday March 11 "
            "between 2pm and 5pm. It is signed by Harrison Chase."
        ),
    },
    {
        "id": "cal_002",
        "description": "Investor call — must land on Monday or Friday 10am-12pm",
        "email": (
            "Subject: Quarterly Check-in\n"
            "From: investor@vcfund.com\n\n"
            "Harrison,\n\n"
            "I'd like to schedule our quarterly 30-minute check-in call. "
            "Can we do this week? I'm open any day.\n\n"
            "Regards, Michael"
        ),
        "expected_tool_calls": ["get_cal", "schedule_cal", "send_email"],
        "success_criteria": (
            "The email confirms a meeting on a Monday or Friday between 10am and 12pm. "
            "It is a 30-minute call. Signed by Harrison Chase."
        ),
    },
    {
        "id": "cal_003",
        "description": "Internal team sync — any weekday 9am-6pm",
        "email": (
            "Subject: Weekly Sync\n"
            "From: teammate@langchain.dev\n\n"
            "Hey Harrison,\n\n"
            "Can we grab 30 minutes this week for our weekly sync? "
            "Any day works for me.\n\nThanks"
        ),
        "expected_tool_calls": ["get_cal", "schedule_cal", "send_email"],
        "success_criteria": (
            "The email confirms an internal sync on a weekday between 9am and 6pm. "
            "Signed by Harrison Chase."
        ),
    },
    {
        "id": "cal_004",
        "description": "Interview — must be Wednesday 10am-4pm",
        "email": (
            "Subject: Interview Scheduling\n"
            "From: recruiter@langchain.dev\n\n"
            "Hi Harrison,\n\n"
            "We have a candidate interview to schedule for this week. "
            "The candidate is available all week. Can you confirm a slot?\n\nThanks"
        ),
        "expected_tool_calls": ["get_cal", "schedule_cal", "send_email"],
        "success_criteria": (
            "The email confirms an interview scheduled on Wednesday between 10am and 4pm. "
            "Signed by Harrison Chase."
        ),
    },
    {
        "id": "cal_005",
        "description": "Vendor requests Monday slot — agent must reschedule to Tuesday/Thursday",
        "email": (
            "Subject: Quick Sync\n"
            "From: partner@partnercorp.com\n\n"
            "Harrison,\n\n"
            "Can we meet Monday at 3pm for a quick 30-minute vendor discussion?\n\nThanks"
        ),
        "expected_tool_calls": ["get_cal", "schedule_cal", "send_email"],
        "success_criteria": (
            "The agent does NOT schedule on Monday. "
            "Instead it proposes or books a Tuesday or Thursday slot between 2pm and 5pm. "
            "The reply is polite and signed by Harrison Chase."
        ),
    },
]
