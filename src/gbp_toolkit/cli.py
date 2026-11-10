"""Command line interface for Google Business Profile Toolkit."""

import argparse
from typing import List, Optional

from gbp_toolkit import GBPToolkit
from gbp_toolkit.cli_handlers import (
    handle_actions_cmd,
    handle_audit_cmd,
    handle_doctor_cmd,
    handle_hours_cmd,
    handle_keywords_cmd,
    handle_posts_cmd,
    handle_reviews_cmd,
)

CTA_CHOICES = ["LEARN_MORE", "CALL", "BOOK", "ORDER", "SHOP", "SIGN_UP"]


def _build_shared_flags() -> argparse.ArgumentParser:
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="Emit structured JSON output")
    shared.add_argument("--dry-run", action="store_true", default=argparse.SUPPRESS, help="Simulate API mutations")
    return shared


def build_parser() -> argparse.ArgumentParser:
    shared = _build_shared_flags()
    parser = argparse.ArgumentParser(prog="gbp", description="Google Business Profile Toolkit CLI")
    parser.add_argument("--dry-run", action="store_true", help="Simulate API calls without modifying profile")
    parser.add_argument("--json", action="store_true", help="Emit structured JSON output")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    p_posts = subparsers.add_parser("posts", parents=[shared], help="Manage GBP local posts")
    p_posts_sub = p_posts.add_subparsers(dest="post_action", required=True)
    p_pub = p_posts_sub.add_parser("publish", parents=[shared], help="Publish a local update")
    p_pub.add_argument("--summary", required=True, help="Post text content")
    p_pub.add_argument("--topic", default="general", help="Topic slug for deduplication")
    p_pub.add_argument("--cta-url", help="Call to action URL (omitted automatically for CALL)")
    p_pub.add_argument("--cta-type", default="CALL", choices=CTA_CHOICES)
    p_pub.add_argument("--media-url", help="Public image attachment URL")
    p_list = p_posts_sub.add_parser("list", parents=[shared], help="List recent local posts")
    p_list.add_argument("--limit", type=int, default=20, help="Max posts to fetch")
    p_paudit = p_posts_sub.add_parser("audit", parents=[shared], help="Audit LIVE vs REJECTED local posts")
    p_paudit.add_argument("--limit", type=int, default=50, help="Max posts to audit")

    p_hours = subparsers.add_parser("hours", parents=[shared], help="Manage operating hours")
    p_hours_sub = p_hours.add_subparsers(dest="hours_action", required=True)
    p_close = p_hours_sub.add_parser("close", parents=[shared], help="Mark date as closed")
    p_close.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_mod = p_hours_sub.add_parser("modify", parents=[shared], help="Set modified holiday hours")
    p_mod.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_mod.add_argument("--open", required=True, help="HH:MM (e.g. 08:00)")
    p_mod.add_argument("--close", required=True, help="HH:MM (e.g. 17:00)")

    p_audit = subparsers.add_parser("audit", parents=[shared], help="Audit NAP consistency")
    p_audit.add_argument("--title", help="Expected business title")
    p_audit.add_argument("--phone", help="Expected canonical phone")
    p_audit.add_argument("--address", help="Expected canonical address")

    subparsers.add_parser("doctor", parents=[shared], help="Verify GBP credentials and configuration")

    p_kw = subparsers.add_parser("keywords", parents=[shared], help="Fetch monthly GBP search keywords")
    p_kw.add_argument("--limit", type=int, default=25, help="Max keywords to return")
    p_kw.add_argument("--months", type=int, default=3, help="Trailing months window")

    p_act = subparsers.add_parser("actions", parents=[shared], help="Fetch N-day GBP impressions & customer actions")
    p_act.add_argument("--days", type=int, default=90, help="Trailing published days window")

    p_rev = subparsers.add_parser("reviews", parents=[shared], help="List customer reviews")
    p_rev.add_argument("--unanswered", action="store_true", help="Filter to reviews missing owner reply")
    p_rev.add_argument("--limit", type=int, default=20, help="Max reviews to fetch")
    return parser


HANDLERS = {
    "posts": handle_posts_cmd,
    "hours": handle_hours_cmd,
    "audit": handle_audit_cmd,
    "doctor": handle_doctor_cmd,
    "keywords": handle_keywords_cmd,
    "actions": handle_actions_cmd,
    "reviews": handle_reviews_cmd,
}


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_parser()
    args = parser.parse_args(argv)
    args.json = getattr(args, "json", False)
    args.dry_run = getattr(args, "dry_run", False)
    toolkit = GBPToolkit.from_env(dry_run=args.dry_run)
    HANDLERS[args.subcommand](toolkit, args)


if __name__ == "__main__":
    main()
