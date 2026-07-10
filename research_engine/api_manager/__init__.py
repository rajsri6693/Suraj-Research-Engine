"""
API Manager

Public entry point for the API Manager package, implementing the
architecture defined in
project_documentation/API_MANAGER_ARCHITECTURE.md. Every Research
Collector that performs live external API calls will go through
APIManager exclusively -- no Collector holds a reference to any
Provider Interface adapter directly.

IMP-10B implemented the complete API infrastructure -- selection,
failover, health tracking, logging, status aggregation, configuration
loading, and five placeholder Provider Interface adapters -- with no
live HTTP call anywhere in the package. Per
Claude-Prompts/IMP_10C_FMP_Integration.md,
IMP_10D_Alpha_Vantage_Integration.md, and
IMP_10E_Twelve_Data_Integration.md, FMP, Alpha Vantage, and Twelve Data
are now real, live-HTTP adapters; every other provider (Finnhub,
NewsAPI) remains an IMP-10B placeholder, and this package's own
selection/failover/health/logging logic (this file's exports below) is
unchanged by any of these integrations. See providers/ for all five
adapters,
and research_database/api_manager_schema.py plus
research_database/repositories/api_*_repository.py for the SQLite
configuration layer.
"""

from __future__ import annotations

from .api_provider import (
    DEFAULT_PROVIDER_REGISTRATIONS,
    APIProvider,
    Category,
    ProviderName,
    ProviderRole,
    copy_default_registrations,
    provider_key,
)
from .api_settings import DEFAULT_KEY_ENV_VARS, APISettings, load_env_file
from .api_health import (
    COOL_DOWN_ELIGIBLE_STATUSES,
    FAILURE_STATUSES,
    APIHealth,
    HealthStatus,
    HealthTracker,
    InvalidHealthStatusError,
)
from .api_logging import APILogEntry, APILogger, CallOutcome
from .api_registry import APIRegistry, DuplicateRoleError, ProviderRoleNotFoundError
from .provider_interface import (
    ProviderCallError,
    ProviderDownError,
    ProviderInterface,
    ProviderInvalidKeyError,
    ProviderRateLimitedError,
    ProviderResponse,
    ProviderTimeoutError,
)
from .providers import (
    AlphaVantageProvider,
    FinnhubProvider,
    FMPProvider,
    NewsAPIProvider,
    TwelveDataProvider,
    default_placeholder_adapters,
)
from .api_status import APIStatus, CategoryStatus, ProviderStatusView
from .api_manager import APIManager, APIManagerResult, InvalidRequestError

__all__ = [
    "APIManager",
    "APIManagerResult",
    "InvalidRequestError",
    "APIRegistry",
    "DuplicateRoleError",
    "ProviderRoleNotFoundError",
    "APIProvider",
    "Category",
    "ProviderRole",
    "ProviderName",
    "provider_key",
    "DEFAULT_PROVIDER_REGISTRATIONS",
    "copy_default_registrations",
    "APISettings",
    "DEFAULT_KEY_ENV_VARS",
    "load_env_file",
    "APIHealth",
    "HealthStatus",
    "HealthTracker",
    "InvalidHealthStatusError",
    "COOL_DOWN_ELIGIBLE_STATUSES",
    "FAILURE_STATUSES",
    "APILogEntry",
    "APILogger",
    "CallOutcome",
    "APIStatus",
    "CategoryStatus",
    "ProviderStatusView",
    "ProviderInterface",
    "ProviderResponse",
    "ProviderCallError",
    "ProviderDownError",
    "ProviderRateLimitedError",
    "ProviderInvalidKeyError",
    "ProviderTimeoutError",
    "FMPProvider",
    "FinnhubProvider",
    "AlphaVantageProvider",
    "TwelveDataProvider",
    "NewsAPIProvider",
    "default_placeholder_adapters",
]
