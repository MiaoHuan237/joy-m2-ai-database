# Joy M2 AI Database — Task 9C V1.19 Incremental Candidate Writer Design

Date: 2026-09-11 (Asia/Shanghai)

Status: APPROVED — INDEPENDENT REVIEW PASSED

Task 9A: CLOSED / PASS

Task 9B: CLOSED / PASS

First real V1.19 write: HUMAN GATE B — NOT AUTHORIZED

## 1. Purpose and authority

Task 9C adds the maintained V1.19 incremental candidate writer and its
independent verifier. It consumes one exact, READY Task 9A
`ImportPreflightResult`, the canonical package root needed to re-read approved
image bytes, and one exact digest-bound import approval. It produces a new,
atomic, self-verifying candidate artifact tree under staging.

This Design authorizes Design, Plan, tests, production implementation, and
in-memory or temporary-root execution. It does **not** authorize the first real
V1.19 candidate database or any artifact under the repository's actual
`data/staging/` or `releases/V1.19/`. That operation remains HUMAN GATE B.

Task 9C never edits V1.18. It never imports a real batch without HUMAN GATE C,
and it never promotes a candidate without HUMAN GATE D.

## 2. Required-now architecture

Task 9C is a narrow candidate writer, not a second audit or release framework:

```text
READY Task 9A preflight + exact import approval + explicit package root
-> independent input and approval validation
-> revalidate only consumed image bytes
-> copy frozen V1.18 SQLite to a temporary candidate tree
-> one deterministic transaction adds Task 9 candidate tables
-> deterministic content-addressed image staging
-> canonical manifest + rollback declaration + SHA256SUMS
-> independent read-only verification
-> one atomic directory rename to a new staging destination
```

The implementation must adapt the maintained SQLite authority. It must not
import or call a legacy writer.

## 3. Publication separation and database strategy

Import approval is not formal publication authority. Therefore new Task 9 rows
must not be inserted into `complete_questions_v2` with
`record_status='published'` or `joy_approval='approved_by_joy'`.

The V1.19 candidate SQLite is an exact byte copy of frozen V1.18 followed by a
deterministic additive candidate-schema transaction:

- every pre-existing V1.18 table, view, index, schema SQL, and logical row
  remains unchanged;
- `PRAGMA user_version` becomes exactly `119` in the candidate copy only;
- new candidate rows live only in `task9_import_candidates_v1` and its
  supporting Task 9 tables;
- every new row has `record_status='candidate'` and `selectable=0`;
- the existing `selectable_complete_questions_v2` view remains unchanged and
  continues to expose only the 497 published V1.18 rows;
- projected candidate count is verified as `497 + new_candidate_count`, but
  the formal published count remains 497 until a separately approved
  promotion design acts.

This is the smallest truthful representation. Rebuilding the frozen V2 table,
writing candidate rows as published, or creating a second formal source of
truth is forbidden.

## 4. Public carriers

All carriers are frozen dataclasses with exact runtime-type validation, no
defaults, defensive tuple canonicalization, and no compatibility aliases.
Every annotated domain carrier must be the exact runtime class named below:
subclasses and duck-typed objects are rejected. Path locators use
`isinstance(value, Path)` (so platform `PosixPath`/`WindowsPath` instances are
valid), while strings standing in for paths and `bool` standing in for `int`
are rejected. Paths are resolved with `strict=False` only after validation;
this changes transport location, not semantic identity.

### 4.1 `ImportApproval`

Exact fields and order:

```python
@dataclass(frozen=True)
class ImportApproval:
    batch_id: str
    preflight_sha256: str
    target_release_version: str
    statement: str
```

`target_release_version` is exactly `V1.19`. `preflight_sha256` is an exact
lowercase SHA-256. `statement` is exactly one line:

```text
USER APPROVED IMPORT BATCH <batch_id> <preflight_sha256> V1.19
```

`batch_id` remains otherwise governed by Task 9A, but Task 9C rejects CR or LF
in `batch_id` with `ImportApprovalError` before output creation because such a
value cannot produce this one-line approval statement. This writer entry limit
does not change the Task 9A manifest or digest contract.

No timestamp, runtime path, user-session identity, or promotion approval is
added. Tests may construct a synthetic approval; no real user approval is
implied by tests.

### 4.2 `V119WriterContract`

Exact fields and order:

