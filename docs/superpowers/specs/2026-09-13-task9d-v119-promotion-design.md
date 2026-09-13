# Joy M2 AI Database — Task 9D Formal V1.19 Promotion Design

Date: 2026-09-13 (Asia/Shanghai)

Status: proposed executable authority, pending independent Design review

## 1. Purpose and hard boundary

Task 9D promotes exactly one independently verified, import-approved Task 9C
candidate into a deterministic formal V1.19 release. It does not parse source
material, classify duplicates, enrich records, rewrite mathematics, or create a
second import authority.

This Design authorizes reversible engineering, tests, and real-candidate
promotion dry-runs. It does **not** authorize creation of `releases/V1.19/`.
Formal publication remains HUMAN GATE D. Until that exact approval is received:

- V1.18 remains the current formal authority at 497 questions;
- `releases/V1.19/` must remain absent, including transient creation followed by
  deletion;
- no current-release pointer, release index, or production lookup may change;
- every real-candidate Task 9D output must remain under `data/staging/`.

Task 9D consumes the already completed Task 9A, Task 9B, and Task 9C contracts.
Import approval is evidence only and never implies promotion approval.

## 2. Exact real authority envelope

The first Task 9D release is closed to this exact authority:

| Authority | Exact value |
|---|---|
| baseline release | `V1.18` |
| baseline SQLite SHA-256 | `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7` |
| baseline formal count | `497` |
| candidate SQLite SHA-256 | `9d30cf444e9d6686128f884d5a3cf57f4e58ce544b7933d7a0a47ec0e8212d20` |
| candidate manifest SHA-256 | `b2e0b4607b49f5e1e097fd036dd0614c67128976e7d282f4e2783eb092be9634` |
| batch ID | `TASK9B-REAL-0918-INTERVAL-REPRODUCTION-001` |
| preflight SHA-256 | `4aa3ff8b419a0fcca57c805d5f10f252658cb30c00f6cf1b74c95ab3009333c9` |
| approved additions | `5` |
| projected formal count | `502` |

The exact import statement retained as evidence is:

```text
USER APPROVED IMPORT BATCH TASK9B-REAL-0918-INTERVAL-REPRODUCTION-001 4aa3ff8b419a0fcca57c805d5f10f252658cb30c00f6cf1b74c95ab3009333c9 V1.19
```

Production code is contract-driven and may be tested with synthetic temporary
authority, but the repository dry-run must use only the real envelope above.

## 3. Architecture

```text
V1.18 frozen SQLite + exact Task 9C verification request
    -> independently verify candidate and import approval
    -> copy candidate SQLite into a private staging build root
    -> transactionally add the V1.19 formal projection
    -> preserve the candidate tables as immutable provenance evidence
    -> write deterministic manifest, rollback receipt, and SHA256SUMS.txt
    -> independently verify complete release tree
    -> atomic no-replace rename to a non-formal staging dry-run root

verified dry-run + exact Gate D approval
    -> copy exact bytes into a private sibling of releases/V1.19
    -> compare exact bytes with the already verified dry-run
    -> atomic no-replace rename to releases/V1.19
    -> verify the exact formal root
```

Build, verification, and publication are separate operations. The first path is
authorized now. The second path is implemented and tested only in isolated
temporary repositories; it must not be invoked against this repository before
Gate D.

## 4. Public carriers

All carriers below are exact, frozen dataclasses. Exact runtime types are
required; mappings, subclasses, path-like objects, or parallel authority
carriers are rejected rather than coerced.

### 4.1 `V119PromotionContract`

```python
@dataclass(frozen=True)
class V119PromotionContract:
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
```

The only approved values are, in field order:

```text
V1.19
task9-v119-formal-manifest-v1
task9-v119-formal-v1
task9-v119-promotion-identity-v1
task9-v119-formal-rollback-v1
119
Joy_M2_Complete_Question_DB_V1_19.sqlite3
manifest.json
SHA256SUMS.txt
rollback.json
images/sha256
task9_promoted_questions_v1
task9_promotion_v1
formal_complete_questions_v119
```

### 4.2 Requests and results

