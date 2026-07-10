"""Unit tests for research_engine.api_manager.api_settings."""

import os
import tempfile
import unittest

from research_engine.api_manager.api_provider import ProviderName
from research_engine.api_manager.api_settings import (
    DEFAULT_KEY_ENV_VARS,
    APISettings,
    load_env_file,
)


class TestAPISettingsDefaults(unittest.TestCase):
    def test_defaults_are_sane(self):
        settings = APISettings()
        self.assertGreater(settings.timeout_seconds, 0)
        self.assertGreaterEqual(settings.retry_count, 0)
        self.assertGreater(settings.cool_down_seconds, 0)
        self.assertGreater(settings.invalid_key_cool_down_seconds, settings.cool_down_seconds)
        self.assertFalse(settings.restart_required_for_registry_changes)

    def test_default_key_env_vars_cover_all_five_providers(self):
        settings = APISettings()
        self.assertEqual(set(settings.provider_key_env_vars.keys()), set(ProviderName))

    def test_default_key_env_var_names_match_env_example_style(self):
        self.assertEqual(DEFAULT_KEY_ENV_VARS[ProviderName.FMP], "FMP_API_KEY")
        self.assertEqual(DEFAULT_KEY_ENV_VARS[ProviderName.FINNHUB], "FINNHUB_API_KEY")
        self.assertEqual(DEFAULT_KEY_ENV_VARS[ProviderName.ALPHA_VANTAGE], "ALPHA_VANTAGE_API_KEY")
        self.assertEqual(DEFAULT_KEY_ENV_VARS[ProviderName.TWELVE_DATA], "TWELVE_DATA_API_KEY")
        self.assertEqual(DEFAULT_KEY_ENV_VARS[ProviderName.NEWSAPI], "NEWSAPI_API_KEY")

    def test_two_independent_settings_do_not_share_the_env_var_dict(self):
        a = APISettings()
        b = APISettings()
        a.provider_key_env_vars[ProviderName.FMP] = "SOMETHING_ELSE"
        self.assertEqual(b.provider_key_env_vars[ProviderName.FMP], "FMP_API_KEY")


class TestFromEnv(unittest.TestCase):
    def test_from_env_reads_injected_mapping(self):
        env = {
            "API_MANAGER_TIMEOUT_SECONDS": "5",
            "API_MANAGER_RETRY_COUNT": "3",
            "API_MANAGER_COOL_DOWN_SECONDS": "30",
            "API_MANAGER_INVALID_KEY_COOL_DOWN_SECONDS": "9000",
            "API_MANAGER_RESTART_REQUIRED_FOR_REGISTRY_CHANGES": "true",
        }
        settings = APISettings.from_env(env)
        self.assertEqual(settings.timeout_seconds, 5.0)
        self.assertEqual(settings.retry_count, 3)
        self.assertEqual(settings.cool_down_seconds, 30.0)
        self.assertEqual(settings.invalid_key_cool_down_seconds, 9000.0)
        self.assertTrue(settings.restart_required_for_registry_changes)

    def test_from_env_falls_back_to_defaults_when_unset(self):
        settings = APISettings.from_env({})
        self.assertEqual(settings.timeout_seconds, APISettings().timeout_seconds)
        self.assertFalse(settings.restart_required_for_registry_changes)


class TestResolveKey(unittest.TestCase):
    def test_resolve_key_reads_from_injected_environment(self):
        settings = APISettings()
        env = {"FMP_API_KEY": "secret-value"}
        self.assertEqual(settings.resolve_key(ProviderName.FMP, env), "secret-value")

    def test_resolve_key_returns_none_when_unset(self):
        settings = APISettings()
        self.assertIsNone(settings.resolve_key(ProviderName.FMP, {}))

    def test_resolve_key_returns_none_when_blank(self):
        settings = APISettings()
        self.assertIsNone(settings.resolve_key(ProviderName.FMP, {"FMP_API_KEY": ""}))

    def test_resolve_key_never_raises_for_a_missing_key(self):
        settings = APISettings()
        try:
            result = settings.resolve_key(ProviderName.NEWSAPI, {})
        except Exception as exc:  # pragma: no cover - failure path
            self.fail(f"resolve_key raised unexpectedly: {exc}")
        self.assertIsNone(result)


class TestLoadEnvFile(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".env")
        os.close(fd)
        self._original_environ = dict(os.environ)

    def tearDown(self):
        os.remove(self.path)
        os.environ.clear()
        os.environ.update(self._original_environ)

    def _write(self, content: str) -> None:
        with open(self.path, "w", encoding="utf-8") as handle:
            handle.write(content)

    def test_missing_file_returns_empty_dict_and_raises_nothing(self):
        result = load_env_file("this_file_does_not_exist.env")
        self.assertEqual(result, {})

    def test_parses_simple_key_value_pairs(self):
        self._write("FMP_API_KEY=abc123\nNEWSAPI_API_KEY=def456\n")
        os.environ.pop("FMP_API_KEY", None)
        os.environ.pop("NEWSAPI_API_KEY", None)
        result = load_env_file(self.path)
        self.assertEqual(result["FMP_API_KEY"], "abc123")
        self.assertEqual(result["NEWSAPI_API_KEY"], "def456")
        self.assertEqual(os.environ["FMP_API_KEY"], "abc123")

    def test_skips_blank_lines_and_comments(self):
        self._write("# a comment\n\nFMP_API_KEY=abc123\n")
        result = load_env_file(self.path)
        self.assertEqual(result, {"FMP_API_KEY": "abc123"})

    def test_strips_surrounding_quotes(self):
        self._write('FMP_API_KEY="abc123"\nNEWSAPI_API_KEY=\'def456\'\n')
        result = load_env_file(self.path)
        self.assertEqual(result["FMP_API_KEY"], "abc123")
        self.assertEqual(result["NEWSAPI_API_KEY"], "def456")

    def test_does_not_override_existing_environment_by_default(self):
        os.environ["FMP_API_KEY"] = "already-set"
        self._write("FMP_API_KEY=from-file\n")
        load_env_file(self.path)
        self.assertEqual(os.environ["FMP_API_KEY"], "already-set")

    def test_override_true_replaces_existing_environment(self):
        os.environ["FMP_API_KEY"] = "already-set"
        self._write("FMP_API_KEY=from-file\n")
        load_env_file(self.path, override=True)
        self.assertEqual(os.environ["FMP_API_KEY"], "from-file")


if __name__ == "__main__":
    unittest.main()
