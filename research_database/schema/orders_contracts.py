"""
Orders & Contracts Schema

Logical schema for the Orders & Contracts entity of the Verified
Knowledge Database, as defined in DATABASE_ARCHITECTURE.md (Layer 3 -
Financial & Contractual Knowledge).
"""

from dataclasses import dataclass


@dataclass
class OrderContract:
    """Represents a single material order or contract held by a company.

    Purpose: track material orders, contracts, and agreements a company
    has entered into.
    """

    id: int  # Unique identifier for the order/contract record.
    company_id: int  # Reference to the owning Company.
    counterparty: str  # Name of the counterparty to the order/contract.
    contract_value: float  # Value of the contract or order.
    currency: str  # Currency the contract value is denominated in.
    start_date: str  # Date the contract or order began.
    duration: str  # Duration of the contract or order.
    status: str  # Current status (e.g. active, completed, terminated).
    description: str  # Description of the order or contract.
