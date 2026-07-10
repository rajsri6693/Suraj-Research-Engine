"""
Twelve Data Provider

Live Provider Interface adapter for Twelve Data -- Backup Provider for
Category 2 (Market & Technical), per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 2/5.8 and
Claude-Prompts/IMP_10E_Twelve_Data_Integration.md. Alpha Vantage
remains the Primary Provider for this Category, unchanged. FMP and
Alpha Vantage remain the IMP-10C/IMP-10D live adapters; Finnhub and
NewsAPI remain the IMP-10B placeholders, all unchanged.

API Authentication: the Twelve Data API key is never hardcoded. It is
resolved from the environment's TWELVE_DATA_API_KEY variable (the
single project .env file) via APISettings.resolve_key() on every call
-- not cached at construction, matching FMPProvider's and
AlphaVantageProvider's own pattern.

HTTP Client: uses only the Python standard library (urllib.request,
json) -- no external HTTP dependency. The one place a socket is ever
touched is _send_request(); every test in this repository replaces it,
so no test in this codebase ever makes a live internet call.

Response shape: confirmed live against the real Twelve Data API during
IMP-10E validation. Unlike Alpha Vantage, Twelve Data signals errors
through ordinary HTTP status codes (401 for an invalid key, 404 for a
missing/invalid symbol, confirmed live) with a JSON body of the shape
{"code": <int>, "message": <str>, "status": "error"} -- this module
still checks the response body for an in-band error as a second
signal (Twelve Data's own documentation notes rate-limit responses can
arrive this way too), but classification here leans primarily on the
real HTTP status, unlike FMPProvider/AlphaVantageProvider.

`simulate_failure` is preserved from the IMP-10B placeholder contract
and still takes precedence over any real HTTP work when set, exactly
like FMPProvider/AlphaVantageProvider -- this is what lets every
IMP-10B/10C/10D test that exercises Provider Selection Logic and the
Failover Rules through TwelveDataProvider keep passing completely
unmodified.
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

DEFAULT_BASE_URL = "https://api.twelvedata.com"

# Operation -> Twelve Data endpoint path, per
# IMP_10E_Twelve_Data_Integration.md's Supported Data list -- only
# officially supported Twelve Data endpoints, all confirmed live
# during IMP-10E validation. "Volume" has no standalone Twelve Data
# endpoint -- volume is already a field on every OHLC data point, so
# it reuses "time_series", exactly as AlphaVantageProvider does.
# "Chart Dataset" is not a Twelve Data operation at all -- it is built
# locally from already-fetched OHLC data by the Historical Price
# Collector.
_OPERATION_ENDPOINTS: Dict[str, str] = {
    "Live Price": "price",
    "Daily OHLC": "time_series",
    "Weekly OHLC": "time_series",
    "Monthly OHLC": "time_series",
    "Intraday OHLC": "time_series",
    "RSI": "rsi",
    "SMA": "sma",
    "EMA": "ema",
    "Volume": "time_series",
}

# The `interval` query parameter each OHLC operation defaults to,
# overridable by the caller's own parameters.
_DEFAULT_INTERVAL_BY_OPERATION: Dict[str, str] = {
    "Daily OHLC": "1day",
    "Weekly OHLC": "1week",
    "Monthly OHLC": "1month",
    "Intraday OHLC": "1h",
    "Volume": "1day",
}

# RSI/SMA/EMA all default to a daily interval unless the caller
# overrides it, confirmed live.
_DEFAULT_INDICATOR_INTERVAL = "1day"

_RATE_LIMIT_MESSAGE_MARKERS = ("rate limit", "too many requests", "credits")

_HEALTH_CHECK_SYMBOL = "AAPL"


class TwelveDataRequestError(Exception):
    """Raised for a malformed request -- an unsupported Operation, or a
    missing required `symbol` parameter -- before any network call is
    attempted. Distinct from ProviderCallError: this is a caller
    programming error, never a provider health signal, so APIManager
    never sees or maps it."""


@dataclass
class TwelveDataRequestLogEntry:
    """One HTTP attempt this adapter instance made, kept in memory for
    inspection and testing -- mirrors FMPRequestLogEntry /
    AlphaVantageRequestLogEntry. Never persisted, never read by
    APIManager itself."""

    url: str
    attempt: int
    status_code: Optional[int]
    response_time_ms: float
    outcome: str  # "SUCCESS" or "FAILURE"
    error: Optional[str] = None


class TwelveDataProvider(ProviderInterface):
    """Live Provider Interface adapter for Twelve Data."""

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
        self._request_log: List[TwelveDataRequestLogEntry] = []

    @property
    def provider_name(self) -> ProviderName:
        return ProviderName.TWELVE_DATA

    @property
    def request_log(self) -> List[TwelveDataRequestLogEntry]:
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
        """A lightweight real call (Live Price for a fixed, benign
        symbol) used to answer APIManager's manual Health Check
        (API_MANAGER_ARCHITECTURE.md Section 9), unchanged."""
        return self._request("Live Price", {"symbol": _HEALTH_CHECK_SYMBOL})

    # ------------------------------------------------------------------
    # API Authentication
    # ------------------------------------------------------------------

    def _resolve_api_key(self) -> Optional[str]:
        if self._explicit_api_key:
            return self._explicit_api_key
        return self.settings.resolve_key(ProviderName.TWELVE_DATA, self._env)

    # ------------------------------------------------------------------
    # Request Builder
    # ------------------------------------------------------------------

    def _endpoint_for(self, operation: str) -> str:
        endpoint = _OPERATION_ENDPOINTS.get(operation)
        if endpoint is None:
            raise TwelveDataRequestError(
                f"'{operation}' is not a supported Twelve Data operation; expected one of "
                f"{sorted(_OPERATION_ENDPOINTS)}."
            )
        return endpoint

    def _build_url(self, operation: str, parameters: Dict[str, Any], api_key: str) -> str:
        endpoint = self._endpoint_for(operation)

        symbol = parameters.get("symbol")
        if not symbol:
            raise TwelveDataRequestError(f"Operation '{operation}' requires a 'symbol' parameter.")

        query_params: Dict[str, Any] = {"symbol": symbol}
        default_interval = _DEFAULT_INTERVAL_BY_OPERATION.get(
            operation, _DEFAULT_INDICATOR_INTERVAL if endpoint in ("rsi", "sma", "ema") else None
        )
        if default_interval is not None:
            query_params["interval"] = default_interval
        for key, value in parameters.items():
            if key != "symbol":
                query_params[key] = value
        query_params["apikey"] = api_key

        query_string = urllib.parse.urlencode(query_params)
        return f"{self.base_url}/{endpoint}?{query_string}"

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
        """Twelve Data's normal error shape is an HTTP status code plus
        {"code", "message", "status": "error"} -- checked here too as a
        second signal, since a 200-status rate-limit warning is
        documented to be possible on some Twelve Data plans."""
        if isinstance(payload, dict) and payload.get("status") == "error":
            return str(payload.get("message") or "Twelve Data reported an error.")
        return None

    def _classify_message(self, message: str) -> Type[ProviderCallError]:
        lowered = message.lower()
        if any(marker in lowered for marker in _RATE_LIMIT_MESSAGE_MARKERS):
            return ProviderRateLimitedError
        if "apikey" in lowered or "api key" in lowered:
            return ProviderInvalidKeyError
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

        message = in_band_message or f"Twelve Data request failed with HTTP {code}"
        if code in (401, 403):
            return ProviderInvalidKeyError, message
        if code == 429:
            return ProviderRateLimitedError, message
        # 404 (invalid/missing symbol per Twelve Data's own convention,
        # confirmed live), 5xx, and any other unclassified status all
        # fall to DOWN -- per API_MANAGER_ARCHITECTURE.md Section 8,
        # DOWN already covers "a failure other than rate limiting or an
        # invalid key... unexpected response."
        return ProviderDownError, message

    def _classify_url_error(
        self, error: urllib.error.URLError
    ) -> Tuple[Type[ProviderCallError], str]:
        reason = error.reason
        message = f"Twelve Data request failed: {reason}"
        if isinstance(reason, TimeoutError) or "timed out" in str(reason).lower():
            return ProviderTimeoutError, message
        return ProviderDownError, message

    # ------------------------------------------------------------------
    # Response Parser
    # ------------------------------------------------------------------

    def _parse_response(self, operation: str, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if endpoint == "price":
            series: Any = payload
        else:
            series = payload.get("values")
        return {
            "provider": "Twelve Data",
            "operation": operation,
            "endpoint": endpoint,
            "meta": payload.get("meta"),
            "series": series,
        }

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    @staticmethod
    def _redact_api_key(url: str) -> str:
        """Replace the `apikey` query parameter's value with a fixed
        redaction marker before a URL is ever stored or surfaced --
        mirrors FMPProvider._redact_api_key /
        AlphaVantageProvider._redact_api_key exactly. The real,
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
        messages, not just URLs. Added defensively per IMP-10E: live
        validation confirmed Alpha Vantage's own rate-limit message
        echoes the caller's key back verbatim, and Twelve Data shares
        this exact adapter architecture closely enough that the same
        class of leak is worth closing here too, even though no Twelve
        Data response observed live has done this. Applied to every
        constructed message before it is ever logged or raised."""
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
            TwelveDataRequestLogEntry(
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
                "TWELVE_DATA_API_KEY is not set in the environment; cannot authenticate "
                "with Twelve Data."
            )

        endpoint = self._endpoint_for(operation)
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
                message = f"Twelve Data request timed out: {error}"
                message = self._redact_key_in_text(message, api_key)
                self._log_attempt(url, attempt, None, elapsed_ms, message)
                last_retryable_error = ProviderTimeoutError(message)
            else:
                elapsed_ms = (time.monotonic() - started) * 1000
                outcome = self._handle_response(
                    operation, endpoint, status_code, body, url, attempt, elapsed_ms, api_key
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
        endpoint: str,
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
        raised."""
        try:
            payload = json.loads(body.decode("utf-8")) if body else {}
        except (ValueError, UnicodeDecodeError) as error:
            message = f"Twelve Data returned an unparseable response: {error}"
            self._log_attempt(url, attempt, status_code, elapsed_ms, message)
            return ProviderDownError(message)

        in_band_error = self._extract_in_band_error(payload)
        if in_band_error is not None:
            error_class = self._classify_message(in_band_error)
            message = self._redact_key_in_text(f"Twelve Data error: {in_band_error}", api_key)
            self._log_attempt(url, attempt, status_code, elapsed_ms, message)
            if error_class in (ProviderInvalidKeyError, ProviderRateLimitedError):
                raise error_class(message)
            return error_class(message)

        self._log_attempt(url, attempt, status_code, elapsed_ms, None)
        return ProviderResponse(
            data=self._parse_response(operation, endpoint, payload), response_time_ms=elapsed_ms
        )
