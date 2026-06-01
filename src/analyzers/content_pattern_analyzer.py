"""Content pattern analysis for Instagram ecosystem posts.

Reads phase1_posts JSON files for one or more target accounts, extracts
hashtag patterns, posting times, and content themes, and generates
actionable (but hedged) strategic recommendations.
"""

import json
import logging
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────────────

STOPWORDS: set = {
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "shall", "can", "this",
    "that", "these", "those", "it", "its", "i", "you", "he", "she", "we",
    "they", "me", "him", "her", "us", "them", "my", "your", "his", "our",
    "their", "what", "which", "who", "whom", "when", "where", "why", "how",
    "all", "both", "each", "few", "more", "most", "other", "some", "such",
    "no", "nor", "not", "only", "own", "same", "so", "than", "too", "very",
    "just", "like", "if", "then", "there", "up", "out", "into", "about",
    "after", "before", "between", "through", "during", "without", "against",
    "now", "new", "one", "two", "three", "amp", "also", "via", "here",
    "get", "got", "see", "say", "said", "come", "came", "go", "went",
    "take", "took", "make", "made", "know", "think", "look", "want",
    "give", "back", "still", "even", "well", "much", "many", "first",
    "last", "long", "great", "little", "right", "big", "high", "next",
    "across", "around", "per", "re", "s", "t", "ll", "ve", "d", "m",
}

# Cluster keyword matching — order matters (checked top to bottom; first match wins)
CLUSTER_ORDER = [
    "gallery_collector",
    "institutional_fair",
    "interior_design",
    "wood_material",
    "craft_making",
]

CLUSTER_KEYWORDS: dict = {
    "craft_making": [
        "craft", "make", "maker", "handmade", "artisan", "studio",
        "process", "material",
    ],
    "wood_material": [
        "wood", "oak", "walnut", "timber", "grain", "lathe",
        "turning", "carving",
    ],
    "gallery_collector": [
        "gallery", "collect", "design", "contemporary", "art",
        "sculpture", "fine",
    ],
    "interior_design": [
        "interior", "home", "decor", "living", "architect", "space", "luxury",
    ],
    "institutional_fair": [
        "fair", "museum", "foundation", "exhibition", "show",
        "week", "london", "milan", "paris",
    ],
}

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

# Hashtag set templates — order is the set number (1–7)
HASHTAG_SET_TEMPLATES = [
    {
        "name": "Gallery/Collector Visibility",
        "description": "Tags used by galleries, collectors, and design-focused accounts in the target ecosystem",
        "use_when": "Posts featuring finished work, gallery partnerships, or collector-ready pieces",
        "clusters": ["gallery_collector"],
        "fill_from": ["institutional_fair", "craft_making"],
        "rationale": (
            "These tags are actively used by galleries and collectors in your target ecosystem. "
            "Reaching this audience is the primary goal for gallery representation."
        ),
    },
    {
        "name": "Craft Community",
        "description": "Tags connecting you to the wider craft and making community",
        "use_when": "Behind-the-scenes, process, studio shots, and maker collaborations",
        "clusters": ["craft_making"],
        "fill_from": ["wood_material", "gallery_collector"],
        "rationale": (
            "Connecting to the broader craft community builds credibility and peer recognition, "
            "which galleries notice when evaluating emerging artists."
        ),
    },
    {
        "name": "Material Focus",
        "description": "Tags emphasising your material and process — wood, turning, carving",
        "use_when": "Close-up detail shots, material studies, and in-progress work",
        "clusters": ["wood_material"],
        "fill_from": ["craft_making"],
        "rationale": (
            "Material-specific tags attract buyers and makers who appreciate craft process "
            "and specialist knowledge. They also signal depth of practice."
        ),
    },
    {
        "name": "Interior Design Crossover",
        "description": "Tags reaching interior designers, architects, and luxury home audiences",
        "use_when": "Styled shots showing work in living spaces or with interior design context",
        "clusters": ["interior_design"],
        "fill_from": ["gallery_collector"],
        "rationale": (
            "Interior design audiences are active buyers of functional art. "
            "These tags bridge studio craft and luxury living markets."
        ),
    },
    {
        "name": "Institutional/Fair",
        "description": "Tags associated with art fairs, museums, and institutional programmes",
        "use_when": "Fair appearances, museum visits, exhibition openings, residencies",
        "clusters": ["institutional_fair"],
        "fill_from": ["gallery_collector"],
        "rationale": (
            "Art fair and institutional tags signal seriousness of practice "
            "and can attract curatorial attention from programme selectors."
        ),
    },
    {
        "name": "Cross-Category Mix",
        "description": "Balanced mix across craft, gallery, and material themes for general posts",
        "use_when": "General posts balancing craft process and gallery-ready imagery",
        "clusters": ["gallery_collector", "craft_making", "wood_material"],
        "fill_from": ["interior_design", "institutional_fair"],
        "rationale": (
            "A balanced set works well for posts that combine gallery-worthy imagery "
            "with process content, reaching multiple audience segments simultaneously."
        ),
    },
    {
        "name": "Niche/Emerging",
        "description": "Lower-frequency tags from the ecosystem for niche community building",
        "use_when": "Experimental posts targeting specific sub-communities",
        "clusters": ["unclassified"],
        "fill_from": ["wood_material", "craft_making"],
        "rationale": (
            "Niche tags have less competition. Consistent use can establish you "
            "as a go-to voice in a specific sub-community before it scales."
        ),
    },
]

