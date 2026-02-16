#!/usr/bin/env python3
"""
gate.py — Triple-gate verification for the Gardener skill.

Checks:
0. No forbidden files modified (tests, skill scripts, constitution)
1. Modified files pass syntax check (py_compile)
2. pytest passes (tests not broken)
3. Complexity of the target function decreased

If ANY gate fails, reverts ALL changes with `git checkout .`

Usage:
    python3 gate.py <repo_path> <file_path> <function_name> <original_cc>

Exit codes:
    0 = gate passed (changes committed)
    1 = gate failed (changes reverted)
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Files/dirs the agent must NEVER modify
FORBIDDEN_PATTERNS = [
    "test_", "tests/", "_test.py",          # test files
    "conftest.py",                            # test config
    "scanner.py", "gate.py", "journal.py",    # gardener scripts (itself)
    "SKILL.md", "CONSTITUTION.md",            # governance docs
    ".github/",                               # CI config
]


def check_forbidden_files(repo_path: str) -> list[str]:
    """Check if any forbidden files were modified. Returns list of violations."""
    result = subprocess.run(
        ["git", "diff", "--name-only", "HEAD"],
        capture_output=True, text=True, cwd=repo_path,
    )
    changed = result.stdout.strip().split("\n") if result.stdout.strip() else []
    violations = []
    for f in changed:
        for pattern in FORBIDDEN_PATTERNS:
            if pattern in f:
                violations.append(f)
                break
    return violations


def syntax_check(repo_path: str, file_path: str) -> tuple[bool, str]:
    """Run py_compile on the modified file. Fast syntax validation."""
    result = subprocess.run(
        ["python3", "-m", "py_compile", file_path],
        capture_output=True, text=True, cwd=repo_path,
        timeout=10,
    )
    passed = result.returncode == 0
    output = result.stderr if not passed else ""
    return passed, output


def run_tests(repo_path: str) -> tuple[bool, str]:
    """Run pytest. Returns (passed, output)."""
    result = subprocess.run(
        ["python3", "-m", "pytest", "-x", "--tb=short", "-q", "--timeout=30"],
        capture_output=True, text=True, cwd=repo_path,
        timeout=120,
    )
    passed = result.returncode == 0
    output = result.stdout + result.stderr
    return passed, output


def get_function_complexity(repo_path: str, file_path: str, function_name: str) -> int | None:
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


def revert_all(repo_path: str):
    """Revert ALL uncommitted changes. Nuclear option — safe."""
    subprocess.run(
        ["git", "checkout", "."],
        cwd=repo_path, capture_output=True,
    )
    # Also clean any new untracked files the agent might have created
    subprocess.run(
        ["git", "clean", "-fd"],
        cwd=repo_path, capture_output=True,
    )


def commit_change(repo_path: str, file_path: str, function_name: str, old_cc: int, new_cc: int):
    """Stage and commit the change."""
    subprocess.run(["git", "add", file_path], cwd=repo_path, capture_output=True)
    msg = f"refactor: reduce complexity of {function_name} ({old_cc} → {new_cc})"
    subprocess.run(["git", "commit", "-m", msg], cwd=repo_path, capture_output=True)


def main():
    parser = argparse.ArgumentParser(description="Gardener gate check")
    parser.add_argument("repo_path", help="Path to the target repository")
    parser.add_argument("file_path", help="Relative path to the modified file")
    parser.add_argument("function_name", help="Name of the refactored function")
    parser.add_argument("original_cc", type=int, help="Original cyclomatic complexity")
    args = parser.parse_args()

    repo = args.repo_path
    file_path = args.file_path
    func_name = args.function_name
    original_cc = args.original_cc

    print(f"🌿 Gate check: {func_name} (original CC={original_cc})")

    def fail(reason: str, detail: str = ""):
        """Fail gate, revert ALL changes, exit."""
        revert_all(repo)
        result = {"result": "FAIL", "reason": reason}
        if detail:
            result["detail"] = detail
        print(json.dumps(result))
        sys.exit(1)

    # Gate 0: Forbidden file check
    print("  [0/3] Checking for forbidden file modifications...")
    violations = check_forbidden_files(repo)
    if violations:
        print(f"  ❌ Agent modified forbidden files: {violations}")
        fail("forbidden_files_modified", str(violations))

    print("  ✅ No forbidden files touched.")

    # Gate 1: Syntax check (fast, catches dead code before pytest)
    print("  [1/3] Syntax check...")
    try:
        syntax_ok, syntax_err = syntax_check(repo, file_path)
    except subprocess.TimeoutExpired:
        print("  ❌ py_compile timed out.")
        fail("syntax_timeout")

    if not syntax_ok:
        print(f"  ❌ Syntax error: {syntax_err[:200]}")
        fail("syntax_error", syntax_err[:500])

    print("  ✅ Syntax OK.")

    # Gate 2: Tests
    print("  [2/3] Running pytest...")
    try:
        tests_passed, test_output = run_tests(repo)
    except subprocess.TimeoutExpired:
        print("  ❌ pytest timed out (120s).")
        fail("pytest_timeout")

    if not tests_passed:
        lines = test_output.strip().split("\n")
        summary = "\n".join(lines[-5:])
        print(f"  ❌ Tests failed.")
        fail("tests_failed", summary)

    print("  ✅ Tests passed.")

    # Gate 3: Complexity decreased
    print("  [3/3] Checking complexity...")
    new_cc = get_function_complexity(repo, file_path, func_name)

    if new_cc is None:
        print(f"  ⚠️ Could not find {func_name} after refactor (may have been split).")
        print(f"  ✅ Accepting — function was likely decomposed.")
        commit_change(repo, file_path, func_name, original_cc, 0)
        print(json.dumps({"result": "PASS", "reason": "function_decomposed", "old_cc": original_cc, "new_cc": "N/A"}))
        sys.exit(0)

    if new_cc >= original_cc:
        print(f"  ❌ Complexity not reduced ({original_cc} → {new_cc}).")
        fail("complexity_not_reduced", f"{original_cc} → {new_cc}")

    # ALL gates passed
    print(f"  ✅ Complexity reduced: {original_cc} → {new_cc}")
    commit_change(repo, file_path, func_name, original_cc, new_cc)
    print(json.dumps({"result": "PASS", "old_cc": original_cc, "new_cc": new_cc}))
    sys.exit(0)


if __name__ == "__main__":
    main()
