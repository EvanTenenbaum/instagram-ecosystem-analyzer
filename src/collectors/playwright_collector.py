import logging
import os
import re
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from src.collectors.base_collector import BaseCollector
from src.utils.rate_limiter import RateLimiter
from src.utils.session_manager import SessionManager

def _load_env_credentials():
    """Load Instagram credentials from local .env file (never committed)."""
    env_path = Path(__file__).parent.parent.parent / ".env"
    creds = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                creds[k.strip()] = v.strip()
    return (
        creds.get("INSTAGRAM_USERNAME") or os.environ.get("INSTAGRAM_USERNAME"),
        creds.get("INSTAGRAM_PASSWORD") or os.environ.get("INSTAGRAM_PASSWORD"),
    )

logger = logging.getLogger(__name__)


class PlaywrightCollector(BaseCollector):
    """Playwright-based browser automation collector"""

    def __init__(self, config):
        super().__init__(config)
        self.rate_limiter = RateLimiter(config["rate_limiting"])
        self.session_manager = SessionManager(config)
        self.max_posts = config["collection"]["max_posts"]
        self.max_commenters = config["collection"]["max_commenters_per_post"]
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

                # Auto-login if credentials are available and not yet authenticated
                if not self.session_manager.is_authenticated():
                    ig_user, ig_pass = _load_env_credentials()
                    if ig_user and ig_pass:
                        logger.info("Credentials found — attempting auto-login before collection")
                        self.session_manager.auto_login(self.page, ig_user, ig_pass)

                # Phase 0: Collect target profile
                phase0_data = self.collect_phase0_profile(self.page)

                # Phase 1: Collect recent posts
                phase1_data = self.collect_phase1_posts(self.page)

                # Phase 2: Collect following list
                phase2_data = self.collect_phase2_following(self.page)

                # Phase 3: Collect first-degree profiles
                phase3_data = self.collect_phase3_first_degree(self.page)

                # Save session for next run
                self.session_manager.save_session(self.context)

                return {
                    "phase0": phase0_data,
                    "phase1": phase1_data,
                    "phase2": phase2_data,
                    "phase3": phase3_data
                }

        finally:
            if self.browser:
                self.browser.close()

    def collect_quick(self):
        """
        Quick collection: Phase 0 (profile) + Phase 1 (posts/commenters) only.
        Skips Phase 2 (following) and Phase 3 (first-degree profile enrichment).
        Use collect() for full collection including Phase 3.
        Returns dict with phase0 and phase1 data only.
        """
        logger.info(f"Starting quick collection (Phase 0+1) for {self.target_account}")

        try:
            with sync_playwright() as p:
                self.browser = p.chromium.launch(headless=False)
                self.context = self.browser.new_context()
                self.page = self.context.new_page()

                # Load saved session if available
                self.session_manager.load_session(self.context)

                # Auto-login if credentials are available and not yet authenticated
                if not self.session_manager.is_authenticated():
                    ig_user, ig_pass = _load_env_credentials()
                    if ig_user and ig_pass:
                        logger.info("Credentials found — attempting auto-login before collection")
                        self.session_manager.auto_login(self.page, ig_user, ig_pass)

                # Phase 0: Collect target profile
                phase0_data = self.collect_phase0_profile(self.page)

                # Phase 1: Collect recent posts and commenters
                phase1_data = self.collect_phase1_posts(self.page)

                # Save session for next run
                self.session_manager.save_session(self.context)

                return {
                    "phase0": phase0_data,
                    "phase1": phase1_data,
                }

        finally:
            if self.browser:
                self.browser.close()

    def collect_phase3_selective(self, page, usernames: list) -> dict:
        """
        Selective Phase 3: fetch profiles only for the given usernames.
        Used by enrich.py to do targeted enrichment after --quick collection.
        Returns same format as collect_phase3_first_degree.
        """
        logger.info(f"Selective Phase 3: fetching {len(usernames)} profiles")

        discovered_accounts = []
        for username in usernames:
            logger.info(f"Collecting profile for {username}")
            profile = self.collect_account_profile(page, username)
            if profile:
                discovered_accounts.append(profile)
            self.rate_limiter.wait()

        metadata = self.create_metadata(
            source="playwright",
            phase="phase3_selective",
            authenticated=self.session_manager.is_authenticated()
        )

        result = {
            "metadata": metadata,
            "discovered_accounts": discovered_accounts,
        }

        self.save_progress("phase3_enriched", result)

        return result

    def collect_phase0_profile(self, page):
        """Phase 0: Collect target account profile data"""
        logger.info(f"Phase 0: Collecting profile for {self.target_account}")

        url = self.build_profile_url(self.target_account)

        try:
            page.goto(url, wait_until="networkidle")
            self.rate_limiter.wait()

            # Check for login wall
            if self.session_manager.detect_login_wall(page):
                if not self.session_manager.is_authenticated():
                    ig_user, ig_pass = _load_env_credentials()
                    if ig_user and ig_pass:
                        self.session_manager.auto_login(page, ig_user, ig_pass)
                    else:
                        self.session_manager.prompt_for_login()
                if not self.session_manager.is_authenticated():
                    logger.warning("Not authenticated, data may be limited")

            # Extract profile data
            profile_data = self.extract_profile_data(page, self.target_account)

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

    def collect_phase1_posts(self, page):
        """Phase 1: Collect recent posts"""
        logger.info("Phase 1: Collecting recent posts")

        try:
            # Navigate back to profile
            url = self.build_profile_url(self.target_account)
            page.goto(url, wait_until="networkidle")
            self.rate_limiter.wait()

            # Scroll and collect post URLs
            post_links = self.scroll_and_collect_posts(page, limit=self.max_posts)
            logger.info(f"Found {len(post_links)} posts to collect")

            # Visit each post and extract data
            posts = []
            for idx, post_url in enumerate(post_links, 1):
                logger.info(f"Extracting post {idx}/{len(post_links)}: {post_url}")
                post_data = self.extract_post_data(page, post_url)
                if post_data:
                    posts.append(post_data)
                self.rate_limiter.wait()

            # Create metadata
            metadata = self.create_metadata(
                source="playwright",
                phase="phase1_posts",
                authenticated=self.session_manager.is_authenticated()
            )

            result = {
                "metadata": metadata,
                "posts": posts
            }

            # Save progress
            self.save_progress("phase1_posts", result)

            return result

        except Exception as e:
            logger.error(f"Error in Phase 1: {e}")
            return None

    def scroll_and_collect_posts(self, page, limit):
        """Scroll and collect post URLs"""
        post_urls = set()
        max_scrolls = 10
        selector = 'a[href*="/p/"]'

        try:
            for scroll_num in range(max_scrolls):
                # Find all post links
                post_links = page.query_selector_all(selector)

                for link in post_links:
                    href = link.get_attribute("href")
                    if href:
                        # Build full URL if relative
                        if href.startswith("/"):
                            href = f"https://www.instagram.com{href}"
                        post_urls.add(href)

                # Check if we have enough
                if len(post_urls) >= limit:
                    break

                # Scroll down
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                page.wait_for_timeout(1000)

            # Return limited list
            return list(post_urls)[:limit]

        except Exception as e:
            logger.error(f"Error scrolling and collecting posts: {e}")
            return list(post_urls)[:limit]

    def extract_post_data(self, page, post_url):
        """Extract data from a single post"""
        try:
            page.goto(post_url, wait_until="networkidle")
            self.rate_limiter.wait()

            post_data = {
                "post_url": post_url,
                "caption": None,
                "mentions": [],
                "timestamp": None,
                "commenters": []
            }

            # Extract caption using multiple selectors
            caption_selectors = [
                'h1',
                '[class*="Caption"]',
                'span[dir="auto"]',
                'article div span'
            ]

            for selector in caption_selectors:
                try:
                    caption_element = page.query_selector(selector)
                    if caption_element:
                        caption_text = caption_element.text_content()
                        if caption_text and len(caption_text) > 10:  # Avoid grabbing UI text
                            post_data["caption"] = caption_text.strip()
                            break
                except:
                    continue

            # Extract mentions from caption
            if post_data["caption"]:
                mention_matches = re.findall(r'@([a-zA-Z0-9._]+)', post_data["caption"])
                post_data["mentions"] = list(set(mention_matches))

            # Extract timestamp
            try:
                time_element = page.query_selector('time[datetime]')
                if time_element:
                    post_data["timestamp"] = time_element.get_attribute("datetime")
            except:
                pass

            # Extract commenters
            commenters = self.extract_commenters(page)
            post_data["commenters"] = commenters[:self.max_commenters]

            logger.info(f"Extracted post data: {len(post_data['commenters'])} commenters, {len(post_data['mentions'])} mentions")
            return post_data

        except Exception as e:
            logger.error(f"Error extracting post data from {post_url}: {e}")
            return None

    # Instagram system/nav paths that appear as hrefs but are not user accounts
    INSTAGRAM_SYSTEM_PATHS = frozenset({
        "accounts", "explore", "legal", "web", "popular", "about", "press",
        "blog", "jobs", "help", "privacy", "terms", "locations", "language",
        "api", "p", "r", "tv", "reels", "stories", "direct", "lite",
        "challenge", "login", "signup", "oauth", "favicon.ico",
    })

    def extract_commenters(self, page):
        """Extract commenter usernames, filtering Instagram nav/system paths."""
        commenter_counts = {}

        try:
            # Find username links in comments
            # Comments typically have links to user profiles
            comment_links = page.query_selector_all('a[href*="/"][role="link"]')

            for link in comment_links:
                href = link.get_attribute("href")
                if href and href.startswith("/") and not "/p/" in href:
                    # Extract username from href like "/username/"
                    username = href.strip("/").split("/")[0]

                    # Skip Instagram system/nav paths
                    if username in self.INSTAGRAM_SYSTEM_PATHS:
                        continue

                    # Skip the target account itself
                    if username == self.target_account:
                        continue

                    # Skip if empty or looks like a path
                    if not username or len(username) < 2:
                        continue

                    # Count appearances
                    if username not in commenter_counts:
                        commenter_counts[username] = 0
                    commenter_counts[username] += 1

            # Convert to list of dicts
            commenters = [
                {
                    "username": username,
                    "comment_count": count,
                    "target_replied": False  # Will be enhanced in later tasks
                }
                for username, count in commenter_counts.items()
            ]

            # Sort by comment count (most active first)
            commenters.sort(key=lambda x: x["comment_count"], reverse=True)

            return commenters

        except Exception as e:
            logger.error(f"Error extracting commenters: {e}")
            return []

    def collect_phase2_following(self, page):
        """Phase 2: Collect following list"""
        logger.info("Phase 2: Collecting following list")

        try:
            # Navigate to following URL
            url = f"https://www.instagram.com/{self.target_account}/following/"
            page.goto(url, wait_until="networkidle")
            self.rate_limiter.wait()

            # Check for login wall
            if self.session_manager.detect_login_wall(page):
                if not self.session_manager.prompt_for_login():
                    logger.warning("User skipped authentication, following list unavailable")
                    return None

            # Scroll and collect usernames
            following_list = self.scroll_and_collect_usernames(page, list_type="following")
            logger.info(f"Collected {len(following_list)} following accounts")

            # Create metadata
            metadata = self.create_metadata(
                source="playwright",
                phase="phase2_following",
                authenticated=self.session_manager.is_authenticated()
            )

            result = {
                "metadata": metadata,
                "following": following_list,
                "status": "complete" if following_list else "failed"
            }

            # Save progress
            self.save_progress("phase2_following", result)

            return result

        except Exception as e:
            logger.error(f"Error in Phase 2: {e}")
            return None

    def scroll_and_collect_usernames(self, page, list_type):
        """Scroll through following modal and collect usernames"""
        usernames = set()
        max_scrolls = 20
        stall_counter = 0
        previous_count = 0

        try:
            for scroll_num in range(max_scrolls):
                # Find all username links in the dialog
                # Following modal uses role="dialog" container
                links = page.query_selector_all('[role="dialog"] a[href^="/"]')

                for link in links:
                    href = link.get_attribute("href")
                    if href and href.startswith("/") and not "/p/" in href:
                        # Extract username from href like "/username/"
                        username = href.strip("/").split("/")[0]

                        # Skip if empty or looks invalid
                        if username and len(username) >= 2:
                            usernames.add(username)

                # Check for stall (no new usernames for 3 scrolls)
                current_count = len(usernames)
                if current_count == previous_count:
                    stall_counter += 1
                    if stall_counter >= 3:
                        logger.info(f"No new usernames for 3 scrolls, stopping at {current_count}")
                        break
                else:
                    stall_counter = 0

                previous_count = current_count

                # Scroll the dialog
                page.evaluate("document.querySelector('[role=dialog]')?.scrollBy(0, 500)")
                page.wait_for_timeout(800)

                logger.debug(f"Scroll {scroll_num + 1}/{max_scrolls}: {current_count} usernames")

            return list(usernames)

        except Exception as e:
            logger.error(f"Error scrolling and collecting usernames: {e}")
            return list(usernames)

    def collect_phase3_first_degree(self, page):
        """Phase 3: Collect first-degree connection profiles"""
        logger.info("Phase 3: Collecting first-degree profiles")

        try:
            # Load Phase 1 checkpoint for mentions and commenters
            phase1_data = self.load_checkpoint("phase1_posts")

            # Load Phase 2 checkpoint for following list
            phase2_data = self.load_checkpoint("phase2_following")

            # Gather all discovered usernames
            discovered_usernames = set()

            # From Phase 1 mentions
            if phase1_data and "posts" in phase1_data:
                for post in phase1_data["posts"]:
                    if "mentions" in post:
                        discovered_usernames.update(post["mentions"])

            # From Phase 1 commenters
            if phase1_data and "posts" in phase1_data:
                for post in phase1_data["posts"]:
                    if "commenters" in post:
                        for commenter in post["commenters"]:
                            discovered_usernames.add(commenter["username"])

            # From Phase 2 following list
            if phase2_data and "following" in phase2_data:
                discovered_usernames.update(phase2_data["following"])

            logger.info(f"Found {len(discovered_usernames)} unique first-degree accounts")

            # Collect profile for each account
            discovered_accounts = []
            for username in discovered_usernames:
                logger.info(f"Collecting profile for {username}")
                profile = self.collect_account_profile(page, username)
                if profile:
                    discovered_accounts.append(profile)
                self.rate_limiter.wait()

            # Create metadata
            metadata = self.create_metadata(
                source="playwright",
                phase="phase3_first_degree",
                authenticated=self.session_manager.is_authenticated()
            )

            result = {
                "metadata": metadata,
                "discovered_accounts": discovered_accounts
            }

            # Save progress
            self.save_progress("phase3_first_degree", result)

            return result

        except Exception as e:
            logger.error(f"Error in Phase 3: {e}")
            return None

    def collect_account_profile(self, page, username):
        """Collect profile for a single account"""
        try:
            # Navigate to profile
            url = self.build_profile_url(username)
            page.goto(url, wait_until="networkidle")
            self.rate_limiter.wait()

            # Extract profile data (reuse from Phase 0)
            profile_data = self.extract_profile_data(page, username)

            # Add source metadata
            profile_data["source"] = "first_degree"
            profile_data["first_seen"] = self.create_metadata(
                source="playwright",
                phase="phase3_first_degree",
                authenticated=self.session_manager.is_authenticated()
            )["timestamp"]

            return profile_data

        except Exception as e:
            logger.error(f"Error collecting profile for {username}: {e}")
            return None
