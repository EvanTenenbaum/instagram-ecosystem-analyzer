"""Multi-target Instagram collection orchestrator.

Runs sequential collection across multiple target accounts, namespacing raw
data into data/raw/{target}/ and manifest into data/raw/multi_target_manifest.json.
Playwright is imported lazily so dry_run and unit tests never require a browser.
"""

import copy
import json
import logging
import random
import time
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class MultiTargetCollector:
    """Orchestrate collection for multiple Instagram target accounts.

    Each target's raw data is written to data/raw/{target}/ to avoid
    collisions with single-target runs and with other targets.

    Usage::

        collector = MultiTargetCollector(config, ["alice", "bob"], limit=5)

        # Dry-run: creates directories, skips browser
        results = collector.collect_all(dry_run=True)

        # Real run: launches Playwright for each target sequentially
        results = collector.collect_all()
    """

    #: Seconds to pause between targets (chosen randomly in this range)
    INTER_TARGET_PAUSE_MIN = 30
    INTER_TARGET_PAUSE_MAX = 60

    def __init__(self, config: dict, targets: list, limit: int = 10):
        """Initialise the collector.

        Args:
            config: Base configuration dict (will be deep-copied per target).
            targets: List of Instagram usernames to collect.
            limit: Maximum posts to collect per target.
        """
        self.config = config
        self.targets = list(targets)
        self.limit = limit
        self.manifest_path = Path("data/raw/multi_target_manifest.json")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def collect_all(self, skip_existing: bool = False, dry_run: bool = False,
                    quick: bool = False) -> dict:
        """Run collection for every target in sequence.

        Args:
            skip_existing: If True, skip targets that already have data files.
            dry_run: If True, create directories but do not launch browser.
            quick: If True, Phase 0+1 only — skip Phase 2/3 enrichment (~3-5 min/target).

        Returns:
            Dict mapping each target username to its status dict.
        """
        results = {}

        for idx, target in enumerate(self.targets):
            # Conservative inter-target pause (skip before first and in dry_run)
            if idx > 0 and not dry_run:
                delay = random.randint(
                    self.INTER_TARGET_PAUSE_MIN, self.INTER_TARGET_PAUSE_MAX
                )
                logger.info(
                    f"Pausing {delay}s before collecting target {idx + 1}/{len(self.targets)}: {target}"
                )
                time.sleep(delay)

            logger.info(
                f"Collecting target {idx + 1}/{len(self.targets)}: {target}"
            )
            results[target] = self.collect_single(
                target, skip_existing=skip_existing, dry_run=dry_run, quick=quick
            )

        self._save_manifest(results)
        return results

    def collect_single(
        self, target: str, skip_existing: bool = False, dry_run: bool = False,
        quick: bool = False
    ) -> dict:
        """Collect one target account.

        Args:
            target: Instagram username to collect.
            skip_existing: Skip if data files already exist for this target.
            dry_run: Create directories but skip browser launch.
            quick: If True, use collect_quick() (Phase 0+1 only, no Phase 3).

        Returns:
            Status dict with keys: status, target, data_dir, files_written, enrichment_status.
        """
        target_dir = Path("data/raw") / target
        target_dir.mkdir(parents=True, exist_ok=True)

        if dry_run:
            logger.info(f"[dry_run] Skipping browser collection for {target}")
            return {
                "status": "dry_run",
                "target": target,
                "data_dir": str(target_dir),
                "files_written": 0,
                "enrichment_status": "none" if quick else "complete",
                "timestamp": datetime.now().isoformat(),
            }

        existing_files = list(target_dir.glob("*.json"))
        if skip_existing and existing_files:
            logger.info(
                f"Skipping {target}: {len(existing_files)} existing file(s) found"
            )
            return {
                "status": "skipped",
                "target": target,
                "data_dir": str(target_dir),
                "files_written": len(existing_files),
                "enrichment_status": "unknown",
                "timestamp": datetime.now().isoformat(),
            }

        # Build per-target config
        target_config = copy.deepcopy(self.config)
        target_config["target_account"] = target
        target_config["collection"]["max_posts"] = self.limit

        try:
            # Lazy import — keeps dry_run/test paths free of playwright dep
            from src.collectors.playwright_collector import PlaywrightCollector

            class _NamespacedCollector(PlaywrightCollector):
                """PlaywrightCollector that writes to a per-target raw-data dir."""

                def __init__(self_, config, raw_data_dir: Path):  # noqa: N805
                    super().__init__(config)
                    self_.raw_data_dir = raw_data_dir
                    self_.raw_data_dir.mkdir(parents=True, exist_ok=True)

            collector = _NamespacedCollector(target_config, target_dir)

            if quick:
                collector.collect_quick()
                enrichment_status = "none"
            else:
                collector.collect()
                enrichment_status = "complete"

            files_written = len(list(target_dir.glob("*.json")))
            logger.info(
                f"Completed {target}: {files_written} file(s) written to {target_dir}"
            )
            return {
                "status": "complete",
                "target": target,
                "data_dir": str(target_dir),
                "files_written": files_written,
                "enrichment_status": enrichment_status,
                "timestamp": datetime.now().isoformat(),
            }

        except Exception as exc:
            logger.error(f"Collection failed for {target}: {exc}")
            return {
                "status": "error",
                "target": target,
                "data_dir": str(target_dir),
                "files_written": 0,
                "enrichment_status": "error",
                "error": str(exc),
                "timestamp": datetime.now().isoformat(),
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _save_manifest(self, results: dict) -> None:
        """Write multi_target_manifest.json summarising this run."""
        self.manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest = {
            "generated_at": datetime.now().isoformat(),
            "targets": self.targets,
            "limit_per_target": self.limit,
            "results": results,
        }
        with open(self.manifest_path, "w") as f:
            json.dump(manifest, f, indent=2)
        logger.info(f"Manifest written to {self.manifest_path}")
