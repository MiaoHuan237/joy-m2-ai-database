# Task 8A Pipeline Contracts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the approved typed pipeline contracts and behavior locks, then migrate the Task 5/6 behavior layer by layer without changing the frozen V1.18 release or any question data.

**Architecture:** `release` is the only high-level orchestrator. It passes immutable dataclass values through `audit → db → export`, builds only in an atomic staging run, verifies every artifact, and promotes only a manifest-bound Joy approval into a new non-existing formal release directory. Legacy code remains an independent oracle and is never imported by maintained production modules.

**Tech Stack:** Python 3.12.13, Python standard library only (`dataclasses`, `pathlib`, `sqlite3`, `csv`, `json`, `hashlib`, `zipfile`, `unittest`).

## Global Constraints

- This plan is a Task 8A deliverable. Executing it requires a separate explicit authorization and constitutes Task 8B; do not execute it during Task 8A.
- The current user instruction forbids subagents. When execution is authorized, use `superpowers:executing-plans` inline, not subagent-driven development.
- Start execution from the approved Task 8A commit on a new Task 8B branch and isolated worktree.
- Never modify `releases/V1.18/` or `data/baselines/V1.18/` in place.
- Preserve 497 complete questions, V1.17×45, Task 6×452, and answer identity 392/71/34.
- Preserve stable IDs, boundaries, source/reviewed text, answers, provenance, Joy Level, tags, images, corrections, hashes, selection state, compatibility tables, and compatibility views.
- SQLite remains the sole formal source of truth; CSV, Markdown, reports, statistics, manifests, and packages remain derived outputs.
- Do not add third-party dependencies.
- Do not implement the CLI in this plan; expose only the Python boundaries the future CLI will call.
- Do not implement App/API, question generation, M1, consumer migration, or compatibility-view deletion.
- All writes during implementation and equivalence testing go to `tempfile.TemporaryDirectory()` or a new `data/staging/<run_id>/`; no formal promotion test may target the real repository release tree.
- Use the current Python 3.12 runtime for commands:

```bash
task8_python=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
```

- Every task follows red-green-refactor, ends with a focused test run, runs `git diff --check`, and creates one reviewable commit.
- Before Task 8B completion, run Task 7 7/7, Task 3–6 54/54, the V1.18 independent verifier, all new tests, `git diff`, and frozen-directory hash checks.

---

## File Map

### Maintained package

- `src/joy_m2/errors.py`: stable domain exception hierarchy.
- `src/joy_m2/models.py`: immutable shared requests, contracts, results, artifact references, and approval values.
- `src/joy_m2/config.py`: absolute path resolution and repository containment rules.
- `src/joy_m2/audit/pipeline.py`: Task 5/6 candidate loading, audit aggregation, and `AuditedBatch` production.
- `src/joy_m2/audit/profiles.py`: reviewed V1.17 and V1.18 audit decisions and expected counts.
- `src/joy_m2/audit/__init__.py`: public audit exports only.
- `src/joy_m2/db/pipeline.py`: protected-baseline copy, transactional V1.17/V1.18 database builds, and database verification.
- `src/joy_m2/db/profiles.py`: V1.17 schema creation and V1.18 append contracts.
- `src/joy_m2/db/__init__.py`: public database exports only.
- `src/joy_m2/export/formats.py`: canonical JSON, CSV, and UTF-8/LF writing primitives.
- `src/joy_m2/export/pipeline.py`: SQLite-derived files plus supplied typed
  audit evidence export; never reopens the candidate.
- `src/joy_m2/export/__init__.py`: public export API only.
- `src/joy_m2/release/hashing.py`: SHA-256, manifest, and `SHA256SUMS.txt` primitives.
- `src/joy_m2/release/transformers.py`: deterministic V1.17 historical
  audit-PASS-to-release-stage transformation only.
- `src/joy_m2/release/packaging.py`: deterministic ZIP creation and ZIP metadata verification.
- `src/joy_m2/release/verification.py`: candidate/formal release verification and structured reports.
- `src/joy_m2/release/pipeline.py`: atomic staging build and approval-bound formal promotion.
- `src/joy_m2/release/__init__.py`: public release API only.

### Tests and fixtures

- `tests/fixtures/pipeline/V1.17.json`: reviewed V1.17 counts, names, hashes, and layout facts.
- `tests/fixtures/pipeline/V1.18.json`: reviewed V1.18 counts, names, hashes, and layout facts.
- `tests/regression/test_task8b_legacy_pipeline_behavior.py`: characterization tests that call legacy only as an oracle.
- `tests/unit/test_pipeline_models.py`: dataclass immutability and result semantics.
- `tests/unit/test_pipeline_config.py`: path resolution, containment, symlink, and overlap checks.
- `tests/unit/test_audit_pipeline.py`: aggregation, duplicate blocking, provenance, and pass conversion.
- `tests/unit/test_v117_release_transformer.py`: release-stage envelope,
  deterministic V1.17 decision, and oracle/byte-equivalence.
- `tests/integration/test_db_pipeline.py`: V1.17/V1.18 SQLite byte and logical equivalence.
- `tests/integration/test_export_pipeline.py`: CSV/Markdown/JSON byte contracts.
- `tests/unit/test_release_primitives.py`: hashing, manifest, sums, and deterministic ZIP.
- `tests/integration/test_release_pipeline.py`: atomic candidate build, verification, conflicts, approval, and promotion safety.
- `tests/regression/test_task8b_pipeline_equivalence.py`: maintained-vs-legacy end-to-end comparison and frozen-release protection.

### Documentation

- `PROJECT_STATE.md`: record Task 8B completion only after every gate passes.
- `docs/reports/TASK8B_VERIFICATION.md`: record exact commands, counts, hashes, and remaining limitations at Task 8B completion.

---

### Task 1: Lock the Legacy V1.17 and V1.18 Oracles

**Files:**
- Create: `tests/fixtures/pipeline/V1.17.json`
- Create: `tests/fixtures/pipeline/V1.18.json`
- Create: `tests/regression/test_task8b_legacy_pipeline_behavior.py`

**Interfaces:**
- Consumes: `legacy/task5_work/build_task5_release.py`, `legacy/task6_work/build_task6_release.py`, and the frozen release assets.
- Produces: reviewed fixture contracts and safe characterization helpers used by all later equivalence tests.

- [ ] **Step 1: Add exact reviewed fixture facts**

Create `tests/fixtures/pipeline/V1.17.json` with these fixed values:

```json
{
  "answer_status_counts": {"source_provided": 45},
  "csv_name": "Joy_M2_Complete_Questions_V1_17.csv",
  "csv_sha256": "308728abb9936cd0feb84ac7e30922833b60565a2942656311aa9e23aed1e2ba",
  "legacy_complete_question_count": 497,
  "question_count": 45,
  "release_version": "V1.17",
  "sqlite_name": "Joy_M2_Complete_Question_DB_V1_17.sqlite3",
  "sqlite_sha256": "58f32e547c4ff0cdd2ae25a9368ea288cbaa70af52869b779d698233aee93fab",
  "user_version": 117
}
```

Create `tests/fixtures/pipeline/V1.18.json` with these fixed values:

```json
{
  "answer_status_counts": {
    "ai_solved_verified": 71,
    "missing_from_source": 34,
    "source_provided": 392
  },
  "csv_name": "Joy_M2_Complete_Questions_V1_18.csv",
  "csv_sha256": "94e4b8060f80c485b6cd4c20d0cd9bbe7c4b0939f289ad38762900f9bceec2c5",
  "existing_v117_question_count": 45,
  "question_count": 497,
  "release_version": "V1.18",
  "sqlite_name": "Joy_M2_Complete_Question_DB_V1_18.sqlite3",
  "sqlite_sha256": "fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7",
  "task6_question_count": 452,
  "user_version": 118
}
```

- [ ] **Step 2: Write safe characterization helpers**

In `test_task8b_legacy_pipeline_behavior.py`, resolve the repository root from the test file, import legacy modules only inside test code, and build into `TemporaryDirectory`:

```python
ROOT = Path(__file__).resolve().parents[2]
LEGACY = ROOT / "legacy"

@contextmanager
def legacy_import_path(path: Path):
    sys.path.insert(0, str(path))
    try:
        yield
    finally:
        sys.path.remove(str(path))
```

Never pass `releases/` or `data/baselines/` as an output argument.

- [ ] **Step 3: Characterize Task 5 outputs and destructive target semantics**

Add tests that build V1.17 twice in separate temporary directories, compare every returned artifact byte-for-byte, assert SQLite/CSV hashes from the fixture, and safely demonstrate that a sentinel inside a temporary Task 5 target is removed:

```python
sentinel = output_dir / "sentinel.txt"
output_dir.mkdir()
sentinel.write_text("legacy-only", encoding="utf-8")
paths = build_release(output_dir)
self.assertFalse(sentinel.exists())
self.assertEqual(sha256(paths["sqlite"]), fixture["sqlite_sha256"])
```

- [ ] **Step 4: Characterize Task 6 outputs, verification, and stale-file semantics**

Build V1.18 in a temporary directory, assert all seven primary artifacts exist, assert core bytes equal the corresponding files in `releases/V1.18/`, and safely demonstrate that a temporary sentinel remains after `build_release()`.

Package twice to different temporary ZIP paths and assert identical bytes, fixed timestamps, `0644` mode, `create_system=3`, sorted member names, and independent verifier PASS.

- [ ] **Step 5: Run the characterization suite**

Run:

```bash
$task8_python -m unittest -v tests.regression.test_task8b_legacy_pipeline_behavior
```

Expected: PASS. These are characterization tests of existing behavior, so their first run is expected to pass rather than provide a red test.

- [ ] **Step 6: Re-run the existing gates**

Run:

```bash
$task8_python -m unittest -v tests/regression/test_task7_project_initialization.py
(cd legacy && $task8_python -m unittest -v task6_work/test_task6_migration.py)
(cd legacy/task5_work && $task8_python -m unittest -v test_task5_import.py)
```

Expected: Task 7 7/7, Task 6 22/22, Task 5 10/10.

- [ ] **Step 7: Commit the behavior locks**

```bash
git add tests/fixtures/pipeline/V1.17.json tests/fixtures/pipeline/V1.18.json tests/regression/test_task8b_legacy_pipeline_behavior.py
git diff --cached --check
git commit -m "test: lock legacy pipeline behavior"
```

---

### Task 2: Add Shared Errors, Models, and Path Configuration

**Files:**
- Create: `src/joy_m2/errors.py`
- Create: `src/joy_m2/models.py`
- Create: `src/joy_m2/config.py`
- Create: `tests/unit/test_pipeline_models.py`
- Create: `tests/unit/test_pipeline_config.py`

**Interfaces:**
- Consumes: fixture facts from Task 1.
- Produces: `PipelineConfig`, all immutable request/result types, `AuditResult.require_passed()`, and the domain exception hierarchy.

- [ ] **Step 1: Write failing model and exception tests**

Test exact imports, frozen mutation rejection, tuple normalization, PASS/FAIL semantics, and exception inheritance:

```python
def test_verification_report_requires_every_check_to_pass(self):
    report = VerificationReport(
        status="FAIL",
        checks=(VerificationCheck("hashes", False, "mismatch"),),
    )
    self.assertEqual(report.status, "FAIL")
    self.assertFalse(all(check.passed for check in report.checks))

def test_blocked_audit_cannot_become_a_batch(self):
    result = AuditResult(records=(), issues=(AuditIssue("exact_duplicate", "blocker", "Q1", "question_text_original", "Q0"),))
    with self.assertRaises(AuditBlockedError):
        result.require_passed()
```

Run:

```bash
$task8_python -m unittest -v tests.unit.test_pipeline_models
```

Expected: FAIL because `joy_m2.models` and `joy_m2.errors` do not exist.

- [ ] **Step 2: Implement the exception hierarchy**

Define exactly these public exceptions in `errors.py`:

```python
class PipelineError(Exception): ...
class ConfigurationError(PipelineError): ...
class InputError(PipelineError): ...
class InputMissingError(InputError): ...
class InputFormatError(InputError): ...
class BaselineMismatchError(InputError): ...
class AuditBlockedError(PipelineError): ...
class DatabaseBuildError(PipelineError): ...
class ForeignKeyViolationError(DatabaseBuildError): ...
class DatabaseIntegrityError(DatabaseBuildError): ...
class OutputConflictError(PipelineError): ...
class PromotionError(PipelineError): ...
```

- [ ] **Step 3: Implement immutable shared values**

Define frozen dataclasses for:

```python
ReleaseSpec
ApprovalRecord
ArtifactRef
AuditIssue
Correction
PublicationEvidence
AuditedQuestion
Task4Compatibility
ReleaseCompatibility
AuditedRecord
AuditedBatch
AuditResult
AuditContract
AuditRequest
DatabaseContract
DatabaseBuildRequest
DatabaseArtifact
ExportContract
ExportRequest
DerivedArtifacts
ReleaseContract
CandidateBuildRequest
VerificationCheck
VerificationReport
CandidateRelease
FormalRelease
```

`AuditedQuestion` must explicitly declare the audit-stage domain fields represented
by legacy records; convert `image_paths`, `tags`, `corrections`, `review_checks`,
and `unresolved_issues` to immutable tuples of typed values. Represent the
historical `record_status`, `joy_approval`, and nullable `approved_at` fields as
a typed `PublicationEvidence` child value rather than treating them as a new
audit decision. Do not put the release-only `formal_release_version`,
`selectable`, `source_order`, `task4_resolution`, or `task4_processed_at` fields
on `AuditedQuestion`, and do not add an `extras` mapping. The later Task 2 model
amendment adds the exact public frozen compatibility values and record envelope
frozen in the Task 2 chapter below; this historical implementation step does not
authorize that amendment. `AuditResult.require_passed()` rejects any issue with
severity `blocker`; callers inspect `VerificationReport.status` and every named
check explicitly.

- [ ] **Step 4: Run model tests to green**

```bash
$task8_python -m unittest -v tests.unit.test_pipeline_models
```

Expected: PASS.

- [ ] **Step 5: Write failing path-boundary tests**

Cover absolute resolution, staging/releases overlap, `..`, a symlink escaping the repository, V1.18 protected paths, and target containment:

```python
def test_release_target_is_derived_and_v118_is_protected(self):
    config = PipelineConfig(self.root)
    with self.assertRaises(ConfigurationError):
        config.new_formal_target("V1.18")

def test_output_symlink_cannot_escape_staging(self):
    outside = self.root.parent / "outside"
    (self.root / "data/staging/link").symlink_to(outside, target_is_directory=True)
    with self.assertRaises(ConfigurationError):
        config.require_staging_output(self.root / "data/staging/link/file")
```

Run and expect missing implementation failure:

```bash
$task8_python -m unittest -v tests.unit.test_pipeline_config
```

- [ ] **Step 6: Implement `PipelineConfig`**

Resolve `repo_root` once in `__post_init__`, derive `staging_root`, `releases_root`, and `baselines_root`, require those roots not to overlap, and expose:

```python
def require_staging_output(self, path: Path) -> Path
def require_release_input(self, path: Path) -> Path
def new_formal_target(self, release_version: str) -> Path
```

Use `Path.resolve(strict=False)` plus `Path.is_relative_to()` for containment. Reject existing formal targets, all writes to V1.18, symlink escapes, and versions not matching `V[0-9]+\.[0-9]+`.