```python
@dataclass(frozen=True)
class V119WriterContract:
    profile: str
    candidate_manifest_schema: str
    candidate_database_schema: str
    expected_user_version: int
    database_filename: str
    manifest_filename: str
    sha256s_filename: str
    rollback_filename: str
    image_root: str
    required_baseline_tables: tuple[str, ...]
    required_candidate_tables: tuple[str, ...]
    required_candidate_views: tuple[str, ...]
```

The only approved scalar values are:

```text
profile = V1.19
candidate_manifest_schema = task9-v119-candidate-manifest-v1
candidate_database_schema = task9-v119-candidate-v1
expected_user_version = 119
database_filename = Joy_M2_V1.19_candidate.sqlite3
manifest_filename = candidate_manifest.json
sha256s_filename = SHA256SUMS
rollback_filename = rollback.json
image_root = images/sha256
```

Filenames are direct canonical names. `image_root` is a canonical relative
POSIX path. Required object tuples are exact, unique, and deterministic.

The exact object tuples are:

```python
required_baseline_tables = (
    "complete_question_corrections_v2",
    "complete_question_tags_v2",
    "complete_question_taxonomy_v2",
    "complete_questions_v2",
    "import_runs_v2",
    "question_topics",
    "questions",
    "release_metadata_v2",
    "sources",
    "topics",
)
required_candidate_tables = (
    "task9_import_batches_v1",
    "task9_import_candidates_v1",
    "task9_import_images_v1",
    "task9_import_taxonomy_v1",
)
required_candidate_views = ("task9_candidate_questions_v1",)
```

### 4.3 `V119WriteRequest`

Exact fields and order:

```python
@dataclass(frozen=True)
class V119WriteRequest:
    preflight_result: ImportPreflightResult
    package_root: Path
    approval: ImportApproval
    output_dir: Path
    contract: V119WriterContract
```

The request retains the authoritative typed preflight object. Raw candidates,
raw report dictionaries, or a digest without its typed preflight are forbidden.
`package_root` and `output_dir` are transport locators and never enter semantic
identity.

### 4.4 `V119VerificationRequest`

Exact fields and order:

```python
@dataclass(frozen=True)
class V119VerificationRequest:
    candidate_dir: Path
    preflight_result: ImportPreflightResult
    approval: ImportApproval
    contract: V119WriterContract
```

The verifier binds candidate bytes to the same typed preflight and approval. It
does not infer authority from a directory name.

### 4.5 `V119CandidateArtifacts`

Exact fields and order:

```python
@dataclass(frozen=True)
class V119CandidateArtifacts:
    database: ArtifactRef
    manifest: ArtifactRef
    sha256sums: ArtifactRef
    rollback: ArtifactRef
    images: tuple[ArtifactRef, ...]
    verification_report: VerificationReport
```

Artifact references point to final candidate-tree paths. Images are ordered by
candidate destination path. This carrier creates no approval or promotion
authority. Result artifact kinds are exact: database `sqlite`, manifest
`manifest`, sums `sha256sums`, rollback `rollback`, and image `image`.

## 5. Public APIs and package surface

Exact APIs:

```python
def build_v119_candidate(
    request: V119WriteRequest,
    config: PipelineConfig,
) -> V119CandidateArtifacts

def verify_v119_candidate(
    request: V119VerificationRequest,
    config: PipelineConfig,
) -> VerificationReport
```

Task 9C creates `src/joy_m2/ingest/__init__.py`. Its exact `__all__` is the
existing Task 9A surface, followed by Task 9B, followed by Task 9C:

```python
(
    "BatchImportManifest",
    "ImportAdaptation",
    "ImportCandidate",
    "ImportFileEvidence",
    "ImportIssue",
    "ImportPreflightReport",
    "ImportPreflightResult",
    "load_import_manifest",
    "preflight_import",
    "MmdSelection",
    "MmdAdapterManifest",
    "MmdAdapterIssue",
    "MmdAdapterBlockedError",
    "AdaptedImportPackage",
    "adapt_mmd_package",
    "ImportApproval",
    "V119WriterContract",
    "V119WriteRequest",
    "V119VerificationRequest",
    "V119CandidateArtifacts",
    "build_v119_candidate",
    "verify_v119_candidate",
)
```

No private profile, serializer, projection, filesystem, or SQLite helper is
exported. `ImportApprovalError` has the sole public import path
`joy_m2.errors.ImportApprovalError`; it is intentionally absent from
`joy_m2.ingest.__all__`.

