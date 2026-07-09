"""
Management Collector package.

Public entry point for the Management Collector, implementing the
Management Knowledge Section per
project_documentation/RESEARCH_COLLECTORS.md.
"""

from .management_collector import InvalidResearchTopicError, ManagementCollector
from .management_result import CollectorStatus, ManagementResult

__all__ = [
    "ManagementCollector",
    "ManagementResult",
    "CollectorStatus",
    "InvalidResearchTopicError",
]