- [ ] **Step 7: Run shared-contract tests**

```bash
$task8_python -m unittest -v tests.unit.test_pipeline_models tests.unit.test_pipeline_config
```

Expected: PASS.

- [ ] **Step 8: Commit shared contracts**

```bash
git add src/joy_m2/errors.py src/joy_m2/models.py src/joy_m2/config.py tests/unit/test_pipeline_models.py tests/unit/test_pipeline_config.py
git diff --cached --check
git commit -m "feat: add typed pipeline contracts"
```

---

## Task 2 — Profile Parsing, Serialization and Audit Contract

**Task 8B / Task 1:** **CLOSED — APPROVED**

**Task 8B / Task 2 Phase 1 models/tests:** **CLOSED — INDEPENDENT REVIEW PASSED**

**Task 8B / Task 2 Phase 2 contract decisions:** **DESIGN APPROVED — CONTRACT REVISION AUTHORIZED**

**Task 8B / Task 2 Phase 2 implementation:** **NOT STARTED — NOT APPROVED**

This chapter originally froze the human-approved Task 2 contract revision.
Its Phase 1 public models and model tests have since been implemented and passed
independent review. The Phase 2 revision below freezes additional interfaces
and data flow only; it does not authorize profile parser/serializer code,
`audit_batch()`, the V1.17 transformer, database/export/release changes, tests,
or any other Phase 2 production implementation.

The staged approval name “Task 2” in this chapter refers to profile parsing,
record-level audit serialization, and audit aggregation. The historical numbered
implementation step below remains unapproved and is governed by this chapter.

### 1. Public type and module boundaries

The dependency direction is:

```text
external profile input
→ audit/profiles.py
→ typed AuditedRecord envelopes
→ audit/pipeline.py
→ AuditResult
→ AuditResult.require_passed()
→ AuditedBatch
```

Responsibilities are frozen as follows:

- `src/joy_m2/models.py` defines immutable domain values and public types only.
  It does not parse external profile shapes, preserve arbitrary compatibility
  fields, perform approval conversion, or encode JSON.
- `src/joy_m2/audit/profiles.py` is the sole external profile-shape conversion
  boundary. It parses V1.17/V1.18 records, validates profile-specific structure,
  constructs the approved typed representation, and serializes audit-stage
  record-level mappings. It does not access the filesystem or database, compute
  real file hashes, call export/release/CLI code, perform approval conversion,
  or use a hidden mutable registry or generic `extras`.
- `src/joy_m2/audit/pipeline.py` performs `audit_batch()` input preflight, invokes
  the selected profile parser, executes business audit rules, aggregates and
  sorts issues, and constructs `AuditResult`. It does not write databases,
  export files, perform release approval, or call CLI code.
- A later, separately authorized release transformer owns all V1.17 publication
  and approval conversion. The Phase 2 chapter below now freezes its API and
  release-stage envelope, but does not authorize implementation.
- `src/joy_m2/export/formats.py` receives a record-level mapping after the
  applicable business-stage transformation. It owns final file representation
  and bytes only; it does not audit or change publication semantics.

`AuditContract.profile` is exactly the approved `AuditProfile` literal. The only
valid values are `"V1.17"` and `"V1.18"`; Task 5 maps to `"V1.17"` and Task 6
maps to `"V1.18"`. Arbitrary strings, implicit profile inference, fallback
profiles, and a mutable profile registry are forbidden.

The required Phase 1 stage-model amendment is implemented and independently
approved. The three public `@dataclass(frozen=True)` values have the exact field
names, order, and Python types shown:

```python
Task4Compatibility(
    task4_resolution_present: bool,
    task4_resolution: str | None,
    task4_processed_at_present: bool,
    task4_processed_at: str | None,
)

ReleaseCompatibility(
    formal_release_version: str,
    selectable: bool,
    source_order: int,
)

AuditedRecord(
    question: AuditedQuestion,
    task4_compatibility: Task4Compatibility | None,
    release_compatibility: ReleaseCompatibility | None,
)
```

Their public model boundaries are frozen as follows:

- `AuditedQuestion` is the audit-stage core record. Relative to the currently
  approved field order, it omits exactly `formal_release_version`, `selectable`,
  `source_order`, `task4_resolution`, and `task4_processed_at`; those five values
  are compatibility evidence, not audit-stage domain fields.
- `PublicationEvidence.approved_at` has the target type `str | None`. JSON
  `null` maps losslessly to Python `None`, and Python `None` serializes
  losslessly to JSON `null`; neither direction may replace it with an empty or
  missing value or a fabricated timestamp.
- `Task4Compatibility` is the only legal carrier for the two V1.17 Task 4
  compatibility keys. Each `*_present` field is a true `bool`. Each value is a
  true `str` or `None`; `None` is the unique empty slot when its key was absent,
  but presence is never inferred from the value. If a present flag is false,
  its value must be `None`. If it is true, `None` represents an explicit JSON
  `null` and a string preserves the exact input string. The two flags remain
  independent even though the frozen 45-record input currently has both keys
  absent or both present.
- `ReleaseCompatibility` is the only legal carrier for already-issued V1.18
  release-only values. `formal_release_version` is a true `str`, `selectable`
  is a true `bool`, and `source_order` is a true `int` (not `bool`). All three
  fields are required; partial construction, coercion, defaults, derivation,
  normalization, or replacement is forbidden.
- `AuditedRecord` is the audit pipeline's only legal typed record envelope.
  Business audit rules may read only `question`. `task4_compatibility` serves
  only V1.17 Task 4/Audit shape replay, while `release_compatibility` serves
  only V1.18 release-shape replay. The carriers must not be merged, converted
  to `extras`, or stored outside the envelope.
- `AuditResult.records` and `AuditedBatch.records` have the exact public
  type `tuple[AuditedRecord, ...]`. Each input record produces one envelope,
  and `require_passed()` preserves the same ordered envelope tuple.

The only supported carrier combinations are:

| Profile path | `task4_compatibility` | `release_compatibility` |
|---|---|---|
| V1.17 Task 4/Audit | `Task4Compatibility` | `None` |
| V1.18 frozen release | `None` | `ReleaseCompatibility` |

A V1.17 record constructs `Task4Compatibility` even when both source keys are
absent; both flags are then false and both values are `None`.
`task4_compatibility=None` means the record is not on the V1.17 compatibility
path, not that both keys were absent. The two carriers must never both be
non-`None`. Because Task 2 supports no third input profile, they must never both
be `None`. Empty mappings, empty strings, sentinel objects, partially populated
carriers, hidden mappings, parallel lists, `question_id` joins, position joins,
object-identity joins, and global registries are forbidden.

Direct construction that violates these closed value or carrier-combination
invariants uses the existing `PipelineError` model boundary; no new exception or
issue code is introduced. Invalid external profile input is rejected at the
profile boundary as `InputFormatError` before any partial result is exposed.

Phase 1 does not authorize the Phase 2 parsers, serializer, audit pipeline,
transformer, database, export, or release work specified later in this plan.

### 2. Common parsing and serialization rules

The outer pipeline performs file/container preflight and JSON decoding. An
invalid outer container raises `InputFormatError` there. A profile parser then
accepts only the exact selected-profile record shape. It must:

- reject a non-`dict` record, missing or forbidden key, extra key, incorrect key
  order, wrong scalar/container type, or invalid image shape with
  `InputFormatError`;
- use exact runtime types: `bool` is not an `int`, and no `str()`, `int()`, or
  other permissive conversion is allowed;
- preserve record order, array order, image order, and approved field order;
- fail fast on external shape errors, without returning a partial
  `AuditResult`, partial `AuditedBatch`, or partial serialized result;
- never accept `extras`, an unconstrained `dict`, or a generic `Mapping` as an
  extension bag.

Profile serializers accept only an `AuditedRecord` for the same profile. They
return a record-level `dict`, preserve the stage-specific field names, presence,
values, and order, and do not write files or perform final JSON encoding. They
read compatibility values only from the carrier in that same envelope. They may
not query an external mapping or another record, reconstruct pairings by
`question_id`, position, file order, or object identity, or consult global
state.

`Task4Compatibility` and `ReleaseCompatibility` are closed named values, not
raw JSON blobs, generic mappings, arbitrary-field passthrough, or parallel fact
sources. They preserve existing compatibility evidence only. They do not create,
derive, normalize, default, repair, or modify it; carry `AuditIssue` values; or
participate in business audit decisions. Neither carrier object is itself a JSON
field: serializers replay only its named source fields in their frozen external
positions.

### 3. V1.17 audit-stage parser input

The V1.17 parser consumes records eligible to enter Task 2 in the real Task
4/Audit-stage shape. It does not consume already-published V1.17 approved
records. Eligibility is exact: `record_status == "audit_passed"` and
`unresolved_issues == []` must both hold. Either a different status or any
non-empty unresolved-issue list is a profile eligibility failure that raises
`InputFormatError` immediately. It returns no partial `AuditResult`, produces no
`AuditIssue`, maps to none of the six business issue codes, and does not create a
seventh code.

The legacy Task 4 P1 checks for status and unresolved issues are historical
upstream audit behavior. Task 2 receives only records that already satisfy that
eligibility boundary; it does not rerun the upstream approval process or
manufacture, modify, or complete an approval state.

The exact 50-field base order is:

```python
V117_AUDIT_BASE_FIELDS = (
    "question_id",
    "source_id",
    "source_question_number",
    "source_section",
    "source_file",
    "source_member",
    "source_sha256",
    "source_member_sha256",
    "source_fragment_hash",
    "source_page",
    "solution_source_file",
    "solution_source_member",
    "solution_source_member_sha256",
    "question_text_original",
    "question_text_zh",
    "question_latex",
    "marks_total",
    "image_paths",
    "solution_original",
    "solution_verified",
    "answer_status",
    "answer_verification_status",
    "official_marking_available",
    "primary_type",
    "tags",
    "difficulty_level",
    "difficulty_evidence",
    "old_difficulty",
    "old_difficulty_label",
    "old_tags",
    "question_review_status",
    "formula_review_status",
    "image_review_status",
    "answer_review_status",
    "correction_status",
    "corrections",
    "duplicate_status",
    "duplicate_reference",
    "duplicate_evidence",
    "audit_notes",
    "record_status",
    "joy_approval",
    "audited_at",
    "approved_at",
    "schema_version",
    "source_heading",
    "question_text_zh_reviewed",
    "difficulty_dimensions",
    "unresolved_issues",
    "review_checks",
)
```

The 24 records without Task 4 compatibility fields use exactly this 50-field
shape. The other 21 records append exactly these two keys, in this order, and
therefore use a 52-field shape:

```python
V117_TASK4_COMPATIBILITY_FIELDS = (
    "task4_resolution",
    "task4_processed_at",
)
```

Both compatibility keys are either absent together or present together in the
approved external shape. When present, each value is a true `str` or JSON
`null`. `audit/profiles.py` nevertheless records each key independently in a
`Task4Compatibility`: `task4_resolution_present` and
`task4_processed_at_present` record original key presence, while
`task4_resolution: str | None` and `task4_processed_at: str | None` preserve the
original values. A missing key has `present=False` and value `None`; an explicit
JSON `null` has `present=True` and value `None`. The flag, never the value,
controls whether the serializer emits the key. No flag may be omitted or shared,
and the carrier cannot become a general extension mechanism. For this frozen
V1.17 profile, the only valid flag pairs are `(False, False)` and
`(True, True)`; the serializer rejects a mixed pair rather than emitting an
unapproved 51-field shape. Separate flags remain mandatory so each key's
presence and explicit-null value are represented directly rather than inferred
or collapsed.

Every valid V1.17 input record, including each of the 24 records with neither
key, produces exactly:

```python
AuditedRecord(
    question=<AuditedQuestion without either Task 4 key>,
    task4_compatibility=<Task4Compatibility>,
    release_compatibility=None,
)
```

The parser constructs the envelope once. `AuditResult.records` and
`AuditedBatch.records` carry that same record pairing in input order without
dropping, replacing, swapping, or reordering either the question or carrier.

The complete frozen V1.17 path is:

```text
Task 4/Audit 50/52-field input
→ parser reads the core fields and independently checks both Task 4 keys
→ Task4Compatibility preserves both values and both presence flags
→ AuditedQuestion excludes both Task 4 keys and all three release-only keys
→ AuditedRecord(question, Task4Compatibility, None)
→ AuditResult.records carries the envelope unchanged
→ AuditedBatch.records carries the envelope unchanged
├─ audit evidence: Task 2 serializer replays 50/52 fields from that envelope
└─ release path: Phase 2 transformer directly retains each envelope,
   creates release-stage values, and rewrites release state
   → release-stage serializer emits approved V1.17 53/55 fields
```

The exact special-field contract is:

| Field | Input presence and type | Audit-stage meaning | Task 2 serialized shape |
|---|---|---|---|
| `year` | forbidden, including explicit `null` | common domain value is `None` | omitted |
| `marks_total` | required; true `int` or `null`; `bool` rejected | `int | None` | unchanged value |
| `image_paths` | required list of exact V1.17 image objects | `tuple[QuestionImage, ...]` | exact image-object list |
| `record_status` | required literal `"audit_passed"` | technical audit state only | `"audit_passed"` |
| `joy_approval` | required empty true string | no publication approval | unchanged empty string |
| `approved_at` | required JSON `null` | `PublicationEvidence.approved_at: str | None` is exactly `None` | `null` |
| `schema_version` | required literal `"complete-question-v1.0-draft"` | audit-stage schema | unchanged draft value |
| `unresolved_issues` | required empty list | Task 2 eligibility has already passed | unchanged empty list |
| `task4_resolution` | absent, or present with true `str`/`null` | explicit compatibility value plus presence flag | preserve exact presence and value |
| `task4_processed_at` | absent, or present with true `str`/`null` | explicit compatibility value plus presence flag | preserve exact presence and value |
| other 43 base fields | required with their approved exact JSON types | existing typed domain fields | unchanged value and base order |

Every V1.17 image element is a true `dict` with exactly these keys in this
order, with no missing or additional key:

```python
("path", "sha256", "role")
```

`path` is a non-empty true `str`. `sha256` and `role` are either both `None` or
both true strings satisfying the approved `QuestionImage` value invariant;
`role`, when present, is non-empty. Only `audit/profiles.py` converts this exact
external object to `QuestionImage`. The model layer does not accept a string,
`dict`, or `Mapping` in `AuditedQuestion.image_paths`.

The V1.17 Task 2 input must not contain `formal_release_version`, `selectable`,
or `source_order`. It must not be pre-converted to `published`, pre-populated
with approval identity/time, or changed to the formal schema version. Such a
record is the wrong stage and is rejected as an external profile-shape error;
it is not converted into a seventh business issue. The parser and serializer
must not prefill the three release-only fields with `""`, `None`, `0`, `False`,
another placeholder, or a derived value.

### 4. V1.17 audit-stage serializer output

The V1.17 profile serializer emits only an audit-stage record-level mapping. Its
only compatibility source is the same
`AuditedRecord.task4_compatibility` received from the pipeline. That carrier is
required and `release_compatibility` must be `None`. Its output contains exactly
`V117_AUDIT_BASE_FIELDS` followed, independently according to the two presence
flags, by each applicable key in `V117_TASK4_COMPATIBILITY_FIELDS` order. For the
frozen input this yields exactly the original 24×50-field and 21×52-field
shapes.

