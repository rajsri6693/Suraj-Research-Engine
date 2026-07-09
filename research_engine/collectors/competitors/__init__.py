"""
Competitors Collector package.

Public entry point for the Competitors Collector, implementing the
Competitors Knowledge Section per
project_documentation/RESEARCH_COLLECTORS.md.
"""

from .competitor_result import CollectorStatus, CompetitorResult
from .competitors_collector import CompetitorsCollector, InvalidResearchTopicError

__all__ = [
    "CompetitorsCollector",
    "CompetitorResult",
    "CollectorStatus",
    "InvalidResearchTopicError",
]
