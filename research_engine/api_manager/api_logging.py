"""
API Logging

Implements APILogEntry and APILogger, per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 5.6 and
Section 10.3. Records one entry per call attempt ever made through
APIManager -- never summarized or overwritten. Every Dashboard Usage
Count and Success Rate figure (Section 9) is computed from these
entries, never stored as a separate counter that could drift out of
sync.

Performs no network call and writes no file by itself -- this is the
in-memory record APIManager appends to. Persisting an entry into the
`api_logs` SQLite table (Section 10.3) is a separate, optional step
via research_database.repositories.api_logs_repository.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

from .api_health import HealthStatus
from .api_provider import Category, ProviderName, ProviderRole


class CallOutcome(Enum):
    """The outcome of one attempt against one provider row."""

    SUCCESS = "SUCCESS"
    FAILURE = "FAILURE"


@dataclass
class APILogEntry:
    """One call attempt, per Section 10.3.

    served_by is set only on the attempt that actually succeeded and
    served the request -- left None on a failed attempt row, including
    a Primary attempt that later failed over to a Backup that
    succeeded (that success is its own, separate entry). This lets
    "Current Provider in use" (Section 9) be read directly off the log
    without needing a separate request-id concept: it is simply the
    most recent entry, for a Category, whose served_by is not None.
    """

    timestamp: datetime
    category: Category
    operation: str
    provider_name: ProviderName
    role_attempted: ProviderRole
    outcome: CallOutcome
    health_status: HealthStatus
    response_time_ms: Optional[float] = None
    served_by: Optional[ProviderRole] = None
    collector_name: Optional[str] = None
    error: Optional[str] = None


class APILogger:
    """In-memory, append-only store of every APILogEntry, per Section
    5.6. Also computes the aggregates (Usage Count, Success Rate,
    Current Provider in use) the Dashboard needs, per Section 9 --
    these are always computed here, never separately maintained
    counters."""

    def __init__(self) -> None:
        self._entries: List[APILogEntry] = []

    def record(self, entry: APILogEntry) -> None:
        self._entries.append(entry)

    def entries(self) -> List[APILogEntry]:
        """Every entry recorded so far, oldest first."""
        return list(self._entries)

    def entries_for(
        self,
        provider_name: ProviderName,
        category: Category,
        role: Optional[ProviderRole] = None,
    ) -> List[APILogEntry]:
        return [
            entry
            for entry in self._entries
            if entry.provider_name == provider_name
            and entry.category == category
            and (role is None or entry.role_attempted == role)
        ]

    def usage_count(
        self,
        provider_name: ProviderName,
        category: Category,
        role: Optional[ProviderRole] = None,
    ) -> int:
        return len(self.entries_for(provider_name, category, role))

    def success_count(
        self,
        provider_name: ProviderName,
        category: Category,
        role: Optional[ProviderRole] = None,
    ) -> int:
        return sum(
            1
            for entry in self.entries_for(provider_name, category, role)
            if entry.outcome == CallOutcome.SUCCESS
        )

    def success_rate(
        self,
        provider_name: ProviderName,
        category: Category,
        role: Optional[ProviderRole] = None,
    ) -> Optional[float]:
        """Successful attempts / total attempts, per Section 9. None
        (not zero) when there have been no attempts at all, so a
        Dashboard can distinguish "0% success" from "never called"."""
        total = self.usage_count(provider_name, category, role)
        if total == 0:
            return None
        return self.success_count(provider_name, category, role) / total

    def most_recent_served_by(self, category: Category) -> Optional[ProviderRole]:
        """The "Current Provider in use" Dashboard field, per Section
        9 -- the role of the most recent entry, for this Category,
        that actually served a request."""
        for entry in reversed(self._entries):
            if entry.category == category and entry.served_by is not None:
                return entry.served_by
        return None

    def last_error(
        self, provider_name: ProviderName, category: Category, role: ProviderRole
    ) -> Optional[str]:
        for entry in reversed(self.entries_for(provider_name, category, role)):
            if entry.outcome == CallOutcome.FAILURE:
                return entry.error
        return None
