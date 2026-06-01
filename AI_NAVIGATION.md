# AI Navigation Guide
## Quick Context Loading for AI Agents

**Repository:** Instagram Ecosystem Analyzer  
**Purpose:** Strategic network intelligence for contemporary craft/design career development  
**Last Updated:** June 1, 2026

---

## ⚡ Quick Start (60 Second Context Load)

### What This Tool Does
Maps Instagram networks to identify **strategic career pathways** in gallery/craft/design ecosystems. Not for follower growth. Not for automation. For **professional intelligence**.

### Core Workflow
```
Target Account → Collect Engagement Data → Build Network Graph → 
Score Accounts → Detect Communities → Identify Bridge Nodes → 
Generate Strategic Reports
```

### Key Output
**Bridge nodes** (people who connect you to target ecosystem) + **Strategic pathways** (fastest routes to galleries/collectors/curators) + **Engagement plans** (tactical execution guides)

---

## 📁 Repository Structure (What to Read First)

### For Understanding Past Analyses
```
analyses/
└── ANALYSIS_INDEX.md          ← START HERE - catalog of all analyses
    └── 2026-05-30-sarah-myerscough/
        ├── executive_summary_strategic_recommendations.md  ← HIGH-LEVEL FINDINGS
        ├── strategic_pathways_analysis.md                  ← DETAILED PATHWAYS
        ├── engagement_plan_30_days.md                      ← TACTICAL EXECUTION
        └── top_100_accounts_enriched.csv                   ← ACCOUNT INTELLIGENCE
```

### For Understanding the System
```
src/
├── collectors/
│   └── playwright_collector.py    ← How data is collected (4 phases)
├── analyzers/
│   ├── graph_builder.py           ← How networks are constructed
│   ├── account_scorer.py          ← How accounts are scored (READ THIS)
│   └── community_detector.py      ← How communities are found
└── reporters/
    └── ai_reporter.py             ← How reports are generated
```

### For Configuration
```
config.json                        ← Target account, rate limits, scoring weights
```

---

## 🎯 Analysis Methodology (Core Concepts)

### Multi-Factor Account Scoring

**Formula:** `Overall Score = (0.4 × Proximity) + (0.3 × Engagement) + (0.2 × Bridge) + (0.1 × Category)`

