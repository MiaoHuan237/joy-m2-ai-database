# Joy M2 AI Database — V1.21 Formal Promotion Readiness Design

Date: 2026-09-19 (Asia/Shanghai)

Status: proposed executable authority; formal publication requires a later exact
human gate

## 1. Purpose and boundary

This task proves that the exact accumulated V1.21 generation `000004` can be
promoted from immutable formal V1.20 without changing approved question content.
It is the smallest versioned successor to the V1.20 promotion pipeline. It is
not a generic release engine, new ingestion framework, or authority to ingest
2019 or begin V1.22.

This Design authorizes a version-specific implementation Plan, RED-first tests,
promotion models and behavior, two deterministic non-formal dry-runs, an
independent verifier, rollback validation, historical regression, review,
documentation, ordinary commits, and ordinary pushes. It does **not** authorize
creation of `releases/V1.21/`. Until exact final approval is received:

- formal current remains V1.20 at 543 complete questions;
- `releases/V1.21/` remains absent, including transiently;
- all real promotion builds remain below `data/staging/`;
- no release pointer, current-release index, or consumer selection changes;
- 2019 ingestion and V1.22 work remain out of scope.

Readiness stops at:

```text
USER DECISION REQUIRED — FINAL V1.21 PROMOTION AUTHORIZATION
```

## 2. Exact promotion envelope

Only this exact authority is eligible:

| Authority | Exact value |
|---|---|
| baseline | `V1.20` |
| baseline formal count | `543` |
| baseline SQLite | `releases/V1.20/Joy_M2_Complete_Question_DB_V1_20.sqlite3` |
| baseline SQLite SHA-256 | `b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292` |
| baseline SQLite size | `9768960` |
| baseline manifest SHA-256 | `19ac2e43ded74a3f3eaf75c184b5eb231c9f1b0b152f5914cd822a321b045098` |
| baseline manifest size | `6643` |
| baseline release digest | `1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf` |
| candidate generation | `000004` |
| candidate directory | `data/staging/task11-v121-hkdse-2018/candidate-generation-000004` |
| candidate digest | `ecf624e3cb9fd8e7b1e0c664ddc5d51ef67f2d7f16f277c276be828eba32282c` |
| candidate SQLite SHA-256 | `6e27e5b5eff5a701b4671a3e12ee538eed985147d86c23edef1e9489f714a53c` |
| candidate SQLite size | `9957376` |
| candidate manifest SHA-256 | `dc82e04639a4b54e24bbf7eceeb4ecec8a3751dfa7e8595f260b9d894d91fc83` |
| candidate manifest size | `6849` |
| accepted batch count | `4` |
| approved additions | `48` |
| projected formal count | `591` |
| candidate images | `0` |

Older generations, reconstructed candidates, parallel carriers, or equivalent
content with a different byte identity are ineligible. The builder and verifier
both require the current candidate verifier to return all 24 ordered checks as
PASS before reading candidate rows for promotion.

## 3. Ordered ledger closure

The builder and verifier independently close this exact chain:

1. `000001 — JOY-M2-HKDSE-2015-PP-MS — 12`, parent
   `331192032f184a44ed383e6dacc2f06fbacb60ad94414298fcb935ff56cb5906`;
2. `000002 — JOY-M2-HKDSE-2016-PP-MS — 12`, parent
   `2716ddff85775c15a332bcf7716749c6976d834ae8f20a114b64f108844c0e36`;
3. `000003 — JOY-M2-HKDSE-2017-PP-MS — 12`, parent
   `59f424d5aae3fd67eddceef9202a4de63eb42899dcf7a9b0a78bbe567d39adb0`;
4. `000004 — JOY-M2-HKDSE-2018-PP-MS — 12`, parent
   `b9439dc14799504788d7a663b0bf789df2898dcf0d273dd4fac7fea9cb1dbcdf`.

The cumulative additions are `12, 24, 36, 48`; projected counts are
`555, 567, 579, 591`. The final preflight SHA-256 is
`32808eeeace90852c8fa9749ad37c484f4ca90fe8c4a4c99f1645427c22a6108`.
Every stored manifest, preflight, import approval, transcription evidence,
source PP/MS identity, and parent link remains immutable provenance. Promotion
does not regenerate or reinterpret any of them.

## 4. Architecture

