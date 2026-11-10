"""Google Business Profile operating hours and holiday/special hours engine."""

from datetime import date
from typing import Any, Dict, List, Tuple

from gbp_toolkit.client import GBPClient
from gbp_toolkit.types import SpecialHoursDay

DateTuple = Tuple[int, int, int]
PeriodKey = Tuple[DateTuple, DateTuple]


def _date_tuple(raw: Dict[str, Any]) -> DateTuple:
    return (int(raw.get("year", 0)), int(raw.get("month", 0)), int(raw.get("day", 0)))


def _period_key(period: Dict[str, Any]) -> PeriodKey:
    start = _date_tuple(period.get("startDate", {}))
    end = _date_tuple(period.get("endDate") or period.get("startDate", {}))
    return (start, end)


def format_special_hour_period(day: SpecialHoursDay) -> Dict[str, Any]:
    """Formats a SpecialHoursDay into Google Business Information API schema."""
    d_dict = {"year": day.date_val.year, "month": day.date_val.month, "day": day.date_val.day}
    period: Dict[str, Any] = {"startDate": dict(d_dict), "endDate": dict(d_dict)}
    if not day.is_closed and day.open_time and day.close_time:
        oh, om = map(int, day.open_time.split(":"))
        ch, cm = map(int, day.close_time.split(":"))
        period["openTime"] = {"hours": oh, "minutes": om} if om else {"hours": oh}
        period["closeTime"] = {"hours": ch, "minutes": cm} if cm else {"hours": ch}
    else:
        period["closed"] = True
    return period


def merge_special_hour_periods(existing: List[Dict[str, Any]], incoming: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Merges incoming specialHourPeriods onto existing periods keyed by (startDate, endDate)."""
    merged: Dict[PeriodKey, Dict[str, Any]] = {}
    for p in existing:
        if "startDate" in p:
            merged[_period_key(p)] = p
    for p in incoming:
        merged[_period_key(p)] = p
    return [merged[k] for k in sorted(merged.keys())]


class HoursService:
    """Manages regular store hours and holiday / special operating hours."""

    def __init__(self, client: GBPClient):
        self.client = client

    def _location_resource(self) -> str:
        loc = self.client.location_id
        return loc if loc.startswith("locations/") else f"locations/{loc}"

    def get_special_hours(self) -> List[Dict[str, Any]]:
        """Reads existing specialHourPeriods from Google Business Information API."""
        url = (
            f"https://mybusinessbusinessinformation.googleapis.com/v1/{self._location_resource()}"
            "?readMask=specialHours"
        )
        data = self.client.request("GET", url)
        return list(data.get("specialHours", {}).get("specialHourPeriods", []))

    def set_holiday_hours(self, special_days: List[SpecialHoursDay]) -> Dict[str, Any]:
        """Reads existing special hours and upserts incoming holiday periods without wiping prior dates."""
        existing = self.get_special_hours()
        incoming = [format_special_hour_period(d) for d in special_days]
        merged = merge_special_hour_periods(existing, incoming)
        payload = {"specialHours": {"specialHourPeriods": merged}}
        url = (
            f"https://mybusinessbusinessinformation.googleapis.com/v1/{self._location_resource()}"
            "?updateMask=specialHours"
        )
        return self.client.request("PATCH", url, json_data=payload)

    def set_holiday_closure(self, holiday_date: date) -> Dict[str, Any]:
        """Convenience method to mark a specific holiday date as closed."""
        return self.set_holiday_hours([SpecialHoursDay(date_val=holiday_date, is_closed=True)])

    def set_holiday_modified(self, holiday_date: date, open_time: str, close_time: str) -> Dict[str, Any]:
        """Convenience method to set modified operating hours for a holiday."""
        day = SpecialHoursDay(date_val=holiday_date, is_closed=False, open_time=open_time, close_time=close_time)
        return self.set_holiday_hours([day])