It preserves `record_status="audit_passed"`, the empty `joy_approval`, null
`approved_at`, the draft `schema_version`, all field values, field presence, the
50/52 field order, list order, image order, and compatibility presence
semantics. A false flag omits its key; a true flag emits its exact string or an
explicit JSON `null`. It must not serialize a `task4_compatibility` object,
expand a 50-field record to 52 fields, shrink a 52-field record to 50 fields, or:

- produce a `published` record;
- manufacture or change `joy_approval`;
- populate `approved_at`;
- promote `schema_version` to a formal version;
- add `formal_release_version`, `selectable`, or `source_order`;
- consult any compatibility source outside the current `AuditedRecord`;
- invoke release code or simulate the legacy approval step;
- claim that its direct output equals the frozen approved V1.17 record or file.

### 5. Later V1.17 release transformation

The frozen approved V1.17 record shape belongs to a later, separately authorized
release transformer, not to the audit-stage serializer. Based on the protected
legacy oracle, it transforms each passing V1.17 `AuditedBatch` into direct
release-stage wrappers and applies these mapping operations:

| Operation | Audit-stage value | Approved V1.17 value |
|---|---|---|
| add `formal_release_version` | key absent | `"V1.17"` |
| add `selectable` | key absent | `True` |
| add `source_order` | key absent | stable record position, starting at 1 |
| rewrite `record_status` | `"audit_passed"` | `"published"` |
| rewrite `joy_approval` | `""` | `"approved_by_joy"` |
| rewrite `approved_at` | `None` | `"2026-08-08T20:00:00+08:00"` |
| rewrite `schema_version` | `"complete-question-v1.0-draft"` | `"complete-question-v1.0"` |

The transformer thereby produces the approved V1.17 53-field base record or
55-field record with the two compatibility keys. These operations carry release
and approval meaning. Task 2 must not implement, call, or imitate them. The
release transformer API is frozen by the Phase 2 chapter below; its tests and
implementation require a later independent task and approval.

Each release wrapper directly retains the original `AuditedRecord`, including
its `Task4Compatibility`, and adds a release-stage `ReleaseCompatibility`
outside that audit envelope. It never puts the new carrier into the retained
`AuditedRecord`. The transformer is the only component allowed to create the
three new V1.17 release-only values. Conversely, Task 2's V1.17 adapter,
pipeline, and audit-stage serializer may not prefill, default, or derive them.

### 6. V1.18 profile contract

The V1.18 compatibility record has exactly the 54 fields and order already
frozen in `complete_questions_452_task6_audited.json`; unknown fields and Task 4
compatibility fields are forbidden. The special rules remain:

```python
year_valid = value is None or type(value) is int
marks_total_valid = type(value) is int
```

- `year` is required; a true `int` or `None` is valid, and `bool` is rejected.
- `marks_total` is required; only a true `int` is valid, and `None` and `bool`
  are rejected.
- `image_paths` is a required JSON list of non-empty true path strings.
  `audit/profiles.py` converts each string to `QuestionImage(path, None, None)`
  and the V1.18 record serializer converts it back to a path string.
- V1.17 structured image objects must never be emitted as V1.18 images.
- Missing, extra, or wrongly typed fields raise `InputFormatError`; no generic
  mapping or `extras` may bypass the exact profile shape.
- Already-issued V1.18 publication evidence is preserved as typed
  `PublicationEvidence`; Task 2 does not manufacture a new approval.
- The already-issued `formal_release_version`, `selectable`, and `source_order`
  values are read exactly once by the adapter and preserved only in a public
  `ReleaseCompatibility(formal_release_version: str, selectable: bool,
  source_order: int)`. Exact runtime types are required: subclasses and
  coercions are not accepted, and `bool` is not valid for `source_order`. A
  missing or invalid field raises `InputFormatError` fail-fast, with no partial
  `AuditResult`, partial output, `AuditIssue`, or mapping to a business issue
  code.

Every valid V1.18 input record produces exactly:

```python
AuditedRecord(
    question=<AuditedQuestion without the three release-only fields>,
    task4_compatibility=None,
    release_compatibility=ReleaseCompatibility(
        formal_release_version=<input value>,
        selectable=<input value>,
        source_order=<input value>,
    ),
)
```

The pipeline carries that envelope unchanged through `AuditResult.records` and
`AuditedBatch.records`. The V1.18 serializer reads only the same envelope's
`release_compatibility` and replays all three exact values in their frozen
positions, leaving the record at 54 fields. It must not serialize a
`release_compatibility` object; create, derive, default, replace, normalize,
delete, exchange, or reorder any of the three values; or call the release
transformer. The release transformer does not participate in this compatibility
replay path.

The complete frozen V1.18 path is:

```text
frozen V1.18 54-field input
→ adapter strictly reads the three existing release-only values
→ ReleaseCompatibility preserves those exact values
→ AuditedQuestion excludes the three release-only values and both Task 4 keys
→ AuditedRecord(question, None, ReleaseCompatibility)
→ AuditResult.records carries the envelope unchanged
→ AuditedBatch.records carries the envelope unchanged
→ V1.18 serializer replays the same three values from the same envelope
→ output remains exactly 54 fields
```

### 7. InputFormatError and business-issue boundary

An outer container or record that cannot be parsed as the selected profile
raises `InputFormatError`, fails fast, and produces neither an `AuditIssue` nor a
partial `AuditResult`. This includes JSON/container failure, missing, forbidden,
extra, or misordered keys, wrong types, and invalid profile-specific image
shapes. It also includes either V1.17 eligibility failure frozen in Section 3;
those failures are not business blockers.

A successfully parsed record that violates an approved business audit rule
produces one of the six blocker issues below. Business blockers do not fail
fast: the pipeline continues auditing the other successfully parsed records and
then sorts the complete issue list. A domain/profile discrepancy is a business
issue only when it is exactly one of these six rules; it never creates a seventh
code.

All six business rules read only `AuditedRecord.question`.
`Task4Compatibility` and `ReleaseCompatibility` do not participate in duplicate
matching, issue triggers, codes, fields, evidence, severities, ordering, or
PASS/FAIL. `exact_duplicate` derives its normalized key and evidence only from
questions. Two envelopes with equal questions and different compatibility
evidence therefore produce the same business audit result. Issue production and
sorting must not drop, replace, swap, or reorder the compatibility carrier paired
with any question.

`AuditIssue.field` remains a plain `str`. No location object, JSON Pointer, tuple
path, or index-path type is added. The exact top-level field is stored in
`field`; a specific image path is stored deterministically in `evidence`.

| Code | Profile | Severity | Exact trigger after successful parsing | `field` | Deterministic `evidence` |
|---|---|---|---|---|---|
| `missing_question_text` | V1.17/V1.18 | `blocker` | `question_text_original` has no non-whitespace content | `question_text_original` | literal `"empty"` |
| `invalid_difficulty` | V1.17/V1.18 | `blocker` | true-integer `difficulty_level` is outside 1–5 | `difficulty_level` | `str(level)` |
| `missing_solution` | V1.17/V1.18 | `blocker` | `answer_status != "missing_from_source"` and `solution_verified` has no non-whitespace content | `solution_verified` | exact `answer_status` |
| `missing_image` | V1.17/V1.18 | `blocker` | a declared relative image reference cannot be resolved by pipeline input preflight | `image_paths` | exact declared relative path |
| `exact_duplicate` | V1.17/V1.18 | `blocker` | normalized complete-question text exactly matches another candidate or protected baseline record | `question_text_original` | deterministic duplicate `question_id` |
| `invalid_tag` | V1.17/V1.18 | `blocker` | a parsed tag is absent from `AuditContract.allowed_tags` | `tags` | exact invalid tag |

The list is closed: all six severities are `blocker`; there is no warning/error
extension, catch-all issue, shape-drift issue, or seventh business code. Image
shape errors remain `InputFormatError`. Image-reference resolution does not
authorize profile-layer filesystem access, image-content validation, real hash
calculation, or authenticity checks.

For `exact_duplicate`, “deterministic duplicate `question_id`” means the rolling
predecessor held in `normalized_seen` immediately before the current record is
checked. The algorithm is frozen as follows:

1. Process candidate records in their stable input order, using normalized
   complete-question text as the `normalized_seen` key.
2. If that key already exists, emit exactly one `exact_duplicate` issue for the
   current record and use the currently stored preceding `question_id` as
   `evidence`.
3. After the check, always overwrite that key with the current record's
   `question_id`, whether or not the current record was a duplicate.

Thus, when one normalized text appears as Q1, Q2, and Q3 in stable input order,
Q1 has no `exact_duplicate`, Q2 has `evidence="Q1"`, and Q3 has
`evidence="Q2"`. The implementation must not emit separate issues for a
baseline match, earliest match, minimum ID, or every historical match, and must
not choose evidence through a set, unordered traversal, object identity,
filesystem order, or hash randomization.

For the V1.18 legacy oracle, `normalized_seen` is seeded before candidate
processing from `complete_questions_v2` by normalizing each baseline
`question_text_original` and storing its `question_id`. The historical query has
no `ORDER BY`, but the protected V1.17 baseline has 45 rows and 45 distinct
normalized keys, so initialization performs no competing overwrite and its
result is unambiguous. Candidates then use the legacy's explicit stable
`ORDER BY q.source_id, q.question_number, q.question_id`; each candidate follows
the same check-then-overwrite rule above. The absence of `ORDER BY` in that
historical baseline query is not permission to select duplicate evidence by an
unstable order.

### 8. Deterministic issue ordering

The exact issue sort key is:

```python
key = (issue.question_id, issue.code, issue.field, issue.evidence)
```

Sorting must be stable. When all four keys are identical, issue production order
is preserved. Implementations must not add a hidden fifth key, deduplicate equal
issues, or depend on a set, unordered traversal, object identity, filesystem
order, or hash randomization.

### 9. AuditResult and AuditedBatch

After external parsing succeeds, the pipeline aggregates every business blocker
and constructs one internally consistent `AuditResult`:

- `records` has exact type `tuple[AuditedRecord, ...]` and contains one envelope
  per successfully parsed input record in input order;
- `issues` contains all blocker issues in the deterministic order above;
- `answer_status_counts` exactly counts those records by the real
  `record.question.answer_status` values and follows the approved
  unique-positive-count model contract;
- Phase 1 currently uses uppercase status; the approved Phase 2 amendment below
  replaces it with lowercase `"passed"`/`"failed"` and adds report/evidence
  closure. Historical wording in this subsection is not the Phase 2 target.

With no blocker, `AuditResult.require_passed()` returns an immutable
`AuditedBatch` whose `records` has the same exact
`tuple[AuditedRecord, ...]` value and order. The question and its two carrier
slots remain in the same envelope; separate question/carrier lists and later
reassociation by position, `question_id`, object identity, file order, or global
state are forbidden. With one or more blockers, the pipeline still returns the
failed aggregate `AuditResult`, but `require_passed()` raises the approved
`AuditBlockedError`; no `AuditedBatch` may be obtained or exposed. External
format failures raise `InputFormatError` earlier and return no partial result.
Except for the record element type changing from `AuditedQuestion` to
`AuditedRecord`, this revision does not expand the responsibilities of
`AuditResult`, `AuditedBatch`, `require_passed()`, or `AuditBlockedError`.

### 10. Stage authority matrix

`Allowed` identifies the unique owner. `Invoke only` permits orchestration but
not reimplementation. `Carry only` means the component may preserve the same
envelope but may not inspect a carrier for business logic or modify it. Every
other cell is forbidden.

| Behavior | `audit/profiles.py` | `audit/pipeline.py` | later release transformer | `export/formats.py` |
|---|---|---|---|---|
| outer file/container preflight and JSON decoding | Forbidden | **Allowed** | Forbidden | Forbidden |
| record-level profile-shape parsing | **Allowed** | Invoke only | Forbidden | Forbidden |
| inspect V1.17 Task 4 key presence and read existing values | **Allowed** | Forbidden | Forbidden | Forbidden |
| construct `Task4Compatibility` and V1.17 `AuditedRecord` | **Allowed** | Forbidden | Forbidden | Forbidden |
| read existing V1.18 release-only values | **Allowed** | Forbidden | Forbidden | Forbidden |
| construct `ReleaseCompatibility` and V1.18 `AuditedRecord` | **Allowed** | Forbidden | Forbidden | Forbidden |
| carry an `AuditedRecord` and both carrier slots | Forbidden | **Carry only** | **Direct retained child only** | Forbidden; consumes mapping only |
| business audit rules over `record.question` | Forbidden | **Allowed** | Forbidden | Forbidden |
| issue aggregation and sorting | Forbidden | **Allowed** | Forbidden | Forbidden |
| `AuditResult` construction | Forbidden | **Allowed** | Forbidden | Forbidden |
| V1.17 audit-stage mapping and presence-controlled Task 4 replay | **Allowed** | Forbidden | Forbidden | Forbidden |
| V1.18 54-field mapping and exact release-value replay | **Allowed** | Forbidden | Forbidden | Forbidden |
| generate `published` state for V1.17 | Forbidden | Forbidden | **Allowed** | Forbidden |
| write V1.17 approval identity/time | Forbidden | Forbidden | **Allowed** | Forbidden |
| create V1.17 `formal_release_version`, `selectable`, `source_order` | Forbidden | Forbidden | **Allowed** | Forbidden |
| rewrite V1.17 `record_status`, `joy_approval`, `approved_at`, `schema_version` | Forbidden | Forbidden | **Allowed** | Forbidden |
| JSON encoding | Forbidden | Forbidden | Forbidden | **Allowed** |
| file-level record ordering | Forbidden | Forbidden | Forbidden | **Allowed** |
| file writing | Forbidden | Forbidden | Forbidden | **Allowed** |
| final bytes generation | Forbidden | Forbidden | Forbidden | **Allowed** |

The verbs are intentionally distinct. A profile adapter checks key presence,
reads existing values, and constructs the exact carrier. The pipeline carries
the complete envelope unchanged. A V1.17 serializer replays keys according to
presence flags; a V1.18 serializer replays three required existing fields. Only
the later V1.17 release transformer creates new release-only values. No Task 2
component may generate or infer compatibility values, fill a missing required
value with `""`, `0`, `False`, `None`, or a sentinel, move a carrier between
records, merge the two carriers, or use a hidden mapping, parallel list,
secondary join, `extras`, or mutable registry.

The final frozen V1.17 compatibility guarantee is therefore a complete-chain
property:

```text
Task 2 `AuditedBatch` with V1.17 envelopes
→ Phase 2 release transformer directly retaining those envelopes
→ release-stage mapping producing 53/55 fields
→ export/formats.py encoding
→ frozen approved V1.17 JSON bytes
```

Task 2 serializer alone is not required or permitted to reproduce the frozen
approved V1.17 bytes. `export/formats.py` owns UTF-8 JSON encoding, approved key
presentation, file-level record order, indentation, separators, final newline,
and final bytes. It does not add release fields or change status, approval time,
approval identity, or schema version.

### 11. Explicit non-goals and authorization gate

Task 2 does not include database migration, export implementation migration,
release implementation, CLI migration, image-content authenticity verification,
frozen-asset changes, warning/error severity expansion, generic `extras`,
automatic profile upgrade, or any later task's code. The older real-SHA
non-goal is superseded for candidate/baseline input identity by the approved
Phase 2 preflight and `AuditInputEvidence` contract below; this does not extend
to the missing V1.16 ZIP historical constant.

