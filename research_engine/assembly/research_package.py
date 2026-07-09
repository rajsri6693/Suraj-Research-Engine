"""
Research Package

Implements the ResearchPackage data model — the single, unified output of
Research Result Assembly, per
project_documentation/RESEARCH_RESULT_ASSEMBLY.md Section 3 (Assembly
Output).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

from research_engine.planner.research_plan import KnowledgeSection, ResearchCategory

from .collector_result import CollectorStatus


class SectionStatus(Enum):
    """The four Knowledge Section statuses a Research Package
    distinguishes, per RESEARCH_RESULT_ASSEMBLY.md Section 6 (Missing
    Section Handling). Never conflated."""

    COMPLETED = "Completed"
    FAILED = "Failed"
    MISSING = "Missing"
    SKIPPED = "Skipped"


class OverallCollectionStatus(Enum):
    """The aggregate Overall Collection Status for a whole Research
    Package, per RESEARCH_RESULT_ASSEMBLY.md Section 3."""

    COMPLETE = "Complete"
    PARTIAL = "Partial"
    FAILED = "Failed"


@dataclass
class AssembledSection:
    """One Knowledge Sections entry within a Research Package.

    Only a Completed entry carries collected_knowledge and sources;
    Failed, Missing, and Skipped entries never carry fabricated or
    placeholder content, per RESEARCH_RESULT_ASSEMBLY.md Section 6 — a
    Skipped entry's collected_knowledge/sources reflect whatever a prior
    pass's entry for this section already carried (which may itself be
    populated, if that prior entry was Completed).
    """

    knowledge_section: KnowledgeSection
    status: SectionStatus
    collected_knowledge: Optional[str]
    sources: List[str]
    collection_time: Optional[datetime]


@dataclass
class CollectorSummaryEntry:
    """One row of the Research Package's Collector Summary, per
    RESEARCH_RESULT_ASSEMBLY.md Section 7. One entry per collector
    triggered during this Assembly run — never one for a Skipped section,
    since no collector ran for it this run."""

    collector_name: str
    execution_status: CollectorStatus
    completion_time: datetime


@dataclass
class ResearchPackage:
    """The single, unified, Human-readable Research Package Research
    Result Assembly produces, per RESEARCH_RESULT_ASSEMBLY.md Section 3.

    research_id identifies this specific Package (one Assembly run may
    produce more than one Package for the same session, across Revision
    Loop passes); research_session is the Research ID of the Research
    Session this Package belongs to, per RESEARCH_SESSION.md.
    """

    research_id: str
    research_session: str
    research_topic: str
    research_profile: List[str]
    research_category: ResearchCategory
    knowledge_sections: List[AssembledSection]
    collector_summary: List[CollectorSummaryEntry]
    missing_sections: List[AssembledSection]
    overall_collection_status: OverallCollectionStatus
    collection_completed_time: datetime

    def to_human_readable(self) -> str:
        """Render this Package in the plain-language form shown in
        RESEARCH_RESULT_ASSEMBLY.md Section 9 (Research Package Example)."""
        profile_text = ", ".join(self.research_profile)
        sections_text = "\n".join(
            f"- {entry.knowledge_section.value} — {entry.status.value}"
            for entry in self.knowledge_sections
        )
        summary_text = "\n".join(
            f"| {row.collector_name} | {row.execution_status.value} | "
            f"{row.completion_time} |"
            for row in self.collector_summary
        )
        missing_text = "\n".join(
            f"- {entry.knowledge_section.value} — {entry.status.value}"
            for entry in self.missing_sections
        )
        return (
            "Research Package\n\n"
            f"Research Session: {self.research_session}\n"
            f"Research Topic: {self.research_topic}\n"
            f"Research Profile: {profile_text}\n"
            f"Research Category: {self.research_category.value}\n\n"
            f"Knowledge Sections:\n{sections_text}\n\n"
            f"Collector Summary:\n{summary_text}\n\n"
            f"Missing Sections:\n{missing_text or '(none)'}\n\n"
            f"Overall Collection Status: {self.overall_collection_status.value}\n"
            f"Collection Completed Time: {self.collection_completed_time}"
        )
