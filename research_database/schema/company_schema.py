"""
Company Schema

Logical schema for the company knowledge registry backing the Knowledge
Viewer. This is the master list of companies (and their key attributes)
that the viewer searches against, independent of the research pipeline
tables.
"""

from dataclasses import dataclass


@dataclass
class Company:
    """Represents a single company known to the knowledge base.

    Purpose: provide a searchable master record of companies for the
    Knowledge Viewer.
    """

    id: int  # Unique identifier for the company record.
    name: str  # Company name.
    sector: str  # Broad sector the company belongs to.
    industry: str  # Specific industry within the sector.
    market_cap: str  # Market capitalization, as a display string.
    country: str  # Country the company is headquartered in.
    exchange: str  # Stock exchange(s) the company is listed on.
    last_updated: str  # Timestamp when this company record was last updated.


TABLE_NAME = "companies"

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    sector TEXT,
    industry TEXT,
    market_cap TEXT,
    country TEXT,
    exchange TEXT,
    last_updated TEXT NOT NULL
)
"""