```python
@dataclass(frozen=True)
class V119PromotionBuildRequest:
    candidate: V119VerificationRequest
    output_dir: Path
    contract: V119PromotionContract

@dataclass(frozen=True)
class V119PromotionVerificationRequest:
    release_dir: Path
    candidate: V119VerificationRequest
    contract: V119PromotionContract

@dataclass(frozen=True)
class ReleasePromotionApproval:
    release_version: str
    release_digest: str
    statement: str

@dataclass(frozen=True)
class V119PublicationRequest:
    dry_run_dir: Path
    candidate: V119VerificationRequest
    approval: ReleasePromotionApproval
    contract: V119PromotionContract

@dataclass(frozen=True)
class V119PromotionArtifacts:
    database: ArtifactRef
    manifest: ArtifactRef
    sha256sums: ArtifactRef
    rollback: ArtifactRef
    images: tuple[ArtifactRef, ...]
    release_digest: str
    verification_report: VerificationReport
```

Paths resolve defensively. Image artifacts are exact `ArtifactRef(kind="image")`
values ordered by release-relative path. The result owns no approval authority.

### 4.3 Public APIs

```python
def build_v119_promotion(
    request: V119PromotionBuildRequest,
    config: PipelineConfig,
) -> V119PromotionArtifacts

def verify_v119_promotion(
    request: V119PromotionVerificationRequest,
    config: PipelineConfig,
) -> VerificationReport

def publish_v119_release(
    request: V119PublicationRequest,
    config: PipelineConfig,
) -> V119PromotionArtifacts
```

`build_v119_promotion()` accepts only a new strict descendant of
`PipelineConfig.staging_root`. `publish_v119_release()` derives the only formal
target through `config.new_formal_target("V1.19")`; no caller-supplied formal
target is accepted.

The new names are appended to `joy_m2.ingest.__all__` in this exact order:

```text
V119PromotionContract
V119PromotionBuildRequest
V119PromotionVerificationRequest
ReleasePromotionApproval
V119PublicationRequest
V119PromotionArtifacts
build_v119_promotion
verify_v119_promotion
publish_v119_release
```

Existing Task 9A/9B/9C exports and order remain unchanged.

## 5. Gate D authority

The release digest is a lowercase SHA-256 over canonical JSON bytes of the
exact promotion-identity payload defined in section 9. It is known only after a
successful dry-run.

The exact approval syntax is:

```text
USER APPROVED RELEASE PROMOTION V1.19 <release_digest>
```

`ReleasePromotionApproval` accepts only `release_version == "V1.19"`, a
lowercase 64-hex digest, and the exact one-line statement above. CR/LF, wrong
version, wrong digest, subclasses, or reconstructed lookalikes are rejected
with `PromotionError`.

Neither `ImportApproval`, candidate existence, candidate verification PASS,
dry-run verification PASS, nor knowledge of the release digest authorizes
publication. Only the exact new user statement does.

## 6. Formal SQLite model

The formal database starts as an exact byte copy of the verified Task 9C
candidate SQLite. One deterministic transaction then performs only these
changes:

1. create `task9_promotion_v1`;
2. create `task9_promoted_questions_v1`;
3. insert exactly one promotion row and exactly five formal rows in candidate
   order;
4. create `formal_complete_questions_v119`;
5. update existing `release_metadata_v2` to V1.19 release identity;
6. retain `PRAGMA user_version = 119`.

No row, schema SQL, table, view, or index inherited from frozen V1.18 is
modified except the explicitly versioned `release_metadata_v2` key values. In
particular, all 497 `complete_questions_v2` rows remain exactly equal in all 55
columns. The Task 9C candidate tables remain unchanged as provenance evidence;
they are not a formal query source.

### 6.1 Promotion metadata table

`task9_promotion_v1` has this exact column order:

```text
release_version
formal_database_schema
release_model
release_status
baseline_release_version
baseline_database_sha256
baseline_question_count
candidate_database_sha256
candidate_manifest_sha256
batch_id
preflight_sha256
import_approval_statement
promoted_question_count
formal_question_count
```

It contains exactly one row. Fixed values are `V1.19`,
`task9-v119-formal-v1`, `incremental-import-promotion`, `published`, `V1.18`,
497, 5, and 502 where applicable. Digest and count constraints are enforced by
DDL.

Its exact DDL, modulo insignificant SQL whitespace, is:

```sql
CREATE TABLE task9_promotion_v1 (
    release_version TEXT PRIMARY KEY CHECK(release_version='V1.19'),
    formal_database_schema TEXT NOT NULL CHECK(formal_database_schema='task9-v119-formal-v1'),
    release_model TEXT NOT NULL CHECK(release_model='incremental-import-promotion'),
    release_status TEXT NOT NULL CHECK(release_status='published'),
    baseline_release_version TEXT NOT NULL CHECK(baseline_release_version='V1.18'),
    baseline_database_sha256 TEXT NOT NULL CHECK(length(baseline_database_sha256)=64 AND baseline_database_sha256 NOT GLOB '*[^0-9a-f]*'),
    baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count=497),
    candidate_database_sha256 TEXT NOT NULL CHECK(length(candidate_database_sha256)=64 AND candidate_database_sha256 NOT GLOB '*[^0-9a-f]*'),
    candidate_manifest_sha256 TEXT NOT NULL CHECK(length(candidate_manifest_sha256)=64 AND candidate_manifest_sha256 NOT GLOB '*[^0-9a-f]*'),
    batch_id TEXT NOT NULL UNIQUE,
    preflight_sha256 TEXT NOT NULL CHECK(length(preflight_sha256)=64 AND preflight_sha256 NOT GLOB '*[^0-9a-f]*'),
    import_approval_statement TEXT NOT NULL,
    promoted_question_count INTEGER NOT NULL CHECK(promoted_question_count=5),
    formal_question_count INTEGER NOT NULL CHECK(formal_question_count=baseline_question_count+promoted_question_count AND formal_question_count=502)
)
```

### 6.2 Promoted-question table

`task9_promoted_questions_v1` has this exact column order:

```text
batch_id
candidate_order
formal_order
question_id
source_id
source_question_number
source_section
source_fragment_hash
normalized_text_sha256
question_text_original
question_text_zh
translation_status
translation_evidence
solution_original
solution_verified
answer_status
explanation_text
explanation_status
explanation_evidence
source_image_paths_json
source_image_sha256s_json
source_image_roles_json
primary_type
tags_json
tag_status
difficulty_level
difficulty_status
enrichment_status
formal_image_paths_json
record_status
selectable
```

Candidate fields are copied without content transformation. Only authority
projection changes:

- `proposed_question_id -> question_id`;
- candidate orders `0..4` become formal orders `498..502`;
- source image arrays retain exact source evidence;
- `candidate_image_paths_json -> formal_image_paths_json` without path change;
- `record_status` becomes exact `published`;
- `selectable` becomes exact integer `1`.

The table rejects ID collision with the 497 baseline IDs before any output is
published. It retains exact nullable enrichment semantics. In particular the
real five rows remain:

- `explanation_status = "missing"` and empty explanation text;
- `tags_json = "[]"` and `tag_status = "missing"`;
- `difficulty_level IS NULL` and `difficulty_status = "missing"`;
- `enrichment_status = "incomplete"`;
- unchanged primary type, question text, answer text, answer status,
  translation provenance, and source provenance.

Missing enrichment is valid release data, not a promotion blocker.

Its exact DDL, modulo insignificant SQL whitespace, is:

```sql
CREATE TABLE task9_promoted_questions_v1 (
    batch_id TEXT NOT NULL REFERENCES task9_promotion_v1(batch_id),
    candidate_order INTEGER NOT NULL CHECK(candidate_order BETWEEN 0 AND 4),
    formal_order INTEGER PRIMARY KEY CHECK(formal_order BETWEEN 498 AND 502),
    question_id TEXT NOT NULL UNIQUE,
    source_id TEXT NOT NULL,
    source_question_number TEXT NOT NULL,
    source_section TEXT NOT NULL,
    source_fragment_hash TEXT NOT NULL CHECK(length(source_fragment_hash)=64 AND source_fragment_hash NOT GLOB '*[^0-9a-f]*'),
    normalized_text_sha256 TEXT NOT NULL CHECK(length(normalized_text_sha256)=64 AND normalized_text_sha256 NOT GLOB '*[^0-9a-f]*'),
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
    UNIQUE(batch_id, candidate_order),
    CHECK(formal_order=498+candidate_order)
)
```

### 6.3 Formal query view

`formal_complete_questions_v119` is the sole V1.19 cross-generation formal
query. It has this exact column order:

```text
formal_order
question_id
authority_kind
batch_id
candidate_order
source_id
source_question_number
source_section
source_fragment_hash
normalized_text_sha256
question_text_original
question_text_zh
question_text_zh_reviewed
translation_status
translation_evidence
solution_original
solution_verified
answer_status
explanation_text
explanation_status
explanation_evidence
source_image_paths_json
source_image_sha256s_json
source_image_roles_json
primary_type
tags_json
tag_status
difficulty_level
difficulty_status
enrichment_status
formal_image_paths_json
record_status
selectable
```

The first arm projects the 497 rows of `complete_questions_v2` directly, in
their exact `source_order` 1..497, with `authority_kind="baseline_v118"`.
Both `question_text_zh` and the separately reviewed
`question_text_zh_reviewed` remain distinct. Task-9-only provenance fields are
`NULL`; they are never inferred. The second arm projects the five new formal
rows with `authority_kind="task9_promoted"`, formal orders 498..502, published
status, `question_text_zh_reviewed IS NULL` because Task 9 granted no separate
reviewed-text authority, and selectability 1. The view is ordered by
`formal_order` and contains exactly 502 unique IDs. It never selects from
`task9_import_candidates_v1`.

This additive model avoids forcing nullable Task 9 evidence into the frozen
V1.18 table and avoids inventing V2-only enrichment values.

The exact view SQL, modulo insignificant SQL whitespace, is:

```sql
CREATE VIEW formal_complete_questions_v119 AS
SELECT
    q.source_order AS formal_order,
    q.question_id AS question_id,
    'baseline_v118' AS authority_kind,
    CAST(NULL AS TEXT) AS batch_id,
    CAST(NULL AS INTEGER) AS candidate_order,
    q.source_id AS source_id,
    q.source_question_number AS source_question_number,
    q.source_section AS source_section,
    q.source_fragment_hash AS source_fragment_hash,
    CAST(NULL AS TEXT) AS normalized_text_sha256,
    q.question_text_original AS question_text_original,
    q.question_text_zh AS question_text_zh,
    q.question_text_zh_reviewed AS question_text_zh_reviewed,
    CAST(NULL AS TEXT) AS translation_status,
    CAST(NULL AS TEXT) AS translation_evidence,
    q.solution_original AS solution_original,
    q.solution_verified AS solution_verified,
    q.answer_status AS answer_status,
    CAST(NULL AS TEXT) AS explanation_text,
    CAST(NULL AS TEXT) AS explanation_status,
    CAST(NULL AS TEXT) AS explanation_evidence,
    q.image_paths_json AS source_image_paths_json,
    CAST(NULL AS TEXT) AS source_image_sha256s_json,
    CAST(NULL AS TEXT) AS source_image_roles_json,
    q.primary_type AS primary_type,
    q.tags_json AS tags_json,
    CAST(NULL AS TEXT) AS tag_status,
    q.difficulty_level AS difficulty_level,
    CAST(NULL AS TEXT) AS difficulty_status,
    CAST(NULL AS TEXT) AS enrichment_status,
    q.image_paths_json AS formal_image_paths_json,
    q.record_status AS record_status,
    q.selectable AS selectable
FROM complete_questions_v2 AS q
UNION ALL
SELECT
    p.formal_order,
    p.question_id,
    'task9_promoted' AS authority_kind,
    p.batch_id,
    p.candidate_order,
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
FROM task9_promoted_questions_v1 AS p
ORDER BY formal_order
```

### 6.4 Release metadata

The transaction changes only these keys in `release_metadata_v2`:

```text
release_version = V1.19
baseline_version = V1.18
baseline_sqlite_sha256 = fd9fe44f...
release_model = incremental-import-promotion
schema_version = task9-v119-formal-v1
```

It adds deterministic `task9_batch_id`, `task9_preflight_sha256`,
`task9_candidate_sqlite_sha256`, `task9_candidate_manifest_sha256`,
`task9_promoted_questions=5`, and `formal_question_count=502`. Existing
historical keys remain unchanged. No timestamp or new user identity is added.

## 7. Baseline and candidate preservation

The builder and verifier independently compare:

- frozen V1.18 bytes, SHA, user version, integrity, foreign keys, schema SQL,
  and all logical rows;
- all pre-existing V1.18 schema objects and 497 complete rows inside the
  candidate and formal database, while treating only the explicit
  `release_metadata_v2` value changes in section 6.4 as the approved exception;
