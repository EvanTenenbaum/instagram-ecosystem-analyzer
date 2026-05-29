# Instagram Ecosystem Mapping Tool - Design Specification

**Date:** 2026-05-29  
**Target:** @sarah_myerscough Instagram account  
**Purpose:** Map Instagram ecosystem to identify galleries, curators, collectors, artists, and bridge nodes for strategic engagement planning

## Executive Summary

This tool collects publicly visible Instagram data, builds a network graph, scores accounts by engagement relevance, and outputs structured data optimized for AI analysis. The tool is designed to:

- Start with conservative, unauthenticated data collection
- Gracefully handle rate limits and authentication walls
- Support manual data injection via screenshot OCR
- Analyze two degrees of separation (target → first degree → top 50 second degree)
- Output machine-readable structured data (CSV, JSON) for downstream AI analysis
- Execute data collection with Sonnet model (lighter, cost-effective for repetitive tasks)

## Project Goals

### Primary Goals
1. Identify high-value accounts in Sarah Myerscough's Instagram ecosystem
2. Map relationships and interaction patterns
3. Find bridge accounts that connect different communities
4. Classify accounts by type (gallery, artist, curator, collector, etc.)
5. Generate actionable engagement recommendations

### Non-Goals
- Automated engagement (likes, follows, comments, DMs)
- Private account data collection
- Real-time monitoring or continuous scraping
- Authentication bypass or anti-detection evasion

## User Requirements

**Compliance Requirements:**
- No login bypass or session token theft
- No private data collection
- No automated engagement
- Conservative pacing (2-5 seconds between requests)
- Respect rate limits with exponential backoff
- Pause if CAPTCHA or anti-bot warnings appear

**Execution Requirements:**
- Hybrid authentication: start without login, prompt if needed
- Conservative rate limiting for unattended execution
- Screenshot OCR fallback for manual data injection
- Two-degree network analysis (target + first degree + top 50 second degree)
- Output optimized for AI consumption (structured data, not visualizations)

## Architecture

### Design Approach: Modular Pipeline

The system is split into three independent modules with clear data contracts:

1. **Collection Module** - Browser automation and manual data collection
2. **Analysis Module** - Graph construction, scoring, and ranking
3. **Reporting Module** - Generate AI-consumable structured outputs

**Key Architectural Decisions:**

- **Independence:** Each module can run separately. Analysis can process partial/manual data even if collection fails.
- **Resumability:** Collection saves progress incrementally. Can resume from last checkpoint.
- **Reusability:** Analysis module works for any Instagram account, not just Sarah Myerscough.
- **Testability:** Each module has clear inputs/outputs and can be tested in isolation.

### Project Structure

```
~/code/instagram-ecosystem-tool/
├── README.md                          # Setup and usage instructions
├── requirements.txt                   # Python dependencies
├── config.json                        # Configuration (target account, pacing, limits)
│
├── src/
│   ├── collectors/
│   │   ├── __init__.py
│   │   ├── base_collector.py         # Abstract collector interface
│   │   ├── playwright_collector.py   # Browser automation collection
│   │   └── screenshot_collector.py   # OCR-based manual fallback
│   │
│   ├── analyzers/
│   │   ├── __init__.py
│   │   ├── graph_builder.py          # Build network graph from collected data
│   │   ├── account_scorer.py         # Score and rank accounts
│   │   └── community_detector.py     # Find clusters and bridge nodes
│   │
│   ├── reporters/
│   │   ├── __init__.py
│   │   └── ai_reporter.py            # Generate AI-consumable outputs
│   │
│   └── utils/
│       ├── __init__.py
│       ├── rate_limiter.py           # Pacing and backoff logic
│       ├── data_validator.py         # Validate collected data
│       └── session_manager.py        # Handle browser sessions and auth state
│
├── scripts/
│   ├── collect.py                    # Run data collection
│   ├── analyze.py                    # Run graph analysis
│   ├── report.py                     # Generate final report
│   ├── run_all.py                    # Orchestrator script
│   ├── test_connection.py            # Smoke test - verify Instagram accessible
│   ├── test_playwright.py            # Smoke test - verify browser automation
│   ├── test_target_account.py        # Smoke test - verify target account accessible
│   ├── test_ocr.py                   # Test OCR accuracy
│   └── validate_output.py            # Validate output file formats
│
├── tests/
│   ├── __init__.py
│   ├── test_graph_builder.py
│   ├── test_account_scorer.py
│   ├── test_full_pipeline.py
│   └── fixtures/
│       └── sample_instagram_data.json
│
├── data/
│   ├── raw/                          # Raw collected data (JSON, timestamped)
│   ├── manual/                       # Manual inputs (screenshots, CSV)
│   │   └── screenshots/              # Drop screenshots here for OCR
│   └── processed/                    # Normalized, merged data
│
├── outputs/
│   ├── accounts.csv                  # All discovered accounts
│   ├── relationships.csv             # Edge list for graph
│   ├── scores.json                   # Account scores and rankings
│   ├── graph_metrics.json            # Network analysis metrics
│   ├── recommended_targets.csv       # Top accounts to engage with
│   └── ai_summary.md                 # Context summary for AI analysis
│
├── logs/
│   ├── collection_{timestamp}.log
│   ├── analysis_{timestamp}.log
│   └── errors.log
│
└── docs/
    └── superpowers/
        └── specs/
            └── 2026-05-29-instagram-ecosystem-mapping-design.md
```

