#!/usr/bin/env python3
"""
scanner.py — Deterministic complexity scanner for the Gardener skill.

Supports multiple languages:
  - Python: uses `radon cc` for cyclomatic complexity
  - Rust:   uses `cargo clippy` cognitive_complexity lint

Auto-detects language from repo contents (Cargo.toml → Rust, else → Python).

Usage:
    python3 scanner.py <repo_path> [--top N] [--skip-days D] [--lang python|rust]

Output:
    JSON list of targets, sorted by complexity (highest first).
"""

import argparse
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path


# ─── Language detection ───────────────────────────────────────────────

def detect_language(repo_path: str) -> str:
    """Auto-detect project language from repo contents."""
    repo = Path(repo_path)
    if (repo / "Cargo.toml").exists():
        return "rust"
    if any((repo / f).exists() for f in ["pyproject.toml", "setup.py", "setup.cfg", "requirements.txt"]):
        return "python"
    # Fallback: count files
    rs_count = len(list(repo.rglob("*.rs")))
    py_count = len(list(repo.rglob("*.py")))
    return "rust" if rs_count > py_count else "python"


# ─── Python backend (radon) ──────────────────────────────────────────

def scan_python(repo_path: str) -> list[dict]:
    """Run radon cc on the repo, return parsed results."""
    result = subprocess.run(
        ["radon", "cc", repo_path, "-j", "-n", "C"],
        capture_output=True, text=True, cwd=repo_path
    )
    if result.returncode != 0:
        print(f"radon error: {result.stderr}", file=sys.stderr)
        result = subprocess.run(
            ["radon", "cc", repo_path, "-j"],
            capture_output=True, text=True, cwd=repo_path
        )

    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Failed to parse radon output: {result.stdout[:200]}", file=sys.stderr)
        return []

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
                "lang": "python",
            })

    targets.sort(key=lambda t: t["complexity"], reverse=True)
    return targets


# ─── Rust backend (cargo clippy) ─────────────────────────────────────

def scan_rust(repo_path: str) -> list[dict]:
    """
    Use cargo clippy's cognitive_complexity lint to find complex functions.
    
    Strategy: set cognitive-complexity-threshold to 1, so clippy reports ALL
    functions with complexity > 1. Parse the JSON diagnostics output.
    """
    # Create a temporary clippy.toml with threshold=1 to catch everything
    clippy_toml = Path(repo_path) / "clippy.toml"
    clippy_existed = clippy_toml.exists()
    original_content = clippy_toml.read_text() if clippy_existed else None

    try:
        # Write temporary config (restore later)
        clippy_toml.write_text("cognitive-complexity-threshold = 1\n")

        result = subprocess.run(
            ["cargo", "clippy", "--message-format=json", "--", "-W", "clippy::cognitive_complexity"],
            capture_output=True, text=True, cwd=repo_path,
            timeout=300,
            env={**os.environ, "CARGO_TERM_COLOR": "never"},
        )
    finally:
        # Restore original clippy.toml
        if original_content is not None:
            clippy_toml.write_text(original_content)
        elif clippy_toml.exists():
            clippy_toml.unlink()

    targets = []
    seen = set()

    for line in result.stdout.splitlines():
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        if msg.get("reason") != "compiler-message":
            continue

        diag = msg.get("message", {})
        # Look for cognitive_complexity warnings
        if "cognitive_complexity" not in diag.get("code", {}).get("code", ""):
            continue

        text = diag.get("message", "")
        # Extract complexity from message like:
        # "the function has a cognitive complexity of (28/1)"
        cc_match = re.search(r"cognitive complexity of \((\d+)/\d+\)", text)
        if not cc_match:
            continue
        complexity = int(cc_match.group(1))

        # Get file location and function name from spans
        spans = diag.get("spans", [])
        if not spans:
            continue
        primary = next((s for s in spans if s.get("is_primary")), spans[0])
        file_path = primary.get("file_name", "unknown")
        line_num = primary.get("line_start", 0)

        # Extract function name from the span's source text
        # e.g. "pub fn resolve_home(" or "pub async fn run_dora("
        func_name = "unknown"
        span_texts = primary.get("text", [])
        if span_texts:
            source_line = span_texts[0].get("text", "")
            fn_match = re.search(r"\bfn\s+(\w+)\s*[(<]", source_line)
            if fn_match:
                func_name = fn_match.group(1)

        # Deduplicate
        key = f"{file_path}::{func_name}:{line_num}"
        if key in seen:
            continue
        seen.add(key)

        targets.append({
            "file": file_path,
            "function": func_name,
            "complexity": complexity,
            "line": line_num,
            "rank": _rank(complexity),
            "type": "function",
            "classname": None,
            "lang": "rust",
        })

    targets.sort(key=lambda t: t["complexity"], reverse=True)
    return targets


def _rank(cc: int) -> str:
    """Map complexity score to letter grade (like radon)."""
    if cc <= 5: return "A"
    if cc <= 10: return "B"
    if cc <= 20: return "C"
    if cc <= 30: return "D"
    return "F"


# ─── Journal reader (language-agnostic) ──────────────────────────────

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


# ─── Target selection (language-agnostic) ─────────────────────────────

def select_targets(
    targets: list[dict],
    recently_failed: set[str],
    top_n: int = 3,
) -> list[dict]:
    """Select top N targets, skipping recently failed ones."""
    selected = []
    for t in targets:
        name = t["function"]
        if t.get("classname"):
            name = f"{t['classname']}.{t['function']}"

        # Also build file::func key for journal matching
        file_func_key = f"{t['file']}::{name}"

        if name in recently_failed or file_func_key in recently_failed:
            t["skipped"] = True
            t["skip_reason"] = "recently failed (see journal.md)"
            continue

        selected.append(t)
        if len(selected) >= top_n:
            break

    return selected


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Gardener complexity scanner")
    parser.add_argument("repo_path", help="Path to the target repository")
    parser.add_argument("--top", type=int, default=3, help="Number of targets to return")
    parser.add_argument("--skip-days", type=int, default=3, help="Skip functions that failed within N days")
    parser.add_argument("--lang", choices=["python", "rust"], default=None, help="Override language detection")
    args = parser.parse_args()

    repo = args.repo_path
    if not Path(repo).is_dir():
        print(f"Error: {repo} is not a directory", file=sys.stderr)
        sys.exit(1)

    # Detect language
    lang = args.lang or detect_language(repo)
    print(f"🌿 Detected language: {lang}", file=sys.stderr)

    # Sense: deterministic scan
    if lang == "python":
        all_targets = scan_python(repo)
    elif lang == "rust":
        all_targets = scan_rust(repo)
    else:
        print(f"Error: unsupported language '{lang}'", file=sys.stderr)
        sys.exit(1)

    if not all_targets:
        print(json.dumps({"targets": [], "lang": lang, "message": "No complexity targets found (all functions are clean!)"}))
        sys.exit(0)

    # Memory: check journal
    recently_failed = read_journal(repo, skip_days=args.skip_days)

    # Select
    selected = select_targets(all_targets, recently_failed, top_n=args.top)

    output = {
        "lang": lang,
        "targets": selected,
        "total_scanned": len(all_targets),
        "skipped_from_journal": len(recently_failed),
        "avg_complexity": round(sum(t["complexity"] for t in all_targets) / len(all_targets), 2),
        "max_complexity": all_targets[0]["complexity"] if all_targets else 0,
    }

    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
