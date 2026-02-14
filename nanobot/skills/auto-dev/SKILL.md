---
name: auto-dev
description: "Pick an open auto-report issue, use Codex YOLO mode to develop a fix in an isolated workspace, then create a pull request."
metadata: {"nanobot":{"emoji":"🛠️","requires":{"bins":["gh","git","codex"]}}}
---

# Auto Dev

Pick an open issue, delegate development to Codex in an **isolated workspace**, and submit a PR.

**IMPORTANT**: You are the project manager, NOT the developer. Never modify files in your own running directory. All development happens in a temporary clone.

## Step 1: Find an issue

```bash
gh issue list --repo l1veIn/nanobot-auto --label auto-report --state open --json number,title,body --limit 1
```

If no issues found, stop.

## Step 2: Create isolated workspace

Clone the repo into a temporary directory. Never develop in the bot's own running directory.

```bash
WORK_DIR=$(mktemp -d)/nanobot-auto
git clone git@github.com:l1veIn/nanobot-auto.git "$WORK_DIR"
cd "$WORK_DIR"
git checkout -b fix/issue-<NUMBER>
```

## Step 3: Delegate to Codex (YOLO mode)

Run Codex in the isolated workspace:

```bash
cd "$WORK_DIR" && codex --approval-mode full-auto "You are working on GitHub issue #<NUMBER> in repo l1veIn/nanobot-auto. The issue title is: <TITLE>. The issue body is: <BODY>. Please read the relevant source code, implement the fix or enhancement, and run 'python -m py_compile' on any modified .py files to verify syntax. If there are tests in tests/, run 'python -m pytest tests/ -x --tb=short' as well."
```

Wait for Codex to complete. If Codex fails or is not available, skip to cleanup.

## Step 4: Verify Codex output

```bash
cd "$WORK_DIR" && git diff --stat
```

If no changes were made, skip to cleanup.

## Step 5: Commit, push, create PR

```bash
cd "$WORK_DIR"
git add -A
git commit -m "fix: <description> (closes #<NUMBER>)"
git push origin fix/issue-<NUMBER>
gh pr create --repo l1veIn/nanobot-auto \
  --title "fix: <description>" \
  --body "Closes #<NUMBER> — developed by Codex in full-auto mode."
```

## Step 6: Cleanup

Always run this, even if previous steps failed:

```bash
rm -rf "$WORK_DIR"
```

The bot's running directory is never touched. Safe, isolated, disposable.
