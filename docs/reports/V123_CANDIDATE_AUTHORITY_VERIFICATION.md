# V1.23 candidate authority — implementation evidence

Status: IMPLEMENTATION VERIFIED; REAL 2023 PREFLIGHT READY; EXACT IMPORT APPROVAL PENDING.
Approved Design/Plan base: c7d54371bc809c204799f94ab6908bd6bd9641eb.
Human Native / Inline execution approval received 2026-10-10. No real import approval.

## Task 1 — models / API scaffolds / strict loader

- Module existence RED: 1 collected, 1 assertion FAIL, 0 ERROR, exit 1.
- Model-contract existence RED: 15 collected, 1 PASS / 14 assertion FAIL, 0 ERROR, exit 1; exact model GREEN 15/15. These assertions establish missing public contracts, not preflight/writer behavior.
- API RED: 3 collected, exact suffix and five function assertions fail (6 subtest failures), 0 ERROR, exit 1; models/API GREEN 17/17.
- Six historical export suites: 55 collected, six exact-surface failures before the approved expectation migration. All old exports/order retained; only the exact 18-name suffix appended (old promotion tail remains checked).
- Loader behavior RED: 16 collected, 28 assertion/subtest FAIL, 0 ERROR, exit 1. Only operation-under-test NotImplementedError is converted to assertion failure. Valid fixture setup precedes the operation.
- Loader GREEN and additional nested-carrier/tuple isolation preservation checks: 35 new tests; combined six historical modules 90/90, no skip/expectedFailure. UTF-8/JSON/nonfinite/duplicate keys, wrong target/schema/types/order, unsafe paths, inventory and hash/size controls included.
- Scoped inline review: compared all 13 field/type envelopes, fixed V1.22/639 baseline and V1.23 namespace/genesis, five API annotations, exact export suffix and six historical test diffs. Preflight/bridge/writer/verifier remain NotImplementedError; profile module is docstring-only. No later behavior ported.
- User AGENTS SHA remains `75ffa9680b18a0875fde8d36a8ca3e0ebda0603f10e8dc788e71ea8353d0311d`; excluded from every task commit.

## Task 2 — approved-transcription canonical bridge

- Effective RED: 11 collected, 1 API PASS, 14 assertion/subtest FAIL, 0 ERROR, exit 1. A preliminary forged-record fixture used the validating constructor and was corrected before recording behavioral RED; that setup error is not RED evidence.
- GREEN: 11 bridge + 35 model/loader + 50 existing Task10B = 96/96 PASS, no skips/expected failures.
- Independent files in two roots are byte-identical. Four non-manifest files exactly match V122 for the same synthetic verified carrier; only manifest target/schema changes. Two duplicate-looking synthetic source records are both retained, including MS, subparts, marks, taxonomy, difficulty and PDF region references. No canonical image assets are invented.
- Forged proposal/record/approval, nonverified input, symlink/path escape/source overlap, existing destination and atomic publication failure are independently exercised. Failure leaves no new output/owned temporary tree.
- Scoped inline review: only the V123 bridge/imports implement behavior; neutral projection and safety helpers are reused, all historical bridge bodies remain unchanged. Real 2023 source/approval not consumed yet.

## Task 3 — genesis preflight

- RED: 23 collected, 27 assertion/subtest failures, 0 errors, exit 1. Strict package-load smoke passes before calling the scaffold. Two preservation/API tests are already GREEN; no setup errors count as RED.
- GREEN: 23/23 focused; Tasks1–3 69/69, no skips/expected failures. Effective state 639/empty ledger/fixed reconstructed genesis, one synthetic net-new projects640; not a prediction for real2023.
- Tests cover all four 2019–2022 inherited layers and historical image reference identity, complete639 indexing, frozen counts, malformed/invalid candidate issues, taxonomy, exact duplicates despite fuller MS, truthful second-source hash collisions, adaptations and candidate-ID exclusion, ambiguity, mixed duplicate batch blocking, package blocker vs per-record counts, and untrusted file omission.
- Copied-baseline negative controls reach metadata version/schema, view/count/unique-ID/published/selectable checks independently of outer file hashes. Escaped-space/#/Unicode URI baseline copies are read-only. No formal file changes.
- Scoped review: no candidate DDL/writer or verified-parent branch implemented. Genesis helper reconstructs the literal approved projection using neutral canonical-JSON/hash helpers. The copied formal reader explicitly checks published/selectable state and query-only immutable URI under the approved V123 contract; historical readers are unchanged.
- Protected snapshot: 292/292 files unchanged; user AGENTS SHA unchanged; releases/V1.23 absent.

