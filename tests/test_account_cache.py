"""Unit tests for AccountCache."""
import json
import pytest
from datetime import datetime, timezone, timedelta
from src.utils.account_cache import AccountCache


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def cache(tmp_path):
    """Fresh in-memory cache backed by a tmp file."""
    return AccountCache(cache_file=str(tmp_path / "test_cache.json"), max_age_days=30)


def _make_profile(username="test_user", **kwargs):
    return {"username": username, "follower_count": 1000, **kwargs}


def _stale_timestamp(max_age_days=30):
    """ISO timestamp older than max_age_days."""
    stale_dt = datetime.now(timezone.utc) - timedelta(days=max_age_days + 1)
    return stale_dt.isoformat()


def _fresh_timestamp():
    """ISO timestamp from 1 day ago — definitely fresh."""
    return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()


# ---------------------------------------------------------------------------
# Basic get/set
# ---------------------------------------------------------------------------

def test_set_and_get_fresh(cache):
    """Stored entry is returned immediately after set()."""
    profile = _make_profile("alice")
    cache.set(profile)
    result = cache.get("alice")
    assert result is not None
    assert result["username"] == "alice"
    assert result["follower_count"] == 1000


def test_get_returns_none_for_missing(cache):
    """get() returns None for unknown username."""
    assert cache.get("nobody") is None


def test_stale_entry_returns_none(cache):
    """Entry older than max_age_days is treated as missing."""
    cache._cache["old_user"] = {
        "username": "old_user",
        "fetched_at": _stale_timestamp(cache.max_age_days),
    }
    assert cache.get("old_user") is None


def test_fresh_entry_within_max_age(cache):
    """Entry within max_age_days is returned."""
    cache._cache["fresh_user"] = {
        "username": "fresh_user",
        "fetched_at": _fresh_timestamp(),
    }
    result = cache.get("fresh_user")
    assert result is not None
    assert result["username"] == "fresh_user"


# ---------------------------------------------------------------------------
# has_fresh
# ---------------------------------------------------------------------------

def test_has_fresh_true_for_fresh_entry(cache):
    cache.set(_make_profile("bob"))
    assert cache.has_fresh("bob") is True


def test_has_fresh_false_for_missing(cache):
    assert cache.has_fresh("nobody") is False


def test_has_fresh_false_for_stale(cache):
    cache._cache["stale_user"] = {
        "username": "stale_user",
        "fetched_at": _stale_timestamp(cache.max_age_days),
    }
    assert cache.has_fresh("stale_user") is False


# ---------------------------------------------------------------------------
# set() behaviour
# ---------------------------------------------------------------------------

def test_set_adds_fetched_at_timestamp(cache):
    """set() always adds fetched_at even if not in profile dict."""
    profile = {"username": "carol", "follower_count": 500}
    assert "fetched_at" not in profile
    cache.set(profile)
    entry = cache._cache["carol"]
    assert "fetched_at" in entry


def test_set_overwrites_existing(cache):
    """set() replaces stale entry with fresh one."""
    cache._cache["dave"] = {
        "username": "dave",
        "fetched_at": _stale_timestamp(cache.max_age_days),
        "follower_count": 100,
    }
    assert cache.has_fresh("dave") is False

    cache.set({"username": "dave", "follower_count": 200})
    assert cache.has_fresh("dave") is True
    assert cache.get("dave")["follower_count"] == 200


def test_set_ignores_profile_without_username(cache):
    """set() silently ignores dicts with no username."""
    cache.set({"follower_count": 999})
    assert cache.size() == 0


# ---------------------------------------------------------------------------
# Persistence
# ---------------------------------------------------------------------------

def test_save_and_reload(tmp_path):
    """Cache persists to disk and reloads correctly."""
    cache_path = str(tmp_path / "cache.json")
    c1 = AccountCache(cache_file=cache_path, max_age_days=30)
    c1.set(_make_profile("eve"))
    c1.save()

    c2 = AccountCache(cache_file=cache_path, max_age_days=30)
    result = c2.get("eve")
    assert result is not None
    assert result["username"] == "eve"


# ---------------------------------------------------------------------------
# Stats and counts
# ---------------------------------------------------------------------------

def test_stats_returns_correct_counts(cache):
    cache.set(_make_profile("frank"))
    cache._cache["stale"] = {
        "username": "stale",
        "fetched_at": _stale_timestamp(cache.max_age_days),
    }
    stats = cache.stats()
    assert stats["total_entries"] == 2
    assert stats["fresh_entries"] == 1
    assert stats["stale_entries"] == 1
    assert stats["max_age_days"] == 30


def test_get_all_fresh_excludes_stale(cache):
    cache.set(_make_profile("grace"))
    cache._cache["stale2"] = {
        "username": "stale2",
        "fetched_at": _stale_timestamp(cache.max_age_days),
    }
    fresh = cache.get_all_fresh()
    assert "grace" in fresh
    assert "stale2" not in fresh


def test_size_counts_all_including_stale(cache):
    cache.set(_make_profile("henry"))
    cache._cache["stale3"] = {
        "username": "stale3",
        "fetched_at": _stale_timestamp(cache.max_age_days),
    }
    assert cache.size() == 2