1. **Proximity Score (40%):** How close to target in network graph
   - 1 hop = 100 points, 2 hops = 50 points, etc.
   - Penalized for reverse path (if they're far from you)

2. **Engagement Score (30%):** Bidirectional interaction strength
   - Comment frequency × weight
   - Tags, mentions, collaborations
   - Normalized to 0-100 scale

3. **Bridge Score (20%):** Betweenness centrality
   - How many shortest paths pass through this node
   - Identifies connectors between communities

4. **Category Fit (10%):** Bio keyword matching
   - Gallery, curator, collector, designer, artist categories
   - Keyword lists in `config.json`

### Graph Metrics Used

- **Degree Centrality:** Raw connection count (who's well-connected)
- **Betweenness Centrality:** Bridge importance (who connects communities)
- **Closeness Centrality:** Average distance (who's close to everyone)
- **Community Detection:** Greedy modularity (Louvain-like clustering)

### Data Collection Phases

1. **Phase 0:** Target profile metadata
2. **Phase 1:** Recent posts → commenters, likers, tagged accounts
3. **Phase 2:** Following list (often private/unavailable)
4. **Phase 3:** First-degree account profiles

**Rate Limiting:** 2-5s between requests, 30-60s pause every 20 requests

---

## 📊 Output File Types

### Automatically Generated (in `data/processed/outputs/`)
- `recommended_targets.csv` - Tiered A/B/C recommendations with scores
- `ai_summary.md` - Human-readable markdown summary
- `graph_*.json` - NetworkX graph structure
- `edges_*.csv` - Relationship list
- `accounts_*.csv` - Account metadata
- `account_scores_*.json` - Detailed scoring breakdown

### Manually Created Strategic Analysis (in `analyses/[date]-[target]/`)
- `executive_summary_strategic_recommendations.md` - **Read this first**
- `strategic_pathways_analysis.md` - Deep pathway analysis
- `engagement_plan_30_days.md` - Day-by-day tactical guide
- `top_100_accounts_enriched.csv` - Enriched with web research

---

## 🔑 Key Concepts to Understand

### Bridge Nodes
**Definition:** Accounts that connect multiple communities in the network.

**Why They Matter:** Fastest path to your target ecosystem. One introduction from a bridge node can open entire networks.

**Example:** Gallery staff member who knows collectors, other galleries, designers, and artists. Introduction from them = access to all those networks.

**How to Identify:** High betweenness centrality score + connections across communities

### Strategic Pathways
**Definition:** Sequences of relationships that lead to career objectives (gallery representation, collector access, etc.)

**Types:**
1. **Direct Path:** You → Target Gallery (requires strong portfolio + visibility)
2. **Bridge Path:** You → Bridge Node → Target (faster, warmer introduction)
3. **Platform Path:** You → Exhibition Platform → Gallery Interest (stepping stone)
4. **Commission Path:** You → Designer → Commission → Gallery Credibility (parallel channel)

### Tier System
- **Tier A:** Immediate outreach priorities (highest ROI, warmest paths)
- **Tier B:** Secondary targets (strategic but longer timeline)
- **Tier C:** Monitor only (low priority or unclear strategic value)

### Career Leverage Score
**Not** follower count. **Not** engagement rate.

**Formula:** `How likely is this person to accelerate your career through introductions, influence, or access?`

**High Career Leverage Examples:**
- Gallery staff (direct representation access)
- Interior designers (commission channel + collector intros)
- Art advisors (collector influence)
- Represented artists (peer validation + gallery intros)

**Low Career Leverage Examples:**
- Large following but no industry connections
- Generic influencers
- Adjacent industries (not craft/design focused)

---

## 📖 How to Read Analysis Reports

### Executive Summary Structure
1. **Key Finding:** The single most important discovery (usually a bridge node)
2. **Top 25 Lists:** Galleries, collectors, designers, press, platforms
3. **Strategic Pathways:** Ranked routes to objectives
4. **30-Day Plan:** Immediate actions
5. **Expected ROI:** Time investment vs. career impact

### Strategic Pathways Analysis Structure
1. **Path Overview:** Route description + probability + timeline
2. **Why It Works:** Strategic reasoning
3. **Critical Success Factors:** What must be true for this path to succeed
4. **Risk Assessment:** What could go wrong
5. **Tactical Steps:** Specific actions to take

### Engagement Plan Structure
1. **Daily Actions:** Specific posts to engage with + comment examples
2. **Weekly Milestones:** What to accomplish each week
3. **Red Flags:** What NOT to do (avoid these mistakes)
4. **Success Metrics:** How to measure progress

---

## 🚀 Common AI Agent Tasks

### Task 1: Analyze New Instagram Network
**Input:** Target account username  
**Process:**
1. Update `config.json` with new target
2. Run `python scripts/collect.py --limit 10`
3. Run `python scripts/analyze.py`
4. Run `python scripts/report.py`
5. Read outputs in `data/processed/outputs/`
6. Enrich top accounts with web research
7. Generate strategic analysis documents

**Key Files to Create:**
- `analyses/[date]-[target]/executive_summary_strategic_recommendations.md`
- `analyses/[date]-[target]/strategic_pathways_analysis.md`
- `analyses/[date]-[target]/engagement_plan_30_days.md`

### Task 2: Update Existing Analysis
**Input:** Previous analysis directory  
**Process:**
1. Re-run collection with same target
2. Compare new graph to old graph (growth, changes)
3. Identify new high-value accounts
4. Update strategic recommendations
5. Adjust engagement plan based on progress

**Key Comparisons:**
- Network size change
- New bridge nodes
- Account category shifts
- Relationship strength changes

### Task 3: Generate 90-Day Follow-Up Plan
**Input:** 30-day engagement plan + progress notes  
**Process:**
1. Review what worked in first 30 days
2. Identify which relationships progressed
3. Determine next strategic moves
4. Create month-by-month milestones
5. Adjust based on feedback/results

### Task 4: Cross-Network Analysis
**Input:** Multiple target accounts (e.g., 5 galleries)  
**Process:**
1. Collect data from all targets
2. Find overlapping accounts (who appears in multiple networks?)
3. Identify super-connectors (high betweenness across all networks)
4. Map shared communities
5. Prioritize accounts with access to multiple targets

**Output:** "Universal bridge nodes" who connect multiple target ecosystems

### Task 5: LinkedIn Integration Analysis
**Input:** LinkedIn connections CSV + Instagram network data  
**Process:**
1. Match names across platforms
2. Identify which LinkedIn connections are in Instagram ecosystem
3. Calculate "warm path score" (existing relationship + strategic value)
4. Prioritize reconnections with strategic overlay
5. Generate personalized outreach templates

**Output:** Ranked list of existing connections to reactivate strategically

---

## 🗺️ Analysis Index Quick Reference

### Latest Analysis: Sarah Myerscough Ecosystem (May 30, 2026)

**Target:** @sarah_myerscough (Contemporary craft gallery, London)  
**Network Size:** 88 accounts, 87 relationships  
**Collection Date:** May 30, 2026  
**Analysis Date:** June 1, 2026

**Key Findings:**
- **Critical Bridge:** @ingridpilkingtonwright (Gallery staff at The New Craftmaker)
- **Primary Target:** Sarah Myerscough Gallery (wood specialist, PAD/Design Miami exhibitor)
- **Commission Channel:** @nicolehollis (AD Top 100 interior designer)
- **Major Fair:** @tefaf (TEFAF Maastricht - world's premier)
- **Press:** @houseandgardenuk (Condé Nast publication)
- **Platforms:** Future Icons Selects, Cluster Crafts

**Strategic Outcome:**
- 5 pathways identified
- Bridge relationship prioritized (existing warm connection)
- 30-day tactical plan created
- Expected timeline: 6-18 months to gallery representation

**Files:**
- Executive summary: `analyses/2026-05-30-sarah-myerscough/executive_summary_strategic_recommendations.md`
- Full analysis: `analyses/2026-05-30-sarah-myerscough/strategic_pathways_analysis.md`
- Tactical plan: `analyses/2026-05-30-sarah-myerscough/engagement_plan_30_days.md`
- Account data: `analyses/2026-05-30-sarah-myerscough/top_100_accounts_enriched.csv`

---

## 💡 Pro Tips for AI Agents

### When Analyzing Networks
1. **Bridge nodes > follower count** - Always prioritize connectors over influencers
2. **Warm paths > cold outreach** - Existing relationships are 10x more valuable
3. **Gallery staff = gold** - They know everyone and control access
4. **Interior designers = revenue** - Commission channel + collector intros
5. **Platform exhibitions = stepping stones** - Easier entry point than galleries

### When Generating Strategic Recommendations
1. **Be specific** - "Contact Ingrid Pilkington-Wright this week" not "Network with galleries"
2. **Provide exact templates** - Write the actual message/comment to send
3. **Timeline everything** - Week 1, Month 3, etc. not "eventually"
4. **Rank by ROI** - Time investment vs. career impact
5. **Include red flags** - What NOT to do is as important as what to do

### When Creating Engagement Plans
1. **One action per day** - Sustainable rhythm beats bursts
2. **Authentic comments only** - Generic praise is useless
3. **Demonstrate expertise** - Comments should show craft/design knowledge
4. **Physical events matter** - Instagram alone isn't enough
5. **Patience is strategic** - 6-12 month timelines are normal for gallery representation

### Common Pitfalls to Avoid in Analysis
1. ❌ **Don't confuse followers with influence** - Small accounts can be critical bridges
2. ❌ **Don't ignore existing connections** - LinkedIn/past relationships are lowest-hanging fruit
3. ❌ **Don't recommend cold pitching galleries** - It never works
4. ❌ **Don't over-optimize for engagement rate** - It's not about likes
5. ❌ **Don't skip the enrichment step** - Auto-generated data needs manual research

---

## 🔄 Workflow Checklist for New Analysis

```
☐ Configure target in config.json
☐ Run collection scripts (collect.py)
☐ Verify data quality (check data/raw/ files)
☐ Run analysis scripts (analyze.py)
☐ Review auto-generated outputs (data/processed/outputs/)
☐ Identify top 25 accounts for enrichment
☐ Web research each account (role, company, connections)
☐ Classify accounts (gallery, curator, designer, etc.)
☐ Identify bridge nodes (high betweenness centrality)
☐ Map strategic pathways (5-7 distinct routes)
☐ Calculate ROI for each pathway
☐ Create 30-day engagement plan with specific actions
☐ Generate executive summary with top 25 lists
☐ Save all outputs to analyses/[date]-[target]/
☐ Update ANALYSIS_INDEX.md
☐ Commit to git
```

---

## 📚 Further Reading

**In This Repo:**
- `README.md` - Main documentation
- `ANALYSIS_INDEX.md` - Catalog of past analyses
- `src/analyzers/account_scorer.py` - Scoring algorithm implementation
- `config.json` - Configurable parameters

**Past Analyses (Start Here):**
- `analyses/2026-05-30-sarah-myerscough/` - Complete example analysis

**For Deep Dives:**
- NetworkX documentation (graph analysis library)
- Instagram Graph API limitations (why we use Playwright)
- Gallery representation processes (industry knowledge)
- Contemporary craft market dynamics

---

## 🆘 Quick Troubleshooting

**"How do I know which accounts are most important?"**
→ Look for high `career_leverage_score` in enriched CSV, high betweenness centrality in graph data, and accounts classified as "Gallery Staff", "Gallery Owner", or "Art Advisor"

**"What if I can't find any bridge nodes?"**
→ Network may be too sparse. Collect more data (increase --limit) or analyze a more connected target account

**"How do I handle private accounts?"**
→ Focus on public engagement data (comments, tags). Private accounts appear as nodes but with limited metadata. Prioritize researching them externally.

**"Timeline seems long (6-18 months) - can it be faster?"**
→ Only if you have existing warm relationships (bridge nodes). Cold approaches to galleries almost never work quickly. Platforms/fairs can accelerate to 3-6 months.

**"Should I automate the Instagram engagement?"**
→ **NO.** Never automate likes, comments, follows, or DMs. This is a planning tool, not an automation tool. Build authentic relationships manually.

---

**End of AI Navigation Guide**

*For humans reading this: The above guide is optimized for AI agent context loading. For traditional documentation, see README.md.*