No parser, serializer, release transformer, `audit_batch()`, database/export/
release component, or CLI is authorized by this documentation-only Phase 2
contract freeze. Phase 1 `Task4Compatibility`, `ReleaseCompatibility`,
`AuditedRecord`, `AuditResult.records`, and `AuditedBatch.records` are already
implemented and independently approved; this revision neither reopens nor
redesigns them. Task 2 Phase 2 implementation remains **NOT STARTED — NOT
APPROVED**.
Even a passing independent re-review does not authorize the next action; model
changes, tests, and implementation still require separate human authorization.

---

## Task 2 Phase 2 — Explicit Inputs, Historical Transformation, and Audit Evidence

This chapter is the approved Phase 2 contract revision. It supersedes later
historical Task 3–7 steps wherever they treat V1.17 SQLite extraction as a
maintained candidate producer, omit the V1.17 release-stage transformer, let
database create publication fields, or assign audit-report semantics/encoding
to the wrong stage. Everything in this chapter is frozen design and remains
unimplemented until separately authorized.

### 1. Exact future public interfaces

`AuditRequest` must be revised to this exact structure:

```python
@dataclass(frozen=True)
class AuditRequest:
    candidate_path: Path
    baseline_database: ArtifactRef
    asset_root: Path
    contract: AuditContract
    selected_source_ids: tuple[str, ...]

@dataclass(frozen=True)
class AuditInputEvidence:
    candidate_json: ArtifactRef
    baseline_database: ArtifactRef
```

`candidate_path` and `baseline_database` are independent explicit inputs. No
library code may infer either from cwd, environment variables, repository
layout, profile, or the other path. `audit/pipeline.py` owns candidate JSON,
file, asset-root, and baseline SQLite preflight, including existence, exact
kind, actual size, and independently recomputed SHA-256. `audit/profiles.py`
receives decoded record values only and performs no filesystem, SQLite, or
hashing access. Candidate digest is observed evidence with no runtime expected
digest; pipeline constructs its actual `ArtifactRef`. The request baseline
`ArtifactRef` is expected identity, and any existence/kind/size/SHA mismatch
raises `BaselineMismatchError` before audit proceeds.

`AuditInputEvidence` is the only authoritative typed carrier for candidate and
baseline input evidence. `AuditResult` is its sole public owner;
`AuditReport`, `ExportRequest`, `DerivedArtifacts`, and every other public model
must not retain parallel input digest carriers or scalar fields. Every returned
result, passed or business-blocked, has
`result.input_evidence.baseline_database == request.baseline_database`.
Preflight failure constructs no `AuditInputEvidence`, `AuditReport`, or
`AuditResult`.

Phase 2 also freezes these future release-stage values:

```python
@dataclass(frozen=True)
class V117ReleaseDecision:
    formal_release_version: Literal["V1.17"]
    selectable: Literal[True]
    record_status: Literal["published"]
    joy_approval: Literal["approved_by_joy"]
    approved_at: Literal["2026-08-08T20:00:00+08:00"]
    schema_version: Literal["complete-question-v1.0"]

@dataclass(frozen=True)
class V117ReleaseRecord:
    audited_record: AuditedRecord
    publication_evidence: PublicationEvidence
    release_compatibility: ReleaseCompatibility
    schema_version: str

@dataclass(frozen=True)
class V117ReleaseBatch:
    records: tuple[V117ReleaseRecord, ...]

def transform_v117_release(
    result: AuditResult,
    decision: V117ReleaseDecision,
) -> V117ReleaseBatch: ...
```

The decision is a deterministic historical V1.17 replay value, not a current
candidate approval and not the promotion-stage `ApprovalRecord`. The
transformer reads no clock, environment variable, approval manifest, or global
registry. It accepts a V1.17 `AuditResult`, calls `result.require_passed()`
internally, runs after audit and before database, and is forbidden on V1.18.
A failed result raises `AuditBlockedError`; empty, V1.18, or mixed envelope
input raises `PipelineError`. No provenance token, registry, object identity,
or parallel `passed` bool is added.

Each `V117ReleaseRecord` directly retains its matching `AuditedRecord` and
preserves order and one-to-one cardinality. `AuditedRecord` remains the only
audit-stage public envelope; its two compatibility carriers retain the Phase 1
legal combination and are never merged. Parallel lists, `question_id` joins,
position/file-order joins, and object-identity joins are forbidden. The
release-stage `ReleaseCompatibility.source_order` starts at 1 in stable order,
but implementation must prove the values through the protected legacy oracle
and byte-equivalence rather than relying on an unchecked positional assumption.

`ReleaseCompatibility` is a reusable immutable value type. V1.18-only applies
only to the legal `AuditedRecord.release_compatibility` slot. A
`V117ReleaseRecord` may independently hold a new `ReleaseCompatibility`, but
the transformer must never write it back into the retained V1.17
`AuditedRecord`.

The future semantic report is:

```python
@dataclass(frozen=True)
class AuditReport:
    release_version: str
    status: str
    candidate_count: int
    source_count: int
    audit_passed: int
    audit_pending: int
    blocked: int
    exact_duplicate_count: int
    answer_status_counts: tuple[tuple[str, int], ...]
    image_reference_count: int
    source_counts: tuple[tuple[str, int], ...]
```

`AuditResult` will add exact fields `report: AuditReport` and
`input_evidence: AuditInputEvidence`, in that order, after its existing
`status: str` field. Report counts cover successfully parsed records only:
`candidate_count == len(records)`; `blocked` counts distinct records having one
or more blockers; `audit_pending == 0`; `audit_passed == candidate_count -
blocked`; and `exact_duplicate_count` counts distinct records having that
blocker. Answer/source/image counts cover all records, `source_count` counts
distinct sources, and both tuple-count keys are sorted by string value.

The only status formula is: empty `issues` means both result/report status are
`"passed"`; non-empty `issues` means both are `"failed"`. The two status fields
must always be equal. Any mismatch among status, issues, blocked,
`audit_passed`, records, result, report, or envelope raises `PipelineError`.
Container/profile errors raise `InputFormatError` before result construction.
`audit_batch()` rejects an empty candidate because the profile expected count
does not match; the public empty no-issue PASS `AuditResult` semantics remain.

The exact target is:

```python
@dataclass(frozen=True)
class AuditResult:
    records: tuple[AuditedRecord, ...]
    issues: tuple[AuditIssue, ...]
    answer_status_counts: tuple[tuple[str, int], ...]
    status: str
    report: AuditReport
    input_evidence: AuditInputEvidence
```

The Phase 1 compatibility field `AuditResult.answer_status_counts` must equal
`report.answer_status_counts`; it is not a separately maintained source.

`AuditReport.status` is a typed semantic field, not permission to change frozen
evidence JSON schemas. The frozen V1.18 `task6_audit_report.json` has no
`status` key. Export validates status closure before serialization but emits
only historical fields for V1.18 and must remain byte-equivalent; V1.17 likewise
emits only its frozen artifact schema. These one-way compatibility projections
are not parallel typed carriers and cannot be read back as maintained state.

The database request target will be:

```python
@dataclass(frozen=True)
class DatabaseBuildRequest:
    batch: AuditedBatch | V117ReleaseBatch
    baseline_database: ArtifactRef
    baseline_manifest: ArtifactRef
    output_path: Path
    release_spec: ReleaseSpec
    contract: DatabaseContract
```

The V1.17 database profile accepts only `V117ReleaseBatch`; the V1.18 profile
accepts only `AuditedBatch`. A profile/batch mismatch is rejected before output
creation. Database never owns publication business authority and may not
generally construct or rewrite publication values. Its only exception is the
one-way frozen V1.18 SQLite serialization projection from an upstream exact
`record_status="audit_passed"` to the persisted value `"published"`; this does
not mutate any `AuditedRecord`, `AuditedBatch`, or `AuditResult`, cannot be read
back to reconstruct audit state, and does not apply to V1.17, future versions,
export, release orchestration, or manifest business state.

The successful export boundary will be:

```python
@dataclass(frozen=True)
class ExportRequest:
    database: DatabaseArtifact
    audit_result: AuditResult
    record_batch: AuditedBatch | V117ReleaseBatch
    output_dir: Path
    contract: ExportContract
```

Before any write, this public boundary must reject with the existing
`PipelineError` boundary unless all of the following hold:

1. `audit_result.status == "passed"` and
   `audit_result.report.status == "passed"`;
2. record counts are equal;
3. an `AuditedBatch` has records exactly equal and ordered identically to
   `audit_result.records`; or a `V117ReleaseBatch`, in its own order, directly
   yields the exact `audit_result.records` tuple through each item's
   `audited_record`;
4. no external map, second lookup, object identity, or ordering reconstruction
   participates in the comparison.

Supporting target structures are exact:

```python
@dataclass(frozen=True)
class ExportContract:
    profile: str
    audit_records_filename: str
    audit_report_filename: str
    csv_filename: str
    knowledge_markdown_filename: str
    import_report_filename: str
    project_state_filename: str
    taxonomy_filename: str | None
    expected_question_count: int
    expected_missing_answer_count: int

@dataclass(frozen=True)
class DerivedArtifacts:
    csv: ArtifactRef
    knowledge_markdown: ArtifactRef
    import_report: ArtifactRef
    project_state: ArtifactRef
    taxonomy: ArtifactRef | None
    audit_records: ArtifactRef
    audit_report: ArtifactRef
```

`ReleaseContract` removes its existing `audit_records_filename` and
`audit_report_filename` fields; every other field retains its current order and
type. Audit owns report semantics and counts. The applicable profile serializer
or V1.17 transformer
owns record mapping. `export/formats.py` and `export/pipeline.py` own JSON
representation, encoding, and file writing. Release only orchestrates and
collects the resulting artifacts into manifest, sums, package, and verification.

Input evidence SHA ownership is frozen as follows. Phase 2 supersedes the older
Task 2 real-SHA non-goal: audit preflight owns observation/verification and
`AuditResult.input_evidence` is the only typed source. `AuditReport`,
`ExportRequest`, and `DerivedArtifacts` add no digest fields. Export/release may
not reread or rehash candidate/baseline inputs, accept raw digest parameters,
or reconstruct evidence from manifest scalars.

Frozen V1.17/V1.18 manifests retain their historical scalar schema and receive
only deterministic one-way compatibility projections:

```text
V1.17 task4_candidate_sha256
    = audit_result.input_evidence.candidate_json.sha256
V1.17 baseline_v116_sqlite_sha256
    = audit_result.input_evidence.baseline_database.sha256
V1.18 baseline_v117_sqlite_sha256
    = audit_result.input_evidence.baseline_database.sha256
```

V1.17 additionally uses exactly one profile-local historical constant:

```python
V117_BASELINE_V116_ZIP_SHA256: Final[str] = (
    "5f73f541f5c2da5bf3e5540daf7dbfb40566a339eaee79ef3e25d8eabd0404ae"
)
```

and projects `baseline_v116_zip_sha256` from that constant. The
`legacy/task4_work/task3_package/05_标准规则/pre_task_hashes.json`
`formal_v116_package` record (which also records `34_735_850` bytes), frozen
`legacy/outputs/25757421d1d8/Task5_V1.17_正式入库/manifest.json`, and
`legacy/task5_work/build_task5_release.py` record the same digest. The actual
V1.16 ZIP is missing, so maintained code cannot claim
it reread or reverified the archive. The constant is not an
`AuditInputEvidence` field, public input, audit fact, database decision, or
license to read legacy `BASE_ZIP_SHA256`; it is a V1.17 serializer compatibility
fact only. It must not appear in V1.18.

No frozen manifest receives a structured `audit_input_evidence` node or a new
digest field. `artifact_sha256` remains only the generated-output hash set. A
carrier/projection/profile/constant inconsistency raises `PipelineError` rather
than choosing one value. Manifest scalars are not maintained pipeline inputs
and must never be read backward into `AuditInputEvidence`.

### 2. Candidate JSON and baseline SQLite responsibilities

| Profile | Maintained candidate | Protected baseline / duplicate reference | Database responsibility |
|---|---|---|---|
| V1.17 | `legacy/task4_work/task4_package/03_候选数据/complete_questions_45_task4.json`, exact 50/52-field audit-stage records | V1.16 SQLite | Build V1.17 from baseline and the transformed 45-record release batch |
| V1.18 | `releases/V1.18/complete_questions_452_task6_audited.json`, exactly 452 records and 54 fields per record | V1.17 SQLite | Copy the existing 45 formal records from baseline, then append the 452 audited records |

Legacy extraction of the 452 candidates from V1.17 SQLite remains a read-only
characterization and byte-equivalence oracle. Maintained production never uses
it as a candidate producer. The candidate JSON and baseline SQLite are checked
separately; neither substitutes for or reconstructs the other.

### 3. Stage authority matrix

| Behavior | `audit/profiles.py` | `audit/pipeline.py` | V1.17 transformer | `db/pipeline.py` | `export/*` | `release/pipeline.py` |
|---|---|---|---|---|---|---|
| candidate JSON/file and baseline SQLite preflight | Forbidden | **Owns** | Forbidden | baseline recheck only | Forbidden | Invoke only |
| construct and own `AuditInputEvidence` | Forbidden | **Owns** | Consume through result only | Forbidden | Consume through result only | Carry result only |
| exact profile parsing and audit-stage record mapping | **Owns** | Invoke only | Forbidden | Forbidden | Invoke serializer only | Forbidden |
| duplicate seed and business audit | Forbidden | **Owns** | Forbidden | Forbidden | Forbidden | Invoke only |
| `AuditResult` / `AuditReport` semantics and statistics | Forbidden | **Owns** | Forbidden | Forbidden | Consume only | Forbidden |
| V1.17 historical publication decision and release-stage mapping | Forbidden | Forbidden | **Owns** | Consume only | Consume only | Invoke only |
| preserve V1.18 release compatibility | **Owns** | Carry only | Forbidden | Consume only | Consume only | Forbidden |
| publication business authority / general publication-field construction or rewrite | Forbidden | Forbidden | **Owns for V1.17 only** | Forbidden | Forbidden | Forbidden |
| V1.18 frozen SQLite `record_status` compatibility projection | Forbidden | Forbidden | Forbidden | **Allowed only for `audit_passed` → `published` serialization** | Forbidden | Forbidden |
| database copy, transaction, schema, integrity | Forbidden | Forbidden | Forbidden | **Owns** | Forbidden | Invoke only |
| audit evidence JSON encoding and file writing | Mapping only | Semantics only | Mapping only | Forbidden | **Owns** | Invoke/collect only |
| frozen manifest input-digest projections | Forbidden | Evidence source only | Forbidden | Forbidden | Forbidden | **Serialize from result only** |
| V1.17 frozen historical ZIP digest constant projection | Forbidden | Forbidden | Forbidden | Forbidden | Forbidden | **Owns serialization only** |
| manifest, sums, ZIP, candidate verification | Forbidden | Forbidden | Forbidden | Forbidden | Artifact source only | **Owns** |

### 4. Complete successful and failed flows

V1.17 success:

```text
Task 4 50/52-field candidate JSON + protected V1.16 SQLite + asset root
→ audit preflight and exact V1.17 parser
→ baseline-seeded audit → AuditInputEvidence
→ AuditResult(AuditReport, AuditInputEvidence)
→ transform_v117_release(AuditResult, decision)
  → internal require_passed() → V117ReleaseBatch
→ database builds V1.17 without creating publication semantics
→ export consumes database + original audit_result + matching release batch
→ release emits frozen manifest scalar projections
  (input evidence plus V1.17 historical ZIP constant)
→ release collects artifacts, packages, and verifies candidate
```

