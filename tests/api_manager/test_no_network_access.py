"""Structural boundary test for research_engine.api_manager.

Mirrors tests/collectors/financial/test_financial_collector.py's
TestNoForeignDependencies pattern: parses every .py file in the
package with the standard library `ast` module and asserts only an
explicit allow-list of standard-library imports is used. Proves, at
the import-graph level rather than by convention alone, that the core
API Manager (api_manager.py, api_registry.py, api_health.py,
api_logging.py, api_settings.py, api_status.py, provider_interface.py)
and every still-placeholder provider adapter make no HTTP request,
touch no network, and have no dependency on the database or an AI
provider.

Per Claude-Prompts/IMP_10C_FMP_Integration.md, FMP alone is now a real,
live-HTTP adapter -- fmp_provider.py is the one deliberate, narrowly
scoped exception to this boundary, verified separately below by
test_fmp_provider_is_the_only_module_using_the_network_allowlist. Every
other module in this package, including the four remaining placeholder
providers (Finnhub, Alpha Vantage, Twelve Data, NewsAPI), is still held
to the original zero-network standard.
"""

import ast
import pathlib
import unittest

ALLOWED_STDLIB = {
    "__future__",
    "abc",
    "dataclasses",
    "datetime",
    "enum",
    "os",
    "time",
    "typing",
}

# fmp_provider.py's additional, narrowly scoped allowance -- HTTP
# client and response-parsing modules only, still standard library.
FMP_NETWORK_ALLOWLIST = ALLOWED_STDLIB | {"json", "urllib.error", "urllib.parse", "urllib.request"}

FORBIDDEN_MODULES = {
    "http",
    "http.client",
    "requests",
    "socket",
    "ftplib",
    "smtplib",
    "telnetlib",
    "sqlite3",
    "research_database",
    "ai",
    "openai",
    "anthropic",
}

FMP_PROVIDER_MODULE_NAME = "fmp_provider.py"


def _package_dir() -> pathlib.Path:
    return pathlib.Path(__file__).resolve().parents[2] / "research_engine" / "api_manager"


def _module_paths() -> list:
    package_dir = _package_dir()
    return list(package_dir.glob("*.py")) + list(package_dir.glob("providers/*.py"))


def _imported_names(module_path: pathlib.Path):
    """Yield every top-level (non-relative) import name in a module."""
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level > 0:
                continue  # relative import within the api_manager package
            yield node.module
        elif isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name


class TestNoNetworkOrDatabaseAccess(unittest.TestCase):
    def test_only_standard_library_and_framework_imports(self):
        module_paths = _module_paths()
        self.assertGreater(len(module_paths), 0, "no modules found to scan")

        for module_path in module_paths:
            allowlist = (
                FMP_NETWORK_ALLOWLIST
                if module_path.name == FMP_PROVIDER_MODULE_NAME
                else ALLOWED_STDLIB
            )
            for name in _imported_names(module_path):
                top = name.split(".")[0]
                self.assertNotIn(
                    top, FORBIDDEN_MODULES, f"{module_path}: forbidden import '{name}'"
                )
                self.assertTrue(
                    name in allowlist or top in allowlist,
                    f"{module_path}: unexpected import '{name}'",
                )

    def test_fmp_provider_is_the_only_module_using_the_network_allowlist(self):
        """Every module except fmp_provider.py must be satisfiable by
        the strict, network-free allowlist alone -- proving the live-
        HTTP exception is exactly one file wide, per
        IMP_10C_FMP_Integration.md's 'Only FMP is implemented' scope."""
        for module_path in _module_paths():
            if module_path.name == FMP_PROVIDER_MODULE_NAME:
                continue
            for name in _imported_names(module_path):
                top = name.split(".")[0]
                self.assertTrue(
                    name in ALLOWED_STDLIB or top in ALLOWED_STDLIB,
                    f"{module_path}: '{name}' is only permitted in {FMP_PROVIDER_MODULE_NAME}",
                )

    def test_no_module_calls_urlopen_or_socket_connect(self):
        """Belt-and-suspenders textual check in case a forbidden call is
        reached through an already-allowed module. fmp_provider.py is
        expected to call urlopen() -- that is its one job -- and is
        exempted here; every other module must still contain none of
        these snippets."""
        forbidden_snippets = ("urlopen(", "socket.socket(", "requests.get(", "requests.post(")
        for module_path in _module_paths():
            if module_path.name == FMP_PROVIDER_MODULE_NAME:
                continue
            source = module_path.read_text(encoding="utf-8")
            for snippet in forbidden_snippets:
                self.assertNotIn(snippet, source, f"{module_path}: found '{snippet}'")

    def test_fmp_provider_only_touches_the_network_inside_send_request(self):
        """fmp_provider.py's urlopen() call must live inside exactly
        one method (_send_request) -- the single isolated seam every
        test in this repository replaces, per that module's own
        docstring, so no test anywhere can accidentally make a live
        call through a different code path."""
        fmp_path = _package_dir() / "providers" / FMP_PROVIDER_MODULE_NAME
        tree = ast.parse(fmp_path.read_text(encoding="utf-8"))

        calling_methods = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for inner in ast.walk(node):
                    if (
                        isinstance(inner, ast.Attribute)
                        and inner.attr == "urlopen"
                    ):
                        calling_methods.append(node.name)

        self.assertEqual(calling_methods, ["_send_request"])


if __name__ == "__main__":
    unittest.main()
