"""
Metadata Collector package.

Public entry point for the Metadata Collector, implementing the
Metadata Knowledge Section per
project_documentation/RESEARCH_COLLECTORS.md.
"""

from .metadata_collector import InvalidResearchTopicError, MetadataCollector
from .metadata_result import CollectorStatus, MetadataResult

__all__ = [
    "MetadataCollector",
    "MetadataResult",
    "CollectorStatus",
    "InvalidResearchTopicError",
]
