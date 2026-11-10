"""Tests for GBP CLI subcommands (doctor, keywords, reviews --unanswered, --json)."""

import json
from unittest.mock import MagicMock, patch

from gbp_toolkit.cli import main
from gbp_toolkit.types import ReviewItem


def _mock_toolkit() -> MagicMock:
    tk = MagicMock()
    tk.client.client_id = "cid"
    tk.client.client_secret = "csec"
    tk.client.refresh_token = "rtok"
    tk.client.account_id = "accounts/111"
    tk.client.location_id = "locations/222"
    tk.performance.get_search_keywords.return_value = [
        {"keyword": "lavanderia hialeah", "impressions": 85, "insights": {"value": "85"}}
    ]
    tk.reviews.list_reviews.return_value = [
        ReviewItem(review_id="rev1", reviewer_name="Elena", star_rating=5, comment="Muy limpio", reply_comment=None)
    ]
    return tk


def test_cli_doctor_json(capsys):
    with patch("gbp_toolkit.cli.GBPToolkit.from_env", return_value=_mock_toolkit()):
        main(["doctor", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert out["ok"] is True
    assert out["account_id"] == "accounts/111"


def test_cli_keywords_json(capsys):
    tk = _mock_toolkit()
    with patch("gbp_toolkit.cli.GBPToolkit.from_env", return_value=tk):
        main(["--json", "keywords", "--limit", "5", "--months", "2"])
    out = json.loads(capsys.readouterr().out)
    assert out["count"] == 1
    assert out["keywords"][0]["keyword"] == "lavanderia hialeah"
    tk.performance.get_search_keywords.assert_called_once_with(page_size=5, months_back=2)


def test_cli_reviews_unanswered_json(capsys):
    tk = _mock_toolkit()
    with patch("gbp_toolkit.cli.GBPToolkit.from_env", return_value=tk):
        main(["reviews", "--unanswered", "--limit", "10", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert out["unanswered_only"] is True
    assert out["count"] == 1
    assert out["reviews"][0]["reviewer_name"] == "Elena"
    tk.reviews.list_reviews.assert_called_once_with(page_size=10, unanswered_only=True)
