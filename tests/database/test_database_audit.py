"""Database Audit tests, per Claude-Prompts/IMP_09E_End_To_End_Test.md's
Database Audit requirements: schema, table relationships, primary keys,
foreign keys, constraints, data integrity, and which pipeline stages
actually persist to a database today.

Two independent database surfaces exist in this repository, and this
audit covers both separately -- the Research Engine (research_engine/)
never uses the Phase 01 Verified Knowledge Database schema
(research_database/schema/) at all; it only ever creates and writes its
own `approved_research` table, via ApprovalService:

1. The Phase 01 Verified Knowledge Database schema
   (research_database/database_initializer.py) -- 17 entity tables plus
   schema_version, generated automatically from the dataclasses under
   research_database/schema/. Audited here for schema shape, primary
   keys, foreign keys, and constraints, exactly as DatabaseInitializer
   builds it today. This audit makes no schema change.

2. The Research Engine's own `approved_research` table
   (research_engine/approval/approval_service.py) -- the only table the
   Research Engine pipeline actually writes to. Audited here for schema
   shape, primary key, NOT NULL enforcement, and end-to-end data
   integrity through real ApprovalService runs.

Every database used here is an isolated, temp-file-backed
DatabaseManager -- never the real project database file
(research_database/data/verified_knowledge.db).
"""

import json
import os
import tempfile
import unittest
from datetime import datetime

from research_database.database_initializer import SCHEMA_VERSION, DatabaseInitializer
from research_database.database_manager import DatabaseError, DatabaseManager
from research_engine.approval.approval_service import ApprovalService
from research_engine.notifications.telegram_notification import (
    TelegramConfig,
    TelegramNotificationService,
)
from research_engine.planner.research_plan import KnowledgeSection
from research_engine.review.review_decision import ReviewDecision
from research_engine.review.review_result import ReviewResult


def make_isolated_database_manager() -> DatabaseManager:
    fd, db_path = tempfile.mkstemp(suffix=".db")
    os.close(fd)
    os.remove(db_path)  # DatabaseManager creates it on first use.
    manager = DatabaseManager(db_path)
    manager.audit_db_path = db_path  # type: ignore[attr-defined]
    return manager


def close_isolated_database_manager(manager: DatabaseManager) -> None:
    manager.close()
    db_path = getattr(manager, "audit_db_path", None)
    if db_path and os.path.exists(db_path):
        os.remove(db_path)


def make_review_result(
    decision: ReviewDecision, research_id: str, sections=None
) -> ReviewResult:
    return ReviewResult(
        research_id=research_id,
        review_decision=decision,
        review_notes="Database audit fixture.",
        reviewed_by="db.auditor",
        review_time=datetime(2026, 7, 9, 10, 0, 0),
        reviewed_sections=sections
        or [KnowledgeSection.FINANCIAL_INFORMATION, KnowledgeSection.COMPANY_INFORMATION],
        revision_sections=[],
    )


