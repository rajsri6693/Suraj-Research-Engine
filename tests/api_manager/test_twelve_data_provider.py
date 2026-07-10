"""Unit tests for research_engine.api_manager.providers.twelve_data_provider.

Every HTTP interaction is mocked at the _send_request() seam -- no
test in this module ever performs a live internet call, per
Claude-Prompts/IMP_10E_Twelve_Data_Integration.md's Testing
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
from research_engine.api_manager.providers.twelve_data_provider import (
    TwelveDataProvider,
    TwelveDataRequestError,
)


def _provider(**overrides) -> TwelveDataProvider:
    defaults = dict(api_key="test-key", max_retries=0, retry_delay_seconds=0.0)
    defaults.update(overrides)
    return TwelveDataProvider(**defaults)


def _http_error(code: int, reason: str, body: bytes = b"") -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://example.invalid", code, reason, {}, io.BytesIO(body))


class FakeSendRequest:
    """A drop-in replacement for TwelveDataProvider._send_request that
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
        self.assertIsInstance(TwelveDataProvider(), ProviderInterface)

    def test_provider_name(self):
        self.assertEqual(TwelveDataProvider().provider_name, ProviderName.TWELVE_DATA)


class TestAPIAuthentication(unittest.TestCase):
    def test_missing_key_raises_invalid_key_before_any_network_call(self):
        provider = TwelveDataProvider(env={})
        fake = FakeSendRequest()
        provider._send_request = fake

        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Live Price", {"symbol": "AAPL"})
        self.assertEqual(fake.calls, [])

    def test_blank_key_is_treated_as_missing(self):
        provider = TwelveDataProvider(env={"TWELVE_DATA_API_KEY": ""})
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Live Price", {"symbol": "AAPL"})

    def test_explicit_api_key_takes_precedence_over_env(self):
        provider = _provider(api_key="explicit-key", env={"TWELVE_DATA_API_KEY": "env-key"})
        fake = FakeSendRequest((200, b'{"price": "1.0"}'))
        provider._send_request = fake
        provider.call("Live Price", {"symbol": "AAPL"})
        self.assertIn("apikey=explicit-key", fake.calls[0])

    def test_key_resolved_from_injected_env_when_no_explicit_key(self):
        provider = TwelveDataProvider(env={"TWELVE_DATA_API_KEY": "from-env"}, max_retries=0)
        fake = FakeSendRequest((200, b'{"price": "1.0"}'))
        provider._send_request = fake
        provider.call("Live Price", {"symbol": "AAPL"})
        self.assertIn("apikey=from-env", fake.calls[0])

    def test_key_is_never_hardcoded_anywhere_in_the_module(self):
        import pathlib

        source = (
            pathlib.Path(__file__).resolve().parents[2]
            / "research_engine"
            / "api_manager"
            / "providers"
            / "twelve_data_provider.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('api_key = "', source)
        self.assertNotIn("api_key = '", source)


class TestRequestBuilder(unittest.TestCase):
    def test_price_endpoint_is_used_for_live_price(self):
        provider = _provider()
        fake = FakeSendRequest((200, b'{"price": "1.0"}'))
        provider._send_request = fake
        provider.call("Live Price", {"symbol": "AAPL"})
        self.assertIn("/price?", fake.calls[0])
        self.assertIn("symbol=AAPL", fake.calls[0])

    def test_missing_symbol_raises_request_error_before_any_call(self):
        provider = _provider()
        fake = FakeSendRequest()
        provider._send_request = fake
        with self.assertRaises(TwelveDataRequestError):
            provider.call("Live Price", {})
        self.assertEqual(fake.calls, [])

    def test_unsupported_operation_raises_request_error(self):
        provider = _provider()
        fake = FakeSendRequest()
        provider._send_request = fake
        with self.assertRaises(TwelveDataRequestError):
            provider.call("Not A Real Operation", {"symbol": "AAPL"})
        self.assertEqual(fake.calls, [])

    def test_every_documented_operation_builds_a_url_without_error(self):
        operations = (
            "Live Price",
            "Daily OHLC",
            "Weekly OHLC",
            "Monthly OHLC",
            "Intraday OHLC",
            "RSI",
            "SMA",
            "EMA",
            "Volume",
        )
        for operation in operations:
            provider = _provider()
            fake = FakeSendRequest((200, b'{"meta": {}, "values": []}'))
            provider._send_request = fake
            response = provider.call(operation, {"symbol": "AAPL"})
            self.assertIsInstance(response, ProviderResponse)
            self.assertIn("apikey=test-key", fake.calls[0])

    def test_daily_weekly_monthly_use_the_correct_interval(self):
        expectations = {
            "Daily OHLC": "interval=1day",
            "Weekly OHLC": "interval=1week",
            "Monthly OHLC": "interval=1month",
            "Intraday OHLC": "interval=1h",
        }
        for operation, expected_interval in expectations.items():
            provider = _provider()
            fake = FakeSendRequest((200, b'{"meta": {}, "values": []}'))
            provider._send_request = fake
            provider.call(operation, {"symbol": "AAPL"})
            self.assertIn(expected_interval, fake.calls[0])
            self.assertIn("/time_series?", fake.calls[0])

    def test_rsi_sma_ema_default_to_a_daily_interval(self):
        for operation, endpoint in (("RSI", "/rsi?"), ("SMA", "/sma?"), ("EMA", "/ema?")):
            provider = _provider()
            fake = FakeSendRequest((200, b'{"meta": {}, "values": []}'))
            provider._send_request = fake
            provider.call(operation, {"symbol": "AAPL"})
            self.assertIn(endpoint, fake.calls[0])
            self.assertIn("interval=1day", fake.calls[0])

    def test_caller_supplied_interval_overrides_the_default(self):
        provider = _provider()
        fake = FakeSendRequest((200, b'{"meta": {}, "values": []}'))
        provider._send_request = fake
        provider.call("RSI", {"symbol": "AAPL", "interval": "1week"})
        self.assertIn("interval=1week", fake.calls[0])

    def test_volume_reuses_the_time_series_endpoint(self):
        provider = _provider()
        fake = FakeSendRequest((200, b'{"meta": {}, "values": []}'))
        provider._send_request = fake
        provider.call("Volume", {"symbol": "AAPL"})
        self.assertIn("/time_series?", fake.calls[0])


class TestSuccessfulResponseParsing(unittest.TestCase):
    def test_price_parses_into_normalized_response(self):
        provider = _provider()
        provider._send_request = FakeSendRequest((200, b'{"price": "316.22"}'))
        response = provider.call("Live Price", {"symbol": "AAPL"})
        self.assertIsInstance(response, ProviderResponse)
        self.assertEqual(response.data["provider"], "Twelve Data")
        self.assertEqual(response.data["endpoint"], "price")
        self.assertEqual(response.data["series"]["price"], "316.22")
        self.assertGreaterEqual(response.response_time_ms, 0.0)

    def test_time_series_parses_values_list(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            (
                200,
                b'{"meta": {"symbol": "AAPL"}, "values": '
                b'[{"datetime": "2026-07-10", "close": "312.78"}]}',
            )
        )
        response = provider.call("Daily OHLC", {"symbol": "AAPL"})
        self.assertEqual(response.data["series"][0]["close"], "312.78")
        self.assertEqual(response.data["meta"]["symbol"], "AAPL")

    def test_empty_values_response_is_success_not_failure(self):
        """An unrecognized symbol still returns a proper HTTPError (404)
        for Twelve Data -- but an empty *values* list on an otherwise
        200 response (e.g. no data for a valid symbol/date range) is a
        legitimate success with no data, not a failure."""
        provider = _provider()
        provider._send_request = FakeSendRequest((200, b'{"meta": {}, "values": []}'))
        response = provider.call("Daily OHLC", {"symbol": "AAPL"})
        self.assertEqual(response.data["series"], [])


class TestErrorClassification(unittest.TestCase):
    def test_http_404_invalid_symbol_raises_down(self):
        """Confirmed live: Twelve Data returns HTTP 404 with
        {"code":404,"message":...,"status":"error"} for an invalid
        symbol -- unlike FMP/Alpha Vantage's graceful-empty-body
        approach, this is a genuine HTTP error status."""
        provider = _provider()
        provider._send_request = FakeSendRequest(
            _http_error(
                404,
                "Not Found",
                b'{"code":404,"message":"**symbol** parameter is missing or invalid.","status":"error"}',
            )
        )
        with self.assertRaises(ProviderDownError):
            provider.call("Live Price", {"symbol": "NOSUCHSYMBOL"})

    def test_http_401_raises_invalid_key_with_no_retry(self):
        """Confirmed live: Twelve Data returns HTTP 401 for an invalid
        API key."""
        provider = _provider(max_retries=2)
        fake = FakeSendRequest(
            _http_error(401, "Unauthorized", b'{"code":401,"message":"apikey is incorrect.","status":"error"}')
        )
        provider._send_request = fake
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Live Price", {"symbol": "AAPL"})
        self.assertEqual(len(fake.calls), 1)

    def test_http_429_raises_rate_limited_with_no_retry(self):
        provider = _provider(max_retries=2)
        fake = FakeSendRequest(_http_error(429, "Too Many Requests"))
        provider._send_request = fake
        with self.assertRaises(ProviderRateLimitedError):
            provider.call("Live Price", {"symbol": "AAPL"})
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
            provider.call("Live Price", {"symbol": "AAPL"})
        self.assertEqual(len(fake.calls), 3)

    def test_retry_succeeds_on_a_later_attempt(self):
        provider = _provider(max_retries=2)
        fake = FakeSendRequest(
            _http_error(500, "Server Error"),
            (200, b'{"price": "1.0"}'),
        )
        provider._send_request = fake
        response = provider.call("Live Price", {"symbol": "AAPL"})
        self.assertIsInstance(response, ProviderResponse)
        self.assertEqual(len(fake.calls), 2)

    def test_in_band_200_status_error_raises_rate_limited(self):
        """Twelve Data's docs note some plans surface rate-limit
        warnings as HTTP 200 with a {"status": "error"} body -- checked
        as a second signal alongside the primary HTTP-status path."""
        provider = _provider()
        provider._send_request = FakeSendRequest(
            (200, b'{"code":429,"message":"You have run out of API credits for this minute.","status":"error"}')
        )
        with self.assertRaises(ProviderRateLimitedError):
            provider.call("Live Price", {"symbol": "AAPL"})

    def test_url_error_timeout_reason_raises_timeout(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            urllib.error.URLError(TimeoutError("timed out"))
        )
        with self.assertRaises(ProviderTimeoutError):
            provider.call("Live Price", {"symbol": "AAPL"})

    def test_bare_timeout_error_raises_timeout(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(TimeoutError("timed out"))
        with self.assertRaises(ProviderTimeoutError):
            provider.call("Live Price", {"symbol": "AAPL"})

    def test_url_error_connection_refused_raises_down(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            urllib.error.URLError(ConnectionRefusedError("refused"))
        )
        with self.assertRaises(ProviderDownError):
            provider.call("Live Price", {"symbol": "AAPL"})

    def test_malformed_json_body_raises_down(self):
        provider = _provider()
        provider._send_request = FakeSendRequest((200, b"not json at all"))
        with self.assertRaises(ProviderDownError):
            provider.call("Live Price", {"symbol": "AAPL"})


class TestConnectionValidation(unittest.TestCase):
    def test_health_check_operation_makes_a_live_price_request(self):
        provider = _provider()
        fake = FakeSendRequest((200, b'{"price": "1.0"}'))
        provider._send_request = fake
        response = provider.call("HealthCheck", {})
        self.assertIsInstance(response, ProviderResponse)
        self.assertIn("/price?", fake.calls[0])
        self.assertIn("symbol=AAPL", fake.calls[0])

    def test_health_check_fails_the_same_way_a_normal_request_would(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(_http_error(401, "Unauthorized"))
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("HealthCheck", {})


class TestSimulateFailureShortCircuitsEverything(unittest.TestCase):
    def test_simulate_failure_skips_authentication_and_network_entirely(self):
        error = ProviderDownError("forced")
        provider = TwelveDataProvider(simulate_failure=error, env={})
        fake = FakeSendRequest()
        provider._send_request = fake
        with self.assertRaises(ProviderDownError) as ctx:
            provider.call("Live Price", {"symbol": "AAPL"})
        self.assertIs(ctx.exception, error)
        self.assertEqual(fake.calls, [])


class TestRequestLog(unittest.TestCase):
    def test_successful_call_logs_one_entry(self):
        provider = _provider()
        provider._send_request = FakeSendRequest((200, b'{"price": "1.0"}'))
        provider.call("Live Price", {"symbol": "AAPL"})
        self.assertEqual(len(provider.request_log), 1)
        self.assertEqual(provider.request_log[0].outcome, "SUCCESS")
        self.assertEqual(provider.request_log[0].status_code, 200)

    def test_api_key_is_never_stored_in_the_request_log(self):
        provider = _provider(api_key="super-secret-real-key")
        provider._send_request = FakeSendRequest((200, b'{"price": "1.0"}'))
        provider.call("Live Price", {"symbol": "AAPL"})
        logged_url = provider.request_log[0].url
        self.assertNotIn("super-secret-real-key", logged_url)
        self.assertIn("REDACTED", logged_url)

    def test_the_real_key_is_still_used_for_the_actual_network_call(self):
        provider = _provider(api_key="super-secret-real-key")
        fake = FakeSendRequest((200, b'{"price": "1.0"}'))
        provider._send_request = fake
        provider.call("Live Price", {"symbol": "AAPL"})
        self.assertIn("apikey=super-secret-real-key", fake.calls[0])

    def test_each_retry_attempt_is_logged_separately(self):
        provider = _provider(max_retries=2)
        provider._send_request = FakeSendRequest(
            _http_error(500, "Server Error"),
            (200, b'{"price": "1.0"}'),
        )
        provider.call("Live Price", {"symbol": "AAPL"})
        self.assertEqual(len(provider.request_log), 2)
        self.assertEqual(provider.request_log[0].outcome, "FAILURE")
        self.assertEqual(provider.request_log[1].outcome, "SUCCESS")


if __name__ == "__main__":
    unittest.main()
