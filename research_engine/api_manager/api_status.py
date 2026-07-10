"""
API Status

Implements APIStatus, the read-only aggregated view combining
APIRegistry, HealthTracker, and APILogger for one Category, per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 5.7 and
Section 9 (Dashboard Requirements). Computes every value it returns
from those three components -- it never stores data of its own, so it
can never drift out of sync with them.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from .api_health import HealthStatus, HealthTracker
from .api_logging import APILogger
from .api_provider import Category, ProviderName, ProviderRole
from .api_registry import APIRegistry


@dataclass
class ProviderStatusView:
    """One provider row's status, as a Dashboard would display it, per
    Section 9's per-Category field list."""

    provider_name: ProviderName
    role: ProviderRole
    active: bool
    status: HealthStatus
    last_health_check: Optional[datetime]
    response_time_ms: Optional[float]
    last_error: Optional[str]
    usage_count: int
    success_rate: Optional[float]


@dataclass
class CategoryStatus:
    """The complete Dashboard view for one Category, per Section 9:
    Primary Provider, Backup Provider, Current Provider in use, and
    each provider's Status/Last Health Check/Response Time/Last
    Error/Usage Count/Success Rate."""

    category: Category
    primary: ProviderStatusView
    backup: ProviderStatusView
    current_provider_in_use: Optional[ProviderRole]


class APIStatus:
    """Read-only aggregator over APIRegistry + HealthTracker +
    APILogger, per Section 5.7. Never writes to any of the three --
    only a Manual Provider Switch (APIRegistry) or a real/manual call
    (HealthTracker, APILogger) may do that, per Section 9."""

    def __init__(
        self, registry: APIRegistry, health_tracker: HealthTracker, logger: APILogger
    ) -> None:
        self.registry = registry
        self.health_tracker = health_tracker
        self.logger = logger

    def _provider_view(self, category: Category, role: ProviderRole) -> ProviderStatusView:
        provider = self.registry.get(category, role)
        health = self.health_tracker.get(provider.provider_name, category)
        return ProviderStatusView(
            provider_name=provider.provider_name,
            role=provider.role,
            active=provider.active,
            status=health.status,
            last_health_check=health.last_health_check,
            response_time_ms=health.response_time_ms,
            last_error=health.last_error,
            usage_count=self.logger.usage_count(provider.provider_name, category, provider.role),
            success_rate=self.logger.success_rate(
                provider.provider_name, category, provider.role
            ),
        )

    def get_category_status(self, category: Category) -> CategoryStatus:
        """The complete Dashboard view for one Category, per Section
        9."""
        return CategoryStatus(
            category=category,
            primary=self._provider_view(category, ProviderRole.PRIMARY),
            backup=self._provider_view(category, ProviderRole.BACKUP),
            current_provider_in_use=self.logger.most_recent_served_by(category),
        )

    def get_all_status(self) -> List[CategoryStatus]:
        """The complete Dashboard view for every Category, per Section
        9."""
        return [self.get_category_status(category) for category in self.registry.categories()]
