---
name: auto-dev
description: "Pick an open auto-report issue, use Codex to develop a fix in an isolated workspace, then create a pull request."
metadata: {"nanobot":{"emoji":"🛠️","requires":{"bins":["gh","git","codex"]}}}
---

# Auto Dev

Pick an open issue, delegate development to Codex in an **isolated workspace**, and submit a PR.

## ⛔ Hard Rules (NEVER violate)

1. **You are the project manager, NOT the developer.** You MUST NOT write, edit, or modify any source code yourself. All code changes come from Codex ONLY.
2. **Never modify your own running directory.** All work happens in `/tmp`.
3. **If Codex fails or produces no changes → STOP.** Do not attempt manual fixes. Do not write code. Just clean up and report "Codex failed" in the issue comment.
4. **Never modify production code to make tests pass.** If tests fail, the fix is wrong — abandon.

## Step 1: Find an issue

```bash
gh issue list --repo l1veIn/nanobot-auto --label auto-report --state open --json number,title,body --limit 1
```

If no issues found, stop.

## Step 2: Create isolated workspace

```bash
WORK_DIR=$(mktemp -d)/nanobot-auto
git clone git@github.com:l1veIn/nanobot-auto.git "$WORK_DIR"
cd "$WORK_DIR"
git checkout -b fix/issue-<NUMBER>
```

## Step 3: Delegate to Codex

Run Codex in the isolated workspace. **This is the ONLY step that produces code changes.**

```bash
cd "$WORK_DIR" && codex --approval-mode full-auto \
  "You are working on GitHub issue #<NUMBER> in repo l1veIn/nanobot-auto.
   Title: <TITLE>
   Body: <BODY>
   
   Rules:
   - Read the relevant source code first
   - Implement the fix or enhancement
   - Do NOT modify production code just to make tests pass
   - Run 'python -m py_compile' on any modified .py files
   - If there are tests, run 'python -m pytest tests/ -x --tb=short'"
```

Wait for Codex to complete.

## Step 4: Verify output

```bash
cd "$WORK_DIR" && git diff --stat
```

**Decision tree:**
- No changes → go to Step 6 (cleanup)
- Changes exist → check if they make sense for the issue
- Production code modified just for test convenience → `git checkout -- <file>` to revert, then go to Step 6

## Step 5: Commit, push, create PR

```bash
cd "$WORK_DIR"
git add -A
git commit -m "fix: <description> (closes #<NUMBER>)"
git push origin fix/issue-<NUMBER>
gh pr create --repo l1veIn/nanobot-auto \
  --title "fix: <description>" \
  --body "Closes #<NUMBER>

Developed by Codex in full-auto mode. Changes:
<paste git diff --stat output here>"
```

## Step 6: Cleanup

Always run this, even if previous steps failed:

```bash
rm -rf "$WORK_DIR"
```

## Step 7: Report failure (if applicable)

If Codex failed or produced no usable changes, comment on the issue:

```bash
gh issue comment <NUMBER> --repo l1veIn/nanobot-auto \
  --body "auto-dev attempted this issue but Codex could not produce a valid fix. Leaving open for next cycle or manual intervention."
```

This ensures the issue stays visible and the system learns what kind of tasks Codex struggles with.
