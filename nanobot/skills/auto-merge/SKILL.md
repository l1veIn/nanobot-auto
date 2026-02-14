---
name: auto-merge
description: "Review open PRs with code quality checks, merge if CI passes AND code is sound, close if low quality, then self-update."
metadata: {"nanobot":{"emoji":"🔀","requires":{"bins":["gh","git"]}}}
---

# Auto Merge

Review open PRs: check CI, review code quality, merge good ones, reject bad ones. Self-update after merge.

> **Governed by [CONSTITUTION.md](../../CONSTITUTION.md)** — Articles 4, 6, 7. Enforces ALL articles.

## Step 1: List open PRs

```bash
gh pr list --repo l1veIn/nanobot-auto --state open --json number,title,headRefName --jq '.[] | "\(.number) \(.title)"'
```

If no PRs found, stop.

## Step 2: Check CI status

```bash
gh pr checks <NUMBER> --repo l1veIn/nanobot-auto
```

- **Checks failed** → go to Step 6 (close with reason)
- **Checks pending / no checks** → note CI status, but **still continue** to Step 3 and Step 4 (code review happens regardless)
- **All passed** → continue to Step 3

**Important:** Code review (Steps 3-4) ALWAYS runs, even without CI. A PR can be rejected by code review alone. A PR can only be MERGED if CI passes AND code review passes.

## Step 3: Constitution check (FIRST)

Before any code review, check if the PR touches protected files:

```bash
gh pr diff <NUMBER> --repo l1veIn/nanobot-auto --name-only
```

**If the diff includes ANY of these files → REJECT IMMEDIATELY:**
- `CONSTITUTION.md`
- `run.sh`

Close with:
```bash
gh pr close <NUMBER> --repo l1veIn/nanobot-auto --comment "❌ Constitutional violation. This PR modifies a protected file (CONSTITUTION.md or run.sh). These files may only be changed by the human operator. Rejected."
```

## Step 4: Code review

CI passing is NOT enough. You must review the actual changes:

```bash
gh pr diff <NUMBER> --repo l1veIn/nanobot-auto
```

**Review checklist — reject if ANY of these are true:**

1. **Production code modified just for tests** — e.g. making required params optional, adding dead code paths
2. **Signature changes to public APIs** — changing function signatures without clear justification from the issue
3. **More deletions than additions in core modules** — removing functionality without explanation
4. **Hardcoded paths, credentials, or secrets** in the diff
5. **Empty or trivial implementation** — functions that just `pass` or return constants
6. **Unrelated changes** — diff touches files not mentioned in the issue

**Accept if:**
- Changes are focused on what the issue describes
- No production code is modified unnecessarily
- Tests (if added) test real behavior, not mocked-out stubs
- Code compiles and makes logical sense

## Step 5: Merge good PRs

```bash
gh pr merge <NUMBER> --repo l1veIn/nanobot-auto --squash --delete-branch
```

## Step 6: Close bad PRs

For CI failures:
```bash
gh pr close <NUMBER> --repo l1veIn/nanobot-auto --comment "❌ CI checks failed. Closing.

Failed checks:
<list failed check names>"
```

For code quality issues:
```bash
gh pr close <NUMBER> --repo l1veIn/nanobot-auto --comment "❌ Code review failed. Closing.

Issues found:
<list specific problems, e.g. 'Modified SessionManager.__init__ signature to make workspace optional — this breaks callers'>

The original issue remains open for a better attempt next cycle."
```

## Step 7: Self-update and restart

After any successful merge, pull latest and restart:

```bash
git checkout main
git pull origin main
pip install -e .
```

Then exit so `run.sh` restarts with new code:

```bash
kill $$
```

**IMPORTANT**: Use `./run.sh` to start the bot, not `nanobot gateway` directly.