```text
exact V1.21 generation 000004 + exact typed four-batch authority
    -> verify_v121_candidate (24/24 PASS)
    -> copy candidate SQLite into a private staging build tree
    -> in one transaction add V1.21 promotion metadata and 48 projections
    -> retain all V1.20 and V1.21 candidate/ledger tables as evidence
    -> create formal_complete_questions_v121 (543 preserved + 48 promoted)
    -> write canonical manifest, rollback receipt, and SHA256SUMS.txt
    -> independently verify the complete private release tree
    -> atomically rename without replacement to a non-formal dry-run root

verified dry-run + later exact final human approval
    -> re-verify the exact public staging dry-run
    -> copy it to a private sibling of releases/V1.21
    -> compare the private copy byte-for-byte with the approved dry-run
    -> atomically rename without replacement to releases/V1.21
    -> independently verify only the exact formal target
```

The real repository must not execute the second path during readiness. Tests
exercise it only inside isolated temporary repository roots. Existing targets
always conflict; no overwrite, merge, or replace behavior exists.

## 5. Public contracts and API

Create exact versioned carriers:

```python
@dataclass(frozen=True)
class V121PromotionContract:
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
class V121PromotionBuildRequest:
    candidate: V121CandidateVerificationRequest
    output_dir: Path
    contract: V121PromotionContract

@dataclass(frozen=True)
class V121PromotionVerificationRequest:
    release_dir: Path
    candidate: V121CandidateVerificationRequest
    contract: V121PromotionContract

@dataclass(frozen=True)
class V121ReleasePromotionApproval:
    release_version: str
    release_digest: str
    statement: str

@dataclass(frozen=True)
class V121PublicationRequest:
    dry_run_dir: Path
    candidate: V121CandidateVerificationRequest
    approval: V121ReleasePromotionApproval
    contract: V121PromotionContract

@dataclass(frozen=True)
class V121PromotionArtifacts:
    database: ArtifactRef
    manifest: ArtifactRef
    sha256sums: ArtifactRef
    rollback: ArtifactRef
    images: tuple[ArtifactRef, ...]
    release_digest: str
    verification_report: VerificationReport
```

The exact contract values in field order are:

```text
V1.21
task11-v121-formal-manifest-v1
task11-v121-formal-v1
task11-v121-promotion-identity-v1
task11-v121-formal-rollback-v1
121
Joy_M2_Complete_Question_DB_V1_21.sqlite3
manifest.json
SHA256SUMS.txt
rollback.json
images/sha256
task11_v121_promoted_questions_v1
task11_v121_promotion_v1
formal_complete_questions_v121
```

Public APIs are:

```python
build_v121_promotion(request, config) -> V121PromotionArtifacts
verify_v121_promotion(request, config) -> VerificationReport
publish_v121_release(request, config) -> V121PromotionArtifacts
```

The six carriers and three APIs append to `joy_m2.ingest.__all__` in this order.
Every pre-existing export remains an exact unchanged prefix. V1.19 and V1.20
types and behavior remain untouched.

## 6. Final human gate

The release digest is the lowercase SHA-256 of the canonical promotion identity
in section 10. Publication accepts only:

```text
USER APPROVED RELEASE PROMOTION V1.21 <release_digest>
```

The approval must be an exact `V121ReleasePromotionApproval`, must bind the
verified dry-run digest, and may be consumed only by `publish_v121_release()`.
Import approvals and all earlier V1.19/V1.20 promotion approvals are invalid.
Readiness work never constructs or invokes this approval against the real repo.

## 7. Formal database semantics

The copied candidate database retains every V1.20 formal relation and every
V1.21 candidate/provenance relation. One transaction adds the promotion table,
the promoted table, and the formal view defined below, updates only the exact
metadata keys in section 7.4, and leaves `PRAGMA user_version=121`.

For the 48 V1.21 rows only:

- `record_status` changes from `candidate` to `published`;
- `selectable` changes from exact integer `0` to exact integer `1`;
- `authority_kind` becomes `task11_v121_promoted`.

Every other field remains value-identical. The first 543 formal rows remain
identical to `formal_complete_questions_v120`. All 591 rows are published and
selectable in `formal_complete_questions_v121`; no approved record remains
candidate-only in the formal projection.

### 7.1 Promotion metadata table

