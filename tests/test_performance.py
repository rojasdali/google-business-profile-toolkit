from unittest.mock import MagicMock

from gbp_toolkit.client import GBPClient
from gbp_toolkit.performance import PerformanceService


def test_get_search_keywords():
    mock_client = MagicMock(spec=GBPClient)
    mock_client.location_id = "locations/loc123"
    mock_client.request.return_value = {
        "searchKeywordsCounts": [
            {
                "searchKeyword": "laundromat near me",
                "insightsValue": {"threshold": 15},
            },
            {
                "searchKeyword": "wash and fold",
                "insightsValue": {"threshold": 8},
            },
        ]
    }
    service = PerformanceService(mock_client)
    res = service.get_search_keywords(page_size=10)
    assert len(res) == 2
    assert res[0]["keyword"] == "laundromat near me"
    assert res[1]["keyword"] == "wash and fold"


def test_fetch_actions_summary():
    mock_client = MagicMock(spec=GBPClient)
    mock_client.location_id = "locations/loc123"
    mock_client.request.return_value = {
        "multiDailyMetricTimeSeries": [{"dailyMetric": "BUSINESS_CALLS_AND_MESSAGES"}]
    }
    service = PerformanceService(mock_client)
    data = service.fetch_actions_summary()
    assert "multiDailyMetricTimeSeries" in data
