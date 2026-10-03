"""High-level Google Business Profile Local Posts publishing service."""

import logging
from typing import Any, Dict, Optional

from gbp_toolkit.client import GBPClient
from gbp_toolkit.dedup import PostDeduplicationLedger
from gbp_toolkit.types import CallToAction, LocalPostPayload, LocalPostResult, PostActionType, PostTopicType

logger = logging.getLogger(__name__)


def build_post_payload(payload: LocalPostPayload) -> Dict[str, Any]:
    """Formats a LocalPostPayload into Google My Business v4/v1 API schema."""
    if len(payload.summary) > 1500:
        raise ValueError(f"Post summary exceeds Google 1500-char limit ({len(payload.summary)} chars)")

    body: Dict[str, Any] = {
        "languageCode": payload.language_code,
        "summary": payload.summary,
        "topicType": payload.topic_type.value,
    }
    if payload.call_to_action:
        body["callToAction"] = {
            "actionType": payload.call_to_action.action_type.value,
            "url": payload.call_to_action.url,
        }
    if payload.media_url:
        body["media"] = [{"mediaFormat": "PHOTO", "sourceUrl": payload.media_url}]

    return body


class PostsService:
    """Manages creation, deduplication, and listing of Google Business Profile local posts."""

    def __init__(self, client: GBPClient, ledger: Optional[PostDeduplicationLedger] = None):
        self.client = client
        self.ledger = ledger or PostDeduplicationLedger()

    def publish(
        self,
        summary: str,
        topic_slug: str = "general",
        cta_url: Optional[str] = None,
        cta_type: PostActionType = PostActionType.LEARN_MORE,
        media_url: Optional[str] = None,
        topic_type: PostTopicType = PostTopicType.STANDARD,
        check_duplicate: bool = True,
    ) -> LocalPostResult:
        """Publishes a local post with zero-repeat deduplication and CTA attachment."""
        if check_duplicate and self.ledger.is_duplicate(summary, topic_slug=topic_slug):
            raise ValueError(f"Duplicate post rejected: Content or topic '{topic_slug}' published within cooldown.")

        cta = CallToAction(action_type=cta_type, url=cta_url) if cta_url else None
        payload = LocalPostPayload(
            summary=summary,
            topic_type=topic_type,
            call_to_action=cta,
            media_url=media_url,
        )
        api_body = build_post_payload(payload)

        # Endpoint structure: accounts/{account}/locations/{location}/localPosts
        account = self.client.account_id or "accounts/current"
        location = self.client.location_id
        url = f"https://mybusiness.googleapis.com/v4/{account}/{location}/localPosts"

        resp = self.client.request("POST", url, json_data=api_body)
        post_id = resp.get("name", "simulated_post_id")

        if not self.client.dry_run:
            self.ledger.record_publication(summary, topic_slug=topic_slug, post_id=post_id)

        return LocalPostResult(
            post_id=post_id,
            name=resp.get("name", ""),
            state=resp.get("state", "LIVE" if not self.client.dry_run else "SIMULATED"),
            create_time=resp.get("createTime", ""),
            summary=summary,
            search_url=resp.get("searchUrl"),
        )
