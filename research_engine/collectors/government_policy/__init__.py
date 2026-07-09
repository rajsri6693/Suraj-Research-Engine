"""
Government Policy Collector package.

Public entry point for the Government Policy Collector, implementing the
Government Policies Knowledge Section per
project_documentation/RESEARCH_COLLECTORS.md.
"""

from .government_policy_collector import (
    GovernmentPolicyCollector,
    InvalidResearchTopicError,
)
from .government_policy_result import CollectorStatus, GovernmentPolicyResult

__all__ = [
    "GovernmentPolicyCollector",
    "GovernmentPolicyResult",
    "CollectorStatus",
    "InvalidResearchTopicError",
]
