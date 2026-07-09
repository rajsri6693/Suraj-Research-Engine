"""
Research Session module.

Public entry point for the Research Session package, implementing
project_documentation/RESEARCH_SESSION.md.
"""

from .research_session import (
    InvalidSessionTransitionError,
    ResearchSession,
    SessionNotFoundError,
    SessionStatus,
)
from .session_manager import SessionManager

__all__ = [
    "ResearchSession",
    "SessionManager",
    "SessionStatus",
    "SessionNotFoundError",
    "InvalidSessionTransitionError",
]
