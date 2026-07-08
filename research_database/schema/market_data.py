"""
Market Data Schema

Logical schema for the Market Data entity of the Verified Knowledge
Database, as defined in DATABASE_ARCHITECTURE.md (Layer 6 - Market &
Technical Data).
"""

from dataclasses import dataclass


@dataclass
class MarketDataSnapshot:
    """Represents a single point-in-time market snapshot for a company.

    Purpose: hold live, quantitative market data sourced from market
    feeds, distinct from qualitative market context and reported
    financial figures.
    """

    id: int  # Unique identifier for the market data record.
    company_id: int  # Reference to the owning Company.
    snapshot_timestamp: str  # Timestamp the snapshot was taken.
    current_price: float  # Current trading price.
    day_low: float  # Lowest price for the current trading day.
    day_high: float  # Highest price for the current trading day.
    week_52_low: float  # Lowest price over the trailing 52 weeks.
    week_52_high: float  # Highest price over the trailing 52 weeks.
    traded_volume: int  # Volume traded as of the snapshot.
    market_capitalization: float  # Market capitalization as of the snapshot.
    currency: str  # Currency the price figures are denominated in.
