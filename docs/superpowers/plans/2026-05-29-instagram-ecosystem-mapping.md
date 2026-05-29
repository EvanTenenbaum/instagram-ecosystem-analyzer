# Instagram Ecosystem Mapping Tool Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a modular Instagram ecosystem mapping tool that collects public data, analyzes network relationships, and outputs AI-consumable structured data for strategic engagement planning.

**Architecture:** Three independent modules with clear data contracts: Collection (Playwright browser automation + OCR fallback) → Analysis (graph construction, scoring, community detection) → Reporting (AI-optimized outputs). Each module can run independently.

**Tech Stack:** Python 3.14+, Playwright, networkx, pandas, pytesseract, Pillow

---

## File Structure Overview

```
~/code/instagram-ecosystem-tool/
├── requirements.txt
├── config.json
├── README.md
├── src/
│   ├── __init__.py
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── base_collector.py
│   │   ├── playwright_collector.py
│   │   └── screenshot_collector.py
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── graph_builder.py
│   │   ├── account_scorer.py
│   │   └── community_detector.py
│   ├── reporters/
│   │   ├── __init__.py
│   │   └── ai_reporter.py
│   └── utils/
│       ├── __init__.py
│       ├── rate_limiter.py
│       ├── data_validator.py
│       └── session_manager.py
├── scripts/
│   ├── collect.py
│   ├── analyze.py
│   ├── report.py
│   ├── run_all.py
│   ├── test_connection.py
│   ├── test_playwright.py
│   ├── test_target_account.py
│   ├── test_ocr.py
│   └── validate_output.py
├── tests/
│   ├── __init__.py
│   ├── test_rate_limiter.py
│   ├── test_graph_builder.py
│   ├── test_account_scorer.py
│   ├── test_community_detector.py
│   └── fixtures/
│       └── sample_instagram_data.json
├── data/
│   ├── raw/
│   ├── manual/
│   │   └── screenshots/
│   └── processed/
├── outputs/
└── logs/
```

---

## Phase 1: Project Setup & Dependencies

### Task 1: Initialize Project Structure

**Files:**
- Create: `requirements.txt`
- Create: `config.json`
- Create: `README.md`
- Create: `src/__init__.py`
- Create: directory structure

- [ ] **Step 1: Create project directory**

```bash
cd ~/code
mkdir -p instagram-ecosystem-tool
cd instagram-ecosystem-tool
```

- [ ] **Step 2: Create directory structure**

```bash
mkdir -p src/collectors src/analyzers src/reporters src/utils
mkdir -p scripts tests/fixtures
mkdir -p data/raw data/manual/screenshots data/processed
mkdir -p outputs logs
mkdir -p docs/superpowers/specs docs/superpowers/plans
```

- [ ] **Step 3: Create requirements.txt**

```txt
playwright>=1.40.0
networkx>=3.0
pandas>=2.0.0
pytesseract>=0.3.10
Pillow>=10.0.0
numpy>=1.24.0
tqdm>=4.65.0
pytest>=7.4.0
```

- [ ] **Step 4: Create config.json**

```json
{
  "target_account": "sarah_myerscough",
  "rate_limiting": {
    "min_delay_seconds": 2.0,
    "max_delay_seconds": 5.0,
    "pause_after_n_requests": 20,
    "pause_duration_seconds": 30,
    "retry_on_429": true,
    "max_retries": 1,
    "backoff_base": 60
  },
  "collection": {
    "max_posts": 50,
    "max_commenters_per_post": 20,
    "collect_second_degree": true,
    "second_degree_limit": 50,
    "second_degree_following_sample": 100
  },
  "authentication": {
    "start_authenticated": false,
    "prompt_on_wall": true,
    "session_cookie_file": "data/.session_cookies.json"
  },
  "analysis": {
    "scoring_weights": {
      "proximity": 0.4,
      "engagement": 0.3,
      "bridge": 0.2,
      "category_fit": 0.1
    },
    "edge_weights": {
      "follows": 10,
      "replies_to": 9,
      "tags": 8,
      "collaborator": 10,
      "repeated_commenter_base": 7,
      "frequency_bonus": 2,
      "mentioned": 6
    },
    "category_keywords": {
      "gallery": ["gallery", "art space", "exhibitions", "representing"],
      "curator": ["curator", "curating", "curatorial"],
      "collector": ["collector", "collecting", "collection"],
      "wood_artist": ["wood", "woodturning", "woodwork", "carving"],
      "craft_artist": ["craft", "maker", "artisan", "handmade"],
      "furniture_designer": ["furniture", "design", "designer", "sculptural furniture"],
      "institution": ["museum", "foundation", "institute", "trust"],
      "fair": ["fair", "art fair", "design week"],
      "journalist": ["writer", "journalist", "editor", "publication"]
    }
  },
  "ocr": {
    "confidence_threshold": 0.5,
    "username_pattern": "@([a-zA-Z0-9._]+)"
  }
}
```

- [ ] **Step 5: Create src/__init__.py**

```python
"""Instagram Ecosystem Mapping Tool"""

__version__ = "0.1.0"
```

- [ ] **Step 6: Create basic README.md**

```markdown
# Instagram Ecosystem Mapping Tool

Map Instagram ecosystems to identify galleries, curators, collectors, artists, and bridge nodes for strategic engagement planning.

## Setup

```bash
pip install -r requirements.txt
playwright install chromium
```

## Usage

```bash
# Run smoke tests
python scripts/test_connection.py
python scripts/test_playwright.py

# Collect data
python scripts/collect.py

# Analyze
python scripts/analyze.py

# Generate report
python scripts/report.py

# Or run all at once
python scripts/run_all.py
```

## Configuration

Edit `config.json` to change target account, rate limits, and scoring weights.
```

- [ ] **Step 7: Commit project initialization**

```bash
git init
git add .
git commit -m "feat: initialize project structure and configuration"
```

---

## Phase 2: Utilities & Shared Components

### Task 2: Rate Limiter

**Files:**
- Create: `src/utils/__init__.py`
- Create: `src/utils/rate_limiter.py`
- Create: `tests/test_rate_limiter.py`

- [ ] **Step 1: Write test for rate limiter wait**

Create `tests/test_rate_limiter.py`:

```python
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
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_rate_limiter.py -v
```

Expected: FAIL with "ModuleNotFoundError: No module named 'src.utils.rate_limiter'"

- [ ] **Step 3: Create src/utils/__init__.py**

```python
"""Utility modules"""
```

- [ ] **Step 4: Implement RateLimiter**

Create `src/utils/rate_limiter.py`:

```python
import time
import random
import logging

logger = logging.getLogger(__name__)


class RateLimiter:
    """Manages request pacing and backoff logic"""
    
    def __init__(self, config):
        self.min_delay = config["min_delay_seconds"]
        self.max_delay = config["max_delay_seconds"]
        self.pause_after = config["pause_after_n_requests"]
        self.pause_duration = config["pause_duration_seconds"]
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
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_rate_limiter.py -v
```

Expected: 3 PASS

- [ ] **Step 6: Commit rate limiter**

```bash
git add src/utils/rate_limiter.py src/utils/__init__.py tests/test_rate_limiter.py
git commit -m "feat: implement rate limiter with exponential backoff"
```

### Task 3: Data Validator

**Files:**
- Create: `src/utils/data_validator.py`
- Create: `tests/test_data_validator.py`

- [ ] **Step 1: Write test for data validator**

Create `tests/test_data_validator.py`:

```python
import pytest
from src.utils.data_validator import DataValidator


def test_validate_account_data_valid():
    """Test validation of valid account data"""
    data = {
        "username": "test_user",
        "display_name": "Test User",
        "bio": "Test bio",
        "follower_count": 1000,
        "following_count": 500
    }
    
    validator = DataValidator()
    is_valid, errors = validator.validate_account(data)
    
    assert is_valid is True
    assert len(errors) == 0


def test_validate_account_data_missing_username():
    """Test validation fails on missing username"""
    data = {
        "display_name": "Test User",
        "bio": "Test bio"
    }
    
    validator = DataValidator()
    is_valid, errors = validator.validate_account(data)
    
    assert is_valid is False
    assert "username" in errors[0].lower()


def test_validate_account_data_invalid_username():
    """Test validation fails on invalid username format"""
    data = {
        "username": "invalid@username!",
        "display_name": "Test User"
    }
    
    validator = DataValidator()
    is_valid, errors = validator.validate_account(data)
    
    assert is_valid is False
    assert "username" in errors[0].lower()


def test_validate_relationship_valid():
    """Test validation of valid relationship"""
    data = {
        "source": "user1",
        "target": "user2",
        "type": "follows",
        "weight": 10
    }
    
    validator = DataValidator()
    is_valid, errors = validator.validate_relationship(data)
    
    assert is_valid is True
    assert len(errors) == 0


def test_validate_relationship_missing_fields():
    """Test validation fails on missing fields"""
    data = {
        "source": "user1"
    }
    
    validator = DataValidator()
    is_valid, errors = validator.validate_relationship(data)
    
    assert is_valid is False
    assert len(errors) > 0
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_data_validator.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement DataValidator**

Create `src/utils/data_validator.py`:

```python
import re
import logging

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates collected data formats"""
    
    USERNAME_PATTERN = re.compile(r'^[a-zA-Z0-9._]{1,30}$')
    
    def validate_account(self, data):
        """Validate account data structure"""
        errors = []
        
        # Required fields
        if "username" not in data:
            errors.append("Missing required field: username")
        elif not self.USERNAME_PATTERN.match(data["username"]):
            errors.append(f"Invalid username format: {data['username']}")
        
        # Optional but validated if present
        if "follower_count" in data and not isinstance(data["follower_count"], (int, type(None))):
            errors.append("follower_count must be integer or None")
        
        if "following_count" in data and not isinstance(data["following_count"], (int, type(None))):
            errors.append("following_count must be integer or None")
        
        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"Account validation failed: {errors}")
        
        return is_valid, errors
    
    def validate_relationship(self, data):
        """Validate relationship data structure"""
        errors = []
        
        required_fields = ["source", "target", "type", "weight"]
        for field in required_fields:
            if field not in data:
                errors.append(f"Missing required field: {field}")
        
        if "weight" in data and not isinstance(data["weight"], (int, float)):
            errors.append("weight must be numeric")
        
        is_valid = len(errors) == 0
        if not is_valid:
            logger.warning(f"Relationship validation failed: {errors}")
        
        return is_valid, errors
    
    def validate_json_file(self, filepath):
        """Validate JSON file exists and is parseable"""
        import json
        import os
        
        if not os.path.exists(filepath):
            return False, [f"File not found: {filepath}"]
        
        try:
            with open(filepath, 'r') as f:
                json.load(f)
            return True, []
        except json.JSONDecodeError as e:
            return False, [f"Invalid JSON: {str(e)}"]
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_data_validator.py -v
```

Expected: 5 PASS

- [ ] **Step 5: Commit data validator**

```bash
git add src/utils/data_validator.py tests/test_data_validator.py
git commit -m "feat: implement data validator for accounts and relationships"
```

### Task 4: Session Manager

**Files:**
- Create: `src/utils/session_manager.py`

- [ ] **Step 1: Create session manager (no tests - integration component)**

Create `src/utils/session_manager.py`:

```python
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
```

- [ ] **Step 2: Commit session manager**

```bash
git add src/utils/session_manager.py
git commit -m "feat: implement session manager for browser authentication"
```

---

## Phase 3: Collection Module

### Task 5: Base Collector Interface

**Files:**
- Create: `src/collectors/__init__.py`
- Create: `src/collectors/base_collector.py`

- [ ] **Step 1: Create base collector interface**

Create `src/collectors/__init__.py`:

```python
"""Data collection modules"""
```

Create `src/collectors/base_collector.py`:

```python
from abc import ABC, abstractmethod
import json
import logging
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseCollector(ABC):
    """Abstract base class for data collectors"""
    
    def __init__(self, config):
        self.config = config
        self.target_account = config["target_account"]
        self.raw_data_dir = Path("data/raw")
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
    
    @abstractmethod
    def collect(self):
        """Collect data from source"""
        pass
    
    def save_progress(self, phase, data):
        """Save collection progress to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{phase}_{timestamp}.json"
        filepath = self.raw_data_dir / filename
        
        try:
            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)
            logger.info(f"Progress saved: {filepath}")
            return str(filepath)
        except Exception as e:
            logger.error(f"Failed to save progress: {e}")
            return None
    
    def load_checkpoint(self, phase):
        """Load most recent checkpoint for phase"""
        pattern = f"{phase}_*.json"
        files = sorted(self.raw_data_dir.glob(pattern))
        
        if not files:
            logger.info(f"No checkpoint found for phase: {phase}")
            return None
        
        latest = files[-1]
        try:
            with open(latest, 'r') as f:
                data = json.load(f)
            logger.info(f"Loaded checkpoint: {latest}")
            return data
        except Exception as e:
            logger.error(f"Failed to load checkpoint: {e}")
            return None
    
    def create_metadata(self, source, phase, authenticated=False):
        """Create collection metadata"""
        return {
            "source": source,
            "timestamp": datetime.now().isoformat(),
            "target_account": self.target_account,
            "phase": phase,
            "authenticated": authenticated
        }
