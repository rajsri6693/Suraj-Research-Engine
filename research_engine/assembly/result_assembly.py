"""
Research Result Assembly

Implements ResearchResultAssembly, per
project_documentation/RESEARCH_RESULT_ASSEMBLY.md. It combines Collector
Results into one unified Research Package.

It NEVER performs research, calls APIs, verifies knowledge, approves
knowledge, modifies collected knowledge, accesses a database, or
generates scripts or videos. Per IMP-04's Implementation Rules, it
depends only on Research Session and Research Plan (Workflow State is
permitted but not required by this implementation's design — see the
`previous_package` parameter below for how Revision Loop carry-forward is
handled without it).
"""

from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from research_engine.planner.research_plan import KnowledgeSection, ResearchPlan
from research_engine.session.research_session import ResearchSession

from .collector_result import CollectorResult, CollectorStatus
from .research_package import (
    AssembledSection,
    CollectorSummaryEntry,
    OverallCollectionStatus,
    ResearchPackage,
    SectionStatus,
)


class InvalidAssemblyInputError(Exception):
    """Raised when Assembly Input does not satisfy
    RESEARCH_RESULT_ASSEMBLY.md Section 2 -- for example a Collector
    Result for a section the Research Plan did not require, a duplicate
    Collector Result for one section, or a Research Session/Research Plan
    pair that do not correspond to the same Research Input."""


