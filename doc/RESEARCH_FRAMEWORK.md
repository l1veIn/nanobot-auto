# OCLSE Research Framework

> **Status:** Draft — TEP v2.0 Crystalized (S=3, Δ=8%, G=1)
> **Date:** 2025-02-14
> **Origin:** TEP adversarial deduction, 2 runs, 6 rounds total
> **Note:** SICA (Robeyns et al., 2025) is referenced as potential related work but **has not been fully evaluated yet**. All SICA-comparative claims are provisional and subject to revision after reading the original paper.

---

## 1. Positioning

**nanobot-auto** explores a paradigm we call **OCLSE: Online Closed-Loop Self-Evolution** — a software system that runs in production, observes its own runtime behavior, diagnoses problems, modifies its own code, deploys changes, and repeats.

The core research question is:
> *Can a software system, driven by an LLM, sustain meaningful self-improvement through an online closed-loop — and what are the fundamental problems it encounters when doing so?*

### OCLSE vs Offline Self-Improvement

Offline self-improvement (e.g., optimizing against a fixed benchmark in a sandbox) differs fundamentally from online closed-loop evolution:

| Dimension | Offline Self-Improvement | Online Self-Evolution (OCLSE) |
|-----------|------------------------|-------------------------------|
| Feedback source | Static benchmarks | Live runtime logs & metrics |
| Improvement target | Agent code only | Entire project codebase |
| Deployment | Not applicable | Auto-merge + self-restart |
| Environment stability | Fixed | Non-stationary (self-modified) |
| Observer independence | Yes (external benchmark) | No (observer = observed) |
| Safety constraints | None (sandbox) | Required (production) |

> **Pending evaluation:** SICA (Robeyns et al., 2025) appears to be the closest related work in the offline self-improvement category. Full comparison deferred until paper review.

### What we are NOT claiming

- We are NOT claiming to "solve" any of the three core problems identified below.
- We are NOT claiming a novel algorithm or model architecture.
- We are NOT claiming superiority over any existing system on benchmarks.

### What we ARE claiming

- OCLSE surfaces **three practical problems** that offline self-improvement does not encounter.
- nanobot-auto serves as a **living testbed** to observe and measure these problems in the wild.
- The Code Health Vector provides a **quantitative framework** to track self-evolution trajectory.

---

## 2. Three Core Problems of OCLSE

### P1: Observer-Modifier Coupling

**The system that observes problems is also the system being modified.**

When `log-miner` identifies a bug in its own code and `auto-dev` fixes it, the next cycle's `log-miner` behaves differently — not because the environment changed, but because the observer itself changed. This creates a feedback coupling where the reliability of observation depends on the quality of previous modifications.

- **Theoretical root:** Self-referential systems (Gödel, Turing)
- **Engineering manifestation:** log-miner analyzing its own session logs
- **Current mitigation:** Isolated development in `/tmp` (version separation)
- **Open question:** Can we formally bound the observational drift?

### P2: Self-Induced Distribution Shift

**Each self-modification changes the distribution of future problems.**

After fixing class A errors, the system's behavior profile shifts. Error patterns that were common become rare; new patterns may emerge. Strategies that worked for V(n) may not work for V(n+1). This is the classic non-stationary environment problem from continual learning.

- **Theoretical root:** Distribution shift, concept drift (continual learning)
- **Engineering manifestation:** Diminishing returns over self-improvement cycles
- **Current mitigation:** None
- **Open question:** Does H(t) improvement rate decay over time? (Testable)

### P3: Safe Self-Modification

**Online self-modification must not cause unrecoverable failure.**

Unlike offline self-improvement systems which run in sandboxes, nanobot-auto's modifications are deployed to the running system. A bad self-modification could break the observation pipeline (P1), corrupt the development pipeline, or cause a restart loop.

- **Theoretical root:** Safe exploration (safe RL), formal verification
- **Engineering manifestation:** CONSTITUTION.md as immutable safety constraint
- **Current mitigation:** CI gate + CONSTITUTION.md + run.sh restart wrapper
- **Open question:** Are these safeguards sufficient? Can we quantify their effectiveness?

---

## 3. Code Health Vector H(t)

A multi-dimensional, time-series metric to quantify the trajectory of self-evolution.

### 3.1 Dimensions

#### Category A: Intrinsic Code Quality

| Metric | Definition | Tool / Source |
|--------|-----------|---------------|
| `cognitive_complexity` | Human difficulty of understanding code | SonarQube (2024) |
| `technical_debt_ratio` | Refactoring cost / development cost | SonarQube |
| `code_churn_30d` | % of files changed >2x in 30 days | Git analysis |
| `duplication_ratio` | % of duplicated code blocks | GitClear (2024) |
| `defect_density` | Defects per KLOC | Static analysis |

