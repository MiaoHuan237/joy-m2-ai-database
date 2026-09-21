# Execution ledger — plan: docs/superpowers/plans/2026-09-21-v122-next-version-candidate.md

## Authority and boundaries

Design clarification: f51aaceaf08359747983a4dbccdb3b5ad0ee9cea.
Plan: 2e67696bd6ab12a6716360f4b868af7fbad160c1; user approved Native / Inline Execution.
Docs remote checkpoint verified at 2e67696bd6ab12a6716360f4b868af7fbad160c1.
During the implementation and pre-approval checkpoints, no real V1.22 writer was
authorized. The subsequent exact 2019 import approval and candidate write are
recorded in the final section below. Formal release, 2020 ingestion and formal
baseline mutation remain unauthorized.

Ruling: Keep the inline execution ledger in this approved report and scratch evidence
under tmp/pdfs/task12-v122-hkdse-2019 instead of the skill's default scratch directory.
The Design's closed file scope takes precedence; cost if wrong is record relocation only.

## Interface pre-flight

| Producer → consumer | Shared contract | Resolution |
|---|---|---|
| Task 1 → 2 / 3 / 4 | 13 carriers, strict loader, five safe API scaffolds | Exact frozen V122 counterparts; scaffolds do not claim behavior |
| Task 2 → 6 | Verified transcription → five-file package | Four non-manifest payloads unchanged |
| Task 3 → 4A | Genesis preflight + synthetic approval | Parent artifact absent, authority digest mandatory |
| Task 4A → 4B1 | Verified first generation | Parent-dependent RED prohibited until first-generation GREEN |
| Task 4B1 → 4B2 | Valid second-batch preflight / approval | Multi-batch RED prohibited until parent-preflight GREEN |
| Task 4 → 5 → 6 | Independent verification, review, committed engineering | Critical/Important zero before real preflight |

## Progress

- Task 1: models/loader/API complete; base 2e67696bd6ab12a6716360f4b868af7fbad160c1.
- Tasks 2 / 3 / 4A / 4B1 / 4B2: implemented in dependency order; evidence below.
- Task 5: complete; final maintained 1082/1082 and independent review C0/I0/M0.
- Task 6: canonical/preflight complete; stopped at the human gate, subsequently
  satisfied by the exact user approval recorded in the final section.
- Post-approval operation: 2019 accepted as V1.22 candidate generation 000001;
  independent verification 24/24 PASS. No formal promotion.

## Task 1 evidence

- Missing model module: 1 collected / 1 assertion FAIL / 0 ERROR.
- Empty importable model module: 14 collected / 1 PASS / 13 assertion FAIL /
  0 ERROR. Assertions were moved out of setup and rerun before production;
  the earlier setup assertion run is not counted as contract RED.
- Models implemented: new + historical models 29/29 PASS.
- API/surface RED: 2 test methods / 6 failed assertions (five subcases), 0 ERROR.
- Annotated nonbehavioral scaffolds: 16/16 PASS.
- Strict loader RED: 4 methods / 11 failed assertions, 0 ERROR; all fail because
  the intentional loader stub lacks behavior, not imports/fixtures.
- Loader implemented: models/API/loader plus historical model/surface/replay
  tests 57/57 PASS before additional frozen/copy/genesis lock.
- No real source processing or candidate write.

Final Task 1 gate: 58/58 PASS, 0 skips/expected failures; commit 1fbbc0d.
Baseline maintained suite (started before edits): 1005/1005 PASS, 0 errors,
skips or expected failures, 253.860 seconds.

## Task 2 evidence

Base 1fbbc0d. Synthetic bridge RED: 9 methods, 1 API PASS, 12 failed
assertions including subcases; 0 ERROR. Only deliberate missing behavior.
Bridge implementation is a fixed V122 sibling; existing four payload helpers
and old bridge bodies remain unchanged.
Task 2 GREEN: 9 new + 7 old bridge + 50 Task 10B = 66/66 PASS.
The first combined GREEN command misspelled an integration module; its
import ERROR is not RED or a passing gate. The corrected command passed.
No real 2019 proposal, source, approval or candidate was changed.

Task 2 complete: commit be360e8.

## Task 3 evidence

