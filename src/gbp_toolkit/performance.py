"""Google Business Profile Performance API insights and metrics service."""

from typing import Any, Dict, List

from gbp_toolkit.client import GBPClient

METRICS_MAPPING = {
    "CALL_CLICKS": "BUSINESS_IMPRESSIONS_FROM_CALL_CLICKS",
    "WEBSITE_CLICKS": "BUSINESS_IMPRESSIONS_FROM_WEBSITE_CLICKS",
    "DIRECTION_CLICKS": "BUSINESS_IMPRESSIONS_FROM_DIRECTION_CLICKS",
}


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
        results = []
        for item in data.get("searchKeywordsCounts", []):
            results.append({
                "keyword": item.get("searchKeyword"),
                "insights": item.get("insightsValue", {}),
            })
        return results

    def fetch_actions_summary(self) -> Dict[str, Any]:
        """Queries overall customer action counts for the location."""
        location = self.client.location_id
        url = (
            f"https://businessprofileperformance.googleapis.com/v1/{location}:fetchMultiDailyMetricsTimeSeries"
            "?dailyMetrics=BUSINESS_CALLS_AND_MESSAGES,BUSINESS_DIRECTION_REQUESTS,BUSINESS_WEBSITE_CLICKS"
        )
        return self.client.request("GET", url)
