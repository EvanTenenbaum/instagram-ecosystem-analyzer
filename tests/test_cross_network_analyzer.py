"""Unit tests for CrossNetworkAnalyzer.

All tests use synthetic in-memory fixture data — no browser, no Instagram,
no filesystem writes beyond a temporary directory.
"""

import csv
import json
import os
import tempfile
from pathlib import Path

import pytest

from src.analyzers.cross_network_analyzer import CrossNetworkAnalyzer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _make_score_file(directory: Path, target: str, scores: list) -> Path:
    """Write a synthetic account_scores_<timestamp>.json file and return its path."""
    target_dir = directory / target
    target_dir.mkdir(parents=True, exist_ok=True)
    score_file = target_dir / "account_scores_20260101_000000.json"
    payload = {
        "metadata": {
            "timestamp": "2026-01-01T00:00:00",
            "target_account": target,
            "total_accounts_scored": len(scores),
        },
        "scores": scores,
    }
    with open(score_file, "w") as f:
        json.dump(payload, f)
    return score_file


def _make_score(username: str, overall: float = 50.0, **kwargs) -> dict:
    """Return a minimal scored-account dict."""
    return {
        "username": username,
        "overall_score": overall,
        "proximity_score": kwargs.get("proximity_score", 50.0),
        "engagement_score": kwargs.get("engagement_score", 50.0),
        "bridge_score": kwargs.get("bridge_score", 0.0),
        "category_fit_score": kwargs.get("category_fit_score", 0),
        "category": kwargs.get("category", "unknown"),
        "bio": kwargs.get("bio", ""),
        "follower_count": kwargs.get("follower_count", 1000),
        "following_count": kwargs.get("following_count", 200),
    }


# ---------------------------------------------------------------------------
# Tests: load_target_scores
# ---------------------------------------------------------------------------

class TestLoadTargetScores:
    def test_returns_empty_list_when_directory_missing(self, tmp_path):
        analyzer = CrossNetworkAnalyzer(["target1"], processed_base_dir=str(tmp_path))
        result = analyzer.load_target_scores("nonexistent")
        assert result == []

    def test_returns_empty_list_when_no_score_file(self, tmp_path):
        (tmp_path / "target1").mkdir()
        analyzer = CrossNetworkAnalyzer(["target1"], processed_base_dir=str(tmp_path))
        result = analyzer.load_target_scores("target1")
        assert result == []

    def test_loads_scores_from_json(self, tmp_path):
        scores = [_make_score("alice"), _make_score("bob")]
        _make_score_file(tmp_path, "target1", scores)
        analyzer = CrossNetworkAnalyzer(["target1"], processed_base_dir=str(tmp_path))
        result = analyzer.load_target_scores("target1")
        assert len(result) == 2
        usernames = {s["username"] for s in result}
        assert usernames == {"alice", "bob"}

    def test_picks_latest_score_file(self, tmp_path):
        """When multiple score files exist, the lexicographically last is loaded."""
        target_dir = tmp_path / "target1"
        target_dir.mkdir()
        # Write two files; the later timestamp should win
        for name, username in [
            ("account_scores_20260101_000000.json", "old_alice"),
            ("account_scores_20260601_120000.json", "new_alice"),
        ]:
            path = target_dir / name
            with open(path, "w") as f:
                json.dump({"scores": [_make_score(username)]}, f)

        analyzer = CrossNetworkAnalyzer(["target1"], processed_base_dir=str(tmp_path))
        result = analyzer.load_target_scores("target1")
        assert result[0]["username"] == "new_alice"


# ---------------------------------------------------------------------------
# Tests: find_super_accounts
# ---------------------------------------------------------------------------

