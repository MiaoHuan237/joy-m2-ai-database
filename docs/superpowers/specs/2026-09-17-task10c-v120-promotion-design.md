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
- Task 10C never creates or updates any release pointer or index, before or
  after publication; consumer/current-release selection remains out of scope;
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
    -> re-verify the exact public staging dry-run
    -> copy to a private sibling of releases/V1.20
    -> compare the complete private tree byte-for-byte with the dry-run
    -> atomic no-replace rename to releases/V1.20
    -> independently verify only the exact formal target
```

The private sibling is never accepted as a public verifier root. Before rename,
failure removes only that newly created private sibling. After rename, a failed
post-verification may remove the formal target only when its release digest
matches and its complete fingerprint equals the approved dry-run: the exact
relative-path set is identical, every entry is a regular file (no symlink or
other type), and every file is byte-for-byte identical. Otherwise the target is
retained for manual recovery. The second path is implemented and tested
only in isolated temporary repository roots. It is not invoked against this
repository during readiness work.

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

### 7.1 Exact promotion metadata DDL

Modulo ASCII whitespace and an optional terminal semicolon, the DDL is:

```sql
CREATE TABLE task10_v120_promotion_v1 (
    release_version TEXT PRIMARY KEY CHECK(release_version='V1.20'),
    formal_database_schema TEXT NOT NULL CHECK(formal_database_schema='task10-v120-formal-v1'),
    release_model TEXT NOT NULL CHECK(release_model='append-only-multi-batch-promotion'),
    release_status TEXT NOT NULL CHECK(release_status='published'),
    baseline_release_version TEXT NOT NULL CHECK(baseline_release_version='V1.19'),
    baseline_database_sha256 TEXT NOT NULL CHECK(baseline_database_sha256='5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff'),
    baseline_release_digest TEXT NOT NULL CHECK(baseline_release_digest='7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d'),
    baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count=502),
    candidate_digest TEXT NOT NULL CHECK(candidate_digest='88cc945b6296652c88041e8e51a5c586300c2201a9f48e21abde80d97da3a7b3'),
    candidate_database_sha256 TEXT NOT NULL CHECK(candidate_database_sha256='d8ff5bf9e38f27e23e72c39ae41cb297b4223fde5d2bc149178a7033fe9769d1'),
    candidate_database_size INTEGER NOT NULL CHECK(candidate_database_size=9662464),
    candidate_manifest_sha256 TEXT NOT NULL CHECK(candidate_manifest_sha256='673a598b7d5b59394ebaf1307943f90a293c165ecc7aa349c23c2947397f5052'),
    candidate_manifest_size INTEGER NOT NULL CHECK(candidate_manifest_size=5581),
    accepted_batch_count INTEGER NOT NULL CHECK(accepted_batch_count=3),
    promoted_question_count INTEGER NOT NULL CHECK(promoted_question_count=41),
    formal_question_count INTEGER NOT NULL CHECK(formal_question_count=543)
)
```

Integer fields require exact Python/JSON integers, not booleans, at every model,
manifest, identity, and verifier boundary.

### 7.2 Exact promoted table DDL

```sql
CREATE TABLE task10_v120_promoted_questions_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal BETWEEN 1 AND 3),
    batch_id TEXT NOT NULL,
    batch_candidate_order INTEGER NOT NULL CHECK(batch_candidate_order>=0),
    formal_order INTEGER PRIMARY KEY CHECK(formal_order BETWEEN 503 AND 543),
    question_id TEXT NOT NULL UNIQUE,
    source_id TEXT NOT NULL,
    source_question_number TEXT NOT NULL,
    source_section TEXT NOT NULL,
    source_fragment_hash TEXT NOT NULL,
    normalized_text_sha256 TEXT NOT NULL,
    question_text_original TEXT NOT NULL,
    question_text_zh TEXT NOT NULL,
    translation_status TEXT NOT NULL CHECK(translation_status IN ('source_present','ai_proposed','verified','missing')),
    translation_evidence TEXT,
    solution_original TEXT NOT NULL,
    solution_verified TEXT NOT NULL,
    answer_status TEXT NOT NULL CHECK(answer_status IN ('source_provided','ai_solved_verified','missing_from_source')),
    explanation_text TEXT NOT NULL,
    explanation_status TEXT NOT NULL CHECK(explanation_status IN ('source_present','ai_proposed','verified','missing')),
    explanation_evidence TEXT,
    source_image_paths_json TEXT NOT NULL,
    source_image_sha256s_json TEXT NOT NULL,
    source_image_roles_json TEXT NOT NULL,
    primary_type TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    tag_status TEXT NOT NULL CHECK(tag_status IN ('source_provided','proposed','missing')),
    difficulty_level INTEGER CHECK(difficulty_level BETWEEN 1 AND 5 OR difficulty_level IS NULL),
    difficulty_status TEXT NOT NULL CHECK(difficulty_status IN ('source_provided','proposed','missing')),
    enrichment_status TEXT NOT NULL CHECK(enrichment_status IN ('complete','incomplete')),
    formal_image_paths_json TEXT NOT NULL,
    record_status TEXT NOT NULL CHECK(record_status='published'),
    selectable INTEGER NOT NULL CHECK(selectable=1),
    UNIQUE(batch_ordinal,batch_candidate_order),
    FOREIGN KEY(batch_ordinal,batch_id)
        REFERENCES task10_v120_batch_ledger_v1(batch_ordinal,batch_id)
)
```

Rows are selected from `task10_v120_candidates_v1 ORDER BY aggregate_order`.
The mapping is exact:

```text
batch_ordinal -> batch_ordinal
batch_id -> batch_id
batch_candidate_order -> batch_candidate_order
aggregate_order -> formal_order
proposed_question_id -> question_id
image_paths_json -> source_image_paths_json
image_sha256s_json -> source_image_sha256s_json
image_roles_json -> source_image_roles_json
candidate_image_paths_json -> formal_image_paths_json
record_status -> literal published
selectable -> exact integer 1
```

All intervening source/content/provenance/taxonomy/enrichment columns preserve
their candidate value and order exactly. There are exactly 41 rows, formal
orders 503..543, batch counts 14/14/13, and no duplicate formal order or ID.

### 7.3 Exact formal view

The view has the existing 33-column order of
`formal_complete_questions_v119`. Its SQL is:

```sql
CREATE VIEW formal_complete_questions_v120 AS
SELECT * FROM formal_complete_questions_v119
UNION ALL
SELECT
    p.formal_order,
    p.question_id,
    'task10_v120_promoted' AS authority_kind,
    p.batch_id,
    p.batch_candidate_order AS candidate_order,
    p.source_id,
    p.source_question_number,
    p.source_section,
    p.source_fragment_hash,
    p.normalized_text_sha256,
    p.question_text_original,
    p.question_text_zh,
    CAST(NULL AS TEXT) AS question_text_zh_reviewed,
    p.translation_status,
    p.translation_evidence,
    p.solution_original,
    p.solution_verified,
    p.answer_status,
    p.explanation_text,
    p.explanation_status,
    p.explanation_evidence,
    p.source_image_paths_json,
    p.source_image_sha256s_json,
    p.source_image_roles_json,
    p.primary_type,
    p.tags_json,
    p.tag_status,
    p.difficulty_level,
    p.difficulty_status,
    p.enrichment_status,
    p.formal_image_paths_json,
    p.record_status,
    p.selectable
