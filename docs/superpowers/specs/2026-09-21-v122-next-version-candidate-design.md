# Joy M2 AI Database — V1.22 Minimal Next-Version Candidate Design

Date: 2026-09-21 (Asia/Shanghai)

Status: APPROVED — FIRST-GENERATION GENESIS PARENT BINDING CLARIFIED

## 1. Intent, authority, and current checkpoint

Continue the already-authorized real HKDSE 2019 ingestion over immutable formal
V1.21/591. The user authorized the minimum append-only next-version roll-forward
needed for that ingestion and confirmed this design direction in conversation.
The subsequent written Design review approved it subject to the sole
first-generation genesis parent clarification, now recorded in section 5.
After this clarification is committed, proceed directly to writing and reviewing
the implementation Plan; no further Design approval is required absent a new
authority conflict. Both documents must be committed and unambiguous, and the
Plan reviewed, before implementation starts. Design approval is not approval
of any real import or release promotion.

The immediate operational deliverable is an exact V1.22 canonical package and
authoritative, read-only preflight for the approved 2019 transcription, followed
by `USER DECISION REQUIRED — REAL BATCH IMPORT`. A READY result does not approve
a write. No 2019 candidate database may be created before separate exact import
approval. No V1.22 formal release or promotion is authorized.

The existing versioned multi-batch architecture is retained. Version-neutral
carriers and pure helpers may be reused; historical modules must not be
generalized, patched at runtime, or relabelled as if they already support V1.22.
This is a fixed-version roll-forward, not a generic ingestion framework.

The normative historical counterpart is the V1.21 candidate implementation at
commit `2c23402225c68e6dc0796547f68c47e5884e4d78`, together with
`docs/superpowers/specs/2026-09-18-v121-next-version-candidate-design.md`.
Where that document describes a standalone `approve_v121_import` function, use
the actual committed carrier-based approval interface: `V121ImportApproval`
plus `V121ApprovedBatch`, independently revalidated by the writer. Do not invent
an additional V1.22 approval API. This clarification changes no historical API.

## 2. Frozen baseline, target, and historical preservation

The only V1.22 baseline is the following published release, verified read-only:

```text
release_version = V1.21
release_status = published
release_model = append-only-multi-batch-promotion
question_count = 591
database_schema = task11-v121-formal-v1
manifest_schema = task11-v121-formal-manifest-v1
formal_view = formal_complete_questions_v121
SQLite path = releases/V1.21/Joy_M2_Complete_Question_DB_V1_21.sqlite3
SQLite SHA-256 = 93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a
SQLite size_bytes = 10063872
manifest path = releases/V1.21/manifest.json
manifest SHA-256 = a04f7ee7b67991427bffd3e5a3de70a310d0889fdf8f0535649840a44baf3a40
manifest size_bytes = 7913
release digest = f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3
semantic SHA-256 = 0a4e70acb1cc657207dd0fefb1e20581d34baadda804219ae2fbbfb2b5ca817f
```

The target is exactly `V1.22`. V1.18/497, V1.19/502, V1.20/543, and V1.21/591
remain byte-identical formal releases. Historical candidate generations,
packages, approvals, digests, API semantics, and release artifacts stay intact.
The presence of published `releases/V1.21/` is required, not a lifecycle error.
`releases/V1.22/` must remain absent throughout this work.

The 591 baseline questions already include the 2015–2018 additions. Read them
once through the formal V1.21 view; do not count those historical candidate
tables again or reuse V1.21 generation 000004 as a V1.22 parent. The first V1.22
batch starts from its own genesis with zero V1.22 additions.

## 3. Minimal architecture and scope classification

```text
exact approved 2019 transcription
  -> V1.22 canonical package
  -> read-only preflight over formal V1.21 + verified V1.22 parent
  -> STOP: exact real-batch import approval
  -> only after approval: immutable V1.22 staging generation
```

REQUIRED NOW: fixed public carriers, strict manifest loader, the HKDSE canonical
bridge, read-only preflight, candidate verifier, and the matching versioned
writer/profile mechanics needed to test first/second-generation and stale-parent
closure. Writer verification before real approval uses isolated synthetic test
inputs only, never the 2019 records with a fabricated approval. This preserves
the existing multi-batch contract rather than introducing a genesis-only fork
that would require another authority migration for the second batch.

