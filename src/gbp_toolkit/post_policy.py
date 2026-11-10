"""Content-policy linter and post state parser for Google Business Profile local posts."""

import logging
import re
from typing import Any, Dict, List, Union

from gbp_toolkit.types import LINK_ACTION_TYPES, PostActionType, PostPolicyReport

logger = logging.getLogger(__name__)
URL_PATTERN = re.compile(r"(?:https?://|www\.|wa\.me/)\S+", re.IGNORECASE)
PHONE_PATTERN = re.compile(r"(?:\+?1[-.\s]?)?(?:\(\d{3}\)[-.\s]?|\b\d{3}[-.\s])\d{3}[-.\s]\d{4}\b|\b\d{10}\b")
WORD_TOKEN_PATTERN = re.compile(r"\b\w+\b", re.UNICODE)


def coerce_action_type(cta_type: Union[PostActionType, str]) -> PostActionType:
    if isinstance(cta_type, PostActionType):
        return cta_type
    key = (cta_type or "CALL").strip().upper()
    return PostActionType[key] if key in PostActionType.__members__ else PostActionType.CALL


def _find_shouting_words(summary: str) -> List[str]:
    shouting: List[str] = []
    for token in WORD_TOKEN_PATTERN.findall(summary):
        letters = [ch for ch in token if ch.isalpha()]
        if len(letters) >= 4 and all(ch.isupper() for ch in letters):
            shouting.append(token)
    return shouting


def validate_post_policy(summary: str, cta_type: Union[PostActionType, str] = "CALL") -> PostPolicyReport:
    """Validates GBP post summary and CTA against async content-rejection triggers."""
    violations: List[str] = []
    warnings: List[str] = []
    text = (summary or "").strip()

    if not text:
        violations.append("Post summary cannot be empty.")
    elif len(summary) > 1500:
        violations.append(f"Post summary exceeds Google 1500-char limit ({len(summary)} chars).")

    urls = URL_PATTERN.findall(text)
    if urls:
        violations.append(f"Raw URL in summary ({urls[0]}): GBP rejects inline URLs; attach CTA instead.")

    phones = PHONE_PATTERN.findall(text)
    if phones:
        violations.append(f"Phone number in summary ({phones[0]}): GBP rejects inline phones; use cta_type='CALL'.")

    shouting = _find_shouting_words(text)
    if shouting:
        violations.append(f"ALL-CAPS shouting words detected ({', '.join(shouting[:4])}): use sentence case.")

    action = coerce_action_type(cta_type)
    if action in LINK_ACTION_TYPES:
        warnings.append(f"Link CTA '{action.value}' has an elevated GBP rejection rate; prefer cta_type='CALL'.")

    return PostPolicyReport(valid=len(violations) == 0, violations=violations, warnings=warnings)


def enforce_post_policy(summary: str, action: PostActionType, enforce: bool = True) -> PostPolicyReport:
    report = validate_post_policy(summary, cta_type=action)
    for warn in report.warnings:
        logger.warning("GBP post policy warning: %s", warn)
    if enforce and not report.valid:
        raise ValueError("GBP post policy violation: " + "; ".join(report.violations))
    return report


def parse_local_post(raw: Dict[str, Any]) -> Dict[str, Any]:
    """Normalizes a raw GMB v4 localPost object with policy and rejection indicators."""
    name = raw.get("name", "")
    summary = raw.get("summary", "")
    cta = raw.get("callToAction")
    cta_type = (cta or {}).get("actionType", "CALL") if cta else "CALL"
    policy = validate_post_policy(summary, cta_type=cta_type) if summary else None
    indicators: List[str] = (list(policy.violations) + list(policy.warnings)) if policy else []
    if "wa.me/" in ((cta or {}).get("url", "") if cta else "").lower():
        indicators.append("CTA URL uses wa.me shortlink (frequently rejected by GBP content filter).")
    if not raw.get("media"):
        indicators.append("No photo media attached.")
    return {
        "post_id": name.split("/")[-1] if name else "",
        "name": name,
        "state": raw.get("state", "UNKNOWN"),
        "topicType": raw.get("topicType", "STANDARD"),
        "callToAction": cta,
        "summary": summary,
        "createTime": raw.get("createTime", ""),
        "updateTime": raw.get("updateTime", ""),
        "searchUrl": raw.get("searchUrl"),
        "hasMedia": bool(raw.get("media")),
        "rejectionIndicators": indicators,
    }


def summarize_post_audit(posts: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregates LIVE vs REJECTED local post counts and rejection rate."""
    counts: Dict[str, int] = {}
    for p in posts:
        counts[p["state"]] = counts.get(p["state"], 0) + 1
    rejected = [p for p in posts if p["state"] == "REJECTED"]
    live_cnt = sum(1 for p in posts if p["state"] in ("LIVE", "RECURRING"))
    total = len(posts)
    return {
        "total": total,
        "liveCount": live_cnt,
        "rejectedCount": len(rejected),
        "rejectionRate": round(len(rejected) / total, 4) if total else 0.0,
        "stateCounts": counts,
        "rejectedPosts": rejected,
        "posts": posts,
    }
