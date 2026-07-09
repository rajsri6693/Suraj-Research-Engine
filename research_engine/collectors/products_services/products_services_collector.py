"""
Products & Services Collector

Implements ProductsServicesCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Products & Services Knowledge Section and
returning a ProductsServicesResult.

This phase does NOT perform live research. collect() returns a valid
ProductsServicesResult built from placeholder/mock values only -- the
goal is to validate the Collector architecture and the Products &
Services data contract, not external data retrieval. It NEVER calls an
API, accesses the internet, verifies data, approves data, accesses a
database, writes SQLite, generates scripts or videos, or calls any other
collector.

Preferred Source Category: Official Company Information. Fallback
Category: Official Corporate Filings, per
COLLECTOR_SOURCE_STRATEGY.md's Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime

from ..base_collector import BaseCollector
from .products_services_result import CollectorStatus, ProductsServicesResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class ProductsServicesCollector(BaseCollector):
    """Collects the Products & Services Knowledge Section."""

    @property
    def collector_name(self) -> str:
        return "Products & Services Collector"

    @property
    def knowledge_section(self) -> str:
        return "Products & Services"

    def collect(self, research_topic: str) -> ProductsServicesResult:
        """Gather Products & Services information for `research_topic`.

        Input: Research Topic. Output: a ProductsServicesResult.

        This phase returns placeholder/mock values only -- no live
        research, no API call, no internet access. It validates the
        collector's interface and data contract, not real collection.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        return ProductsServicesResult(
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