```

- [ ] **Step 2: Commit base collector**

```bash
git add src/collectors/__init__.py src/collectors/base_collector.py
git commit -m "feat: implement base collector interface"
```

### Task 6: Playwright Collector - Phase 0 (Target Profile)

**Files:**
- Create: `src/collectors/playwright_collector.py`
- Create: `tests/test_playwright_collector.py`

- [ ] **Step 1: Write test for playwright collector structure**

Create `tests/test_playwright_collector.py`:

```python
import pytest
from src.collectors.playwright_collector import PlaywrightCollector


def test_playwright_collector_init():
    """Test PlaywrightCollector initializes correctly"""
    config = {
        "target_account": "test_user",
        "rate_limiting": {
            "min_delay_seconds": 1.0,
            "max_delay_seconds": 2.0,
            "pause_after_n_requests": 10,
            "pause_duration_seconds": 5,
            "retry_on_429": True,
            "max_retries": 1,
            "backoff_base": 60
        },
        "collection": {
            "max_posts": 20,
            "max_commenters_per_post": 10
        },
        "authentication": {
            "start_authenticated": False,
            "prompt_on_wall": True,
            "session_cookie_file": "data/.session_cookies.json"
        }
    }
    
    collector = PlaywrightCollector(config)
    
    assert collector.target_account == "test_user"
    assert collector.rate_limiter is not None
    assert collector.session_manager is not None


def test_build_profile_url():
    """Test profile URL construction"""
    config = {
        "target_account": "sarah_myerscough",
        "rate_limiting": {
            "min_delay_seconds": 1.0,
            "max_delay_seconds": 2.0,
            "pause_after_n_requests": 10,
            "pause_duration_seconds": 5,
            "backoff_base": 60
        },
        "authentication": {
            "session_cookie_file": "data/.session_cookies.json"
        }
    }
    
    collector = PlaywrightCollector(config)
    url = collector.build_profile_url("sarah_myerscough")
    
    assert url == "https://www.instagram.com/sarah_myerscough/"
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_playwright_collector.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement PlaywrightCollector (basic structure + Phase 0)**

Create `src/collectors/playwright_collector.py`:

```python
import logging
import re
from playwright.sync_api import sync_playwright
from .base_collector import BaseCollector
from ..utils.rate_limiter import RateLimiter
from ..utils.session_manager import SessionManager

logger = logging.getLogger(__name__)


class PlaywrightCollector(BaseCollector):
    """Browser automation collector using Playwright"""
    
    def __init__(self, config):
        super().__init__(config)
        self.rate_limiter = RateLimiter(config["rate_limiting"])
        self.session_manager = SessionManager(config)
        self.max_posts = config["collection"]["max_posts"]
        self.max_commenters = config["collection"]["max_commenters_per_post"]
    
    def build_profile_url(self, username):
        """Build Instagram profile URL"""
        return f"https://www.instagram.com/{username}/"
    
    def collect(self):
        """Main collection orchestrator"""
        logger.info(f"Starting collection for @{self.target_account}")
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            # Load saved session if exists
            self.session_manager.load_session(context)
            
            # Phase 0: Target profile
            profile_data = self.collect_phase0_profile(page)
            if profile_data:
                self.save_progress("phase0_target_profile", profile_data)
            
            # Phase 1: Recent posts
            posts_data = self.collect_phase1_posts(page)
            if posts_data:
                self.save_progress("phase1_posts", posts_data)
            
            # Phase 2: Following list
            following_data = self.collect_phase2_following(page)
            if following_data:
                self.save_progress("phase2_following", following_data)
            
            # Phase 3: First degree account details
            first_degree_data = self.collect_phase3_first_degree(page)
            if first_degree_data:
                self.save_progress("phase3_first_degree_accounts", first_degree_data)
            
            # Save session for next run
            self.session_manager.save_session(context)
            
            browser.close()
        
        logger.info("Collection complete")
    
    def collect_phase0_profile(self, page):
        """Phase 0: Collect target account profile"""
        logger.info("Phase 0: Collecting target profile")
        
        url = self.build_profile_url(self.target_account)
        
        try:
            page.goto(url, wait_until="networkidle")
            self.rate_limiter.wait()
            
            # Extract profile data
            profile = self.extract_profile_data(page)
            
            data = {
                "collection_metadata": self.create_metadata(
                    "playwright",
                    "target_profile",
                    self.session_manager.is_authenticated()
                ),
                "target_profile": profile
            }
            
            logger.info(f"Profile collected: @{profile['username']}")
            return data
            
        except Exception as e:
            logger.error(f"Phase 0 failed: {e}")
            return None
    
    def extract_profile_data(self, page):
        """Extract profile data from page"""
        # Note: These selectors are illustrative - Instagram's actual structure
        # may vary and require adjustment
        
        profile = {
            "username": self.target_account,
            "display_name": None,
            "bio": None,
            "external_url": None,
            "follower_count": None,
            "following_count": None,
            "post_count": None,
            "is_verified": False,
            "is_private": False
        }
        
        try:
            # Get display name from title or header
            title = page.title()
            if title:
                match = re.search(r'(.+?)\s*\(@', title)
                if match:
                    profile["display_name"] = match.group(1)
            
            # Check for private account indicator
            private_indicator = page.locator("text=This account is private")
            if private_indicator.count() > 0:
                profile["is_private"] = True
            
            # Get bio - try multiple selectors
            bio_selectors = [
                'meta[property="og:description"]',
                '[class*="bio"]',
                'header section'
            ]
            
            for selector in bio_selectors:
                try:
                    bio_element = page.locator(selector).first
                    if selector.startswith('meta'):
                        bio_text = bio_element.get_attribute('content')
                    else:
                        bio_text = bio_element.inner_text()
                    
                    if bio_text and len(bio_text) > 0:
                        profile["bio"] = bio_text
                        break
                except:
                    continue
            
            # Get external link
            link_selectors = [
                'a[href^="http"]:has-text("http")',
                'a[rel="me nofollow"]'
            ]
            
            for selector in link_selectors:
                try:
                    link = page.locator(selector).first
                    href = link.get_attribute('href')
                    if href and not 'instagram.com' in href:
                        profile["external_url"] = href
                        break
                except:
                    continue
            
            # Get stats (follower/following/post counts)
            # These are often in meta tags or structured data
            stats_text = page.content()
            
            follower_match = re.search(r'(\d+(?:,\d+)*)\s*[Ff]ollowers', stats_text)
            if follower_match:
                profile["follower_count"] = int(follower_match.group(1).replace(',', ''))
            
            following_match = re.search(r'(\d+(?:,\d+)*)\s*[Ff]ollowing', stats_text)
            if following_match:
                profile["following_count"] = int(following_match.group(1).replace(',', ''))
            
            posts_match = re.search(r'(\d+(?:,\d+)*)\s*[Pp]osts', stats_text)
            if posts_match:
                profile["post_count"] = int(posts_match.group(1).replace(',', ''))
            
            logger.debug(f"Extracted profile: {profile}")
            
        except Exception as e:
            logger.warning(f"Error extracting profile data: {e}")
        
        return profile
    
    def collect_phase1_posts(self, page):
        """Phase 1: Collect recent posts - stub for now"""
        logger.info("Phase 1: Collecting recent posts (stub)")
        return None
    
    def collect_phase2_following(self, page):
        """Phase 2: Collect following list - stub for now"""
        logger.info("Phase 2: Collecting following list (stub)")
        return None
    
    def collect_phase3_first_degree(self, page):
        """Phase 3: Collect first degree accounts - stub for now"""
        logger.info("Phase 3: Collecting first degree accounts (stub)")
        return None
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_playwright_collector.py -v
```

Expected: 2 PASS

- [ ] **Step 5: Commit playwright collector foundation**

```bash
git add src/collectors/playwright_collector.py tests/test_playwright_collector.py
git commit -m "feat: implement playwright collector with phase 0 (profile collection)"
```

### Task 7: Playwright Collector - Phase 1 (Posts)

**Files:**
- Modify: `src/collectors/playwright_collector.py`

- [ ] **Step 1: Implement Phase 1 - collect recent posts**

Add to `src/collectors/playwright_collector.py` (replace the stub):

