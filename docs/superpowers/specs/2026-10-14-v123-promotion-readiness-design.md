# V1.23 Promotion Readiness — fixed generation 000003

Date: 2026-10-14 (Asia/Shanghai)

Status: WRITTEN DESIGN APPROVED (2026-10-19). Implementation NOT STARTED.
Human approval binds commit `1c66a8e9daaaa991fc72b3ca891d87251051831b`
and Design SHA-256
`dac063c914b2a7003295d1306d39b0390329f408bace59c9f14d0e943e943541`.
This status-only synchronization does not change the approved technical contract.
Plan review and implementation authorization remain pending.
The user authorized preparation of the minimum missing promotion authority,
not publication. Written Design approval precedes Plan preparation; reviewed,
committed Plan and implementation authorization precede production changes.
Native / Inline is the requested eventual execution mode.

## 1. Purpose, choice and non-goals

Make the already accepted generation 000003 eligible for a later exact release
approval: 639 preserved formal V1.22 records + 38 approved source records = 677
published/selectable records in a non-formal release-equivalent output.
677 is a storage-record count, not a distinct-original-question count. The
2023/2025 additions are known originals with another source; retain both sources.
Readiness never reimports Oxford or rewrites its source/answer identity.

Use three fixed V1.23 promotion sibling modules patterned on the existing V1.22
promotion. Reusing the V1.22 publisher with substituted constants is invalid;
a generic future-version framework is unnecessary and prohibited. Reuse only
existing genuinely version-neutral primitives (e.g. atomic no-replace rename).
Keep the verifier independent of builder projections/DDL/identity helpers.

Do not change the scheduler, whitelist, notifications, runner, backup service,
source adapters, historical candidate APIs/digests/approvals, or formal files.
No history cleanup, 2024 remediation, V1.24, new ingestion, live rollback or
query-default/pointer migration. Preserve the user's dirty AGENTS.md verbatim.

## 2. Exact observed input envelope

Engineering baseline: `716ab3ae1536d788be0bd2107a4e7aed8b64ac19`, branch
`task8b/pipeline-migration`, existing worktree. Values below were freshly read
from files and checked with the existing independent candidate verifier (24/24).

| Identity | Exact value |
|---|---|
| baseline | V1.22 / 639 published/selectable records |
| baseline SQLite | `releases/V1.22/Joy_M2_Complete_Question_DB_V1_22.sqlite3` |
| baseline SQLite SHA / bytes | `a474846a5b1d10a0fe48a259522fbb327747319f4a114452bf9f294405d8d9e0` / 10510336 |
| baseline manifest SHA / bytes | `441e00ac1536b959b40b6177bd17a6f14632a287f85145e202a51bcf137ddc8b` / 7915 |
| baseline release digest | `89a592abf52507cc0325f9c6f30ee2c74d4ec55fdcef988fdae6cb12f5a3073b` |
| baseline semantic SHA | `964cceff64cdeaedf663d1f9be98aaaf6adf3ffe2cddf6a18447ea141948a1c4` |
| candidate generation / accepted batches | 000003 / 3 |
| candidate digest | `c5c51df58d64349d58bd71469fe67a72cced56e77369126d6fec66bb2fcc955a` |
| candidate SQLite SHA / bytes | `b7e2247e004cc4c91c339693de4f106edef11bb7067e34b52887547a8006cb01` / 10764288 |
| candidate manifest SHA / bytes | `febe70a572b82783bf6199679bf1a2024294d98b44b4fbe047a2349a3830a076` / 5664 |
| candidate additions / projected total | 38 / 677 |
| canonical standalone image files | 0; existing PDF/page/region references remain evidence |

Candidate directory:
`data/staging/auto-ingestion/candidates/8531b270990b350afbbcdc16eff2fddf63a1f33d7a451402199344eae2447a20/`.
Names: `Joy_M2_V1.23_candidate.sqlite3`, `candidate_manifest.json`,
`SHA256SUMS`, `rollback.json`, and six ordered batch authority files.
Latest receipt: `data/staging/auto-ingestion/receipts/000003.json`.

