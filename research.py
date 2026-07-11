"""
Research Engine Runtime (CLI)

Production entry point for the Research Engine, per
Claude-Prompts/IMP_10I_Research_Runtime.md and its follow-up
architecture refactor:

User Input -> Research Planner -> Research Workflow -> Collectors ->
API Manager -> Verification -> Human Review -> Approval -> Telegram
Notification -> Completion

research_engine.integration.integration_engine.IntegrationEngine is
the single orchestration path: it already connects Research Planner's
output through Research Workflow, Collectors (via the existing
Collector Registry/Factory), Research Result Assembly, Knowledge
Verification, and Chart Generation. This module only adds thin
bootstrap logic around it -- building a live APIManager-bound
CollectorRegistry/Factory to inject (IntegrationEngine's own optional
`registry`/`factory` constructor parameters), an interactive Human
Review front end, and wiring to Approval and Telegram Notification.
No orchestration is re-implemented here; this module never calls a
Collector directly, and never touches API Manager routing/failover
logic itself.

This is a separate, additional entry point alongside main.py --
main.py's own Knowledge Viewer is untouched and remains reachable
exactly as before (`python main.py`).
"""

from __future__ import annotations

import os
import re
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple

from research_database.database_manager import DatabaseManager
from research_engine.api_manager import APIManager
from research_engine.api_manager.api_settings import load_env_file
from research_engine.approval.approval_service import ApprovalService
from research_engine.integration.integration_engine import IntegrationEngine, IntegrationResult
from research_engine.notifications.telegram_notification import (
    TelegramConfig,
    TelegramNotificationService,
)
from research_engine.planner.research_plan import ResearchCategory
from research_engine.planner.research_planner import (
    InvalidResearchInputError,
    ResearchPlanner,
)
from research_engine.review.human_review import HumanReview, InvalidReviewError
from research_engine.runtime import build_collector_factory

_BANNER = "=" * 34
_TITLE = "Suraj Research Engine"

# Matches the chart-request wording Research Planner itself detects
# (\bcharts?\b) plus an optional leading "with" -- used only to derive
# a clean Research Profile identifier; the raw Research Topic string
# passed to ResearchPlanner (and on into every collector via
# IntegrationEngine.run()) is never altered.
_CHART_WORDING_PATTERN = re.compile(r"\s*\bwith\s+charts?\b|\s*\bcharts?\b", re.IGNORECASE)

_DECISION_LABELS = {
    "A": "Approve",
    "R": "Reject",
    "V": "Request Revision",
    "S": "Skip",
}


def derive_profile_and_category(research_topic: str) -> Tuple[List[str], ResearchCategory]:
    """Derive Research Profile and Research Category from a raw
    Research Topic string, per IMP-10I's User Input examples (bare
    symbols like "BEL", "BEL with chart", "NIFTY 50"). Research
    Planner itself only detects Chart Required from the topic's own
    wording (determine_chart_required); it does not derive Research
    Profile or Research Category, since RESEARCH_PLANNER.md defines
    those as separate Planner Input the caller supplies. Every example
    topic names exactly one company/index, so this always derives a
    single-item Research Profile and defaults to Stock Analysis -- the
    broadest single-company Research Category, matching every
    example's own single-symbol shape."""
    cleaned = _CHART_WORDING_PATTERN.sub("", research_topic).strip()
    symbol = cleaned or research_topic.strip()
    return [symbol], ResearchCategory.STOCK_ANALYSIS


def print_banner(print_fn: Callable[[str], None] = print) -> None:
    print_fn(_BANNER)
    print_fn(_TITLE)
    print_fn(_BANNER)


def prompt_research_topic(input_fn: Callable[[str], str] = input) -> str:
    return input_fn("Enter Research Topic:\n> ").strip()


def prompt_reviewer_decision(
    verification_report: Any,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
) -> Tuple[str, str, str]:
    """Prompt the console operator for a Human Review decision.
    Returns (decision_code, reviewer_name, notes) -- decision_code is
    one of "A"/"R"/"V"/"S", defaulting to "S" (Skip) for anything else
    typed, so an unrecognized response never silently approves."""
    print_fn("\nVerified sections eligible for review:")
    for section in verification_report.verified_sections:
        print_fn(f"  - {section.value}")
    reviewer = input_fn("Reviewed by: ").strip() or "console-operator"
    raw_decision = input_fn(
        "Decision [A]pprove / [R]eject / Re[V]ision / [S]kip: "
    ).strip().upper()
    decision_code = raw_decision if raw_decision in _DECISION_LABELS else "S"
    notes = input_fn("Notes (optional): ").strip()
    return decision_code, reviewer, notes


def apply_review_decision(
    human_review: HumanReview,
    verification_report: Any,
    decision_code: str,
    reviewer: str,
    notes: str,
) -> Any:
    """Call the HumanReview method matching `decision_code` against
    every Verified section -- the runtime's own interactive front end
    for the existing, unmodified Human Review module."""
    sections = list(verification_report.verified_sections)
    action = {
        "A": human_review.approve,
        "R": human_review.reject,
        "V": human_review.request_revision,
        "S": human_review.skip,
    }.get(decision_code, human_review.skip)
    return action(verification_report, sections, reviewer, notes)