Modulo ASCII whitespace and one optional terminal semicolon:

```sql
CREATE TABLE task11_v121_promotion_v1 (
    release_version TEXT PRIMARY KEY CHECK(release_version='V1.21'),
    formal_database_schema TEXT NOT NULL CHECK(formal_database_schema='task11-v121-formal-v1'),
    release_model TEXT NOT NULL CHECK(release_model='append-only-multi-batch-promotion'),
    release_status TEXT NOT NULL CHECK(release_status='published'),
    baseline_release_version TEXT NOT NULL CHECK(baseline_release_version='V1.20'),
    baseline_database_sha256 TEXT NOT NULL CHECK(baseline_database_sha256='b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292'),
    baseline_release_digest TEXT NOT NULL CHECK(baseline_release_digest='1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf'),
    baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count=543),
    candidate_digest TEXT NOT NULL CHECK(candidate_digest='ecf624e3cb9fd8e7b1e0c664ddc5d51ef67f2d7f16f277c276be828eba32282c'),
    candidate_database_sha256 TEXT NOT NULL CHECK(candidate_database_sha256='6e27e5b5eff5a701b4671a3e12ee538eed985147d86c23edef1e9489f714a53c'),
    candidate_database_size INTEGER NOT NULL CHECK(candidate_database_size=9957376),
    candidate_manifest_sha256 TEXT NOT NULL CHECK(candidate_manifest_sha256='dc82e04639a4b54e24bbf7eceeb4ecec8a3751dfa7e8595f260b9d894d91fc83'),
    candidate_manifest_size INTEGER NOT NULL CHECK(candidate_manifest_size=6849),
    accepted_batch_count INTEGER NOT NULL CHECK(accepted_batch_count=4),
    promoted_question_count INTEGER NOT NULL CHECK(promoted_question_count=48),
    formal_question_count INTEGER NOT NULL CHECK(formal_question_count=591)
)
```

Every integer boundary rejects booleans.

### 7.2 Promoted question table

```sql
CREATE TABLE task11_v121_promoted_questions_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal BETWEEN 1 AND 4),
    batch_id TEXT NOT NULL,
    batch_candidate_order INTEGER NOT NULL CHECK(batch_candidate_order>=0),
    formal_order INTEGER PRIMARY KEY CHECK(formal_order BETWEEN 544 AND 591),
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
        REFERENCES task11_v121_batch_ledger_v1(batch_ordinal,batch_id)
)
```

Rows come from `task11_v121_candidates_v1 ORDER BY aggregate_order`. The only
renames are `aggregate_order -> formal_order`, `proposed_question_id ->
question_id`, the three source image JSON fields, and
`candidate_image_paths_json -> formal_image_paths_json`; all intervening values
preserve exact order and value.

### 7.3 Formal view

```sql
CREATE VIEW formal_complete_questions_v121 AS
SELECT * FROM formal_complete_questions_v120
UNION ALL
SELECT
    p.formal_order,
    p.question_id,
    'task11_v121_promoted' AS authority_kind,
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
FROM task11_v121_promoted_questions_v1 AS p
ORDER BY formal_order
```

### 7.4 Exact metadata delta

Exactly these `release_metadata_v2` keys are inserted or updated:

```text
release_version = V1.21
baseline_version = V1.20
baseline_sqlite_sha256 = b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292
release_model = append-only-multi-batch-promotion
schema_version = task11-v121-formal-v1
formal_question_count = 591
task11_baseline_release_digest = 1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf
task11_candidate_digest = ecf624e3cb9fd8e7b1e0c664ddc5d51ef67f2d7f16f277c276be828eba32282c
task11_candidate_sqlite_sha256 = 6e27e5b5eff5a701b4671a3e12ee538eed985147d86c23edef1e9489f714a53c
task11_candidate_manifest_sha256 = dc82e04639a4b54e24bbf7eceeb4ecec8a3751dfa7e8595f260b9d894d91fc83
task11_accepted_batch_count = 4
task11_promoted_questions = 48
```

All historical keys remain exact.

## 8. Formal artifact contract

The current exact release tree has four regular files and no images:

```text
Joy_M2_Complete_Question_DB_V1_21.sqlite3
manifest.json
SHA256SUMS.txt
rollback.json
```

