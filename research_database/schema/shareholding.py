"""
Shareholding Schema

Logical schema for the Shareholding entity of the Verified Knowledge
Database, as defined in DATABASE_ARCHITECTURE.md (Layer 2 - Company
Knowledge).
"""

from dataclasses import dataclass
from typing import List


@dataclass
class ShareholdingRecord:
    """Represents a company's ownership structure as observed on one date.

    Purpose: record who owns a company at a given point in time.
    """

    id: int  # Unique identifier for the shareholding record.
    company_id: int  # Reference to the owning Company.
    observed_date: str  # Date this holding pattern was observed.
    promoter_holding_percent: float  # Promoter/founder holding percentage.
    institutional_holding_percent: float  # Institutional ownership percentage.
    public_float_percent: float  # Publicly held float percentage.
    major_shareholders: List[str]  # Named major shareholders.
    pledge_percent: float  # Percentage of holdings currently pledged.