DEFER: execution of any real V1.22 candidate write until the exact import gate;
every later real batch until the user selects it; any formal promotion design
or implementation until separately authorized.

DO NOT BUILD: arbitrary-version configuration, plugin/DSL infrastructure,
alternative approval paths, a new source parser, OCR/retranscription, CLI/App/API,
M1 support, question generation, or a new current-release pointer.

## 4. Exact public carriers and package surface

Define these thirteen frozen dataclasses in `v122_models.py`:

```text
V122BatchImportManifest
V122AdaptedImportPackage
V122BatchLedgerEntry
V122EffectiveState
V122PreflightRequest
V122ImportPreflightReport
V122ImportPreflightResult
V122ImportApproval
V122ApprovedBatch
V122CandidateContract
V122CandidateBuildRequest
V122CandidateVerificationRequest
V122CandidateArtifacts
```

Each has exactly its committed V121 counterpart's field names, field order,
runtime types, no-default policy, frozen behavior, independent tuple copying,
and validation semantics. Replace nested V121 carrier types with V122 types,
and fixed version/baseline literals only as specified in sections 2 and 5.
The manifest has 18 fields, preflight report 34, candidate contract 25. No
convenience fields, compatibility aliases, parallel approval carriers, or new
defaults are permitted. Booleans must not satisfy exact-integer requirements.

The unchanged shared carriers are `ImportFileEvidence`, `ImportCandidate`,
`ImportAdaptation`, `ImportIssue`, `ArtifactRef`, and `VerificationReport`.
Task 9A's manifest/candidate/digest/issue contracts do not change.

Append the thirteen names above, in that order, followed by exactly these five
names to the current `joy_m2.ingest.__all__` tuple, preserving its entire existing
prefix and order:

```text
load_v122_import_manifest
preflight_v122_import
build_v122_candidate
verify_v122_candidate
adapt_verified_hkdse_pdf_transcription_v122
```

No V1.22 promotion name or standalone approval function is exported.

## 5. Fixed V1.22 contract and independent genesis

```text
profile = V1.22
baseline_release_version = V1.21
baseline_question_count = 591
baseline_database_sha256 = 93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a
baseline_database_size_bytes = 10063872
baseline_manifest_sha256 = a04f7ee7b67991427bffd3e5a3de70a310d0889fdf8f0535649840a44baf3a40
baseline_manifest_size_bytes = 7913
baseline_release_digest = f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3
canonical_manifest_schema = task12-v122-import-manifest-v1
preflight_schema = task12-v122-preflight-v1
approval_schema = task12-v122-import-approval-v1
candidate_manifest_schema = task12-v122-candidate-manifest-v1
candidate_database_schema = task12-v122-candidate-v1
candidate_identity_schema = task12-v122-candidate-identity-v1
rollback_schema = task12-v122-rollback-v1
expected_user_version = 122
database_filename = Joy_M2_V1.22_candidate.sqlite3
manifest_filename = candidate_manifest.json
sha256s_filename = SHA256SUMS
rollback_filename = rollback.json
authority_root = authority/batches
image_root = images/sha256
required_baseline_view = formal_complete_questions_v121
required_candidate_tables = task12_v122_batch_ledger_v1,
  task12_v122_candidates_v1, task12_v122_images_v1,
  task12_v122_taxonomy_v1
required_candidate_views = task12_candidate_questions_v122
```

`task12` is the new fixed serialization namespace; it does not authorize a
separate speculative project. Keep historical `task11`/`task10` schema identities
inside copied baseline objects unchanged. Blind global version replacement is
not a migration specification.

Genesis is SHA-256 of this exact UTF-8 canonical JSON object, with sorted keys,
compact separators, `ensure_ascii=False`, `allow_nan=False`, and one final LF:

```json
{"baseline_database_sha256":"93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a","baseline_question_count":591,"baseline_release_digest":"f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3","baseline_release_version":"V1.21","candidate_count":0,"schema":"task12-v122-genesis-v1","target_release_version":"V1.22"}
```

Computed SHA-256:
`7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7`.

For generation `000001`, `parent_candidate=None` means only that no parent
candidate artifact/path exists, and is permitted only while there is no accepted
V1.22 generation. It never means that parent authority is absent. The first
preflight report MUST bind `parent_candidate_digest` to exactly
`7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7`.
The first real import approval MUST be:

```text
USER APPROVED IMPORT BATCH <batch_id> <preflight_sha256> V1.22 PARENT 7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7
```

Authority-level parent digests that are `None`, empty, omitted, a V1.20/V1.21
genesis, or any alternative digest MUST be rejected. The writer and verifier
must each independently reconstruct the V1.22 genesis digest from the exact
frozen canonical projection above and verify equality with both the bound
preflight parent digest and approval parent digest. Merely trusting a supplied
constant or matching two supplied values is insufficient; a recomputation using
an alternative projection cannot create replacement authority.

For generation `000002` and later, the exact independently verified previous
V1.22 candidate digest replaces genesis as the required parent authority. The
previous candidate artifact must be supplied and verified; neither absent-parent
mode nor genesis may bypass an existing generation. An older version's genesis,
approval, candidate artifact, or parent digest is not interchangeable.

## 6. Canonical bridge and source fidelity

```python
load_v122_import_manifest(path: Path) -> V122BatchImportManifest

adapt_verified_hkdse_pdf_transcription_v122(
    verified: VerifiedHkdsePdfTranscriptionBatch,
    output_dir: Path,
    config: PipelineConfig,
) -> V122AdaptedImportPackage
```

Require the exact verified carrier, exact embedded transcription approval, and
reconstructed semantic transcription digest. Preserve all records in original
order, with complete-question boundaries, all question/MS text, source IDs,
PDF identities, page spans, subparts, marks, figures, taxonomy, difficulty,
provenance, and the human-confirmed Q10(d) note. Transcription approval is not
reissued merely for the target-version roll-forward.

Use the established five-file staging layout:

```text
import_manifest.json
records/candidates.json
source/transcription.json
source/source-map.json
answers/official-ms.json
```

The last four source/candidate payloads retain the existing source-preserving
projection semantics and bytes for the same verified carrier. Only the manifest's
target and schema select V1.22. The loader retains strict exact-field/type,
duplicate-key, file-group, ordering, and path validation. Publication is atomic,
no-replace, staging-only, and rejects symlink/path escape or overlap with source
proposal/evidence. Never modify the approved proposal or its approval record.

## 7. Authoritative preflight

```python
preflight_v122_import(
    request: V122PreflightRequest,
    config: PipelineConfig,
) -> V122ImportPreflightResult
```

Validate the exact baseline SQLite and sibling manifest identity in section 2,
runtime carrier types, stored metadata, integrity, foreign keys, and rows 1..591
ordered by `formal_order` from `formal_complete_questions_v121`. Open the formal
database read-only. Never substitute an older formal view with fewer questions.

For a non-genesis parent, independently verify its exact V1.22 contract, ordered
batch prefix, approvals, digests, and candidate bytes before extending the
reference indexes. With no first-generation parent artifact, the report still
binds the mandatory exact genesis parent digest from section 5; it cannot omit
or null that field. Preserve the existing normalization, controlled taxonomy,
sixteen-code issue taxonomy, classification precedence, adaptation semantics,
image evidence, report construction, and issue ordering.

```text
before_count = 591 + verified parent V1.22 candidate_count
detected_count = new_candidate_count + duplicate_count + rejected_count
projected_after_count = before_count + new_candidate_count
```

Ambiguous records follow the existing rejected-subset semantics; adaptations do
not add extra questions. Do not pre-assume all twelve 2019 questions are new or
that the projected count is 603. Only the actual authoritative result decides.

The digest retains the counterpart's exact path-independent projection and
canonical bytes, with V1.22 schema/target, exact V1.21 baseline identity, new
genesis or verified parent, ordered candidates, file evidence, classifications,
issues, image evidence, and report. Absolute paths, cwd, timestamps, and temporary
roots do not enter authority. Equivalent independent roots must give identical
manifest, package, report, and preflight identities.

Keep existing error boundaries: inability to establish safe input/baseline/parent
authority raises the approved input/pipeline exception; representable candidate
or readable file-integrity problems produce structured blocking issues. Do not
turn missing/unsafe input into a fabricated READY report, or broaden exception
handling to hide a normal structured blocker. Preflight never writes a database.

## 8. Import approval, candidate accumulation, and verifier

The only real import statement is:

```text
USER APPROVED IMPORT BATCH <batch_id> <preflight_sha256> V1.22 PARENT <parent_candidate_digest>
```

