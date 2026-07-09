"""
Sector Collector package.

Public entry point for the Sector Collector, implementing the Sector
Information Knowledge Section per
project_documentation/RESEARCH_COLLECTORS.md.
"""

from .sector_collector import InvalidResearchTopicError, SectorCollector
from .sector_result import CollectorStatus, SectorResult

__all__ = [
    "SectorCollector",
    "SectorResult",
    "CollectorStatus",
    "InvalidResearchTopicError",
]
