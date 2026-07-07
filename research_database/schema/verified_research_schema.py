"""
Verified Research Schema

Logical schema for research data that has passed fact validation and is
ready for AI analysis.
"""

from dataclasses import dataclass


@dataclass
class VerifiedResearch:
    """Represents a single verified research fact.

    Purpose: store validated research ready for AI, once it has passed the
    Fact Validation Layer.
    """

    id: int  # Unique identifier for the verified research record.
    topic: str  # Research topic this fact belongs to.
    company: str  # Company this fact relates to, if applicable.
    sector: str  # Industry or sector this fact relates to.
    verified_fact: str  # The validated fact or statement.
    confidence_score: float  # Confidence level assigned during validation.
    source_count: int  # Number of independent sources confirming this fact.
    verified_at: str  # Timestamp when validation was completed.


TABLE_NAME = "verified_research"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS verified_research (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    topic TEXT NOT NULL,
    company TEXT,
    sector TEXT,
    verified_fact TEXT NOT NULL,
    confidence_score REAL NOT NULL,
    source_count INTEGER NOT NULL,
    verified_at TEXT NOT NULL
)
"""
