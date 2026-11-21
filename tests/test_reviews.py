from unittest.mock import MagicMock

from gbp_toolkit.client import GBPClient
from gbp_toolkit.reviews import ReviewsManager, ReviewsService, parse_review_item, parse_star_rating


def test_parse_star_rating():
    assert parse_star_rating("FIVE") == 5
    assert parse_star_rating("FOUR") == 4
    assert parse_star_rating("THREE") == 3
    assert parse_star_rating("TWO") == 2
    assert parse_star_rating("ONE") == 1
    assert parse_star_rating("five") == 5
    assert parse_star_rating("UNKNOWN") == 0
    assert parse_star_rating("STAR_RATING_UNSPECIFIED") == 0
    assert parse_star_rating("") == 0
    assert parse_star_rating(None) == 0
    assert parse_star_rating(123) == 0  # type: ignore[arg-type]


def test_parse_review_item_missing_or_unknown_rating():
    missing = parse_review_item({"reviewId": "r_miss", "reviewer": {"displayName": "Sam"}})
    assert missing.star_rating == 0

    none_rating = parse_review_item({"reviewId": "r_none", "starRating": None})
    assert none_rating.star_rating == 0

    unspec = parse_review_item({"reviewId": "r_unspec", "starRating": "STAR_RATING_UNSPECIFIED"})
    assert unspec.star_rating == 0


def test_parse_review_item_null_reviewer_and_reply():
    rev = parse_review_item(
        {"reviewId": "r_null_rev", "reviewer": None, "starRating": "FIVE", "reviewReply": None}
    )
    assert rev.review_id == "r_null_rev"
    assert rev.reviewer_name == "Anonymous"
    assert rev.star_rating == 5
    assert rev.reply_comment is None


def test_reviews_manager_alias():
    assert ReviewsManager is ReviewsService


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
    assert rev.reply_comment == "Thank you Jane!"


def test_batch_reply_unanswered_template_and_callable():
    mock_client = MagicMock(spec=GBPClient)
    mock_client.account_id = "accounts/acc123"
    mock_client.location_id = "locations/loc456"
    mock_client.dry_run = False
    mock_client.request.side_effect = [
        {
            "reviews": [
                {"reviewId": "r1", "reviewer": {"displayName": "Maria"}, "starRating": "FIVE", "comment": "Excelente!"},
                {
                    "reviewId": "r2",
                    "reviewer": {"displayName": "Carlos"},
                    "starRating": "FIVE",
                    "reviewReply": {"comment": "Gracias!"},
                },
            ]
        },
        {"comment": "Gracias Maria!"},
    ]

    service = ReviewsService(mock_client)
    outcomes = service.batch_reply_unanswered("Gracias {reviewer_name}!", dry_run=False)
    assert len(outcomes) == 1
    assert outcomes[0] == {
        "review_id": "r1",
        "reviewer_name": "Maria",
        "star_rating": 5,
        "reply": "Gracias Maria!",
        "status": "replied",
    }

    mock_client.request.reset_mock()
    mock_client.request.side_effect = [
        {"reviews": [{"reviewId": "r3", "reviewer": {"displayName": "Ana"}, "starRating": "FOUR"}]}
    ]
    sim = service.batch_reply_unanswered(lambda r: f"Hola {r.reviewer_name} ({r.star_rating}★)", dry_run=True)
    assert len(sim) == 1
    assert sim[0]["status"] == "dry_run"
    assert mock_client.request.call_count == 1


def test_get_reviews_summary():
    mock_client = MagicMock(spec=GBPClient)
    mock_client.account_id = "accounts/acc123"
    mock_client.location_id = "locations/loc456"
    mock_client.request.return_value = {
        "averageRating": 4.86,
        "totalReviewCount": 140,
        "reviews": [{"starRating": "FIVE", "comment": "Super clean!", "createTime": "2026-11-01T12:00:00Z"}],
    }
    service = ReviewsService(mock_client)
    summary = service.get_reviews_summary()
    assert summary["averageRating"] == 4.9
    assert summary["totalReviews"] == 140
    assert summary["latest"]["rating"] == 5


def test_get_reviews_summary_unknown_latest_rating():
    mock_client = MagicMock(spec=GBPClient)
    mock_client.account_id = "accounts/acc123"
    mock_client.location_id = "locations/loc456"
    for raw_rating in ("UNKNOWN", None):
        mock_client.request.return_value = {
            "averageRating": 4.2,
            "totalReviewCount": 10,
            "reviews": [{"starRating": raw_rating, "comment": "Ok"}],
        }
        summary = ReviewsService(mock_client).get_reviews_summary()
        assert summary["latest"]["rating"] == 0


