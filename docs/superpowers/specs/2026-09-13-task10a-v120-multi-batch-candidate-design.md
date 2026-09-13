# Joy M2 AI Database — Task 10A V1.20 Multi-Batch Candidate Authority Design

Date: 2026-09-13 (Asia/Shanghai)

Status: HUMAN GATE A DESIGN AUTHORIZED — INDEPENDENT REVIEW PASSED — IMPLEMENTATION NOT STARTED

Historical V1.19 authority: CLOSED / PASS

## 1. Purpose and hard boundary

Task 10A defines an append-only V1.20 candidate lifecycle over the immutable
formal V1.19 release. It permits multiple independently preflighted and
approved batches to accumulate into one deterministic logical V1.20 candidate.

This Design and its implementation Plan authorize documentation only at this
checkpoint. Production code, tests, fixtures, candidate artifacts, database
writes, real imports, and V1.20 promotion remain forbidden until a later exact
implementation authorization.

The architecture is versioned and additive:

```text
immutable formal V1.19 / 502
+ approved V1.20 batch 1
+ approved V1.20 batch 2
+ approved V1.20 batch 3
= one accumulated, non-formal V1.20 candidate
```

Task 10A does not retrofit Task 9A, 9B, 9C, or 9D. Their V1.19 public models,
function signatures, constants, digest payloads, exact approval statement,
candidate/release schemas, tests, and historical evidence remain replayable.

## 2. Frozen baseline and target identity

The exact formal baseline is:

```text
release_version = V1.19
formal_question_count = 502
formal_database_schema = task9-v119-formal-v1
formal_view = formal_complete_questions_v119
SQLite path = releases/V1.19/Joy_M2_Complete_Question_DB_V1_19.sqlite3
SQLite SHA-256 = 5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff
SQLite size = 9478144
manifest SHA-256 = cd048408df5e062592d5ed8553b3461860c876b0264660ab65c78c428584a510
manifest size = 3242
release digest = 7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d
```

The target candidate identity is exactly `V1.20`. A V1.20 candidate is staging
evidence, not a formal release. Formal retrieval continues to use the V1.19
formal view and its 502 rows until a separately designed and explicitly
approved V1.20 promotion occurs.

Historical V1.18 remains byte-frozen at 497 questions and SQLite SHA-256
`fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7`.
Neither V1.18 nor V1.19 may be edited, replaced, normalized, or regenerated.

## 3. Architecture and version separation

Task 10A adds narrow V1.20 modules beside the historical implementation:

```text
Task 9B source parsing / explicit mapping / private Source IR
        |
        +-- historical V1.19 target projection (unchanged)
        |
        `-- new V1.20 target projection
                  |
                  v
       V1.20 effective-state preflight
                  |
          exact parent-bound approval
                  |
                  v
 full ordered-prefix candidate rebuild in a private staging root
                  |
          independent verification
                  |
          atomic no-replace publication
                  v
      one immutable V1.20 candidate generation
```

The implementation keeps V1.20 projection and collision behavior inside the
new V1.20 modules authorized in section 16. It does not extract a shared
collision module or modify historical `preflight.py`. V1.20 may reproduce only
the minimum closed Task 9A normalization/collision semantics needed for this
version, with literal historical replay proving V1.19 unchanged. It may not
replace named V1.19 public carriers with generic unions, add a future-version
engine, or scatter mutable `if version == ...` policy throughout existing
modules.

Every current V1.19 API continues to accept and return only its exact historical
carrier types. New V1.20 public names are separately versioned.

## 4. Canonical V1.20 package projection

### 4.1 Manifest carrier

`V120BatchImportManifest` is a new frozen dataclass. Its exact fields, order,
and runtime types are:

```python
@dataclass(frozen=True)
class V120BatchImportManifest:
    schema_version: str
    batch_id: str
    project: str
    module: str
    chapter: str
    target_release_version: str
    candidate_records: tuple[ImportFileEvidence, ...]
    source_files: tuple[ImportFileEvidence, ...]
    answer_files: tuple[ImportFileEvidence, ...]
    image_files: tuple[ImportFileEvidence, ...]
    teacher_notes_files: tuple[ImportFileEvidence, ...]
    common_errors_files: tuple[ImportFileEvidence, ...]
    language_policy: str
    split_policy: str
    difficulty_policy: str
    tag_policy: str
    answer_policy: str
    explanation_policy: str
```

All fields have no defaults. The six evidence groups retain exact
`ImportFileEvidence` items, manifest order, kind matching, path uniqueness, and
defensive tuple canonicalization. Exact fixed values are:

```text
schema_version = task10-v120-import-manifest-v1
project = Joy M2 AI Database
module = M2
target_release_version = V1.20
language_policy = preserve_source_and_store_reviewed_chinese_separately
split_policy = one_complete_question_per_record
difficulty_policy = joy_level_1_5
tag_policy = controlled_primary_type_and_tags
answer_policy = preserve_source_answer_identity
explanation_policy = source_or_independently_verified_with_identity
```

V1.20 `batch_id` values must match the exact ASCII regular expression
`[A-Za-z0-9][A-Za-z0-9._-]{0,127}`. This makes the authority-directory segment
unambiguous; it rejects whitespace, separators, dot components, control
characters, and non-NFC/non-ASCII aliases. This is a new V1.20 boundary only
and does not change accepted historical V1.19 batch IDs.

`ImportFileEvidence`, `ImportCandidate`, `ImportAdaptation`, and `ImportIssue`
are version-independent canonical evidence carriers and remain unchanged.

### 4.2 Task 9B target projection

Task 9B retains its exact `MmdSelection`, `MmdAdapterManifest`, source-mapping
approval, parser, explicit mapping, Source IR, provenance, source-map schema,
image authority, and canonical package layout. New V1.20 entry points are:

```python
def adapt_mmd_package_v120(
    selection_manifest_path: Path,
    source_path: Path,
    output_dir: Path,
    config: PipelineConfig,
) -> V120AdaptedImportPackage

