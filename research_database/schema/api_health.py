"""
API Health Schema

Logical schema for the API Health entity, per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 5.5, Section
8, and Section 10.2. One row per ApiProvider row (One-to-One, Section
10.4) -- the live, current status only; history of every attempt
belongs to ApiLog, not this entity.
"""

from dataclasses import dataclass


@dataclass
class ApiHealth:
    """Represents the current, live status of one ApiProvider row.

    Purpose: answer "is this provider row usable right now" for
    Provider Selection Logic (Section 6), and to back the Dashboard's
    Provider Status / Last Health Check / Response Time / Last Error
    fields (Section 9).
    """

    id: int  # Unique identifier for this health record.
    provider_id: int  # Reference to the owning ApiProvider row.
    status: str  # One of: ONLINE, DOWN, RATE_LIMITED, INVALID_KEY, TIMEOUT, UNKNOWN.
    last_health_check: str  # ISO timestamp of the most recent call attempt or manual check.
    response_time_ms: float  # Response time of the most recent attempt.
    last_error: str  # Failure detail from the most recent failed attempt, empty if status is ONLINE.
    consecutive_failures: int  # Consecutive failures since the last ONLINE status.
