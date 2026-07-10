"""
Company Collector

Implements CompanyCollector, the first real Research Collector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Company Information Knowledge Section and
returning a CompanyResult.

Per Claude-Prompts/IMP_10C_FMP_Integration.md, this collector may
optionally be given an APIManager (research_engine/api_manager/) for
Fundamental Data Category requests -- Company Profile is Primary
Provider FMP's operation for this section, per
API_MANAGER_ARCHITECTURE.md Section 2/3. Without an APIManager (the
default), collect() returns the same placeholder/mock CompanyResult as
every prior phase, so every existing caller and test is unaffected.
When one is given, collect() requests through it exclusively -- it
NEVER calls FMP, Finnhub, or any provider directly, per IMP-10C's
Collectors rule -- and reflects the real call's outcome (Success or
Failed, and the real provider that served it) onto the same
placeholder shape. Mapping FMP's raw JSON response onto each of
CompanyResult's individual typed fields is future work outside this
phase's scope.

It NEVER accesses the internet itself, verifies data, approves data,
accesses a database, writes SQLite, generates scripts or videos, or
calls any other collector.

Preferred Source Category: Official Company Information. Fallback
Category: Official Corporate Filings, per
COLLECTOR_SOURCE_STRATEGY.md's Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from ...api_manager import APIManager, Category
from ..base_collector import BaseCollector
from .company_result import CollectorStatus, CompanyResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class CompanyCollector(BaseCollector):
    """Collects the Company Information Knowledge Section."""

    FMP_OPERATION = "Company Profile"

    def __init__(self, api_manager: Optional[APIManager] = None) -> None:
        self.api_manager = api_manager

    @property
    def collector_name(self) -> str:
        return "Company Information Collector"

    @property
    def knowledge_section(self) -> str:
        return "Company Information"

    def collect(self, research_topic: str) -> CompanyResult:
        """Gather Company Information for `research_topic`.

        Input: Research Topic. Output: a CompanyResult.

        Without an APIManager, returns placeholder/mock values only, as
        every prior phase did. With one, requests through it
        exclusively and reflects the real outcome onto the same
        placeholder shape -- see this module's docstring.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        result = CompanyResult(
            company_name="Sample Manufacturing Ltd",
            nse_symbol="SMFG",
            bse_symbol="500123",
            isin="INE000A00000",
            sector="Industrials",
            industry="Diversified Manufacturing",
            headquarters="Mumbai, Maharashtra, India",
            founded_year=1998,
            business_description=(
                "A placeholder business description used to validate the "
                "Company Collector's data contract; not the result of live "
                "research."
            ),
            official_website="https://example.invalid",
            sources=["Official Company Information (placeholder)"],
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
