import time
import random
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Manages request pacing and backoff logic"""

    def __init__(self, config):
        self.min_delay = config.get("min_delay_seconds", 0)
        self.max_delay = config.get("max_delay_seconds", 0)
        self.pause_after = config.get("pause_after_n_requests", float('inf'))
        self.pause_duration = config.get("pause_duration_seconds", 0)
        self.backoff_base = config.get("backoff_base", 60)
        self.request_count = 0

    def wait(self):
        """Enforce delay between requests"""
        self.request_count += 1

        # Periodic pause after N requests
        if self.request_count % self.pause_after == 0:
            logger.info(f"Periodic pause after {self.request_count} requests")
            time.sleep(self.pause_duration)

        # Random delay between min and max
        delay = random.uniform(self.min_delay, self.max_delay)
        logger.debug(f"Waiting {delay:.2f}s before next request")
        time.sleep(delay)

    def on_rate_limit(self):
        """Handle rate limit signal (429, CAPTCHA)"""
        logger.warning("Rate limit detected, pausing 60 seconds")
        time.sleep(60)

    def on_failure(self, attempt):
        """Calculate exponential backoff delay"""
        delay = self.backoff_base * (2 ** attempt)
        logger.warning(f"Failure attempt {attempt}, backing off {delay}s")
        return delay

    def reset(self):
        """Reset request counter"""
        self.request_count = 0
