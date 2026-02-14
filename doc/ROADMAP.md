# nanobot-auto Roadmap

> **Date:** 2025-02-14
> **Basis:** TEP v2.0 crystallization results (RESEARCH_FRAMEWORK.md)

---

## Where We Are Now

### Current State: A Working Toy ⚙️

nanobot-auto is a **functional prototype** that runs the daily Sense→Effect→Gate cycle.
It can discover issues in its own logs, delegate fixes to Codex, and auto-merge passing PRs.

**What works:**
- ✅ Three-component pipeline (log-miner / auto-dev / auto-merge) runs daily via cron
- ✅ Multi-channel notifications (Feishu, Telegram, etc.)
- ✅ Isolated development (/tmp workspace, never modifies running code directly)
- ✅ Safety guardrails (CONSTITUTION.md, CI gate, run.sh restart wrapper)
- ✅ GitHub integration (Issues, PRs, CI checks)

**What's missing:**
- ❌ No Knowledge layer — system is memoryless across cycles
- ❌ No quantitative self-evaluation — no way to know if it's getting better or worse
- ❌ No theoretical grounding — no framework to reason about the system's behavior
- ❌ No experimental evidence — claims are untested
- ❌ Fixed cron only — no event-driven or cascaded triggering
- ❌ No structured Issue format — analysis and plan are mixed in free-form text

### Current Maturity: Pre-research

The system can run, but we cannot yet answer the question:
> *"Is nanobot-auto actually improving itself, or is it just making random changes that happen to pass CI?"*

---

## Where We Want to Go

### End Goal: A Validated OCLSE Reference Implementation 🎯

A system that:
1. **Demonstrably self-improves** — H(t) trajectory shows measurable, sustained improvement
2. **Knows its own limits** — Variety Gap measurement tells us what problem types it can't handle
3. **Has memory** — Knowledge layer enables learning from past cycles
4. **Responds appropriately** — Variable tempo: fast for critical issues, slow for routine
5. **Is safe** — Empirically validated safety boundaries (CONSTITUTION.md ablation study)
6. **Is documented** — Publishable as an OCLSE empirical study

### What "Done" Looks Like

- A 10-week experiment run with complete H(t) time-series data
- Three hypotheses (P1/P2/P3) tested with statistical evidence
- A paper draft (workshop or arXiv) with clear positioning against related work (including SICA, once evaluated)
- Open-source codebase with H(t) collection, Knowledge layer, and variable tempo triggering

---

## The Road Between

### Milestone 0: Instrumentation Foundation 📏

**Goal:** Make the system observable before changing anything else.

| Task | Description | Deliverable |
|------|------------|-------------|
| 0.1 | Implement Fix Outcome Log (JSON) | `workspace/memory/fix_outcomes.json` |
| 0.2 | Implement H(t) Category D: runtime error_rate + uptime_ratio | Heartbeat-based collection script |
| 0.3 | Implement H(t) Category B: lead_time + change_failure_rate via GitHub API | DORA metrics collection script |
| 0.4 | Implement H(t) Category C: tokens_per_fix + fix_success_rate from logs | Agent efficiency parser |
| 0.5 | Implement H(t) Category A: cognitive_complexity + code_churn via static analysis | Ruff/radon integration |
| 0.6 | Daily H(t) snapshot persisted to `workspace/memory/health_vector/` | JSON time-series file per day |

**Exit criteria:** After one daily cycle, a complete H(t) JSON is automatically generated.

**Why this is first:** Every subsequent milestone depends on having data. Without H(t), we can't validate any hypothesis. This is pure infrastructure — no behavior change.

---

### Milestone 1: Knowledge Layer (Phase 0) 🧠

**Goal:** Give the system memory.

| Task | Description | Deliverable |
|------|------------|-------------|
| 1.1 | auto-merge writes Fix Outcome Log entry after each merge/reject decision | K write path |
| 1.2 | log-miner queries Fix Outcome Log for deduplication before creating Issues | K read path (Sense) |
| 1.3 | auto-dev injects relevant Fix Outcome entries into Codex prompt | K read path (Effect) |
| 1.4 | Implement Issue Type Registry (aggregated from Fix Outcome Log) | Variety Gap data source |

**Exit criteria:** log-miner does not create duplicate Issues for problems already fixed. auto-dev receives historical context in its prompt.

**Why this is second:** K is the biggest structural gap (MAPE-K analysis). Without K, the system can't learn from past cycles, and we can't compute Variety Gap.

---

### Milestone 2: Structured Issue Format 📋

**Goal:** Separate Monitor, Analyze, and Plan outputs within each Issue.

| Task | Description | Deliverable |
|------|------------|-------------|
| 2.1 | Define structured Issue template (Observation / Analysis / Plan / Constraints) | Template spec in log-miner skill |
| 2.2 | Update log-miner prompt to output in structured format | Modified skill prompt |
| 2.3 | auto-dev parses structured Issue to extract actionable plan | Modified auto-dev skill |

**Exit criteria:** All auto-generated Issues follow the structured template. auto-dev can extract the Plan section and use it directly.

