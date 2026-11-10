from unittest.mock import MagicMock

from gbp_toolkit.client import GBPClient
from gbp_toolkit.locations import LocationsService, parse_location_details


def test_parse_location_details():
    raw = {
        "name": "locations/12345",
        "title": "Clean Laundromat",
        "phoneNumbers": {"primaryPhone": "(555) 123-4567"},
        "storefrontAddress": {
            "addressLines": ["100 Main St"],
            "locality": "Miami",
            "administrativeArea": "FL",
            "postalCode": "33101",
        },
        "websiteUri": "https://cleanlaundromat.com",
    }
    details = parse_location_details(raw)
    assert details.location_id == "locations/12345"
    assert details.title == "Clean Laundromat"
    assert details.phone == "(555) 123-4567"
    assert details.locality == "Miami"


def test_verify_nap_consistency_match_with_suffix_normalization():
    mock_client = MagicMock(spec=GBPClient)
    mock_client.location_id = "locations/12345"
    mock_client.request.return_value = {
        "name": "locations/12345",
        "title": "Clean Laundromat",
        "phoneNumbers": {"primaryPhone": "+1 (555) 123-4567"},
        "storefrontAddress": {
            "addressLines": ["100 West Main Street"],
            "locality": "Miami",
            "administrativeArea": "FL",
            "postalCode": "33101",
        },
    }
    service = LocationsService(mock_client)
    issues = service.verify_nap_consistency(
        expected_title="Clean Laundromat",
        expected_phone="5551234567",
        expected_address="100 W Main St, Miami, FL 33101",
    )
    assert issues == []


def test_verify_nap_consistency_rejects_same_city_wrong_street():
    mock_client = MagicMock(spec=GBPClient)
    mock_client.location_id = "locations/12345"
    mock_client.request.return_value = {
        "name": "locations/12345",
        "title": "Clean Laundromat",
        "phoneNumbers": {"primaryPhone": "(555) 123-4567"},
        "storefrontAddress": {
            "addressLines": ["999 Palm Ave"],
            "locality": "Miami",
            "administrativeArea": "FL",
            "postalCode": "33101",
        },
    }
    service = LocationsService(mock_client)
    issues = service.verify_nap_consistency(
        expected_title="Clean Laundromat",
        expected_phone="5551234567",
        expected_address="100 Main St, Miami, FL 33101",
    )
    assert len(issues) == 1
    assert "Address mismatch" in issues[0]


def test_verify_nap_consistency_discrepancy():
    mock_client = MagicMock(spec=GBPClient)
    mock_client.location_id = "locations/12345"
    mock_client.request.return_value = {
        "name": "locations/12345",
        "title": "Old Name",
        "phoneNumbers": {"primaryPhone": "(555) 999-9999"},
        "storefrontAddress": {
            "addressLines": ["500 Other Rd"],
            "locality": "Tampa",
            "administrativeArea": "FL",
            "postalCode": "33601",
        },
    }
    service = LocationsService(mock_client)
    issues = service.verify_nap_consistency(
        expected_title="Clean Laundromat",
        expected_phone="5551234567",
        expected_address="100 Main St, Miami, FL 33101",
    )
    assert len(issues) == 3
