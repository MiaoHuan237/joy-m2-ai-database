# Joy M2 AI Database — Project State

Updated: 2026-08-25 (Asia/Shanghai)

## Formal data

- Current formal release: V1.18
- Formal SQLite: `releases/V1.18/Joy_M2_Complete_Question_DB_V1_18.sqlite3`
- Complete-question records: 497
- V1.17 retained records: 45
- Task 6 migrated records: 452
- Answer identity: 392 `source_provided`, 71 `ai_solved_verified`, 34 `missing_from_source`
- P0/P1 audit blockers: 0/0
- V1.18 is frozen and must not be edited in place.

## Current task

Task 9A: `BLOCKED — TDD SCAFFOLD SEQUENCING REMEDIATION IN REVIEW`. Task 8B remains `CLOSED / PASS`; Task 1–2 of Task 9A completed RED→GREEN, while no real import has started.

Scope:

- Task 8A's approved design and plan were implemented layer by layer with TDD and independent review checkpoints.
- The approved design is `docs/superpowers/specs/2026-08-08-task8a-pipeline-contracts-design.md`.
- The follow-up implementation plan is `docs/superpowers/plans/2026-08-08-task8a-pipeline-contracts.md`.
- Audit: `COMPLETED`.
- Task 3A: `COMPLETED`.
- Database: `COMPLETED`.
- Export: `COMPLETED`.
- Release: `COMPLETED`.
- Task 8 completion evidence: `COMPLETED`.
- Maintained typed implementations now exist under `src/joy_m2/audit/`, `db/`, `export/`, and `release/`; no CLI or consumer migration was added.
- Task 8 completion authority is the maintained replay against approved protected/frozen references and compatibility contracts. Fresh legacy generation remains attribution evidence only.
- Completion evidence commit: `6969f3d88b00537386212bc91203c837cac58915`.
- Current branch is `task8b/pipeline-migration`; the pre-Task-9-design local and remote HEAD is `2f14a99cde2199945194cdc57bd6f3d622a3fea1` with ahead/behind `0/0`.
- V1.18 remains the current formal release. No formal database, frozen hash, compatibility object, question data, `data/`, `releases/`, or `legacy/` file changed.
- Task 8B unresolved blockers: `NONE`. Task 9A Task 3 is blocked pending independent review of the two-stage API-RED/scaffold/behavior-RED sequencing remediation.
- Production contracts remain frozen; the actual V1.16 ZIP is not a maintained runtime input.
- Historical Task 8B post-commit clean-tree checkpoint: `PASS`; Task 9 now has only the explicitly authorized docs draft changes.
- GitHub backup: `COMPLETE`; branch push and annotated tag push both completed.
- Tag: `joy-m2-task8b-closed-20260824`, targeting `6969f3d88b00537386212bc91203c837cac58915`.
- Pull request: not created.
- Task 8C: `NOT STARTED — PENDING EXPLICIT AUTHORIZATION`.
- Task 9 design: `docs/superpowers/specs/2026-08-25-task9-batch-import-design.md`.
- Task 9A implementation plan: `docs/superpowers/plans/2026-08-25-task9a-import-contract-preflight.md`.
- Task 9 recovered scope is batch-import manifest and preflight first; no new questions, SQLite writes, formal version changes, CLI, App/API, worksheet generation, or promotion are authorized.
- Task 9A Task 1 immutable carriers: `RED→GREEN COMPLETED` (uncommitted).
- Task 9A Task 2 typed manifest/inventory: `RED→GREEN COMPLETED` (uncommitted).
- Task 9A Task 3 baseline/candidate preflight: `NOT STARTED / BLOCKED`; the explicit `package_root` API is defined, while behavior REDs require an importable no-behavior scaffold after the API-existence RED. That TDD sequencing remediation is pending independent review.
- Task 9A exact target identity remains V1.19, while frozen V1.18 remains the read-only 497-question baseline.
- Task 9B: `NOT STARTED`; its priority scope is a separately approved Mathpix MMD/MMD.ZIP-to-canonical-JSON adapter.
- Task 9C: `NOT STARTED`; V1.19 database/manifest serialization, writer, image destination, schema policy, and rollback authority remain deferred.
- Task 9D: `NOT STARTED`; no real batch acceptance has begun.
- `teacher_notes` and `common_errors` are Task 9A hashed import evidence/enrichment metadata, not current V2 formal fields; future formal representation requires separate schema authority.
- Task 9A images are read-only deterministic evidence only; no copy, move, rename, destination, or formal image identity change is authorized.
- Import approval binds `(batch_id, preflight_sha256, V1.19)` and is strictly separate from formal release/promotion authorization.
- Task 9 authority continues to freeze path-independent preflight digests, explicit translation/explanation provenance, and manifest-declared candidate ordering. The two-stage API-existence RED → scaffold → behavior RED remediation is pending independent review before Task 3 may resume.
- Formal database remains V1.18 with 497 questions; no new questions have been imported, no V1.19 artifact exists, no writer is authorized, and no promotion is authorized.
- Safety branch `backup/task-7.1-ceb179e-20260808` remains retained.

## Completion gate

- Explicit complete maintained suite: 195/195 passed, including Task 8 completion 3/3; skip=0 and expectedFailure=0.
- Task 8 equivalence: 3/3 passed.
- Task 7 structure and frozen-baseline tests: 7/7 passed.
- V1.18 independent verifier: `PASS` with 497/452/45 counts, integrity `ok`, and 0 foreign-key errors.
- Task 3–6 executable regressions: 13 + 9 + 10 + 22 = 54/54 passed.
- Task 6 oracle: 22/22 passed.
- Release focused tests: 48/48; Public Models: 66/66; Models + Config: 80/80; Audit: 21/21; Task 3A: 6/6; Database: 14/14; Export: 22/22; Export + Database: 36/36.
- Legacy attribution remains the approved 9 PASS / 2 FAIL surface: deterministic SQLite hash attribution and frozen artifact byte-equivalence attribution, with no third failure.
- Task 8B verification record: `docs/reports/TASK8B_VERIFICATION.md`.
- Task 8B implementation and completion evidence are fully closed; no next implementation stage is authorized.
- Task 8A final acceptance record remains `docs/reports/TASK8A_FINAL_ACCEPTANCE.md`.
- Verification record: `docs/reports/TASK7_VERIFICATION.md`.
- Remote backup branch remains retained; no cleanup has been performed.

## Next task

Independent review of the Task 9A TDD scaffold sequencing remediation. Task 1–2 remain completed and uncommitted; Task 3 must remain `NOT STARTED / BLOCKED` until the remediation review passes and implementation is explicitly resumed. Do not create the scaffold during this docs review, and do not start Task 8C, Phase 2A, CLI/consumer migration, Task 9B/9C/9D, a real import, SQLite mutation, or formal promotion.
