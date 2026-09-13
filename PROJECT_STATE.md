# Joy M2 AI Database — Project State

Updated: 2026-09-13 (Asia/Shanghai)

## Formal data

- Current formal release: V1.18
- Formal SQLite: `releases/V1.18/Joy_M2_Complete_Question_DB_V1_18.sqlite3`
- Frozen SQLite SHA-256: `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7`
- Complete-question records: 497
- V1.17 retained records: 45
- Task 6 migrated records: 452
- Answer identity: 392 `source_provided`, 71 `ai_solved_verified`, 34 `missing_from_source`
- P0/P1 audit blockers: 0/0
- V1.18 is frozen and must not be edited in place.
- V1.19 formal artifacts: `0`; formal imported questions: `0`. The first real
  user batch passed Gate C and exists only as the verified, unpromoted Task 9C
  candidate at `data/staging/task9c-v119-real-0918-interval-candidate/`.
  It binds 5 approved additions, batch
  `TASK9B-REAL-0918-INTERVAL-REPRODUCTION-001`, preflight SHA-256
  `4aa3ff8b419a0fcca57c805d5f10f252658cb30c00f6cf1b74c95ab3009333c9`,
  candidate SQLite SHA-256
  `9d30cf444e9d6686128f884d5a3cf57f4e58ce544b7933d7a0a47ec0e8212d20`,
  and projected formal count 502. Task 9D technical preparation is complete,
  but Human Gate D is unsatisfied and `releases/V1.19/` remains absent.

## Current task

Task 9D formal V1.19 promotion preparation is `READY FOR PROMOTION
AUTHORIZATION`. Its independently reviewed Design is committed at
`4f9924a712d02feb889cbd24e5c3867a9daba31c`; the implementation Plan at
`d1057affd79e7fd81119cd62bdc08d0982958cd3`; public-surface scope alignment at
`7af421fdce7a722da6f43aec7d3cd6656d7675b9`; and the verified implementation at
`b5a47f4a231b2374ae6db0931a6754a52d11296e` (`feat: add verified V1.19
promotion pipeline`). Final dual independent review is Critical 0 / Important
0 / Minor 0. Task 9D focused tests are 43/43 PASS and the complete maintained
suite is 706/706 PASS with zero skips or expected failures. Two independent
non-formal real-candidate dry-runs are byte-identical, independently verify
18/18 checks, and bind release digest
`7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d`.
No current-release pointer/index exists or changes. The only next action is an
explicit Human Gate D decision; formal publication has not occurred.

Task 9B remains `CLOSED / PASS`. Its original parser-mode implementation is
committed at `35778b80f931ecf4903ca553ab0fb1b1bb5e8110` and its explicit
source-mapping extension authority is committed at `c11f463`, `4a5b6a3`,
`ea6bf7f`, and `78a5262`. The extension implementation and this closure update
are recorded by the commit containing this state (`feat: add explicit MMD
source mapping`). It remains a staging-only adapter; it imported no question
and created no V1.19 database or formal artifact.

Task 9A remains `CLOSED / PASS` at implementation commit
`6fec37c45346b1680fb0bf0676c38e515c18cacd` (`feat: implement Task 9A import
preflight`), parent `a742f56bb49e644ed062d78ec2de9505d47b593d`.
Task 8B remains `CLOSED / PASS`; Task 9A Task 1–2, the adaptation-model
checkpoint, and Restarted Task 3 are completed and committed. The final Task 9A
integration suite is 41/41 PASS with 0 failures, errors, or skips. No real
user-batch import or promotion has started. Its post-Gate-B lifecycle test now
preserves pre-existing V1.19 state by immutable before/after fingerprint while
continuing to require formal `releases/V1.19/` absence and exact V1.18
immutability.

Current Task 3 execution state:

- Restarted Task 3: `COMPLETED`.
- C1: `PASS`.
- C2: `PASS`.
- C3: `PASS`.
- C4: `PASS`.
- C4 SIGNAL-SHAPE ALIGNMENT: `COMPLETED / PASS`.
- C5 classification layer: `COMPLETED / PASS`.
- C6: `COMPLETED / PASS`.

Scope:

