"""Unit tests for research_engine.session.session_manager."""

import unittest

from research_engine.session.research_session import (
    InvalidSessionTransitionError,
    SessionNotFoundError,
    SessionStatus,
)
from research_engine.session.session_manager import SessionManager


def create_sample_session(manager: SessionManager):
    return manager.create_session(
        research_topic="Full analysis ahead of quarterly results next week.",
        research_profile="Sample Manufacturing Ltd (SMFG, NSE)",
        research_category="Stock Analysis",
    )


class TestCreateSession(unittest.TestCase):
    def setUp(self):
        self.manager = SessionManager()

    def test_create_session_starts_at_created_status(self):
        session = create_sample_session(self.manager)
        self.assertEqual(session.overall_status, SessionStatus.CREATED)

    def test_create_session_assigns_start_time(self):
        session = create_sample_session(self.manager)
        self.assertIsNotNone(session.start_time)

    def test_create_session_assigns_unique_research_ids(self):
        first = create_sample_session(self.manager)
        second = create_sample_session(self.manager)
        self.assertNotEqual(first.research_id, second.research_id)

    def test_create_session_research_id_matches_documented_form(self):
        session = create_sample_session(self.manager)
        # RS-YYYYMMDD-NNN, per RESEARCH_SESSION.md Section 6.
        prefix, date_stamp, sequence = session.research_id.split("-")
        self.assertEqual(prefix, "RS")
        self.assertEqual(len(date_stamp), 8)
        self.assertEqual(len(sequence), 3)

    def test_created_session_is_retrievable(self):
        session = create_sample_session(self.manager)
        self.assertIs(self.manager.get_session(session.research_id), session)


class TestGetSession(unittest.TestCase):
    def setUp(self):
        self.manager = SessionManager()

    def test_get_session_raises_for_unknown_id(self):
        with self.assertRaises(SessionNotFoundError):
            self.manager.get_session("RS-00000000-999")


class TestUpdateStatus(unittest.TestCase):
    def setUp(self):
        self.manager = SessionManager()
        self.session = create_sample_session(self.manager)

    def test_update_status_moves_session_forward(self):
        self.manager.update_status(self.session.research_id, SessionStatus.PLANNING)
        self.assertEqual(
            self.manager.get_session(self.session.research_id).overall_status,
            SessionStatus.PLANNING,
        )

    def test_update_status_rejects_illegal_transition(self):
        with self.assertRaises(InvalidSessionTransitionError):
            self.manager.update_status(self.session.research_id, SessionStatus.COMPLETED)

    def test_update_status_raises_for_unknown_session(self):
        with self.assertRaises(SessionNotFoundError):
            self.manager.update_status("RS-00000000-999", SessionStatus.PLANNING)

    def test_update_status_can_set_current_stage(self):
        self.manager.update_status(
            self.session.research_id,
            SessionStatus.PLANNING,
            current_stage="Planning Research Input",
        )
        session = self.manager.get_session(self.session.research_id)
        self.assertEqual(session.current_stage, "Planning Research Input")


class TestFinishSession(unittest.TestCase):
    def setUp(self):
        self.manager = SessionManager()
        self.session = create_sample_session(self.manager)

    def _advance_to_waiting_human_review(self):
        for status in [
            SessionStatus.PLANNING,
            SessionStatus.COLLECTING,
            SessionStatus.ASSEMBLING,
            SessionStatus.VERIFYING,
            SessionStatus.WAITING_HUMAN_REVIEW,
        ]:
            self.manager.update_status(self.session.research_id, status)

    def test_finish_session_completes_from_waiting_human_review(self):
        self._advance_to_waiting_human_review()
        finished = self.manager.finish_session(self.session.research_id)
        self.assertEqual(finished.overall_status, SessionStatus.COMPLETED)
        self.assertIsNotNone(finished.end_time)

    def test_finish_session_rejected_before_waiting_human_review(self):
        with self.assertRaises(InvalidSessionTransitionError):
            self.manager.finish_session(self.session.research_id)


class TestCancelSession(unittest.TestCase):
    def setUp(self):
        self.manager = SessionManager()
        self.session = create_sample_session(self.manager)

    def test_cancel_session_from_created(self):
        cancelled = self.manager.cancel_session(self.session.research_id)
        self.assertEqual(cancelled.overall_status, SessionStatus.CANCELLED)
        self.assertIsNotNone(cancelled.end_time)

    def test_cancel_session_from_mid_lifecycle(self):
        self.manager.update_status(self.session.research_id, SessionStatus.PLANNING)
        self.manager.update_status(self.session.research_id, SessionStatus.COLLECTING)
        cancelled = self.manager.cancel_session(self.session.research_id)
        self.assertEqual(cancelled.overall_status, SessionStatus.CANCELLED)

    def test_cancel_session_already_terminal_raises(self):
        self.manager.cancel_session(self.session.research_id)
        with self.assertRaises(InvalidSessionTransitionError):
            self.manager.cancel_session(self.session.research_id)


class TestRevisionLoopThroughManager(unittest.TestCase):
    def setUp(self):
        self.manager = SessionManager()
        self.session = create_sample_session(self.manager)
        for status in [
            SessionStatus.PLANNING,
            SessionStatus.COLLECTING,
            SessionStatus.ASSEMBLING,
            SessionStatus.VERIFYING,
            SessionStatus.WAITING_HUMAN_REVIEW,
        ]:
            self.manager.update_status(self.session.research_id, status)

    def test_needs_revision_sends_session_back_to_collecting(self):
        self.manager.update_status(self.session.research_id, SessionStatus.COLLECTING)
        session = self.manager.get_session(self.session.research_id)
        self.assertEqual(session.overall_status, SessionStatus.COLLECTING)
        self.assertFalse(session.is_terminal)

    def test_session_can_reach_completed_after_a_revision_loop_pass(self):
        self.manager.update_status(self.session.research_id, SessionStatus.COLLECTING)
        for status in [
            SessionStatus.ASSEMBLING,
            SessionStatus.VERIFYING,
            SessionStatus.WAITING_HUMAN_REVIEW,
        ]:
            self.manager.update_status(self.session.research_id, status)
        finished = self.manager.finish_session(self.session.research_id)
        self.assertEqual(finished.overall_status, SessionStatus.COMPLETED)


class TestSessionManagerIsolation(unittest.TestCase):
    def test_two_managers_do_not_share_sessions(self):
        manager_one = SessionManager()
        manager_two = SessionManager()
        session = create_sample_session(manager_one)
        with self.assertRaises(SessionNotFoundError):
            manager_two.get_session(session.research_id)


if __name__ == "__main__":
    unittest.main()