V1.18 success:

```text
frozen 452×54-field candidate JSON + protected V1.17 SQLite + asset root
→ audit preflight and exact V1.18 parser
→ baseline-seeded audit → AuditInputEvidence
→ AuditResult(AuditReport, AuditInputEvidence)
→ require_passed() → AuditedBatch (no release transformer)
→ database copies 45 baseline records and appends 452 records
  → frozen V1.18 SQLite serialization only projects `audit_passed` to
    `published` without mutating the audited batch
→ export consumes database + original audit_result + matching audited batch
→ release emits frozen baseline_v117_sqlite_sha256 projection
→ release collects artifacts, packages, and verifies candidate
```

Input/container/profile failures occur before `AuditResult` and write no normal
artifact. A business blocker returns a failed `AuditResult` and `AuditReport`,
but cannot produce `AuditedBatch`, call the transformer/database, create normal
database/candidate artifacts, or enter promotion. Within `build_candidate()`,
the caller-supplied deterministic `run_id` selects
`data/staging/.failed/<run_id>/`. A standalone failed-audit evidence output must
receive its output directory explicitly from its caller; its exact public
request and filenames are deferred to a separately reviewed contract. No
random run ID, timestamp naming, cwd lookup, or new implicit API is permitted.

### 5. Required contract tests

The separately authorized implementation must add tests that prove:

- `AuditRequest` has the exact field order/types and candidate/baseline cannot
  be inferred or substituted;
- V1.17 accepts only Task 4 50/52 JSON with V1.16 baseline, and V1.18 accepts
  only frozen 452×54 JSON with V1.17 baseline;
- candidate and baseline missing/type failures, candidate digest capture, and
  baseline digest mismatch occur before partial audit;
- `AuditInputEvidence(candidate_json, baseline_database)` has the exact frozen
  fields, is owned only by `AuditResult`, and every returned result preserves
  the request baseline `ArtifactRef` by value;
- preflight failure returns no evidence/report/result; passed and blocked
  results use the same baseline evidence equality rule;
- profiles perform no filesystem or SQLite access;
- transformer accepts `AuditResult`, internally calls `require_passed()`, maps a
  failed result to `AuditBlockedError`, rejects empty/V1.18/mixed input with
  `PipelineError`, and adds no provenance or parallel pass token;
- the decision is deterministic, every release record directly retains its
  audit envelope, `ReleaseCompatibility` remains reusable without being written
  back into the V1.17 envelope, and source order is oracle/byte-equivalent;
- database cannot manufacture or rewrite V1.17 publication fields;
- the sole V1.18 compatibility projection accepts only upstream
  `record_status="audit_passed"`, persists `"published"` only at the frozen
  SQLite serialization boundary, leaves the original typed carriers unchanged,
  rejects every other source status, and cannot affect V1.17 or be reversed;
- database validates the existing frozen V1.17 manifest identity before any
  output parent or temporary database is created: `release_version="V1.17"`,
  `release_status="formal"`, `schema_version="complete-question-v1.0"`, and
  `release_model="transitional-dual-layer"`. V1.17 additionally binds
  `baseline_v116_sqlite_sha256`; V1.18 additionally binds the V1.17 baseline
  filename under `artifact_sha256`. Correct database digest with a wrong or
  missing manifest identity/binding must be rejected;
- `AuditReport` record-level counts, distinct-blocked formulas, sorted tuple
  keys, and result/report lowercase status equivalence are owned by audit;
  inconsistent result/report/envelope state raises `PipelineError`, and export
  does not recompute it;
- `DatabaseBuildRequest`, `ExportRequest`, `ExportContract`,
  `DerivedArtifacts`, and the reduced `ReleaseContract` have the exact frozen
  field order and types;
- `ExportRequest` rejects count, order, value, profile, or direct-envelope
  mismatch before writing;
- failed audit evidence uses deterministic caller-provided location and cannot
  create database/candidate/promotion artifacts;
- maintained candidate loading never calls the legacy SQLite extractor, while
  legacy remains available only inside tests as an oracle.
- one `AuditInputEvidence` produces all V1.17 candidate/baseline manifest scalar
  projections, while `baseline_v116_zip_sha256` equals only the approved frozen
  historical constant; serializer accepts no independent raw digest parameter,
  does not read legacy `BASE_ZIP_SHA256`, and V1.17 still passes its historical
  oracle and byte-equivalence;
- one `AuditInputEvidence` produces V1.18
  `baseline_v117_sqlite_sha256`; the manifest passes frozen
  `verify_task6_release.py`, does not emit a V1.16 ZIP field, structured evidence
  node, or new digest field;
- manifest scalars cannot construct maintained evidence, carrier/projection
  inconsistency raises `PipelineError`, and export/release never reread or
  rehash candidate/baseline inputs;
- `artifact_sha256` remains exclusively the generated-output hash collection.

### 6. Minimal implementation files and commit order

The contract revision itself changes only the two Task 8A authority documents.
After separate authorizations, the minimum expected implementation surface is:

- `src/joy_m2/models.py` and `tests/unit/test_pipeline_models.py` for the Phase 2
  request/evidence/report/release/export values and closed status/count
  invariants; Task 3A is specifically authorized to revisit only these two
  files for the three frozen V1.17 release models and the
  `DatabaseBuildRequest.batch` union migration described below;
- `src/joy_m2/audit/profiles.py`, `src/joy_m2/audit/pipeline.py`, and focused
  audit tests for JSON-backed profiles and explicit baseline preflight;
- `src/joy_m2/release/transformers.py` and a focused V1.17 transformer test;
- `src/joy_m2/db/pipeline.py` and integration tests for typed batch consumption;
- `src/joy_m2/export/formats.py`, `src/joy_m2/export/pipeline.py`, and integration
  tests for typed audit evidence without digest duplication;
- `src/joy_m2/release/pipeline.py` and end-to-end tests for frozen manifest
  scalar projections, including the V1.17-only historical ZIP compatibility
  constant, only after lower stages pass independently.
- `tests/regression/test_task7_project_initialization.py`, limited to two
  controlled edits of its one historical Task 8 pipeline non-existence
  assertion: Stage 1 replaces it with the transitional subset + required-three
  rule, and Task 4 Stage 2 upgrades that same assertion to the permanent
  four-file exact-set rule. No other Task 7 assertion may be deleted, weakened,
  or rewritten.

Recommended implementation commit order is: migrate the Task 7 temporal gate
and add behavior-free approved pipeline scaffolds; Phase 2 public
contracts/tests; JSON-backed audit; V1.17 transformer; database consumption;
typed audit export; release orchestration and end-to-end equivalence. Each
commit requires its own explicit authorization and review gate.

### 7. First implementation step: migrate the Task 7 temporal gate

Task 7 originally passed 7/7 with
`test_task7_does_not_implement_the_task8_pipeline`, which asserted that
`src/joy_m2/audit/pipeline.py`, `src/joy_m2/export/pipeline.py`, and
`src/joy_m2/release/pipeline.py` did not exist. That was the correct historical
gate for Task 7 project initialization: it proved Task 8 implementation had not
started early. It is not a permanent architecture invariant after approved
Phase 2 intentionally adds those modules. This migration preserves, rather
than revises, the historical Task 7 acceptance conclusion.

**Files:**
- Modify: `tests/regression/test_task7_project_initialization.py`
- Create: `src/joy_m2/audit/pipeline.py`
- Create: `src/joy_m2/export/pipeline.py`
- Create: `src/joy_m2/release/pipeline.py`

This Stage 1 test modification is authorized only for replacing that single
temporal test. Keep the other six Task 7 tests and their assertions unchanged,
so the migrated suite remains exactly seven tests. The replacement test must
use a literal expected set and prove all of the following in one structural
boundary:

1. every discovered `src/joy_m2/**/pipeline.py` belongs to the literal approved
   set `audit/pipeline.py`, `db/pipeline.py`, `export/pipeline.py`, and
   `release/pipeline.py`; the literal required set
   `audit/pipeline.py`, `export/pipeline.py`, and `release/pipeline.py` is
   present after this migration. Every discovered file is regular and not a
   symlink. `db/pipeline.py` remains absent until Task 4 creates it through its
   focused RED/GREEN cycle, after which it is already permitted by this gate.
   No other maintained Python module whose filename contains `pipeline` may
   exist;
2. `src/joy_m2/__init__.py` and the existing `audit`, `db`, `export`, and
   `release` package `__init__.py` files remain present, while the existing
   project-entry bootstrap test remains unchanged;
3. the original gate's still-unapproved `src/joy_m2/db/migrate.py` remains
   absent; `src/joy_m2/cli.py` and `src/joy_m2/__main__.py` remain absent and
   `pyproject.toml` has no `[project.scripts]` table; the approved pipeline
   files remain importable library modules, with no separately executable or
   command entry point. An AST scan of all `src/joy_m2/**/*.py` permits
   `audit_batch` definitions only in `audit/pipeline.py`,
   `build_database`/`verify_database` only in `db/pipeline.py`,
   `export_database`/`verify_exports` only in `export/pipeline.py`, and
   `build_candidate`/`promote_candidate` only in `release/pipeline.py`;
4. `legacy/` contains no Python module whose filename includes `pipeline`, and
   an AST inspection of every discovered maintained pipeline module finds no
   import whose top-level package is `legacy`; tests may invoke legacy as an
   oracle, maintained runtime may not;
5. the existing minimal-legacy-snapshot and four frozen V1.18 tests remain
   unchanged. The migration cannot edit a frozen artifact, baseline lock,
   protected hash, SQLite file, or validator to pass.

- [ ] **Step 1: Replace the historical assertion and verify RED**

Make only the test replacement above, before creating any pipeline module.
Run:

```bash
$task8_python -m unittest -v tests.regression.test_task7_project_initialization
```

Expected: exactly 7 tests collected, 6 PASS/1 FAIL. The sole failure must
report that the literal three-file required pipeline set is missing; syntax,
import, frozen-hash, SQLite, legacy-snapshot, or verifier failures are not an
acceptable RED.

- [ ] **Step 2: Add minimal approved module scaffolds and verify GREEN**

Create the three required `pipeline.py` files with only a module docstring. They
must be directly importable, contain no public behavior API, import no legacy
module, and perform no filesystem, database, hashing, export, or release work.
Then rerun the command above.

Expected: the migrated Task 7 suite returns to exactly 7/7 PASS. This GREEN
proves only the approved transitional package/location boundary. It does not satisfy any
later audit/database/export/release behavior test: those tests must still be
written first and fail because their public function or behavior is absent.

The three-file required set is only the planned transition before Task 4.
Task 4 must perform the separately authorized Stage 2 edit and prove its RED
before its focused RED remains the first authority to create `db/pipeline.py`.
After Task 4 GREEN, every run of this migrated Task 7 test must enforce exact
equality to the complete four-file approved set. After this structural commit
is independently approved, append the migrated Task 7 command to every later
Task 3/3A/4/5/6/7 focused gate as a continuous 7/7 regression; the final Task 8
command below remains mandatory.

- [ ] **Step 3: Commit the structural migration separately**

```bash
git add tests/regression/test_task7_project_initialization.py \
  src/joy_m2/audit/pipeline.py \
  src/joy_m2/export/pipeline.py \
  src/joy_m2/release/pipeline.py
git diff --cached --check
git commit -m "test: migrate Task 7 pipeline structure gate"
```

Do not delete the test, permit any path outside the four-item literal approved
set, add skip or expected-failure handling, implement a behavior API in these
scaffolds, or start the next Phase 2 step before this commit receives its
required review.

---

### Task 3: Implement Aggregating Task 5/6 Audit Profiles

**Files:**
- Create: `src/joy_m2/audit/profiles.py`
- Modify: `src/joy_m2/audit/pipeline.py`
- Modify: `src/joy_m2/audit/__init__.py`
- Create: `tests/unit/test_audit_pipeline.py`

**Interfaces:**
- Consumes: `AuditRequest`, `AuditContract`, `AuditedRecord`,
  `Task4Compatibility`, `ReleaseCompatibility`, `AuditInputEvidence`,
  `AuditReport`, `AuditResult`, `AuditedBatch`, and input exceptions from Task 2.
- Produces: `audit_batch(request: AuditRequest) -> AuditResult` with stable issue codes and byte-equivalent passed records.

- [ ] **Step 1: Write failing Task 6 happy-path tests**

Use the frozen 452-record, 54-field V1.18 audited JSON as
`AuditRequest.candidate_path` and the protected V1.17 database under
`legacy/outputs/25757421d1d8/Task5_V1.17_正式入库/` as the separate
`baseline_database`. Assert 452 `AuditedRecord` envelopes, 23 sources, unique
IDs, preserved JSON record order, answer counts 347/71/34, 33 image references,
and no blockers. Do not extract candidate records from the baseline. Do not
assert or populate a `source_order` field on `AuditedQuestion`; compatibility
replay obtains it only from the same envelope's `ReleaseCompatibility`.

```python
result = audit_batch(task6_request(ROOT))
self.assertEqual(len(result.records), 452)
self.assertEqual(result.status, "passed")
self.assertEqual(result.report.status, "passed")
self.assertEqual(result.report.answer_status_counts, (("ai_solved_verified", 71), ("missing_from_source", 34), ("source_provided", 347)))
self.assertEqual(result.require_passed().records, result.records)
```

Run:

```bash
$task8_python -m unittest -v tests.unit.test_audit_pipeline.Task6AuditContractTests
```

Expected: FAIL because `audit_batch` is not implemented.

- [ ] **Step 2: Implement fatal input validation and explicit candidate loading**

Before producing records, independently require the candidate JSON, baseline
database, and asset root to exist with the correct kinds; compute candidate
path/size/SHA into observed `ArtifactRef`, verify baseline path/kind/size/SHA
against its expected `ArtifactRef`, construct the sole `AuditInputEvidence`, decode
the exact 452-record JSON container, and open baseline SQLite read-only only to
seed duplicate references and validate the protected baseline. Map missing
candidate/asset missing files to `InputMissingError`, invalid SQLite/JSON to
`InputFormatError`, and missing or mismatched expected baseline identity to
`BaselineMismatchError`, all before any evidence,
report, or result is exposed. The Task 6 SQLite join and
its `ORDER BY` remain test-oracle code only and must not be called by maintained
candidate loading.

- [ ] **Step 3: Implement exact V1.18 JSON parsing without approval coupling**

Parse the already-audited frozen V1.18 JSON through the exact 54-field profile.
The legacy extraction/conversion rules for excluded source, 2026 marks, Joy
Levels, answer identity, tag cleaning, source hashes, and Q8 notes are comparison
oracles, not maintained candidate transformations. Resolve image references and
apply the approved normalized-text duplicate rule in `audit/pipeline.py`. Do not
manufacture a new approval or populate `formal_release_version`, `selectable`,
or `source_order` on `AuditedQuestion`. Preserve the input publication fields
inside typed `PublicationEvidence` and its three release-only
values inside the exact public `ReleaseCompatibility` on the same
`AuditedRecord`; the V1.18 compatibility serializer maps only those preserved
values back to their historical JSON keys. It must not create that carrier from
missing fields or derive any of its values.
Future promotion authority still comes only from `ApprovalRecord`.