`V122ImportApproval` binds that exact statement. `V122ApprovedBatch` binds the
exact READY result, package root, and approval. The writer reconstructs preflight
and the entire approved parent prefix rather than trusting in-memory carriers.
For the first batch, both writer and verifier independently reconstruct genesis
and enforce the exact preflight/approval parent binding specified in section 5.
Wrong target, wrong parent, stale package/preflight, reordered prefix, and reused
older-version approval are rejected. Import approval is not promotion approval.

```python
build_v122_candidate(
    request: V122CandidateBuildRequest, config: PipelineConfig,
) -> V122CandidateArtifacts

verify_v122_candidate(
    request: V122CandidateVerificationRequest, config: PipelineConfig,
) -> VerificationReport
```

The candidate writer copies exact formal V1.21 into a private staging sibling,
preserves every inherited schema object and row, changes only the private copy's
`user_version` to 122, and adds the four tables and one view in section 5. Their
DDL, columns, constraints, ownership, ordering, and serialization match the
committed V1.21 candidate counterparts with only new-version namespace and
baseline constants substituted. First new `aggregate_order` is 592. The view
is the ordered union of the 591 formal baseline records and V1.22 candidate
records, which remain `candidate` and `selectable=0`.

Each generation rebuilds its entire ordered V1.22 batch prefix, independently
verifies the private output, and publishes atomically without replacing prior
generations. On failure, only owned temporary output is cleaned; the parent and
all formal files remain byte-identical. Tests may use synthetic approved batches
in isolated temporary roots. The actual 2019 carrier must not reach this writer
until the user separately supplies its exact new import approval.

Verification remains read-only and checks the same 24 counterpart obligations:
directory, contract, baseline authority, batch authority artifacts, parent chain,
approval binding, reconstructed preflight, filesystem/SHA closure, ArtifactRefs,
rollback contract, image projection, SQLite readability/integrity/foreign keys,
schema, baseline preservation, ledger, candidate projection, collision closure,
counts, candidate digest, deterministic identity, and formal boundary. Rename
the version-specific preservation check to `v121_preservation`. A required check
failure means FAIL; never repair an artifact during verification. No V1.21
metadata or publication decision is recomputed or overwritten.

Rollback receipts are declarative, staging-generation-only evidence. They grant
no automatic deletion authority and cannot target a formal release or older
candidate generation.

## 9. Exact 2019 operational input and human stop

```text
batch_id = JOY-M2-HKDSE-2019-PP-MS
transcription_digest = 3139b39d7c42d17fbc28870d00127dd2792943860ef615a2c950d528f98b6829
records = 12 whole questions
marks = 100
verified carrier status = VERIFIED
review_required = 0
issues = 0
MS PDF SHA-256 = 076cdf9a43cb41f196450c78bf1ee4be3069ca0e5303c0680fdda9f2fce244e6
Q10(d) human-confirmed note = 保留不給 1M 若遺漏檢驗
Q12 original printed cross-reference = 藉 (b)(ii)
```

Reuse the existing proposal and exact recorded approval at
`data/staging/task10b-hkdse-2019/transcription-human-resolution-000002/`.
Preserve the old unresolved proposal/digest and supplemental human evidence.
Do not rerun OCR, alter taxonomy or difficulty, repair the Q12 source typo, or
change source mathematics. Any subsequently discovered semantic transcription
change requires a new proposal digest and the existing human transcription gate.

After committed implementation and clean independent review, generate canonical
packages in two independent staging roots, compare bytes, and run authoritative
preflight twice with exact baseline/genesis. Publish an approval report containing
the exact batch/preflight/parent identities, detected/new/duplicate/rejected/
ambiguous/adaptation counts, missing-answer/explanation counts, taxonomy and
difficulty summaries, issues, image evidence, projected count, and frozen proofs.
If blocked, report the actual blockers without changing records to improve the
counts. If READY, stop at `USER DECISION REQUIRED — REAL BATCH IMPORT`, showing
the exact new statement. Do not self-approve or create the real candidate.

## 10. Closed file scope

This design checkpoint changes only this specification and `PROJECT_STATE.md`.
After written Design review and a committed implementation Plan, engineering
scope is restricted to:

