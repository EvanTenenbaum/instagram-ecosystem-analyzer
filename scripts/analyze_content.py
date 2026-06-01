#!/usr/bin/env python3
"""Content and hashtag intelligence analysis.

Reads phase1_posts data for one or more target accounts and produces
hashtag recommendations, posting time insights, and content theme analysis.

Examples::

    python3 scripts/analyze_content.py --targets sarah_myerscough hostlerburrows

    python3 scripts/analyze_content.py \\
        --targets sarah_myerscough \\
        --output-dir outputs/content_2026

    python3 scripts/analyze_content.py \\
        --targets sarah_myerscough hostlerburrows \\
        --verbose
"""

import argparse
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzers.content_pattern_analyzer import ContentPatternAnalyzer


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Content and hashtag intelligence analysis for Instagram ecosystems"
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        required=True,
        metavar="USERNAME",
        help="Target Instagram usernames to analyse (must have collected phase1_posts data)",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory for analysis outputs (default: outputs)",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config JSON (default: config.json, currently unused by this analyser)",
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
    logger = logging.getLogger(__name__)

    targets = args.targets
    print(f"Analysing content for {len(targets)} target(s): {', '.join(targets)}")

    analyzer = ContentPatternAnalyzer(targets=targets)

    # Pre-flight: check which targets have data
    targets_with_data = []
    for target in targets:
        posts = analyzer.load_posts_for_target(target)
        if posts:
            targets_with_data.append(target)
            print(f"  ✓  {target}: {len(posts)} posts found")
        else:
            print(
                f"  ⚠  {target}: no phase1_posts data found — "
                "run collect_multi.py first, or check data/raw/{target}/",
                file=sys.stderr,
            )

    if not targets_with_data:
        print(
            "\nERROR: No targets have phase1_posts data. "
            "Run the collector first:\n"
            "  python3 scripts/collect_multi.py --targets " + " ".join(targets),
            file=sys.stderr,
        )
        return 1

    if len(targets_with_data) < len(targets):
        skipped = [t for t in targets if t not in targets_with_data]
        print(
            f"\nWARNING: {len(skipped)} target(s) skipped (no data): {', '.join(skipped)}",
            file=sys.stderr,
        )

    print(f"\nRunning content pattern analysis on: {', '.join(targets_with_data)}")

    # Run analysis only on targets that have data
    analyzer_for_run = ContentPatternAnalyzer(
        targets=targets_with_data,
        raw_base_dir="data/raw",
        processed_base_dir="data/processed",
    )

    result = analyzer_for_run.run()
    stats = result["stats"]
    files = result["files_saved"]

    print("\n--- Content analysis results ---")
    print(f"  Posts analysed         : {stats['total_posts']}")
    print(f"  Unique hashtags found  : {stats['unique_hashtags']}")
    print(f"  Hashtag sets generated : {stats['hashtag_sets_generated']}")

    results = result["results"]
    best_windows = results.get("posting_times", {}).get("best_windows", [])
    if best_windows:
        w = best_windows[0]
        print(f"  Top posting window     : {w['day']} at {w['hour']:02d}:00 UTC")

    if files:
        print("\nOutputs:")
        for key, path in files.items():
            print(f"  {key}: {path}")

    # Print top hashtag sets summary
    hashtag_sets = results.get("hashtag_sets", [])
    if hashtag_sets:
        print(f"\nTop hashtag set — {hashtag_sets[0]['name']}:")
        print("  " + " ".join(hashtag_sets[0]["hashtags"][:10]))
        if len(hashtag_sets) > 1:
            print(f"  ({len(hashtag_sets) - 1} additional sets in the markdown report)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
