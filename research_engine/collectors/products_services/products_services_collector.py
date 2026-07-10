"""
Products & Services Collector

Implements ProductsServicesCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Products & Services Knowledge Section and
returning a ProductsServicesResult.

Per Claude-Prompts/IMP_10C_FMP_Integration.md, this collector may
optionally be given an APIManager (research_engine/api_manager/) for
Fundamental Data Category requests -- Products & Services is Primary
Provider FMP's operation for this section, per
API_MANAGER_ARCHITECTURE.md Section 2/3. Without an APIManager (the
default), collect() returns the same placeholder/mock
ProductsServicesResult as every prior phase, so every existing caller
and test is unaffected. When one is given, collect() requests through
it exclusively -- it NEVER calls FMP, Finnhub, or any provider
directly, per IMP-10C's Collectors rule -- and reflects the real
call's outcome (Success or Failed, and the real provider that served
it) onto the same placeholder shape. Mapping FMP's raw JSON response
onto each of ProductsServicesResult's individual typed fields is
future work outside this phase's scope.

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
from .products_services_result import CollectorStatus, ProductsServicesResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class ProductsServicesCollector(BaseCollector):
    """Collects the Products & Services Knowledge Section."""

    FMP_OPERATION = "Products & Services"

    def __init__(self, api_manager: Optional[APIManager] = None) -> None:
        self.api_manager = api_manager

    @property
    def collector_name(self) -> str:
        return "Products & Services Collector"

    @property
    def knowledge_section(self) -> str:
        return "Products & Services"

    def collect(self, research_topic: str) -> ProductsServicesResult:
        """Gather Products & Services information for `research_topic`.

        Input: Research Topic. Output: a ProductsServicesResult.

        Without an APIManager, returns placeholder/mock values only, as
        every prior phase did. With one, requests through it
        exclusively and reflects the real outcome onto the same
        placeholder shape -- see this module's docstring.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        result = ProductsServicesResult(
            company_name="Sample Manufacturing Ltd",
            products=["Industrial fasteners", "Precision-machined components"],
            services=["Custom manufacturing", "After-sales maintenance"],
            business_segments=["Industrial Components", "Contract Manufacturing"],
            major_brands=["Placeholder Brand A"],
            key_customers=["Placeholder Infrastructure Ltd"],
            revenue_segments={
                "Industrial Components": 68.0,
                "Contract Manufacturing": 32.0,
            },
            geographic_presence=["India", "Southeast Asia"],
            business_summary=(
                "A placeholder business summary used to validate the "
                "Products & Services Collector's data contract; not the "
                "result of live research."
            ),
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
