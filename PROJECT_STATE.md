# Joy M2 AI Database — Project State

Updated: 2026-10-20 (Asia/Shanghai)

## Formal data

- Current formal release: V1.23
- Formal SQLite: `releases/V1.23/Joy_M2_Complete_Question_DB_V1_23.sqlite3`
- Formal SQLite SHA-256: `28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd`
- Formal release digest: `84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc`
- Complete-question records: 677 (639 immutable V1.22 records + 38 approved
  source records: 2023 HKDSE12, 2025 HKDSE13, Oxford13). This is a record count,
  not a distinct-original-question count.
- Formal read-only query view: `formal_complete_questions_v123`; all677 unique
  IDs are published/selectable. No persistent default-query pointer was changed.
- V1.17 retained records: 45
- Task 6 migrated records: 452
- Answer identity: 572 `source_provided`, 71 `ai_solved_verified`, 34 `missing_from_source`
- P0/P1 audit blockers: 0/0
- V1.18 remains the frozen, byte-identical 497-question baseline and must not be
  edited in place. Its SQLite SHA-256 remains
  `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7`.
- V1.19 is formally published as four release artifacts with 5 imported
  questions. The release binds batch
  `TASK9B-REAL-0918-INTERVAL-REPRODUCTION-001`, preflight SHA-256
  `4aa3ff8b419a0fcca57c805d5f10f252658cb30c00f6cf1b74c95ab3009333c9`,
  candidate SQLite SHA-256
  `9d30cf444e9d6686128f884d5a3cf57f4e58ce544b7933d7a0a47ec0e8212d20`,
  release digest
  `7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d`,
  and exact formal count 502.
- V1.20 is formally published as four release artifacts with 41 appended
  questions from the approved 2012/2013/2014 HKDSE PP/MS batches. It binds
  candidate digest
  `88cc945b6296652c88041e8e51a5c586300c2201a9f48e21abde80d97da3a7b3`,
  release digest
  `1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf`,
  and exact formal count 543. V1.18 and V1.19 remain byte-identical.
- V1.21 is formally published as four release artifacts, binds release digest
  `f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3`,
  and contains 591 published/selectable complete questions. The manifest SHA-256
  is `a04f7ee7b67991427bffd3e5a3de70a310d0889fdf8f0535649840a44baf3a40`;
  semantic SHA-256 is
  `0a4e70acb1cc657207dd0fefb1e20581d34baadda804219ae2fbbfb2b5ca817f`.
  V1.18/497, V1.19/502, and V1.20/543 remain immutable historical authority.
- V1.22 remains immutable at639 records, SQLite SHA
  `a474846a5b1d10a0fe48a259522fbb327747319f4a114452bf9f294405d8d9e0`,
  release digest
  `89a592abf52507cc0325f9c6f30ee2c74d4ec55fdcef988fdae6cb12f5a3073b`.

## Current task

### F6 selected source batch / V1.24 candidate bridge — WRITTEN DESIGN REVIEW (2026-10-20)

- User authorized the minimal school-mock selected-batch mapping and the next
  candidate lifecycle after published V1.23. This supersedes the historical
  post-publication "no V1.24 authorized" stopping statement below only for this
  narrow candidate/source direction, not for promotion or real import approval.
- Design:
  `docs/superpowers/specs/2026-10-20-f6-selected-batch-v124-candidate-design.md`.
  Direction approved; written Design review pending. Plan and implementation
  NOT STARTED. Existing exact transcription/import/release gates remain intact.
- F6 source review retained at
  `data/staging/f6-mock-1516-source-review-20261020-000001/`: 12 original
  questions / 100 marks; prioritize complete Q1,Q3,Q6,Q8 (4 / 24 marks).
  Remaining eight retain their original source issues and evidence. No question
  was removed from the old draft or an approved/preflighted batch.
- Proposed independent source identity:
  `HKSYCIA-WTS-M2-MOCK-2015-16` (`school_mock`, not Oxford/HKEAA).
  First selected batch:
  `JOY-M2-STG-F6-MOCK-2015-16-0428-20260905-Q01-Q03-Q06-Q08`.
  Existing review draft is not a consumable approved transcription.
- Fresh read-only baseline check: formal V1.23 remains677 unique published/
  selectable records with the identities above. Proposed V1.24 genesis:
  `797ed06ca5833bac060c1603cada38a6f2aa9eb080a40d9dc892bba9a549773a`;
  computed from the Design projection, not an existing candidate/release.
- Current docs-only scope is this state file and the new Design. AGENTS.md stays
  user-owned/unstaged; production, tests, sources, old candidates, runner and
  formal artifacts are unchanged. No new canonical/preflight or writer call.

### V1.23 exact-approved publication — COMPLETED / PASS (2026-10-20)

- Actual human approval received:
  `USER APPROVED RELEASE PROMOTION V1.23 84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc`.
  Freshly verified existing publisher consumed this approval once under
  `cycle.lock`; no pending intent or newer receipt was present. No candidate
  writer, transcription, rebuild, live rollback or next-version work occurred.
- Selected generation000003 remains
  `c5c51df58d64349d58bd71469fe67a72cced56e77369126d6fec66bb2fcc955a`.
  Ledger remains2023(12),2025(13),Oxford(13). All3 candidate prefixes24/24 PASS.
  Formal V1.23 four files exactly match both approved dry-runs byte-for-byte.
  Fresh independent formal verifier21/21 PASS; all639 baseline and38 promoted
  records match the approved projection field-for-field.
- Oxford13 are queryable by batch/source with unchanged publisher solutions,
  not HKEAA official MS. PDF/page/region figure references remain references;
  no nonexistent canonical image files or independent explanations are claimed.
- Fresh post-publication focused/historical gate51/51 PASS (108.271s);
  maintained65modules1331/1331 PASS (560.267s),0 failures/errors/skips/
  expectedFailures; V1.18 validator PASS/497. Separate read-only operational
  review: Critical0/Important0/Minor0. Only the Design §8 lifecycle approval
  literal/comment changed; historical negative controls remain intact.
- All784 protected file identities, including formalV1.18–V1.22, old candidates,
  source/approval evidence,2024 and user AGENTS.md, remain unchanged. AGENTS stays
  unstaged and excluded from the task commit. Scheduler/config unchanged.
- Publication receipt and fresh gate evidence:
  `data/staging/task13-v123-promotion-readiness/publication-20261020-000001/`.
  Publication audit, exact artifacts and local recovery evidence:
  `docs/reports/V123_PROMOTION_READINESS.md`.
  Existing-tool local archive `dist/backups/v123-published-20261020-000001.zip`
  SHA `46e1b4a738378d72c81a90c27fb624d192e088413e78743b3ff59d4d0fb583c7`;
  all805 files verified against original and isolated restored bytes. This is
  local recovery, not off-device backup; no live rollback was performed.
- Branch `task8b/pipeline-migration`; pre-publication HEAD
  `92fd257801f8d49bd0fff7c3b772652591f33d84`. The task-only publication checkpoint
  and actual ordinary-push outcome are reported at delivery; no assumed remote
  backup. Git does not back up ignored runtime data. Stop after publication
  verification and checkpoint; no new ingestion or V1.24 is authorized.

### Historical V1.23 readiness — final human release gate (2026-10-19)

The following readiness snapshot predates the exact approval/publication above;
its pending gate and absent-target statements are historical, not current status.

- Human written Design approval binds commit
  `1c66a8e9daaaa991fc72b3ca891d87251051831b`, file
  `docs/superpowers/specs/2026-10-14-v123-promotion-readiness-design.md`, SHA
  `dac063c914b2a7003295d1306d39b0390329f408bace59c9f14d0e943e943541`.
  Only its approval header is synchronized; technical sections1–10 unchanged.
- Written Plan: `docs/superpowers/plans/2026-10-14-v123-promotion-readiness.md`.
  Self-review and separate read-only technical Plan review completed. Initial
  Critical0/Important0/Minor1 (explicit protected-path enumeration) was remediated;
  targeted independent re-review: Critical0/Important0/Minor0. All16 existing
  candidate trees are covered by the enumerated protection roots. This is Plan
  review only, not implementation certification.
  Human Plan review and Native / Inline implementation authorization received
  2026-10-19. Tasks1–7 implemented and verified under that authorization; no
  publication authority has been received. Implementation checkpoints:
  `94cb717`, `6703041`, `ffb5aa5`, `d463de7`, `cfc20e6`, followed by reviewed
  boundary repairs and the final readiness documentation checkpoint.
- Fresh read-only recovery reconstructs the exact received approval/preflight
  prefix and verifies each of generations000001–000003:24/24 PASS each. Final
  digest remains `c5c51df58d64349d58bd71469fe67a72cced56e77369126d6fec66bb2fcc955a`;
  three batches2023(12),2025(13),Oxford(13),639+38=677 records, not distinct
  originals. No later runtime receipt was present. Four baseline/candidate
  SQLite/manifest SHA+size identities and six authority file refs matched Design.
- Two independent non-formal dry-runs are byte-identical across all4 artifacts;
  independent formal verifier21/21 PASS each. Exact639 baseline and38 promoted
  projections match,677 unique IDs all published/selectable in the dry-runs only.
  Oxford13 publisher-source answers remain unchanged and are not HKEAA MS;
  PDF/page/region locators remain references, not invented image files.
- Actual readiness release digest:
  `84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc`.
  Formal-equivalent SQLite SHA:
  `28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd`.
  Manifest SHA:
  `54d192436e761c9bfe810510b77a902c5ae659bebdfbc4da8475aac271be8498`.
  Full identity/file closure and rollback limits:
  `docs/reports/V123_PROMOTION_READINESS.md`.
- Fresh repaired serial maintained gate1331/1331 PASS (65modules),0 failures,
  errors, skips or expectedFailures; focused plus historical replay51/51 PASS;
  V1.18 independent validator PASS/497. Separate implementation review and
  targeted re-review: Critical0/Important0/Minor0. Initial ownership-race,
  filesystem/sums closure and whitespace findings were repaired with effective
  RED/GREEN; no historical assertions weakened. The earlier full-run failure
  caused by concurrent staging evidence creation is preserved in the report,
  not treated as passing; the final accepted full run was serial.
- All784 protected file identities unchanged. Existing Oxford archive665files
  verified; new local readiness archive795files and isolated restore verified.
  Archive SHA `3b14de979d67272b5265ea51b0b2a2a2120fdafbc0f894c25d9ae91745a93fda`.
  This is local recovery, not off-device backup; Git does not back up ignored data.
- No real candidate writer or publisher called, no default query pointer,
  scheduler or source/approval change. Formal querying remains V1.22/639;
  `releases/V1.23/` remains absent. User AGENTS.md stays unchanged/unstaged;
  2024 remains excluded and unresolved. No further ingestion starts here.
- Next human gate: `USER DECISION REQUIRED — FINAL V1.23 PROMOTION AUTHORIZATION`.
  Only an exact later human approval of the actual release digest can authorize
  publication; this readiness report and generated statement are not approval.

### V1.23 promotion readiness — written Design checkpoint (2026-10-14)

- Historical checkpoint below; its pending Design review is resolved by the
  2026-10-19 approval above. Original verification evidence remains historical.
- Current priority is the entire immutable generation000003, not another Oxford
  import. User authorized minimal missing promotion Design/Plan preparation and
  later Native / Inline execution subject to the existing written approval gates.
  Ordinary reviewed task commit/push is now permitted; the preceding checkpoint's
  no-push instruction is historical. No real publication is authorized.
- Design: `docs/superpowers/specs/2026-10-14-v123-promotion-readiness-design.md`.
  Written Design awaits human review. Plan and implementation NOT STARTED;
  candidate authority and import approvals are not promotion authority.
- Independent read-only Design review and targeted re-review: Critical0,
  Important0, Minor0 after explicitly fixing the baseline schema projection to
  `task12-v122-formal-v1` and requiring an independent literal-oracle regression.
  This is not human Design approval or implementation certification.
