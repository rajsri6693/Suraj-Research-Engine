"""Unit tests for research_engine.session.research_session."""

import unittest
from datetime import datetime, timedelta

from research_engine.session.research_session import (
    InvalidSessionTransitionError,
    ResearchSession,
    SessionStatus,
    is_valid_transition,
)


def make_session(**overrides) -> ResearchSession:
    defaults = dict(
        research_id="RS-20260709-001",
        research_topic="Full analysis ahead of quarterly results next week.",
        research_profile="Sample Manufacturing Ltd (SMFG, NSE)",
        research_category="Stock Analysis",
        start_time=datetime(2026, 7, 9, 9, 0, 0),
    )
    defaults.update(overrides)
    return ResearchSession(**defaults)


class TestResearchSessionConstruction(unittest.TestCase):
    def test_defaults_to_created_status(self):
        session = make_session()
        self.assertEqual(session.overall_status, SessionStatus.CREATED)
        self.assertIsNone(session.current_stage)
        self.assertIsNone(session.end_time)

    def test_tracks_exactly_one_research_input(self):
        session = make_session()
        self.assertEqual(session.research_profile, "Sample Manufacturing Ltd (SMFG, NSE)")
        self.assertEqual(session.research_category, "Stock Analysis")
        self.assertEqual(
            session.research_topic,
            "Full analysis ahead of quarterly results next week.",
        )

    def test_rejects_empty_research_id(self):
        with self.assertRaises(ValueError):
            make_session(research_id="   ")

    def test_rejects_empty_research_topic(self):
        with self.assertRaises(ValueError):
            make_session(research_topic="")

    def test_rejects_empty_research_profile(self):
        with self.assertRaises(ValueError):
            make_session(research_profile="   ")

    def test_rejects_empty_research_category(self):
        with self.assertRaises(ValueError):
            make_session(research_category="")


class TestIsValidTransition(unittest.TestCase):
    def test_full_forward_path_is_valid_one_step_at_a_time(self):
        ordered = [
            SessionStatus.CREATED,
            SessionStatus.PLANNING,
            SessionStatus.COLLECTING,
            SessionStatus.ASSEMBLING,
            SessionStatus.VERIFYING,
            SessionStatus.WAITING_HUMAN_REVIEW,
            SessionStatus.COMPLETED,
        ]
        for current, nxt in zip(ordered, ordered[1:]):
            self.assertTrue(is_valid_transition(current, nxt), f"{current} -> {nxt}")

    def test_skipping_a_stage_is_invalid(self):
        self.assertFalse(is_valid_transition(SessionStatus.CREATED, SessionStatus.COLLECTING))
        self.assertFalse(is_valid_transition(SessionStatus.PLANNING, SessionStatus.VERIFYING))

    def test_moving_backward_off_the_one_permitted_exception_is_invalid(self):
        self.assertFalse(
            is_valid_transition(SessionStatus.VERIFYING, SessionStatus.COLLECTING)
        )
        self.assertFalse(
            is_valid_transition(SessionStatus.ASSEMBLING, SessionStatus.PLANNING)
        )

    def test_revision_loop_backward_transition_is_valid(self):
        self.assertTrue(
            is_valid_transition(
                SessionStatus.WAITING_HUMAN_REVIEW, SessionStatus.COLLECTING
            )
        )

    def test_failed_and_cancelled_reachable_from_any_active_status(self):
        active_statuses = [
            SessionStatus.CREATED,
            SessionStatus.PLANNING,
            SessionStatus.COLLECTING,
            SessionStatus.ASSEMBLING,
            SessionStatus.VERIFYING,
            SessionStatus.WAITING_HUMAN_REVIEW,
        ]
        for status in active_statuses:
            self.assertTrue(is_valid_transition(status, SessionStatus.FAILED))
            self.assertTrue(is_valid_transition(status, SessionStatus.CANCELLED))

    def test_terminal_statuses_never_change_again(self):
        terminal_statuses = [
            SessionStatus.COMPLETED,
            SessionStatus.FAILED,
            SessionStatus.CANCELLED,
        ]
        every_status = list(SessionStatus)
        for terminal in terminal_statuses:
            for candidate in every_status:
                self.assertFalse(
                    is_valid_transition(terminal, candidate),
                    f"{terminal} -> {candidate} should be blocked once terminal",
                )

    def test_same_status_refinement_is_valid_while_active(self):
        self.assertTrue(is_valid_transition(SessionStatus.COLLECTING, SessionStatus.COLLECTING))


