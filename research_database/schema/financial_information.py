"""
Financial Information Schema

Logical schema for the Financial Information entity of the Verified
Knowledge Database, as defined in DATABASE_ARCHITECTURE.md (Layer 3 -
Financial & Contractual Knowledge).
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class FinancialRecord:
    """Represents one company's verified financial figures for one period.

    Purpose: hold verified financial facts, tied to the reporting period
    and currency they apply to.
    """

    id: int  # Unique identifier for the financial record.
    company_id: int  # Reference to the owning Company.
    reporting_period: str  # Reporting period this record covers (e.g. FY2025 Q2).
    currency: str  # Currency the figures are reported in.
    revenue: float  # Reported revenue for the period.
    profit: float  # Reported profit for the period.
    gross_margin: float  # Gross margin for the period.
    operating_margin: float  # Operating margin for the period.
    net_margin: float  # Net margin for the period.
    balance_sheet_summary: str  # Summary of key balance sheet figures.
    cash_flow_summary: str  # Summary of key cash flow figures.
    key_ratios: Dict[str, float]  # Named financial ratios for the period.
