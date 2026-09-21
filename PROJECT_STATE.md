# Joy M2 AI Database — Project State

Updated: 2026-09-21 (Asia/Shanghai)

## Formal data

- Current formal release: V1.21
- Formal SQLite: `releases/V1.21/Joy_M2_Complete_Question_DB_V1_21.sqlite3`
- Formal SQLite SHA-256: `93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a`
- Complete-question records: 591 (543 immutable V1.20 records + 48 approved
  2015–2018 HKDSE PP/MS additions)
- V1.17 retained records: 45
- Task 6 migrated records: 452
- Answer identity: 486 `source_provided`, 71 `ai_solved_verified`, 34 `missing_from_source`
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

## Current task

### Active operational checkpoint — HKDSE 2019 transcription approved

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
previous V1.22 digest. After the docs-only clarification commit, the Design is
approved and the next action is Plan writing/review/commit, without another
Design approval. No V1.22 Plan, production code, tests, canonical package,
preflight, or candidate database has been created.
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

## Next task

Task 9A, Task 9B, Task 9C, Task 9D, Task 10A, Task 10B, and Task 10C are closed.
Formal V1.21 promotion is `CLOSED / PASS` at 591 complete questions. Formal
V1.20/543, V1.19/502, and frozen V1.18/497 remain unchanged. The approved
four-batch V1.21 generation `000004` remains immutable staging evidence.
No current-release pointer/index exists or was added.

2019 real-source ingestion is in progress using V1.21/591 as the immutable
formal baseline. Q10(d) source recovery and exact transcription approval are
complete. The written V1.22 Design is approved with its sole required genesis
parent clarification closed. Commit that clarification, then write, review and
commit its implementation Plan before any RED-first implementation. No new
Design approval is required unless a genuine new authority conflict appears.
Keep the approved transcription unchanged, preserve historical APIs and formal
releases, and stop at exact real-batch import approval after a valid preflight.
No 2019 import approval, candidate write, speculative architecture, or automatic
promotion is authorized.