class TestResearchSessionTransitionTo(unittest.TestCase):
    def test_valid_transition_updates_status(self):
        session = make_session()
        session.transition_to(SessionStatus.PLANNING)
        self.assertEqual(session.overall_status, SessionStatus.PLANNING)

    def test_invalid_transition_raises_and_leaves_status_unchanged(self):
        session = make_session()
        with self.assertRaises(InvalidSessionTransitionError):
            session.transition_to(SessionStatus.COLLECTING)
        self.assertEqual(session.overall_status, SessionStatus.CREATED)

    def test_current_stage_can_be_set_alongside_a_status_change(self):
        session = make_session()
        session.transition_to(SessionStatus.PLANNING, current_stage="Planning Research Input")
        self.assertEqual(session.current_stage, "Planning Research Input")

    def test_current_stage_can_advance_without_changing_overall_status(self):
        session = make_session()
        session.transition_to(SessionStatus.PLANNING)
        session.transition_to(SessionStatus.COLLECTING)
        session.transition_to(
            SessionStatus.COLLECTING, current_stage="Stage 2 - Identify Required Collectors"
        )
        self.assertEqual(session.overall_status, SessionStatus.COLLECTING)
        self.assertEqual(session.current_stage, "Stage 2 - Identify Required Collectors")

        session.transition_to(
            SessionStatus.COLLECTING, current_stage="Stage 3 - Run Collectors in Parallel"
        )
        self.assertEqual(session.overall_status, SessionStatus.COLLECTING)
        self.assertEqual(session.current_stage, "Stage 3 - Run Collectors in Parallel")

    def test_reaching_a_terminal_status_sets_end_time(self):
        session = make_session()
        session.transition_to(SessionStatus.FAILED)
        self.assertIsNotNone(session.end_time)
        self.assertTrue(session.is_terminal)

    def test_non_terminal_transition_leaves_end_time_unset(self):
        session = make_session()
        session.transition_to(SessionStatus.PLANNING)
        self.assertIsNone(session.end_time)
        self.assertFalse(session.is_terminal)

    def test_revision_loop_transition_does_not_set_end_time(self):
        session = make_session()
        for status in [
            SessionStatus.PLANNING,
            SessionStatus.COLLECTING,
            SessionStatus.ASSEMBLING,
            SessionStatus.VERIFYING,
            SessionStatus.WAITING_HUMAN_REVIEW,
        ]:
            session.transition_to(status)
        session.transition_to(SessionStatus.COLLECTING)
        self.assertEqual(session.overall_status, SessionStatus.COLLECTING)
        self.assertIsNone(session.end_time)
        self.assertFalse(session.is_terminal)

    def test_cannot_transition_once_terminal(self):
        session = make_session()
        session.transition_to(SessionStatus.CANCELLED)
        with self.assertRaises(InvalidSessionTransitionError):
            session.transition_to(SessionStatus.PLANNING)


class TestResearchSessionDuration(unittest.TestCase):
    def test_duration_reflects_elapsed_time_while_active(self):
        start = datetime.now() - timedelta(minutes=5)
        session = make_session(start_time=start)
        self.assertGreaterEqual(session.duration, timedelta(minutes=5))

    def test_duration_is_fixed_once_terminal(self):
        start = datetime(2026, 7, 9, 9, 0, 0)
        session = make_session(start_time=start)
        session.transition_to(SessionStatus.FAILED)
        first_reading = session.duration
        second_reading = session.duration
        self.assertEqual(first_reading, second_reading)
        self.assertEqual(first_reading, session.end_time - start)


if __name__ == "__main__":
    unittest.main()
