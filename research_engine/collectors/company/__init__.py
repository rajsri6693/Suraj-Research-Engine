"""
Company Collector package.

Public entry point for the first real Research Collector, implementing
the Company Information Knowledge Section per
project_documentation/RESEARCH_COLLECTORS.md.
"""

from .company_collector import CompanyCollector, InvalidResearchTopicError
from .company_result import CollectorStatus, CompanyResult

__all__ = [
    "CompanyCollector",
    "CompanyResult",
    "CollectorStatus",
    "InvalidResearchTopicError",
]