FROM task10_v120_promoted_questions_v1 AS p
ORDER BY formal_order
```

The first 502 rows must equal `formal_complete_questions_v119` in all 33
columns. The last 41 must equal the candidate view after only the three
authority changes listed above.

### 7.4 Exact `release_metadata_v2` delta

In the same transaction, exactly these keys are inserted or updated:

```text
release_version = V1.20
baseline_version = V1.19
baseline_sqlite_sha256 = 5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff
release_model = append-only-multi-batch-promotion
schema_version = task10-v120-formal-v1
formal_question_count = 543
task10_baseline_release_digest = 7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d
task10_candidate_digest = 88cc945b6296652c88041e8e51a5c586300c2201a9f48e21abde80d97da3a7b3
task10_candidate_sqlite_sha256 = d8ff5bf9e38f27e23e72c39ae41cb297b4223fde5d2bc149178a7033fe9769d1
task10_candidate_manifest_sha256 = 673a598b7d5b59394ebaf1307943f90a293c165ecc7aa349c23c2947397f5052
task10_accepted_batch_count = 3
task10_promoted_questions = 41
```

All other metadata keys and values, including the historical `task9_*` keys,
remain exact. `PRAGMA user_version` remains the approved exact integer `120`.

## 8. Formal artifact contract

The exact release tree contains only:

```text
Joy_M2_Complete_Question_DB_V1_20.sqlite3
manifest.json
SHA256SUMS.txt
rollback.json
images/sha256/...  # only if referenced by the exact candidate
```

Canonical JSON is UTF-8 with `ensure_ascii=False`, sorted keys, compact
separators, `allow_nan=False`, and exactly one terminal LF. This same byte rule
applies to files, the SQLite semantic payload, and the promotion identity.
`SHA256SUMS.txt` uses one lowercase digest, two ASCII spaces, and one
canonical relative path per LF-terminated line; lines are ordered by UTF-8 path
bytes, exclude `SHA256SUMS.txt` itself, and bind every other artifact.

The manifest is one exact mapping with these keys:

```text
schema_version, release_version, release_status, release_model,
database_schema, baseline, candidate, batch_ledger,
batch_authority_artifacts, counts, database, images, artifacts,
rollback, promotion, verification
```

The complete nested schema below is exact. `str` values are non-empty unless a
literal is shown; `sha256` is lowercase 64-hex; every `int` is exact int and
rejects bool; `relative_path` is canonical POSIX-relative and rejects empty,
absolute, dot, dot-dot, backslash, NUL, and non-normalized forms. Mappings reject
missing and extra keys.

```text
manifest = {
  schema_version: "task10-v120-formal-manifest-v1",
  release_version: "V1.20",
  release_status: "published",
  release_model: "append-only-multi-batch-promotion",
  database_schema: "task10-v120-formal-v1",
  baseline: {
    release_version: "V1.19", question_count: 502,
    release_digest: "7246...69d", database_schema: "task9-v119-formal-v1",
    sqlite: {kind: "sqlite", sha256: "5a7f...0ff", size_bytes: 9478144},
    manifest: {kind: "manifest", sha256: "cd04...510", size_bytes: 3242}
  },
  candidate: {
    generation: 3, release_version: "V1.20", release_status: "candidate",
    database_schema: "task10-v120-candidate-v1",
    candidate_digest: "88cc...7b3",
    sqlite: {kind: "sqlite", sha256: "d8ff...9d1", size_bytes: 9662464},
    manifest: {kind: "manifest", sha256: "673a...052", size_bytes: 5581}
  },
  batch_ledger: [<the exact three candidate-manifest ledger mappings>],
  batch_authority_artifacts: [
    {kind: "approval"|"preflight", relative_path: relative_path,
     sha256: sha256, size_bytes: int}
  ],
  counts: {baseline_question_count: 502, accepted_batch_count: 3,
           promoted_question_count: 41, formal_question_count: 543},
  database: {kind: "sqlite",
             relative_path: "Joy_M2_Complete_Question_DB_V1_20.sqlite3",
             sha256: sha256, size_bytes: int, semantic_sha256: sha256},
  images: [{kind: "image", relative_path: relative_path,
            sha256: sha256, size_bytes: int}],
  artifacts: [{kind: "sqlite"|"rollback"|"image",
               relative_path: relative_path, sha256: sha256, size_bytes: int}],
  rollback: {kind: "rollback", relative_path: "rollback.json",
             sha256: sha256, size_bytes: int},
  promotion: {formal_target: "releases/V1.20", gate: "FINAL",
              release_digest: sha256,
              required_statement:
                "USER APPROVED RELEASE PROMOTION V1.20 <release_digest>"},
  verification: {authority: "verify_v120_promotion",
                 check_names: [<exact section-10 order>],
                 required_status: "PASS"}
}
```

Shortened literal digests above (`7246...69d`, etc.) mean the full exact values
in section 2, never the shortened display text. `batch_ledger` is the exact
ordered three-object array from the candidate manifest, with no field removed
or rewritten. `batch_authority_artifacts` is likewise the exact ordered six
preflight/approval projections, including relative path, kind, SHA, and size.
`counts` is exactly baseline 502, batches 3, promoted 41, formal 543. `database`
adds `semantic_sha256` to its ArtifactRef projection. `images` is the exact
path-sorted candidate image projection. `artifacts` is database, rollback, then
images in canonical relative-path order. `promotion` contains formal target,
gate, release digest, and required statement. `verification` contains authority,
the exact 21 check names, and required status PASS. No unspecified key is valid.

This embeds the exact ordered content/hash/size/kind projections of all six
Task 10A authority artifacts. `provenance_closure` also re-verifies the candidate
24/24 using those typed approved batches and proves each promoted row's
batch/source identity maps to ledger year 2012, 2013, or 2014. The formal tree
does not duplicate the six files because the independently verified candidate
is the immutable source; its manifest cryptographically binds them.

## 9. Deterministic identities

The SQLite semantic payload is one exact mapping:

```text
schema_version = task10-v120-sqlite-semantic-v1
user_version = 120
schema_objects = ordered array
relations = ordered array
```

`schema_objects` contains every non-`sqlite_%` row from `sqlite_master`, ordered
by `(type,name)`, projected as `type,name,table_name,sql`. SQL is normalized by
collapsing only ASCII space/tab/CR/LF/form-feed/vertical-tab runs to one space,
trimming outer ASCII space, and removing one optional terminal semicolon.
`relations` contains every non-internal table ordered by name followed once by
`formal_complete_questions_v120`. Each relation stores `name`, PRAGMA column
order, and rows. Tables order rows by their primary-key columns in PK ordinal,
or all columns when no PK exists; the formal view orders by `formal_order`.
SQLite values project as JSON null, exact int, finite float, string, or
`{"blob_hex":"<lowercase hex>"}`. Canonical JSON bytes of this mapping determine
the semantic SHA-256.

The promotion identity mapping is exactly:

```text
identity = {
  schema_version: "task10-v120-promotion-identity-v1",
  release_version: "V1.20",
  contract: {<the exact 14 V120PromotionContract fields and literal values>},
  baseline: <the exact manifest baseline mapping>,
  candidate: <the exact manifest candidate mapping>,
  batch_ledger: <the exact manifest ordered ledger array>,
  batch_authority_artifacts: <the exact manifest ordered authority array>,
  counts: <the exact manifest counts mapping>,
  formal_sqlite_sha256: sha256,
  formal_sqlite_size_bytes: int,
  formal_sqlite_semantic_sha256: sha256,
  images: <the exact manifest ordered image array>,
  rollback_action: "remove_release_tree_if_release_digest_matches"
}
```

`contract` is the exact 14-field contract mapping in dataclass field order;
baseline/candidate/ledger/authority/count/image values equal the manifest
projections defined above; `rollback_action` is the exact literal
`remove_release_tree_if_release_digest_matches`. The lowercase SHA-256 of its
canonical JSON bytes is the release digest. Absolute paths, temporary roots,
mtimes, and host state are excluded. Both digest fields are lowercase 64-hex;
`formal_sqlite_size_bytes` is an exact nonnegative integer and rejects bool.

The rollback mapping is exactly:

```text
rollback = {
  schema_version: "task10-v120-formal-rollback-v1",
  release_version: "V1.20",
  release_digest: sha256,
  action: "remove_release_tree_if_release_digest_matches",
  protected_baseline: {
    release_version: "V1.19", question_count: 502,
    sqlite_sha256: "5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff",
    release_digest: "7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d"
  },
  candidate_digest:
    "88cc945b6296652c88041e8e51a5c586300c2201a9f48e21abde80d97da3a7b3",
  release_artifacts: [relative_path]
}
```

Its schema/action are the exact contract literals. `protected_baseline` is the
exact V1.19 release version, count 502, SQLite SHA, and release digest.
`candidate_digest` is the exact generation-000003 digest. `release_artifacts`
is the UTF-8-path-sorted list of database, `SHA256SUMS.txt`, manifest, rollback,
and every image relative path.

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

All path decisions use resolved containment plus lexical symlink inspection.
Build output must be a new strict descendant of the configured real
`data/staging` root; the staging root, output leaf, and every existing ancestor
between repository and output must not be symlinks. Output must not equal,
contain, or be contained by V1.18, V1.19, any of the three candidate roots, any
canonical source package, or `releases/V1.20`. Verification accepts only a
strict staging descendant or the exact resolved formal target; it rejects a
private publication sibling and all symlink roots/ancestors. Publication derives
the formal target only through `config.new_formal_target("V1.20")`, rejects an
existing target, and requires real parent `releases/` with no symlink component.
Focused negatives permanently lock every containment, overlap, and symlink rule.

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
- `tests/unit/test_v119_writer_models.py`
- `tests/unit/test_v119_promotion_models.py`
- `tests/regression/test_v119_historical_replay.py`
- `tests/integration/test_hkdse_pdf_adapter.py`

Completion may modify `PROJECT_STATE.md` and create
`docs/reports/TASK10C_VERIFICATION.md`. No other production, test, formal,
source, candidate, legacy, data, or release file is authorized. Generated
dry-run roots remain ignored staging evidence and are never committed.

The historical reporting typo search is read-only. No persistent accessor is
currently known. If one is found, implementation stops for a Design scope
amendment naming the exact production and regression-test files; this scope
does not implicitly authorize such a fix.

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