Base be360e8. Initial genesis behavior RED: 12 test methods, 2 PASS /
13 failed assertions including subcases / 0 ERROR, exclusively missing
preflight behavior. No parent creation was used as a prerequisite.
Schema/count fixture SQL and unrepresentable-record expected counts were
corrected after first GREEN attempt; these construction/expectation failures
are not claimed as behavior RED.
Additional sibling-manifest contract RED: valid DB plus wrong/missing sibling
manifest incorrectly accepted (2 failed assertions); fixed with exact frozen
manifest hash/size and regular-file validation.
Final genesis + unchanged V121 + Task 9A: 61/61 PASS, zero skips/xfails.
Exact 591-row index including 2015–2018 duplicate, deep schema/view/count
controls, genesis oracle, path-independent equality and zero-write verified.
Non-None parent still raises explicit NotImplementedError pending Task 4B1.

Task 3 complete: commit 72227cd.

## Task 4A evidence

Base 72227cd. First-generation RED (after correcting test wrapper construction):
14 methods / 1 API PASS / 15 failed assertions including subcases / 0 ERROR.
Earlier uncaught deliberate stubs and wrapper syntax error are NOT valid RED.
Writer/verifier/profile implementation accepts only a single approved batch;
multi-batch entry explicitly remains NotImplementedError, as does parent preflight.
New regression identified candidate SQLite readability incorrectly inferred
without reading its schema: assertion RED → candidate schema read → GREEN.
The output-path negative fixture was corrected because its initial path was
actually inside approved staging; no production rule was relaxed.
Final Task 4A + Tasks 1–3: 60/60 PASS (17 candidate tests), zero skips/xfails.
Verified 24 checks, full old SQLite schema/row preservation, first order 592,
private user_version 122, candidate selectable=0, deterministic roots, independent
genesis calls, forged matching parents, corruption and cleanup controls.
This is NOT evidence of parent-preflight or multi-batch GREEN.

## Task 4B1 / 4B2 and hardening evidence

- After 4A GREEN, parent-preflight RED: 3 methods / 3 FAIL / 0 ERROR,
  each first built and independently verified generation 1, then reached the
  explicit parent-preflight stub. Minimum parent implementation: 3/3 GREEN.
- After 4B1 GREEN, multi-batch RED: 4 methods / 5 assertion failures
  (including subcases) / 0 ERROR. Valid B preflight/approval bound generation
  1 before writer/verifier calls. Removing first-generation-only entry guards
  enabled full-prefix reconstruction; initial 4B2 GREEN: 4/4.
- Genesis mutation checks executed in memory, without source edits: removing
  writer's own boundary caused its targeted test to FAIL; removing verifier's
  own boundary caused its targeted test to FAIL (each 1 FAIL / 0 ERROR).
- Additional forged empty-prefix/nested-approval control: 1 method / 2 FAIL /
  0 ERROR (IndexError/AttributeError leaked by writer); request validation now
  precedes field access. Existing genesis checks remain independent.
- Added forged count, source-byte drift, parent-output overlap and second
  generation deterministic artifact assertions.
- The integrity-negative fixture was calibrated before claiming coverage:
  read-only SQLite in this runtime did not report the attempted CHECK/header
  mutations. Those failed fixture assertions are not production RED. Corrupting
  the synthetic candidate data b-tree page type produces a real integrity
  failure and its dedicated failed verification check (focused 1/1 GREEN).
- No real batch approval was constructed; all writer inputs are synthetic.

Final Task 4 focused regression: 153/153 PASS in 51.703s, zero skips/xfails;
25 new candidate cases + Tasks 1–3 + unchanged V120/V121 candidate suites.
Command: runtime Python -m unittest -q tests.integration.test_v122_candidate
tests.integration.test_v122_preflight tests.integration.test_v122_hkdse_bridge
tests.unit.test_v122_models tests.integration.test_v121_candidate
tests.integration.test_v120_candidate.

## Historical Task 5 first review — superseded scope blocker

Task 4 commit: 788eee1f28a8e91ccf6af45f4fbf6572529b76b8.
New historical replay: 3/3 PASS; existing formal verifier checks V119 18/18,
V120 21/21 and V121 21/21 PASS with materialization disabled.
Explicit Task9A + Task10B + Task7 gate: 41 + 50 + 7 = 98/98 PASS.
V1.18 independent validator: PASS, 497 questions.
All four formal database hashes/counts (497/502/543/591), 21 original 2019
files and seven approval-bound evidence files passed immutable replay.
Historical HKDSE function/class ASTs are unchanged; the original 99 public
names remain an exact ordered prefix followed by the approved 18 names.

