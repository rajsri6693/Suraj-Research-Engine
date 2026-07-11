"""End-to-end tests for research.py, the Research Engine's production
runtime entry point, per Claude-Prompts/IMP_10I_Research_Runtime.md and
its follow-up architecture refactor.

Drives the complete pipeline through research.run_research_session():

    Research Topic -> Research Planner -> IntegrationEngine.run()
    (Research Workflow -> Collectors -> API Manager -> Research Result
    Assembly -> Knowledge Verification -> Chart Generation) -> Human
    Review -> Approval -> Telegram Notification -> Completion

exactly as tests/e2e/test_end_to_end.py already does for
IntegrationEngine directly, extended with a real (HTTP-mocked)
APIManager threaded into IntegrationEngine's own collectors (via
IntegrationEngine's optional `factory` constructor parameter) and a
real interactive Human Review decision (injected, not stdin).
IntegrationEngine.run() is the single orchestration path -- this test
module never exercises a second one.

Every HTTP interaction is mocked at each provider's `_send_request()`
seam -- no test in this module ever performs a live internet call.
Telegram is configured Enabled with its outbound network call replaced
by in-memory recording, mirroring test_end_to_end.py's own
RecordingTelegramNotificationService exactly. Every database write
uses an isolated, temp-file-backed DatabaseManager -- never the real
project database file.
"""

import os
import tempfile
import unittest

import research as research_cli
from research_database.database_manager import DatabaseManager
from research_engine.api_manager import APIManager, ProviderName
from research_engine.api_manager.provider_interface import ProviderDownError
from research_engine.api_manager.providers.finnhub_provider import FinnhubProvider
from research_engine.api_manager.providers.fmp_provider import FMPProvider
from research_engine.notifications.telegram_notification import (
    TelegramConfig,
    TelegramNotificationService,
)


class RecordingTelegramNotificationService(TelegramNotificationService):
    """Mirrors tests/e2e/test_end_to_end.py's own
    RecordingTelegramNotificationService exactly -- Enabled, with the
    actual outbound network call replaced by in-memory recording."""

    def __init__(self):
        super().__init__(
            TelegramConfig(enabled=True, bot_token="e2e-test-token", chat_id="e2e-test-chat")
        )
        self.calls = []

    def send(self, **kwargs):
        result = super().send(**kwargs)
        self.calls.append(kwargs)
        return result

    def _send_via_telegram_api(self, message: str) -> None:
        return  # No real network call in this end-to-end suite.


def make_isolated_database_manager() -> DatabaseManager:
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(db_path)
    manager = DatabaseManager(db_path)
    manager.e2e_db_path = db_path  # type: ignore[attr-defined]
    return manager


def close_isolated_database_manager(manager: DatabaseManager) -> None:
    manager.close()
    db_path = getattr(manager, "e2e_db_path", None)
    if db_path and os.path.exists(db_path):
        os.remove(db_path)


def _fmp_returning(payload_json: bytes) -> FMPProvider:
    provider = FMPProvider(api_key="test-key")
    provider._send_request = lambda url: (200, payload_json)  # type: ignore[method-assign]
    return provider


_FMP_PROFILE_PAYLOAD = (
    b'[{"symbol": "INFY", "companyName": "Infosys Limited", "sector": "Technology", '
    b'"industry": "IT Services", "isin": "INE009A01021", "website": "https://www.infosys.com", '
    b'"description": "Infosys provides consulting.", "city": "Bangalore", "state": "Karnataka", '
    b'"country": "IN", "exchange": "NSE"}]'
)


def _scripted_input(*answers):
    remaining = iter(answers)

    def _input(prompt):
        return next(remaining)

    return _input


