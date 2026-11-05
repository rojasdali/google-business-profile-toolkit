"""Google Business Profile Performance API insights and metrics service."""

from datetime import date, timedelta
from typing import Any, Dict, List, Optional

from gbp_toolkit.client import GBPClient

PERF_URL = "https://businessprofileperformance.googleapis.com/v1/{loc}:fetchMultiDailyMetricsTimeSeries"
METRICS = {
    "CALL_CLICKS": "calls",
    "BUSINESS_DIRECTION_REQUESTS": "directions",
    "WEBSITE_CLICKS": "websiteClicks",
}
LOOKBACK_DAYS = 14


def _range_params(start: date, end: date) -> str:
    parts = [f"dailyMetrics={m}" for m in METRICS]
    for label, d in (("startDate", start), ("endDate", end)):
        parts += [
            f"dailyRange.{label}.year={d.year}",
            f"dailyRange.{label}.month={d.month}",
            f"dailyRange.{label}.day={d.day}",
        ]
    return "&".join(parts)


def _extract_points(series: Dict[str, Any], out: Dict[str, Dict[str, int]]) -> None:
    key = METRICS.get(series.get("dailyMetric", ""))
    if not key:
        return
    for point in series.get("timeSeries", {}).get("datedValues", []):
        if "value" in point:
            d = point["date"]
            out[key][date(d["year"], d["month"], d["day"]).isoformat()] = int(point["value"])


def parse_daily_values(response: Dict[str, Any]) -> Dict[str, Dict[str, int]]:
    """Extracts {metric_key: {YYYY-MM-DD: value}} from multiDailyMetricTimeSeries."""
    out: Dict[str, Dict[str, int]] = {key: {} for key in METRICS.values()}
    for block in response.get("multiDailyMetricTimeSeries", []):
        for series in block.get("dailyMetricTimeSeries", []):
            _extract_points(series, out)
    return out


def summarize_last_7_published_days(values: Dict[str, Dict[str, int]]) -> Optional[Dict[str, Any]]:
    """Sums the 7 most recent days that Google has actually published."""
    published = sorted({day for series in values.values() for day in series})
    if not published:
        return None
    window: List[str] = published[-7:]
    totals = {key: sum(series.get(day, 0) for day in window) for key, series in values.items()}
    return {"startDate": window[0], "endDate": window[-1], **totals}


class PerformanceService:
    """Queries customer search keywords, map views, and direct interaction metrics."""

    def __init__(self, client: GBPClient):
        self.client = client

    def get_search_keywords(self, page_size: int = 25) -> List[Dict[str, Any]]:
        """Retrieves top search queries that displayed this business profile in Google Search/Maps."""
        location = self.client.location_id
        url = (
            f"https://businessprofileperformance.googleapis.com/v1/{location}:getDailySearchKeywords"
            f"?pageSize={page_size}"
        )
        data = self.client.request("GET", url)
        return [
            {"keyword": item.get("searchKeyword"), "insights": item.get("insightsValue", {})}
            for item in data.get("searchKeywordsCounts", [])
        ]

    def fetch_actions_summary(self, today: Optional[date] = None) -> Dict[str, Any]:
        """Queries raw multi-daily customer action time series for the location."""
        end = (today or date.today()) - timedelta(days=1)
        start = end - timedelta(days=LOOKBACK_DAYS)
        url = f"{PERF_URL.format(loc=self.client.location_id)}?{_range_params(start, end)}"
        return self.client.request("GET", url)

    def get_7day_customer_actions(self, today: Optional[date] = None) -> Optional[Dict[str, Any]]:
        """Fetches and summarizes the trailing 7 published days of calls, directions, and website clicks."""
        raw = self.fetch_actions_summary(today=today)
        return summarize_last_7_published_days(parse_daily_values(raw))
