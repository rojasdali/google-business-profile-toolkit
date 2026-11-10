"""Pure metric constants, URL parameter builders, and daily series parsers for GBP Performance API."""

from datetime import date
from typing import Any, Dict, List, Optional

METRICS = {
    "BUSINESS_IMPRESSIONS_MOBILE_MAPS": "mobileMapsImpressions",
    "BUSINESS_IMPRESSIONS_MOBILE_SEARCH": "mobileSearchImpressions",
    "BUSINESS_IMPRESSIONS_DESKTOP_MAPS": "desktopMapsImpressions",
    "BUSINESS_IMPRESSIONS_DESKTOP_SEARCH": "desktopSearchImpressions",
    "BUSINESS_DIRECTION_REQUESTS": "directions",
    "CALL_CLICKS": "calls",
    "WEBSITE_CLICKS": "websiteClicks",
    "BUSINESS_CONVERSATIONS": "conversations",
    "BUSINESS_BOOKINGS": "bookings",
}
IMPRESSION_KEYS = (
    "mobileMapsImpressions",
    "mobileSearchImpressions",
    "desktopMapsImpressions",
    "desktopSearchImpressions",
)
ACTION_KEYS = ("directions", "calls", "websiteClicks", "conversations", "bookings")


def normalize_loc(loc: str) -> str:
    return loc if loc.startswith("locations/") else f"locations/{loc}"


def build_daily_range_params(start: date, end: date) -> str:
    parts = [f"dailyMetrics={m}" for m in METRICS]
    for label, d in (("startDate", start), ("endDate", end)):
        parts.extend(
            [
                f"dailyRange.{label}.year={d.year}",
                f"dailyRange.{label}.month={d.month}",
                f"dailyRange.{label}.day={d.day}",
            ]
        )
    return "&".join(parts)


def build_monthly_range_params(today: date, months_back: int, page_size: int) -> str:
    end_first = today.replace(day=1)
    start_idx = (end_first.year * 12 + (end_first.month - 1)) - max(months_back - 1, 0)
    start_year, start_month = divmod(start_idx, 12)
    return "&".join(
        [
            f"monthlyRange.startMonth.year={start_year}",
            f"monthlyRange.startMonth.month={start_month + 1}",
            f"monthlyRange.endMonth.year={end_first.year}",
            f"monthlyRange.endMonth.month={end_first.month}",
            f"pageSize={page_size}",
        ]
    )


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


def summarize_published_days(values: Dict[str, Dict[str, int]], days: int = 7) -> Optional[Dict[str, Any]]:
    """Sums the N most recent published days across all GBP impression and action metrics."""
    published = sorted({day for series in values.values() for day in series})
    if not published:
        return None
    window: List[str] = published[-days:] if days > 0 else published
    totals = {key: sum(series.get(day, 0) for day in window) for key, series in values.items()}
    return {
        "startDate": window[0],
        "endDate": window[-1],
        "publishedDays": len(window),
        **totals,
        "totalImpressions": sum(totals.get(k, 0) for k in IMPRESSION_KEYS),
        "totalActions": sum(totals.get(k, 0) for k in ACTION_KEYS),
    }
