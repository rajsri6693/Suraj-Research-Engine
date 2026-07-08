"""
Sources Schema

Logical schema for the Sources entity of the Verified Knowledge
Database, as defined in DATABASE_ARCHITECTURE.md (Layer 5 -
Verification & Metadata).
"""

from dataclasses import dataclass


@dataclass
class Source:
    """Represents a single source backing one verified fact.

    Purpose: record where a fact came from, making the knowledge
    database "verified" rather than merely "collected."
    """

    id: int  # Unique identifier for the source record.
    entity_name: str  # Name of the entity the supported fact belongs to.
    record_id: int  # Identifier of the specific fact record being supported.
    source_name: str  # Name of the source.
    source_url: str  # URL or reference for the source.
    source_type: str  # Type of source (filing, news outlet, official statement, etc.).
    retrieval_date: str  # Date the source was retrieved.