## 6. Exact entry gates

Before filesystem output or package-image access, the builder requires:

- exact `V119WriteRequest` and `PipelineConfig` types;
- exact contract constants and object sets;
- exact `ImportPreflightResult`, manifest, report, candidate, issue, baseline
  `ArtifactRef`, and approval carrier types;
- independent reconstruction of the frozen Task 9A path-free manifest and
  preflight digest payloads from the typed object, using the exact committed
  Task 9A algorithm, with both recomputed digests equal their authoritative
  report values; the writer does not call `preflight_import()` or re-read any
  candidate/source/answer/teacher/common-error file;
- report status exactly `READY FOR USER IMPORT APPROVAL`;
- report target exactly `V1.19`, baseline exactly `V1.18`, before count 497,
  approved count 0, projected count closure, and batch/manifest identity equal
  to the typed manifest;
- `issues == ()`, `blocking_errors == ()`, and
  `new_candidate_count == detected_count == len(candidates)`;
- unique candidate IDs in manifest semantic order;
- approval fields and exact statement equal the preflight batch, digest, and
  target version;
- frozen baseline `ArtifactRef` kind/size/SHA/bytes and read-only SQLite
  identity exactly match V1.18, SHA-256
  `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7`,
  `user_version=118`, release metadata V1.18 / `complete-question-v1.0`, 497
  complete V2 rows, integrity `ok`, and zero FK errors;
- `package_root` exists, is a directory, and is safely resolved;
- `output_dir` is a new strict descendant of `config.staging_root`, with no
  symlink/normalization escape and no overlap with the package or baseline.

Mismatched or forged approval raises `ImportApprovalError`, a new
`PipelineError` subtype. A non-READY or internally inconsistent preflight also
raises `ImportApprovalError`; it must never be repaired or re-preflighted by
the writer. Input paths, missing bytes, and output conflicts keep the existing
maintained exception families.

## 7. Image serialization authority

Only images referenced by the READY typed candidates are consumed. For each
candidate image position, source relative path, expected SHA-256, role, and
candidate order come from `ImportCandidate`; size and kind come from the exact
matching manifest `ImportFileEvidence`.

The builder independently resolves each referenced path beneath
`package_root`, rejects symlink escape/non-regular/missing/unreadable inputs,
and verifies exact size and SHA before any output tree is published.

Candidate image destination is content-addressed:

```text
images/sha256/<first-two-digest-characters>/<full-sha256><canonical-extension>
```

Task 9C accepts exactly the source suffixes `.jpg`, `.jpeg`, and `.png`, with
case-insensitive comparison. Canonical extensions are `.jpg` for `.jpg` or
`.jpeg`, and `.png` for `.png`. Any otherwise-valid READY Task 9A image path
with another suffix, including an empty suffix, raises `InputFormatError`
during the entry gate and before any output/temp directory is created. This is
a Task 9C serialization limit and does not change Task 9A's accepted manifest
or candidate contract. Source relative paths retain their approved spelling in
evidence. If one digest appears with conflicting canonical extensions or
different bytes claim one destination, the builder blocks. Identical digest
plus canonical extension is staged once while all ordered question bindings
remain in the manifest and database.

Both collision cases raise `InputFormatError`: (1) one digest is declared with
more than one canonical extension, and (2) byte-distinct sources claim the
same content-addressed destination. The builder completes this image preflight
before creating any output or temporary directory, so either exception leaves
the destination absent and staging unchanged.

Destination paths, never source package paths, are stored in the candidate
SQLite image projection. Existing V1.18 image values remain untouched.

## 8. Candidate SQLite profile

The writer executes the following normalized DDL in this exact object order.
Keywords/whitespace are implementation formatting choices, but identifiers,
column order, declared SQLite types, nullability, defaults, keys, and checks are
exact authority. Default collation is SQLite `BINARY`. There are no
application-created indexes or triggers and no other new SQLite objects;
SQLite internal auto-indexes implied by the declared keys are permitted.
Every constraint uses SQLite's default `ABORT` conflict policy; `OR IGNORE`,
`OR REPLACE`, UPSERT, and partial insertion are forbidden. One candidate tree
contains exactly one batch row.

