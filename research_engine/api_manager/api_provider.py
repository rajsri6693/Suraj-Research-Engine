"""
API Provider

Implements the API Provider entity and the fixed Category mapping it
represents, per project_documentation/API_MANAGER_ARCHITECTURE.md
Section 2, Section 3, and Section 5.3. An APIProvider row is one
Category role -- for example "FMP as Primary for Fundamental Data" --
never a raw provider identity by itself. Finnhub holds two roles
(Category 1 Backup, Category 3 Backup) and is represented by two
separate APIProvider rows sharing the same key_env_var and the same
Provider Interface adapter, per Section 2.

This module defines identity only. It does NOT hold live status (that
is APIHealth, api_health.py) and performs no network call.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from enum import Enum
from typing import List


class Category(Enum):
    """The three fixed API Categories, per Section 3. Exactly three --
    no others exist."""

    FUNDAMENTAL_DATA = "Fundamental Data"
    MARKET_TECHNICAL = "Market & Technical"
    NEWS = "News"


class ProviderRole(Enum):
    """A provider's role within one Category, per Section 5.3. Exactly
    one Primary and one Backup exist per Category (Section 3)."""

    PRIMARY = "Primary"
    BACKUP = "Backup"


class ProviderName(Enum):
    """The five total providers, per Section 2. Exactly five names --
    Finnhub appears once here regardless of how many Category roles it
    holds; its roles are separate APIProvider rows below, not separate
    names."""

    FMP = "Financial Modeling Prep (FMP)"
    FINNHUB = "Finnhub"
    ALPHA_VANTAGE = "Alpha Vantage"
    TWELVE_DATA = "Twelve Data"
    NEWSAPI = "NewsAPI"


@dataclass
class APIProvider:
    """One Category-role row, per Section 5.3 and Section 10.1.

    Identity only -- provider name, the Category this row applies to,
    its Role (Primary/Backup) within that Category, the name of the
    .env variable holding its key (never the key value itself), and
    whether this row is currently active. Live status belongs to
    APIHealth, never to this class.
    """

    provider_name: ProviderName
    category: Category
    role: ProviderRole
    key_env_var: str
    active: bool = True


def provider_key(provider_name: ProviderName, category: Category) -> str:
    """Stable identity for one Provider row's live status, independent
    of its current Role -- Health persists across a Manual Provider
    Switch's role swap (Section 9), per Section 8's requirement that
    Finnhub's two roles carry independent health."""
    return f"{provider_name.value}::{category.value}"


# The finalized Section 2/3 mapping -- five providers, six Category-role
# rows (Finnhub holds two Backup roles). This is the default an
# APIRegistry seeds itself with; a Future Dashboard's Manual Provider
# Switch (Section 9) mutates copies of these, never these originals.
DEFAULT_PROVIDER_REGISTRATIONS: List[APIProvider] = [
    APIProvider(ProviderName.FMP, Category.FUNDAMENTAL_DATA, ProviderRole.PRIMARY, "FMP_API_KEY"),
    APIProvider(
        ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA, ProviderRole.BACKUP, "FINNHUB_API_KEY"
    ),
    APIProvider(
        ProviderName.ALPHA_VANTAGE,
        Category.MARKET_TECHNICAL,
        ProviderRole.PRIMARY,
        "ALPHA_VANTAGE_API_KEY",
    ),
    APIProvider(
        ProviderName.TWELVE_DATA,
        Category.MARKET_TECHNICAL,
        ProviderRole.BACKUP,
        "TWELVE_DATA_API_KEY",
    ),
    APIProvider(ProviderName.NEWSAPI, Category.NEWS, ProviderRole.PRIMARY, "NEWSAPI_API_KEY"),
    APIProvider(ProviderName.FINNHUB, Category.NEWS, ProviderRole.BACKUP, "FINNHUB_API_KEY"),
]


def copy_default_registrations() -> List[APIProvider]:
    """Return a fresh, independent copy of DEFAULT_PROVIDER_REGISTRATIONS.

    APIRegistry uses this rather than the module-level list directly --
    APIProvider is mutable (role/active can change at runtime via a
    Manual Provider Switch, Section 9) and instances must never be
    shared across separate APIRegistry objects, or a change in one
    registry (or one test) would silently leak into every other.
    """
    return [dataclasses.replace(provider) for provider in DEFAULT_PROVIDER_REGISTRATIONS]
