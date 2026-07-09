"""
Sources Collector package.

Public entry point for the Sources Collector, implementing the Sources
Knowledge Section per project_documentation/RESEARCH_COLLECTORS.md.
"""

from .sources_collector import InvalidResearchTopicError, SourcesCollector
from .sources_result import (
    CollectorStatus,
    SourceCategory,
    SourcePriority,
    SourcesResult,
)

__all__ = [
    "SourcesCollector",
    "SourcesResult",
    "SourceCategory",
    "SourcePriority",
    "CollectorStatus",
    "InvalidResearchTopicError",
]
