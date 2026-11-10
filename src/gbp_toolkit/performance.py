"""Google Business Profile Performance API insights and metrics service."""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from gbp_toolkit.client import GBPClient
from gbp_toolkit.performance_parser import (
    ACTION_KEYS,
    IMPRESSION_KEYS,
    METRICS,
    build_daily_range_params,
    build_monthly_range_params,
    normalize_loc,
    parse_daily_values,
    summarize_published_days,
)

PERF_URL = "https://businessprofileperformance.googleapis.com/v1/{loc}:fetchMultiDailyMetricsTimeSeries"
KEYWORDS_URL = "https://businessprofileperformance.googleapis.com/v1/{loc}/searchkeywords/impressions/monthly"
LOOKBACK_DAYS = 14


def summarize_last_7_published_days(values: Dict[str, Dict[str, int]]) -> Optional[Dict[str, Any]]:
    """Backward-compatible alias summing the 7 most recent published days."""
    return summarize_published_days(values, days=7)


class PerformanceService:
    """Queries customer search keywords, map views, and direct interaction metrics."""

    def __init__(self, client: GBPClient):
        self.client = client

    def get_search_keywords(
        self, page_size: int = 25, months_back: int = 3, today: Optional[date] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves monthly search keywords via Business Profile Performance API v1."""
        loc = normalize_loc(self.client.location_id)
        params = build_monthly_range_params(today or date.today(), months_back=months_back, page_size=page_size)
        data = self.client.request("GET", f"{KEYWORDS_URL.format(loc=loc)}?{params}")
        results: List[Dict[str, Any]] = []
        for item in data.get("searchKeywordsCounts", []):
            ins = item.get("insightsValue", {})
            impr = int(ins.get("value") or ins.get("threshold") or 0)
            results.append({"keyword": item.get("searchKeyword"), "insights": ins, "impressions": impr})
        return results

    def fetch_actions_summary(self, days: int = 90, today: Optional[date] = None) -> Dict[str, Any]:
        """Queries multi-daily impression and action time series plus N-day totals."""
        end = (today or date.today()) - timedelta(days=1)
        start = end - timedelta(days=max(days + 5, LOOKBACK_DAYS))
        loc = normalize_loc(self.client.location_id)
        url = f"{PERF_URL.format(loc=loc)}?{build_daily_range_params(start, end)}"
        raw = self.client.request("GET", url)
        daily = parse_daily_values(raw)
        return {**raw, "days": days, "daily": daily, "summary": summarize_published_days(daily, days=days)}

    def get_customer_actions(self, days: int = 90, today: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """Fetches and summarizes the trailing N published days across all GBP metrics."""
        return self.fetch_actions_summary(days=days, today=today).get("summary")

    def get_7day_customer_actions(self, days: int = 7, today: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """Fetches and summarizes trailing published days (defaults to 7 days)."""
        return self.get_customer_actions(days=days, today=today)


__all__ = [
    "ACTION_KEYS",
    "IMPRESSION_KEYS",
    "METRICS",
    "PerformanceService",
    "parse_daily_values",
    "summarize_last_7_published_days",
    "summarize_published_days",
]
