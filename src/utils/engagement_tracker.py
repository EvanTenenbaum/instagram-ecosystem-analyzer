"""Engagement tracker data model and persistence.

Handles reading/writing the engagement_tracker.json file and provides
helper methods for status checks, checklist management, and weekly reports.

Usage::

    from src.utils.engagement_tracker import EngagementTracker

    tracker = EngagementTracker("evan_tenenbaum")
    tracker.log_engagement("jbblunkestate", "comment", date="2026-06-01", substantive=True)
    tracker.check_off_week("blunk_space_comment")
    status = tracker.get_status()
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class EngagementTracker:
    """Manage artist engagement tracking data."""

    DEFAULT_VISIBILITY_THRESHOLDS: dict[str, int] = {
        "jbblunkestate": 6,
        "coupdetatsf": 4,
        "sarah_myerscough": 6,
        "thefutureperfect": 4,
        "johansson_projects": 4,
        "rebeccacamachopresents": 4,
        "anthony_meier_": 4,
        "hosfeltgallery": 4,
        "hostlerburrows": 4,
        "anglimtrimble": 4,
        "hainesgallery": 4,
        "donnaseagerfinearts": 4,
        "renacharlesgallery": 4,
        "transmissiongallery": 4,
        "paulmahdergallery": 4,
        "staffordartgal": 4,
        "museumofcraftanddesign": 4,
        "woodsymphony": 4,
        "paradiseridgewinery": 4,
        "friedmanbenda": 4,
    }

    def __init__(
        self,
        artist_username: str,
        tracker_file: str = "data/engagement_tracker.json",
    ):
        self.artist_username = artist_username
        self.tracker_file = Path(tracker_file)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load(self) -> dict:
        """Load the engagement tracker JSON file.

        Returns:
            Dict with tracker data, or a fresh default dict if file doesn't exist.
        """
        if not self.tracker_file.exists():
            return self._default_data()

        try:
            with open(self.tracker_file) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Could not read tracker file, starting fresh: %s", exc)
            return self._default_data()

        # Ensure key structure exists
        data.setdefault("artist_username", self.artist_username)
        data.setdefault("targets", {})
        data.setdefault("super_accounts", {})
        data.setdefault("weekly_checklist", {})
        return data

    def save(self, data: dict) -> None:
        """Persist tracker data to JSON file."""
        self.tracker_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.tracker_file, "w") as f:
            json.dump(data, f, indent=2, default=str)

    def _default_data(self) -> dict:
        return {
            "artist_username": self.artist_username,
            "targets": {},
            "super_accounts": {},
            "weekly_checklist": {},
        }

    # ------------------------------------------------------------------
    # Engagement logging
    # ------------------------------------------------------------------

    def log_engagement(
        self,
        target: str,
        engagement_type: str,
        date: str = None,
        substantive: bool = False,
        post_url: str = None,
    ) -> dict:
        """Log an engagement interaction with a target or peer.

        Args:
            target: Username of the account engaged with.
            engagement_type: One of 'comment', 'like', 'dm', 'share', 'mention'.
            date: ISO date string (defaults to today in UTC).
            substantive: Whether this was a meaningful comment.
            post_url: Optional URL of the specific post engaged with.

        Returns:
            Updated data dict.
        """
        data = self.load()
        date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        # Initialize target entry if needed
        if target not in data["targets"]:
            data["targets"][target] = {
                "target_name": target,
                "visibility_threshold": self.DEFAULT_VISIBILITY_THRESHOLDS.get(target, 4),
                "comments_this_month": [],
                "engagements_this_month": [],
                "last_engagement": None,
                "status": "not_started",
            }

        entry = data["targets"][target]

        if engagement_type == "comment":
            entry["comments_this_month"].append(
                {
                    "date": date,
                    "post_url": post_url,
                    "substantive": substantive,
                }
            )

        entry["engagements_this_month"].append(
            {"date": date, "type": engagement_type, "substantive": substantive}
        )
        entry["last_engagement"] = date

        # Determine status
        substantive_count = len(entry["comments_this_month"])
        threshold = entry["visibility_threshold"]
        if substantive_count >= threshold:
            entry["status"] = "visible"
        elif substantive_count >= threshold * 0.5:
            entry["status"] = "building"
        elif substantive_count > 0:
            entry["status"] = "starting"
        else:
            entry["status"] = "not_started"

        self.save(data)
        return data

    # ------------------------------------------------------------------
    # Super account interactions
    # ------------------------------------------------------------------

    def log_super_interaction(self, username: str, date: str = None) -> dict:
        """Log an interaction with a super account / peer."""
        data = self.load()
        date = date or datetime.now(timezone.utc).strftime("%Y-%m-%d")

        if username not in data["super_accounts"]:
            data["super_accounts"][username] = {
                "interactions_this_month": 0,
                "last_interaction": None,
            }

        entry = data["super_accounts"][username]
        entry["interactions_this_month"] = entry.get("interactions_this_month", 0) + 1
        entry["last_interaction"] = date

        self.save(data)
        return data

    # ------------------------------------------------------------------
    # Weekly checklist
    # ------------------------------------------------------------------

    def get_week_key(self) -> str:
        """Get current ISO week key like '2026-W22'."""
        return datetime.now(timezone.utc).strftime("%G-W%V")

    def check_off_week(self, *items: str, week_key: str = None) -> dict:
        """Mark checklist items as completed for a given week.

        Args:
            items: Checklist keys (e.g., 'blunk_space_comment', 'process_post').
            week_key: ISO week string (defaults to current week).

        Returns:
            Updated data dict.
        """
        data = self.load()
        wk = week_key or self.get_week_key()

        checklist = data["weekly_checklist"].setdefault(wk, {})
        for item in items:
            checklist[item] = True

        self.save(data)
        return data

    def uncheck_week(self, *items: str, week_key: str = None) -> dict:
        """Remove checklist items for a given week."""
        data = self.load()
        wk = week_key or self.get_week_key()

        checklist = data["weekly_checklist"].setdefault(wk, {})
        for item in items:
            checklist[item] = False

        self.save(data)
        return data

    def get_week_checklist(self, week_key: str = None) -> dict:
        """Get checklist state for a given week."""
        data = self.load()
        wk = week_key or self.get_week_key()
        return data.get("weekly_checklist", {}).get(wk, {})

    # ------------------------------------------------------------------
    # Status / reporting
    # ------------------------------------------------------------------

    def get_status(self) -> dict:
        """Get current engagement status summary.

        Returns:
            Dict with targets, super_accounts, weekly_checklist, and overall assessment.
        """
        data = self.load()

        # Build target statuses
        target_statuses = {}
        for name, entry in data.get("targets", {}).items():
            substantive = len(entry.get("comments_this_month", []))
            threshold = entry.get("visibility_threshold", 4)
            need = max(0, threshold - substantive)
            status = entry.get("status", "not_started")

            if status == "visible":
                next_action = "✓ Visibility threshold met — maintain consistency"
            elif status == "building":
                next_action = f"{need} more substantive comments to reach visibility"
            elif status == "starting":
                next_action = f"{need} more substantive comments needed (just getting started)"
            else:
                next_action = "Start commenting now"

            target_statuses[name] = {
                "threshold": threshold,
                "substantive_comments": substantive,
                "need": need,
                "status": status,
                "next_action": next_action,
                "last_engagement": entry.get("last_engagement"),
            }

        # Super account statuses
        sa_statuses = {}
        for name, entry in data.get("super_accounts", {}).items():
            interactions = entry.get("interactions_this_month", 0)
            if interactions >= 3:
                sa_status = "strong"
            elif interactions >= 1:
                sa_status = "building"
            else:
                sa_status = "not_yet_started"
            sa_statuses[name] = {
                "interactions": interactions,
                "status": sa_status,
                "last_interaction": entry.get("last_interaction"),
            }

        # Current week checklist
        current_week = self.get_week_key()
        week_checklist = data.get("weekly_checklist", {}).get(current_week, {})

        # Overall assessment
        total_targets = len(target_statuses)
        visible = sum(1 for v in target_statuses.values() if v["status"] == "visible")
        building = sum(1 for v in target_statuses.values() if v["status"] == "building")
        invisible = sum(1 for v in target_statuses.values() if v["status"] in ("starting", "not_started"))

        progress_pct = (
            round(visible / total_targets * 100) if total_targets > 0 else 0
        )

        # Find biggest gap
        biggest_gap = None
        max_need = 0
        for name, ts in target_statuses.items():
            if ts["need"] > max_need and ts["status"] != "visible":
                max_need = ts["need"]
                biggest_gap = name

        assessment = {
            "total_targets": total_targets,
            "visible": visible,
            "building": building,
            "invisible": invisible,
            "progress_pct": progress_pct,
            "biggest_gap": biggest_gap,
            "biggest_gap_need": max_need,
            "recommendation": "",
        }

        if biggest_gap:
            assessment[
                "recommendation"
            ] = f"Add {biggest_gap} to weekly checklist immediately"

        return {
            "artist_username": self.artist_username,
            "targets": target_statuses,
            "super_accounts": sa_statuses,
            "weekly_checklist": week_checklist,
            "current_week": current_week,
            "assessment": assessment,
        }

    def format_status(self) -> str:
        """Format current engagement status as a readable text report."""
        status = self.get_status()
        lines = []
        lines.append("=" * 80)
        lines.append(f"ENGAGEMENT TRACKER — @{status['artist_username']}")
        lines.append("=" * 80)
        lines.append("")

        # Visibility progress
        now = datetime.now(timezone.utc)
        lines.append(f"VISIBILITY PROGRESS ({now.strftime('%B %Y')})")
        lines.append(f"  {'Gallery':<28} {'Need':<6} {'Have':<6} {'Status':<12} Next Action")
        lines.append("  " + "─" * 76)

        status_order = {
            "not_started": 0,
            "starting": 1,
            "building": 2,
            "visible": 3,
        }
        sorted_targets = sorted(
            status["targets"].items(),
            key=lambda x: (status_order.get(x[1]["status"], 0), -x[1]["threshold"]),
        )

        for name, ts in sorted_targets:
            status_icon = {
                "visible": "VISIBLE",
                "building": "BUILDING",
                "starting": "STARTING",
                "not_started": "INVISIBLE",
            }.get(ts["status"], ts["status"].upper())
            lines.append(
                f"  @{name:<27} {ts['threshold']:<6} {ts['substantive_comments']:<6} "
                f"{status_icon:<12} {ts['next_action']}"
            )

        # Peer relationships
        lines.append("")
        lines.append("PEER RELATIONSHIPS")
        if not status["super_accounts"]:
            lines.append("  No peer interactions logged yet.")
        else:
            for name, sa in status["super_accounts"].items():
                sa_status = {
                    "strong": "STRONG (good)",
                    "building": "BUILDING (good)",
                    "not_yet_started": "NOT YET STARTED",
                }.get(sa["status"], sa["status"])
                lines.append(
                    f"  @{name:<30} {sa['interactions']} interactions → {sa_status}"
                )

        # Weekly checklist
        lines.append("")
        lines.append(f"WEEKLY DISCIPLINE ({status['current_week']})")
        checklist = status.get("weekly_checklist", {})
        checklist_labels = {
            "blunk_space_comment": "Commented on Blunk Space post",
            "coup_detat_comment": "Commented on Coup D'Etat post",
            "peer_engagement": "Engaged with peer artist",
            "process_post": "Posted process content",
            "gallery_comment": "Commented on gallery post",
            "dm_outreach": "Sent DM / outreach",
        }
        if not checklist:
            lines.append("  No checklist items recorded this week.")
        else:
            for key, label in checklist_labels.items():
                checked = checklist.get(key, False)
                icon = "✅" if checked else "❌"
                if key in checklist:
                    lines.append(f"  {icon} {label}")

        # Overall assessment
        lines.append("")
        lines.append("OVERALL ASSESSMENT")
        assessment = status["assessment"]
        lines.append(
            f"  Progress: {assessment['progress_pct']}% toward visibility across "
            f"{assessment['total_targets']} galleries"
        )
        if assessment["biggest_gap"]:
            lines.append(
                f"  Biggest gap: @{assessment['biggest_gap']} "
                f"({assessment['biggest_gap_need']} more comments needed)"
            )
        lines.append(f"  Recommendation: {assessment['recommendation']}")
        lines.append("")

        return "\n".join(lines)

    def format_report(self) -> str:
        """Generate a weekly engagement report (same as status for now)."""
        return self.format_status()