Full maintained suite command follows Plan Task5's module enumeration,
excluding only the separately attributed legacy module:
1076 collected, 1075 PASS, 1 FAIL, 0 ERROR, 0 skip, 0 expectedFailure;
279.790 seconds. This run preceded the three new remediation RED tests.
Failure: tests.unit.test_v121_promotion_models.V121PromotionPublicContractTests
.test_exact_append_only_public_surface, line 73.
Its absolute suffix assertion conflicts with V122's mandated append-only
surface. That file is absent from Design §10's closed scope (lines 385–418)
and the Plan closed file map. It was neither modified nor skipped.
This is a scope-authority conflict, not permission to weaken a maintained gate.
Minimum resolution: explicitly authorize this fourth historical test-surface
migration, preserving the nine V121 names and their order immediately before
the 18 V122 names; leave all model/behavior assertions unchanged.

Independent reviewer: /root/v122_implementation_review (gpt-6-astra), fresh
read-only review of base 2e67696 through 788eee1 plus the new replay test.
Verdict: Critical 0 / Important 2 / Minor 0, NOT PASS.
1. v122_verification.py:615–630: supplied candidate carrier can diverge from
   canonical records while matching a recomputed preflight/approval digest.
   Synthetic changed answer was written and verifier returned PASS 24/24.
2. v122_verification.py:1061–1062: unencoded SQLite URI with '#' or '?' may
   misaddress/open a sibling DB instead of remaining read-only.
Targeted test-first reproduction: 3 methods, 6 assertion FAIL, 0 ERROR, exit 1.
These cover changed answer/question/controlled taxonomy, independent verifier
acceptance and both reserved path characters. No production fix yet; the
full-gate scope conflict was discovered while these RED tests ran.
After scope authorization, fix within existing V122 files and re-review.

Reviewer declined to judge real import/promotion/2020 (correctly unauthorized)
and independent replay of earlier intermediate RED command outputs (ledger
records observations from this execution, not independently archived logs).
Executor ruling: preserve that evidentiary limitation; do not claim independent
reproduction of historical intermediate REDs. No behavior was silently omitted.

No new real canonical package, preflight, import approval or V122 candidate;
releases/V1.22 remains absent. Legacy attribution was not rerun; known 9/2
surface is historical, not part of this maintained GREEN claim.
That checkpoint stopped for the narrow test-file scope decision. It does not
override the subsequent explicit authorization recorded below.

## Task 5 authorized remediation

User authorization: MINIMAL TEST-ONLY SCOPE EXTENSION. Docs-only commit
`a61bd93` adds exactly `tests/unit/test_v121_promotion_models.py`, bringing
Design/Plan to 21 paths; no other behavior/scope is enlarged.
Only its exact-surface test method changed: the fixed historical 99-name prefix
plus the exact approved 18-name suffix is asserted. All nine V1.21 promotion
names/order and all other test-method ASTs are unchanged. The recorded
1075/1/0 maintained run is the accepted migration RED; migrated suite 6/6 GREEN.

Before production remediation, extended counterexamples ran 4 methods with
10 failed assertions / 0 ERROR / exit 1 in 4.782s. Failures reproduce canonical
answer, question, controlled taxonomy, source identity/evidence, difficulty
and record-order forgery, independent verifier acceptance, and both '#'/'?'
SQLite output paths. Matching forged reports/approval digests do not excuse
divergence from the unchanged canonical package.

The minimal production change is confined to `v122_verification.py`:
independently reconstruct the exact canonical candidate tuple (all raw fields,
derived normalized/image hashes and declared order), validate package binding,
and use encoded absolute file URIs with mode=ro for both SQLite connections.
Writer preflight uses this package-authority gate before creating output.
No historical preflight/model/writer/verifier production file changed.

Targeted GREEN: 4/4 PASS in 3.624s. V1.22 focused 75 plus migrated historical
surface/model suite 6 = 81/81 PASS in 35.573s. Task9A 41/41, Task10B 50/50,
Task7 7/7, V1.18 validator PASS; formal read-only V119 18/18, V120 21/21,
V121 21/21 PASS. Frozen counts remain 497/502/543/591.

