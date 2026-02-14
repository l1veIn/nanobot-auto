#!/bin/bash
# Log digest tool for log-miner skill.
# Produces a compact summary of recent logs to avoid context overflow.
# Usage: log-digest.sh [hours=24]

HOURS=${1:-24}
SESSIONS_DIR="$HOME/.nanobot/sessions"
FIND_ARGS="-name *.jsonl -mmin -$((HOURS * 60))"

echo "=== Log Digest (past ${HOURS}h) ==="
echo ""

# Stats
TOTAL_FILES=$(find "$SESSIONS_DIR" $FIND_ARGS 2>/dev/null | wc -l | tr -d ' ')
TOTAL_LINES=$(find "$SESSIONS_DIR" $FIND_ARGS -exec cat {} + 2>/dev/null | wc -l | tr -d ' ')
echo "Files: $TOTAL_FILES | Lines: $TOTAL_LINES"
echo ""

# Error summary (deduplicated, with counts)
echo "=== Errors (deduplicated) ==="
find "$SESSIONS_DIR" $FIND_ARGS -exec grep -hi 'error\|failed\|timeout\|traceback\|exception\|panic' {} + 2>/dev/null \
  | sed 's/.*"content":"\([^"]*\)".*/\1/' \
  | sort | uniq -c | sort -rn | head -20
echo ""

# Session activity summary (one line per file)
echo "=== Session Activity ==="
find "$SESSIONS_DIR" $FIND_ARGS -print 2>/dev/null | while read f; do
  LINES=$(wc -l < "$f" | tr -d ' ')
  BASENAME=$(basename "$f")
  FIRST_ROLE=$(head -1 "$f" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('role','?'))" 2>/dev/null || echo "?")
  echo "  $BASENAME: ${LINES} turns, starts with: $FIRST_ROLE"
done
echo ""

# Tool usage frequency
echo "=== Tool Usage ==="
find "$SESSIONS_DIR" $FIND_ARGS -exec grep -ho '"tool_calls"' {} + 2>/dev/null | wc -l | tr -d ' ' | xargs -I{} echo "  Tool calls: {}"
find "$SESSIONS_DIR" $FIND_ARGS -exec cat {} + 2>/dev/null \
  | grep -o '"name":"[^"]*"' | sed 's/"name":"//;s/"//' \
  | sort | uniq -c | sort -rn | head -10
