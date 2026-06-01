# Instagram Ecosystem Analyzer

**AI-powered network intelligence tool for strategic career development in contemporary craft, collectible design, and gallery ecosystems.**

## 🎯 Purpose

This tool maps Instagram networks around target accounts (galleries, fairs, publications) to identify:
- Strategic relationship pathways
- Bridge nodes and key connectors  
- Collector, curator, and gallery access routes
- Commission and representation opportunities
- Hidden high-value contacts

**Not a follower growth tool. Not an engagement hack. A professional intelligence system.**

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

## 🧠 AI Navigation

**For AI agents analyzing this repository:**

1. **Quick Start:** Read `AI_NAVIGATION.md` first - loads essential context
2. **Past Analyses:** Check `analyses/` directory - historical reports indexed in `ANALYSIS_INDEX.md`
3. **System Understanding:** `src/analyzers/account_scorer.py` - scoring methodology
4. **Current Config:** `config.json` - active target and parameters

## ⚠️ Ethics & Compliance

**What this tool does:**
- ✅ Collects public engagement data (comments, likes on public posts)
- ✅ Maps public relationships
- ✅ Provides strategic career intelligence
- ✅ Respects rate limits (2-5s delays, periodic pauses)

**What this tool does NOT do:**
- ❌ No automated likes, follows, comments, or DMs
- ❌ No private data collection
- ❌ No Instagram ToS violations  
- ❌ No spam or bulk outreach

**Use responsibly:** This is for strategic planning and authentic relationship building only.

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
