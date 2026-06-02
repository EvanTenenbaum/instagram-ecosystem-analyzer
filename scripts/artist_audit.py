#!/usr/bin/env python3
"""Artist self-audit CLI — run following audit and content gap analysis.

Usage::

    python scripts/artist_audit.py --artist evan_tenenbaum --targets jbblunkestate coupdetatsf

    python scripts/artist_audit.py \\
        --artist evan_tenenbaum \\
        --targets jbblunkestate coupdetatsf sarah_myerscough \\
        --super-accounts outputs/super_accounts_20260602_100156.csv \\
        --output-dir outputs \\
        --json
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzers.following_auditor import FollowingAuditor
from src.analyzers.content_auditor import ContentAuditor


def _load_config(config_path: str = "config.json") -> dict:
    with open(config_path) as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Artist self-audit: following list analysis + content gap analysis"
    )
    parser.add_argument(
        "--artist",
        default="evan_tenenbaum",
        help="Artist username to audit (default: evan_tenenbaum)",
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        required=True,
        metavar="USERNAME",
        help="Target gallery usernames to compare against",
    )
    parser.add_argument(
        "--super-accounts",
        default=None,
        help="Path to super_accounts_*.csv from cross-network analysis",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config JSON (default: config.json)",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory for output files (default: outputs)",
    )
    parser.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        help="Also write JSON output files",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Load config for known_accounts
    try:
        config = _load_config(args.config)
    except FileNotFoundError:
        print(f"ERROR: Config file not found: {args.config}", file=sys.stderr)
        return 1

    known_accounts = config.get("known_strategic_accounts", [])

    # --- Tool 1: Following Audit ---
    print()
    following_auditor = FollowingAuditor(args.artist)
    fa_result = following_auditor.run(
        targets=args.targets,
        super_accounts_csv=args.super_accounts,
        known_accounts=known_accounts,
    )
    print(fa_result["report"])

    # --- Tool 2: Content Gap Analysis ---
    content_auditor = ContentAuditor(
        artist_username=args.artist,
        targets=args.targets,
    )
    ca_result = content_auditor.run()
    print(ca_result["report"])

    # --- Optional JSON output ---
    if args.output_json:
        out = Path(args.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Following audit JSON
        fa_json_path = out / f"artist_audit_following_{timestamp}.json"
        with open(fa_json_path, "w") as f:
            json.dump(
                {
                    "artist": args.artist,
                    "type": "following_audit",
                    "timestamp": timestamp,
                    "targets": args.targets,
                    "result": fa_result["audit_result"],
                },
                f,
                indent=2,
                default=str,
            )
        print(f"Saved following audit: {fa_json_path}")

        # Content audit JSON
        ca_json_path = out / f"artist_audit_content_{timestamp}.json"
        with open(ca_json_path, "w") as f:
            json.dump(
                {
                    "artist": args.artist,
                    "type": "content_audit",
                    "timestamp": timestamp,
                    "targets": args.targets,
                    "result": ca_result["audit_result"],
                },
                f,
                indent=2,
                default=str,
            )
        print(f"Saved content audit: {ca_json_path}")

        # Combined markdown
        md_path = out / f"artist_audit_{timestamp}.md"
        with open(md_path, "w") as f:
            f.write(f"# Artist Audit Report — @{args.artist}\n\n")
            f.write(f"Generated: {timestamp}\n\n")
            f.write(f"Targets: {', '.join(args.targets)}\n\n")
            f.write("---\n\n")
            f.write(fa_result["report"])
            f.write("\n\n---\n\n")
            f.write(ca_result["report"])
        print(f"Saved combined report: {md_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
