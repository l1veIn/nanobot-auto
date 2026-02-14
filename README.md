<div align="center">
  <h1>🐈 nanobot-auto</h1>
  <p><strong>Self-Evolving AI Agent</strong></p>
  <p>
    <img src="https://img.shields.io/badge/python-≥3.11-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <img src="https://img.shields.io/badge/contributors-AI_only-ff6b6b" alt="AI Only">
    <img src="https://img.shields.io/badge/dev_engine-OpenAI_Codex-black" alt="Codex">
  </p>
  <p><em>Software that writes, reviews, and deploys itself. Every day. Without humans.</em></p>
</div>

---

## What is this?

**nanobot-auto** is an experiment in fully autonomous software evolution. A single [nanobot](https://github.com/HKUDS/nanobot) instance runs three daily jobs that form a closed self-improvement loop:

```
┌────────────────────────────────────────────────────────┐
│                    Daily Cycle                         │
│                                                        │
│  20:00  🔍 log-miner     Analyze logs → create Issue   │
│  00:30  🛠️ auto-dev       Pick Issue → Codex → PR      │
│  02:00  🔀 auto-merge     CI pass → merge → restart    │
│                                                        │
│  ↻ repeat forever                                      │
└────────────────────────────────────────────────────────┘
```

The entire development lifecycle — from bug discovery to production deployment — is handled by AI.

## Why?

AI dev tools (Cursor, Copilot, Codex) have matured. Requirements analysis, coding, and testing are solved. **The missing piece is the feedback loop** — automatically collecting real-world usage data, turning it into actionable tasks, and deploying fixes.

nanobot-auto closes that loop.

## Architecture

```
./run.sh  (auto-restart wrapper, preserves shell env)
└── nanobot gateway  (agent + cron + channels)
    │
    ├── 🔍 log-miner  (20:00)
    │   ├── Run log-digest.sh → compact summary
    │   ├── Explore log format (don't assume, verify)
    │   ├── 3-layer analysis:
    │   │   ├── A: Errors (surface)
    │   │   ├── B: Behavioral patterns (deeper)
    │   │   └── C: Improvement opportunities (deepest)
    │   ├── Deduplicate against open issues
    │   ├── Create [bug] / [enhance] / [research] issue
    │   └── If nothing found → self-reflection research task
    │
    ├── 🛠️ auto-dev  (00:30)
    │   ├── Pick oldest open auto-report issue
    │   ├── Clone repo to /tmp (isolated workspace)
    │   ├── Delegate to Codex --approval-mode full-auto
    │   ├── Verify Codex output (git diff --stat)
    │   └── Push branch + create PR
    │
    └── 🔀 auto-merge  (02:00)
        ├── List open PRs
        ├── Check CI status per PR
        ├── Merge passing / close failing
        ├── git pull + pip install -e . (self-update)
        └── kill $$ → run.sh restarts with new code
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Isolated dev workspace** | auto-dev clones to `/tmp`, never modifies the running directory |
| **Codex as developer** | nanobot is the project manager, Codex writes all code |
| **Shell-level restart** | `run.sh` wrapper preserves PATH/env across restarts |
| **Feishu notifications** | All cron results delivered to Feishu via `deliver=true` |
| **Mandatory issue output** | log-miner MUST produce ≥1 issue per run (prevents stagnation) |
| **Research tasks** | When analysis finds nothing, create `[research]` issue instead of blind enhancement |

## Setup

### 1. Install

```bash
git clone https://github.com/l1veIn/nanobot-auto.git
cd nanobot-auto
pip install -e .
```

### 2. Configure

Edit `~/.nanobot/config.json`:

```json
{
  "agents": {
    "defaults": {
      "model": "your-model",
      "maxToolIterations": 50
    }
  },
  "providers": {
    "your-provider": {
      "apiKey": "sk-xxx"
    }
  }
}
```

### 3. Prerequisites

```bash
gh auth login          # GitHub CLI
codex --version        # OpenAI Codex CLI
```

### 4. Start

```bash
# Option A: foreground
nanobot gateway

# Option B: auto-restart (recommended for production)
./run.sh

# Option C: background with tmux (recommended for overnight)
tmux new -s nanobot -d './run.sh'
```

Then tell the bot to set up cron jobs, or they'll be picked up from `~/.nanobot/cron/jobs.json` if already configured.

## The Rules

1. **AI-only commits.** Human contributions are limited to initial setup and rule changes.
2. **CI is the gatekeeper.** PRs are only merged if all checks pass.
3. **Self-update on merge.** The bot pulls, reinstalls, and restarts after each merge.
4. **Always produce work.** log-miner must output at least one issue per cycle.
5. **Research before action.** When uncertain, create a `[research]` task instead of blind code changes.

## Issue Taxonomy

| Prefix | Meaning | auto-dev action |
|--------|---------|----------------|
| `[bug]` | Runtime error found in logs | Fix the code |
| `[enhance]` | Improvement opportunity | Implement enhancement |
| `[research]` | Need investigation first | Investigate, then convert to bug/enhance |

## Origin

Based on [HKUDS/nanobot](https://github.com/HKUDS/nanobot) (Python). See [doc/anchor_v0.md](doc/anchor_v0.md) for the full design rationale.

A parallel Rust experiment based on [nanobot-rs](https://github.com/open-vibe/nanobot-rs) is running separately for iteration speed comparison.

## License

MIT
