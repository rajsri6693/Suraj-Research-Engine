"""
Corporate Action Collector package.

Public entry point for the Corporate Action Collector, implementing the
Corporate Actions Knowledge Section per
project_documentation/RESEARCH_COLLECTORS.md.
"""

from .corporate_action_collector import (
    CorporateActionCollector,
    InvalidResearchTopicError,
)
from .corporate_action_result import CollectorStatus, CorporateActionResult

__all__ = [
    "CorporateActionCollector",
    "CorporateActionResult",
    "CollectorStatus",
    "InvalidResearchTopicError",
]
