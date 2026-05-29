import logging
import re
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from src.collectors.base_collector import BaseCollector
from src.utils.rate_limiter import RateLimiter
from src.utils.session_manager import SessionManager

logger = logging.getLogger(__name__)


class PlaywrightCollector(BaseCollector):
    """Playwright-based browser automation collector"""

    def __init__(self, config):
        super().__init__(config)
        self.rate_limiter = RateLimiter(config["rate_limiting"])
        self.session_manager = SessionManager(config)
        self.browser = None
        self.context = None
        self.page = None

    def build_profile_url(self, username):
        """Build Instagram profile URL"""
        return f"https://www.instagram.com/{username}/"

    def collect(self):
        """Main collection orchestration (Phase 0-3)"""
        logger.info(f"Starting Playwright collection for {self.target_account}")

        try:
            with sync_playwright() as p:
                self.browser = p.chromium.launch(headless=False)
                self.context = self.browser.new_context()
                self.page = self.context.new_page()

                # Load saved session if available
                self.session_manager.load_session(self.context)

                # Phase 0: Collect target profile
                phase0_data = self.collect_phase0_profile()

                # Save session for next run
                self.session_manager.save_session(self.context)

                return {
                    "phase0": phase0_data,
                    "phase1": None,  # Stub
                    "phase2": None,  # Stub
                    "phase3": None   # Stub
                }

        finally:
            if self.browser:
                self.browser.close()

    def collect_phase0_profile(self):
        """Phase 0: Collect target account profile data"""
        logger.info(f"Phase 0: Collecting profile for {self.target_account}")

        url = self.build_profile_url(self.target_account)

        try:
            self.page.goto(url, wait_until="networkidle")
            self.rate_limiter.wait()

            # Check for login wall
            if self.session_manager.detect_login_wall(self.page):
                if not self.session_manager.prompt_for_login():
                    logger.warning("User skipped authentication, data may be limited")

            # Extract profile data
            profile_data = self.extract_profile_data(self.page, self.target_account)

            # Create metadata
            metadata = self.create_metadata(
                source="playwright",
                phase="phase0_profile",
                authenticated=self.session_manager.is_authenticated()
            )

            result = {
                "metadata": metadata,
                "profile": profile_data
            }

            # Save progress
            self.save_progress("phase0_profile", result)

            return result

        except PlaywrightTimeout as e:
            logger.error(f"Timeout loading profile: {e}")
            return None
        except Exception as e:
            logger.error(f"Error in Phase 0: {e}")
            return None

    def extract_profile_data(self, page, username):
        """Extract profile data from page"""
        data = {"username": username}

        try:
            # Strategy 1: Try header section with multiple selectors
            header_selectors = [
                "header section",
                '[role="main"] header',
                "article header"
            ]

            header_text = None
            for selector in header_selectors:
                try:
                    element = page.locator(selector).first
                    if element:
                        header_text = element.text_content(timeout=5000)
                        if header_text:
                            break
                except:
                    continue

            # Parse counts from header text
            if header_text:
                # Posts: "123 posts" or "1,234 posts"
                post_match = re.search(r'([\d,]+)\s*posts?', header_text, re.IGNORECASE)
                if post_match:
                    data["post_count"] = int(post_match.group(1).replace(',', ''))

                # Followers: "1,234 followers" or "5.6M followers"
                follower_match = re.search(r'([\d,\.]+[KMB]?)\s*followers?', header_text, re.IGNORECASE)
                if follower_match:
                    data["follower_count"] = self._parse_count(follower_match.group(1))

                # Following: "910 following"
                following_match = re.search(r'([\d,]+)\s*following', header_text, re.IGNORECASE)
                if following_match:
                    data["following_count"] = int(following_match.group(1).replace(',', ''))

            # Strategy 2: Try individual stat elements
            if "follower_count" not in data:
                try:
                    followers_link = page.locator('a[href*="/followers/"]').first
                    if followers_link:
                        text = followers_link.text_content(timeout=5000)
                        data["follower_count"] = self._parse_count(text.split()[0])
                except:
                    pass

            # Extract bio
            bio_selectors = [
                "h1 + div",
                "header section div.-vDIg span",
                '[data-testid="bio"]'
            ]

            for selector in bio_selectors:
                try:
                    bio_element = page.query_selector(selector)
                    if bio_element:
                        data["bio"] = bio_element.text_content()
                        break
                except:
                    continue

            # Extract profile picture URL
            try:
                img_elements = page.query_selector_all("header img")
                for img in img_elements:
                    src = img.get_attribute("src")
                    if src and ("profile" in src.lower() or "150x150" in src):
                        data["profile_pic_url"] = src
                        break
            except:
                pass

            # Set None for missing optional fields
            data.setdefault("post_count", None)
            data.setdefault("follower_count", None)
            data.setdefault("following_count", None)
            data.setdefault("bio", None)
            data.setdefault("profile_pic_url", None)

            logger.info(f"Extracted profile data for {username}: {data}")
            return data

        except Exception as e:
            logger.error(f"Error extracting profile data: {e}")
            return data

    def _parse_count(self, text):
        """Parse count strings like '1.2M' or '5,678' to integers"""
        text = text.strip().replace(',', '')

        # Handle M (millions), K (thousands), B (billions)
        multipliers = {'K': 1000, 'M': 1000000, 'B': 1000000000}

        for suffix, multiplier in multipliers.items():
            if suffix in text.upper():
                number = float(text.upper().replace(suffix, ''))
                return int(number * multiplier)

        try:
            return int(text)
        except ValueError:
            return None

    # Phase 1-3 stubs (to be implemented in later tasks)

    def collect_phase1_followers_following(self):
        """Phase 1: Collect followers and following lists (STUB)"""
        logger.info("Phase 1: Followers/Following collection not yet implemented")
        return None

    def collect_phase2_recent_posts(self):
        """Phase 2: Collect recent posts and engagement (STUB)"""
        logger.info("Phase 2: Recent posts collection not yet implemented")
        return None

    def collect_phase3_commenters(self):
        """Phase 3: Collect top commenters (STUB)"""
        logger.info("Phase 3: Commenters collection not yet implemented")
        return None
