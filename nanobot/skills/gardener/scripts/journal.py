#!/usr/bin/env python3
"""
journal.py — Memory read/write for the Gardener skill.

Manages journal.md in the target repository root.

Usage:
    python3 journal.py <repo_path> write --function <name> --result <Success|Fail> --reason <text>
    python3 journal.py <repo_path> read [--days N]

journal.md format (STRICT — one entry per line, pipe-delimited):
    # Gardener Journal
    [2025-02-16] | target: nanobot/agent/tools/base.py::Tool._validate | status: Success | cc: 27->18 | reason: Extracted validation helpers
    [2025-02-16] | target: nanobot/channels/email.py::_fetch_messages | status: Fail | cc: 22->22 | reason: Tests failed after extracting loop body
"""

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path


HEADER = "# Gardener Journal\n\n"


def ensure_journal(repo_path: str) -> Path:
    """Ensure journal.md exists, return its path."""
    journal = Path(repo_path) / "journal.md"
    if not journal.exists():
        journal.write_text(HEADER)
    return journal


def write_entry(repo_path: str, function: str, result: str, reason: str, old_cc: int = 0, new_cc: int = 0):
    """Append a pipe-delimited entry to journal.md."""
    journal = ensure_journal(repo_path)
    date_str = datetime.now().strftime("%Y-%m-%d")
    cc_str = f"{old_cc}->{new_cc}" if result == "Success" else f"{old_cc}->{old_cc}"
    entry = f"[{date_str}] | target: {function} | status: {result} | cc: {cc_str} | reason: {reason}\n"
    
    with open(journal, "a") as f:
        f.write(entry)
    
    print(f"📝 Journal: {entry.strip()}")


def read_journal_failures(repo_path: str, skip_days: int = 3) -> set[str]:
    """Read journal.md, return set of function identifiers that failed recently."""
    journal = Path(repo_path) / "journal.md"
    if not journal.exists():
        return set()

    skip_since = datetime.now() - timedelta(days=skip_days)
    recently_failed = set()

    for line in journal.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Strict pipe-delimited: [date] | target: X | status: Y | cc: Z | reason: W
        try:
            parts = [p.strip() for p in line.split("|")]
            date_str = parts[0].strip("[] ")
            entry_date = datetime.strptime(date_str, "%Y-%m-%d")
            if entry_date < skip_since:
                continue

            status_part = next((p for p in parts if p.startswith("status:")), None)
            target_part = next((p for p in parts if p.startswith("target:")), None)
            if status_part and "Fail" in status_part and target_part:
                func_id = target_part.split(":", 1)[1].strip()
                recently_failed.add(func_id)
        except (IndexError, ValueError):
            continue

    return recently_failed


def read_entries(repo_path: str, days: int = 7):
    """Read and display recent journal entries."""
    journal = Path(repo_path) / "journal.md"
    if not journal.exists():
        print("No journal found.")
        return

    since = datetime.now() - timedelta(days=days)
    entries = []
    
    for line in journal.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        try:
            parts = [p.strip() for p in line.split("|")]
            date_str = parts[0].strip("[] ")
            entry_date = datetime.strptime(date_str, "%Y-%m-%d")
            if entry_date >= since:
                entries.append(line)
        except (IndexError, ValueError):
            continue

    if entries:
        print(f"Recent entries (last {days} days):")
        for e in entries:
            print(f"  {e}")
        
        successes = sum(1 for e in entries if "status: Success" in e)
        fails = sum(1 for e in entries if "status: Fail" in e)
        print(f"\n  Total: {len(entries)} | ✅ {successes} | ❌ {fails}")
    else:
        print(f"No entries in the last {days} days.")


def main():
    parser = argparse.ArgumentParser(description="Gardener journal manager")
    parser.add_argument("repo_path", help="Path to the target repository")
    sub = parser.add_subparsers(dest="command", required=True)

    # write
    w = sub.add_parser("write", help="Write a journal entry")
    w.add_argument("--function", required=True, help="Qualified function name (file::class.func)")
    w.add_argument("--result", required=True, choices=["Success", "Fail"], help="Outcome")
    w.add_argument("--reason", required=True, help="One-line explanation")
    w.add_argument("--old-cc", type=int, default=0, help="Original complexity")
    w.add_argument("--new-cc", type=int, default=0, help="New complexity")

    # read
    r = sub.add_parser("read", help="Read recent journal entries")
    r.add_argument("--days", type=int, default=7, help="Show entries from last N days")

    args = parser.parse_args()

    if args.command == "write":
        write_entry(args.repo_path, args.function, args.result, args.reason, args.old_cc, args.new_cc)
    elif args.command == "read":
        read_entries(args.repo_path, args.days)


if __name__ == "__main__":
    main()
