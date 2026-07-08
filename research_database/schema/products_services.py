"""
Products & Services Schema

Logical schema for the Products & Services entity of the Verified
Knowledge Database, as defined in DATABASE_ARCHITECTURE.md (Layer 2 -
Company Knowledge).
"""

from dataclasses import dataclass


@dataclass
class ProductService:
    """Represents a single product or service offering of a company.

    Purpose: catalog what a company sells or offers, tied back to the
    company that offers it.
    """

    id: int  # Unique identifier for the product/service record.
    company_id: int  # Reference to the owning Company.
    name: str  # Name of the product line or service.
    brand_name: str  # Brand associated with this offering.
    category: str  # Whether this offering is a product or a service.
    revenue_segment: str  # Revenue segment this offering maps to.
    target_market: str  # Target market for this offering.
    description: str  # Description of the offering.
