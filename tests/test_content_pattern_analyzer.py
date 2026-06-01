"""Unit tests for ContentPatternAnalyzer.

All tests use synthetic in-memory data only — no browser, no Instagram,
no filesystem access beyond pytest's tmp_path fixture.
"""

import json
from pathlib import Path

import pytest

from src.analyzers.content_pattern_analyzer import ContentPatternAnalyzer


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def _make_analyzer(targets=None, raw_base_dir=None, tmp_path=None):
    """Return a ContentPatternAnalyzer pointed at tmp_path (or a dummy dir)."""
    raw = str(raw_base_dir or (tmp_path or Path("/tmp")))
    return ContentPatternAnalyzer(targets=targets or ["test_target"], raw_base_dir=raw)


def _make_post(caption="", timestamp=None, commenters=None, mentions=None):
    """Return a minimal post dict matching the phase1_posts schema."""
    return {
        "post_url": "https://instagram.com/p/TEST/",
        "caption": caption,
        "mentions": mentions or [],
        "timestamp": timestamp,
        "commenters": commenters or [],
    }


def _write_phase1_file(tmp_path: Path, target: str, posts: list) -> Path:
    """Write a synthetic phase1_posts JSON file and return its path."""
    target_dir = tmp_path / target
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "phase1_posts_20260101_000000.json"
    payload = {
        "metadata": {
            "phase": "phase1_posts",
            "target_account": target,
            "timestamp": "2026-01-01T00:00:00Z",
        },
        "posts": posts,
    }
    path.write_text(json.dumps(payload))
    return path


# ─────────────────────────────────────────────────────────────────────────────
# Hashtag extraction
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractHashtags:
    def test_basic(self):
        analyzer = _make_analyzer()
        posts = [
            _make_post("#woodart #contemporarycraft"),
            _make_post("Love this #woodart piece!"),
        ]
        result = analyzer.extract_hashtags(posts)
        assert result["woodart"] == 2
        assert result["contemporarycraft"] == 1

    def test_case_insensitive(self):
        """#WoodArt and #woodart must be counted as the same hashtag."""
        analyzer = _make_analyzer()
        posts = [
            _make_post("#WoodArt is great"),
            _make_post("Another post #woodart"),
            _make_post("#WOODART again"),
        ]
        result = analyzer.extract_hashtags(posts)
        assert result["woodart"] == 3
        assert "WoodArt" not in result
        assert "WOODART" not in result

    def test_empty_caption(self):
        """Posts with None or empty captions should not raise and contribute nothing."""
        analyzer = _make_analyzer()
        posts = [
            _make_post(None),
            _make_post(""),
            _make_post("   "),
        ]
        result = analyzer.extract_hashtags(posts)
        assert result == {}

    def test_no_hashtags(self):
        """Captions with no # tokens return an empty dict."""
        analyzer = _make_analyzer()
        posts = [_make_post("Beautiful work, love the oak grain")]
        result = analyzer.extract_hashtags(posts)
        assert result == {}


# ─────────────────────────────────────────────────────────────────────────────
# Posting time analysis
# ─────────────────────────────────────────────────────────────────────────────

class TestExtractPostingTimes:
    def test_day_of_week(self):
        """Timestamps should be correctly mapped to day names."""
        analyzer = _make_analyzer()
        # 2026-01-05 is a Monday
        posts = [
            _make_post(timestamp="2026-01-05T10:00:00+00:00"),
            _make_post(timestamp="2026-01-05T14:00:00+00:00"),
            _make_post(timestamp="2026-01-06T09:00:00+00:00"),  # Tuesday
        ]
        result = analyzer.extract_posting_times(posts)
        assert result["day_of_week"]["Monday"] == 2
        assert result["day_of_week"]["Tuesday"] == 1

    def test_missing_timestamps(self):
        """Posts with None timestamps should be skipped without raising."""
        analyzer = _make_analyzer()
        posts = [
            _make_post(timestamp=None),
            _make_post(timestamp=""),
            _make_post(timestamp="not-a-date"),
        ]
        result = analyzer.extract_posting_times(posts)
        assert result["day_of_week"] == {}
        assert result["hour_of_day"] == {}
        assert result["best_windows"] == []


# ─────────────────────────────────────────────────────────────────────────────
# Hashtag clustering
# ─────────────────────────────────────────────────────────────────────────────