- Fresh selected-candidate verifier24/24 PASS; receipt/manifest/SQLite agree on
  2023(12) ->2025(13) ->Oxford(13),38 additions,639+38=677. No later accepted
  generation was found. Candidate digest remains
  `c5c51df58d64349d58bd71469fe67a72cced56e77369126d6fec66bb2fcc955a`.
  SQLite/manifest identities remain those in the accepted-import checkpoint below.
- Fresh publisher-mock plus V123 historical-replay tests18/18 PASS (11.417s),
  including historical formal verifiers; V1.18 independent validator PASS/497.
  Task7 project initialization7/7 PASS; tracked/new-doc whitespace checks PASS.
  All587 protected/candidate checkpoint identities match. Existing local backup
  archive and isolated restore both verify665/665; no new backup service or live
  restore. This is local recoverability, not off-device backup.
- Formal V1.22 remains639; Oxford13 remain candidate/selectable0, not published.
  No V1.23 formal-equivalent build or release digest exists yet. The proposed
  four-file release, formal677 projection and independent verification must be
  implemented and proven only after the written Design/Plan gates.
- No code, tests, scheduler, candidate, formal artifact or evidence changes.
  `releases/V1.23/` remains absent. User's original AGENTS.md remains unstaged
  and byte-identical. No2024 remediation, V1.24, historical cleanup or promotion.

### Real content growth — publication capability checkpoint (2026-10-14)

- User requested published/selectable growth, Oxford first, no schedule changes
  and no automatic GitHub push. Fresh source/approval/canonical/SQLite comparison
  confirms all13 Oxford records retain exact approved complete questions and
  full publisher MS,100 marks, `publisher_mock`/Oxford identity and zero source
  eligibility issues. This reuses approved page review; it is not a new whole-
  PDF transcription or independent mathematical re-solution.
- Current V123 generation000003 independently verifies24/24 PASS. Ledger stays
  2023(12),2025(13),Oxford(13),38 additions/677 candidate total. Formal V122 is
  still639 published/selectable; Oxford formal matches0. Fresh publisher-mock
  and V123 historical-replay tests18/18 PASS; protected587 identities unchanged.
- Concrete publication gap: there is no committed V123 promotion Design/Plan,
  builder, formal verifier or publication approval carrier. Existing V122
  promotion accepts exact V122 candidate/contract types and a V122 release
  digest approval only. It cannot publish V123 by changing an output directory.
  The committed V123 candidate Design explicitly stops before formal release.
  A bounded V123 promotion extension needs its own written/reviewed authority
  under AGENTS before implementation, then real dry-run identity and the final
  exact promotion approval. Do not substitute the candidate digest or pretend
  a release digest exists. No formal V123 artifacts were built this checkpoint.
- Scoped PP follow-up: existing authorized HKDSE staging covers2012–2025;
  2023/2025 supplemental batches already accepted, not replayed.2024's13-record
  proposal still carries Q11 `official_ms_missing` review_required; its accepted
  unknown suffix and evidence are unchanged. `approve_hkdse_pdf_transcription`
  rejects nonempty issues/non-PROPOSED rows. No exact eligible transcription or
  import approval exists for that batch; no diagnostic was cleared to force it.
- Formal newly published records this checkpoint:0. No candidate write, code or
  test edit, schedule change, historical cleanup or push. joy-m2 remains ACTIVE;
  the original user AGENTS change is preserved. Next decision is the minimum
  V123 promotion extension for the intact approved generation000003, not a new
  adapter, ingestion framework or repeat Oxford import.
- Machine-readable checkpoint:
  `data/staging/oxford-c1-review-20261014/publication-capability-check-20261014.json`.

### Auto-ingestion phase 1 — approval-preserving orchestration

**OXFORD EXACT-APPROVED IMPORT COMPLETED — V1.23 GENERATION 000003**

- Exact user import approval was matched to the unchanged READY preflight,
  approved transcription/canonical and independently verified generation000002.
  The committed writer appended13 Oxford records atomically once. Receipt:
  `data/staging/auto-ingestion/receipts/000003.json`.
- Ordered ledger:2023(12) ->2025(13) ->Oxford2025/26 C Set1(13).
  Accepted batches3; cumulative additions38; candidate total677.
  New candidate digest / next parent:
  `c5c51df58d64349d58bd71469fe67a72cced56e77369126d6fec66bb2fcc955a`.
  Candidate SQLite SHA:
  `b7e2247e004cc4c91c339693de4f106edef11bb7067e34b52887547a8006cb01`.
  Candidate manifest SHA:
  `febe70a572b82783bf6199679bf1a2024294d98b44b4fbe047a2349a3830a076`.
  Output: `data/staging/auto-ingestion/candidates/8531b270990b350afbbcdc16eff2fddf63a1f33d7a451402199344eae2447a20/`.
- Fresh independent verifier24/24 PASS;677unique IDs;639published/selectable1
  plus38candidate/selectable0; Oxford13 retain source_provided publisher identity.
  SQLite integrity/FK PASS; rollback contract verified, no live rollback run.
  Two repeat cycles preserve receipt/candidate bytes and create no duplicates;
  final processed0/model0. Fresh V1.23/runner/backup focused suite168/168 PASS,
  V1.18 validator PASS. No code or tests changed for this accepted operation.
  Evidence: `data/staging/oxford-c1-review-20261014/import-000003/REAL_BATCH_IMPORT_VERIFICATION.json`.
- Independent read-only operational review: Critical0 / Important0 / Minor0.
  Exact approvals, ordered parent chain, Oxford identities and candidate status,
  inherited tables/prior-batch rows and protected hashes checked unchanged.
  This review did not repeat whole-PDF transcription or independently re-solve
  mathematics, execute live rollback or establish off-device backup.
- All576 protected/canonical file identities unchanged, including formalV1.18–22,
  prior generations, source/approval evidence,2024 and the dirty userAGENTS.
  Post-append665-file local backup and isolated byte-verified restore PASS:
  `dist/backups/oxford-c1-accepted-20261014-000003.zip`, SHA
  `317afa362a7bfcbe5c256b1c611f90b599013b8fcf4f804c8c73685d6a37b149`.
  Original archives/live paths preserved; off-device backup remains outstanding.

- User authorized direct, reversible implementation while retaining exact
  batch transcription/import approvals. Phase1 is not the long-term approval
  policy. Design/Plan checkpoint: `8d935fa1fa870bf9d91544aafac3349b1e8a7840`.
  Entry point and operating instructions: `docs/AUTO_INGESTION.md`.
- Added an independent ignored SQLite journal, explicit source inventory,
  bounded retries, repository lock, existing Task10B/V123 orchestration,
  parent-bound approval continuation and durable writer-intent recovery.
  No new public ingest API, dependency, formal publisher or model client.
  Unknown sources are identified, not silently parsed or approved. Existing
  evidence passes are required for the supported HKDSE preparation path.
- The user authorized the bounded Oxford `publisher_mock` evidence mapping;
  Design/Plan committed as `c63cfd1`. It reuses the existing runner, V1.23
  preflight/atomic writer/verifier; the HKDSE profile and public API are unchanged.
  Original mock question IDs, Oxford/2025-26/C Set1 identity and PDF/page/mark
  provenance are retained. Outline/missing MS or unresolved necessary figures
  cannot become an approved canonical package.
- Actual PP question pages and all23 publisher-MS pages were inspected. The
  new13-record/100-mark proposal supplements original outlines with full
  publisher solutions/marking, including Q11 equations, Q12(b) and alternatives.
  It is not HKDSE official MS, nor an independent re-solution of all mathematics.
  Controlled taxonomy passes; no unresolved source/review issues remain.
  Proposal: `data/staging/oxford-c1-review-20261014/proposal-000001/transcription.json`.
  Digest: `2038db4f3486aae8a92ec0e38acc338f9c0c2782a5b245301cca85792a29928f`.
  Exact user transcription approval received and saved unchanged in
  `data/staging/oxford-c1-review-20261014/received-transcription-approval.txt`.
  Real canonical generation and parent-bound preflight completed with the
  committed implementation `bca7aed`. The later exact import approval has now
  been consumed once by the successful operation recorded above.
- Actual preflight: READY, detected13/new13/duplicate0/rejected0/ambiguous0,
  adaptations0/issues0; answers present13, independent explanations missing13.
  Difficulty L2=1/L3=7/L4=3/L5=2; no missing/orphan images. Current fingerprint
  classification is not a global semantic original-question uniqueness claim.
  Approval-bound pre-import parent was
  `9d6b16cf357e7d32268552ab17c74a16a409d502d7873aa6c7a3854f77edebb9`;
  before664/projected677, subsequently appended as above. Preflight SHA:
  `8531b270990b350afbbcdc16eff2fddf63a1f33d7a451402199344eae2447a20`.
  Canonical manifest SHA:
  `f015d0f334379c7ae524077c80c74f768c831cfcdc0b62f963f0ff07eba96b67`.
  Review/report: `data/staging/oxford-c1-review-20261014/preflight-000001/`;
  package: `data/staging/auto-ingestion/packages/2038db4f3486aae8a92ec0e38acc338f9c0c2782a5b245301cca85792a29928f/`.
  Fresh read-only prefix verification24/24 and focused regressions49/49 PASS;
  two identical replay cycles processed0/model0, same report and package bytes.
  All571 combined protected/present-generation file identities unchanged.
- Resume config: `data/staging/oxford-c1-review-20261014/runner.json`.
  Repeated identical real runs processed0, `no_change=true`, model calls0;
  original draft, source PDFs and evidence are preserved. Receipt/crash recovery
  and exact approval continuation are tested with isolated synthetic inputs.
- Original2023/2025 receipts independently replayed:24/24 candidate checks,
  generation000002,25 additions,total664, digest
  `9d6b16cf357e7d32268552ab17c74a16a409d502d7873aa6c7a3854f77edebb9`.
  No writer replay.2024 Q11 proposal/accepted-defect evidence remains unchanged
  and unapproved, isolated from the Oxford job. All563 prior protected file
  identities were checked unchanged; formalV1.22 remains639/originalSHA.
- Final full maintained run1285/1285 PASS,0failures/errors/skips/expected failures;
  final focused49/49 PASS includes both SQLite backup regressions.
  Independent reviewer inspected all new
  implementation and real PP/MS, found and verified the WAL-backup correction;
  final Critical0 / Important0 / Minor0, independently reran19 new tests across
  the two review rounds. V1.18 validator PASS. Historical legacy attribution is
  9PASS/2knownFAIL (SQLite hash/frozen byte-equivalence); not rerun for this extension.
- Independent local ignored-data archive and isolated restore verified637 files,
  including Oxford evidence, runner state, accepted prefix and protected inputs.
  Archive: `dist/backups/oxford-c1-checkpoint-20261014-000001.zip`.
  SHA: `d029babf84a1a895c88d7fc535f9742278c261388a8f45acf31fdb579eb917d3`.
  Result: `data/staging/oxford-c1-review-20261014/BACKUP_RECOVERY_RESULT.json`.
  No live path was restored. This is local-disk recovery, not off-device backup.
- After transcription approval/preflight, a new immutable649-file archive and
  isolated restore also passed: `dist/backups/oxford-c1-preflight-20261014-000002.zip`;
  SHA `5d724c6b63f081da1484e5f2e2fdcf9c8e0839ce7b1a5d244912f73799a47613`.
  Prior archive is preserved; neither archive is an off-device/Git backup.
- Daily incremental check enabled by explicit user authorization: Codex local
  thread heartbeat `joy-m2`, daily09:00 using host Asia/Shanghai timezone.
  PAUSED registration and ACTIVE resume were read back; scheduler's recorded
  first due time is2026-10-15 09:01:25+08:00 (not an exact-second guarantee).
  It targets this existing worktree and runner config, not a new checkout.
  No duplicate ingestion schedule found. Smoke:processed0/no_change=true,
  model_calls0/no new write; BUSY lock check PASS, candidate verifier24/24 PASS,
  protected587 identities unchanged; current generation/receipt covered in the
  verified665-file archive. Evidence: `data/staging/auto-ingestion/daily-check-enablement-20261014.json`.
  App/thread notifications are restricted by the task instructions to new
  approvals or blocking identity/backup failures; first unattended run and OS
  notification delivery have not occurred/tested. Scheduling itself uses a
  model; Python ingestion does not. No code/tests or approval policy changed.
  Phase2 simplification remains advisory. No further batch started here.