def build_telegram_service(
    env: Optional[Dict[str, str]] = None
) -> TelegramNotificationService:
    """Build a TelegramNotificationService from the environment's
    TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID -- enabled only when both are
    actually configured, matching TelegramConfig's own default-disabled,
    fail-soft behavior otherwise (research_engine/notifications/
    telegram_notification.py, unmodified)."""
    environment = env if env is not None else os.environ
    bot_token = environment.get("TELEGRAM_BOT_TOKEN") or None
    chat_id = environment.get("TELEGRAM_CHAT_ID") or None
    config = TelegramConfig(
        enabled=bool(bot_token and chat_id), bot_token=bot_token, chat_id=chat_id
    )
    return TelegramNotificationService(config)


def run_research_session(
    research_topic: str,
    *,
    database_manager: Optional[DatabaseManager] = None,
    api_manager: Optional[APIManager] = None,
    notifier: Optional[TelegramNotificationService] = None,
    input_fn: Callable[[str], str] = input,
    print_fn: Callable[[str], None] = print,
) -> Dict[str, Any]:
    """Run one complete Research Session end to end, per IMP-10I's
    Workflow order: Research Planner -> IntegrationEngine.run()
    (Research Workflow -> Collectors -> API Manager -> Research Result
    Assembly -> Knowledge Verification -> Chart Generation) -> Human
    Review -> Approval -> Telegram Notification -> Completion.

    IntegrationEngine is the single orchestration path -- this
    function never re-implements any of its stage sequencing; it only
    builds the one thing IntegrationEngine's own default construction
    cannot provide (a live-APIManager-bound CollectorFactory) and
    drives the three stages that remain the caller's own
    responsibility (Human Review's actual decision, Approval, Telegram).

    Never raises for an ordinary, handled failure -- Invalid Topic,
    an API/collector failure, an SQLite failure, a Telegram failure, or
    an unexpected exception at any single stage are all reported in
    the returned summary dict's "error" field instead, per IMP-10I's
    Error Handling section, so a caller (this module's own main(), or
    a test) always gets a well-formed result to act on."""
    summary: Dict[str, Any] = {
        "research_topic": research_topic,
        "stage_reached": "Start",
        "success": False,
        "error": None,
    }
    try:
        research_profile, research_category = derive_profile_and_category(research_topic)

        print_fn("Planning research...")
        try:
            plan = ResearchPlanner().create_research_plan(
                research_profile=research_profile,
                research_category=research_category,
                research_topic=research_topic,
            )
        except InvalidResearchInputError as error:
            summary["error"] = f"Invalid Research Topic: {error}"
            return summary
        summary["stage_reached"] = "Planned"
        summary["research_plan"] = plan

        print_fn("Running collectors through the API Manager...")
        factory = build_collector_factory(api_manager or APIManager())
        engine = IntegrationEngine(factory=factory)
        integration_result: IntegrationResult = engine.run(plan)
        summary["stage_reached"] = "Collected"
        summary["integration_result"] = integration_result

        verification_report = integration_result.verification_report
        print_fn(f"Verification: {verification_report.overall_status.value}")
        summary["stage_reached"] = "Verified"

        if not verification_report.verified_sections:
            print_fn("No sections passed Verification; nothing is eligible for Human Review.")
            summary["success"] = True
            summary["stage_reached"] = "Completed (nothing to review)"
            return summary

        print_fn("Awaiting Human Review...")
        human_review = HumanReview()
        decision_code, reviewer, notes = prompt_reviewer_decision(
            verification_report, input_fn, print_fn
        )
        try:
            review_result = apply_review_decision(
                human_review, verification_report, decision_code, reviewer, notes
            )
        except InvalidReviewError as error:
            summary["error"] = f"Human Review failed: {error}"
            return summary
        summary["review_result"] = review_result
        summary["stage_reached"] = "Reviewed"
        print_fn(f"Review Decision: {_DECISION_LABELS.get(decision_code, 'Skip')}")

        print_fn("Processing Approval...")
        approval_service = ApprovalService(
            database_manager=database_manager or DatabaseManager(),
            notifier=notifier or build_telegram_service(),
        )
        outcome = approval_service.process(
            review_result,
            research_topic=plan.research_topic,
            research_category=plan.research_category.value,
            chart_available=integration_result.review_package.chart_available,
            chart_type=integration_result.review_package.chart_type,
        )
        summary["approval_outcome"] = outcome
        summary["stage_reached"] = "Completed"
        summary["success"] = True
        print_fn(f"Completion: {outcome.reason}")
        return summary
    except Exception as error:  # pragma: no cover - defensive top-level catch
        summary["error"] = (
            f"Unexpected error at stage '{summary['stage_reached']}': "
            f"{type(error).__name__}: {error}"
        )
        return summary


def main(
    input_fn: Callable[[str], str] = input, print_fn: Callable[[str], None] = print
) -> int:
    load_env_file(".env")
    print_banner(print_fn)
    topic = prompt_research_topic(input_fn)
    summary = run_research_session(topic, input_fn=input_fn, print_fn=print_fn)

    print_fn("")
    if summary["success"]:
        print_fn(f"SUCCESS -- {summary['stage_reached']}.")
        return 0
    print_fn(f"FAILED -- {summary.get('error') or 'Unknown error.'}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
