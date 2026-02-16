#!/usr/bin/env python3
"""
scanner.py — Deterministic complexity scanner for the Gardener skill.

Uses `radon` to find the highest cyclomatic-complexity functions in a repo.
Checks journal.md to skip recently-failed targets.

Usage:
    python3 scanner.py <repo_path> [--top N] [--skip-days D]

Output:
    JSON list of targets, sorted by complexity (highest first).
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


def scan_complexity(repo_path: str) -> list[dict]:
    """Run radon cc on the repo, return parsed results."""
    result = subprocess.run(
        ["radon", "cc", repo_path, "-j", "-n", "C"],  # -n C = only show C+ (complexity >= 11)
        capture_output=True, text=True, cwd=repo_path
    )
    if result.returncode != 0:
        # radon returns 0 even with results; non-zero is an error
        print(f"radon error: {result.stderr}", file=sys.stderr)
        # Try without -n filter (show all)
        result = subprocess.run(
            ["radon", "cc", repo_path, "-j"],
            capture_output=True, text=True, cwd=repo_path
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Failed to parse radon output: {result.stdout[:200]}", file=sys.stderr)
        return []

    # radon -j output: { "filepath": [ {type, name, complexity, lineno, ...}, ... ], ... }
    targets = []
    for filepath, blocks in data.items():
        for block in blocks:
            targets.append({
                "file": filepath,
                "function": block.get("name", "unknown"),
                "complexity": block.get("complexity", 0),
                "line": block.get("lineno", 0),
                "rank": block.get("rank", "?"),
                "type": block.get("type", "function"),
                "classname": block.get("classname", None),
            })

    # Sort by complexity, highest first
    targets.sort(key=lambda t: t["complexity"], reverse=True)
    return targets


def read_journal(repo_path: str, skip_days: int = 3) -> set[str]:
    """Read journal.md, return set of function identifiers that failed recently."""
    journal_path = Path(repo_path) / "journal.md"
    if not journal_path.exists():
        return set()

    skip_since = datetime.now() - timedelta(days=skip_days)
    recently_failed = set()

    for line in journal_path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        # Pipe-delimited: [date] | target: file::func | status: X | cc: Y | reason: Z
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


def select_targets(
    targets: list[dict],
    recently_failed: set[str],
    top_n: int = 3,
) -> list[dict]:
    """Select top N targets, skipping recently failed ones."""
    selected = []
    for t in targets:
        # Build a qualified name for matching
        name = t["function"]
        if t.get("classname"):
            name = f"{t['classname']}.{t['function']}"

        if name in recently_failed:
            t["skipped"] = True
            t["skip_reason"] = "recently failed (see journal.md)"
            continue

        selected.append(t)
        if len(selected) >= top_n:
            break

    return selected


def main():
    parser = argparse.ArgumentParser(description="Gardener complexity scanner")
    parser.add_argument("repo_path", help="Path to the target repository")
    parser.add_argument("--top", type=int, default=3, help="Number of targets to return")
    parser.add_argument("--skip-days", type=int, default=3, help="Skip functions that failed within N days")
    args = parser.parse_args()

    repo = args.repo_path
    if not Path(repo).is_dir():
        print(f"Error: {repo} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Sense: deterministic scan
    all_targets = scan_complexity(repo)
    if not all_targets:
        print(json.dumps({"targets": [], "message": "No complexity targets found (all functions are clean!)"}))
        sys.exit(0)

    # Memory: check journal
    recently_failed = read_journal(repo, skip_days=args.skip_days)

    # Select
    selected = select_targets(all_targets, recently_failed, top_n=args.top)

    output = {
        "targets": selected,
        "total_scanned": len(all_targets),
        "skipped_from_journal": len(recently_failed),
        "avg_complexity": round(sum(t["complexity"] for t in all_targets) / len(all_targets), 2),
        "max_complexity": all_targets[0]["complexity"] if all_targets else 0,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