## Core Components

### Collection Module

#### `base_collector.py`
Abstract interface defining collection contract:
- `collect(target_account: str) -> dict`
- `save_progress(phase: str, data: dict) -> None`
- `resume_from_checkpoint() -> Optional[dict]`

#### `playwright_collector.py`
Main browser automation collector.

**Responsibilities:**
- Launch headless Chromium browser via Playwright
- Navigate to Instagram.com
- Start collection without authentication
- Detect authentication walls and pause for user login
- Collect data in phases (see below)
- Implement conservative rate limiting (2-5 second delays with jitter)
- Save progress after each phase
- Detect and handle rate limiting/CAPTCHA

**Collection Phases:**

1. **Phase 0: Target Profile**
   - Navigate to `instagram.com/@sarah_myerscough`
   - Extract: username, display name, bio, external URL, follower count, following count, post count, verification status
   - Save to: `data/raw/phase0_target_profile_{timestamp}.json`

2. **Phase 1: Recent Posts**
   - Scroll through recent posts (target: 20-50 posts)
   - For each post extract:
     - Post URL
     - Timestamp (if visible)
     - Caption text
     - Tagged accounts (`@username` in tags)
     - Collaborator accounts (if marked)
     - Top commenters (visible without expanding)
     - Whether target replied to any commenters
   - Save to: `data/raw/phase1_posts_{timestamp}.json`

3. **Phase 2: Following List (First Degree)**
   - Attempt to access following list
   - If blocked by login wall → pause and prompt user
   - If accessible → collect usernames
   - Save to: `data/raw/phase2_following_{timestamp}.json`

4. **Phase 3: First Degree Account Details**
   - For each discovered account (following + commenters + tagged + mentioned)
   - Visit profile and extract: username, display name, bio, follower count, following count, category hints
   - Deduplicate by username
   - Save to: `data/raw/phase3_first_degree_accounts_{timestamp}.json`

5. **Phase 4: Second Degree Analysis (Top 50 Only)**
   - Load scoring from previous analysis run (if available) or use heuristic (frequent commenters, tagged, replied-to)
   - Select top 50 first-degree accounts by engagement
   - For each, collect: who they follow (first 100), recent interactions
   - Save to: `data/raw/phase4_second_degree_{timestamp}.json`

**Rate Limiting Strategy:**
- 2-5 second random delay between each request
- Use `time.sleep(random.uniform(2.0, 5.0))`
- After every 20 requests, take a 30-second break
- If HTTP 429 or slow response (>10s) detected → pause 60 seconds, retry once
- If CAPTCHA detected → save progress, exit with clear message

**Authentication Handling:**
- Start without authentication
- Track which data points are accessible
- If login wall detected (e.g., "Log in to see following"):
  - Pause collection
  - Print message: "Login required to access [following list]. Options: (1) Continue without this data, (2) Press Enter after manually logging in to Instagram in the browser window."
  - Wait for user input
  - If user logs in → resume collection, set `authenticated: true` flag
  - If user skips → mark data as incomplete, continue