The selected candidate is immutable even if daily ingestion later advances.
Report later generations separately; never silently select the latest, reorder
the ledger, regenerate the candidate, or replay a writer. Both builder and
independent verifier require the exact typed V123 authority, identities/sizes,
all 24 candidate checks PASS, and the exact three-entry ledger below.

## 3. Ordered approval and provenance closure

| Ordinal / batch | Count / cumulative / projected | Preflight SHA | Required parent |
|---|---|---|---|
| 000001 — JOY-M2-HKDSE-2023-PP-MS | 12 / 12 / 651 | `64b61671f337dafddd5d316ca0e9ba837e24948fe91256c5df7d1c1b779059a4` | `ea3b7db78210e045761784a2e415387c1b17f13b5aedde484ca2ae248a45eec7` |
| 000002 — JOY-M2-HKDSE-2025-PP-MS | 13 / 25 / 664 | `732f05c7d36203fcb920d5bfd59673041533abb84db5d82e6fa8fc3407bda5e0` | `f2fb80e7a7f9e4478877446a8e74cccac8cd1c8829784cef0eb93637bcfacaf1` |
| 000003 — JOY-M2-STG-MOCK-2025-26-C-SET1-20260903 | 13 / 38 / 677 | `8531b270990b350afbbcdc16eff2fddf63a1f33d7a451402199344eae2447a20` | `9d6b16cf357e7d32268552ab17c74a16a409d502d7873aa6c7a3854f77edebb9` |

Canonical manifest SHAs in this order:

1. `2aafa67c591dd1ca9976530e5cdead3d6b0021c244c0d8875b3826de1150b3ea`
2. `d3ebf556340a1e278d1141e2c87432c5dc12c2c113ca8566db90d8957a0c5862`
3. `f015d0f334379c7ae524077c80c74f768c831cfcdc0b62f963f0ff07eba96b67`

Reconstruct exact existing approved batches from canonical evidence and received
approvals without writing or inventing approvals. Read-only preflight replay is
allowed for independent verification; source extraction/transcription is not.
The manifest's six authority ArtifactRefs bind the exact approval/preflight
files; promotion copies their ordered projections without rewriting evidence.

Oxford source_id stays `OXFORD-M2-2025-26-C-SET1`, with IDs
`MOCK-C1-2025-26-Q01` through `MOCK-C1-2025-26-Q13`, 100 marks,
`publisher_mock` source identity and `source_provided` publisher solutions.
Preserve Oxford / 2025-26 / C Set 1 and PP/MS locators: never label these as
HKEAA official MS. Its approved transcription digest remains
`2038db4f3486aae8a92ec0e38acc338f9c0c2782a5b245301cca85792a29928f`.
Keep all missing independent explanations and all existing content unchanged.
No taxonomy, difficulty, translation, question, solution, mark or figure edit.

## 4. Normative counterpart and exact role-specific delta

At the engineering baseline in §2, the three
`src/joy_m2/ingest/v122_promotion*.py` modules and
`docs/superpowers/specs/2026-09-27-v122-promotion-readiness-design.md` define
the counterpart. Its detailed predecessor is
`docs/superpowers/specs/2026-09-19-v121-formal-promotion-readiness-design.md`
§§5–12. This Design freezes the following substitutions in NEW modules only;
it does not authorize editing any historical contract or implementation:

- Promotion role: V1.22/v122/V122/task12 becomes V1.23/v123/V123/task13.
- Baseline role: V1.21/v121/591 becomes V1.22/v122/639, with §2 identities.
  In both the manifest baseline projection and promotion identity baseline
  projection, database_schema is exactly `task12-v122-formal-v1` (not inherited
  `task11-v121-formal-v1` and not new-promotion `task13-v123-formal-v1`). Builder
  and verifier use this literal independently; a literal-oracle regression must
  reject either wrong schema even when the surrounding hashes are consistent.
- Candidate role: exact V123 carriers and verifier, task13-v123-candidate-v1,
  generation 3, three batches with counts 12/13/13, 38 additions, not four
  identical 12-record batches. SQLite and manifest identity is exactly §2.
- New formal orders 640–677, batch ordinal 1–3; FK references
  `task13_v123_batch_ledger_v1`. Source rows come only from
  `task13_v123_candidates_v1 ORDER BY aggregate_order`.
