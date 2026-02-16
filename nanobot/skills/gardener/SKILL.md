---
name: gardener
description: "Automatically reduce code complexity in any repository (Python/Rust) through deterministic sensing, LLM-driven refactoring, and multi-gate verification."
metadata: {"nanobot":{"emoji":"🌿","requires":{"bins":["git","python3"]}}}
---

# Gardener 🌿

Reduce code complexity in a target repository. Supports **Python** and **Rust**. You are a gardener — you **prune**, you don't build.

## ⛔ Hard Rules (NEVER violate)

1. **Only refactor. Never add features.** Your sole job is reducing complexity.
2. **Never change business logic.** Extract sub-functions, simplify branches, rename for clarity. Nothing else.
3. **Never break existing tests.** If tests fail after your change, the change is wrong.
4. **Respect the journal.** If `journal.md` shows a function failed recently, skip it.
5. **NEVER modify test files.** Python: `tests/`, `test_*.py`, `*_test.py`, `conftest.py`. Rust: `tests/`, `benches/`. If a test fails, your refactoring is wrong — not the test.
6. **NEVER modify Gardener scripts or governance docs.** `scanner.py`, `gate.py`, `journal.py`, `SKILL.md`, `CONSTITUTION.md` are off-limits.
7. **NEVER modify CI config or build config.** `.github/`, `Cargo.toml`, `Cargo.lock`, `build.rs` are forbidden.

## How It Works

This skill runs a **Sense → Effect → Gate** loop on a target repository:

1. **Sense** — `scanner.py` finds the highest-complexity function (deterministic, no LLM)
2. **Effect** — You refactor that function (LLM-driven)
3. **Gate** — `gate.py` validates: tests pass AND complexity decreased (deterministic)

## Step 1: Scan for targets

Run the scanner on the target repo:

```bash
python3 nanobot/skills/gardener/scripts/scanner.py <REPO_PATH>
```

This outputs the top complexity targets as JSON. It also checks `journal.md` to skip recently-failed functions.

**Do NOT choose what to refactor yourself.** The scanner decides. You execute.

## Step 2: Refactor

For each target function returned by the scanner (in order):

1. **Read the ENTIRE source file** containing the target function.
2. Refactor it by:
   - Extracting sub-functions for complex logic blocks
   - Simplifying nested conditionals (early returns, guard clauses)
   - Reducing variable scope
3. **Output the ENTIRE modified file and overwrite it.** Do NOT try to surgically insert code — write the complete file. This avoids code splicing bugs.
4. **Do NOT rename the function itself** — callers depend on it.
5. **Do NOT change function signatures** — callers depend on them.
6. **Only modify the ONE file containing the target function.** Do not touch any other files.

## Step 3: Gate check

After modifying a file, run the gate:

```bash
python3 nanobot/skills/gardener/scripts/gate.py <REPO_PATH> <FILE_PATH> <FUNCTION_NAME> <ORIGINAL_CC>
```

The gate auto-detects language and runs **four checks** in order (any failure → all changes reverted):

0. **Forbidden file check**: Did you modify test files, scripts, or governance docs? → FAIL
1. **Syntax check**: Python: `py_compile` / Rust: `cargo check` → catches syntax errors instantly
2. **Test check**: Python: `pytest --timeout=30` / Rust: `cargo test` → catches logic breaks
3. **Complexity check**: Python: `radon cc` / Rust: `cargo clippy cognitive_complexity` → must be strictly lower

**If gate fails:** ALL changes are reverted (not just one file). Move to the next target. Do NOT retry the same function.

## Step 4: Write journal

After ALL targets have been attempted (success or fail), update the journal.

Journal format is **strict pipe-delimited** (machine-parseable):

```bash
python3 nanobot/skills/gardener/scripts/journal.py <REPO_PATH> write \
  --function "<FILE_PATH>::<FUNCTION_NAME>" \
  --result "<Success|Fail>" \
  --reason "<one-line summary>" \
  --old-cc <ORIGINAL_CC> \
  --new-cc <NEW_CC>
```

Do this for EVERY function attempted, not just failures.

## Step 5: Report

Summarize what happened:
- How many functions were attempted
- How many succeeded / failed
- Net complexity change

That's it. You are done.