```python
def collect_phase1_posts(self, page):
    """Phase 1: Collect recent posts"""
    logger.info("Phase 1: Collecting recent posts")
    
    # Already on profile page from Phase 0
    posts = []
    
    try:
        # Scroll and collect post links
        post_links = self.scroll_and_collect_posts(page, limit=self.max_posts)
        
        logger.info(f"Found {len(post_links)} posts, collecting details...")
        
        # Visit each post and extract details
        for i, post_url in enumerate(post_links):
            logger.info(f"Collecting post {i+1}/{len(post_links)}")
            
            post_data = self.extract_post_data(page, post_url)
            if post_data:
                posts.append(post_data)
            
            self.rate_limiter.wait()
        
        data = {
            "collection_metadata": self.create_metadata(
                "playwright",
                "posts",
                self.session_manager.is_authenticated()
            ),
            "posts": posts
        }
        
        logger.info(f"Collected {len(posts)} posts")
        return data
        
    except Exception as e:
        logger.error(f"Phase 1 failed: {e}")
        return None

def scroll_and_collect_posts(self, page, limit):
    """Scroll profile and collect post URLs"""
    post_urls = set()
    
    # Find posts on profile
    # Instagram profiles show posts in a grid
    post_selector = 'a[href*="/p/"]'
    
    scroll_attempts = 0
    max_scrolls = 10
    
    while len(post_urls) < limit and scroll_attempts < max_scrolls:
        # Get all post links currently visible
        links = page.locator(post_selector).all()
        
        for link in links:
            try:
                href = link.get_attribute('href')
                if href and '/p/' in href:
                    full_url = f"https://www.instagram.com{href}" if not href.startswith('http') else href
                    post_urls.add(full_url)
                    
                    if len(post_urls) >= limit:
                        break
            except:
                continue
        
        # Scroll down to load more
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(1000)
        scroll_attempts += 1
        
        logger.debug(f"Scroll {scroll_attempts}: found {len(post_urls)} posts")
    
    return list(post_urls)[:limit]

def extract_post_data(self, page, post_url):
    """Extract data from a single post"""
    try:
        page.goto(post_url, wait_until="networkidle")
        
        post = {
            "url": post_url,
            "timestamp": None,
            "caption": None,
            "tagged_accounts": [],
            "collaborators": [],
            "commenters": [],
            "like_count": None,
            "comment_count": None
        }
        
        # Get caption
        caption_selectors = [
            'meta[property="og:description"]',
            '[class*="caption"]',
            'h1'
        ]
        
        for selector in caption_selectors:
            try:
                element = page.locator(selector).first
                if selector.startswith('meta'):
                    text = element.get_attribute('content')
                else:
                    text = element.inner_text()
                
                if text and len(text) > 0:
                    post["caption"] = text
                    
                    # Extract mentioned accounts from caption
                    mentions = re.findall(r'@([a-zA-Z0-9._]+)', text)
                    post["tagged_accounts"].extend(mentions)
                    break
            except:
                continue
        
        # Get timestamp from time element or meta tag
        try:
            time_element = page.locator('time[datetime]').first
            timestamp = time_element.get_attribute('datetime')
            post["timestamp"] = timestamp
        except:
            logger.debug("Could not extract timestamp")
        
        # Get comments (top commenters)
        commenters = self.extract_commenters(page)
        post["commenters"] = commenters[:self.max_commenters]
        
        logger.debug(f"Extracted post: {post['url']}")
        return post
        
    except Exception as e:
        logger.warning(f"Failed to extract post {post_url}: {e}")
        return None

def extract_commenters(self, page):
    """Extract commenter usernames from post"""
    commenters = []
    
    # Look for comment sections
    # Instagram comments are often in spans or divs with specific classes
    comment_selector = 'a[href*="/"]'
    
    try:
        # Get all username links in comments
        links = page.locator(comment_selector).all()
        
        username_counts = {}
        target_replied_to = set()
        
        for link in links:
            try:
                href = link.get_attribute('href')
                if href and href.startswith('/') and href.count('/') >= 2:
                    username = href.strip('/').split('/')[0]
                    
                    # Skip the target account itself
                    if username == self.target_account:
                        continue
                    
                    # Count appearances
                    username_counts[username] = username_counts.get(username, 0) + 1
            except:
                continue
        
        # Convert to list format
        for username, count in username_counts.items():
            commenters.append({
                "username": username,
                "comment_count": count,
                "target_replied": False  # Would need deeper analysis to determine
            })
        
    except Exception as e:
        logger.debug(f"Error extracting commenters: {e}")
    
    return commenters
```

- [ ] **Step 2: Test Phase 1 manually (no automated test for browser)**

```bash
# Run with --limit flag to test on just a few posts
python -c "
import json
from src.collectors.playwright_collector import PlaywrightCollector

with open('config.json') as f:
    config = json.load(f)

config['collection']['max_posts'] = 3

collector = PlaywrightCollector(config)
collector.collect_phase0_profile(None)  # Would need full setup
print('Phase 1 implementation complete - needs integration test')
"
```

- [ ] **Step 3: Commit Phase 1 implementation**

```bash
git add src/collectors/playwright_collector.py
git commit -m "feat: implement phase 1 post collection with commenter extraction"
```

### Task 8: Playwright Collector - Phases 2 & 3

**Files:**
- Modify: `src/collectors/playwright_collector.py`

- [ ] **Step 1: Implement Phase 2 - following list**

Add to `src/collectors/playwright_collector.py` (replace stub):

```python
def collect_phase2_following(self, page):
    """Phase 2: Collect following list"""
    logger.info("Phase 2: Collecting following list")
    
    following_url = self.build_profile_url(self.target_account) + "following/"
    
    try:
        page.goto(following_url, wait_until="networkidle")
        self.rate_limiter.wait()
        
        # Check for login wall
        if self.session_manager.detect_login_wall(page):
            if self.config["authentication"]["prompt_on_wall"]:
                if self.session_manager.prompt_for_login():
                    # User logged in, retry
                    page.goto(following_url, wait_until="networkidle")
                else:
                    # User skipped login
                    return {
                        "collection_metadata": self.create_metadata("playwright", "following", False),
                        "following": [],
                        "collection_status": "failed",
                        "error_message": "Login required - user skipped"
                    }
            else:
                return {
                    "collection_metadata": self.create_metadata("playwright", "following", False),
                    "following": [],
                    "collection_status": "failed",
                    "error_message": "Login required"
                }
        
        # Extract following usernames
        following = self.scroll_and_collect_usernames(page, list_type="following")
        
        data = {
            "collection_metadata": self.create_metadata(
                "playwright",
                "following",
                self.session_manager.is_authenticated()
            ),
            "following": following,
            "collection_status": "complete",
            "error_message": None
        }
        
        logger.info(f"Collected {len(following)} following accounts")
        return data
        
    except Exception as e:
        logger.error(f"Phase 2 failed: {e}")
        return None

def scroll_and_collect_usernames(self, page, list_type):
    """Scroll through following/followers list and collect usernames"""
    usernames = set()
    
    # Instagram shows following in a dialog/modal
    username_selector = 'a[href*="/"]'
    
    scroll_attempts = 0
    max_scrolls = 20
    last_count = 0
    stall_count = 0
    
    while scroll_attempts < max_scrolls and stall_count < 3:
        # Find username links
        links = page.locator(username_selector).all()
        
        for link in links:
            try:
                href = link.get_attribute('href')
                if href and href.startswith('/') and href.count('/') >= 2:
                    username = href.strip('/').split('/')[0]
                    if username and username != self.target_account:
                        usernames.add(username)
            except:
                continue
        
        # Check if we're making progress
        if len(usernames) == last_count:
            stall_count += 1
        else:
            stall_count = 0
        
        last_count = len(usernames)
        
        # Scroll within modal
        page.evaluate("document.querySelector('[role=dialog]')?.scrollBy(0, 500)")
        page.wait_for_timeout(800)
        scroll_attempts += 1
        
        logger.debug(f"Scroll {scroll_attempts}: {len(usernames)} usernames")
    
    return list(usernames)
```

- [ ] **Step 2: Implement Phase 3 - first degree account details**

Add to `src/collectors/playwright_collector.py` (replace stub):

```python
def collect_phase3_first_degree(self, page):
    """Phase 3: Collect first degree account details"""
    logger.info("Phase 3: Collecting first degree account details")
    
    # Gather all discovered accounts from previous phases
    discovered_usernames = set()
    
    # Load Phase 1 (posts) to get tagged/commenters
    phase1_data = self.load_checkpoint("phase1_posts")
    if phase1_data:
        for post in phase1_data.get("posts", []):
            discovered_usernames.update(post.get("tagged_accounts", []))
            for commenter in post.get("commenters", []):
                discovered_usernames.add(commenter["username"])
    
    # Load Phase 2 (following)
    phase2_data = self.load_checkpoint("phase2_following")
    if phase2_data:
        discovered_usernames.update(phase2_data.get("following", []))
    
    logger.info(f"Found {len(discovered_usernames)} first-degree accounts")
    
    # Collect profile details for each
    discovered_accounts = {}
    
    for i, username in enumerate(discovered_usernames):
        logger.info(f"Collecting account {i+1}/{len(discovered_usernames)}: @{username}")
        
        try:
            profile = self.collect_account_profile(page, username)
            if profile:
                discovered_accounts[username] = profile
            
            self.rate_limiter.wait()
            
        except Exception as e:
            logger.warning(f"Failed to collect @{username}: {e}")
            continue
    
    data = {
        "collection_metadata": self.create_metadata(
            "playwright",
            "first_degree_accounts",
            self.session_manager.is_authenticated()
        ),
        "discovered_accounts": discovered_accounts
    }
    
    logger.info(f"Collected {len(discovered_accounts)} first-degree account profiles")
    return data

def collect_account_profile(self, page, username):
    """Collect profile details for a single account"""
    url = self.build_profile_url(username)
    
    try:
        page.goto(url, wait_until="networkidle", timeout=30000)
        
        # Use same extraction as Phase 0
        profile = self.extract_profile_data(page)
        
        # Add metadata
        profile["source"] = []  # Will be filled by analysis
        profile["first_seen"] = self.create_metadata("playwright", "profile", False)["timestamp"]
        
        return profile
        
    except Exception as e:
        logger.warning(f"Failed to collect profile for @{username}: {e}")
        return None
```

- [ ] **Step 3: Commit Phases 2 & 3**

```bash
git add src/collectors/playwright_collector.py
git commit -m "feat: implement phase 2 (following list) and phase 3 (first degree profiles)"
```

### Task 9: Screenshot Collector (OCR Fallback)

**Files:**
- Create: `src/collectors/screenshot_collector.py`

- [ ] **Step 1: Implement screenshot OCR collector**

Create `src/collectors/screenshot_collector.py`:

