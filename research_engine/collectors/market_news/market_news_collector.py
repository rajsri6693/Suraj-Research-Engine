"""
Market News Collector

Implements MarketNewsCollector, per
project_documentation/RESEARCH_COLLECTORS.md and
project_documentation/COLLECTOR_SOURCE_STRATEGY.md. It is responsible
ONLY for collecting the Market News Knowledge Section and returning a
MarketNewsResult.

Per Claude-Prompts/IMP_10F_NewsAPI_Integration.md, this collector may
optionally be given an APIManager (research_engine/api_manager/) for
News Category requests -- Company News is Primary Provider NewsAPI's
operation for this section, per API_MANAGER_ARCHITECTURE.md Section
2/3 (this collector requests "Company News" for `research_topic`, the
one query shape that scopes results to a specific company or market
topic such as "NIFTY 50"). Without an APIManager (the default),
collect() returns the same placeholder/mock MarketNewsResult as every
prior phase, so every existing caller and test is unaffected. When one
is given, collect() requests through it exclusively -- it NEVER calls
NewsAPI, Finnhub, or any provider directly, per IMP-10F's Collectors
rule.

When NewsAPI itself serves the request with at least one real article,
collect() maps the most recent deduplicated article onto news_title,
news_summary, published_time (NewsAPI's own `publishedAt`, preserved
exactly, never regenerated), source_name, and url. `url` is always
assigned NewsAPI's own article `url` exactly as returned when it is a
non-empty, absolute http(s) URL (see `_valid_article_url`) -- a
missing, empty, or non-http(s) value is set to "" rather than silently
keeping a stale value from this result's own placeholder construction,
so a NewsAPI article with no usable URL never breaks or fabricates
anything further downstream. NewsAPI has no sentiment or
category-classification field, so news_category and impact are
deliberately left as neutral, non-fabricated values ("News", "Unknown")
rather than invented, per "Do not fabricate summaries." When the Backup
Provider (Finnhub, still a placeholder) serves the request instead, or
NewsAPI returns no articles for the query, every field keeps its
placeholder value and only Sources/Collector Status reflect the real
outcome.

It NEVER accesses the internet itself, verifies data, approves data,
accesses a database, writes SQLite, generates scripts or videos, or
calls any other collector.

Preferred Source Category: Financial News Sources. Fallback Category:
Official Exchange Information, per COLLECTOR_SOURCE_STRATEGY.md's
Collector Mapping (Section 4).
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, Optional

from ...api_manager import APIManager, Category, ProviderName
from ..base_collector import BaseCollector
from .market_news_result import CollectorStatus, MarketNewsResult


class InvalidResearchTopicError(Exception):
    """Raised when collect() is given an empty or missing Research
    Topic."""


class MarketNewsCollector(BaseCollector):
    """Collects the Market News Knowledge Section."""

    NEWSAPI_OPERATION = "Company News"

    def __init__(self, api_manager: Optional[APIManager] = None) -> None:
        self.api_manager = api_manager

    @property
    def collector_name(self) -> str:
        return "Market News Collector"

    @property
    def knowledge_section(self) -> str:
        return "Market News"

    def collect(self, research_topic: str) -> MarketNewsResult:
        """Gather Market News for `research_topic`.

        Input: Research Topic. Output: a MarketNewsResult.

        Without an APIManager, returns placeholder/mock values only, as
        every prior phase did. With one, requests through it
        exclusively and reflects the real outcome onto the same
        placeholder shape -- see this module's docstring.
        """
        if not research_topic or not research_topic.strip():
            raise InvalidResearchTopicError("Research Topic must not be empty.")

        result = MarketNewsResult(
            news_title="Sample Manufacturing Ltd announces new plant expansion",
            news_summary=(
                "A placeholder news summary used to validate the Market News "
                "Collector's data contract; not the result of live research."
            ),
            news_category="Corporate Announcement",
            published_time=datetime(2026, 7, 8, 15, 30, 0),
            source_name="Business News Wire (placeholder)",
            related_companies=["Sample Manufacturing Ltd"],
            related_sectors=["Industrials"],
            impact="Positive",
            sources=["Financial News Sources (placeholder)"],
            collection_time=datetime.now(),
            collector_status=CollectorStatus.SUCCESS,
            url="https://example.com/sample-manufacturing-plant-expansion",
        )

        if self.api_manager is None:
            return result

        api_result = self.api_manager.request(
            Category.NEWS,
            self.NEWSAPI_OPERATION,
            {"query": research_topic},
            collector_name=self.collector_name,
        )
        article = self._newsapi_article(api_result)

        if api_result.success and (article is not None or api_result.provider_name != ProviderName.NEWSAPI):
            result.sources = [f"{api_result.provider_name.value} ({api_result.served_by.value})"]
            result.collector_status = CollectorStatus.SUCCESS
            if article is not None:
                self._apply_newsapi_article(result, article, research_topic)
        else:
            # Either the API call itself failed, or NewsAPI succeeded
            # but returned no article for this query -- either way, no
            # real Collected Data exists for this section, per
            # COLLECTOR_SOURCE_STRATEGY.md's Missing Source Rules.
            result.sources = []
            result.collector_status = CollectorStatus.FAILED

        return result

    @staticmethod
    def _newsapi_article(api_result) -> Optional[Dict[str, Any]]:
        """Extract the first (most recent) deduplicated article from a
        NewsAPI Company News response, or None if this result did not
        come from NewsAPI, or NewsAPI returned no articles for the
        query."""
        if not api_result.success or api_result.provider_name != ProviderName.NEWSAPI:
            return None
        payload = api_result.data if isinstance(api_result.data, dict) else None
        if payload is None:
            return None
        articles = payload.get("articles")
        if isinstance(articles, list) and articles:
            return articles[0]
        return None

    @staticmethod
    def _apply_newsapi_article(
        result: MarketNewsResult, article: Dict[str, Any], research_topic: str
    ) -> None:
        """Map the fields NewsAPI's article shape actually carries onto
        MarketNewsResult, per this module's docstring. Only overwrites a
        field when NewsAPI actually provided a value for it; never
        fabricates news_category or impact, which NewsAPI does not
        provide."""
        if article.get("title"):
            result.news_title = article["title"]
        if article.get("description"):
            result.news_summary = article["description"]
        result.url = MarketNewsCollector._valid_article_url(article.get("url"))
        result.news_category = "News"
        published_at = article.get("publishedAt")
        if published_at:
            result.published_time = MarketNewsCollector._parse_published_at(published_at)
        source = article.get("source")
        if isinstance(source, dict) and source.get("name"):
            result.source_name = source["name"]
        result.related_companies = [research_topic]
        result.related_sectors = []
        result.impact = "Unknown"

    @staticmethod
    def _valid_article_url(url: Optional[str]) -> str:
        """Return `url` completely unchanged if it is a non-empty,
        absolute http(s) URL -- otherwise "", so a missing, empty, or
        non-http(s) value (e.g. a relative path, or a scheme other than
        http/https) is never mistaken for a real article URL and never
        leaks a stale value left over from this result's own placeholder
        construction. Always assigned (never conditionally skipped),
        unlike news_title/news_summary/source_name, so a NewsAPI article
        missing a url can never leave MarketNewsResult.url holding an
        unrelated leftover value -- this is what makes a missing/empty
        url a graceful "no URL available" rather than a pipeline
        failure. The value itself, when valid, is returned exactly as
        provided -- never trimmed, re-encoded, or otherwise altered."""
        if isinstance(url, str) and url.lower().startswith(("http://", "https://")):
            return url
        return ""

    @staticmethod
    def _parse_published_at(published_at: str) -> datetime:
        """Parse NewsAPI's ISO-8601 `publishedAt` (e.g.
        "2026-07-10T09:00:00Z") into a datetime, preserving the exact
        original instant -- never regenerated or approximated. Falls
        back to the collection time only if NewsAPI's own timestamp is
        unparseable, which has not been observed live."""
        try:
            return datetime.fromisoformat(published_at.replace("Z", "+00:00"))
        except ValueError:
            return datetime.now()