## Task 4A — first-generation writer / verifier

- Effective RED: 23 collected, 27 assertion/subtest failures, 0 errors, exit 1, at writer/verifier scaffolds. Earlier private-API setup errors were excluded. GREEN: 23/23 focused, 93/93 cumulative including public API; no skips/expected failures.
- Fixed DDL adds only task13 tables/view and private user_version123. First synthetic batch yields640; all inherited schema SQL, tables/views/metadata and image fields remain exact. New rows remain candidate/selectable0.
- Writer and verifier independently reconstruct genesis and bind report/approval. All24 checks, malformed-context exceptions vs parsed corruption FAIL, canonical reconstruction, closure, FK/schema/count/image/rollback tampering, no-replace/fault cleanup and two-root ALL-byte determinism are exercised.
- Scoped inline review: first-generation only. Single-batch projection and SQLite insertion; no prefix replay reconstruction. Multi-batch writer explicitly remains unimplemented and parent preflight remains a scaffold. Pure hash/JSON/path/SQL/image helpers reuse their version-neutral implementations.
- GREEN development corrected a wrong helper import and fixed expected_user_version123 in the verifier contract; these implementation errors were not new RED evidence. A test prerequisite used the same output twice and now uses a separate control directory without relaxing assertions.

## Task 4B1 — verified-parent preflight

- RED: 9/9 failures, 0 errors, exit1, exclusively at parent-preflight scaffold after first-generation build and independent PASS. GREEN: 9 focused; candidate + genesis-preflight suites56/56 PASS, no skips/expected failures.
- Exact parent digest/ledger/count640→641, accepted-parent duplicate and ID collision, retained2022 formal IDs, taxonomy union, missing closure/wrong-version/genesis-reset/stale-request refusal, concurrent parent-change rejection and equivalent-root digest equality are covered. Parent bytes remain unchanged.
- A synthetic taxonomy test initially used B's different tag after intentionally removing formal vocabulary; its input now uses A's actual accepted taxonomy to isolate parent-derived vocabulary. No taxonomy contract or assertion was weakened.
- Scoped review: only parent-preflight and tests changed; first-generation writer remains limited to one batch. All639 baseline rows plus verified parent rows form indexes; independent verification runs before and after parent reads.

## Task 4B2 — ordered multi-batch writer / verifier

- RED: 8 collected, 9 assertion/subtest failures, 0 errors, exit1; every second-batch operation follows verified A and READY B bound to A. The already-safe nonmatching-generation verifier refusal passed before prefix support. Added URI hardening test independently failed on missing immutable flag, not an input/setup error.
- GREEN: 9 focused / 111 cumulative V123 tests PASS, zero skips/expected failures. Full(A,B) gives641, third preflight642 and detects collisions against BOTH A and B. No real-data count is predicted.
- Full prefix replay, stale B/C approvals, old target, null/empty/genesis reset, duplicate/truncated/reordered/substituted batches, forged counts/candidates, changed canonical bytes, no-replace, failed-publication preservation, two-root byte equality and all read-only connections are covered.
- Scope review: only after 4B1 GREEN are full-prefix reconstruction and multi-batch database insertion enabled. All readonly SQLite connections in V123 use escaped absolute URI, mode=ro&immutable=1 and query_only=ON. The parent-preflight hardening is an owning-task in-scope correction under Plan Global Constraints, not historical reader changes.
- Protected baseline/source/candidate snapshot292/292 unchanged; AGENTS hash unchanged; releases/V1.23 absent.

