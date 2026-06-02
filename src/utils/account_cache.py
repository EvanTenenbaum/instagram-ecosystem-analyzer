"""
Global account profile cache with TTL.

Stores fetched profile data keyed by username. Entries expire after
max_age_days (default 30). Used by enrich.py to avoid re-fetching
profiles already collected in previous runs.

Cache file: data/account_cache.json (gitignored)
"""
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

DEFAULT_CACHE_FILE = "data/account_cache.json"
DEFAULT_MAX_AGE_DAYS = 30


class AccountCache:
    """
    Persistent profile cache with TTL.

    Schema per entry:
    {
        "username": str,
        "follower_count": int | None,
        "following_count": int | None,
        "post_count": int | None,
        "bio": str | None,
        "profile_pic_url": str | None,
        "fetched_at": "2026-06-01T16:00:00+00:00",  # ISO with tz
        "source": "playwright"  # for future: "api", "manual"
    }
    """

    def __init__(self, cache_file: str = DEFAULT_CACHE_FILE,
                 max_age_days: int = DEFAULT_MAX_AGE_DAYS):
        self.cache_file = Path(cache_file)
        self.max_age_days = max_age_days
        self._cache: dict[str, dict] = {}
        self._load()

    def _load(self):
        """Load cache from disk. Silent if file doesn't exist."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file) as f:
                    self._cache = json.load(f)
                logger.info(f"Account cache loaded: {len(self._cache)} entries")
            except Exception as e:
                logger.warning(f"Could not load account cache: {e}")
                self._cache = {}
        else:
            self._cache = {}

    def save(self):
        """Persist cache to disk."""
        self.cache_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.cache_file, "w") as f:
            json.dump(self._cache, f, indent=2)
        logger.info(f"Account cache saved: {len(self._cache)} entries")

    def get(self, username: str) -> Optional[dict]:
        """
        Return cached profile if it exists and is not stale.
        Returns None if missing or expired.
        """
        entry = self._cache.get(username)
        if not entry:
            return None

        fetched_at_str = entry.get("fetched_at")
        if not fetched_at_str:
            return None

        try:
            fetched_at = datetime.fromisoformat(fetched_at_str)
            age_days = (datetime.now(timezone.utc) - fetched_at).days
            if age_days > self.max_age_days:
                logger.debug(f"Cache entry for @{username} is stale ({age_days} days old)")
                return None
        except Exception:
            return None

        return entry

    def set(self, profile: dict):
        """
        Store a profile. Adds fetched_at timestamp.
        Profile dict must have 'username' key.
        """
        username = profile.get("username")
        if not username:
            return

        entry = dict(profile)
        entry["fetched_at"] = datetime.now(timezone.utc).isoformat()
        entry["source"] = entry.get("source", "playwright")
        self._cache[username] = entry

    def has_fresh(self, username: str) -> bool:
        """True if username has a non-stale cache entry."""
        return self.get(username) is not None

    def get_all_fresh(self) -> dict[str, dict]:
        """Return all non-stale entries."""
        return {u: e for u in self._cache if (e := self.get(u)) is not None}

    def size(self) -> int:
        return len(self._cache)

    def fresh_count(self) -> int:
        return len(self.get_all_fresh())

    def stats(self) -> dict:
        total = len(self._cache)
        fresh = self.fresh_count()
        return {
            "total_entries": total,
            "fresh_entries": fresh,
            "stale_entries": total - fresh,
            "max_age_days": self.max_age_days,
        }
