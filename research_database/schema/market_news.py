"""
Market News Schema

Logical schema for the Market News entity of the Verified Knowledge
Database, as defined in DATABASE_ARCHITECTURE.md (Layer 4 - Market &
Context Knowledge).
"""

from dataclasses import dataclass
from typing import List


@dataclass
class MarketNewsItem:
    """Represents a single dated, verified news event about a company.

    Purpose: hold time-bound news events relevant to a company.
    """

    id: int  # Unique identifier for the news record.
    company_id: int  # Reference to the owning Company.
    headline: str  # Headline of the news item.
    event_date: str  # Date the news event occurred.
    summary: str  # Summary of the news event.
    extracted_facts: List[str]  # Verified facts extracted from the event.