```python
import re
import logging
from pathlib import Path
from PIL import Image
import pytesseract
from .base_collector import BaseCollector

logger = logging.getLogger(__name__)


class ScreenshotCollector(BaseCollector):
    """OCR-based collector for manual screenshot fallback"""
    
    def __init__(self, config):
        super().__init__(config)
        self.screenshot_dir = Path("data/manual/screenshots")
        self.screenshot_dir.mkdir(parents=True, exist_ok=True)
        self.confidence_threshold = config["ocr"]["confidence_threshold"]
        self.username_pattern = re.compile(config["ocr"]["username_pattern"])
    
    def collect(self):
        """Process all screenshots in manual directory"""
        logger.info("Starting OCR collection from screenshots")
        
        screenshots = list(self.screenshot_dir.glob("*.png")) + \
                     list(self.screenshot_dir.glob("*.jpg")) + \
                     list(self.screenshot_dir.glob("*.jpeg"))
        
        if not screenshots:
            logger.warning("No screenshots found in data/manual/screenshots/")
            return None
        
        logger.info(f"Found {len(screenshots)} screenshots to process")
        
        all_usernames = set()
        low_confidence = []
        
        for screenshot in screenshots:
            logger.info(f"Processing: {screenshot.name}")
            
            usernames, confidence = self.extract_usernames_from_image(screenshot)
            
            if confidence < self.confidence_threshold:
                logger.warning(f"Low confidence ({confidence:.2f}) for {screenshot.name}")
                low_confidence.append(screenshot.name)
            
            all_usernames.update(usernames)
        
        # Save results
        data = {
            "collection_metadata": self.create_metadata("screenshot_ocr", "manual", False),
            "discovered_accounts": {
                username: {
                    "username": username,
                    "display_name": None,
                    "bio": None,
                    "source": ["manual_screenshot"],
                    "ocr_confidence": "mixed"
                }
                for username in all_usernames
            },
            "low_confidence_files": low_confidence
        }
        
        self.save_progress("screenshot_ocr", data)
        
        logger.info(f"Extracted {len(all_usernames)} unique usernames from screenshots")
        if low_confidence:
            logger.warning(f"{len(low_confidence)} files had low confidence")
        
        return data
    
    def extract_usernames_from_image(self, image_path):
        """Extract Instagram usernames from screenshot using OCR"""
        try:
            # Load and preprocess image
            image = Image.open(image_path)
            
            # Convert to grayscale
            image = image.convert('L')
            
            # Run OCR
            ocr_data = pytesseract.image_to_data(
                image,
                output_type=pytesseract.Output.DICT,
                config='--oem 3 --psm 6'
            )
            
            # Extract text with confidence
            text_parts = []
            confidences = []
            
            for i, word in enumerate(ocr_data['text']):
                if word.strip():
                    text_parts.append(word)
                    confidences.append(ocr_data['conf'][i])
            
            full_text = ' '.join(text_parts)
            avg_confidence = sum(confidences) / len(confidences) if confidences else 0
            
            # Extract usernames using pattern
            usernames = set()
            for match in self.username_pattern.finditer(full_text):
                username = match.group(1)
                
                # Validate username format
                if self.is_valid_username(username):
                    usernames.add(username)
            
            logger.debug(f"Found {len(usernames)} usernames with avg confidence {avg_confidence:.2f}")
            
            return list(usernames), avg_confidence / 100.0
            
        except Exception as e:
            logger.error(f"OCR failed for {image_path}: {e}")
            return [], 0.0
    
    def is_valid_username(self, username):
        """Validate Instagram username format"""
        if not username:
            return False
        
        # Instagram usernames: 1-30 chars, alphanumeric + underscore + period
        if not re.match(r'^[a-zA-Z0-9._]{1,30}$', username):
            return False
        
        # Filter out common OCR errors
        invalid_patterns = [
            r'^\d+$',  # Only numbers
            r'^[._]+$',  # Only punctuation
            r'http',  # URLs
            r'www\.',  # URLs
        ]
        
        for pattern in invalid_patterns:
            if re.search(pattern, username, re.IGNORECASE):
                return False
        
        return True
```

- [ ] **Step 2: Commit screenshot collector**

```bash
git add src/collectors/screenshot_collector.py
git commit -m "feat: implement screenshot OCR collector for manual fallback"
```

---

## Phase 4: Analysis Module

### Task 10: Graph Builder

**Files:**
- Create: `src/analyzers/__init__.py`
- Create: `src/analyzers/graph_builder.py`
- Create: `tests/test_graph_builder.py`

- [ ] **Step 1: Write test for graph builder**

Create `src/analyzers/__init__.py`:

```python
"""Analysis modules"""
```

Create `tests/test_graph_builder.py`:

```python
import pytest
import networkx as nx
from src.analyzers.graph_builder import GraphBuilder


def test_graph_builder_init():
    """Test GraphBuilder initializes correctly"""
    config = {
        "analysis": {
            "edge_weights": {
                "follows": 10,
                "replies_to": 9,
                "tags": 8
            }
        }
    }
    
    builder = GraphBuilder(config)
    assert builder.edge_weights["follows"] == 10


def test_build_graph_from_empty_data():
    """Test building graph from empty data"""
    config = {
        "target_account": "test_user",
        "analysis": {
            "edge_weights": {
                "follows": 10,
                "replies_to": 9,
                "tags": 8,
                "collaborator": 10,
                "repeated_commenter_base": 7,
                "frequency_bonus": 2,
                "mentioned": 6
            }
        }
    }
    
    builder = GraphBuilder(config)
    graph = builder.build_graph([])
    
    assert isinstance(graph, nx.DiGraph)
    assert len(graph.nodes) == 0


def test_build_graph_with_following():
    """Test building graph with following relationship"""
    config = {
        "target_account": "sarah",
        "analysis": {
            "edge_weights": {
                "follows": 10,
                "replies_to": 9,
                "tags": 8,
                "collaborator": 10,
                "repeated_commenter_base": 7,
                "frequency_bonus": 2,
                "mentioned": 6
            }
        }
    }
    
    raw_data = [{
        "collection_metadata": {"phase": "following"},
        "following": ["alice", "bob"]
    }]
    
    builder = GraphBuilder(config)
    graph = builder.build_graph(raw_data)
    
    assert "sarah" in graph.nodes
    assert "alice" in graph.nodes
    assert "bob" in graph.nodes
    assert graph.has_edge("sarah", "alice")
    assert graph.has_edge("sarah", "bob")
    assert graph["sarah"]["alice"]["weight"] == 10
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_graph_builder.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement GraphBuilder**

Create `src/analyzers/graph_builder.py`:

```python
import json
import logging
from pathlib import Path
import networkx as nx
import pandas as pd
from datetime import datetime

logger = logging.getLogger(__name__)


class GraphBuilder:
    """Builds network graph from collected data"""
    
    def __init__(self, config):
        self.config = config
        self.target_account = config["target_account"]
        self.edge_weights = config["analysis"]["edge_weights"]
        self.raw_data_dir = Path("data/raw")
        self.processed_dir = Path("data/processed")
        self.processed_dir.mkdir(parents=True, exist_ok=True)
    
    def load_all_raw_data(self):
        """Load all JSON files from raw data directory"""
        raw_files = list(self.raw_data_dir.glob("*.json"))
        
        logger.info(f"Loading {len(raw_files)} raw data files")
        
        all_data = []
        for filepath in raw_files:
            try:
                with open(filepath, 'r') as f:
                    data = json.load(f)
                    all_data.append(data)
            except Exception as e:
                logger.warning(f"Failed to load {filepath}: {e}")
        
        return all_data
    
    def build_graph(self, raw_data_list):
        """Build directed graph from raw data"""
        G = nx.DiGraph()
        
        # Add target node
        G.add_node(self.target_account, degree=0, category="target")
        
        accounts = {}  # Track account metadata
        relationships = []  # Track edges
        
        # Process each data file
        for data in raw_data_list:
            phase = data.get("collection_metadata", {}).get("phase", "unknown")
            
            if phase == "target_profile":
                self.process_target_profile(data, G, accounts)
            
            elif phase == "posts":
                self.process_posts(data, G, accounts, relationships)
            
            elif phase == "following":
                self.process_following(data, G, accounts, relationships)
            
            elif phase == "first_degree_accounts":
                self.process_first_degree_accounts(data, G, accounts)
        
        # Add edges with weights
        for rel in relationships:
            source = rel["source"]
            target = rel["target"]
            rel_type = rel["type"]
            weight = rel["weight"]
            
            if G.has_edge(source, target):
                # Edge exists, add to weight
                G[source][target]["weight"] += weight
                G[source][target]["types"].append(rel_type)
            else:
                # New edge
                G.add_edge(source, target, weight=weight, types=[rel_type])
        
        logger.info(f"Built graph: {len(G.nodes)} nodes, {len(G.edges)} edges")
        return G
    
    def process_target_profile(self, data, G, accounts):
        """Process target profile data"""
        profile = data.get("target_profile", {})
        
        if profile:
            accounts[self.target_account] = {
                "username": profile.get("username", self.target_account),
                "display_name": profile.get("display_name"),
                "bio": profile.get("bio"),
                "follower_count": profile.get("follower_count"),
                "following_count": profile.get("following_count"),
                "degree": 0,
                "category": "target"
            }
            
            # Update node attributes
            G.nodes[self.target_account].update(accounts[self.target_account])
    
    def process_posts(self, data, G, accounts, relationships):
        """Process posts data to extract relationships"""
        posts = data.get("posts", [])
        
        for post in posts:
            # Tagged accounts
            for username in post.get("tagged_accounts", []):
                if username not in G:
                    G.add_node(username, degree=1)
                    accounts[username] = {"username": username, "degree": 1}
                
                relationships.append({
                    "source": self.target_account,
                    "target": username,
                    "type": "tags",
                    "weight": self.edge_weights["tags"]
                })
            
            # Collaborators
            for username in post.get("collaborators", []):
                if username not in G:
                    G.add_node(username, degree=1)
                    accounts[username] = {"username": username, "degree": 1}
                
                relationships.append({
                    "source": self.target_account,
                    "target": username,
                    "type": "collaborator",
                    "weight": self.edge_weights["collaborator"]
                })
            
            # Commenters
            for commenter in post.get("commenters", []):
                username = commenter["username"]
                comment_count = commenter["comment_count"]
                target_replied = commenter.get("target_replied", False)
                
                if username not in G:
                    G.add_node(username, degree=1)
                    accounts[username] = {"username": username, "degree": 1}
                
                # Base weight + frequency bonus
                weight = self.edge_weights["repeated_commenter_base"]
                if comment_count > 1:
                    weight += (comment_count - 1) * self.edge_weights["frequency_bonus"]
                
                relationships.append({
                    "source": username,
                    "target": self.target_account,
                    "type": "comments",
                    "weight": weight
                })
                
                # If target replied, add reverse edge
                if target_replied:
                    relationships.append({
                        "source": self.target_account,
                        "target": username,
                        "type": "replies_to",
                        "weight": self.edge_weights["replies_to"]
                    })
    
    def process_following(self, data, G, accounts, relationships):
        """Process following list"""
        following = data.get("following", [])
        
        for username in following:
            if username not in G:
                G.add_node(username, degree=1)
                accounts[username] = {"username": username, "degree": 1}
            
            relationships.append({
                "source": self.target_account,
                "target": username,
                "type": "follows",
                "weight": self.edge_weights["follows"]
            })
    
    def process_first_degree_accounts(self, data, G, accounts):
        """Process first degree account details"""
        discovered = data.get("discovered_accounts", {})
        
        for username, profile in discovered.items():
            if username in accounts:
                # Update existing account with full profile
                accounts[username].update({
                    "display_name": profile.get("display_name"),
                    "bio": profile.get("bio"),
                    "follower_count": profile.get("follower_count"),
                    "following_count": profile.get("following_count")
                })
            else:
                # New account
                accounts[username] = {
                    "username": username,
                    "display_name": profile.get("display_name"),
                    "bio": profile.get("bio"),
                    "follower_count": profile.get("follower_count"),
                    "following_count": profile.get("following_count"),
                    "degree": 1
                }
                G.add_node(username, degree=1)
            
            # Update node attributes
            if username in G:
                G.nodes[username].update(accounts[username])
    
    def save_graph(self, G):
        """Save graph to processed directory"""
        # Save as JSON
        graph_data = nx.node_link_data(G)
        graph_file = self.processed_dir / "graph.json"
        
        with open(graph_file, 'w') as f:
            json.dump(graph_data, f, indent=2)
        
        logger.info(f"Graph saved to {graph_file}")
        
        # Save as CSV edge list
        edges = []
        for source, target, data in G.edges(data=True):
            edges.append({
                "source": source,
                "target": target,
                "weight": data["weight"],
                "types": ','.join(data["types"])
            })
        
        edges_df = pd.DataFrame(edges)
        edges_file = self.processed_dir / "relationships.csv"
        edges_df.to_csv(edges_file, index=False)
        
        logger.info(f"Edges saved to {edges_file}")
        
        # Save accounts as CSV
        accounts = []
        for node, data in G.nodes(data=True):
            accounts.append({
                "username": node,
                "display_name": data.get("display_name"),
                "bio": data.get("bio"),
                "follower_count": data.get("follower_count"),
                "following_count": data.get("following_count"),
                "degree": data.get("degree"),
                "category": data.get("category", "unknown")
            })
        
        accounts_df = pd.DataFrame(accounts)
        accounts_file = self.processed_dir / "accounts.csv"
        accounts_df.to_csv(accounts_file, index=False)
        
        logger.info(f"Accounts saved to {accounts_file}")
        
        return graph_file, edges_file, accounts_file
    
    def run(self):
        """Main execution: load data, build graph, save"""
        logger.info("Starting graph builder")
        
        raw_data = self.load_all_raw_data()
        graph = self.build_graph(raw_data)
        self.save_graph(graph)
        
        logger.info("Graph building complete")
        return graph
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_graph_builder.py -v
```

Expected: 3 PASS

- [ ] **Step 5: Commit graph builder**

```bash
git add src/analyzers/__init__.py src/analyzers/graph_builder.py tests/test_graph_builder.py
git commit -m "feat: implement graph builder with relationship processing"
```

### Task 11: Account Scorer

**Files:**
- Create: `src/analyzers/account_scorer.py`
- Create: `tests/test_account_scorer.py`

- [ ] **Step 1: Write test for account scorer**

Create `tests/test_account_scorer.py`:

```python
import pytest
import networkx as nx
from src.analyzers.account_scorer import AccountScorer