class TestClusterHashtags:
    def test_wood_material(self):
        """#woodturning should land in the wood_material cluster."""
        analyzer = _make_analyzer()
        counts = {"woodturning": 5, "oakbowl": 3}
        clusters = analyzer.cluster_hashtags(counts)
        assert "woodturning" in clusters["wood_material"]
        assert "oakbowl" in clusters["wood_material"]

    def test_gallery_collector(self):
        """#contemporarycraft should land in gallery_collector (not craft_making)."""
        analyzer = _make_analyzer()
        counts = {"contemporarycraft": 4, "fineart": 2}
        clusters = analyzer.cluster_hashtags(counts)
        assert "contemporarycraft" in clusters["gallery_collector"]
        assert "fineart" in clusters["gallery_collector"]

    def test_unclassified(self):
        """Hashtags with no matching keywords should land in unclassified."""
        analyzer = _make_analyzer()
        counts = {"xyzrandom123": 1, "zyxunknown": 2}
        clusters = analyzer.cluster_hashtags(counts)
        assert "xyzrandom123" in clusters["unclassified"]
        assert "zyxunknown" in clusters["unclassified"]


# ─────────────────────────────────────────────────────────────────────────────
# Hashtag set generation
# ─────────────────────────────────────────────────────────────────────────────

class TestGenerateHashtagSets:
    def _rich_counts_and_clusters(self, analyzer):
        """Build a hashtag_counts and clusters dict with enough data for sets."""
        # 30 hashtags across all clusters
        counts = {}
        for i in range(5):
            counts[f"gallery{i}"] = 10 - i
            counts[f"artpiece{i}"] = 8 - i
            counts[f"woodcraft{i}"] = 7 - i
            counts[f"homedecor{i}"] = 6 - i
            counts[f"artfair{i}"] = 5 - i
            counts[f"unknowntag{i}"] = 4 - i
        clusters = analyzer.cluster_hashtags(counts)
        return counts, clusters

    def test_count_returns_1_to_7(self):
        """generate_hashtag_sets should return between 1 and 7 sets."""
        analyzer = _make_analyzer()
        counts, clusters = self._rich_counts_and_clusters(analyzer)
        sets = analyzer.generate_hashtag_sets(counts, clusters)
        assert 1 <= len(sets) <= 7

    def test_size_per_set(self):
        """Each set should have ≤ 15 hashtags (or fewer if data is sparse)."""
        analyzer = _make_analyzer()
        counts, clusters = self._rich_counts_and_clusters(analyzer)
        sets = analyzer.generate_hashtag_sets(counts, clusters)
        for hset in sets:
            assert len(hset["hashtags"]) <= 15, (
                f"Set '{hset['name']}' has {len(hset['hashtags'])} tags (max 15)"
            )

    def test_set_has_required_keys(self):
        """Each set dict must have name, description, hashtags, and rationale."""
        analyzer = _make_analyzer()
        counts, clusters = self._rich_counts_and_clusters(analyzer)
        sets = analyzer.generate_hashtag_sets(counts, clusters)
        for hset in sets:
            assert "name" in hset
            assert "description" in hset
            assert "hashtags" in hset
            assert "rationale" in hset

    def test_no_crash_with_empty_data(self):
        """generate_hashtag_sets should not raise when given empty inputs."""
        analyzer = _make_analyzer()
        sets = analyzer.generate_hashtag_sets({}, {})
        assert isinstance(sets, list)

    def test_hashtags_are_prefixed(self):
        """Each tag in a set's hashtags list should start with '#'."""
        analyzer = _make_analyzer()
        counts, clusters = self._rich_counts_and_clusters(analyzer)
        sets = analyzer.generate_hashtag_sets(counts, clusters)
        for hset in sets:
            for tag in hset["hashtags"]:
                assert tag.startswith("#"), f"Tag '{tag}' missing '#' prefix"


# ─────────────────────────────────────────────────────────────────────────────
# Engagement by hashtag
# ─────────────────────────────────────────────────────────────────────────────

class TestComputeEngagementByHashtag:
    def test_higher_commenter_count_scores_higher(self):
        """A hashtag used on a post with 5 commenters scores higher than one with 0."""
        analyzer = _make_analyzer()
        posts = [
            _make_post(
                caption="#popularart #commontag",
                commenters=[
                    {"username": "user1", "comment_count": 3},
                    {"username": "user2", "comment_count": 2},
                ],
            ),
            _make_post(
                caption="#nichemaker #commontag",
                commenters=[],
            ),
        ]
        result = analyzer.compute_engagement_by_hashtag(posts)
        assert result.get("popularart", 0) > result.get("nichemaker", 0)
        # commontag appears in both: one post has 5 comments, other has 0 → avg 2.5
        assert "commontag" in result
        assert result["commontag"] == pytest.approx(2.5, abs=0.1)

    def test_no_crash_with_no_commenters(self):
        """Posts with no commenters field should be handled gracefully."""
        analyzer = _make_analyzer()
        posts = [{"post_url": "x", "caption": "#woodart", "commenters": None}]
        result = analyzer.compute_engagement_by_hashtag(posts)
        assert isinstance(result, dict)