- the candidate root, manifest, SHA closure, rollback, database SHA, full five
  candidate rows, taxonomy, images, import statement, batch, and preflight;
- the five promoted rows against the five candidate rows with only the exact
  mapping in section 6.2.

No AI call, text normalization, duplicate query, tagging, or enrichment occurs
during promotion.

## 8. Release tree and artifact closure

The target tree is exact:

```text
<root>/
  Joy_M2_Complete_Question_DB_V1_19.sqlite3
  manifest.json
  SHA256SUMS.txt
  rollback.json
  images/sha256/<prefix>/<digest><canonical-extension>  # zero or more
```

Only images listed in the verified candidate manifest are copied, at their
existing content-addressed candidate paths, byte for byte. The current real
candidate has zero images.

JSON files use canonical UTF-8 JSON (`sort_keys=True`, compact separators,
`allow_nan=False`) plus exactly one LF. `SHA256SUMS.txt` is LF-only, sorted by
canonical release-relative path, and hashes every release file except itself.
Each line is exactly `<lowercase-sha256><two ASCII spaces><relative-path><LF>`;
an empty closure is impossible because the database, manifest, and rollback are
always present.
No absolute path, temporary path, timestamp, random UUID, filesystem traversal
order, or current working directory enters an artifact.

## 9. Promotion identity and manifest

The promotion identity is SHA-256 of canonical JSON plus one LF for this exact
payload:

```text
schema_version
release_version
baseline_database_sha256
baseline_question_count
candidate_database_sha256
candidate_manifest_sha256
batch_id
preflight_sha256
import_approval_statement
promoted_question_count
formal_question_count
formal_sqlite_sha256
formal_sqlite_semantic_sha256
images
```

`images` is a release-path ordered array of exact path/SHA/size/kind objects.
The payload excludes manifest, sums, rollback, Gate D statement, paths outside
the release root, and runtime state, avoiding circular or environmental
identity.

`manifest.json` has this exact top-level order (canonical bytes sort keys, but
the schema is listed semantically here):

```text
schema_version
release_version
release_status
release_model
database_schema
baseline
candidate
import_approval
counts
database
images
artifacts
verification
promotion
rollback
```

Required fixed values are `V1.19`, `published`,
`incremental-import-promotion`, and `task9-v119-formal-v1`. `baseline` binds
V1.18 SHA/count/schema. `candidate` binds candidate SQLite and candidate
manifest ArtifactRefs plus the exact source/answer/teacher/common-error
evidence arrays already retained by the candidate manifest. This preserves the
current source-map file SHA when present; it does not invent a separate source
mapping approval digest that Task 9C did not retain. `import_approval` binds the
exact Gate C statement. `counts` is 497/5/502. `database` includes both byte SHA
and the semantic SHA. `artifacts` covers database, rollback, and images.
`verification` names `verify_v119_promotion` and its required PASS contract.
`promotion` contains Gate `D`, the release digest, and the exact required Gate D
statement. It records required authority without falsely claiming that Gate D
has already occurred.

The exact nested schema is below. `object{...}` rejects extra or missing keys;
`array[T]` preserves declared order; `int` excludes `bool`; every digest is
lowercase 64-hex. `artifact(kind)` is exactly
`{relative_path:str, sha256:sha256, size_bytes:int>=0, kind:kind}`.

```text
manifest = object{
  schema_version: "task9-v119-formal-manifest-v1",
  release_version: "V1.19",
  release_status: "published",
  release_model: "incremental-import-promotion",
  database_schema: "task9-v119-formal-v1",
  baseline: object{
    release_version: "V1.18",
    schema_version: "complete-question-v1.0",
    question_count: 497,
    sqlite: object{sha256: sha256, size_bytes: int>=0, kind: "sqlite"}
  },
  candidate: object{
    release_version: "V1.19",
    database_schema: "task9-v119-candidate-v1",
    database: object{sha256: sha256, size_bytes: int>=0, kind: "sqlite"},
    manifest: object{sha256: sha256, size_bytes: int>=0, kind: "manifest"},
    evidence: object{
      candidate_records: array[evidence],
      sources: array[evidence],
      answers: array[evidence],
      teacher_notes: array[evidence],
      common_errors: array[evidence]
    }
  },
  import_approval: object{
    batch_id: str,
    preflight_sha256: sha256,
    statement: str
  },
  counts: object{
    baseline_question_count: 497,
    promoted_question_count: 5,
    formal_question_count: 502
  },
  database: object{
    relative_path: "Joy_M2_Complete_Question_DB_V1_19.sqlite3",
    sha256: sha256,
    semantic_sha256: sha256,
    size_bytes: int>=0,
    kind: "sqlite"
  },
  images: array[artifact("image")],
  artifacts: array[artifact("sqlite") | artifact("rollback") | artifact("image")],
  verification: object{
    authority: "verify_v119_promotion",
    check_names: array[str],
    required_status: "PASS"
  },
  promotion: object{
    gate: "D",
    release_digest: sha256,
    required_statement: str,
    formal_target: "releases/V1.19"
  },
  rollback: artifact("rollback")
}

evidence = object{
  relative_path: canonical-relative-str,
  sha256: sha256,
  size_bytes: int>=0,
  kind: "candidate_json" | "source" | "answer" |
        "teacher_notes" | "common_errors"
}
```

