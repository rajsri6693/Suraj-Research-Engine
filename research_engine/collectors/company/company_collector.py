"""
Company Collector

Implements CompanyCollector, the first real Research Collector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Company Information Knowledge Section and
returning a CompanyResult.

This phase does NOT perform live research. collect() returns a valid
CompanyResult built from placeholder/mock values only -- the goal is to
validate the Collector architecture, interfaces, and data contracts, not
external data retrieval. It NEVER calls an API, accesses the internet,
verifies data, approves data, accesses a database, writes SQLite,
generates scripts or videos, or calls any other collector.

Preferred Source Category: Official Company Information. Fallback
Category: Official Corporate Filings, per
COLLECTOR_SOURCE_STRATEGY.md's Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime

from ..base_collector import BaseCollector
from .company_result import CollectorStatus, CompanyResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class CompanyCollector(BaseCollector):
    """Collects the Company Information Knowledge Section."""

    @property
    def collector_name(self) -> str:
        return "Company Information Collector"

    @property
    def knowledge_section(self) -> str:
        return "Company Information"

    def collect(self, research_topic: str) -> CompanyResult:
        """Gather Company Information for `research_topic`.

        Input: Research Topic. Output: a CompanyResult.

        This phase returns placeholder/mock values only -- no live
        research, no API call, no internet access. It validates the
        collector's interface and data contract, not real collection.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        return CompanyResult(
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
