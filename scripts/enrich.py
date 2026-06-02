#!/usr/bin/env python3
"""Targeted profile enrichment for high-value accounts.

After a --quick collection run (Phase 0+1 only), use this script to
selectively fetch profiles for accounts that actually matter: known
strategic accounts from config, top scorers per target, and accounts
appearing in multiple target networks.

Examples::

    # Enrich top accounts across targets
    python3 scripts/enrich.py --targets sarah_myerscough hostlerburrows

    # Enrich with custom top-N per target
    python3 scripts/enrich.py --targets sarah_myerscough hostlerburrows --top-n 30

    # Dry run: show what would be fetched without actually fetching
    python3 scripts/enrich.py --targets sarah_myerscough hostlerburrows --dry-run
"""

import argparse
import copy
import json
import logging
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.utils.account_cache import AccountCache

logger = logging.getLogger(__name__)


def _load_config(config_path: str = "config.json") -> dict:
    with open(config_path) as f:
        return json.load(f)


def _load_account_scores(target: str) -> list[dict]:
    """Load the most recent account_scores_*.json for a target."""
    processed_dir = Path("data/processed") / target
    if not processed_dir.exists():
        return []
    score_files = sorted(processed_dir.glob("account_scores_*.json"))
    if not score_files:
        return []
    try:
        with open(score_files[-1]) as f:
            data = json.load(f)
        return data.get("scores", [])
    except Exception as e:
        logger.warning(f"Could not load scores for {target}: {e}")
        return []


def _build_enrichment_list(targets: list[str], config: dict, cache: AccountCache,
                           top_n: int) -> tuple[list[str], dict]:
    """
    Build the prioritised enrichment list.

    Returns:
        (usernames_to_fetch, plan_stats)
    """
    seed_accounts = set(config.get("known_strategic_accounts", []))
    top_per_target: dict[str, list[str]] = {}
    all_scored: Counter = Counter()

    for target in targets:
        scores = _load_account_scores(target)
        # scores may be a list of dicts with "username" and "total_score" (or similar)
        ranked = []
        for entry in scores:
            username = entry.get("username") or entry.get("account")
            if username:
                ranked.append((username, entry.get("overall_score", entry.get("total_score", 0))))
        ranked.sort(key=lambda x: x[1], reverse=True)
        top_usernames = [u for u, _ in ranked[:top_n]]
        top_per_target[target] = top_usernames
        for u in top_usernames:
            all_scored[u] += 1

    # Super accounts: appear in 2+ target networks
    super_accounts = {u for u, count in all_scored.items() if count >= 2}

    # Union of all candidates
    candidates = seed_accounts | super_accounts
    for usernames in top_per_target.values():
        candidates.update(usernames)

    # Split into cached vs. to_fetch
    already_cached = {u for u in candidates if cache.has_fresh(u)}
    to_fetch = sorted(candidates - already_cached)

    # Estimate time (rough: ~10s per profile)
    est_seconds = len(to_fetch) * 10
    est_min = est_seconds // 60
    est_sec = est_seconds % 60

    plan_stats = {
        "seed_list_count": len(seed_accounts),
        "top_n_unique": len({u for ulist in top_per_target.values() for u in ulist}),
        "super_accounts": len(super_accounts),
        "already_cached": len(already_cached),
        "will_fetch": len(to_fetch),
        "estimated_time": f"~{est_min}m {est_sec}s" if est_min else f"~{est_sec}s",
    }

    return to_fetch, plan_stats


def _print_plan(targets: list[str], plan_stats: dict, top_n: int):
    print(f"\nEnrichment plan for {len(targets)} target(s):")
    print(f"  Seed list accounts:      {plan_stats['seed_list_count']} (from config)")
    print(f"  Top-{top_n} per target:       {plan_stats['top_n_unique']} unique")
    print(f"  Super accounts (2+ nets): {plan_stats['super_accounts']}")
    print(f"  Already cached (fresh):  {plan_stats['already_cached']}")
    print(f"  {'─' * 33}")
    print(f"  Will fetch:              {plan_stats['will_fetch']} profiles")
    print(f"  Estimated time:          {plan_stats['estimated_time']}")
    print()


