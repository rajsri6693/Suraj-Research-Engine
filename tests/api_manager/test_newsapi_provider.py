"""Unit tests for research_engine.api_manager.providers.newsapi_provider.

Every HTTP interaction is mocked at the _send_request() seam -- no
test in this module ever performs a live internet call, per
Claude-Prompts/IMP_10F_NewsAPI_Integration.md's Testing requirement.
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
from research_engine.api_manager.providers.newsapi_provider import (
    NewsAPIProvider,
    NewsAPIRequestError,
)


def _provider(**overrides) -> NewsAPIProvider:
    defaults = dict(api_key="test-key", max_retries=0, retry_delay_seconds=0.0)
    defaults.update(overrides)
    return NewsAPIProvider(**defaults)


def _http_error(code: int, reason: str, body: bytes = b"") -> urllib.error.HTTPError:
    return urllib.error.HTTPError("https://example.invalid", code, reason, {}, io.BytesIO(body))


class FakeSendRequest:
    """A drop-in replacement for NewsAPIProvider._send_request that
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


_EMPTY_ARTICLES_BODY = b'{"status": "ok", "totalResults": 0, "articles": []}'


class TestInterfaceContract(unittest.TestCase):
    def test_is_a_provider_interface(self):
        self.assertIsInstance(NewsAPIProvider(), ProviderInterface)

    def test_provider_name(self):
        self.assertEqual(NewsAPIProvider().provider_name, ProviderName.NEWSAPI)


