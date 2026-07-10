"""
Corporate Action Collector

Implements CorporateActionCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Corporate Actions Knowledge Section and
returning a CorporateActionResult.

Per Claude-Prompts/IMP_10C_FMP_Integration.md, this collector may
optionally be given an APIManager (research_engine/api_manager/) for
Fundamental Data Category requests -- Corporate Actions is Primary
Provider FMP's operation for this section, per
API_MANAGER_ARCHITECTURE.md Section 2/3. Without an APIManager (the
default), collect() returns the same placeholder/mock
CorporateActionResult as every prior phase, so every existing caller
and test is unaffected. When one is given, collect() requests through
it exclusively -- it NEVER calls FMP, Finnhub, or any provider
directly, per IMP-10C's Collectors rule -- and reflects the real
call's outcome (Success or Failed, and the real provider that served
it) onto the same placeholder shape. Mapping FMP's raw JSON response
onto each of CorporateActionResult's individual typed fields is future
work outside this phase's scope.

It NEVER accesses the internet itself, verifies data, approves data,
accesses a database, writes SQLite, generates scripts or videos, or
calls any other collector.

Preferred Source Category: Official Corporate Filings. Fallback
Category: Official Exchange Information, per
COLLECTOR_SOURCE_STRATEGY.md's Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from ...api_manager import APIManager, Category
from ..base_collector import BaseCollector
from .corporate_action_result import CollectorStatus, CorporateActionResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class CorporateActionCollector(BaseCollector):
    """Collects the Corporate Actions Knowledge Section."""

    FMP_OPERATION = "Corporate Actions"

    def __init__(self, api_manager: Optional[APIManager] = None) -> None:
        self.api_manager = api_manager

    @property
    def collector_name(self) -> str:
        return "Corporate Actions Collector"

    @property
    def knowledge_section(self) -> str:
        return "Corporate Actions"

    def collect(self, research_topic: str) -> CorporateActionResult:
        """Gather Corporate Action information for `research_topic`.

        Input: Research Topic. Output: a CorporateActionResult.

        Without an APIManager, returns placeholder/mock values only, as
        every prior phase did. With one, requests through it
        exclusively and reflects the real outcome onto the same
        placeholder shape -- see this module's docstring.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        result = CorporateActionResult(
            action_type="Dividend",
            action_title="Interim dividend for FY2026",
            announcement_date=datetime(2026, 7, 1),
            effective_date=datetime(2026, 7, 20),
            record_date=datetime(2026, 7, 15),
            description=(
                "A placeholder corporate action description used to validate "
                "the Corporate Action Collector's data contract; not the "
                "result of live research."
            ),
            impact_summary="Positive -- returns cash to shareholders.",
            related_company="Sample Manufacturing Ltd",
            sources=["Official Corporate Filings (placeholder)"],
            collection_time=datetime.now(),
            collector_status=CollectorStatus.SUCCESS,
        )

        if self.api_manager is None:
            return result

        api_result = self.api_manager.request(
            Category.FUNDAMENTAL_DATA,
            self.FMP_OPERATION,
            {"symbol": research_topic},
            collector_name=self.collector_name,
        )
        if api_result.success:
            result.sources = [f"{api_result.provider_name.value} ({api_result.served_by.value})"]
            result.collector_status = CollectorStatus.SUCCESS
        else:
            result.sources = []
            result.collector_status = CollectorStatus.FAILED

        return result
