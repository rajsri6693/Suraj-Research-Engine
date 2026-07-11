"""
Collector Wiring

Builds the CollectorRegistry + CollectorFactory the Research Runtime
uses, per Claude-Prompts/IMP_10I_Research_Runtime.md's Collectors
section: "Use the existing Collector Registry and Collector Factory.
No Collector may be called directly from the runtime."

Neither CollectorRegistry nor CollectorFactory is modified -- both are
used exactly as already implemented (register_collector/
create_collector is their only public contract, unchanged).
CollectorFactory.create_collector() always instantiates a registered
class with zero constructor arguments, so the only way to thread one
shared APIManager instance into every collector that accepts one
(Company, Financial, Market News, Technical Analysis, Historical
Price, Corporate Actions, Orders & Contracts, Competitors, Management,
Shareholding, Products & Services), without modifying CollectorFactory
or any collector's own source, is to register a tiny per-collector
subclass whose zero-arg __init__ supplies that APIManager -- each
subclass changes no behavior of its own collector at all, it only
binds a constructor argument that collector already, optionally,
accepts (every one of them defaults `api_manager` to None and behaves
exactly as before when it is). Collectors with no such parameter
(Sector, Government Policies, Risks, Sources, Metadata) are registered
unchanged.

The Knowledge Section -> collector class mapping mirrors
research_engine/integration/integration_engine.py's own
`_KNOWN_COLLECTORS` map exactly -- the same sixteen sections, the same
classes -- since that mapping is already the established, tested
answer to "which collector exists for which Knowledge Section" and
this module does not redesign it. IntegrationEngine's own registry is
a private instance attribute built fresh inside its own __init__,
offering no way to inject an APIManager-bound collector class in its
place, which is why the Research Runtime builds its own registry here
rather than reusing IntegrationEngine's.
"""

from __future__ import annotations

from typing import Dict, FrozenSet, Type

from research_engine.api_manager import APIManager
from research_engine.collectors.base_collector import BaseCollector
from research_engine.collectors.collector_factory import CollectorFactory
from research_engine.collectors.collector_registry import CollectorRegistry
from research_engine.collectors.company.company_collector import CompanyCollector
from research_engine.collectors.competitors.competitors_collector import (
    CompetitorsCollector,
)
from research_engine.collectors.corporate_actions.corporate_action_collector import (
    CorporateActionCollector,
)
from research_engine.collectors.financial.financial_collector import (
    FinancialCollector,
)
from research_engine.collectors.government_policy.government_policy_collector import (
    GovernmentPolicyCollector,
)
from research_engine.collectors.historical_price.historical_price_collector import (
    HistoricalPriceCollector,
)
from research_engine.collectors.management.management_collector import (
    ManagementCollector,
)
from research_engine.collectors.market_news.market_news_collector import (
    MarketNewsCollector,
)
from research_engine.collectors.metadata.metadata_collector import MetadataCollector
from research_engine.collectors.orders_contracts.orders_contracts_collector import (
    OrdersContractsCollector,
)
from research_engine.collectors.products_services.products_services_collector import (
    ProductsServicesCollector,
)
from research_engine.collectors.risks.risks_collector import RisksCollector
from research_engine.collectors.sector.sector_collector import SectorCollector
from research_engine.collectors.shareholding.shareholding_collector import (
    ShareholdingCollector,
)
from research_engine.collectors.sources.sources_collector import SourcesCollector
from research_engine.collectors.technical_analysis.technical_analysis_collector import (
    TechnicalAnalysisCollector,
)

# Knowledge Section -> collector class. Mirrors IntegrationEngine's own
# `_KNOWN_COLLECTORS` exactly -- see this module's own docstring.
KNOWN_COLLECTORS: Dict[str, Type[BaseCollector]] = {
    "Company Information": CompanyCollector,
    "Financial Information": FinancialCollector,
    "Market News": MarketNewsCollector,
    "Sector Information": SectorCollector,
    "Technical Analysis": TechnicalAnalysisCollector,
    "Government Policies": GovernmentPolicyCollector,
    "Historical Price (OHLC)": HistoricalPriceCollector,
    "Corporate Actions": CorporateActionCollector,
    "Orders & Contracts": OrdersContractsCollector,
    "Competitors": CompetitorsCollector,
    "Management": ManagementCollector,
    "Shareholding": ShareholdingCollector,
    "Risks": RisksCollector,
    "Products & Services": ProductsServicesCollector,
    "Sources": SourcesCollector,
    "Metadata": MetadataCollector,
}

# Sections whose collector's own __init__ accepts an optional
# `api_manager` keyword argument -- confirmed by reading each
# collector's own source (research_engine/collectors/*/*_collector.py).
# Every other registered collector takes no constructor argument at
# all and is registered completely unchanged.
API_MANAGER_AWARE_SECTIONS: FrozenSet[str] = frozenset(
    {
        "Company Information",
        "Financial Information",
        "Market News",
        "Technical Analysis",
        "Historical Price (OHLC)",
        "Corporate Actions",
        "Orders & Contracts",
        "Competitors",
        "Management",
        "Shareholding",
        "Products & Services",
    }
)


def _bind_api_manager(
    collector_class: Type[BaseCollector], api_manager: APIManager
) -> Type[BaseCollector]:
    """Return a subclass of `collector_class` whose zero-arg
    constructor supplies `api_manager` -- required because
    CollectorFactory.create_collector() always instantiates a
    registered class with no arguments. The subclass overrides nothing
    but __init__; collect(), collector_name, and knowledge_section all
    resolve to the original collector's own unmodified implementation."""

    class _APIManagerBoundCollector(collector_class):  # type: ignore[misc,valid-type]
        def __init__(self) -> None:
            super().__init__(api_manager=api_manager)

    _APIManagerBoundCollector.__name__ = collector_class.__name__
    _APIManagerBoundCollector.__qualname__ = collector_class.__qualname__
    return _APIManagerBoundCollector


def build_collector_registry(api_manager: APIManager) -> CollectorRegistry:
    """Build a fresh CollectorRegistry with every known collector
    registered, using only CollectorRegistry's own public
    register_collector() method. Every collector that accepts an
    APIManager is registered as a small bound subclass supplying it --
    the one wiring detail IntegrationEngine's own zero-arg registry
    does not provide. No collector's own source is modified."""
    registry = CollectorRegistry()
    for section_name, collector_class in KNOWN_COLLECTORS.items():
        if section_name in API_MANAGER_AWARE_SECTIONS:
            bound_class = _bind_api_manager(collector_class, api_manager)
        else:
            bound_class = collector_class
        registry.register_collector(section_name, bound_class)
    return registry


def build_collector_factory(api_manager: APIManager) -> CollectorFactory:
    """Build a CollectorFactory backed by a fresh
    build_collector_registry(api_manager) registry -- the runtime's
    only way to obtain a collector instance, per IMP-10I's "No
    Collector may be called directly from the runtime" rule."""
    return CollectorFactory(build_collector_registry(api_manager))
