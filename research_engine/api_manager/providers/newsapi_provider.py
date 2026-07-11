"""
NewsAPI Provider

Live Provider Interface adapter for NewsAPI -- Primary Provider for
Category 3 (News), per project_documentation/API_MANAGER_ARCHITECTURE.md
Section 2/5.8 and Claude-Prompts/IMP_10F_NewsAPI_Integration.md. Finnhub
remains the configured Backup Provider for this Category, unchanged and
still a placeholder. FMP, Alpha Vantage, and Twelve Data remain the
IMP-10C/10D/10E live adapters, all unchanged.

API Authentication: the NewsAPI key is never hardcoded. It is resolved
from the environment's NEWSAPI_API_KEY variable (the single project
.env file) via APISettings.resolve_key() on every call -- not cached at
construction, matching FMPProvider's/AlphaVantageProvider's/
TwelveDataProvider's own pattern.

HTTP Client: uses only the Python standard library (urllib.request,
json) -- no external HTTP dependency. The one place a socket is ever
touched is _send_request(); every test in this repository replaces it,
so no test in this codebase ever makes a live internet call.

Endpoints: NewsAPI documents exactly two endpoints this adapter uses,
per IMP-10F's officially-documented-endpoints-only rule --
`/v2/everything` (a full-text, historical article search, used for
Company News and Sector News, where a caller-supplied `query` is the
only reliable way to scope results to one company or sector) and
`/v2/top-headlines` (the live headlines feed, used for Market News and
Breaking News, scoped by `country`/`category` rather than free-text
search). Confirmed live during IMP-10F validation.

Query Formatting: this module never hardcodes a ticker-to-company-name
or symbol-to-query conversion table -- whatever string a caller passes
as `query` is sent to NewsAPI's `q` parameter unchanged. If a given
Research Topic needs different formatting to return results, that is
observed and reported during live validation, never silently rewritten
here.

Duplicate Removal: NewsAPI can return more than one entry for what is
effectively the same article (e.g. syndicated wire copy picked up by
several sources). `_deduplicate_articles()` removes duplicates within
one response only, keyed on the article's own `url` (falling back to
the (title, publishedAt) pair when `url` is missing) -- the first
occurrence in NewsAPI's own returned order is kept, every later repeat
is dropped. Original `publishedAt` values are never rewritten or
regenerated.

`simulate_failure` is preserved from the IMP-10B placeholder contract
and still takes precedence over any real HTTP work when set, exactly
like FMPProvider/AlphaVantageProvider/TwelveDataProvider -- this is
what lets every IMP-10B/10C/10D/10E test that exercises Provider
Selection Logic and the Failover Rules through NewsAPIProvider keep
passing completely unmodified.
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

DEFAULT_BASE_URL = "https://newsapi.org/v2"

# Operation -> NewsAPI endpoint path, per IMP_10F_NewsAPI_Integration.md's
# IMPLEMENT list -- only officially documented NewsAPI endpoints, both
# confirmed live during IMP-10F validation. Company News and Sector News
# both need a caller-supplied search term, so both use `everything`;
# Market News and Breaking News are both the live headlines feed, so
# both use `top-headlines`.
_OPERATION_ENDPOINTS: Dict[str, str] = {
    "Company News": "everything",
    "Sector News": "everything",
    "Market News": "top-headlines",
    "Breaking News": "top-headlines",
}

_EVERYTHING_OPERATIONS = ("Company News", "Sector News")
_TOP_HEADLINES_OPERATIONS = ("Market News", "Breaking News")

_DEFAULT_COUNTRY = "in"
_DEFAULT_CATEGORY_BY_OPERATION: Dict[str, str] = {
    "Market News": "business",
}
_DEFAULT_SORT_BY = "publishedAt"
_DEFAULT_PAGE_SIZE = 20

_RATE_LIMIT_ERROR_CODES = ("ratelimited",)
_INVALID_KEY_ERROR_CODES = ("apikeymissing", "apikeyinvalid", "apikeydisabled", "apikeyexhausted")

_HEALTH_CHECK_PARAMETERS: Dict[str, Any] = {"country": _DEFAULT_COUNTRY, "page_size": 1}


class NewsAPIRequestError(Exception):
    """Raised for a malformed request -- an unsupported Operation, or a
    missing required `query` parameter for an `everything`-backed
    Operation -- before any network call is attempted. Distinct from
    ProviderCallError: this is a caller programming error, never a
    provider health signal, so APIManager never sees or maps it."""


@dataclass
class NewsAPIRequestLogEntry:
    """One HTTP attempt this adapter instance made, kept in memory for
    inspection and testing -- mirrors TwelveDataRequestLogEntry /
    FMPRequestLogEntry / AlphaVantageRequestLogEntry. Never persisted,
    never read by APIManager itself."""

    url: str
    attempt: int
    status_code: Optional[int]
    response_time_ms: float
    outcome: str  # "SUCCESS" or "FAILURE"
    error: Optional[str] = None


class NewsAPIProvider(ProviderInterface):
    """Live Provider Interface adapter for NewsAPI."""

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
        self._request_log: List[NewsAPIRequestLogEntry] = []

    @property
    def provider_name(self) -> ProviderName:
        return ProviderName.NEWSAPI

    @property
    def request_log(self) -> List[NewsAPIRequestLogEntry]:
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
        """A lightweight real call (Market News for a fixed, benign
        country) used to answer APIManager's manual Health Check
        (API_MANAGER_ARCHITECTURE.md Section 9), unchanged."""
        return self._request("Market News", dict(_HEALTH_CHECK_PARAMETERS))

    # ------------------------------------------------------------------
    # API Authentication
    # ------------------------------------------------------------------

    def _resolve_api_key(self) -> Optional[str]:
        if self._explicit_api_key:
            return self._explicit_api_key
        return self.settings.resolve_key(ProviderName.NEWSAPI, self._env)

    # ------------------------------------------------------------------
    # Request Builder
    # ------------------------------------------------------------------

    def _endpoint_for(self, operation: str) -> str:
        endpoint = _OPERATION_ENDPOINTS.get(operation)
        if endpoint is None:
            raise NewsAPIRequestError(
                f"'{operation}' is not a supported NewsAPI operation; expected one of "
                f"{sorted(_OPERATION_ENDPOINTS)}."
            )
        return endpoint

    def _build_url(self, operation: str, parameters: Dict[str, Any], api_key: str) -> str:
        endpoint = self._endpoint_for(operation)
        query_params: Dict[str, Any] = {
            "pageSize": parameters.get("page_size", _DEFAULT_PAGE_SIZE)
        }

        if operation in _EVERYTHING_OPERATIONS:
            query = parameters.get("query") or parameters.get("symbol")
            if not query:
                raise NewsAPIRequestError(
                    f"Operation '{operation}' requires a 'query' parameter."
                )
            query_params["q"] = query
            query_params["sortBy"] = parameters.get("sort_by", _DEFAULT_SORT_BY)
            if parameters.get("language"):
                query_params["language"] = parameters["language"]
            if parameters.get("from_date"):
                query_params["from"] = parameters["from_date"]
            if parameters.get("to_date"):
                query_params["to"] = parameters["to_date"]
            if parameters.get("domains"):
                query_params["domains"] = parameters["domains"]
        else:
            query_params["country"] = parameters.get("country", _DEFAULT_COUNTRY)
            default_category = _DEFAULT_CATEGORY_BY_OPERATION.get(operation)
            category = parameters.get("category", default_category)
            if category:
                query_params["category"] = category
            if parameters.get("query"):
                query_params["q"] = parameters["query"]

        query_params["apiKey"] = api_key

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

    def _extract_in_band_error(self, payload: Any) -> Optional[Tuple[str, str]]:
        """NewsAPI's error shape is {"status": "error", "code": <str>,
        "message": <str>} -- returns (code, message), or None if this
        payload carries no in-band error."""
        if isinstance(payload, dict) and payload.get("status") == "error":
            code = str(payload.get("code") or "")
            message = str(payload.get("message") or "NewsAPI reported an error.")
            return code, message
        return None

    def _classify_code(self, code: str) -> Type[ProviderCallError]:
        lowered = code.lower()
        if lowered in _INVALID_KEY_ERROR_CODES:
            return ProviderInvalidKeyError
        if lowered in _RATE_LIMIT_ERROR_CODES:
            return ProviderRateLimitedError
        return ProviderDownError

    def _classify_http_error(
        self, error: urllib.error.HTTPError
    ) -> Tuple[Type[ProviderCallError], str]:
        code = error.code
        in_band = None
        try:
            body = error.read()
            if body:
                payload = json.loads(body.decode("utf-8"))
                in_band = self._extract_in_band_error(payload)
        except (ValueError, UnicodeDecodeError, OSError):
            in_band = None
        finally:
            error.close()

        message = in_band[1] if in_band else f"NewsAPI request failed with HTTP {code}"
        if code in (401, 403):
            return ProviderInvalidKeyError, message
        if code == 429:
            return ProviderRateLimitedError, message
        # 400 (bad/missing parameters), 5xx, and any other unclassified
        # status all fall to DOWN -- per API_MANAGER_ARCHITECTURE.md
        # Section 8, DOWN already covers "a failure other than rate
        # limiting or an invalid key... unexpected response."
        return ProviderDownError, message

    def _classify_url_error(
        self, error: urllib.error.URLError
    ) -> Tuple[Type[ProviderCallError], str]:
        reason = error.reason
        message = f"NewsAPI request failed: {reason}"
        if isinstance(reason, TimeoutError) or "timed out" in str(reason).lower():
            return ProviderTimeoutError, message
        return ProviderDownError, message

    # ------------------------------------------------------------------
    # Duplicate Removal
    # ------------------------------------------------------------------

    @staticmethod
    def _deduplicate_articles(articles: List[Any]) -> Tuple[List[Dict[str, Any]], int]:
        """Remove duplicate articles returned within the same response,
        keyed on the article's own `url` (falling back to the (title,
        publishedAt) pair when `url` is missing/blank). The first
        occurrence in NewsAPI's own returned order is kept; every
        original `publishedAt` value is passed through unmodified.
        Returns (deduplicated_articles, duplicates_removed_count)."""
        seen = set()
        deduped: List[Dict[str, Any]] = []
        duplicates_removed = 0
        for article in articles:
            if not isinstance(article, dict):
                continue
            key = article.get("url") or (article.get("title"), article.get("publishedAt"))
            if key in seen:
                duplicates_removed += 1
                continue
            seen.add(key)
            deduped.append(article)
        return deduped, duplicates_removed

    # ------------------------------------------------------------------
    # Response Parser
    # ------------------------------------------------------------------

    def _parse_response(self, operation: str, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        raw_articles = payload.get("articles")
        articles, duplicates_removed = self._deduplicate_articles(
            raw_articles if isinstance(raw_articles, list) else []
        )
        return {
            "provider": "NewsAPI",
            "operation": operation,
            "endpoint": endpoint,
            "total_results": payload.get("totalResults"),
            "articles": articles,
            "duplicates_removed": duplicates_removed,
        }

    # ------------------------------------------------------------------
    # Logging
    # ------------------------------------------------------------------

    @staticmethod
    def _redact_api_key(url: str) -> str:
        """Replace the `apiKey` query parameter's value with a fixed
        redaction marker before a URL is ever stored or surfaced --
        mirrors TwelveDataProvider._redact_api_key /
        FMPProvider._redact_api_key exactly. The real, unredacted `url`
        is used for the actual network call in _send_request(); only
        the logged copy is ever redacted."""
        parsed = urllib.parse.urlsplit(url)
        query_pairs = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        redacted_pairs = [
            (key, "***REDACTED***" if key == "apiKey" else value) for key, value in query_pairs
        ]
        redacted_query = urllib.parse.urlencode(redacted_pairs)
        return urllib.parse.urlunsplit(
            (parsed.scheme, parsed.netloc, parsed.path, redacted_query, parsed.fragment)
        )

    @staticmethod
    def _redact_key_in_text(text: Optional[str], api_key: Optional[str]) -> Optional[str]:
        """Strip a literal API key value out of free-text error
        messages, not just URLs -- mirrors TwelveDataProvider's own
        defensive redaction. Applied to every constructed message
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
            NewsAPIRequestLogEntry(
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
                "NEWSAPI_API_KEY is not set in the environment; cannot authenticate "
                "with NewsAPI."
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
                message = f"NewsAPI request timed out: {error}"
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
            message = f"NewsAPI returned an unparseable response: {error}"
            self._log_attempt(url, attempt, status_code, elapsed_ms, message)
            return ProviderDownError(message)

        in_band_error = self._extract_in_band_error(payload)
        if in_band_error is not None:
            code, in_band_message = in_band_error
            error_class = self._classify_code(code)
            message = self._redact_key_in_text(f"NewsAPI error: {in_band_message}", api_key)
            self._log_attempt(url, attempt, status_code, elapsed_ms, message)
            if error_class in (ProviderInvalidKeyError, ProviderRateLimitedError):
                raise error_class(message)
            return error_class(message)

        self._log_attempt(url, attempt, status_code, elapsed_ms, None)
        return ProviderResponse(
            data=self._parse_response(operation, endpoint, payload), response_time_ms=elapsed_ms
        )
