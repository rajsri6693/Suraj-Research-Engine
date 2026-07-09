"""
Research Plan

Implements the ResearchPlan data model defined in
project_documentation/RESEARCH_PLANNER.md Section 3 (Planner Output). A
ResearchPlan is a plain-language artifact — not code, not a database
record — produced by ResearchPlanner and handed to Research Workflow.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List


class ResearchCategory(Enum):
    """The fixed set of Research Categories, per
    project_documentation/RESEARCH_INPUT_STANDARD.md."""

    MARKET_NEWS = "Market News"
    STOCK_UPDATE = "Stock Update"
    STOCK_ANALYSIS = "Stock Analysis"
    SECTOR_ANALYSIS = "Sector Analysis"
    COMPARISON = "Comparison"


class ResearchDepth(Enum):
    """Research Depth Rules, per RESEARCH_PLANNER.md Section 4."""

    QUICK = "Quick Research"
    DEEP = "Deep Research"


class ResearchPriority(Enum):
    """Research Priority, per RESEARCH_PLANNER.md Section 6."""

    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class KnowledgeSection(Enum):
    """The 18 Knowledge Sections defined in project_documentation/KNOWLEDGE_MODEL.md."""

    COMPANY_INFORMATION = "Company Information"
    BUSINESS_OVERVIEW = "Business Overview"
    PRODUCTS_SERVICES = "Products & Services"
    FINANCIAL_INFORMATION = "Financial Information"
    ORDERS_CONTRACTS = "Orders & Contracts"
    SHAREHOLDING = "Shareholding"
    MANAGEMENT = "Management"
    COMPETITORS = "Competitors"
    RISKS = "Risks"
    MARKET_NEWS = "Market News"
    SECTOR_INFORMATION = "Sector Information"
    GOVERNMENT_POLICIES = "Government Policies"
    MARKET_DATA = "Market Data"
    HISTORICAL_PRICE_OHLC = "Historical Price (OHLC)"
    TECHNICAL_ANALYSIS = "Technical Analysis"
    CORPORATE_ACTIONS = "Corporate Actions"
    SOURCES = "Sources"
    METADATA = "Metadata"


class CollectorMode(Enum):
    """Research Mode, per RESEARCH_PLANNER.md Section 7.

    Parallel Collectors is the only mode RESEARCH_PLANNER.md defines —
    there is no sequential mode in the architecture.
    """

    PARALLEL = "Parallel"


class PlannerStatus(Enum):
    """The status of a ResearchPlan artifact itself.

    A ResearchPlan only ever comes into existence fully formed — invalid
    Research Input never produces a ResearchPlan at all (see
    ResearchPlanner.create_research_plan) — so Created is the only status
    a ResearchPlan can carry today. The enum exists so a status field is
    present on every plan, per IMP-02's Research Plan field list.
    """

    CREATED = "Created"


@dataclass
class ResearchPlan:
    """A Human-readable Research Plan, per RESEARCH_PLANNER.md Section 3.

    Every field here is required — a ResearchPlan is never partially
    constructed. depth_reason and priority_reason capture the "why it was
    chosen" text RESEARCH_PLANNER.md requires the plan to state alongside
    Research Depth and Research Priority.
    """

    research_id: str
    research_profile: List[str]
    research_category: ResearchCategory
    research_topic: str
    research_depth: ResearchDepth
    depth_reason: str
    research_priority: ResearchPriority
    priority_reason: str
    required_knowledge_sections: List[KnowledgeSection]
    collector_mode: CollectorMode
    planner_status: PlannerStatus
    created_time: datetime

    def to_human_readable(self) -> str:
        """Render this plan in the plain-language form shown in
        RESEARCH_PLANNER.md Section 9 (Planner Output Example)."""
        profile_text = ", ".join(self.research_profile)
        sections_text = "\n".join(
            f"- {section.value}" for section in self.required_knowledge_sections
        )
        return (
            "Research Plan\n\n"
            f"Subject: {profile_text}\n"
            f"Category: {self.research_category.value}\n"
            f"Topic: {self.research_topic}\n\n"
            f"Research Depth: {self.research_depth.value}\n"
            f"Reason: {self.depth_reason}\n\n"
            f"Priority: {self.research_priority.value}\n"
            f"Reason: {self.priority_reason}\n\n"
            f"Required Knowledge Sections:\n{sections_text}\n\n"
            f"Research Mode: {self.collector_mode.value} Collectors\n"
            "Each section above is assigned to its own collector task. All\n"
            "collector tasks run concurrently; none depends on another's result.\n\n"
            "End of Plan."
        )
