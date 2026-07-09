"""
Risks Collector

Implements RisksCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Risks Knowledge Section and returning a
RiskResult.

This phase does NOT perform live research. collect() returns a valid
RiskResult built from placeholder/mock values only -- the goal is to
validate the Collector architecture and the Risk data contract, not
external data retrieval. It NEVER calls an API, accesses the internet,
verifies data, approves data, accesses a database, writes SQLite,
generates scripts or videos, or calls any other collector.

Preferred Source Category: Official Corporate Filings. Fallback
Category: Official Regulatory Information, per
COLLECTOR_SOURCE_STRATEGY.md's Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime

from ..base_collector import BaseCollector
from .risk_result import CollectorStatus, RiskResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class RisksCollector(BaseCollector):
    """Collects the Risks Knowledge Section."""

    @property
    def collector_name(self) -> str:
        return "Risks Collector"

    @property
    def knowledge_section(self) -> str:
        return "Risks"

    def collect(self, research_topic: str) -> RiskResult:
        """Gather Risk information for `research_topic`.

        Input: Research Topic. Output: a RiskResult.

        This phase returns placeholder/mock values only -- no live
        research, no API call, no internet access. It validates the
        collector's interface and data contract, not real collection.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        return RiskResult(
            company_name="Sample Manufacturing Ltd",
            business_risks=["Dependence on a small number of large customers."],
            financial_risks=["Exposure to foreign exchange rate movements."],
            operational_risks=["Reliance on a single primary manufacturing facility."],
            regulatory_risks=["Exposure to changes in import duty policy."],
            sector_risks=["Cyclical demand tied to broader industrial output."],
            market_risks=["Sensitivity to raw material price volatility."],
            key_risk_summary=(
                "A placeholder key risk summary used to validate the Risks "
                "Collector's data contract; not the result of live research."
            ),
            risk_level="Medium",
            mitigation_factors=[
                "Diversifying the customer base.",
                "Long-term supply contracts for key raw materials.",
            ],
            sources=["Official Corporate Filings (placeholder)"],
            collection_time=datetime.now(),
            collector_status=CollectorStatus.SUCCESS,
        )