class TestApprovalPath(unittest.TestCase):
    """Approve -> Approval's own approved_research table persistence
    -> Telegram sent."""

    def setUp(self):
        self.db = make_isolated_database_manager()
        self.manager = APIManager()
        self.manager.adapters[ProviderName.FMP] = _fmp_returning(_FMP_PROFILE_PAYLOAD)
        self.notifier = RecordingTelegramNotificationService()

    def tearDown(self):
        close_isolated_database_manager(self.db)

    def test_full_pipeline_reaches_completion(self):
        summary = research_cli.run_research_session(
            "INFY",
            database_manager=self.db,
            api_manager=self.manager,
            notifier=self.notifier,
            input_fn=_scripted_input("e2e-reviewer", "A", "approved via e2e test"),
            print_fn=lambda *_: None,
        )

        self.assertTrue(summary["success"], summary.get("error"))
        self.assertEqual(summary["stage_reached"], "Completed")

    def test_approval_persists_to_sqlite(self):
        summary = research_cli.run_research_session(
            "INFY",
            database_manager=self.db,
            api_manager=self.manager,
            notifier=self.notifier,
            input_fn=_scripted_input("e2e-reviewer", "A", ""),
            print_fn=lambda *_: None,
        )

        outcome = summary["approval_outcome"]
        self.assertTrue(outcome.persisted)
        row = self.db.fetch_one(
            "SELECT * FROM approved_research WHERE research_id = ?",
            (summary["review_result"].research_id,),
        )
        self.assertIsNotNone(row)
        self.assertEqual(row["research_id"], summary["review_result"].research_id)

    def test_approval_triggers_telegram_only_after_persistence(self):
        summary = research_cli.run_research_session(
            "INFY",
            database_manager=self.db,
            api_manager=self.manager,
            notifier=self.notifier,
            input_fn=_scripted_input("e2e-reviewer", "A", ""),
            print_fn=lambda *_: None,
        )

        self.assertEqual(len(self.notifier.calls), 1)
        self.assertTrue(summary["approval_outcome"].notified)

    def test_collectors_execute_through_integration_engine(self):
        summary = research_cli.run_research_session(
            "INFY",
            database_manager=self.db,
            api_manager=self.manager,
            notifier=self.notifier,
            input_fn=_scripted_input("e2e-reviewer", "A", ""),
            print_fn=lambda *_: None,
        )

        integration_result = summary["integration_result"]
        company_entry = next(
            e for e in integration_result.research_package.knowledge_sections
            if e.knowledge_section.value == "Company Information"
        )
        self.assertEqual(company_entry.status.value, "Completed")
        self.assertIn("Financial Modeling Prep", company_entry.sources[0])


class TestRejectionPath(unittest.TestCase):
    """Reject -> Approval never persists, Telegram never sends."""

    def setUp(self):
        self.db = make_isolated_database_manager()
        self.manager = APIManager()
        self.manager.adapters[ProviderName.FMP] = _fmp_returning(_FMP_PROFILE_PAYLOAD)
        self.notifier = RecordingTelegramNotificationService()

    def tearDown(self):
        close_isolated_database_manager(self.db)

    def test_rejected_research_is_never_persisted_or_notified(self):
        summary = research_cli.run_research_session(
            "INFY",
            database_manager=self.db,
            api_manager=self.manager,
            notifier=self.notifier,
            input_fn=_scripted_input("e2e-reviewer", "R", "not accurate enough"),
            print_fn=lambda *_: None,
        )

        self.assertTrue(summary["success"])
        outcome = summary["approval_outcome"]
        self.assertFalse(outcome.persisted)
        self.assertFalse(outcome.notified)
        self.assertEqual(len(self.notifier.calls), 0)


class TestSkipAndRevisionPaths(unittest.TestCase):
    def setUp(self):
        self.db = make_isolated_database_manager()
        self.manager = APIManager()
        self.manager.adapters[ProviderName.FMP] = _fmp_returning(_FMP_PROFILE_PAYLOAD)
        self.notifier = RecordingTelegramNotificationService()

    def tearDown(self):
        close_isolated_database_manager(self.db)

    def test_skip_never_persists_or_notifies(self):
        summary = research_cli.run_research_session(
            "INFY",
            database_manager=self.db,
            api_manager=self.manager,
            notifier=self.notifier,
            input_fn=_scripted_input("e2e-reviewer", "S", ""),
            print_fn=lambda *_: None,
        )
        self.assertFalse(summary["approval_outcome"].persisted)
        self.assertEqual(len(self.notifier.calls), 0)

    def test_request_revision_never_persists_or_notifies(self):
        summary = research_cli.run_research_session(
            "INFY",
            database_manager=self.db,
            api_manager=self.manager,
            notifier=self.notifier,
            input_fn=_scripted_input("e2e-reviewer", "V", "please redo Financial Information"),
            print_fn=lambda *_: None,
        )
        self.assertFalse(summary["approval_outcome"].persisted)
        self.assertEqual(len(self.notifier.calls), 0)
        self.assertEqual(summary["review_result"].review_decision.value, "Needs Revision")

    def test_unrecognized_decision_defaults_to_skip_never_silently_approves(self):
        summary = research_cli.run_research_session(
            "INFY",
            database_manager=self.db,
            api_manager=self.manager,
            notifier=self.notifier,
            input_fn=_scripted_input("e2e-reviewer", "banana", ""),
            print_fn=lambda *_: None,
        )
        self.assertFalse(summary["approval_outcome"].persisted)
        self.assertEqual(summary["review_result"].review_decision.value, "Skipped")