class TestFindSuperAccounts:
    def test_basic_super_account_detection(self, tmp_path):
        """alice appears in both target1 and target2 → super account; bob does not."""
        _make_score_file(tmp_path, "target1", [_make_score("alice"), _make_score("bob")])
        _make_score_file(tmp_path, "target2", [_make_score("alice"), _make_score("carol")])

        analyzer = CrossNetworkAnalyzer(["target1", "target2"], processed_base_dir=str(tmp_path))
        super_accounts = analyzer.find_super_accounts()

        usernames = {a["username"] for a in super_accounts}
        assert "alice" in usernames, "alice should be a super account (2 networks)"
        assert "bob" not in usernames, "bob is only in target1"
        assert "carol" not in usernames, "carol is only in target2"

    def test_returns_empty_when_no_overlap(self, tmp_path):
        _make_score_file(tmp_path, "target1", [_make_score("alice")])
        _make_score_file(tmp_path, "target2", [_make_score("bob")])

        analyzer = CrossNetworkAnalyzer(["target1", "target2"], processed_base_dir=str(tmp_path))
        result = analyzer.find_super_accounts()
        assert result == []

    def test_sorted_by_cross_network_score_descending(self, tmp_path):
        """Higher-scoring accounts should rank first."""
        _make_score_file(tmp_path, "t1", [
            _make_score("high_scorer", overall=90.0),
            _make_score("low_scorer", overall=10.0),
        ])
        _make_score_file(tmp_path, "t2", [
            _make_score("high_scorer", overall=90.0),
            _make_score("low_scorer", overall=10.0),
        ])

        analyzer = CrossNetworkAnalyzer(["t1", "t2"], processed_base_dir=str(tmp_path))
        result = analyzer.find_super_accounts()

        scores = [a["cross_network_score"] for a in result]
        assert scores == sorted(scores, reverse=True)
        assert result[0]["username"] == "high_scorer"

    def test_three_network_account(self, tmp_path):
        """Account in 3 of 3 networks should receive maximum breadth score."""
        for target in ["t1", "t2", "t3"]:
            _make_score_file(tmp_path, target, [_make_score("ubiquitous", overall=80.0)])

        analyzer = CrossNetworkAnalyzer(["t1", "t2", "t3"], processed_base_dir=str(tmp_path))
        result = analyzer.find_super_accounts()

        assert len(result) == 1
        account = result[0]
        assert account["networks_count"] == 3
        # 3/3 * 60 + 80/100 * 40 = 60 + 32 = 92
        assert account["cross_network_score"] == pytest.approx(92.0, abs=0.1)

    def test_returns_empty_with_no_targets(self, tmp_path):
        analyzer = CrossNetworkAnalyzer([], processed_base_dir=str(tmp_path))
        assert analyzer.find_super_accounts() == []


# ---------------------------------------------------------------------------
# Tests: cross_network_score formula
# ---------------------------------------------------------------------------

class TestCrossNetworkScoreFormula:
    def test_formula_two_of_two_targets_full_score(self, tmp_path):
        """2/2 networks, avg_score=100 → 60 + 40 = 100."""
        for target in ["t1", "t2"]:
            _make_score_file(tmp_path, target, [_make_score("alice", overall=100.0)])

        analyzer = CrossNetworkAnalyzer(["t1", "t2"], processed_base_dir=str(tmp_path))
        result = analyzer.find_super_accounts()
        assert result[0]["cross_network_score"] == pytest.approx(100.0, abs=0.1)

    def test_formula_two_of_four_targets_zero_avg(self, tmp_path):
        """2/4 networks, avg_score=0 → (2/4)*60 + 0 = 30."""
        for target in ["t1", "t2", "t3", "t4"]:
            score = _make_score("alice", overall=0.0)
            if target in ("t1", "t2"):
                _make_score_file(tmp_path, target, [score])
            else:
                _make_score_file(tmp_path, target, [_make_score("other")])  # no alice

        analyzer = CrossNetworkAnalyzer(["t1", "t2", "t3", "t4"], processed_base_dir=str(tmp_path))
        result = analyzer.find_super_accounts()
        # alice appears in t1 and t2 only
        alice = next(a for a in result if a["username"] == "alice")
        expected = (2 / 4 * 60) + (0.0 / 100 * 40)
        assert alice["cross_network_score"] == pytest.approx(expected, abs=0.1)

    def test_tier_a_assigned_for_high_score(self, tmp_path):
        """Score ≥ 70 with 2 networks → Tier A."""
        for target in ["t1", "t2"]:
            _make_score_file(tmp_path, target, [_make_score("alice", overall=100.0)])

        analyzer = CrossNetworkAnalyzer(["t1", "t2"], processed_base_dir=str(tmp_path))
        result = analyzer.find_super_accounts()
        assert result[0]["tier"] == "A"

    def test_tier_b_assigned_for_two_networks_low_score(self, tmp_path):
        """2/4 networks, low score → Tier B."""
        for target in ["t1", "t2", "t3", "t4"]:
            if target in ("t1", "t2"):
                _make_score_file(tmp_path, target, [_make_score("alice", overall=5.0)])
            else:
                _make_score_file(tmp_path, target, [_make_score("other")])

        analyzer = CrossNetworkAnalyzer(["t1", "t2", "t3", "t4"], processed_base_dir=str(tmp_path))
        result = analyzer.find_super_accounts()
        alice = next(a for a in result if a["username"] == "alice")
        assert alice["tier"] == "B"


# ---------------------------------------------------------------------------
# Tests: save_outputs
# ---------------------------------------------------------------------------

