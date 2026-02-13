---
name: auto-merge
description: "Review open PRs, merge if CI passes, close if CI fails, then self-update."
metadata: {"nanobot":{"emoji":"🔀","requires":{"bins":["gh","git"]}}}
---

# Auto Merge

Review open PRs and merge those that pass CI. Self-update after merge.

## When triggered

This skill runs as a daily cron task.

## Step 1: List open PRs

```bash
gh pr list --repo l1veIn/nanobot-auto --state open --json number,title,headRefName --jq '.[] | "\(.number) \(.title)"'
```

If no PRs found, stop — nothing to do.

## Step 2: Check CI status for each PR

```bash
gh pr checks <NUMBER> --repo l1veIn/nanobot-auto
```

Classify each PR:
- **All checks passed** → ready to merge
- **Checks failed** → close with comment
- **Checks pending** → skip, will retry next run

## Step 3: Merge passing PRs

```bash
gh pr merge <NUMBER> --repo l1veIn/nanobot-auto --squash --delete-branch
```

## Step 4: Close failing PRs

```bash
gh pr close <NUMBER> --repo l1veIn/nanobot-auto --comment "CI checks failed. Closing this PR.

Failed checks:
<list failed check names and details>"
```

## Step 5: Self-update

After any successful merge, pull latest code and reinstall:

```bash
git checkout main
git pull origin main
pip install -e .
```

Report what was merged and updated.