- Semantic identity schema `task13-v123-sqlite-semantic-v1`;
  preservation check `v122_preservation`; PRAGMA user_version = 123.
- Output, protected-input paths and query checks use the actual selected
  candidate and package roots, not old year-based task12 paths.

Inherited task9/task10/task11/task12 objects remain exactly as inherited;
there is no recursive version renaming or global text replacement.

## 5. Public API and carriers

Append exactly nine names to `joy_m2.ingest.__all__`, leaving its whole current
prefix unchanged, in this order:

```text
V123PromotionContract
V123PromotionBuildRequest
V123PromotionVerificationRequest
V123ReleasePromotionApproval
V123PublicationRequest
V123PromotionArtifacts
build_v123_promotion
verify_v123_promotion
publish_v123_release
```

Use the exact counterpart carrier fields, order, no-default/frozen semantics,
validation and types, replacing only the V122 candidate/promotion types with
the corresponding V123 types. Function arguments remain exact typed
`(request, config: PipelineConfig)`; returns respectively
V123PromotionArtifacts, VerificationReport, V123PromotionArtifacts.

The 14 contract values, in counterpart field order, are:

```text
V1.23
task13-v123-formal-manifest-v1
task13-v123-formal-v1
task13-v123-promotion-identity-v1
task13-v123-formal-rollback-v1
123
Joy_M2_Complete_Question_DB_V1_23.sqlite3
manifest.json
SHA256SUMS.txt
rollback.json
images/sha256
task13_v123_promoted_questions_v1
task13_v123_promotion_v1
formal_complete_questions_v123
```

## 6. Formal-equivalent projection and metadata

Copy the exact candidate SQLite to a private staging build tree. In one
transaction add the counterpart promotion table, promoted table and formal
view with §4 deltas. Preserve all candidate tables as immutable audit evidence.
For the 38 new projection rows only: candidate becomes published, selectable
0 becomes 1, authority_kind becomes `task13_v123_promoted`. Column renames and
the formal view's NULL reviewed-translation slot follow the counterpart exactly;
all other source field values remain identical.

`formal_complete_questions_v123` UNION ALLs the existing
`formal_complete_questions_v122` once and the new promoted table once, ordered
by formal_order. Require 677 distinct IDs and sequential orders 1–677, all
published/selectable. Do not union old candidate tables: the historical 591+48
are already in 639. Compare all original 639 formal rows field-for-field, and
the new 38 with their approved candidate projections, not merely counts.

Only these release_metadata_v2 values are inserted/updated in the output copy:

```text
release_version = V1.23
baseline_version = V1.22
baseline_sqlite_sha256 = §2 baseline SQLite SHA
release_model = append-only-multi-batch-promotion
schema_version = task13-v123-formal-v1
formal_question_count = 677
task13_baseline_release_digest = §2 baseline release digest
task13_candidate_digest = §2 candidate digest
task13_candidate_sqlite_sha256 = §2 candidate SQLite SHA
task13_candidate_manifest_sha256 = §2 candidate manifest SHA
task13_accepted_batch_count = 3
task13_promoted_questions = 38
```

Metadata is stored as counterpart text values. Every other metadata key,
schema object and inherited row remains identical. In particular all historical
task12 promotion metadata remains unchanged. Real V1.22 bytes never change.

## 7. Exact artifacts, determinism and independent verification

The selected envelope has no standalone image artifacts. Exactly four output
files (no ZIP requirement, no fabricated image assets):

```text
Joy_M2_Complete_Question_DB_V1_23.sqlite3
manifest.json
SHA256SUMS.txt
rollback.json
```

Preserve PDF/page/region graph references as source evidence, including 2023 Q6;
they are not canonical image files. Baseline image references retain their
historical external authority and do not become newly copied images.

Manifest exact keys/nested shapes, artifact kinds, semantic projection and
release-identity projection follow the pinned counterpart with §§2–6 deltas.
`batch_ledger` contains the exact three entries and `batch_authority_artifacts`
the exact six entries; these are evidence references, not six additional formal
files. Canonical JSON: UTF-8, ensure_ascii=False, sort_keys=True, compact
separators, allow_nan=False, terminal LF. SHA256SUMS.txt uses lowercase SHA,
two ASCII spaces, canonical relative paths, UTF-8 path order and terminal LF;
it binds the three other files and excludes itself.