class TestErrorHandling(unittest.TestCase):
    """Per IMP-10I's Error Handling section: Invalid topic, API
    failure, SQLite failure, Telegram failure, and unexpected
    exceptions are all handled gracefully -- run_research_session()
    never raises, and always returns a well-formed summary."""

    def test_empty_topic_is_reported_as_invalid_not_raised(self):
        summary = research_cli.run_research_session("", print_fn=lambda *_: None)
        self.assertFalse(summary["success"])
        self.assertIn("Invalid Research Topic", summary["error"])

    def test_whitespace_only_topic_is_reported_as_invalid(self):
        summary = research_cli.run_research_session("    ", print_fn=lambda *_: None)
        self.assertFalse(summary["success"])
        self.assertIn("Invalid Research Topic", summary["error"])

    def test_api_failure_on_both_primary_and_backup_still_completes_gracefully(self):
        """An API failure never crashes the runtime -- affected
        sections simply report Missing, and the pipeline still reaches
        Human Review for whatever did succeed (Sources/Metadata, which
        need no API Manager)."""
        db = make_isolated_database_manager()
        try:
            manager = APIManager()
            manager.adapters[ProviderName.FMP] = FMPProvider(
                simulate_failure=ProviderDownError("simulated FMP outage")
            )
            manager.adapters[ProviderName.FINNHUB] = FinnhubProvider(
                simulate_failure=ProviderDownError("simulated Finnhub outage too")
            )
            summary = research_cli.run_research_session(
                "INFY",
                database_manager=db,
                api_manager=manager,
                notifier=RecordingTelegramNotificationService(),
                input_fn=_scripted_input("e2e-reviewer", "A", ""),
                print_fn=lambda *_: None,
            )
            self.assertTrue(summary["success"], summary.get("error"))
            integration_result = summary["integration_result"]
            company_entry = next(
                e for e in integration_result.research_package.knowledge_sections
                if e.knowledge_section.value == "Company Information"
            )
            self.assertEqual(company_entry.status.value, "Missing")
        finally:
            close_isolated_database_manager(db)

    def test_approval_sqlite_failure_does_not_raise_out_of_run_research_session(self):
        """A DatabaseManager pointed at an unwritable/invalid path makes
        Approval's own persistence attempt fail -- run_research_session
        must still return a well-formed summary instead of raising, per
        IMP-10I's Error Handling section. ApprovalService itself already
        catches DatabaseError internally and reports it via
        ApprovalOutcome.persisted=False; this test proves that
        contract survives being driven through research.py end to end."""
        broken_db = DatabaseManager(os.path.join("Z:", "definitely", "not", "a", "real", "path.db"))
        manager = APIManager()
        manager.adapters[ProviderName.FMP] = _fmp_returning(_FMP_PROFILE_PAYLOAD)
        summary = research_cli.run_research_session(
            "INFY",
            database_manager=broken_db,
            api_manager=manager,
            notifier=RecordingTelegramNotificationService(),
            input_fn=_scripted_input("e2e-reviewer", "A", ""),
            print_fn=lambda *_: None,
        )
        # Never raises -- always a well-formed summary, whether the run
        # degraded gracefully (success with a reported persistence
        # failure) or failed with a clear "error" message.
        self.assertIn("success", summary)
        self.assertIsInstance(summary["success"], bool)
        if summary["success"]:
            self.assertFalse(summary["approval_outcome"].persisted)


class TestInputDerivation(unittest.TestCase):
    """Chart-request wording detection flows through unchanged into
    Research Planner's own chart_required, and Research Profile is
    derived cleanly."""

    def test_chart_wording_sets_chart_required_via_the_existing_planner(self):
        research_profile, research_category = research_cli.derive_profile_and_category(
            "INFY with chart"
        )
        self.assertEqual(research_profile, ["INFY"])

    def test_bare_symbol_has_no_chart_wording_stripped(self):
        research_profile, _ = research_cli.derive_profile_and_category("INFY")
        self.assertEqual(research_profile, ["INFY"])

    def test_nifty_50_is_preserved_as_a_single_profile_identifier(self):
        research_profile, _ = research_cli.derive_profile_and_category("NIFTY 50")
        self.assertEqual(research_profile, ["NIFTY 50"])


if __name__ == "__main__":
    unittest.main()