#### Category B: Process Effectiveness (DORA)

| Metric | Definition | Source |
|--------|-----------|--------|
| `lead_time` | Issue created → PR merged (hours) | GitHub API |
| `change_failure_rate` | % of PRs that introduce new issues | log-miner tracking |
| `mttr` | Mean time from issue creation to fix deployment | GitHub API |

#### Category C: Agent Efficiency (inspired by SWE-Effi, 2025)

| Metric | Definition | Source |
|--------|-----------|--------|
| `tokens_per_fix` | LLM tokens consumed per successful fix | Codex API logs |
| `api_calls_per_fix` | API calls per successful fix | Codex API logs |
| `fix_success_rate` | % of auto-dev PRs that pass CI | GitHub API |

#### Category D: Runtime Health

| Metric | Definition | Source |
|--------|-----------|--------|
| `error_rate` | Errors per hour in runtime logs | log-miner |
| `uptime_ratio` | % of time system is operational | Heartbeat monitor |

### 3.2 Usage

H(t) is sampled once per daily cycle. The primary analysis is the **trajectory** of H over time:

- **H(t) improving monotonically** → System is self-evolving effectively
- **H(t) oscillating** → P2 (distribution shift) or feedback instability
- **H(t) degrading** → Self-modification is net harmful; trigger human review
- **H(t) plateau** → Diminishing returns; Variety Gap reached

---

## 4. Architecture Analysis — Sense / Effect / Gate

> *TEP v2.0 Crystalized (S=3, Δ=7%, G=1). Second TEP run targeting the three-component design.*

### 4.1 Theoretical Basis: Minimal Complete Decomposition

Any closed-loop self-modifying system requires **at minimum three irreducible functional roles**:

| Role | Function | Why irreducible |
|------|----------|----------------|
| **Sense** | Extract signals from system state | No sensing = blind modification |
| **Effect** | Apply modifications to the system | No action = no improvement |
| **Gate** | Decide whether modifications are accepted | No gate = unsafe (Separation of Privilege) |

Why three, not two? If Effector is its own Gatekeeper (auto-merges its own changes), it violates **Separation of Privilege** — a fundamental security engineering principle. Under OCLSE P3 (Safe Self-Modification), "who modifies" and "who approves" **must be separate**.

Why three, not four or five? Because Monitor, Analyze, and Plan can be accomplished **in a single LLM reasoning call**. Splitting M/A/P into separate LLM invocations loses context and degrades quality. So functionally it's MAPE-K, but implementation-wise M+A+P merge into one Sense component.

### 4.2 MAPE-K Gap Analysis

| MAPE-K Stage | Function | nanobot-auto mapping | Status |
|-------------|----------|---------------------|--------|
| **M** - Monitor | Collect raw data | log-miner (partial) | ✅ Logs only; needs metrics |
| **A** - Analyze | Root cause analysis | log-miner (merged) | ⚠️ Mixed with M |
| **P** - Plan | Formulate fix strategy | log-miner (merged) | ⚠️ Mixed with A |
| **E** - Execute | Apply the fix | auto-dev + Codex | ✅ |
| **K** - Knowledge | Cross-cycle shared state | ❌ Missing | 🔴 Critical gap |
| (Gate) | Quality control | auto-merge | ⚠️ Not in MAPE-K |

**Key finding:** log-miner carries M+A+P responsibilities (acceptable for LLM), but **K is completely absent**.

### 4.3 Knowledge Layer — Minimal Viable Design

K is not a pipeline stage; it is **shared infrastructure** read/written by all stages.

**Two data structures only:**

**a) Fix Outcome Log** — records what happened each cycle:
```json
{
  "cycle_id": "2025-02-14",
  "issue_id": "#42",
  "issue_type": "bug",
  "affected_files": ["nanobot/agent/loop.py"],
  "fix_succeeded": true,
  "introduced_new_issues": false,
  "tokens_consumed": 15000,
  "time_to_fix_hours": 4.5
}
```

**b) Issue Type Registry** — maps problem types to success rates:
```
problem_type → { count, success_rate, avg_tokens }
```

**How K influences decisions:**
- **Sense** queries K before creating Issues (deduplication + reference past fixes)
- **Effect** references K for similar past fix paths (injected into LLM prompt)
- Both implemented via K summary injection into LLM context — no RL needed.

### 4.4 Triggering Strategy — Variable Tempo

