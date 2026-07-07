"""
Raw Research Schema

Logical schema for research data stored exactly as received from external
APIs, before any fact validation has occurred.
"""

from dataclasses import dataclass


@dataclass
class RawResearch:
    """Represents a single unit of raw, unverified research data.

    Purpose: store data exactly as received from external APIs, so the
    original source payload is preserved prior to validation.
    """

    id: int  # Unique identifier for the raw research record.
    topic: str  # Research topic this record was fetched for.
    source_name: str  # Name of the external source or provider.
    source_type: str  # Category of the source (e.g. news, financial, filing).
    raw_payload: str  # Unmodified response payload from the source.
    fetched_at: str  # Timestamp when the data was fetched.
    status: str  # Processing status (e.g. pending, validated, rejected).


TABLE_NAME = "raw_research"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS raw_research (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    source_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    raw_payload TEXT NOT NULL,
    fetched_at TEXT NOT NULL,
    status TEXT NOT NULL
)
"""
