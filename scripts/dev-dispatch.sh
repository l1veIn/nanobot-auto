#!/bin/bash
# dev-dispatch.sh — Run Codex on an issue in background, then create PR.
# Called by auto-dev skill via: nohup bash scripts/dev-dispatch.sh <ISSUE_NUMBER> &
#
# This script runs independently of nanobot. It:
# 1. Clones the repo to a temp dir
# 2. Runs Codex in full-auto mode
# 3. If Codex produces changes, commits, pushes, and creates a PR
# 4. Cleans up

set -e

ISSUE_NUMBER=$1
REPO="l1veIn/nanobot-auto"

if [ -z "$ISSUE_NUMBER" ]; then
  echo "Usage: dev-dispatch.sh <issue_number>"
  exit 1
fi

LOG_FILE="$HOME/.nanobot/dev-dispatch-${ISSUE_NUMBER}.log"
exec > "$LOG_FILE" 2>&1

echo "=== dev-dispatch started at $(date) ==="
echo "Issue: #$ISSUE_NUMBER"

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

# Run Codex
echo "Running Codex..."
codex --approval-mode full-auto \
  "You are working on GitHub issue #${ISSUE_NUMBER} in repo ${REPO}.
Title: ${TITLE}
Body: ${BODY}

Rules:
- Read the relevant source code first
- Implement the fix or enhancement
- Do NOT modify production code just to make tests pass
- Run 'python -m py_compile' on any modified .py files
- If there are tests, run 'python -m pytest tests/ -x --tb=short'" \
  || true

# Check if Codex made changes
CHANGES=$(git diff --stat HEAD)
if [ -z "$CHANGES" ]; then
  echo "Codex produced no changes. Abandoning."
  gh issue comment "$ISSUE_NUMBER" --repo "$REPO" \
    --body "🤖 auto-dev dispatched Codex for this issue, but no changes were produced. Leaving open for next cycle."
  rm -rf "$WORK_DIR"
  echo "=== dev-dispatch finished (no changes) at $(date) ==="
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

echo "PR created successfully."

# Cleanup
rm -rf "$WORK_DIR"
echo "=== dev-dispatch finished (PR created) at $(date) ==="
