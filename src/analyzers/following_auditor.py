"""Following list auditor — compare artist's follows to strategic ecosystem.

Usage::

    auditor = FollowingAuditor(artist_username="evan_tenenbaum")
    strategic = auditor.build_strategic_lists(
        targets=["jbblunkestate", "coupdetatsf"],
        super_accounts_csv="outputs/super_accounts_20260602_100156.csv",
    )
    result = auditor.audit(strategic)
    # result["coverage"], result["missing"], result["followed"]
"""

import csv
import json
import logging
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)


class FollowingAuditor:
    """Compare an artist's following list against strategic ecosystem accounts.

    The artist username is passed as a parameter (no hardcoded default) so the
    library code stays generic.  Defaults live only in the CLI argparse layer.
    """

    def __init__(self, artist_username: str, data_dir: str = "data/raw"):
        self.artist_username = artist_username
        self.data_dir = Path(data_dir)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def load_artist_following(self) -> list[str]:
        """Load the artist's following list from data/raw/{artist}/phase2_following_*.json.

        Returns:
            List of usernames the artist follows (may be empty if no data collected).
        """
        artist_dir = self.data_dir / self.artist_username
        if not artist_dir.exists():
            logger.warning(
                "Artist data directory not found: %s. "
                "Run collection first: python scripts/collect_multi.py --targets %s",
                artist_dir,
                self.artist_username,
            )
            return []

        following_files = sorted(artist_dir.glob("phase2_following_*.json"))
        if not following_files:
            logger.warning(
                "No phase2_following_*.json found for %s. "
                "Run collection with following-list collection enabled.",
                self.artist_username,
            )
            return []

        latest = following_files[-1]
        try:
            with open(latest) as f:
                data = json.load(f)
        except Exception as exc:
            logger.error("Failed to load following data from %s: %s", latest, exc)
            return []

        following = data.get("following", [])
        if isinstance(following, list):
            return [str(u) for u in following if u]
        return []

    def load_super_accounts(self, csv_path: str) -> list[dict]:
        """Load super accounts from a CrossNetworkAnalyzer CSV export.

        Args:
            csv_path: Path to super_accounts_*.csv file.

        Returns:
            List of super-account dicts with keys: username, networks_count,
            networks_list, cross_network_score, tier, etc.
        """
        path = Path(csv_path)
        if not path.exists():
            logger.warning("Super accounts CSV not found: %s", csv_path)
            return []

        try:
            with open(path, newline="") as f:
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as exc:
            logger.error("Failed to load super accounts CSV %s: %s", csv_path, exc)
            return []

    # ------------------------------------------------------------------
    # Strategic list building
    # ------------------------------------------------------------------

    def build_strategic_lists(
        self,
        targets: list[str],
        super_accounts_csv: str = None,
        known_accounts: list[str] = None,
    ) -> dict:
        """Build categorized strategic lists from all available sources.

        Categories:
            - target_galleries: Gallery accounts the artist should follow
            - super_accounts: High-value cross-network accounts
            - peer_artists: Known peer artists / connectors
            - major_institutions: Museums, fairs, design weeks
            - design_collectors: Design collectors / curators

        Returns:
            Dict mapping category name -> list of dicts with at least
            ``username`` and ``reason`` keys.  Some entries include
            extra metadata (follower_count, networks, tier, etc.).
        """
        strategic: dict[str, list[dict]] = {
            "target_galleries": [],
            "super_accounts": [],
            "peer_artists": [],
            "major_institutions": [],
            "design_collectors": [],
        }

        seen = set()

        # --- Target galleries ---
        institutional_keywords = {
            "museum", "foundation", "institute", "trust", "fair",
            "design week", "magazine", "publication",
        }
        peer_keywords = {"artist", "wood_artist", "craft_artist", "furniture_designer"}
        collector_keywords = {"collector", "curator"}

        for target in targets:
            if target in seen:
                continue
            seen.add(target)
            # Try to load follower count from profile data
            follower_count = self._load_follower_count(target)
            strategic["target_galleries"].append(
                {
                    "username": target,
                    "reason": "Target gallery",
                    "follower_count": follower_count,
                }
            )

        # --- Super accounts ---
        if super_accounts_csv:
            super_accounts = self.load_super_accounts(super_accounts_csv)
            for sa in super_accounts:
                username = sa.get("username", "")
                if not username or username in seen:
                    continue
                seen.add(username)

                networks_count = int(sa.get("networks_count", 0))
                tier = sa.get("tier", "C")
                category_str = sa.get("categories", "unknown")

                entry = {
                    "username": username,
                    "reason": f"Super account (tier {tier}, {networks_count} networks)",
                    "networks_count": networks_count,
                    "tier": tier,
                    "cross_network_score": float(sa.get("cross_network_score", 0)),
                    "categories": category_str,
                }
                # Always include in super_accounts
                strategic["super_accounts"].append(entry)

                # Also slot into relevant sub-categories
                cats_lower = category_str.lower()
                if any(kw in cats_lower for kw in institutional_keywords):
                    strategic["major_institutions"].append(entry)
                elif any(kw in cats_lower for kw in collector_keywords):
                    strategic["design_collectors"].append(entry)
                elif any(kw in cats_lower for kw in peer_keywords):
                    strategic["peer_artists"].append(entry)

        # --- Known accounts (from config) ---
        if known_accounts:
            for username in known_accounts:
                if username in seen:
                    continue
                seen.add(username)
                strategic["major_institutions"].append(
                    {"username": username, "reason": "Known strategic account"}
                )

        return strategic

    def _load_follower_count(self, username: str) -> int:
        """Try to load follower_count from a target's phase0_profile JSON."""
        target_dir = self.data_dir / username
        if not target_dir.exists():
            return 0
        profile_files = sorted(target_dir.glob("phase0_profile_*.json"))
        if not profile_files:
            return 0
        try:
            with open(profile_files[-1]) as f:
                data = json.load(f)
            return data.get("profile", {}).get("follower_count", 0)
        except Exception:
            return 0

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    def audit(self, strategic_lists: dict) -> dict:
        """Compare artist's following list against strategic lists.

        Args:
            strategic_lists: Output of build_strategic_lists().

        Returns:
            Dict with keys:
                - coverage: {category: {followed, total, pct}}
                - missing: {category: [dict with username, reason, priority_score]}
                - followed: {category: [username]}
        """
        following = set(self.load_artist_following())
        has_data = len(following) > 0

        result: dict = {
            "coverage": {},
            "missing": {},
            "followed": {},
            "has_following_data": has_data,
        }

        for category, accounts in strategic_lists.items():
            if not accounts:
                result["coverage"][category] = {"followed": 0, "total": 0, "pct": 0.0}
                result["missing"][category] = []
                result["followed"][category] = []
                continue

            usernames = [a["username"] for a in accounts]
            followed_set = following & set(usernames)
            missing_set = set(usernames) - following

            total = len(accounts)
            followed_count = len(followed_set)
            pct = (followed_count / total * 100) if total > 0 else 0.0

            result["coverage"][category] = {
                "followed": followed_count,
                "total": total,
                "pct": round(pct, 1),
            }

            # Build missing list sorted by priority
            missing_entries = []
            for a in accounts:
                if a["username"] in missing_set:
                    entry = dict(a)
                    entry["priority_score"] = self.priority_score(
                        a["username"], strategic_lists
                    )
                    missing_entries.append(entry)

            missing_entries.sort(key=lambda x: x["priority_score"], reverse=True)
            result["missing"][category] = missing_entries
            result["followed"][category] = sorted(followed_set)

        return result

    def priority_score(self, username: str, strategic_lists: dict) -> float:
        """Calculate a priority score for following this account.

        Higher = more important to follow.

        Heuristic:
            +10  Tier A super account (3+ networks)
            +5   Tier B super account (2+ networks)
            +3   Target gallery account
            +2   In engagement top-5 of any target (not yet implemented)
            +1   Known institutional account
            + (follower_count / 10000) small bonus for major accounts
        """
        score = 0.0

        # Check if in super accounts
        for sa in strategic_lists.get("super_accounts", []):
            if sa["username"] == username:
                tier = sa.get("tier", "")
                if tier == "A":
                    score += 10
                elif tier == "B":
                    score += 5
                break

        # Check if target gallery
        for tg in strategic_lists.get("target_galleries", []):
            if tg["username"] == username:
                score += 3
                fc = tg.get("follower_count", 0)
                if isinstance(fc, (int, float)):
                    score += fc / 10000
                break

        # Check if known institutional
        for inst in strategic_lists.get("major_institutions", []):
            if inst["username"] == username:
                score += 1
                break

        return round(score, 2)

    # ------------------------------------------------------------------
    # Output formatting
    # ------------------------------------------------------------------

    def format_report(self, audit_result: dict) -> str:
        """Format audit result as a readable text report.

        Args:
            audit_result: Output of audit().

        Returns:
            Multi-line string suitable for console or markdown output.
        """
        lines = []
        lines.append("=" * 80)
        lines.append(f"FOLLOWING LIST AUDIT for @{self.artist_username}")
        lines.append("=" * 80)
        lines.append("")

        if not audit_result.get("has_following_data"):
            lines.append(
                "⚠️  No following data found for this artist.\n"
                "   Run collection first:\n"
                f"     python scripts/collect.py --target {self.artist_username} --phase following\n"
                "   Or collect multi-target data that includes this account."
            )
            lines.append("")
            lines.append(
                "--- Strategic lists (what you SHOULD be following) ---"
            )
            lines.append("")
            for category, accounts in {
                "target_galleries": "TARGET GALLERIES",
                "super_accounts": "SUPER ACCOUNTS",
                "peer_artists": "PEER ARTISTS",
                "major_institutions": "MAJOR INSTITUTIONS",
                "design_collectors": "DESIGN COLLECTORS",
            }.items():
                entries = audit_result.get("missing", {}).get(category, [])
                if not entries:
                    continue
                total = audit_result.get("coverage", {}).get(category, {}).get("total", len(entries))
                lines.append(f"  {accounts} ({len(entries)} accounts to follow)")
                for entry in entries[:10]:
                    username = entry.get("username", "?")
                    reason = entry.get("reason", "")
                    lines.append(f"    @{username} — {reason}")
                if len(entries) > 10:
                    lines.append(f"    ... and {len(entries) - 10} more")
                lines.append("")
            return "\n".join(lines)

        for category, label in [
            ("target_galleries", "TARGET GALLERIES"),
            ("super_accounts", "SUPER ACCOUNTS"),
            ("peer_artists", "PEER ARTISTS"),
            ("major_institutions", "MAJOR INSTITUTIONS"),
            ("design_collectors", "DESIGN COLLECTORS"),
        ]:
            cov = audit_result["coverage"].get(category, {})
            missing = audit_result["missing"].get(category, [])
            followed_list = audit_result["followed"].get(category, [])

            if cov.get("total", 0) == 0:
                continue

            lines.append(label)
            pct = cov.get("pct", 0)
            bar = "■" * min(int(pct / 10), 10)
            lines.append(
                f"  Following: {cov['followed']} / {cov['total']} ({pct}%)"
            )
            if missing:
                lines.append(f"  Missing {len(missing)} (high priority → {bar}):")
                for entry in missing[:8]:
                    username = entry.get("username", "?")
                    reason = entry.get("reason", "")
                    fc = entry.get("follower_count", 0)
                    fc_str = f" — {fc:,} followers" if fc else ""
                    lines.append(f"    @{username}  [{reason}]{fc_str}")
                if len(missing) > 8:
                    lines.append(f"    ... and {len(missing) - 8} more")
            if followed_list:
                lines.append(f"  Already following ({len(followed_list)}):")
                lines.append(f"    {', '.join(f'@{u}' for u in followed_list[:10])}")
                if len(followed_list) > 10:
                    lines.append(f"    ... and {len(followed_list) - 10} more")
            lines.append("")

        # Immediate action recommendations
        lines.append("RECOMMENDED IMMEDIATE ACTIONS")
        actions = []
        # Missing target galleries sorted by priority
        tg_missing = sorted(
            audit_result["missing"].get("target_galleries", []),
            key=lambda x: x["priority_score"],
            reverse=True,
        )
        if tg_missing:
            top_tg = [f"@{a['username']}" for a in tg_missing[:4]]
            actions.append(f"  1. Follow {' , '.join(top_tg)}")

        # Missing peer artists / high-value super accounts
        sa_missing = sorted(
            audit_result["missing"].get("super_accounts", []),
            key=lambda x: x["priority_score"],
            reverse=True,
        )
        if sa_missing:
            top_sa = [f"@{a['username']}" for a in sa_missing[:3]]
            actions.append(f"  2. Follow {' , '.join(top_sa)}")

        inst_missing = sorted(
            audit_result["missing"].get("major_institutions", []),
            key=lambda x: x["priority_score"],
            reverse=True,
        )
        if inst_missing:
            top_inst = [f"@{a['username']}" for a in inst_missing[:3]]
            actions.append(f"  3. Follow {' , '.join(top_inst)}")

        if not actions:
            actions.append("  ✓ You're following all recommended accounts!")

        lines.extend(actions)
        lines.append("")

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(
        self,
        targets: list[str],
        super_accounts_csv: str = None,
        known_accounts: list[str] = None,
    ) -> dict:
        """Run a full following audit in one call.

        Returns:
            Dict with keys: strategic_lists, audit_result, report.
        """
        strategic = self.build_strategic_lists(
            targets=targets,
            super_accounts_csv=super_accounts_csv,
            known_accounts=known_accounts,
        )
        audit_result = self.audit(strategic)
        report = self.format_report(audit_result)
        return {
            "strategic_lists": strategic,
            "audit_result": audit_result,
            "report": report,
        }