def table_names(manager: DatabaseManager) -> set:
    rows = manager.fetch_all(
        "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    )
    return {row["name"] for row in rows}


def table_info(manager: DatabaseManager, table: str):
    return manager.fetch_all(f"PRAGMA table_info({table})")


def foreign_key_list(manager: DatabaseManager, table: str):
    return manager.fetch_all(f"PRAGMA foreign_key_list({table})")


class Phase01SchemaAuditTestCase(unittest.TestCase):
    """Audits the Phase 01 Verified Knowledge Database schema exactly as
    DatabaseInitializer builds it today -- read-only verification, no
    schema change made."""

    @classmethod
    def setUpClass(cls):
        cls.manager = make_isolated_database_manager()
        initializer = DatabaseInitializer(cls.manager)
        initializer.initialize()
        cls.entity_tables = initializer.tables()

    @classmethod
    def tearDownClass(cls):
        close_isolated_database_manager(cls.manager)

    def test_every_entity_table_and_schema_version_table_exist(self):
        existing = table_names(self.manager)
        for table in self.entity_tables:
            self.assertIn(table, existing)
        self.assertIn("schema_version", existing)
        self.assertEqual(len(self.entity_tables), 17)

    def test_every_entity_table_has_an_integer_primary_key_named_id(self):
        for table in self.entity_tables:
            columns = table_info(self.manager, table)
            id_columns = [c for c in columns if c["name"] == "id"]
            self.assertEqual(len(id_columns), 1, f"{table} has no single 'id' column.")
            self.assertEqual(id_columns[0]["pk"], 1, f"{table}.id is not the Primary Key.")
            self.assertEqual(id_columns[0]["type"], "INTEGER")

    def test_no_table_declares_any_foreign_key(self):
        # AUDIT FINDING: DatabaseConnection enables `PRAGMA foreign_keys
        # = ON`, but DatabaseInitializer's generated DDL never emits a
        # FOREIGN KEY clause for any reference-style column (company_id,
        # sector_id, price_history_id, and similar) -- so the pragma
        # currently has nothing to enforce. Documented, not fixed, per
        # this audit's read-only scope.
        for table in self.entity_tables:
            self.assertEqual(
                foreign_key_list(self.manager, table),
                [],
                f"{table} unexpectedly declares a foreign key.",
            )

    def test_no_entity_table_declares_not_null_or_unique_beyond_the_primary_key(self):
        # AUDIT FINDING: every non-id column is generated as a bare
        # `<name> <TYPE>` with no NOT NULL, even though every
        # corresponding dataclass field is non-Optional. Documented, not
        # fixed, per this audit's read-only scope.
        for table in self.entity_tables:
            for column in table_info(self.manager, table):
                if column["name"] == "id":
                    continue
                self.assertEqual(
                    column["notnull"],
                    0,
                    f"{table}.{column['name']} unexpectedly declares NOT NULL.",
                )
        # Confirmed exception: schema_version.id has a CHECK (id = 1)
        # constraint, which is not exposed via PRAGMA table_info's
        # notnull column -- verified separately via sqlite_master's SQL.
        version_table_sql = self.manager.fetch_one(
            "SELECT sql FROM sqlite_master WHERE name = 'schema_version'"
        )["sql"]
        self.assertIn("CHECK (id = 1)", version_table_sql)

    def test_schema_version_row_is_recorded(self):
        row = self.manager.fetch_one("SELECT * FROM schema_version WHERE id = 1")
        self.assertIsNotNone(row)
        self.assertEqual(row["version"], SCHEMA_VERSION)


class ApprovedResearchSchemaAuditTestCase(unittest.TestCase):
    """Audits the Research Engine's own `approved_research` table -- the
    only table the Research Engine pipeline itself ever writes to."""

    @classmethod
    def setUpClass(cls):
        cls.manager = make_isolated_database_manager()
        service = ApprovalService(
            database_manager=cls.manager,
            notifier=TelegramNotificationService(TelegramConfig(enabled=False)),
        )
        # One process() call is enough to create the table via
        # ApprovalService's own idempotent _ensure_table().
        service.process(make_review_result(ReviewDecision.APPROVED, "RS-AUDIT-SCHEMA"))

    @classmethod
    def tearDownClass(cls):
        close_isolated_database_manager(cls.manager)

    def test_table_has_integer_primary_key_named_id(self):
        columns = {c["name"]: c for c in table_info(self.manager, "approved_research")}
        self.assertIn("id", columns)
        self.assertEqual(columns["id"]["pk"], 1)
        self.assertEqual(columns["id"]["type"], "INTEGER")

    def test_required_columns_are_declared_not_null(self):
        columns = {c["name"]: c for c in table_info(self.manager, "approved_research")}
        for required in (
            "research_id",
            "review_time",
            "reviewed_sections",
            "approved_at",
            "chart_available",
        ):
            self.assertEqual(
                columns[required]["notnull"], 1, f"{required} is not declared NOT NULL."
            )
        for optional in ("reviewed_by", "review_notes", "chart_type"):
            self.assertEqual(
                columns[optional]["notnull"], 0, f"{optional} is unexpectedly NOT NULL."
            )

    def test_not_null_constraint_is_actually_enforced_by_sqlite(self):
        with self.assertRaises(DatabaseError):
            self.manager.execute(
                "INSERT INTO approved_research "
                "(reviewed_by, review_notes, review_time, reviewed_sections, approved_at) "
                "VALUES (?, ?, ?, ?, ?)",
                ("someone", "notes", "2026-07-09 10:00:00", "[]", "2026-07-09 10:00:00"),
            )

    def test_chart_available_column_has_default_zero(self):
        columns = {c["name"]: c for c in table_info(self.manager, "approved_research")}
        self.assertEqual(columns["chart_available"]["dflt_value"], "0")

    def test_no_foreign_key_declared_on_approved_research(self):
        # AUDIT FINDING: approved_research.research_id is a plain TEXT
        # column with no FK to any table -- there is no
        # research_session/research_package table in this database for
        # it to reference; every other pipeline artifact is in-memory
        # only (see PipelineStagePersistenceCoverageTestCase).
        self.assertEqual(foreign_key_list(self.manager, "approved_research"), [])


class ApprovedResearchDataIntegrityTestCase(unittest.TestCase):
    """Runs real ApprovalService approvals -- one without a chart, one
    with -- into a single isolated database, then verifies the stored
    rows are internally consistent."""

    @classmethod
    def setUpClass(cls):
        cls.manager = make_isolated_database_manager()
        cls.notifier = TelegramNotificationService(TelegramConfig(enabled=False))
        cls.service = ApprovalService(database_manager=cls.manager, notifier=cls.notifier)

        cls.outcome_no_chart = cls.service.process(
            make_review_result(ReviewDecision.APPROVED, "RS-AUDIT-NOCHART")
        )
        cls.outcome_with_chart = cls.service.process(
            make_review_result(ReviewDecision.APPROVED, "RS-AUDIT-CHART"),
            chart_available=True,
            chart_type="Candlestick",
        )
        cls.rows = cls.manager.fetch_all("SELECT * FROM approved_research ORDER BY id")

    @classmethod
    def tearDownClass(cls):
        close_isolated_database_manager(cls.manager)

    def test_both_approvals_persisted(self):
        self.assertTrue(self.outcome_no_chart.persisted)
        self.assertTrue(self.outcome_with_chart.persisted)
        self.assertEqual(len(self.rows), 2)

    def test_reviewed_sections_round_trips_as_a_valid_json_list_of_section_names(self):
        for row in self.rows:
            sections = json.loads(row["reviewed_sections"])
            self.assertIsInstance(sections, list)
            self.assertIn("Financial Information", sections)
            self.assertIn("Company Information", sections)

    def test_review_time_and_approved_at_are_iso_parseable(self):
        for row in self.rows:
            datetime.fromisoformat(row["review_time"])
            datetime.fromisoformat(row["approved_at"])

    def test_chart_available_is_always_zero_or_one(self):
        for row in self.rows:
            self.assertIn(row["chart_available"], (0, 1))

    def test_chart_type_is_null_exactly_when_chart_unavailable(self):
        no_chart_row = next(r for r in self.rows if r["research_id"] == "RS-AUDIT-NOCHART")
        with_chart_row = next(r for r in self.rows if r["research_id"] == "RS-AUDIT-CHART")
        self.assertEqual(no_chart_row["chart_available"], 0)
        self.assertIsNone(no_chart_row["chart_type"])
        self.assertEqual(with_chart_row["chart_available"], 1)
        self.assertEqual(with_chart_row["chart_type"], "Candlestick")

    def test_ids_are_unique_and_autoincrementing(self):
        ids = [row["id"] for row in self.rows]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(ids, sorted(ids))

    def test_reprocessing_the_same_research_id_inserts_an_additional_row(self):
        # AUDIT FINDING (not a defect): approved_research has no UNIQUE
        # constraint on research_id, so calling process() again for the
        # same research_id inserts a second row rather than upserting.
        # Nothing in RESEARCH_WORKFLOW.md/HUMAN_REVIEW.md requires
        # idempotent re-approval, and IntegrationEngine only ever
        # produces one ReviewResult per pipeline run, so this is
        # documented here rather than changed.
        before = self.manager.fetch_all(
            "SELECT * FROM approved_research WHERE research_id = ?",
            ("RS-AUDIT-NOCHART",),
        )
        self.service.process(make_review_result(ReviewDecision.APPROVED, "RS-AUDIT-NOCHART"))
        after = self.manager.fetch_all(
            "SELECT * FROM approved_research WHERE research_id = ?",
            ("RS-AUDIT-NOCHART",),
        )
        self.assertEqual(len(after), len(before) + 1)


class PipelineStagePersistenceCoverageTestCase(unittest.TestCase):
    """Confirms, by direct inspection of sqlite_master, exactly which
    pipeline stages persist to a database today, per RESEARCH_SESSION.md
    ("It NEVER writes to the database"), RESEARCH_RESULT_ASSEMBLY.md
    ("Write to the database" is a forbidden action), KNOWLEDGE_
    VERIFICATION.md, and HUMAN_REVIEW.md ("Write directly to the
    database" is a forbidden action) -- every one of those stages is
    documented as in-memory-only, with database writes reserved for the
    Approval/Knowledge Storage step alone."""

    def test_only_approved_research_table_exists_after_one_approval(self):
        manager = make_isolated_database_manager()
        try:
            service = ApprovalService(
                database_manager=manager,
                notifier=TelegramNotificationService(TelegramConfig(enabled=False)),
            )
            service.process(make_review_result(ReviewDecision.APPROVED, "RS-AUDIT-COVERAGE"))

            existing = table_names(manager)
            self.assertEqual(existing, {"approved_research"})
            for absent_table in (
                "research_session",
                "research_package",
                "verification_report",
                "human_review",
                "review_result",
                "telegram_log",
                "telegram_notification",
                "chart",
            ):
                self.assertNotIn(absent_table, existing)
        finally:
            close_isolated_database_manager(manager)

    def test_phase01_schema_and_approved_research_table_do_not_overlap(self):
        phase01_manager = make_isolated_database_manager()
        approval_manager = make_isolated_database_manager()
        try:
            DatabaseInitializer(phase01_manager).initialize()
            ApprovalService(
                database_manager=approval_manager,
                notifier=TelegramNotificationService(TelegramConfig(enabled=False)),
            ).process(make_review_result(ReviewDecision.APPROVED, "RS-AUDIT-DISJOINT"))

            phase01_tables = table_names(phase01_manager)
            approval_tables = table_names(approval_manager)

            self.assertNotIn("approved_research", phase01_tables)
            self.assertEqual(phase01_tables & approval_tables, set())
        finally:
            close_isolated_database_manager(phase01_manager)
            close_isolated_database_manager(approval_manager)

    def test_no_telegram_notification_is_ever_persisted(self):
        # Telegram notifications are returned as an in-memory
        # NotificationResult only, per notifications/telegram_notification.py
        # -- nothing about a sent message is written to any table.
        manager = make_isolated_database_manager()
        try:
            service = ApprovalService(
                database_manager=manager,
                notifier=TelegramNotificationService(TelegramConfig(enabled=False)),
            )
            outcome = service.process(
                make_review_result(ReviewDecision.APPROVED, "RS-AUDIT-TELEGRAM")
            )
            self.assertIsNotNone(outcome.notification)

            columns = {c["name"] for c in table_info(manager, "approved_research")}
            self.assertNotIn("notification_sent", columns)
            self.assertNotIn("telegram_message", columns)
            self.assertEqual(table_names(manager), {"approved_research"})
        finally:
            close_isolated_database_manager(manager)


if __name__ == "__main__":
    unittest.main()