`candidate.evidence` arrays are copied exactly from the corresponding five
arrays in `candidate_manifest.json`, including array order. The candidate
manifest's physical `images` entries are separately projected to formal
`images`; no sixth evidence array is invented. `artifacts` is ordered by
`relative_path` and contains exactly the database, rollback, and zero or more
image objects after one combined sort. `verification.check_names` equals the exact 18-name
sequence in section 12. `promotion.required_statement` is exactly
`USER APPROVED RELEASE PROMOTION V1.19 <release_digest>`.

The target manifest can say `published` in a staging dry-run because these are
the exact immutable target bytes. Formal publication authority is the
combination of exact Gate D approval and atomic presence at
`releases/V1.19/`; a staging tree is never a formal release.

## 10. Semantic SQLite digest

The formal SQLite semantic digest is SHA-256 of one canonical payload covering
`PRAGMA user_version`, every non-internal schema object, every non-internal
table, and the 502-row formal view. The following rules, rather than physical
page layout or incidental insertion order, define that payload.

The exact digest payload is:

```text
object{
  schema_version: "task9-v119-sqlite-semantic-v1",
  user_version: 119,
  schema_objects: array[object{
    type: str,
    name: str,
    table_name: str,
    sql: str | null
  }],
  relations: array[object{
    name: str,
    columns: array[str],
    rows: array[array[sqlite-value]]
  }]
}
```

`schema_objects` contains every `sqlite_master` row whose name does not begin
`sqlite_`, ordered by `(type, name)`. `sql` normalization is exact: replace each
maximal run of ASCII space, tab, CR, LF, form-feed, or vertical-tab with one
ASCII space; strip leading/trailing ASCII space; if the result ends in one
semicolon remove it; strip trailing ASCII space once more. SQL `NULL` remains
JSON `null`.

`relations` contains every non-internal table in table-name order, followed by
the one view `formal_complete_questions_v119`. Columns use `PRAGMA table_info`
CID order. Table rows are ordered by declared primary-key columns in PK-rank
order; a table without a primary key is ordered by all its columns in CID
order. The formal view is ordered by `formal_order`. Each row is serialized in
column order. A `sqlite-value` maps SQL NULL to JSON null, INTEGER to JSON int,
REAL to finite JSON number, TEXT to exact JSON string, and BLOB to exact
`{"blob_hex":"<lowercase hex>"}`. Booleans are not a distinct SQLite result
type. Non-finite numbers or any other value fail verification.

The payload is encoded as canonical UTF-8 JSON with sorted object keys, compact
separators, `ensure_ascii=False`, `allow_nan=False`, plus exactly one LF, then
hashed once with SHA-256. This is the portable determinism authority. The
maintained builder must also produce byte-identical SQLite under two equivalent
independent roots in the supported runtime; byte SHA is recorded as artifact
identity, while the semantic digest explains the invariant should physical
SQLite tooling ever change.

## 11. Rollback

`rollback.json` has exact schema `task9-v119-formal-rollback-v1` and exact keys:

```text
schema_version
action
release_version
release_digest
protected_baseline
release_artifacts
```

`action` is `remove_release_tree_if_release_digest_matches`.
`protected_baseline` binds V1.18 SHA/count. `release_artifacts` is the sorted
list of all expected release-relative paths including `SHA256SUMS.txt`.

The exact payload is:

