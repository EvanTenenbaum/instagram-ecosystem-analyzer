"""Unit tests for ContentAuditor.

All tests use synthetic in-memory fixture data only — no browser, no Instagram,
no filesystem writes beyond pytest's tmp_path fixture.
"""

import json
from pathlib import Path

import pytest

from src.analyzers.content_auditor import ContentAuditor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_auditor(artist: str = "test_artist", targets=None, raw_base_dir=None, tmp_path=None):
    """Return a ContentAuditor."""
    raw = str(raw_base_dir or tmp_path)
    return ContentAuditor(
        artist_username=artist,
        targets=targets or ["test_target"],
        raw_base_dir=raw,
    )


def _make_post(caption="", timestamp=None, commenters=None, mentions=None):
    """Return a minimal post dict matching the phase1_posts schema."""
    return {
        "post_url": "https://instagram.com/p/TEST/",
        "caption": caption,
        "mentions": mentions or [],
        "timestamp": timestamp,
        "commenters": commenters or [],
    }


def _write_phase1_file(tmp_path: Path, username: str, posts: list) -> Path:
    """Write a synthetic phase1_posts JSON file."""
    target_dir = tmp_path / username
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "phase1_posts_20260101_000000.json"
    payload = {
        "metadata": {
            "phase": "phase1_posts",
            "target_account": username,
            "timestamp": "2026-01-01T00:00:00Z",
        },
        "posts": posts,
    }
    path.write_text(json.dumps(payload))
    return path


# ---------------------------------------------------------------------------
# Tests: load_artist_posts / load_target_posts
# ---------------------------------------------------------------------------

class TestLoadPosts:
    def test_returns_empty_when_no_directory(self, tmp_path):
        auditor = _make_auditor(tmp_path=tmp_path)
        result = auditor.load_artist_posts()
        assert result == []

    def test_returns_empty_when_no_files(self, tmp_path):
        (tmp_path / "test_artist").mkdir()
        auditor = _make_auditor(tmp_path=tmp_path)
        result = auditor.load_artist_posts()
        assert result == []

    def test_loads_posts(self, tmp_path):
        posts = [
            _make_post(caption="Hello #art"),
            _make_post(caption="Beautiful #design"),
        ]
        _write_phase1_file(tmp_path, "test_artist", posts)

        auditor = _make_auditor(tmp_path=tmp_path)
        result = auditor.load_artist_posts()
        assert len(result) == 2

    def test_loads_target_posts(self, tmp_path):
        posts = [_make_post(caption="#gallery")]
        _write_phase1_file(tmp_path, "target1", posts)

        auditor = _make_auditor(targets=["target1"], tmp_path=tmp_path)
        result = auditor.load_target_posts("target1")
        assert len(result) == 1


# ---------------------------------------------------------------------------
# Tests: extract_hashtags
# ---------------------------------------------------------------------------

class TestExtractHashtags:
    def test_basic_extraction(self, tmp_path):
        auditor = _make_auditor(tmp_path=tmp_path)
        posts = [
            _make_post(caption="#wood #craft #design"),
            _make_post(caption="#wood #art"),
        ]
        result = auditor.extract_hashtags(posts)
        assert result["wood"] == 2
        assert result["craft"] == 1
        assert result["design"] == 1
        assert result["art"] == 1

    def test_strips_punctuation(self, tmp_path):
        auditor = _make_auditor(tmp_path=tmp_path)
        posts = [
            _make_post(caption="#wood. #craft! #design,"),
        ]
        result = auditor.extract_hashtags(posts)
        assert "wood" in result
        assert "craft" in result
        assert "design" in result

    def test_case_insensitive(self, tmp_path):
        auditor = _make_auditor(tmp_path=tmp_path)
        posts = [
            _make_post(caption="#WOOD #Wood #wood"),
        ]
        result = auditor.extract_hashtags(posts)
        assert result["wood"] == 3

    def test_empty_captions(self, tmp_path):
        auditor = _make_auditor(tmp_path=tmp_path)
        posts = [
            _make_post(caption=None),
            _make_post(caption=""),
            _make_post(caption="no hashtags here"),
        ]
        result = auditor.extract_hashtags(posts)
        assert result == {}