# ─────────────────────────────────────────────────────────────────────────────
# Full analyze() integration
# ─────────────────────────────────────────────────────────────────────────────

class TestAnalyze:
    def test_returns_required_keys(self, tmp_path):
        """analyze() must return a dict containing all required top-level keys."""
        posts = [_make_post("#woodart #gallery", timestamp="2026-01-05T10:00:00+00:00")]
        _write_phase1_file(tmp_path, "test_target", posts)

        analyzer = ContentPatternAnalyzer(
            targets=["test_target"], raw_base_dir=str(tmp_path)
        )
        result = analyzer.analyze()

        for key in ("hashtags", "posting_times", "themes", "hashtag_sets"):
            assert key in result, f"Missing key: {key}"

    def test_analyze_aggregates_across_targets(self, tmp_path):
        """Posts from multiple targets should be combined in the analysis."""
        posts_a = [_make_post("#woodart")]
        posts_b = [_make_post("#gallery")]
        _write_phase1_file(tmp_path, "target_a", posts_a)
        _write_phase1_file(tmp_path, "target_b", posts_b)

        analyzer = ContentPatternAnalyzer(
            targets=["target_a", "target_b"], raw_base_dir=str(tmp_path)
        )
        result = analyzer.analyze()

        assert result["hashtags"].get("woodart", 0) >= 1
        assert result["hashtags"].get("gallery", 0) >= 1
        assert result["total_posts"] == 2


# ─────────────────────────────────────────────────────────────────────────────
# load_posts_for_target
# ─────────────────────────────────────────────────────────────────────────────

class TestLoadPostsForTarget:
    def test_missing_target_returns_empty_list(self, tmp_path):
        """load_posts_for_target should return [] and not raise when target has no data."""
        analyzer = ContentPatternAnalyzer(
            targets=["nonexistent"], raw_base_dir=str(tmp_path)
        )
        result = analyzer.load_posts_for_target("nonexistent")
        assert result == []

    def test_loads_posts_from_file(self, tmp_path):
        """Posts written to a phase1_posts file should be returned."""
        posts = [
            _make_post("#woodart", timestamp="2026-01-01T10:00:00Z"),
            _make_post("#gallery"),
        ]
        _write_phase1_file(tmp_path, "my_target", posts)

        analyzer = ContentPatternAnalyzer(
            targets=["my_target"], raw_base_dir=str(tmp_path)
        )
        result = analyzer.load_posts_for_target("my_target")
        assert len(result) == 2


# ─────────────────────────────────────────────────────────────────────────────
# save_outputs
# ─────────────────────────────────────────────────────────────────────────────

class TestSaveOutputs:
    def test_creates_both_files(self, tmp_path):
        """save_outputs should create both the JSON and markdown files."""
        analyzer = ContentPatternAnalyzer(targets=["test"], raw_base_dir=str(tmp_path))
        results = {
            "hashtags": {"woodart": 3},
            "posting_times": {"day_of_week": {}, "hour_of_day": {}, "best_windows": []},
            "themes": {"keywords": {}, "mentioned_accounts": {}, "content_signals": {}},
            "hashtag_sets": [],
            "clusters": {},
            "engagement_by_hashtag": {},
            "targets_analyzed": ["test"],
            "targets_skipped": [],
            "total_posts": 1,
        }
        out_dir = str(tmp_path / "outputs")
        files = analyzer.save_outputs(results, output_dir=out_dir)

        assert "content_analysis_json" in files
        assert "content_strategy_md" in files
        assert Path(files["content_analysis_json"]).exists()
        assert Path(files["content_strategy_md"]).exists()

    def test_markdown_contains_limitations(self, tmp_path):
        """The generated markdown must include the limitations caveat section."""
        analyzer = ContentPatternAnalyzer(targets=["test"], raw_base_dir=str(tmp_path))
        results = {
            "hashtags": {},
            "posting_times": {"day_of_week": {}, "hour_of_day": {}, "best_windows": []},
            "themes": {"keywords": {}, "mentioned_accounts": {}, "content_signals": {}},
            "hashtag_sets": [],
            "clusters": {},
            "engagement_by_hashtag": {},
            "targets_analyzed": ["test"],
            "targets_skipped": [],
            "total_posts": 0,
        }
        out_dir = str(tmp_path / "outputs")
        files = analyzer.save_outputs(results, output_dir=out_dir)

        md_content = Path(files["content_strategy_md"]).read_text()
        assert "Important Limitations" in md_content
        assert "declined" in md_content.lower() or "de-prioritised" in md_content.lower()