```sql
CREATE TABLE task9_import_batches_v1 (
    batch_id TEXT PRIMARY KEY,
    target_release_version TEXT NOT NULL CHECK(target_release_version='V1.19'),
    candidate_database_schema TEXT NOT NULL CHECK(candidate_database_schema='task9-v119-candidate-v1'),
    preflight_sha256 TEXT NOT NULL,
    manifest_sha256 TEXT NOT NULL,
    approval_statement TEXT NOT NULL,
    baseline_release_version TEXT NOT NULL CHECK(baseline_release_version='V1.18'),
    baseline_database_sha256 TEXT NOT NULL,
    baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count=497),
    candidate_count INTEGER NOT NULL CHECK(candidate_count>=0),
    projected_question_count INTEGER NOT NULL CHECK(projected_question_count=baseline_question_count+candidate_count),
    record_status TEXT NOT NULL CHECK(record_status='candidate')
);

CREATE TABLE task9_import_candidates_v1 (
    batch_id TEXT NOT NULL REFERENCES task9_import_batches_v1(batch_id),
    candidate_order INTEGER NOT NULL CHECK(candidate_order>=0),
    proposed_question_id TEXT NOT NULL,
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
    image_paths_json TEXT NOT NULL,
    image_sha256s_json TEXT NOT NULL,
    image_roles_json TEXT NOT NULL,
    primary_type TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    tag_status TEXT NOT NULL CHECK(tag_status IN ('source_provided','proposed','missing')),
    difficulty_level INTEGER CHECK(difficulty_level BETWEEN 1 AND 5 OR difficulty_level IS NULL),
    difficulty_status TEXT NOT NULL CHECK(difficulty_status IN ('source_provided','proposed','missing')),
    enrichment_status TEXT NOT NULL CHECK(enrichment_status IN ('complete','incomplete')),
    candidate_image_paths_json TEXT NOT NULL,
    record_status TEXT NOT NULL CHECK(record_status='candidate'),
    selectable INTEGER NOT NULL CHECK(selectable=0),
    PRIMARY KEY(batch_id, proposed_question_id),
    UNIQUE(batch_id, candidate_order)
);

CREATE TABLE task9_import_images_v1 (
    batch_id TEXT NOT NULL,
    proposed_question_id TEXT NOT NULL,
    image_order INTEGER NOT NULL CHECK(image_order>=0),
    source_relative_path TEXT NOT NULL,
    candidate_relative_path TEXT NOT NULL,
    sha256 TEXT NOT NULL,
    size_bytes INTEGER NOT NULL CHECK(size_bytes>=0),
    kind TEXT NOT NULL CHECK(kind='image'),
    role TEXT NOT NULL,
    PRIMARY KEY(batch_id, proposed_question_id, image_order),
    FOREIGN KEY(batch_id, proposed_question_id)
        REFERENCES task9_import_candidates_v1(batch_id, proposed_question_id)
);

CREATE TABLE task9_import_taxonomy_v1 (
    batch_id TEXT NOT NULL REFERENCES task9_import_batches_v1(batch_id),
    taxonomy_kind TEXT NOT NULL CHECK(taxonomy_kind IN ('primary_type','tag')),
    value TEXT NOT NULL,
    sort_order INTEGER NOT NULL CHECK(sort_order>=1),
    PRIMARY KEY(batch_id, taxonomy_kind, value),
    UNIQUE(batch_id, taxonomy_kind, sort_order)
);

CREATE VIEW task9_candidate_questions_v1 AS
SELECT *
FROM task9_import_candidates_v1
ORDER BY batch_id, candidate_order;
```

### 8.1 Exact row projections

The batch row stores the exact approval/preflight identity. Both digest columns
are lowercase 64-hex values. `candidate_count` equals
`len(preflight_result.candidates)` and `projected_question_count` equals the
unchanged Task 9A report value. It stores no timestamp and no database
self-hash. This table is the candidate-stage hash-bound import/migration record;
there is no separate migration artifact, and formal-only `import_runs_v2`
remains byte/logically unchanged.

The candidate table stores all 25 `ImportCandidate` fields in dataclass order.
The tuple-field mapping is exactly `image_paths -> image_paths_json`,
`image_sha256s -> image_sha256s_json`, `image_roles -> image_roles_json`, and
`tags -> tags_json`; every other field retains its dataclass name. Tuple values
use canonical compact JSON arrays with UTF-8 semantics and no trailing LF.
`candidate_image_paths_json` is the ordered destination-path array corresponding
one-for-one to source `image_paths`. Optional model values use SQL NULL; legal
empty text remains empty text. Candidate order is the Task 9A tuple order and
starts at zero with no gaps.