# Keywords for content signal detection
CONTENT_SIGNALS = {
    "new_work": ["new work", "new piece", "new collection", "just finished", "just completed"],
    "commission": ["commission", "bespoke", "custom", "made to order"],
    "exhibition": ["exhibition", "show", "opening", "preview", "vernissage", "on view"],
    "available": ["available", "for sale", "shop", "link in bio", "dm for"],
    "studio_process": ["studio", "process", "work in progress", "wip", "making", "workshop"],
}


# ──────────────────────────────────────────────────────────────────────────────
# Analyzer
# ──────────────────────────────────────────────────────────────────────────────

class ContentPatternAnalyzer:
    """Analyse content patterns from collected Instagram post data.

    Workflow::

        analyzer = ContentPatternAnalyzer(["sarah_myerscough", "hostlerburrows"])
        result = analyzer.run()
        # result["results"]     — full analysis dict
        # result["files_saved"] — output file paths
        # result["stats"]       — summary counts
    """

    def __init__(
        self,
        targets: list,
        raw_base_dir: str = "data/raw",
        processed_base_dir: str = "data/processed",
    ):
        """Initialise the analyzer.

        Args:
            targets: List of target Instagram usernames.
            raw_base_dir: Root directory for per-target raw data.
                phase1_posts files expected at ``{raw_base_dir}/{target}/phase1_posts_*.json``.
            processed_base_dir: Root directory for per-target processed data.
        """
        self.targets = list(targets)
        self.raw_base_dir = Path(raw_base_dir)
        self.processed_base_dir = Path(processed_base_dir)

    # ──────────────────────────────────────────────────────────────────────
    # Data loading
    # ──────────────────────────────────────────────────────────────────────

    def load_posts_for_target(self, target: str) -> list:
        """Load all phase1_posts JSON files for a target.

        Args:
            target: Instagram username of the target account.

        Returns:
            Flat list of post dicts (may be empty if no files exist).
        """
        target_dir = self.raw_base_dir / target
        if not target_dir.exists():
            logger.warning(f"Raw data directory not found for '{target}': {target_dir}")
            return []

        post_files = sorted(target_dir.glob("phase1_posts_*.json"))
        if not post_files:
            logger.warning(f"No phase1_posts_*.json files found for '{target}'")
            return []

        posts = []
        for path in post_files:
            try:
                with open(path) as f:
                    data = json.load(f)
                batch = data.get("posts", [])
                posts.extend(batch)
                logger.info(f"Loaded {len(batch)} posts for '{target}' from {path.name}")
            except Exception as exc:
                logger.error(f"Failed to load {path}: {exc}")

        return posts

    # ──────────────────────────────────────────────────────────────────────
    # Hashtag analysis
    # ──────────────────────────────────────────────────────────────────────

    def extract_hashtags(self, posts: list) -> dict:
        """Extract and count hashtags from post captions.

        Hashtags are lowercased; #WoodArt and #woodart are treated as the same.

        Args:
            posts: List of post dicts, each optionally containing a 'caption' key.

        Returns:
            Dict mapping lowercase hashtag (without #) to frequency count.
        """
        counts: dict = defaultdict(int)
        for post in posts:
            caption = post.get("caption") or ""
            if not caption:
                continue
            tags = re.findall(r"#(\w+)", caption)
            for tag in tags:
                counts[tag.lower()] += 1
        return dict(counts)

    def compute_engagement_by_hashtag(self, posts: list) -> dict:
        """For each hashtag, compute the average engagement on posts that used it.

        Engagement proxy = total comment count across all commenters on a post
        (sum of each commenter's ``comment_count`` value, or 1 per commenter if
        the field is absent).

        Args:
            posts: List of post dicts.

        Returns:
            Dict mapping hashtag to average engagement float.
        """
        tag_engagements: dict = defaultdict(list)
        for post in posts:
            caption = post.get("caption") or ""
            commenters = post.get("commenters") or []
            tags = [t.lower() for t in re.findall(r"#(\w+)", caption)]
            if not tags:
                continue

            engagement = sum(
                c.get("comment_count", 1) if isinstance(c, dict) else 1
                for c in commenters
            )
            for tag in set(tags):  # count each tag once per post
                tag_engagements[tag].append(engagement)

        return {
            tag: round(sum(vals) / len(vals), 2)
            for tag, vals in tag_engagements.items()
        }

    # ──────────────────────────────────────────────────────────────────────
    # Posting time analysis
    # ──────────────────────────────────────────────────────────────────────

    def extract_posting_times(self, posts: list) -> dict:
        """Analyse posting time patterns from post timestamps.

        Args:
            posts: List of post dicts, each optionally containing a 'timestamp' key.

        Returns:
            Dict with keys:
                - ``day_of_week``: {day_name: count}
                - ``hour_of_day``: {hour_int: count}
                - ``best_windows``: list of up to 3 {day, hour, count} dicts
        """
        day_counts: dict = defaultdict(int)
        hour_counts: dict = defaultdict(int)
        window_counts: dict = defaultdict(int)

        for post in posts:
            ts_raw = post.get("timestamp")
            if not ts_raw:
                continue
            try:
                dt = datetime.fromisoformat(str(ts_raw))
                day_name = DAY_NAMES[dt.weekday()]
                hour = dt.hour
                day_counts[day_name] += 1
                hour_counts[hour] += 1
                window_counts[(day_name, hour)] += 1
            except (ValueError, TypeError) as exc:
                logger.debug(f"Skipping malformed timestamp '{ts_raw}': {exc}")

        best_windows = [
            {"day": day, "hour": hour, "count": count}
            for (day, hour), count in sorted(
                window_counts.items(), key=lambda x: x[1], reverse=True
            )[:3]
        ]

        return {
            "day_of_week": dict(day_counts),
            "hour_of_day": {str(h): c for h, c in hour_counts.items()},
            "best_windows": best_windows,
        }

    # ──────────────────────────────────────────────────────────────────────
    # Content theme analysis
    # ──────────────────────────────────────────────────────────────────────

    def extract_content_themes(self, posts: list) -> dict:
        """Extract keyword frequency from caption text (excluding hashtags).

        Args:
            posts: List of post dicts.

        Returns:
            Dict with keys:
                - ``keywords``: {word: count} for non-stopword caption words
                - ``mentioned_accounts``: {username: count} from mentions/tagged_accounts
                - ``content_signals``: {signal_name: count} for detected signal types
        """
        keyword_counts: dict = defaultdict(int)
        mention_counts: dict = defaultdict(int)
        signal_counts: dict = defaultdict(int)

        for post in posts:
            caption = post.get("caption") or ""

            # Collect @mentions
            raw_mentions = post.get("mentions") or post.get("tagged_accounts") or []
            for username in raw_mentions:
                if isinstance(username, str):
                    mention_counts[username.lower().strip("@")] += 1

            # Also extract @mentions from caption text
            for mention in re.findall(r"@(\w+)", caption):
                mention_counts[mention.lower()] += 1

            if not caption:
                continue

            # Strip hashtags and mentions from caption for keyword extraction
            clean = re.sub(r"#\w+", " ", caption)
            clean = re.sub(r"@\w+", " ", clean)

            # Tokenise and filter
            words = re.findall(r"\b[a-zA-Z]{3,}\b", clean.lower())
            for word in words:
                if word not in STOPWORDS:
                    keyword_counts[word] += 1

            # Detect content signals
            caption_lower = caption.lower()
            for signal_name, phrases in CONTENT_SIGNALS.items():
                for phrase in phrases:
                    if phrase in caption_lower:
                        signal_counts[signal_name] += 1
                        break  # one match per signal per post

        # Sort by frequency
        top_keywords = dict(
            sorted(keyword_counts.items(), key=lambda x: x[1], reverse=True)[:50]
        )
        top_mentions = dict(
            sorted(mention_counts.items(), key=lambda x: x[1], reverse=True)[:20]
        )

        return {
            "keywords": top_keywords,
            "mentioned_accounts": top_mentions,
            "content_signals": dict(signal_counts),
        }

    # ──────────────────────────────────────────────────────────────────────
    # Hashtag clustering
    # ──────────────────────────────────────────────────────────────────────

    def cluster_hashtags(self, hashtag_counts: dict) -> dict:
        """Assign hashtags to thematic clusters using substring keyword matching.

        Clusters are checked in CLUSTER_ORDER; the first match wins.
        Unmatched hashtags go to the ``unclassified`` bucket.

        Args:
            hashtag_counts: Dict mapping hashtag to frequency count.

        Returns:
            Dict mapping cluster_name to list of hashtags in that cluster,
            sorted by frequency descending.
        """
        clusters: dict = {name: [] for name in CLUSTER_ORDER}
        clusters["unclassified"] = []

        for tag, count in hashtag_counts.items():
            assigned = False
            for cluster_name in CLUSTER_ORDER:
                keywords = CLUSTER_KEYWORDS[cluster_name]
                if any(kw in tag for kw in keywords):
                    clusters[cluster_name].append(tag)
                    assigned = True
                    break
            if not assigned:
                clusters["unclassified"].append(tag)

        # Sort each cluster by frequency descending
        for cluster_name in clusters:
            clusters[cluster_name].sort(
                key=lambda t: hashtag_counts.get(t, 0), reverse=True
            )

        return clusters

    # ──────────────────────────────────────────────────────────────────────
    # Hashtag set generation
    # ──────────────────────────────────────────────────────────────────────

    def generate_hashtag_sets(self, hashtag_counts: dict, clusters: dict) -> list:
        """Generate recommended hashtag sets from cluster data.

        Produces up to 7 themed sets of up to 15 hashtags each (or however
        many tags are available when data is sparse).  Sets with zero tags
        are omitted.

        Args:
            hashtag_counts: Dict mapping hashtag to frequency count.
            clusters: Cluster dict from ``cluster_hashtags()``.

        Returns:
            List of dicts, each with keys:
                ``name``, ``description``, ``hashtags`` (list), ``rationale``
        """
        sets = []
        seen: set = set()  # prevent exact duplicates across sets

        for template in HASHTAG_SET_TEMPLATES:
            tag_pool: list = []

            # Primary clusters
            for cluster_name in template["clusters"]:
                for tag in clusters.get(cluster_name, []):
                    if tag not in seen:
                        tag_pool.append(tag)

            # Fill from secondary clusters up to 15
            for cluster_name in template.get("fill_from", []):
                if len(tag_pool) >= 15:
                    break
                for tag in clusters.get(cluster_name, []):
                    if tag not in seen and tag not in tag_pool:
                        tag_pool.append(tag)
                        if len(tag_pool) >= 15:
                            break

            # Cap at 15
            chosen = tag_pool[:15]
            if not chosen:
                continue

            seen.update(chosen)
            sets.append(
                {
                    "name": template["name"],
                    "description": template["description"],
                    "use_when": template["use_when"],
                    "hashtags": [f"#{t}" for t in chosen],
                    "rationale": template["rationale"],
                }
            )

        return sets

    # ──────────────────────────────────────────────────────────────────────
    # Full analysis pipeline
    # ──────────────────────────────────────────────────────────────────────

    def analyze(self) -> dict:
        """Run full content analysis across all targets.

        Returns:
            Structured results dict with keys:
                ``hashtags``, ``posting_times``, ``themes``, ``hashtag_sets``,
                ``clusters``, ``engagement_by_hashtag``, ``targets_analyzed``,
                ``targets_skipped``, ``total_posts``.
        """
        all_posts: list = []
        targets_with_data: list = []
        targets_without_data: list = []

        for target in self.targets:
            posts = self.load_posts_for_target(target)
            if posts:
                all_posts.extend(posts)
                targets_with_data.append(target)
                logger.info(f"Target '{target}': {len(posts)} posts loaded")
            else:
                targets_without_data.append(target)
                logger.warning(f"Target '{target}': no post data found, skipping")

        empty_base = {
            "hashtags": {},
            "posting_times": {"day_of_week": {}, "hour_of_day": {}, "best_windows": []},
            "themes": {"keywords": {}, "mentioned_accounts": {}, "content_signals": {}},
            "hashtag_sets": [],
            "clusters": {name: [] for name in CLUSTER_ORDER + ["unclassified"]},
            "engagement_by_hashtag": {},
            "targets_analyzed": targets_with_data,
            "targets_skipped": targets_without_data,
            "total_posts": 0,
        }

        if not all_posts:
            return empty_base

        hashtag_counts = self.extract_hashtags(all_posts)
        posting_times = self.extract_posting_times(all_posts)
        themes = self.extract_content_themes(all_posts)
        engagement_by_hashtag = self.compute_engagement_by_hashtag(all_posts)
        clusters = self.cluster_hashtags(hashtag_counts)
        hashtag_sets = self.generate_hashtag_sets(hashtag_counts, clusters)

        return {
            "hashtags": hashtag_counts,
            "posting_times": posting_times,
            "themes": themes,
            "hashtag_sets": hashtag_sets,
            "clusters": clusters,
            "engagement_by_hashtag": engagement_by_hashtag,
            "targets_analyzed": targets_with_data,
            "targets_skipped": targets_without_data,
            "total_posts": len(all_posts),
        }

    # ──────────────────────────────────────────────────────────────────────
    # Output generation
    # ──────────────────────────────────────────────────────────────────────

    def _generate_markdown(self, results: dict) -> str:
        """Render analysis results as a markdown strategy report."""
        targets_str = ", ".join(results.get("targets_analyzed", self.targets) or self.targets)
        analysis_date = datetime.now().strftime("%Y-%m-%d")
        total_posts = results.get("total_posts", 0)

        hashtags = results.get("hashtags", {})
        posting_times = results.get("posting_times", {})
        themes = results.get("themes", {})
        hashtag_sets = results.get("hashtag_sets", [])
        clusters = results.get("clusters", {})
        engagement = results.get("engagement_by_hashtag", {})

        lines = [
            "# Content Strategy Analysis",
            f"## Target ecosystem: {targets_str}",
            f"## Analysis date: {analysis_date}",
            f"## Posts analysed: {total_posts}",
            "",
            "---",
            "",
            "## ⚠️ Important Limitations",
            "",
            "- **Hashtag reach has declined 40–60% since 2021–2022.** "
            "Instagram de-prioritised hashtag-based discovery in favour of interest signals.",
            "- **Saves and shares** (Instagram's top two ranking signals) are invisible to "
            "public data collection. We cannot measure the most important engagement metric.",
            "- **Posting time optimisation** has limited impact compared to content quality. "
            "The windows below reflect when target accounts post, not audience peak activity.",
            "- **These recommendations are directional, not prescriptive.** "
            "Content quality and authentic community engagement outperform any hashtag strategy.",
            "",
            "---",
            "",
        ]

        # ── Hashtag Analysis ────────────────────────────────────────────
        lines += [
            "## Hashtag Analysis",
            "",
            f"Total unique hashtags found: **{len(hashtags)}**",
            "",
        ]

        if hashtags:
            top_tags = sorted(hashtags.items(), key=lambda x: x[1], reverse=True)[:30]
            lines += [
                "### Top Hashtags in Ecosystem",
                "",
                "| Hashtag | Frequency | Cluster | Avg Engagement |",
                "|---------|-----------|---------|----------------|",
            ]
            # Build reverse cluster lookup
            tag_to_cluster: dict = {}
            for cluster_name, tags in clusters.items():
                for tag in tags:
                    tag_to_cluster[tag] = cluster_name

            for tag, count in top_tags:
                cluster = tag_to_cluster.get(tag, "unclassified")
                eng = engagement.get(tag, 0.0)
                lines.append(f"| #{tag} | {count} | {cluster} | {eng:.1f} |")

            lines.append("")

        # ── Hashtag Clusters ─────────────────────────────────────────────
        lines += [
            "### Hashtag Clusters",
            "",
        ]
        all_cluster_names = CLUSTER_ORDER + ["unclassified"]
        for cluster_name in all_cluster_names:
            tags_in_cluster = clusters.get(cluster_name, [])
            if not tags_in_cluster:
                continue
            display_name = cluster_name.replace("_", " ").title()
            top10 = tags_in_cluster[:10]
            lines += [
                f"**{display_name}** ({len(tags_in_cluster)} tags)  ",
                "  " + "  ".join(f"`#{t}`" for t in top10),
                "",
            ]

        lines += ["---", ""]

        # ── Recommended Hashtag Sets ──────────────────────────────────────
        lines += [
            "## Recommended Hashtag Sets",
            "",
            "> **Note on volume tiers:** Without Instagram API access, hashtag post volume cannot "
            "be measured directly. Volume estimates below are inferred from context and marked as "
            "*estimated*. Actual reach varies significantly.",
            "",
        ]

        if hashtag_sets:
            for i, hset in enumerate(hashtag_sets, 1):
                tag_str = " ".join(hset["hashtags"])
                lines += [
                    f"### Set {i}: {hset['name']}",
                    f"**Use when:** {hset.get('use_when', '')}",
                    "",
                    f"_{hset['description']}_",
                    "",
                    f"**Tags ({len(hset['hashtags'])}):** {tag_str}",
                    "",
                    f"**Rationale:** {hset['rationale']}",
                    "",
                ]
        else:
            lines += [
                "_No hashtag sets could be generated — insufficient post data collected._",
                "",
            ]

        lines += ["---", ""]

        # ── Posting Time Analysis ──────────────────────────────────────────
        lines += [
            "## Posting Time Analysis",
            "",
            "### Best Windows (based on ecosystem activity)",
            "",
        ]

        best_windows = posting_times.get("best_windows", [])
        if best_windows:
            lines += [
                "| Rank | Day | Hour (UTC) | Posts |",
                "|------|-----|------------|-------|",
            ]
            for rank, window in enumerate(best_windows, 1):
                hour = window["hour"]
                hour_str = f"{hour:02d}:00–{(hour + 1) % 24:02d}:00"
                lines.append(f"| {rank} | {window['day']} | {hour_str} | {window['count']} |")
        else:
            lines.append("_Insufficient timestamp data to identify posting windows._")

        lines += [
            "",
            "**Caveat:** These windows reflect when target accounts post, "
            "not when their audience is most active. Audience peak times vary by account.",
            "",
        ]

        # Day of week summary
        day_counts = posting_times.get("day_of_week", {})
        if day_counts:
            sorted_days = sorted(day_counts.items(), key=lambda x: x[1], reverse=True)
            lines += [
                "### Day of Week Distribution",
                "",
            ]
            for day, count in sorted_days:
                bar = "█" * min(count, 20)
                lines.append(f"- **{day}**: {count} posts  {bar}")
            lines.append("")

        lines += ["---", ""]

        # ── Content Theme Analysis ────────────────────────────────────────
        lines += [
            "## Content Theme Analysis",
            "",
        ]

        keywords = themes.get("keywords", {})
        if keywords:
            top_keywords = list(keywords.items())[:20]
            lines += [
                "### Top Caption Keywords",
                "",
                "| Keyword | Count |",
                "|---------|-------|",
            ]
            for word, count in top_keywords:
                lines.append(f"| {word} | {count} |")
            lines.append("")

        mentioned = themes.get("mentioned_accounts", {})
        if mentioned:
            top_mentions = list(mentioned.items())[:15]
            lines += [
                "### Top Mentioned Accounts",
                "",
                "| Account | Mentions |",
                "|---------|----------|",
            ]
            for username, count in top_mentions:
                lines.append(f"| @{username} | {count} |")
            lines += [
                "",
                "> Cross-reference with account scores to prioritise engagement targets.",
                "",
            ]

        signals = themes.get("content_signals", {})
        if signals:
            lines += [
                "### Content Signal Types",
                "",
            ]
            signal_labels = {
                "new_work": "New Work Announcements",
                "commission": "Commissions/Bespoke",
                "exhibition": "Exhibition/Show Mentions",
                "available": "Work Available/For Sale",
                "studio_process": "Studio Process Content",
            }
            for signal, count in sorted(signals.items(), key=lambda x: x[1], reverse=True):
                label = signal_labels.get(signal, signal.replace("_", " ").title())
                lines.append(f"- **{label}**: {count} posts")
            lines.append("")

        lines += ["---", ""]

        # ── Actionable Recommendations ────────────────────────────────────
        lines += [
            "## Actionable Recommendations",
            "",
            "> These are directional signals based on ecosystem data, not prescriptions. "
            "Content quality and authentic engagement matter more than any tactical choice.",
            "",
        ]

        recs = self._build_recommendations(results)
        for i, rec in enumerate(recs, 1):
            lines.append(f"{i}. {rec}")
        lines.append("")

        return "\n".join(lines)

    def _build_recommendations(self, results: dict) -> list:
        """Generate honest, hedged recommendations from analysis results."""
        recs = []
        hashtags = results.get("hashtags", {})
        hashtag_sets = results.get("hashtag_sets", [])
        posting_times = results.get("posting_times", {})
        themes = results.get("themes", {})
        best_windows = posting_times.get("best_windows", [])

        # Hashtag set recommendation
        if hashtag_sets:
            primary_set = hashtag_sets[0]["name"]
            recs.append(
                f"**Prioritise the '{primary_set}' hashtag set** for posts featuring "
                "finished work — these tags reflect what galleries and collectors in your "
                "target ecosystem are already using. Rotate sets to avoid repetition."
            )
        else:
            recs.append(
                "**Collect more post data** before committing to a hashtag strategy — "
                "the current dataset is too small to draw reliable conclusions."
            )

        # Posting time
        if best_windows:
            w = best_windows[0]
            recs.append(
                f"**Experiment with posting on {w['day']}s around {w['hour']:02d}:00 UTC** "
                "(the most common posting window in your target ecosystem), but treat this "
                "as a low-confidence signal: audience peak time ≠ creator posting time."
            )
        else:
            recs.append(
                "**Collect timestamped post data** to identify posting windows — "
                "current data lacks sufficient timestamps for time analysis."
            )

        # Top mentioned accounts
        mentioned = themes.get("mentioned_accounts", {})
        if mentioned:
            top_accounts = list(mentioned.keys())[:3]
            accounts_str = ", ".join(f"@{a}" for a in top_accounts)
            recs.append(
                f"**Engage authentically with {accounts_str}** — these accounts are most "
                "frequently mentioned in your target ecosystem and represent high-value "
                "community nodes. Genuine comments on their posts outperform hashtag reach."
            )

        # Content signals
        signals = themes.get("content_signals", {})
        if signals.get("studio_process", 0) > 0 and signals.get("exhibition", 0) > 0:
            recs.append(
                "**Balance process and exhibition content** — your target ecosystem shows "
                "both studio/process posts and exhibition announcements. A mix signals "
                "active practice and institutional credibility."
            )
        elif signals.get("studio_process", 0) > 0:
            recs.append(
                "**Add exhibition and collector-facing posts** alongside process content — "
                "the ecosystem leans process-heavy; gallery-ready imagery may differentiate you."
            )

        # Hashtag volume caution
        recs.append(
            "**Do not over-optimise for hashtags.** Instagram's own research suggests saves "
            "and shares drive reach far more than hashtag use. Post work that makes people "
            "want to save it first; choose hashtags second."
        )

        # Consistency
        recs.append(
            "**Post consistently over 90 days before evaluating results.** "
            "Ecosystem positioning takes time. Track profile visits and follows as "
            "leading indicators; hashtag reach alone is an unreliable success metric."
        )

        return recs[:7]

    def save_outputs(self, results: dict, output_dir: str = "outputs") -> dict:
        """Save analysis results to JSON and markdown files.

        Args:
            results: Results dict from ``analyze()``.
            output_dir: Directory to write outputs into.

        Returns:
            Dict with keys ``content_analysis_json`` and ``content_strategy_md``.
        """
        out = Path(output_dir)
        out.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # JSON
        json_path = out / f"content_analysis_{timestamp}.json"
        with open(json_path, "w") as f:
            json.dump(results, f, indent=2, default=str)
        logger.info(f"Saved content analysis JSON: {json_path}")

        # Markdown
        md_content = self._generate_markdown(results)
        md_path = out / f"content_strategy_{timestamp}.md"
        with open(md_path, "w") as f:
            f.write(md_content)
        logger.info(f"Saved content strategy markdown: {md_path}")

        return {
            "content_analysis_json": str(json_path),
            "content_strategy_md": str(md_path),
        }

    # ──────────────────────────────────────────────────────────────────────
    # Main entry point
    # ──────────────────────────────────────────────────────────────────────

    def run(self) -> dict:
        """Execute full content pattern analysis pipeline.

        Returns:
            Dict with keys:
                - ``results``: full analysis dict
                - ``files_saved``: output file paths
                - ``stats``: summary counts
        """
        logger.info(
            f"Starting content pattern analysis for {len(self.targets)} target(s): "
            + ", ".join(self.targets)
        )

        results = self.analyze()
        files_saved = self.save_outputs(results)

        stats = {
            "total_targets": len(self.targets),
            "targets_with_data": len(results.get("targets_analyzed", [])),
            "targets_skipped": len(results.get("targets_skipped", [])),
            "total_posts": results.get("total_posts", 0),
            "unique_hashtags": len(results.get("hashtags", {})),
            "hashtag_sets_generated": len(results.get("hashtag_sets", [])),
        }

        logger.info(
            f"Content analysis complete: {stats['total_posts']} posts, "
            f"{stats['unique_hashtags']} hashtags, "
            f"{stats['hashtag_sets_generated']} sets generated"
        )

        return {
            "results": results,
            "files_saved": files_saved,
            "stats": stats,
        }
