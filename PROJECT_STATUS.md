# Project Status
## Instagram Ecosystem Analyzer — PM Tracking Document

**Last Updated:** June 1, 2026  
**PM:** OpenCode Agent (Claude)  
**Repo:** https://github.com/EvanTenenbaum/instagram-ecosystem-analyzer

---

## Overall Roadmap

| Phase | Description | Status | Priority | Feasibility |
|-------|-------------|--------|----------|-------------|
| Phase 0 | Single-target data collection + analysis + reporting | ✅ COMPLETE | — | Done |
| Phase 1 | Multi-target cross-network analyzer | ✅ COMPLETE | — | Done |
| Phase 2 | Content & hashtag intelligence | ⏳ NOT STARTED | HIGH | 7-9/10 |
| Phase 3 | Progressive engagement strategy generator | ⏳ NOT STARTED | MEDIUM | 6-8/10 |

**Rule:** Do NOT start Phase 2 until Phase 1 outputs are validated by user. Do NOT start Phase 3 until Phase 2 is validated.

---

## Phase 0 — COMPLETE

**Deliverables:**
- ✅ `src/collectors/playwright_collector.py` — 4-phase browser automation (profile, posts/commenters, following, first-degree profiles)
- ✅ `src/collectors/screenshot_collector.py` — OCR fallback via pytesseract
- ✅ `src/collectors/base_collector.py` — Abstract base with checkpoint save/load
- ✅ `src/analyzers/graph_builder.py` — NetworkX DiGraph construction from all phases
- ✅ `src/analyzers/account_scorer.py` — Multi-factor scoring: Proximity (40%) + Engagement (30%) + Bridge (20%) + Category (10%)
- ✅ `src/analyzers/community_detector.py` — Greedy modularity community detection
- ✅ `src/reporters/ai_reporter.py` — Tiered A/B/C recommendations, CSV + markdown outputs
- ✅ `src/utils/` — rate_limiter, data_validator, session_manager
- ✅ `scripts/` — collect.py, analyze.py, report.py, run_all.py + test scripts
- ✅ `tests/` — 5 test files covering core modules
- ✅ Sarah Myerscough analysis — 88 accounts, 87 relationships, 5 pathways, complete docs

**Known Gaps in Phase 0 Code (to fix during Phase 1 work):**
- `graph_builder.py:process_following()` expects `following` as list of dicts with `username` key, but `playwright_collector.py` Phase 2 returns list of strings → potential mismatch worth fixing
- `collect_second_degree` config key is not wired up in the collector
- No `IMPLEMENTATION_PLAN.md` in repo root (the actual plan lives at `docs/superpowers/plans/2026-05-29-instagram-ecosystem-mapping.md`)

---

## Phase 1 — Multi-Target Cross-Network Analyzer (NEXT)

**Goal:** Collect data from 5-10 target accounts simultaneously, identify accounts that appear in multiple networks ("super accounts"), surface universal bridge nodes.

**Acceptance Criteria:**
- [ ] `scripts/collect_multi.py` — CLI accepts list of target accounts, runs collection for each
- [ ] `src/collectors/multi_target_collector.py` — Orchestrates sequential collection across targets (rate-limit safe)
- [ ] `src/analyzers/cross_network_analyzer.py` — Finds overlapping accounts, scores them by cross-network presence
- [ ] `outputs/super_accounts.csv` — Accounts appearing in 2+ target networks, ranked by frequency and strategic score
- [ ] `outputs/cross_network_summary.md` — Human/AI readable summary of findings
- [ ] Manual spot-check: do super accounts actually make strategic sense?
- [ ] User validation: Evan confirms Phase 1 outputs are valuable before Phase 2 begins

**Planned Target Accounts (from ANALYSIS_INDEX.md):**
1. `hostlerburrows` — Gallery (NYC/LA, Nordic/American design)
2. `nicolehollis` — Interior designer (AD Top 100, commission channel)
3. `designmiami` — Fair ecosystem
4. `padesignart` — PAD London
5. `archdigest` — AD designer network

**Test run targets (small):** `sarah_myerscough`, `hostlerburrows`, `friedmanbenda` with `--limit 3`

**Estimated effort:** 2-3 days of implementation + 1 day testing

**Blockers:**
- None currently

---

## Phase 2 — Content & Hashtag Intelligence (PENDING PHASE 1 VALIDATION)

**Goal:** Analyze what content/hashtags work in the target ecosystem, generate recommended posting strategies.

**NOT STARTING until Phase 1 validated.**

**Planned deliverables:**
- `src/analyzers/content_pattern_analyzer.py`
- Hashtag effectiveness analysis (5-7 recommended hashtag sets)
- Optimal posting time analysis
- Content mix recommendations

**Caveat:** Instagram has deprecated hashtag reach; this has limited measured impact.

---

## Phase 3 — Progressive Engagement Strategy (PENDING PHASE 2 VALIDATION)

**Goal:** Generate 6-month engagement ladder (Tier C → B → A), daily action checklists, algorithmic visibility roadmap.

**NOT STARTING until Phase 2 validated.**

---

## Analyses Queue

| Priority | Target | Type | Status |
|----------|--------|------|--------|
| ✅ Done | @sarah_myerscough | Gallery ecosystem | Complete |
| 1 | @hostlerburrows | Gallery ecosystem | Queued for Phase 1 |
| 2 | @nicolehollis | Commission pipeline | Queued for Phase 1 |
| 3 | @designmiami | Fair cross-network | Queued for Phase 1 |
| 4 | @padesignart | Fair cross-network | Queued for Phase 1 |
| 5 | @archdigest | Designer network | Queued for Phase 1 |

---

## Decisions Log

| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-06-01 | Repo wired to GitHub at EvanTenenbaum/instagram-ecosystem-analyzer | User confirmed GitHub as canonical source |
| 2026-06-01 | Phase 1 before Phase 2/3 — strict sequencing | Multi-target analysis is most feasible (10/10) and highest strategic value; build incrementally |
| 2026-06-01 | Success probability: 30% realistic, 10% optimistic | Set honest expectations; critical metrics (saves, shares) are invisible |

---

## Escalation Triggers (When to Involve Evan)

**Escalate:**
- Instagram breaks public data access (Playwright fails at scale)
- Rate limiting is so severe that collecting 5+ targets is infeasible
- Phase 1 outputs prove strategically worthless (pivot decision needed)
- Major architectural decision not covered in plan

**Don't escalate:**
- Minor implementation bugs
- Choosing between equivalent data structures
- Output formatting choices
- Typical rate-limiting (just wait and retry)

---

## Success Probability Reminders

| Scenario | Probability | Outcome |
|----------|-------------|---------|
| Pessimistic | 60% | 20-30% reach growth, 100-200 followers, 0-1 opportunities |
| Realistic | 30% | 50-100% reach growth, 300-500 followers, 1 exhibition |
| Optimistic | 10% | 150-300% reach growth, 800-1500 followers, representation |

**Critical reminder:** Saves, shares, watch time — the metrics that matter most to the algorithm — are invisible to this tool. Content quality is the ultimate success factor, not strategy.
