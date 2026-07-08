"""
Corporate Actions Schema

Logical schema for the Corporate Actions entity of the Verified
Knowledge Database, as defined in DATABASE_ARCHITECTURE.md (Layer 6 -
Market & Technical Data).
"""

from dataclasses import dataclass


@dataclass
class CorporateAction:
    """Represents a single corporate action affecting a company's shares.

    Purpose: track events (dividends, splits, bonuses, buybacks,
    mergers) that require adjustment of historical price and market
    data.
    """

    id: int  # Unique identifier for the corporate action record.
    company_id: int  # Reference to the owning Company.
    action_type: str  # Type of action (dividend, split, bonus, buyback, merger).
    announcement_date: str  # Date the action was announced.
    effective_date: str  # Date the action takes effect.
    terms: str  # Terms of the action (e.g. ratio, amount per share).
    description: str  # Description of the corporate action.