# ---------------------------------------------------------------------------
# Tests: extract_posting_pattern
# ---------------------------------------------------------------------------

class TestExtractPostingPattern:
    def test_empty_posts(self, tmp_path):
        auditor = _make_auditor(tmp_path=tmp_path)
        result = auditor.extract_posting_pattern([])
        assert result["total_posts"] == 0
        assert result["posts_per_week"] == 0.0

    def test_extracts_day_of_week(self, tmp_path):
        auditor = _make_auditor(tmp_path=tmp_path)
        # 2026-06-01 is a Monday
        posts = [
            _make_post(timestamp="2026-06-01T10:00:00Z"),
            _make_post(timestamp="2026-06-01T14:00:00Z"),
            _make_post(timestamp="2026-06-03T09:00:00Z"),  # Wednesday
        ]
        result = auditor.extract_posting_pattern(posts)
        assert result["day_of_week"]["Monday"] == 2
        assert result["day_of_week"]["Wednesday"] == 1

    def test_calculates_posts_per_week(self, tmp_path):
        auditor = _make_auditor(tmp_path=tmp_path)
        posts = []
        # 14 posts over 14 days = 7 per week
        for day in range(14):
            posts.append(_make_post(timestamp=f"2026-06-{day+1:02d}T10:00:00Z"))
        result = auditor.extract_posting_pattern(posts)
        assert pytest.approx(result["posts_per_week"], 0.5) == 7.0

    def test_bad_timestamps_handled(self, tmp_path):
        auditor = _make_auditor(tmp_path=tmp_path)
        posts = [
            _make_post(timestamp="not-a-date"),
            _make_post(timestamp="2026-06-01T10:00:00Z"),
        ]
        result = auditor.extract_posting_pattern(posts)
        assert result["total_posts"] == 2
        assert result["posts_per_week"] == 0.0  # Only 1 valid timestamp, can't calc span


# ---------------------------------------------------------------------------
# Tests: build_network_hashtags
# ---------------------------------------------------------------------------

class TestBuildNetworkHashtags:
    def test_aggregates_across_targets(self, tmp_path):
        _write_phase1_file(tmp_path, "target1", [
            _make_post(caption="#wood #craft"),
        ])
        _write_phase1_file(tmp_path, "target2", [
            _make_post(caption="#wood #gallery"),
        ])

        auditor = _make_auditor(targets=["target1", "target2"], tmp_path=tmp_path)
        result = auditor.build_network_hashtags()
        assert result["wood"] == 2
        assert result["craft"] == 1
        assert result["gallery"] == 1


# ---------------------------------------------------------------------------
# Tests: compare_hashtags
# ---------------------------------------------------------------------------

class TestCompareHashtags:
    def test_identifies_aligned_and_missing(self, tmp_path):
        auditor = _make_auditor(tmp_path=tmp_path)

        artist_tags = {"wood": 10, "craft": 5, "handmade": 3}
        network_tags = {"wood": 8, "gallery": 4, "design": 3, "contemporary": 2}

        result = auditor.compare_hashtags(artist_tags, network_tags)
        assert "wood" in result["aligned"]
        assert "craft" in result["artist_only"]
        assert "gallery" in result["network_only"]
        assert "handmade" in result["artist_only"]
        assert "design" in result["network_only"]

    def test_generates_recommendations(self, tmp_path):
        auditor = _make_auditor(tmp_path=tmp_path)

        artist_tags = {"wood": 10, "craft": 5, "handmade": 3, "lathe": 3, "turning": 3}
        network_tags = {"wood": 8, "gallery": 4, "design": 3, "contemporary": 2, "collectible": 2}

        result = auditor.compare_hashtags(artist_tags, network_tags)
        recs = result["recommendations"]
        # Should have add recommendations for network tags not used
        add_recs = [r for r in recs if r["action"] == "add"]
        assert len(add_recs) > 0