## Task 5 — historical regression and independent review

- Added five read-only historical acceptance tests: formal V1.18–V1.22 hashes/
  counts, complete639 inheritance, past candidate replay and formal verification,
  approved2023 source/receipt preservation, exact API boundary and isolated
  formal-output rejection. No historical candidate is rebuilt.
- An initial full run overlapped a focused run and failed one historical
  staging-tree snapshot tearDown: `test_all_inherited_baseline_and_candidate_relations_are_preserved`.
  The difference consisted of concurrent synthetic V123 test directories.
  No assertion was weakened or maintained module excluded. Single-process
  recovery: 1233/1233 PASS in446.250s, FAIL0/ERROR0/skip0/expectedFailure0.
- Independent reviewer `v123_implementation_review` initially found C0/I1/M0:
  new output could be nested under historical candidate/canonical artifact
  roots, invalidating their inventory closure without overwriting any file.
  A zero-write diagnostic on the actual historical V122 root confirmed the
  ancestor guard missed it; no real output was attempted.
- Three public-API regression tests then produced genuine RED:
  3 collected / 10 subtest assertion failures / 0 errors, exit1.
  Writer and bridge unexpectedly accepted both fixed markers (ordinary file
  and dangling symlink); verifier unexpectedly returned PASS for valid
  synthetic candidates copied under either marker.
- Minimal fix only in V123 writer, independent verifier and new bridge:
  reject ancestors containing `candidate_manifest.json` or
  `import_manifest.json`, even malformed/dangling markers, before output.
  No historical database/schema parsing or shared historical-function changes.
  Focused GREEN3/3; parent content/marker identity and noncreation are checked.
- Independent incremental re-review: **Critical0 / Important0 / Minor0**.
  Original I1 closed; 51 historical adapter definitions remain AST-identical.
  Reviewer did not run tests concurrently, did not judge future Task6 runtime
  outputs and did not add malicious external directory-replacement race/lock
  guarantees.
- Final serial maintained gate: **1236 collected/run, 1236 PASS**, 454.581s,
  FAIL0/ERROR0/skip0/expectedFailure0. It includes the I1 fix and its new tests.
  Separate fresh gates: Task9A41/41, Task10B50/50, Task7 7/7, V123119/119
  (including historical replay5/5), all zero errors/skips/expected failures.
  V1.18 independent validator PASS497, integrity ok, FK errors0, hash errors0.
  Historical formal verifiers PASS18/21/21/21 checks for V119/V120/V121/V122.
- All23 approved paths accounted for; diff check PASS; protected snapshot
  292/292 unchanged. User AGENTS hash remains unchanged and excluded.
  Legacy attribution was not rerun: its known9PASS/2FAIL surface (SQLite
  deterministic hash / frozen byte equivalence) is not a maintained PASS claim.
  No actual V1.16 ZIP was searched, read or hashed.

## Task 6 — actual approved 2023 canonical / read-only preflight

- Task5 engineering checkpoint `ae9ad0a7f47b771007194f07d7a14d5cb3a2f283`
  was ordinarily pushed; local/upstream0/0 before Task6. Post-commit historical/
  fix verification8/8 PASS. No force/merge/rebase/amend/PR.
- Reused exact received transcription approval for
  `JOY-M2-HKDSE-2023-PP-MS` /
  `3a3a223a23f694083469281c64be5c5402152c557e3bc36654d400ce5143d618`.
  Proposal fileSHA `4c9df20019c54876f01e9c0a58352fceb07ed78d9d14246e3bd8288fcab6f700`.
  Original PROPOSED bytes remain unchanged; existing approval API reconstructs
  12 VERIFIED records / 100marks. No repeated OCR, patch or transcription gate.