Canonical JSON is UTF-8, `ensure_ascii=False`, sorted keys, compact separators,
`allow_nan=False`, and one terminal LF. `SHA256SUMS.txt` has one lowercase
digest, two ASCII spaces, and one canonical relative path per LF-terminated
line, ordered by UTF-8 path bytes, excluding itself and binding the other three
files.

The manifest has exactly these top-level keys:

```text
schema_version, release_version, release_status, release_model,
database_schema, baseline, candidate, batch_ledger,
batch_authority_artifacts, counts, database, images, artifacts,
rollback, promotion, verification
```

Its fixed values include:

```text
schema_version = task11-v121-formal-manifest-v1
release_version = V1.21
release_status = published
release_model = append-only-multi-batch-promotion
database_schema = task11-v121-formal-v1
counts = {baseline_question_count: 543, accepted_batch_count: 4,
          promoted_question_count: 48, formal_question_count: 591}
images = []
promotion.formal_target = releases/V1.21
promotion.gate = FINAL
verification.authority = verify_v121_promotion
verification.required_status = PASS
```

`baseline` binds the exact V1.20 release version, release digest, database
schema, SQLite hash/size, and manifest hash/size in section 2. `candidate` binds
generation 4, V1.21 candidate schema/status, candidate digest, SQLite hash/size,
and manifest hash/size. `batch_ledger` and `batch_authority_artifacts` are the
exact ordered projections from the candidate manifest without rewriting.
Mappings reject missing and extra keys; exact integers reject booleans; paths
reject absolute, empty, dot, dot-dot, backslash, NUL, and non-normalized forms.

## 9. Rollback and atomicity

The rollback receipt is exactly:

```text
schema_version = task11-v121-formal-rollback-v1
release_version = V1.21
release_digest = <exact readiness digest>
action = remove_release_tree_if_release_digest_matches
protected_baseline = {
  release_version: V1.20,
  question_count: 543,
  sqlite_sha256: b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292,
  release_digest: 1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf
}
candidate_digest = ecf624e3cb9fd8e7b1e0c664ddc5d51ef67f2d7f16f277c276be828eba32282c
release_artifacts = <UTF-8-path-sorted exact four-file set>
```

Before publication, failure removes only the newly created private/unpublished
tree. After publication, automatic removal is permitted only when the target's
release digest and complete regular-file fingerprint still equal the approved
dry-run. Any mismatch retains the target for manual recovery. No rollback path
rewrites V1.20, V1.19, V1.18, a candidate generation, or source data.

## 10. Deterministic identities

The SQLite semantic mapping follows the committed V1.20 algorithm, with exact
schema `task11-v121-sqlite-semantic-v1`, `user_version=121`, all non-internal
schema objects and tables ordered identically, and the formal view included once
in `formal_order`. Its canonical JSON digest is the semantic SHA-256.

The promotion identity is exactly:

```text
{
  schema_version: task11-v121-promotion-identity-v1,
  release_version: V1.21,
  contract: <14 fields in dataclass order>,
  baseline: <exact manifest baseline>,
  candidate: <exact manifest candidate>,
  batch_ledger: <exact ordered four-entry ledger>,
  batch_authority_artifacts: <exact ordered eight-entry projection>,
  counts: <exact manifest counts>,
  formal_sqlite_sha256: <sha256>,
  formal_sqlite_size_bytes: <exact int>,
  formal_sqlite_semantic_sha256: <sha256>,
  images: [],
  rollback_action: remove_release_tree_if_release_digest_matches
}
```

Its canonical JSON SHA-256 is the release digest. Absolute paths, temporary
roots, mtimes, and host state are excluded. Two independent builds must have
byte-identical SQLite, manifest, sums, rollback, ArtifactRefs, semantic digest,
and release digest. No semantic-only exception is authorized.

## 11. Independent formal verifier

