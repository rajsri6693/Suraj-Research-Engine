"""
Risks Collector package.

Public entry point for the Risks Collector, implementing the Risks
Knowledge Section per project_documentation/RESEARCH_COLLECTORS.md.
"""

from .risk_result import CollectorStatus, RiskResult
from .risks_collector import InvalidResearchTopicError, RisksCollector

__all__ = [
    "RisksCollector",
    "RiskResult",
    "CollectorStatus",
    "InvalidResearchTopicError",
]
