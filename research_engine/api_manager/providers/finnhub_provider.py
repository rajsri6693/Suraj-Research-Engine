"""
Finnhub Provider

Live Provider Interface adapter for Finnhub -- the single Backup
Provider for BOTH Category 1 (Fundamental Data, Primary FMP) and
Category 3 (News, Primary NewsAPI), per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 2/5.8 and
Claude-Prompts/IMP_10G_Finnhub_Integration.md. One adapter, one key,
two Category roles -- exactly as Section 2 requires; this module has
no notion of "which role" it is answering, only Operation and
Parameters, matching every other Provider Interface adapter. FMP,
Alpha Vantage, Twelve Data, and NewsAPI remain the IMP-10C/10D/10E/10F
live adapters, all unchanged.

API Authentication: the Finnhub API key is never hardcoded. It is
resolved from the environment's FINNHUB_API_KEY variable (the single
project .env file) via APISettings.resolve_key() on every call -- not
cached at construction, matching FMPProvider's/NewsAPIProvider's own
pattern. Finnhub accepts the key as the `token` query parameter,
confirmed live.

HTTP Client: uses only the Python standard library (urllib.request,
json) -- no external HTTP dependency. The one place a socket is ever
touched is _send_request(); every test in this repository replaces it,
so no test in this codebase ever makes a live internet call.

Endpoint Mapping: no Collector ever parses a Backup Provider's response
shape -- FinancialCollector/CompanyCollector/ManagementCollector/etc.
only branch on `provider_name == ProviderName.FMP` before attempting
any field mapping, and MarketNewsCollector only branches on
`provider_name == ProviderName.NEWSAPI`, per each collector's own
`_<primary>_record`/`_<primary>_article` gate (confirmed by reading
every Fundamental Data and News collector during IMP-10G). Finnhub's
job is therefore only to make a genuine, correctly authenticated call
to a real, officially documented Finnhub endpoint for every operation
the Primary it backs up might be given -- not to return data shaped for
any specific collector. Every mapping below was confirmed live against
the real Finnhub API on 2026-07-11 using this repository's own
configured key:

  - "Company Profile" / "Management" / "Products & Services" ->
    /stock/profile2 -- Finnhub's free tier has no distinct executives
    or products endpoint, so these reuse Company Profile, mirroring
    FMPProvider's own precedent of reusing "/profile" for "Products &
    Services".
  - "Financial Statements" -> /stock/metric (Basic Financials) -- the
    closest free-tier equivalent to a financial-statement summary.
  - "Shareholding" -> /stock/insider-transactions -- Finnhub's
    dedicated institutional-ownership endpoint (/stock/ownership)
    returned HTTP 403 ("You don't have access to this resource") on
    this plan, confirmed live; insider-transactions is a real,
    working, shareholding-adjacent free endpoint.
  - "Competitors" -> /stock/peers -- exact match.
  - "Corporate Actions" / "Orders & Contracts" -> /stock/filings (SEC
    Filings) -- Finnhub's dividend endpoints (/stock/dividend,
    /stock/dividend2) returned HTTP 403 on this plan, confirmed live,
    and no distinct "orders & contracts" endpoint exists; SEC filings
    is the closest working, corporate-actions-adjacent data, mirroring
    FMPProvider's own admitted "no direct analog" reuse for "Orders &
    Contracts".
  - "Company News" / "Sector News" -> /company-news -- Finnhub has no
    distinct sector-news endpoint; Company News is reused, requiring
    the `from`/`to` date range Finnhub itself requires (defaulted to
    the trailing 30 days when the caller does not supply one).
  - "Market News" / "Breaking News" -> /news (General News, `category`
    defaulting to "general") -- Finnhub's general news feed, an exact
    match for a broad market feed; no distinct "breaking" feed exists.

Error Classification: HTTP 401 ("Invalid API key", confirmed live) maps
to INVALID_KEY. HTTP 403 on Finnhub is deliberately NOT classified as
INVALID_KEY here, unlike FMPProvider's 401/403 pairing -- live
validation confirmed Finnhub's own 403 body ("You don't have access to
this resource") means a plan-tier restriction on that specific
endpoint, not a bad key (the same key authenticates every other mapped
endpoint successfully); per API_MANAGER_ARCHITECTURE.md Section 8,
INVALID_KEY is long-lived and only clears when the key itself is
corrected in .env, which would never resolve a 403 plan restriction, so
403 falls to DOWN instead, alongside 5xx and any other unclassified
status.

`simulate_failure` is preserved from the IMP-10B placeholder contract
and still takes precedence over any real HTTP work when set, exactly
like every other live adapter -- this is what lets every IMP-10B/10C/
10D/10E/10F test that exercises Provider Selection Logic and the
Failover Rules through FinnhubProvider keep passing completely
unmodified.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Mapping, Optional, Set, Tuple, Type

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

DEFAULT_BASE_URL = "https://finnhub.io/api/v1"

# Operation -> Finnhub endpoint path, per this module's own docstring.
# Covers every operation string any Fundamental Data or News collector
# passes through the API Manager today (research_engine/collectors/),
# plus the full News operation set from API_MANAGER_ARCHITECTURE.md
# Section 3 for completeness, mirroring TwelveDataProvider's own
# precedent of implementing every documented operation even when only a
# subset is wired to a collector.
_OPERATION_ENDPOINTS: Dict[str, str] = {
    # Fundamental Data -- Backup for FMP (Category 1)
    "Company Profile": "/stock/profile2",
    "Financial Statements": "/stock/metric",
    "Management": "/stock/profile2",
    "Shareholding": "/stock/insider-transactions",
    "Competitors": "/stock/peers",
    "Products & Services": "/stock/profile2",
    "Corporate Actions": "/stock/filings",
    "Orders & Contracts": "/stock/filings",
    # News -- Backup for NewsAPI (Category 3)
    "Company News": "/company-news",
    "Sector News": "/company-news",
    "Market News": "/news",
    "Breaking News": "/news",
}

# Every mapped endpoint except the general news feed takes `symbol` as
# a query parameter.
_SYMBOL_ENDPOINTS: Set[str] = {
    "/stock/profile2",
    "/stock/metric",
    "/stock/insider-transactions",
    "/stock/peers",
    "/stock/filings",
    "/company-news",
}

_DEFAULT_NEWS_LOOKBACK_DAYS = 30
_DEFAULT_NEWS_CATEGORY = "general"

_HEALTH_CHECK_OPERATION = "Company Profile"
_HEALTH_CHECK_SYMBOL = "AAPL"


class FinnhubRequestError(Exception):
    """Raised for a malformed request -- an unsupported Operation, or a
    missing required `symbol` parameter -- before any network call is
    attempted. Distinct from ProviderCallError: this is a caller
    programming error, never a provider health signal, so APIManager
    never sees or maps it."""


@dataclass
class FinnhubRequestLogEntry:
    """One HTTP attempt this adapter instance made, kept in memory for
    inspection and testing -- mirrors FMPRequestLogEntry /
    NewsAPIRequestLogEntry. Never persisted, never read by APIManager
    itself."""

    url: str
    attempt: int
    status_code: Optional[int]
    response_time_ms: float
    outcome: str  # "SUCCESS" or "FAILURE"
    error: Optional[str] = None


class FinnhubProvider(ProviderInterface):
    """Live Provider Interface adapter for Finnhub."""

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
        self._request_log: List[FinnhubRequestLogEntry] = []

    @property
    def provider_name(self) -> ProviderName:
        return ProviderName.FINNHUB

    @property
    def request_log(self) -> List[FinnhubRequestLogEntry]:
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
        (API_MANAGER_ARCHITECTURE.md Section 9), unchanged."""
        return self._request(_HEALTH_CHECK_OPERATION, {"symbol": _HEALTH_CHECK_SYMBOL})

    # ------------------------------------------------------------------
    # API Authentication
    # ------------------------------------------------------------------

    def _resolve_api_key(self) -> Optional[str]:
        if self._explicit_api_key:
            return self._explicit_api_key
        return self.settings.resolve_key(ProviderName.FINNHUB, self._env)

    # ------------------------------------------------------------------
    # Request Builder
    # ------------------------------------------------------------------

    def _endpoint_for(self, operation: str) -> str:
        endpoint = _OPERATION_ENDPOINTS.get(operation)
        if endpoint is None:
            raise FinnhubRequestError(
                f"'{operation}' is not a supported Finnhub operation; expected one of "
                f"{sorted(_OPERATION_ENDPOINTS)}."
            )
        return endpoint

    def _build_url(self, operation: str, parameters: Dict[str, Any], api_key: str) -> str:
        endpoint = self._endpoint_for(operation)
        query_params: Dict[str, Any] = {}

        if endpoint in _SYMBOL_ENDPOINTS:
            # Fundamental Data collectors pass `symbol`; MarketNewsCollector
            # passes `query` for the same News operations Finnhub answers
            # as Backup -- accept either, matching whichever the Primary
            # this operation belongs to was actually given.
            symbol = parameters.get("symbol") or parameters.get("query")
            if not symbol:
                raise FinnhubRequestError(f"Operation '{operation}' requires a 'symbol' parameter.")
            query_params["symbol"] = symbol

        if endpoint == "/stock/metric":
            query_params["metric"] = "all"

        if endpoint == "/company-news":
            today = datetime.now()
            default_from = (today - timedelta(days=_DEFAULT_NEWS_LOOKBACK_DAYS)).strftime("%Y-%m-%d")
            query_params["from"] = parameters.get("from_date") or default_from
            query_params["to"] = parameters.get("to_date") or today.strftime("%Y-%m-%d")

        if endpoint == "/news":
            query_params["category"] = parameters.get("category", _DEFAULT_NEWS_CATEGORY)

        query_params["token"] = api_key
        query_string = urllib.parse.urlencode(query_params)
        return f"{self.base_url}{endpoint}?{query_string}"

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
        """Finnhub's error shape is {"error": <str>}, confirmed live for
        both HTTP 401 and HTTP 403 -- checked here too as a defensive
        second signal for the rare case a 200 response ever carries one,
        matching the same defensive pattern TwelveDataProvider already
        uses."""
        if isinstance(payload, dict) and payload.get("error"):
            return str(payload["error"])
        return None

    def _classify_message(self, message: str) -> Type[ProviderCallError]:
        lowered = message.lower()
        if "invalid api key" in lowered:
            return ProviderInvalidKeyError
        if "limit" in lowered:
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

        message = in_band_message or f"Finnhub request failed with HTTP {code}"
        if code == 401:
            return ProviderInvalidKeyError, message
        if code == 429:
            return ProviderRateLimitedError, message
        # 403 (a plan-tier restriction on this specific endpoint, per
        # this module's own docstring -- never a bad key), 5xx, and any
        # other unclassified status all fall to DOWN, per
        # API_MANAGER_ARCHITECTURE.md Section 8's "unexpected response"
        # bucket.
        return ProviderDownError, message

    def _classify_url_error(
        self, error: urllib.error.URLError
    ) -> Tuple[Type[ProviderCallError], str]:
        reason = error.reason
        message = f"Finnhub request failed: {reason}"
        if isinstance(reason, TimeoutError) or "timed out" in str(reason).lower():
            return ProviderTimeoutError, message
        return ProviderDownError, message

    # ------------------------------------------------------------------
    # Response Parser
    # ------------------------------------------------------------------

    def _parse_response(self, operation: str, endpoint: str, payload: Any) -> Dict[str, Any]:
        return {
            "provider": "Finnhub",
            "operation": operation,
            "endpoint": endpoint,
            "payload": payload,
        }

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    @staticmethod
    def _redact_api_key(url: str) -> str:
        """Replace the `token` query parameter's value with a fixed
        redaction marker before a URL is ever stored or surfaced --
        mirrors FMPProvider._redact_api_key exactly. The real,
        unredacted `url` is used for the actual network call in
        _send_request(); only the logged copy is ever redacted."""
        parsed = urllib.parse.urlsplit(url)
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        redacted_pairs = [
            (key, "***REDACTED***" if key == "token" else value) for key, value in query_pairs
        ]
        redacted_query = urllib.parse.urlencode(redacted_pairs)
        return urllib.parse.urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, redacted_query, parsed.fragment)
        )

    @staticmethod
    def _redact_key_in_text(text: Optional[str], api_key: Optional[str]) -> Optional[str]:
        """Strip a literal API key value out of free-text error
        messages, not just URLs -- mirrors every other live adapter's
        own defensive redaction. Applied to every constructed message
        before it is ever logged or raised."""
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
            FinnhubRequestLogEntry(
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
                "FINNHUB_API_KEY is not set in the environment; cannot authenticate "
                "with Finnhub."
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
                message = f"Finnhub request timed out: {error}"
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
            message = f"Finnhub returned an unparseable response: {error}"
            self._log_attempt(url, attempt, status_code, elapsed_ms, message)
            return ProviderDownError(message)

        in_band_error = self._extract_in_band_error(payload)
        if in_band_error is not None:
            error_class = self._classify_message(in_band_error)
            message = self._redact_key_in_text(f"Finnhub error: {in_band_error}", api_key)
            self._log_attempt(url, attempt, status_code, elapsed_ms, message)
            if error_class in (ProviderInvalidKeyError, ProviderRateLimitedError):
                raise error_class(message)
            return error_class(message)

        self._log_attempt(url, attempt, status_code, elapsed_ms, None)
        return ProviderResponse(
            data=self._parse_response(operation, endpoint, payload), response_time_ms=elapsed_ms
        )
