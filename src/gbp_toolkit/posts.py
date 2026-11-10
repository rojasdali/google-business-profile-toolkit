"""High-level Google Business Profile Local Posts publishing and auditing service."""

import os
from typing import Any, Dict, List, Optional, Union

from gbp_toolkit.client import GBPClient
from gbp_toolkit.dedup import PostDeduplicationLedger
from gbp_toolkit.post_payload import build_cta, build_post_payload
from gbp_toolkit.post_policy import (
    coerce_action_type,
    enforce_post_policy,
    parse_local_post,
    summarize_post_audit,
    validate_post_policy,
)
from gbp_toolkit.types import LocalPostPayload, LocalPostResult, PostActionType, PostTopicType

ACCOUNTS_URL = "https://mybusinessaccountmanagement.googleapis.com/v1/accounts"


class PostsService:
    """Manages creation, policy linting, deduplication, and auditing of GBP local posts."""

    validate_post_policy = staticmethod(validate_post_policy)

    def __init__(self, client: GBPClient, ledger: Optional[PostDeduplicationLedger] = None):
        self.client = client
        self.ledger = ledger or PostDeduplicationLedger()

    def publish(
        self,
        summary: str,
        topic_slug: str = "general",
        cta_url: Optional[str] = None,
        cta_type: Union[PostActionType, str] = PostActionType.LEARN_MORE,
        media_url: Optional[str] = None,
        topic_type: PostTopicType = PostTopicType.STANDARD,
        check_duplicate: bool = True,
        enforce_policy: bool = True,
    ) -> LocalPostResult:
        """Publishes a local post with policy linting, zero-repeat dedup, and GMB v4 CTA."""
        action = coerce_action_type(cta_type)
        enforce_post_policy(summary, action, enforce=enforce_policy)
        if check_duplicate and self.ledger.is_duplicate(summary, topic_slug=topic_slug):
            raise ValueError(f"Duplicate post rejected: Content or topic '{topic_slug}' published within cooldown.")
        payload = LocalPostPayload(
            summary=summary, topic_type=topic_type, call_to_action=build_cta(action, cta_url), media_url=media_url
        )
        resp = self.client.request("POST", self._posts_url(), json_data=build_post_payload(payload))
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

    def list_posts(self, page_size: int = 20) -> List[Dict[str, Any]]:
        resp = self.client.request("GET", f"{self._posts_url()}?pageSize={page_size}")
        return [parse_local_post(p) for p in resp.get("localPosts", [])]

    def audit_rejected_posts(self, page_size: int = 50) -> Dict[str, Any]:
        return summarize_post_audit(self.list_posts(page_size=page_size))

    def _posts_url(self) -> str:
        return f"https://mybusiness.googleapis.com/v4/{self._resolve_account()}/{self._resolve_location()}/localPosts"

    def _resolve_account(self) -> str:
        acc = self.client.account_id or os.getenv("GBP_ACCOUNT_ID", "").strip()
        if acc and acc != "accounts/current":
            return acc if acc.startswith("accounts/") else f"accounts/{acc}"
        if self.client.dry_run:
            return "accounts/000000000"
        accounts = self.client.request("GET", ACCOUNTS_URL).get("accounts", [])
        if accounts:
            return accounts[0]["name"]
        raise ValueError("Missing GBP_ACCOUNT_ID in environment and unable to resolve from API")

    def _resolve_location(self) -> str:
        loc = self.client.location_id or os.getenv("GBP_LOCATION_ID", "").strip()
        if loc:
            return loc if loc.startswith("locations/") else f"locations/{loc}"
        if self.client.dry_run:
            return "locations/000000000"
        raise ValueError("Missing GBP_LOCATION_ID in environment")


__all__ = ["PostsService", "build_post_payload", "validate_post_policy"]
