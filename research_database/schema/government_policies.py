"""
Government Policies Schema

Logical schema for the Government Policies entity of the Verified
Knowledge Database, as defined in DATABASE_ARCHITECTURE.md (Layer 4 -
Market & Context Knowledge).
"""

from dataclasses import dataclass


@dataclass
class GovernmentPolicy:
    """Represents a single policy or regulatory action.

    Purpose: track policies, regulations, and government actions
    relevant to a company or its sector.
    """

    id: int  # Unique identifier for the policy record.
    sector_id: int  # Reference to the Sector this policy applies to, if any.
    company_id: int  # Reference to the Company this policy targets, if any.
    policy_name: str  # Name of the law, regulation, or action.
    policy_type: str  # Type of policy (e.g. subsidy, tariff, regulation).
    description: str  # Description of the policy.
    effective_date: str  # Date the policy takes or took effect.