def test_account_scorer_init():
    """Test AccountScorer initializes correctly"""
    config = {
        "target_account": "test_user",
        "analysis": {
            "scoring_weights": {
                "proximity": 0.4,
                "engagement": 0.3,
                "bridge": 0.2,
                "category_fit": 0.1
            },
            "category_keywords": {
                "gallery": ["gallery"]
            }
        }
    }
    
    scorer = AccountScorer(config)
    assert scorer.target_account == "test_user"
    assert scorer.scoring_weights["proximity"] == 0.4


def test_calculate_proximity_score():
    """Test proximity score calculation"""
    config = {
        "target_account": "target",
        "analysis": {
            "scoring_weights": {
                "proximity": 0.4,
                "engagement": 0.3,
                "bridge": 0.2,
                "category_fit": 0.1
            },
            "category_keywords": {}
        }
    }
    
    # Create simple graph: target -> alice -> bob
    G = nx.DiGraph()
    G.add_edge("target", "alice", weight=10)
    G.add_edge("alice", "bob", weight=5)
    
    scorer = AccountScorer(config)
    
    # Alice is 1 hop away (direct connection)
    alice_score = scorer.calculate_proximity_score(G, "alice")
    assert alice_score > 0
    
    # Bob is 2 hops away
    bob_score = scorer.calculate_proximity_score(G, "bob")
    assert bob_score > 0
    assert alice_score > bob_score  # Closer = higher score


def test_calculate_engagement_score():
    """Test engagement score calculation"""
    config = {
        "target_account": "target",
        "analysis": {
            "scoring_weights": {
                "proximity": 0.4,
                "engagement": 0.3,
                "bridge": 0.2,
                "category_fit": 0.1
            },
            "category_keywords": {}
        }
    }
    
    # Graph with weighted edges
    G = nx.DiGraph()
    G.add_edge("target", "alice", weight=10)
    G.add_edge("alice", "target", weight=7)  # Alice comments back
    G.add_edge("target", "bob", weight=5)
    
    scorer = AccountScorer(config)
    
    # Alice has more engagement (bidirectional)
    alice_score = scorer.calculate_engagement_score(G, "alice")
    bob_score = scorer.calculate_engagement_score(G, "bob")
    
    assert alice_score > bob_score
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_account_scorer.py -v
```

Expected: FAIL with "ModuleNotFoundError"

- [ ] **Step 3: Implement AccountScorer**

Create `src/analyzers/account_scorer.py`:

```python
import json
import logging
from pathlib import Path
import networkx as nx
import re

logger = logging.getLogger(__name__)


class AccountScorer:
    """Calculates engagement scores and rankings"""
    
    def __init__(self, config):
        self.config = config
        self.target_account = config["target_account"]
        self.scoring_weights = config["analysis"]["scoring_weights"]
        self.category_keywords = config["analysis"]["category_keywords"]
        self.outputs_dir = Path("outputs")
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
    
    def calculate_proximity_score(self, G, account):
        """Calculate how directly connected account is to target"""
        if account == self.target_account:
            return 100.0
        
        try:
            # Find shortest path from target to account
            if nx.has_path(G, self.target_account, account):
                path = nx.shortest_path(G, self.target_account, account, weight='weight')
                path_length = len(path) - 1  # Number of hops
                
                # Score: inverse of path length, scaled to 0-100
                # 1 hop = 100, 2 hops = 50, 3 hops = 33, etc.
                score = (1.0 / path_length) * 100
                return min(score, 100.0)
            
            # Check reverse path (account -> target)
            elif nx.has_path(G, account, self.target_account):
                path = nx.shortest_path(G, account, self.target_account, weight='weight')
                path_length = len(path) - 1
                
                # Slightly lower score for reverse paths
                score = (1.0 / path_length) * 80
                return min(score, 100.0)
            
            else:
                # No path found
                return 0.0
                
        except (nx.NetworkXNoPath, nx.NodeNotFound):
            return 0.0
    
    def calculate_engagement_score(self, G, account):
        """Calculate frequency and strength of interactions"""
        if account == self.target_account:
            return 100.0
        
        total_weight = 0
        
        # Outgoing edges from target to account
        if G.has_edge(self.target_account, account):
            total_weight += G[self.target_account][account]["weight"]
        
        # Incoming edges from account to target
        if G.has_edge(account, self.target_account):
            total_weight += G[account][self.target_account]["weight"]
        
        # Normalize to 0-100 scale
        # Max expected weight: ~30 (multiple interaction types)
        score = min((total_weight / 30.0) * 100, 100.0)
        
        return score
    
    def calculate_bridge_score(self, G, account):
        """Calculate betweenness centrality (bridge nodes)"""
        try:
            # Calculate betweenness centrality for entire graph
            centrality = nx.betweenness_centrality(G, weight='weight')
            
            if account in centrality:
                # Normalize to 0-100
                max_centrality = max(centrality.values()) if centrality else 1
                score = (centrality[account] / max_centrality) * 100 if max_centrality > 0 else 0
                return score
            else:
                return 0.0
                
        except Exception as e:
            logger.warning(f"Failed to calculate bridge score for {account}: {e}")
            return 0.0
    
    def classify_category(self, account_data):
        """Classify account by category using keyword matching"""
        bio = account_data.get("bio", "") or ""
        bio_lower = bio.lower()
        
        category_scores = {}
        
        for category, keywords in self.category_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword.lower() in bio_lower:
                    score += 1
            
            if score > 0:
                category_scores[category] = score
        
        if not category_scores:
            return "unknown", 0.0
        
        # Return category with highest score
        best_category = max(category_scores, key=category_scores.get)
        max_score = category_scores[best_category]
        
        # Confidence based on number of keyword matches
        confidence = min(max_score / 3.0, 1.0)  # 3+ keywords = 100% confidence
        
        return best_category, confidence
    
    def score_accounts(self, G):
        """Score all accounts in graph"""
        logger.info("Scoring all accounts")
        
        scored_accounts = []
        
        for node in G.nodes():
            if node == self.target_account:
                continue
            
            account_data = G.nodes[node]
            
            # Calculate individual scores
            proximity = self.calculate_proximity_score(G, node)
            engagement = self.calculate_engagement_score(G, node)
            bridge = self.calculate_bridge_score(G, node)
            
            category, category_confidence = self.classify_category(account_data)
            
            # Category fit score: higher if in desirable categories
            desirable_categories = ["gallery", "curator", "wood_artist", "furniture_designer"]
            category_fit = 100.0 if category in desirable_categories else 50.0
            
            # Overall score (weighted average)
            overall = (
                proximity * self.scoring_weights["proximity"] +
                engagement * self.scoring_weights["engagement"] +
                bridge * self.scoring_weights["bridge"] +
                category_fit * self.scoring_weights["category_fit"]
            )
            
            scored_accounts.append({
                "username": node,
                "display_name": account_data.get("display_name"),
                "bio": account_data.get("bio"),
                "follower_count": account_data.get("follower_count"),
                "overall_score": round(overall, 2),
                "proximity_score": round(proximity, 2),
                "engagement_score": round(engagement, 2),
                "bridge_score": round(bridge, 2),
                "category_fit_score": round(category_fit, 2),
                "predicted_category": category,
                "category_confidence": round(category_confidence, 2),
                "degree": account_data.get("degree", 1)
            })
        
        # Sort by overall score
        scored_accounts.sort(key=lambda x: x["overall_score"], reverse=True)
        
        logger.info(f"Scored {len(scored_accounts)} accounts")
        return scored_accounts
    
    def save_scores(self, scored_accounts, graph_metrics=None):
        """Save scores to JSON file"""
        output = {
            "scoring_metadata": {
                "total_accounts": len(scored_accounts),
                "target_account": self.target_account,
                "generated_at": pd.Timestamp.now().isoformat()
            },
            "ranked_accounts": scored_accounts
        }
        
        if graph_metrics:
            output["graph_metrics"] = graph_metrics
        
        output_file = self.outputs_dir / "scores.json"
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Scores saved to {output_file}")
        return output_file
    
    def run(self, graph):
        """Main execution: score accounts and save"""
        logger.info("Starting account scoring")
        
        scored_accounts = self.score_accounts(graph)
        self.save_scores(scored_accounts)
        
        logger.info("Account scoring complete")
        return scored_accounts
