"""
Research History Schema

Logical schema for tracking every completed research request, independent
of the research content itself.
"""

from dataclasses import dataclass


@dataclass
class ResearchHistory:
    """Represents a historical record of a completed research request.

    Purpose: track every completed research request for auditing,
    analytics, and future comparison.
    """

    id: int  # Unique identifier for the history record.
    topic: str  # Research topic that was processed.
    started_at: str  # Timestamp when the research request started.
    completed_at: str  # Timestamp when the research request completed.
    duration: float  # Total duration of the research request, in seconds.
    ai_provider: str  # AI provider used during this research request.
    status: str  # Final status of the request (e.g. success, failed).


TABLE_NAME = "research_history"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS research_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    started_at TEXT NOT NULL,
    completed_at TEXT,
    duration REAL,
    ai_provider TEXT,
    status TEXT NOT NULL
)
"""
