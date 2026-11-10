"""Tests for GBP CLI subcommands (doctor, keywords, actions, posts audit, reviews --unanswered)."""

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
        {"keyword": "lavanderia local", "impressions": 85, "insights": {"value": "85"}}
    ]
    tk.performance.get_customer_actions.return_value = {
        "startDate": "2026-08-10",
        "endDate": "2026-11-07",
        "publishedDays": 90,
        "totalImpressions": 2817,
        "totalActions": 448,
        "calls": 32,
        "directions": 381,
        "websiteClicks": 35,
    }
    tk.posts.audit_rejected_posts.return_value = {
        "total": 11,
        "liveCount": 7,
        "rejectedCount": 4,
        "rejectionRate": 0.3636,
        "stateCounts": {"LIVE": 7, "REJECTED": 4},
        "rejectedPosts": [],
        "posts": [],
    }
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
    assert out["keywords"][0]["keyword"] == "lavanderia local"
    tk.performance.get_search_keywords.assert_called_once_with(page_size=5, months_back=2)


def test_cli_actions_and_posts_audit_json(capsys):
    tk = _mock_toolkit()
    with patch("gbp_toolkit.cli.GBPToolkit.from_env", return_value=tk):
        main(["actions", "--days", "90", "--json"])
    out_act = json.loads(capsys.readouterr().out)
    assert out_act["totalImpressions"] == 2817
    tk.performance.get_customer_actions.assert_called_once_with(days=90)

    with patch("gbp_toolkit.cli.GBPToolkit.from_env", return_value=tk):
        main(["posts", "audit", "--limit", "25", "--json"])
    out_posts = json.loads(capsys.readouterr().out)
    assert out_posts["liveCount"] == 7
    assert out_posts["rejectedCount"] == 4
    tk.posts.audit_rejected_posts.assert_called_once_with(page_size=25)


def test_cli_reviews_unanswered_json(capsys):
    tk = _mock_toolkit()
    with patch("gbp_toolkit.cli.GBPToolkit.from_env", return_value=tk):
        main(["reviews", "--unanswered", "--limit", "10", "--json"])
    out = json.loads(capsys.readouterr().out)
    assert out["unanswered_only"] is True
    assert out["count"] == 1
    assert out["reviews"][0]["reviewer_name"] == "Elena"
    tk.reviews.list_reviews.assert_called_once_with(page_size=10, unanswered_only=True)