#### `screenshot_collector.py`
OCR-based fallback for manual data injection.

**Responsibilities:**
- Monitor `data/manual/screenshots/` directory
- For each screenshot:
  - Run OCR using pytesseract
  - Detect Instagram username patterns (`@[a-zA-Z0-9._]+`)
  - Extract visible text (bios, captions)
  - Generate confidence scores
- Output same JSON format as `playwright_collector.py`
- Flag low-confidence extractions for manual review

**OCR Strategy:**
- Preprocess images: grayscale, increase contrast, denoise
- Run tesseract with `--oem 3 --psm 6` (assume uniform text block)
- Username pattern matching: `r'@([a-zA-Z0-9._]+)'`
- Confidence threshold: 50% minimum (below this, flag for review)
- Save to: `data/raw/screenshot_ocr_{timestamp}.json`

#### `rate_limiter.py`
Centralized rate limiting logic.

**Responsibilities:**
- Enforce delays between requests
- Detect rate limit signals (429, CAPTCHA, slow responses)
- Implement exponential backoff
- Log all delays for transparency

**Implementation:**
- `wait()` - Enforce 2-5 second delay
- `on_rate_limit()` - Handle 429 or CAPTCHA, pause 60s
- `on_failure(attempt: int)` - Exponential backoff: 2^attempt seconds

#### `session_manager.py`
Browser session and authentication state management.

**Responsibilities:**
- Launch Playwright browser
- Manage browser context and cookies
- Detect authentication state
- Save/load session cookies for resume
- Detect login walls and prompt user

### Analysis Module

#### `graph_builder.py`
Constructs network graph from collected data.

**Responsibilities:**
- Load all JSON files from `data/raw/` and `data/manual/`
- Merge data by username (deduplicate)
- Resolve conflicts: most recent timestamp wins, manual data takes precedence
- Build directed graph using networkx
- Assign edge weights based on relationship type
- Output graph to `data/processed/graph.json` and edge list to `data/processed/relationships.csv`

**Edge Weights:**
- `target_follows`: 10
- `target_replies_to`: 9
- `target_tags`: 8
- `collaborator`: 10
- `repeated_commenter`: 7 + (frequency_bonus: +2 per additional appearance)
- `mentioned_in_caption`: 6
- `appears_in_multiple_posts`: +2 per additional post

**Graph Schema:**
- Nodes: Instagram accounts (username as ID)
- Node attributes: `display_name`, `bio`, `follower_count`, `following_count`, `category`, `degree` (0=target, 1=first, 2=second)
- Edges: Directed relationships with `type` and `weight`

#### `account_scorer.py`
Calculates engagement scores and rankings.

**Responsibilities:**
- Load graph from `graph_builder.py`
- Calculate per-account scores:
  - **Proximity score** (0-100): How directly connected to target. Inverse of shortest path distance, weighted by edge weights.
  - **Engagement score** (0-100): Frequency and strength of interactions. Sum of all edge weights to/from target.
  - **Bridge score** (0-100): Betweenness centrality. How often account appears on shortest paths between other accounts.
  - **Category confidence** (0.0-1.0): ML-based classification using bio keywords and interaction patterns.
- Generate overall score: `0.4 * proximity + 0.3 * engagement + 0.2 * bridge + 0.1 * category_fit`
- Output ranked lists by dimension
- Save to `outputs/scores.json`

**Category Classification:**
Keyword-based heuristic:
- Gallery: "gallery", "art space", "exhibitions", "representing"
- Curator: "curator", "curating", "curatorial"
- Collector: "collector", "collecting", "collection"
- Artist (wood): "wood", "woodturning", "woodwork", "carving", "sculptor"
- Artist (craft): "craft", "maker", "artisan", "handmade"
- Designer (furniture): "furniture", "design", "designer", "sculptural furniture"
- Institution: "museum", "foundation", "institute", "trust"
- Fair: "fair", "art fair", "design week"
- Journalist: "writer", "journalist", "editor", "publication"
- Unknown: default if no keywords match