Release digest is SHA-256 of the canonical counterpart promotion identity:
versioned schema, contract, exact baseline/candidate projections, ledger,
authority refs, counts, actual formal SQLite hash/size/semantic hash, images=[],
and rollback_action. Do not insert absolute paths, mtimes or temporary roots.
Compute final SQLite/manifest/semantic/release hashes only from real dry-runs;
there is no approved or predicted release digest at the Design checkpoint.

Two independent builds under distinct non-formal roots must be byte-identical
for all four files. Compare relative ArtifactRef path/kind/size/hash, semantic
SHA and release digest as well; absolute output root naturally differs. No
semantic-only waiver if SQLite bytes differ.

Independent verifier must not import builder helpers or trust builder PASS.
It reconstructs constants, DDL, projections and identity independently; the
21 ordered counterpart checks remain, replacing only v121_preservation with
v122_preservation. All must PASS, including candidate 24-check prerequisites,
ledger/approval/parent closure, SQLite integrity/FK/schema, preserved639,
exact38, provenance, count/ID/order/status, manifest/artifact/SHA/filesystem
closure and location. Use escaped Path.as_uri() + read-only SQLite connections.
Malformed JSON unable to establish context retains InputFormatError; parsed
invalid manifests produce structured FAIL, including wrong types/bool-as-int.
Invalid typed request/config and missing verification root retain counterpart
exceptions. No repair or write occurs in the verifier.

## 8. Publication, lifecycle and rollback boundary

Real readiness builds only below
`data/staging/task13-v123-promotion-readiness/`. The API's general path boundary
remains a new strict staging descendant, rejecting symlinks, existing targets,
lexical path aliases, any ancestor/descendant overlap with formal releases,
all old candidate trees, canonical packages or source/approval evidence.
Plan must enumerate actual protected roots before implementation.
Real `releases/V1.23/` must not exist even transiently during readiness.

The later approval syntax, not yet a received approval, is:

```text
USER APPROVED RELEASE PROMOTION V1.23 <actual_release_digest>
```

Only an exact V123ReleasePromotionApproval matching a freshly verified dry-run
and its private copied bytes may publish. Derive only
`config.new_formal_target("V1.23")`; reject an existing target and use atomic
no-replace publication, post-copy identity verification and final independent
verification. No import approval, candidate digest, generated required-statement
template, historical release approval or scheduler permission can authorize it.

Rollback receipt follows the counterpart with protected V1.22/639, §2 baseline
SHA/release digest, selected candidate digest and exact four-file set. Action
remains `remove_release_tree_if_release_digest_matches`. Failure cleanup removes
only owned private output, or newly created output whose complete fingerprint
and bound identity remain the verified snapshot; unexpected changes retain the
tree for manual recovery. No live rollback is authorized. Prove cleanup and
rollback guards in isolated roots, never by publishing and deleting real V1.23.
There is no persistent query-pointer/default change in this implementation.
Daily formal querying remains V1.22/639 until a separate exact publication gate.

Real lifecycle regression uses a checked-in literal
`APPROVED_V123_RELEASE_DIGEST = None` in test_v123_historical_replay.py during
readiness. None requires real target absence. After a later exact real human
approval, only its literal evidence value may change; the gate requires present
independently verified formal output with exactly that digest. Never discover
approval from a manifest, receipt, environment or dry-run. Isolated tests cover
unapproved absence, exact approved presence, wrong digest and missing output.
Retain candidate-writer formal-root rejection independently of this lifecycle.

## 9. Closed file scope after approvals

NEW production (only these):

- `src/joy_m2/ingest/v123_promotion_models.py`
- `src/joy_m2/ingest/v123_promotion.py`
- `src/joy_m2/ingest/v123_promotion_verification.py`

MODIFIED production: `src/joy_m2/ingest/__init__.py`, append nine exports only.

NEW tests:

- `tests/unit/test_v123_promotion_models.py`
- `tests/unit/test_v123_promotion_primitives.py`
- `tests/integration/test_v123_promotion.py`

