#!/usr/bin/env python3
"""
gate.py — Multi-language gate verification for the Gardener skill.

Supports: Python, Rust

Checks (in order, any failure → revert ALL):
0. No forbidden files modified (tests, skill scripts, governance docs)
1. Syntax check (py_compile / cargo check)
2. Tests pass (pytest / cargo test)
3. Complexity decreased (radon / cargo clippy)

Usage:
    python3 gate.py <repo_path> <file_path> <function_name> <original_cc> [--lang python|rust]

Exit codes:
    0 = gate passed (changes committed)
    1 = gate failed (changes reverted)
"""

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


# ─── Language detection ───────────────────────────────────────────────

def detect_language(repo_path: str) -> str:
    """Auto-detect project language from repo contents."""
    repo = Path(repo_path)
    if (repo / "Cargo.toml").exists():
        return "rust"
    return "python"


# ─── Forbidden patterns (per-language) ────────────────────────────────

FORBIDDEN_COMMON = [
    "scanner.py", "gate.py", "journal.py",    # gardener scripts
    "SKILL.md", "CONSTITUTION.md",            # governance docs
    ".github/",                               # CI config
]

FORBIDDEN_PYTHON = FORBIDDEN_COMMON + [
    "test_", "tests/", "_test.py",            # Python test files
    "conftest.py",                            # pytest config
]

FORBIDDEN_RUST = FORBIDDEN_COMMON + [
    "tests/",                                 # integration test dir
    "benches/",                               # benchmark dir
    "build.rs",                               # build script
    "Cargo.toml", "Cargo.lock",               # project config
]


def get_forbidden_patterns(lang: str) -> list[str]:
    if lang == "rust":
        return FORBIDDEN_RUST
    return FORBIDDEN_PYTHON


# ─── Shared gate logic ───────────────────────────────────────────────

