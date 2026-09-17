# Joy M2 AI Database — Task 10C Formal V1.20 Promotion Design

Date: 2026-09-17 (Asia/Shanghai)

Status: approved executable authority; formal publication pending final human gate

## 1. Purpose and boundary

Task 10C proves that the exact accumulated V1.20 candidate can be promoted from
formal V1.19 without changing any approved question content. It is the smallest
append-only V1.20 counterpart of Task 9D. It is not a generic release engine,
new ingest framework, or authority to continue ingesting later sources.

This Design authorizes models, tests, implementation, two deterministic
non-formal dry-runs, an independent verifier, rollback validation, review,
documentation, ordinary commits, and an ordinary push. It does **not** authorize
creation of `releases/V1.20/`. Until the exact final approval is received:

- formal current remains V1.19 at 502 questions;
- `releases/V1.20/` must remain absent, even transiently;
- all real promotion builds remain under `data/staging/`;
- no release pointer or index is created or changed;
- no 2015 or other source is ingested.

## 2. Exact promotion envelope

Only this candidate is eligible:

| Authority | Exact value |
|---|---|
| baseline | `V1.19` |
| baseline formal count | `502` |
| baseline SQLite SHA-256 | `5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff` |
| baseline release digest | `7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d` |
| candidate generation | `000003` |
| candidate directory | `data/staging/task10a-v120-real-candidate-000003-hkdse-2014` |
| candidate digest | `88cc945b6296652c88041e8e51a5c586300c2201a9f48e21abde80d97da3a7b3` |
| candidate SQLite SHA-256 | `d8ff5bf9e38f27e23e72c39ae41cb297b4223fde5d2bc149178a7033fe9769d1` |
| candidate SQLite size | `9662464` |
| candidate manifest SHA-256 | `673a598b7d5b59394ebaf1307943f90a293c165ecc7aa349c23c2947397f5052` |
| candidate manifest size | `5581` |
| accepted batch count | `3` |
| approved additions | `41` |
| projected formal count | `543` |

Older generations, reconstructed candidates, parallel carriers, or equivalent
content with different bytes/digest are ineligible.

## 3. Ledger closure

The builder and verifier independently reconstruct this ordered ledger:

1. `000001 — JOY-M2-HKDSE-2012-PP-MS — 14`, parent genesis
   `4ff624aca875b0191fe8a617516d2919c6d700ce69c5a3b5d236adcf7ecc59f1`;
2. `000002 — JOY-M2-HKDSE-2013-PP-MS — 14`, parent
   `e6b30bfc1553b4202db12db4fb3182eafeff7dcab0d4ef0acc7be6d33d3827a4`;
3. `000003 — JOY-M2-HKDSE-2014-PP-MS — 13`, parent
   `12a6a2409c33f3644648f6e2a9da327ce54e559e016afff48a32b0e22ff92856`.

The cumulative counts must be 14, 28, and 41; projected counts must be 516,
530, and 543. All preflight, approval, manifest, source/transcription, and batch
identities already stored by Task 10A remain immutable provenance.

## 4. Architecture

```text
exact V1.20 generation 000003 + its exact typed three-batch authority
    -> verify_v120_candidate (24/24 PASS)
    -> copy candidate SQLite into a private staging build tree
    -> add V1.20 promotion metadata and 41 published projections atomically
    -> retain Task 10A candidate and ledger tables as provenance evidence
    -> create formal_complete_questions_v120 (502 preserved + 41 promoted)
    -> write canonical manifest, rollback receipt, and SHA256SUMS.txt
    -> independently verify the complete release tree
    -> atomic no-replace rename to a non-formal staging dry-run root

verified dry-run + exact final human approval
    -> copy exact verified bytes to a private sibling of releases/V1.20
    -> byte-compare and independently verify
    -> atomic no-replace rename to releases/V1.20
```

The second path is implemented and tested only in isolated temporary repository
roots. It is not invoked against this repository during readiness work.

## 5. Public contracts

Create versioned Task 10C modules without modifying Task 9D behavior:

```python
@dataclass(frozen=True)
class V120PromotionContract:
    profile: str
    release_manifest_schema: str
    formal_database_schema: str
    promotion_identity_schema: str
    rollback_schema: str
    expected_user_version: int
    database_filename: str
    manifest_filename: str
    sha256s_filename: str
    rollback_filename: str
    image_root: str
    promoted_table: str
    promotion_table: str
    formal_view: str

@dataclass(frozen=True)
class V120PromotionBuildRequest:
    candidate: V120CandidateVerificationRequest
    output_dir: Path
    contract: V120PromotionContract

@dataclass(frozen=True)
class V120PromotionVerificationRequest:
    release_dir: Path
    candidate: V120CandidateVerificationRequest
    contract: V120PromotionContract

@dataclass(frozen=True)
class V120ReleasePromotionApproval:
    release_version: str
    release_digest: str
    statement: str

@dataclass(frozen=True)
class V120PublicationRequest:
    dry_run_dir: Path
    candidate: V120CandidateVerificationRequest
    approval: V120ReleasePromotionApproval
    contract: V120PromotionContract

@dataclass(frozen=True)
class V120PromotionArtifacts:
    database: ArtifactRef
    manifest: ArtifactRef
    sha256sums: ArtifactRef
    rollback: ArtifactRef
    images: tuple[ArtifactRef, ...]
    release_digest: str
    verification_report: VerificationReport
```

The exact contract values are:

