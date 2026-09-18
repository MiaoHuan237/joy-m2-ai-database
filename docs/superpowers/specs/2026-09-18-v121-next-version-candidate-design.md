# Joy M2 AI Database — V1.21 Next-Version Candidate Authority Design

Date: 2026-09-18 (Asia/Shanghai)

Status: HUMAN GATE A APPROVED — IMPLEMENTATION AUTHORIZED

## 1. Purpose and boundary

V1.21 is an append-only, multi-batch staging candidate lifecycle over the
immutable formal V1.20 release. It reuses the proven V1.20 mechanics without
reopening the closed V1.20 lifecycle and without creating a generic future
version framework.

This authority permits Design, Plan, RED-first implementation, review,
remediation, commits, and ordinary pushes. It does not permit mutation of
V1.18, V1.19, or formal V1.20; creation of `releases/V1.21/`; or V1.21
promotion.

## 2. Frozen baseline and target

The only baseline is:

```text
release_version = V1.20
question_count = 543
database_schema = task10-v120-formal-v1
formal_view = formal_complete_questions_v120
SQLite path = releases/V1.20/Joy_M2_Complete_Question_DB_V1_20.sqlite3
SQLite SHA-256 = b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292
SQLite size = 9768960
manifest SHA-256 = 19ac2e43ded74a3f3eaf75c184b5eb231c9f1b0b152f5914cd822a321b045098
manifest size = 6643
release digest = 1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf
```

The target is exactly `V1.21`. Historical V1.18/V1.19/V1.20 APIs, constants,
digests, approval statements, candidate bytes, release bytes, and replay tests
remain unchanged.

## 3. Architecture

```text
verified source transcription
        |
        v
V1.21 canonical package
        |
        v
read-only preflight against formal V1.20 + verified V1.21 parent
        |
exact parent-bound approval
        |
        v
copy immutable V1.20 baseline into private staging root
        |
add ordered V1.21 batch ledger/candidate tables and assets
        |
independent verification
        |
atomic no-replace publication
        v
immutable V1.21 staging generation
```

No V1.20 production module is generalized. V1.21 may reuse the existing
version-independent `ImportFileEvidence`, `ImportCandidate`,
`ImportAdaptation`, `ImportIssue`, `ArtifactRef`, and `VerificationReport`.
Normalization, collision classification, canonical JSON, atomic publication,
and SQLite determinism must remain semantically identical, but V1.21 keeps its
own named public carriers and entry points.

## 4. Public carriers

V1.21 defines the following frozen dataclasses with the exact same field names,
order, runtime types, no-default policy, tuple copying, and validation shape as
their V1.20 counterparts, with every nested V1.20 type replaced by its V1.21
counterpart:

```text
V121BatchImportManifest
V121AdaptedImportPackage
V121ImportApproval
V121BatchLedgerEntry
V121EffectiveState
V121CandidateContract
V121PreflightRequest
V121ImportPreflightReport
V121ImportPreflightResult
V121ApprovedBatch
V121CandidateBuildRequest
V121CandidateVerificationRequest
V121CandidateArtifacts
```

`V121BatchImportManifest` retains the exact 18-field V1.20 order.
`V121ImportPreflightReport` retains the exact 34-field V1.20 order.
`V121CandidateContract` retains the exact 25-field V1.20 order. Other carriers
retain their historical counterpart order exactly.

## 5. Fixed V1.21 contract