class TestAPIAuthentication(unittest.TestCase):
    def test_missing_key_raises_invalid_key_before_any_network_call(self):
        provider = NewsAPIProvider(env={})
        fake = FakeSendRequest()
        provider._send_request = fake

        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Company News", {"query": "Infosys"})
        self.assertEqual(fake.calls, [])

    def test_blank_key_is_treated_as_missing(self):
        provider = NewsAPIProvider(env={"NEWSAPI_API_KEY": ""})
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Company News", {"query": "Infosys"})

    def test_explicit_api_key_takes_precedence_over_env(self):
        provider = _provider(api_key="explicit-key", env={"NEWSAPI_API_KEY": "env-key"})
        fake = FakeSendRequest((200, _EMPTY_ARTICLES_BODY))
        provider._send_request = fake
        provider.call("Company News", {"query": "Infosys"})
        self.assertIn("apiKey=explicit-key", fake.calls[0])

    def test_key_resolved_from_injected_env_when_no_explicit_key(self):
        provider = NewsAPIProvider(env={"NEWSAPI_API_KEY": "from-env"}, max_retries=0)
        fake = FakeSendRequest((200, _EMPTY_ARTICLES_BODY))
        provider._send_request = fake
        provider.call("Company News", {"query": "Infosys"})
        self.assertIn("apiKey=from-env", fake.calls[0])

    def test_key_is_never_hardcoded_anywhere_in_the_module(self):
        import pathlib

        source = (
            pathlib.Path(__file__).resolve().parents[2]
            / "research_engine"
            / "api_manager"
            / "providers"
            / "newsapi_provider.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn('api_key = "', source)
        self.assertNotIn("api_key = '", source)


class TestRequestBuilder(unittest.TestCase):
    def test_company_news_uses_the_everything_endpoint(self):
        provider = _provider()
        fake = FakeSendRequest((200, _EMPTY_ARTICLES_BODY))
        provider._send_request = fake
        provider.call("Company News", {"query": "Infosys"})
        self.assertIn("/everything?", fake.calls[0])
        self.assertIn("q=Infosys", fake.calls[0])

    def test_sector_news_uses_the_everything_endpoint(self):
        provider = _provider()
        fake = FakeSendRequest((200, _EMPTY_ARTICLES_BODY))
        provider._send_request = fake
        provider.call("Sector News", {"query": "Banking sector"})
        self.assertIn("/everything?", fake.calls[0])

    def test_market_news_uses_the_top_headlines_endpoint(self):
        provider = _provider()
        fake = FakeSendRequest((200, _EMPTY_ARTICLES_BODY))
        provider._send_request = fake
        provider.call("Market News", {})
        self.assertIn("/top-headlines?", fake.calls[0])
        self.assertIn("country=in", fake.calls[0])
        self.assertIn("category=business", fake.calls[0])

    def test_breaking_news_uses_the_top_headlines_endpoint_with_no_default_category(self):
        provider = _provider()
        fake = FakeSendRequest((200, _EMPTY_ARTICLES_BODY))
        provider._send_request = fake
        provider.call("Breaking News", {})
        self.assertIn("/top-headlines?", fake.calls[0])
        self.assertNotIn("category=", fake.calls[0])

    def test_missing_query_raises_request_error_before_any_call_for_everything_operations(self):
        for operation in ("Company News", "Sector News"):
            provider = _provider()
            fake = FakeSendRequest()
            provider._send_request = fake
            with self.assertRaises(NewsAPIRequestError):
                provider.call(operation, {})
            self.assertEqual(fake.calls, [])

    def test_unsupported_operation_raises_request_error(self):
        provider = _provider()
        fake = FakeSendRequest()
        provider._send_request = fake
        with self.assertRaises(NewsAPIRequestError):
            provider.call("Not A Real Operation", {"query": "Infosys"})
        self.assertEqual(fake.calls, [])

    def test_caller_supplied_country_and_category_override_the_default(self):
        provider = _provider()
        fake = FakeSendRequest((200, _EMPTY_ARTICLES_BODY))
        provider._send_request = fake
        provider.call("Market News", {"country": "us", "category": "technology"})
        self.assertIn("country=us", fake.calls[0])
        self.assertIn("category=technology", fake.calls[0])

    def test_query_conversion_is_never_hardcoded(self):
        """Whatever string is passed as `query` reaches `q` unchanged --
        no ticker/company-name rewriting happens inside this module,
        per IMP-10F's 'Do not hardcode query conversion' rule."""
        provider = _provider()
        fake = FakeSendRequest((200, _EMPTY_ARTICLES_BODY))
        provider._send_request = fake
        provider.call("Company News", {"query": "NIFTY 50"})
        self.assertIn("q=NIFTY+50", fake.calls[0])


class TestSuccessfulResponseParsing(unittest.TestCase):
    def test_articles_parse_into_normalized_response(self):
        provider = _provider()
        body = (
            b'{"status": "ok", "totalResults": 1, "articles": ['
            b'{"source": {"id": null, "name": "Reuters"}, "title": "Infosys wins deal",'
            b' "description": "A summary.", "url": "https://example.com/a",'
            b' "publishedAt": "2026-07-10T09:00:00Z"}]}'
        )
        provider._send_request = FakeSendRequest((200, body))
        response = provider.call("Company News", {"query": "Infosys"})
        self.assertIsInstance(response, ProviderResponse)
        self.assertEqual(response.data["provider"], "NewsAPI")
        self.assertEqual(response.data["endpoint"], "everything")
        self.assertEqual(len(response.data["articles"]), 1)
        self.assertEqual(response.data["articles"][0]["title"], "Infosys wins deal")
        self.assertEqual(response.data["articles"][0]["publishedAt"], "2026-07-10T09:00:00Z")
        self.assertGreaterEqual(response.response_time_ms, 0.0)

    def test_empty_articles_response_is_success_not_failure(self):
        provider = _provider()
        provider._send_request = FakeSendRequest((200, _EMPTY_ARTICLES_BODY))
        response = provider.call("Company News", {"query": "NoSuchCompanyXYZ"})
        self.assertEqual(response.data["articles"], [])

    def test_duplicate_articles_within_one_response_are_removed(self):
        provider = _provider()
        body = (
            b'{"status": "ok", "totalResults": 3, "articles": ['
            b'{"title": "A", "url": "https://example.com/a", "publishedAt": "2026-07-10T09:00:00Z"},'
            b'{"title": "A (syndicated)", "url": "https://example.com/a", "publishedAt": "2026-07-10T09:05:00Z"},'
            b'{"title": "B", "url": "https://example.com/b", "publishedAt": "2026-07-10T10:00:00Z"}]}'
        )
        provider._send_request = FakeSendRequest((200, body))
        response = provider.call("Company News", {"query": "Infosys"})
        self.assertEqual(len(response.data["articles"]), 2)
        self.assertEqual(response.data["duplicates_removed"], 1)
        urls = [article["url"] for article in response.data["articles"]]
        self.assertEqual(urls, ["https://example.com/a", "https://example.com/b"])

    def test_duplicate_removal_falls_back_to_title_and_published_at_when_url_missing(self):
        provider = _provider()
        body = (
            b'{"status": "ok", "totalResults": 2, "articles": ['
            b'{"title": "A", "publishedAt": "2026-07-10T09:00:00Z"},'
            b'{"title": "A", "publishedAt": "2026-07-10T09:00:00Z"}]}'
        )
        provider._send_request = FakeSendRequest((200, body))
        response = provider.call("Company News", {"query": "Infosys"})
        self.assertEqual(len(response.data["articles"]), 1)
        self.assertEqual(response.data["duplicates_removed"], 1)

    def test_published_at_timestamp_is_preserved_exactly(self):
        provider = _provider()
        body = (
            b'{"status": "ok", "totalResults": 1, "articles": ['
            b'{"title": "A", "url": "https://example.com/a", '
            b'"publishedAt": "2026-07-09T23:45:12Z"}]}'
        )
        provider._send_request = FakeSendRequest((200, body))
        response = provider.call("Company News", {"query": "Infosys"})
        self.assertEqual(response.data["articles"][0]["publishedAt"], "2026-07-09T23:45:12Z")


class TestErrorClassification(unittest.TestCase):
    def test_http_401_raises_invalid_key_with_no_retry(self):
        provider = _provider(max_retries=2)
        fake = FakeSendRequest(
            _http_error(
                401,
                "Unauthorized",
                b'{"status":"error","code":"apiKeyInvalid","message":"Your API key is invalid."}',
            )
        )
        provider._send_request = fake
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Company News", {"query": "Infosys"})
        self.assertEqual(len(fake.calls), 1)

    def test_http_429_raises_rate_limited_with_no_retry(self):
        provider = _provider(max_retries=2)
        fake = FakeSendRequest(_http_error(429, "Too Many Requests"))
        provider._send_request = fake
        with self.assertRaises(ProviderRateLimitedError):
            provider.call("Company News", {"query": "Infosys"})
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
            provider.call("Company News", {"query": "Infosys"})
        self.assertEqual(len(fake.calls), 3)

    def test_http_400_raises_down(self):
        """A malformed/missing parameter is a genuine HTTP error status
        from NewsAPI -- classified DOWN, per API_MANAGER_ARCHITECTURE.md
        Section 8's 'unexpected response' bucket."""
        provider = _provider()
        fake = FakeSendRequest(
            _http_error(
                400,
                "Bad Request",
                b'{"status":"error","code":"parametersMissing","message":"Required parameters are missing."}',
            )
        )
        provider._send_request = fake
        with self.assertRaises(ProviderDownError):
            provider.call("Company News", {"query": "Infosys"})

    def test_retry_succeeds_on_a_later_attempt(self):
        provider = _provider(max_retries=2)
        fake = FakeSendRequest(
            _http_error(500, "Server Error"),
            (200, _EMPTY_ARTICLES_BODY),
        )
        provider._send_request = fake
        response = provider.call("Company News", {"query": "Infosys"})
        self.assertIsInstance(response, ProviderResponse)
        self.assertEqual(len(fake.calls), 2)

    def test_in_band_200_status_rate_limited_error_raises_rate_limited(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            (
                200,
                b'{"status":"error","code":"rateLimited","message":"You have exceeded your rate limit."}',
            )
        )
        with self.assertRaises(ProviderRateLimitedError):
            provider.call("Company News", {"query": "Infosys"})

    def test_in_band_200_status_invalid_key_error_raises_invalid_key(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            (
                200,
                b'{"status":"error","code":"apiKeyExhausted","message":"You have exhausted your daily quota."}',
            )
        )
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("Company News", {"query": "Infosys"})

    def test_url_error_timeout_reason_raises_timeout(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            urllib.error.URLError(TimeoutError("timed out"))
        )
        with self.assertRaises(ProviderTimeoutError):
            provider.call("Company News", {"query": "Infosys"})

    def test_bare_timeout_error_raises_timeout(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(TimeoutError("timed out"))
        with self.assertRaises(ProviderTimeoutError):
            provider.call("Company News", {"query": "Infosys"})

    def test_url_error_connection_refused_raises_down(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(
            urllib.error.URLError(ConnectionRefusedError("refused"))
        )
        with self.assertRaises(ProviderDownError):
            provider.call("Company News", {"query": "Infosys"})

    def test_malformed_json_body_raises_down(self):
        provider = _provider()
        provider._send_request = FakeSendRequest((200, b"not json at all"))
        with self.assertRaises(ProviderDownError):
            provider.call("Company News", {"query": "Infosys"})


class TestConnectionValidation(unittest.TestCase):
    def test_health_check_operation_makes_a_market_news_request(self):
        provider = _provider()
        fake = FakeSendRequest((200, _EMPTY_ARTICLES_BODY))
        provider._send_request = fake
        response = provider.call("HealthCheck", {})
        self.assertIsInstance(response, ProviderResponse)
        self.assertIn("/top-headlines?", fake.calls[0])
        self.assertIn("country=in", fake.calls[0])

    def test_health_check_fails_the_same_way_a_normal_request_would(self):
        provider = _provider()
        provider._send_request = FakeSendRequest(_http_error(401, "Unauthorized"))
        with self.assertRaises(ProviderInvalidKeyError):
            provider.call("HealthCheck", {})


class TestSimulateFailureShortCircuitsEverything(unittest.TestCase):
    def test_simulate_failure_skips_authentication_and_network_entirely(self):
        error = ProviderDownError("forced")
        provider = NewsAPIProvider(simulate_failure=error, env={})
        fake = FakeSendRequest()
        provider._send_request = fake
        with self.assertRaises(ProviderDownError) as ctx:
            provider.call("Company News", {"query": "Infosys"})
        self.assertIs(ctx.exception, error)
        self.assertEqual(fake.calls, [])


class TestRequestLog(unittest.TestCase):
    def test_successful_call_logs_one_entry(self):
        provider = _provider()
        provider._send_request = FakeSendRequest((200, _EMPTY_ARTICLES_BODY))
        provider.call("Company News", {"query": "Infosys"})
        self.assertEqual(len(provider.request_log), 1)
        self.assertEqual(provider.request_log[0].outcome, "SUCCESS")
        self.assertEqual(provider.request_log[0].status_code, 200)

    def test_api_key_is_never_stored_in_the_request_log(self):
        provider = _provider(api_key="super-secret-real-key")
        provider._send_request = FakeSendRequest((200, _EMPTY_ARTICLES_BODY))
        provider.call("Company News", {"query": "Infosys"})
        logged_url = provider.request_log[0].url
        self.assertNotIn("super-secret-real-key", logged_url)
        self.assertIn("REDACTED", logged_url)

    def test_the_real_key_is_still_used_for_the_actual_network_call(self):
        provider = _provider(api_key="super-secret-real-key")
        fake = FakeSendRequest((200, _EMPTY_ARTICLES_BODY))
        provider._send_request = fake
        provider.call("Company News", {"query": "Infosys"})
        self.assertIn("apiKey=super-secret-real-key", fake.calls[0])

    def test_each_retry_attempt_is_logged_separately(self):
        provider = _provider(max_retries=2)
        provider._send_request = FakeSendRequest(
            _http_error(500, "Server Error"),
            (200, _EMPTY_ARTICLES_BODY),
        )
        provider.call("Company News", {"query": "Infosys"})
        self.assertEqual(len(provider.request_log), 2)
        self.assertEqual(provider.request_log[0].outcome, "FAILURE")
        self.assertEqual(provider.request_log[1].outcome, "SUCCESS")


if __name__ == "__main__":
    unittest.main()
