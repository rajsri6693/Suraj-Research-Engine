"""
Session Manager

Implements SessionManager, the in-memory coordinator for creating, looking
up, and transitioning Research Sessions, per
project_documentation/RESEARCH_SESSION.md. It holds no database
connection and performs no research, planning, collection, or
verification of its own — it only tracks Research Session state, for the
lifetime of the SessionManager instance holding it.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional

from .research_session import ResearchSession, SessionNotFoundError, SessionStatus


class SessionManager:
    """Creates and tracks Research Sessions in memory.

    One SessionManager instance owns every Research Session it has
    created. It never accesses a database, a Research Planner, a Research
    Workflow, a collector, or Knowledge Verification — it only tracks the
    state a Research Session is already in.
    """

    _ID_PREFIX = "RS"

    def __init__(self) -> None:
        self._sessions: Dict[str, ResearchSession] = {}
        self._sequence: int = 0

    def create_session(
        self,
        research_topic: str,
        research_profile: str,
        research_category: str,
    ) -> ResearchSession:
        """Create Session.

        Starts a new Research Session at Overall Status Created, per
        RESEARCH_SESSION.md Section 2, assigning it a unique Research ID
        and a Start Time.
        """
        self._sequence += 1
        research_id = self._generate_research_id()
        session = ResearchSession(
            research_id=research_id,
            research_topic=research_topic,
            research_profile=research_profile,
            research_category=research_category,
            start_time=datetime.now(),
        )
        self._sessions[research_id] = session
        return session

    def get_session(self, research_id: str) -> ResearchSession:
        """Get Session.

        Looks up a Research Session by its Research ID. Raises
        SessionNotFoundError if no session with that Research ID exists.
        """
        try:
            return self._sessions[research_id]
        except KeyError as exc:
            raise SessionNotFoundError(
                f"No Research Session found with Research ID '{research_id}'."
            ) from exc

    def update_status(
        self,
        research_id: str,
        new_status: SessionStatus,
        current_stage: Optional[str] = None,
    ) -> ResearchSession:
        """Update Status.

        Moves a session to `new_status`, optionally refining Current
        Stage at the same time. Enforces the transition rules defined in
        RESEARCH_SESSION.md Section 5 (forward-only, the one Revision
        Loop exception, and Failed/Cancelled reachable from any active
        status) via ResearchSession.transition_to.
        """
        session = self.get_session(research_id)
        session.transition_to(new_status, current_stage=current_stage)
        return session

    def finish_session(self, research_id: str) -> ResearchSession:
        """Finish Session.

        Completes a session once Human Review has reached a decision on
        every eligible section. Only valid when the session is at
        Waiting Human Review, since Completed only follows Waiting Human
        Review in the Session Lifecycle (RESEARCH_SESSION.md Section 2).
        """
        return self.update_status(research_id, SessionStatus.COMPLETED)

    def cancel_session(self, research_id: str) -> ResearchSession:
        """Cancel Session.

        Deliberately stops a session before it reaches Completed. Valid
        from any active, non-terminal status, per RESEARCH_SESSION.md
        Section 4 ("Cancelled ... reflects a deliberate stop rather than
        a breakdown").
        """
        return self.update_status(research_id, SessionStatus.CANCELLED)

    def _generate_research_id(self) -> str:
        """Produce a Research ID in the RS-YYYYMMDD-NNN form shown in
        RESEARCH_SESSION.md Section 6."""
        date_stamp = datetime.now().strftime("%Y%m%d")
        return f"{self._ID_PREFIX}-{date_stamp}-{self._sequence:03d}"