class TestSaveOutputs:
    def test_creates_csv_and_markdown(self, tmp_path):
        """save_outputs should create both output files."""
        analyzer = CrossNetworkAnalyzer(["t1", "t2"], processed_base_dir=str(tmp_path))
        super_accounts = [
            {
                "username": "alice",
                "networks_count": 2,
                "networks_list": "t1,t2",
                "cross_network_score": 80.0,
                "avg_overall_score": 75.0,
                "max_overall_score": 80.0,
                "avg_proximity": 60.0,
                "avg_engagement": 70.0,
                "avg_bridge": 5.0,
                "categories": "gallery",
                "tier": "A",
            }
        ]
        summary = "# Test Summary\nContent here.\n"
        out_dir = str(tmp_path / "outputs")

        files = analyzer.save_outputs(super_accounts, summary, output_dir=out_dir)

        assert "super_accounts_csv" in files
        assert "cross_network_summary" in files
        assert Path(files["super_accounts_csv"]).exists()
        assert Path(files["cross_network_summary"]).exists()

    def test_csv_has_correct_columns(self, tmp_path):
        analyzer = CrossNetworkAnalyzer(["t1", "t2"], processed_base_dir=str(tmp_path))
        account = {
            "username": "bob",
            "networks_count": 2,
            "networks_list": "t1,t2",
            "cross_network_score": 55.0,
            "avg_overall_score": 50.0,
            "max_overall_score": 60.0,
            "avg_proximity": 40.0,
            "avg_engagement": 50.0,
            "avg_bridge": 10.0,
            "categories": "curator",
            "tier": "B",
        }
        out_dir = str(tmp_path / "out")
        files = analyzer.save_outputs([account], "# summary", output_dir=out_dir)

        expected_columns = {
            "username", "networks_count", "networks_list", "cross_network_score",
            "avg_overall_score", "max_overall_score", "avg_proximity",
            "avg_engagement", "avg_bridge", "categories", "tier",
        }
        with open(files["super_accounts_csv"]) as f:
            reader = csv.DictReader(f)
            actual_columns = set(reader.fieldnames or [])
        assert expected_columns == actual_columns

    def test_csv_values_match_input(self, tmp_path):
        analyzer = CrossNetworkAnalyzer(["t1"], processed_base_dir=str(tmp_path))
        account = {
            "username": "carol",
            "networks_count": 2,
            "networks_list": "t1,t2",
            "cross_network_score": 45.0,
            "avg_overall_score": 42.0,
            "max_overall_score": 48.0,
            "avg_proximity": 35.0,
            "avg_engagement": 40.0,
            "avg_bridge": 2.0,
            "categories": "unknown",
            "tier": "B",
        }
        out_dir = str(tmp_path / "out")
        files = analyzer.save_outputs([account], "summary", output_dir=out_dir)

        with open(files["super_accounts_csv"]) as f:
            rows = list(csv.DictReader(f))
        assert len(rows) == 1
        assert rows[0]["username"] == "carol"
        assert float(rows[0]["cross_network_score"]) == pytest.approx(45.0)
        assert rows[0]["tier"] == "B"

    def test_markdown_is_written(self, tmp_path):
        analyzer = CrossNetworkAnalyzer([], processed_base_dir=str(tmp_path))
        summary = "# My Cross-Network Summary\nSome content.\n"
        out_dir = str(tmp_path / "out")
        files = analyzer.save_outputs([], summary, output_dir=out_dir)

        content = Path(files["cross_network_summary"]).read_text()
        assert content == summary


# ---------------------------------------------------------------------------
# Tests: generate_summary
# ---------------------------------------------------------------------------

class TestGenerateSummary:
    def test_summary_contains_target_names(self):
        analyzer = CrossNetworkAnalyzer(["alice_target", "bob_target"])
        md = analyzer.generate_summary([])
        assert "alice_target" in md
        assert "bob_target" in md

    def test_summary_mentions_zero_super_accounts(self):
        analyzer = CrossNetworkAnalyzer(["t1", "t2"])
        md = analyzer.generate_summary([])
        assert "0 super accounts" in md

    def test_summary_lists_tier_a_accounts(self):
        analyzer = CrossNetworkAnalyzer(["t1", "t2"])
        accounts = [
            {
                "username": "star_gallery",
                "networks_count": 2,
                "networks_list": "t1,t2",
                "cross_network_score": 90.0,
                "avg_overall_score": 85.0,
                "max_overall_score": 90.0,
                "avg_proximity": 80.0,
                "avg_engagement": 75.0,
                "avg_bridge": 10.0,
                "categories": "gallery",
                "tier": "A",
            }
        ]
        md = analyzer.generate_summary(accounts)
        assert "star_gallery" in md
        assert "Tier A" in md
