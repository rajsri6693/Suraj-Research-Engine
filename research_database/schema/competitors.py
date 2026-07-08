"""
Competitors Schema

Logical schema for the Competitors entity of the Verified Knowledge
Database, as defined in DATABASE_ARCHITECTURE.md (Layer 4 - Market &
Context Knowledge).
"""

from dataclasses import dataclass


@dataclass
class CompetitorComparison:
    """Represents a single comparison between a company and one competitor.

    Purpose: place a company within its competitive landscape.
    """

    id: int  # Unique identifier for the comparison record.
    company_id: int  # Reference to the Company being described.
    competitor_company_id: int  # Reference to the competing Company.
    comparison_basis: str  # Basis on which the comparison is made.
    relative_market_position: str  # Company's market position relative to competitor.
    strengths: str  # Comparative strengths.
    weaknesses: str  # Comparative weaknesses.
    competitive_advantage: str  # Competitive advantage or moat, if any.
