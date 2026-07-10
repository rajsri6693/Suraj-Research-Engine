"""
Twelve Data Provider (Placeholder)

Placeholder Provider Interface adapter for Twelve Data, per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 5.8 and
Section 2 (Twelve Data is Backup for Category 2 -- Market &
Technical).

This phase implements ONLY the adapter contract and a deterministic
placeholder response. It makes NO HTTP request, touches NO network,
performs NO API key validation, and returns NO live data -- call()
never actually reaches Twelve Data.
"""

from __future__ import annotations

import time
from typing import Any, Dict, Optional

from ..api_provider import ProviderName
from ..provider_interface import ProviderCallError, ProviderInterface, ProviderResponse


class TwelveDataProvider(ProviderInterface):
    """Placeholder adapter for Twelve Data. Returns deterministic mock
    data unless `simulate_failure` is set, in which case call() raises
    it instead -- the mechanism tests use to exercise the Failover
    Rules deterministically, with no network involved either way."""

    def __init__(self, simulate_failure: Optional[ProviderCallError] = None) -> None:
        self.simulate_failure = simulate_failure

    @property
    def provider_name(self) -> ProviderName:
        return ProviderName.TWELVE_DATA

    def call(self, operation: str, parameters: Dict[str, Any]) -> ProviderResponse:
        started = time.monotonic()
        if self.simulate_failure is not None:
            raise self.simulate_failure
        return ProviderResponse(
            data={
                "provider": "Twelve Data",
                "operation": operation,
                "parameters": dict(parameters),
                "placeholder": True,
            },
            response_time_ms=(time.monotonic() - started) * 1000,
        )