#### `community_detector.py`
Identifies clusters and bridge nodes.

**Responsibilities:**
- Use Louvain community detection algorithm (networkx)
- Find clusters of densely connected accounts
- Identify bridge accounts (high betweenness centrality + connect multiple clusters)
- Label clusters by dominant category
- Save to `outputs/graph_metrics.json`

**Output:**
- List of communities with member accounts
- Bridge accounts with cluster connections
- Community metadata (size, density, dominant category)

### Reporting Module

#### `ai_reporter.py`
Generates AI-consumable outputs.

**Responsibilities:**
- Load processed data and scores
- Generate structured outputs:
  - `outputs/accounts.csv` - All discovered accounts with metadata
  - `outputs/relationships.csv` - Edge list
  - `outputs/scores.json` - Ranked accounts with evidence
  - `outputs/recommended_targets.csv` - Top 50 prioritized accounts
  - `outputs/graph_metrics.json` - Network statistics
  - `outputs/ai_summary.md` - High-level context for AI

**CSV Schemas:**

`accounts.csv`:
```
username,display_name,bio,follower_count,following_count,category,predicted_category_confidence,source_list,first_seen,degree,overall_score,proximity_score,engagement_score,bridge_score
```

`relationships.csv`:
```
source,target,relationship_type,weight,evidence_count,last_seen
```

`recommended_targets.csv`:
```
username,display_name,category,overall_score,engagement_score,recommendation_tier,evidence_summary,engagement_strategy
```

**Recommendation Tiers:**
- **Tier A (Top 15)**: Highest priority. Direct connections to target with strong engagement signals. Likely galleries representing similar artists or frequent collaborators.
- **Tier B (Next 20)**: Secondary priority. Strong bridge accounts or category matches. Useful for expanding reach.
- **Tier C (Next 15)**: Monitor only. Weaker signals but worth tracking for pattern changes.

**Engagement Strategy Generation:**
For each recommended account, suggest:
- Comment strategy: What kind of comments would be appropriate (based on their content type)
- Posting strategy: Whether to tag them, mention them, or seek collaboration
- Risk assessment: Public vs. private account, engagement history with target

`ai_summary.md` format:
```markdown
# Instagram Ecosystem Analysis: @sarah_myerscough

**Collection Date:** 2026-05-29
**Accounts Analyzed:** 250 (50 first degree, 200 second degree)
**Authentication Used:** Yes/No
**Data Completeness:** 85% (following list accessible, comments partial)

## Key Findings
- Most common account type: Gallery (40%)
- Strongest engagement cluster: Contemporary wood sculptors (25 accounts)
- Top bridge accounts: @username1, @username2

## Top 15 Recommendations (Tier A)
[Table with username, category, score, evidence]

## Network Structure
- Average path length from target: 1.8
- Clustering coefficient: 0.45
- Number of communities: 5

## Data Limitations
- Could not access: Follower list (login wall)
- Partial data: Comments on posts older than 6 months
- Manual data sources: 3 screenshots (usernames from external research)
```

## Data Flow

### Phase 1: Collection → Raw Data
```
playwright_collector.py
  ↓
data/raw/phase0_target_profile_{timestamp}.json
data/raw/phase1_posts_{timestamp}.json
data/raw/phase2_following_{timestamp}.json
data/raw/phase3_first_degree_accounts_{timestamp}.json
data/raw/phase4_second_degree_{timestamp}.json
```

Optional manual augmentation:
```
User drops screenshots into data/manual/screenshots/
  ↓
screenshot_collector.py
  ↓
data/raw/screenshot_ocr_{timestamp}.json
```

### Phase 2: Analysis → Processed Data
```
graph_builder.py reads data/raw/*.json
  ↓
data/processed/graph.json
data/processed/relationships.csv
data/processed/accounts.csv

account_scorer.py reads processed data
  ↓
outputs/scores.json

community_detector.py reads graph
  ↓
outputs/graph_metrics.json
```

### Phase 3: Reporting → AI-Consumable Outputs
```
ai_reporter.py reads outputs/*.json + data/processed/*.csv
  ↓
outputs/recommended_targets.csv
outputs/ai_summary.md
```

