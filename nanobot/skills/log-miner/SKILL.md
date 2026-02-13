---
name: log-miner
description: "Analyze recent nanobot session logs to detect errors, anomalies, and patterns. Create GitHub issues for problems found."
metadata: {"nanobot":{"emoji":"🔍","requires":{"bins":["gh"]}}}
---

# Log Miner

Analyze nanobot's own session logs to find problems and create issues.

## When triggered

This skill runs as a daily cron task. Analyze logs from the past 24 hours only.

## Step 1: Find recent logs

```bash
find ~/.nanobot/sessions -name '*.jsonl' -mtime -1
```

If no files found, stop — nothing to analyze.

## Step 2: Scan for anomalies

```bash
grep -c -i 'error\|failed\|timeout\|traceback\|exception\|panic' <file>
```

Run this for each file found in Step 1. If total count is 0, stop — no issues to report.

## Step 3: Extract error context

For files with anomalies, extract the relevant lines with context:

```bash
grep -n -i -B2 -A2 'error\|failed\|timeout\|traceback\|exception\|panic' <file> | head -100
```

## Step 4: Analyze and summarize

Read the extracted errors. Identify:
- **Pattern**: Is this a one-time error or recurring?
- **Component**: Which tool/skill/channel is affected?
- **Severity**: Is it blocking functionality or just a warning?
- **Suggested fix**: What code change might resolve this?

Only create an issue if the problem is **actionable** — skip transient network errors or user-caused issues.

## Step 5: Check for duplicates

Before creating a new issue, check if a similar one already exists:

```bash
gh issue list --repo l1veIn/nanobot-auto --label auto-report --state open --json number,title --jq '.[].title'
```

If a similar issue exists, skip creation.

## Step 6: Create issue

```bash
gh issue create --repo l1veIn/nanobot-auto \
  --title "[auto-report] <concise problem description>" \
  --body "<detailed analysis from Step 4>" \
  --label "auto-report"
```

The issue body should include:
- Error pattern observed
- Affected component/file
- Frequency (how many times in 24h)
- Suggested fix approach
