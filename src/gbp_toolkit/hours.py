"""Google Business Profile operating hours and holiday/special hours engine."""

from datetime import date
from typing import Any, Dict, List

from gbp_toolkit.client import GBPClient
from gbp_toolkit.types import SpecialHoursDay


def format_special_hour_period(day: SpecialHoursDay) -> Dict[str, Any]:
    """Formats a SpecialHoursDay into Google Business Information API schema."""
    period: Dict[str, Any] = {
        "startDate": {
            "year": day.date_val.year,
            "month": day.date_val.month,
            "day": day.date_val.day,
        },
        "endDate": {
            "year": day.date_val.year,
            "month": day.date_val.month,
            "day": day.date_val.day,
        },
    }
    if day.is_closed:
        period["closed"] = True
    else:
        if day.open_time and day.close_time:
            oh, om = map(int, day.open_time.split(":"))
            ch, cm = map(int, day.close_time.split(":"))
            period["openTime"] = {"hours": oh, "minutes": om} if om else {"hours": oh}
            period["closeTime"] = {"hours": ch, "minutes": cm} if cm else {"hours": ch}
        else:
            period["closed"] = True
    return period


class HoursService:
    """Manages regular store hours and holiday / special operating hours."""

    def __init__(self, client: GBPClient):
        self.client = client

    def set_holiday_hours(self, special_days: List[SpecialHoursDay]) -> Dict[str, Any]:
        """Updates special holiday hours for the configured location."""
        periods = [format_special_hour_period(d) for d in special_days]
        payload = {"specialHours": {"specialHourPeriods": periods}}

        location = self.client.location_id
        url = (
            f"https://mybusinessbusinessinformation.googleapis.com/v1/{location}"
            "?updateMask=specialHours"
        )
        return self.client.request("PATCH", url, json_data=payload)

    def set_holiday_closure(self, holiday_date: date) -> Dict[str, Any]:
        """Convenience method to mark a specific holiday date as closed."""
        day = SpecialHoursDay(date_val=holiday_date, is_closed=True)
        return self.set_holiday_hours([day])

    def set_holiday_modified(self, holiday_date: date, open_time: str, close_time: str) -> Dict[str, Any]:
        """Convenience method to set modified operating hours for a holiday."""
        day = SpecialHoursDay(date_val=holiday_date, is_closed=False, open_time=open_time, close_time=close_time)
        return self.set_holiday_hours([day])