The verifier is implemented independently of builder helpers and returns these
ordered checks:

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
v120_preservation
batch_ledger_closure
promotion_projection
formal_query
count_closure
provenance_closure
deterministic_identity
publication_boundary
```

It independently proves 24/24 candidate verification, exact generation and
three hashes, the four-parent ledger, 543 + 48 = 591 closure, unchanged baseline
rows, exact promoted values, no candidate-only leakage, provenance links,
manifest/SHA/filesystem closure, and the formal/non-formal boundary. Parsed
corruption produces structured FAIL; malformed JSON follows the existing input
format exception boundary. Verification is read-only and never repairs output.

## 12. Path and publication boundary

Build output must be a new strict descendant of the configured real
`data/staging` root. It must not equal, contain, or be contained by V1.18,
V1.19, V1.20, any candidate generation, any canonical source package, or the
formal target. Existing or symlinked output leaves/ancestors are rejected.

Verification accepts only a strict staging descendant or the exact resolved
formal target. Publication derives its target only through
`config.new_formal_target("V1.21")`, requires a real non-symlink `releases/`
parent, rejects an existing target, and uses a private sibling plus no-replace
atomic rename. The readiness workflow does not invoke real publication.

## 13. Closed file scope

Authority documentation may create:

- `docs/superpowers/specs/2026-09-19-v121-formal-promotion-readiness-design.md`
- `docs/superpowers/plans/2026-09-19-v121-formal-promotion-readiness.md`

Implementation may create:

- `src/joy_m2/ingest/v121_promotion_models.py`
- `src/joy_m2/ingest/v121_promotion.py`
- `src/joy_m2/ingest/v121_promotion_verification.py`
- `tests/unit/test_v121_promotion_models.py`
- `tests/unit/test_v121_promotion_primitives.py`
- `tests/integration/test_v121_promotion.py`

It may minimally modify:

- `src/joy_m2/ingest/__init__.py`
- historical exact-public-surface tests that must append the nine approved
  V1.21 promotion exports without changing older behavior assertions.

Readiness closure may modify `PROJECT_STATE.md` and create
`docs/reports/V121_PROMOTION_READINESS_VERIFICATION.md`. Generated dry-run roots
remain ignored under `data/staging/` and are never committed. No production,
test, docs, data, release, legacy, fixture, CLI, dependency, or project-script
file outside this closed scope is authorized. If an exact historical test path
is not identified by the Plan, implementation stops rather than inferring it.

## 14. RED-first implementation and review gates

1. Public carrier/API tests establish RED before any production file exists.
2. Models/signature scaffolds make only the public-contract group GREEN.
3. Primitive, builder, verifier, determinism, rollback, isolated publication,
   and historical-preservation tests all establish valid behavior RED before
   behavior implementation.
4. Minimal behavior makes the focused suite GREEN.
5. Two independent generation-000004 dry-runs are built under distinct staging
   roots, independently verify 21/21, and compare byte-for-byte.
6. Tests prove failure cleanup, no-replace publication, exact-gate enforcement,
   conservative post-publication rollback, and absence of real
   `releases/V1.21/`.
7. Fresh gates include all maintained suites, Task 9A/9B/9C/9D,
   Task 10A/10B/10C, V1.21 candidate tests, V1.18 validator, V1.19 verifier,
   V1.20 formal verifier, current candidate 24/24, zero skips/expected failures,
   frozen hashes/counts, and `git diff --check`.
8. Independent review must report Critical 0 and Important 0. Findings are
   remediated under this closed authority and re-reviewed.
9. Design, Plan, implementation, tests, verification report, and state may be
   committed and ordinarily pushed. No force push, merge, rebase, or squash.
10. After readiness closure, stop before publication at the final human gate.

## 15. Readiness completion report

`PROJECT_STATE.md` and the verification report record:

- current formal remains V1.20 / 543;
- V1.21 candidate generation `000004`, 48 additions, 591 projected;
- exact candidate digest, SQLite SHA, and manifest SHA;
- two dry-run identities and byte equivalence;
- independent 21/21 verification;
- rollback and historical preservation results;
- `releases/V1.21/` remains absent;
- status `READY FOR FINAL V1.21 PROMOTION AUTHORIZATION`;
- exact required approval statement using the computed release digest.

No report claims formal publication before that later approval is received and
consumed.

## 16. Non-goals

- creating or deleting `releases/V1.21/` during readiness;
- changing formal V1.18, V1.19, or V1.20;
- altering any of the 48 approved records or their source evidence;
- rerunning OCR, transcription, taxonomy mapping, or preflight;
- ingesting 2019 or beginning V1.22;
- refactoring historical promotion modules into a generic engine;
- adding current-release pointers, consumer migration, CLI, App/API, or new
  dependencies;
- force push, merge, rebase, squash, or automatic final approval.
