# Auto-ingestion Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans.

**Goal:** Deliver an incremental, resumable, approval-preserving local runner.
**Architecture:** A repository-scoped journal/lock drives fixed existing V1.23
operations. Unsupported profiles stay in review, never bypass frozen adapters.
**Tech Stack:** Python 3.12, stdlib SQLite/fcntl, current maintained APIs.
**Spec:** `docs/superpowers/specs/2026-10-14-auto-ingestion-design.md`.

## Global Constraints

- User explicitly requested immediate implementation; preserve exact data gates.
- No formal writes, promotion, source edits, AGENTS edits or invented approvals.
- Runtime data ignored; thin CLI, no dependency additions or public export drift.

## Review Focus

- Two runners must not consume a batch twice, including separate processes.
- Crash after atomic writer success must recover without another write.
- Approval/input/parent changes must invalidate cached waiting results.
- Changed accepted sources must not become automatically new input.
- Unsupported/malformed sources must not prevent independent good jobs.

### Task 1: Journal, discovery and repeatable entry point

Files: create automation.py, scripts/run_auto_ingestion.py,
tests/unit/test_auto_ingestion.py.
Interface: `run_cycle(config_path: Path, repo_root: Path) -> dict`.
- [ ] Add minimal callable scaffold, then behavioral RED tests for discovery,
  identity/revisions, no-change, input errors, retries, lock and safe paths.
- [ ] Run unit tests; confirm assertion failures, not setup errors.
- [ ] Implement transactions and scoped lock; run the same tests GREEN.

### Task 2: Existing authority integration

Files: create automation_v123.py, tests/integration/test_auto_ingestion.py.
Interface: `V123Operations(repo_root, runtime_root, receipts)` reconstructs a
verified prefix; `process(job, revision)` returns structured state/evidence.
- [ ] Write RED for missing approval, valid continuation, stale approval,
  repeat accepted input, recovery and unsupported Oxford profile.
- [ ] Reuse existing APIs; no new mathematical/source interpretation contract.
- [ ] Run integration plus Task10B/V123 regression; inspect results.

### Task 3: Real trial, review and delivery

Files: operations guide, PROJECT_STATE, ignored config/report/journal.
- [ ] Register real source roots, existing 2023/2025 receipts and Oxford PDFs.
- [ ] Run intake twice; verify no second processing/write and frozen hashes.
- [ ] Run full maintained suite and independent whole-change review; fix
  Critical/Important findings with RED/GREEN evidence.
- [ ] Document exact remaining human gate and phase-2 recommendations.
- [ ] Commit only owned files after GREEN/review. No scheduler while real
  authoritative E2E remains blocked; do not describe intake-only as full import.
