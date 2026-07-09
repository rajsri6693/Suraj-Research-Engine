"""
Orders & Contracts Collector package.

Public entry point for the Orders & Contracts Collector, implementing
the Orders & Contracts Knowledge Section per
project_documentation/RESEARCH_COLLECTORS.md.
"""

from .order_contract_result import CollectorStatus, OrderContractResult
from .orders_contracts_collector import (
    InvalidResearchTopicError,
    OrdersContractsCollector,
)

__all__ = [
    "OrdersContractsCollector",
    "OrderContractResult",
    "CollectorStatus",
    "InvalidResearchTopicError",
]
