"""
Shareholding Collector package.

Public entry point for the Shareholding Collector, implementing the
Shareholding Knowledge Section per
project_documentation/RESEARCH_COLLECTORS.md.
"""

from .shareholding_collector import InvalidResearchTopicError, ShareholdingCollector
from .shareholding_result import CollectorStatus, ShareholdingResult

__all__ = [
    "ShareholdingCollector",
    "ShareholdingResult",
    "CollectorStatus",
    "InvalidResearchTopicError",
]
