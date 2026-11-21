"""Google Business Profile customer reviews and automated replies service."""

from typing import Any, Callable, Dict, List, Optional, Union

from gbp_toolkit.client import GBPClient
from gbp_toolkit.types import ReviewItem

ReplyGenerator = Union[str, Callable[[ReviewItem], Optional[str]]]
STAR_MAP = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}


def parse_star_rating(rating_str: Optional[str]) -> int:
    """Converts StarRating enum string (e.g. 'FIVE') to 1-5, or 0 if unknown/invalid."""
    if not isinstance(rating_str, str):
        return 0
    return STAR_MAP.get(rating_str.strip().upper(), 0)


def parse_review_item(data: Dict[str, Any]) -> ReviewItem:
    """Parses raw Google My Business v4 review payload."""
    reply_data = data.get("reviewReply") or {}
    return ReviewItem(
        review_id=data.get("reviewId", ""),
        reviewer_name=(data.get("reviewer") or {}).get("displayName") or "Anonymous",
        star_rating=parse_star_rating(data.get("starRating")),
        comment=data.get("comment"),
        reply_comment=reply_data.get("comment"),
    )


def _render_reply(review: ReviewItem, reply_fn_or_template: ReplyGenerator) -> Optional[str]:
    if callable(reply_fn_or_template):
        rendered = reply_fn_or_template(review)
        return rendered.strip() if rendered else None
    rendered = reply_fn_or_template.format(
        reviewer_name=review.reviewer_name,
        star_rating=review.star_rating,
        review_id=review.review_id,
    )
    return rendered.strip() or None


def _outcome(rev: ReviewItem, reply: Optional[str], status: str) -> Dict[str, Any]:
    return {
        "review_id": rev.review_id, "reviewer_name": rev.reviewer_name,
        "star_rating": rev.star_rating, "reply": reply, "status": status,
    }


class ReviewsService:
    """Manages customer review stream, rating calculations, and owner replies."""

    def __init__(self, client: GBPClient):
        self.client = client

    def list_reviews(self, page_size: int = 20, unanswered_only: bool = False) -> List[ReviewItem]:
        """Fetches recent reviews for the configured location."""
        account = self.client.account_id or "accounts/current"
        location = self.client.location_id
        url = f"https://mybusiness.googleapis.com/v4/{account}/{location}/reviews?pageSize={page_size}"
        data = self.client.request("GET", url)
        items = [parse_review_item(r) for r in data.get("reviews", [])]
        return [r for r in items if not r.reply_comment] if unanswered_only else items

    def get_reviews_summary(self) -> Dict[str, Any]:
        """Fetches aggregate star rating, total review count, and latest review."""
        account = self.client.account_id or "accounts/current"
        location = self.client.location_id
        url = f"https://mybusiness.googleapis.com/v4/{account}/{location}/reviews?pageSize=1"
        data = self.client.request("GET", url)
        latest = (data.get("reviews") or [{}])[0]
        latest_payload = None
        if latest:
            latest_payload = {
                "rating": parse_star_rating(latest.get("starRating")),
                "text": (latest.get("comment") or "")[:280],
                "createTime": latest.get("createTime"),
            }
        return {
            "averageRating": round(float(data.get("averageRating", 0.0)), 1),
            "totalReviews": int(data.get("totalReviewCount", 0)),
            "latest": latest_payload,
        }

    def reply_to_review(self, review_id: str, reply_text: str) -> Dict[str, Any]:
        """Submits an owner response to a specific customer review."""
        if not reply_text.strip():
            raise ValueError("Reply text cannot be empty.")
        if len(reply_text) > 4096:
            raise ValueError("Reply text exceeds 4096-char maximum.")
        account = self.client.account_id or "accounts/current"
        location = self.client.location_id
        url = f"https://mybusiness.googleapis.com/v4/{account}/{location}/reviews/{review_id}/reply"
        return self.client.request("PUT", url, json_data={"comment": reply_text})

    def batch_reply_unanswered(
        self, reply_fn_or_template: ReplyGenerator, dry_run: bool = False,
        page_size: int = 50, hold_below: int = 4,
    ) -> List[Dict[str, Any]]:
        """Replies to unanswered reviews, holding ratings below hold_below for human review."""
        outcomes: List[Dict[str, Any]] = []
        is_sim = dry_run or self.client.dry_run
        for rev in self.list_reviews(page_size=page_size, unanswered_only=True):
            if rev.star_rating < max(1, hold_below):
                outcomes.append(_outcome(rev, None, "held"))
                continue
            reply_text = _render_reply(rev, reply_fn_or_template)
            if not reply_text:
                continue
            if not is_sim:
                self.reply_to_review(rev.review_id, reply_text)
            outcomes.append(_outcome(rev, reply_text, "dry_run" if is_sim else "replied"))
        return outcomes


ReviewsManager = ReviewsService