# ---------------------------------------------------------------------------
# Tests: audit
# ---------------------------------------------------------------------------

class TestAudit:
    def test_audit_returns_structure(self, tmp_path):
        _write_phase1_file(tmp_path, "test_artist", [
            _make_post(caption="#wood #craft", timestamp="2026-06-01T10:00:00Z"),
        ])
        _write_phase1_file(tmp_path, "target1", [
            _make_post(caption="#wood #gallery", timestamp="2026-06-01T10:00:00Z"),
        ])

        auditor = _make_auditor(targets=["target1"], tmp_path=tmp_path)
        result = auditor.audit()

        assert "artist_hashtags" in result
        assert "network_hashtags" in result
        assert "hashtag_gaps" in result
        assert "artist_posting" in result
        assert "network_posting" in result
        assert result["has_artist_data"] is True
        assert result["has_network_data"] is True

    def test_audit_graceful_no_artist_data(self, tmp_path):
        _write_phase1_file(tmp_path, "target1", [
            _make_post(caption="#gallery"),
        ])

        auditor = _make_auditor(targets=["target1"], tmp_path=tmp_path)
        result = auditor.audit()

        assert result["has_artist_data"] is False
        assert result["has_network_data"] is True

    def test_audit_graceful_no_network_data(self, tmp_path):
        _write_phase1_file(tmp_path, "test_artist", [
            _make_post(caption="#wood"),
        ])

        auditor = _make_auditor(targets=["empty_target"], tmp_path=tmp_path)
        result = auditor.audit()

        assert result["has_artist_data"] is True
        # No network data if target has no posts
        assert result["has_network_data"] is False


# ---------------------------------------------------------------------------
# Tests: format_report
# ---------------------------------------------------------------------------

class TestFormatReport:
    def test_includes_artist_name(self, tmp_path):
        _write_phase1_file(tmp_path, "test_artist", [
            _make_post(caption="#wood", timestamp="2026-06-01T10:00:00Z"),
        ])
        _write_phase1_file(tmp_path, "target1", [
            _make_post(caption="#wood", timestamp="2026-06-01T10:00:00Z"),
        ])

        auditor = _make_auditor(targets=["target1"], tmp_path=tmp_path)
        result = auditor.audit()
        report = auditor.format_report(result)
        assert "@test_artist" in report

    def test_no_data_shows_warning(self, tmp_path):
        auditor = _make_auditor(targets=["target1"], tmp_path=tmp_path)
        result = auditor.audit()
        report = auditor.format_report(result)
        assert "No post data found" in report

    def test_includes_hashtag_section(self, tmp_path):
        _write_phase1_file(tmp_path, "test_artist", [
            _make_post(caption="#wood #craft", timestamp="2026-06-01T10:00:00Z"),
        ])
        _write_phase1_file(tmp_path, "target1", [
            _make_post(caption="#gallery", timestamp="2026-06-01T10:00:00Z"),
        ])

        auditor = _make_auditor(targets=["target1"], tmp_path=tmp_path)
        result = auditor.audit()
        report = auditor.format_report(result)
        assert "HASHTAG" in report.upper()


# ---------------------------------------------------------------------------
# Tests: run
# ---------------------------------------------------------------------------

class TestRun:
    def test_run_returns_all_keys(self, tmp_path):
        _write_phase1_file(tmp_path, "test_artist", [
            _make_post(caption="#wood", timestamp="2026-06-01T10:00:00Z"),
        ])
        _write_phase1_file(tmp_path, "target1", [
            _make_post(caption="#wood", timestamp="2026-06-01T10:00:00Z"),
        ])

        auditor = _make_auditor(targets=["target1"], tmp_path=tmp_path)
        result = auditor.run()

        assert "audit_result" in result
        assert "report" in result
        assert isinstance(result["report"], str)
