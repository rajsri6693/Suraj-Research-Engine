"""
Sector Schema

Logical schema for the Sector entity of the Verified Knowledge Database,
as defined in DATABASE_ARCHITECTURE.md (Layer 4 - Market & Context
Knowledge).
"""

from dataclasses import dataclass


@dataclass
class Sector:
    """Represents a sector or industry, shared across many companies.

    Purpose: describe the broader sector a company operates in,
    independent of any single company.
    """

    id: int  # Unique identifier for the sector record.
    name: str  # Name of the sector.
    size: str  # Sector size, as a display value.
    growth_trend: str  # Sector growth trend.
    dynamics_summary: str  # Summary of sector-wide dynamics.
    regulatory_environment: str  # Regulatory environment specific to the sector.
    benchmark_summary: str  # Comparative sector benchmarks.
