from datetime import date
from unittest.mock import MagicMock

from gbp_toolkit.client import GBPClient
from gbp_toolkit.performance import METRICS, PerformanceService


def test_get_search_keywords_uses_monthly_impressions_endpoint():
    mock_client = MagicMock(spec=GBPClient)
    mock_client.location_id = "loc123"
    mock_client.request.return_value = {
        "searchKeywordsCounts": [
            {"searchKeyword": "laundromat near me", "insightsValue": {"value": "120"}},
            {"searchKeyword": "wash and fold", "insightsValue": {"threshold": 15}},
        ]
    }
    service = PerformanceService(mock_client)
    res = service.get_search_keywords(page_size=10, months_back=3, today=date(2026, 11, 10))
    called_url = mock_client.request.call_args.args[1]
    assert "/v1/locations/loc123/searchkeywords/impressions/monthly?" in called_url
    assert "monthlyRange.startMonth.year=2026" in called_url
    assert "monthlyRange.startMonth.month=9" in called_url
    assert "monthlyRange.endMonth.month=11" in called_url
    assert "getDailySearchKeywords" not in called_url
    assert len(res) == 2
    assert res[0]["keyword"] == "laundromat near me"
    assert res[0]["impressions"] == 120
    assert res[1]["impressions"] == 15


def test_fetch_actions_summary_90d_and_all_metrics():
    mock_client = MagicMock(spec=GBPClient)
    mock_client.location_id = "locations/loc123"
    mock_client.request.return_value = {
        "multiDailyMetricTimeSeries": [
            {
                "dailyMetricTimeSeries": [
                    {
                        "dailyMetric": "BUSINESS_IMPRESSIONS_MOBILE_MAPS",
                        "timeSeries": {"datedValues": [{"date": {"year": 2026, "month": 11, "day": 1}, "value": "40"}]},
                    },
                    {
                        "dailyMetric": "BUSINESS_IMPRESSIONS_MOBILE_SEARCH",
                        "timeSeries": {"datedValues": [{"date": {"year": 2026, "month": 11, "day": 1}, "value": "30"}]},
                    },
                    {
                        "dailyMetric": "BUSINESS_IMPRESSIONS_DESKTOP_MAPS",
                        "timeSeries": {"datedValues": [{"date": {"year": 2026, "month": 11, "day": 1}, "value": "10"}]},
                    },
                    {
                        "dailyMetric": "BUSINESS_IMPRESSIONS_DESKTOP_SEARCH",
                        "timeSeries": {"datedValues": [{"date": {"year": 2026, "month": 11, "day": 1}, "value": "5"}]},
                    },
                    {
                        "dailyMetric": "CALL_CLICKS",
                        "timeSeries": {
                            "datedValues": [
                                {"date": {"year": 2026, "month": 11, "day": 1}, "value": "4"},
                                {"date": {"year": 2026, "month": 11, "day": 2}, "value": "3"},
                            ]
                        },
                    },
                    {
                        "dailyMetric": "BUSINESS_DIRECTION_REQUESTS",
                        "timeSeries": {"datedValues": [{"date": {"year": 2026, "month": 11, "day": 1}, "value": "12"}]},
                    },
                    {
                        "dailyMetric": "WEBSITE_CLICKS",
                        "timeSeries": {"datedValues": [{"date": {"year": 2026, "month": 11, "day": 2}, "value": "2"}]},
                    },
                    {
                        "dailyMetric": "BUSINESS_CONVERSATIONS",
                        "timeSeries": {"datedValues": [{"date": {"year": 2026, "month": 11, "day": 2}, "value": "1"}]},
                    },
                    {
                        "dailyMetric": "BUSINESS_BOOKINGS",
                        "timeSeries": {"datedValues": [{"date": {"year": 2026, "month": 11, "day": 2}, "value": "1"}]},
                    },
                ]
            }
        ]
    }
    service = PerformanceService(mock_client)
    data = service.fetch_actions_summary(days=90, today=date(2026, 11, 10))
    called_url = mock_client.request.call_args.args[1]
    for metric_enum in METRICS:
        assert f"dailyMetrics={metric_enum}" in called_url
    assert "multiDailyMetricTimeSeries" in data
    assert data["days"] == 90
    assert data["summary"]["mobileMapsImpressions"] == 40
    assert data["summary"]["mobileSearchImpressions"] == 30
    assert data["summary"]["desktopMapsImpressions"] == 10
    assert data["summary"]["desktopSearchImpressions"] == 5
    assert data["summary"]["totalImpressions"] == 85
    assert data["summary"]["calls"] == 7
    assert data["summary"]["directions"] == 12
    assert data["summary"]["websiteClicks"] == 2
    assert data["summary"]["conversations"] == 1
    assert data["summary"]["bookings"] == 1
    assert data["summary"]["totalActions"] == 23

    summary_7d = service.get_7day_customer_actions(today=date(2026, 11, 10))
    assert summary_7d is not None
    assert summary_7d["calls"] == 7
    assert summary_7d["directions"] == 12
