import time
import pytest
from src.utils.rate_limiter import RateLimiter


def test_rate_limiter_enforces_delay():
    """Test that wait() enforces minimum delay"""
    config = {
        "min_delay_seconds": 0.1,
        "max_delay_seconds": 0.2,
        "pause_after_n_requests": 5,
        "pause_duration_seconds": 0.5
    }
    limiter = RateLimiter(config)

    start = time.time()
    limiter.wait()
    elapsed = time.time() - start

    assert elapsed >= config["min_delay_seconds"], "Delay too short"
    assert elapsed <= config["max_delay_seconds"] + 0.1, "Delay too long"


def test_rate_limiter_periodic_pause():
    """Test that periodic pause happens after N requests"""
    config = {
        "min_delay_seconds": 0.01,
        "max_delay_seconds": 0.02,
        "pause_after_n_requests": 3,
        "pause_duration_seconds": 0.1
    }
    limiter = RateLimiter(config)

    # First 2 requests should be fast
    for _ in range(2):
        limiter.wait()

    # 3rd request should trigger pause
    start = time.time()
    limiter.wait()
    elapsed = time.time() - start

    assert elapsed >= config["pause_duration_seconds"], "Pause not triggered"


def test_rate_limiter_exponential_backoff():
    """Test exponential backoff on failures"""
    config = {"backoff_base": 1}
    limiter = RateLimiter(config)

    # First failure: 2^0 = 1 second
    delay1 = limiter.on_failure(attempt=0)
    assert delay1 == 1

    # Second failure: 2^1 = 2 seconds
    delay2 = limiter.on_failure(attempt=1)
    assert delay2 == 2

    # Third failure: 2^2 = 4 seconds
    delay3 = limiter.on_failure(attempt=2)
    assert delay3 == 4
