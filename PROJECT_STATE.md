# Joy M2 AI Database — Project State

Updated: 2026-09-04 (Asia/Shanghai)

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

Task 9A: `BLOCKED — MISSING-IMAGE REPRESENTABILITY AUTHORITY IN REVIEW`.
Task 8B remains `CLOSED / PASS`; Task 9A Task 1–2 and the adaptation-model
checkpoint are completed and committed. Restarted Task 3 dependency-aware
behavior groups C1–C4 are implemented/GREEN. C5 has not started. The current
docs remediation resolves `missing_image` representability by making it a
pre-candidate/package-level blocking issue that constructs no incomplete public
candidate, while preserving the fifteen-code authority and the separate C4
private signal-shape alignment checkpoint before C5. No real import has started.

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
- Current branch is `task8b/pipeline-migration`; current committed HEAD is `05e099a666839858247d233d48dad1a74194292c`.
- V1.18 remains the current formal release. No formal database, frozen hash, compatibility object, question data, `data/`, `releases/`, or `legacy/` file changed.
- Task 8B unresolved blockers: `NONE`. Task 9A C5 remains unimplemented while this docs-only remediation freezes formal authority for all eight non-duplicate signals. `missing_image` is pre-candidate/package-level, has `proposed_question_id=None`, constructs no `ImportCandidate`, contributes no candidate count, and blocks only through the unified issue/report/digest authority.
- Production contracts remain frozen; the actual V1.16 ZIP is not a maintained runtime input.
- Historical Task 8B post-commit clean-tree checkpoint: `PASS`; the current Task 9 worktree contains the two byte-preserved C4 assets plus the three explicitly authorized authority-doc changes.
- GitHub backup: `COMPLETE`; branch push and annotated tag push both completed.
- Tag: `joy-m2-task8b-closed-20260824`, targeting `6969f3d88b00537386212bc91203c837cac58915`.
- Pull request: not created.
- Task 8C: `NOT STARTED — PENDING EXPLICIT AUTHORIZATION`.
- Task 9 design: `docs/superpowers/specs/2026-08-25-task9-batch-import-design.md`.
- Task 9A implementation plan: `docs/superpowers/plans/2026-08-25-task9a-import-contract-preflight.md`.
- Task 9 recovered scope is batch-import manifest and preflight first; no new questions, SQLite writes, formal version changes, CLI, App/API, worksheet generation, or promotion are authorized.
- Task 9A Task 1 immutable carriers: `RED→GREEN COMPLETED / COMMITTED`.
- Task 9A Task 2 typed manifest/inventory: `RED→GREEN COMPLETED / COMMITTED`.
- Task 9A Task 1–2 checkpoint commit: `dd1cfed2cf3d09caf9136d3c9e2cc8d487186221`; its history must not be rewritten.
- Task 9A Task 3 Stage 3A: `COMPLETED / GREEN`; its historical immediate-`NotImplementedError` scaffold and signature-only test have since evolved through approved dependency groups C1–C4. The current byte-preserved C4 assets are `preflight.py` (`610e144a808bf88b69dcf3cc9e1f1d8d153a477fbae9eee274d1e1c5786abb33`) and `test_ingest_preflight.py` (`0fb7401c4a8b5b3a9fc1b9a07d2936a37e97f47b0045617f7ca5be4b2a029720`).
- Task 9A Task 3 dependency-aware behavior: C1–C4 `IMPLEMENTED / GREEN`; C5 `NOT STARTED`. Current status is `BLOCKED — MISSING-IMAGE REPRESENTABILITY AUTHORITY IN REVIEW`. The approved C4 production and integration-test assets remain uncommitted and byte-preserved; C5 production behavior is unimplemented.
- `src/joy_m2/ingest/__init__.py`: `NOT CREATED`; it is not a Stage 3A asset and remains deferred to its approved later task.
- Task 3 authority Revision 4 retains all approved Revision 3 manifest/normalization/digest, adaptation/issue, image-identity, and duplicate/rejected rules. It freezes that proposed-ID collision or competing-reference identity makes the adaptation predicate false, while only an independent candidate-bound blocker that preserves the unique adapted reference may coexist with and retain an adaptation. The current remediation preserves the seven-code duplicate/collision taxonomy and eight non-duplicate blocking codes, yielding the complete fifteen-code authority. It also freezes `missing_image` before typed candidate construction: raw candidate ID/path/role are issue evidence, no placeholder digest/carrier is allowed, and no adaptation, matching, classification, or count is produced for that record. Independent review and a docs checkpoint are required before the separately authorized C4 signal-shape alignment; that checkpoint must pass review and be committed before any explicit C5 authorization.
- Task 9A exact target identity remains V1.19, while frozen V1.18 remains the read-only 497-question baseline.
- Task 9B: `NOT STARTED`; its priority scope is a separately approved Mathpix MMD/MMD.ZIP-to-canonical-JSON adapter.
- Task 9C: `NOT STARTED`; V1.19 database/manifest serialization, writer, image destination, schema policy, and rollback authority remain deferred.
- Task 9D: `NOT STARTED`; no real batch acceptance has begun.
- `teacher_notes` and `common_errors` are Task 9A hashed import evidence/enrichment metadata, not current V2 formal fields; future formal representation requires separate schema authority.
- Task 9A images are read-only deterministic evidence only; no copy, move, rename, destination, or formal image identity change is authorized.
- Import approval binds `(batch_id, preflight_sha256, V1.19)` and is strictly separate from formal release/promotion authorization.
- Task 9 authority continues to freeze path-independent preflight digests, explicit translation/explanation provenance, and manifest-declared candidate ordering. The pending remediation additionally makes the manifest digest, normalized-text digest, duplicate/collision issue taxonomy, and independent literal oracle fully reproducible without inspecting production projection code.
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
- Current Task 9A dependency-aware implementation is GREEN through C4. C5 has not started. The next possible implementation after this missing-image authority review and docs commit is only the separately authorized C4 private signal-shape alignment checkpoint; C5 classification remains unauthorized until that checkpoint passes review and is committed.
- Task 8A final acceptance record remains `docs/reports/TASK8A_FINAL_ACCEPTANCE.md`.
- Verification record: `docs/reports/TASK7_VERIFICATION.md`.
- Remote backup branch remains retained; no cleanup has been performed.

## Next task

Independently review Task 9A missing-image representability authority while
preserving the byte-identical C4 production and integration-test assets. After
that review passes and the docs checkpoint is committed, the next separately
authorized action is only C4 private signal-shape alignment. C5 classification
may begin only after the alignment checkpoint passes independent review, is
committed, and receives another explicit authorization. Do not start Task 8C,
Phase 2A, CLI/consumer migration, Task 9B/9C/9D, a real import, SQLite mutation,
or formal promotion.
