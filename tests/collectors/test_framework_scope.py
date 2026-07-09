"""Confirms the Collectors package is framework-only: standard Python
only, and no real collector implementation exists."""

import ast
import pathlib
import unittest

PACKAGE_DIR = (
    pathlib.Path(__file__).resolve().parents[2] / "research_engine" / "collectors"
)

FORBIDDEN_COLLECTOR_NAMES = {
    "CompanyCollector",
    "FinancialCollector",
    "NewsCollector",
    "TechnicalCollector",
    "GovernmentCollector",
    "CorporateActionCollector",
}


class TestCollectorsHaveNoForeignDependencies(unittest.TestCase):
    def test_only_standard_library_imports(self):
        allowed_stdlib = {"abc", "typing", "__future__"}
        for module_path in PACKAGE_DIR.glob("*.py"):
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom):
                    if node.level > 0:
                        continue  # relative import within this package
                    self.assertIn(
                        node.module,
                        allowed_stdlib,
                        f"{module_path.name}: unexpected import '{node.module}'",
                    )
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        top = alias.name.split(".")[0]
                        self.assertIn(
                            top,
                            allowed_stdlib,
                            f"{module_path.name}: unexpected import '{alias.name}'",
                        )


class TestNoRealCollectorsExist(unittest.TestCase):
    def test_no_forbidden_collector_class_names_are_defined(self):
        defined_class_names = set()
        for module_path in PACKAGE_DIR.glob("*.py"):
            tree = ast.parse(module_path.read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    defined_class_names.add(node.name)
        self.assertEqual(defined_class_names & FORBIDDEN_COLLECTOR_NAMES, set())

    def test_only_the_three_framework_files_exist(self):
        python_files = {path.name for path in PACKAGE_DIR.glob("*.py")}
        self.assertEqual(
            python_files,
            {"__init__.py", "base_collector.py", "collector_registry.py", "collector_factory.py"},
        )


if __name__ == "__main__":
    unittest.main()
