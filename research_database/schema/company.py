"""
Company Schema

Logical schema for the Company entity of the Verified Knowledge Database,
as defined in DATABASE_ARCHITECTURE.md (Layer 1 - Identity). Combines the
Company Information and Business Overview sections of KNOWLEDGE_MODEL.md.
"""

from dataclasses import dataclass
from typing import List


@dataclass
class Company:
    """Represents the identity and business description of one company.

    Purpose: act as the root entity that every other entity in the
    Verified Knowledge Database attaches to, directly or indirectly.
    """

    id: int  # Unique identifier for the company record.
    legal_name: str  # Registered legal name of the company.
    common_name: str  # Common or brand name the company is known by.
    registration_details: str  # Company registration/incorporation reference.
    incorporation_country: str  # Country the company is incorporated in.
    headquarters_location: str  # Location of the company's headquarters.
    founding_date: str  # Date the company was founded.
    website: str  # Official company website.
    stock_exchanges: List[str]  # Stock exchange(s) the company is listed on.
    ticker_symbols: List[str]  # Ticker symbol(s) used on each exchange.
    business_description: str  # Plain-language description of the business.
    mission: str  # Company mission statement.
    industry: str  # Specific industry the company operates in.
    sector_id: int  # Reference to the Sector entity this company belongs to.
    business_model_summary: str  # Summary of how the company generates value.
    geographic_footprint: List[str]  # Regions/countries the company operates in.
    customer_segments: List[str]  # Core customer segments served.