Fixed cron (20:00 / 00:30 / 02:00) is the **slowest viable strategy**. Per OODA loop theory, cycle speed is a decisive advantage — but must be balanced against cost and safety (OCLSE P3).

| Signal level | Trigger | Rationale |
|-------------|---------|-----------|
| INFO/WARNING | Daily cron batch | Cost control + human review window |
| CRITICAL/FATAL | Immediate event trigger | OODA tempo advantage |
| PR created | Cascade to auto-merge | Eliminate idle wait |

### 4.5 Target Architecture

```
┌─────────────────────────────────────────────┐
│            Knowledge (K)                     │
│   Fix Outcome Log + Issue Type Registry      │
├──────────┬──────────────┬───────────────────┤
│          ▼              ▼                ▼   │
│   ┌──────────┐   ┌──────────┐   ┌─────────┐│
│   │  Sense   │──▶│  Effect  │──▶│  Gate   ││
│   │(M+A+P)   │   │(Execute) │   │(Verify) ││
│   │log-miner │   │ auto-dev │   │auto-merge│
│   └──────────┘   └──────────┘   └─────────┘│
│       ▲                              │      │
│       └──────── feedback ◀───────────┘      │
└─────────────────────────────────────────────┘
```

---

## 5. Recording & Analysis Strategy

> *Consolidated from TEP runs #3 and #4, plus code-level instrumentation analysis.*

The quality of self-evolution is bounded by the quality of the data the system collects about itself. SICA's advantage is that its "user data" (benchmark execution traces) is inherently structured. nanobot-auto's raw runtime logs are unstructured — this gap must be closed.

### 5.1 Recording: Tool-Call Event Log

**Every Agent action is a tool call.** The `Tool.execute()` method in `nanobot/agent/loop.py` is the single unified entry point for all agent behavior (file I/O, shell commands, API calls, messaging). Instrumenting this one location captures all agent activity automatically.

**Event schema:**
```json
{
  "case_id": "cycle_042",
  "activity": "filesystem.read",
  "skill": "auto-dev",
  "timestamp": "2025-02-16T00:30:15Z",
  "args_summary": "{path: /tmp/fix/loop.py}",
  "success": true,
  "duration_ms": 150
}
```

**Output format:** XES-compatible event log → directly consumable by pm4py for process mining.

**Implementation cost:** ~20 lines in `loop.py`, zero changes to individual tools.

### 5.2 Analysis: Process Mining + LLM Hybrid

Two analysis tracks, each playing to its strengths:

| Track | Tool | Strengths | Scope |
|-------|------|-----------|-------|
| **Deterministic** | pm4py | No hallucination, formally grounded, handles conformance | Control-flow patterns, timing, variant distribution |
| **Semantic** | LLM (log-miner) | Context understanding, natural language, causal reasoning | Root cause inference, fix planning, language-level constraints |

**pm4py provides three capabilities:**

1. **Process Discovery** — Automatically discover the actual execution flow from event logs (Inductive Miner). Answers: "What does the system actually do vs. what we think it does?"
2. **Conformance Checking** — Encode CONSTITUTION.md's formalizable rules as a Petri Net reference model, auto-detect violations. (e.g., Article 1: log-miner must not emit `write_file` events)
3. **Variant Analysis** — Track how the distribution of process variants changes over time → direct measurement of P2 (distribution shift)

**LLM handles what pm4py cannot:**
- Semantic constraints (e.g., "every cycle must produce at least one Issue")
- Causal reasoning ("this error was introduced by PR #55")
- Fix strategy generation

**Data flow:**
```
Tool calls → XES Event Log → pm4py → Conformance Report ─┐
                                                          ├→ LLM (Sense) → Issues
                          Cycle Report (narrative MD) ─────┘
```

### 5.3 Cycle Report (LLM Context Layer)

Each component appends its section after execution:
1. log-miner → "What was observed" + "Issues created"
2. auto-dev → "What was done" + "PR details"  
3. auto-merge → "Outcome" + "Health Vector Delta"

Context window management: sliding window of 3 recent full reports + 30-day compressed summaries (~10K tokens total).

### 5.4 Key Principles

1. **Data collection is never done by LLM.** Event logging and metric snapshots are deterministic scripts. LLM only interprets.
2. **Tool calls are the natural event granularity.** Not high-level stages, not raw log lines.
3. **pm4py doesn't replace LLM; it feeds LLM.** Conformance reports become part of LLM input context.

### 5.5 Open Question: Human Input as External Signal

> **Status:** Identified 2025-02-16, not yet resolved.

