"""
Knowledge Verification module.

Public entry point for the Verification package, implementing
project_documentation/KNOWLEDGE_VERIFICATION.md.
"""

from .knowledge_verifier import InvalidVerificationInputError, KnowledgeVerifier
from .verification_report import OverallVerificationStatus, VerificationReport
from .verification_result import Confidence, VerificationResult, VerificationStatus

__all__ = [
    "VerificationResult",
    "VerificationStatus",
    "Confidence",
    "VerificationReport",
    "OverallVerificationStatus",
    "KnowledgeVerifier",
    "InvalidVerificationInputError",
]