def _make_mock_client(reviews_payload, dry_run: bool = False):
    mock_client = MagicMock(spec=GBPClient)
    mock_client.account_id = "accounts/acc123"
    mock_client.location_id = "locations/loc456"
    mock_client.dry_run = dry_run
    mock_client.request.side_effect = [{"reviews": reviews_payload}] + [{"comment": "ok"}] * len(reviews_payload)
    return mock_client


def test_batch_reply_unanswered_holds_below_default_4():
    payload = [
        {"reviewId": "r1", "reviewer": {"displayName": "U1"}, "starRating": "ONE"},
        {"reviewId": "r2", "reviewer": {"displayName": "U2"}, "starRating": "TWO"},
        {"reviewId": "r3", "reviewer": {"displayName": "U3"}, "starRating": "THREE"},
        {"reviewId": "r4", "reviewer": {"displayName": "U0"}, "starRating": "UNKNOWN"},
        {"reviewId": "r5", "reviewer": {"displayName": "UM"}},
        {"reviewId": "r6", "reviewer": {"displayName": "U4"}, "starRating": "FOUR"},
        {"reviewId": "r7", "reviewer": {"displayName": "U5"}, "starRating": "FIVE"},
    ]
    mock_client = _make_mock_client(payload)
    called_for = []

    def reply_fn(rev):
        called_for.append(rev.review_id)
        return f"Thanks {rev.reviewer_name}!"

    outcomes = ReviewsService(mock_client).batch_reply_unanswered(reply_fn, dry_run=False)
    by_id = {o["review_id"]: o for o in outcomes}
    for held_id in ("r1", "r2", "r3", "r4", "r5"):
        assert by_id[held_id]["status"] == "held"
        assert by_id[held_id]["reply"] is None
    for replied_id in ("r6", "r7"):
        assert by_id[replied_id]["status"] == "replied"
        assert by_id[replied_id]["reply"].startswith("Thanks ")
    assert called_for == ["r6", "r7"]
    put_calls = [c for c in mock_client.request.call_args_list if c.args[0] == "PUT"]
    assert len(put_calls) == 2
    assert all(url.endswith("/r6/reply") or url.endswith("/r7/reply") for url in (c.args[1] for c in put_calls))


def test_batch_reply_unanswered_dry_run_still_marks_held():
    payload = [
        {"reviewId": "r2", "reviewer": {"displayName": "U2"}, "starRating": "TWO"},
        {"reviewId": "r0", "reviewer": {"displayName": "U0"}, "starRating": "UNKNOWN"},
        {"reviewId": "r5", "reviewer": {"displayName": "U5"}, "starRating": "FIVE"},
    ]
    for param_dry, client_dry in ((True, False), (False, True)):
        mock_client = _make_mock_client(payload, dry_run=client_dry)
        outcomes = ReviewsService(mock_client).batch_reply_unanswered("Hi {reviewer_name}", dry_run=param_dry)
        by_id = {o["review_id"]: o for o in outcomes}
        assert by_id["r2"] == {
            "review_id": "r2",
            "reviewer_name": "U2",
            "star_rating": 2,
            "reply": None,
            "status": "held",
        }
        assert by_id["r0"] == {
            "review_id": "r0",
            "reviewer_name": "U0",
            "star_rating": 0,
            "reply": None,
            "status": "held",
        }
        assert by_id["r5"]["status"] == "dry_run"
        assert mock_client.request.call_count == 1


def test_batch_reply_unanswered_custom_hold_below():
    payload = [
        {"reviewId": "r0", "starRating": "UNKNOWN"},
        {"reviewId": "r1", "starRating": "ONE"},
        {"reviewId": "r4", "starRating": "FOUR"},
        {"reviewId": "r5", "starRating": "FIVE"},
    ]
    c5 = _make_mock_client(payload)
    res5 = {o["review_id"]: o["status"] for o in ReviewsService(c5).batch_reply_unanswered("Thanks!", hold_below=5)}
    assert res5 == {"r0": "held", "r1": "held", "r4": "held", "r5": "replied"}

    for hb in (1, 0):
        c_low = _make_mock_client([
            {"reviewId": "r0", "starRating": "UNKNOWN"},
            {"reviewId": "r1", "starRating": "ONE"},
        ])
        res_low = {
            o["review_id"]: o["status"]
            for o in ReviewsService(c_low).batch_reply_unanswered("Thanks!", hold_below=hb)
        }
        assert res_low == {"r0": "held", "r1": "replied"}