The image table stores one row per candidate binding in candidate order then
image position. The taxonomy table stores distinct primary types and tags:
rows are grouped in `primary_type`, then `tag` order; within each kind values
are Unicode-code-point sorted and `sort_order` starts at one independently for
each kind. Therefore the same text may legally appear once under each kind and
is never ambiguous.

The candidate table does not invent V2-only source files, pages, audit
timestamps, corrections, publication evidence, or review claims. The original
497 V2 rows remain the only rows in `complete_questions_v2`. The view exposes
the candidate table's exact DDL column order and grants no selectability or
publication authority.

## 9. Teacher notes, common errors, and other evidence

Teacher notes and common errors remain hashed Task 9 evidence only. They are
not written into V2 fields, candidate question columns, or image assets. The
candidate manifest retains their exact ordered four-field evidence entries, so
exclusion from the database is explicit and audit-visible rather than silent.

The same manifest evidence projection preserves candidate JSON, source, and
answer file identities without copying those source files into the candidate
tree. Task 9A remains their parsing and digest authority.

## 10. Candidate manifest

`candidate_manifest.json` is UTF-8 canonical JSON plus exactly one LF. It has
exactly these top-level keys:

For this Design, canonical JSON bytes are exactly:

```python
json.dumps(
    value,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

JSON artifact files append one and only one `b"\n"`; database JSON text columns
use the canonical bytes decoded as UTF-8 without an appended LF.

```text
schema_version
release_version
release_status
release_model
batch
baseline
counts
database
images
candidate_record_evidence
source_evidence
answer_evidence
teacher_notes_evidence
common_errors_evidence
rollback
```

Exact fixed identity:

```text
schema_version = task9-v119-candidate-manifest-v1
release_version = V1.19
release_status = candidate
release_model = incremental-import-candidate
```

The following JSON-shape notation is exact. `str`, `int`, and `list` mean exact
runtime JSON types; `bool` is never accepted as `int`. Every object rejects
missing and extra keys. Digests are lowercase 64-hex strings, sizes/counts are
non-negative integers, and relative paths are canonical POSIX paths. Fixed
literals are shown quoted:

```text
batch = {
  batch_id: str,
  preflight_sha256: sha256,
  manifest_sha256: sha256,
  approval_statement: str,
  candidate_database_schema: "task9-v119-candidate-v1"
}

baseline = {
  release_version: "V1.18",
  question_count: 497,
  schema_version: "complete-question-v1.0",
  sqlite: {sha256: sha256, size_bytes: int, kind: "sqlite"}
}

counts = {
  before_count: int,
  detected_count: int,
  new_candidate_count: int,
  duplicate_count: int,
  rejected_count: int,
  ambiguous_count: int,
  approved_count: int,
  projected_after_count: int
}

relative_artifact = {
  relative_path: canonical_relative_path,
  sha256: sha256,
  size_bytes: int,
  kind: str
}

file_evidence = {
  relative_path: canonical_relative_path,
  sha256: sha256,
  size_bytes: int,
  kind: "candidate_json" | "source" | "answer" |
        "teacher_notes" | "common_errors"
}

image_binding = {
  proposed_question_id: str,
  image_order: int,
  source_relative_path: canonical_relative_path,
  role: str
}

image_entry = {
  relative_path: canonical_relative_path,
  sha256: sha256,
  size_bytes: int,
  kind: "image",
  bindings: list[image_binding]
}
```

`database` is one `relative_artifact` with exact kind `sqlite` and relative
path equal `contract.database_filename`. `rollback` is one
`relative_artifact` with exact kind `rollback` and relative path equal
`contract.rollback_filename`. The result carrier additionally binds the
manifest, sums, and image files with the exact kinds defined in section 4.5.

`candidate_record_evidence`, `source_evidence`, `answer_evidence`,
`teacher_notes_evidence`, and `common_errors_evidence` are arrays of exact
`file_evidence` projections from their correspondingly named Task 9A manifest
groups, preserving each group's manifest order. No Task 9A `image_files` entry
appears in these five arrays; image source evidence is preserved by the
physical image entry plus each ordered binding and is cross-checked against
the exact Task 9A image evidence.

`images` is an array of exact `image_entry` objects ordered by candidate
destination path. A physical image appears once. Its `bindings` array is
ordered by Task 9A candidate order then zero-based image position; it is never
deduplicated. `counts` is the exact projection of the eight same-named Task 9A
report fields and is not recomputed into a new approval count. `batch` and
`baseline` are the exact projections described above.

Absolute paths, package/output/temp roots, cwd, timestamps, memory identity,
database self-hash, and environment data are forbidden.

The final candidate tree has exactly this layout and no other files:

```text
<output_dir>/
  Joy_M2_V1.19_candidate.sqlite3
  candidate_manifest.json
  SHA256SUMS
  rollback.json
  images/sha256/<prefix>/<digest><canonical-extension>  # zero or more
