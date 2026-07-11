"""Unit tests for research_engine.api_manager.providers.finnhub_provider.

Every HTTP interaction is mocked at the _send_request() seam -- no
test in this module ever performs a live internet call, per
Claude-Prompts/IMP_10G_Finnhub_Integration.md's Testing requirement.
"""

import io
import unittest
import urllib.error

from research_engine.api_manager.api_provider import ProviderName
from research_engine.api_manager.provider_interface import (
    ProviderDownError,
    ProviderInterface,
    ProviderInvalidKeyError,
    ProviderRateLimitedError,
    ProviderResponse,
    ProviderTimeoutError,
)
from research_engine.api_manager.providers.finnhub_provider import (
    FinnhubProvider,
    FinnhubRequestError,
)


def _provider(**overrides) -> FinnhubProvider:
    defaults = dict(api_key="test-key", max_retries=0, retry_delay_seconds=0.0)
    defaults.update(overrides)
    return FinnhubProvider(**defaults)


def _http_error(code: int, reason: str, body: bytes = b"") -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://example.invalid", code, reason, {}, io.BytesIO(body))


class FakeSendRequest:
    """A drop-in replacement for FinnhubProvider._send_request that
    returns a scripted sequence of results (or raises a scripted
    exception) and records every URL it was called with."""

    def __init__(self, *responses):
        self._responses = list(responses)
        self.calls = []

    def __call__(self, url: str):
        self.calls.append(url)
        outcome = self._responses.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


_PROFILE_BODY = b'{"ticker": "AAPL", "name": "Apple Inc", "marketCapitalization": 4600000.0}'
_PEERS_BODY = b'["AAPL", "DELL", "HPQ"]'
_NEWS_BODY = b'[{"headline": "Apple news", "url": "https://example.com/a", "datetime": 1783737970}]'


class TestInterfaceContract(unittest.TestCase):
    def test_is_a_provider_interface(self):
        self.assertIsInstance(FinnhubProvider(), ProviderInterface)

    def test_provider_name(self):
        self.assertEqual(FinnhubProvider().provider_name, ProviderName.FINNHUB)