### Data Format Specifications

#### Raw Collection JSON (`data/raw/`)

**phase0_target_profile_{timestamp}.json:**
```json
{
  "collection_metadata": {
    "source": "playwright",
    "timestamp": "2026-05-29T14:30:00Z",
    "target_account": "sarah_myerscough",
    "phase": "target_profile",
    "authenticated": false
  },
  "target_profile": {
    "username": "sarah_myerscough",
    "display_name": "Sarah Myerscough",
    "bio": "Contemporary Design Gallery | London | Representing exceptional makers",
    "external_url": "https://sarahmyerscough.com",
    "follower_count": 12500,
    "following_count": 850,
    "post_count": 420,
    "is_verified": false,
    "is_private": false,
    "profile_image_url": "https://..."
  }
}
```

**phase1_posts_{timestamp}.json:**
```json
{
  "collection_metadata": { ... },
  "posts": [
    {
      "url": "https://instagram.com/p/ABC123",
      "timestamp": "2026-05-20T10:00:00Z",
      "caption": "Excited to share new work by @artist_username...",
      "tagged_accounts": ["artist_username", "another_artist"],
      "collaborators": ["collab_username"],
      "commenters": [
        {
          "username": "commenter1",
          "comment_count": 3,
          "target_replied": true
        },
        {
          "username": "commenter2",
          "comment_count": 1,
          "target_replied": false
        }
      ],
      "like_count": 450,
      "comment_count": 28
    }
  ]
}
```

**phase2_following_{timestamp}.json:**
```json
{
  "collection_metadata": { ... },
  "following": [
    "username1",
    "username2",
    "username3"
  ],
  "collection_status": "complete|partial|failed",
  "error_message": "Login required" or null
}
```

**phase3_first_degree_accounts_{timestamp}.json:**
```json
{
  "collection_metadata": { ... },
  "discovered_accounts": {
    "username1": {
      "display_name": "Artist Name",
      "bio": "Wood sculptor | London",
      "follower_count": 5000,
      "following_count": 300,
      "post_count": 150,
      "is_verified": false,
      "is_private": false,
      "category_hints": ["wood", "sculptor"],
      "source": ["following", "tagged"],
      "first_seen": "2026-05-29T15:00:00Z"
    }
  }
}
```

**phase4_second_degree_{timestamp}.json:**
```json
{
  "collection_metadata": {
    "phase": "second_degree",
    "selected_accounts": ["username1", "username2", ...],
    "selection_criteria": "top_50_by_engagement"
  },
  "second_degree_accounts": {
    "username1": {
      "following_sample": ["user_a", "user_b"],
      "recent_interactions": [
        {
          "type": "comment",
          "target": "user_c",
          "timestamp": "2026-05-25T12:00:00Z"
        }
      ]
    }
  }
}
```

## Error Handling & Resilience

### Collection Error Scenarios

#### Rate Limiting
**Detection:**
- HTTP 429 response
- CAPTCHA challenge page
- Slow responses (>10 seconds)
- Multiple consecutive failures (3+)

**Response:**
- 429 → pause 60 seconds, retry once, then abort phase if still failing
- CAPTCHA → save progress, exit with message: "CAPTCHA detected. Run `scripts/collect.py --resume` after challenge clears."
- Slow responses → increase delays by 2x temporarily
- 3+ failures → abort phase, save partial data, log what was collected

#### Authentication Walls
**Detection:**
- Page contains "Log in to see more" or similar
- Following/follower list not accessible
- Comment threads truncated

**Response:**
- Pause collection
- Display message: "Login required to access [specific data]. Continue without login (limited data) or press Enter after manually logging in?"
- Wait for user input
- If user logs in → set `authenticated: true`, resume
- If user skips → mark data as incomplete, continue with available data

#### Partial Data
**Strategy:**
- Save progress after each phase (never lose all data on crash)
- Resume script: `collect.py --resume` checks `data/raw/` for latest checkpoint
- Missing fields marked as `null` with reason: `"not_accessible"`, `"rate_limited"`, `"auth_required"`
- Generate completeness report at end: "85% complete (following list accessible, comments partial)"