```text
object{
  schema_version: "task9-v119-formal-rollback-v1",
  action: "remove_release_tree_if_release_digest_matches",
  release_version: "V1.19",
  release_digest: sha256,
  protected_baseline: object{
    release_version: "V1.18",
    sqlite_sha256: sha256,
    question_count: 497
  },
  release_artifacts: array[canonical-relative-str]
}
```

No extra keys are allowed. `release_artifacts` is strictly increasing by UTF-8
relative-path bytes and has no duplicates.

The receipt is declarative and grants no deletion authority by itself. Before
formal publication, rollback means remove only a failed private temporary
tree. After an approved publication, rollback may remove the complete V1.19
tree only after its release digest and artifact closure still match; it never
rewrites or replaces V1.18.

## 12. Independent verifier

`verify_v119_promotion()` is read-only and never repairs, regenerates, removes,
or rewrites artifacts. Malformed JSON syntax raises `InputFormatError` because
verification context cannot be established. Parsed but invalid content,
corruption, mismatch, missing/extra artifacts, or unreadable SQLite produce a
structured `VerificationReport(status="FAIL")`.

Its exact ordered checks are:

```text
release_directory
promotion_contract
candidate_verification
manifest_contract
authority_binding
filesystem_closure
sha256sums_closure
artifact_references
rollback_contract
sqlite_readability
sqlite_integrity
sqlite_foreign_keys
sqlite_schema
baseline_preservation
promotion_projection
formal_query
count_closure
publication_boundary
```

All checks PASS closes the report to PASS; any check FAIL closes it to FAIL.
Checks cover root containment and exact shape; independent Task 9C verification;
manifest runtime types and exact schema; SHA and ArtifactRef binding; SQLite
integrity/FK/user-version/schema; all 497 baseline rows; all five promoted rows;
502 unique ordered formal rows; no candidate-only status/selectability in the
formal view; and exact release digest/rollback closure.

For a staging root, `publication_boundary` passes only when the root is beneath
`staging_root` and is not `releases/V1.19`. For a formal root, it passes only
when the root is exactly `releases/V1.19`; formal verification does not itself
grant permission to create that root.

## 13. Publication transaction

`publish_v119_release()` performs these exact steps after Gate D:

1. validate exact typed request and Gate D approval;
2. verify the dry-run tree and bind its release digest;
3. require the dry-run beneath staging and target exactly new
   `releases/V1.19`;
4. copy exact files to a private sibling directory under `releases/`;
5. require byte-for-byte tree equality with the already verified dry-run;
6. atomically rename without replacement to `releases/V1.19`;
7. verify the formal root and return ArtifactRefs rebound to it.

The private sibling is neither a staging verification target nor a formal
release target, so it is never passed to the public verifier. Its only gate is
exact tree-byte equality with the already verified dry-run. Full verification
runs immediately before the copy on the staging source and immediately after
the atomic rename on the exact formal target.

An exception before rename deletes only the private temporary copy. A failed
post-rename verification removes the just-created V1.19 tree only when its
release digest and complete tree fingerprint still equal the preverified
source; otherwise it raises `PromotionError` without touching V1.18. Existing
targets are always conflicts; overwrite, merge, UPSERT, force, and partial
publication are forbidden.

No current-release pointer or index exists in maintained code or repository
authority. Task 9D therefore creates no pointer/index and changes no lookup.

## 14. TDD and negative controls

No production promotion behavior may be written before valid RED tests exist.
Tests first freeze exact carriers, APIs, schema, mapping, manifest, identity,
rollback, verification, and publication boundary. Required independent negative
controls include:

- wrong baseline SHA and mutated baseline row;
- wrong candidate SQLite/manifest SHA;
- wrong batch, wrong preflight, forged or absent import approval;
- candidate verifier FAIL;
- wrong counts, missing candidate row, duplicate promoted ID;
- missing/extra/invalid release root artifacts and pre-existing output;
- malformed manifest JSON versus parsed-invalid manifest;
- manifest, SHA, ArtifactRef, semantic-digest, SQLite integrity, FK, schema,
  projection, and formal-view mismatch;
- an old baseline row mutation;
- missing-enrichment preservation without auto-fill;
- publication without Gate D, wrong Gate D digest/statement, and import approval
  reused as promotion approval;
