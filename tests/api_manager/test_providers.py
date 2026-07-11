"""Unit tests for research_engine.api_manager.providers.

One of the five adapters (Finnhub) remains the IMP-10B placeholder:
deterministic mock data, never raising unless `simulate_failure` is
set. FMP (IMP-10C), Alpha Vantage (IMP-10D), Twelve Data (IMP-10E), and
NewsAPI (IMP-10F) are now real, live-HTTP adapters -- their
provider_name/interface-contract compliance is still checked
generically below, but their real request/response/error behavior has
its own dedicated suite (test_fmp_provider.py,
test_alpha_vantage_provider.py, test_twelve_data_provider.py,
test_newsapi_provider.py), not here.
"""

import unittest

from research_engine.api_manager.api_provider import ProviderName
from research_engine.api_manager.provider_interface import (
    ProviderDownError,
    ProviderInterface,
    ProviderResponse,
)
from research_engine.api_manager.providers import (
    AlphaVantageProvider,
    FinnhubProvider,
    FMPProvider,
    NewsAPIProvider,
    TwelveDataProvider,
    default_placeholder_adapters,
)

ADAPTER_EXPECTATIONS = (
    (FMPProvider, ProviderName.FMP),
    (FinnhubProvider, ProviderName.FINNHUB),
    (AlphaVantageProvider, ProviderName.ALPHA_VANTAGE),
    (TwelveDataProvider, ProviderName.TWELVE_DATA),
    (NewsAPIProvider, ProviderName.NEWSAPI),
)

# The one adapter still implemented as an IMP-10B placeholder -- FMP,
# Alpha Vantage, Twelve Data, and NewsAPI are deliberately excluded,
# since none of the four returns placeholder data or stays
# exception-free without simulate_failure any more (see
# test_fmp_provider.py, test_alpha_vantage_provider.py,
# test_twelve_data_provider.py, test_newsapi_provider.py).
STILL_PLACEHOLDER_ADAPTERS = (
    (FinnhubProvider, ProviderName.FINNHUB),
)


class TestEachAdapterImplementsTheContract(unittest.TestCase):
    def test_every_adapter_is_a_provider_interface(self):
        for adapter_class, _ in ADAPTER_EXPECTATIONS:
            self.assertIsInstance(adapter_class(), ProviderInterface)

    def test_provider_name_matches_expectation(self):
        for adapter_class, expected_name in ADAPTER_EXPECTATIONS:
            self.assertEqual(adapter_class().provider_name, expected_name)


class TestStillPlaceholderAdapters(unittest.TestCase):
    """Finnhub -- unchanged from IMP-10B. FMP, Alpha Vantage, Twelve
    Data, and NewsAPI are intentionally not part of this suite."""

    def test_call_returns_a_provider_response_with_placeholder_data(self):
        for adapter_class, _ in STILL_PLACEHOLDER_ADAPTERS:
            adapter = adapter_class()
            response = adapter.call("Company Profile", {"symbol": "SMFG"})
            self.assertIsInstance(response, ProviderResponse)
            self.assertTrue(response.data["placeholder"])
            self.assertEqual(response.data["operation"], "Company Profile")
            self.assertEqual(response.data["parameters"], {"symbol": "SMFG"})
            self.assertGreaterEqual(response.response_time_ms, 0.0)

    def test_response_data_parameters_are_a_copy_not_a_reference(self):
        adapter = FinnhubProvider()
        parameters = {"symbol": "SMFG"}
        response = adapter.call("Company Profile", parameters)
        parameters["symbol"] = "CHANGED"
        self.assertEqual(response.data["parameters"], {"symbol": "SMFG"})

    def test_default_adapter_never_raises(self):
        for adapter_class, _ in STILL_PLACEHOLDER_ADAPTERS:
            adapter = adapter_class()
            try:
                adapter.call("Company Profile", {})
            except Exception as exc:  # pragma: no cover - failure path
                self.fail(f"{adapter_class.__name__} raised unexpectedly: {exc}")

    def test_simulate_failure_raises_exactly_that_instance(self):
        for adapter_class, _ in STILL_PLACEHOLDER_ADAPTERS:
            error = ProviderDownError("simulated outage")
            adapter = adapter_class(simulate_failure=error)
            with self.assertRaises(ProviderDownError) as ctx:
                adapter.call("Company Profile", {})
            self.assertIs(ctx.exception, error)


class TestLiveProvidersSimulateFailureBackwardCompatibility(unittest.TestCase):
    """FMPProvider, AlphaVantageProvider, TwelveDataProvider, and
    NewsAPIProvider keep honoring simulate_failure exactly as the
    IMP-10B placeholder did -- see each module's own docstring and
    dedicated test file for its real (non-simulated) behavior."""

    def test_fmp_simulate_failure_raises_exactly_that_instance(self):
        error = ProviderDownError("simulated outage")
        adapter = FMPProvider(simulate_failure=error)
        with self.assertRaises(ProviderDownError) as ctx:
            adapter.call("Company Profile", {})
        self.assertIs(ctx.exception, error)

    def test_alpha_vantage_simulate_failure_raises_exactly_that_instance(self):
        error = ProviderDownError("simulated outage")
        adapter = AlphaVantageProvider(simulate_failure=error)
        with self.assertRaises(ProviderDownError) as ctx:
            adapter.call("Real-time Price", {})
        self.assertIs(ctx.exception, error)

    def test_twelve_data_simulate_failure_raises_exactly_that_instance(self):
        error = ProviderDownError("simulated outage")
        adapter = TwelveDataProvider(simulate_failure=error)
        with self.assertRaises(ProviderDownError) as ctx:
            adapter.call("Live Price", {})
        self.assertIs(ctx.exception, error)

    def test_newsapi_simulate_failure_raises_exactly_that_instance(self):
        error = ProviderDownError("simulated outage")
        adapter = NewsAPIProvider(simulate_failure=error)
        with self.assertRaises(ProviderDownError) as ctx:
            adapter.call("Company News", {})
        self.assertIs(ctx.exception, error)


class TestDefaultPlaceholderAdapters(unittest.TestCase):
    def test_returns_all_five_providers(self):
        adapters = default_placeholder_adapters()
        self.assertEqual(set(adapters.keys()), set(ProviderName))

    def test_each_value_matches_its_key(self):
        adapters = default_placeholder_adapters()
        for name, adapter in adapters.items():
            self.assertEqual(adapter.provider_name, name)

    def test_two_calls_return_independent_adapter_instances(self):
        first = default_placeholder_adapters()
        second = default_placeholder_adapters()
        self.assertIsNot(first[ProviderName.FMP], second[ProviderName.FMP])


if __name__ == "__main__":
    unittest.main()
