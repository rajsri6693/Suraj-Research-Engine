"""
Order Contract Result

Implements OrderContractResult, the structured Collected Data the Orders
& Contracts Collector produces for the Orders & Contracts Knowledge
Section, per project_documentation/KNOWLEDGE_MODEL.md and
project_documentation/RESEARCH_COLLECTORS.md.

CollectorStatus is defined locally here, matching RESEARCH_COLLECTORS.md
Section 5's own three values exactly (Success, Partial, Failed), rather
than imported from research_engine.assembly -- that module is outside
IMP-08I's source of truth, and a real collector's own result package
should be self-contained.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List


class CollectorStatus(Enum):
    """Whether this collector's own attempt succeeded, per
    RESEARCH_COLLECTORS.md Section 5."""

    SUCCESS = "Success"
    PARTIAL = "Partial"
    FAILED = "Failed"


@dataclass
class OrderContractResult:
    """The Orders & Contracts Collector's Collected Data for one order
    or contract, per IMP-08I's field list."""

    order_title: str
    order_type: str
    customer_name: str
    contract_value: float
    currency: str
    announcement_date: datetime
    execution_period: str
    order_status: str
    related_company: str
    sources: List[str]
    collection_time: datetime
    collector_status: CollectorStatus