- Task 8A's approved design and plan were implemented layer by layer with TDD and independent review checkpoints.
- The approved Task 8 design is `docs/superpowers/specs/2026-08-08-task8a-pipeline-contracts-design.md`.
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
- Current branch is `task8b/pipeline-migration`. The Task 9C Phase B
  implementation checkpoint is `1881a3aff5e064646395516102e5f3d39a2b619c`;
  its closure documentation is committed at
  `018e6184a26be5df7c1502e4e6a92d34fd0ee688`. The branch tracks
  `origin/task8b/pipeline-migration`; no force push or history rewrite is
  authorized.
- V1.18 remains the current formal release. No formal database, frozen hash,
  compatibility object, question data, `releases/`, or `legacy/` file changed.
  V1.19 state remains non-formal and ignored: the approved synthetic staging
  candidate, the verified real Task 9C candidate, and the verified Task 9D
  dry-run roots described below. None is formal release authority.
- Task 8B unresolved blockers: `NONE`. Task 9A unresolved implementation
  blockers: `NONE`. Its exact sixteen-code issue pipeline includes
  `file_integrity_mismatch` as the sole package/file-level integrity issue; its
  field is `file_integrity`, its proposed candidate ID is `None`, and its exact
  evidence retains canonical relative path plus expected/actual SHA and size.
  It contributes no candidate count and blocks only through the unified
  issue/report/digest authority.
- Production contracts remain frozen; the actual V1.16 ZIP is not a maintained runtime input.
- Historical Task 8B post-commit clean-tree checkpoint: `PASS`; the Task 9A
  implementation commit passed its own post-commit clean-tree checkpoint.
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
- Task 9A Task 3 Stage 3A: `COMPLETED / GREEN`; its historical
  immediate-`NotImplementedError` scaffold and signature-only test have since
  evolved through approved dependency groups C1–C4. The historical C4
  checkpoint asset SHAs were `preflight.py`
  (`610e144a808bf88b69dcf3cc9e1f1d8d153a477fbae9eee274d1e1c5786abb33`) and
  `test_ingest_preflight.py`
  (`0fb7401c4a8b5b3a9fc1b9a07d2936a37e97f47b0045617f7ca5be4b2a029720`).
  The historical C5 production asset is recorded below.
- Task 9A Task 3 dependency-aware behavior: C1–C6 `COMPLETED / PASS`.
  Historical C4 and file-integrity signal-alignment checkpoints remain recorded
  in the Design and Plan as completed RED-first audit evidence. The committed
  production asset is `src/joy_m2/ingest/preflight.py`, SHA-256
  `c1df58017a08c66173648f82f287d625f2208d371981aa01ae09d75199d9bebd`;
  the committed integration test is
  `tests/integration/test_ingest_preflight.py`, SHA-256
  `5e5f01271dbbe67ad8b0119781af223d9c1d29a68254eecf0689520c8c83975b`.
- `src/joy_m2/ingest/__init__.py`: its exact append-only public surface combines
  the frozen Task 9A, Task 9B, Task 9C, and approved Task 9D contracts without
  exporting private helpers or `ImportApprovalError`.
- Task 3 authority preserves all approved manifest/normalization/digest, adaptation/issue, image-identity, duplicate/rejected, and missing-image rules. The completed remediation left the existing seven duplicate/collision and eight non-duplicate codes unchanged and added exactly one package/file-level code, yielding a closed sixteen-code authority. A safely read file with a size/SHA mismatch emits `file_integrity_mismatch`; missing, unreadable, non-regular, and containment failures remain early `PipelineError`. Corrupted bytes are excluded from downstream parsing/evidence/matching, affected candidates are not constructed, and no second integrity channel or thirteenth digest key is allowed.
- The independent 37-method / 29-RED blocker scan found no other structured-BLOCKED condition lacking an approved `ImportIssue` code. That result preserves the closed sixteen-code inventory and does not authorize a seventeenth code.
- Historical audit sequence only, with no current execution effect: the earlier
  37-test RED state advanced to a 39-test mixed RED checkpoint after the C6
  stop-type boundary repair (39 collected, 8 PASS methods, 31 RED methods, 60
  failure instances, 0 ERROR, 0 skip), then to 39/39 PASS after C6 final
  closure. Final independent review identified the `missing_images` ordering
  and duplicate-ID occurrence-ambiguity gaps; two regression tests
  expanded the suite to its current final 41/41 PASS. All intermediate
  checkpoints are `HISTORICAL / CLOSED` audit evidence and must not be replayed.
