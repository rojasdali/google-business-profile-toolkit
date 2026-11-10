"""Google Business Profile customer reviews and automated replies service."""

from typing import Any, Callable, Dict, List, Optional, Union

from gbp_toolkit.client import GBPClient
from gbp_toolkit.types import ReviewItem

ReplyGenerator = Union[str, Callable[[ReviewItem], Optional[str]]]


def parse_star_rating(rating_str: str) -> int:
    """Converts StarRating enum string (e.g. 'FIVE') to numeric integer."""
    mapping = {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}
    return mapping.get(rating_str.upper(), 5)


def parse_review_item(data: Dict[str, Any]) -> ReviewItem:
    """Parses raw Google My Business v4 review payload."""
    reply_data = data.get("reviewReply", {})
    return ReviewItem(
        review_id=data.get("reviewId", ""),
        reviewer_name=data.get("reviewer", {}).get("displayName", "Anonymous"),
        star_rating=parse_star_rating(data.get("starRating", "FIVE")),
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
        return {
            "averageRating": round(float(data.get("averageRating", 0.0)), 1),
            "totalReviews": int(data.get("totalReviewCount", 0)),
            "latest": (
                {
                    "rating": parse_star_rating(latest.get("starRating", "FIVE")) if latest.get("starRating") else 0,
                    "text": (latest.get("comment") or "")[:280],
                    "createTime": latest.get("createTime"),
                }
                if latest
                else None
            ),
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
        self,
        reply_fn_or_template: ReplyGenerator,
        dry_run: bool = False,
        page_size: int = 50,
    ) -> List[Dict[str, Any]]:
        """Replies to all unanswered reviews using a template string or callable."""
        unanswered = self.list_reviews(page_size=page_size, unanswered_only=True)
        outcomes: List[Dict[str, Any]] = []
        for rev in unanswered:
            reply_text = _render_reply(rev, reply_fn_or_template)
            if not reply_text:
                continue
            is_sim = dry_run or self.client.dry_run
            if not is_sim:
                self.reply_to_review(rev.review_id, reply_text)
            outcomes.append(
                {
                    "review_id": rev.review_id,
                    "reviewer_name": rev.reviewer_name,
                    "star_rating": rev.star_rating,
                    "reply": reply_text,
                    "status": "dry_run" if is_sim else "replied",
                }
            )
        return outcomes
