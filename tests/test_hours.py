"""Tests for operating hours and holiday formatting."""

from datetime import date

from gbp_toolkit.hours import format_special_hour_period
from gbp_toolkit.types import SpecialHoursDay


def test_format_holiday_closed_period():
    day = SpecialHoursDay(date_val=date(2026, 12, 25), is_closed=True)
    res = format_special_hour_period(day)
    assert res["isClosed"] is True
    assert res["startDate"] == {"year": 2026, "month": 12, "day": 25}


def test_format_holiday_modified_hours():
    day = SpecialHoursDay(
        date_val=date(2026, 11, 26),
        is_closed=False,
        open_time="08:00",
        close_time="14:00",
    )
    res = format_special_hour_period(day)
    assert res.get("isClosed") is not True
    assert res["openTime"] == "08:00:00"
    assert res["closeTime"] == "14:00:00"
    assert res["startDate"] == {"year": 2026, "month": 11, "day": 26}