- Task 9A exact target identity remains V1.19, while frozen V1.18 remains the read-only 497-question baseline.
- Task 9B implementation: `COMPLETED / PASS`. The independently reviewed Design
  is committed at `d19baa812213c8015dbb63a9ce3f431eaa077f42`; the Plan at
  `e46bd5b856591b36f69fbaa5fc80738335ba3c66`; representative fixtures at
  `c1125252efea59805f616d6347960b81f5d4f08c`; independently authored golden
  reconciliation at `141d2c8daf431a7512d689395c5b31f84c8a8251`; and implementation at
  `35778b80f931ecf4903ca553ab0fb1b1bb5e8110`. The explicit source-mapping
  extension Design/Plan closure is committed through `78a5262`; its four-name
  module API, typed proposal/approval carriers, strict line-draft-to-byte-map
  conversion, exact approval binding, shared private Source IR, deterministic
  review report, and parser/explicit canonical equivalence are implemented in
  the current checkpoint. Its final dual independent review is Critical 0 /
  Important 0 / Minor 0 after all remediation RED-to-GREEN cycles. Direct PDF
  remains deferred. Task 9B unresolved implementation blockers: `NONE`.
- Task 9C: Phase A public contracts and Phase B temporary-root behavior are
  `COMPLETED / COMMITTED`. The writer creates the approved additive candidate
  database, content-addressed images, canonical manifest, `SHA256SUMS`, and
  declarative rollback receipt atomically beneath approved temporary/staging
  roots; the independent verifier closes all 16 ordered checks. Human Gate B
  authorized the synthetic `TASK9B-FIXTURE-VECTOR-17` candidate at
  `data/staging/task9c-v119-candidate/`; it is immutable verification evidence,
  not a real import and not eligible for promotion. Human Gate C separately
  authorized the current 5-question real candidate; that candidate remains
  verified and unpromoted.
- Task 9D: `READY FOR PROMOTION AUTHORIZATION`; deterministic builder,
  independent verifier, rollback receipt, atomic publication gate, real dual
  dry-run, maintained regressions, and independent implementation review are
  complete. Human Gate D remains `REQUIRED`; formal publication is `NOT
  STARTED`.
- `teacher_notes` and `common_errors` are Task 9A hashed import evidence/enrichment metadata, not current V2 formal fields; future formal representation requires separate schema authority.
- Task 9A images are read-only deterministic evidence only; no copy, move, rename, destination, or formal image identity change is authorized.
- Import approval binds `(batch_id, preflight_sha256, V1.19)` and is strictly separate from formal release/promotion authorization.
- Task 9 authority continues to freeze path-independent preflight digests,
  explicit translation/explanation provenance, and manifest-declared candidate
  ordering. The completed implementation makes the manifest digest,
  normalized-text digest, duplicate/collision issue taxonomy, and independent
  literal oracle fully reproducible without inspecting production projection
  code.
- The literal happy-path oracle remains unchanged: `manifest_sha256` is `b5a0ae6597028c48c6f7cdc81bd7e67d61dd369cbf96d7c6a4e96efd73984c5d` and final `preflight_sha256` is `087574a8af6fe28ac65a5b5810794952044cb5f0778ed3492d1e7819a4be33c2`.
- Formal database remains V1.18 with 497 questions; no new question has entered
  formal authority and no formal V1.19 artifact exists. Human Gate C authorized
  exactly the current five-question real candidate. Formal promotion remains a
  separate Human Gate D decision.
- Task 9A capability closure includes canonical JSON import preflight,
  deterministic and path-independent processing, read-only baseline access,
  exact sixteen-code structured issues, duplicate/collision/adaptation and
  file-integrity classification, candidate/package blocker separation, count
  closure, READY/BLOCKED status, deterministic ordering, exact final digest,
  the frozen literal oracle, and zero-write verification.
- Final independent implementation review: `PASS`. Remediation findings: two
  IMPORTANT found, two IMPORTANT remediated; final remediation review: `PASS`.