- [ ] **Step 4: Implement issue aggregation**

For each `record.question` append stable issues rather than raising immediately:

```python
AuditIssue("missing_question_text", "blocker", question_id, "question_text_original", "empty")
AuditIssue("invalid_difficulty", "blocker", question_id, "difficulty_level", str(level))
AuditIssue("missing_solution", "blocker", question_id, "solution_verified", answer_status)
AuditIssue("missing_image", "blocker", question_id, "image_paths", relative_path)
AuditIssue("exact_duplicate", "blocker", question_id, "question_text_original", duplicate_id)
AuditIssue("invalid_tag", "blocker", question_id, "tags", tag)
```

Continue processing any field that remains interpretable. Return all issues in deterministic `(question_id, code, field, evidence)` order.

Construct `AuditReport` from all parsed records using the frozen distinct-record
formulas. Sort answer/source tuple keys lexically. Set result/report status to
`"passed"` only for empty issues and `"failed"` otherwise; reject any internal
count/status/envelope inconsistency with `PipelineError`.

- [ ] **Step 5: Add failure aggregation tests**

Create temporary candidate JSON values with two exact duplicates, a missing
image reference, an invalid tag, and an empty non-missing answer; keep the
protected baseline read-only. Assert all relevant issue codes are present in one
result and `require_passed()` raises `AuditBlockedError` without any output
database. Assert the failed result retains the same verified baseline evidence
as the request. Also test that missing/type/baseline preflight failures expose no
`AuditInputEvidence`, `AuditReport`, or `AuditResult`, and that profile-count
validation rejects an empty candidate while the public empty PASS result remains
constructible.

- [ ] **Step 6: Add Task 5 profile tests**

Load the Task 4 candidate JSON through a Task 5 `AuditContract` and pass the
protected V1.16 SQLite separately as `baseline_database`; assert exactly
45 unique `audit_passed` envelopes with no unresolved issues, and preserve their
order. Assert every envelope has a `Task4Compatibility`, including all 24
double-absent records, and has `release_compatibility=None`. Assert a non-eligible
record raises `InputFormatError` fail-fast without a partial result or business
issue, while a successfully parsed duplicate produces the approved
`exact_duplicate` blocker rather than a published row.

- [ ] **Step 7: Compare passing audit records with legacy JSON bytes**

For already-issued V1.18 compatibility input, serialize through the approved
profile serializer and assert the exact 54-field record mappings are unchanged,
including the three values preserved in each `AuditedRecord` outside
`AuditedQuestion`. Compare every audit-stage core value and its stable order
with the Task 6 oracle after excluding the three release-only fields; do not
invent those fields to force direct byte equality. Full V1.18 compatibility
bytes require serialization of envelopes whose three values came from the
frozen input, followed by `export/formats.py` encoding; the release transformer
does not participate in that path.

- [ ] **Step 8: Run audit and legacy gates**

```bash
$task8_python -m unittest -v tests.unit.test_audit_pipeline tests.regression.test_task8b_legacy_pipeline_behavior
$task8_python -m unittest -v tests.regression.test_task7_project_initialization
(cd legacy && $task8_python -m unittest -v task6_work/test_task6_migration.py)
```

Expected: all PASS.

- [ ] **Step 9: Commit audit migration**

```bash
git add src/joy_m2/audit tests/unit/test_audit_pipeline.py
git diff --cached --check
git commit -m "feat: add typed audit pipeline"
```

---

### Task 3A: Implement the V1.17 Historical Release Transformer

**Files:**
- Modify: `src/joy_m2/models.py` (only `V117ReleaseDecision`,
  `V117ReleaseRecord`, `V117ReleaseBatch`, and
  `DatabaseBuildRequest.batch: AuditedBatch | V117ReleaseBatch`)
- Modify: `tests/unit/test_pipeline_models.py` (only exact tests for those
  release models and that batch-type migration)
- Create: `src/joy_m2/release/transformers.py`
- Modify: `src/joy_m2/release/__init__.py`
- Create: `tests/unit/test_v117_release_transformer.py`

This five-file list is the complete Task 3A modification scope. It authorizes
no other production, test, data, release, legacy, validator, state, or contract
file.

**Interfaces:**
- Consumes: a V1.17 `AuditResult` and an explicit `V117ReleaseDecision`; the
  transformer calls `require_passed()` internally.
- Produces: `transform_v117_release(...) -> V117ReleaseBatch` with direct,
  ordered audit-envelope retention.

- [ ] **Step 1: Write the failing public release-model tests**

Modify only `tests/unit/test_pipeline_models.py`. Assert the exact approved
field names, order, type hints, frozen behavior, validation, deterministic
record ordering, and ownership for `V117ReleaseDecision`,
`V117ReleaseRecord`, and `V117ReleaseBatch`. Add exact
`DatabaseBuildRequest.batch` tests proving that `AuditedBatch` remains valid,
`V117ReleaseBatch` becomes valid, every other batch type is rejected, and no
other `DatabaseBuildRequest` field or behavior changes.

Run the public-model suite before changing `models.py`. Expected: RED only
because the three approved release models are absent and
`DatabaseBuildRequest.batch` still has the old `AuditedBatch`-only contract;
syntax, fixture, unrelated import, or setup errors are not acceptable.

- [ ] **Step 2: Implement the minimal public release models and verify GREEN**

Modify only `src/joy_m2/models.py`. Add the three dataclasses with exactly the
fields and frozen semantics in the approved design, with no convenience fields
or third release-batch carrier. Preserve input order in
`V117ReleaseBatch.records`. Migrate only `DatabaseBuildRequest.batch` to
`AuditedBatch | V117ReleaseBatch`; keep all other fields and behavior unchanged.
Run the complete public-model suite and require GREEN before writing any
transformer behavior test.

- [ ] **Step 3: Write failing transformer contract and boundary tests**

Create `tests/unit/test_v117_release_transformer.py`. Assert
`AuditBlockedError` for a failed result, `PipelineError` for empty/V1.18/mixed
input, no clock/environment/registry/identity/parallel-pass/`ApprovalRecord`
dependency, and one direct `AuditedRecord` child per output record. Assert
neither compatibility carrier on the retained `AuditedRecord` is changed. Run
the focused transformer suite before creating `release/transformers.py` and
require RED only because the approved transformer API/behavior is absent; an
unrelated model, syntax, path, fixture, or setup error is not acceptable.

- [ ] **Step 4: Implement the minimal deterministic transformer**

Call `result.require_passed()` internally, then apply only the seven protected
V1.17 historical operations frozen above. Create
release-stage `PublicationEvidence`, `ReleaseCompatibility`, and schema value on
the direct wrapper. Preserve input order and cardinality. Do not serialize JSON
or access files/databases.

- [ ] **Step 5: Export only the approved transformer API**

Modify `src/joy_m2/release/__init__.py` only to expose the approved
`transform_v117_release` API. The public release types remain owned by
`models.py`; do not re-declare them here. Do not add release orchestration,
manifest, database, export, file, hashing, clock, environment, registry, or
V1.16 ZIP behavior.

At this Task 3A checkpoint, lock the exact temporal package surface as
`release.__all__ == ("transform_v117_release",)`. This proves that Phase B
orchestration APIs were not exposed early and preserves the historical Task 3A
`6/6 PASS` as valid. It is not a permanent post-Phase-B architecture invariant:
Phase B is separately authorized below to migrate only this one public-surface
assertion to the final five-name tuple, without changing any transformer
behavior or other Task 3A protection.

- [ ] **Step 6: Prove source-order and record equivalence**

Compare all 45 transformed records against the protected legacy oracle,
including 1-based `source_order`, 53/55-field mapping, Task 4 key presence,
publication values, and final byte-equivalence after the approved serializer.
Position alone is not accepted as proof; the oracle comparison is required.

- [ ] **Step 7: Verify focused GREEN and all prerequisite regressions**

Run the focused transformer suite, the complete public-model and audit suites,
and the continuous compatibility gates:

```bash
$task8_python -m unittest -v tests.unit.test_v117_release_transformer
$task8_python -m unittest -v tests.unit.test_pipeline_models
$task8_python -m unittest -v tests.unit.test_pipeline_models tests.unit.test_pipeline_config
$task8_python -m unittest -v tests.unit.test_audit_pipeline
$task8_python -m unittest -v tests.regression.test_task7_project_initialization
(cd legacy && $task8_python -m unittest -v task6_work/test_task6_migration.py)
$task8_python releases/V1.18/verify_task6_release.py releases/V1.18
```

Expected: all PASS; Audit remains 21/21, Task 7 remains exactly 7/7, Task 6
remains 22/22, and the independent V1.18 validator reports `PASS`.

- [ ] **Step 8: Commit the models and transformer together after review**

```bash
git add src/joy_m2/models.py \
  src/joy_m2/release/transformers.py \
  src/joy_m2/release/__init__.py \
  tests/unit/test_pipeline_models.py \
  tests/unit/test_v117_release_transformer.py
git diff --cached --check
git commit -m "feat: add V1.17 release transformer"
```

Task 4 remains blocked until this complete five-file Task 3A change has passed
independent review and been committed. Task 4 consumes the already-migrated
`DatabaseBuildRequest.batch: AuditedBatch | V117ReleaseBatch`; it must not add
the release models, repeat this public-model migration, or start from an
unreviewed/uncommitted Task 3A worktree state.

---

### Task 4: Implement Transactional V1.17 and V1.18 Database Builds

**Files:**
- Create: `src/joy_m2/db/profiles.py`
- Create: `src/joy_m2/db/pipeline.py`
- Modify: `src/joy_m2/db/__init__.py`
- Create: `tests/integration/test_db_pipeline.py`
- Modify: `tests/regression/test_task7_project_initialization.py` (Stage 2 only:
  upgrade the one pipeline structural assertion to the four-file exact set;
  leave the other six Task 7 tests and all of their assertions unchanged)

**Interfaces:**
- Consumes: V1.18 `AuditedBatch` or V1.17 `V117ReleaseBatch`, `ReleaseSpec`,
  `DatabaseContract`, and `DatabaseBuildRequest`.
- Produces: `build_database(request) -> DatabaseArtifact` and `verify_database(path, contract) -> VerificationReport`.

- [ ] **Step 1: Upgrade the Task 7 structural gate to Stage 2 and verify RED**

Before creating `src/joy_m2/db/pipeline.py`, change only the migrated pipeline
structural assertion from the Stage 1 approved-path subset + required-three rule
to exact equality with this independently written literal set:

```text
{
  audit/pipeline.py,
  db/pipeline.py,
  export/pipeline.py,
  release/pipeline.py,
}
```

Do not modify the other six Task 7 tests or weaken the existing forbidden-path,
legacy, bootstrap/package, or frozen V1.18 checks. Run:

```bash
$task8_python -m unittest -v tests.regression.test_task7_project_initialization
```

Expected: exactly 7 tests collected, 6 PASS/1 FAIL. The sole failure must report
that `db/pipeline.py` is missing. If any other test or condition fails, stop and
report a contract/implementation deviation; do not create the database module.

- [ ] **Step 2: Write the failing V1.18 byte-equivalence test**

Audit the 452 candidates with Task 3, build to a new temporary path, and assert:

```python
self.assertEqual(sha256(output_db), "fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7")
self.assertEqual(output_db.read_bytes(), (ROOT / "releases/V1.18/Joy_M2_Complete_Question_DB_V1_18.sqlite3").read_bytes())
```

Also assert `user_version=118`, integrity `ok`, foreign-key errors 0, 497 total rows, 452 rows with `source_order>45`, and 45 byte/logically unchanged V1.17 rows.

Still without creating `db/pipeline.py`, run and expect an import failure:

```bash
$task8_python -m unittest -v tests.integration.test_db_pipeline.V118DatabaseBuildTests
```

- [ ] **Step 3: Implement protected baseline validation**

Only after both the Stage 2 structural RED and the focused database RED above
are confirmed, create `db/pipeline.py` for the first time. Validate the source
path, V1.17 hash, manifest identity and binding, integrity, foreign keys, 45 V2
rows, and 497 compatibility-view rows before creating the output parent or file.
`baseline_manifest` is the existing frozen V1.17 formal manifest. For both
profiles require its existing identity fields to be exactly
`release_version="V1.17"`, `release_status="formal"`,
`schema_version="complete-question-v1.0"`, and
`release_model="transitional-dual-layer"`; no new `profile` field is added.
For a V1.17 build require
`baseline_v116_sqlite_sha256 == baseline_database.sha256`. For a V1.18 build
require `artifact_sha256[Path(baseline_database.path).name] ==
baseline_database.sha256`. Map each failure to the specified input/database
exception.

After this authority remediation passes independent review and before changing
the paused production implementation, add two focused RED groups to
`tests/integration/test_db_pipeline.py` and run them:

1. V1.18 serialization projection: assert upstream `audit_passed`, original
   `AuditedRecord`/`AuditedBatch` unchanged, persisted SQLite `published`, every
   other source status rejected before output, and the V1.17 path unchanged.
2. Manifest identity: with the correct SQLite digest, change
   `release_version` to `V9.99`, change or remove `schema_version`,
   `release_status`, or `release_model`, and remove or corrupt the required
   profile-specific baseline binding. Every case must fail before any output
   parent, temporary database, or output file exists.

Both groups must fail for the missing production contract rather than import,
fixture, or setup errors. Only after both RED groups are confirmed may the
minimal production correction begin.

- [ ] **Step 4: Implement the V1.18 transaction**

Copy the baseline to a temporary database in the target parent, set `foreign_keys=ON` and `journal_mode=DELETE`, begin one immediate transaction, insert all typed rows and tags in stable order, rebuild taxonomy from ordered distinct values, update metadata/import run, set `user_version=118`, commit, check integrity/foreign keys, and run `VACUUM` exactly where the legacy profile requires it.

Database retains no publication business authority. At the row-serialization
boundary only, require each V1.18 upstream record to have exact
`record_status="audit_passed"` and persist `"published"` solely as the frozen
V1.18 historical compatibility projection. Do not mutate the input record or
batch, do not accept another source status, do not reverse the mapping, and do
not reuse this exception for V1.17 or any other stage/version.

Use the exact `DB_TABLE_COLUMNS` order from the oracle as a named constant in `profiles.py`; every JSON-valued cell uses the approved canonical JSON serializer.

- [ ] **Step 5: Make publication of the database atomic**

Run final read-only verification against the temporary file. Only after PASS, use `Path.replace(output_path)` when `output_path` does not exist. On any exception, remove only the known temporary file and leave `output_path` absent.

- [ ] **Step 6: Add duplicate, foreign-key, integrity, and conflict tests**

Inject a duplicate ID, an unknown `source_id`, a malformed baseline, and an existing output path. Assert `AuditBlockedError`, `ForeignKeyViolationError`, `DatabaseIntegrityError` or `BaselineMismatchError`, and `OutputConflictError` as applicable. After each failure assert the original target bytes are absent or unchanged.

- [ ] **Step 7: Add V1.17 build support and equivalence**

Implement the schema-creation profile from Task 5, accepting only the
`V117ReleaseBatch` produced by Task 3A and copying its already-decided
publication values without creating or rewriting them. Include V2 tables,
constraints, indexes, metadata, taxonomy, import run, selectable view,
`user_version=117`, and `VACUUM`. Assert the temporary output database bytes
equal the protected V1.17 database and the V1.16 historical tables are logically
unchanged. Assert an audit-stage `AuditedBatch` is rejected for V1.17 before
output creation.

