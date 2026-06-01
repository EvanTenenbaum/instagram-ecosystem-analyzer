# Quick Start Guide
## Get Running in 5 Minutes

### For Humans

```bash
# 1. Clone and setup
git clone https://github.com/EvanTenenbaum/instagram-ecosystem-analyzer.git
cd instagram-ecosystem-analyzer
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium

# 2. Configure
# Edit config.json - change "target_account" to your target Instagram username

# 3. Run
python scripts/run_all.py
# Follow prompts if Instagram asks for login

# 4. View results
open data/processed/outputs/ai_summary.md
```

### For AI Agents

```
1. Read AI_NAVIGATION.md (context loading)
2. Read analyses/ANALYSIS_INDEX.md (past analyses)
3. For new analysis:
   - Update config.json target_account
   - Run: python scripts/collect.py --limit 10
   - Run: python scripts/analyze.py  
   - Run: python scripts/report.py
   - Read: data/processed/outputs/ for auto-generated results
   - Enrich: Web research top 25 accounts
   - Generate: Strategic analysis documents
   - Save: To analyses/YYYY-MM-DD-[target]/
```

### What You Get

**Automatic Outputs:**
- `recommended_targets.csv` - Top 50 accounts ranked by strategic value
- `ai_summary.md` - Network overview and recommendations
- Graph data (JSON/CSV) for further analysis

**After Manual Enrichment:**
- Executive summary with top 25 lists (galleries, collectors, designers, etc.)
- Strategic pathway analysis (5-7 routes to your objectives)
- 30-day tactical engagement plan (specific daily actions)
- Account intelligence report (career leverage scores + recommended actions)

### Key Files to Understand

1. **AI_NAVIGATION.md** - Read this first (AI agents)
2. **README.md** - Full documentation
3. **config.json** - Configure target and parameters
4. **analyses/ANALYSIS_INDEX.md** - Browse past analyses

### Example: Analyze a Gallery's Network

```bash
# Target: Sarah Myerscough Gallery
# Objective: Find paths to gallery representation

# 1. Set target
# config.json: "target_account": "sarah_myerscough"

# 2. Collect data (30-60 min)
python scripts/collect.py --limit 10

# 3. Analyze (< 1 min)
python scripts/analyze.py

# 4. Generate report (< 1 min)  
python scripts/report.py

# 5. Review
cat data/processed/outputs/ai_summary.md
```

**Result:** Network map with bridge nodes, gallery connections, collector access routes, and strategic recommendations.

### What NOT to Do

- ❌ Don't automate engagement (likes, comments, follows)
- ❌ Don't use for spam or mass outreach
- ❌ Don't collect private/auth-required data
- ❌ Don't violate Instagram Terms of Service

### Need Help?

- **Documentation:** README.md
- **Past analyses:** analyses/ directory  
- **AI context:** AI_NAVIGATION.md
- **Issues:** GitHub issues

---

**Ready to dive deeper?** Read AI_NAVIGATION.md for comprehensive AI agent guide.