- Autonomous execution policy: `ACTIVE` at
  `93566e4fb4f95d1258f83ae2da3bcaad9573a737`; `AGENTS.md` and
  `docs/AUTONOMY_POLICY.md` define the default checkpoint sequence, independent
  review requirements, session recovery, ordinary Git authority, and HUMAN
  GATES A–F. Task 9B remains staging-only; Task 9C constructed the verified real
  candidate only after Gate C; Task 9D stops immediately before the first
  digest-bound formal V1.19 publication at Gate D.
- Safety branch `backup/task-7.1-ceb179e-20260808` remains retained.

## Completion gate

- Current explicit maintained suite, excluding the separately attributed legacy
  behavior module: 706/706 passed; skip=0 and expectedFailure=0.
- Task 9D focused promotion suite: 43/43 passed; final dual independent review:
  Critical 0 / Important 0 / Minor 0.
- Task 9C Phase B focused writer/verifier suite: 71/71 passed; final independent
  review: Critical 0 / Important 0 / Minor 0.
- Task 9C Phase A public contracts: 9/9 passed; independent review:
  Critical 0 / Important 0.
- Task 9B focused adapter plus explicit source-mapping suite: 342/342 passed;
  final dual independent review: `CLEAN` (Critical 0, Important 0, Minor 0).
- Task 8 equivalence: 3/3 passed.
- Task 7 structure and frozen-baseline tests: 7/7 passed.
- V1.18 independent verifier: `PASS` with 497/452/45 counts, integrity `ok`, and 0 foreign-key errors.
- Task 3–6 executable regressions: 13 + 9 + 10 + 22 = 54/54 passed.
- Task 6 oracle: 22/22 passed.
- Release focused tests: 48/48; Public Models: 66/66; Models + Config: 80/80; Audit: 21/21; Task 3A: 6/6; Database: 14/14; Export: 22/22; Export + Database: 36/36.
- Legacy attribution remains the approved 9 PASS / 2 FAIL surface: deterministic SQLite hash attribution and frozen artifact byte-equivalence attribution, with no third failure.
- Task 8B verification record: `docs/reports/TASK8B_VERIFICATION.md`.
- Task 8B implementation and completion evidence are fully closed; no next implementation stage is authorized.
- Task 9A integration: 41/41 PASS; Models/Manifest: 14/14 PASS; Public Models:
  66/66 PASS; Task 7: 7/7 PASS; Task 8 equivalence: 3/3 PASS; Release:
  48/48 PASS; V1.18 independent validator: `PASS`.
- Task 9A implementation is `CLOSED / PASS`; current remaining Task 9A
  implementation work: `NONE`. Its authority closure, RED gates, C1–C6,
  file-integrity migration and signal alignment, final independent review,
  remediation review, 41/41 GREEN, and implementation commit are completed.
- Task 8A final acceptance record remains `docs/reports/TASK8A_FINAL_ACCEPTANCE.md`.
- Verification record: `docs/reports/TASK7_VERIFICATION.md`.
- Remote backup branch remains retained; no cleanup has been performed.
- Task 9B parser-mode golden-equivalence preflight is `READY FOR USER IMPORT APPROVAL` with
  17 candidates, 0 issues, and path-independent preflight SHA-256
  `49ab71e26cf2256581ecb5ada14b0eefc601317169ee897599aeb9a39976187b`.
  Its exact approval was used only to build the approved synthetic Task 9C
  staging candidate. It must not be reused as approval for a real Task 9D user
  batch; no formal import was performed.
- Task 9B verification record: `docs/reports/TASK9B_VERIFICATION.md`.

## Next task

Task 9A and Task 9B are closed; Task 9C candidate construction and Task 9D
technical promotion preparation are complete. The verified real candidate
remains unpromoted, V1.18 remains the current 497-question formal authority,
and `releases/V1.19/` is absent. The only next action is Human Gate D. The exact
required statement is:

```text
USER APPROVED RELEASE PROMOTION V1.19 7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d
```

Until that exact approval is received, do not call `publish_v119_release`,
create `releases/V1.19/`, update any release pointer/index, begin Task 8C or
Phase 2A, or perform any other formal-data mutation.

`USER DECISION REQUIRED — FINAL V1.19 PROMOTION AUTHORIZATION`
