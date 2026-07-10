"""Unit tests for research_engine.api_manager.api_registry."""

import unittest

from research_engine.api_manager.api_provider import (
    DEFAULT_PROVIDER_REGISTRATIONS,
    APIProvider,
    Category,
    ProviderName,
    ProviderRole,
)
from research_engine.api_manager.api_registry import (
    APIRegistry,
    DuplicateRoleError,
    ProviderRoleNotFoundError,
)


class TestDefaultSeeding(unittest.TestCase):
    def test_seeds_six_rows_by_default(self):
        registry = APIRegistry()
        self.assertEqual(len(registry.all_providers()), 6)

    def test_get_primary_and_backup_match_finalized_architecture(self):
        registry = APIRegistry()
        self.assertEqual(
            registry.get_primary(Category.FUNDAMENTAL_DATA).provider_name, ProviderName.FMP
        )
        self.assertEqual(
            registry.get_backup(Category.FUNDAMENTAL_DATA).provider_name, ProviderName.FINNHUB
        )
        self.assertEqual(
            registry.get_primary(Category.MARKET_TECHNICAL).provider_name,
            ProviderName.ALPHA_VANTAGE,
        )
        self.assertEqual(
            registry.get_backup(Category.MARKET_TECHNICAL).provider_name,
            ProviderName.TWELVE_DATA,
        )
        self.assertEqual(registry.get_primary(Category.NEWS).provider_name, ProviderName.NEWSAPI)
        self.assertEqual(registry.get_backup(Category.NEWS).provider_name, ProviderName.FINNHUB)

    def test_categories_returns_all_three(self):
        registry = APIRegistry()
        self.assertEqual(set(registry.categories()), set(Category))

    def test_two_registries_do_not_share_provider_objects(self):
        registry_a = APIRegistry()
        registry_b = APIRegistry()
        registry_a.set_active(Category.FUNDAMENTAL_DATA, ProviderRole.PRIMARY, False)
        self.assertTrue(registry_b.get_primary(Category.FUNDAMENTAL_DATA).active)
        self.assertTrue(DEFAULT_PROVIDER_REGISTRATIONS[0].active)


class TestRegisterAndLookup(unittest.TestCase):
    def test_duplicate_role_registration_raises(self):
        registry = APIRegistry(providers=[])
        registry.register(
            APIProvider(ProviderName.FMP, Category.FUNDAMENTAL_DATA, ProviderRole.PRIMARY, "FMP_API_KEY")
        )
        with self.assertRaises(DuplicateRoleError):
            registry.register(
                APIProvider(
                    ProviderName.FINNHUB,
                    Category.FUNDAMENTAL_DATA,
                    ProviderRole.PRIMARY,
                    "FINNHUB_API_KEY",
                )
            )

    def test_lookup_of_unregistered_role_raises(self):
        registry = APIRegistry(providers=[])
        with self.assertRaises(ProviderRoleNotFoundError):
            registry.get_primary(Category.FUNDAMENTAL_DATA)


class TestSwapRoles(unittest.TestCase):
    def test_swap_exchanges_primary_and_backup(self):
        registry = APIRegistry()
        original_primary = registry.get_primary(Category.FUNDAMENTAL_DATA).provider_name
        original_backup = registry.get_backup(Category.FUNDAMENTAL_DATA).provider_name

        registry.swap_roles(Category.FUNDAMENTAL_DATA)

        self.assertEqual(registry.get_primary(Category.FUNDAMENTAL_DATA).provider_name, original_backup)
        self.assertEqual(registry.get_backup(Category.FUNDAMENTAL_DATA).provider_name, original_primary)

    def test_swap_only_affects_the_named_category(self):
        registry = APIRegistry()
        before = registry.get_primary(Category.NEWS).provider_name
        registry.swap_roles(Category.FUNDAMENTAL_DATA)
        self.assertEqual(registry.get_primary(Category.NEWS).provider_name, before)

    def test_swap_takes_effect_immediately_no_extra_call_needed(self):
        registry = APIRegistry()
        registry.swap_roles(Category.MARKET_TECHNICAL)
        self.assertEqual(
            registry.get_primary(Category.MARKET_TECHNICAL).provider_name,
            ProviderName.TWELVE_DATA,
        )


class TestSetActive(unittest.TestCase):
    def test_disable_and_enable_a_role(self):
        registry = APIRegistry()
        registry.set_active(Category.NEWS, ProviderRole.BACKUP, False)
        self.assertFalse(registry.get_backup(Category.NEWS).active)
        registry.set_active(Category.NEWS, ProviderRole.BACKUP, True)
        self.assertTrue(registry.get_backup(Category.NEWS).active)


class TestFindByName(unittest.TestCase):
    def test_finnhub_returns_its_two_rows(self):
        registry = APIRegistry()
        rows = registry.find_by_name(ProviderName.FINNHUB)
        self.assertEqual(len(rows), 2)
        self.assertEqual({row.category for row in rows}, {Category.FUNDAMENTAL_DATA, Category.NEWS})

    def test_fmp_returns_a_single_row(self):
        registry = APIRegistry()
        rows = registry.find_by_name(ProviderName.FMP)
        self.assertEqual(len(rows), 1)


if __name__ == "__main__":
    unittest.main()
