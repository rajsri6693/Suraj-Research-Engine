"""
API Logs Schema

Logical schema for the API Logging entity, per
project_documentation/API_MANAGER_ARCHITECTURE.md Section 5.6, Section
7, and Section 10.3. One row per call attempt ever made through the
API Manager -- never summarized or overwritten, per Section 5.6.
"""

from dataclasses import dataclass


@dataclass
class ApiLog:
    """Represents one call attempt made through the API Manager.

    Purpose: the permanent record every Dashboard Usage Count and
    Success Rate figure (Section 9) is computed from, and the record
    of which provider ultimately served each request, per the fifth
    Failover Rule (Section 7).
    """

    id: int  # Unique identifier for this log row.
    timestamp: str  # ISO timestamp of the attempt.
    category: str  # Category this attempt was made for.
    operation: str  # Operation requested (for example, "Company Profile").
    collector_name: str  # Name of the requesting Collector, empty if not applicable (e.g. a manual Health Check).
    provider_id: int  # Reference to the ApiProvider row attempted.
    role_attempted: str  # Primary or Backup -- which role this specific attempt represents.
    served_by: str  # Primary or Backup if this attempt succeeded and served the request, empty otherwise.
    outcome: str  # SUCCESS or FAILURE.
    health_status: str  # The Health status this attempt resulted in.
    response_time_ms: float  # Response time of this attempt.