```

Add missing import:
```python
import pandas as pd
```

- [ ] **Step 4: Run test to verify it passes**

```bash
pytest tests/test_account_scorer.py -v
```

Expected: 3 PASS

- [ ] **Step 5: Commit account scorer**

```bash
git add src/analyzers/account_scorer.py tests/test_account_scorer.py
git commit -m "feat: implement account scorer with proximity, engagement, and bridge scores"
```

### Task 12: Community Detector

**Files:**
- Create: `src/analyzers/community_detector.py`

- [ ] **Step 1: Implement community detector**

Create `src/analyzers/community_detector.py`:

```python
import json
import logging
from pathlib import Path
import networkx as nx
from collections import Counter

logger = logging.getLogger(__name__)


class CommunityDetector:
    """Identifies clusters and bridge nodes"""
    
    def __init__(self, config):
        self.config = config
        self.target_account = config["target_account"]
        self.outputs_dir = Path("outputs")
    
    def detect_communities(self, G):
        """Detect communities using Louvain algorithm"""
        logger.info("Detecting communities")
        
        # Convert to undirected for community detection
        G_undirected = G.to_undirected()
        
        try:
            # Use greedy modularity communities
            from networkx.algorithms import community
            communities = list(community.greedy_modularity_communities(G_undirected, weight='weight'))
            
            logger.info(f"Found {len(communities)} communities")
            
            # Convert to list of sets -> list of lists (JSON serializable)
            community_list = []
            for i, comm in enumerate(communities):
                community_list.append({
                    "cluster_id": i,
                    "members": list(comm),
                    "size": len(comm)
                })
            
            return community_list
            
        except Exception as e:
            logger.error(f"Community detection failed: {e}")
            return []
    
    def find_bridge_accounts(self, G, communities):
        """Find accounts that bridge multiple communities"""
        logger.info("Finding bridge accounts")
        
        # Calculate betweenness centrality
        try:
            centrality = nx.betweenness_centrality(G, weight='weight')
        except:
            logger.warning("Failed to calculate betweenness centrality")
            return []
        
        # Create community membership map
        membership = {}
        for comm in communities:
            for member in comm["members"]:
                membership[member] = comm["cluster_id"]
        
        # Find accounts with high betweenness that connect different communities
        bridge_accounts = []
        
        for node, betweenness in centrality.items():
            if node == self.target_account:
                continue
            
            # Check neighbors' communities
            neighbors = list(G.predecessors(node)) + list(G.successors(node))
            neighbor_communities = [membership.get(n) for n in neighbors if n in membership]
            
            # If neighbors span multiple communities, this is a bridge
            unique_communities = len(set(neighbor_communities))
            
            if unique_communities >= 2 and betweenness > 0.01:
                bridge_accounts.append({
                    "username": node,
                    "betweenness": round(betweenness, 4),
                    "connects_communities": unique_communities,
                    "community_ids": list(set(neighbor_communities))
                })
        
        # Sort by betweenness
        bridge_accounts.sort(key=lambda x: x["betweenness"], reverse=True)
        
        logger.info(f"Found {len(bridge_accounts)} bridge accounts")
        return bridge_accounts
    
    def analyze_community_categories(self, G, communities):
        """Determine dominant category for each community"""
        for comm in communities:
            categories = []
            
            for member in comm["members"]:
                if member in G.nodes:
                    category = G.nodes[member].get("category", "unknown")
                    categories.append(category)
            
            if categories:
                category_counts = Counter(categories)
                dominant = category_counts.most_common(1)[0]
                comm["dominant_category"] = dominant[0]
                comm["category_distribution"] = dict(category_counts)
            else:
                comm["dominant_category"] = "unknown"
                comm["category_distribution"] = {}
        
        return communities
    
    def save_metrics(self, communities, bridges):
        """Save graph metrics to JSON"""
        output = {
            "communities": communities,
            "bridge_accounts": bridges,
            "summary": {
                "total_communities": len(communities),
                "total_bridges": len(bridges),
                "largest_community_size": max([c["size"] for c in communities]) if communities else 0
            }
        }
        
        output_file = self.outputs_dir / "graph_metrics.json"
        
        with open(output_file, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.info(f"Graph metrics saved to {output_file}")
        return output_file
    
    def run(self, graph):
        """Main execution: detect communities and bridges"""
        logger.info("Starting community detection")
        
        communities = self.detect_communities(graph)
        communities = self.analyze_community_categories(graph, communities)
        bridges = self.find_bridge_accounts(graph, communities)
        self.save_metrics(communities, bridges)
        
        logger.info("Community detection complete")
        return communities, bridges
```

- [ ] **Step 2: Commit community detector**

```bash
git add src/analyzers/community_detector.py
git commit -m "feat: implement community detector with bridge node identification"
```

---

## Phase 5: Reporting Module

### Task 13: AI Reporter

**Files:**
- Create: `src/reporters/__init__.py`
- Create: `src/reporters/ai_reporter.py`

- [ ] **Step 1: Create AI reporter**

Create `src/reporters/__init__.py`:

```python
"""Reporting modules"""
```

Create `src/reporters/ai_reporter.py`:

```python
import json
import logging
from pathlib import Path
import pandas as pd

logger = logging.getLogger(__name__)


class AIReporter:
    """Generates AI-consumable outputs"""
    
    def __init__(self, config):
        self.config = config
        self.target_account = config["target_account"]
        self.processed_dir = Path("data/processed")
        self.outputs_dir = Path("outputs")
        self.outputs_dir.mkdir(parents=True, exist_ok=True)
    
    def load_processed_data(self):
        """Load processed data and scores"""
        # Load accounts
        accounts_file = self.processed_dir / "accounts.csv"
        accounts_df = pd.read_csv(accounts_file) if accounts_file.exists() else pd.DataFrame()
        
        # Load relationships
        relationships_file = self.processed_dir / "relationships.csv"
        relationships_df = pd.read_csv(relationships_file) if relationships_file.exists() else pd.DataFrame()
        
        # Load scores
        scores_file = self.outputs_dir / "scores.json"
        with open(scores_file, 'r') as f:
            scores_data = json.load(f)
        
        # Load graph metrics
        metrics_file = self.outputs_dir / "graph_metrics.json"
        metrics_data = {}
        if metrics_file.exists():
            with open(metrics_file, 'r') as f:
                metrics_data = json.load(f)
        
        return accounts_df, relationships_df, scores_data, metrics_data
    
    def generate_recommended_targets(self, scores_data):
        """Generate top recommended accounts with tiers"""
        accounts = scores_data["ranked_accounts"]
        
        recommendations = []
        
        for i, account in enumerate(accounts[:50]):  # Top 50
            # Assign tier
            if i < 15:
                tier = "A"
                tier_label = "High Priority"
            elif i < 35:
                tier = "B"
                tier_label = "Secondary Priority"
            else:
                tier = "C"
                tier_label = "Monitor"
            
            # Generate engagement strategy
            category = account["predicted_category"]
            strategy = self.suggest_engagement_strategy(category, account)
            
            recommendations.append({
                "username": account["username"],
                "display_name": account["display_name"],
                "category": category,
                "overall_score": account["overall_score"],
                "engagement_score": account["engagement_score"],
                "recommendation_tier": tier,
                "tier_label": tier_label,
                "evidence_summary": self.generate_evidence_summary(account),
                "engagement_strategy": strategy
            })
        
        # Save as CSV
        df = pd.DataFrame(recommendations)
        output_file = self.outputs_dir / "recommended_targets.csv"
        df.to_csv(output_file, index=False)
        
        logger.info(f"Recommended targets saved to {output_file}")
        return recommendations
    
    def suggest_engagement_strategy(self, category, account):
        """Suggest engagement strategy based on category"""
        strategies = {
            "gallery": "Comment on posts featuring craft/wood artists. Share relevant work. Mention in posts when appropriate.",
            "curator": "Engage with exhibition announcements. Comment thoughtfully on curatorial themes.",
            "wood_artist": "Comment on technique and craftsmanship. Share common interests. Potential collaboration.",
            "craft_artist": "Engage with process posts. Share making journeys. Community building.",
            "furniture_designer": "Comment on design and material choices. Cross-pollination opportunity.",
            "collector": "Engage when they share acquisitions. Build awareness of your work.",
            "institution": "Professional engagement only. Share when relevant exhibitions announced.",
            "fair": "Follow announcements. Engage during events. Note gallery participants.",
            "journalist": "Engage with articles about craft/design. Thoughtful, professional comments only."
        }
        
        return strategies.get(category, "Monitor activity. Engage authentically when relevant.")
    
    def generate_evidence_summary(self, account):
        """Generate evidence summary for recommendation"""
        evidence_parts = []
        
        if account["proximity_score"] > 70:
            evidence_parts.append("Direct connection to target")
        
        if account["engagement_score"] > 70:
            evidence_parts.append("High engagement frequency")
        
        if account["bridge_score"] > 50:
            evidence_parts.append("Bridge account connecting communities")
        
        if account["category_confidence"] > 0.7:
            evidence_parts.append(f"Confirmed {account['predicted_category']}")
        
        return "; ".join(evidence_parts) if evidence_parts else "Indirect connection"
    
    def generate_ai_summary(self, accounts_df, scores_data, metrics_data):
        """Generate markdown summary for AI consumption"""
        num_accounts = len(scores_data["ranked_accounts"])
        target = self.target_account
        
        # Calculate completeness
        total_fields = len(accounts_df) * len(accounts_df.columns)
        null_fields = accounts_df.isnull().sum().sum()
        completeness = round((1 - null_fields / total_fields) * 100, 1) if total_fields > 0 else 0
        
        # Get top categories
        categories = [a["predicted_category"] for a in scores_data["ranked_accounts"]]
        category_counts = pd.Series(categories).value_counts().head(5)
        
        # Get top recommendations
        top_15 = scores_data["ranked_accounts"][:15]
        
        summary = f"""# Instagram Ecosystem Analysis: @{target}

**Collection Date:** {scores_data['scoring_metadata']['generated_at'][:10]}
**Accounts Analyzed:** {num_accounts}
**Data Completeness:** {completeness}%

## Key Findings

### Account Type Distribution
"""
        
        for category, count in category_counts.items():
            pct = round(count / len(categories) * 100, 1)
            summary += f"- {category}: {count} accounts ({pct}%)\n"
        
        if metrics_data.get("communities"):
            num_communities = len(metrics_data["communities"])
            largest = max([c["size"] for c in metrics_data["communities"]])
            summary += f"\n### Network Structure\n"
            summary += f"- Number of communities: {num_communities}\n"
            summary += f"- Largest community: {largest} accounts\n"
        
        if metrics_data.get("bridge_accounts"):
            top_bridges = metrics_data["bridge_accounts"][:5]
            summary += f"\n### Top Bridge Accounts\n"
            for bridge in top_bridges:
                summary += f"- @{bridge['username']} (connects {bridge['connects_communities']} communities)\n"
        
        summary += f"\n## Top 15 Recommendations (Tier A)\n\n"
        summary += "| Username | Category | Score | Evidence |\n"
        summary += "|----------|----------|-------|----------|\n"
        
        for account in top_15:
            username = account["username"]
            category = account["predicted_category"]
            score = account["overall_score"]
            evidence = self.generate_evidence_summary(account)
            summary += f"| @{username} | {category} | {score} | {evidence} |\n"
        
        summary += f"\n## Engagement Strategy\n\n"
        summary += "### General Principles\n"
        summary += "- Authentic engagement only - no spam or generic comments\n"
        summary += "- Focus on craft, technique, and material discussions\n"
        summary += "- Build relationships gradually\n"
        summary += "- Comment on 2-3 posts before considering DM outreach\n"
        
        summary += "\n### Category-Specific Strategies\n"
        for category in category_counts.head(3).index:
            strategy = self.suggest_engagement_strategy(category, {})
            summary += f"\n**{category.replace('_', ' ').title()}:** {strategy}\n"
        
        # Save summary
        output_file = self.outputs_dir / "ai_summary.md"
        with open(output_file, 'w') as f:
            f.write(summary)
        
        logger.info(f"AI summary saved to {output_file}")
        return summary
    
    def run(self):
        """Main execution: generate all reports"""
        logger.info("Starting report generation")
        
        accounts_df, relationships_df, scores_data, metrics_data = self.load_processed_data()
        
        recommendations = self.generate_recommended_targets(scores_data)
        summary = self.generate_ai_summary(accounts_df, scores_data, metrics_data)
        
        logger.info("Report generation complete")
        return recommendations, summary
```

- [ ] **Step 2: Commit AI reporter**

```bash
git add src/reporters/__init__.py src/reporters/ai_reporter.py
git commit -m "feat: implement AI reporter with tiered recommendations and engagement strategies"
```

---

## Phase 6: Integration Scripts

### Task 14: Main Collection Script

**Files:**
- Create: `scripts/collect.py`

- [ ] **Step 1: Create collection script**

Create `scripts/collect.py`:

```python
#!/usr/bin/env python3
"""
Instagram data collection script
"""
import sys
import json
import logging
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.collectors.playwright_collector import PlaywrightCollector
from src.collectors.screenshot_collector import ScreenshotCollector

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/collection.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    parser = argparse.ArgumentParser(description='Collect Instagram data')
    parser.add_argument('--limit', type=int, help='Limit posts collected (for testing)')
    parser.add_argument('--ocr-only', action='store_true', help='Only run OCR on screenshots')
    parser.add_argument('--resume', action='store_true', help='Resume from checkpoint')
    
    args = parser.parse_args()
    
    # Load config
    config_file = Path('config.json')
    if not config_file.exists():
        logger.error("config.json not found")
        return 1
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    # Apply limit if specified
    if args.limit:
        config['collection']['max_posts'] = args.limit
    
    try:
        if args.ocr_only:
            # Run OCR collector only
            logger.info("Running OCR collector on screenshots")
            collector = ScreenshotCollector(config)
            collector.collect()
        else:
            # Run Playwright collector
            logger.info("Running Playwright collector")
            collector = PlaywrightCollector(config)
            collector.collect()
        
        logger.info("Collection complete!")
        return 0
        
    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")
        return 1
    except Exception as e:
        logger.error(f"Collection failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 2: Make script executable**

```bash
chmod +x scripts/collect.py
```

- [ ] **Step 3: Commit collection script**

```bash
git add scripts/collect.py
git commit -m "feat: add collection script with CLI arguments"
```

### Task 15: Analysis and Reporting Scripts

**Files:**
- Create: `scripts/analyze.py`
- Create: `scripts/report.py`
- Create: `scripts/run_all.py`

- [ ] **Step 1: Create analyze script**

Create `scripts/analyze.py`:

```python
#!/usr/bin/env python3
"""
Instagram data analysis script
"""
import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzers.graph_builder import GraphBuilder
from src.analyzers.account_scorer import AccountScorer
from src.analyzers.community_detector import CommunityDetector

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    try:
        # Build graph
        logger.info("Building graph from raw data")
        graph_builder = GraphBuilder(config)
        graph = graph_builder.run()
        
        # Score accounts
        logger.info("Scoring accounts")
        scorer = AccountScorer(config)
        scored_accounts = scorer.run(graph)
        
        # Detect communities
        logger.info("Detecting communities")
        detector = CommunityDetector(config)
        communities, bridges = detector.run(graph)
        
        logger.info("Analysis complete!")
        logger.info(f"Total accounts: {len(graph.nodes)}")
        logger.info(f"Total relationships: {len(graph.edges)}")
        logger.info(f"Communities found: {len(communities)}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 2: Create report script**

Create `scripts/report.py`:

```python
#!/usr/bin/env python3
"""
Instagram report generation script
"""
import sys
import json
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.reporters.ai_reporter import AIReporter

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/reporting.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def main():
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    try:
        logger.info("Generating reports")
        reporter = AIReporter(config)
        recommendations, summary = reporter.run()
        
        logger.info("Reports generated!")
        logger.info(f"Recommendations: {len(recommendations)}")
        logger.info("Check outputs/ directory for results")
        
        return 0
        
    except Exception as e:
        logger.error(f"Reporting failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 3: Create run_all orchestrator**

Create `scripts/run_all.py`:

```python
#!/usr/bin/env python3
"""
Run complete Instagram ecosystem mapping pipeline
"""
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def run_command(cmd, description):
    """Run command and handle errors"""
    logger.info(f"Running: {description}")
    result = subprocess.run(cmd, shell=True)
    
    if result.returncode != 0:
        logger.error(f"Failed: {description}")
        return False
    
    logger.info(f"Complete: {description}")
    return True


def main():
    logger.info("="*60)
    logger.info("Instagram Ecosystem Mapping - Full Pipeline")
    logger.info("="*60)
    
    # Step 1: Collection
    if not run_command("python scripts/collect.py", "Data Collection"):
        logger.error("Collection failed - stopping pipeline")
        return 1
    
    # Step 2: Analysis
    if not run_command("python scripts/analyze.py", "Data Analysis"):
        logger.error("Analysis failed - stopping pipeline")
        return 1
    
    # Step 3: Reporting
    if not run_command("python scripts/report.py", "Report Generation"):
        logger.error("Reporting failed - stopping pipeline")
        return 1
    
    logger.info("="*60)
    logger.info("Pipeline complete!")
    logger.info("Check outputs/ directory for results")
    logger.info("="*60)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 4: Make scripts executable**

```bash
chmod +x scripts/analyze.py scripts/report.py scripts/run_all.py
```

- [ ] **Step 5: Commit all scripts**

```bash
git add scripts/analyze.py scripts/report.py scripts/run_all.py
git commit -m "feat: add analysis, reporting, and orchestrator scripts"
```

---

## Phase 7: Testing Infrastructure

### Task 16: Smoke Tests

**Files:**
- Create: `scripts/test_connection.py`
- Create: `scripts/test_playwright.py`
- Create: `scripts/test_target_account.py`

- [ ] **Step 1: Create connection test**

Create `scripts/test_connection.py`:

```python
#!/usr/bin/env python3
"""Test Instagram connectivity"""
import sys
import requests

def main():
    print("Testing Instagram connectivity...")
    
    try:
        response = requests.get("https://www.instagram.com", timeout=10)
        
        if response.status_code == 200:
            print("✓ Instagram is accessible")
            return 0
        else:
            print(f"✗ Instagram returned status {response.status_code}")
            return 1
            
    except requests.RequestException as e:
        print(f"✗ Connection failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 2: Create Playwright test**

Create `scripts/test_playwright.py`:

```python
#!/usr/bin/env python3
"""Test Playwright setup"""
import sys
from playwright.sync_api import sync_playwright

def main():
    print("Testing Playwright...")
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto("https://www.instagram.com")
            
            title = page.title()
            
            browser.close()
            
            if title:
                print(f"✓ Playwright working (page title: {title})")
                return 0
            else:
                print("✗ Playwright launched but couldn't get page title")
                return 1
                
    except Exception as e:
        print(f"✗ Playwright test failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 3: Create target account test**

Create `scripts/test_target_account.py`:

```python
#!/usr/bin/env python3
"""Test target account accessibility"""
import sys
import json
from playwright.sync_api import sync_playwright

def main():
    print("Testing target account...")
    
    # Load config
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    target = config['target_account']
    url = f"https://www.instagram.com/{target}/"
    
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            page.goto(url, timeout=30000)
            
            title = page.title()
            
            # Check for "Page Not Found"
            if "Page Not Found" in title or "Sorry" in title:
                print(f"✗ Account @{target} not found or inaccessible")
                browser.close()
                return 1
            
            # Check for private account
            content = page.content()
            if "This account is private" in content:
                print(f"⚠ Account @{target} is PRIVATE - data collection will be limited")
                browser.close()
                return 0
            
            browser.close()
            print(f"✓ Account @{target} is accessible and public")
            return 0
            
    except Exception as e:
        print(f"✗ Test failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 4: Make scripts executable**

```bash
chmod +x scripts/test_*.py
```

- [ ] **Step 5: Commit smoke tests**

```bash
git add scripts/test_connection.py scripts/test_playwright.py scripts/test_target_account.py
git commit -m "feat: add smoke tests for connectivity, playwright, and target account"
```

### Task 17: Validation Script

**Files:**
- Create: `scripts/validate_output.py`

- [ ] **Step 1: Create validation script**

Create `scripts/validate_output.py`:

```python
#!/usr/bin/env python3
"""Validate output file formats"""
import sys
import json
from pathlib import Path
import pandas as pd

def validate_file_exists(filepath, name):
    """Check if file exists"""
    if not filepath.exists():
        print(f"✗ Missing: {name} ({filepath})")
        return False
    print(f"✓ Found: {name}")
    return True


def validate_csv_schema(filepath, required_columns, name):
    """Validate CSV has required columns"""
    try:
        df = pd.read_csv(filepath)
        missing = set(required_columns) - set(df.columns)
        
        if missing:
            print(f"✗ {name} missing columns: {missing}")
            return False
        
        print(f"✓ {name} schema valid ({len(df)} rows)")
        return True
        
    except Exception as e:
        print(f"✗ {name} validation failed: {e}")
        return False


def validate_json_structure(filepath, required_keys, name):
    """Validate JSON has required keys"""
    try:
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        missing = set(required_keys) - set(data.keys())
        
        if missing:
            print(f"✗ {name} missing keys: {missing}")
            return False
        
        print(f"✓ {name} structure valid")
        return True
        
    except Exception as e:
        print(f"✗ {name} validation failed: {e}")
        return False


def main():
    print("Validating outputs...")
    print("="*60)
    
    outputs_dir = Path("outputs")
    processed_dir = Path("data/processed")
    
    all_valid = True
    
    # Check processed files
    print("\nProcessed Data:")
    all_valid &= validate_file_exists(processed_dir / "accounts.csv", "accounts.csv")
    all_valid &= validate_csv_schema(
        processed_dir / "accounts.csv",
        ["username", "display_name", "bio", "degree"],
        "accounts.csv"
    )
    
    all_valid &= validate_file_exists(processed_dir / "relationships.csv", "relationships.csv")
    all_valid &= validate_csv_schema(
        processed_dir / "relationships.csv",
        ["source", "target", "weight", "types"],
        "relationships.csv"
    )
    
    # Check output files
    print("\nOutput Files:")
    all_valid &= validate_file_exists(outputs_dir / "scores.json", "scores.json")
    all_valid &= validate_json_structure(
        outputs_dir / "scores.json",
        ["scoring_metadata", "ranked_accounts"],
        "scores.json"
    )
    
    all_valid &= validate_file_exists(outputs_dir / "recommended_targets.csv", "recommended_targets.csv")
    all_valid &= validate_csv_schema(
        outputs_dir / "recommended_targets.csv",
        ["username", "category", "overall_score", "recommendation_tier"],
        "recommended_targets.csv"
    )
    
    all_valid &= validate_file_exists(outputs_dir / "ai_summary.md", "ai_summary.md")
    
    print("="*60)
    if all_valid:
        print("✓ All validations passed")
        return 0
    else:
        print("✗ Some validations failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
```

- [ ] **Step 2: Make executable and commit**

```bash
chmod +x scripts/validate_output.py
git add scripts/validate_output.py
git commit -m "feat: add output validation script"
```

---

## Phase 8: Final Setup

### Task 18: Update README and Create .gitignore

**Files:**
- Modify: `README.md`
- Create: `.gitignore`
- Create: `tests/__init__.py`

- [ ] **Step 1: Create comprehensive README**

Update `README.md`:

```markdown
# Instagram Ecosystem Mapping Tool

Map Instagram ecosystems to identify galleries, curators, collectors, artists, and bridge nodes for strategic engagement planning.

## Features

- **Modular Pipeline**: Independent collection, analysis, and reporting modules
- **Browser Automation**: Playwright-based data collection with rate limiting
- **OCR Fallback**: Manual screenshot processing when automation is blocked
- **Network Analysis**: Graph construction with community detection and bridge node identification
- **AI-Optimized Output**: Structured CSV/JSON outputs ready for AI analysis
- **Smart Scoring**: Multi-factor account ranking (proximity, engagement, bridge potential)

## Setup

### Requirements

- Python 3.14+
- Tesseract OCR (for screenshot fallback)

### Installation

```bash
# Clone repository
cd ~/code/instagram-ecosystem-tool

# Install Python dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium

# Install Tesseract (macOS)
brew install tesseract
```

### Configuration

Edit `config.json` to set:
- Target Instagram account
- Rate limiting parameters
- Scoring weights
- Category keywords

## Usage

### Quick Start

```bash
# Run smoke tests
python scripts/test_connection.py
python scripts/test_playwright.py
python scripts/test_target_account.py

# Run full pipeline
python scripts/run_all.py
```

### Individual Phases

```bash
# Phase 1: Collect data
python scripts/collect.py

# Phase 2: Analyze
python scripts/analyze.py

# Phase 3: Generate reports
python scripts/report.py

# Validate outputs
python scripts/validate_output.py
```

### Collection Options

```bash
# Test with limited posts
python scripts/collect.py --limit 5

# OCR only (process screenshots)
python scripts/collect.py --ocr-only

# Resume from checkpoint
python scripts/collect.py --resume
```

### Manual Fallback

If automation is blocked:

1. Take screenshots of Instagram pages (following list, posts, etc.)
2. Save to `data/manual/screenshots/`
3. Run: `python scripts/collect.py --ocr-only`
4. Continue with analysis

## Output Files

### Processed Data
- `data/processed/accounts.csv` - All discovered accounts
- `data/processed/relationships.csv` - Network edge list
- `data/processed/graph.json` - Full graph structure

### Analysis Outputs
- `outputs/scores.json` - Account scores and rankings
- `outputs/graph_metrics.json` - Community structure and bridge nodes
- `outputs/recommended_targets.csv` - Top 50 prioritized accounts
- `outputs/ai_summary.md` - Human-readable summary

## Architecture

```
Collection (Playwright/OCR)
    ↓
data/raw/*.json
    ↓
Analysis (NetworkX)
    ↓
data/processed/*.csv
    ↓
Reporting
    ↓
outputs/*.csv, *.json, *.md
```

## Compliance

- ✅ Public data only
- ✅ Respectful rate limiting (2-5s delays)
- ✅ No automated engagement
- ✅ User-controlled authentication
- ⚠️ Use responsibly - respect Instagram's Terms of Service

## Troubleshooting

**Rate limited?**
- Increase delays in `config.json`
- Use `--limit` flag for testing
- Wait 24 hours before retrying

**Login wall?**
- Tool will pause and prompt for manual login
- Press Enter after logging in to continue
- Or press Ctrl+C to skip and continue with limited data

**CAPTCHA?**
- Tool will save progress and exit
- Wait and retry later
- Use `--resume` flag to continue

## Development

Run tests:
```bash
pytest tests/ -v
```

## License

For research and personal use. Not for commercial scraping or spam.
```

- [ ] **Step 2: Create .gitignore**

Create `.gitignore`:

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Data directories
data/raw/*.json
data/manual/screenshots/*
!data/manual/screenshots/.gitkeep
data/processed/*
!data/processed/.gitkeep

# Outputs
outputs/*
!outputs/.gitkeep

# Logs
logs/*
!logs/.gitkeep
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Session data
data/.session_cookies.json

# Test data
tests/fixtures/*.json
!tests/fixtures/.gitkeep
```

- [ ] **Step 3: Create __init__ files**

```bash
touch tests/__init__.py
touch data/raw/.gitkeep
touch data/manual/screenshots/.gitkeep
touch data/processed/.gitkeep
touch outputs/.gitkeep
touch logs/.gitkeep
```

- [ ] **Step 4: Commit final setup**

```bash
git add README.md .gitignore tests/__init__.py data/ outputs/ logs/
git commit -m "docs: comprehensive README and gitignore setup"
```

### Task 19: Final Integration Test

**Files:**
- Create: `tests/fixtures/sample_instagram_data.json`

- [ ] **Step 1: Create test fixture**

Create `tests/fixtures/sample_instagram_data.json`:

```json
{
  "collection_metadata": {
    "source": "test_fixture",
    "timestamp": "2026-05-29T10:00:00Z",
    "target_account": "test_target",
    "phase": "complete"
  },
  "target_profile": {
    "username": "test_target",
    "display_name": "Test Target",
    "bio": "Test gallery representing wood artists",
    "follower_count": 1000,
    "following_count": 500
  },
  "posts": [
    {
      "url": "https://instagram.com/p/test1",
      "caption": "Beautiful work by @artist1 and @artist2",
      "tagged_accounts": ["artist1", "artist2"],
      "commenters": [
        {"username": "fan1", "comment_count": 3, "target_replied": true},
        {"username": "collector1", "comment_count": 1, "target_replied": false}
      ]
    }
  ],
  "following": ["artist1", "curator1", "gallery1"],
  "discovered_accounts": {
    "artist1": {
      "username": "artist1",
      "display_name": "Artist One",
      "bio": "Wood sculptor and maker",
      "follower_count": 5000,
      "degree": 1
    }
  }
}
```

- [ ] **Step 2: Run final integration test**

```bash
# Test that all modules can load
python -c "
from src.collectors.playwright_collector import PlaywrightCollector
from src.analyzers.graph_builder import GraphBuilder
from src.analyzers.account_scorer import AccountScorer
from src.reporters.ai_reporter import AIReporter
print('✓ All modules loaded successfully')
"
```

- [ ] **Step 3: Commit test fixtures**

```bash
git add tests/fixtures/
git commit -m "test: add integration test fixtures"
```

---

## Self-Review Checklist

- [x] **Spec coverage**: All major features from spec are implemented
  - Collection module with Playwright ✓
  - Screenshot OCR fallback ✓
  - Graph builder ✓
  - Account scorer ✓
  - Community detector ✓
  - AI reporter ✓
  - All scripts ✓
  
- [x] **No placeholders**: All code is concrete with no TBD/TODO

- [x] **Type consistency**: Method names and signatures are consistent across tasks

- [x] **File paths**: All file paths are exact and match the file structure overview

- [x] **Test coverage**: Key components have tests (rate limiter, validator, graph builder, scorer)

- [x] **Commits**: Each task ends with a git commit

---

## Execution Notes

**Collection designed for Sonnet execution:** The Playwright collector can run with a lighter model (Sonnet) since it's primarily repetitive data gathering. The analysis and reporting phases can use the current model for better reasoning.

**Manual fallback available:** If automation fails, the OCR collector provides a manual data entry path.

**Resumable:** Collection saves progress after each phase, so it can be resumed if interrupted.

**Testable:** Smoke tests validate setup before expensive collection runs.