```text
profile = V1.21
baseline_release_version = V1.20
baseline_question_count = 543
baseline_database_sha256 = b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292
baseline_database_size_bytes = 9768960
baseline_manifest_sha256 = 19ac2e43ded74a3f3eaf75c184b5eb231c9f1b0b152f5914cd822a321b045098
baseline_manifest_size_bytes = 6643
baseline_release_digest = 1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf
canonical_manifest_schema = task11-v121-import-manifest-v1
preflight_schema = task11-v121-preflight-v1
approval_schema = task11-v121-import-approval-v1
candidate_manifest_schema = task11-v121-candidate-manifest-v1
candidate_database_schema = task11-v121-candidate-v1
candidate_identity_schema = task11-v121-candidate-identity-v1
rollback_schema = task11-v121-rollback-v1
expected_user_version = 121
database_filename = Joy_M2_V1.21_candidate.sqlite3
manifest_filename = candidate_manifest.json
sha256s_filename = SHA256SUMS
rollback_filename = rollback.json
authority_root = authority/batches
image_root = images/sha256
required_baseline_view = formal_complete_questions_v120
required_candidate_tables = task11_v121_batch_ledger_v1,
  task11_v121_candidates_v1, task11_v121_images_v1,
  task11_v121_taxonomy_v1
required_candidate_views = task11_candidate_questions_v121
```

The deterministic V1.21 genesis digest is the SHA-256 of canonical JSON plus
one LF for the exact object:

```json
{"baseline_database_sha256":"b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292","baseline_question_count":543,"baseline_release_digest":"1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf","baseline_release_version":"V1.20","candidate_count":0,"schema":"task11-v121-genesis-v1","target_release_version":"V1.21"}
```

The computed digest is
`331192032f184a44ed383e6dacc2f06fbacb60ad94414298fcb935ff56cb5906`.
It is frozen by tests and must not reuse the V1.20 genesis.

## 6. Canonical package and HKDSE bridge

The new entry point is:

```python
adapt_verified_hkdse_pdf_transcription_v121(
    verified: VerifiedHkdsePdfTranscriptionBatch,
    output_dir: Path,
    config: PipelineConfig,
) -> V121AdaptedImportPackage
```

It accepts only an exact verified transcription carrier with an exact approval.
It preserves candidate/source/MS bytes and ordering, writes only below staging,
and atomically publishes the same five-file layout as V1.20. The manifest uses
`task11-v121-import-manifest-v1` and target `V1.21`. The historical V1.20 bridge
and its output bytes remain unchanged.

The strict loader is:

```python
load_v121_import_manifest(path: Path) -> V121BatchImportManifest
```

## 7. Authoritative preflight

```python
preflight_v121_import(
    request: V121PreflightRequest,
    config: PipelineConfig,
) -> V121ImportPreflightResult
```

Preflight is read-only. It validates the exact V1.20 baseline bytes, manifest,
schema metadata, integrity, foreign keys, and 543 ordered rows from
`formal_complete_questions_v120`. It then extends duplicate/collision indexes
with every independently verified parent V1.21 candidate batch before
classifying the incoming package.

The exact existing sixteen-code Task 9A/10A issue taxonomy and stable ordering
remain authoritative. No new issue code is introduced. Counts close as:

```text
before_count = 543 + parent candidate count
projected_after_count = before_count + incoming new count
```

The preflight digest binds exact baseline identity, target V1.21, parent digest,
batch/manifest/file evidence, ordered candidates, issues, classifications,
image evidence, and report.

## 8. Approval and stale-state protection

The only accepted statement is:

```text
USER APPROVED IMPORT BATCH <batch_id> <preflight_sha256> V1.21 PARENT <parent_candidate_digest>
```

Both preflight and approval carry the parent digest. An approval or preflight
against parent A is invalid once parent B is current. Historical V1.20 approval
types and syntax remain V1.20-only.

## 9. Candidate database and accumulation

The V1.21 writer copies the exact V1.20 formal SQLite into a private staging
sibling, preserves every baseline table/view/row, sets `user_version=121`, and
adds only:

```text
task11_v121_batch_ledger_v1
task11_v121_candidates_v1
task11_v121_images_v1
task11_v121_taxonomy_v1
task11_candidate_questions_v121
```

The candidate view is the ordered union of `formal_complete_questions_v120`
and V1.21 candidate rows. Candidate rows remain non-formal and non-selectable.
Each generation rebuilds the full ordered V1.21 batch prefix, verifies it in a
private root, and atomically publishes without replacing prior generations.
Failed append leaves the parent generation byte-identical.

The writer and verifier public APIs are:

```python
approve_v121_import(result, package_root, approval) -> V121ApprovedBatch
build_v121_candidate(request, config) -> V121CandidateArtifacts
verify_v121_candidate(request, config) -> VerificationReport
```

## 10. Independent verification and rollback

The verifier reopens all bytes read-only and checks candidate directory,
contract, baseline authority, batch authority artifacts, parent chain,
approval binding, preflight reconstruction, exact filesystem/SHA closure,
ArtifactRefs, rollback receipt, image projection, SQLite integrity/foreign
keys/schema, V1.20 preservation, ledger, candidate projection, effective
collision closure, counts, candidate digest, deterministic identity, and the
formal boundary. It never repairs or rewrites.

Rollback is declarative and may only delete the unpromoted V1.21 candidate
tree. It grants no authority to alter formal releases.

## 11. First real batch

The already-approved transcription is reused exactly:

```text
batch_id = JOY-M2-HKDSE-2015-PP-MS
transcription_digest = 41e284c25e41759f72debd192e58c00288d14a355e704978d80587c201e970fc
records = 12
issues = 0
status = VERIFIED
```

No OCR or transcription regeneration is allowed. If controlled taxonomy
requires semantic changes to the approved transcription payload, stop at the
existing taxonomy/transcription approval gate. Otherwise create the V1.21
canonical package and preflight against the V1.21 genesis.

## 12. File scope

Implementation is closed to:

```text
NEW       src/joy_m2/ingest/v121_models.py
NEW       src/joy_m2/ingest/v121_manifest.py
NEW       src/joy_m2/ingest/v121_preflight.py
NEW       src/joy_m2/ingest/v121_writer_profiles.py
NEW       src/joy_m2/ingest/v121_writer.py
NEW       src/joy_m2/ingest/v121_verification.py
MODIFIED  src/joy_m2/ingest/hkdse_pdf_adapter.py
MODIFIED  src/joy_m2/ingest/__init__.py
NEW       tests/unit/test_v121_models.py
NEW       tests/integration/test_v121_hkdse_bridge.py
NEW       tests/integration/test_v121_preflight.py
NEW       tests/integration/test_v121_candidate.py
NEW       tests/regression/test_v121_historical_replay.py
MODIFIED  tests/unit/test_v119_writer_models.py
MODIFIED  tests/unit/test_v119_promotion_models.py
MODIFIED  tests/regression/test_v119_historical_replay.py
MODIFIED  PROJECT_STATE.md
NEW       docs/reports/V121_CANDIDATE_AUTHORITY_VERIFICATION.md
NEW       docs/superpowers/specs/2026-09-18-v121-next-version-candidate-design.md
NEW       docs/superpowers/plans/2026-09-18-v121-next-version-candidate.md
```

Ignored real operational output may be written only below
`data/staging/task11-v121-hkdse-2015/**`. No fixture, project script, dependency,
CLI, formal release path, promotion module, or unrelated refactor is approved.
The three historical test modifications are limited to extending their exact
append-only `joy_m2.ingest.__all__` expectation with the approved V1.21 public
surface; their V1.19/V1.20 behavior assertions remain unchanged.

## 13. TDD, review, and completion gates

All new behavior follows RED then minimal GREEN. Tests must cover exact public
contracts, strict manifest loading, V1.21 bridge, baseline identity, genesis,
first/second batch, stale preflight/approval, formal and parent duplicates,
failed append preservation, deterministic replay, historical V1.20 replay, and
absence of `releases/V1.21/`.

Completion requires focused V1.21 tests, all maintained Task 9A–10C suites,
V1.18 validator, V1.19 verifier, V1.20 formal verifier, frozen hashes/counts,
zero skips/expected failures, `git diff --check`, independent review with
Critical 0 / Important 0, commits, and ordinary push.

## 14. Non-goals

- V1.21 formal release or promotion;
- modifying any historical release or API;
- V1.22 or arbitrary version support;
- generic migration DSL/plugin architecture;
- OCR or retranscription of the approved 2015 source;
- App/API/CLI work or new question generation.
