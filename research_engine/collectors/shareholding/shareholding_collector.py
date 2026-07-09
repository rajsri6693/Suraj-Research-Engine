"""
Shareholding Collector

Implements ShareholdingCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Shareholding Knowledge Section and returning a
ShareholdingResult.

This phase does NOT perform live research. collect() returns a valid
ShareholdingResult built from placeholder/mock values only -- the goal
is to validate the Collector architecture and the Shareholding data
contract, not external data retrieval. It NEVER calls an API, accesses
the internet, verifies data, approves data, accesses a database, writes
SQLite, generates scripts or videos, or calls any other collector.

Preferred Source Category: Official Corporate Filings. Fallback
Category: Official Regulatory Information, per
COLLECTOR_SOURCE_STRATEGY.md's Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime

from ..base_collector import BaseCollector
from .shareholding_result import CollectorStatus, ShareholdingResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class ShareholdingCollector(BaseCollector):
    """Collects the Shareholding Knowledge Section."""

    @property
    def collector_name(self) -> str:
        return "Shareholding Collector"

    @property
    def knowledge_section(self) -> str:
        return "Shareholding"

    def collect(self, research_topic: str) -> ShareholdingResult:
        """Gather Shareholding information for `research_topic`.

        Input: Research Topic. Output: a ShareholdingResult.

        This phase returns placeholder/mock values only -- no live
        research, no API call, no internet access. It validates the
        collector's interface and data contract, not real collection.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        return ShareholdingResult(
            company_name="Sample Manufacturing Ltd",
            quarter="Q1 FY2027",
            promoter_holding=52.3,
            fii_holding=14.8,
            dii_holding=11.2,
            public_holding=21.1,
            government_holding=0.0,
            insider_holding=0.6,
            shareholding_changes=[
                "Promoter holding unchanged quarter-on-quarter.",
                "FII holding increased by 0.9 percentage points.",
            ],
            share_pledged=2.5,
            institutional_holding_summary=(
                "A placeholder institutional holding summary used to "
                "validate the Shareholding Collector's data contract; not "
                "the result of live research."
            ),
            sources=["Official Corporate Filings (placeholder)"],
            collection_time=datetime.now(),
            collector_status=CollectorStatus.SUCCESS,
        )
