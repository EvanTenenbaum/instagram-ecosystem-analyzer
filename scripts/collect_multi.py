#!/usr/bin/env python3
"""Multi-target Instagram network collection.

Examples::

    # Live collection (requires authenticated browser session)
    python scripts/collect_multi.py --targets sarah_myerscough hostlerburrows --limit 3

    # Quick mode: Phase 0+1 only (posts/commenters, no profile enrichment)
    python scripts/collect_multi.py --targets sarah_myerscough hostlerburrows --quick

    # Reuse already-collected data (skips browser)
    python scripts/collect_multi.py --targets sarah_myerscough hostlerburrows --skip-collection

    # Dry-run: create directory structure only, no browser launched
    python scripts/collect_multi.py --targets sarah_myerscough hostlerburrows --dry-run
"""

import argparse
import json
import logging
import sys
from pathlib import Path

# Allow running from the repo root without installing the package
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collectors.multi_target_collector import MultiTargetCollector


def _load_config(config_path: str = "config.json") -> dict:
    with open(config_path) as f:
        return json.load(f)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Multi-target Instagram ecosystem collection"
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        required=True,
        metavar="USERNAME",
        help="One or more target Instagram usernames",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum posts to collect per target (default: 10)",
    )
    parser.add_argument(
        "--skip-collection",
        action="store_true",
        help="Skip browser collection and use existing raw data",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Create directory structure only — do not launch browser",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config JSON (default: config.json)",
    )
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Phase 0+1 only (posts/commenters). Skip Phase 3 profile enrichment. "
             "Run enrich.py afterward to selectively fetch high-value profiles.",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    try:
        config = _load_config(args.config)
    except FileNotFoundError:
        print(f"ERROR: Config file not found: {args.config}", file=sys.stderr)
        return 1

    collector = MultiTargetCollector(config, args.targets, limit=args.limit)

    print(f"Collecting {len(args.targets)} target(s): {', '.join(args.targets)}")
    if args.dry_run:
        print("[dry-run] No browser will be launched.")
    if args.quick:
        print(
            "Quick mode: collecting posts and commenters only (no profile enrichment).\n"
            "Run 'python3 scripts/enrich.py --targets ...' afterward to enrich top accounts."
        )

    results = collector.collect_all(
        skip_existing=args.skip_collection,
        dry_run=args.dry_run,
        quick=args.quick,
    )

    # Summary
    print("\n--- Collection summary ---")
    for target, result in results.items():
        status = result.get("status", "unknown")
        data_dir = result.get("data_dir", "")
        files = result.get("files_written", 0)
        err = result.get("error", "")
        if err:
            print(f"  {target}: {status} — {err}")
        else:
            print(f"  {target}: {status} ({files} file(s)) → {data_dir}")

    manifest = Path("data/raw/multi_target_manifest.json")
    if manifest.exists():
        print(f"\nManifest: {manifest}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
