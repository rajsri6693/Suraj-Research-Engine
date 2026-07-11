"""Integration tests for the production runtime's wiring into
IntegrationEngine, per Claude-Prompts/IMP_10I_Research_Runtime.md's API
Manager requirement ("Use the existing API Manager. Verify: Primary
routing, Backup routing, Failover, Failback. No provider-specific
logic inside runtime") and its follow-up architecture refactor
("IntegrationEngine.run() as the single orchestration path").

research_engine.runtime.build_collector_factory() builds a live-
APIManager-bound CollectorFactory; these tests inject it into
IntegrationEngine(factory=...) -- exactly research.py's own pattern --
and prove Primary/Backup/Failover/Failback routing flows correctly
through IntegrationEngine's existing, unmodified run() sequence, with
no second orchestration path involved anywhere.

Every HTTP interaction is mocked at each provider's `_send_request()`
seam -- no test in this module ever performs a live internet call.
"""

import unittest

from research_engine.api_manager import APIManager, Category, HealthStatus, ProviderName, ProviderRole
from research_engine.api_manager.provider_interface import ProviderDownError
from research_engine.api_manager.providers.finnhub_provider import FinnhubProvider
from research_engine.api_manager.providers.fmp_provider import FMPProvider
from research_engine.integration.integration_engine import IntegrationEngine
from research_engine.planner.research_plan import KnowledgeSection, ResearchCategory
from research_engine.planner.research_planner import ResearchPlanner
from research_engine.runtime import build_collector_factory


def _fmp_returning(payload_json: bytes) -> FMPProvider:
    provider = FMPProvider(api_key="test-key")
    provider._send_request = lambda url: (200, payload_json)  # type: ignore[method-assign]
    return provider


def _finnhub_returning(payload_json: bytes = b'{"ticker": "INFY", "name": "Infosys Limited"}') -> FinnhubProvider:
    provider = FinnhubProvider(api_key="test-key")
    provider._send_request = lambda url: (200, payload_json)  # type: ignore[method-assign]
    return provider


_FMP_PROFILE_PAYLOAD = (
    b'[{"symbol": "INFY", "companyName": "Infosys Limited", "sector": "Technology", '
    b'"industry": "IT Services", "isin": "INE009A01021", "website": "https://www.infosys.com", '
    b'"description": "Infosys provides consulting.", "city": "Bangalore", "state": "Karnataka", '
    b'"country": "IN", "exchange": "NSE"}]'
)


def _plan(topic: str = "INFY"):
    return ResearchPlanner().create_research_plan(
        research_profile=["INFY"], research_category=ResearchCategory.STOCK_ANALYSIS, research_topic=topic
    )


class TestBuildCollectorFactoryFeedsIntegrationEngineDirectly(unittest.TestCase):
    """Confirms research.py's own wiring pattern: build a live factory,
    inject it into IntegrationEngine -- no intermediate orchestrator
    exists between them."""

    def test_factory_from_build_collector_factory_is_accepted_by_integration_engine(self):
        manager = APIManager()
        factory = build_collector_factory(manager)
        engine = IntegrationEngine(factory=factory)
        result = engine.run(_plan())
        self.assertIsNotNone(result.research_package)


