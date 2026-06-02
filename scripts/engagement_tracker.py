#!/usr/bin/env python3
"""Engagement tracker CLI — log and track Instagram engagement activities.

Usage::

    # Log an engagement activity
    python scripts/engagement_tracker.py log \\
        --target jbblunkestate \\
        --type comment \\
        --date 2026-06-01 \\
        --substantive

    # Show current progress toward visibility thresholds
    python scripts/engagement_tracker.py status

    # Check off this week's items
    python scripts/engagement_tracker.py checklist \\
        --blunk-space-comment \\
        --coup-detat-comment \\
        --peer-engagement \\
        --process-post

    # Weekly report
    python scripts/engagement_tracker.py report
"""

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.engagement_tracker import EngagementTracker


def _load_config(config_path: str = "config.json") -> dict:
    with open(config_path) as f:
        return json.load(f)


def cmd_log(args, tracker: EngagementTracker) -> int:
    """Handle the 'log' subcommand."""
    tracker.log_engagement(
        target=args.target,
        engagement_type=args.type,
        date=args.date,
        substantive=args.substantive,
        post_url=args.post_url,
    )
    print(f"✓ Logged {args.type} on @{args.target}" + (" (substantive)" if args.substantive else ""))
    if args.type == "comment":
        data = tracker.load()
        entry = data["targets"].get(args.target, {})
        substantive_count = len(entry.get("comments_this_month", []))
        threshold = entry.get("visibility_threshold", 4)
        print(f"  Progress: {substantive_count} / {threshold} substantive comments")
    return 0


def cmd_status(args, tracker: EngagementTracker) -> int:
    """Handle the 'status' subcommand."""
    print()
    print(tracker.format_status())
    return 0


def cmd_checklist(args, tracker: EngagementTracker) -> int:
    """Handle the 'checklist' subcommand."""
    items = []

    checklist_map = {
        "blunk_space_comment": "blunk_space_comment",
        "coup_detat_comment": "coup_detat_comment",
        "peer_engagement": "peer_engagement",
        "process_post": "process_post",
        "gallery_comment": "gallery_comment",
        "dm_outreach": "dm_outreach",
    }

    # argparse stores these as bool attributes
    for attr, key in checklist_map.items():
        flag_name = attr.replace("_", "-")
        if getattr(args, attr, False):
            items.append(key)

    if not items:
        print("No checklist items specified. Use --blunk-space-comment, --process-post, etc.")
        return 1

    tracker.check_off_week(*items)
    print(f"✓ Checked off {len(items)} item(s) for week {tracker.get_week_key()}:")
    checklist = tracker.get_week_checklist()
    for item in items:
        icon = "✅" if checklist.get(item) else "❌"
        print(f"  {icon} {item}")
    return 0


def cmd_report(args, tracker: EngagementTracker) -> int:
    """Handle the 'report' subcommand."""
    print()
    print(tracker.format_report())
    return 0


def cmd_uncheck(args, tracker: EngagementTracker) -> int:
    """Handle the 'uncheck' subcommand — remove a checklist item."""
    items = []
    checklist_map = {
        "blunk_space_comment": "blunk_space_comment",
        "coup_detat_comment": "coup_detat_comment",
        "peer_engagement": "peer_engagement",
        "process_post": "process_post",
        "gallery_comment": "gallery_comment",
        "dm_outreach": "dm_outreach",
    }
    for attr, key in checklist_map.items():
        if getattr(args, attr, False):
            items.append(key)

    if not items:
        print("No checklist items specified.")
        return 1

    tracker.uncheck_week(*items)
    print(f"✓ Unchecked {len(items)} item(s) for week {tracker.get_week_key()}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Instagram engagement tracker for artist self-audit"
    )
    parser.add_argument(
        "--artist",
        default="evan_tenenbaum",
        help="Artist username (default: evan_tenenbaum)",
    )
    parser.add_argument(
        "--tracker-file",
        default="data/engagement_tracker.json",
        help="Path to tracker JSON file (default: data/engagement_tracker.json)",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config JSON (default: config.json)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # --- log ---
    log_parser = subparsers.add_parser("log", help="Log an engagement activity")
    log_parser.add_argument("--target", required=True, help="Target username")
    log_parser.add_argument(
        "--type",
        required=True,
        choices=["comment", "like", "dm", "share", "mention"],
        help="Type of engagement",
    )
    log_parser.add_argument("--date", default=None, help="Date (YYYY-MM-DD), defaults to today")
    log_parser.add_argument(
        "--substantive",
        action="store_true",
        help="Mark as a substantive interaction",
    )
    log_parser.add_argument("--post-url", default=None, help="URL of the post engaged with")

    # --- status ---
    subparsers.add_parser("status", help="Show current engagement status")

    # --- report ---
    subparsers.add_parser("report", help="Generate weekly engagement report")

    # --- checklist ---
    check_parser = subparsers.add_parser("checklist", help="Check off weekly items")
    check_parser.add_argument("--blunk-space-comment", action="store_true", help="Commented on Blunk Space post")
    check_parser.add_argument("--coup-detat-comment", action="store_true", help="Commented on Coup D'Etat post")
    check_parser.add_argument("--peer-engagement", action="store_true", help="Engaged with peer artist")
    check_parser.add_argument("--process-post", action="store_true", help="Posted process content")
    check_parser.add_argument("--gallery-comment", action="store_true", help="Commented on gallery post")
    check_parser.add_argument("--dm-outreach", action="store_true", help="Sent DM / outreach")

    # --- uncheck ---
    uncheck_parser = subparsers.add_parser("uncheck", help="Remove a checklist item")
    uncheck_parser.add_argument("--blunk-space-comment", action="store_true")
    uncheck_parser.add_argument("--coup-detat-comment", action="store_true")
    uncheck_parser.add_argument("--peer-engagement", action="store_true")
    uncheck_parser.add_argument("--process-post", action="store_true")
    uncheck_parser.add_argument("--gallery-comment", action="store_true")
    uncheck_parser.add_argument("--dm-outreach", action="store_true")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Load config to get tracker file path if not overridden
    try:
        config = _load_config(args.config)
        tracker_file = args.tracker_file
        if "engagement_tracker_file" in config:
            tracker_file = config["engagement_tracker_file"]
    except FileNotFoundError:
        tracker_file = args.tracker_file

    tracker = EngagementTracker(
        artist_username=args.artist,
        tracker_file=tracker_file,
    )

    commands = {
        "log": cmd_log,
        "status": cmd_status,
        "report": cmd_report,
        "checklist": cmd_checklist,
        "uncheck": cmd_uncheck,
    }

    handler = commands.get(args.command)
    if handler:
        return handler(args, tracker)

    print(f"Unknown command: {args.command}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