- [ ] **Step 8: Run database, audit, and permanent structural suites**

```bash
$task8_python -m unittest -v tests.integration.test_db_pipeline tests.unit.test_audit_pipeline
$task8_python -m unittest -v tests.regression.test_task7_project_initialization
```

Expected: all PASS, with Task 7 restored to exactly 7/7 and its structural test
now permanently enforcing exact equality to the complete four-file approved
pipeline set. Deleting `db/pipeline.py` or adding a fifth maintained pipeline
module must fail this test; no later implementation may restore the Stage 1
subset rule.

- [ ] **Step 9: Commit database migration**

```bash
git add src/joy_m2/db \
  tests/integration/test_db_pipeline.py \
  tests/regression/test_task7_project_initialization.py
git diff --cached --check
git commit -m "feat: add transactional database pipeline"
```

---

### Task 5: Implement Deterministic Database and Audit-Evidence Exports

**Files:**
- Modify: `src/joy_m2/models.py` (only the approved Export public carrier migration)
- Modify: `tests/unit/test_pipeline_models.py` (only the corresponding model-contract tests)
- Create: `src/joy_m2/export/formats.py`
- Modify: `src/joy_m2/export/pipeline.py`
- Modify: `src/joy_m2/export/__init__.py`
- Create: `tests/integration/test_export_pipeline.py`

**Interfaces:**
- Consumes: `DatabaseArtifact`, the original `AuditResult`, its directly
  corresponding `AuditedBatch | V117ReleaseBatch`, `ExportContract`, and a
  current staging output directory.
- Produces: `export_database(request) -> DerivedArtifacts` and `verify_exports(request) -> VerificationReport`.

This is the complete Task 5 modification scope; no other source, test, data,
release, legacy, or documentation file is implicitly authorized. Task 5 owns
implementation of the already-approved Export public carrier definitions in
the design, not their redesign. It may add no convenience field or third batch
carrier and must not alter any other public model contract.

#### Phase A: Export Public Models RED -> GREEN

- [ ] **Step 1: Write failing Export public-model contract tests**

Modify only `tests/unit/test_pipeline_models.py`. Assert the exact field order,
types, frozen behavior, runtime validation, and lack of defaults or extra fields
for these approved migrations:

```python
@dataclass(frozen=True)
class ExportContract:
    profile: str
    audit_records_filename: str
    audit_report_filename: str
    csv_filename: str
    knowledge_markdown_filename: str
    import_report_filename: str
    project_state_filename: str
    taxonomy_filename: str | None
    expected_question_count: int
    expected_missing_answer_count: int

@dataclass(frozen=True)
class ExportRequest:
    database: DatabaseArtifact
    audit_result: AuditResult
    record_batch: AuditedBatch | V117ReleaseBatch
    output_dir: Path
    contract: ExportContract

@dataclass(frozen=True)
class DerivedArtifacts:
    csv: ArtifactRef
    knowledge_markdown: ArtifactRef
    import_report: ArtifactRef
    project_state: ArtifactRef
    taxonomy: ArtifactRef | None
    audit_records: ArtifactRef
    audit_report: ArtifactRef
```

The `ExportRequest` tests must accept only the two approved batch types and must
show that `audit_result` and `record_batch` are part of this one public carrier,
not parallel arguments or digest/evidence fields. Do not modify `models.py` yet.
Run the Public Models suite and require a real RED caused only by the old public
carrier shapes. Import, setup, fixture, or unrelated failures are not valid RED.

- [ ] **Step 2: Implement the minimal Export public-model migration**

Only after the model RED is confirmed, minimally modify `src/joy_m2/models.py`
to implement the three exact approved structures. Preserve existing path
normalization, shared frozen/runtime-type rules, all existing field meanings,
and the absence of independent input-evidence or digest fields.

- [ ] **Step 3: Restore Public Models GREEN**

Run `tests.unit.test_pipeline_models` and require all tests to pass before any
Export behavior test or production Export implementation is created.

#### Phase B: Export behavior RED -> GREEN

- [ ] **Step 4: Write failing serializer/format contract tests**

With all Export production files still unchanged, create or modify the focused
serializer/format tests. Assert canonical JSON bytes, evidence JSON bytes, CSV
BOM/CRLF, LF-only text, field ordering, deterministic bytes, and exactly one
trailing newline:

```python
self.assertEqual(canonical_json_bytes({"中": [2, 1]}), b'{"\xe4\xb8\xad":[2,1]}')
self.assertEqual(evidence_json_bytes({"b": 1, "a": "中"}), '{\n  "a": "中",\n  "b": 1\n}\n'.encode())
```

Run:

```bash
$task8_python -m unittest -v tests.integration.test_export_pipeline.FormatContractTests
```

Expected: FAIL through explicit assertions because the approved serializer APIs
or behavior are absent. A `ModuleNotFoundError`, import/setup error, fixture
error, test-construction error, environment error, or Public Models dependency
error is not a valid RED. Do not create or modify `export/formats.py`,
`export/pipeline.py`, or `export/__init__.py` yet.

- [ ] **Step 5: Write failing pipeline and equivalence tests**

Still without changing any Export production file, add focused tests for
`export_database`, `verify_exports`, the typed `ExportRequest`, exact
`DerivedArtifacts` output binding, deterministic artifact bytes, atomic
write/cleanup, and invalid, mismatched, pre-existing, or conflicting inputs.

Build a temporary V1.18 database through Task 4, retain the exact Task 3
`AuditResult` and `AuditedBatch`, and export all V1.18 profile files. Compare
CSV, knowledge Markdown, audit JSON, audit report, import report, and
project-state bytes to their `releases/V1.18/` counterparts. Assert CSV rows
equal every SQLite cell after NULL-to-empty conversion, Markdown contains 497
unique headings plus 34 missing-source markers, and the audit report bytes encode
the existing `AuditReport` without exporter-side recounting. Assert typed
`AuditReport.status` is validated but omitted from the frozen V1.18 JSON schema,
which remains byte-equivalent.

Assert export accepts no raw input digest parameter, returns no input-evidence
carrier/scalar, and never rereads or rehashes candidate/baseline files. Frozen
manifest projection assertions belong to Task 7 release orchestration below.

Pass the exact original V1.17 `AuditResult` and Task 3A `V117ReleaseBatch`.
Assert V1.17 CSV, knowledge Markdown, report, project state, approved JSON, and
taxonomy JSON bytes equal the protected legacy Task 5 release artifacts, and
that a reordered, truncated, or unrelated release batch is rejected before
writing. Assert export accepts no independent candidate/database/ZIP digest
argument, does not expose a parallel carrier, and does not read legacy
`BASE_ZIP_SHA256`. V1.17 manifest mapping/oracle tests belong to Task 7.

The pipeline/equivalence group must remain importable and fail through explicit
contract assertions because the corresponding Export behavior is absent. An
import/setup error, fixture error, test-construction error, environment error,
or Public Models dependency error is not a valid RED. Do not create or modify
`export/formats.py`, `export/pipeline.py`, or `export/__init__.py` yet.

- [ ] **Step 6: Validate both RED groups before production**

Run the serializer/format group and the pipeline/equivalence group separately.
Record the command, collected count, PASS/FAIL/ERROR counts, exit code, and the
specific missing Export behavior for every failure. Both groups must have a
non-zero exit code caused only by their corresponding absent production
behavior. Only after both valid REDs are confirmed may any Export production
file change.

The forbidden sequence is:

```text
serializer RED -> implement formats.py -> pipeline RED
```

The only approved Phase B sequence is:

```text
serializer RED
-> pipeline/equivalence RED
-> verify both REDs
-> minimal Export production implementation
-> unified GREEN
-> full regression gates
```

Only after Step 6 may Steps 7-9 create or modify
`src/joy_m2/export/formats.py`, `src/joy_m2/export/pipeline.py`, and
`src/joy_m2/export/__init__.py`. The implementation may proceed in minimum
dependency order, but no one of these three production files may change before
both RED groups are validated.

- [ ] **Step 7: Implement exact format primitives**

Only after Step 6, create `src/joy_m2/export/formats.py`. Use
`json.dumps(ensure_ascii=False, sort_keys=True, separators=(",", ":"))` for
canonical JSON and `indent=2` plus one LF for evidence JSON. Open CSV with
`encoding="utf-8-sig", newline=""` and set `lineterminator="\r\n"`. Normalize
generated Markdown/report/state text to LF before writing and append exactly one
final LF.

- [ ] **Step 8: Implement `export_database`**

Before opening an output, enforce the frozen count/order/direct-envelope
relationship between `audit_result` and `record_batch`. Read only the supplied
`DatabaseArtifact` for CSV/Markdown and database-derived summaries; never reopen
source JSON. Query CSV by `question_id`, Markdown by `source_order`, and database
summaries with explicit `ORDER BY`. Serialize records from the supplied matching
batch and serialize the supplied `AuditReport` without re-auditing or
recounting. Refuse any mismatch, target outside the current staging run, or
existing output file before partial writes.

Do not place input evidence on `ExportRequest`/`DerivedArtifacts`, accept
independent digest scalars, or read manifest scalars backward. Leave manifest
projection to release and keep exported artifact refs limited to generated
outputs.

The complete upstream authority must enter only through the single
`ExportRequest`; `export_database()` must not accept `audit_result` or
`record_batch` as extra positional, keyword-only, private, registry-backed, or
otherwise parallel parameters. `DerivedArtifacts.audit_records` and
`DerivedArtifacts.audit_report` describe only bytes actually generated by
Export. Export may hash and size its generated outputs for those `ArtifactRef`
values, but it must not recompute candidate/baseline evidence,
`AuditInputEvidence`, audit statistics, or the V1.17 release decision.

- [ ] **Step 9: Implement `verify_exports`**

Return individual checks for expected file set, CSV BOM, CSV column/value
equality, row count, Markdown unique headings, missing-answer markers, audit JSON
parseability, batch/report count and order agreement, and deterministic
re-export hashes. Return FAIL for artifact mismatches and raise only when the
verification cannot execute. Modify `src/joy_m2/export/__init__.py` only to
expose the approved `export_database` and `verify_exports` public APIs; add no
compatibility shim or second parameter entry point.

- [ ] **Step 10: Restore unified GREEN, then run full regression gates**

First run the serializer/format focused tests, the pipeline/equivalence focused
tests, and the complete `tests.integration.test_export_pipeline` suite. Require
all three to be GREEN before running the broader database, Task 7, legacy, and
frozen-compatibility gates:

```bash
$task8_python -m unittest -v tests.integration.test_export_pipeline.FormatContractTests
$task8_python -m unittest -v tests.integration.test_export_pipeline.ExportPipelineTests
$task8_python -m unittest -v tests.integration.test_export_pipeline
$task8_python -m unittest -v tests.integration.test_export_pipeline tests.integration.test_db_pipeline
$task8_python -m unittest -v tests.regression.test_task7_project_initialization
(cd legacy/task5_work && $task8_python -m unittest -v test_task5_import.py)
```

Expected: PASS.

- [ ] **Step 11: Commit deterministic exporters**

```bash
git add src/joy_m2/models.py \
  tests/unit/test_pipeline_models.py \
  src/joy_m2/export \
  tests/integration/test_export_pipeline.py
git diff --cached --check
git commit -m "feat: add deterministic SQLite exports"
```

Task 6 release primitives and later release orchestration remain blocked until
this complete Task 5 public-model plus Export behavior change has passed
independent review and been committed. Those later tasks consume the completed
public carriers and must not repeat or assume ownership of this migration.

---

### Release Phase A: Migrate the CandidateBuildRequest Public Carrier

**Files:**
- Modify: `src/joy_m2/models.py` (only the approved `CandidateBuildRequest` migration)
- Modify: `tests/unit/test_pipeline_models.py` (only the corresponding model-contract tests)

The exact target is:

```python
@dataclass(frozen=True)
class CandidateBuildRequest:
    config: PipelineConfig
    run_id: str
    release_spec: ReleaseSpec
    audit_request: AuditRequest
    v117_release_decision: V117ReleaseDecision | None
    baseline_manifest: ArtifactRef
    database_contract: DatabaseContract
    export_contract: ExportContract
    release_contract: ReleaseContract
```

Every field is required and has no default. Both V1.17 and V1.18 require a typed
`baseline_manifest: ArtifactRef`, which orchestration passes unchanged to
`DatabaseBuildRequest`. V1.17 requires an exact `V117ReleaseDecision`; V1.18
requires `v117_release_decision is None` and rejects a non-`None` value. Release
accepts only `release_spec.release_version in {"V1.17", "V1.18"}` in this
maintained build contract and rejects every other/future version at public-model
construction. A future version requires a separately approved version-specific
design, public carrier, publication authority, TDD, and independent review; it
must not reuse `V117ReleaseDecision`, treat it as generic authority, default a
decision, infer publication from audit status, or fall back to V1.17 semantics.
Release must not hard-code or default the V1.17 decision, infer it from audit status,
config, environment, or manifest, recover it from serialized data, discover a
manifest from the filesystem, look beside the baseline database, glob/search a
legacy path, or use a private extra pipeline parameter. All orchestration
authority enters through this one public carrier.

- [ ] **Step A1: Write the Public Models RED**

Modify only `tests/unit/test_pipeline_models.py`. Lock exact fields and order,
exact annotations and runtime types, frozen behavior, lack of defaults, valid
V1.17 and V1.18 combinations, invalid decision and manifest types, V1.17 missing
decision, V1.18 non-`None` decision, unsupported/future version rejection, and
future version plus `V117ReleaseDecision` rejection. Explicitly prove V1.17 plus
decision and V1.18 plus `None` are accepted, while the inverse combinations are
rejected. Require a real RED caused only by the old `CandidateBuildRequest`
shape.

- [ ] **Step A2: Implement the minimal carrier migration**

Only after the valid RED, minimally modify `src/joy_m2/models.py`. Do not change
Audit, Export, Database, Task 3A, or any unrelated public model.

- [ ] **Step A3: Restore Public Models GREEN, review, and commit**

Run the complete Public Models and related model/config regressions. Phase A
must pass independent review and be committed before any Phase B Release test or
production file changes.

### ReleaseContract Public Models Checkpoint: Remove Duplicate Audit Filename Authority

This separately reviewed checkpoint must complete before any Release Phase B
test or production file changes.

**Files:**
- Modify: `src/joy_m2/models.py` (only the approved `ReleaseContract` field deletion)
- Modify: `tests/unit/test_pipeline_models.py` (only the corresponding model-contract tests)

The exact target is:

```python
@dataclass(frozen=True)
class ReleaseContract:
    profile: str
    approval_filename: str
    manifest_filename: str
    sha256sums_filename: str
    candidate_zip_filename: str
    formal_zip_filename: str
    archive_root: str
    protected_artifact_kinds: tuple[str, ...]
    manifest_required_fields: tuple[str, ...]
    hash_excluded_kinds: tuple[str, ...]
    zip_excluded_kinds: tuple[str, ...]
```

Only `audit_records_filename` and `audit_report_filename` are removed. Every
remaining field keeps its exact order, annotation, required/no-default status,
frozen behavior, and existing validation. `ExportContract` remains the sole
owner of those two filename fields. Release later consumes
`DerivedArtifacts.audit_records` and `DerivedArtifacts.audit_report` as produced
by Export and may not rename them, infer filenames, or introduce a second
filename contract. This checkpoint does not modify `CandidateBuildRequest`, any
other public model, or the four approved Phase B orchestration APIs.

