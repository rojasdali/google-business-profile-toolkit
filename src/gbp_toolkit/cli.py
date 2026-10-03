"""Command line interface for Google Business Profile Toolkit."""

import argparse
import os
from datetime import date

from gbp_toolkit import GBPToolkit
from gbp_toolkit.types import PostActionType


def handle_posts_cmd(toolkit: GBPToolkit, args: argparse.Namespace) -> None:
    if args.post_action == "publish":
        res = toolkit.posts.publish(
            summary=args.summary,
            topic_slug=args.topic or "general",
            cta_url=args.cta_url,
            cta_type=PostActionType[args.cta_type] if args.cta_type else PostActionType.LEARN_MORE,
            media_url=args.media_url,
        )
        print(f"✅ Published GBP post: {res.post_id} (State: {res.state})")


def handle_hours_cmd(toolkit: GBPToolkit, args: argparse.Namespace) -> None:
    target_date = date.fromisoformat(args.date)
    if args.hours_action == "close":
        toolkit.hours.set_holiday_closure(target_date)
        print(f"✅ Marked store as CLOSED on {target_date.isoformat()}")
    elif args.hours_action == "modify":
        toolkit.hours.set_holiday_modified(target_date, open_time=args.open, close_time=args.close)
        print(f"✅ Set modified hours for {target_date.isoformat()}: {args.open} - {args.close}")

def handle_audit_cmd(toolkit: GBPToolkit, args: argparse.Namespace) -> None:
    expected_title = args.title or os.getenv("GBP_BUSINESS_NAME", "")
    expected_phone = args.phone or os.getenv("GBP_BUSINESS_PHONE", "")
    expected_address = args.address or os.getenv("GBP_BUSINESS_ADDRESS", "")
    if not any([expected_title, expected_phone, expected_address]):
        print("❌ Error: Provide --title, --phone, and/or --address to verify NAP consistency.")
        return
    issues = toolkit.locations.verify_nap_consistency(
        expected_title=expected_title,
        expected_phone=expected_phone,
        expected_address=expected_address,
    )
    if not issues:
        print("✅ 100% NAP Consistency verified between profile and canonical constants!")
    else:
        print(f"⚠️ Found {len(issues)} discrepancies:")
        for iss in issues:
            print(f"  • {iss}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="gbp", description="Google Business Profile Toolkit CLI")
    parser.add_argument("--dry-run", action="store_true", help="Simulate API calls without modifying profile")
    subparsers = parser.add_subparsers(dest="subcommand", required=True)

    # Posts parser
    p_posts = subparsers.add_parser("posts", help="Manage GBP local posts")
    p_posts_sub = p_posts.add_subparsers(dest="post_action", required=True)
    p_pub = p_posts_sub.add_parser("publish", help="Publish a local update")
    p_pub.add_argument("--summary", required=True, help="Post text content")
    p_pub.add_argument("--topic", default="general", help="Topic slug for deduplication")
    p_pub.add_argument("--cta-url", help="Call to action URL (e.g. WhatsApp wa.me)")
    p_pub.add_argument("--cta-type", default="LEARN_MORE", choices=["LEARN_MORE", "CALL", "BOOK", "SIGN_UP"])
    p_pub.add_argument("--media-url", help="Public image attachment URL")

    # Hours parser
    p_hours = subparsers.add_parser("hours", help="Manage operating hours")
    p_hours_sub = p_hours.add_subparsers(dest="hours_action", required=True)
    p_close = p_hours_sub.add_parser("close", help="Mark date as closed")
    p_close.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_mod = p_hours_sub.add_parser("modify", help="Set modified holiday hours")
    p_mod.add_argument("--date", required=True, help="YYYY-MM-DD")
    p_mod.add_argument("--open", required=True, help="HH:MM (e.g. 08:00)")
    p_mod.add_argument("--close", required=True, help="HH:MM (e.g. 17:00)")

    # Audit parser
    p_audit = subparsers.add_parser("audit", help="Audit NAP consistency")
    p_audit.add_argument("--title", help="Expected business title")
    p_audit.add_argument("--phone", help="Expected canonical phone")
    p_audit.add_argument("--address", help="Expected canonical address")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    toolkit = GBPToolkit.from_env(dry_run=args.dry_run)

    if args.subcommand == "posts":
        handle_posts_cmd(toolkit, args)
    elif args.subcommand == "hours":
        handle_hours_cmd(toolkit, args)
    elif args.subcommand == "audit":
        handle_audit_cmd(toolkit, args)


if __name__ == "__main__":
    main()
