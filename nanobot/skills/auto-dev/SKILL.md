---
name: auto-dev
description: "Pick an open auto-report issue, develop a fix, verify with py_compile, and create a pull request."
metadata: {"nanobot":{"emoji":"🛠️","requires":{"bins":["gh","git"]}}}
---

# Auto Dev

Pick an open issue, develop a fix, and submit a PR.

## When triggered

This skill runs as a daily cron task. Process one issue per run.

## Step 1: Find an issue to work on

```bash
gh issue list --repo l1veIn/nanobot-auto --label auto-report --state open --json number,title,body --limit 1
```

If no issues found, stop — nothing to do.

## Step 2: Analyze the issue

Read the issue title and body. Understand:
- What is the problem?
- Which file(s) need to be changed?
- What is the expected fix?

## Step 3: Prepare workspace

```bash
git checkout main
git pull origin main
git checkout -b fix/issue-<NUMBER>
```

## Step 4: Develop the fix

Use `read_file` to examine the relevant source files. Use `write_file` or `edit_file` to make changes.

Rules:
- **Minimal changes only** — fix the reported issue, nothing else
- **Do not modify** files outside `nanobot/` directory unless necessary
- **Add comments** explaining the change (in English)

## Step 5: Verify

Run syntax check on every modified `.py` file:

```bash
python -m py_compile <modified_file.py>
```

If any file fails compilation, revert the change and try a different approach.

If tests exist, run them:

```bash
python -m pytest tests/ -x --tb=short 2>&1 | tail -30
```

If tests fail, investigate and fix. If you cannot fix tests, abandon this issue.

## Step 6: Commit and push

```bash
git add -A
git commit -m "fix: <concise description> (closes #<NUMBER>)"
git push origin fix/issue-<NUMBER>
```

## Step 7: Create PR

```bash
gh pr create --repo l1veIn/nanobot-auto \
  --title "fix: <concise description>" \
  --body "Closes #<NUMBER>

## Changes
- <list what was changed and why>

## Verification
- py_compile: ✅
- pytest: ✅ / ⚠️ no tests / ❌ (details)"
```

## Step 8: Clean up

```bash
git checkout main
```
