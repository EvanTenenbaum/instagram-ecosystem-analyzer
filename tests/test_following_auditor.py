"""Unit tests for FollowingAuditor.

All tests use synthetic in-memory fixture data only — no browser, no Instagram,
no filesystem writes beyond pytest's tmp_path fixture.
"""

import csv
import json
from pathlib import Path

import pytest

from src.analyzers.following_auditor import FollowingAuditor


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_auditor(artist: str = "test_artist", data_dir: str = None, tmp_path=None):
    """Return a FollowingAuditor."""
    return FollowingAuditor(artist_username=artist, data_dir=str(data_dir or tmp_path))


def _write_following_file(tmp_path: Path, username: str, following: list[str]) -> Path:
    """Write a synthetic phase2_following JSON file."""
    target_dir = tmp_path / username
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "phase2_following_20260101_000000.json"
    payload = {
        "metadata": {
            "phase": "phase2_following",
            "target_account": username,
            "timestamp": "2026-01-01T00:00:00",
        },
        "following": following,
    }
    path.write_text(json.dumps(payload))
    return path


def _write_profile_file(tmp_path: Path, username: str, follower_count: int = 1000) -> Path:
    """Write a synthetic phase0_profile JSON file."""
    target_dir = tmp_path / username
    target_dir.mkdir(parents=True, exist_ok=True)
    path = target_dir / "phase0_profile_20260101_000000.json"
    payload = {
        "metadata": {
            "phase": "phase0_profile",
            "target_account": username,
            "timestamp": "2026-01-01T00:00:00",
        },
        "profile": {
            "username": username,
            "follower_count": follower_count,
            "following_count": 200,
            "post_count": 50,
        },
    }
    path.write_text(json.dumps(payload))
    return path