Fresh separate legacy attribution: 11 collected, 9 PASS / 2 FAIL / 0 ERROR,
exit 1. Exact failures remain:
- Task5LegacyBehaviorTests.test_build_is_deterministic_and_matches_reviewed_core_hashes
- Task6LegacyBehaviorTests.test_build_matches_all_seven_frozen_primary_artifacts
Both are the known runtime SQLite hash/byte-equivalence baseline surface;
there is no new failure category and neither is represented as maintained PASS.

All 21 actual changed paths match the closed authority. All old HKDSE adapter
function/class ASTs remain unchanged. Final full-maintained output and
independent re-review disposition will be recorded before Task 5 closes.

### Follow-up strict-manifest remediation and independent re-review

The fresh reviewer found one additional Important inside existing V122 scope:
ordinary JSON parsing accepted duplicate/reordered canonical manifest fields
after approval, although fresh preflight's strict loader rejected them.
Two independent writer/verifier test methods established 4 assertion FAIL,
0 ERROR, exit 1 in 2.305s; each first proves that strict loading rejects the
mutated envelope. Minimal correction reuses `load_v122_import_manifest` at
the package-authority boundary and compares the frozen manifest carrier.
It preserves record rebinding and does not modify the strict loader or any
historical production module. Focused GREEN: 2/2 in 1.186s.
Final V122 focused suite: 77/77 PASS in 41.694s.

Independent reviewer `/root/v122_remediation_rereview` (gpt-6-astra) re-read
the final diff and repeated the original hostile-manifest probe: writer blocks,
verifier returns FAIL with `batch_authority_artifacts` failed, and the package
and existing synthetic candidate remain byte-identical. Fresh reviewer suite
(candidate + historical promotion models + historical replay): 40/40 PASS,
41.848s, zero errors/skips/expected failures. Final verdict:
Critical 0 / Important 0 / Minor 0. All three Important findings are closed.

Reviewer did not judge the main agent's still-running full gate, historical
intermediate RED reproduction, real transcription mathematics, Task 6 not yet
executed, or unauthorized real import/promotion/later-year ingestion. Executor
accepts these limits; the exact previously approved transcription remains
input authority and the full gate must independently pass before Task 6.

### Full-suite isolation

An overlapping full run (1080 tests, 347.183s) had two teardown failures:
- tests.integration.test_v119_promotion.PromotionBehaviorContractTests.test_manifest_upstream_sizes_and_canonical_json_bytes_are_verified
- tests.integration.test_v119_writer.V119DeterminismAndAtomicityRedTests.test_transaction_artifact_and_rename_failures_clean_only_private_temp
Both compare the entire shared staging tree, and detected temporary
`task12-v122-hkdse-2019/synthetic-*` roots created concurrently by the focused
test/reviewer processes. This is execution interference, not valid behavior
RED or a passing gate. No assertion was changed, skipped or suppressed.
All concurrent probes completed and cleaned up before the final 1082-test
serial maintained run; that final result is required for completion.

## Task 5 final gate — PASS

Final serial maintained run: **1082/1082 PASS**, 288.613s, 0 FAIL, 0 ERROR,
0 skip, 0 expectedFailure, 0 unexpectedSuccess. Only the separately named legacy
attribution module is excluded by the approved maintained command.

After the final production correction, explicit gates were run sequentially:
Task9A 41/41; Task10B 50/50; Task7 7/7; historical replay 3/3;
V1.18 independent validator PASS (497); formal verifiers V119 18/18,
V120 21/21, V121 21/21 PASS. Legacy attribution was re-run separately:
9 PASS / 2 FAIL / 0 ERROR, exact same named tests/categories; the byte-difference
may first surface in SQLite or its hash-derived frozen report because artifact
iteration order differs. This is not a new failure class or a maintained blocker.
`git diff --check` passes. No production change followed clean independent review.

The exact 24 checks remain:
`candidate_directory`, `candidate_contract`, `baseline_authority`,
`batch_authority_artifacts`, `parent_chain`, `approval_binding`,
`preflight_reconstruction`, `filesystem_closure`, `sha256sums_closure`,
`artifact_references`, `rollback_contract`, `image_projection`,
`sqlite_readability`, `sqlite_integrity`, `sqlite_foreign_keys`,
`sqlite_schema`, `v121_preservation`, `batch_ledger`,
`candidate_projection`, `effective_collision_closure`, `count_closure`,
`candidate_digest`, `deterministic_identity`, `formal_boundary`.