```text
V1.20
task10-v120-formal-manifest-v1
task10-v120-formal-v1
task10-v120-promotion-identity-v1
task10-v120-formal-rollback-v1
120
Joy_M2_Complete_Question_DB_V1_20.sqlite3
manifest.json
SHA256SUMS.txt
rollback.json
images/sha256
task10_v120_promoted_questions_v1
task10_v120_promotion_v1
formal_complete_questions_v120
```

Public APIs:

```python
build_v120_promotion(request, config) -> V120PromotionArtifacts
verify_v120_promotion(request, config) -> VerificationReport
publish_v120_release(request, config) -> V120PromotionArtifacts
```

These six carriers and three APIs are appended to `joy_m2.ingest.__all__` in
the order shown. Existing exports remain an exact unchanged prefix.

## 6. Final promotion gate

The release digest is the lowercase SHA-256 of canonical JSON for the exact
promotion identity. Publication requires:

```text
USER APPROVED RELEASE PROMOTION V1.20 <release_digest>
```

The approval must be an exact `V120ReleasePromotionApproval` and must bind the
dry-run digest. Import approvals cannot substitute for it. This repository's
publication API is not called before the user provides that exact statement.

## 7. Formal database semantics

The copied database retains immutable V1.19 and Task 10A provenance tables.
One transaction adds:

- `task10_v120_promotion_v1`: exact release/candidate/count/ledger authority;
- `task10_v120_promoted_questions_v1`: exact 41-row projection;
- `formal_complete_questions_v120`: ordered 543-row formal view.

The formal view is the exact 502 rows of `formal_complete_questions_v119`
followed by exact Task 10A candidates 503–543. For the 41 new rows only:

- `record_status` changes from `candidate` to `published`;
- `selectable` changes from `0` to `1`;
- `authority_kind` becomes `task10_v120_promoted`.

Every other field is byte/value identical. All 543 formal rows are published
and selectable. Existing V1.19 rows, IDs, text, solutions, provenance,
taxonomy, hashes, and image identities are not enriched or rewritten.

## 8. Formal artifact contract

The exact release tree contains only:

```text
Joy_M2_Complete_Question_DB_V1_20.sqlite3
manifest.json
SHA256SUMS.txt
rollback.json
images/sha256/...  # only if referenced by the exact candidate
```

Canonical JSON is UTF-8, sorted keys, compact separators, no NaN, one terminal
LF. `SHA256SUMS.txt` is path-sorted, excludes itself, and binds every other
artifact. The manifest binds baseline, exact candidate, ordered ledger,
database byte and semantic identities, counts, artifacts, and verifier contract.

## 9. Deterministic identities

The SQLite semantic digest covers normalized schema plus all application tables
and views in deterministic order. The release digest covers the exact contract,
baseline authority, candidate authority, ledger, counts, database byte SHA and
semantic digest, images, and rollback action. It excludes absolute paths,
temporary roots, mtimes, and host state.

Two independent builds from equivalent roots must have byte-identical SQLite,
manifest, sums, rollback, image bytes, ArtifactRefs, semantic digest, and
release digest. No weaker semantic-only exception is authorized.

## 10. Independent verifier

The verifier is read-only and returns these ordered checks:

```text
release_directory
promotion_contract
candidate_verification
candidate_binding
manifest_contract
filesystem_closure
sha256sums_closure
artifact_references
rollback_contract
sqlite_readability
sqlite_integrity
sqlite_foreign_keys
sqlite_schema
v119_preservation
batch_ledger_closure
promotion_projection
formal_query
count_closure
provenance_closure
deterministic_identity
publication_boundary
```

Parsed corruption produces structured FAIL. Malformed JSON follows the existing
input-format exception boundary. Verification never repairs or mutates.

## 11. Rollback and atomicity

Before publication, failure discards only the private unpublished tree. The
rollback receipt is declarative and authorizes only removal of the V1.20 release
tree if its exact release digest still matches. It never rewrites V1.19,
V1.18, a candidate generation, or a source package. Existing targets conflict;
no overwrite, merge, or destructive automatic rollback is allowed.

## 12. Closed file scope

Implementation may create:

- `src/joy_m2/ingest/v120_promotion_models.py`
- `src/joy_m2/ingest/v120_promotion.py`
- `src/joy_m2/ingest/v120_promotion_verification.py`
- `tests/unit/test_v120_promotion_models.py`
- `tests/unit/test_v120_promotion_primitives.py`
- `tests/integration/test_v120_promotion.py`

It may minimally modify:

- `src/joy_m2/ingest/__init__.py`
- exact public-surface expectations in maintained ingest model/API tests.

Completion may modify `PROJECT_STATE.md` and create
`docs/reports/TASK10C_VERIFICATION.md`. No other production, test, formal,
source, candidate, legacy, data, or release file is authorized. Generated
dry-run roots remain ignored staging evidence and are never committed.

## 13. TDD and exit gate

1. Establish public-contract RED; implement only carriers/signature scaffolds.
2. Establish primitive, builder, verifier, determinism, rollback, and isolated
   publication RED against those scaffolds.
3. Verify all RED failures are missing Task 10C behavior.
4. Implement the minimum behavior; run focused GREEN.
5. Build two real non-formal dry-runs and independently verify both.
6. Prove byte identity, rollback safety, V1.18/V1.19 immutability, current
   candidate 24/24 PASS, and `releases/V1.20/` absence.
7. Run all maintained gates and independent review to Critical 0 / Important 0.
8. Commit and ordinarily push readiness code/evidence.
9. Stop at the exact final human gate. Formal publication remains unexecuted.
