"""Location details, NAP consistency, and business attributes service."""

from typing import Any, Dict, List

from gbp_toolkit.client import GBPClient
from gbp_toolkit.types import LocationDetails


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


class LocationService:
    """Manages location information, NAP consistency audits, and business attributes."""

    def __init__(self, client: GBPClient):
        self.client = client

    def get_details(self) -> LocationDetails:
        """Fetches current business details for the configured location."""
        location = self.client.location_id
        url = (
            f"https://mybusinessbusinessinformation.googleapis.com/v1/{location}"
            "?readMask=name,title,phoneNumbers,storefrontAddress,websiteUri,regularHours"
        )
        data = self.client.request("GET", url)
        return parse_location_details(data)

    def verify_nap_consistency(
        self,
        expected_title: str,
        expected_phone: str,
        expected_address: str,
    ) -> List[str]:
        """Audits live profile data against canonical store constants and returns discrepancies."""
        details = self.get_details()
        issues: List[str] = []

        if details.title.lower() != expected_title.lower():
            issues.append(f"Title mismatch: '{details.title}' vs expected '{expected_title}'")

        clean_live_phone = "".join(filter(str.isdigit, details.phone))
        clean_exp_phone = "".join(filter(str.isdigit, expected_phone))
        if clean_live_phone != clean_exp_phone:
            issues.append(f"Phone mismatch: '{details.phone}' vs expected '{expected_phone}'")

        full_addr = " ".join(details.address_lines + [details.locality, details.postal_code]).lower()
        has_part = any(part.strip().lower() in full_addr for part in expected_address.split(","))
        if expected_address.lower() not in full_addr and not has_part:
            issues.append(f"Address mismatch: '{full_addr}' vs expected '{expected_address}'")

        return issues
