"""
Research Planner

Implements ResearchPlanner, the decision-making component defined in
project_documentation/RESEARCH_PLANNER.md. It converts Research Input
into a Human-readable Research Plan.

It is a pure decision engine: it never performs research, never calls
APIs, never calls collectors, never calls the Research Workflow, never
accesses a database, never verifies knowledge, and never generates
scripts or videos. It has no dependency on any other Research Engine
module — only the Python standard library.
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from .research_plan import (
    CollectorMode,
    KnowledgeSection,
    PlannerStatus,
    ResearchCategory,
    ResearchDepth,
    ResearchPlan,
    ResearchPriority,
)


class InvalidResearchInputError(Exception):
    """Raised when Research Input does not satisfy
    project_documentation/RESEARCH_INPUT_STANDARD.md's Validity Rules, so
    no Research Plan can be produced."""


# Categories that require exactly one company identifier in Research
# Profile, per RESEARCH_INPUT_STANDARD.md's cardinality rules.
_SINGLE_COMPANY_CATEGORIES = frozenset(
    {
        ResearchCategory.MARKET_NEWS,
        ResearchCategory.STOCK_UPDATE,
        ResearchCategory.STOCK_ANALYSIS,
    }
)

# Categories whose default Research Depth is Deep Research and can never
# be downgraded to Quick Research by Research Topic wording, per
# RESEARCH_PLANNER.md Section 4 (Precedence).
_DEEP_RESEARCH_CATEGORIES = frozenset(
    {
        ResearchCategory.STOCK_ANALYSIS,
        ResearchCategory.SECTOR_ANALYSIS,
        ResearchCategory.COMPARISON,
    }
)

# Categories whose default Research Priority is High and can never be
# lowered, per RESEARCH_PLANNER.md Section 6.
_HIGH_PRIORITY_CATEGORIES = frozenset(
    {ResearchCategory.MARKET_NEWS, ResearchCategory.STOCK_UPDATE}
)

# Research Topic wording that signals a snapshot rather than an analysis,
# per RESEARCH_PLANNER.md Section 4 (Quick Research).
_QUICK_SIGNAL_PHRASES: Tuple[str, ...] = (
    "latest",
    "today",
    "current price",
    "what happened",
)

# Research Topic wording that signals breadth or judgment, per
# RESEARCH_PLANNER.md Section 4 (Deep Research). Upgrades a Quick-default
# category to Deep Research; never downgrades a Deep-default category.
_DEEP_SIGNAL_PHRASES: Tuple[str, ...] = (
    "full analysis",
    "compare",
    "outlook",
    "risks",
    "should we",
)

# Research Topic wording that signals urgency, per RESEARCH_PLANNER.md
# Section 6. Raises priority to High; never lowers it.
_URGENCY_SIGNAL_PHRASES: Tuple[str, ...] = ("today", "breaking", "just announced")

# Required Knowledge Sections per Research Category, per
# RESEARCH_PLANNER.md Section 5 (Knowledge Selection Rules). This table
# holds only the category-driven, unconditional portion of that section —
# the Research-Topic-conditional additions it also describes (Government
# Policies for policy-driven Market News, Corporate Actions for a
# corporate-action-driven Stock Update) are not applied here, because
# IMP-02 scopes this determination to Research Category, Research
# Profile, and the Knowledge Model only, excluding Research Topic.
_REQUIRED_SECTIONS_BY_CATEGORY: Dict[ResearchCategory, List[KnowledgeSection]] = {
    ResearchCategory.MARKET_NEWS: [
        KnowledgeSection.COMPANY_INFORMATION,
        KnowledgeSection.MARKET_NEWS,
        KnowledgeSection.SOURCES,
        KnowledgeSection.METADATA,
    ],
    ResearchCategory.STOCK_UPDATE: [
        KnowledgeSection.COMPANY_INFORMATION,
        KnowledgeSection.MARKET_DATA,
        KnowledgeSection.HISTORICAL_PRICE_OHLC,
        KnowledgeSection.SOURCES,
        KnowledgeSection.METADATA,
    ],
    ResearchCategory.STOCK_ANALYSIS: [
        KnowledgeSection.COMPANY_INFORMATION,
        KnowledgeSection.BUSINESS_OVERVIEW,
        KnowledgeSection.FINANCIAL_INFORMATION,
        KnowledgeSection.PRODUCTS_SERVICES,
        KnowledgeSection.SHAREHOLDING,
        KnowledgeSection.MANAGEMENT,
        KnowledgeSection.RISKS,
        KnowledgeSection.MARKET_DATA,
        KnowledgeSection.HISTORICAL_PRICE_OHLC,
        KnowledgeSection.TECHNICAL_ANALYSIS,
        KnowledgeSection.SOURCES,
        KnowledgeSection.METADATA,
    ],
    ResearchCategory.SECTOR_ANALYSIS: [
        KnowledgeSection.SECTOR_INFORMATION,
        KnowledgeSection.GOVERNMENT_POLICIES,
        KnowledgeSection.COMPANY_INFORMATION,
        KnowledgeSection.BUSINESS_OVERVIEW,
        KnowledgeSection.COMPETITORS,
        KnowledgeSection.SOURCES,
        KnowledgeSection.METADATA,
    ],
    ResearchCategory.COMPARISON: [
        KnowledgeSection.COMPANY_INFORMATION,
        KnowledgeSection.BUSINESS_OVERVIEW,
        KnowledgeSection.FINANCIAL_INFORMATION,
        KnowledgeSection.COMPETITORS,
        KnowledgeSection.MARKET_DATA,
        KnowledgeSection.SOURCES,
        KnowledgeSection.METADATA,
    ],
}


class ResearchPlanner:
    """Converts Research Input into a Human-readable Research Plan.

    Pure decision engine: every method here only reasons over its
    arguments and returns a result. Nothing is fetched, called, saved,
    or verified.
    """

    _ID_PREFIX = "RP"

    def __init__(self) -> None:
        self._sequence: int = 0

    def create_research_plan(
        self,
        research_profile: Union[str, List[str]],
        research_category: Union[ResearchCategory, str],
        research_topic: str,
    ) -> ResearchPlan:
        """Create Research Plan.

        Input: Research Profile, Research Category, Research Topic, per
        RESEARCH_PLANNER.md Section 2 (Planner Input).
        Output: a fully formed ResearchPlan, per Section 3.

        Raises InvalidResearchInputError if the input does not satisfy
        RESEARCH_INPUT_STANDARD.md's Validity Rules — no partial or
        invalid Research Input ever produces a plan.
        """
        category = self._normalize_category(research_category)
        profile = self._normalize_profile(research_profile)
        self._validate_input(profile, category, research_topic)

        depth, depth_reason = self.determine_research_depth(category, research_topic)
        priority, priority_reason = self.determine_research_priority(
            category, research_topic
        )
        required_sections = self.determine_required_knowledge_sections(
            category, profile
        )
        collector_mode = self.determine_collector_mode()

        self._sequence += 1
        return ResearchPlan(
            research_id=self._generate_research_id(),
            research_profile=profile,
            research_category=category,
            research_topic=research_topic,
            research_depth=depth,
            depth_reason=depth_reason,
            research_priority=priority,
            priority_reason=priority_reason,
            required_knowledge_sections=required_sections,
            collector_mode=collector_mode,
            planner_status=PlannerStatus.CREATED,
            created_time=datetime.now(),
        )

    def determine_research_depth(
        self, research_category: ResearchCategory, research_topic: str
    ) -> Tuple[ResearchDepth, str]:
        """Determine Research Depth: Quick Research or Deep Research.

        Implements RESEARCH_PLANNER.md Section 4 exactly: Research
        Category sets the default; Research Topic wording can upgrade a
        Quick-default category to Deep, but never downgrades a
        Deep-default category to Quick.
        """
        if research_category in _DEEP_RESEARCH_CATEGORIES:
            return (
                ResearchDepth.DEEP,
                f"{research_category.value} is always Deep Research.",
            )

        matched_signal = self._first_match(research_topic, _DEEP_SIGNAL_PHRASES)
        if matched_signal is not None:
            return (
                ResearchDepth.DEEP,
                f"{research_category.value} defaults to Quick Research, but the "
                f'topic\'s wording ("{matched_signal}") signals breadth, which '
                "upgrades it to Deep Research.",
            )
        return (
            ResearchDepth.QUICK,
            f"{research_category.value} is Quick Research by default, and the "
            "topic shows no signal of needing broader analysis.",
        )

    def determine_research_priority(
        self, research_category: ResearchCategory, research_topic: str
    ) -> Tuple[ResearchPriority, str]:
        """Determine Research Priority: High, Medium, or Low.

        Implements RESEARCH_PLANNER.md Section 6 exactly: Research
        Category sets the default; Research Topic wording can raise the
        default toward High, but never lowers it.
        """
        if research_category in _HIGH_PRIORITY_CATEGORIES:
            return (
                ResearchPriority.HIGH,
                f"{research_category.value} is always High priority.",
            )

        matched_signal = self._first_match(research_topic, _URGENCY_SIGNAL_PHRASES)
        if matched_signal is not None:
            return (
                ResearchPriority.HIGH,
                f"{research_category.value} defaults to a lower priority, but the "
                f'topic\'s wording ("{matched_signal}") signals urgency, which '
                "raises it to High.",
            )

        if research_category == ResearchCategory.STOCK_ANALYSIS:
            return (
                ResearchPriority.MEDIUM,
                "Stock Analysis defaults to Medium priority, and the topic shows "
                "no urgency signal.",
            )

        return (
            ResearchPriority.LOW,
            f"{research_category.value} defaults to Low priority, and the topic "
            "shows no urgency signal.",
        )

    def determine_required_knowledge_sections(
        self, research_category: ResearchCategory, research_profile: List[str]
    ) -> List[KnowledgeSection]:
        """Determine Required Knowledge Sections.

        Based ONLY on Research Category, Research Profile, and the
        Knowledge Model, per IMP-02. Research Profile is accepted for
        interface completeness — the current RESEARCH_PLANNER.md
        Knowledge Selection Rules select section *types* by Research
        Category alone; Research Profile's size instead determines how
        many times each section is collected (for example, once per
        company for Comparison), which is not reflected in this flat
        list of required section types.
        """
        del research_profile  # Unused by today's category-only selection rules.
        return list(_REQUIRED_SECTIONS_BY_CATEGORY[research_category])

    def determine_collector_mode(self) -> CollectorMode:
        """Determine Collector Mode.

        RESEARCH_PLANNER.md Section 7 defines exactly one Research Mode —
        Parallel Collectors — so this always returns CollectorMode.PARALLEL.
        """
        return CollectorMode.PARALLEL

    def _validate_input(
        self,
        research_profile: List[str],
        research_category: ResearchCategory,
        research_topic: str,
    ) -> None:
        """Enforce RESEARCH_INPUT_STANDARD.md's Validity Rules."""
        if research_topic is None or not research_topic.strip():
            raise InvalidResearchInputError("Research Topic must not be empty.")

        if not research_profile or any(
            not isinstance(identifier, str) or not identifier.strip()
            for identifier in research_profile
        ):
            raise InvalidResearchInputError(
                "Research Profile must contain at least one non-empty company "
                "identifier."
            )

        if (
            research_category in _SINGLE_COMPANY_CATEGORIES
            and len(research_profile) != 1
        ):
            raise InvalidResearchInputError(
                f"{research_category.value} requires exactly one company "
                "identifier in Research Profile."
            )

        if (
            research_category == ResearchCategory.COMPARISON
            and len(research_profile) < 2
        ):
            raise InvalidResearchInputError(
                "Comparison requires at least two company identifiers in "
                "Research Profile."
            )
        # Sector Analysis requires at least one identifier, already
        # enforced by the empty-profile check above.

    @staticmethod
    def _normalize_category(
        research_category: Union[ResearchCategory, str]
    ) -> ResearchCategory:
        if isinstance(research_category, ResearchCategory):
            return research_category
        try:
            return ResearchCategory(research_category)
        except ValueError as exc:
            raise InvalidResearchInputError(
                f"'{research_category}' is not a valid Research Category."
            ) from exc

    @staticmethod
    def _normalize_profile(research_profile: Union[str, List[str]]) -> List[str]:
        if isinstance(research_profile, str):
            return [research_profile]
        return list(research_profile)

    @staticmethod
    def _first_match(text: str, phrases: Tuple[str, ...]) -> Optional[str]:
        lowered = text.lower()
        for phrase in phrases:
            if phrase in lowered:
                return phrase
        return None

    def _generate_research_id(self) -> str:
        date_stamp = datetime.now().strftime("%Y%m%d")
        return f"{self._ID_PREFIX}-{date_stamp}-{self._sequence:03d}"
