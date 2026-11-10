"""Pure payload builders for Google My Business v4 localPosts endpoint."""

from typing import Any, Dict, Optional

from gbp_toolkit.post_policy import coerce_action_type
from gbp_toolkit.types import LINK_ACTION_TYPES, CallToAction, LocalPostPayload, PostActionType


def format_cta(cta: CallToAction) -> Optional[Dict[str, str]]:
    action = coerce_action_type(cta.action_type)
    if action == PostActionType.CALL:
        return {"actionType": PostActionType.CALL.value}
    if action in LINK_ACTION_TYPES and cta.url:
        return {"actionType": action.value, "url": cta.url}
    return None


def build_cta(action: PostActionType, cta_url: Optional[str]) -> Optional[CallToAction]:
    if action == PostActionType.CALL:
        return CallToAction(action_type=PostActionType.CALL, url=None)
    return CallToAction(action_type=action, url=cta_url) if cta_url else None


def build_post_payload(payload: LocalPostPayload) -> Dict[str, Any]:
    """Formats a LocalPostPayload into Google My Business v4 API schema."""
    if len(payload.summary) > 1500:
        raise ValueError(f"Post summary exceeds Google 1500-char limit ({len(payload.summary)} chars)")
    body: Dict[str, Any] = {
        "languageCode": payload.language_code,
        "summary": payload.summary,
        "topicType": payload.topic_type.value,
    }
    cta_dict = format_cta(payload.call_to_action) if payload.call_to_action else None
    if cta_dict:
        body["callToAction"] = cta_dict
    if payload.media_url:
        body["media"] = [{"mediaFormat": "PHOTO", "sourceUrl": payload.media_url}]
    return body