- UserAGENTS remains byte-identical to its incoming dirty state, unstaged and
  uncommitted. Runtime journal/candidates/reports are ignored, not carried by Git;
  the separate archive above provides the tested local recovery checkpoint.
  No releases/V1.23, promotion or historical cleanup.

### HKDSE 2025 exact-approved append — V1.23 generation 000002

**APPROVED 2025 IMPORT COMPLETED — OPERATIONAL CHECKPOINT / STOP**

- Before execution, actual receipts and candidate files showed only the2023
  generation000001;2025 had not been written. Reconstructed the exact approved
  transcription, canonical package, READY preflight and independent parent
  verification before consuming the newly received2025 import approval once.
  Existing successful output is verification-only on subsequent invocations;
  an output/receipt mismatch is a recovery blocker, never a reason to rebuild.
- Consumed exact preflight
  `732f05c7d36203fcb920d5bfd59673041533abb84db5d82e6fa8fc3407bda5e0`
  against parent
  `f2fb80e7a7f9e4478877446a8e74cccac8cd1c8829784cef0eb93637bcfacaf1`.
  Existing writer independently reconstructs the approved ordered prefix and
  validates before atomic no-replace publication into the new staging root.
- Complete accepted ledger:
  1. `000001 — JOY-M2-HKDSE-2023-PP-MS`:12 records; cumulative12; total651.
  2. `000002 — JOY-M2-HKDSE-2025-PP-MS`:13 records; cumulative25; total664.
  These are additional source records for already-represented originals, not
  a claim of25 first-time original questions. No old record was merged/deleted.
- New candidate digest / next parent authority:
  `9d6b16cf357e7d32268552ab17c74a16a409d502d7873aa6c7a3854f77edebb9`.
  Candidate SQLite SHA:
  `3bc409ce5e7afa01706a023b990ac99842484d65409e2c843a94565711dd1470`.
  Manifest SHA:
  `d10afaa7eb1453b8ccd05d85cd67e897ebd74692f0b9627678b8a54633c1047b`.
- Output: `data/staging/task13-v123-hkdse-2025/candidate-generation-000002/`.
  Exact received import approval and original success receipt are
  `REAL_BATCH_IMPORT_APPROVAL.json` and `REAL_BATCH_IMPORT_RECEIPT.json` in its
  parent directory. The receipt contains the complete ledger, approval chain,
  artifact hashes, independent verification and protected-file snapshot.
- Independent candidate verifier24/24 PASS; SQLite integrity/FK PASS;
  664unique IDs =639 inherited published/selectable1 +25 candidate/selectable0.
  Formal V1.22 remains639 with its original SHA and verifier21/21 PASS.
  All563 protected identities remain unchanged, including formalV1.18–22,
  oldgeneration000001, canonical/source/approval evidence,2024 and userAGENTS.
- Fresh scoped regression: V123119 +Task7 7 =126/126 PASS;
  Task10B50 +Task9A41 =91/91 PASS; no skips/expected failures.
  V1.18 validator PASS. No production/test change or full-maintained-suite claim.
- Independent operational reviewer: Critical0 / Important0 / Minor0. With
  writer disabled, readonly replay returned the original successful receipt;
  all639 inherited rows matched field-by-field and in order,25candidate rows
  had the required state, all563 protected hashes and254reviewed runtime
  artifacts remained unchanged. No duplicate2025 acceptance or2024 approval.
- 2024 remains unapproved/unaccepted; its accepted local source defect and all
  evidence remain intact. No releases/V1.23, promotion or next-batch work.
  Prior preflight sections below are historical and do not authorize reuse of
  their now-consumed parent. Any future batch needs the actual latest parent.
- This operational append has no mandatory remote-sync-before-write gate.
  Ordinary documentation backup is separate from ignored candidate/receipt
  backup; Git push does not back up these runtime artifacts. UserAGENTS remains
  unchanged and unstaged. Stop after this batch.

### HKDSE 2025 approved transcription / pre-append preflight evidence

**HISTORICAL APPROVAL GATE — CONSUMED BY GENERATION 000002 ABOVE**

- The user explicitly accepted the unknown cropped suffix of the2024 Q11(c)
  first1M remark, without confirming missing characters or approving the batch.
  Existing Task10B approval cannot represent an accepted issue; the original
  proposal and its diagnostic remain unchanged. The same instruction expressly
  authorized2025 preparation if2024 cannot proceed under the existing contract.
- Reused local2025 PP/MS,13-question/100-mark staging, historical question
  contents and the existing year-specific audit. No whole-year OCR or source
  re-upload. New ignored root:
  `data/staging/task10b-hkdse-2025/source-review-000001/`.
  Complete review: `FULL_TRANSCRIPTION_REVIEW.md`; proposal:
  `transcription-proposal-000001/transcription.json`.
  Exact human-approved transcription digest:
  `35d28e145a03726c066170406980671979d689af8decec462a8987e4b247e13d`.
  Received approval is recorded in `TRANSCRIPTION_APPROVAL.json` under that
  source-review root. The existing approval API reconstructs the semantic
  digest and produces VERIFIED carriers; the stored proposal stays unchanged.
- All13 questions/100marks and complete officialMS were visually reconciled to
  source pages and independently reviewed. Q3(b) both methods, Q8 exact score
  alignment, Q12(b) shared assumptions and Q13 shared method marks are retained.
  Source bare1 scores and Q11(b)(ii)'s final1M are not silently rewritten.
  Review_required0 / issues0 / unknown_primary_type0 / unknown_tag0.
  There are no source figures; MS sign tables are preserved as tables.
- Source PP SHA:
  `79cd39e9ea906f57a2db9167de6e5920955bd39b13e315e8b42084022d175d5c`;
  MS SHA:
  `e9ec8117424f47e3ebc30ce71f491ae74626238855b3c8ec76ed88c2e1ef15ca`.
  New staging copy corrects page anchors and controlled taxonomy, retaining
  original difficulty, marks, IDs, order and source identities. Its serialized
  original-staging snapshot is semantically identical, not a byte-identical
  copy; both actual source and snapshot SHA are recorded separately.
- Two roots reproduce identical four proposal files and semantic digest.
  Pass agreement is source-reconciled after separate review, not blind OCR.
  These13 originals already have historical formal records. Current preflight
  classifies13 additional stored records, not13 first-time original questions;
  no historical record is overwritten or merged.
- New ignored operation root:
  `data/staging/task13-v123-hkdse-2025/preflight-20261013-000001/`.
  `canonical-a` and `canonical-b` contain the same five files byte-for-byte;
  original question/MS, taxonomy, difficulty, subparts and source references
  are unchanged. Both independent-root preflights produce identical candidate
  tuples, issues, report and digest. Complete report: `PREFLIGHT_SUMMARY.json`;
  full result: `PREFLIGHT_RESULT.json`.
- Actual status: `READY FOR USER IMPORT APPROVAL`; detected13 / new13 /
  duplicate0 / rejected0 / ambiguous0 / adaptations0 / issues0; missing
  answers0 / missing independent explanations13 / canonical image files0.
  Difficulty counts: L1=1, L2=4, L3=4, L4=2, L5=2. Existing count651;
  projected count after approval664. Real import approved_count remains0.
  Preflight SHA:
  `732f05c7d36203fcb920d5bfd59673041533abb84db5d82e6fa8fc3407bda5e0`.
  Canonical manifest SHA:
  `d3ebf556340a1e278d1141e2c87432c5dc12c2c113ca8566db90d8957a0c5862`.
  Required verified parent:
  `f2fb80e7a7f9e4478877446a8e74cccac8cd1c8829784cef0eb93637bcfacaf1`.
- At this pre-append checkpoint, no2025 import approval, writer or new candidate
  existed. Its ledger contained only2023;2024 remains unaccepted and its
  preserved source-defect decision is not replaced by this2025 approval.
  On later exact import approval, reverify unchanged content and current parent
  before any atomic append. No automatic further batch or formal release.
  Git documentation backup does not include ignored runtime artifacts.
- Fresh scoped gates: Task10B50/50, Task9A41/41, V123119/119 (models,
  bridge, preflight, candidate and historical replay), Task7 7/7; no skipped
  or expected failures. V1.18 validator PASS; actual formalV1.22 verifier21/21
  and parent candidate verifier24/24 PASS. Read-only preflight replay PASS.
  All534 protected file identities remain unchanged, including prior2024 and
  2025 source evidence, formal releases, existing candidate and userAGENTS.
  Formal639 / candidate651 remain unchanged. No code/tests changed and no
  claim that the entire maintained suite was rerun for this operation.
- Independent operational review: Critical0 / Important0 / unresolved Minor0.
  Reviewer independently reconstructed the transcription digest, replayed
  parent-bound preflight and checked complete canonical/source/MS mappings
  plus all534 protected identities. Review-request report:
  `REAL_BATCH_IMPORT_REVIEW.md` in the operation root; it is not an approval
  receipt. That requested real-import approval was subsequently received and
  consumed by generation000002 above; do not request or consume it again.

### HKDSE 2024 PP/MS operational preparation — V1.23

**LOCAL SOURCE DEFECT ACCEPTED — EXISTING APPROVAL CONTRACT BLOCKED**

- The user separately authorized2024 preparation using the existing Task10B /
  V123 implementation; no new architecture or implementation work. Existing
  generation000001 was independently verified24/24 and remains unchanged:
  accepted2023 batch1, additions12, projected651. Its preparation-time parent was
  `f2fb80e7a7f9e4478877446a8e74cccac8cd1c8829784cef0eb93637bcfacaf1`.
  This is historical, not the current parent after2025's generation000002.
- Reused the actual2024 PP/MS,13-question/100-mark staging,13 historical formal
  source records and existing source-audit figure crops. This is additional
  source preparation for known originals, not a claim of13 first-time originals
  or13 accepted/new storage records. No2024 authoritative preflight has run.
- New ignored operation root:
  `data/staging/task10b-hkdse-2024/source-review-000001/`.
  Proposal: `transcription-proposal-000001/transcription.json`; full human
  review: `FULL_TRANSCRIPTION_REVIEW.md`; evidence: `operational-evidence.json`.
  Unapproved transcription digest:
  `48f260c37950c2e852abe326fcd1501e6058246312b5f1898daa29b8f49e3cb7`.
- All13 question texts and100 marks were visually checked against PP; full
  officialMS steps, alternatives, shared scoring and page anchors were read
  against MS2–18, separately from historical answer summaries. Independent
  source reviewer confirmed12 complete MS records and Q11 partial evidence.
  Sole unresolved source field: Q11(c), MS physical13 / printed83, first1M
  remark visibly ends `保留不給 1M 若遺漏步`; the high-resolution original edge
  does not reveal any following characters. No inferred completion was made.
  The user has now explicitly accepted this local defect while keeping the
  suffix unknown; do not request the same screenshot or complete PDFs again.
  Decision binding and teaching limitation are recorded in
  `human-source-acceptance-000001/ACCEPTED_LOCAL_SOURCE_DEFECT.json` and
  `REVIEW_RESOLUTION.md` under this operation root. No missing letter was
  confirmed. Do not borrow2025's similar but fully legible note to complete it.
- The reviewed passB withholds a *complete* Q11 MS string; passA and the proposal
  retain all available Q11 mathematics, both(b) methods and the partial remark.
  Existing adapter reports review_required1 / issues1 (`official_ms_missing`).
  Its MS-complete13 metric merely counts nonempty A strings, not complete source
  validation; actual fully confirmed MS count is12/13. Auto-agree12 describes
  source-reconciled serialization after independent review, not blind extraction.
