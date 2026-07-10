"""Unit tests for research_engine.api_manager.providers.fmp_provider.

Every HTTP interaction is mocked at the _send_request() seam -- no
test in this module ever performs a live internet call, per
Claude-Prompts/IMP_10C_FMP_Integration.md's Testing requirement.
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
from research_engine.api_manager.providers.fmp_provider import (
    FMPProvider,
    FMPRequestError,
)


def _provider(**overrides) -> FMPProvider:
    defaults = dict(api_key="test-key", max_retries=0, retry_delay_seconds=0.0)
    defaults.update(overrides)
    return FMPProvider(**defaults)


def _http_error(code: int, reason: str, body: bytes = b"") -> urllib.error.HTTPError:
    """Build an HTTPError backed by a real (empty) file object rather
    than fp=None -- avoids a ResourceWarning from Python's own HTTPError
    implicitly allocating cleanup state for a None fp."""
    return urllib.error.HTTPError("https://example.invalid", code, reason, {}, io.BytesIO(body))


class FakeSendRequest:
    """A drop-in replacement for FMPProvider._send_request that returns
    a scripted sequence of results (or raises a scripted exception) and
    records every URL it was called with."""

    def __init__(self, *responses):
        self._responses = list(responses)
        self.calls = []

    def __call__(self, url: str):
        self.calls.append(url)
        outcome = self._responses.pop(0)
        if isinstance(outcome, BaseException):
            raise outcome
        return outcome


class TestInterfaceContract(unittest.TestCase):
    def test_is_a_provider_interface(self):
        self.assertIsInstance(FMPProvider(), ProviderInterface)

    def test_provider_name(self):
        self.assertEqual(FMPProvider().provider_name, ProviderName.FMP)


class TestAPIAuthentication(unittest.TestCase):
    def test_missing_key_raises_invalid_key_before_any_network_call(self):
        provider = FMPProvider(env={})
        fake = FakeSendRequest()
        provider._send_request = fake

        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertEqual(fake.calls, [])

    def test_blank_key_is_treated_as_missing(self):
        provider = FMPProvider(env={"FMP_API_KEY": ""})
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Company Profile", {"symbol": "AAPL"})

    def test_explicit_api_key_takes_precedence_over_env(self):
        provider = _provider(api_key="explicit-key", env={"FMP_API_KEY": "env-key"})
        fake = FakeSendRequest((200, b'{"symbol": "AAPL"}'))
        provider._send_request = fake
        provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertIn("apikey=explicit-key", fake.calls[0])

    def test_key_resolved_from_injected_env_when_no_explicit_key(self):
        provider = FMPProvider(env={"FMP_API_KEY": "from-env"}, max_retries=0)
        fake = FakeSendRequest((200, b'{"symbol": "AAPL"}'))
        provider._send_request = fake
        provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertIn("apikey=from-env", fake.calls[0])

    def test_key_is_never_hardcoded_anywhere_in_the_module(self):
        import pathlib

        source = (
            pathlib.Path(__file__).resolve().parents[2]
            / "research_engine"
            / "api_manager"
            / "providers"
            / "fmp_provider.py"
        ).read_text(encoding="utf-8")
        # No literal-looking API key assignment; the only "key" strings
        # are the env var name and query-parameter name.
        self.assertNotIn('api_key = "', source)
        self.assertNotIn("api_key = '", source)


class TestRequestBuilder(unittest.TestCase):
    def test_symbol_is_url_encoded_into_the_path(self):
        provider = _provider()
        fake = FakeSendRequest((200, b'{"symbol": "AAPL"}'))
        provider._send_request = fake
        provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertIn("/profile/AAPL", fake.calls[0])

    def test_missing_symbol_raises_fmp_request_error_before_any_call(self):
        provider = _provider()
        fake = FakeSendRequest()
        provider._send_request = fake
        with self.assertRaises(FMPRequestError):
            provider.call("Company Profile", {})
        self.assertEqual(fake.calls, [])

    def test_unsupported_operation_raises_fmp_request_error(self):
        provider = _provider()
        fake = FakeSendRequest()
        provider._send_request = fake
        with self.assertRaises(FMPRequestError):
            provider.call("Not A Real Operation", {"symbol": "AAPL"})
        self.assertEqual(fake.calls, [])

    def test_every_documented_operation_builds_a_url_without_error(self):
        operations = (
            "Company Profile",
            "Financial Statements",
            "Financial Ratios",
            "Earnings",
            "Dividend",
            "Stock Split",
            "Management",
            "Shareholding",
            "Competitors",
            "Products & Services",
            "Corporate Actions",
            "Orders & Contracts",
        )
        for operation in operations:
            provider = _provider()
            fake = FakeSendRequest((200, b"[]"))
            provider._send_request = fake
            response = provider.call(operation, {"symbol": "AAPL"})
            self.assertIsInstance(response, ProviderResponse)
            self.assertIn("apikey=test-key", fake.calls[0])

    def test_financial_statements_statement_type_selects_sub_endpoint(self):
        for statement_type, expected_segment in (
            ("income", "/income-statement/"),
            ("balance", "/balance-sheet-statement/"),
            ("cash", "/cash-flow-statement/"),
        ):
            provider = _provider()
            fake = FakeSendRequest((200, b"[]"))
            provider._send_request = fake
            provider.call(
                "Financial Statements", {"symbol": "AAPL", "statement_type": statement_type}
            )
            self.assertIn(expected_segment, fake.calls[0])

    def test_unknown_statement_type_raises(self):
        provider = _provider()
        provider._send_request = FakeSendRequest()
        with self.assertRaises(FMPRequestError):
            provider.call("Financial Statements", {"symbol": "AAPL", "statement_type": "bogus"})

    def test_competitors_operation_does_not_require_symbol_in_path(self):
        provider = _provider()
        fake = FakeSendRequest((200, b"[]"))
        provider._send_request = fake
        provider.call("Competitors", {"symbol": "AAPL"})
        self.assertIn("/stock-peers", fake.calls[0])
        self.assertIn("symbol=AAPL", fake.calls[0])

    def test_extra_parameters_are_appended_to_the_query_string(self):
        provider = _provider()
        fake = FakeSendRequest((200, b"[]"))
        provider._send_request = fake
        provider.call("Company Profile", {"symbol": "AAPL", "extra_param": "value"})
        self.assertIn("extra_param=value", fake.calls[0])


class TestSuccessfulResponseParsing(unittest.TestCase):
    def test_returns_a_normalized_provider_response(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            (200, b'[{"symbol": "AAPL", "companyName": "Apple Inc."}]')
        )
        response = provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertIsInstance(response, ProviderResponse)
        self.assertEqual(response.data["provider"], "Financial Modeling Prep (FMP)")
        self.assertEqual(response.data["operation"], "Company Profile")
        self.assertEqual(response.data["payload"][0]["symbol"], "AAPL")
        self.assertGreaterEqual(response.response_time_ms, 0.0)

    def test_empty_list_response_is_success_not_failure(self):
        provider = _provider()
        provider._send_request = FakeSendRequest((200, b"[]"))
        response = provider.call("Company Profile", {"symbol": "UNKNOWN"})
        self.assertEqual(response.data["payload"], [])


class TestErrorClassification(unittest.TestCase):
    def test_http_401_raises_invalid_key_with_no_retry(self):
        provider = _provider(max_retries=2)
        fake = FakeSendRequest(
            _http_error(401, "Unauthorized")
        )
        provider._send_request = fake
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertEqual(len(fake.calls), 1)

    def test_http_403_raises_invalid_key(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            _http_error(403, "Forbidden")
        )
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Company Profile", {"symbol": "AAPL"})

    def test_http_429_raises_rate_limited_with_no_retry(self):
        provider = _provider(max_retries=2)
        fake = FakeSendRequest(
            _http_error(429, "Too Many Requests")
        )
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
        self.assertEqual(len(fake.calls), 3)  # 1 initial + 2 retries

    def test_retry_succeeds_on_a_later_attempt(self):
        provider = _provider(max_retries=2)
        fake = FakeSendRequest(
            _http_error(500, "Server Error"),
            (200, b'{"symbol": "AAPL"}'),
        )
        provider._send_request = fake
        response = provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertIsInstance(response, ProviderResponse)
        self.assertEqual(len(fake.calls), 2)

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

    def test_in_band_invalid_key_error_message_raises_invalid_key(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            (200, b'{"Error Message": "Invalid API KEY."}')
        )
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Company Profile", {"symbol": "AAPL"})

    def test_in_band_rate_limit_message_raises_rate_limited(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            (200, b'{"Error Message": "Limit Reach. Please upgrade your plan."}')
        )
        with self.assertRaises(ProviderRateLimitedError):
            provider.call("Company Profile", {"symbol": "AAPL"})

    def test_in_band_unrecognized_error_message_raises_down(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            (200, b'{"Error Message": "Something went wrong."}')
        )
        with self.assertRaises(ProviderDownError):
            provider.call("Company Profile", {"symbol": "AAPL"})

    def test_unexpected_4xx_status_falls_back_to_down(self):
        provider = _provider(max_retries=1)
        fake = FakeSendRequest(
            _http_error(404, "Not Found"),
            _http_error(404, "Not Found"),
        )
        provider._send_request = fake
        with self.assertRaises(ProviderDownError):
            provider.call("Company Profile", {"symbol": "AAPL"})


class TestConnectionValidation(unittest.TestCase):
    def test_health_check_operation_makes_a_company_profile_request(self):
        provider = _provider()
        fake = FakeSendRequest((200, b'{"symbol": "AAPL"}'))
        provider._send_request = fake
        response = provider.call("HealthCheck", {})
        self.assertIsInstance(response, ProviderResponse)
        self.assertIn("/profile/AAPL", fake.calls[0])

    def test_health_check_fails_the_same_way_a_normal_request_would(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            _http_error(401, "Unauthorized")
        )
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("HealthCheck", {})


class TestSimulateFailureShortCircuitsEverything(unittest.TestCase):
    def test_simulate_failure_skips_authentication_and_network_entirely(self):
        error = ProviderDownError("forced")
        provider = FMPProvider(simulate_failure=error, env={})  # no key, would normally fail auth first
        fake = FakeSendRequest()
        provider._send_request = fake
        with self.assertRaises(ProviderDownError) as ctx:
            provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertIs(ctx.exception, error)
        self.assertEqual(fake.calls, [])


class TestRequestLog(unittest.TestCase):
    def test_successful_call_logs_one_entry(self):
        provider = _provider()
        provider._send_request = FakeSendRequest((200, b'{"symbol": "AAPL"}'))
        provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertEqual(len(provider.request_log), 1)
        self.assertEqual(provider.request_log[0].outcome, "SUCCESS")
        self.assertEqual(provider.request_log[0].status_code, 200)

    def test_each_retry_attempt_is_logged_separately(self):
        provider = _provider(max_retries=2)
        provider._send_request = FakeSendRequest(
            _http_error(500, "Server Error"),
            (200, b'{"symbol": "AAPL"}'),
        )
        provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertEqual(len(provider.request_log), 2)
        self.assertEqual(provider.request_log[0].outcome, "FAILURE")
        self.assertEqual(provider.request_log[0].attempt, 1)
        self.assertEqual(provider.request_log[1].outcome, "SUCCESS")
        self.assertEqual(provider.request_log[1].attempt, 2)

    def test_request_log_returns_a_copy(self):
        provider = _provider()
        provider._send_request = FakeSendRequest((200, b"[]"))
        provider.call("Company Profile", {"symbol": "AAPL"})
        log = provider.request_log
        log.clear()
        self.assertEqual(len(provider.request_log), 1)

    def test_non_retryable_failures_are_still_logged(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            _http_error(401, "Unauthorized")
        )
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Company Profile", {"symbol": "AAPL"})
        self.assertEqual(len(provider.request_log), 1)
        self.assertEqual(provider.request_log[0].outcome, "FAILURE")


if __name__ == "__main__":
    unittest.main()
