"""Location details, NAP consistency, and business attributes service."""

import re
from typing import Any, Dict, List, Set, Tuple

from gbp_toolkit.client import GBPClient
from gbp_toolkit.types import LocationDetails

STREET_ABBREVS = {
    "street": "st",
    "avenue": "ave",
    "road": "rd",
    "boulevard": "blvd",
    "drive": "dr",
    "lane": "ln",
    "court": "ct",
    "place": "pl",
    "terrace": "ter",
    "parkway": "pkwy",
    "highway": "hwy",
    "north": "n",
    "south": "s",
    "east": "e",
    "west": "w",
    "suite": "ste",
    "florida": "fl",
}


def parse_location_details(data: Dict[str, Any]) -> LocationDetails:
    """Parses raw Google Business Information API payload into a LocationDetails schema."""
    addr = data.get("storefrontAddress", {})
    return LocationDetails(
        location_id=data.get("name", ""),
        title=data.get("title", ""),
        phone=data.get("phoneNumbers", {}).get("primaryPhone", ""),
        address_lines=addr.get("addressLines", []),
        locality=addr.get("locality", ""),
        administrative_area=addr.get("administrativeArea", ""),
        postal_code=addr.get("postalCode", ""),
        website_url=data.get("websiteUri"),
    )


def _normalize_phone(phone: str) -> str:
    digits = "".join(filter(str.isdigit, phone))
    return digits[1:] if len(digits) == 11 and digits.startswith("1") else digits


def _extract_street_signature(street_text: str) -> Tuple[str, Set[str]]:
    raw_tokens = re.findall(r"[a-z0-9]+", street_text.lower())
    norm = [STREET_ABBREVS.get(t, t) for t in raw_tokens]
    street_num = next((t for t in norm if t.isdigit()), "")
    name_tokens = {t for t in norm if t != street_num}
    return street_num, name_tokens


def _street_matches(details: LocationDetails, exp_street_raw: str) -> bool:
    exp_num, exp_street = _extract_street_signature(exp_street_raw)
    live_num, live_street = _extract_street_signature(" ".join(details.address_lines))
    if exp_num and exp_num != live_num:
        return False
    return not exp_street or exp_street.issubset(live_street)


def _check_address_match(details: LocationDetails, expected_address: str) -> bool:
    exp_parts = [p.strip() for p in expected_address.split(",") if p.strip()]
    if not _street_matches(details, exp_parts[0] if exp_parts else expected_address):
        return False
    exp_zip_m = re.search(r"\b(\d{5})\b", expected_address)
    live_zip = (details.postal_code or "")[:5]
    if exp_zip_m and live_zip and exp_zip_m.group(1) != live_zip:
        return False
    if len(exp_parts) >= 2 and details.locality:
        return exp_parts[1].lower() == details.locality.strip().lower()
    return True


class LocationService:
    """Manages location information, NAP consistency audits, and business attributes."""

    def __init__(self, client: GBPClient):
        self.client = client

    def get_details(self) -> LocationDetails:
        """Fetches current business details for the configured location."""
        loc = self.client.location_id
        loc_res = loc if loc.startswith("locations/") else f"locations/{loc}"
        url = (
            f"https://mybusinessbusinessinformation.googleapis.com/v1/{loc_res}"
            "?readMask=name,title,phoneNumbers,storefrontAddress,websiteUri,regularHours"
        )
        return parse_location_details(self.client.request("GET", url))

    def verify_nap_consistency(
        self,
        expected_title: str,
        expected_phone: str,
        expected_address: str,
    ) -> List[str]:
        """Audits live profile data against canonical store constants and returns discrepancies."""
        details = self.get_details()
        issues: List[str] = []
        if expected_title and details.title.strip().lower() != expected_title.strip().lower():
            issues.append(f"Title mismatch: '{details.title}' vs expected '{expected_title}'")
        if expected_phone and _normalize_phone(details.phone) != _normalize_phone(expected_phone):
            issues.append(f"Phone mismatch: '{details.phone}' vs expected '{expected_phone}'")
        if expected_address and not _check_address_match(details, expected_address):
            parts = [" ".join(details.address_lines), details.locality, details.postal_code]
            full_addr = ", ".join(filter(None, parts))
            issues.append(f"Address mismatch: '{full_addr}' vs expected '{expected_address}'")
        return issues


LocationsService = LocationService
