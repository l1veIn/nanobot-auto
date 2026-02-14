---
name: log-miner
description: "Analyze recent nanobot session logs to detect errors, anomalies, and improvement opportunities. Always produces at least one issue."
metadata: {"nanobot":{"emoji":"🔍","requires":{"bins":["gh"]}}}
---

# Log Miner

Analyze nanobot's own session logs. **You must always produce at least one issue per run** — either a bug report, an enhancement proposal, or a self-improvement task.

## Philosophy

You are not just an error scanner. You are an intelligence analyst. Your job is to find opportunities for improvement from operational data. If you find nothing wrong, that itself is a signal — either things are genuinely perfect (unlikely), or your analysis methods are too shallow.

## Step 1: Gather data

```bash
find ~/.nanobot/sessions -name '*.jsonl' -mtime -1
```

Read the content of recent log files. Don't just grep keywords — **read and understand the conversations**.

## Step 2: Multi-layer analysis

Analyze logs at three levels:

### Level A — Errors (surface)
Scan for explicit failures: error, failed, timeout, traceback, exception, panic.

### Level B — Behavioral patterns (deeper)
Look for signals that don't appear as errors but indicate problems:
- **Abandoned conversations**: user started a task but never completed it
- **Repeated attempts**: user asked the same thing multiple times (bot didn't solve it)
- **Frustration signals**: user said "never mind", "forget it", "I'll do it myself"
- **Long response times**: conversations where the bot took unusually long
- **Tool failures**: tools that were called but produced unhelpful results
- **Missing capabilities**: user asked for something the bot couldn't do

### Level C — Improvement opportunities (deepest)
Even if everything works fine, look for:
- **Code quality**: are there modules that lack tests, documentation, or type hints?
- **Performance**: are there operations that could be optimized?
- **Security**: are there potential security concerns in how tools operate?
- **Skill gaps**: what skills could be added to make the bot more useful?

## Step 3: Check for duplicates

```bash
gh issue list --repo l1veIn/nanobot-auto --label auto-report --state open --json number,title --jq '.[].title'
```

Skip any issue that already exists.

## Step 4: Create issues

Create **at least one issue** per run. Use the appropriate label:

### For bugs (Level A findings):
```bash
gh issue create --repo l1veIn/nanobot-auto \
  --title "[bug] <description>" \
  --body "<analysis>" \
  --label "auto-report"
```

### For enhancements (Level B/C findings):
```bash
gh issue create --repo l1veIn/nanobot-auto \
  --title "[enhance] <description>" \
  --body "<analysis and proposed approach>" \
  --label "auto-report"
```

## Step 5: Self-reflection

If after all analysis you found **nothing at all** from the logs, you MUST create a self-improvement issue about log-miner itself:

```bash
gh issue create --repo l1veIn/nanobot-auto \
  --title "[enhance] Improve log-miner: <specific weakness found>" \
  --body "log-miner was unable to extract useful insights from today's logs.

## What was analyzed
<summary of logs examined>

## Why nothing was found
<honest assessment: too few logs? analysis too shallow? wrong keywords?>

## Proposed improvement
<concrete suggestion to make log-miner smarter, e.g. add new analysis patterns, parse JSONL structure instead of grep, track metrics over time>" \
  --label "auto-report"
```

This ensures the system **always has work to do** and **always improves**.
