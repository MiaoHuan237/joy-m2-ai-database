# Task 7 Git Project Initialization Plan

> **For agentic workers:** Execute this plan inline with verification checkpoints. Do not modify any file inside `releases/V1.18/`.

**Goal:** Initialize Joy M2 AI Database as a standard Git-managed Python project while preserving the complete V1.18 release byte-for-byte as the read-only golden baseline.

**Architecture:** Keep the self-contained formal release under `releases/V1.18/`. Put reusable baseline verification in `src/joy_m2/`, regression tests in `tests/regression/`, and current project guidance at the repository root. The verification command treats unexpected, missing, or changed baseline files as failures.

**Tech Stack:** Python 3.12, standard library, SQLite, `unittest`, Git.

## Global Constraints

- V1.18 is a read-only golden baseline.
- Do not modify the 497 formal questions or any business data.
- Only organize directories, dependencies, test entry points, and project documentation.
- Update root `PROJECT_STATE.md` after verification.

---

### Task 1: Lock and isolate V1.18

**Files:**
- Move unchanged: the 14 files listed by `SHA256SUMS.txt` to `releases/V1.18/`
- Preserve: `releases/V1.18/manifest.json`
- Preserve: `releases/V1.18/SHA256SUMS.txt`

- [x] Verify all hashes before moving.
- [x] Move the full release without changing file contents.
- [x] Run the release's independent verifier with Python 3.12 and require `PASS`.

### Task 2: Add the regression contract using TDD

**Files:**
- Create: `tests/regression/test_v118_baseline.py`
- Create: `src/joy_m2/baseline.py`
- Create: `src/joy_m2/cli.py`
- Create: `src/joy_m2/__main__.py`

- [x] Write tests for the protected file set, database invariants, CSV mirror, Markdown coverage, and CLI exit status.
- [x] Run the tests and verify they fail because `joy_m2.baseline` does not exist.
- [x] Implement the minimal verifier and CLI.
- [x] Run the tests and require all tests to pass.

### Task 3: Add project metadata and documentation

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `.gitattributes`
- Create: `AGENTS.md`
- Create: `README.md`
- Modify: `PROJECT_CONTEXT.md`
- Modify: `PROJECT_STATE.md`

- [x] Declare Python `>=3.12,<3.13` and no third-party runtime dependencies.
- [x] Document setup, test, verification, and immutable release boundaries.
- [x] Record Task 7 completion and fresh verification evidence.

### Task 4: Final verification and Git baseline

- [x] Run the original V1.18 verifier and require `PASS`.
- [x] Run `python -m unittest discover -s tests -v` and require zero failures.
- [x] Run the new CLI and require `status=PASS`.
- [x] Run `shasum -a 256 -c releases/V1.18/SHA256SUMS.txt` and require every file to report `OK`.
- [x] Review `git diff --check`, staged file scope, and sensitive-file scan.
- [x] Leave the intended initial snapshot staged because no Git author identity is configured.