- copy/verification/rename failure cleanup and incomplete-publication rollback;
- two equivalent independent roots producing identical semantic digest,
  manifest, sums, report, release digest, and supported-runtime SQLite bytes.

Tests that exercise publication use isolated temporary repository roots and
synthetic approval values. They must never create this repository's
`releases/V1.19/`.

## 15. Real dry-run and completion gates

After focused GREEN, reconstruct the exact real Task 9A preflight from the
approved canonical package, form the exact Gate C `ImportApproval`, and verify
the unchanged real Task 9C candidate. Build twice under separate new descendants
of `data/staging/`, verify both, and compare all deterministic identities.

The dry-run must prove:

- 502 formal-view rows, 497 baseline + 5 promoted;
- V1.18 SHA/count unchanged;
- candidate tree SHA/fingerprint unchanged;
- new five rows and missing enrichment unchanged;
- identical release digest, semantic digest, manifest, sums, rollback,
  verification checks, and SQLite bytes across roots;
- `releases/V1.19/` absent before and after.

Required maintained regressions are current Task 9A 41/41, Task 9B 342/342,
Task 9C 71/71, complete Task 9D focused GREEN, and V1.18 independent validator
PASS, all with zero skips/expected failures where applicable.

## 16. Closed file scope

Design checkpoint:

- `docs/superpowers/specs/2026-09-13-task9d-v119-promotion-design.md`

Plan checkpoint:

- `docs/superpowers/plans/2026-09-13-task9d-v119-promotion.md`

Implementation:

- `src/joy_m2/ingest/promotion_models.py` (new)
- `src/joy_m2/ingest/promotion.py` (new)
- `src/joy_m2/ingest/promotion_verification.py` (new)
- `src/joy_m2/ingest/__init__.py` (approved exports only)
- `tests/unit/test_v119_promotion_models.py` (new)
- `tests/unit/test_v119_promotion_primitives.py` (new)
- `tests/integration/test_v119_promotion.py` (new)

Completion documentation:

- `PROJECT_STATE.md`
- `docs/reports/TASK9D_VERIFICATION.md` (new)

No other production, test, data, release, legacy, frozen, CLI, script, or
configuration file is authorized. Real dry-run outputs under ignored
`data/staging/` are evidence, not commit content.

## 17. Review, Git, and final stop

The Design, Plan, implementation, and completion evidence each require an
independent review with zero Critical and zero Important findings before their
checkpoint proceeds. Ordinary focused commits and ordinary pushes are allowed;
force push, history rewrite, merge, rebase, and squash are not.

After all technical work is committed and pushed, Task 9D status becomes
`READY FOR PROMOTION AUTHORIZATION`, not published. The final report must give
the Design/Plan/implementation commits, reviews, maintained gates, exact real
candidate authority, dual-root identities, expected formal files, rollback,
publication action, lack of pointer update, and confirmation that
`releases/V1.19/` remains absent.

Then stop at:

```text
USER DECISION REQUIRED — FINAL V1.19 PROMOTION AUTHORIZATION
```

The only acceptable next approval is:

```text
USER APPROVED RELEASE PROMOTION V1.19 <exact dry-run release_digest>
```

## 18. Non-goals

- source adaptation, parsing, OCR, PDF, AI solving, or enrichment;
- duplicate reclassification or selection-policy changes;
- edits to Task 9A/9B/9C authority or artifacts;
- mutation of V1.18 or its frozen artifacts;
- CSV/Markdown/application export or a generic release framework;
- CLI, API, consumer migration, Task 8C, Phase 2A, or later batch support;
- formal publication before Gate D.

## 19. Decision register

| Decision | Result |
|---|---|
| formal representation | additive promoted table plus exact 502-row formal view |
| baseline preservation | all 497 V2 rows exact; version metadata only changes explicitly |
| missing enrichment | preserved as missing/null/incomplete and allowed |
| deterministic authority | canonical artifacts plus SQLite semantic digest; byte identity required in supported runtime |
| dry-run status | final target bytes under non-formal staging; location and Gate D define publication |
| candidate evidence | retained unchanged; never selected by formal view |
| Gate D binding | `USER APPROVED RELEASE PROMOTION V1.19 <release_digest>` |
| publication target | exact `releases/V1.19/`, atomic no-replace, no pointer/index update |

All Task 9D V1 implementation decisions are closed by this Design. No formal
publication authority is granted here.
