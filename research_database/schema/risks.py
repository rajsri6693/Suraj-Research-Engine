"""
Risks Schema

Logical schema for the Risks entity of the Verified Knowledge Database,
as defined in DATABASE_ARCHITECTURE.md (Layer 4 - Market & Context
Knowledge).
"""

from dataclasses import dataclass


@dataclass
class RiskFactor:
    """Represents a single verified risk factor facing a company.

    Purpose: capture downside factors so research remains balanced.
    """

    id: int  # Unique identifier for the risk record.
    company_id: int  # Reference to the owning Company.
    risk_type: str  # Category of risk (business, financial, regulatory, etc.).
    description: str  # Description of the risk factor.
    severity: str  # Assessed severity of the risk.
    identified_date: str  # Date this risk was identified.