**Why this is third:** Structured Issues are the communication protocol between Sense and Effect. Better structure = better fix quality. Also enables more precise H(t) Category B tracking.

---

### Milestone 3: Baseline Experiment (Weeks 1-4) 🔬

**Goal:** Collect 4 weeks of H(t) data with M0-M2 improvements in place.

| Task | Description | Deliverable |
|------|------------|-------------|
| 3.1 | Run nanobot-auto daily for 4 weeks without further changes | 28 daily H(t) snapshots |
| 3.2 | Collect Issue taxonomy (classify all created Issues by type) | Issue Type distribution |
| 3.3 | Compute baseline Variety Gap from Issue Type Registry | Variety Gap initial measurement |
| 3.4 | Generate H(t) trajectory visualization | Time-series charts per dimension |

**Exit criteria:** 4 weeks of clean data. Baseline H(t) trajectory and Issue taxonomy documented.

**Why now:** We need a stable baseline before testing any hypothesis. M0-M2 must be in place so the data we collect is representative of the "instrumented" system, not the pre-instrumentation version.

---

### Milestone 4: Cascaded Triggering 🔗

**Goal:** Eliminate idle wait between Effect and Gate.

| Task | Description | Deliverable |
|------|------------|-------------|
| 4.1 | After auto-dev creates a PR, immediately trigger auto-merge check | Event cascade logic |
| 4.2 | Measure lead_time improvement (before/after cascade) | H(t) Category B comparison |

**Exit criteria:** lead_time drops by >50% compared to baseline (M3 data).

**Why here:** This is the simplest triggering improvement. It directly affects H(t) Category B (lead_time), and the M3 baseline gives us a clear before/after comparison (which is Experiment 3 data).

---

### Milestone 5: Hypothesis Testing (Weeks 5-9) 📊

**Goal:** Test the three OCLSE predictions.

| Task | Description | Deliverable |
|------|------------|-------------|
| 5.1 | P1 test: Compare Issue-type distribution before/after log-miner code changes | KL divergence analysis |
| 5.2 | P2 test: Regress H(t) improvement rate over time; test for decay | Second derivative analysis |
| 5.3 | P3 test: Ablation study — remove CONSTITUTION.md + CI gate on isolated clone | Catastrophic failure count |
| 5.4 | Compile experimental results | Results summary document |

**Exit criteria:** Three hypotheses tested. Each has a clear accept/reject conclusion with supporting data.

---

### Milestone 6: Write-Up & Publication 📝

**Goal:** Produce a publishable document.

| Task | Description | Deliverable |
|------|------------|-------------|
| 6.1 | Draft paper: Introduction + Related Work (SICA evaluation, MAPE-K, DORA) | Paper §1-2 |
| 6.2 | Draft paper: OCLSE Framework + Code Health Vector | Paper §3 |
| 6.3 | Draft paper: Experimental Results + Discussion | Paper §4-5 |
| 6.4 | Choose venue and format (workshop / arXiv / blog) based on results | Submission target |

**Exit criteria:** Complete draft ready for review.

---

## Timeline Overview

```
         (We are here)
              │
              ▼
 ┌─── M0: Instrumentation Foundation ──────────── ~1 week
 │
 ├─── M1: Knowledge Layer (Fix Outcome Log) ───── ~1 week
 │
 ├─── M2: Structured Issue Format ─────────────── ~3 days
 │
 ├─── M3: Baseline Experiment ─────────────────── 4 weeks (running)
 │
 ├─── M4: Cascaded Triggering ─────────────────── ~3 days
 │
 ├─── M5: Hypothesis Testing ──────────────────── 5 weeks (running)
 │
 └─── M6: Write-Up ────────────────────────────── ~1 week
              │
              ▼
     Total: ~14 weeks from start to submission
```

---

## Decision Points

At certain milestones, results may change the direction:

| After | If... | Then... |
|-------|-------|---------|
| M3 | H(t) is completely flat (no self-improvement signal at all) | Re-evaluate log-miner quality; possibly not ready for experiments |
| M3 | Variety Gap is 100% (system can't fix anything) | Focus on improving auto-dev capability before continuing |
| M5.1 | P1 not detected (no observer coupling) | Drop P1 from paper; focus on P2/P3 |
| M5.2 | P2 not detected (no diminishing returns) | This is actually a positive finding — report as "sustained improvement" |
| M5.3 | P3 not detected (system survives without CONSTITUTION) | Revise safety assumptions; possibly CONSTITUTION is unnecessary |
| M5 | All three hypotheses rejected | Pivot to engineering contribution only (framework + tool) |

---

## Principles

1. **Observe before you change.** M0 (instrumentation) comes before any behavioral modification.
2. **Baseline before you experiment.** M3 (4 weeks of data) before any hypothesis testing.
3. **Smallest change first.** Each milestone is the minimum viable step that enables the next.
4. **Data over intuition.** Every architectural decision in M1-M4 will be validated against H(t) in M5.
5. **Honest reporting.** If hypotheses are rejected, we report that. Negative results are still publishable.

---

*Roadmap derived from TEP v2.0 crystallized framework. Subject to revision at decision points.*
