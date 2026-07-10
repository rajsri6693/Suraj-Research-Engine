"""
Provider Interface Adapters

Public entry point for the five Provider Interface adapters, per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 2 and
Section 5.8. Per Claude-Prompts/IMP_10C_FMP_Integration.md,
IMP_10D_Alpha_Vantage_Integration.md, and
IMP_10E_Twelve_Data_Integration.md, FMP, Alpha Vantage, and Twelve Data
are now real, live-HTTP adapters (resolving their keys from
FMP_API_KEY, ALPHA_VANTAGE_API_KEY, and TWELVE_DATA_API_KEY in .env,
respectively); Finnhub and NewsAPI remain the IMP-10B placeholders --
neither makes an HTTP request, touches the network, or returns live
data. See each adapter's own module docstring for its exact scope.
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
    are explicitly injected. FMP, Alpha Vantage, and Twelve Data are
    real; the other two remain IMP-10B placeholders. Kept under its
    original name for backward compatibility with every existing
    IMP-10B caller and test."""
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