The current R&A strategy only covers **system-generated data** (tool calls, logs, metrics). But nanobot-auto receives **human input** via 9 communication channels (Feishu, Telegram, Discord, etc.). This breaks the "closed loop" assumption:

- Human input is the highest-priority signal (VSM S4: external intelligence)
- Human intent/priority is not captured by tool-call event logs
- The system may be **human-machine co-evolution**, not pure self-evolution

This may require redefining OCLSE from "closed loop" to "semi-open loop with external input." Deferred to next session.

---

## 6. Experiment Plan

### Experiment 1: Baseline Observation (Weeks 1-4)

**Goal:** Establish H(t) baseline without intervention.

- Let nanobot-auto run its daily cycle for 4 weeks
- Collect H(t) at each cycle
- Record all Issues created, PRs generated, merge/reject decisions
- **Output:** Baseline trajectory + issue type taxonomy

**No theory validation yet — just data collection.**

### Experiment 2: P1 Detection — Observer Coupling (Weeks 5-8)

**Goal:** Test whether log-miner modifications change observation patterns.

- **Metric:** KL divergence of issue-type distribution before/after log-miner is modified
- **Method:** Compare issue-type distributions in weeks 1-4 vs weeks 5-8
- **Hypothesis (P1-test):** KL divergence > threshold when log-miner code was changed during the period, vs ≈ 0 when it was not changed

### Experiment 3: P2 Detection — Diminishing Returns (Weeks 1-8)

**Goal:** Test whether H(t) improvement rate decays.

- **Metric:** Slope of H(t) per dimension over time
- **Method:** Regress each H dimension against time; test for negative second derivative
- **Hypothesis (P2-test):** The improvement rate of at least 3/5 Category A metrics will decrease in the second half of the observation period

### Experiment 4: P3 Validation — Safety Boundary (Week 9)

**Goal:** Ablation study on safety mechanisms.

- **Method:** In a **cloned, isolated copy** of the system (NOT production):
  - Remove CONSTITUTION.md protections
  - Remove CI gate (auto-merge all PRs)
  - Run 1 week of cycles
- **Metric:** Count of catastrophic failures (system unable to self-restart)
- **Hypothesis (P3-test):** Unconstrained system will experience ≥1 catastrophic failure within 7 cycles

### Timeline

```
Week 1-4:   Experiment 1 (Baseline)
Week 5-8:   Experiment 2 + 3 (P1 & P2 detection, overlapping)
Week 9:     Experiment 4 (P3 ablation, isolated clone)
Week 10:    Analysis & write-up
```

---

## 7. Expected Contribution

If experiments validate the hypotheses:

> *"We present nanobot-auto, an OCLSE (Online Closed-Loop Self-Evolution) system that extends the SICA offline self-improvement paradigm to production environments. Through 9 weeks of continuous operation, we identify and empirically measure three problems unique to online self-evolution: observer-modifier coupling, self-induced distribution shift, and safe self-modification constraints. We propose Code Health Vector H(t) as a quantitative framework for tracking self-evolution trajectory, drawing on DORA metrics, Cognitive Complexity, and SWE-Effi."*

**Contribution type:** Empirical study + framework proposal (not algorithmic breakthrough)

**Target venue options (ordered by fit):**
1. Workshop paper at ICSE / FSE (software engineering)
2. Workshop paper at NeurIPS / ICML (as SICA follow-up)
3. arXiv preprint + open-source reference implementation

---

## 8. References

- Robeyns, M., Szummer, M., & Aitchison, L. (2025). *Self-Improving Coding Agent.* NeurIPS 2025.
- Kephart, J. O., & Chess, D. M. (2003). *The Vision of Autonomic Computing.* IEEE Computer, 36(1). (MAPE-K)
- van der Aalst, W. M. P. (2016). *Process Mining: Data Science in Action.* Springer. (Process Mining, pm4py)
- Berti, A., van Zelst, S., & van der Aalst, W. M. P. (2024). *PM4Py and LLM integration.* arXiv.
- DORA Team, Google. (2024). *Accelerate State of DevOps Report.*
- SWE-Effi. (2025). *Multi-dimensional efficiency evaluation for SWE agents.* arXiv.
- Campbell, G. A. (2018). *Cognitive Complexity: A new way of measuring understandability.* SonarSource.
- GitClear. (2024). *Coding on Copilot: AI code quality report.*
- Boyd, J. R. (1987). *A Discourse on Winning and Losing.* (OODA Loop)

---

*Document generated via TEP v2.0 adversarial deduction (4 runs, 12 rounds total). Reviewed and committed by human operator.*
