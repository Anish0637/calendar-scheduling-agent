"""Mock tools for the Calendar Scheduling agent."""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from langchain_core.tools import tool

# ---------------------------------------------------------------------------
# Simulated calendar state (in-memory for testing)
# ---------------------------------------------------------------------------
_CALENDAR: list[dict] = [
    {"date": "2025-03-10", "time": "14:00", "duration": 30, "title": "Team sync", "type": "internal"},
    {"date": "2025-03-11", "time": "10:00", "duration": 60, "title": "Investor call", "type": "investor"},
    {"date": "2025-03-12", "time": "14:00", "duration": 30, "title": "Vendor demo", "type": "vendor"},
]

_SENT_EMAILS: list[dict] = []


@tool
def get_cal(date: str) -> dict:
    """
    Get the calendar for a specific date to check availability.
    Args:
        date: Date in YYYY-MM-DD format.
    Returns a dict with 'date' and 'events' list.
    """
    events = [e for e in _CALENDAR if e["date"] == date]
    return {
        "date": date,
        "events": events,
        "available_slots": _compute_available_slots(date, events),
    }


def _compute_available_slots(date: str, events: list[dict]) -> list[str]:
    """Return available 30-min slots from 9am-6pm given booked events."""
    try:
        day = datetime.strptime(date, "%Y-%m-%d").weekday()  # 0=Mon
    except ValueError:
        return []

    all_slots = [f"{h:02d}:{m:02d}" for h in range(9, 18) for m in (0, 30)]
    booked = set()
    for e in events:
        start_h, start_m = map(int, e["time"].split(":"))
        duration = e.get("duration", 30)
        slots_used = duration // 30
        for i in range(slots_used + 1):  # +1 for 30-min buffer
            total_mins = start_h * 60 + start_m + i * 30
            booked.add(f"{total_mins // 60:02d}:{total_mins % 60:02d}")

    return [s for s in all_slots if s not in booked]


@tool
def schedule_cal(date: str, time: str, title: str, attendee_email: str, duration: int = 30) -> dict:
    """
    Schedule a meeting on the calendar.
    Args:
        date: Date in YYYY-MM-DD format.
        time: Time in HH:MM format (24h).
        title: Meeting title/subject.
        attendee_email: Email of the external attendee.
        duration: Duration in minutes (default 30).
    Returns confirmation dict.
    """
    event = {
        "date": date,
        "time": time,
        "title": title,
        "attendee": attendee_email,
        "duration": duration,
    }
    _CALENDAR.append(event)
    return {
        "status": "scheduled",
        "event": event,
        "calendar_link": f"https://calendar.example.com/event/{date}-{time.replace(':', '')}",
    }


@tool
def send_email(to: str, subject: str, body: str) -> dict:
    """
    Send an email response to the user.
    This must always be the final step.
    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body text (plain text, signed as Harrison Chase).
    Returns confirmation dict.
    """
    email = {"to": to, "subject": subject, "body": body}
    _SENT_EMAILS.append(email)
    return {"status": "sent", "to": to, "subject": subject}


def get_sent_emails() -> list[dict]:
    """Test helper: return all sent emails."""
    return list(_SENT_EMAILS)


def clear_state() -> None:
    """Test helper: reset calendar and sent emails."""
    _CALENDAR.clear()
    _SENT_EMAILS.clear()


TOOLS = [get_cal, schedule_cal, send_email]
