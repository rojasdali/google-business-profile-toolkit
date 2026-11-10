"""Tests for operating hours and holiday upsert merging."""

from datetime import date
from unittest.mock import MagicMock

from gbp_toolkit.client import GBPClient
from gbp_toolkit.hours import HoursService, format_special_hour_period
from gbp_toolkit.types import SpecialHoursDay


def test_format_holiday_closed_period():
    day = SpecialHoursDay(date_val=date(2026, 12, 25), is_closed=True)
    res = format_special_hour_period(day)
    assert res["closed"] is True
    assert res["startDate"] == {"year": 2026, "month": 12, "day": 25}
    assert res["endDate"] == {"year": 2026, "month": 12, "day": 25}


def test_format_holiday_modified_hours():
    day = SpecialHoursDay(date_val=date(2026, 11, 26), is_closed=False, open_time="08:00", close_time="14:00")
    res = format_special_hour_period(day)
    assert res.get("closed") is not True
    assert res["openTime"] == {"hours": 8}
    assert res["closeTime"] == {"hours": 14}


def test_set_holiday_hours_preserves_existing_periods_and_upserts():
    mock_client = MagicMock(spec=GBPClient)
    mock_client.location_id = "locations/12345"
    existing_thanksgiving = {
        "startDate": {"year": 2026, "month": 11, "day": 26},
        "endDate": {"year": 2026, "month": 11, "day": 26},
        "closed": True,
    }
    mock_client.request.side_effect = [
        {"specialHours": {"specialHourPeriods": [existing_thanksgiving]}},
        {"specialHours": {}},
    ]

    svc = HoursService(mock_client)
    svc.set_holiday_closure(date(2026, 12, 25))

    assert mock_client.request.call_count == 2
    patch_call = mock_client.request.call_args_list[1]
    assert patch_call.args[0] == "PATCH"
    periods = patch_call.kwargs["json_data"]["specialHours"]["specialHourPeriods"]
    assert len(periods) == 2
    assert periods[0]["startDate"] == {"year": 2026, "month": 11, "day": 26}
    assert periods[1]["startDate"] == {"year": 2026, "month": 12, "day": 25}


def test_set_holiday_hours_updates_same_date_in_place():
    mock_client = MagicMock(spec=GBPClient)
    mock_client.location_id = "locations/12345"
    existing_thanksgiving = {
        "startDate": {"year": 2026, "month": 11, "day": 26},
        "endDate": {"year": 2026, "month": 11, "day": 26},
        "closed": True,
    }
    mock_client.request.side_effect = [
        {"specialHours": {"specialHourPeriods": [existing_thanksgiving]}},
        {"specialHours": {}},
    ]

    svc = HoursService(mock_client)
    svc.set_holiday_modified(date(2026, 11, 26), open_time="08:00", close_time="15:00")

    periods = mock_client.request.call_args_list[1].kwargs["json_data"]["specialHours"]["specialHourPeriods"]
    assert len(periods) == 1
    assert periods[0]["openTime"] == {"hours": 8}
    assert periods[0]["closeTime"] == {"hours": 15}
    assert "closed" not in periods[0]
