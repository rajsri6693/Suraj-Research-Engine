"""
Research Result Assembly module.

Public entry point for the Assembly package, implementing
project_documentation/RESEARCH_RESULT_ASSEMBLY.md.
"""

from .collector_result import CollectorResult, CollectorStatus
from .research_package import (
    AssembledSection,
    CollectorSummaryEntry,
    OverallCollectionStatus,
    ResearchPackage,
    SectionStatus,
)
from .result_assembly import InvalidAssemblyInputError, ResearchResultAssembly

__all__ = [
    "CollectorResult",
    "CollectorStatus",
    "ResearchPackage",
    "AssembledSection",
    "CollectorSummaryEntry",
    "SectionStatus",
    "OverallCollectionStatus",
    "ResearchResultAssembly",
    "InvalidAssemblyInputError",
]
