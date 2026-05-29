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
