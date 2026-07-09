"""
Knowledge Verifier

Implements KnowledgeVerifier, per
project_documentation/KNOWLEDGE_VERIFICATION.md. It decides whether
collected knowledge in a Research Package is trustworthy enough to be
marked Verified, ahead of Human Review.

It NEVER performs research, calls APIs, approves knowledge, modifies
collected knowledge, accesses a database, or generates scripts or videos.

Scope note: KNOWLEDGE_VERIFICATION.md Section 4 defines six Verification
Rules. This implementation evaluates one Research Package snapshot at a
time, with no database and no access to previously-stored verified
knowledge. Three rules are fully checkable from that snapshot alone and
are implemented exactly: Source validation, Missing information, and
Metadata requirements. Duplicate detection is checked within the
Research Package's own structure (no external stored knowledge exists to
compare against here, so a duplicate means two entries for the same
Knowledge Section in one Package -- a malformed input). Time-sensitive
knowledge and Conflicting information require context this module is
never given (Research Topic freshness expectations, and previously
verified stored knowledge, respectively) and are therefore never
triggered by this implementation -- consequently, determine_verification_
status here only ever returns Verified or Rejected; Pending and Needs
Human Review exist in the VerificationStatus vocabulary for fidelity to
KNOWLEDGE_VERIFICATION.md, but nothing in this module produces them.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from research_engine.assembly.research_package import AssembledSection, ResearchPackage
from research_engine.planner.research_plan import KnowledgeSection

from .verification_report import OverallVerificationStatus, VerificationReport
from .verification_result import Confidence, VerificationResult, VerificationStatus


class InvalidVerificationInputError(Exception):
    """Raised when a Research Package does not satisfy the structural
    conditions Knowledge Verification requires to evaluate it -- for
    example duplicate entries for one Knowledge Section, or no Knowledge
    Sections at all."""


class KnowledgeVerifier:
    """Evaluates a Research Package and produces a Verification Report."""

    def verify_research_package(
        self, research_package: ResearchPackage
    ) -> VerificationReport:
        """Verify Research Package.

        Input: Research Package, per KNOWLEDGE_VERIFICATION.md Section 2.
        Output: a VerificationReport, per Section 6.
        """
        self._validate_input(research_package)
        results = [
            self._verify_section(entry) for entry in research_package.knowledge_sections
        ]
        return self.generate_verification_report(research_package, results)

    def validate_sources(self, entry: AssembledSection) -> bool:
        """Validate Sources.

        True only if the section has Collected Knowledge and at least
        one source, per KNOWLEDGE_VERIFICATION.md Section 4 (Source
        validation) -- the same rule RESEARCH_WORKFLOW.md states as
        "every knowledge section must have at least one valid source."
        """
        return entry.collected_knowledge is not None and len(entry.sources) > 0

    def detect_missing_sections(
        self, research_package: ResearchPackage
    ) -> List[KnowledgeSection]:
        """Detect Missing Sections.

        Every Knowledge Section with no Collected Knowledge in the
        Research Package -- reusing Assembly's own Missing Sections
        computation (RESEARCH_RESULT_ASSEMBLY.md Section 3), since
        Verification has nothing to evaluate for a section Assembly
        never received data for, per KNOWLEDGE_VERIFICATION.md Section 4
        (Missing information).
        """
        return [
            entry.knowledge_section for entry in research_package.missing_sections
        ]

    def detect_duplicate_sections(
        self, research_package: ResearchPackage
    ) -> List[KnowledgeSection]:
        """Detect Duplicate Sections.

        Every Knowledge Section that appears more than once among the
        Research Package's Knowledge Sections entries. A well-formed
        Research Package never has this, per RESEARCH_RESULT_ASSEMBLY.md
        Section 4 ("every section... gets an entry" -- singular);
        encountering it signals a malformed input.
        """
        seen = set()
        duplicates: List[KnowledgeSection] = []
        for entry in research_package.knowledge_sections:
            if entry.knowledge_section in seen and entry.knowledge_section not in duplicates:
                duplicates.append(entry.knowledge_section)
            seen.add(entry.knowledge_section)
        return duplicates

    def determine_verification_status(
        self, entry: AssembledSection
    ) -> Tuple[VerificationStatus, str]:
        """Determine Verification Status.

        Applies the three Verification Rules checkable from a single
        Research Package snapshot, in order: Missing information, Source
        validation, Metadata requirements. See this module's docstring
        for why only Verified and Rejected are ever returned.
        """
        if entry.collected_knowledge is None:
            return (
                VerificationStatus.REJECTED,
                "No Collected Knowledge was received for this section.",
            )
        if not entry.sources:
            return (
                VerificationStatus.REJECTED,
                "No source was provided for this section's Collected Knowledge.",
            )
        if entry.collection_time is None:
            return (
                VerificationStatus.REJECTED,
                "No Collection Time metadata was provided for this section.",
            )
        return (
            VerificationStatus.VERIFIED,
            "Collected Knowledge is present with at least one valid source and "
            "collection metadata.",
        )

    def generate_verification_report(
        self,
        research_package: ResearchPackage,
        results: List[VerificationResult],
    ) -> VerificationReport:
        """Generate Overall Verification Report.

        Rolls per-section VerificationResults up into the report's
        summary buckets, per KNOWLEDGE_VERIFICATION.md. Pending Sections
        holds both Pending and Needs Human Review outcomes -- see
        VerificationReport's docstring.
        """
        verified_sections = [
            result.knowledge_section
            for result in results
            if result.verification_status == VerificationStatus.VERIFIED
        ]
        failed_sections = [
            result.knowledge_section
            for result in results
            if result.verification_status == VerificationStatus.REJECTED
        ]
        pending_sections = [
            result.knowledge_section
            for result in results
            if result.verification_status
            in (VerificationStatus.PENDING, VerificationStatus.NEEDS_HUMAN_REVIEW)
        ]

        if results and len(verified_sections) == len(results):
            overall_status = OverallVerificationStatus.VERIFIED
        elif not verified_sections:
            overall_status = OverallVerificationStatus.REJECTED
        else:
            overall_status = OverallVerificationStatus.PARTIAL

        return VerificationReport(
            research_id=research_package.research_session,
            verification_results=results,
            overall_status=overall_status,
            verified_sections=verified_sections,
            failed_sections=failed_sections,
            pending_sections=pending_sections,
            generated_time=datetime.now(),
        )

    def _verify_section(self, entry: AssembledSection) -> VerificationResult:
        status, reason = self.determine_verification_status(entry)
        source_count = len(entry.sources)
        return VerificationResult(
            knowledge_section=entry.knowledge_section,
            verification_status=status,
            reason=reason,
            source_count=source_count,
            confidence=self._determine_confidence(status, source_count),
            last_updated=entry.collection_time,
        )

    def _determine_confidence(
        self, status: VerificationStatus, source_count: int
    ) -> Optional[Confidence]:
        """Confidence is only assigned to Verified sections, per
        KNOWLEDGE_VERIFICATION.md Section 6. High when multiple sources
        agree, Medium for a single source. This implementation has no
        signal (freshness, independent corroboration) to distinguish a
        thin/borderline single source from an ordinary one, so it never
        produces Low -- see this module's docstring."""
        if status != VerificationStatus.VERIFIED:
            return None
        if source_count >= 2:
            return Confidence.HIGH
        return Confidence.MEDIUM

    def _validate_input(self, research_package: ResearchPackage) -> None:
        if not research_package.knowledge_sections:
            raise InvalidVerificationInputError(
                "Research Package has no Knowledge Sections to verify."
            )
        duplicates = self.detect_duplicate_sections(research_package)
        if duplicates:
            names = ", ".join(section.value for section in duplicates)
            raise InvalidVerificationInputError(
                f"Research Package has duplicate entries for: {names}."
            )
