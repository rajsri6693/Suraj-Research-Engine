"""
Financial Collector

Implements FinancialCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Financial Information Knowledge Section and
returning a FinancialResult.

This phase does NOT perform live research. collect() returns a valid
FinancialResult built from placeholder/mock values only -- the goal is to
validate the Collector architecture and the Financial data contract, not
external data retrieval. It NEVER calls an API, accesses the internet,
verifies data, approves data, accesses a database, writes SQLite,
generates scripts or videos, or calls any other collector.

Preferred Source Category: Official Financial Statements. Fallback
Category: Official Corporate Filings, per
COLLECTOR_SOURCE_STRATEGY.md's Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime

from ..base_collector import BaseCollector
from .financial_result import CollectorStatus, FinancialResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class FinancialCollector(BaseCollector):
    """Collects the Financial Information Knowledge Section."""

    @property
    def collector_name(self) -> str:
        return "Financial Information Collector"

    @property
    def knowledge_section(self) -> str:
        return "Financial Information"

    def collect(self, research_topic: str) -> FinancialResult:
        """Gather Financial Information for `research_topic`.

        Input: Research Topic. Output: a FinancialResult.

        This phase returns placeholder/mock values only -- no live
        research, no API call, no internet access. It validates the
        collector's interface and data contract, not real collection.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        return FinancialResult(
            revenue=412_00_00_000.0,
            net_profit=28_00_00_000.0,
            eps=14.75,
            book_value=182.30,
            pe_ratio=21.6,
            roe=16.2,
            roce=18.9,
            debt_to_equity=0.42,
            market_capitalization=6_500_00_00_000.0,
            dividend_yield=1.3,
            financial_year="FY2026",
            sources=["Official Financial Statements (placeholder)"],
            collection_time=datetime.now(),
            collector_status=CollectorStatus.SUCCESS,
        )
