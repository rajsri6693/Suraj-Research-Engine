"""
Government Policy Collector

Implements GovernmentPolicyCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Government Policies Knowledge Section and
returning a GovernmentPolicyResult.

This phase does NOT perform live research. collect() returns a valid
GovernmentPolicyResult built from placeholder/mock values only -- the
goal is to validate the Collector architecture and the Government Policy
data contract, not external data retrieval. It NEVER calls an API,
accesses the internet, verifies data, approves data, accesses a
database, writes SQLite, generates scripts or videos, or calls any other
collector.

Preferred Source Category: Government Information. Fallback Category:
Official Regulatory Information, per COLLECTOR_SOURCE_STRATEGY.md's
Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime

from ..base_collector import BaseCollector
from .government_policy_result import CollectorStatus, GovernmentPolicyResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class GovernmentPolicyCollector(BaseCollector):
    """Collects the Government Policies Knowledge Section."""

    @property
    def collector_name(self) -> str:
        return "Government Policies Collector"

    @property
    def knowledge_section(self) -> str:
        return "Government Policies"

    def collect(self, research_topic: str) -> GovernmentPolicyResult:
        """Gather Government Policy information for `research_topic`.

        Input: Research Topic. Output: a GovernmentPolicyResult.

        This phase returns placeholder/mock values only -- no live
        research, no API call, no internet access. It validates the
        collector's interface and data contract, not real collection.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        return GovernmentPolicyResult(
            policy_title="Placeholder Manufacturing Incentive Scheme",
            policy_category="Industrial Policy",
            policy_description=(
                "A placeholder policy description used to validate the "
                "Government Policy Collector's data contract; not the "
                "result of live research."
            ),
            government_authority="Ministry of Industry (placeholder)",
            effective_date=datetime(2026, 4, 1),
            affected_sectors=["Industrials"],
            affected_companies=["Sample Manufacturing Ltd"],
            expected_impact="Positive -- reduces input costs for eligible manufacturers.",
            policy_status="In Effect",
            sources=["Government Information (placeholder)"],
            collection_time=datetime.now(),
            collector_status=CollectorStatus.SUCCESS,
        )
