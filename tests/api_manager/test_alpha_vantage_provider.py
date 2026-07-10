"""Unit tests for research_engine.api_manager.providers.alpha_vantage_provider.

Every HTTP interaction is mocked at the _send_request() seam -- no
test in this module ever performs a live internet call, per
Claude-Prompts/IMP_10D_Alpha_Vantage_Integration.md's Testing
requirement.
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
from research_engine.api_manager.providers.alpha_vantage_provider import (
    AlphaVantageProvider,
    AlphaVantageRequestError,
)


def _provider(**overrides) -> AlphaVantageProvider:
    defaults = dict(api_key="test-key", max_retries=0, retry_delay_seconds=0.0)
    defaults.update(overrides)
    return AlphaVantageProvider(**defaults)


def _http_error(code: int, reason: str, body: bytes = b"") -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://example.invalid", code, reason, {}, io.BytesIO(body))


class FakeSendRequest:
    """A drop-in replacement for AlphaVantageProvider._send_request that
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


class TestInterfaceContract(unittest.TestCase):
    def test_is_a_provider_interface(self):
        self.assertIsInstance(AlphaVantageProvider(), ProviderInterface)

    def test_provider_name(self):
        self.assertEqual(AlphaVantageProvider().provider_name, ProviderName.ALPHA_VANTAGE)