MODIFIED tests, exact historical prefix/suffix expectations only:

- `tests/unit/test_v119_writer_models.py`
- `tests/unit/test_v119_promotion_models.py`
- `tests/unit/test_v121_promotion_models.py`
- `tests/unit/test_v122_models.py`
- `tests/unit/test_v122_promotion_models.py`
- `tests/unit/test_v123_models.py`
- `tests/regression/test_v119_historical_replay.py`

Additionally `tests/regression/test_v123_historical_replay.py`: replace its
obsolete no-promotion-export assertion with the exact appended API expectation;
replace only perpetual real-root absence with §8 lifecycle gate/controls.
Retain all frozen hashes/counts, historical verifier/replay checks, source
approval evidence and candidate-writer formal-root negative controls.

DOC: this Design; future
`docs/superpowers/plans/2026-10-14-v123-promotion-readiness.md`;
`docs/reports/V123_PROMOTION_READINESS.md`; `PROJECT_STATE.md`.
Ignored runtime only: `data/staging/task13-v123-promotion-readiness/**` and
`tmp/pdfs/task13-v123-promotion-readiness/**` for evidence/scripts/logs.
Existing backup tooling may checkpoint explicit readiness files under
`dist/backups/` and restore into a new isolated `tmp/` directory; no backup code,
service or live restore changes. Do not commit runtime evidence or source PDFs.
Any additional tracked implementation path needs a specific scope decision.

## 10. Execution, acceptance and human gates

1. Written Design review/approval -> written Plan + independent technical
   review/commit -> human Plan approval/implementation authorization. Current
   request supplies readiness direction and preferred Native / Inline execution,
   not approval of documents which did not exist when it was issued.
2. Recheck selected candidate, all receipts and original evidence; fingerprint
   formal V1.18–V1.22, old generations, canonical, source/approval and dirtyAGENTS.
   Use existing process lock for consistent read-only recovery, without invoking
   run_cycle, pending-intent recovery or any real candidate writer. Later batches
   do not replace this selected input; record any changed operational state.
3. Valid API/model RED (assertions, not import/setup failure), models and stubs
   GREEN, primitive RED/GREEN, independently constructed formal-fixture verifier
   RED/GREEN, builder RED/GREEN, then publication/lifecycle RED/GREEN. Missing
   builder fixture is not publication RED. No real approval fabricated for tests.
4. Build twice under distinct readiness staging roots; independent formal
   verifier 21/21 each; byte compare four files, all identities and projection.
   Query batch/source Oxford13 and exact solutions/answer statuses; check all
   three batch counts, baseline639 preservation, new38, unique677, FK/integrity.
5. Fresh complete maintained suite (exclude only existing separate legacy
   attribution suite), zero skip/expected failure; record actual discovered
   counts. Fresh promotion-focused suite, candidate verifier, historical formal
   verifiers, V1.18 validator, replay/source-evidence fingerprints, diff/scope
   checks. Do not substitute old reports for fresh results or waive new failures.
6. Independent implementation review, Critical=0 and Important=0, with in-scope
   repairs and re-review. Design review alone does not certify implementation.
7. Report/state sync, explicit task paths only, ordinary commit/push. Keep
   dirtyAGENTS unstaged and unchanged. Do not claim clean tree when it is dirty;
   network failure never authorizes force/history rewrite or regeneration.
8. Stop at USER DECISION REQUIRED — FINAL V1.23 PROMOTION AUTHORIZATION with
   real release/SQLite/manifest/semantic identities, four-file closure, both
   dry-runs, query/backup/rollback results and exact statement. Do not consume it.

The existing local archive
`dist/backups/oxford-c1-accepted-20261014-000003.zip` has SHA
`317afa362a7bfcbe5c256b1c611f90b599013b8fcf4f804c8c73685d6a37b149`.
Fresh archive and isolated-restored-file checks pass 665/665, covering all587
protected/candidate identities from the existing import checkpoint. This is
local recoverability, not off-device backup or Git storage of ignored inputs.
Recheck these inputs and include the eventual approved dry-run in the existing
local backup policy before requesting final publication approval.
