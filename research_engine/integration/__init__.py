"""
Integration Engine module.

Public entry point for the Integration package, connecting Research
Planner output through Research Workflow, Collectors, Research Result
Assembly, Knowledge Verification, and Human Review into one pipeline
run.
"""

from .integration_engine import IntegrationEngine, IntegrationResult
from .review_package import HumanReviewPackage, ReviewPackageStatus

__all__ = [
    "IntegrationEngine",
    "IntegrationResult",
    "HumanReviewPackage",
    "ReviewPackageStatus",
]
