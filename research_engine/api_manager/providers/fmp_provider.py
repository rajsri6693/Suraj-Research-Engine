"""
FMP Provider

Live Provider Interface adapter for Financial Modeling Prep (FMP) --
Primary Provider for Category 1 (Fundamental Data), per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 2/5.8 and
Claude-Prompts/IMP_10C_FMP_Integration.md. Only FMP is implemented
live in this phase -- Finnhub, Alpha Vantage, Twelve Data, and NewsAPI
remain the IMP-10B placeholders in their own modules, unchanged.

API Authentication: the FMP API key is never hardcoded. It is resolved
from the environment's FMP_API_KEY variable (the single project .env
file) via APISettings.resolve_key() on every call -- not cached at
construction, so a key corrected in .env is picked up without
recreating this adapter, matching the INVALID_KEY recovery story in
API_MANAGER_ARCHITECTURE.md Section 8.

HTTP Client: uses only the Python standard library (urllib.request,
json) -- no external HTTP dependency, matching the existing convention
already used by research_engine/notifications/telegram_notification.py.
The one place a socket is ever touched is _send_request(); every test
in this repository replaces it (or urllib.request.urlopen beneath it),
so no test in this codebase ever makes a live internet call.

`simulate_failure` is preserved from the IMP-10B placeholder contract
and still takes precedence over any real HTTP work when set. This is
what lets every IMP-10B test that exercises Provider Selection Logic
and the Failover Rules through FMPProvider keep passing completely
unmodified -- this file adds real behavior behind the same interface,
it does not replace or redesign it.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Dict, List, Mapping, Optional, Tuple, Type

from ..api_provider import ProviderName
from ..api_settings import APISettings
from ..provider_interface import (
    ProviderCallError,
    ProviderDownError,
    ProviderInterface,
    ProviderInvalidKeyError,
    ProviderRateLimitedError,
    ProviderResponse,
    ProviderTimeoutError,
)

DEFAULT_BASE_URL = "https://financialmodelingprep.com/api/v3"

# Operation -> FMP endpoint path template, per IMP_10C_FMP_Integration.md's
# Supported Data list. `{symbol}` is filled in from the request's
# `symbol` parameter. Exactly the twelve Fundamental Data operations
# FMP is Primary for -- no other operation is implemented in this
# phase.
_OPERATION_ENDPOINTS: Dict[str, str] = {
    "Company Profile": "/profile/{symbol}",
    "Financial Statements": "/income-statement/{symbol}",
    "Financial Ratios": "/ratios/{symbol}",
    "Earnings": "/earnings-surprises/{symbol}",
    "Dividend": "/historical-price-full/stock_dividend/{symbol}",
    "Stock Split": "/historical-price-full/stock_split/{symbol}",
    "Management": "/key-executives/{symbol}",
    "Shareholding": "/institutional-holder/{symbol}",
    "Competitors": "/stock-peers",
    "Products & Services": "/profile/{symbol}",
    "Corporate Actions": "/historical-price-full/stock_dividend/{symbol}",
    "Orders & Contracts": "/sec_filings/{symbol}",
}

# "Financial Statements" alone has a `statement_type` sub-selector
# ("income" (default), "balance", "cash") layered on top of the table
# above.
_FINANCIAL_STATEMENT_PATHS: Dict[str, str] = {
    "income": "/income-statement/{symbol}",
    "balance": "/balance-sheet-statement/{symbol}",
    "cash": "/cash-flow-statement/{symbol}",
}

_INVALID_KEY_MESSAGE_MARKERS = ("invalid api key", "apikey")
_RATE_LIMIT_MESSAGE_MARKERS = ("limit reach", "rate limit", "too many requests")

_HEALTH_CHECK_OPERATION = "Company Profile"
_HEALTH_CHECK_SYMBOL = "AAPL"


class FMPRequestError(Exception):
    """Raised for a malformed request -- an unsupported Operation, an
    unknown `statement_type`, or a missing required `symbol` parameter
    -- before any network call is attempted. Distinct from
    ProviderCallError: this is a caller programming error, never a
    provider health signal, so APIManager never sees or maps it."""


@dataclass
class FMPRequestLogEntry:
    """One HTTP attempt this adapter instance made, kept in memory for
    inspection and testing. Distinct from, and in addition to, the
    api_logs record APIManager already keeps for every provider
    (API_MANAGER_ARCHITECTURE.md Section 5.6/10.3) -- this is FMP's own
    finer-grained record of retries within a single APIManager
    request, never persisted, never read by APIManager itself."""

    url: str
    attempt: int
    status_code: Optional[int]
    response_time_ms: float
    outcome: str  # "SUCCESS" or "FAILURE"
    error: Optional[str] = None


class FMPProvider(ProviderInterface):
    """Live Provider Interface adapter for Financial Modeling Prep."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        settings: Optional[APISettings] = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout_seconds: Optional[float] = None,
        max_retries: int = 2,
        retry_delay_seconds: float = 0.0,
        env: Optional[Mapping[str, str]] = None,
        simulate_failure: Optional[ProviderCallError] = None,
    ) -> None:
        self._explicit_api_key = api_key
        self.settings = settings or APISettings()
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else self.settings.timeout_seconds
        )
        self.max_retries = max(0, max_retries)
        self.retry_delay_seconds = retry_delay_seconds
        self._env = env
        # IMP-10B placeholder compatibility -- see module docstring.
        self.simulate_failure = simulate_failure
        self._request_log: List[FMPRequestLogEntry] = []

    @property
    def provider_name(self) -> ProviderName:
        return ProviderName.FMP

    @property
    def request_log(self) -> List[FMPRequestLogEntry]:
        """Every HTTP attempt made by this instance, oldest first."""
        return list(self._request_log)

    # ------------------------------------------------------------------
    # Provider Interface contract
    # ------------------------------------------------------------------

    def call(self, operation: str, parameters: Dict[str, Any]) -> ProviderResponse:
        if self.simulate_failure is not None:
            raise self.simulate_failure

        if operation == "HealthCheck":
            return self._connection_check()

        return self._request(operation, parameters)

    # ------------------------------------------------------------------
    # Connection Validation
    # ------------------------------------------------------------------

    def _connection_check(self) -> ProviderResponse:
        """A lightweight real call (Company Profile for a fixed, benign
        symbol) used to answer APIManager's manual Health Check
        (API_MANAGER_ARCHITECTURE.md Section 9), unchanged. Fails
        exactly like a normal request -- INVALID_KEY, TIMEOUT,
        RATE_LIMITED, or DOWN -- there is no separate connectivity
        error type."""
        return self._request(_HEALTH_CHECK_OPERATION, {"symbol": _HEALTH_CHECK_SYMBOL})

    # ------------------------------------------------------------------
    # API Authentication
    # ------------------------------------------------------------------

    def _resolve_api_key(self) -> Optional[str]:
        if self._explicit_api_key:
            return self._explicit_api_key
        return self.settings.resolve_key(ProviderName.FMP, self._env)

    # ------------------------------------------------------------------
    # Request Builder
    # ------------------------------------------------------------------

    def _endpoint_path(self, operation: str, parameters: Dict[str, Any]) -> str:
        if operation == "Financial Statements":
            statement_type = parameters.get("statement_type", "income")
            path = _FINANCIAL_STATEMENT_PATHS.get(statement_type)
            if path is None:
                raise FMPRequestError(
                    f"Unknown statement_type '{statement_type}'; expected one of "
                    f"{sorted(_FINANCIAL_STATEMENT_PATHS)}."
                )
            return path

        path = _OPERATION_ENDPOINTS.get(operation)
        if path is None:
            raise FMPRequestError(
                f"'{operation}' is not a supported FMP operation; expected one of "
                f"{sorted(_OPERATION_ENDPOINTS)}."
            )
        return path

    def _build_url(self, operation: str, parameters: Dict[str, Any], api_key: str) -> str:
        path_template = self._endpoint_path(operation, parameters)

        query_params = {
            key: value
            for key, value in parameters.items()
            if key not in ("symbol", "statement_type")
        }

        if "{symbol}" in path_template:
            symbol = parameters.get("symbol")
            if not symbol:
                raise FMPRequestError(f"Operation '{operation}' requires a 'symbol' parameter.")
            path = path_template.format(symbol=urllib.parse.quote(str(symbol)))
        else:
            path = path_template
            if "symbol" in parameters:
                query_params["symbol"] = parameters["symbol"]

        query_params["apikey"] = api_key
        query_string = urllib.parse.urlencode(query_params)
        return f"{self.base_url}{path}?{query_string}"

    # ------------------------------------------------------------------
    # HTTP Client
    # ------------------------------------------------------------------

    def _send_request(self, url: str) -> Tuple[int, bytes]:
        """The one place an actual network call happens. Isolated so
        tests replace it entirely -- no live internet call is ever made
        during a test in this repository."""
        request = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
            return response.status, response.read()

    # ------------------------------------------------------------------
    # Error Handling / Rate Limit Handling / Timeout Handling
    # ------------------------------------------------------------------

    def _extract_in_band_error(self, payload: Any) -> Optional[str]:
        """FMP frequently signals an error with HTTP 200 and a JSON body
        such as {"Error Message": "Invalid API KEY."} rather than a
        non-2xx status code -- this must be checked on every successful
        HTTP response, not only on HTTPError."""
        if isinstance(payload, dict):
            for key in ("Error Message", "error", "message"):
                value = payload.get(key)
                if value:
                    return str(value)
        return None

    def _classify_message(self, message: str) -> Type[ProviderCallError]:
        lowered = message.lower()
        if any(marker in lowered for marker in _INVALID_KEY_MESSAGE_MARKERS):
            return ProviderInvalidKeyError
        if any(marker in lowered for marker in _RATE_LIMIT_MESSAGE_MARKERS):
            return ProviderRateLimitedError
        return ProviderDownError

    def _classify_http_error(self, error: urllib.error.HTTPError) -> Tuple[Type[ProviderCallError], str]:
        code = error.code
        in_band_message = None
        try:
            body = error.read()
            if body:
                payload = json.loads(body.decode("utf-8"))
                in_band_message = self._extract_in_band_error(payload)
        except (ValueError, UnicodeDecodeError, OSError):
            in_band_message = None
        finally:
            error.close()

        message = in_band_message or f"FMP request failed with HTTP {code}"
        if code in (401, 403):
            return ProviderInvalidKeyError, message
        if code == 429:
            return ProviderRateLimitedError, message
        # 5xx (server error) and any other/unclassified status code
        # both fall to DOWN -- per API_MANAGER_ARCHITECTURE.md Section
        # 8, DOWN already covers "a failure other than rate limiting or
        # an invalid key (connection error, server error, unexpected
        # response)"; an unrecognized status is exactly an unexpected
        # response.
        return ProviderDownError, message

    def _classify_url_error(self, error: urllib.error.URLError) -> Tuple[Type[ProviderCallError], str]:
        reason = error.reason
        message = f"FMP request failed: {reason}"
        if isinstance(reason, TimeoutError) or "timed out" in str(reason).lower():
            return ProviderTimeoutError, message
        return ProviderDownError, message

    # ------------------------------------------------------------------
    # Response Parser
    # ------------------------------------------------------------------

    def _parse_response(self, operation: str, payload: Any) -> Dict[str, Any]:
        return {
            "provider": "Financial Modeling Prep (FMP)",
            "operation": operation,
            "payload": payload,
        }

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    def _log_attempt(
        self,
        url: str,
        attempt: int,
        status_code: Optional[int],
        response_time_ms: float,
        error_message: Optional[str],
    ) -> None:
        self._request_log.append(
            FMPRequestLogEntry(
                url=url,
                attempt=attempt,
                status_code=status_code,
                response_time_ms=response_time_ms,
                outcome="FAILURE" if error_message else "SUCCESS",
                error=error_message,
            )
        )

    # ------------------------------------------------------------------
    # Retry Logic
    # ------------------------------------------------------------------

    def _request(self, operation: str, parameters: Dict[str, Any]) -> ProviderResponse:
        api_key = self._resolve_api_key()
        if not api_key:
            raise ProviderInvalidKeyError(
                "FMP_API_KEY is not set in the environment; cannot authenticate with FMP."
            )

        url = self._build_url(operation, parameters, api_key)
        attempts_allowed = self.max_retries + 1
        last_retryable_error: Optional[ProviderCallError] = None

        for attempt in range(1, attempts_allowed + 1):
            started = time.monotonic()
            try:
                status_code, body = self._send_request(url)
            except urllib.error.HTTPError as error:
                elapsed_ms = (time.monotonic() - started) * 1000
                error_class, message = self._classify_http_error(error)
                self._log_attempt(url, attempt, error.code, elapsed_ms, message)
                if error_class in (ProviderInvalidKeyError, ProviderRateLimitedError):
                    raise error_class(message) from error
                last_retryable_error = error_class(message)
            except urllib.error.URLError as error:
                elapsed_ms = (time.monotonic() - started) * 1000
                error_class, message = self._classify_url_error(error)
                self._log_attempt(url, attempt, None, elapsed_ms, message)
                last_retryable_error = error_class(message)
            except TimeoutError as error:
                elapsed_ms = (time.monotonic() - started) * 1000
                message = f"FMP request timed out: {error}"
                self._log_attempt(url, attempt, None, elapsed_ms, message)
                last_retryable_error = ProviderTimeoutError(message)
            else:
                elapsed_ms = (time.monotonic() - started) * 1000
                outcome = self._handle_response(
                    operation, status_code, body, url, attempt, elapsed_ms
                )
                if isinstance(outcome, ProviderResponse):
                    return outcome
                last_retryable_error = outcome

            if attempt < attempts_allowed and self.retry_delay_seconds > 0:
                time.sleep(self.retry_delay_seconds)

        assert last_retryable_error is not None
        raise last_retryable_error

    def _handle_response(
        self,
        operation: str,
        status_code: int,
        body: bytes,
        url: str,
        attempt: int,
        elapsed_ms: float,
    ):
        """Returns a ProviderResponse on success, or a retryable
        ProviderCallError instance to record and possibly retry.
        Raises directly for a non-retryable in-band error (INVALID_KEY,
        RATE_LIMITED), exactly like _request()'s HTTPError branch."""
        try:
            payload = json.loads(body.decode("utf-8")) if body else []
        except (ValueError, UnicodeDecodeError) as error:
            message = f"FMP returned an unparseable response: {error}"
            self._log_attempt(url, attempt, status_code, elapsed_ms, message)
            return ProviderDownError(message)

        in_band_error = self._extract_in_band_error(payload)
        if in_band_error is not None:
            error_class = self._classify_message(in_band_error)
            message = f"FMP error: {in_band_error}"
            self._log_attempt(url, attempt, status_code, elapsed_ms, message)
            if error_class in (ProviderInvalidKeyError, ProviderRateLimitedError):
                raise error_class(message)
            return error_class(message)

        self._log_attempt(url, attempt, status_code, elapsed_ms, None)
        return ProviderResponse(
            data=self._parse_response(operation, payload), response_time_ms=elapsed_ms
        )
