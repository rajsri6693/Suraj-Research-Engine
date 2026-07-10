"""
Company Collector

Implements CompanyCollector, the first real Research Collector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Company Information Knowledge Section and
returning a CompanyResult.

Per Claude-Prompts/IMP_10C_FMP_Integration.md, this collector may
optionally be given an APIManager (research_engine/api_manager/) for
Fundamental Data Category requests -- Company Profile is Primary
Provider FMP's operation for this section, per
API_MANAGER_ARCHITECTURE.md Section 2/3. Without an APIManager (the
default), collect() returns the same placeholder/mock CompanyResult as
every prior phase, so every existing caller and test is unaffected.
When one is given, collect() requests through it exclusively -- it
NEVER calls FMP, Finnhub, or any provider directly, per IMP-10C's
Collectors rule.

When FMP itself serves the request with at least one real record,
collect() maps FMP's live Company Profile fields onto CompanyResult
(company_name, sector, industry, isin, official_website,
business_description, headquarters, and nse_symbol/bse_symbol when the
listing exchange is identifiable) -- confirmed live against the real
FMP API (INFY -> "Infosys Limited") during IMP-10C validation.
founded_year is deliberately left as-is: FMP's profile carries an IPO
date, not an incorporation/founding date, and substituting one for the
other would be a data-integrity error, not an improvement. When the
Backup Provider (Finnhub, still a placeholder) serves the request
instead, or FMP returns no record for the symbol, the existing
placeholder field values are kept and only Sources/Collector Status
reflect the real outcome -- there is nothing further to genuinely map
from a placeholder response or an empty result set.

It NEVER accesses the internet itself, verifies data, approves data,
accesses a database, writes SQLite, generates scripts or videos, or
calls any other collector.

Preferred Source Category: Official Company Information. Fallback
Category: Official Corporate Filings, per
COLLECTOR_SOURCE_STRATEGY.md's Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from ...api_manager import APIManager, Category, ProviderName
from ..base_collector import BaseCollector
from .company_result import CollectorStatus, CompanyResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class CompanyCollector(BaseCollector):
    """Collects the Company Information Knowledge Section."""

    FMP_OPERATION = "Company Profile"

    def __init__(self, api_manager: Optional[APIManager] = None) -> None:
        self.api_manager = api_manager

    @property
    def collector_name(self) -> str:
        return "Company Information Collector"

    @property
    def knowledge_section(self) -> str:
        return "Company Information"

    def collect(self, research_topic: str) -> CompanyResult:
        """Gather Company Information for `research_topic`.

        Input: Research Topic. Output: a CompanyResult.

        Without an APIManager, returns placeholder/mock values only, as
        every prior phase did. With one, requests through it
        exclusively and reflects the real outcome onto the same
        placeholder shape -- see this module's docstring.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        result = CompanyResult(
            company_name="Sample Manufacturing Ltd",
            nse_symbol="SMFG",
            bse_symbol="500123",
            isin="INE000A00000",
            sector="Industrials",
            industry="Diversified Manufacturing",
            headquarters="Mumbai, Maharashtra, India",
            founded_year=1998,
            business_description=(
                "A placeholder business description used to validate the "
                "Company Collector's data contract; not the result of live "
                "research."
            ),
            official_website="https://example.invalid",
            sources=["Official Company Information (placeholder)"],
            collection_time=datetime.now(),
            collector_status=CollectorStatus.SUCCESS,
        )

        if self.api_manager is None:
            return result

        api_result = self.api_manager.request(
            Category.FUNDAMENTAL_DATA,
            self.FMP_OPERATION,
            {"symbol": research_topic},
            collector_name=self.collector_name,
        )
        record = self._fmp_record(api_result)

        if api_result.success and (record is not None or api_result.provider_name != ProviderName.FMP):
            result.sources = [f"{api_result.provider_name.value} ({api_result.served_by.value})"]
            result.collector_status = CollectorStatus.SUCCESS
            if record is not None:
                self._apply_fmp_record(result, record)
        else:
            # Either the API call itself failed, or FMP succeeded but
            # returned no record for this symbol -- either way, no
            # real Collected Data exists for this section, per
            # COLLECTOR_SOURCE_STRATEGY.md's Missing Source Rules.
            result.sources = []
            result.collector_status = CollectorStatus.FAILED

        return result

    @staticmethod
    def _fmp_record(api_result) -> Optional[dict]:
        """Extract the first record from an FMP Company Profile
        response, or None if this result did not come from FMP, or FMP
        returned an empty payload (symbol not found)."""
        if not api_result.success or api_result.provider_name != ProviderName.FMP:
            return None
        payload = api_result.data.get("payload") if isinstance(api_result.data, dict) else None
        if isinstance(payload, list) and payload:
            return payload[0]
        return None

    @staticmethod
    def _apply_fmp_record(result: CompanyResult, record: dict) -> None:
        """Map FMP's live /stable/profile fields onto CompanyResult,
        per this module's docstring. Only overwrites a field when FMP
        actually provided a non-empty value for it."""
        if record.get("companyName"):
            result.company_name = record["companyName"]
        if record.get("sector"):
            result.sector = record["sector"]
        if record.get("industry"):
            result.industry = record["industry"]
        if record.get("isin"):
            result.isin = record["isin"]
        if record.get("website"):
            result.official_website = record["website"]
        if record.get("description"):
            result.business_description = record["description"]

        headquarters_parts = [
            part for part in (record.get("city"), record.get("state"), record.get("country")) if part
        ]
        if headquarters_parts:
            result.headquarters = ", ".join(headquarters_parts)

        exchange = (record.get("exchange") or "").upper()
        symbol = record.get("symbol")
        if symbol and "NSE" in exchange:
            result.nse_symbol = symbol
        elif symbol and "BSE" in exchange:
            result.bse_symbol = symbol