Task 5 may close and be committed/pushed normally. Task 6 is the only next
approved execution: exact recorded 2019 transcription approval, two canonical
roots, read-only preflight, then human import gate. No real import approval,
candidate database, release or 2020 ingestion has been created.

## Historical Task 6 pre-approval operational checkpoint

Task 5 engineering commit `59140a0207ea4e9b348b7b55e403a2c3b2552052` was
pushed normally; remote/local matched with 0/0 ahead/behind before Task 6.
The recorded, already-approved 2019 transcription was loaded and verified:
`3139b39d7c42d17fbc28870d00127dd2792943860ef615a2c950d528f98b6829`,
12 whole questions / 100 marks. No new transcription approval was fabricated.
Q10(d)'s exact human-confirmed note and Q12's source typo remain unchanged.

Two fresh canonical roots under `data/staging/task12-v122-hkdse-2019/`:
`canonical-v122-approved-a` and `canonical-v122-approved-b`.
Relative file sets, all bytes and full preflight results are equal.
Actual report: `REAL_BATCH_IMPORT_APPROVAL_REPORT.json` in the same staging
directory (ignored, not committed), containing full source/canonical identities,
all primary-type/tag counts, difficulty, exact issues and frozen tree hashes.

| Field | Actual result |
|---|---|
| batch_id | JOY-M2-HKDSE-2019-PP-MS |
| preflight_sha256 | 674624abcd338b2fa3683b982300a30082e3d0e62f95f97e3e8d25e12d1d0fa5 |
| parent_candidate_digest | 7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7 |
| status | READY FOR USER IMPORT APPROVAL |
| detected / new | 12 / 12 |
| duplicate / rejected / ambiguous / adaptations | 0 / 0 / 0 / 0 |
| issues | 0 |
| before / projected count | 591 / 603 |
| missing answers / independent explanations | 0 / 12 |
| difficulty | D2:4 / D3:4 / D4:2 / D5:2 |
| image files / image references / source figure references | 0 / 0 / 0 |

Official MS is complete and preserved as answer authority; missing independent
explanation content is reported honestly and not auto-filled.

Source staging SHA:
`4b730381e97743b34fc3bf41e1da29cb303895ebe5ccea5a8de270f1eaf0b755`.
PP SHA: `5fb0366a46c08c9215410d7bd8005998fd5bc00178aa4abde92c6b2961caf879`.
MS SHA: `076cdf9a43cb41f196450c78bf1ee4be3069ca0e5303c0680fdda9f2fce244e6`.
Canonical manifest file-byte SHA:
`240a9b7919106e6792c0c796c3d2cd1b3958444efcc17d791923d0c1bc493310`.
Preflight's canonical manifest projection SHA (distinct from original file bytes):
`67e4b9cc7b4f2d19364aae2a0ef6d71737a526f7cc5666f2c7bfedf17cdf5613`.
Canonical record-byte SHA:
`9bf42ba5a0e0fc26f6fd13bfd4936d24e222991ec860b0d91cdadde92a5b14eb`.

All four formal release trees/SQLite SHA/counts are unchanged before/after.
Original 2019 approval/evidence tree is unchanged. Before genesis preflight,
no accepted V122 generation existed. No real import approval object or writer
invocation occurred. Proposed `candidate-generation-000001` remains absent;
no V122 staging SQLite or `releases/V1.22` exists. No 2020 ingestion.

**USER DECISION REQUIRED — REAL BATCH IMPORT**

```text
USER APPROVED IMPORT BATCH JOY-M2-HKDSE-2019-PP-MS 674624abcd338b2fa3683b982300a30082e3d0e62f95f97e3e8d25e12d1d0fa5 V1.22 PARENT 7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7
```

At that checkpoint this statement was a requested human decision, not approval
received. The later actual authorization and execution are recorded below.

Post-operation fresh Task9A + Task7 + immutable historical replay: 51/51 PASS,
7.039s, zero skips/expected failures. `git diff --check` PASS; delivery sync
modifies only this report and `PROJECT_STATE.md`. Canonical outputs and the
one-off API orchestration script remain ignored runtime artifacts.

