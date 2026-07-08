"""
Technical Analysis Schema

Logical schema for the Technical Analysis entity of the Verified
Knowledge Database, as defined in DATABASE_ARCHITECTURE.md (Layer 6 -
Market & Technical Data).
"""

from dataclasses import dataclass


@dataclass
class TechnicalIndicator:
    """Represents a single computed technical indicator for a company.

    Purpose: hold computed indicator values derived from Historical
    Price (OHLC) data, kept distinct from the raw prices they are
    calculated from.
    """

    id: int  # Unique identifier for the technical analysis record.
    company_id: int  # Reference to the owning Company.
    price_history_id: int  # Reference to the Historical Price window used.
    indicator_name: str  # Name of the indicator (e.g. RSI, MACD, SMA-50).
    indicator_value: float  # Computed value of the indicator.
    computed_date: str  # Date the indicator was computed for.
    lookback_period: str  # Lookback window used in the computation.
