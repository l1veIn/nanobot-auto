---
name: auto-dev
description: "Pick an open auto-report issue, use Codex YOLO mode to develop a fix, then create a pull request."
metadata: {"nanobot":{"emoji":"🛠️","requires":{"bins":["gh","git","codex"]}}}
---

# Auto Dev

Pick an open issue, delegate development to Codex, and submit a PR.

**IMPORTANT**: You are the project manager, NOT the developer. Your job is to find the issue, set up the branch, call Codex to do the work, and submit the PR. Do NOT write code yourself — let Codex do it.

## Step 1: Find an issue

```bash
gh issue list --repo l1veIn/nanobot-auto --label auto-report --state open --json number,title,body --limit 1
```

If no issues found, stop.

## Step 2: Prepare branch

```bash
git checkout main
git pull origin main
git checkout -b fix/issue-<NUMBER>
```

## Step 3: Delegate to Codex (YOLO mode)

This is the core step. Run Codex in full-auto mode and let it handle everything:

```bash
codex --approval-mode full-auto "You are working on GitHub issue #<NUMBER> in repo l1veIn/nanobot-auto. The issue title is: <TITLE>. The issue body is: <BODY>. Please read the relevant source code, implement the fix or enhancement, and run 'python -m py_compile' on any modified .py files to verify syntax. If there are tests in tests/, run 'python -m pytest tests/ -x --tb=short' as well."
```

Wait for Codex to complete. If Codex fails or is not available:
- Log the failure
- Abandon this issue for now (do NOT attempt manual development)

## Step 4: Verify Codex output

Check if Codex actually made changes:

```bash
git diff --stat
```

If no changes were made, abandon — Codex couldn't solve it.

## Step 5: Commit, push, create PR

```bash
git add -A
git commit -m "fix: <description> (closes #<NUMBER>)"
git push origin fix/issue-<NUMBER>
gh pr create --repo l1veIn/nanobot-auto \
  --title "fix: <description>" \
  --body "Closes #<NUMBER> — developed by Codex in full-auto mode."
git checkout main
```