def adapt_mmd_package_from_mapping_v120(
    selection_manifest_path: Path,
    source_mapping_path: Path,
    approval: SourceMappingApproval,
    source_path: Path,
    output_dir: Path,
    config: PipelineConfig,
) -> V120AdaptedImportPackage
```

The result carrier has exact fields:

```python
@dataclass(frozen=True)
class V120AdaptedImportPackage:
    package_root: Path
    manifest_path: Path
    manifest: V120BatchImportManifest
```

Persisted canonical packages are loaded through one versioned decoder:

```python
def load_v120_import_manifest(path: Path) -> V120BatchImportManifest
```

It retains the Task 9A strict UTF-8/JSON, exact-key, and typed-construction
rules while accepting only the V1.20 manifest carrier. Duplicate-key rejection
is a new V1.20 decoder boundary; it does not alter the historical V1.19
`load_import_manifest()`, which remains V1.19-only with its committed behavior.

For valid canonical inputs, the V1.20 package differs from its logically
equivalent historical projection only where target authority requires it: the
manifest carrier/schema and `target_release_version`. Candidate JSON, raw MMD,
source-map, answer, and image bytes remain identical for the same
selection/mapping. The outer MMD.ZIP digest remains input validation evidence
only and never enters canonical identity.

The historical `adapt_mmd_package()` and
`adapt_mmd_package_from_mapping()` signatures and V1.19 results remain exact.
The explicit-mapping extension remains module-scoped: the existing four-name
`joy_m2.ingest.source_mapping.__all__` is the unchanged prefix and appends only
`"adapt_mmd_package_from_mapping_v120"`. That name is not re-exported from the
root `joy_m2.ingest` package, preserving the historical module boundary.

## 5. Deterministic effective candidate state

### 5.1 State carrier

The preflight input state is represented by this exact frozen carrier:

```python
@dataclass(frozen=True)
class V120EffectiveState:
    baseline_database: ArtifactRef
    candidate_digest: str
    batch_ledger: tuple[V120BatchLedgerEntry, ...]
    candidate_count: int
    projected_question_count: int
```

It is path-independent except for the one runtime `ArtifactRef.path`, which is
never projected into a digest. `candidate_count` is the number of accumulated
V1.20 candidate rows. `projected_question_count` is exactly
`502 + candidate_count`.

For the first batch, the state is the genesis state: empty ledger, zero
candidate rows, projected count 502, and `candidate_digest` equal to the fixed
genesis digest in section 8.3. For later batches, preflight first requires the
parent verifier to return PASS, then independently rebuilds the state from the
verified parent manifest, SQLite rows, and exact approved-batch prefix. Its
`candidate_digest` is the verified parent manifest's exact
`candidate_digest`; it is never read from the generic `VerificationReport`,
which carries only status and checks. A caller-provided state is revalidated;
the preflight may not trust counts, ledger, or digest merely because they are
inside a frozen dataclass.

### 5.2 Effective duplicate index

The reference set for every V1.20 preflight is exactly:

```text
all 502 rows from formal_complete_questions_v119
+ all accepted V1.20 candidate rows from the verified parent generation
```

The formal V1.19 view, not the 497-row `complete_questions_v2` table, is the
baseline query authority. The effective index uses the unchanged Task 9A
normalization and comparison semantics for question ID, source locator,
source-fragment digest, normalized original-text digest, and image bindings.
Previously accepted V1.20 rows are authoritative references for later batches;
therefore a duplicate in another batch is not treated as new.

The preflight never loads the entire formal question corpus into an AI context.
It uses compact deterministic indexes and candidate-local evidence.

## 6. Batch ledger and semantic order

The append-only ledger carrier is:

```python
@dataclass(frozen=True)
class V120BatchLedgerEntry:
    ordinal: int
    batch_id: str
    parent_candidate_digest: str
    preflight_sha256: str
    manifest_sha256: str
    approval: V120ImportApproval
    batch_candidate_count: int
    cumulative_candidate_count: int
    projected_question_count: int
```

All fields have no defaults. The nested approval's batch, preflight, target,
parent, and statement must exactly match the ledger entry. `ordinal` starts at
1 and is contiguous. The semantic batch order is the tuple order and must equal
ordinal order. It is the order in which exact parent-bound approvals were
accepted. No implementation may sort this tuple by batch ID, digest, path,
creation time, filesystem order, random UUID, directory enumeration, or LLM
output.

Within a batch, Task 9A manifest-declared candidate order remains semantic.
Aggregate candidate order is:

```text
formal V1.19 rows: formal_order 1..502
then V1.20 rows: batch ordinal, then zero-based batch candidate order
```

The first V1.20 aggregate order is 503. The ledger and all candidate IDs are
unique. A later build request contains the complete approved prefix; it does
not append by discovering directories.

## 7. Versioned preflight authority

### 7.1 Request and result

The preflight request is:

```python
@dataclass(frozen=True)
class V120PreflightRequest:
    manifest: V120BatchImportManifest
    package_root: Path
    baseline_database: ArtifactRef
    parent_candidate: V120CandidateVerificationRequest | None
    contract: V120CandidateContract
```

The public API is:

```python
def preflight_v120_import(
    request: V120PreflightRequest,
    config: PipelineConfig,
) -> V120ImportPreflightResult
```

`parent_candidate=None` is legal only for the genesis state. Otherwise the
preflight first requires the exact parent candidate verifier to return PASS,
then derives its `V120EffectiveState`. This prevents a raw database path or a
caller-supplied count from bypassing effective-state verification.

The exact result is:

```python
@dataclass(frozen=True)
class V120ImportPreflightResult:
    manifest: V120BatchImportManifest
    effective_state: V120EffectiveState
    candidates: tuple[ImportCandidate, ...]
    issues: tuple[ImportIssue, ...]
    report: V120ImportPreflightReport