class ResearchResultAssembly:
    """Combines Collector Results into one unified Research Package.

    Organizes; never merges facts together, never judges them, and never
    acts on them, per RESEARCH_RESULT_ASSEMBLY.md Section 1.
    """

    _ID_PREFIX = "RPK"

    def __init__(self) -> None:
        self._sequence: int = 0

    def create_research_package(
        self,
        collector_results: List[CollectorResult],
        research_session: ResearchSession,
        research_plan: ResearchPlan,
        previous_package: Optional[ResearchPackage] = None,
    ) -> ResearchPackage:
        """Create Research Package.

        Input: Collector Results, Research Session, Research Plan, per
        RESEARCH_RESULT_ASSEMBLY.md Section 2. Output: a unified
        ResearchPackage, per Section 3.

        `previous_package` is optional and defaults to None. When given
        (during a Revision Loop pass), required sections with no
        Collector Result in this run carry forward that prior package's
        entry unchanged, as Skipped, per Section 6. Without it, such
        sections are Missing.
        """
        self._validate_input(collector_results, research_session, research_plan)

        knowledge_sections = self.merge_collector_results(
            collector_results, research_plan.required_knowledge_sections, previous_package
        )
        collector_summary = self.generate_collector_summary(collector_results)
        missing_sections = self.identify_missing_sections(knowledge_sections)
        overall_status = self.determine_overall_collection_status(knowledge_sections)

        self._sequence += 1
        return ResearchPackage(
            research_id=self._generate_research_id(),
            research_session=research_session.research_id,
            research_topic=research_session.research_topic,
            research_profile=list(research_plan.research_profile),
            research_category=research_plan.research_category,
            knowledge_sections=knowledge_sections,
            collector_summary=collector_summary,
            missing_sections=missing_sections,
            overall_collection_status=overall_status,
            collection_completed_time=datetime.now(),
        )

    def merge_collector_results(
        self,
        collector_results: List[CollectorResult],
        required_sections: List[KnowledgeSection],
        previous_package: Optional[ResearchPackage] = None,
    ) -> List[AssembledSection]:
        """Merge Collector Results.

        Organizes Collector Results into one entry per required Knowledge
        Section, per RESEARCH_RESULT_ASSEMBLY.md Section 4 (Combine
        Collector Results, Preserve every Knowledge Section). Never
        merges facts across sections -- each stays its own entry.
        """
        results_by_section: Dict[KnowledgeSection, CollectorResult] = {
            result.knowledge_section: result for result in collector_results
        }
        previous_by_section: Dict[KnowledgeSection, AssembledSection] = (
            {entry.knowledge_section: entry for entry in previous_package.knowledge_sections}
            if previous_package is not None
            else {}
        )
        return [
            self._assemble_section(section, results_by_section, previous_by_section)
            for section in required_sections
        ]

    def identify_missing_sections(
        self, knowledge_sections: List[AssembledSection]
    ) -> List[AssembledSection]:
        """Identify Missing Sections.

        The subset of the Package's Knowledge Sections with no Collected
        Data attached, whichever status caused that absence -- Failed,
        Missing, or a Skipped entry carrying forward one of those two --
        per RESEARCH_RESULT_ASSEMBLY.md Section 3 and Section 6.
        """
        return [
            entry for entry in knowledge_sections if entry.collected_knowledge is None
        ]

    def generate_collector_summary(
        self, collector_results: List[CollectorResult]
    ) -> List[CollectorSummaryEntry]:
        """Generate Collector Summary.

        One row per collector triggered during this Assembly run, per
        RESEARCH_RESULT_ASSEMBLY.md Section 7. A Skipped section has no
        row here, since it was never registered this run.
        """
        return [
            CollectorSummaryEntry(
                collector_name=result.collector_name,
                execution_status=result.collector_status,
                completion_time=result.collection_time,
            )
            for result in collector_results
        ]

    def determine_overall_collection_status(
        self, knowledge_sections: List[AssembledSection]
    ) -> OverallCollectionStatus:
        """Determine Overall Collection Status.

        Complete if every required section reached Completed; Failed if
        none did; Partial otherwise, per RESEARCH_RESULT_ASSEMBLY.md
        Section 3.
        """
        completed_count = sum(
            1 for entry in knowledge_sections if entry.status == SectionStatus.COMPLETED
        )
        if completed_count == len(knowledge_sections):
            return OverallCollectionStatus.COMPLETE
        if completed_count == 0:
            return OverallCollectionStatus.FAILED
        return OverallCollectionStatus.PARTIAL

    def _assemble_section(
        self,
        section: KnowledgeSection,
        results_by_section: Dict[KnowledgeSection, CollectorResult],
        previous_by_section: Dict[KnowledgeSection, AssembledSection],
    ) -> AssembledSection:
        result = results_by_section.get(section)
        if result is not None:
            if result.collector_status in (
                CollectorStatus.SUCCESS,
                CollectorStatus.PARTIAL,
            ):
                return AssembledSection(
                    knowledge_section=section,
                    status=SectionStatus.COMPLETED,
                    collected_knowledge=result.collected_knowledge,
                    sources=list(result.sources),
                    collection_time=result.collection_time,
                )
            return AssembledSection(
                knowledge_section=section,
                status=SectionStatus.FAILED,
                collected_knowledge=None,
                sources=[],
                collection_time=result.collection_time,
            )

        previous_entry = previous_by_section.get(section)
        if previous_entry is not None:
            return AssembledSection(
                knowledge_section=section,
                status=SectionStatus.SKIPPED,
                collected_knowledge=previous_entry.collected_knowledge,
                sources=list(previous_entry.sources),
                collection_time=previous_entry.collection_time,
            )

        return AssembledSection(
            knowledge_section=section,
            status=SectionStatus.MISSING,
            collected_knowledge=None,
            sources=[],
            collection_time=None,
        )

    def _validate_input(
        self,
        collector_results: List[CollectorResult],
        research_session: ResearchSession,
        research_plan: ResearchPlan,
    ) -> None:
        required = set(research_plan.required_knowledge_sections)
        seen_sections = set()
        for result in collector_results:
            if result.knowledge_section not in required:
                raise InvalidAssemblyInputError(
                    f"'{result.knowledge_section.value}' is not a Required "
                    "Knowledge Section of this Research Plan."
                )
            if result.knowledge_section in seen_sections:
                raise InvalidAssemblyInputError(
                    f"Duplicate Collector Result for "
                    f"'{result.knowledge_section.value}'."
                )
            seen_sections.add(result.knowledge_section)

        if research_session.research_category != research_plan.research_category.value:
            raise InvalidAssemblyInputError(
                "Research Session and Research Plan do not share the same "
                "Research Category; they do not correspond to the same "
                "Research Input."
            )

    def _generate_research_id(self) -> str:
        date_stamp = datetime.now().strftime("%Y%m%d")
        return f"{self._ID_PREFIX}-{date_stamp}-{self._sequence:03d}"
