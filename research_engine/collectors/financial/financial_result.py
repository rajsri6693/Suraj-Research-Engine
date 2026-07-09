"""
Financial Result

Implements FinancialResult, the structured Collected Data the Financial
Collector produces for the Financial Information Knowledge Section, per
project_documentation/KNOWLEDGE_MODEL.md and
project_documentation/RESEARCH_COLLECTORS.md.

CollectorStatus is defined locally here, matching RESEARCH_COLLECTORS.md
Section 5's own three values exactly (Success, Partial, Failed), rather
than imported from research_engine.assembly -- that module is outside
IMP-08B's source of truth, and a real collector's own result package
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
class FinancialResult:
    """The Financial Information Collector's Collected Data for one
    company, for one financial period, per IMP-08B's field list."""

    revenue: float
    net_profit: float
    eps: float
    book_value: float
    pe_ratio: float
    roe: float
    roce: float
    debt_to_equity: float
    market_capitalization: float
    dividend_yield: float
    financial_year: str
    sources: List[str]
    collection_time: datetime
    collector_status: CollectorStatus
