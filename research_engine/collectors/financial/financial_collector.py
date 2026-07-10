"""
Financial Collector

Implements FinancialCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Financial Information Knowledge Section and
returning a FinancialResult.

Per Claude-Prompts/IMP_10C_FMP_Integration.md, this collector may
optionally be given an APIManager (research_engine/api_manager/) for
Fundamental Data Category requests -- Financial Statements, Financial
Ratios, Earnings, Dividend, and Stock Split are Primary Provider FMP's
operations for this section, per API_MANAGER_ARCHITECTURE.md Section
2/3 (this collector requests "Financial Statements", i.e. FMP's
income-statement). Without an APIManager (the default), collect()
returns the same placeholder/mock FinancialResult as every prior
phase, so every existing caller and test is unaffected. When one is
given, collect() requests through it exclusively -- it NEVER calls
FMP, Finnhub, or any provider directly, per IMP-10C's Collectors rule.

When FMP itself serves the request with at least one real record,
collect() maps the four fields FMP's income-statement actually
carries -- revenue, net_profit (from netIncome), eps, and
financial_year (from fiscalYear) -- confirmed live against the real
FMP API during IMP-10C validation. book_value, pe_ratio, roe, roce,
debt_to_equity, market_capitalization, and dividend_yield come from a
different FMP operation (Financial Ratios / Company Profile, not
Financial Statements) that this collector does not call, so they are
deliberately left as placeholder values rather than fabricated --
combining multiple FMP operations into one collector call is future
work outside this phase's scope. When the Backup Provider (Finnhub,
still a placeholder) serves the request instead, or FMP returns no
record for the symbol, every field keeps its placeholder value and
only Sources/Collector Status reflect the real outcome.

It NEVER accesses the internet itself, verifies data, approves data,
accesses a database, writes SQLite, generates scripts or videos, or
calls any other collector.

Preferred Source Category: Official Financial Statements. Fallback
Category: Official Corporate Filings, per
COLLECTOR_SOURCE_STRATEGY.md's Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from ...api_manager import APIManager, Category, ProviderName
from ..base_collector import BaseCollector
from .financial_result import CollectorStatus, FinancialResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class FinancialCollector(BaseCollector):
    """Collects the Financial Information Knowledge Section."""

    FMP_OPERATION = "Financial Statements"

    def __init__(self, api_manager: Optional[APIManager] = None) -> None:
        self.api_manager = api_manager

    @property
    def collector_name(self) -> str:
        return "Financial Information Collector"

    @property
    def knowledge_section(self) -> str:
        return "Financial Information"

    def collect(self, research_topic: str) -> FinancialResult:
        """Gather Financial Information for `research_topic`.

        Input: Research Topic. Output: a FinancialResult.

        Without an APIManager, returns placeholder/mock values only, as
        every prior phase did. With one, requests through it
        exclusively and reflects the real outcome onto the same
        placeholder shape -- see this module's docstring.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        result = FinancialResult(
            revenue=412_00_00_000.0,
            net_profit=28_00_00_000.0,
            eps=14.75,
            book_value=182.30,
            pe_ratio=21.6,
            roe=16.2,
            roce=18.9,
            debt_to_equity=0.42,
            market_capitalization=6_500_00_00_000.0,
            dividend_yield=1.3,
            financial_year="FY2026",
            sources=["Official Financial Statements (placeholder)"],
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
        """Extract the first record from an FMP Financial Statements
        (income-statement) response, or None if this result did not
        come from FMP, or FMP returned an empty payload."""
        if not api_result.success or api_result.provider_name != ProviderName.FMP:
            return None
        payload = api_result.data.get("payload") if isinstance(api_result.data, dict) else None
        if isinstance(payload, list) and payload:
            return payload[0]
        return None

    @staticmethod
    def _apply_fmp_record(result: FinancialResult, record: dict) -> None:
        """Map the fields FMP's income-statement actually carries onto
        FinancialResult, per this module's docstring. Only overwrites a
        field when FMP actually provided a value for it."""
        if record.get("revenue") is not None:
            result.revenue = float(record["revenue"])
        if record.get("netIncome") is not None:
            result.net_profit = float(record["netIncome"])
        if record.get("eps") is not None:
            result.eps = float(record["eps"])
        fiscal_year = record.get("fiscalYear")
        if fiscal_year:
            result.financial_year = f"FY{fiscal_year}"
