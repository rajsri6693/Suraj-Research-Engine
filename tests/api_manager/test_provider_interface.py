"""Unit tests for research_engine.api_manager.provider_interface."""

import unittest

from research_engine.api_manager.provider_interface import (
    ProviderCallError,
    ProviderDownError,
    ProviderInterface,
    ProviderInvalidKeyError,
    ProviderRateLimitedError,
    ProviderResponse,
    ProviderTimeoutError,
)


class TestProviderInterfaceIsAbstract(unittest.TestCase):
    def test_cannot_instantiate_directly(self):
        with self.assertRaises(TypeError):
            ProviderInterface()  # type: ignore[abstract]


class TestExceptionHierarchy(unittest.TestCase):
    def test_all_four_failure_errors_subclass_provider_call_error(self):
        for error_class in (
            ProviderDownError,
            ProviderRateLimitedError,
            ProviderInvalidKeyError,
            ProviderTimeoutError,
        ):
            self.assertTrue(issubclass(error_class, ProviderCallError))

    def test_provider_call_error_is_an_exception(self):
        self.assertTrue(issubclass(ProviderCallError, Exception))

    def test_failure_errors_are_distinct_from_each_other(self):
        errors = (
            ProviderDownError,
            ProviderRateLimitedError,
            ProviderInvalidKeyError,
            ProviderTimeoutError,
        )
        for a in errors:
            for b in errors:
                if a is not b:
                    self.assertFalse(issubclass(a, b))


class TestProviderResponse(unittest.TestCase):
    def test_holds_data_and_response_time(self):
        response = ProviderResponse(data={"a": 1}, response_time_ms=3.2)
        self.assertEqual(response.data, {"a": 1})
        self.assertEqual(response.response_time_ms, 3.2)


if __name__ == "__main__":
    unittest.main()