- Actual V123 state had no candidate database or receipt; parent artifact=None,
  authority parent=`ea3b7db78210e045761784a2e415387c1b17f13b5aedde484ca2ae248a45eec7`.
- NEW ignored operation root:
  `data/staging/task13-v123-hkdse-2023/preflight-20261012-000001/`.
  `canonical-a/` and `canonical-b/` are byte-identical across all5files.
  Question/MS/subpart/taxonomy/difficulty/source-map projections equal the
  approved proposal. Both preflight candidate tuples/issues/reports/digests
  are identical; an additional read-only replay matches saved output.
- **READY FOR USER IMPORT APPROVAL**. Actual preflight SHA:
  `64b61671f337dafddd5d316ca0e9ba837e24948fe91256c5df7d1c1b779059a4`.
  Before639; detected12; new_candidate12; duplicate0; rejected0; ambiguous0;
  adaptations0; issues0; approved0; projected651. Real additions so far0.
  Missing answers0, missing independent explanations12, incomplete enrichment12.
  Unknown primary_type0/tag0; L2:4/L3:4/L4:2/L5:2.
- All12 originals already have formal `2023-Q1`–`2023-Q12`.
  Proposed `HKDSE-2023-M2-Q01`–`Q12` are known-original extra-source/content
  evidence records, NOT12 newly discovered originals. No old row is replaced
  or relabelled, and no fingerprint/collision behavior was bypassed.
- Q6 preserves2approved PP SHA/page8/figure-region references only.
  `image_files=()`; no canonical image assets were manufactured. Empty
  missing_images reflects declared inventory only, not standalone figure
  completeness. Source PDF remains necessary. Q7/Q10 approved bytes preserved.
- Manifest projectionSHA:
  `2aafa67c591dd1ca9976530e5cdead3d6b0021c244c0d8875b3826de1150b3ea`.
  Physical manifest fileSHA:
  `a4581692e8bcb356d0d22b390b132546818c576a30dcef8ac18614765de65dca`.
  Exact source/canonical file hashes, per-ID source reconciliation, taxonomy,
  counts and issues are saved in `PREFLIGHT_SUMMARY.json` and
  `PREFLIGHT_RESULT.json`; human report is
  `REAL_BATCH_IMPORT_APPROVAL_REPORT.md` within the operation root.
- Source-review directory and all292 protected hashes unchanged; AGENTS unchanged
  and uncommitted. Formal V122 remains639; no real V123 candidate/approval object,
  writer call, release, next-year ingestion or promotion.
- Independent Task6 evidence check by `v123_implementation_review`: C0/I0/M0.
  Read-only JSON/hash/SQLite checks confirm six source identities, exact receipt,
  two-root5-file equality, 12records/100marks, exact genesis, actual report counts,
  known-original disclosure and Q6 image limitation. No reviewer rebuild or writer.

## Execution rulings

- Final independent review and any remediation re-review follow the approved Plan (stronger than the inline skill's no-re-review default); cost: additional review time only.
- The skill's self-ignored per-plan workspace holds disposable logs/ledger under Design section 10's scratch allowance, not an extra maintained entry point.
- Staging-sensitive gates run serially; independent review is static/zero-write
  while they run. Cost: longer runtime; historical protections stay intact.
- External hostile directory-replacement races do not introduce an unapproved
  lock/registry framework. Existing symlink/no-replace protections remain;
  external TOCTOU risk is not claimed newly eliminated by this bounded fix.

## Remaining gates

Only the new exact real-import human decision remains. The approval request
(not a received approval) is:

```text
USER APPROVED IMPORT BATCH JOY-M2-HKDSE-2023-PP-MS 64b61671f337dafddd5d316ca0e9ba837e24948fe91256c5df7d1c1b779059a4 V1.23 PARENT ea3b7db78210e045761784a2e415387c1b17f13b5aedde484ca2ae248a45eec7
```

Reverify parent before any future real write; a changed parent requires new
preflight and approval. No V1.23 formal release or next-year ingestion is authorized.
