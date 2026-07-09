"""
Financial Collector package.

Public entry point for the Financial Collector, implementing the
Financial Information Knowledge Section per
project_documentation/RESEARCH_COLLECTORS.md.
"""

from .financial_collector import FinancialCollector, InvalidResearchTopicError
from .financial_result import CollectorStatus, FinancialResult

__all__ = [
    "FinancialCollector",
    "FinancialResult",
    "CollectorStatus",
    "InvalidResearchTopicError",
]
