"""
Approval Service module.

Public entry point for the Approval package, implementing IMP-09C's
approval persistence workflow: Review Result -> Save Approved Research
-> Trigger Telegram Notification.
"""

from .approval_service import ApprovalOutcome, ApprovalPersistenceError, ApprovalService

__all__ = [
    "ApprovalService",
    "ApprovalOutcome",
    "ApprovalPersistenceError",
]
