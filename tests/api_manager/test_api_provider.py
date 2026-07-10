"""Unit tests for research_engine.api_manager.api_provider."""

import unittest

from research_engine.api_manager.api_provider import (
    DEFAULT_PROVIDER_REGISTRATIONS,
    APIProvider,
    Category,
    ProviderName,
    ProviderRole,
    copy_default_registrations,
    provider_key,
)


class TestCategoryAndRoleEnums(unittest.TestCase):
    def test_exactly_three_categories(self):
        self.assertEqual(len(list(Category)), 3)

    def test_category_values_match_architecture(self):
        self.assertEqual(Category.FUNDAMENTAL_DATA.value, "Fundamental Data")
        self.assertEqual(Category.MARKET_TECHNICAL.value, "Market & Technical")
        self.assertEqual(Category.NEWS.value, "News")

    def test_exactly_two_roles(self):
        self.assertEqual(len(list(ProviderRole)), 2)

    def test_exactly_five_provider_names(self):
        self.assertEqual(len(list(ProviderName)), 5)


class TestDefaultProviderRegistrations(unittest.TestCase):
    def test_six_rows_for_five_providers(self):
        self.assertEqual(len(DEFAULT_PROVIDER_REGISTRATIONS), 6)

    def test_exactly_one_primary_and_one_backup_per_category(self):
        for category in Category:
            rows = [p for p in DEFAULT_PROVIDER_REGISTRATIONS if p.category == category]
            self.assertEqual(len(rows), 2)
            roles = {p.role for p in rows}
            self.assertEqual(roles, {ProviderRole.PRIMARY, ProviderRole.BACKUP})

    def test_finalized_category_mapping(self):
        mapping = {
            (p.category, p.role): p.provider_name for p in DEFAULT_PROVIDER_REGISTRATIONS
        }
        self.assertEqual(
            mapping[(Category.FUNDAMENTAL_DATA, ProviderRole.PRIMARY)], ProviderName.FMP
        )
        self.assertEqual(
            mapping[(Category.FUNDAMENTAL_DATA, ProviderRole.BACKUP)], ProviderName.FINNHUB
        )
        self.assertEqual(
            mapping[(Category.MARKET_TECHNICAL, ProviderRole.PRIMARY)],
            ProviderName.ALPHA_VANTAGE,
        )
        self.assertEqual(
            mapping[(Category.MARKET_TECHNICAL, ProviderRole.BACKUP)], ProviderName.TWELVE_DATA
        )
        self.assertEqual(mapping[(Category.NEWS, ProviderRole.PRIMARY)], ProviderName.NEWSAPI)
        self.assertEqual(mapping[(Category.NEWS, ProviderRole.BACKUP)], ProviderName.FINNHUB)

    def test_finnhub_appears_exactly_twice_always_as_backup(self):
        finnhub_rows = [
            p for p in DEFAULT_PROVIDER_REGISTRATIONS if p.provider_name == ProviderName.FINNHUB
        ]
        self.assertEqual(len(finnhub_rows), 2)
        self.assertTrue(all(row.role == ProviderRole.BACKUP for row in finnhub_rows))
        self.assertEqual({row.category for row in finnhub_rows}, {Category.FUNDAMENTAL_DATA, Category.NEWS})

    def test_finnhub_rows_share_the_same_key_env_var(self):
        finnhub_rows = [
            p for p in DEFAULT_PROVIDER_REGISTRATIONS if p.provider_name == ProviderName.FINNHUB
        ]
        self.assertEqual(finnhub_rows[0].key_env_var, finnhub_rows[1].key_env_var)
        self.assertEqual(finnhub_rows[0].key_env_var, "FINNHUB_API_KEY")

    def test_no_provider_is_ever_primary_more_than_once_except_by_design(self):
        primaries = [
            p.provider_name
            for p in DEFAULT_PROVIDER_REGISTRATIONS
            if p.role == ProviderRole.PRIMARY
        ]
        self.assertEqual(len(primaries), len(set(primaries)))

    def test_every_row_is_active_by_default(self):
        self.assertTrue(all(p.active for p in DEFAULT_PROVIDER_REGISTRATIONS))


class TestCopyDefaultRegistrations(unittest.TestCase):
    def test_returns_equal_but_independent_objects(self):
        copy_a = copy_default_registrations()
        copy_b = copy_default_registrations()
        self.assertEqual(copy_a, copy_b)
        for a, b in zip(copy_a, copy_b):
            self.assertIsNot(a, b)

    def test_mutating_a_copy_never_affects_the_module_level_defaults(self):
        mutated = copy_default_registrations()
        mutated[0].active = False
        mutated[0].role = ProviderRole.BACKUP
        self.assertTrue(DEFAULT_PROVIDER_REGISTRATIONS[0].active)
        self.assertEqual(DEFAULT_PROVIDER_REGISTRATIONS[0].role, ProviderRole.PRIMARY)

    def test_mutating_one_copy_never_affects_another_copy(self):
        copy_a = copy_default_registrations()
        copy_b = copy_default_registrations()
        copy_a[0].active = False
        self.assertTrue(copy_b[0].active)


class TestProviderKey(unittest.TestCase):
    def test_same_provider_same_category_same_key(self):
        self.assertEqual(
            provider_key(ProviderName.FMP, Category.FUNDAMENTAL_DATA),
            provider_key(ProviderName.FMP, Category.FUNDAMENTAL_DATA),
        )

    def test_finnhub_gets_independent_keys_per_category(self):
        key_fundamental = provider_key(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA)
        key_news = provider_key(ProviderName.FINNHUB, Category.NEWS)
        self.assertNotEqual(key_fundamental, key_news)

    def test_key_is_stable_regardless_of_role(self):
        # provider_key never takes a role -- it must stay the same across
        # a Manual Provider Switch's role swap (Section 8/9).
        provider_a = APIProvider(
            ProviderName.FMP, Category.FUNDAMENTAL_DATA, ProviderRole.PRIMARY, "FMP_API_KEY"
        )
        provider_b = APIProvider(
            ProviderName.FMP, Category.FUNDAMENTAL_DATA, ProviderRole.BACKUP, "FMP_API_KEY"
        )
        self.assertEqual(
            provider_key(provider_a.provider_name, provider_a.category),
            provider_key(provider_b.provider_name, provider_b.category),
        )


if __name__ == "__main__":
    unittest.main()
