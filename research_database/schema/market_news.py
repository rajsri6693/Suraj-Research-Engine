"""
Market News Schema

Logical schema for the Market News entity of the Verified Knowledge
Database, as defined in DATABASE_ARCHITECTURE.md (Layer 4 - Market &
Context Knowledge).

Per Claude-Prompts/IMP_10F_NewsAPI_Integration.md's follow-up URL
requirement, `url` was added after this entity's original field list
to carry the source article's own URL -- the one new column this
change adds to the `market_news` table, per that phase's "do not
modify the schema beyond what is strictly required for storing the
URL" rule. Appended at the end of the field list, not inserted between
existing fields, so a table already created under the pre-IMP-10F
column order stays column-order-compatible with a freshly created one
once research_database.repositories.market_news_repository migrates it
(see that module's `_ensure_url_column`).
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
    url: str = ""  # Source article's own URL, preserved exactly.