class TestPrimaryRouting(unittest.TestCase):
    """FMP ONLINE -> the Company Information collector uses FMP as
    Primary, end to end through IntegrationEngine.run()."""

    def test_primary_serves_the_request_through_integration_engine(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = _fmp_returning(_FMP_PROFILE_PAYLOAD)
        engine = IntegrationEngine(factory=build_collector_factory(manager))

        result = engine.run(_plan())

        company_entry = next(
            e for e in result.research_package.knowledge_sections
            if e.knowledge_section.value == "Company Information"
        )
        self.assertEqual(company_entry.status.value, "Completed")
        self.assertIn("Financial Modeling Prep", company_entry.sources[0])
        self.assertIn("Primary", company_entry.sources[0])
        self.assertEqual(
            manager.logger.usage_count(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA), 0
        )


class TestBackupRoutingAndFailover(unittest.TestCase):
    """FMP DOWN -> automatic switch to Finnhub, end to end through
    IntegrationEngine.run() -- provider selection logged via the
    existing, unmodified API Manager logging mechanism."""

    def test_backup_serves_the_request_when_primary_is_down(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated FMP outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning()
        engine = IntegrationEngine(factory=build_collector_factory(manager))

        result = engine.run(_plan())

        company_entry = next(
            e for e in result.research_package.knowledge_sections
            if e.knowledge_section.value == "Company Information"
        )
        self.assertEqual(company_entry.status.value, "Completed")
        self.assertIn("Finnhub", company_entry.sources[0])
        self.assertIn("Backup", company_entry.sources[0])

    def test_provider_selection_is_logged_by_the_existing_api_manager(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated FMP outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning()
        engine = IntegrationEngine(factory=build_collector_factory(manager))

        engine.run(_plan())

        fmp_entries = manager.logger.entries_for(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
        finnhub_entries = manager.logger.entries_for(ProviderName.FINNHUB, Category.FUNDAMENTAL_DATA)
        self.assertGreaterEqual(len(fmp_entries), 1)
        self.assertEqual(fmp_entries[0].outcome.value, "FAILURE")
        self.assertGreaterEqual(len(finnhub_entries), 1)
        self.assertEqual(finnhub_entries[0].served_by, ProviderRole.BACKUP)

    def test_both_primary_and_backup_down_reports_missing_never_fabricated(self):
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated FMP outage")
        )
        manager.adapters[ProviderName.FINNHUB] = FinnhubProvider(
            simulate_failure=ProviderDownError("simulated Finnhub outage too")
        )
        engine = IntegrationEngine(factory=build_collector_factory(manager))

        result = engine.run(_plan())

        company_entry = next(
            e for e in result.research_package.knowledge_sections
            if e.knowledge_section.value == "Company Information"
        )
        self.assertEqual(company_entry.status.value, "Missing")


class TestFailback(unittest.TestCase):
    """FMP recovers -> subsequent IntegrationEngine.run() calls
    automatically use it as Primary again, with no manual reset. Reuses
    the same engine instance across both calls, matching
    TestIntegrationEngineIsReusable's own established pattern
    (tests/integration/test_integration_engine.py)."""

    def test_fmp_resumes_as_primary_once_cool_down_elapses(self):
        manager = APIManager()
        manager.health_tracker.cool_down_seconds = 0.0
        manager.adapters[ProviderName.FMP] = FMPProvider(
            simulate_failure=ProviderDownError("simulated FMP outage")
        )
        manager.adapters[ProviderName.FINNHUB] = _finnhub_returning()
        engine = IntegrationEngine(factory=build_collector_factory(manager))

        first = engine.run(_plan())
        first_company = next(
            e for e in first.research_package.knowledge_sections
            if e.knowledge_section.value == "Company Information"
        )
        self.assertIn("Finnhub", first_company.sources[0])

        manager.adapters[ProviderName.FMP] = _fmp_returning(_FMP_PROFILE_PAYLOAD)
        second = engine.run(_plan())
        second_company = next(
            e for e in second.research_package.knowledge_sections
            if e.knowledge_section.value == "Company Information"
        )
        self.assertIn("Financial Modeling Prep", second_company.sources[0])
        self.assertIn("Primary", second_company.sources[0])

        fmp_health = manager.health_tracker.get(ProviderName.FMP, Category.FUNDAMENTAL_DATA)
        self.assertEqual(fmp_health.status, HealthStatus.ONLINE)


class TestSingleOrchestrationPath(unittest.TestCase):
    """Structural proof that research.py and research_engine.runtime
    contain no second orchestration implementation -- both only ever
    call into IntegrationEngine.run(), never re-implement Workflow
    stage advancement themselves."""

    def test_research_engine_runtime_package_no_longer_exists(self):
        import importlib

        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module("research_engine.runtime.research_runtime")

    def test_research_cli_never_advances_a_workflow_stage_itself(self):
        import pathlib

        path = pathlib.Path(__file__).resolve().parents[2] / "research.py"
        source = path.read_text(encoding="utf-8")
        self.assertNotIn("ResearchWorkflow", source)
        self.assertNotIn("advance_stage", source)
        self.assertNotIn("register_collector", source)
        self.assertNotIn("mark_collector_complete", source)

    def test_research_cli_calls_integration_engine_run(self):
        import pathlib

        path = pathlib.Path(__file__).resolve().parents[2] / "research.py"
        source = path.read_text(encoding="utf-8")
        self.assertIn("IntegrationEngine", source)
        self.assertIn(".run(plan)", source)

    def test_collector_wiring_module_contains_no_orchestration_sequencing(self):
        """The one file this refactor keeps (collector_wiring.py) only
        builds a registry/factory -- it must never itself call
        ResearchWorkflow, ResearchResultAssembly, or KnowledgeVerifier,
        which would mean a second orchestration path had crept back in."""
        import pathlib

        path = (
            pathlib.Path(__file__).resolve().parents[2]
            / "research_engine"
            / "runtime"
            / "collector_wiring.py"
        )
        source = path.read_text(encoding="utf-8")
        for forbidden in ("ResearchWorkflow", "ResearchResultAssembly", "KnowledgeVerifier"):
            self.assertNotIn(forbidden, source)


class TestResearchCliContainsNoBusinessWorkflowLogic(unittest.TestCase):
    """research.py must contain only bootstrap/CLI logic -- input/output,
    dependency construction, and dispatch to already-existing modules.
    Confirmed both structurally (no domain rule ever re-implemented, no
    module it doesn't already call being reached into) and behaviorally
    (validation stays single-sourced in ResearchPlanner, never
    duplicated at the CLI layer)."""

    def _source(self) -> str:
        import pathlib

        return (pathlib.Path(__file__).resolve().parents[2] / "research.py").read_text(
            encoding="utf-8"
        )

    def test_no_duplicate_research_topic_validation(self):
        """research.py must not re-implement ResearchPlanner's own
        "Research Topic must not be empty" rule -- it relies entirely
        on ResearchPlanner raising InvalidResearchInputError, caught
        and reported, never pre-checked itself."""
        source = self._source()
        self.assertNotIn("must not be empty", source)
        # The only validation-flavored string research.py contains of
        # its own is the *error label* it wraps InvalidResearchInputError
        # with -- never a re-implementation of the rule's own condition.
        self.assertIn("except InvalidResearchInputError", source)

    def test_no_verification_rule_reimplemented(self):
        """Knowledge Verification's own rules (source validation,
        missing information, metadata requirements) belong exclusively
        to KnowledgeVerifier -- research.py only ever reads
        verification_report.verified_sections/overall_status, it never
        computes a verification outcome itself."""
        source = self._source()
        for forbidden in ("VerificationStatus.VERIFIED", "VerificationStatus.REJECTED", "collected_knowledge is None"):
            self.assertNotIn(forbidden, source)

    def test_no_approval_rule_reimplemented(self):
        """Approval's own rule (persist only if Approved, notify only
        after persistence) belongs exclusively to ApprovalService --
        research.py only calls .process() and reads the outcome."""
        source = self._source()
        self.assertNotIn("ReviewDecision.APPROVED", source)
        self.assertIn("approval_service.process(", source)

    def test_research_topic_validation_is_still_reported_correctly(self):
        """Behavioral confirmation that removing research.py's own
        redundant guard did not remove the *capability* -- an empty
        topic is still gracefully reported as invalid, sourced entirely
        from ResearchPlanner's own InvalidResearchInputError."""
        import research as research_cli

        summary = research_cli.run_research_session("", print_fn=lambda *_: None)
        self.assertFalse(summary["success"])
        self.assertIn("Invalid Research Topic", summary["error"])


class TestIntegrationEngineIsTheSoleOrchestrator(unittest.TestCase):
    """IntegrationEngine remains the single source of truth for
    workflow orchestration -- no other module in the repository
    constructs a ResearchWorkflow or drives its stage transitions."""

    def test_only_integration_engine_constructs_a_research_workflow(self):
        import pathlib

        repo_root = pathlib.Path(__file__).resolve().parents[2]
        matches = []
        for path in repo_root.rglob("*.py"):
            relative = path.relative_to(repo_root)
            parts = relative.parts
            if parts[0] == "tests" or (parts[0] == "research_engine" and parts[1] == "workflow"):
                continue
            if "ResearchWorkflow()" in path.read_text(encoding="utf-8"):
                matches.append(relative.as_posix())
        self.assertEqual(
            matches,
            ["research_engine/integration/integration_engine.py"],
            f"unexpected ResearchWorkflow() construction site(s): {matches}",
        )

    def test_research_cli_never_constructs_a_research_workflow(self):
        import pathlib

        source = (pathlib.Path(__file__).resolve().parents[2] / "research.py").read_text(
            encoding="utf-8"
        )
        self.assertNotIn("ResearchWorkflow", source)

    def test_collector_wiring_never_constructs_a_research_workflow(self):
        import pathlib

        source = (
            pathlib.Path(__file__).resolve().parents[2]
            / "research_engine" / "runtime" / "collector_wiring.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("ResearchWorkflow", source)


class TestNoProviderSpecificLogicInsideRuntime(unittest.TestCase):
    """Structural proof, per IMP-10I: "No provider-specific logic
    inside runtime." research.py, research_engine/runtime/, and
    IntegrationEngine never reference a concrete provider adapter class
    or provider name string -- routing/failover/failback are entirely
    APIManager's own, unmodified responsibility."""

    def _assert_no_provider_references(self, path):
        source = path.read_text(encoding="utf-8")
        for forbidden in (
            "FMPProvider",
            "FinnhubProvider",
            "AlphaVantageProvider",
            "TwelveDataProvider",
            "NewsAPIProvider",
            "ProviderName.FMP",
            "ProviderName.FINNHUB",
        ):
            self.assertNotIn(forbidden, source, f"{path}: found provider-specific reference: {forbidden}")

    def test_research_cli_never_references_a_concrete_provider(self):
        import pathlib

        self._assert_no_provider_references(pathlib.Path(__file__).resolve().parents[2] / "research.py")

    def test_collector_wiring_never_references_a_concrete_provider(self):
        import pathlib

        self._assert_no_provider_references(
            pathlib.Path(__file__).resolve().parents[2]
            / "research_engine"
            / "runtime"
            / "collector_wiring.py"
        )

    def test_integration_engine_never_references_a_concrete_provider(self):
        import pathlib

        self._assert_no_provider_references(
            pathlib.Path(__file__).resolve().parents[2]
            / "research_engine"
            / "integration"
            / "integration_engine.py"
        )


if __name__ == "__main__":
    unittest.main()