class TestAPIAuthentication(unittest.TestCase):
    def test_missing_key_raises_invalid_key_before_any_network_call(self):
        provider = AlphaVantageProvider(env={})
        fake = FakeSendRequest()
        provider._send_request = fake

        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Real-time Price", {"symbol": "AAPL"})
        self.assertEqual(fake.calls, [])

    def test_blank_key_is_treated_as_missing(self):
        provider = AlphaVantageProvider(env={"ALPHA_VANTAGE_API_KEY": ""})
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Real-time Price", {"symbol": "AAPL"})

    def test_explicit_api_key_takes_precedence_over_env(self):
        provider = _provider(api_key="explicit-key", env={"ALPHA_VANTAGE_API_KEY": "env-key"})
        fake = FakeSendRequest((200, b'{"Global Quote": {"05. price": "1.0"}}'))
        provider._send_request = fake
        provider.call("Real-time Price", {"symbol": "AAPL"})
        self.assertIn("apikey=explicit-key", fake.calls[0])

    def test_key_resolved_from_injected_env_when_no_explicit_key(self):
        provider = AlphaVantageProvider(env={"ALPHA_VANTAGE_API_KEY": "from-env"}, max_retries=0)
        fake = FakeSendRequest((200, b'{"Global Quote": {"05. price": "1.0"}}'))
        provider._send_request = fake
        provider.call("Real-time Price", {"symbol": "AAPL"})
        self.assertIn("apikey=from-env", fake.calls[0])

    def test_key_is_never_hardcoded_anywhere_in_the_module(self):
        import pathlib

        source = (
            pathlib.Path(__file__).resolve().parents[2]
            / "research_engine"
            / "api_manager"
            / "providers"
            / "alpha_vantage_provider.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('api_key = "', source)
        self.assertNotIn("api_key = '", source)


class TestRequestBuilder(unittest.TestCase):
    def test_symbol_and_function_are_sent_as_query_parameters(self):
        provider = _provider()
        fake = FakeSendRequest((200, b'{"Global Quote": {"05. price": "1.0"}}'))
        provider._send_request = fake
        provider.call("Real-time Price", {"symbol": "AAPL"})
        self.assertIn("function=GLOBAL_QUOTE", fake.calls[0])
        self.assertIn("symbol=AAPL", fake.calls[0])

    def test_missing_symbol_raises_request_error_before_any_call(self):
        provider = _provider()
        fake = FakeSendRequest()
        provider._send_request = fake
        with self.assertRaises(AlphaVantageRequestError):
            provider.call("Real-time Price", {})
        self.assertEqual(fake.calls, [])

    def test_unsupported_operation_raises_request_error(self):
        provider = _provider()
        fake = FakeSendRequest()
        provider._send_request = fake
        with self.assertRaises(AlphaVantageRequestError):
            provider.call("Not A Real Operation", {"symbol": "AAPL"})
        self.assertEqual(fake.calls, [])

    def test_every_documented_operation_builds_a_url_without_error(self):
        operations = (
            "Real-time Price",
            "Daily OHLC",
            "Weekly OHLC",
            "Monthly OHLC",
            "Intraday OHLC",
            "RSI",
            "MACD",
            "SMA",
            "EMA",
            "Volume",
        )
        for operation in operations:
            provider = _provider()
            fake = FakeSendRequest((200, b'{"Meta Data": {}, "Some Series": {}}'))
            provider._send_request = fake
            response = provider.call(operation, {"symbol": "AAPL"})
            self.assertIsInstance(response, ProviderResponse)
            self.assertIn("apikey=test-key", fake.calls[0])

    def test_rsi_uses_documented_default_parameters(self):
        provider = _provider()
        fake = FakeSendRequest((200, b'{"Meta Data": {}, "Technical Analysis: RSI": {}}'))
        provider._send_request = fake
        provider.call("RSI", {"symbol": "AAPL"})
        self.assertIn("interval=daily", fake.calls[0])
        self.assertIn("time_period=14", fake.calls[0])
        self.assertIn("series_type=close", fake.calls[0])

    def test_caller_supplied_parameters_override_defaults(self):
        provider = _provider()
        fake = FakeSendRequest((200, b'{"Meta Data": {}, "Technical Analysis: RSI": {}}'))
        provider._send_request = fake
        provider.call("RSI", {"symbol": "AAPL", "time_period": "9"})
        self.assertIn("time_period=9", fake.calls[0])

    def test_volume_reuses_the_daily_ohlc_function(self):
        provider = _provider()
        fake = FakeSendRequest((200, b'{"Meta Data": {}, "Time Series (Daily)": {}}'))
        provider._send_request = fake
        provider.call("Volume", {"symbol": "AAPL"})
        self.assertIn("function=TIME_SERIES_DAILY", fake.calls[0])


class TestSuccessfulResponseParsing(unittest.TestCase):
    def test_global_quote_parses_into_normalized_response(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            (200, b'{"Global Quote": {"01. symbol": "AAPL", "05. price": "316.22"}}')
        )
        response = provider.call("Real-time Price", {"symbol": "AAPL"})
        self.assertIsInstance(response, ProviderResponse)
        self.assertEqual(response.data["provider"], "Alpha Vantage")
        self.assertEqual(response.data["function"], "GLOBAL_QUOTE")
        self.assertEqual(response.data["series"]["05. price"], "316.22")
        self.assertGreaterEqual(response.response_time_ms, 0.0)

    def test_time_series_daily_parses_series_key(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            (
                200,
                b'{"Meta Data": {"2. Symbol": "AAPL"}, "Time Series (Daily)": '
                b'{"2026-07-09": {"1. open": "310.51", "4. close": "316.22"}}}',
            )
        )
        response = provider.call("Daily OHLC", {"symbol": "AAPL"})
        self.assertEqual(response.data["series"]["2026-07-09"]["4. close"], "316.22")

    def test_intraday_series_key_resolved_dynamically(self):
        """TIME_SERIES_INTRADAY's series key embeds the interval (e.g.
        "Time Series (60min)") -- resolved by scanning for the
        non-Meta-Data key, not hardcoded."""
        provider = _provider()
        provider._send_request = FakeSendRequest(
            (
                200,
                b'{"Meta Data": {}, "Time Series (60min)": '
                b'{"2026-07-09 15:00:00": {"4. close": "316.22"}}}',
            )
        )
        response = provider.call("Intraday OHLC", {"symbol": "AAPL"})
        self.assertEqual(
            response.data["series"]["2026-07-09 15:00:00"]["4. close"], "316.22"
        )

    def test_empty_series_response_is_success_not_failure(self):
        """An unrecognized symbol returns HTTP 200 with an empty
        series dict, e.g. {"Global Quote": {}} -- confirmed live
        against the real API during IMP-10D validation."""
        provider = _provider()
        provider._send_request = FakeSendRequest((200, b'{"Global Quote": {}}'))
        response = provider.call("Real-time Price", {"symbol": "UNKNOWN"})
        self.assertEqual(response.data["series"], {})


class TestErrorClassification(unittest.TestCase):
    def test_in_band_error_message_for_bad_function_raises_down(self):
        """Confirmed live: an unrecognized `function` value returns
        HTTP 200 with {"Error Message": "This API function (...) does
        not exist."} -- never a distinct HTTP status."""
        provider = _provider()
        provider._send_request = FakeSendRequest(
            (200, b'{"Error Message": "This API function (BOGUS) does not exist."}')
        )
        with self.assertRaises(ProviderDownError):
            provider.call("Real-time Price", {"symbol": "AAPL"})

    def test_in_band_information_rate_limit_message_raises_rate_limited(self):
        """Confirmed live: Alpha Vantage's current rate-limit wording
        arrives under the "Information" key, not "Error Message" or
        "Note"."""
        provider = _provider()
        provider._send_request = FakeSendRequest(
            (
                200,
                b'{"Information": "Thank you for using Alpha Vantage! Please consider '
                b'spreading out your free API requests more sparingly (1 request per '
                b'second). You may subscribe to any of the premium plans to lift the '
                b'free key rate limit (25 requests per day)."}',
            )
        )
        with self.assertRaises(ProviderRateLimitedError):
            provider.call("Real-time Price", {"symbol": "AAPL"})

    def test_in_band_note_rate_limit_message_raises_rate_limited(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            (200, b'{"Note": "Thank you for using Alpha Vantage! Our standard API call frequency is 5 calls per minute."}')
        )
        with self.assertRaises(ProviderRateLimitedError):
            provider.call("Real-time Price", {"symbol": "AAPL"})

    def test_in_band_invalid_key_message_raises_invalid_key(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            (200, b'{"Error Message": "the parameter apikey is invalid or missing."}')
        )
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Real-time Price", {"symbol": "AAPL"})

    def test_http_401_raises_invalid_key_with_no_retry(self):
        provider = _provider(max_retries=2)
        fake = FakeSendRequest(_http_error(401, "Unauthorized"))
        provider._send_request = fake
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Real-time Price", {"symbol": "AAPL"})
        self.assertEqual(len(fake.calls), 1)

    def test_http_429_raises_rate_limited_with_no_retry(self):
        provider = _provider(max_retries=2)
        fake = FakeSendRequest(_http_error(429, "Too Many Requests"))
        provider._send_request = fake
        with self.assertRaises(ProviderRateLimitedError):
            provider.call("Real-time Price", {"symbol": "AAPL"})
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
            provider.call("Real-time Price", {"symbol": "AAPL"})
        self.assertEqual(len(fake.calls), 3)

    def test_retry_succeeds_on_a_later_attempt(self):
        provider = _provider(max_retries=2)
        fake = FakeSendRequest(
            _http_error(500, "Server Error"),
            (200, b'{"Global Quote": {"05. price": "1.0"}}'),
        )
        provider._send_request = fake
        response = provider.call("Real-time Price", {"symbol": "AAPL"})
        self.assertIsInstance(response, ProviderResponse)
        self.assertEqual(len(fake.calls), 2)

    def test_url_error_timeout_reason_raises_timeout(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            urllib.error.URLError(TimeoutError("timed out"))
        )
        with self.assertRaises(ProviderTimeoutError):
            provider.call("Real-time Price", {"symbol": "AAPL"})

    def test_bare_timeout_error_raises_timeout(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(TimeoutError("timed out"))
        with self.assertRaises(ProviderTimeoutError):
            provider.call("Real-time Price", {"symbol": "AAPL"})

    def test_url_error_connection_refused_raises_down(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            urllib.error.URLError(ConnectionRefusedError("refused"))
        )
        with self.assertRaises(ProviderDownError):
            provider.call("Real-time Price", {"symbol": "AAPL"})

    def test_malformed_json_body_raises_down(self):
        provider = _provider()
        provider._send_request = FakeSendRequest((200, b"not json at all"))
        with self.assertRaises(ProviderDownError):
            provider.call("Real-time Price", {"symbol": "AAPL"})


class TestConnectionValidation(unittest.TestCase):
    def test_health_check_operation_makes_a_real_time_price_request(self):
        provider = _provider()
        fake = FakeSendRequest((200, b'{"Global Quote": {"05. price": "1.0"}}'))
        provider._send_request = fake
        response = provider.call("HealthCheck", {})
        self.assertIsInstance(response, ProviderResponse)
        self.assertIn("function=GLOBAL_QUOTE", fake.calls[0])
        self.assertIn("symbol=AAPL", fake.calls[0])

    def test_health_check_fails_the_same_way_a_normal_request_would(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(_http_error(401, "Unauthorized"))
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("HealthCheck", {})


class TestSimulateFailureShortCircuitsEverything(unittest.TestCase):
    def test_simulate_failure_skips_authentication_and_network_entirely(self):
        error = ProviderDownError("forced")
        provider = AlphaVantageProvider(simulate_failure=error, env={})
        fake = FakeSendRequest()
        provider._send_request = fake
        with self.assertRaises(ProviderDownError) as ctx:
            provider.call("Real-time Price", {"symbol": "AAPL"})
        self.assertIs(ctx.exception, error)
        self.assertEqual(fake.calls, [])


class TestRequestLog(unittest.TestCase):
    def test_successful_call_logs_one_entry(self):
        provider = _provider()
        provider._send_request = FakeSendRequest((200, b'{"Global Quote": {"05. price": "1.0"}}'))
        provider.call("Real-time Price", {"symbol": "AAPL"})
        self.assertEqual(len(provider.request_log), 1)
        self.assertEqual(provider.request_log[0].outcome, "SUCCESS")
        self.assertEqual(provider.request_log[0].status_code, 200)

    def test_api_key_is_never_stored_in_the_request_log(self):
        provider = _provider(api_key="super-secret-real-key")
        provider._send_request = FakeSendRequest((200, b'{"Global Quote": {"05. price": "1.0"}}'))
        provider.call("Real-time Price", {"symbol": "AAPL"})
        logged_url = provider.request_log[0].url
        self.assertNotIn("super-secret-real-key", logged_url)
        self.assertIn("REDACTED", logged_url)

    def test_the_real_key_is_still_used_for_the_actual_network_call(self):
        provider = _provider(api_key="super-secret-real-key")
        fake = FakeSendRequest((200, b'{"Global Quote": {"05. price": "1.0"}}'))
        provider._send_request = fake
        provider.call("Real-time Price", {"symbol": "AAPL"})
        self.assertIn("apikey=super-secret-real-key", fake.calls[0])

    def test_each_retry_attempt_is_logged_separately(self):
        provider = _provider(max_retries=2)
        provider._send_request = FakeSendRequest(
            _http_error(500, "Server Error"),
            (200, b'{"Global Quote": {"05. price": "1.0"}}'),
        )
        provider.call("Real-time Price", {"symbol": "AAPL"})
        self.assertEqual(len(provider.request_log), 2)
        self.assertEqual(provider.request_log[0].outcome, "FAILURE")
        self.assertEqual(provider.request_log[1].outcome, "SUCCESS")


if __name__ == "__main__":
    unittest.main()
