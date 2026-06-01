#!/usr/bin/env python3
"""Multi-target cross-network analysis.

Runs graph building + account scoring for each target (skips if already done),
then executes CrossNetworkAnalyzer to find accounts present in multiple networks.

Examples::

    python scripts/analyze_multi.py --targets sarah_myerscough hostlerburrows

    python scripts/analyze_multi.py \\
        --targets sarah_myerscough hostlerburrows \\
        --output-dir outputs/cross_network_20250601
"""

import argparse
import json
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzers.graph_builder import GraphBuilder
from src.analyzers.account_scorer import AccountScorer
from src.analyzers.cross_network_analyzer import CrossNetworkAnalyzer


def _load_config(config_path: str = "config.json") -> dict:
    with open(config_path) as f:
        return json.load(f)


def _build_and_score(config: dict, target: str) -> bool:
    """Run graph building and account scoring for one target.

    Returns True if scoring completed (or score file already exists), False on error.
    """
    raw_dir = Path(f"data/raw/{target}")
    processed_dir = Path(f"data/processed/{target}")

    # Skip if score file already exists
    processed_dir.mkdir(parents=True, exist_ok=True)
    existing_scores = list(processed_dir.glob("account_scores_*.json"))
    if existing_scores:
        logging.getLogger(__name__).info(
            f"Skipping graph build for '{target}': score file already exists"
        )
        return True

    if not raw_dir.exists() or not list(raw_dir.glob("*.json")):
        logging.getLogger(__name__).warning(
            f"No raw data found for '{target}' at {raw_dir}. "
            "Run collect_multi.py first or use --skip-collection."
        )
        return False

    try:
        # Per-target config copy
        import copy
        target_config = copy.deepcopy(config)
        target_config["target_account"] = target

        builder = GraphBuilder(
            target_config,
            data_dir=str(raw_dir),
            processed_dir=str(processed_dir),
        )
        build_result = builder.run()
        if not build_result:
            return False

        graph = build_result["graph"]
        scorer = AccountScorer(target_config, processed_dir=str(processed_dir))
        scorer.run(graph)
        return True

    except Exception as exc:
        logging.getLogger(__name__).error(
            f"Analysis failed for '{target}': {exc}", exc_info=True
        )
        return False


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Multi-target cross-network analysis"
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        required=True,
        metavar="USERNAME",
        help="Target usernames (must already have collected data)",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs",
        help="Directory for cross-network outputs (default: outputs)",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config JSON (default: config.json)",
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

    try:
        config = _load_config(args.config)
    except FileNotFoundError:
        print(f"ERROR: Config file not found: {args.config}", file=sys.stderr)
        return 1

    print(f"Analyzing {len(args.targets)} target(s): {', '.join(args.targets)}")

    # Phase A: build graphs and score accounts per target
    analysis_ready = []
    for target in args.targets:
        ok = _build_and_score(config, target)
        if ok:
            analysis_ready.append(target)
        else:
            logger.warning(f"'{target}' will be excluded from cross-network analysis")

    if len(analysis_ready) < 2:
        print(
            f"\nWARNING: Only {len(analysis_ready)} target(s) have data. "
            "Cross-network analysis requires at least 2.",
            file=sys.stderr,
        )
        if not analysis_ready:
            return 1

    # Phase B: cross-network analysis
    print(f"\nRunning cross-network analysis on: {', '.join(analysis_ready)}")
    analyzer = CrossNetworkAnalyzer(analysis_ready)
    result = analyzer.run()

    stats = result["stats"]
    files = result["files_saved"]

    print("\n--- Cross-network results ---")
    print(f"  Super accounts found : {stats['total_super_accounts']}")
    print(f"  Tier A               : {stats['tier_a']}")
    print(f"  Tier B               : {stats['tier_b']}")
    if files:
        print(f"\nOutputs:")
        for key, path in files.items():
            print(f"  {key}: {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
