# Joy M2 AI Database — Project State

Updated: 2026-08-30 (Asia/Shanghai)

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

Task 9A: `BLOCKED — DIGEST/TAXONOMY REVISION 4 IN REVIEW`.
Task 8B remains `CLOSED / PASS`; Task 1–2 and the adaptation-model checkpoint
are completed and committed. Restarted Task 3 Stage 3A is API/signature GREEN;
Stage 3B behavior RED count is 0 while the independent-oracle contract is under
docs-only remediation. No real import has started.

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
- Current branch is `task8b/pipeline-migration`; current committed HEAD is `4c028b0a65194686fe392ba642ce8fc3f9d55dfe`.
- V1.18 remains the current formal release. No formal database, frozen hash, compatibility object, question data, `data/`, `releases/`, or `legacy/` file changed.
- Task 8B unresolved blockers: `NONE`. Task 9A Task 3 Stage 3B remains blocked while Revision 4 closes the remaining adaptation-predicate versus independent-blocker coexistence precedence gap.
- Production contracts remain frozen; the actual V1.16 ZIP is not a maintained runtime input.
- Historical Task 8B post-commit clean-tree checkpoint: `PASS`; the current Task 9 worktree contains the two byte-preserved Stage 3A files plus the three explicitly authorized authority-doc changes.
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
- Task 9A Task 3 Stage 3A: `COMPLETED / GREEN`; its only current assets are the approved immediate-`NotImplementedError` `preflight.py` scaffold (`edcad17caf8f57e9ba7037c502d32091b1e0c0aecd9012005556cf116e186e24`) and integration signature test (`7ffc163ac105cb0257042567fa512492d0bd08d5a261ab0f418ffbcd9626a2d6`).
- Task 9A Task 3 Stage 3B: `BLOCKED — DIGEST/TAXONOMY REVISION 4 IN REVIEW`; behavior RED count is exactly 0 and production behavior is unimplemented.
- `src/joy_m2/ingest/__init__.py`: `NOT CREATED`; it is not a Stage 3A asset and remains deferred to its approved later task.
- Task 3 authority Revision 4 retains all approved Revision 3 manifest/normalization/digest, adaptation/issue, image-identity, and duplicate/rejected rules. It additionally freezes that proposed-ID collision or competing-reference identity makes the adaptation predicate false, while only an independent blocker that preserves the unique adapted reference—represented by an additional same-reference image path/role SHA conflict—may coexist with and retain an adaptation. Independent review and a docs checkpoint are required before a new explicit Stage 3B authorization.
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
- Current Task 9A Stage 3A checkpoint is API/signature 1/1 plus models/manifest 14/14 PASS. Stage 3B behavior RED count remains 0; no behavior implementation is commit-eligible or authorized.
- Task 8A final acceptance record remains `docs/reports/TASK8A_FINAL_ACCEPTANCE.md`.
- Verification record: `docs/reports/TASK7_VERIFICATION.md`.
- Remote backup branch remains retained; no cleanup has been performed.

## Next task

Independently review the Task 9A digest/taxonomy authority Revision 4. Preserve
the byte-identical Stage 3A scaffold and API test. After a reviewed docs
checkpoint and a new explicit authorization, directly extend the existing
integration test with the complete Stage 3B behavior RED suite before any
production behavior; do not delete or recreate Stage 3A. Do not
start Task 8C, Phase 2A, CLI/consumer migration, Task 9B/9C/9D, a real import,
SQLite mutation, or formal promotion.