def _write_super_csv(tmp_path: Path, filename: str, accounts: list[dict]) -> Path:
    """Write a synthetic super_accounts CSV."""
    path = tmp_path / filename
    fieldnames = [
        "username", "networks_count", "networks_list", "cross_network_score",
        "avg_overall_score", "max_overall_score", "avg_proximity",
        "avg_engagement", "avg_bridge", "categories", "tier",
    ]
    with open(path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for a in accounts:
            row = {k: "" for k in fieldnames}
            row.update(a)
            writer.writerow(row)

    return path


# ---------------------------------------------------------------------------
# Tests: load_artist_following
# ---------------------------------------------------------------------------

class TestLoadArtistFollowing:
    def test_returns_empty_when_no_directory(self, tmp_path):
        auditor = _make_auditor(data_dir=str(tmp_path))
        result = auditor.load_artist_following()
        assert result == []

    def test_returns_empty_when_no_files(self, tmp_path):
        artist_dir = tmp_path / "test_artist"
        artist_dir.mkdir()
        auditor = _make_auditor(data_dir=str(tmp_path))
        result = auditor.load_artist_following()
        assert result == []

    def test_loads_following_list(self, tmp_path):
        _write_following_file(tmp_path, "test_artist", ["alice", "bob", "charlie"])
        auditor = _make_auditor(data_dir=str(tmp_path))
        result = auditor.load_artist_following()
        assert sorted(result) == ["alice", "bob", "charlie"]

    def test_uses_latest_file_only(self, tmp_path):
        target_dir = tmp_path / "test_artist"
        target_dir.mkdir(parents=True)
        # Write older file
        older = target_dir / "phase2_following_20250101_000000.json"
        older.write_text(json.dumps({"metadata": {}, "following": ["old"]}))
        # Write newer file
        newer = target_dir / "phase2_following_20260101_000000.json"
        newer.write_text(json.dumps({"metadata": {}, "following": ["new"]}))

        auditor = _make_auditor(data_dir=str(tmp_path))
        result = auditor.load_artist_following()
        assert result == ["new"]


# ---------------------------------------------------------------------------
# Tests: build_strategic_lists
# ---------------------------------------------------------------------------

class TestBuildStrategicLists:
    def test_builds_target_galleries(self, tmp_path):
        _write_profile_file(tmp_path, "gallery1", 5000)
        _write_profile_file(tmp_path, "gallery2", 10000)

        auditor = _make_auditor(data_dir=str(tmp_path))
        result = auditor.build_strategic_lists(
            targets=["gallery1", "gallery2"],
        )

        assert len(result["target_galleries"]) == 2
        usernames = {t["username"] for t in result["target_galleries"]}
        assert usernames == {"gallery1", "gallery2"}

    def test_includes_super_accounts_from_csv(self, tmp_path):
        csv_path = _write_super_csv(tmp_path, "super_accounts.csv", [
            {"username": "super1", "networks_count": "3", "tier": "A", "cross_network_score": "70", "categories": "gallery"},
            {"username": "super2", "networks_count": "2", "tier": "B", "cross_network_score": "40", "categories": "collector"},
        ])

        auditor = _make_auditor(data_dir=str(tmp_path))
        result = auditor.build_strategic_lists(
            targets=["gallery1"],
            super_accounts_csv=str(csv_path),
        )

        assert len(result["super_accounts"]) == 2
        assert "super1" in [s["username"] for s in result["super_accounts"]]

    def test_deduplicates_across_categories(self, tmp_path):
        _write_profile_file(tmp_path, "gallery1", 5000)
        csv_path = _write_super_csv(tmp_path, "super_accounts.csv", [
            {"username": "gallery1", "networks_count": "2", "tier": "B", "cross_network_score": "45", "categories": "gallery"},
        ])

        auditor = _make_auditor(data_dir=str(tmp_path))
        result = auditor.build_strategic_lists(
            targets=["gallery1"],
            super_accounts_csv=str(csv_path),
        )

        # gallery1 should only appear once — in target_galleries
        assert len(result["target_galleries"]) == 1
        # gallery1 should NOT appear in super_accounts (dedup)
        sa_usernames = [s["username"] for s in result["super_accounts"]]
        assert "gallery1" not in sa_usernames

    def test_includes_known_accounts(self, tmp_path):
        auditor = _make_auditor(data_dir=str(tmp_path))
        result = auditor.build_strategic_lists(
            targets=[],
            known_accounts=["museum1", "fair1"],
        )
        assert len(result["major_institutions"]) == 2
        usernames = {i["username"] for i in result["major_institutions"]}
        assert usernames == {"museum1", "fair1"}


# ---------------------------------------------------------------------------
# Tests: audit
# ---------------------------------------------------------------------------

class TestAudit:
    def test_returns_empty_without_data(self, tmp_path):
        auditor = _make_auditor(data_dir=str(tmp_path))
        strategic = auditor.build_strategic_lists(targets=["gallery1"])
        result = auditor.audit(strategic)

        assert result["has_following_data"] is False
        assert result["coverage"]["target_galleries"]["followed"] == 0

    def test_calculates_coverage(self, tmp_path):
        _write_following_file(tmp_path, "test_artist", ["gallery1", "gallery2"])
        _write_profile_file(tmp_path, "gallery1")
        _write_profile_file(tmp_path, "gallery2")
        _write_profile_file(tmp_path, "gallery3")

        auditor = _make_auditor(data_dir=str(tmp_path))
        strategic = auditor.build_strategic_lists(targets=["gallery1", "gallery2", "gallery3"])
        result = auditor.audit(strategic)

        assert result["has_following_data"] is True
        assert result["coverage"]["target_galleries"]["followed"] == 2
        assert result["coverage"]["target_galleries"]["total"] == 3
        assert result["coverage"]["target_galleries"]["pct"] == 66.7

    def test_identifies_missing_accounts(self, tmp_path):
        _write_following_file(tmp_path, "test_artist", ["gallery1"])
        _write_profile_file(tmp_path, "gallery1")
        _write_profile_file(tmp_path, "gallery2")

        auditor = _make_auditor(data_dir=str(tmp_path))
        strategic = auditor.build_strategic_lists(targets=["gallery1", "gallery2"])
        result = auditor.audit(strategic)

        missing = result["missing"]["target_galleries"]
        assert len(missing) == 1
        assert missing[0]["username"] == "gallery2"

    def test_identifies_followed_accounts(self, tmp_path):
        _write_following_file(tmp_path, "test_artist", ["gallery1", "gallery3"])
        _write_profile_file(tmp_path, "gallery1")
        _write_profile_file(tmp_path, "gallery2")
        _write_profile_file(tmp_path, "gallery3")

        auditor = _make_auditor(data_dir=str(tmp_path))
        strategic = auditor.build_strategic_lists(targets=["gallery1", "gallery2", "gallery3"])
        result = auditor.audit(strategic)

        followed = result["followed"]["target_galleries"]
        assert sorted(followed) == ["gallery1", "gallery3"]


# ---------------------------------------------------------------------------
# Tests: priority_score
# ---------------------------------------------------------------------------

class TestPriorityScore:
    def test_tier_a_super_account_gets_10(self, tmp_path):
        auditor = _make_auditor(data_dir=str(tmp_path))
        strategic = {
            "super_accounts": [
                {"username": "super_a", "tier": "A", "networks_count": 3},
            ],
        }
        score = auditor.priority_score("super_a", strategic)
        assert score >= 10.0

    def test_target_gallery_gets_3_plus_follower_bonus(self, tmp_path):
        auditor = _make_auditor(data_dir=str(tmp_path))
        strategic = {
            "target_galleries": [
                {"username": "big_gallery", "reason": "target", "follower_count": 50000},
            ],
        }
        score = auditor.priority_score("big_gallery", strategic)
        # 3 base + 50000/10000 = 3 + 5 = 8
        assert score == 8.0

    def test_unknown_gets_zero(self, tmp_path):
        auditor = _make_auditor(data_dir=str(tmp_path))
        strategic = {
            "target_galleries": [],
            "super_accounts": [],
        }
        score = auditor.priority_score("nobody", strategic)
        assert score == 0.0


# ---------------------------------------------------------------------------
# Tests: format_report
# ---------------------------------------------------------------------------

class TestFormatReport:
    def test_includes_artist_name(self, tmp_path):
        auditor = _make_auditor(artist="test_artist", data_dir=str(tmp_path))
        strategic = auditor.build_strategic_lists(targets=[])
        result = auditor.audit(strategic)
        report = auditor.format_report(result)
        assert "@test_artist" in report

    def test_no_data_shows_help_message(self, tmp_path):
        auditor = _make_auditor(data_dir=str(tmp_path))
        strategic = auditor.build_strategic_lists(targets=["gallery1"])
        result = auditor.audit(strategic)
        report = auditor.format_report(result)
        assert "No following data found" in report

    def test_includes_recommendations(self, tmp_path):
        _write_following_file(tmp_path, "test_artist", ["gallery1"])
        _write_profile_file(tmp_path, "gallery1")
        _write_profile_file(tmp_path, "gallery2")
        _write_profile_file(tmp_path, "gallery3")

        auditor = _make_auditor(data_dir=str(tmp_path))
        strategic = auditor.build_strategic_lists(targets=["gallery1", "gallery2", "gallery3"])
        result = auditor.audit(strategic)
        report = auditor.format_report(result)
        assert "RECOMMENDED IMMEDIATE ACTIONS" in report


# ---------------------------------------------------------------------------
# Tests: run
# ---------------------------------------------------------------------------

class TestRun:
    def test_run_returns_all_keys(self, tmp_path):
        _write_following_file(tmp_path, "test_artist", ["gallery1"])
        _write_profile_file(tmp_path, "gallery1")

        auditor = _make_auditor(data_dir=str(tmp_path))
        result = auditor.run(targets=["gallery1"])

        assert "strategic_lists" in result
        assert "audit_result" in result
        assert "report" in result
        assert isinstance(result["report"], str)
