"""Google Business Profile customer reviews and automated replies service."""

from typing import Any, Dict, List

from gbp_toolkit.client import GBPClient
from gbp_toolkit.types import ReviewItem


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


class ReviewsService:
    """Manages customer review stream, rating calculations, and owner replies."""

    def __init__(self, client: GBPClient):
        self.client = client

    def list_reviews(self, page_size: int = 20) -> List[ReviewItem]:
        """Fetches recent reviews for the configured location."""
        account = self.client.account_id or "accounts/current"
        location = self.client.location_id
        url = f"https://mybusiness.googleapis.com/v4/{account}/{location}/reviews?pageSize={page_size}"
        data = self.client.request("GET", url)
        return [parse_review_item(r) for r in data.get("reviews", [])]

    def reply_to_review(self, review_id: str, reply_text: str) -> Dict[str, Any]:
        """Submits an owner response to a specific customer review."""
        if not reply_text.strip():
            raise ValueError("Reply text cannot be empty.")
        if len(reply_text) > 4096:
            raise ValueError("Reply text exceeds 4096-char maximum.")

        account = self.client.account_id or "accounts/current"
        location = self.client.location_id
        url = f"https://mybusiness.googleapis.com/v4/{account}/{location}/reviews/{review_id}/reply"
        payload = {"comment": reply_text}
        return self.client.request("PUT", url, json_data=payload)
