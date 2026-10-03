from unittest.mock import MagicMock

from gbp_toolkit.client import GBPClient
from gbp_toolkit.reviews import ReviewsService, parse_review_item, parse_star_rating


def test_parse_star_rating():
    assert parse_star_rating("FIVE") == 5
    assert parse_star_rating("FOUR") == 4
    assert parse_star_rating("ONE") == 1
    assert parse_star_rating("UNKNOWN") == 5


def test_parse_review_item():
    raw = {
        "reviewId": "rev_100",
        "reviewer": {"displayName": "Jane Doe"},
        "starRating": "FIVE",
        "comment": "Great clean machines and fast service!",
        "reviewReply": {"comment": "Thank you Jane!"},
    }
    rev = parse_review_item(raw)
    assert rev.review_id == "rev_100"
    assert rev.reviewer_name == "Jane Doe"
    assert rev.star_rating == 5
    assert rev.comment == "Great clean machines and fast service!"
    assert rev.reply_comment == "Thank you Jane!"


def test_reply_to_review():
    mock_client = MagicMock(spec=GBPClient)
    mock_client.account_id = "accounts/acc123"
    mock_client.location_id = "locations/loc456"
    mock_client.request.return_value = {"comment": "Thanks for your visit!"}

    service = ReviewsService(mock_client)
    res = service.reply_to_review("rev_100", "Thanks for your visit!")
    assert res["comment"] == "Thanks for your visit!"
    mock_client.request.assert_called_once()
