"""
Alpha Vantage Provider

Live Provider Interface adapter for Alpha Vantage -- Primary Provider
for Category 2 (Market & Technical), per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 2/5.8 and
Claude-Prompts/IMP_10D_Alpha_Vantage_Integration.md. Only Alpha Vantage
is implemented live in this phase -- FMP remains the IMP-10C live
adapter, and Finnhub, Twelve Data, and NewsAPI remain the IMP-10B
placeholders, all unchanged.

API Authentication: the Alpha Vantage API key is never hardcoded. It is
resolved from the environment's ALPHA_VANTAGE_API_KEY variable (the
single project .env file) via APISettings.resolve_key() on every call
-- not cached at construction, matching FMPProvider's own pattern
(research_engine/api_manager/providers/fmp_provider.py).

HTTP Client: uses only the Python standard library (urllib.request,
json) -- no external HTTP dependency. The one place a socket is ever
touched is _send_request(); every test in this repository replaces it,
so no test in this codebase ever makes a live internet call.

Response shape: confirmed live against the real Alpha Vantage API
during IMP-10D validation. Every numeric field arrives as a JSON
string (Alpha Vantage convention, not a parsing bug) and is converted
to float/int by this module. Errors are signaled in-band, inside a 200
OK JSON body, under one of three keys -- "Error Message" (bad
function/symbol/parameter), "Note" (legacy rate-limit wording), or
"Information" (current rate-limit and premium-endpoint wording) --
never via a distinct HTTP status in normal operation. A wrong API key
was observed, live, to NOT reliably trigger any of these three keys for
every function (GLOBAL_QUOTE returned real data even with a garbage
key) -- INVALID_KEY detection here is therefore message-content-based,
the same honest, non-assuming approach FMPProvider already takes,
never a hardcoded "this status code always means X" assumption.

`simulate_failure` is preserved from the IMP-10B placeholder contract
and still takes precedence over any real HTTP work when set, exactly
like FMPProvider -- this is what lets every IMP-10B test that exercises
Provider Selection Logic and the Failover Rules through
AlphaVantageProvider keep passing completely unmodified.
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

DEFAULT_BASE_URL = "https://www.alphavantage.co/query"

# Operation -> Alpha Vantage `function` query parameter, per
# IMP_10D_Alpha_Vantage_Integration.md's Supported Data list.
# GLOBAL_QUOTE, TIME_SERIES_DAILY, and RSI confirmed live against the
# real API during IMP-10D validation; WEEKLY/MONTHLY/INTRADAY and
# MACD/SMA/EMA follow the identical, consistently-documented Alpha
# Vantage response shape (Meta Data + one indicator/series key), not
# separately guessed. "Volume" has no standalone Alpha Vantage
# endpoint -- volume is already a field on every OHLC data point, so
# it reuses TIME_SERIES_DAILY. "Chart Dataset" is not an Alpha Vantage
# operation at all -- it is built locally from already-fetched OHLC
# data by the Historical Price Collector, exactly as the IMP-08G
# placeholder already did.
_OPERATION_FUNCTIONS: Dict[str, str] = {
    "Real-time Price": "GLOBAL_QUOTE",
    "Daily OHLC": "TIME_SERIES_DAILY",
    "Weekly OHLC": "TIME_SERIES_WEEKLY",
    "Monthly OHLC": "TIME_SERIES_MONTHLY",
    "Intraday OHLC": "TIME_SERIES_INTRADAY",
    "RSI": "RSI",
    "MACD": "MACD",
    "SMA": "SMA",
    "EMA": "EMA",
    "Volume": "TIME_SERIES_DAILY",
}

# Parameters each function requires beyond `symbol` and `apikey`, with
# sensible defaults a caller may override via the request's parameters
# dict. Confirmed live for RSI; SMA/EMA/MACD share RSI's documented
# parameter contract (interval, time_period, series_type) on Alpha
# Vantage's own API, MACD additionally accepting series_type only (no
# time_period).
_DEFAULT_EXTRA_PARAMS: Dict[str, Dict[str, str]] = {
    "TIME_SERIES_INTRADAY": {"interval": "60min"},
    "RSI": {"interval": "daily", "time_period": "14", "series_type": "close"},
    "SMA": {"interval": "daily", "time_period": "20", "series_type": "close"},
    "EMA": {"interval": "daily", "time_period": "20", "series_type": "close"},
    "MACD": {"interval": "daily", "series_type": "close"},
}

# The single data-series key each function's response body carries,
# alongside its "Meta Data" key -- confirmed live for GLOBAL_QUOTE
# ("Global Quote"), TIME_SERIES_DAILY ("Time Series (Daily)"), and RSI
# ("Technical Analysis: RSI"); the rest follow Alpha Vantage's own
# consistent per-function naming convention.
_RESULT_KEY_BY_FUNCTION: Dict[str, str] = {
    "GLOBAL_QUOTE": "Global Quote",
    "TIME_SERIES_DAILY": "Time Series (Daily)",
    "TIME_SERIES_WEEKLY": "Weekly Time Series",
    "TIME_SERIES_MONTHLY": "Monthly Time Series",
    "TIME_SERIES_INTRADAY": None,  # key includes the interval, e.g. "Time Series (60min)" -- resolved dynamically
    "RSI": "Technical Analysis: RSI",
    "MACD": "Technical Analysis: MACD",
    "SMA": "Technical Analysis: SMA",
    "EMA": "Technical Analysis: EMA",
}

_INVALID_KEY_MESSAGE_MARKERS = ("invalid api", "apikey")
_RATE_LIMIT_MESSAGE_MARKERS = (
    "rate limit",
    "frequency",
    "requests per day",
    "premium",
    "call frequency",
)

_HEALTH_CHECK_FUNCTION = "GLOBAL_QUOTE"
_HEALTH_CHECK_SYMBOL = "AAPL"


class AlphaVantageRequestError(Exception):
    """Raised for a malformed request -- an unsupported Operation, or a
    missing required `symbol` parameter -- before any network call is
    attempted. Distinct from ProviderCallError: this is a caller
    programming error, never a provider health signal, so APIManager
    never sees or maps it."""


@dataclass
class AlphaVantageRequestLogEntry:
    """One HTTP attempt this adapter instance made, kept in memory for
    inspection and testing -- mirrors FMPRequestLogEntry
    (fmp_provider.py). Never persisted, never read by APIManager
    itself."""

    url: str
    attempt: int
    status_code: Optional[int]
    response_time_ms: float
    outcome: str  # "SUCCESS" or "FAILURE"
    error: Optional[str] = None


class AlphaVantageProvider(ProviderInterface):
    """Live Provider Interface adapter for Alpha Vantage."""

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
        self.base_url = base_url
        self.timeout_seconds = (
            timeout_seconds if timeout_seconds is not None else self.settings.timeout_seconds
        )
        self.max_retries = max(0, max_retries)
        self.retry_delay_seconds = retry_delay_seconds
        self._env = env
        # IMP-10B placeholder compatibility -- see module docstring.
        self.simulate_failure = simulate_failure
        self._request_log: List[AlphaVantageRequestLogEntry] = []

    @property
    def provider_name(self) -> ProviderName:
        return ProviderName.ALPHA_VANTAGE

    @property
    def request_log(self) -> List[AlphaVantageRequestLogEntry]:
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
        """A lightweight real call (Real-time Price for a fixed, benign
        symbol) used to answer APIManager's manual Health Check
        (API_MANAGER_ARCHITECTURE.md Section 9), unchanged. Fails
        exactly like a normal request -- there is no separate
        connectivity error type."""
        return self._request("Real-time Price", {"symbol": _HEALTH_CHECK_SYMBOL})

    # ------------------------------------------------------------------
    # API Authentication
    # ------------------------------------------------------------------

    def _resolve_api_key(self) -> Optional[str]:
        if self._explicit_api_key:
            return self._explicit_api_key
        return self.settings.resolve_key(ProviderName.ALPHA_VANTAGE, self._env)

    # ------------------------------------------------------------------
    # Request Builder
    # ------------------------------------------------------------------

    def _function_for(self, operation: str) -> str:
        function = _OPERATION_FUNCTIONS.get(operation)
        if function is None:
            raise AlphaVantageRequestError(
                f"'{operation}' is not a supported Alpha Vantage operation; expected one of "
                f"{sorted(_OPERATION_FUNCTIONS)}."
            )
        return function

    def _build_url(self, operation: str, parameters: Dict[str, Any], api_key: str) -> str:
        function = self._function_for(operation)

        symbol = parameters.get("symbol")
        if not symbol:
            raise AlphaVantageRequestError(f"Operation '{operation}' requires a 'symbol' parameter.")

        query_params: Dict[str, Any] = {"function": function, "symbol": symbol}
        query_params.update(_DEFAULT_EXTRA_PARAMS.get(function, {}))
        for key, value in parameters.items():
            if key != "symbol":
                query_params[key] = value
        query_params["apikey"] = api_key

        query_string = urllib.parse.urlencode(query_params)
        return f"{self.base_url}?{query_string}"

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
        """Alpha Vantage signals essentially every error -- bad
        function, bad symbol, rate limit, premium-only endpoint -- as
        HTTP 200 with one of these three top-level keys, confirmed
        live during IMP-10D validation."""
        if isinstance(payload, dict):
            for key in ("Error Message", "Note", "Information"):
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

    def _classify_http_error(
        self, error: urllib.error.HTTPError
    ) -> Tuple[Type[ProviderCallError], str]:
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

        message = in_band_message or f"Alpha Vantage request failed with HTTP {code}"
        if code in (401, 403):
            return ProviderInvalidKeyError, message
        if code == 429:
            return ProviderRateLimitedError, message
        return ProviderDownError, message

    def _classify_url_error(
        self, error: urllib.error.URLError
    ) -> Tuple[Type[ProviderCallError], str]:
        reason = error.reason
        message = f"Alpha Vantage request failed: {reason}"
        if isinstance(reason, TimeoutError) or "timed out" in str(reason).lower():
            return ProviderTimeoutError, message
        return ProviderDownError, message

    # ------------------------------------------------------------------
    # Response Parser
    # ------------------------------------------------------------------

    def _series_key(self, function: str, payload: Dict[str, Any]) -> Optional[str]:
        """Resolve the data-series key for this function's response.
        TIME_SERIES_INTRADAY's key embeds the interval (e.g. "Time
        Series (60min)"), so it is found by scanning for the one key
        that is not "Meta Data", rather than hardcoded."""
        expected_key = _RESULT_KEY_BY_FUNCTION.get(function)
        if expected_key is not None:
            return expected_key
        for key in payload.keys():
            if key != "Meta Data":
                return key
        return None

    def _parse_response(self, operation: str, function: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        series_key = self._series_key(function, payload)
        series = payload.get(series_key) if series_key else None
        return {
            "provider": "Alpha Vantage",
            "operation": operation,
            "function": function,
            "meta": payload.get("Meta Data"),
            "series": series,
        }

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    @staticmethod
    def _redact_api_key(url: str) -> str:
        """Replace the `apikey` query parameter's value with a fixed
        redaction marker before a URL is ever stored or surfaced --
        mirrors FMPProvider._redact_api_key exactly. The real,
        unredacted `url` is used for the actual network call in
        _send_request(); only the logged copy is ever redacted."""
        parsed = urllib.parse.urlsplit(url)
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        redacted_pairs = [
            (key, "***REDACTED***" if key == "apikey" else value) for key, value in query_pairs
        ]
        redacted_query = urllib.parse.urlencode(redacted_pairs)
        return urllib.parse.urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, redacted_query, parsed.fragment)
        )

    @staticmethod
    def _redact_key_in_text(text: Optional[str], api_key: Optional[str]) -> Optional[str]:
        """Strip a literal API key value out of free-text error
        messages, not just URLs -- confirmed live during IMP-10E
        validation that Alpha Vantage's own rate-limit message echoes
        the caller's key back verbatim ("We have detected your API key
        as <key> and..."). Without this, that key would flow unredacted
        into error_message, into the ProviderCallError raised from it,
        and into api_health.last_error. Applied to every constructed
        message before it is ever logged or raised."""
        if not text or not api_key:
            return text
        return text.replace(api_key, "***REDACTED***")

    def _log_attempt(
        self,
        url: str,
        attempt: int,
        status_code: Optional[int],
        response_time_ms: float,
        error_message: Optional[str],
    ) -> None:
        self._request_log.append(
            AlphaVantageRequestLogEntry(
                url=self._redact_api_key(url),
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
                "ALPHA_VANTAGE_API_KEY is not set in the environment; cannot authenticate "
                "with Alpha Vantage."
            )

        function = self._function_for(operation)
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
                message = self._redact_key_in_text(message, api_key)
                self._log_attempt(url, attempt, error.code, elapsed_ms, message)
                if error_class in (ProviderInvalidKeyError, ProviderRateLimitedError):
                    raise error_class(message) from error
                last_retryable_error = error_class(message)
            except urllib.error.URLError as error:
                elapsed_ms = (time.monotonic() - started) * 1000
                error_class, message = self._classify_url_error(error)
                message = self._redact_key_in_text(message, api_key)
                self._log_attempt(url, attempt, None, elapsed_ms, message)
                last_retryable_error = error_class(message)
            except TimeoutError as error:
                elapsed_ms = (time.monotonic() - started) * 1000
                message = f"Alpha Vantage request timed out: {error}"
                message = self._redact_key_in_text(message, api_key)
                self._log_attempt(url, attempt, None, elapsed_ms, message)
                last_retryable_error = ProviderTimeoutError(message)
            else:
                elapsed_ms = (time.monotonic() - started) * 1000
                outcome = self._handle_response(
                    operation, function, status_code, body, url, attempt, elapsed_ms, api_key
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
        function: str,
        status_code: int,
        body: bytes,
        url: str,
        attempt: int,
        elapsed_ms: float,
        api_key: Optional[str] = None,
    ):
        """Returns a ProviderResponse on success, or a retryable
        ProviderCallError instance to record and possibly retry. Raises
        directly for a non-retryable in-band error (INVALID_KEY,
        RATE_LIMITED), exactly like _request()'s HTTPError branch.
        `api_key` is used only to redact any echo of it out of an
        in-band error message before that message is ever logged or
        raised -- confirmed necessary live, see _redact_key_in_text."""
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except (ValueError, UnicodeDecodeError) as error:
            message = f"Alpha Vantage returned an unparseable response: {error}"
            self._log_attempt(url, attempt, status_code, elapsed_ms, message)
            return ProviderDownError(message)

        in_band_error = self._extract_in_band_error(payload)
        if in_band_error is not None:
            error_class = self._classify_message(in_band_error)
            message = self._redact_key_in_text(f"Alpha Vantage error: {in_band_error}", api_key)
            self._log_attempt(url, attempt, status_code, elapsed_ms, message)
            if error_class in (ProviderInvalidKeyError, ProviderRateLimitedError):
                raise error_class(message)
            return error_class(message)

        self._log_attempt(url, attempt, status_code, elapsed_ms, None)
        return ProviderResponse(
            data=self._parse_response(operation, function, payload), response_time_ms=elapsed_ms
        )
