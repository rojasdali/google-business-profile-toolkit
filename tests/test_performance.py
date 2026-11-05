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
        "multiDailyMetricTimeSeries": [
            {
                "dailyMetricTimeSeries": [
                    {
                        "dailyMetric": "CALL_CLICKS",
                        "timeSeries": {
                            "datedValues": [
                                {"date": {"year": 2026, "month": 11, "day": 1}, "value": "4"},
                                {"date": {"year": 2026, "month": 11, "day": 2}, "value": "3"},
                            ]
                        },
                    }
                ]
            }
        ]
    }
    service = PerformanceService(mock_client)
    data = service.fetch_actions_summary()
    assert "multiDailyMetricTimeSeries" in data
    summary = service.get_7day_customer_actions()
    assert summary is not None
    assert summary["calls"] == 7
    assert summary["directions"] == 0
