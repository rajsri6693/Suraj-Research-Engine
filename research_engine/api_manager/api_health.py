"""
API Health

Implements APIHealth and HealthTracker, per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 5.5, Section
6, and Section 8. Tracks the live, current status of one APIProvider
row -- never a raw provider identity, since a single provider
(Finnhub) can hold two independent Category roles with independent
health, per Section 8.

Performs no network call. Status is only ever set by a caller
(APIManager, after a real Provider Interface call attempt, or a
manual Health Check) -- this module never decides on its own when a
call happened.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from .api_provider import Category, ProviderName, provider_key


class HealthStatus(Enum):
    """The six Health states, per Section 8. Exact set -- no others are
    valid."""

    ONLINE = "ONLINE"
    DOWN = "DOWN"
    RATE_LIMITED = "RATE_LIMITED"
    INVALID_KEY = "INVALID_KEY"
    TIMEOUT = "TIMEOUT"
    UNKNOWN = "UNKNOWN"


# Eligible for the short cool-down retry described in Section 8.
# INVALID_KEY is deliberately excluded -- it is longer-lived and only
# cleared by a deliberate, manual Health Check (Section 9), never an
# automatic cool-down.
COOL_DOWN_ELIGIBLE_STATUSES = frozenset(
    {HealthStatus.DOWN, HealthStatus.RATE_LIMITED, HealthStatus.TIMEOUT}
)

FAILURE_STATUSES = COOL_DOWN_ELIGIBLE_STATUSES | {HealthStatus.INVALID_KEY}


@dataclass
class APIHealth:
    """Live status for one APIProvider row, per Section 5.5 and Section
    10.2. One APIHealth record per APIProvider row (One-to-One, Section
    10.4) -- never per raw provider name."""

    provider_key: str
    status: HealthStatus = HealthStatus.UNKNOWN
    last_health_check: Optional[datetime] = None
    response_time_ms: Optional[float] = None
    last_error: Optional[str] = None
    consecutive_failures: int = 0


class InvalidHealthStatusError(Exception):
    """Raised when record_failure() is given a status that is not one
    of the four failure states (DOWN, RATE_LIMITED, INVALID_KEY,
    TIMEOUT)."""


class HealthTracker:
    """In-memory live-status store, keyed by provider_key(). Owns
    is_usable() -- Provider Selection Logic's (Section 6) gate on
    whether a provider row may currently be attempted -- and the
    record_success()/record_failure() calls APIManager makes after
    every attempt."""

    def __init__(
        self,
        cool_down_seconds: float = 60.0,
        invalid_key_cool_down_seconds: float = 3600.0,
    ) -> None:
        self.cool_down_seconds = cool_down_seconds
        self.invalid_key_cool_down_seconds = invalid_key_cool_down_seconds
        self._records: Dict[str, APIHealth] = {}

    def get(self, provider_name: ProviderName, category: Category) -> APIHealth:
        """Return the APIHealth record for this provider row, creating
        a fresh UNKNOWN one on first access -- UNKNOWN is always the
        default, per Section 8, never an assumed ONLINE."""
        key = provider_key(provider_name, category)
        return self._records.setdefault(key, APIHealth(provider_key=key))

    def record_success(
        self,
        provider_name: ProviderName,
        category: Category,
        response_time_ms: Optional[float],
        checked_at: Optional[datetime] = None,
    ) -> APIHealth:
        health = self.get(provider_name, category)
        health.status = HealthStatus.ONLINE
        health.last_health_check = checked_at or datetime.now()
        health.response_time_ms = response_time_ms
        health.last_error = None
        health.consecutive_failures = 0
        return health

    def record_failure(
        self,
        provider_name: ProviderName,
        category: Category,
        status: HealthStatus,
        error: str,
        response_time_ms: Optional[float] = None,
        checked_at: Optional[datetime] = None,
    ) -> APIHealth:
        if status not in FAILURE_STATUSES:
            raise InvalidHealthStatusError(
                f"'{status}' is not a valid failure status; expected one of "
                f"{sorted(s.value for s in FAILURE_STATUSES)}."
            )
        health = self.get(provider_name, category)
        health.status = status
        health.last_health_check = checked_at or datetime.now()
        health.response_time_ms = response_time_ms
        health.last_error = error
        health.consecutive_failures += 1
        return health

    def is_usable(
        self,
        provider_name: ProviderName,
        category: Category,
        now: Optional[datetime] = None,
    ) -> bool:
        """Provider Selection Logic's health gate, per Section 6 and
        Section 8. ONLINE and UNKNOWN are always usable. INVALID_KEY is
        never auto-retried -- only a manual Health Check (Section 9)
        clears it. DOWN/RATE_LIMITED/TIMEOUT become usable again once
        the configured cool-down has elapsed since the last check.
        """
        health = self.get(provider_name, category)
        if health.status in (HealthStatus.ONLINE, HealthStatus.UNKNOWN):
            return True
        if health.status == HealthStatus.INVALID_KEY:
            return False

        now = now or datetime.now()
        if health.last_health_check is None:
            return True
        elapsed = (now - health.last_health_check).total_seconds()
        return elapsed >= self.cool_down_seconds
