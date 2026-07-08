"""
Metadata Schema

Logical schema for the Metadata entity of the Verified Knowledge
Database, as defined in DATABASE_ARCHITECTURE.md (Layer 5 -
Verification & Metadata).
"""

from dataclasses import dataclass
from typing import Dict


@dataclass
class Metadata:
    """Represents the freshness and completeness of a company's record.

    Purpose: describe the knowledge record itself, not the company,
    independent of the content of that record.
    """

    id: int  # Unique identifier for the metadata record.
    company_id: int  # Reference to the owning Company.
    created_at: str  # Date the knowledge record was created.
    last_verified_at: str  # Date the knowledge record was last verified.
    last_updated_at: str  # Date the knowledge record was last updated.
    verification_status: str  # Current verification status of the record.
    revision_number: int  # Revision marker for the knowledge record.
    section_completeness: Dict[str, bool]  # Completeness indicator per section.