```

## 11. SHA256SUMS and rollback declaration

`SHA256SUMS` is UTF-8, LF-only, sorted by candidate-relative path, and contains
exactly the database, every physical image, rollback JSON, and manifest. It
does not contain itself. Each line is exactly
`<lowercase-sha256><two ASCII spaces><canonical-relative-path><LF>`; the file is
non-empty and ends with exactly one LF. Binary markers (`*`), escaping,
backslash paths, blank lines, comments, duplicate paths, extra whitespace, and
non-UTF-8 bytes are forbidden.

`rollback.json` is canonical JSON plus one LF with exact keys:

```text
schema_version
action
batch_id
preflight_sha256
baseline
candidate_artifacts
```

Its fixed schema is `task9-v119-rollback-v1`; action is
`delete_unpromoted_candidate_tree`. `batch_id` and `preflight_sha256` are the
exact approved values. `baseline` is the exact four-key manifest `baseline`
object from section 10, including its nested path-free SQLite identity.
`candidate_artifacts` is an array of exact canonical relative-path strings,
Unicode-code-point sorted, unique, and complete: database, physical images,
manifest, SHA256SUMS, and rollback itself. No artifact object or absolute path
is permitted in that array. This is a declarative rollback receipt, not an
executable deletion script. Because Task 9C creates only a new candidate tree
and never edits the baseline, rollback is removal of that unpromoted tree.

## 12. Independent verification

`verify_v119_candidate()` is read-only and never repairs, deletes, or rewrites
an artifact. It returns the existing structured `VerificationReport`; any
required failed check closes status to `FAIL`.

The result boundary is exhaustive:

| condition | result |
| --- | --- |
| request/config/carrier has a wrong runtime type or invalid locator | existing `PipelineError` / `ConfigurationError` family |
| candidate root does not exist | `InputMissingError` |
| candidate root exists but is not a contained directory | `InputFormatError` |
| manifest is missing or unreadable | `InputMissingError` / `InputFormatError` respectively |
| manifest bytes are invalid UTF-8, JSON syntax is malformed, or no JSON value can be parsed | `InputFormatError` |
| parsed manifest is a non-mapping, has wrong/missing/extra fields, wrong runtime values, or a malformed digest field | structured `VerificationReport(status="FAIL")` |
| SHA256SUMS is missing | structured `FAIL` |
| SHA256SUMS is unreadable, invalid UTF-8, or has malformed line syntax/digest tokens | `InputFormatError` |
| artifact is missing, extra, unreadable, wrong kind, wrong size, or hash-mismatched | structured `FAIL` |
| SQLite cannot be opened/read as a database, has wrong schema/content, fails integrity/FK checks, or has a closure mismatch | structured `FAIL` |
| parsed rollback/image/database content is structurally or semantically invalid | structured `FAIL` |

Every structured PASS or FAIL report always contains exactly these checks in
order; only the exception rows in the matrix return no report:

```text
candidate_directory
manifest_contract
preflight_approval_binding
filesystem_closure
sha256sums_closure
artifact_references
rollback_contract
image_projection
sqlite_readability
sqlite_integrity
sqlite_foreign_keys
sqlite_schema
sqlite_projection
baseline_preservation
count_closure
publication_boundary
```

Each `VerificationCheck.name` is the literal above. `passed` has exact runtime
type `bool`. `detail` is exactly `PASS` when true and `FAIL` when false; it
never embeds paths, exception prose, unordered diagnostics, or environment
data. A failed prerequisite does not omit later checks: every dependent check
is safely short-circuited to `(passed=False, detail="FAIL")`. Final status is
`PASS` only when all sixteen checks pass and is otherwise `FAIL`.
For example, a missing SHA256SUMS produces the complete tuple with
`filesystem_closure` and `sha256sums_closure` failed and every check that needs
the sums safely failed; it never returns a shortened report.

It verifies independently:

- exact candidate directory containment and exact filesystem closure;
- manifest syntax, exact top-level/nested schema, fixed identity, runtime
  types, and typed preflight/approval bindings;
- SHA256SUMS syntax, ordering, file set, and byte hashes;
- every `ArtifactRef` hash/size/kind;
- rollback schema, baseline binding, and complete path closure;
- image destination formula, binding order, deduplication, bytes, SHA, size,
  suffix, and database/manifest equality;
- SQLite `user_version=119`, integrity, FK closure, required objects, batch row,
  exact candidate rows/order/values, taxonomy, and projected counts;
- byte-identical schema SQL and logical contents for every pre-existing V1.18
  table, view, and index;
- frozen `complete_questions_v2` count 497 and candidate count equal the Task
  9A new count;
- no published/selectable Task 9 candidate and no mutation of V1.18 metadata.

The builder must call the same independent verifier against the complete
temporary tree and publish only after PASS.

## 13. Transaction, determinism, and atomicity

The builder creates one private temporary sibling inside the staging parent,
copies the frozen baseline database, enables foreign keys, uses
`BEGIN IMMEDIATE`, creates/inserts all Task 9 objects in fixed order, sets
`user_version=119`, commits, checks integrity/FKs, runs one deterministic
`VACUUM`, and normalizes the non-semantic SQLite header library version to the
existing maintained constant.

All candidates follow manifest order; taxonomy, artifacts, and physical images
use the explicit orders above. No wall-clock time, random ID, tempfile name,
root path, filesystem iteration, hash-map/set iteration, SQLite row discovery
order, or ZIP metadata enters output bytes.

Equivalent inputs under distinct absolute roots must produce identical
database, image, manifest, rollback, and SHA256SUMS bytes and identical artifact
hashes.

The final destination must not exist. Publication is one atomic directory
rename. Every exception removes only the known temporary sibling and leaves
the final destination absent. It never deletes or mutates source, baseline, or
unrelated staging content.

## 14. Promotion boundary

The Task 9C promotion contract is closed as a prohibition: no Task 9C carrier,
API, artifact, PASS report, or `ImportApproval` authorizes promotion. The
candidate manifest SHA-256 is the only future Task 9D candidate identity input,
but this Design adds no promotion API or formal-release approval carrier.
Future promotion must first obtain separate Design/Plan authority plus HUMAN
GATE D, independently verify the complete candidate, consume a distinct
formal-release approval, preserve import approval as evidence only, and
atomically create a new `releases/V1.19/` tree. It may not infer promotion
authority from `ImportApproval`, candidate existence, or verification PASS.

The exact formal-row merge/export/release packaging and promotion operation
remain deferred because defining them would change formal release authority and
therefore belongs behind HUMAN GATES A/D. No Task 9C test may call
`promote_candidate()` for V1.19. This negative-only boundary is the complete
promotion contract required before the candidate writer may proceed; it grants
no future implementation authority.

## 15. TDD and checkpoint sequence

### Phase A — public contracts

1. Add model and package-surface tests first.
2. Prove RED only because Task 9C carriers/error/API surface do not exist.
3. Implement the error/carriers and create signature-only API scaffolds in
   `writer.py` and `writer_verification.py`. Each scaffold has the exact public
   signature in section 5 and raises exactly
   `NotImplementedError("Task 9C writer behavior is not implemented")`; it does
   no I/O, validation, hashing, or serialization.
4. Create `ingest/__init__.py` only to re-export the approved surface, then
   restore focused model/signature/package-surface GREEN.
5. Obtain independent review and commit this public-contract checkpoint.

### Phase B — writer and verifier behavior

Before modifying any writer/profile/verifier production file, establish and
validate all behavior RED groups:

1. database/profile/row projection and V1.18 logical-preservation RED;
2. image destination/deduplication/integrity RED;
3. manifest/SHA/rollback/verifier RED;
4. builder approval/preflight gate, transaction, deterministic-root,
   atomicity, cleanup, and non-mutation RED.

All tests must import successfully. A missing public-model dependency, setup
error, fixture error, or environment error is not valid behavior RED. Only
after all groups have valid RED may production behavior begin.

Implement minimal GREEN in dependency order, run all focused and maintained
gates, obtain independent review, remediate every Critical/Important finding
with its own valid RED, and commit one implementation checkpoint.

All tests and builds before HUMAN GATE B must use in-memory or OS temporary
roots. They must assert that the real repository retains zero V1.19 artifacts.

## 16. Exact implementation scope

Phase A may modify only:

```text
src/joy_m2/errors.py
src/joy_m2/ingest/__init__.py
src/joy_m2/ingest/writer_models.py
src/joy_m2/ingest/writer.py
src/joy_m2/ingest/writer_verification.py
tests/unit/test_v119_writer_models.py
```

Phase B may modify the two approved scaffolds and additionally create only:

```text
src/joy_m2/ingest/writer_profiles.py
tests/unit/test_v119_writer_primitives.py
tests/integration/test_v119_writer.py
```

No existing Task 9A/9B production or test file may change. No Database, Audit,
Export, Release, CLI, data, releases, legacy, frozen artifact, or Task 8 file
may change.

Implementation commits contain only the Phase A or Phase B code/test files
above. After the reviewed Phase A implementation commit, a separate docs-only
checkpoint may modify only `PROJECT_STATE.md`. After the reviewed Phase B
implementation commit, the closure docs-only checkpoint may modify only
`PROJECT_STATE.md` and create `docs/reports/TASK9C_VERIFICATION.md`. No docs
file may be mixed into an implementation commit, and neither docs checkpoint
may change Design/Plan authority or any code, test, data, release, legacy, or
frozen artifact.

## 17. Required gates

Each checkpoint runs its focused tests, the complete maintained suite, Task 9A
41/41, Task 9B 214/214, Task 7 7/7, Task 8 equivalence 3/3, Release 48/48,
Task 3-6 54/54, V1.18 independent validator, legacy attribution (only the
approved 9 PASS / 2 FAIL), `git diff --check`, exact scope, and frozen SHA/count.

Passing maintained suites require zero skip and zero expected failure.

Before the first real V1.19 artifact, report exact target files, frozen source
baseline, this proposed schema, projected counts, expected deterministic SHA
behavior, rollback, V1.18 zero-impact evidence, and writer-test status, then
stop with:

```text
USER DECISION REQUIRED — FIRST V1.19 WRITE AUTHORIZATION
```

## 18. Deferred and forbidden work

Deferred to Task 9D or later:

- first real batch approval and write;
- merge of candidate rows into a formal complete-question table;
- formal V1.19 exports, archive, release verification, and promotion;
- candidate-to-formal status/selectability transition;
- direct PDF/OCR;
- teacher-note/common-error formal schema fields.

Forbidden in Task 9C:

- any V1.18 mutation;
- any path under real `releases/V1.19/`;
- treating import approval as promotion;
- changing Task 9A manifest/candidate/digest/taxonomy;
- changing Task 9B adapter authority;
- legacy imports or a second writer;
- generic workflow/plugin/ingestion frameworks;
- CLI/App/API work;
- force push, merge, rebase, or history rewrite.

## 19. Decision register

| Decision | Classification | Status |
|---|---|---|
| additive candidate tables; frozen V2 rows remain formal | REQUIRED NOW | APPROVED |
| exact digest-bound `ImportApproval` carrier | REQUIRED NOW | APPROVED |
| content-addressed candidate image destinations | REQUIRED NOW | APPROVED |
| explicit exclusion plus manifest binding for teacher/common evidence | REQUIRED NOW | APPROVED |
| canonical candidate manifest, sums, rollback receipt | REQUIRED NOW | APPROVED |
| independent structured verifier | REQUIRED NOW | APPROVED |
| formal-row merge and V1.19 promotion | DEFER | HUMAN GATES C/D |
| direct PDF/OCR or generic framework | DO NOT BUILD | CLOSED |

## 20. Exit condition

This Design becomes executable only after independent review reports zero
Critical and zero Important findings and the Design is committed. Then a
separate implementation Plan must be authored, independently reviewed, and
committed before Phase A RED.

Task 9C implementation may complete with temporary-root evidence, but execution
must stop before the first real V1.19 candidate/formal write artifact at HUMAN
GATE B.
