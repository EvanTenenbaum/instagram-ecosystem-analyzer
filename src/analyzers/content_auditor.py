"""Content auditor — compare artist's content to target network patterns.

Usage::

    auditor = ContentAuditor(
        artist_username="evan_tenenbaum",
        targets=["jbblunkestate", "coupdetatsf"],
    )
    result = auditor.audit()
    # result["hashtag_gaps"], result["posting_pattern"], ...
"""

import json
import logging
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

logger = logging.getLogger(__name__)


class ContentAuditor:
    """Compare an artist's Instagram content strategy to target gallery patterns."""

    def __init__(
        self,
        artist_username: str,
        targets: list[str],
        raw_base_dir: str = "data/raw",
    ):
        self.artist_username = artist_username
        self.targets = list(targets)
        self.raw_base_dir = Path(raw_base_dir)

    # ------------------------------------------------------------------
    # Data loading
    # ------------------------------------------------------------------

    def load_artist_posts(self) -> list[dict]:
        """Load the artist's collected posts from phase1_posts JSON."""
        return self._load_posts(self.artist_username)

    def load_target_posts(self, target: str) -> list[dict]:
        """Load a target gallery's collected posts."""
        return self._load_posts(target)

    def _load_posts(self, username: str) -> list[dict]:
        """Generic post loader for any username."""
        target_dir = self.raw_base_dir / username
        if not target_dir.exists():
            logger.debug("No raw data directory for %s", username)
            return []

        post_files = sorted(target_dir.glob("phase1_posts_*.json"))
        if not post_files:
            logger.debug("No phase1_posts files for %s", username)
            return []

        latest = post_files[-1]
        try:
            with open(latest) as f:
                data = json.load(f)
        except Exception as exc:
            logger.error("Failed to load posts for %s from %s: %s", username, latest, exc)
            return []

        return data.get("posts", [])

    # ------------------------------------------------------------------
    # Metric extraction
    # ------------------------------------------------------------------

    def extract_hashtags(self, posts: list[dict]) -> dict[str, int]:
        """Extract hashtag frequency from post captions.

        Returns:
            {hashtag_lower: count}
        """
        counter: Counter = Counter()
        for post in posts:
            caption = post.get("caption") or ""
            if not caption:
                continue
            # Extract hashtags — match #word sequences
            words = caption.split()
            for w in words:
                if w.startswith("#") and len(w) > 1:
                    tag = w.lstrip("#").rstrip(".,;:!?\"'\n\r").lower()
                    if tag:
                        counter[tag] += 1
        return dict(counter.most_common())

    def extract_posting_pattern(self, posts: list[dict]) -> dict:
        """Extract posting frequency and timing patterns.

        Returns:
            Dict with keys:
                - total_posts: int
                - posts_per_week: float
                - day_of_week: {day_name: count}
                - hour_distribution: {hour: count}
                - first_post: ISO timestamp
                - last_post: ISO timestamp
        """
        if not posts:
            return {
                "total_posts": 0,
                "posts_per_week": 0.0,
                "day_of_week": {},
                "hour_distribution": {},
                "first_post": None,
                "last_post": None,
            }

        timestamps = []
        dow_counter: Counter = Counter()
        hour_counter: Counter = Counter()

        days = [
            "Monday", "Tuesday", "Wednesday", "Thursday",
            "Friday", "Saturday", "Sunday",
        ]

        for post in posts:
            ts_str = post.get("timestamp")
            if not ts_str:
                continue
            try:
                dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                timestamps.append(dt)
                dow_counter[days[dt.weekday()]] += 1
                hour_counter[dt.hour] += 1
            except (ValueError, TypeError):
                continue

        if not timestamps:
            return {
                "total_posts": len(posts),
                "posts_per_week": 0.0,
                "day_of_week": {},
                "hour_distribution": {},
                "first_post": None,
                "last_post": None,
            }

        timestamps.sort()
        span_days = (timestamps[-1] - timestamps[0]).total_seconds() / 86400
        posts_per_week = (
            (len(timestamps) / span_days * 7) if span_days > 0 else 0.0
        )

        return {
            "total_posts": len(posts),
            "posts_per_week": round(posts_per_week, 1),
            "day_of_week": dict(dow_counter.most_common()),
            "hour_distribution": dict(sorted(hour_counter.items())),
            "first_post": timestamps[0].isoformat(),
            "last_post": timestamps[-1].isoformat(),
        }

    def extract_content_type(self, posts: list[dict]) -> dict:
        """Estimate content type distribution.

        Instagram scraping doesn't reliably give us image/video/carousel
        metadata, so we provide an approximate count and note the limitation.

        Returns:
            Dict with total_posts and a note about content type extraction.
        """
        return {
            "total_posts": len(posts),
            "note": (
                "Content type (image/video/carousel) is not reliably available "
                "from current Playwright collection.  Use engagement patterns "
                "as a proxy for content strategy analysis."
            ),
        }

    # ------------------------------------------------------------------
    # Network comparison
    # ------------------------------------------------------------------

    def build_network_hashtags(self) -> dict[str, int]:
        """Aggregate hashtag counts across all target galleries.

        Returns:
            {hashtag_lower: total_count}
        """
        network_counter: Counter = Counter()
        for target in self.targets:
            posts = self.load_target_posts(target)
            target_tags = self.extract_hashtags(posts)
            network_counter.update(target_tags)
        return dict(network_counter.most_common())

    def build_network_posting_pattern(self) -> dict:
        """Aggregate posting patterns across all target galleries.

        Returns:
            Dict with combined stats.
        """
        all_posts = []
        gallery_counts = {}
        for target in self.targets:
            posts = self.load_target_posts(target)
            gallery_counts[target] = len(posts)
            all_posts.extend(posts)
        pattern = self.extract_posting_pattern(all_posts)
        pattern["gallery_post_counts"] = gallery_counts
        return pattern

    # ------------------------------------------------------------------
    # Gap analysis
    # ------------------------------------------------------------------

    def compare_hashtags(
        self, artist_hashtags: dict[str, int], network_hashtags: dict[str, int]
    ) -> dict:
        """Compare artist hashtags to target gallery network hashtags.

        Returns:
            Dict with:
                - aligned: hashtags used by both
                - artist_only: hashtags used by artist, not by galleries
                - network_only: hashtags used by galleries, not by artist
                - top_artist_missing: artist's top 10 tags not in network
                - top_network_missing: network's top 10 tags not used by artist
                - recommendations: list of "add"/"drop"/"keep" dicts
        """
        artist_set = set(artist_hashtags)
        network_set = set(network_hashtags)

        aligned = artist_set & network_set
        artist_only = artist_set - network_set
        network_only = network_set - artist_set

        # Top 10 artist tags not in network
        top_artist_missing = [
            {"hashtag": tag, "count": artist_hashtags[tag], "pct_of_posts": 0}
            for tag in artist_hashtags
            if tag in artist_only
        ][:10]

        # Top 10 network tags not used by artist
        top_network_missing = [
            {
                "hashtag": tag,
                "count": network_hashtags[tag],
                "galleries_using": self._count_galleries_using(tag),
            }
            for tag in network_hashtags
            if tag in network_only
        ][:10]

        # Recommendations
        recommendations = []
        for tag_info in top_artist_missing[:5]:
            recommendations.append(
                {
                    "hashtag": tag_info["hashtag"],
                    "action": "drop",
                    "reason": (
                        "Not seen in target galleries — may signal hobby community "
                        "rather than contemporary craft ecosystem"
                    ),
                }
            )
        for tag_info in top_network_missing[:5]:
            recommendations.append(
                {
                    "hashtag": tag_info["hashtag"],
                    "action": "add",
                    "reason": (
                        f"Used by {tag_info['galleries_using']} target gallery(ies)"
                    ),
                }
            )

        return {
            "aligned": sorted(aligned),
            "artist_only": sorted(artist_only),
            "network_only": sorted(network_only),
            "top_artist_missing": top_artist_missing,
            "top_network_missing": top_network_missing,
            "recommendations": recommendations,
        }

    def _count_galleries_using(self, hashtag: str) -> int:
        """Count how many target galleries use a given hashtag."""
        count = 0
        for target in self.targets:
            posts = self.load_target_posts(target)
            tags = self.extract_hashtags(posts)
            if hashtag in tags:
                count += 1
        return count

    # ------------------------------------------------------------------
    # Full audit
    # ------------------------------------------------------------------

    def audit(self) -> dict:
        """Run full content audit.

        Returns:
            Dict with:
                - artist_hashtags: {hashtag: count}
                - network_hashtags: {hashtag: count}
                - hashtag_gaps: gap analysis dict
                - artist_posting: posting pattern dict
                - network_posting: network posting pattern dict
                - artist_content_type: content type dict
                - has_artist_data: bool
                - has_network_data: bool
        """
        artist_posts = self.load_artist_posts()
        has_artist_data = len(artist_posts) > 0

        artist_hashtags = self.extract_hashtags(artist_posts) if has_artist_data else {}
        artist_posting = (
            self.extract_posting_pattern(artist_posts) if has_artist_data else {}
        )
        artist_content_type = (
            self.extract_content_type(artist_posts) if has_artist_data else {}
        )

        network_hashtags = self.build_network_hashtags()
        network_posting = self.build_network_posting_pattern()
        has_network_data = len(network_hashtags) > 0 or network_posting.get("total_posts", 0) > 0

        hashtag_gaps = (
            self.compare_hashtags(artist_hashtags, network_hashtags)
            if has_artist_data and network_hashtags
            else {}
        )

        return {
            "artist_hashtags": artist_hashtags,
            "network_hashtags": network_hashtags,
            "hashtag_gaps": hashtag_gaps,
            "artist_posting": artist_posting,
            "network_posting": network_posting,
            "artist_content_type": artist_content_type,
            "has_artist_data": has_artist_data,
            "has_network_data": has_network_data,
        }

    # ------------------------------------------------------------------
    # Output formatting
    # ------------------------------------------------------------------

    def format_report(self, audit_result: dict) -> str:
        """Format content audit as a readable text report."""
        lines = []
        lines.append("=" * 80)
        lines.append(f"CONTENT GAP ANALYSIS for @{self.artist_username}")
        lines.append("=" * 80)
        lines.append("")

        if not audit_result.get("has_artist_data"):
            lines.append(
                "⚠️  No post data found for this artist.\n"
                "   Run collection first:\n"
                f"     python scripts/collect.py --target {self.artist_username}"
            )
            lines.append("")
            return "\n".join(lines)

        # --- Hashtag alignment ---
        lines.append("HASHTAG ALIGNMENT")
        lines.append("")

        artist_hashtags = audit_result.get("artist_hashtags", {})
        network_hashtags = audit_result.get("network_hashtags", {})
        gaps = audit_result.get("hashtag_gaps", {})
        target_count = len(self.targets)

        if artist_hashtags:
            lines.append("  Your top hashtags:")
            for tag, count in list(artist_hashtags.items())[:8]:
                pct = round(count / max(audit_result.get("artist_posting", {}).get("total_posts", 1), 1) * 100)
                status = "✓ ALIGNED" if tag in gaps.get("aligned", []) else "NOT SEEN in target galleries"
                gallery_usage = self._count_galleries_using(tag)
                if gallery_usage > 0 and tag not in gaps.get("aligned", []):
                    status = f"LOW presence ({gallery_usage}/{target_count} galleries)"
                elif tag in gaps.get("aligned", []):
                    status = f"ALIGNED ({gallery_usage}/{target_count} galleries)"
                lines.append(f"    #{tag}  ({pct}% of posts) → {status}")

        if gaps:
            lines.append("")
            top_missing = gaps.get("top_network_missing", [])
            if top_missing:
                lines.append(
                    f"  Target gallery top hashtags (you're NOT using):"
                )
                for tm in top_missing[:10]:
                    gu = tm.get("galleries_using", 0)
                    lines.append(f"    #{tm['hashtag']}  — used in {gu}/{target_count} galleries → ADD THIS")

            recs = gaps.get("recommendations", [])
            if recs:
                lines.append("")
                lines.append("  Recommended hashtag shift:")
                for rec in recs:
                    action = rec["action"].upper()
                    lines.append(f"    {action}: #{rec['hashtag']} — {rec['reason']}")

        # --- Posting frequency ---
        lines.append("")
        lines.append("POSTING FREQUENCY")
        artist_ppw = audit_result.get("artist_posting", {}).get("posts_per_week", 0)
        network_ppw = audit_result.get("network_posting", {}).get("posts_per_week", 0)
        lines.append(f"  You: {artist_ppw} posts / week")
        lines.append(f"  Target galleries: {network_ppw} posts / week (across {target_count} galleries)")
        if artist_ppw < 2 and network_ppw > 1:
            lines.append("  Recommendation: Increase to 2–3 posts / week minimum")

        # --- Posting timing ---
        lines.append("")
        lines.append("POSTING TIMING")
        artist_dow = audit_result.get("artist_posting", {}).get("day_of_week", {})
        network_dow = audit_result.get("network_posting", {}).get("day_of_week", {})
        artist_hours = audit_result.get("artist_posting", {}).get("hour_distribution", {})

        if artist_dow:
            top_days = list(artist_dow.keys())[:3]
            hours_str = ""
            if artist_hours:
                top_hours = sorted(artist_hours.items(), key=lambda x: x[1], reverse=True)[:2]
                hours_str = f", {top_hours[0][0]}:00–{top_hours[0][0]+1}:00" if top_hours else ""
            lines.append(f"  You post: mostly {', '.join(top_days)}{hours_str}")

        if network_dow:
            top_ndays = list(network_dow.keys())[:3]
            lines.append(f"  Target networks post: {', '.join(top_ndays)}")
            lines.append("  Recommendation: Try Sunday afternoon or Tuesday morning (top engagement windows)")

        # --- Content type strategy ---
        lines.append("")
        lines.append("CONTENT TYPE STRATEGY")
        artist_posts = self.load_artist_posts()
        # Use engagement as proxy — count commenters per post to find high-engagement posts
        avg_commenters = 0
        if artist_posts:
            commenter_counts = [len(p.get("commenters", [])) for p in artist_posts]
            avg_commenters = round(sum(commenter_counts) / len(commenter_counts), 1) if commenter_counts else 0
            lines.append(f"  Your posts: avg {avg_commenters} unique commenters per post (last {len(artist_posts)})")

        # Network engagement stats
        all_network_posts = []
        for t in self.targets:
            all_network_posts.extend(self.load_target_posts(t))
        if all_network_posts:
            net_commenters = [len(p.get("commenters", [])) for p in all_network_posts]
            net_avg = round(sum(net_commenters) / len(net_commenters), 1) if net_commenters else 0
            lines.append(f"  Target gallery posts: avg {net_avg} unique commenters per post")
            lines.append("")
            lines.append("  Content engagement insight:")
            lines.append("    - Posts with more unique commenters = broader network engagement")
            lines.append("    - Aim for posts that attract comments from 5+ unique accounts")
            lines.append("")
            lines.append("  Recommendation: Post process/studio content to drive conversation")

        lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Run
    # ------------------------------------------------------------------

    def run(self) -> dict:
        """Run full content audit and return results + formatted report.

        Returns:
            Dict with keys: audit_result, report.
        """
        audit_result = self.audit()
        report = self.format_report(audit_result)
        return {
            "audit_result": audit_result,
            "report": report,
        }