- [ ] **Step R1: Write the ReleaseContract Public Models RED**

Modify only `tests/unit/test_pipeline_models.py`. Lock the exact remaining
fields and order, exact annotations and runtime types, no defaults, frozen
behavior, preserved validation, and the absence of
`audit_records_filename`/`audit_report_filename`. Also prove that
`ExportContract` still has both fields and retains its existing authority.
Run the complete Public Models suite and require a real RED caused only by the
committed `ReleaseContract` still containing the duplicate fields. Do not modify
`models.py` yet.

- [ ] **Step R2: Implement the minimal ReleaseContract migration**

Only after the valid RED, modify `src/joy_m2/models.py` solely to delete the two
fields. Do not change any remaining field, validation, `CandidateBuildRequest`,
Audit, Task 3A, Database, Export, or unrelated verification/release models.

- [ ] **Step R3: Restore Public Models GREEN, review, and commit**

Run the complete Public Models and model/config regressions, obtain independent
review, and commit this two-file migration separately. Only after that commit may
Release Phase B restart in the existing order: Task 6 primitives RED, candidate
orchestration RED, approval/promotion RED, verification of all three RED groups,
and then production.

The combined unique Release file set remains these two Public Models files plus
the eight Phase B files listed in Tasks 6 and 7 below. Phase B itself remains
strictly limited to its eight files and may not modify the Public Models files.
No other source, test, data, release, legacy, frozen artifact, or documentation
file is implicitly authorized.

### Release Phase B / Task 6: Implement Hashing, Verification, and Deterministic Packaging

**Files:**
- Create: `src/joy_m2/release/hashing.py`
- Create: `src/joy_m2/release/packaging.py`
- Create: `src/joy_m2/release/verification.py`
- Modify: `src/joy_m2/release/__init__.py`
- Create: `tests/unit/test_release_primitives.py`

**Interfaces:**
- Consumes: `ArtifactRef`, `ReleaseContract`, typed audit/database/export artifacts.
- Produces: SHA/manifest/sums writers, deterministic ZIP builder, `verify_candidate()`, and `verify_release()`.

- [ ] **Step 1: Write failing SHA and manifest tests**

Create three temporary files with non-ASCII names and assert lowercase SHA-256, sorted relative paths, two-space `SHA256SUMS.txt` separation, manifest self-exclusion, sums self-exclusion, and ZIP exclusion.

```python
self.assertEqual(
    sums_path.read_text(encoding="utf-8"),
    f"{sha_a}  a.txt\n{sha_zh}  数据.json\n{sha_manifest}  manifest.json\n",
)
```

- [ ] **Step 2: Write failing deterministic ZIP tests**

Build the same payload twice and assert identical bytes. Inspect every `ZipInfo` for fixed timestamp, `create_system=3`, regular-file `0644`, DEFLATE, sorted names, no directory entries, and the contract root.

- [ ] **Step 3: Write failing structured verification tests**

Start with a valid temporary release, then separately corrupt a protected byte, remove a sums entry, add an undeclared file, alter CSV, remove a Markdown heading, and break the audit report. Assert each fully executable case returns `VerificationReport(status="FAIL")` with its own failed check. Assert missing manifest or malformed JSON raises the appropriate input exception.

- [ ] **Step 4: Validate the complete Release primitive RED without production**

```bash
$task8_python -m unittest -v tests.unit.test_release_primitives
$task8_python -m unittest -v tests.regression.test_task7_project_initialization
```

Expected at this point: non-zero exit because the approved Release primitives are
absent. Record collected, PASS, FAIL, ERROR, exit code, and each precise missing
behavior. Import/setup, fixture, test-construction, environment, Public Models
dependency, or upstream regression errors are not valid RED. Do not create or
modify any Release production file; production remains blocked until both Task 7
RED groups below are also valid.

---

### Release Phase B / Task 7: Implement Atomic Candidate Builds and Approval-Bound Promotion

**Files:**
- Modify: `src/joy_m2/release/pipeline.py`
- Modify: `src/joy_m2/release/__init__.py`
- Create: `tests/integration/test_release_pipeline.py`
- Modify: `tests/unit/test_v117_release_transformer.py` (only the exact
  package-public-surface assertion)

**Interfaces:**
- Consumes: `CandidateBuildRequest`, low-level audit/db/export/release APIs, `ApprovalRecord`, `PipelineConfig`.
- Produces: `build_candidate(request) -> CandidateRelease` and `promote_candidate(candidate, approval, config) -> FormalRelease`.

- [ ] **Step 1: Write the complete candidate-orchestration RED group**

In a temporary repository-shaped root, cover `build_candidate(request)`, the
typed `CandidateBuildRequest`, explicit V1.17 decision, V1.18 `None`, explicit
`baseline_manifest`, Audit -> transformer -> Database -> Export ordering,
manifest projection, exact artifact set, invalid upstream gating, existing run,
ZIP and declared-output conflicts, and stale-candidate rejection. A successful
build may appear only at `data/staging/<run_id>/` after every check passes.
Inject an export failure and assert the valid run directory never appears;
diagnostics may exist only under `.failed/<run_id>/` with a non-formal status.
Do not modify any Release production file.

Run:

```bash
$task8_python -m unittest -v tests.integration.test_release_pipeline.CandidateBuildTests
```

Expected: explicit assertion failures because `build_candidate` behavior is absent.

- [ ] **Step 2: Write the complete approval/promotion RED group**

Still without modifying any Release production file, cover
`promote_candidate(...)`, approval binding, fresh candidate verification, wrong
version, wrong candidate manifest hash, wrong approver, empty scope, invalid
approval timestamp, failed or stale candidate rejection, existing formal-release
conflict, atomic promotion, and frozen promotion semantics. Include successful
synthetic promotion into a temporary `releases/V9.99/`, followed by rejection of
a second promotion. Never exercise promotion against the real workspace.

In this same promotion/public-surface RED group, modify only the existing
`release.__all__` assertion in `tests/unit/test_v117_release_transformer.py`.
Replace its temporal Task 3A expectation with the final exact tuple:

```python
(
    "transform_v117_release",
    "build_candidate",
    "verify_candidate",
    "verify_release",
    "promote_candidate",
)
```

Also require all five names to be directly importable and reject any additional
public name. Do not change the transformer behavior tests, failed-audit gates,
V1.17 profile tests, deterministic mapping tests, or any other Task 3A
protection. This assertion must be RED because the four Phase B APIs have not
yet been exposed; `release/__init__.py` remains unchanged.

- [ ] **Step 3: Validate both Task 7 RED groups before production**

Run candidate-orchestration and approval/promotion groups separately. For each,
record collected, PASS, FAIL, ERROR, exit code, and precise missing Release
behavior. Both groups must be importable and fail only because the corresponding
Release behavior is absent. Public Models dependency, import/setup, fixture,
test-construction, environment, or upstream Audit/Database/Export regression is
not a valid RED. The Task 6 primitive RED must also remain valid.

The forbidden sequence is:

```text
candidate RED -> implement build_candidate() -> promotion RED
```

The only approved Phase B sequence is:

```text
Task 6 primitive RED
-> candidate orchestration RED
-> approval/promotion RED
-> verify both Task 7 RED groups (and retain the primitive RED)
-> minimal Release production implementation
-> unified focused GREEN
-> full regression/frozen compatibility gates
```

Before this gate passes, do not create or modify `release/hashing.py`,
`release/packaging.py`, `release/verification.py`, `release/pipeline.py`, or
`release/__init__.py`.

- [ ] **Step 4: Implement minimal Release production in dependency order**

First expose the approved hashing and manifest primitives:

```python
sha256_bytes(value: bytes) -> str
sha256_file(path: Path) -> str
write_manifest(path: Path, payload: Mapping[str, object]) -> ArtifactRef
write_sha256sums(path: Path, protected: tuple[ArtifactRef, ...]) -> ArtifactRef
```

Sort protected paths by POSIX relative path and reject duplicate paths, absolute
archive paths, `..`, or inclusion of sums/ZIP. Implement deterministic ZIP with
fixed 1980 timestamp, Unix regular-file `0644`, `create_system=3`, DEFLATE level
9, sorted names and no directory entries. Implement independent candidate and
release verification without calling builder functions. Only then implement
`build_candidate` and `promote_candidate`.

After all three RED groups are valid, update `release/__init__.py` to retain
`transform_v117_release` and expose the four Phase B APIs. Its final exact
`__all__` is the five-name tuple above in that order. Expose no hashing,
packaging, verification helper, private API, or compatibility shim. This public
surface union does not merge authority: Task 3A retains transformer and V1.17
publication ownership; the four new names retain only their approved
orchestration, verification, and promotion responsibilities. CandidateBuildRequest,
Database, Export, and manifest-projection authority remain unchanged.

`build_candidate` preflights every input and output conflict before creating its
hidden temporary run, consumes the exact request `baseline_manifest`, calls
`audit_batch()`, passes the V1.17 request decision unchanged to
`transform_v117_release()` or requires V1.18 `None`, then calls Database and
Export with the matching typed values. It projects manifest scalars only from
the original `AuditResult.input_evidence` plus the V1.17 historical ZIP constant,
writes sums/ZIP, independently verifies, and atomically renames only a PASS
candidate. It never re-encodes audit JSON, recomputes audit authority, rereads or
rehashes candidate/baseline, accepts raw digest parameters, discovers the
manifest, or reverses manifest scalars. A typed failure may create only the
deterministic `.failed/<run_id>/` diagnostic and must re-raise the original
exception without transformer/database/normal candidate output after failed
audit.

For V1.17 assert `task4_candidate_sha256` and
`baseline_v116_sqlite_sha256` come from evidence and
`baseline_v116_zip_sha256` comes only from
`V117_BASELINE_V116_ZIP_SHA256`. For V1.18 assert only
`baseline_v117_sqlite_sha256`, no V1.16 ZIP field, and the frozen validator.

`promote_candidate` requires fresh candidate PASS, validates version, exact
candidate manifest hash, `approved_by == "Joy"`, timezone-aware timestamp and
non-empty scope, builds only in an unexposed temporary release directory, writes
approval/candidate bindings, regenerates sums/ZIP, independently verifies, and
atomically renames. It never deletes or replaces an existing release and cleans
up only its known temporary directory on failure.

- [ ] **Step 5: Restore unified focused GREEN**

```bash
$task8_python -m unittest -v \
  tests.integration.test_release_pipeline \
  tests.unit.test_release_primitives \
  tests.unit.test_v117_release_transformer
$task8_python -m unittest -v tests.regression.test_task7_project_initialization
```

Expected: PASS.

- [ ] **Step 6: Run full gates, obtain independent review, and commit**

Only after focused GREEN, run every approved maintained, legacy-oracle, Task 7,
and V1.18 frozen-compatibility gate. After independent review, commit only the
eight Phase B files.

---

### Task 8: Prove End-to-End Equivalence and Close Task 8B

**Files:**
- Create: `tests/regression/test_task8b_pipeline_equivalence.py`
- Modify: `PROJECT_STATE.md`
- Create: `docs/reports/TASK8B_VERIFICATION.md`

**Interfaces:**
- Consumes: all maintained APIs and Task 1 legacy oracle fixtures.
- Produces: the final regression gate and evidence that maintained code can replace legacy execution without modifying formal data.

- [ ] **Step 1: Write the end-to-end V1.18 equivalence test**

Build one legacy V1.18 candidate and one maintained V1.18 candidate in separate temporary roots. Assert byte equality for SQLite, CSV, audited-question JSON, audit-report JSON, knowledge Markdown, import report, and generated project-state artifact. Assert the maintained manifest/sums/package satisfy their new contracts and two maintained builds produce byte-identical ZIPs.

- [ ] **Step 2: Add V1.17 equivalence coverage**

Build Task 5 through both oracles in temporary roots and compare SQLite, CSV, approved JSON, taxonomy JSON, knowledge Markdown, report, and generated state bytes. Verify the maintained Task 5 layout profile produces the categorized archive paths required by its contract.

- [ ] **Step 3: Add frozen and compatibility assertions**

Hash every file under `releases/V1.18/` before and after both builds and assert the mappings are identical. Query maintained outputs to assert compatibility tables/views still exist and their logical digests match the frozen inputs.

- [ ] **Step 4: Run all new tests**

```bash
$task8_python -m unittest discover -v -s tests -p 'test_*.py'
```

Expected: all new unit, integration, and regression tests PASS.

- [ ] **Step 5: Run the full legacy and frozen release gate**

```bash
$task8_python -m unittest -v tests/regression/test_task7_project_initialization.py
$task8_python releases/V1.18/verify_task6_release.py releases/V1.18
(cd legacy && $task8_python -m unittest -v task6_work/test_task6_migration.py)
(cd legacy/task5_work && $task8_python -m unittest -v test_task5_import.py)
(cd legacy && $task8_python -m unittest discover -v -s task4_work/task3_package/06_构建与测试 -p 'test_task3_review.py')
(cd legacy && $task8_python -m unittest discover -v -s task4_work/task4_package/05_构建与测试 -p 'test_task4*.py')
```

Expected: Task 7 7/7, V1.18 status PASS, and Task 3–6 54/54.

- [ ] **Step 6: Inspect the complete change set**

```bash
git diff --check origin/main...HEAD
git diff --stat origin/main...HEAD
git diff --name-status origin/main...HEAD
git status --short
```

Expected: only planned source, test, fixture, state, and report files changed; no frozen release/baseline changes; clean worktree after final commit.

- [ ] **Step 7: Write the verification report**

Record in `docs/reports/TASK8B_VERIFICATION.md`:

- exact commit and branch;
- Python version;
- every command above and its result count;
- V1.17/V1.18 core artifact hash comparisons;
- maintained double-build ZIP hashes;
- confirmation that `releases/V1.18/` and `data/baselines/V1.18/` are unchanged;
- compatibility objects retained;
- remaining limitation that CLI and consumer migration are not implemented.

- [ ] **Step 8: Update project state only after all gates pass**

Change `PROJECT_STATE.md` from “Task 8 has not started” to a factual Task 8B completion entry. Keep V1.18 as the current formal release, record that no formal data changed, link the verification report, and name the next separately approved task without starting it.

- [ ] **Step 9: Re-run documentation and status checks**

```bash
git diff --check
git diff -- releases/V1.18 data/baselines/V1.18
git status --short
```

Expected: no whitespace errors, no frozen-path diff, and only the report/state/equivalence test pending for the final commit.

- [ ] **Step 10: Commit Task 8B completion evidence**

```bash
git add tests/regression/test_task8b_pipeline_equivalence.py PROJECT_STATE.md docs/reports/TASK8B_VERIFICATION.md
git diff --cached --check
git commit -m "test: verify unified pipeline equivalence"
```

- [ ] **Step 11: Run one final clean-tree gate**

Repeat Step 5 after the commit, then run:

```bash
git status --porcelain=v1 --untracked-files=all
```

Expected: all gates still pass and status output is empty.

---

## Execution Stop Condition

This plan ends with a verified Task 8B branch. It does not authorize formal promotion, merging to `main`, pushing, opening a pull request, deleting legacy code, deleting compatibility views, implementing the CLI, or starting Task 8C. Report the final commit and verification evidence to Joy and wait for explicit direction.