## Approved 2019 import — generation 000001

Execution baseline: `7567f080d5c3db2cfa41fa18371e3d303fae430a`,
`task8b/pipeline-migration`, clean tree/index and upstream ahead/behind 0/0.
The user explicitly supplied this exact statement:

```text
USER APPROVED IMPORT BATCH JOY-M2-HKDSE-2019-PP-MS 674624abcd338b2fa3683b982300a30082e3d0e62f95f97e3e8d25e12d1d0fa5 V1.22 PARENT 7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7
```

Before writing, the strict loader and maintained preflight independently
reconstructed both existing canonical roots; their full results matched each
other and the unchanged pre-approval report. Exact batch/preflight/target/genesis
matched the user statement; detected/new 12/12, duplicate/rejected/ambiguous/
adaptations 0/0/0/0, issues 0, before/projected 591/603. No accepted V1.22
generation or output existed. No synthetic approval was reused.

Fresh serial pre-write regression: V122 models 21, bridge 9, preflight 13,
candidate 31, historical replay 3 = **77/77 PASS**; Task9A **41/41**;
Task10B **50/50**; Task7 **7/7**. Total **175/175 PASS**, zero skips,
expected failures or unexpected successes. V1.18 independent validator PASS.
The prior 1082/1082 full maintained result is historical engineering evidence;
this operational execution made no production or test changes. Legacy
attribution was not rerun; the separately recorded 9 PASS / 2 known FAIL
surface is not represented as fresh maintained verification.

`build_v122_candidate()` consumed the exact `V122ApprovedBatch` and atomically
published only this new staging generation:
`data/staging/task12-v122-hkdse-2019/candidate-generation-000001`.

| Field | Accepted value |
|---|---|
| Generation / accepted batches | 000001 / 1 |
| Accumulated additions / projected count | 12 / 603 |
| Candidate digest / next required parent | 83c5efa109132c85dca8b96679ac97d4d9a59dd94e0cc76a57c80871a944ff07 |
| Candidate SQLite SHA-256 | 7a3b8892063ec3feba36f4cda61d955ffe09d9bf0498056684e3066b46eea4d0 |
| Candidate manifest SHA-256 | 4feeb629ff0c28a20e10c031f8823217b2d42b673d9a0eb1e771fca833d64147 |
| Independent verifier | 24/24 PASS |
| New rows | candidate, selectable=0, aggregate_order 592–603 |
| Formal production | V1.21 / 591, unchanged |

The independent `verify_v122_candidate()` ran after publication and again in
a separate process, with fresh preflight/request reconstruction; all 24 named
checks passed and the candidate file tree was unchanged by verification.
Read-only SQLite checks confirmed private user_version 122, 591 preserved
formal rows, 12 candidate rows, 603 aggregate rows and the sole ledger entry's
exact batch/parent/preflight/approval statement.

Post-write Task9A + Task7 + historical replay: **51/51 PASS**, 7.138s,
zero skips/expected failures/unexpected successes. Historical replay includes
read-only formal V119/V120/V121 verification (18/21/21 checks). The independent
read-back also matched the stored receipt exactly. `git diff --check` PASS;
tracked changes are restricted to this report and `PROJECT_STATE.md`.

`REAL_BATCH_IMPORT_RECEIPT.json` in the same staging parent records the complete
verification report, exact approval, artifact hashes, source/canonical identities,
four frozen release trees/counts, and original 2019 evidence hashes.
`REAL_BATCH_IMPORT_APPROVAL_REPORT.json` remains byte-identical historical
pre-approval evidence. Candidate-local `rollback.json` is a declarative receipt,
not permission to delete any generation. No operational artifact enters Git.

Formal V1.18/497, V1.19/502, V1.20/543 and V1.21/591 retain their exact SQLite
and release-tree hashes. The original 2019 proposals, approvals, Q10(d) note,
Q12 printed typo, source evidence and both canonical packages are unchanged.
No production/test/Design/Plan/legacy change, formal mutation, `releases/V1.22`,
promotion or 2020 ingestion occurred. Generation 000002 must use the new verified
candidate digest, not genesis. Stop at this operational checkpoint until the
user explicitly selects further ingestion or authorizes promotion-readiness work.
