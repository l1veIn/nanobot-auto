---
name: auto-dev
description: "Pick an open auto-report issue, dispatch Codex via background script, report dispatch status."
metadata: {"nanobot":{"emoji":"🛠️","requires":{"bins":["gh","git","codex"]}}}
---

# Auto Dev

Pick an open issue and dispatch development to Codex in the background.

> **Governed by [CONSTITUTION.md](../../CONSTITUTION.md)** — Articles 1, 2, 3, 4.

## ⛔ Hard Rules (NEVER violate)

1. **You are the project manager, NOT the developer.** You MUST NOT write, edit, or modify any source code yourself.
2. **Never modify your own running directory.** All work happens via the dispatch script.
3. **If dispatch fails → STOP.** Do not attempt manual fixes. Do not write code.

## Step 1: Find an issue

```bash
gh issue list --repo l1veIn/nanobot-auto --label auto-report --state open --json number,title --limit 1
```

If no issues found, stop and report "No open issues".

## Step 2: Dispatch to Codex

Launch the background development script. **Do NOT wait for it to finish.**

```bash
nohup bash nanobot/skills/auto-dev/scripts/dev-dispatch.sh <NUMBER> > /dev/null 2>&1 &
echo "Dispatched issue #<NUMBER> to Codex (PID: $!)"
```

This script will independently:
1. Clone the repo to `/tmp`
2. Run Codex in full-auto mode
3. If changes are made: commit, push, create PR
4. If no changes: comment on the issue
5. Clean up the temp directory

## Step 3: Report

Report to the user:
- Which issue was dispatched
- That Codex is working in the background
- That results will appear as a PR (picked up by auto-merge next cycle)

**DO NOT:**
- Wait for Codex to finish
- Check if Codex succeeded
- Try to read or modify any files
- Write any code

You are done. The dispatch script handles everything else.
