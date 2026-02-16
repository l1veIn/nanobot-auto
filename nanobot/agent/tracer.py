"""
Event tracer — XES-compatible event logging for nanobot agent tool calls.

Writes JSONL event logs to .logs/trace_{case_id}.jsonl.
Each tool call is one event. No LLM involved — pure deterministic recording.

XES standard fields used:
- case_id: identifies the cycle/session (e.g., "20250216_cron_01")
- concept:name: activity name (tool name)
- time:timestamp: ISO8601 timestamp
- lifecycle:transition: "start" or "complete"
- org:resource: who invoked this (skill name or "agent")
- outcome: "success" or "error"
"""

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path

# Default log directory
_LOG_DIR: Path | None = None
_CURRENT_CASE_ID: str | None = None
_CURRENT_SKILL: str = "agent"


def configure(log_dir: str | Path, case_id: str | None = None, skill: str = "agent"):
    """Configure the tracer. Call once at startup."""
    global _LOG_DIR, _CURRENT_CASE_ID, _CURRENT_SKILL
    _LOG_DIR = Path(log_dir)
    _LOG_DIR.mkdir(parents=True, exist_ok=True)
    _CURRENT_CASE_ID = case_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    _CURRENT_SKILL = skill


def set_skill(skill: str):
    """Update the current skill context (e.g., when switching skills)."""
    global _CURRENT_SKILL
    _CURRENT_SKILL = skill


def set_case_id(case_id: str):
    """Update the current case ID (e.g., for a new cycle)."""
    global _CURRENT_CASE_ID
    _CURRENT_CASE_ID = case_id


def _log_file() -> Path | None:
    """Get the current log file path."""
    if _LOG_DIR is None or _CURRENT_CASE_ID is None:
        return None
    return _LOG_DIR / f"trace_{_CURRENT_CASE_ID}.jsonl"


def log_event(
    activity: str,
    lifecycle: str = "complete",
    outcome: str = "success",
    duration_ms: int | None = None,
    detail: str | None = None,
    **extra,
):
    """
    Write a single XES-compatible event to the log file.
    
    Args:
        activity: The tool/action name (concept:name in XES)
        lifecycle: "start" or "complete" (lifecycle:transition in XES)
        outcome: "success" or "error"
        duration_ms: Execution time in milliseconds (if lifecycle="complete")
        detail: Optional short detail string (truncated to 200 chars)
        **extra: Additional attributes to record
    """
    log_file = _log_file()
    if log_file is None:
        return  # Tracer not configured, silently skip

    event = {
        "case_id": _CURRENT_CASE_ID,
        "concept:name": activity,
        "time:timestamp": datetime.now(timezone.utc).isoformat(),
        "lifecycle:transition": lifecycle,
        "org:resource": _CURRENT_SKILL,
        "outcome": outcome,
    }

    if duration_ms is not None:
        event["duration_ms"] = duration_ms
    if detail:
        event["detail"] = detail[:200]
    if extra:
        event.update(extra)

    try:
        with open(log_file, "a") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
    except OSError:
        pass  # Never crash the agent for logging failures


class ToolTracer:
    """
    Context manager for tracing a tool call.
    
    Usage:
        with ToolTracer("read_file", args_summary="path=/tmp/foo.py") as t:
            result = await tool.execute(**params)
            t.set_result(result)
    """

    def __init__(self, tool_name: str, args_summary: str = ""):
        self.tool_name = tool_name
        self.args_summary = args_summary[:200]
        self.start_time = 0.0
        self.outcome = "success"
        self.detail = ""

    def __enter__(self):
        self.start_time = time.monotonic()
        log_event(
            activity=self.tool_name,
            lifecycle="start",
            detail=self.args_summary,
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = int((time.monotonic() - self.start_time) * 1000)
        if exc_type is not None:
            self.outcome = "error"
            self.detail = str(exc_val)[:200] if exc_val else "exception"

        log_event(
            activity=self.tool_name,
            lifecycle="complete",
            outcome=self.outcome,
            duration_ms=duration,
            detail=self.detail,
        )
        return False  # Don't suppress exceptions

    def set_result(self, result: str):
        """Check if result indicates an error."""
        if result.startswith("Error"):
            self.outcome = "error"
            self.detail = result[:200]
