<div align="center">
  <h1>🐈 nanobot-auto</h1>
  <p><strong>Self-Evolving AI Agent Framework</strong></p>
  <p>
    <img src="https://img.shields.io/badge/python-≥3.11-blue" alt="Python">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
    <img src="https://img.shields.io/badge/contributors-AI_only-ff6b6b" alt="AI Only">
  </p>
  <p><em>Software that improves itself. No human commits allowed.</em></p>
</div>

## What is this?

**nanobot-auto** is an experiment in fully autonomous software evolution. A single [nanobot](https://github.com/HKUDS/nanobot) instance analyzes its own logs, identifies problems, writes fixes, and merges them — on a daily cycle, without human intervention.

```
20:00  log-miner   → Analyze logs, create Issue if problems found
02:00  auto-dev    → Pick an Issue, develop fix, submit PR
08:00  auto-merge  → Review PR, merge if CI passes, self-update
```

The entire development lifecycle — from bug discovery to deployment — is handled by AI.

## Why?

AI development tools (Cursor, Copilot, Devin) have matured. Requirements analysis, coding, and testing are solved problems. **The missing piece is automated collection and processing of real-world usage data.** Currently, humans still bridge this gap.

nanobot-auto closes the loop: software evolves based on its own operational data, not human judgment.

## Architecture

```
nanobot instance (single bot, 3 cron jobs)
│
├── log-miner skill (20:00 daily)
│   ├── Scan ~/.nanobot/sessions/*.jsonl
│   ├── Detect errors, failures, anomalies
│   └── gh issue create --label auto-report
│
├── auto-dev skill (02:00 daily)
│   ├── gh issue list --label auto-report
│   ├── Analyze issue → develop fix
│   ├── python -m py_compile (safety check)
│   └── gh pr create
│
└── auto-merge skill (08:00 daily)
    ├── gh pr checks (verify CI)
    ├── gh pr merge --squash
    └── git pull && pip install -e . (self-update)
```

## Setup

**1. Install**

```bash
pip install -e .
```

**2. Configure** (`~/.nanobot/config.json`)

```json
{
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-v1-xxx"
    }
  },
  "agents": {
    "defaults": {
      "model": "anthropic/claude-sonnet-4"
    }
  }
}
```

**3. Authenticate GitHub**

```bash
gh auth login
```

**4. Start**

```bash
nanobot agent
```

Then tell the bot to set up its cron jobs:

```
Set up 3 cron jobs:
1. "Analyze recent logs and create issues" at 20:00 daily
2. "Check auto-report issues, develop fixes, create PRs" at 02:00 daily  
3. "Review PRs, merge if CI passes, self-update" at 08:00 daily
```

## The Rules

1. **AI-only commits.** Human contributions are not accepted.
2. **CI is the gatekeeper.** PRs are only merged if CI passes.
3. **Self-update on merge.** The bot pulls and reinstalls itself after each merge.

## Origin

Based on [HKUDS/nanobot](https://github.com/HKUDS/nanobot) (Python). See [doc/anchor_v0.md](doc/anchor_v0.md) for the full design rationale and TEP crystallization reports.

A parallel Rust experiment based on [nanobot-rs](https://github.com/open-vibe/nanobot-rs) is running separately for comparison.

## License

MIT
