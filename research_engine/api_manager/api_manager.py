"""
API Manager

Implements APIManager, the single gateway every Research Collector
will call instead of any external provider directly, per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 5.1. Owns
Provider Selection Logic (Section 6) and the five-step Failover Rules
(Section 7), delegating the actual call to whichever Provider
Interface adapter it selects, and recording every attempt through
HealthTracker and APILogger.

This phase wires the gateway to placeholder Provider Interface
adapters only (research_engine/api_manager/providers/) -- none of
which make an HTTP request, touch the network, or return live data.
Wiring a real HTTP-calling adapter in place of a placeholder is future
work; nothing in this class needs to change when that happens, since
APIManager only ever depends on the ProviderInterface contract
(provider_interface.py), never on a concrete provider.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from .api_health import HealthStatus, HealthTracker
from .api_logging import APILogEntry, APILogger, CallOutcome
from .api_provider import APIProvider, Category, ProviderName, ProviderRole
from .api_registry import APIRegistry
from .api_settings import APISettings
from .provider_interface import (
    ProviderCallError,
    ProviderDownError,
    ProviderInterface,
    ProviderInvalidKeyError,
    ProviderRateLimitedError,
    ProviderResponse,
    ProviderTimeoutError,
)
from .providers import default_placeholder_adapters

_HEALTH_STATUS_BY_ERROR: Dict[type, HealthStatus] = {
    ProviderDownError: HealthStatus.DOWN,
    ProviderRateLimitedError: HealthStatus.RATE_LIMITED,
    ProviderInvalidKeyError: HealthStatus.INVALID_KEY,
    ProviderTimeoutError: HealthStatus.TIMEOUT,
}


class InvalidRequestError(Exception):
    """Raised when request() is given an empty Operation, or no
    Provider Interface adapter is registered for a provider the
    Registry names."""


@dataclass
class APIManagerResult:
    """The outcome of one APIManager.request() call -- what a Collector
    actually receives. Never raises for an ordinary provider failure;
    a Collector inspects `success` exactly as it inspects Collector
    Status, per RESEARCH_COLLECTORS.md Section 5, rather than catching
    an exception for an expected, ordinary outcome."""

    success: bool
    category: Category
    operation: str
    data: Optional[Any] = None
    served_by: Optional[ProviderRole] = None
    provider_name: Optional[ProviderName] = None
    response_time_ms: Optional[float] = None
    error: Optional[str] = None


class APIManager:
    """Single gateway for every external API call, per Section 5.1.
    Collectors call only this class -- never a Provider Interface
    adapter directly, per the "Collectors ONLY communicate with API
    Manager" rule."""

    def __init__(
        self,
        registry: Optional[APIRegistry] = None,
        settings: Optional[APISettings] = None,
        health_tracker: Optional[HealthTracker] = None,
        logger: Optional[APILogger] = None,
        adapters: Optional[Dict[ProviderName, ProviderInterface]] = None,
    ) -> None:
        self.registry = registry or APIRegistry()
        self.settings = settings or APISettings()
        self.health_tracker = health_tracker or HealthTracker(
            self.settings.cool_down_seconds, self.settings.invalid_key_cool_down_seconds
        )
        self.logger = logger or APILogger()
        self.adapters = adapters or default_placeholder_adapters()

    def _adapter_for(self, provider_name: ProviderName) -> ProviderInterface:
        try:
            return self.adapters[provider_name]
        except KeyError as exc:
            raise InvalidRequestError(
                f"No Provider Interface adapter registered for {provider_name.value}."
            ) from exc

    def _attempt(
        self,
        provider: APIProvider,
        operation: str,
        parameters: Dict[str, Any],
        category: Category,
        collector_name: Optional[str],
    ) -> Tuple[Optional[ProviderResponse], Optional[str]]:
        """Call one provider row's adapter once. Always logs the
        attempt and updates Health, regardless of outcome, per the
        five Failover Rule steps (Section 7). Returns (response, None)
        on success, or (None, error message) on failure."""
        adapter = self._adapter_for(provider.provider_name)
        started = datetime.now()
        try:
            response = adapter.call(operation, parameters)
        except ProviderCallError as error:
            health_status = _HEALTH_STATUS_BY_ERROR.get(type(error), HealthStatus.DOWN)
            # Steps 1-2: record the failure, mark the provider.
            self.health_tracker.record_failure(
                provider.provider_name,
                category,
                health_status,
                str(error),
                checked_at=started,
            )
            self.logger.record(
                APILogEntry(
                    timestamp=started,
                    category=category,
                    operation=operation,
                    provider_name=provider.provider_name,
                    role_attempted=provider.role,
                    outcome=CallOutcome.FAILURE,
                    health_status=health_status,
                    response_time_ms=None,
                    served_by=None,
                    collector_name=collector_name,
                    error=str(error),
                )
            )
            return None, str(error)

        self.health_tracker.record_success(
            provider.provider_name, category, response.response_time_ms, checked_at=started
        )
        # Step 5: log which provider actually served the request.
        self.logger.record(
            APILogEntry(
                timestamp=started,
                category=category,
                operation=operation,
                provider_name=provider.provider_name,
                role_attempted=provider.role,
                outcome=CallOutcome.SUCCESS,
                health_status=HealthStatus.ONLINE,
                response_time_ms=response.response_time_ms,
                served_by=provider.role,
                collector_name=collector_name,
            )
        )
        return response, None

    def request(
        self,
        category: Category,
        operation: str,
        parameters: Optional[Dict[str, Any]] = None,
        collector_name: Optional[str] = None,
    ) -> APIManagerResult:
        """Provider Selection Logic (Section 6) + Failover Rules
        (Section 7): attempt the Category's Primary Provider first
        unless Health already marks it unusable; on failure, record
        the failure, mark it DOWN/RATE_LIMITED/INVALID_KEY/TIMEOUT,
        call the Backup (Step 3), and return whichever response
        actually served the request (Step 4). Returns an explicit
        failure result if both fail -- never fabricated data."""
        if not operation or not operation.strip():
            raise InvalidRequestError("Operation must not be empty.")
        parameters = dict(parameters) if parameters else {}

        primary = self.registry.get_primary(category)
        backup = self.registry.get_backup(category)

        last_error: Optional[str] = None

        if not primary.active:
            last_error = f"{primary.provider_name.value} (Primary) is disabled."
        elif not self.health_tracker.is_usable(primary.provider_name, category):
            primary_status = self.health_tracker.get(primary.provider_name, category).status
            last_error = (
                f"{primary.provider_name.value} (Primary) is currently "
                f"{primary_status.value} per API Health."
            )
        else:
            response, error = self._attempt(
                primary, operation, parameters, category, collector_name
            )
            if response is not None:
                return APIManagerResult(
                    success=True,
                    category=category,
                    operation=operation,
                    data=response.data,
                    served_by=ProviderRole.PRIMARY,
                    provider_name=primary.provider_name,
                    response_time_ms=response.response_time_ms,
                )
            last_error = error

        # Failover Rules, Section 7, Step 3: the Backup is attempted
        # whenever the Primary actually failed this request, or was
        # already known unusable -- never called speculatively
        # alongside the Primary (Section 6).
        if not backup.active:
            failure_message = last_error or f"{backup.provider_name.value} (Backup) is disabled."
            return APIManagerResult(
                success=False, category=category, operation=operation, error=failure_message
            )

        response, error = self._attempt(backup, operation, parameters, category, collector_name)
        if response is not None:
            return APIManagerResult(
                success=True,
                category=category,
                operation=operation,
                data=response.data,
                served_by=ProviderRole.BACKUP,
                provider_name=backup.provider_name,
                response_time_ms=response.response_time_ms,
            )

        return APIManagerResult(
            success=False,
            category=category,
            operation=operation,
            error=error or "Both Primary and Backup providers failed.",
        )

    def health_check(self, category: Category, role: ProviderRole) -> "HealthStatus":
        """Manual Health Check button, per Section 9: an on-demand call
        through the given Category-role's adapter, purely to refresh
        Health -- bypasses is_usable()/cool-down entirely, since a
        human deliberately triggered this (for example, after fixing a
        key). This is the one path, alongside a real request(), allowed
        to update Health, per Section 8. Returns the refreshed
        status."""
        provider = self.registry.get(category, role)
        self._attempt(provider, "HealthCheck", {}, category, collector_name=None)
        return self.health_tracker.get(provider.provider_name, category).status
