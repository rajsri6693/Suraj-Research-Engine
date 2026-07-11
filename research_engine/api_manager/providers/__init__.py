"""
Provider Interface Adapters

Public entry point for the five Provider Interface adapters, per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 2 and
Section 5.8. Per Claude-Prompts/IMP_10C_FMP_Integration.md,
IMP_10D_Alpha_Vantage_Integration.md,
IMP_10E_Twelve_Data_Integration.md, IMP_10F_NewsAPI_Integration.md, and
IMP_10G_Finnhub_Integration.md, all five providers are now real,
live-HTTP adapters (resolving their keys from FMP_API_KEY,
FINNHUB_API_KEY, ALPHA_VANTAGE_API_KEY, TWELVE_DATA_API_KEY, and
NEWSAPI_API_KEY in .env, respectively). Finnhub is the only adapter
answering two Category roles (Fundamental Data Backup and News
Backup) through this one adapter and key, per Section 2. See each
adapter's own module docstring for its exact scope.
"""

from __future__ import annotations

from typing import Dict

from ..api_provider import ProviderName
from ..provider_interface import ProviderInterface
from .alpha_vantage_provider import AlphaVantageProvider
from .finnhub_provider import FinnhubProvider
from .fmp_provider import FMPProvider
from .newsapi_provider import NewsAPIProvider
from .twelve_data_provider import TwelveDataProvider


def default_placeholder_adapters() -> Dict[ProviderName, ProviderInterface]:
    """One adapter instance per provider (five total, matching Section
    2) -- what APIManager wires itself to by default when no adapters
    are explicitly injected. All five are now real, live-HTTP adapters.
    Kept under its original name for backward compatibility with every
    existing IMP-10B caller and test."""
    return {
        ProviderName.FMP: FMPProvider(),
        ProviderName.FINNHUB: FinnhubProvider(),
        ProviderName.ALPHA_VANTAGE: AlphaVantageProvider(),
        ProviderName.TWELVE_DATA: TwelveDataProvider(),
        ProviderName.NEWSAPI: NewsAPIProvider(),
    }


__all__ = [
    "FMPProvider",
    "FinnhubProvider",
    "AlphaVantageProvider",
    "TwelveDataProvider",
    "NewsAPIProvider",
    "default_placeholder_adapters",
]
