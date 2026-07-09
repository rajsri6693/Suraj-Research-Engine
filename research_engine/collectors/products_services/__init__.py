"""
Products & Services Collector package.

Public entry point for the Products & Services Collector, implementing
the Products & Services Knowledge Section per
project_documentation/RESEARCH_COLLECTORS.md.
"""

from .products_services_collector import (
    InvalidResearchTopicError,
    ProductsServicesCollector,
)
from .products_services_result import CollectorStatus, ProductsServicesResult

__all__ = [
    "ProductsServicesCollector",
    "ProductsServicesResult",
    "CollectorStatus",
    "InvalidResearchTopicError",
]
