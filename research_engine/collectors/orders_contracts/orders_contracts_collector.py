"""
Orders & Contracts Collector

Implements OrdersContractsCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Orders & Contracts Knowledge Section and
returning an OrderContractResult.

This phase does NOT perform live research. collect() returns a valid
OrderContractResult built from placeholder/mock values only -- the goal
is to validate the Collector architecture and the Orders & Contracts
data contract, not external data retrieval. It NEVER calls an API,
accesses the internet, verifies data, approves data, accesses a
database, writes SQLite, generates scripts or videos, or calls any other
collector.

Preferred Source Category: Official Corporate Filings. Fallback
Category: Financial News Sources, per COLLECTOR_SOURCE_STRATEGY.md's
Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime

from ..base_collector import BaseCollector
from .order_contract_result import CollectorStatus, OrderContractResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class OrdersContractsCollector(BaseCollector):
    """Collects the Orders & Contracts Knowledge Section."""

    @property
    def collector_name(self) -> str:
        return "Orders & Contracts Collector"

    @property
    def knowledge_section(self) -> str:
        return "Orders & Contracts"

    def collect(self, research_topic: str) -> OrderContractResult:
        """Gather Orders & Contracts information for `research_topic`.

        Input: Research Topic. Output: an OrderContractResult.

        This phase returns placeholder/mock values only -- no live
        research, no API call, no internet access. It validates the
        collector's interface and data contract, not real collection.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        return OrderContractResult(
            order_title="Placeholder supply contract for industrial components",
            order_type="Supply Contract",
            customer_name="Placeholder Infrastructure Ltd",
            contract_value=85_00_00_000.0,
            currency="INR",
            announcement_date=datetime(2026, 7, 3),
            execution_period="24 months from effective date",
            order_status="In Progress",
            related_company="Sample Manufacturing Ltd",
            sources=["Official Corporate Filings (placeholder)"],
            collection_time=datetime.now(),
            collector_status=CollectorStatus.SUCCESS,
        )
