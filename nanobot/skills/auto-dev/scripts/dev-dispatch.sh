#!/bin/bash
# dev-dispatch.sh — Run Codex on an issue in background, then create PR.
# Called by auto-dev skill via: nohup bash nanobot/skills/auto-dev/scripts/dev-dispatch.sh <ISSUE_NUMBER> &
#
# This script runs independently of nanobot. It:
# 1. Clones the repo to a temp dir
# 2. Runs Codex with a timeout
# 3. If Codex produces changes, commits, pushes, and creates a PR
# 4. Always cleans up, even on failure or timeout

CODEX_TIMEOUT=600  # 10 minutes max for Codex
ISSUE_NUMBER=$1
REPO="l1veIn/nanobot-auto"
WORK_DIR=""

# === Cleanup trap — always runs, even on timeout/crash ===
cleanup() {
  if [ -n "$WORK_DIR" ] && [ -d "$WORK_DIR" ]; then
    rm -rf "$WORK_DIR"
    echo "Cleaned up $WORK_DIR"
  fi
  echo "=== dev-dispatch finished at $(date) ==="
}
trap cleanup EXIT

if [ -z "$ISSUE_NUMBER" ]; then
  echo "Usage: dev-dispatch.sh <issue_number>"
  exit 1
fi

LOG_FILE="$HOME/.nanobot/dev-dispatch-${ISSUE_NUMBER}.log"
exec > "$LOG_FILE" 2>&1

echo "=== dev-dispatch started at $(date) ==="
echo "Issue: #$ISSUE_NUMBER"
echo "Timeout: ${CODEX_TIMEOUT}s"

# Get issue details
ISSUE_JSON=$(gh issue view "$ISSUE_NUMBER" --repo "$REPO" --json title,body)
TITLE=$(echo "$ISSUE_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['title'])" 2>/dev/null || echo "unknown")
BODY=$(echo "$ISSUE_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin)['body'])" 2>/dev/null || echo "")

echo "Title: $TITLE"

# Clone to temp dir
WORK_DIR=$(mktemp -d)/nanobot-auto
echo "Cloning to $WORK_DIR..."
git clone "git@github.com:${REPO}.git" "$WORK_DIR"
cd "$WORK_DIR"

BRANCH="fix/issue-${ISSUE_NUMBER}"
git checkout -b "$BRANCH"

# Run Codex with timeout
echo "Running Codex (timeout: ${CODEX_TIMEOUT}s)..."
CODEX_EXIT=0
timeout "$CODEX_TIMEOUT" codex --approval-mode full-auto \
  "You are working on GitHub issue #${ISSUE_NUMBER} in repo ${REPO}.
Title: ${TITLE}
Body: ${BODY}

Rules:
- Read the relevant source code first
- Implement the fix or enhancement
- Do NOT modify production code just to make tests pass
- Run 'python -m py_compile' on any modified .py files
- If there are tests, run 'python -m pytest tests/ -x --tb=short'" \
  || CODEX_EXIT=$?

if [ "$CODEX_EXIT" -eq 124 ]; then
  echo "⚠️ Codex timed out after ${CODEX_TIMEOUT}s"
  gh issue comment "$ISSUE_NUMBER" --repo "$REPO" \
    --body "🤖 auto-dev: Codex timed out after ${CODEX_TIMEOUT}s. Task may be too complex. Leaving open for next cycle." \
    || true
  exit 1
elif [ "$CODEX_EXIT" -ne 0 ]; then
  echo "⚠️ Codex exited with code $CODEX_EXIT"
  gh issue comment "$ISSUE_NUMBER" --repo "$REPO" \
    --body "🤖 auto-dev: Codex failed (exit code: $CODEX_EXIT). Leaving open for next cycle." \
    || true
  exit 1
fi

# Check if Codex made changes
CHANGES=$(git diff --stat HEAD)
if [ -z "$CHANGES" ]; then
  echo "Codex produced no changes. Abandoning."
  gh issue comment "$ISSUE_NUMBER" --repo "$REPO" \
    --body "🤖 auto-dev: Codex ran successfully but produced no changes. Leaving open for next cycle."
  exit 0
fi

echo "Changes:"
echo "$CHANGES"

# Commit and push
git add -A
git commit -m "fix: ${TITLE} (closes #${ISSUE_NUMBER})"
git push origin "$BRANCH"

# Create PR
gh pr create --repo "$REPO" \
  --title "fix: ${TITLE}" \
  --body "Closes #${ISSUE_NUMBER}

Developed by Codex in full-auto mode.

Changes:
\`\`\`
${CHANGES}
\`\`\`"

echo "✅ PR created successfully."
