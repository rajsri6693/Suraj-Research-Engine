"""
Research Session

Implements the ResearchSession data model and lifecycle rules defined in
project_documentation/RESEARCH_SESSION.md. A Research Session tracks one
complete research lifecycle for one Research Input. It never performs
research, never verifies knowledge, and never writes to a database.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional


class SessionStatus(Enum):
    """Overall Status values for a Research Session.

    Matches RESEARCH_SESSION.md Section 4 exactly.
    """

    CREATED = "Created"
    PLANNING = "Planning"
    COLLECTING = "Collecting"
    ASSEMBLING = "Assembling"
    VERIFYING = "Verifying"
    WAITING_HUMAN_REVIEW = "Waiting Human Review"
    COMPLETED = "Completed"
    FAILED = "Failed"
    CANCELLED = "Cancelled"


# Statuses a session never leaves once reached, per RESEARCH_SESSION.md
# Section 5: "Once a session reaches a terminal status... its status does
# not change again."
_TERMINAL_STATUSES = frozenset(
    {SessionStatus.COMPLETED, SessionStatus.FAILED, SessionStatus.CANCELLED}
)

# The normal forward order of the lifecycle, per RESEARCH_SESSION.md
# Section 2. A session may only advance one step at a time along this
# order, except for the one permitted backward transition below.
_FORWARD_ORDER = [
    SessionStatus.CREATED,
    SessionStatus.PLANNING,
    SessionStatus.COLLECTING,
    SessionStatus.ASSEMBLING,
    SessionStatus.VERIFYING,
    SessionStatus.WAITING_HUMAN_REVIEW,
    SessionStatus.COMPLETED,
]

# The one permitted backward transition: the Revision Loop sends a session
# from Waiting Human Review back to Collecting when Human Review records
# Needs Revision for a section. See RESEARCH_SESSION.md Section 5.
_REVISION_LOOP_TRANSITION = (SessionStatus.WAITING_HUMAN_REVIEW, SessionStatus.COLLECTING)


class SessionNotFoundError(Exception):
    """Raised when a Research Session cannot be found by its Research ID."""


class InvalidSessionTransitionError(Exception):
    """Raised when a Session Status change would violate the transition
    rules defined in RESEARCH_SESSION.md Section 5."""


def is_valid_transition(current: SessionStatus, new: SessionStatus) -> bool:
    """Return whether moving from `current` to `new` is legal.

    Enforces RESEARCH_SESSION.md Section 5:
    - A terminal status (Completed, Failed, Cancelled) never changes again.
    - Failed and Cancelled are reachable from any active, non-terminal
      status.
    - Waiting Human Review -> Collecting is the one permitted backward
      transition (the Revision Loop).
    - Refining Current Stage without changing Overall Status (new == current)
      is always allowed while the session is active.
    - Every other move must advance exactly one step along the forward
      lifecycle order.
    """
    if current in _TERMINAL_STATUSES:
        return False
    if new == current:
        return True
    if new in (SessionStatus.FAILED, SessionStatus.CANCELLED):
        return True
    if (current, new) == _REVISION_LOOP_TRANSITION:
        return True
    try:
        current_index = _FORWARD_ORDER.index(current)
        new_index = _FORWARD_ORDER.index(new)
    except ValueError:
        return False
    return new_index == current_index + 1


@dataclass
class ResearchSession:
    """One complete research lifecycle for one Research Input.

    Fields mirror the Session Information defined in RESEARCH_SESSION.md
    Section 3. A session tracks exactly one Research Profile, one Research
    Category, and one Research Topic — never more than one Research Input.
    """

    research_id: str
    research_topic: str
    research_profile: str
    research_category: str
    start_time: datetime
    overall_status: SessionStatus = SessionStatus.CREATED
    current_stage: Optional[str] = None
    end_time: Optional[datetime] = None

    def __post_init__(self) -> None:
        if not self.research_id.strip():
            raise ValueError("research_id must not be empty.")
        if not self.research_topic.strip():
            raise ValueError("research_topic must not be empty.")
        if not self.research_profile.strip():
            raise ValueError("research_profile must not be empty.")
        if not self.research_category.strip():
            raise ValueError("research_category must not be empty.")

    @property
    def is_terminal(self) -> bool:
        """Whether this session has reached a status it will never leave."""
        return self.overall_status in _TERMINAL_STATUSES

    @property
    def duration(self) -> timedelta:
        """Elapsed time between Start Time and End Time.

        Final once End Time is set (a terminal status has been reached).
        Reflects elapsed time since Start Time otherwise, per
        RESEARCH_SESSION.md Section 3.
        """
        end = self.end_time if self.end_time is not None else datetime.now()
        return end - self.start_time

    def transition_to(
        self, new_status: SessionStatus, current_stage: Optional[str] = None
    ) -> None:
        """Move this session to `new_status`.

        Also updates Current Stage when `current_stage` is given, whether
        or not Overall Status itself changes — Current Stage is a
        finer-grained pointer than Overall Status (RESEARCH_SESSION.md
        Section 3) and can advance within a single Overall Status.

        Raises InvalidSessionTransitionError if the move is not permitted
        from the session's current status, per Section 5.
        """
        if not is_valid_transition(self.overall_status, new_status):
            raise InvalidSessionTransitionError(
                f"Cannot move Research Session '{self.research_id}' from "
                f"{self.overall_status.value} to {new_status.value}."
            )
        self.overall_status = new_status
        if current_stage is not None:
            self.current_stage = current_stage
        if new_status in _TERMINAL_STATUSES:
            self.end_time = datetime.now()