- Controlled taxonomy: unknown_primary_type0 / unknown_tag0. Q12 is mapped to
  matrices/linear systems/vectors, not its historical integration misclassification;
  Q1's unsupported trigonometry and Q6's generic application tags were excluded.
  Q5's English module label was aligned; original difficulty, marks, order and
  source identities remain. Changes exist only in a new staging copy.
- Q9 figure is bound to PP12 / printed39; Q10 official graph to MS10 / printed80.
  Existing audit crops were hash-verified and reused. These are source locators
  and audit evidence, **not generated canonical image files**.
- Two proposal roots have identical four output files and reconstructed digest.
  Fresh gates: Task10B50/50, Task9A41/41, Task7 7/7, V1.18 validator PASS;
  V1.22 independent formal verifier21/21 and V123 candidate verifier24/24 PASS.
  All338 protected identities (formal releases, historical/candidate evidence,
  source files and the user's AGENTS.md) remain unchanged; formal V1.22=639.
  No code/tests changed and no fresh full maintained-suite claim is made.
- No2024 transcription approval, canonical package, preflight, real writer or
  promotion. Design sections9/12 and the approval API reject any issue/non-
  PROPOSED record; there is no accepted-defect carrier. The minimum unresolved
  authority decision is a narrow digest-bound review resolution that preserves
  this unknown and its teaching restriction. No contract or code was changed.
  Do not clear diagnostics or fabricate VERIFIED. The original payload/digest
  is unchanged and is not offered as an eligible final approval. Conditional
  2025 preparation is now separately authorized above, not a2024 import.
  No releases/V1.23 or V1.24 work. The user's AGENTS.md change is untouched.

### V1.23 minimal candidate roll-forward / HKDSE 2023 preparation

**APPROVED 2023 IMPORT COMPLETED — V1.23 CANDIDATE GENERATION 000001**

- The exact human batch/preflight/V1.23/genesis approval was received and
  consumed once on 2026-10-13. Fresh preflight reproduced the approved digest
  before the existing atomic no-replace writer ran; no package rebuild or
  transcription change. Receipt and received approval:
  `data/staging/task13-v123-hkdse-2023/REAL_BATCH_IMPORT_RECEIPT.json` and
  `REAL_BATCH_IMPORT_APPROVAL.json` in the same ignored operation root.
- Candidate: `data/staging/task13-v123-hkdse-2023/candidate-generation-000001/`.
  Ledger: `000001 — JOY-M2-HKDSE-2023-PP-MS`; accepted batches1, additions12,
  projected records651. All12 are known-original additional-source records,
  not twelve previously unrepresented original questions. Existing rows remain.
  Candidate digest / required next parent:
  `f2fb80e7a7f9e4478877446a8e74cccac8cd1c8829784cef0eb93637bcfacaf1`.
  Candidate SQLite SHA:
  `4c37c43d1ea2c34c7837ff275331c5289e4089b5177237001492996233c83a35`.
  Candidate manifest SHA:
  `bd21d622fde3af459bcf7105e877650d51c3b43a72c4806208450b8416b542c6`.
- Independent candidate verifier24/24 PASS; subsequent read-only replay PASS.
  SQLite integrity/FK and651 unique IDs PASS:639 published/selectable inherited
  records plus12 candidate/nonselectable records. Formal V1.22 remains639.
  All332 protected identities, including original sources, approved proposal,
  canonical roots, historical artifacts and the user's AGENTS.md, are unchanged.
  Fresh operational gates: V123119/119 (including historical formal verifier
  replay), Task9A41/41, Task10B50/50, Task7 7/7, V1.18 validator PASS.
  No production/tests changed; the earlier1236/1236 full maintained gate remains
  the implementation checkpoint, not a claimed fresh full-suite run today.
  Independent operational reviewer `v123_implementation_review`: C0/I0/M0;
  separately reconstructed exact approval/preflight and verified24/24, all639
  inherited rows field-by-field/in order,12 candidate rows and file preservation.
- At the2023 import checkpoint, execution stopped after that batch; the later
  separate2024 preparation authorization is recorded above. No2025 work,
  V1.23 formal release/promotion or formal-query pointer change is authorized. Q6 remains
  PDF/page/region evidence only; independent explanations remain missing12.

- Approved Design: `docs/superpowers/specs/2026-10-09-v123-next-version-candidate-design.md`.
  The user explicitly approved the written Design and authorized its Plan.
  Plan: `docs/superpowers/plans/2026-10-09-v123-next-version-candidate.md`.
  The user explicitly approved the committed Plan and Native / Inline Execution.
  Task 1 models, exact API scaffolds and strict loader are GREEN (35 new tests;
  90 including six historical surface suites). At that checkpoint other APIs were scaffolds;
  this is not a completed candidate implementation or real-import authority.
  Task 2 bridge is now GREEN: 11 focused tests / 96 with models and Task10B.
  Five-file output, four unchanged non-manifest projections, duplicate-looking
  source retention and PDF-locator-only image semantics are locked. Genesis
  preflight and candidate writing were still unimplemented at that checkpoint.
  Task 3 genesis preflight is now GREEN: 23 focused / 69 cumulative V123 tests.
  It indexes all 639 formal rows with exact baseline identity, reads published/
  selectable rows only and preserves duplicate/collision/adaptation semantics.
  Task 4A first-generation writer/verifier is GREEN: 23 focused / 93 cumulative.
  Task 4B1 verified-parent preflight is GREEN: 9 focused / 56 candidate+preflight.
  Task 4B2 multi-batch writer/verifier is GREEN: 9 focused / 111 cumulative.
  Task5 final serial maintained gate is GREEN: 1236/1236, with zero failures,
  errors, skips or expected failures. V123119/119 includes historical replay5/5;
  Task9A41/41, Task10B50/50, Task7 7/7 and V1.18 validator PASS.
  Independent implementation review/re-review is Critical0/Important0/Minor0.
  One artifact-ancestor protection defect was fixed with genuine RED→GREEN,
  confined to V123 boundaries; historical APIs and functions remain unchanged.
  The initial concurrent staging snapshot failure is recorded in the report;
  final gates run serially without weakening any assertion.
  Engineering checkpoint `ae9ad0a7f47b771007194f07d7a14d5cb3a2f283` was
  ordinarily pushed and verified local/upstream0/0 before Task6.
  Task6 has now reused the approved2023 transcription, producing two identical
  five-file canonical packages and matching authoritative read-only preflights.
  At that Task6 checkpoint no real writer was authorized or called; the separate
  exact approval and completed operation are recorded above.
  Do not request the completed Design approval again.
- Actual2023 result: READY FOR USER IMPORT APPROVAL; detected12/new_candidate12/
  duplicate0/rejected0/ambiguous0/adaptations0/issues0/approved0.
  Before639; projected651 only after exact approval and successful append.
  Preflight SHA `64b61671f337dafddd5d316ca0e9ba837e24948fe91256c5df7d1c1b779059a4`.
  Parent artifact=None; exact genesis authority
  `ea3b7db78210e045761784a2e415387c1b17f13b5aedde484ca2ae248a45eec7`.
  New operation root:
  `data/staging/task13-v123-hkdse-2023/preflight-20261012-000001/`;
  `canonical-a` is the proposed consumption package; `canonical-b` is the
  byte-equivalent replay. Human report: `REAL_BATCH_IMPORT_APPROVAL_REPORT.md`.
  All12 are known-original additional-source/content-evidence records, not12
  previously unrepresented originals. At the pre-approval checkpoint actual
  new stored records were0; the approved append above has now stored12.
  Missing answers0; independent explanations missing12. Q6 retains approved
  PDF/page8/region evidence only, with no generated canonical image files.
  No new transcription approval was needed; the separate exact real-import
  approval has now been received and consumed once.
  Separate independent read-only Task6 evidence review: C0/I0/M0.
- Formal V1.22 remains the published 639-record baseline; this is not a count
  of semantically distinct originals. All V1.18–V1.22 formal identities and old
  candidates remain frozen. No `releases/V1.23/` exists; the new non-formal
  V1.23 generation000001 is identified above.
- Existing 2023 originals are already represented by `2023-Q1`–`2023-Q12`.
  Full official MS/figures/source supplementation is useful, but the existing
  classifier is fingerprint-based and the writer only appends records. Exact
  duplicate/collision blockers remain blocking; no old-record update operation
  or guaranteed twelve-record addition is authorized. Design section 4 records
  the exact preserved cases and the narrow decision needed if supplementation
  cannot be accepted under them.
- The separate Task 10B track completed a new 12-question/100-mark proposal
  under ignored `data/staging/task10b-hkdse-2023/source-review-000001/`, reusing
  verified PP/MS and local page evidence. The original staging is metadata,
  not a complete approved transcription. No 2023 transcription/import approval
  is fabricated or inherited from another year.
- Proposal: `transcription-proposal-000001/transcription.json` within that root;
  digest `3a3a223a23f694083469281c64be5c5402152c557e3bc36654d400ce5143d618`.
  Full human review: `FULL_TRANSCRIPTION_REVIEW.md`. The original proposal
  preserves its 12 PROPOSED records as immutable pre-approval evidence. Issues and
  review-required records are zero; both controlled-vocabulary unknown counts
  are zero. Two independent output roots reproduce the same four proposal files.
- Exact human transcription approval for this batch/digest has now been received
  and saved as `TRANSCRIPTION_APPROVAL.json` within the same ignored root.
  The existing `approve_hkdse_pdf_transcription` API reconstructed and verified
  the exact proposal, producing 12 VERIFIED records / 100 marks without changing
  any question, MS, metadata or original proposal file. The pre-approval review
  and operational-evidence files remain unchanged historical snapshots.
  This approval does not approve the V1.23 Design, create canonical/preflight
  output, authorize a real import, or grant promotion. Written Design has since
  been separately approved; Plan and Native execution approval have now followed.
- Independent source reviewer `hkdse2023_source_review` visually checked the
  twelve PP question pages and nineteen MS pages. Q6's two figures are bound
  to the original PDF SHA/page/region; Q7's shared (b) condition and Q10's
  notation are preserved. Full official alternatives/marking notes are included.
  Source-backed page/taxonomy corrections use a new staging copy; original
  artifacts are retained. Q7's integral tag and Q12's unsupported application
  tag were corrected before final review (Critical 0 / Important 0 / Minor 0).
  Pass B records this source reconciliation, not a claimed blind transcription.
- Before any real canonical package/preflight, BOTH the version implementation
  and exact human transcription approval must pass. Real candidate writing
  then requires exact batch/preflight/V1.23/parent import approval.
- Historical cleanup is paused, not an ingestion prerequisite. No merging,
  deletion, whole-library recategorization or historical approval reconstruction.
  This2023 preparation checkpoint did not authorize2024 processing; the separate
  later authorization is recorded above. Promotion remains unauthorized.
  Preserve the user's unrelated AGENTS.md edit.
- Docs checkpoint checks: Task 7 7/7, Task 10B 50/50, V1.22 independent formal
  verifier 21/21 and V1.18 validator PASS; no skipped/expected-failure tests.
  The 292-file protected audit snapshot and the pre-existing AGENTS.md content
  remain unchanged. No production/tests changed; the full maintained suite is
  reserved for the later implementation gate, not rerun for this docs draft.
- Independent written-Design technical reviewer `v123_design_review` checked
  actual predecessor code, formal SQLite and genesis: Critical 0 / Important 0 /
  Minor 0 after a classification-wording correction. Human written-Design
  approval has now also been explicitly received, separately from this review.
- Plan dependency gates: models/scaffolds -> strict loader -> canonical bridge
  -> genesis preflight -> first-generation writer/verifier -> verified-parent
  preflight -> multi-batch writer/verifier -> full regression/independent review
  -> already-approved 2023 canonical/read-only preflight -> real import gate.
  No claim of parent/multi-batch behavior RED before its prerequisite GREEN.
  Existing duplicate/collision blockers and PDF-locator-only image projection
  remain unchanged; no forecast of twelve net-new records.
- Plan self-review and independent technical reviewer `v123_plan_review` PASS:
  Critical 0 / Important 0 / Minor 0. Closed scope is exactly 23 Design paths;
  all five APIs and eighteen appended exports are mapped to tests. Corrected
  one test-preparation ambiguity (valid manifest before preflight file-tamper
  controls); no production or test implementation has begun. Fresh planning
  checks: Task 7 7/7, Task 10B 50/50, approved transcription binding 12 records /
  100 marks, formal read-only count 639/639 unique IDs, 292 protected identities
  unchanged, exact genesis recomputation and diff checks PASS. The next action
  was human Plan review and execution confirmation; that gate is now complete.

### Historical V1.22 approved formal publication — 2019–2022

**CLOSED / PASS — HUMAN-APPROVED FORMAL V1.22 PUBLISHED**

The user explicitly supplied:
`USER APPROVED RELEASE PROMOTION V1.22 89a592abf52507cc0325f9c6f30ee2c74d4ec55fdcef988fdae6cb12f5a3073b`.
The committed publisher at `c5f946b88966447603b77b9ab4186ea14c74d088`
consumed that exact approval once and atomically published the four byte-identical
dry-run files to `releases/V1.22/`. No candidate rebuild/import replay occurred.

- Formal release digest: `89a592abf52507cc0325f9c6f30ee2c74d4ec55fdcef988fdae6cb12f5a3073b`.
- Manifest SHA: `441e00ac1536b959b40b6177bd17a6f14632a287f85145e202a51bcf137ddc8b`.
- Semantic SHA: `964cceff64cdeaedf663d1f9be98aaaf6adf3ffe2cddf6a18447ea141948a1c4`.
- Independent formal verifier: 21/21 PASS; candidate verifier: 24/24 PASS.
- 591 inherited records + four approved 12-question batches = 639; new rows
  are published/selectable, with original content/provenance preserved.
- Pre-publication maintained gate: 1117/1117 PASS, zero skips/expected failures.
- Post-publication maintained gate: 1117/1117 PASS, zero failures/errors/skips/
  expected failures; independent publication review Critical 0 / Important 0.
- All 275 protected historical/candidate/source files retain their identities.
- Design §6 permits recording this human-approved digest in the existing
  lifecycle test literal; no test logic or production code is changed.
- At this publication checkpoint no app/query configuration switch, rollback,
  2023 ingestion or V1.23 work occurred. The later authorization above now
  governs the next operational work; publication itself remains CLOSED / PASS.

### Historical V1.22 promotion readiness — 2019–2022

**TECHNICAL READINESS PASS — PENDING EXPLICIT FINAL PROMOTION AUTHORIZATION**

The user's 2026-09-27 authorization permits fixed-version Design/Plan, TDD,
isolated dry-run, independent review and engineering checkpoint only.
Authority: `docs/superpowers/specs/2026-09-27-v122-promotion-readiness-design.md`
and corresponding Plan (docs checkpoints `174ee6d`, `31b4b35`).

- Exact input remains generation 000004, candidate digest
  `82b10a551f70eebda2e0aa4d10c962e317767e936b4f0d9aa798629bb8070d46`.
- Ordered approved 2019–2022 ledger: four batches, 12 each; 591 + 48 = 639.
- Two non-formal dry-runs are byte-identical and independently verify 21/21.
- Actual dry-run release digest:
  `89a592abf52507cc0325f9c6f30ee2c74d4ec55fdcef988fdae6cb12f5a3073b`.
- Candidate generations and formal V1.18–V1.21 remain unchanged.
  Formal production/query baseline is still V1.21/591.
- Fresh maintained regression: 1117/1117 PASS; promotion focused: 34/34 PASS;
  no skips or expected failures. Legacy Task 3–6 gates: 54/54 PASS.
- Independent implementation review: Critical 0 / Important 0 / Minor 0.
  Candidate verifier 24/24, both dry-run formal verifiers 21/21,
  historical formal verifiers and V1.18 validator PASS.
  Evidence and exact artifact hashes: `docs/reports/V122_PROMOTION_READINESS.md`.
- `releases/V1.22/` remains absent. No real promotion approval has been supplied
  or consumed. No 2023 ingestion or V1.23 work.

At the readiness checkpoint, the human gate was:
`USER DECISION REQUIRED — FINAL V1.22 PROMOTION AUTHORIZATION`.
It was subsequently satisfied by the explicit approval recorded above;
technical readiness alone did not authorize publication.

### Historical operational checkpoint — HKDSE 2022 V1.22 generation 000004

**APPROVED REAL BATCH IMPORT — CANDIDATE VERIFIED; NOT FORMALLY PUBLISHED**

The user supplied the exact 2022 import statement recorded below. Fresh
two-root preflight and the complete verified parent chain matched that approval
before the maintained writer atomically created only the new staging generation:
`data/staging/task12-v122-hkdse-2022/candidate-generation-000004`.

- Accepted ledger: `000001 JOY-M2-HKDSE-2019-PP-MS`,
  `000002 JOY-M2-HKDSE-2020-PP-MS`, `000003 JOY-M2-HKDSE-2021-PP-MS`,
  `000004 JOY-M2-HKDSE-2022-PP-MS`; 12 complete questions per batch.
- This append: 12 net-new questions. Accumulated additions: 48;
  projected V1.22 count: 639. Formal production remains V1.21/591.
- New candidate digest / required parent for any later authorized batch:
  `82b10a551f70eebda2e0aa4d10c962e317767e936b4f0d9aa798629bb8070d46`.
- Consumed preflight:
  `ae96a9a971fafdd6e900ced6f80ee39d4c1365e166b5d4efa7fbcc47383b1fad`.
- Consumed parent:
  `20342ba339ef8200ee6d941683d12698c2504c0872548a26717b2771ee2d1707`.
- Candidate SQLite SHA:
  `f1adf0ff7c2034445b1ee4724c03e8c66c6026c5e94d37cc469e1b350c2a9a7a`.
- Candidate manifest SHA:
  `dc974a1f3180fc3d7d416385242d21aec78266f4e52f5a9de5732f31d57a5403`.
- Independent candidate verifier: 24/24 PASS; 591 preserved formal rows plus
  48 candidate rows, with candidate status and `selectable=0`.
- Receipt: `data/staging/task12-v122-hkdse-2022/REAL_BATCH_IMPORT_RECEIPT.json`.
  Original source/transcription, canonical packages and pre-import report
  remain unchanged. Q9 MS graph remains a PDF source locator, not a new crop.
- Fresh pre-write regressions: 175/175 PASS; V1.18 validator PASS.
  No code, tests, Design or Plan change was required.
- Separate-process post-write candidate read-back: 24/24 PASS; Task9A,
  Task7 and historical replay: 51/51 PASS, no skips/expected failures.
- Independent read-only operational/documentation acceptance: Critical 0 /
  Important 0 / Minor 0; verifier, exact ledger and protected hashes confirmed.

All V1.18–V1.21 formal bytes and generations 000001–000003 remain unchanged.
`releases/V1.22` is absent. No promotion, 2023 ingestion or V1.23 work.
That operational checkpoint stopped for the user's next selection. The subsequent
readiness-only authorization is recorded above; further ingestion remains unauthorized.

### Historical checkpoint — HKDSE 2022 V1.22 import approval gate

**USER DECISION REQUIRED — REAL BATCH IMPORT**

The user supplied the exact 2022 transcription approval shown in the historical
checkpoint below. The maintained approval API reconstructed that digest and
returned 12 VERIFIED records, changing only their status. The original proposal
and source evidence remain byte-identical.

- Batch: `JOY-M2-HKDSE-2022-PP-MS`; 12 whole questions / 100 marks.
- Actual preflight SHA:
  `ae96a9a971fafdd6e900ced6f80ee39d4c1365e166b5d4efa7fbcc47383b1fad`.
- Required current parent:
  `20342ba339ef8200ee6d941683d12698c2504c0872548a26717b2771ee2d1707`.
- Status: READY FOR USER IMPORT APPROVAL. Detected/new: 12/12;
  duplicate/rejected/ambiguous/adaptations: 0/0/0/0; issues: 0;
  approved_count: 0. Before/projected count: 627/639.
- Missing answers: 0. Missing independent explanations: 12; official MS is
  retained in full, without fabricated supplementary explanations.
- Difficulty: D2:4 / D3:4 / D4:2 / D5:2. Controlled taxonomy summaries and
  exact source/canonical identities are in the approval report.
- Canonical image files/paths: 0/0. Q9(c)'s official MS graph remains an
  explicit PDF SHA/page locator in the transcription, answer and source map;
  no reviewed crop was supplied or invented. Enrichment remains incomplete.
- Canonical roots under `data/staging/task12-v122-hkdse-2022/`:
  `canonical-v122-approved-a` and `canonical-v122-approved-b`.
  Their file bytes and complete preflight results are identical.
- Report: `data/staging/task12-v122-hkdse-2022/REAL_BATCH_IMPORT_APPROVAL_REPORT.json`.
- All three previous batches were reconstructed from their immutable canonical
  packages and recorded approvals, then independently verified with 24 checks
  per generation. The exact current ledger is 2019, 2020, 2021; no 2022 entry.
- Formal V1.18–V1.21, all existing candidate generations and source proposals
  remain unchanged. Formal production is V1.21/591; generation 000003 is 627.
- Fresh relevant regressions: 175/175 PASS, no skips/expected failures;
  V1.18 independent validator PASS; no production/test/Design/Plan change.
- Independent read-only operational review: Critical 0 / Important 0 / Minor 0;
  parent chain, both preflight results and canonical source projection replayed.

No real 2022 candidate database was created. The proposed path is
`data/staging/task12-v122-hkdse-2022/candidate-generation-000004`.
639 is only the post-import projection, not an accepted count.
No `releases/V1.22`, promotion, 2023 ingestion or V1.23 work.
Fresh parent verification is required again before consuming an import approval;
an approval bound to a changed parent must not be reused.

```text
USER APPROVED IMPORT BATCH JOY-M2-HKDSE-2022-PP-MS ae96a9a971fafdd6e900ced6f80ee39d4c1365e166b5d4efa7fbcc47383b1fad V1.22 PARENT 20342ba339ef8200ee6d941683d12698c2504c0872548a26717b2771ee2d1707
```

At this historical checkpoint the import statement was requested, not received.
The exact statement has now been supplied and consumed as recorded above.
It does not authorize promotion.

### Historical checkpoint — HKDSE 2022 transcription approval gate

**USER DECISION REQUIRED — PDF TRANSCRIPTION APPROVAL**

Fresh recovery from the actual ledger, receipt and maintained independent
candidate verifier confirms generation `000003`: accepted batches are 2019,
2020 and 2021, each 12 complete questions; 36 additions and 627 projected
questions. The verifier passed 24/24 checks. The prior current-task text was
stale at generation `000002`; that checkpoint is retained below as history.

- Current candidate / required next parent:
  `20342ba339ef8200ee6d941683d12698c2504c0872548a26717b2771ee2d1707`.
- Candidate path: `data/staging/task12-v122-hkdse-2021/candidate-generation-000003`.
- Receipt: `data/staging/task12-v122-hkdse-2021/REAL_BATCH_IMPORT_RECEIPT.json`.
- Candidate SQLite SHA:
  `f9518ee3f954573ecb01a672756804fa0bb8e156ace3edd324742191f8a24801`.
- Batch being prepared: `JOY-M2-HKDSE-2022-PP-MS`; 12 whole questions / 100 marks.
- Unapproved transcription digest:
  `5fcf6b948c3e36518f66c550cc49039d095cf7af6b85d17ca9042699553abd6a`.
- Proposal/report:
  `data/staging/task10b-hkdse-2022/source-review-000001/transcription-proposal-000001/`.
  `PDF_TRANSCRIPTION_REVIEW.md` includes complete source-bound question/MS text.
- Original staging SHA:
  `5c29ee7c4d0fb8dedb55109df4be98e4b18c3f321ea8b96136775e13f1ddba94`.
- PP `M2_2022-pp.pdf`, 28 pages, SHA:
  `5ada06c06c13790f67c3e70731ca4cdbf053304705da025ae936f04b7a67563a`.
- MS `M2_2022-ms.pdf`, 21 pages, SHA:
  `c42aa39e1db5f4f6d437b41a3954d9b9efc68fb4e425caceb98f336dbe6215df`.
- Two independent visual drafts and raw discrepancies remain archived.
  Final passes are source-reconciled serialization, not raw independent
  auto-agreement. Q6(a)'s printed identity symbol was restored; Q9(c)'s
  official graph remains bound to MS SHA/page 8, without redraw.
- Controlled taxonomy is source-supported; Q4 concerns inflection points
  and Q6 indefinite integration. Difficulty, marks and whole-question
  boundaries are unchanged. Unknown primary types/tags: 0/0.
- Question/MS completeness: 12/12 each. Unresolved review/issues: 0/0.
  Final source review: Critical 0 / Important 0. Status remains PROPOSED,
  VERIFIED records 0; no human approval has been inferred.
- Fresh relevant regressions: 175/175 PASS, no skips/expected failures;
  V1.18 validator PASS. Two output roots have identical proposal bytes.
- Original sources, all V1.18–V1.21 release bytes and existing V1.22
  generations remain unchanged. Formal production remains V1.21/591.

2022 has not been accepted. No 2022 canonical package, authoritative
preflight, real writer call or candidate generation was created.
`releases/V1.22` remains absent; no promotion, 2023 ingestion or V1.23 work.
After exact transcription approval, reverify the current parent and prepare
the parent-bound preflight; import requires a separate exact approval.

```text
USER APPROVED PDF TRANSCRIPTION BATCH JOY-M2-HKDSE-2022-PP-MS 5fcf6b948c3e36518f66c550cc49039d095cf7af6b85d17ca9042699553abd6a
```

### Historical checkpoint — HKDSE 2020 V1.22 generation 000002

**APPROVED REAL BATCH IMPORT — CANDIDATE VERIFIED; NOT FORMALLY PUBLISHED**

The user supplied the exact 2020 import statement below after checkpoint
`bffaa3e4829ba4f46d5989564f8d485968337469`. Fresh two-root preflight matched
that approval and the verified generation 000001 parent before writing.
The existing maintained writer atomically created only the new staging generation:
`data/staging/task12-v122-hkdse-2020/candidate-generation-000002`.

- Accepted batches: 2 — `000001 JOY-M2-HKDSE-2019-PP-MS` and
  `000002 JOY-M2-HKDSE-2020-PP-MS`, each 12 complete questions.
- Accumulated additions: 24; projected V1.22 count: 615.
- Candidate digest / required parent for a later V1.22 batch:
  `877cafa7425b53a08835277c828b346f29112ecbfce82ae861336a2575047cfc`.
- Consumed 2020 preflight:
  `f57e4aea6fa36d3721ca6705214c47316010a2db58ed7a092fe08f2e68d63530`.
- Consumed parent:
  `83c5efa109132c85dca8b96679ac97d4d9a59dd94e0cc76a57c80871a944ff07`.
- Candidate SQLite SHA:
  `0d55cf8224819e5ec432e0deb32e90a1b59759ea6cfca4292872c02ff379633f`.
- Candidate manifest SHA:
  `4d56f5a4bd187ccb091bfca79252c258632f85b701b29f716acb52dcf7b57d52`.
- Independent candidate verifier: 24/24 PASS; 591 preserved formal rows and
  24 candidate rows (`candidate`, `selectable=0`), aggregate order 592–615.
- Receipt: `data/staging/task12-v122-hkdse-2020/REAL_BATCH_IMPORT_RECEIPT.json`.
  The earlier approval report and all source/canonical evidence are unchanged.
- Fresh pre-write gates: 175/175 PASS, no skips/expected failures;
  V1.18 validator PASS. No production/test/Design/Plan change.
- Separate-process candidate read-back: 24/24 PASS; post-write Task9A + Task7
  + historical replay: 51/51 PASS, no skips/expected failures.
- Independent operational/documentation acceptance: Critical 0 / Important 0
  / Minor 0; reviewer separately verified the candidate and receipt.

Formal production remains V1.21/591. Full V1.18/497, V1.19/502, V1.20/543,
V1.21/591 release hashes and generation 000001 bytes are unchanged. This is
candidate accumulation, not formal promotion; `releases/V1.22` is absent.
No later-year ingestion or V1.23 work. Stop at this operational checkpoint;
wait for the user's next selected batch or separate promotion-readiness authority.

### Historical checkpoint — HKDSE 2020 V1.22 import approval gate

**USER DECISION REQUIRED — REAL BATCH IMPORT**

The user supplied the exact 2020 transcription approval recorded below.
At baseline `34b8455e86ef86cfd45ebbc413fb0caf921d33c9`, the maintained approval
API reconstructed its digest and returned 12 VERIFIED carrier records; only
status changed. The stored proposal and all source evidence remain unchanged.

- Batch: `JOY-M2-HKDSE-2020-PP-MS`; 12 complete questions / 100 marks.
- Actual preflight digest:
  `f57e4aea6fa36d3721ca6705214c47316010a2db58ed7a092fe08f2e68d63530`.
- Required verified parent:
  `83c5efa109132c85dca8b96679ac97d4d9a59dd94e0cc76a57c80871a944ff07`.
- Status: READY FOR USER IMPORT APPROVAL; detected/new 12/12;
  duplicate/rejected/ambiguous/adaptations 0/0/0/0; issues 0; approved_count 0.
- Before/projected count: 603/615. Missing answers 0; missing independent
  explanations 12. Official MS remains present; explanations are not fabricated.
- Difficulty D2:3 / D3:5 / D4:2 / D5:2; image files/references 0/0.
- Two byte-identical canonical roots under `data/staging/task12-v122-hkdse-2020/`:
  `canonical-v122-approved-a` and `canonical-v122-approved-b`. Full preflight
  results agree; both use the exact non-genesis parent verification request.
- Report: `data/staging/task12-v122-hkdse-2020/REAL_BATCH_IMPORT_APPROVAL_REPORT.json`.
  It contains exact source/canonical/approval identities, taxonomy summaries,
  parent verification and frozen release proofs.
- Fresh regression: 175/175 PASS (V122 77, Task9A 41, Task10B 50, Task7 7),
  no skips/expected failures; V1.18 validator PASS; parent verifier 24/24 PASS.
- Independent read-only operational/documentation review: Critical 0 / Important 0
  / Minor 0; both reports/digests and the verified parent were reconstructed.

Formal V1.18/497, V1.19/502, V1.20/543 and V1.21/591 are unchanged. Existing
generation 000001 remains 603 questions; 615 is only the projected post-import
count. Proposed `data/staging/task12-v122-hkdse-2020/candidate-generation-000002`
does not exist. No 2020 import approval or writer invocation, formal V1.22
release, promotion or later ingestion. Stop for the exact separate approval:

```text
USER APPROVED IMPORT BATCH JOY-M2-HKDSE-2020-PP-MS f57e4aea6fa36d3721ca6705214c47316010a2db58ed7a092fe08f2e68d63530 V1.22 PARENT 83c5efa109132c85dca8b96679ac97d4d9a59dd94e0cc76a57c80871a944ff07
```

At that checkpoint this import statement was requested, not received. The user
has now supplied it exactly; its execution is recorded above. It does not
authorize promotion.

### Historical checkpoint — HKDSE 2020 transcription proposal

**USER DECISION REQUIRED — PDF TRANSCRIPTION APPROVAL**

The user explicitly selected `JOY-M2-HKDSE-2020-PP-MS` under the existing
Task 10B / V1.22 workflow. Execution started at clean, synchronized
`300d30430d6233f7dd4a6c6c1709810611a844b2` on `task8b/pipeline-migration`.
No new architecture or production/test change was needed.

- Proposal: 12 complete questions / 100 marks; 12 `PROPOSED`, 0 `VERIFIED`.
- Transcription digest:
  `b3c3ddafdfa0df756aa23649c7fb6a9cb8a1819a502c45df8cf2b25e5fe15e74`.
- Proposal/report directory:
  `data/staging/task10b-hkdse-2020/source-remediation-000002/transcription-proposal-000001/`.
  Read `PDF_TRANSCRIPTION_REVIEW.md` and `transcription.json` together.
- Question text / official MS complete: 12/12 each; review_required 0; issues 0;
  unresolved formula/subpart/figure mismatches 0; unknown primary types/tags 0/0.
- Difficulty unchanged: D2:3 / D3:5 / D4:2 / D5:2. No source diagrams occur in
  the selected question/MS spans; matrices and sign tables remain transcribed.
- Original staging and PDFs are unchanged. A new input copy records the absent
  wrapper field `formal_import_performed=false`; official PP/MS establish Q4
  marks 6 (not staging 5) and Q8 marks 8 (not staging 9). Total remains 100.
  Original IDs/order, complete-question boundaries, page mappings and difficulty
  are retained. Original Txx proposals are preserved; controlled taxonomy is
  source-supported and does not change question/MS content.
- Original independent visual drafts and their disagreement diagnostics remain
  preserved. Final source-reconciled text is not claimed to be raw extraction
  agreement. Independent final source review: Critical 0 / Important 0 / Minor 0.
  Two-root final proposal replay is byte-identical.
- Fresh operational gates: V122 77/77, Task9A 41/41, Task10B 50/50, Task7 7/7
  (**175/175 PASS**, zero skips/expected failures); V1.18 validator PASS.
  Existing 2019 candidate independent verification remains 24/24 PASS.

Formal V1.18/497, V1.19/502, V1.20/543 and V1.21/591 retain their complete
release-tree hashes. Existing V1.22 generation 000001 remains 1 accepted batch,
12 additions and 603 projected questions; its required parent for 2020 is
`83c5efa109132c85dca8b96679ac97d4d9a59dd94e0cc76a57c80871a944ff07`.
No 2020 canonical package, authoritative preflight, import approval, candidate
generation or writer call exists. Duplicate/net-new counts are not yet decided.
No `releases/V1.22`, promotion or V1.23 work. The only next action is the exact
human transcription decision below; it does not authorize import or publication:

```text
USER APPROVED PDF TRANSCRIPTION BATCH JOY-M2-HKDSE-2020-PP-MS b3c3ddafdfa0df756aa23649c7fb6a9cb8a1819a502c45df8cf2b25e5fe15e74
```

At that checkpoint this statement was requested, not received; it has since
been supplied exactly by the user. Full source identities, remediation
evidence and human-gate boundaries are recorded in
`docs/reports/V122_CANDIDATE_AUTHORITY_VERIFICATION.md`.

### Completed engineering checkpoint — V1.22 Native / Inline Execution

The approved sequence 1 → 2 → 3 → 4A → 4B1 → 4B2 → 5 was completed
with dependency-valid RED-first evidence. User-authorized scope clarification
`a61bd93` adds only the stale V1.21 public-surface test migration, preserving
the historical 99-name prefix and exact approved 18-name V1.22 suffix.
Canonical-record binding, URI encoding and strict-manifest replay findings
were fixed within the V122 verifier after valid REDs. Final independent
re-review: Critical 0 / Important 0 / Minor 0.

Engineering commit `59140a0207ea4e9b348b7b55e403a2c3b2552052` was ordinarily
pushed to `origin/task8b/pipeline-migration`; local/remote matched with 0/0
ahead/behind and a clean tree at that checkpoint. Final serial maintained:
1082/1082 PASS, zero errors/skips/xfails; V122 focused 77/77; Task9A 41/41;
Task10B 50/50; Task7 7/7; historical replay 3/3; V1.18 validator PASS;
formal V119/V120/V121 verifiers 18/18, 21/21, 21/21 PASS.
Legacy attribution remains known 9 PASS / 2 FAIL, not a maintained blocker.
Historical failed runs and their remediation remain in
`docs/reports/V122_CANDIDATE_AUTHORITY_VERIFICATION.md`.

### Completed operational checkpoint — HKDSE 2019 V1.22 generation 000001

**APPROVED REAL BATCH IMPORT — CANDIDATE VERIFIED; NOT FORMALLY PUBLISHED**

The user supplied the exact requested import statement after checkpoint
`7567f080d5c3db2cfa41fa18371e3d303fae430a`. Fresh two-root preflight reconstruction
matched the approved report and genesis before the maintained writer ran.
No re-transcription, taxonomy change or source mutation occurred:

- Batch: `JOY-M2-HKDSE-2019-PP-MS`; 12 complete questions / 100 marks.
- Transcription digest:
  `3139b39d7c42d17fbc28870d00127dd2792943860ef615a2c950d528f98b6829`.
- Actual preflight SHA-256:
  `674624abcd338b2fa3683b982300a30082e3d0e62f95f97e3e8d25e12d1d0fa5`.
- Required authority parent (no parent artifact for generation 000001):
  `7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7`.
- Approved preflight status: `READY FOR USER IMPORT APPROVAL`; detected/new 12/12;
  duplicate/rejected/ambiguous/adaptations 0/0/0/0; issues 0.
- Before/projected count: 591/603. Missing answers 0; independent explanations
  missing 12. Official MS is preserved; no explanation is fabricated.
- Difficulty D2:4 / D3:4 / D4:2 / D5:2; no taxonomy/source edits.
- Two byte-identical roots:
  `data/staging/task12-v122-hkdse-2019/canonical-v122-approved-a` and
  `canonical-v122-approved-b`. Their preflight results are identical.
- Full identities, taxonomy summaries and frozen proofs:
  `data/staging/task12-v122-hkdse-2019/REAL_BATCH_IMPORT_APPROVAL_REPORT.json`.

The exact human approval received and stored in candidate authority is:

```text
USER APPROVED IMPORT BATCH JOY-M2-HKDSE-2019-PP-MS 674624abcd338b2fa3683b982300a30082e3d0e62f95f97e3e8d25e12d1d0fa5 V1.22 PARENT 7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7
```

The existing writer atomically created the new, immutable staging generation:
`data/staging/task12-v122-hkdse-2019/candidate-generation-000001`.

- Accepted batches: 1 (`000001 — JOY-M2-HKDSE-2019-PP-MS`).
- Accumulated additions: 12; projected V1.22 count: 603.
- Candidate digest / required parent for any later V1.22 batch:
  `83c5efa109132c85dca8b96679ac97d4d9a59dd94e0cc76a57c80871a944ff07`.
  Genesis must not be reused for generation 000002.
- Candidate SQLite SHA-256:
  `7a3b8892063ec3feba36f4cda61d955ffe09d9bf0498056684e3066b46eea4d0`.
- Candidate manifest SHA-256:
  `4feeb629ff0c28a20e10c031f8823217b2d42b673d9a0eb1e771fca833d64147`.
- Independent candidate verification: 24/24 PASS, including a separate-process
  read-back. New records are `candidate`, `selectable=0`, ordered 592–603;
  the copied 591-row formal baseline remains unchanged.
- Import receipt: `data/staging/task12-v122-hkdse-2019/REAL_BATCH_IMPORT_RECEIPT.json`.
  The earlier approval report remains unchanged as pre-approval evidence.
  `rollback.json` is declarative only; no deletion was executed.
- Fresh pre-write regression: V122 77/77, Task9A 41/41, Task10B 50/50,
  Task7 7/7 (175 total), zero skips/expected failures; V1.18 validator PASS.
- Fresh post-write Task9A + Task7 + historical replay: 51/51 PASS,
  zero skips/expected failures; all formal historical verifiers remain PASS.

Formal V1.18/497, V1.19/502, V1.20/543, V1.21/591, canonical packages and
original 2019 source/approval evidence remain byte-identical. Formal production
is still V1.21/591. At that completed checkpoint no `releases/V1.22`, promotion
or 2020 ingestion existed. The user subsequently selected the 2020 batch;
its current operational human gate is recorded above. No promotion
or import approval is inferred from that selection.

### Historical checkpoint — HKDSE 2019 transcription approval and Design

The following records the pre-implementation checkpoint; statements about
unavailable V122 APIs or unstarted canonical/preflight work below are historical,
not current execution authority. The later exact import approval and accepted
candidate checkpoint are recorded above.

`JOY-M2-HKDSE-2019-PP-MS` has received exact human transcription approval;
this is not import approval. The exact source staging, PP and MS were verified;
the batch contains 12 whole questions and 100 marks. The original unresolved
proposal remains unchanged at
`data/staging/task10b-hkdse-2019/transcription-review-proposal/` and its digest is
`b2883e39869b86286d4ce0a8f66e772c261128b815b0869d4c8fb61acd87844d`.
That historical proposal has 11 `PROPOSED`, 1 `REVIEW_REQUIRED`, and 0
`VERIFIED` records; it is not the new approval target.

Q10(d), MS PDF page 9 / printed page 77, has a visibly truncated right-edge
scoring remark. On 2026-09-21 the user explicitly confirmed the exact official
note `保留不給 1M 若遺漏檢驗` as supplemental human source authority, resolving
only that field. This is not automatic recovery from the cropped PDF and does
not approve the batch. The primary MS SHA remains
`076cdf9a43cb41f196450c78bf1ee4be3069ca0e5303c0680fdda9f2fce244e6`.
The supplied page image is preserved byte-identically with SHA
`386a577e6fa64b8ef8effe3a57b7687b4656d318edf2bdc683226cfa45062bab`.

The new proposal is
`data/staging/task10b-hkdse-2019/transcription-human-resolution-000002/proposal/`,
with transcription digest
`3139b39d7c42d17fbc28870d00127dd2792943860ef615a2c950d528f98b6829`.
The immutable proposal has 12 `PROPOSED`, 0 `REVIEW_REQUIRED`, 0 issues, and
0 `VERIFIED` records; approval does not rewrite its stored payload.
Question text and official MS are complete for 12/12; formula, subpart and
figure mismatches are zero. Its sibling `evidence/` directory preserves the
human decision, screenshot identity, old diagnostic and semantic immutability
proof. Both new visual-pass copies carry the same human-authorized note;
this does not claim two independent OCR recoveries. All semantic content
outside this one note and derived review/digest state is unchanged.
Q12's printed MS cross-reference `藉 (b)(ii)` is preserved, not silently
corrected. Original PDFs, staging, complete-question boundaries, official
working, alternative methods, marks, difficulty, and page anchors are retained.
Controlled taxonomy has 12 primary types, zero unknown primary types and zero
unknown tags. Difficulty remains D2:4 / D3:4 / D4:2 / D5:2.

The user subsequently supplied exactly:
`USER APPROVED PDF TRANSCRIPTION BATCH JOY-M2-HKDSE-2019-PP-MS 3139b39d7c42d17fbc28870d00127dd2792943860ef615a2c950d528f98b6829`.
The maintained `approve_hkdse_pdf_transcription()` API accepted this approval
after semantic digest reconstruction, producing 12 `VERIFIED` carrier records.
Only the carrier status changes; all record content, ordering, and source
identities remain unchanged. The sibling `approval/` directory contains
`approval.json` and `approval_verification.json`; verified-record payload SHA is
`81a5e564f6eb1c0a4edb2d8a461f94aa89f3e6bd0abebdc0cf4f660f34192733`.
No historical proposal or evidence file was overwritten.

The embedded extraction evidence is retained alongside the visually reviewed
proposal. Source pages were independently read in two groups; Q7–12 also had
an independent draft comparison, while the main agent completed Q1–6's draft
comparison in a second source-page reading. This checkpoint does not claim a
full independent-review PASS or real import approval. The original proposal's
two-root determinism evidence remains preserved. Fresh approval-checkpoint
regressions pass Task 10B 50/50, Task 9A 41/41, Task 7 7/7 and the V1.18
validator, with no skipped or expected-failure tests. Formal V1.21's earlier
21/21 verifier result remains historical; this patch freshly checks unchanged
formal release bytes and exact SQLite counts, not a new promotion operation.

No 2019 canonical package, authoritative preflight, candidate database, import,
or promotion was created/run. No production/test change was made. Formal
V1.18/497, V1.19/502, V1.20/543 and V1.21/591 remain byte-identical.
Read-only inspection confirms that the current versioned bridge/preflight
contract binds formal V1.20/543 to target V1.21; no V1.22 runtime contract or API
exists.
It must not be repurposed to claim a V1.21/591-based preflight. The user's
minimum append-only next-version roll-forward authorization now applies.
The user confirmed the minimal design direction. Its written specification is
`docs/superpowers/specs/2026-09-21-v122-next-version-candidate-design.md`, status
`APPROVED — FIRST-GENERATION GENESIS PARENT BINDING CLARIFIED`. It fixes formal
V1.21/591 as the baseline and V1.22 as the target, preserves every historical
interface, and defines independent genesis
`7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7`.
The written Design review had no Critical finding and one required clarification,
now closed: generation 000001 may lack a parent artifact, never parent digest
authority. Its preflight/approval must bind the exact genesis above; writer and
verifier independently reconstruct it. Generation 000002+ requires the verified
previous V1.22 digest. The docs-only clarification is committed at
`f51aaceaf08359747983a4dbccdb3b5ad0ee9cea`; the Design is approved without another
Design approval checkpoint. Its RED-first Plan is written at
`docs/superpowers/plans/2026-09-21-v122-next-version-candidate.md`.
The Plan keeps the exact 20-path scope and sequences public models/scaffolds,
canonical bridge, genesis preflight, coupled parent/writer/verifier tests,
historical gates and independent implementation review, then real read-only
preflight. Self-review and independent Plan review are complete: Critical 0 /
Important 0 / Minor 0. The sole sequencing finding was closed by separate
first-generation writer/verifier, parent-preflight and multi-batch writer/verifier
RED/GREEN gates (4A → 4B1 → 4B2). This docs-only checkpoint records the Plan;
human Plan review/execution handoff still precedes implementation.
No V1.22 production code, tests, canonical package, preflight, or candidate
database has been created.

Fresh docs-checkpoint verification: Task 9A 41/41, Task 10B 50/50, Task 7 7/7
and the V1.18 validator PASS. The maintained command collects 1005 existing
tests; collection is not a fresh full-suite PASS. The 20 Design/Plan scope paths
match exactly, canonical genesis recomputes to the frozen digest, and unrelated
Design sections remain unchanged. Formal release bytes/counts, production/test
hashes, and all 28 recorded original/proposal evidence hashes are unchanged.
The transcription approval above remains valid and must not be requested again
merely because the versioned engineering contract is pending. No import or
promotion approval is implied by design confirmation.

### Completed formal V1.21 checkpoint

V1.21 formal promotion is `CLOSED / PASS`. The approved Design/Plan and
implementation are committed at `6eb48ce`, `e7cdf4d`, `45dbb19`, `5f690ee`,
and review remediation `3eef866`. Independent review is Critical 0 / Important
0. The exact generation `000004` contains the four approved 2015–2018 batches,
12 questions each, with candidate digest
`ecf624e3cb9fd8e7b1e0c664ddc5d51ef67f2d7f16f277c276be828eba32282c`,
candidate SQLite SHA-256
`6e27e5b5eff5a701b4671a3e12ee538eed985147d86c23edef1e9489f714a53c`,
and candidate manifest SHA-256
`dc82e04639a4b54e24bbf7eceeb4ecec8a3751dfa7e8595f260b9d894d91fc83`.
It binds immutable formal V1.20/543 plus 48 exact promoted records to 591.

Two independent non-formal dry-runs pass 21/21 checks and are byte-identical.
They bind release digest
`f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3`,
formal SQLite SHA-256
`93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a`,
and semantic SHA-256
`0a4e70acb1cc657207dd0fefb1e20581d34baadda804219ae2fbbfb2b5ca817f`.
The exact final approval was received:
`USER APPROVED RELEASE PROMOTION V1.21 f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3`.
Its authorized publication already created `releases/V1.21/`; this lifecycle
closure did not rebuild, republish, roll back, or alter those bytes. Formal
V1.21 independently verifies 21/21 and matches both approved dry-runs exactly.
The isolated formal release commit is
`879ca8dee9b7e58fa4b24f9c7e82b15aeb63107b`.

The stale pre-promotion absence assertion was migrated to exact post-promotion
identity plus unchanged historical replay in
`tests/regression/test_v121_historical_replay.py`, committed at
`2c50f48cab94d444d0906b80ac0d86b0a054c953`. All V1.20 protections remain;
isolated before/after replay preserves V1.20/V1.21 candidate, preflight, and
approval authority. The migrated regression is 3/3 PASS; independent lifecycle
review is Critical 0 / Important 0 / Minor 0. The V1.21 promotion focused suite
is 26/26 PASS and the complete maintained suite is 1005/1005 PASS with zero
failures, errors, skips, or expected failures on the final serial run. Formal
V1.18/V1.19/V1.20, all four V1.21 candidate generations/packages, the approved
dry-runs, and the existing formal V1.21 files retain their exact bytes.
No production code changed. Unresolved closure blockers: `NONE`.
The original pre-promotion evidence remains historical and auditable in
sections 1–8 of `docs/reports/V121_PROMOTION_READINESS_VERIFICATION.md`;
section 9 records the post-promotion closure and fresh gate results.

Task 10C V1.20 formal promotion is `CLOSED / PASS`. The approved Design/Plan
authority is committed at `59f9f52443405b7e467da8c69855bc45d3dd8223`;
the independently reviewed implementation is committed at
`06bd83768a6619d69a9394ed1b9bf16564c15759`. Final independent review is
Critical 0 / Important 0 / Minor 0. Two non-formal dry-runs independently pass
21/21 checks and are byte-identical. They bind release digest
`1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf`,
formal SQLite SHA-256
`b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292`,
and semantic SHA-256
`e3f3d2b09fa7869ee266d3afb01e6160406764c96127adfaf236a8deee8700ba`.
The exact final approval was received and consumed once by the public
publication API. The isolated formal release commit is
`e8bae856a6f3ad71374b71cc20ac125bae5d621c`. Formal `releases/V1.20/`
independently verifies 21/21 with 543 published/selectable questions. No
current-release pointer/index exists or changed. The subsequently authorized
V1.21 formal publication leaves V1.20 unchanged as historical authority.

Task 10B HKDSE PDF / PP-MS source adapter engineering implementation is
`COMPLETED / PASS`. Its approved source-specific Design and RED-first Plan are
`docs/superpowers/specs/2026-09-14-task10b-hkdse-pdf-adapter-design.md` and
`docs/superpowers/plans/2026-09-14-task10b-hkdse-pdf-adapter.md`. The final
implementation commit is `fb473648a4abfc4e0f6071e2d4a34d44c243d6f9` and
independent re-review is Critical 0 / Important 0. The adapter binds exact
staging, PP, and MS identities; retains two extraction passes and deterministic
review evidence; requires exact human transcription approval; and only then
may construct the existing Task 10A canonical package. Task 10B focused tests
are 50/50 PASS. The 2012, 2013, and 2014 PP/MS batches have since completed
their exact transcription/taxonomy approval gates and are bound into the
current non-formal V1.20 generation-000003 candidate. Task 10B granted no
formal publication authority and modified neither V1.18 nor V1.19.

Task 10A V1.20 multi-batch candidate authority is `CLOSED / PASS`. The approved
Design is
`docs/superpowers/specs/2026-09-13-task10a-v120-multi-batch-candidate-design.md`
and the RED-first Plan is
`docs/superpowers/plans/2026-09-13-task10a-v120-multi-batch-candidate.md`.
Gate A authority is committed at `76b61016928dc865ee895a0963a399aaa959789e`;
the maintained public-surface migration at
`7eabedfa0096272e4c9ec60a470a9231c848a4f0`; and the independently reviewed
implementation at `c2668332e4c912d19e149361ca143637899422c7`
(`feat: add V1.20 multi-batch candidate authority`). Final implementation
review is Critical 0 / Important 0 / Minor 0. The versioned implementation is
append-only over immutable formal V1.19/502, binds every batch to an
independently verified parent candidate digest and exact approval, and keeps
formal V1.20 promotion out of scope. The current generation `000003` contains
the exact approved 2012/2013/2014 batches with additions 14/14/13, candidate
digest `88cc945b6296652c88041e8e51a5c586300c2201a9f48e21abde80d97da3a7b3`,
SQLite SHA-256
`d8ff5bf9e38f27e23e72c39ae41cb297b4223fde5d2bc149178a7033fe9769d1`,
manifest SHA-256
`673a598b7d5b59394ebaf1307943f90a293c165ecc7aa349c23c2947397f5052`,
and projected count 543. Its independent verifier is 24/24 PASS. Task 10C has
since promoted that exact candidate without rewriting it.

Task 9D formal V1.19 promotion is `CLOSED / PASS`. Its independently reviewed
Design is committed at
`4f9924a712d02feb889cbd24e5c3867a9daba31c`; the implementation Plan at
`d1057affd79e7fd81119cd62bdc08d0982958cd3`; public-surface scope alignment at
`7af421fdce7a722da6f43aec7d3cd6656d7675b9`; and the verified implementation at
`b5a47f4a231b2374ae6db0931a6754a52d11296e` (`feat: add verified V1.19
promotion pipeline`). Post-Gate-D lifecycle and symlink-root safety remediation
is committed at `d1954a96e5783a9bfb4d28b4b86b77bbac8c50fd`; the isolated
four-file formal release commit is
`e8b55147d6e0fcaa6e1e842393534adcfda96680`. Final independent review is
Critical 0 / Important 0 / Minor 0.
Task 9D focused tests are 48/48 PASS and the complete maintained suite is
711/711 PASS with zero skips or expected failures. Two independent
non-formal real-candidate dry-runs are byte-identical, independently verify
18/18 checks, and bind release digest
`7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d`.
The exact Human Gate D statement was received and consumed once by the public
publication API. Formal `releases/V1.19/` independently verifies 18/18 and is
byte-identical to the approved dry-run. No current-release pointer/index exists
or changed. Task 10A adds only a non-formal V1.20 candidate lifecycle; it does
not alter or supersede this formal V1.19 authority.

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
integration suite is 41/41 PASS with 0 failures, errors, or skips. Task 9A
itself remains read-only. Its post-Gate-B lifecycle test preserves any
pre-existing formal V1.19 state by immutable before/after fingerprint while
continuing to require exact V1.18 immutability.

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
- At the historical Task 9D checkpoint, V1.19 became the formal release.
  V1.18, compatibility objects, `legacy/`,
  and all pre-existing formal data remain unchanged. The approved synthetic
  candidate, verified real Task 9C candidate, and Task 9D dry-run roots remain
  non-formal staging evidence; only `releases/V1.19/` became new formal
  authority at that checkpoint. Current formal authority is V1.21 as above.
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
- Task 9 recovered scope began with batch-import manifest and read-only preflight;
  that Task 9A checkpoint authorized no writes or promotion. Subsequent Human
  Gates separately authorized the Task 9C candidate and Task 9D formal release.
  CLI, App/API, worksheet generation, and any next data change remain
  unauthorized.
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
  authorized the current 5-question real candidate; Task 9D has now promoted
  that exact candidate without rewriting it.
- Task 9D: `CLOSED / PASS`; deterministic builder, independent verifier,
  rollback receipt, atomic publication gate, real dual dry-run, Gate D
  authorization, formal publication, maintained regressions, and independent
  implementation review are complete.
- Task 10A: `CLOSED / PASS`. Its approved append-only V1.20 public models,
  target projection, effective-state preflight, parent-bound approval,
  deterministic full-prefix candidate writer, and independent 24-check
  verifier are implemented at
  `c2668332e4c912d19e149361ca143637899422c7`. The historical V1.19 API remains
  the exact ordered public prefix; only the approved V1.20 suffix was added.
  Subsequent approved operational runs accumulated the 2012–2014 batches, and
  Task 10C promoted their exact generation without rewriting Task 10A
  authority.
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
- At the historical Task 9D checkpoint, formal V1.19 contained 502 questions.
  Human Gate C authorized exactly
  the five-question real candidate and the exact Human Gate D statement
  authorized its formal promotion. The frozen V1.18 baseline remains unchanged
  at 497 questions.
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
  candidate only after Gate C; Task 9D performed the first digest-bound formal
  V1.19 publication only after Gate D.
- Safety branch `backup/task-7.1-ceb179e-20260808` remains retained.

## Completion gate

- Current explicit maintained suite, excluding the separately attributed legacy
  behavior module: 1005/1005 passed; failures=0, errors=0, skip=0, and
  expectedFailure=0.
- V1.21 promotion focused suite: 26/26 passed; the exact generation
  `000004` candidate verifies 24/24 and both real dry-runs verify 21/21. Final
  independent implementation review: Critical 0 / Important 0. Formal
  `releases/V1.21/` independently verifies 21/21 with 591 questions and the
  exact approved identity. Post-promotion lifecycle regression: 3/3 PASS;
  independent migration review: Critical 0 / Important 0 / Minor 0.
- V1.21 candidate authority focused suite: 44/44 passed.
- Task 10C focused promotion suite: 30/30 passed; two real dry-runs and formal
  `releases/V1.20/` each independently verify 21/21 and are byte-identical.
  Final independent review: Critical 0 / Important 0 / Minor 0.
- Task 10B focused implementation suite: 50/50 passed; final independent
  implementation review: Critical 0 / Important 0.
- Task 10A focused implementation suite: 144/144 passed; final independent
  implementation review: Critical 0 / Important 0 / Minor 0.
- Formal V1.19 independent verifier: 18/18 PASS. V1.20 candidate generation
  `000003` independently verifies 24/24; formal V1.20 independently verifies
  21/21 and is the exact 543-question authority.
- Task 9D focused promotion suite: 48/48 passed; final independent review:
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
- The historical Task 9B parser-mode golden-equivalence preflight reached
  `READY FOR USER IMPORT APPROVAL` with
  17 candidates, 0 issues, and path-independent preflight SHA-256
  `49ab71e26cf2256581ecb5ada14b0eefc601317169ee897599aeb9a39976187b`.
  Its exact approval was used only to build the approved synthetic Task 9C
  staging candidate. It must not be reused as approval for a real Task 9D user
  batch; that synthetic approval produced no formal import.
- Task 9B verification record: `docs/reports/TASK9B_VERIFICATION.md`.
- Task 10A verification record: `docs/reports/TASK10A_VERIFICATION.md`.
- Task 10B verification record: `docs/reports/TASK10B_VERIFICATION.md`.
- Task 10C verification record: `docs/reports/TASK10C_VERIFICATION.md`.
- V1.21 promotion readiness record:
  `docs/reports/V121_PROMOTION_READINESS_VERIFICATION.md`.

## Historical next-task handoff — V1.22 preparation (superseded)

The following retained handoff is historical, not current execution authority.
Current authority is the V1.23 section above and its approved Plan.

Task 9A, Task 9B, Task 9C, Task 9D, Task 10A, Task 10B, and Task 10C are closed.
Formal V1.21 promotion is `CLOSED / PASS` at 591 complete questions. Formal
V1.20/543, V1.19/502, and frozen V1.18/497 remain unchanged. The approved
four-batch V1.21 generation `000004` remains immutable staging evidence.
No current-release pointer/index exists or was added.

2019 real-source ingestion is in progress using V1.21/591 as the immutable
formal baseline. Q10(d) source recovery and exact transcription approval are
complete. The written V1.22 Design is approved with its sole required genesis
parent clarification committed. The implementation Plan has been written and
technically reviewed with zero Critical/Important findings, and is recorded in
this docs-only checkpoint. Human Plan review/execution handoff is next; no task
in it has started. No new Design approval is required unless a genuine new
authority conflict appears.
Keep the approved transcription unchanged, preserve historical APIs and formal
releases, and stop at exact real-batch import approval after a valid preflight.
No 2019 import approval, candidate write, speculative architecture, or automatic
promotion is authorized.
