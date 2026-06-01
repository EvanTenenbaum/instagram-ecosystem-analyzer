"""Cross-network analysis for multi-target Instagram collection.

Loads per-target account score files produced by AccountScorer, identifies
accounts that appear in two or more target networks ("super accounts"), scores
them by cross-network reach, and generates prioritised CSV + markdown outputs.
"""

import csv
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class CrossNetworkAnalyzer:
    """Identify and rank accounts that appear in multiple target networks.

    Workflow::

        analyzer = CrossNetworkAnalyzer(["alice", "bob"])
        result = analyzer.run()
        # result["super_accounts"] — ranked list of dicts
        # result["files_saved"]    — output file paths
        # result["stats"]          — summary counts
    """

    def __init__(self, targets: list, processed_base_dir: str = "data/processed"):
        """Initialise the analyser.

        Args:
            targets: List of target Instagram usernames that were analysed.
            processed_base_dir: Root directory for per-target processed data.
                Each target's scores are expected at
                ``{processed_base_dir}/{target}/account_scores_*.json``.
        """
        self.targets = list(targets)
        self.processed_base_dir = Path(processed_base_dir)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def load_target_scores(self, target: str) -> list:
        """Load scored accounts for a single target.

        Reads the most-recent ``account_scores_*.json`` file from the target's
        processed directory.  Returns an empty list if no file exists rather
        than raising so callers can proceed gracefully.

        Args:
            target: Instagram username of the target network.

        Returns:
            List of scored-account dicts (may be empty).
        """
        target_dir = self.processed_base_dir / target
        if not target_dir.exists():
            logger.warning(f"Processed directory not found for target '{target}': {target_dir}")
            return []

        score_files = sorted(target_dir.glob("account_scores_*.json"))
        if not score_files:
            logger.warning(f"No account_scores_*.json files found for target '{target}'")
            return []

        latest = score_files[-1]
        try:
            with open(latest) as f:
                data = json.load(f)
            scores = data.get("scores", [])
            logger.info(f"Loaded {len(scores)} scores for '{target}' from {latest.name}")
            return scores
        except Exception as exc:
            logger.error(f"Failed to load scores for '{target}' from {latest}: {exc}")
            return []

    # ------------------------------------------------------------------
    # Core analysis
    # ------------------------------------------------------------------

    def find_super_accounts(self) -> list:
        """Identify accounts appearing in two or more target networks.

        Scoring formula (cross_network_score, 0–100):
            ``(networks_count / total_targets * 60) + (avg_overall_score / 100 * 40)``

        Tier assignment:
            - **A**: networks_count ≥ 3  OR  cross_network_score ≥ 70
            - **B**: networks_count ≥ 2  OR  cross_network_score ≥ 40
            - **C**: everything else

        Returns:
            List of super-account dicts sorted by cross_network_score descending.
            Each dict contains the columns documented in the module docstring.
        """
        total_targets = len(self.targets)
        if total_targets == 0:
            return []

        # Build {target: {username: score_dict}} lookup
        target_scores: dict[str, dict[str, dict]] = {}
        for target in self.targets:
            scores = self.load_target_scores(target)
            target_scores[target] = {s["username"]: s for s in scores if "username" in s}

        # Union of all usernames across every network
        all_usernames: set[str] = set()
        for scores in target_scores.values():
            all_usernames.update(scores.keys())

        super_accounts = []

        for username in all_usernames:
            # Networks where this account has a score
            networks = [t for t in self.targets if username in target_scores[t]]

            if len(networks) < 2:
                continue  # Does not meet the "super account" threshold

            scores_in_networks = [target_scores[t][username] for t in networks]

            avg_overall = (
                sum(s.get("overall_score", 0) for s in scores_in_networks) / len(networks)
            )
            max_overall = max(s.get("overall_score", 0) for s in scores_in_networks)
            avg_proximity = (
                sum(s.get("proximity_score", 0) for s in scores_in_networks) / len(networks)
            )
            avg_engagement = (
                sum(s.get("engagement_score", 0) for s in scores_in_networks) / len(networks)
            )
            avg_bridge = (
                sum(s.get("bridge_score", 0) for s in scores_in_networks) / len(networks)
            )
            categories = sorted(
                set(s.get("category", "unknown") for s in scores_in_networks)
            )

            # Cross-network score: 60 % weight on breadth, 40 % on quality
            cross_network_score = (
                (len(networks) / total_targets * 60) + (avg_overall / 100 * 40)
            )

            # Tier
            if len(networks) >= 3 or cross_network_score >= 70:
                tier = "A"
            elif len(networks) >= 2 or cross_network_score >= 40:
                tier = "B"
            else:
                tier = "C"

            super_accounts.append(
                {
                    "username": username,
                    "networks_count": len(networks),
                    "networks_list": ",".join(sorted(networks)),
                    "cross_network_score": round(cross_network_score, 2),
                    "avg_overall_score": round(avg_overall, 2),
                    "max_overall_score": round(max_overall, 2),
                    "avg_proximity": round(avg_proximity, 2),
                    "avg_engagement": round(avg_engagement, 2),
                    "avg_bridge": round(avg_bridge, 2),
                    "categories": ",".join(categories),
                    "tier": tier,
                }
            )

        super_accounts.sort(key=lambda x: x["cross_network_score"], reverse=True)
        logger.info(f"Found {len(super_accounts)} super accounts across {len(self.targets)} targets")
        return super_accounts

    # ------------------------------------------------------------------
    # Output generation
    # ------------------------------------------------------------------

    def generate_summary(self, super_accounts: list) -> str:
        """Generate a markdown summary of cross-network findings.

        Args:
            super_accounts: Ranked super-account list from find_super_accounts().

        Returns:
            Markdown string suitable for writing to a .md file.
        """
        target_list = ", ".join(self.targets)
        lines = [
            "# Cross-Network Analysis Summary",
            f"## {len(self.targets)} targets analyzed: {target_list}",
            "",
            "## Key Finding: Super Accounts (appear in 2+ networks)",
            f"{len(super_accounts)} super accounts identified.",
            "",
        ]

        tier_a = [a for a in super_accounts if a["tier"] == "A"]
        tier_b = [a for a in super_accounts if a["tier"] == "B"]

        def _account_table(accounts: list) -> str:
            if not accounts:
                return "_None identified._"
            rows = [
                "| Username | Networks | Score | Categories |",
                "|----------|----------|-------|------------|",
            ]
            for a in accounts:
                rows.append(
                    f"| {a['username']} | {a['networks_count']} ({a['networks_list']}) "
                    f"| {a['cross_network_score']:.1f} | {a['categories'] or 'unknown'} |"
                )
            return "\n".join(rows)

        lines += [
            "## Tier A Super Accounts (highest priority)",
            _account_table(tier_a),
            "",
            "## Tier B Super Accounts",
            _account_table(tier_b),
            "",
            "## Strategic Implications",
        ]

        if super_accounts:
            lines.append(
                f"- {len(super_accounts)} accounts appear in multiple target networks, "
                "indicating cross-community influence."
            )
            if tier_a:
                top_names = ", ".join(a["username"] for a in tier_a[:3])
                lines.append(f"- Priority engagement targets (Tier A): {top_names}")
            if tier_b:
                top_b = ", ".join(a["username"] for a in tier_b[:5])
                lines.append(f"- Secondary engagement targets (Tier B): {top_b}")
            # Network with most overlap
            network_counts: dict[str, int] = {}
            for a in super_accounts:
                for net in a["networks_list"].split(","):
                    network_counts[net] = network_counts.get(net, 0) + 1
            if network_counts:
                top_net = max(network_counts, key=network_counts.get)  # type: ignore[arg-type]
                lines.append(
                    f"- '{top_net}' has the most cross-network accounts "
                    f"({network_counts[top_net]} shared)."
                )
        else:
            lines.append(
                "- No super accounts found — targets appear to operate in disjoint networks."
            )

        # Per-target overview (populated if we have score data)
        lines += ["", "## Per-Target Network Overview"]
        for target in self.targets:
            scores = self.load_target_scores(target)
            if scores:
                top5 = scores[:5]
                top5_str = ", ".join(s["username"] for s in top5)
                lines.append(
                    f"\n### {target}  \n"
                    f"Network size: {len(scores)} scored accounts  \n"
                    f"Top 5: {top5_str}"
                )
            else:
                lines.append(f"\n### {target}  \n_No score data available._")

        return "\n".join(lines) + "\n"

    def save_outputs(
        self, super_accounts: list, summary: str, output_dir: str = "outputs"
    ) -> dict:
        """Write super_accounts.csv and cross_network_summary.md.

        Args:
            super_accounts: Ranked list from find_super_accounts().
            summary: Markdown string from generate_summary().
            output_dir: Directory for output files.

        Returns:
            Dict with file path keys: ``super_accounts_csv``,
            ``cross_network_summary``.
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # CSV
        csv_path = out / f"super_accounts_{timestamp}.csv"
        fieldnames = [
            "username",
            "networks_count",
            "networks_list",
            "cross_network_score",
            "avg_overall_score",
            "max_overall_score",
            "avg_proximity",
            "avg_engagement",
            "avg_bridge",
            "categories",
            "tier",
        ]
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(super_accounts)
        logger.info(f"Saved super accounts CSV: {csv_path}")

        # Markdown
        md_path = out / f"cross_network_summary_{timestamp}.md"
        with open(md_path, "w") as f:
            f.write(summary)
        logger.info(f"Saved cross-network summary: {md_path}")

        return {
            "super_accounts_csv": str(csv_path),
            "cross_network_summary": str(md_path),
        }

    # ------------------------------------------------------------------
    # Main entry point
    # ------------------------------------------------------------------

    def run(self) -> dict:
        """Execute full cross-network analysis pipeline.

        Returns:
            Dict with keys:
                - ``super_accounts``: ranked list
                - ``files_saved``: output file paths
                - ``stats``: summary counts
        """
        logger.info(
            f"Starting cross-network analysis for {len(self.targets)} targets: "
            + ", ".join(self.targets)
        )

        super_accounts = self.find_super_accounts()
        summary = self.generate_summary(super_accounts)
        files_saved = self.save_outputs(super_accounts, summary)

        tier_counts = {"A": 0, "B": 0, "C": 0}
        for a in super_accounts:
            tier_counts[a["tier"]] = tier_counts.get(a["tier"], 0) + 1

        stats = {
            "total_targets": len(self.targets),
            "total_super_accounts": len(super_accounts),
            "tier_a": tier_counts["A"],
            "tier_b": tier_counts["B"],
            "tier_c": tier_counts["C"],
        }

        logger.info(
            f"Cross-network analysis complete: {stats['total_super_accounts']} super accounts "
            f"(A={stats['tier_a']}, B={stats['tier_b']})"
        )
        return {
            "super_accounts": super_accounts,
            "files_saved": files_saved,
            "stats": stats,
        }