```

Candidates retain manifest order. Issues retain the exact stable key
`(proposed_question_id or "", code, field, evidence)`.

### 7.2 Report

`V120ImportPreflightReport` is frozen, has no defaults, and has this exact field
order:

```text
batch_id, status, preflight_sha256, manifest_sha256,
baseline_version, baseline_release_digest, baseline_question_count,
target_release_version, parent_candidate_digest, parent_batch_count,
before_count, detected_count, new_candidate_count, duplicate_count,
rejected_count, ambiguous_count, approved_count, projected_after_count,
readable_files, unreadable_files, unsupported_files,
teacher_notes_file_count, common_errors_file_count, ambiguous_splits,
missing_answers, missing_explanations, incomplete_enrichments,
missing_images, orphan_images, level_counts, proposed_ids, adaptations,
warnings, blocking_errors
```

Exact fixed identity is baseline V1.19, release digest from section 2,
baseline count 502, and target V1.20. `before_count` equals the verified
effective state's projected count. `projected_after_count` equals
`before_count + new_candidate_count`. The current preflight does not approve
anything, so `approved_count` remains zero.

The two final statuses remain Task 9A-style:

```text
READY FOR USER IMPORT APPROVAL
BLOCKED — IMPORT PREFLIGHT FAILED
```

Missing explanations, tags, difficulty, or other approved incomplete
enrichment remain non-blocking. No automatic fill, deletion, difficulty
promotion, tag invention, or issue reclassification is permitted.

### 7.3 Duplicate and collision authority

V1.20 reuses the exact closed sixteen-code Task 9A issue taxonomy, evidence
objects, severity, classification, ordering, and count closure. It adds no
seventeenth code and changes no V1.19 issue meaning.

The seven existing duplicate/collision codes apply against both formal V1.19
and earlier V1.20 rows:

```text
duplicate_exact
duplicate_ambiguous
collision_candidate_id
collision_source_locator
collision_fragment_sha256
collision_normalized_text_sha256
collision_image_sha256
```

Reference question IDs remain the issue evidence identity. The verified
candidate database maps every earlier V1.20 reference ID to its batch ordinal
and batch ID, so no extra batch field is added to the frozen issue schemas.

Identical image bytes may share one content-addressed staged file while each
question binding remains. One logical `(path, role)` associated with different
digests is `collision_image_sha256`. Different bytes claiming one digest or
content-addressed destination are an input-integrity failure and never reach
candidate publication.

## 8. Path-independent digests and parent binding

### 8.1 Canonical serialization

All Task 10 authority JSON uses exactly:

```python
json.dumps(
    value,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

Authority JSON files add exactly one LF. Digest payload arrays retain semantic
order. No digest contains an absolute path, cwd, repository/staging/temp root,
mtime, timestamp, inode, environment value, memory identity, random value, or
outer ZIP identity.

### 8.2 V1.20 manifest and preflight digests

`manifest_sha256` is SHA-256 of the exact logical projection of all 18
`V120BatchImportManifest` fields, encoded as canonical JSON plus one LF. It is
not the hash of an arbitrary source file representation.

Every Task 10 digest and manifest uses this exact path-free baseline object:

```text
baseline = {
  release_version: "V1.19",
  question_count: 502,
  database_schema: "task9-v119-formal-v1",
  sqlite: {
    sha256: "5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff",
    size_bytes: 9478144,
    kind: "sqlite"
  },
  manifest: {
    sha256: "cd048408df5e062592d5ed8553b3461860c876b0264660ab65c78c428584a510",
    size_bytes: 3242,
    kind: "manifest"
  },
  release_digest: "7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d"
}
```

The `task10-v120-preflight-v1` payload has exactly these top-level keys:

```text
schema
batch_id
target_release_version
baseline
parent_state
manifest_policies
candidate_record_order
file_evidence
candidates
issues
duplicate_classifications
image_evidence
report
```

`baseline` is the exact path-free section 2 identity. `parent_state` has exact
keys `candidate_digest`, `batch_count`, `candidate_count`, and
`projected_question_count`. The remaining projections retain the exact Task 9A
named-key semantics and ordering; `report` includes every report field except
`preflight_sha256`. The digest is SHA-256 of canonical JSON plus one LF.

Changing the parent state, baseline identity, target, batch/package evidence,
candidate order/content, issue/classification, image evidence, or report
changes `preflight_sha256`. Moving equivalent inputs between absolute roots
does not.

### 8.3 Aggregate candidate digest

The aggregate candidate digest is SHA-256 of canonical JSON plus one LF for
the exact `task10-v120-candidate-identity-v1` payload:

```text
schema
baseline
target_release_version
batch_ledger
candidate_projection
image_projection
counts
```

`batch_ledger` contains exact named-key projections of section 6 entries,
including the exact five-field approval object from section 9.
`candidate_projection` is
ordered by `(batch ordinal, batch candidate order)`; each entry has exact keys
`aggregate_order`, `batch_ordinal`, `batch_id`, `batch_candidate_order`,
`record`, and `candidate_image_paths`. `record` is the exact 25-field
`ImportCandidate` named-key projection. `candidate_image_paths` is a JSON array
of canonical relative-path strings, one-for-one in the candidate's
zero-based `image_order`; it is never set-like, deduplicated, or physically
discovery-sorted.

`image_projection` is a JSON array. Every element has exactly these keys and
runtime types, with no defaults or extra keys:

```text
batch_ordinal           exact int >= 1, never bool
batch_id                non-empty str
proposed_question_id    non-empty str
image_order             exact int >= 0, never bool
source_relative_path    canonical non-empty relative str
candidate_relative_path canonical non-empty relative str
sha256                   lowercase 64-hex str
size_bytes               exact int >= 0, never bool
kind                     exact str "image"
role                     non-empty str
```

The array is sorted by the exact key
`(candidate_relative_path, batch_ordinal, batch_id,
proposed_question_id, image_order)`. Every logical binding is retained;
identical content may share one physical candidate-relative file, but bindings
are never deduplicated. For each candidate, its `candidate_image_paths` array
equals, in `image_order`, the `candidate_relative_path` values of precisely its
image-projection elements. These named-key objects and array rules are the
single writer/verifier digest oracle.

`counts` has exact keys `baseline_question_count`, `batch_count`,
`new_candidate_count`, and `projected_question_count`.

The database byte digest and manifest self-digest are excluded to avoid a
circular identity. They remain separately bound by artifact references and
`SHA256SUMS`. The logical candidate digest nevertheless commits every approved
batch authority and the complete candidate row/image projection.

The fixed genesis payload uses the section 2 baseline, target V1.20, empty
ledger/candidate/image arrays, and counts `502/0/0/502`. Its digest is:

```text
4ff624aca875b0191fe8a617516d2919c6d700ce69c5a3b5d236adcf7ecc59f1
```

For ledger ordinal `n`, `parent_candidate_digest` must equal the candidate
digest of the exact prefix ending at ordinal `n-1`; ordinal 1 binds the genesis
digest. The final candidate digest is the digest of the full prefix. Reordering,
inserting, removing, or changing any batch breaks the chain.

## 9. Per-batch approval

Each real batch requires its own exact approval. The new carrier is:

```python
@dataclass(frozen=True)
class V120ImportApproval:
    batch_id: str
    preflight_sha256: str
    target_release_version: str
    parent_candidate_digest: str
    statement: str
```

`target_release_version` is exactly `V1.20`; both digests are lowercase
SHA-256. CR/LF is forbidden in `batch_id`. The exact one-line statement is:

```text
USER APPROVED IMPORT BATCH <batch_id> <preflight_sha256> V1.20 PARENT <parent_candidate_digest>
```

The approval is valid only when all fields equal the READY preflight and its
verified effective state. Reusing an approval after another batch changes the
candidate state and therefore fails the parent binding. Approval authorizes only that batch
inside a non-formal V1.20 candidate; it grants neither future-batch approval
nor promotion authority.

Malformed approval carriers and any preflight/approval/parent mismatch raise
the existing `ImportApprovalError` before output creation. Structured import
issues continue to produce a BLOCKED preflight result rather than an approval
exception.

The historical V1.19 `ImportApproval` and exact statement ending in `V1.19`
remain unchanged and are never parsed as V1.20 authority.

## 10. Approved-batch and build carriers

The exact approved batch carrier is:

```python
@dataclass(frozen=True)
class V120ApprovedBatch:
    preflight_result: V120ImportPreflightResult
    package_root: Path
    approval: V120ImportApproval
```

The complete tuple order is the ledger order. `package_root` is a runtime
locator used to revalidate and stage approved image bytes; it is excluded from
semantic identity.

The exact contract and requests are:

```python
@dataclass(frozen=True)
class V120CandidateContract:
    profile: str
    baseline_release_version: str
    baseline_question_count: int
    baseline_database_sha256: str
    baseline_database_size_bytes: int
    baseline_manifest_sha256: str
    baseline_manifest_size_bytes: int
    baseline_release_digest: str
    canonical_manifest_schema: str
    preflight_schema: str
    approval_schema: str
    candidate_manifest_schema: str
    candidate_database_schema: str
    candidate_identity_schema: str
    rollback_schema: str
    expected_user_version: int
    database_filename: str
    manifest_filename: str
    sha256s_filename: str
    rollback_filename: str
    authority_root: str
    image_root: str
    required_baseline_view: str
    required_candidate_tables: tuple[str, ...]
    required_candidate_views: tuple[str, ...]

@dataclass(frozen=True)
class V120CandidateBuildRequest:
    approved_batches: tuple[V120ApprovedBatch, ...]
    output_dir: Path
    contract: V120CandidateContract

@dataclass(frozen=True)
class V120CandidateVerificationRequest:
    candidate_dir: Path
    approved_batches: tuple[V120ApprovedBatch, ...]
    contract: V120CandidateContract
```

The approved contract scalars are:

```text
profile = V1.20
baseline_release_version = V1.19
baseline_question_count = 502
baseline_database_sha256 = 5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff
baseline_database_size_bytes = 9478144
baseline_manifest_sha256 = cd048408df5e062592d5ed8553b3461860c876b0264660ab65c78c428584a510
baseline_manifest_size_bytes = 3242
baseline_release_digest = 7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d
canonical_manifest_schema = task10-v120-import-manifest-v1
preflight_schema = task10-v120-preflight-v1
approval_schema = task10-v120-import-approval-v1
candidate_manifest_schema = task10-v120-candidate-manifest-v1
candidate_database_schema = task10-v120-candidate-v1
candidate_identity_schema = task10-v120-candidate-identity-v1
rollback_schema = task10-v120-rollback-v1
expected_user_version = 120
database_filename = Joy_M2_V1.20_candidate.sqlite3
manifest_filename = candidate_manifest.json
sha256s_filename = SHA256SUMS
rollback_filename = rollback.json
authority_root = authority/batches
image_root = images/sha256
required_baseline_view = formal_complete_questions_v119
```

The exact candidate object tuples are:

```python
required_candidate_tables = (
    "task10_v120_batch_ledger_v1",
    "task10_v120_candidates_v1",
    "task10_v120_images_v1",
    "task10_v120_taxonomy_v1",
)
required_candidate_views = ("task10_candidate_questions_v120",)
```

Every scalar is exact; all fields have no defaults. Approved-batch tuples are
non-empty, exact, defensively copied, and remain in caller order.

The public builder/verifier APIs are:

```python
def build_v120_candidate(
    request: V120CandidateBuildRequest,
    config: PipelineConfig,
) -> V120CandidateArtifacts

def verify_v120_candidate(
    request: V120CandidateVerificationRequest,
    config: PipelineConfig,
) -> VerificationReport
```

## 11. Candidate database and provenance

The builder starts every generation from the exact formal V1.19 SQLite bytes.
It never starts from or mutates a prior candidate database. In one deterministic
transaction it adds only the four Task 10 tables and one candidate-preview
view, then sets `PRAGMA user_version=120` in the copy.

`task10_v120_batch_ledger_v1` preserves the exact section 6 entry fields plus
fixed V1.19 baseline SHA/release digest, fixed V1.20 schema/target, and
`record_status='candidate'`. Ordinals are contiguous and unique.

The exact normalized schema is the following SQL. It contains no `DEFAULT`
clause. `PRAGMA foreign_keys=ON` is mandatory during build and verification.
Lowercase-digest checks use both exact length and an invalid-character guard;
model validation additionally rejects subclasses and bool-as-int before the
transaction, while the verifier checks SQLite `typeof()` for every scalar.

```sql
CREATE TABLE task10_v120_batch_ledger_v1 (
    batch_ordinal INTEGER PRIMARY KEY CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL UNIQUE CHECK(length(batch_id) BETWEEN 1 AND 128),
    target_release_version TEXT NOT NULL CHECK(target_release_version = 'V1.20'),
    candidate_database_schema TEXT NOT NULL
        CHECK(candidate_database_schema = 'task10-v120-candidate-v1'),
    parent_candidate_digest TEXT NOT NULL
        CHECK(length(parent_candidate_digest) = 64
              AND parent_candidate_digest NOT GLOB '*[^0-9a-f]*'),
    preflight_sha256 TEXT NOT NULL UNIQUE
        CHECK(length(preflight_sha256) = 64
              AND preflight_sha256 NOT GLOB '*[^0-9a-f]*'),
    manifest_sha256 TEXT NOT NULL
        CHECK(length(manifest_sha256) = 64
              AND manifest_sha256 NOT GLOB '*[^0-9a-f]*'),
    approval_statement TEXT NOT NULL
        CHECK(approval_statement =
              'USER APPROVED IMPORT BATCH ' || batch_id || ' ' ||
              preflight_sha256 || ' V1.20 PARENT ' ||
              parent_candidate_digest),
    baseline_release_version TEXT NOT NULL CHECK(baseline_release_version = 'V1.19'),
    baseline_database_sha256 TEXT NOT NULL
        CHECK(baseline_database_sha256 =
              '5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff'),
    baseline_release_digest TEXT NOT NULL
        CHECK(baseline_release_digest =
              '7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d'),
    baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count = 502),
    batch_candidate_count INTEGER NOT NULL CHECK(batch_candidate_count >= 0),
    cumulative_candidate_count INTEGER NOT NULL
        CHECK(cumulative_candidate_count >= batch_candidate_count),
    projected_question_count INTEGER NOT NULL
        CHECK(projected_question_count = 502 + cumulative_candidate_count),
    record_status TEXT NOT NULL CHECK(record_status = 'candidate'),
    UNIQUE(batch_ordinal, batch_id)
);

CREATE TABLE task10_v120_candidates_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL,
    batch_candidate_order INTEGER NOT NULL CHECK(batch_candidate_order >= 0),
    aggregate_order INTEGER NOT NULL CHECK(aggregate_order >= 503),
    proposed_question_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_question_number TEXT NOT NULL,
    source_section TEXT NOT NULL,
    source_fragment_hash TEXT NOT NULL,
    normalized_text_sha256 TEXT NOT NULL,
    question_text_original TEXT NOT NULL,
    question_text_zh TEXT NOT NULL,
    translation_status TEXT NOT NULL
        CHECK(translation_status IN ('source_present','ai_proposed','verified','missing')),
    translation_evidence TEXT,
    solution_original TEXT NOT NULL,
    solution_verified TEXT NOT NULL,
    answer_status TEXT NOT NULL
        CHECK(answer_status IN ('source_provided','ai_solved_verified','missing_from_source')),
    explanation_text TEXT NOT NULL,
    explanation_status TEXT NOT NULL
        CHECK(explanation_status IN ('source_present','ai_proposed','verified','missing')),
    explanation_evidence TEXT,
    image_paths_json TEXT NOT NULL,
    image_sha256s_json TEXT NOT NULL,
    image_roles_json TEXT NOT NULL,
    primary_type TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    tag_status TEXT NOT NULL CHECK(tag_status IN ('source_provided','proposed','missing')),
    difficulty_level INTEGER CHECK(difficulty_level BETWEEN 1 AND 5
                                   OR difficulty_level IS NULL),
    difficulty_status TEXT NOT NULL
        CHECK(difficulty_status IN ('source_provided','proposed','missing')),
    enrichment_status TEXT NOT NULL
        CHECK(enrichment_status IN ('complete','incomplete')),
    candidate_image_paths_json TEXT NOT NULL,
    record_status TEXT NOT NULL CHECK(record_status = 'candidate'),
    selectable INTEGER NOT NULL CHECK(selectable = 0),
    PRIMARY KEY(batch_id, proposed_question_id),
    UNIQUE(proposed_question_id),
    UNIQUE(aggregate_order),
    UNIQUE(batch_ordinal, batch_candidate_order),
    UNIQUE(batch_ordinal, batch_id, proposed_question_id),
    FOREIGN KEY(batch_ordinal, batch_id)
        REFERENCES task10_v120_batch_ledger_v1(batch_ordinal, batch_id)
);

CREATE TABLE task10_v120_images_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL,
    proposed_question_id TEXT NOT NULL,
    image_order INTEGER NOT NULL CHECK(image_order >= 0),
    source_relative_path TEXT NOT NULL,
    candidate_relative_path TEXT NOT NULL,
    sha256 TEXT NOT NULL
        CHECK(length(sha256) = 64 AND sha256 NOT GLOB '*[^0-9a-f]*'),
    size_bytes INTEGER NOT NULL CHECK(size_bytes >= 0),
    kind TEXT NOT NULL CHECK(kind = 'image'),
    role TEXT NOT NULL,
    PRIMARY KEY(batch_id, proposed_question_id, image_order),
    FOREIGN KEY(batch_ordinal, batch_id, proposed_question_id)
        REFERENCES task10_v120_candidates_v1(
            batch_ordinal, batch_id, proposed_question_id
        )
);

CREATE TABLE task10_v120_taxonomy_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL,
    taxonomy_kind TEXT NOT NULL CHECK(taxonomy_kind IN ('primary_type','tag')),
    value TEXT NOT NULL,
    sort_order INTEGER NOT NULL CHECK(sort_order >= 1),
    record_status TEXT NOT NULL CHECK(record_status = 'candidate'),
    PRIMARY KEY(batch_ordinal, batch_id, taxonomy_kind, value),
    UNIQUE(batch_ordinal, batch_id, taxonomy_kind, sort_order),
    FOREIGN KEY(batch_ordinal, batch_id)
        REFERENCES task10_v120_batch_ledger_v1(batch_ordinal, batch_id)
);

CREATE VIEW task10_candidate_questions_v120 AS
SELECT f.*
FROM formal_complete_questions_v119 AS f
UNION ALL
SELECT
    c.aggregate_order AS formal_order,
    c.proposed_question_id AS question_id,
    'task10_v120_candidate' AS authority_kind,
    c.batch_id AS batch_id,
    c.batch_candidate_order AS candidate_order,
    c.source_id,
    c.source_question_number,
    c.source_section,
    c.source_fragment_hash,
    c.normalized_text_sha256,
    c.question_text_original,
    c.question_text_zh,
    CAST(NULL AS TEXT) AS question_text_zh_reviewed,
    c.translation_status,
    c.translation_evidence,
    c.solution_original,
    c.solution_verified,
    c.answer_status,
    c.explanation_text,
    c.explanation_status,
    c.explanation_evidence,
    c.image_paths_json AS source_image_paths_json,
    c.image_sha256s_json AS source_image_sha256s_json,
    c.image_roles_json AS source_image_roles_json,
    c.primary_type,
    c.tags_json,
    c.tag_status,
    c.difficulty_level,
    c.difficulty_status,
    c.enrichment_status,
    c.candidate_image_paths_json AS formal_image_paths_json,
    c.record_status,
    c.selectable
FROM task10_v120_candidates_v1 AS c
ORDER BY formal_order;
```

SQLite cannot express the complete predecessor-digest chain or the aggregate
order formula in row-local `CHECK` constraints. Before publication, both the
writer and independent verifier enforce contiguous ordinals, cumulative
counts, prefix digests, and
`aggregate_order = 502 + prior-prefix candidate count +
batch_candidate_order + 1`.

The four tuple-valued `ImportCandidate` fields are canonical compact JSON TEXT
arrays with no trailing LF. Optional model values use SQL NULL; legal empty
text remains empty text. Candidate order is the original preflight tuple order
and starts at zero without gaps. The image table contains one row per logical
binding; its three-column foreign key makes `batch_ordinal` part of candidate
provenance and prevents ordinal substitution. Taxonomy rows use deterministic
one-based order within each batch and kind.

`task10_candidate_questions_v120` has the same exact 33-column envelope as the
frozen `formal_complete_questions_v119` view. It returns the unchanged 502
formal rows followed by candidate rows in aggregate order. Candidate rows use
authority kind `task10_v120_candidate`, status `candidate`, and
`selectable=0`.

The existing formal view, all V1.19 objects/rows, release metadata, and formal
query results remain logically identical. Formal retrieval must continue to
query `formal_complete_questions_v119`; candidate preview must explicitly name
the Task 10 candidate root and view.

Every candidate row therefore resolves to a batch ledger entry, which binds
its ordinal, preflight, approval, source/canonical manifest evidence, and source
mapping hash. Flattening rows without those foreign-key/provenance links is
forbidden.

## 12. Candidate tree, artifacts, and identity

The exact result carrier is:

```python
@dataclass(frozen=True)
class V120CandidateArtifacts:
    database: ArtifactRef
    manifest: ArtifactRef
    sha256sums: ArtifactRef
    rollback: ArtifactRef
    batch_authorities: tuple[ArtifactRef, ...]
    images: tuple[ArtifactRef, ...]
    state: V120EffectiveState
    verification_report: VerificationReport
```

The tree contains exactly:

```text
<output_dir>/
  Joy_M2_V1.20_candidate.sqlite3
  candidate_manifest.json
  SHA256SUMS
  rollback.json
  authority/batches/000001/<batch-id>/preflight.json
  authority/batches/000001/<batch-id>/approval.json
  authority/batches/000002/<batch-id>/preflight.json
  authority/batches/000002/<batch-id>/approval.json
  ...
  images/sha256/<prefix>/<digest><canonical-extension>  # zero or more
```

Ledger ordinals use six zero-padded decimal digits. `batch-id` is encoded as
the exact canonical filename-safe batch ID required by the V1.20 model; path
separators, dot components, control characters, and non-NFC forms are rejected.

`preflight.json` has exact keys `preflight_sha256` and `payload`; `payload` is
the section 8.2 digest object. `approval.json` has exact keys
`schema_version`, `batch_id`, `preflight_sha256`, `target_release_version`,
`parent_candidate_digest`, and `statement`. Both are canonical JSON plus one
LF. They retain batch-level authority without copying or flattening the entire
canonical source package.

`candidate_manifest.json` has exact top-level keys:

```text
schema_version
release_version
release_status
release_model
baseline
candidate_digest
counts
batch_ledger
database
images
batch_authority_artifacts
rollback
verification
```

Its fixed values are `task10-v120-candidate-manifest-v1`, `V1.20`,
`candidate`, and `append-only-multi-batch-candidate`. It binds the path-free
baseline, aggregate digest, counts, ordered ledger, database/image/authority/
rollback ArtifactRefs using candidate-relative paths, and the required
independent verifier/check names. Every mapping rejects missing or extra keys;
`bool` never passes an integer contract.

The exact nested shapes are:

```text
counts = {
  baseline_question_count: 502,
  batch_count: exact-int,
  new_candidate_count: exact-int,
  projected_question_count: exact-int
}

batch_ledger_entry = {
  ordinal, batch_id, parent_candidate_digest, preflight_sha256,
  manifest_sha256,
  approval: {
    batch_id, preflight_sha256, target_release_version,
    parent_candidate_digest, statement
  },
  batch_candidate_count, cumulative_candidate_count,
  projected_question_count
}

relative_artifact = {
  relative_path: canonical-relative-path,
  sha256: lowercase-sha256,
  size_bytes: exact-nonnegative-int,
  kind: exact-kind
}

verification = {
  authority: "verify_v120_candidate",
  check_names: <exact section-14 ordered array>,
  required_status: "PASS"
}
```

`database` and `rollback` are one relative artifact each. `images` and
`batch_authority_artifacts` are path-sorted arrays of relative artifacts.
Approved kinds are database `sqlite`, manifest `manifest`, sums `sha256sums`,
rollback `rollback`, images `image`, preflight authority `preflight`, and
approval authority `approval`. The result carrier uses the same kinds.

`SHA256SUMS` is UTF-8/LF, path-sorted, and covers every tree file except itself.
Artifact references bind exact hash, size, kind, and final path. Canonical
packages are rebuild inputs and are not copied into the candidate tree.

## 13. Full-prefix rebuild and atomicity

`V120CandidateBuildRequest.approved_batches` is the complete accepted prefix,
not only the incoming batch. The builder performs these steps:

1. validate the exact contract and all nested carrier types;
2. validate the V1.19 baseline artifact and formal identity;
3. for every tuple position, recompute the preflight digest from its typed
   result and package evidence, validate READY/no-blocker closure, validate the
   exact approval, and validate its parent digest against the preceding prefix;
4. independently enforce duplicate/collision semantics against V1.19 plus the
   already processed prefix;
5. copy exact V1.19 SQLite bytes to a private sibling beneath staging;
6. create all Task 10 tables and rows in one transaction;
7. stage content-addressed images and canonical authority artifacts;
8. compute the aggregate digest, manifest, rollback, and `SHA256SUMS`;
9. run the independent verifier against the private tree and complete approved
   batch tuple;
10. only after every check passes, atomically rename without replacement to a
    new explicit staging destination.

Both the private root and final `output_dir` must be new strict descendants of
`PipelineConfig.staging_root`. The builder rejects a symlink leaf, any existing
symlink ancestor, a symlink loop, a resolved-path escape, and any overlap with
the V1.19 baseline, a canonical package, a prior candidate, or a formal release
before creating output. Every staged artifact must be a regular file reached
through a symlink-free descendant chain. These checks preserve the Task 9D
root-identity boundary and may not be replaced by lexical containment alone.

No operation updates a prior candidate root in place. A failed second or later
batch leaves the last verified generation byte-identical and publishes no new
generation. Partial database commits, partial image trees, ledger-only append,
overwrite, merge, UPSERT into an existing candidate, and best-effort batch
acceptance are forbidden.

Equivalent full-prefix rebuilds under different absolute roots produce the
same database bytes, authority JSON, image bytes, manifest, sums, rollback,
artifact digests, candidate digest, and ordered verification result.
ArtifactRef equivalence across roots means the same candidate-relative path,
`sha256`, `size_bytes`, and `kind`; root-specific absolute `ArtifactRef.path`
values are deliberately different and are never compared for equality or
projected into deterministic identity.

## 14. Independent verifier

`verify_v120_candidate()` is read-only. It never repairs, regenerates, deletes,
renames, or writes an artifact. Its exact ordered checks are:

```text
candidate_directory
candidate_contract
baseline_authority
batch_authority_artifacts
parent_chain
approval_binding
preflight_reconstruction
filesystem_closure
sha256sums_closure
artifact_references
rollback_contract
image_projection
sqlite_readability
sqlite_integrity
sqlite_foreign_keys
sqlite_schema
v119_preservation
batch_ledger
candidate_projection
effective_collision_closure
count_closure
candidate_digest
deterministic_identity
formal_boundary
```

All checks PASS closes the existing `VerificationReport` to PASS; any required
check FAIL closes it to FAIL. Malformed authority JSON syntax is an
`InputFormatError` because verification context cannot be established. Parsed
but structurally or semantically invalid JSON, artifact corruption, chain
mismatch, stale approval, collision, or closure mismatch returns structured
FAIL. Missing root is `InputMissingError`; invalid locators retain the existing
configuration/pipeline exception families.

The verifier consumes the exact ordered approved-batch tuple so it can
independently reconstruct every manifest/preflight/approval projection and
replay each effective-state prefix. It imports/calls neither the builder nor
the production preflight function and does not trust the writer's candidate
digest.

The `formal_boundary` check passes only for a strict staging descendant and
requires the formal V1.19 tree to remain exact. Candidate-root symlink leaf,
symlink ancestor, symlink loop, resolved escape, or any symlinked artifact
fails the corresponding directory/filesystem/formal-boundary check without
mutation. It always fails for a path under `releases/V1.20`; no Task 10A API
can publish there.

## 15. Rollback and rebuildability

`rollback.json` is canonical JSON plus one LF with exact keys:

```text
schema_version
action
candidate_digest
protected_baseline
candidate_artifacts
```

Its schema is `task10-v120-rollback-v1`; action is
`delete_unpromoted_v120_candidate_tree_if_digest_matches`.
`protected_baseline` is the exact path-free V1.19 baseline identity.
`candidate_artifacts` is the sorted complete list of candidate-relative paths,
including database, manifest, sums, rollback, batch authority files, and
images. The receipt is declarative and grants no deletion authority by itself.

Rollback of a failed private build removes only the Task 10-owned private
temporary tree. Rollback of an unpromoted generation may remove only that whole
generation after its candidate digest and complete artifact closure still
match. It never edits a prior generation or either formal release.

The candidate tree is not the sole source of truth. The same logical candidate
must be rebuildable from exactly:

- the immutable V1.19 formal baseline;
- the ordered ledger/approved-batch tuple;
- each canonical package;
- each exact parent-bound approval.

No cache, timestamp, directory-discovery order, current-candidate pointer, or
hidden mutable registry is required.

## 16. Public surface and closed implementation scope

The V1.20 public surface appends only the approved carriers and APIs to
`joy_m2.ingest.__all__`; all current names and their order remain the unchanged
prefix. Private digest, SQLite, projection, and filesystem helpers are not
exported.

The exact append-only suffix is:

```python
(
    "V120BatchImportManifest",
    "V120AdaptedImportPackage",
    "V120BatchLedgerEntry",
    "V120EffectiveState",
    "V120PreflightRequest",
    "V120ImportPreflightReport",
    "V120ImportPreflightResult",
    "V120ImportApproval",
    "V120ApprovedBatch",
    "V120CandidateContract",
    "V120CandidateBuildRequest",
    "V120CandidateVerificationRequest",
    "V120CandidateArtifacts",
    "load_v120_import_manifest",
    "adapt_mmd_package_v120",
    "preflight_v120_import",
    "build_v120_candidate",
    "verify_v120_candidate",
)
```

Future implementation authority, if separately granted, is closed to:

```text
NEW       src/joy_m2/ingest/v120_models.py
NEW       src/joy_m2/ingest/v120_manifest.py
NEW       src/joy_m2/ingest/v120_projection.py
NEW       src/joy_m2/ingest/v120_preflight.py
NEW       src/joy_m2/ingest/v120_writer_profiles.py
NEW       src/joy_m2/ingest/v120_writer.py
NEW       src/joy_m2/ingest/v120_verification.py
MODIFIED  src/joy_m2/ingest/adapter.py
MODIFIED  src/joy_m2/ingest/source_mapping.py
MODIFIED  src/joy_m2/ingest/__init__.py
NEW       tests/unit/test_v120_models.py
NEW       tests/integration/test_v120_adapter_projection.py
NEW       tests/integration/test_v120_preflight.py
NEW       tests/unit/test_v120_writer_primitives.py
NEW       tests/integration/test_v120_candidate.py
NEW       tests/regression/test_v119_historical_replay.py
FIXTURE   tests/fixtures/task10a/v120-batch-a/**
FIXTURE   tests/fixtures/task10a/v120-batch-b/**
FIXTURE   tests/fixtures/task10a/v120-batch-c/**
DOC       PROJECT_STATE.md
NEW DOC   docs/reports/TASK10A_VERIFICATION.md
```

`v120_projection.py` is the sole new minimal common projection boundary. It
may accept already validated Task 9B Source IR/output components and select the
V1.19 or V1.20 manifest/result carrier. It may not parse MMD, interpret source
mapping, own approvals, or write a database.

`PROJECT_STATE.md` has two distinct authorized updates: the current docs-only
Gate-A authority checkpoint records Design/Plan completion while implementation
remains NOT STARTED; a future update may record implementation completion only
after implementation review. `docs/reports/TASK10A_VERIFICATION.md` is
future-only completion evidence and must not be created at Gate A. No other
production, test, fixture, documentation, data, release, legacy,
project-script, CLI, App/API, or dependency file is authorized by this Design.

## 17. RED-first implementation sequence

No future production behavior may be written before all corresponding tests
have a valid missing-behavior RED. The separately committed Plan freezes:

1. versioned V1.20 public authority models;
2. V1.20 canonical Task 9B target projection;
3. effective-state and parent-digest preflight;
4. V1.20 approval carrier and stale-parent rejection;
5. first approved batch over clean V1.19;
6. second approved batch over the accumulated candidate;
7. third-batch ordering and cross-batch collisions;
8. independent aggregate verifier over an independently authored valid
   candidate-tree oracle;
9. full-prefix aggregate writer that must call the already-GREEN verifier;
10. deterministic rebuild, failure atomicity, and rollback;
11. complete V1.19 historical replay and maintained/frozen gates;
12. real operational read-only adaptation/preflight dry-run, followed by a
    human stop before any real V1.20 candidate write.

Tests must prove first/second/third order, stale preflight, wrong-parent
approval, duplicate against V1.19, duplicate against an earlier V1.20 batch,
ID/source/image collisions, failure preservation, provenance, deterministic
rebuild, exact 502 baseline preservation, historical V1.19 behavior, and the
absence of formal V1.20 artifacts.

## 18. Human gates and operational cadence

After Design/Plan review, commit, and push, implementation remains stopped at:

```text
USER DECISION REQUIRED — V1.20 AUTHORITY IMPLEMENTATION AUTHORIZATION
```

If implementation is later authorized, synthetic tests and temporary/staging
candidate generations remain non-formal. Every real batch still requires the
exact section 9 approval against its current parent digest. A READY preflight
alone authorizes no write.

V1.20 promotion is a separate future Design, Plan, independent review, digest-
bound Human Gate, and formal commit. Task 10A defines no promotion carrier,
builder, verifier, statement, or API.

Operationally, promotion is normally considered after approximately 30–100
new complete questions or completion of a natural chapter group. This is a
recommendation only, never a schema or validation invariant.

## 19. Required regression and frozen gates

Future implementation checkpoints must keep:

- current Task 9A 41/41 PASS;
- current Task 9B 342/342 PASS;
- current Task 9C 71/71 PASS;
- current Task 9D 48/48 PASS;
- the complete maintained suite at or above its current 711-test baseline,
  with every collected maintained test passing and zero skips/expected failures;
- formal V1.19 independent verification 18/18 PASS;
- V1.18 independent validation PASS;
- formal V1.19 SHA/count/release digest exact;
- formal V1.18 SHA/count exact;
- no formal `releases/V1.20/` artifact.

Historical V1.19 digest/approval/candidate/promotion fixtures must retain their
literal results. The actual historical V1.16 ZIP remains neither searched nor
read nor rehashed.

## 20. Non-goals

Task 10A does not build:

- V1.20 formal promotion or current-release switching;
- V1.21 or an arbitrary future-version engine;
- event sourcing, a distributed ledger, cloud storage, or a vector database;
- generic document ingestion, PDF/OCR, a plugin framework, or new question
  generation;
- enrichment completion, AI translation, tag or difficulty generation;
- CLI, App/API, worksheet generation, or automatic candidate retrieval;
- in-place candidate SQLite mutation or formal release mutation.

## 21. Decision register

| Decision | State |
| --- | --- |
| V1.19 formal baseline is immutable and exact | APPROVED |
| V1.20 is a versioned additive authority, not a V1.19 constant change | APPROVED |
| Batch ledger order is append-only acceptance order | APPROVED |
| Every later preflight uses the full effective candidate state | APPROVED |
| Every batch approval binds the exact parent candidate digest | APPROVED |
| Candidate identity is path-free and commits ordered authorities plus rows/images | APPROVED |
| Every generation is a full-prefix rebuild and atomic no-replace staging publication | APPROVED |
| Existing Task 9A issue semantics cover cross-batch collisions | APPROVED |
| V1.19 historical replay is mandatory | APPROVED |
| V1.20 candidate remains non-formal; promotion is excluded | APPROVED |
| 30–100 questions/chapter cadence is operational guidance only | APPROVED |
| Implementation requires a new explicit Human Gate authorization | APPROVED |

No V1 implementation-blocking authority decision remains open. This statement
does not authorize implementation.
