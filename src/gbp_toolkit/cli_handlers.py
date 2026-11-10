"""Subcommand handlers for the Google Business Profile CLI."""

import argparse
import json
import os
from dataclasses import asdict
from datetime import date
from typing import Any

from gbp_toolkit import GBPToolkit
from gbp_toolkit.types import PostActionType


def _emit(payload: Any, as_json: bool, text_msg: str) -> None:
    if as_json:
        print(json.dumps(payload, indent=2, default=str))
    else:
        print(text_msg)


def handle_posts_cmd(toolkit: GBPToolkit, args: argparse.Namespace) -> None:
    if args.post_action == "publish":
        res = toolkit.posts.publish(
            summary=args.summary,
            topic_slug=args.topic or "general",
            cta_url=args.cta_url,
            cta_type=PostActionType[args.cta_type] if args.cta_type else PostActionType.CALL,
            media_url=args.media_url,
        )
        _emit(asdict(res), args.json, f"✅ Published GBP post: {res.post_id} (State: {res.state})")
    elif args.post_action == "list":
        posts = toolkit.posts.list_posts(page_size=args.limit)
        lines = [f"📋 Found {len(posts)} GBP local posts:"] + [
            f"  • [{p['state']}] {p['post_id']}: {p['summary'][:70]}" for p in posts
        ]
        _emit({"count": len(posts), "posts": posts}, args.json, "\n".join(lines))
    elif args.post_action == "audit":
        rep = toolkit.posts.audit_rejected_posts(page_size=args.limit)
        rate_pct = rep["rejectionRate"] * 100
        msg = f"🛡️ GBP Post Audit: {rep['liveCount']} LIVE / {rep['rejectedCount']} REJECTED ({rate_pct:.1f}%)"
        _emit(rep, args.json, msg)


def handle_hours_cmd(toolkit: GBPToolkit, args: argparse.Namespace) -> None:
    target_date = date.fromisoformat(args.date)
    iso = target_date.isoformat()
    if args.hours_action == "close":
        resp = toolkit.hours.set_holiday_closure(target_date)
        _emit({"date": iso, "closed": True, "response": resp}, args.json, f"✅ Marked store as CLOSED on {iso}")
    elif args.hours_action == "modify":
        resp = toolkit.hours.set_holiday_modified(target_date, open_time=args.open, close_time=args.close)
        payload = {"date": iso, "open": args.open, "close": args.close, "response": resp}
        _emit(payload, args.json, f"✅ Set modified hours for {iso}: {args.open} - {args.close}")


def handle_audit_cmd(toolkit: GBPToolkit, args: argparse.Namespace) -> None:
    expected_title = args.title or os.getenv("GBP_BUSINESS_NAME", "")
    expected_phone = args.phone or os.getenv("GBP_BUSINESS_PHONE", "")
    expected_address = args.address or os.getenv("GBP_BUSINESS_ADDRESS", "")
    if not any([expected_title, expected_phone, expected_address]):
        _emit({"ok": False, "error": "Missing expected NAP parameters"}, args.json, "❌ Provide --title/--phone.")
        return
    issues = toolkit.locations.verify_nap_consistency(expected_title, expected_phone, expected_address)
    ok_msg = "✅ 100% NAP Consistency verified!"
    err_lines = "⚠️ Found discrepancies:\n" + "\n".join(f"  • {i}" for i in issues)
    _emit({"ok": not issues, "issues": issues}, args.json, ok_msg if not issues else err_lines)


def handle_doctor_cmd(toolkit: GBPToolkit, args: argparse.Namespace) -> None:
    c = toolkit.client
    checks = {
        "has_client_id": bool(c.client_id),
        "has_client_secret": bool(c.client_secret),
        "has_refresh_token": bool(c.refresh_token),
        "has_account_id": bool(c.account_id),
        "has_location_id": bool(c.location_id),
    }
    ok = all(checks.values())
    status = {"ok": ok, "account_id": c.account_id, "location_id": c.location_id, "checks": checks}
    lines = [f"{'✅' if ok else '⚠️'} GBP Doctor: {'READY' if ok else 'INCOMPLETE CREDENTIALS'}"] + [
        f"  • {k}: {'OK' if v else 'MISSING'}" for k, v in checks.items()
    ]
    _emit(status, args.json, "\n".join(lines))


def handle_keywords_cmd(toolkit: GBPToolkit, args: argparse.Namespace) -> None:
    rows = toolkit.performance.get_search_keywords(page_size=args.limit, months_back=args.months)
    lines = [f"🔍 Top {len(rows)} GBP Search Keywords:"] + [
        f"  • {r['keyword']}: {r['impressions']} impressions" for r in rows
    ]
    _emit({"count": len(rows), "keywords": rows}, args.json, "\n".join(lines))


def handle_actions_cmd(toolkit: GBPToolkit, args: argparse.Namespace) -> None:
    summary = toolkit.performance.get_customer_actions(days=args.days) or {}
    impr, acts = summary.get("totalImpressions", 0), summary.get("totalActions", 0)
    _emit(summary, args.json, f"📊 GBP {args.days}d Summary: {impr} impr · {acts} actions")


def handle_reviews_cmd(toolkit: GBPToolkit, args: argparse.Namespace) -> None:
    reviews = toolkit.reviews.list_reviews(page_size=args.limit, unanswered_only=args.unanswered)
    payload = {"count": len(reviews), "unanswered_only": args.unanswered, "reviews": [asdict(r) for r in reviews]}
    lines = [f"⭐ Found {len(reviews)} {'unanswered ' if args.unanswered else ''}reviews:"] + [
        f"  • [{r.star_rating}★] {r.reviewer_name}: {(r.comment or '(no text)')[:90]}" for r in reviews
    ]
    _emit(payload, args.json, "\n".join(lines))