#### Network Errors
- Connection timeout → retry 3 times with exponential backoff (2s, 4s, 8s)
- DNS failure → abort with clear error
- Instagram unavailable (503) → pause 5 minutes, retry once

### OCR Fallback Error Handling

**Low Confidence Extractions:**
- If OCR confidence < 50% → skip screenshot, log warning
- Generate `data/manual/review_needed.txt` listing suspicious extractions
- User can manually correct and re-run

**No Usernames Detected:**
- If screenshot yields zero usernames → prompt user to check quality
- Suggest: higher resolution, better lighting, crop to relevant area

**Invalid Username Patterns:**
- Filter out false positives (emails, URLs that aren't Instagram)
- Validate username format: `^[a-zA-Z0-9._]{1,30}$`

### Analysis Error Handling

**Missing Critical Data:**
- If no first-degree accounts found → abort analysis, report collection issue
- If < 20 first-degree accounts → warn but continue (might need manual augmentation)
- If target profile missing → abort, cannot proceed

**Graph Construction Failures:**
- Disconnected nodes → include in graph, mark as isolated
- Invalid edge weights → log warning, use default weight (5)
- Circular dependencies → normal for social graphs, no special handling

**Scoring Failures:**
- If betweenness centrality fails (disconnected graph) → skip bridge score
- If category classification fails → mark as "unknown" with 0.0 confidence
- If overall score cannot be calculated → output unranked list with warning

**Output Generation:**
- If outputs directory write fails → retry once, then log error and exit
- If CSV generation fails → output JSON only
- Always produce *some* output, even if incomplete

### Logging Strategy

**Log Levels:**
- `DEBUG`: Every request, every delay, every data point
- `INFO`: Phase completions, major checkpoints, user prompts
- `WARNING`: Rate limits, partial data, missing fields
- `ERROR`: Failures, crashes, data corruption

**Log Files:**
- `logs/collection_{timestamp}.log` - detailed collection trace
- `logs/analysis_{timestamp}.log` - graph building and scoring
- `logs/errors.log` - all ERROR-level messages across runs

**Console Output:**
- Progress bars for long operations (using `tqdm`)
- High-level status: "Phase 1: Collecting posts... 15/50"
- Errors and warnings
- End-of-phase summary: "Phase 1 complete: 45 posts collected, 3 failed (rate limited)"

## Testing Strategy

### Smoke Tests (Pre-Flight Checks)

**`scripts/test_connection.py`:**
- Verify Instagram.com is accessible
- Check network connectivity
- Verify no VPN/proxy issues
- Exit code: 0 (success) or 1 (failure)

**`scripts/test_playwright.py`:**
- Launch Playwright browser
- Navigate to Instagram
- Verify page loads
- Clean up browser process
- Exit code: 0 (success) or 1 (failure)

**`scripts/test_target_account.py`:**
- Navigate to @sarah_myerscough
- Verify account exists and is public
- Extract basic profile data
- Report accessibility
- Exit code: 0 (success) or 1 (failure)

### Collection Testing

**Dry Run Mode:**
- `collect.py --dry-run`
- Simulates collection without making requests
- Shows estimated time, disk space, request count
- Validates config.json

**Sample Collection:**
- `collect.py --limit 5`
- Collects only 5 posts/accounts
- Tests rate limiting logic
- Verifies data format
- Quick feedback loop (< 2 minutes)

### OCR Testing

**`scripts/test_ocr.py`:**
- Run OCR on `data/manual/screenshots/test_samples/`
- Compare extracted usernames to known ground truth
- Report accuracy and confidence scores
- Flag low-confidence extractions

**Test Samples:**
Include example screenshots in `data/manual/screenshots/test_samples/`:
- `following_list.png` - List of usernames
- `post_comments.png` - Comment thread
- `tagged_accounts.png` - Tagged accounts overlay

### Analysis Testing

**Unit Tests:**
- `tests/test_graph_builder.py` - Build graph from synthetic data
- `tests/test_account_scorer.py` - Verify scoring calculations
- `tests/test_community_detector.py` - Test cluster detection
- Run with: `pytest tests/`

**Integration Test:**
- `tests/test_full_pipeline.py` - End-to-end with fixture data
- Uses `tests/fixtures/sample_instagram_data.json`
- Verifies output format matches spec
- Checks for required fields

**Data Validation:**
- `scripts/validate_output.py`
- Checks output files exist and are well-formed
- Verifies CSV schemas
- Validates JSON structure
- Reports missing fields or malformed data

### Execution Testing Plan

**Phase 1: Setup & Smoke Tests (5 minutes)**
1. Install dependencies: `pip install -r requirements.txt`
2. Run smoke tests: `pytest tests/test_*.py`
3. Run `scripts/test_connection.py`
4. Run `scripts/test_playwright.py`
5. Run `scripts/test_target_account.py`

**Phase 2: Sample Collection (5 minutes)**
1. Run `collect.py --limit 5`
2. Review `logs/collection_{timestamp}.log`
3. Check `data/raw/` for output files
4. Verify data format

**Phase 3: First Full Collection (30-60 minutes)**
1. Run `collect.py` (no auth, first degree only)
2. Monitor progress
3. Review completeness report
4. Check for rate limiting issues

**Phase 4: First Analysis (2 minutes)**
1. Run `analyze.py`
2. Review `outputs/scores.json`
3. Manually review top 50 accounts - do they seem relevant?
4. Check `outputs/ai_summary.md` for sanity

**Phase 5: Second Degree Collection (60-120 minutes)**
1. Run `collect.py --second-degree`
2. Higher volume, more risk of rate limits
3. Monitor closely for first 20 requests
4. Review logs for issues

**Phase 6: Full Analysis & Reporting (5 minutes)**
1. Run `analyze.py` with full dataset
2. Run `report.py`
3. Review all outputs for completeness
4. Validate with `scripts/validate_output.py`

**Phase 7: OCR Fallback Test (10 minutes)**
1. Take screenshots of Instagram pages
2. Drop into `data/manual/screenshots/`
3. Run `screenshot_collector.py`
4. Check OCR accuracy
5. Merge with automated data: `analyze.py --include-manual`
6. Verify integration worked

## Configuration

`config.json` - Central configuration file
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

## Dependencies

`requirements.txt`:
```
playwright>=1.40.0
networkx>=3.0
pandas>=2.0.0
pytesseract>=0.3.10
Pillow>=10.0.0
numpy>=1.24.0
tqdm>=4.65.0
pytest>=7.4.0
```

Additional system dependencies:
- Tesseract OCR: `brew install tesseract` (macOS) or `apt-get install tesseract-ocr` (Linux)
- Playwright browsers: `playwright install chromium`

## Risks & Limitations

### Known Risks

1. **Rate Limiting:** Instagram may still rate limit even with conservative pacing. Mitigation: Save progress frequently, resume capability.

2. **Authentication Required:** Some data (following list, full comment threads) may require login. Mitigation: Hybrid approach with user-controlled authentication.

3. **Data Accessibility:** Private accounts cannot be analyzed. Mitigation: Skip private accounts, focus on public ecosystem.

4. **Account Flagging:** Repeated collection runs could flag the user's Instagram account. Mitigation: Conservative pacing, avoid running multiple times per day, clear user warnings.

5. **Instagram UI Changes:** Playwright relies on page structure. If Instagram redesigns, selectors break. Mitigation: Modular design allows easy selector updates.

6. **OCR Accuracy:** Screenshot OCR may miss usernames or extract false positives. Mitigation: Confidence thresholding, manual review mode.

### Data Limitations

1. **Temporal Snapshot:** Data represents a point in time. Relationships change.
2. **Incomplete View:** Cannot see DMs, private comments, or interactions outside Instagram.
3. **Sample Bias:** Only captures visible public interactions, may miss important private connections.
4. **Second Degree Limited:** Only analyzes top 50 accounts (not all first-degree connections), may miss important bridge nodes.

### Ethical Considerations

1. **Public Data Only:** Tool only collects publicly visible data, respects privacy settings.
2. **No Automated Engagement:** Tool is read-only, does not interact with accounts.
3. **User Responsibility:** User must comply with Instagram Terms of Service. Tool provides warnings but user bears responsibility.
4. **Respectful Use:** Intended for research and strategic planning, not harassment or spam.

## Success Criteria

### Minimum Viable Output
- At least 30 first-degree accounts discovered
- At least 50% data completeness (some fields may be missing due to auth)
- Valid graph structure with weighted edges
- Ranked account list with scores
- AI-consumable CSV and JSON outputs

### Ideal Output
- 50+ first-degree accounts
- 150+ second-degree accounts
- 80%+ data completeness
- Clear community clusters identified
- Top 15 Tier A recommendations with evidence
- Actionable engagement strategies per account

### Quality Metrics
- **Data Quality:** <10% null values in critical fields (username, bio, follower_count)
- **Graph Connectivity:** <5% isolated nodes (accounts with no relationships)
- **Scoring Validity:** Top 20 accounts manually reviewed and confirmed relevant
- **Performance:** Full collection completes in <2 hours
- **Reliability:** Runs successfully without crashes or data corruption

## Future Enhancements (Out of Scope)

1. **Real-Time Monitoring:** Track changes over time, alert on new connections
2. **Engagement Automation:** Automated commenting/liking (requires separate ethical review)
3. **Multi-Account Analysis:** Compare multiple target accounts
4. **Machine Learning:** Train classifier on user feedback to improve category detection
5. **Interactive Dashboard:** Web UI for exploring graph and rankings
6. **Integration with CRM:** Export to contact management tools

## Appendix: Example Workflow

### Happy Path Scenario

**Step 1: Setup**
```bash
cd ~/code/instagram-ecosystem-tool
pip install -r requirements.txt
playwright install chromium
```

**Step 2: Run Smoke Tests**
```bash
python scripts/test_connection.py
python scripts/test_playwright.py
python scripts/test_target_account.py
```

**Step 3: Sample Collection**
```bash
python scripts/collect.py --limit 5
# Review logs/collection_*.log
# Check data/raw/ for output
```

**Step 4: First Collection (Unauthenticated)**
```bash
python scripts/collect.py
# Takes 30-60 minutes
# May pause for authentication prompt
# If prompted: manually log into Instagram in browser, press Enter
```

**Step 5: Analyze First Degree**
```bash
python scripts/analyze.py
# Review outputs/scores.json
# Manually check top 20 accounts - do they make sense?
```

**Step 6: Second Degree Collection**
```bash
python scripts/collect.py --second-degree
# Takes 60-120 minutes
# Higher volume, watch for rate limits
```

**Step 7: Full Analysis & Report**
```bash
python scripts/analyze.py --full
python scripts/report.py
# Review all outputs in outputs/
```

**Step 8: Feed to AI**
```bash
# Copy outputs/ directory to AI analysis tool
# AI ingests: accounts.csv, relationships.csv, scores.json, ai_summary.md
```

### Manual Augmentation Scenario

**If collection fails or hits walls:**

**Step 1: Take Screenshots**
- Manually browse Instagram on desktop
- Screenshot following list, commenters, tagged accounts
- Save to `data/manual/screenshots/`

**Step 2: Run OCR**
```bash
python scripts/screenshot_collector.py
# Check data/raw/screenshot_ocr_*.json
```

**Step 3: Re-run Analysis with Manual Data**
```bash
python scripts/analyze.py --include-manual
# Merges automated + manual data
```

**Step 4: Validate Output**
```bash
python scripts/validate_output.py
# Checks completeness and format
```

## Sign-Off

This design specification defines a modular Instagram ecosystem mapping tool with:
- Clear separation between collection, analysis, and reporting
- Hybrid authentication with user control
- Conservative rate limiting for safe execution
- OCR fallback for manual data injection
- Two-degree network analysis
- AI-optimized structured outputs

**Next Steps:**
1. User reviews and approves this spec
2. Create detailed implementation plan (via `writing-plans` skill)
3. Implement collection module
4. Implement analysis module
5. Implement reporting module
6. Integration testing
7. Full workflow execution

**Execution Model:**
- Data collection scripts designed for Sonnet execution (lighter model, cost-effective)
- Analysis and reporting can use current model
- User maintains control over authentication and rate limiting decisions
