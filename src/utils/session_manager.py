import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages browser session and authentication state"""

    def __init__(self, config):
        self.session_file = config["authentication"]["session_cookie_file"]
        self.authenticated = False

    def save_session(self, context):
        """Save browser context cookies"""
        try:
            cookies = context.cookies()
            Path(self.session_file).parent.mkdir(parents=True, exist_ok=True)
            with open(self.session_file, 'w') as f:
                json.dump(cookies, f, indent=2)
            logger.info(f"Session saved to {self.session_file}")
        except Exception as e:
            logger.error(f"Failed to save session: {e}")

    def load_session(self, context):
        """Load saved cookies into browser context"""
        if not os.path.exists(self.session_file):
            logger.info("No saved session found")
            return False

        try:
            with open(self.session_file, 'r') as f:
                cookies = json.load(f)
            context.add_cookies(cookies)
            logger.info(f"Session loaded from {self.session_file}")
            self.authenticated = True
            return True
        except Exception as e:
            logger.error(f"Failed to load session: {e}")
            return False

    def is_authenticated(self):
        """Check if session is authenticated"""
        return self.authenticated

    def set_authenticated(self, value):
        """Set authentication state"""
        self.authenticated = value
        logger.info(f"Authentication state set to {value}")

    def detect_login_wall(self, page):
        """Detect if page requires login"""
        login_indicators = [
            "Log in to see",
            "Log in to continue",
            "Login • Instagram",
            "Sign up"
        ]

        content = page.content()
        for indicator in login_indicators:
            if indicator in content:
                logger.warning(f"Login wall detected: {indicator}")
                return True

        return False

    def prompt_for_login(self):
        """Prompt user to log in manually"""
        print("\n" + "="*60)
        print("LOGIN REQUIRED")
        print("="*60)
        print("Instagram requires login to access this data.")
        print("Please log in manually in the browser window, then press Enter.")
        print("\nOptions:")
        print("  1. Log in and press Enter to continue")
        print("  2. Press Ctrl+C to skip and continue with limited data")
        print("="*60)

        try:
            input()
            self.set_authenticated(True)
            return True
        except KeyboardInterrupt:
            print("\nSkipping authentication, continuing with limited data...")
            return False

    def auto_login(self, page, username: str, password: str) -> bool:
        """Automated login using credentials. Returns True on success."""
        try:
            logger.info("Attempting automated login...")
            page.goto("https://www.instagram.com/accounts/login/", wait_until="networkidle", timeout=30000)
            page.wait_for_timeout(2000)

            # Fill username
            username_field = page.wait_for_selector('input[name="username"]', timeout=10000)
            username_field.click()
            username_field.fill(username)
            page.wait_for_timeout(800)

            # Fill password
            password_field = page.wait_for_selector('input[name="password"]', timeout=10000)
            password_field.click()
            password_field.fill(password)
            page.wait_for_timeout(800)

            # Submit
            page.keyboard.press("Enter")
            logger.info("Submitted login form, waiting for response...")
            page.wait_for_timeout(5000)

            # Dismiss "Save your login info?" prompt if present
            try:
                not_now = page.query_selector('button:has-text("Not now"), div[role="button"]:has-text("Not now")')
                if not_now:
                    not_now.click()
                    page.wait_for_timeout(2000)
            except Exception:
                pass

            # Dismiss "Turn on Notifications?" prompt if present
            try:
                not_now2 = page.query_selector('button:has-text("Not Now")')
                if not_now2:
                    not_now2.click()
                    page.wait_for_timeout(2000)
            except Exception:
                pass

            # Check if login succeeded by looking for home feed indicators
            page.wait_for_timeout(3000)
            content = page.content()
            if "Log in" in page.title() or "login" in page.url:
                logger.error("Auto-login failed — still on login page")
                return False

            self.set_authenticated(True)
            logger.info("Auto-login successful")
            return True

        except Exception as e:
            logger.error(f"Auto-login error: {e}")
            return False
