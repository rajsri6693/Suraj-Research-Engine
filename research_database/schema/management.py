"""
Management Schema

Logical schema for the Management entity of the Verified Knowledge
Database, as defined in DATABASE_ARCHITECTURE.md (Layer 2 - Company
Knowledge).
"""

from dataclasses import dataclass


@dataclass
class ManagementMember:
    """Represents a single board member or executive of a company.

    Purpose: identify who runs a company, tied back to the company they
    serve.
    """

    id: int  # Unique identifier for the management record.
    company_id: int  # Reference to the owning Company.
    full_name: str  # Full name of the board member or executive.
    role: str  # Role or title held.
    tenure_start_date: str  # Date this person's tenure began.
    tenure_end_date: str  # Date this person's tenure ended, if applicable.
    background: str  # Relevant professional background.
    is_current: bool  # Whether this person currently holds the role.