def _save_phase3_enriched(target: str, profiles: list[dict]):
    """Save fetched profiles as phase3_enriched_*.json in raw dir for graph builder."""
    raw_dir = Path("data/raw") / target
    raw_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = raw_dir / f"phase3_enriched_{timestamp}.json"

    payload = {
        "metadata": {
            "source": "playwright",
            "timestamp": datetime.now().isoformat(),
            "target_account": target,
            "phase": "phase3_enriched",
            "authenticated": True,
        },
        "discovered_accounts": profiles,
    }

    with open(out_path, "w") as f:
        json.dump(payload, f, indent=2)

    logger.info(f"Saved {len(profiles)} profiles to {out_path}")
    return out_path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Targeted profile enrichment for high-value Instagram accounts"
    )
    parser.add_argument(
        "--targets",
        nargs="+",
        required=True,
        metavar="USERNAME",
        help="Target usernames whose top accounts to enrich",
    )
    parser.add_argument(
        "--top-n",
        type=int,
        default=20,
        help="Top N accounts per target to include (default: 20)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show enrichment plan without fetching any profiles",
    )
    parser.add_argument(
        "--config",
        default="config.json",
        help="Path to config JSON (default: config.json)",
    )
    parser.add_argument(
        "--cache-file",
        default="data/account_cache.json",
        help="Path to account cache JSON (default: data/account_cache.json)",
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

    max_age_days = config.get("cache_max_age_days", 30)
    cache = AccountCache(cache_file=args.cache_file, max_age_days=max_age_days)

    to_fetch, plan_stats = _build_enrichment_list(
        args.targets, config, cache, args.top_n
    )

    _print_plan(args.targets, plan_stats, args.top_n)

    if args.dry_run:
        print("[dry-run] No profiles will be fetched.")
        if to_fetch:
            print(f"\nWould fetch ({len(to_fetch)} accounts):")
            for u in to_fetch[:20]:
                print(f"  @{u}")
            if len(to_fetch) > 20:
                print(f"  ... and {len(to_fetch) - 20} more")
        return 0

    if not to_fetch:
        print("Nothing to fetch — all candidates are already cached.")
        return 0

    # Build a minimal config for the collector
    collector_config = copy.deepcopy(config)
    # Use the first target as nominal target_account (won't be used for fetching)
    collector_config["target_account"] = args.targets[0]

    try:
        from playwright.sync_api import sync_playwright
        from src.collectors.playwright_collector import PlaywrightCollector
        from src.utils.session_manager import SessionManager

        class _EnrichCollector(PlaywrightCollector):
            """PlaywrightCollector with raw_data_dir set to a temp path."""
            def __init__(self_, config):  # noqa: N805
                super().__init__(config)
                # Point raw_data_dir at first target's dir for session/checkpoint use
                self_.raw_data_dir = Path("data/raw") / args.targets[0]
                self_.raw_data_dir.mkdir(parents=True, exist_ok=True)

        collector = _EnrichCollector(collector_config)

        fetched_profiles: list[dict] = []

        print(f"Fetching {len(to_fetch)} profiles...")

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            collector.session_manager.load_session(context)

            if not collector.session_manager.is_authenticated():
                from src.collectors.playwright_collector import _load_env_credentials
                ig_user, ig_pass = _load_env_credentials()
                if ig_user and ig_pass:
                    collector.session_manager.auto_login(page, ig_user, ig_pass)

            for idx, username in enumerate(to_fetch, 1):
                print(f"  [{idx}/{len(to_fetch)}] @{username}")
                profile = collector.collect_account_profile(page, username)
                if profile:
                    fetched_profiles.append(profile)
                    cache.set(profile)
                # Save cache incrementally every 5 profiles so partial runs survive timeouts
                if idx % 5 == 0:
                    cache.save()
                    print(f"    [checkpoint] Cache saved ({cache.size()} entries)")
                collector.rate_limiter.wait()

            collector.session_manager.save_session(context)
            browser.close()

    except Exception as exc:
        logger.error(f"Enrichment failed: {exc}")
        print(f"\nERROR during enrichment: {exc}", file=sys.stderr)
        # Save whatever we got before the error
        if fetched_profiles:
            cache.save()
        return 1

    # Persist cache
    cache.save()

    # Save per-target phase3_enriched files so graph builder picks them up
    # Associate each profile back to relevant targets based on discovery
    # Simple approach: save all fetched profiles for each target
    for target in args.targets:
        if fetched_profiles:
            out_path = _save_phase3_enriched(target, fetched_profiles)
            print(f"  Saved to {out_path}")

    print(f"\n--- Enrichment summary ---")
    print(f"  Fetched:  {len(fetched_profiles)} profiles")
    print(f"  Skipped:  {len(to_fetch) - len(fetched_profiles)} (fetch errors)")
    print(f"  Cache:    {cache.stats()['fresh_entries']} fresh entries total")

    return 0


if __name__ == "__main__":
    sys.exit(main())
