"""
Historical Price (OHLC) Schema

Logical schema for the Historical Price (OHLC) entity of the Verified
Knowledge Database, as defined in DATABASE_ARCHITECTURE.md (Layer 6 -
Market & Technical Data).
"""

from dataclasses import dataclass


@dataclass
class HistoricalPrice:
    """Represents a single trading-period OHLC record for a company.

    Purpose: preserve the time-series trading history that Technical
    Analysis is computed from.
    """

    id: int  # Unique identifier for the historical price record.
    company_id: int  # Reference to the owning Company.
    period_date: str  # Date or interval this record covers.
    open_price: float  # Opening price for the period.
    high_price: float  # Highest price during the period.
    low_price: float  # Lowest price during the period.
    close_price: float  # Closing price for the period.
    volume: int  # Volume traded during the period.