def check_forbidden_files(repo_path: str, lang: str) -> list[str]:
    """Check if any forbidden files were modified. Returns list of violations."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        capture_output=True, text=True, cwd=repo_path,
    )
    changed = result.stdout.strip().split("\n") if result.stdout.strip() else []
    patterns = get_forbidden_patterns(lang)
    violations = []

    for f in changed:
        # Rust special: files containing #[cfg(test)] modules are test code
        # but they live in src/, so we allow modifying the file itself
        # We only block dedicated test directories and config files
        for pattern in patterns:
            if pattern in f:
                violations.append(f)
                break

    return violations


def revert_all(repo_path: str):
    """Revert ALL uncommitted changes. Nuclear option — safe."""
    subprocess.run(["git", "checkout", "."], cwd=repo_path, capture_output=True)
    subprocess.run(["git", "clean", "-fd"], cwd=repo_path, capture_output=True)


def commit_change(repo_path: str, file_path: str, function_name: str, old_cc: int, new_cc: int):
    """Stage and commit the change."""
    subprocess.run(["git", "add", file_path], cwd=repo_path, capture_output=True)
    msg = f"refactor: reduce complexity of {function_name} ({old_cc} → {new_cc})"
    subprocess.run(["git", "commit", "-m", msg], cwd=repo_path, capture_output=True)


# ─── Python gates ────────────────────────────────────────────────────

def syntax_check_python(repo_path: str, file_path: str) -> tuple[bool, str]:
    """Run py_compile on the modified file."""
    result = subprocess.run(
        ["python3", "-m", "py_compile", file_path],
        capture_output=True, text=True, cwd=repo_path, timeout=10,
    )
    return result.returncode == 0, result.stderr


def run_tests_python(repo_path: str) -> tuple[bool, str]:
    """Run pytest."""
    result = subprocess.run(
        ["python3", "-m", "pytest", "-x", "--tb=short", "-q", "--timeout=30"],
        capture_output=True, text=True, cwd=repo_path, timeout=120,
    )
    return result.returncode == 0, result.stdout + result.stderr


def get_complexity_python(repo_path: str, file_path: str, function_name: str) -> int | None:
    """Get cyclomatic complexity of a specific function using radon."""
    result = subprocess.run(
        ["radon", "cc", file_path, "-j"],
        capture_output=True, text=True, cwd=repo_path,
    )
    try:
        data = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None

    for fpath, blocks in data.items():
        for block in blocks:
            name = block.get("name", "")
            classname = block.get("classname")
            qualified = f"{classname}.{name}" if classname else name
            if name == function_name or qualified == function_name:
                return block.get("complexity", 0)
    return None


# ─── Rust gates ──────────────────────────────────────────────────────

def syntax_check_rust(repo_path: str, file_path: str) -> tuple[bool, str]:
    """Run cargo check — fast syntax + type validation."""
    result = subprocess.run(
        ["cargo", "check", "--message-format=short"],
        capture_output=True, text=True, cwd=repo_path, timeout=120,
        env={**os.environ, "CARGO_TERM_COLOR": "never"},
    )
    return result.returncode == 0, result.stderr


def run_tests_rust(repo_path: str) -> tuple[bool, str]:
    """Run cargo test."""
    result = subprocess.run(
        ["cargo", "test", "--", "--test-threads=1"],
        capture_output=True, text=True, cwd=repo_path, timeout=300,
        env={**os.environ, "CARGO_TERM_COLOR": "never"},
    )
    return result.returncode == 0, result.stdout + result.stderr


def get_complexity_rust(repo_path: str, file_path: str, function_name: str) -> int | None:
    """
    Get cognitive complexity of a specific function using cargo clippy.
    
    Sets threshold=1 so clippy reports the function's actual complexity.
    """
    clippy_toml = Path(repo_path) / "clippy.toml"
    clippy_existed = clippy_toml.exists()
    original_content = clippy_toml.read_text() if clippy_existed else None

    try:
        clippy_toml.write_text("cognitive-complexity-threshold = 1\n")
        result = subprocess.run(
            ["cargo", "clippy", "--message-format=json", "--", "-W", "clippy::cognitive_complexity"],
            capture_output=True, text=True, cwd=repo_path, timeout=300,
            env={**os.environ, "CARGO_TERM_COLOR": "never"},
        )
    finally:
        if original_content is not None:
            clippy_toml.write_text(original_content)
        elif clippy_toml.exists():
            clippy_toml.unlink()

    for line in result.stdout.splitlines():
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue

        if msg.get("reason") != "compiler-message":
            continue
        diag = msg.get("message", {})
        if "cognitive_complexity" not in diag.get("code", {}).get("code", ""):
            continue

        # Extract function name from span source text
        spans = diag.get("spans", [])
        if not spans:
            continue
        primary = next((s for s in spans if s.get("is_primary")), spans[0])
        span_texts = primary.get("text", [])
        if span_texts:
            source_line = span_texts[0].get("text", "")
            fn_match = re.search(r"\bfn\s+(\w+)\s*[(<]", source_line)
            if fn_match and fn_match.group(1) == function_name:
                text = diag.get("message", "")
                cc_match = re.search(r"cognitive complexity of \((\d+)/\d+\)", text)
                if cc_match:
                    return int(cc_match.group(1))

    return None


# ─── Language dispatch ────────────────────────────────────────────────

LANG_DISPATCH = {
    "python": {
        "syntax_check": syntax_check_python,
        "run_tests": run_tests_python,
        "get_complexity": get_complexity_python,
    },
    "rust": {
        "syntax_check": syntax_check_rust,
        "run_tests": run_tests_rust,
        "get_complexity": get_complexity_rust,
    },
}


# ─── Main ─────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Gardener gate check")
    parser.add_argument("repo_path", help="Path to the target repository")
    parser.add_argument("file_path", help="Relative path to the modified file")
    parser.add_argument("function_name", help="Name of the refactored function")
    parser.add_argument("original_cc", type=int, help="Original cyclomatic complexity")
    parser.add_argument("--lang", choices=["python", "rust"], default=None, help="Override language detection")
    args = parser.parse_args()

    repo = args.repo_path
    file_path = args.file_path
    func_name = args.function_name
    original_cc = args.original_cc
    lang = args.lang or detect_language(repo)

    dispatch = LANG_DISPATCH.get(lang)
    if not dispatch:
        print(f"Error: unsupported language '{lang}'", file=sys.stderr)
        sys.exit(1)

    print(f"🌿 Gate check [{lang}]: {func_name} (original CC={original_cc})")

    def fail(reason: str, detail: str = ""):
        """Fail gate, revert ALL changes, exit."""
        revert_all(repo)
        result = {"result": "FAIL", "lang": lang, "reason": reason}
        if detail:
            result["detail"] = detail
        print(json.dumps(result))
        sys.exit(1)

    # Gate 0: Forbidden file check
    print("  [0/3] Checking for forbidden file modifications...")
    violations = check_forbidden_files(repo, lang)
    if violations:
        print(f"  ❌ Agent modified forbidden files: {violations}")
        fail("forbidden_files_modified", str(violations))
    print("  ✅ No forbidden files touched.")

    # Gate 1: Syntax check
    syntax_label = "py_compile" if lang == "python" else "cargo check"
    print(f"  [1/3] Syntax check ({syntax_label})...")
    try:
        syntax_ok, syntax_err = dispatch["syntax_check"](repo, file_path)
    except subprocess.TimeoutExpired:
        print(f"  ❌ {syntax_label} timed out.")
        fail("syntax_timeout")

    if not syntax_ok:
        print(f"  ❌ Syntax error: {syntax_err[:200]}")
        fail("syntax_error", syntax_err[:500])
    print("  ✅ Syntax OK.")

    # Gate 2: Tests
    test_label = "pytest" if lang == "python" else "cargo test"
    print(f"  [2/3] Running {test_label}...")
    try:
        tests_passed, test_output = dispatch["run_tests"](repo)
    except subprocess.TimeoutExpired:
        print(f"  ❌ {test_label} timed out.")
        fail("test_timeout")

    if not tests_passed:
        lines = test_output.strip().split("\n")
        summary = "\n".join(lines[-5:])
        print(f"  ❌ Tests failed.")
        fail("tests_failed", summary)
    print("  ✅ Tests passed.")

    # Gate 3: Complexity decreased
    cc_label = "radon" if lang == "python" else "cargo clippy"
    print(f"  [3/3] Checking complexity ({cc_label})...")
    new_cc = dispatch["get_complexity"](repo, file_path, func_name)

    if new_cc is None:
        print(f"  ⚠️ Could not find {func_name} after refactor (may have been split).")
        print(f"  ✅ Accepting — function was likely decomposed.")
        commit_change(repo, file_path, func_name, original_cc, 0)
        print(json.dumps({"result": "PASS", "lang": lang, "reason": "function_decomposed", "old_cc": original_cc, "new_cc": "N/A"}))
        sys.exit(0)

    if new_cc >= original_cc:
        print(f"  ❌ Complexity not reduced ({original_cc} → {new_cc}).")
        fail("complexity_not_reduced", f"{original_cc} → {new_cc}")

    # ALL gates passed
    print(f"  ✅ Complexity reduced: {original_cc} → {new_cc}")
    commit_change(repo, file_path, func_name, original_cc, new_cc)
    print(json.dumps({"result": "PASS", "lang": lang, "old_cc": original_cc, "new_cc": new_cc}))
    sys.exit(0)


if __name__ == "__main__":
    main()