```text
NEW       src/joy_m2/ingest/v122_models.py
NEW       src/joy_m2/ingest/v122_manifest.py
NEW       src/joy_m2/ingest/v122_preflight.py
NEW       src/joy_m2/ingest/v122_writer_profiles.py
NEW       src/joy_m2/ingest/v122_writer.py
NEW       src/joy_m2/ingest/v122_verification.py
MODIFIED  src/joy_m2/ingest/hkdse_pdf_adapter.py
MODIFIED  src/joy_m2/ingest/__init__.py
NEW       tests/unit/test_v122_models.py
NEW       tests/integration/test_v122_hkdse_bridge.py
NEW       tests/integration/test_v122_preflight.py
NEW       tests/integration/test_v122_candidate.py
NEW       tests/regression/test_v122_historical_replay.py
MODIFIED  tests/unit/test_v119_writer_models.py
MODIFIED  tests/unit/test_v119_promotion_models.py
MODIFIED  tests/regression/test_v119_historical_replay.py
MODIFIED  PROJECT_STATE.md
NEW       docs/reports/V122_CANDIDATE_AUTHORITY_VERIFICATION.md
NEW       docs/superpowers/specs/2026-09-21-v122-next-version-candidate-design.md
NEW       docs/superpowers/plans/2026-09-21-v122-next-version-candidate.md
```

The three historical test modifications may only append the exact new public
names to their package-surface expectations. Keep historical behavioral assertions
and frozen hashes unchanged. The adapter modification may only add the V1.22
entry point/imports; keep existing bridges and source/transcription behavior
unchanged. Do not modify any V119/V120/V121 production module or shared model.

Operational output is ignored and limited to
`data/staging/task12-v122-hkdse-2019/**`; one-off orchestration scratch may use
ignored `tmp/pdfs/task12-v122-hkdse-2019/**`. It must call maintained APIs rather
than implement an alternative preflight/digest/writer. No operational artifact
or database enters an engineering commit. Existing 2019 source/approval artifacts
are input-only. No other real operational batch, new committed fixture corpus,
dependency, project script, release path, legacy path, or raw source change is
authorized. Synthetic test records stay in isolated temporary roots.

## 11. TDD, review, and completion conditions

The Plan must order public-model RED/GREEN before dependent behavior tests.
For each subsequent bridge, preflight, and candidate/verifier behavior, establish
and run effective behavior RED before its production implementation. Import,
fixture, environment, or setup errors do not count as behavior RED. An API
existence RED may justify only the smallest API scaffold, not full behavior.

Required negative controls include exact-type/default/field-order violations;
wrong baseline hash/size/schema/view/count; old-version or wrong genesis parent;
missing/null/empty first-generation authority parent digest despite a permitted
absent parent artifact; forged matching preflight/approval parent digests;
independent genesis reconstruction and generation-000002 genesis reuse;
unsafe or conflicting output paths; forged transcription approval; mutated
canonical bytes; duplicate against a 2015–2018 record in formal V1.21; parent
candidate duplicates/collisions; reordered prefix; stale approval/preflight;
failed append preservation; and candidate artifact/SHA/SQLite tampering.

Required positive evidence includes two-root canonical/preflight/candidate
determinism, first/second synthetic generation closure, all thirteen exact
carriers and eighteen exports, unchanged historical replay, and byte-identical
formal V1.18/V1.19/V1.20/V1.21 with counts 497/502/543/591.

Run all new focused tests and the complete maintained suite with zero unexpected
failures, errors, skips, or expected failures; run Task 9A 41/41, Task 10B 50/50,
Task 7 7/7, the V1.18 validator, and the existing read-only V1.19/V1.20/V1.21
formal verifiers. Historical legacy attribution is not permission to introduce
a new failure category. No actual V1.16 ZIP is searched, opened, or re-hashed;
its approved historical constant rule is unchanged.

Independent implementation review must have zero Critical and zero Important
findings. Preserve RED/GREEN, review/remediation, exact commands/counts/hashes,
scope, and no-real-write evidence in the verification report. Inspect diff and
run `git diff --check`; explicitly stage only approved engineering/docs paths.
Ordinary commits/upstream pushes follow existing autonomy policy, with no force,
merge, rebase, squash, tag, or PR. The written Design review is satisfied by the
user's conditional approval and this committed clarification. The separate Plan
writing, review, and commit requirements remain mandatory before implementation.

Completion of engineering is separate from real import. The current operational
run ends at the 2019 real-batch import approval gate. It neither publishes V1.22
nor authorizes the next year or any further infrastructure.