class TestAPIAuthentication(unittest.TestCase):
    def test_missing_key_raises_invalid_key_before_any_network_call(self):
        provider = FinnhubProvider(env={})
        fake = FakeSendRequest()
        provider._send_request = fake

        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertEqual(fake.calls, [])

    def test_blank_key_is_treated_as_missing(self):
        provider = FinnhubProvider(env={"FINNHUB_API_KEY": ""})
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Company Profile", {"symbol": "AAPL"})

    def test_explicit_api_key_takes_precedence_over_env(self):
        provider = _provider(api_key="explicit-key", env={"FINNHUB_API_KEY": "env-key"})
        fake = FakeSendRequest((200, _PROFILE_BODY))
        provider._send_request = fake
        provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertIn("token=explicit-key", fake.calls[0])

    def test_key_resolved_from_injected_env_when_no_explicit_key(self):
        provider = FinnhubProvider(env={"FINNHUB_API_KEY": "from-env"}, max_retries=0)
        fake = FakeSendRequest((200, _PROFILE_BODY))
        provider._send_request = fake
        provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertIn("token=from-env", fake.calls[0])

    def test_key_is_never_hardcoded_anywhere_in_the_module(self):
        import pathlib

        source = (
            pathlib.Path(__file__).resolve().parents[2]
            / "research_engine"
            / "api_manager"
            / "providers"
            / "finnhub_provider.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('api_key = "', source)
        self.assertNotIn("api_key = '", source)


class TestRequestBuilder(unittest.TestCase):
    def test_company_profile_uses_the_profile2_endpoint(self):
        provider = _provider()
        fake = FakeSendRequest((200, _PROFILE_BODY))
        provider._send_request = fake
        provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertIn("/stock/profile2?", fake.calls[0])
        self.assertIn("symbol=AAPL", fake.calls[0])

    def test_financial_statements_uses_the_metric_endpoint_with_metric_all(self):
        provider = _provider()
        fake = FakeSendRequest((200, b'{"metric": {}}'))
        provider._send_request = fake
        provider.call("Financial Statements", {"symbol": "AAPL"})
        self.assertIn("/stock/metric?", fake.calls[0])
        self.assertIn("metric=all", fake.calls[0])

    def test_competitors_uses_the_peers_endpoint(self):
        provider = _provider()
        fake = FakeSendRequest((200, _PEERS_BODY))
        provider._send_request = fake
        provider.call("Competitors", {"symbol": "AAPL"})
        self.assertIn("/stock/peers?", fake.calls[0])

    def test_shareholding_uses_the_insider_transactions_endpoint(self):
        provider = _provider()
        fake = FakeSendRequest((200, b'{"data": []}'))
        provider._send_request = fake
        provider.call("Shareholding", {"symbol": "AAPL"})
        self.assertIn("/stock/insider-transactions?", fake.calls[0])

    def test_management_and_products_reuse_profile2(self):
        for operation in ("Management", "Products & Services"):
            provider = _provider()
            fake = FakeSendRequest((200, _PROFILE_BODY))
            provider._send_request = fake
            provider.call(operation, {"symbol": "AAPL"})
            self.assertIn("/stock/profile2?", fake.calls[0])

    def test_corporate_actions_and_orders_reuse_filings(self):
        for operation in ("Corporate Actions", "Orders & Contracts"):
            provider = _provider()
            fake = FakeSendRequest((200, b'[]'))
            provider._send_request = fake
            provider.call(operation, {"symbol": "AAPL"})
            self.assertIn("/stock/filings?", fake.calls[0])

    def test_company_news_uses_the_company_news_endpoint_with_default_date_range(self):
        provider = _provider()
        fake = FakeSendRequest((200, _NEWS_BODY))
        provider._send_request = fake
        provider.call("Company News", {"symbol": "AAPL"})
        self.assertIn("/company-news?", fake.calls[0])
        self.assertIn("from=", fake.calls[0])
        self.assertIn("to=", fake.calls[0])

    def test_company_news_accepts_query_parameter_like_market_news_collector_passes(self):
        """MarketNewsCollector passes {"query": research_topic}, not
        {"symbol": ...} -- Finnhub must accept either, since it answers
        with whatever parameters the Primary (NewsAPI) was given."""
        provider = _provider()
        fake = FakeSendRequest((200, _NEWS_BODY))
        provider._send_request = fake
        provider.call("Company News", {"query": "INFY"})
        self.assertIn("symbol=INFY", fake.calls[0])

    def test_sector_news_reuses_company_news_endpoint(self):
        provider = _provider()
        fake = FakeSendRequest((200, _NEWS_BODY))
        provider._send_request = fake
        provider.call("Sector News", {"query": "Banking"})
        self.assertIn("/company-news?", fake.calls[0])

    def test_market_news_uses_the_general_news_endpoint_with_default_category(self):
        provider = _provider()
        fake = FakeSendRequest((200, _NEWS_BODY))
        provider._send_request = fake
        provider.call("Market News", {})
        self.assertIn("/news?", fake.calls[0])
        self.assertIn("category=general", fake.calls[0])

    def test_breaking_news_reuses_the_general_news_endpoint(self):
        provider = _provider()
        fake = FakeSendRequest((200, _NEWS_BODY))
        provider._send_request = fake
        provider.call("Breaking News", {})
        self.assertIn("/news?", fake.calls[0])

    def test_missing_symbol_raises_request_error_before_any_call(self):
        provider = _provider()
        fake = FakeSendRequest()
        provider._send_request = fake
        with self.assertRaises(FinnhubRequestError):
            provider.call("Company Profile", {})
        self.assertEqual(fake.calls, [])

    def test_unsupported_operation_raises_request_error(self):
        provider = _provider()
        fake = FakeSendRequest()
        provider._send_request = fake
        with self.assertRaises(FinnhubRequestError):
            provider.call("Not A Real Operation", {"symbol": "AAPL"})
        self.assertEqual(fake.calls, [])

    def test_every_documented_operation_builds_a_url_without_error(self):
        operations = (
            "Company Profile",
            "Financial Statements",
            "Management",
            "Shareholding",
            "Competitors",
            "Products & Services",
            "Corporate Actions",
            "Orders & Contracts",
            "Company News",
            "Sector News",
        )
        for operation in operations:
            provider = _provider()
            fake = FakeSendRequest((200, b'{}'))
            provider._send_request = fake
            response = provider.call(operation, {"symbol": "AAPL"})
            self.assertIsInstance(response, ProviderResponse)
            self.assertIn("token=test-key", fake.calls[0])

        for operation in ("Market News", "Breaking News"):
            provider = _provider()
            fake = FakeSendRequest((200, b'[]'))
            provider._send_request = fake
            response = provider.call(operation, {})
            self.assertIsInstance(response, ProviderResponse)
            self.assertIn("token=test-key", fake.calls[0])


class TestSuccessfulResponseParsing(unittest.TestCase):
    def test_dict_payload_parses_into_normalized_response(self):
        provider = _provider()
        provider._send_request = FakeSendRequest((200, _PROFILE_BODY))
        response = provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertIsInstance(response, ProviderResponse)
        self.assertEqual(response.data["provider"], "Finnhub")
        self.assertEqual(response.data["endpoint"], "/stock/profile2")
        self.assertEqual(response.data["payload"]["ticker"], "AAPL")
        self.assertGreaterEqual(response.response_time_ms, 0.0)

    def test_array_payload_parses_into_normalized_response(self):
        provider = _provider()
        provider._send_request = FakeSendRequest((200, _PEERS_BODY))
        response = provider.call("Competitors", {"symbol": "AAPL"})
        self.assertEqual(response.data["payload"], ["AAPL", "DELL", "HPQ"])

    def test_empty_array_response_is_success_not_failure(self):
        provider = _provider()
        provider._send_request = FakeSendRequest((200, b'[]'))
        response = provider.call("Company News", {"symbol": "NOSUCHSYMBOL"})
        self.assertEqual(response.data["payload"], [])


class TestErrorClassification(unittest.TestCase):
    def test_http_401_raises_invalid_key_with_no_retry(self):
        provider = _provider(max_retries=2)
        fake = FakeSendRequest(_http_error(401, "Unauthorized", b'{"error":"Invalid API key"}'))
        provider._send_request = fake
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertEqual(len(fake.calls), 1)

    def test_http_403_raises_down_not_invalid_key(self):
        """Confirmed live: Finnhub's 403 means a plan-tier restriction
        on this specific endpoint, not a bad key -- see this module's
        own docstring."""
        provider = _provider(max_retries=0)
        fake = FakeSendRequest(
            _http_error(403, "Forbidden", b'{"error":"You don\'t have access to this resource."}')
        )
        provider._send_request = fake
        with self.assertRaises(ProviderDownError):
            provider.call("Company Profile", {"symbol": "AAPL"})

    def test_http_429_raises_rate_limited_with_no_retry(self):
        provider = _provider(max_retries=2)
        fake = FakeSendRequest(_http_error(429, "Too Many Requests"))
        provider._send_request = fake
        with self.assertRaises(ProviderRateLimitedError):
            provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertEqual(len(fake.calls), 1)

    def test_http_500_raises_down_after_exhausting_retries(self):
        provider = _provider(max_retries=2)
        fake = FakeSendRequest(
            _http_error(500, "Server Error"),
            _http_error(500, "Server Error"),
            _http_error(500, "Server Error"),
        )
        provider._send_request = fake
        with self.assertRaises(ProviderDownError):
            provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertEqual(len(fake.calls), 3)

    def test_retry_succeeds_on_a_later_attempt(self):
        provider = _provider(max_retries=2)
        fake = FakeSendRequest(
            _http_error(500, "Server Error"),
            (200, _PROFILE_BODY),
        )
        provider._send_request = fake
        response = provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertIsInstance(response, ProviderResponse)
        self.assertEqual(len(fake.calls), 2)

    def test_in_band_200_status_error_raises_down(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            (200, b'{"error": "something went generically wrong"}')
        )
        with self.assertRaises(ProviderDownError):
            provider.call("Company Profile", {"symbol": "AAPL"})

    def test_url_error_timeout_reason_raises_timeout(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            urllib.error.URLError(TimeoutError("timed out"))
        )
        with self.assertRaises(ProviderTimeoutError):
            provider.call("Company Profile", {"symbol": "AAPL"})

    def test_bare_timeout_error_raises_timeout(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(TimeoutError("timed out"))
        with self.assertRaises(ProviderTimeoutError):
            provider.call("Company Profile", {"symbol": "AAPL"})

    def test_url_error_connection_refused_raises_down(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            urllib.error.URLError(ConnectionRefusedError("refused"))
        )
        with self.assertRaises(ProviderDownError):
            provider.call("Company Profile", {"symbol": "AAPL"})

    def test_malformed_json_body_raises_down(self):
        provider = _provider()
        provider._send_request = FakeSendRequest((200, b"not json at all"))
        with self.assertRaises(ProviderDownError):
            provider.call("Company Profile", {"symbol": "AAPL"})


class TestConnectionValidation(unittest.TestCase):
    def test_health_check_operation_makes_a_company_profile_request(self):
        provider = _provider()
        fake = FakeSendRequest((200, _PROFILE_BODY))
        provider._send_request = fake
        response = provider.call("HealthCheck", {})
        self.assertIsInstance(response, ProviderResponse)
        self.assertIn("/stock/profile2?", fake.calls[0])
        self.assertIn("symbol=AAPL", fake.calls[0])

    def test_health_check_fails_the_same_way_a_normal_request_would(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(_http_error(401, "Unauthorized"))
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("HealthCheck", {})


class TestSimulateFailureShortCircuitsEverything(unittest.TestCase):
    def test_simulate_failure_skips_authentication_and_network_entirely(self):
        error = ProviderDownError("forced")
        provider = FinnhubProvider(simulate_failure=error, env={})
        fake = FakeSendRequest()
        provider._send_request = fake
        with self.assertRaises(ProviderDownError) as ctx:
            provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertIs(ctx.exception, error)
        self.assertEqual(fake.calls, [])


class TestRequestLog(unittest.TestCase):
    def test_successful_call_logs_one_entry(self):
        provider = _provider()
        provider._send_request = FakeSendRequest((200, _PROFILE_BODY))
        provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertEqual(len(provider.request_log), 1)
        self.assertEqual(provider.request_log[0].outcome, "SUCCESS")
        self.assertEqual(provider.request_log[0].status_code, 200)

    def test_api_key_is_never_stored_in_the_request_log(self):
        provider = _provider(api_key="super-secret-real-key")
        provider._send_request = FakeSendRequest((200, _PROFILE_BODY))
        provider.call("Company Profile", {"symbol": "AAPL"})
        logged_url = provider.request_log[0].url
        self.assertNotIn("super-secret-real-key", logged_url)
        self.assertIn("REDACTED", logged_url)

    def test_the_real_key_is_still_used_for_the_actual_network_call(self):
        provider = _provider(api_key="super-secret-real-key")
        fake = FakeSendRequest((200, _PROFILE_BODY))
        provider._send_request = fake
        provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertIn("token=super-secret-real-key", fake.calls[0])

    def test_each_retry_attempt_is_logged_separately(self):
        provider = _provider(max_retries=2)
        provider._send_request = FakeSendRequest(
            _http_error(500, "Server Error"),
            (200, _PROFILE_BODY),
        )
        provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertEqual(len(provider.request_log), 2)
        self.assertEqual(provider.request_log[0].outcome, "FAILURE")
        self.assertEqual(provider.request_log[1].outcome, "SUCCESS")


if __name__ == "__main__":
    unittest.main()
