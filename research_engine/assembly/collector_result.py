"""
Collector Result

Implements the CollectorResult data model — the input Research Result
Assembly consumes, per project_documentation/RESEARCH_RESULT_ASSEMBLY.md
Section 2 (Assembly Input). A CollectorResult is a plain record of what
one collector returned for one Knowledge Section; it is never modified
once created.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import List, Optional

from research_engine.planner.research_plan import KnowledgeSection


class CollectorStatus(Enum):
    """Whether a collector's own attempt succeeded, per
    RESEARCH_RESULT_ASSEMBLY.md Section 2."""

    SUCCESS = "Success"
    PARTIAL = "Partial"
    FAILED = "Failed"


@dataclass
class CollectorResult:
    """One collector's raw, unverified result for one Knowledge Section.

    Field name note: RESEARCH_RESULT_ASSEMBLY.md Section 2 calls the
    gathered content "Collected Data"; this implementation names the
    field `collected_knowledge`, matching IMP-04's explicit field list —
    the two names refer to the same thing.
    """

    collector_name: str
    knowledge_section: KnowledgeSection
    collected_knowledge: Optional[str]
    sources: List[str]
    collection_time: datetime
    collector_status: CollectorStatus
