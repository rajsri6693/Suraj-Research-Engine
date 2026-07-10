"""
Provider Interface

Implements ProviderInterface, the contract every provider adapter
(FMP, Finnhub, Alpha Vantage, Twelve Data, NewsAPI) must satisfy, per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 5.8. One
adapter per provider, not per Category role -- the single Finnhub
adapter answers both its Fundamental-Backup and News-Backup roles, per
Section 2.

This module defines the contract only. No adapter implementation lives
here -- see research_engine/api_manager/providers/ for the five
placeholder adapters this phase provides, none of which make an HTTP
request or touch the network.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict

from .api_provider import ProviderName


class ProviderCallError(Exception):
    """Base class for a failed Provider Interface call attempt. A
    concrete adapter raises one of this class's four subclasses below
    -- never this base class directly, and never any other exception
    type -- so APIManager can map every failure onto one of the four
    failure Health statuses (Section 8)."""


class ProviderDownError(ProviderCallError):
    """Maps to HealthStatus.DOWN -- a failure other than rate limiting
    or an invalid key."""


class ProviderRateLimitedError(ProviderCallError):
    """Maps to HealthStatus.RATE_LIMITED."""


class ProviderInvalidKeyError(ProviderCallError):
    """Maps to HealthStatus.INVALID_KEY."""


class ProviderTimeoutError(ProviderCallError):
    """Maps to HealthStatus.TIMEOUT."""


@dataclass
class ProviderResponse:
    """A successful call's normalized result, per Section 5.8."""

    data: Any
    response_time_ms: float


class ProviderInterface(ABC):
    """The contract every provider adapter implements, per Section
    5.8. Hides every vendor-specific detail behind call() so
    APIManager's selection and failover logic never needs to change
    when a provider's own API changes shape."""

    @property
    @abstractmethod
    def provider_name(self) -> ProviderName:
        """Which of the five providers (Section 2) this adapter
        implements."""
        raise NotImplementedError

    @abstractmethod
    def call(self, operation: str, parameters: Dict[str, Any]) -> ProviderResponse:
        """Perform one Operation against this provider and return a
        normalized ProviderResponse, or raise one of the four
        ProviderCallError subclasses above on failure."""
        raise NotImplementedError
