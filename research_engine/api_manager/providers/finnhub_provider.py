"""
Finnhub Provider (Placeholder)

Placeholder Provider Interface adapter for Finnhub, per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 5.8 and
Section 2. Finnhub is the only provider with two Category roles --
Backup for Category 1 (Fundamental Data) and Backup for Category 3
(News, using its news endpoint) -- both answered by this single
adapter and this single key, never two separate adapters.

This phase implements ONLY the adapter contract and a deterministic
placeholder response. It makes NO HTTP request, touches NO network,
performs NO API key validation, and returns NO live data -- call()
never actually reaches Finnhub.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from ..api_provider import ProviderName
from ..provider_interface import ProviderCallError, ProviderInterface, ProviderResponse


class FinnhubProvider(ProviderInterface):
    """Placeholder adapter for Finnhub. Returns deterministic mock data
    unless `simulate_failure` is set, in which case call() raises it
    instead -- the mechanism tests use to exercise the Failover Rules
    deterministically, with no network involved either way. The same
    instance may legitimately be used to answer both of Finnhub's
    Category roles."""

    def __init__(self, simulate_failure: Optional[ProviderCallError] = None) -> None:
        self.simulate_failure = simulate_failure

    @property
    def provider_name(self) -> ProviderName:
        return ProviderName.FINNHUB

    def call(self, operation: str, parameters: Dict[str, Any]) -> ProviderResponse:
        started = time.monotonic()
        if self.simulate_failure is not None:
            raise self.simulate_failure
        return ProviderResponse(
            data={
                "provider": "Finnhub",
                "operation": operation,
                "parameters": dict(parameters),
                "placeholder": True,
            },
            response_time_ms=(time.monotonic() - started) * 1000,
        )
