"""Unit tests for research_engine.api_manager.providers.

All five adapters are now real, live-HTTP adapters -- FMP (IMP-10C),
Alpha Vantage (IMP-10D), Twelve Data (IMP-10E), NewsAPI (IMP-10F), and
Finnhub (IMP-10G). Their provider_name/interface-contract compliance is
still checked generically below, but each adapter's real
request/response/error behavior has its own dedicated suite
(test_fmp_provider.py, test_alpha_vantage_provider.py,
test_twelve_data_provider.py, test_newsapi_provider.py,
test_finnhub_provider.py), not here.
"""

import unittest

from research_engine.api_manager.api_provider import ProviderName
from research_engine.api_manager.provider_interface import (
    ProviderDownError,
    ProviderInterface,
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


class TestEachAdapterImplementsTheContract(unittest.TestCase):
    def test_every_adapter_is_a_provider_interface(self):
        for adapter_class, _ in ADAPTER_EXPECTATIONS:
            self.assertIsInstance(adapter_class(), ProviderInterface)

    def test_provider_name_matches_expectation(self):
        for adapter_class, expected_name in ADAPTER_EXPECTATIONS:
            self.assertEqual(adapter_class().provider_name, expected_name)


class TestLiveProvidersSimulateFailureBackwardCompatibility(unittest.TestCase):
    """FMPProvider, AlphaVantageProvider, TwelveDataProvider,
    NewsAPIProvider, and FinnhubProvider keep honoring simulate_failure
    exactly as the IMP-10B placeholder did -- see each module's own
    docstring and dedicated test file for its real (non-simulated)
    behavior."""

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

    def test_finnhub_simulate_failure_raises_exactly_that_instance(self):
        error = ProviderDownError("simulated outage")
        adapter = FinnhubProvider(simulate_failure=error)
        with self.assertRaises(ProviderDownError) as ctx:
            adapter.call("Company Profile", {})
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
