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
- `status` is `"PASS"` when no blocker exists and `"FAIL"` otherwise.

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
release implementation, CLI migration, file/image authenticity verification,
real SHA-256 recomputation, frozen-asset changes, warning/error severity
expansion, generic `extras`, automatic profile upgrade, or any later task's
code.

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
```

`candidate_path` and `baseline_database` are independent explicit inputs. No
library code may infer either from cwd, environment variables, repository
layout, profile, or the other path. `audit/pipeline.py` owns candidate JSON,
file, asset-root, and baseline SQLite preflight, including existence, exact
kind, and independently recomputed SHA-256. `audit/profiles.py` receives decoded
record values only and performs no filesystem, SQLite, or hashing access. The
candidate digest is recorded in audit/build evidence; the baseline digest must
match `ArtifactRef.sha256` before audit proceeds.

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
    batch: AuditedBatch,
    decision: V117ReleaseDecision,
) -> V117ReleaseBatch: ...
```

The decision is a deterministic historical V1.17 replay value, not a current
candidate approval and not the promotion-stage `ApprovalRecord`. The
transformer reads no clock, environment variable, approval manifest, or global
registry. It accepts only a V1.17 `AuditedBatch` obtained from
`AuditResult.require_passed()`, runs after audit PASS and before database, and
is forbidden on V1.18.

Each `V117ReleaseRecord` directly retains its matching `AuditedRecord` and
preserves order and one-to-one cardinality. `AuditedRecord` remains the only
audit-stage public envelope; its two compatibility carriers retain the Phase 1
legal combination and are never merged. Parallel lists, `question_id` joins,
position/file-order joins, and object-identity joins are forbidden. The
release-stage `ReleaseCompatibility.source_order` starts at 1 in stable order,
but implementation must prove the values through the protected legacy oracle
and byte-equivalence rather than relying on an unchecked positional assumption.

The future semantic report is:

```python
@dataclass(frozen=True)
class AuditReport:
    release_version: str
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

`AuditResult` will add exact field `report: AuditReport` after its existing
`status: str` field. The database request target will be:

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
creation, and database never constructs publication values.

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

1. `audit_result.status == "PASS"`;
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
| exact profile parsing and audit-stage record mapping | **Owns** | Invoke only | Forbidden | Forbidden | Invoke serializer only | Forbidden |
| duplicate seed and business audit | Forbidden | **Owns** | Forbidden | Forbidden | Forbidden | Invoke only |
| `AuditResult` / `AuditReport` semantics and statistics | Forbidden | **Owns** | Forbidden | Forbidden | Consume only | Forbidden |
| V1.17 historical publication decision and release-stage mapping | Forbidden | Forbidden | **Owns** | Consume only | Consume only | Invoke only |
| preserve V1.18 release compatibility | **Owns** | Carry only | Forbidden | Consume only | Consume only | Forbidden |
| create or rewrite database publication fields | Forbidden | Forbidden | **Owns for V1.17** | Forbidden | Forbidden | Forbidden |
| database copy, transaction, schema, integrity | Forbidden | Forbidden | Forbidden | **Owns** | Forbidden | Invoke only |
| audit evidence JSON encoding and file writing | Mapping only | Semantics only | Mapping only | Forbidden | **Owns** | Invoke/collect only |
| manifest, sums, ZIP, candidate verification | Forbidden | Forbidden | Forbidden | Forbidden | Artifact source only | **Owns** |

### 4. Complete successful and failed flows

V1.17 success:

```text
Task 4 50/52-field candidate JSON + protected V1.16 SQLite + asset root
→ audit preflight and exact V1.17 parser
→ baseline-seeded audit → AuditResult(AuditReport)
→ require_passed() → AuditedBatch
→ transform_v117_release(decision) → V117ReleaseBatch
→ database builds V1.17 without creating publication semantics
→ export consumes database + original audit_result + matching release batch
→ release collects artifacts, manifests, packages, and verifies candidate
```

V1.18 success:

```text
frozen 452×54-field candidate JSON + protected V1.17 SQLite + asset root
→ audit preflight and exact V1.18 parser
→ baseline-seeded audit → AuditResult(AuditReport)
→ require_passed() → AuditedBatch (no release transformer)
→ database copies 45 baseline records and appends 452 records
→ export consumes database + original audit_result + matching audited batch
→ release collects artifacts, manifests, packages, and verifies candidate
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
- profiles perform no filesystem or SQLite access;
- only a passed V1.17 batch enters the transformer, V1.18 is rejected, the
  decision is deterministic, every release record directly retains its audit
  envelope, and source order is oracle/byte-equivalent;
- database cannot manufacture or rewrite V1.17 publication fields;
- `AuditReport` counts are owned by audit and export does not recompute them;
- `DatabaseBuildRequest`, `ExportRequest`, `ExportContract`,
  `DerivedArtifacts`, and the reduced `ReleaseContract` have the exact frozen
  field order and types;
- `ExportRequest` rejects count, order, value, profile, or direct-envelope
  mismatch before writing;
- failed audit evidence uses deterministic caller-provided location and cannot
  create database/candidate/promotion artifacts;
- maintained candidate loading never calls the legacy SQLite extractor, while
  legacy remains available only inside tests as an oracle.

### 6. Minimal implementation files and commit order

The contract revision itself changes only the two Task 8A authority documents.
After separate authorizations, the minimum expected implementation surface is:

- `src/joy_m2/models.py` and `tests/unit/test_pipeline_models.py` for the Phase 2
  request/report/release/export values;
- `src/joy_m2/audit/profiles.py`, `src/joy_m2/audit/pipeline.py`, and focused
  audit tests for JSON-backed profiles and explicit baseline preflight;
- `src/joy_m2/release/transformers.py` and a focused V1.17 transformer test;
- `src/joy_m2/db/pipeline.py` and integration tests for typed batch consumption;
- `src/joy_m2/export/formats.py`, `src/joy_m2/export/pipeline.py`, and integration
  tests for typed audit evidence;
- `src/joy_m2/release/pipeline.py` and end-to-end tests only after lower stages
  pass independently.

Recommended implementation commit order is: Phase 2 public contracts/tests;
JSON-backed audit; V1.17 transformer; database consumption; typed audit export;
release orchestration and end-to-end equivalence. Each commit requires its own
explicit authorization and review gate.

---

### Task 3: Implement Aggregating Task 5/6 Audit Profiles

**Files:**
- Create: `src/joy_m2/audit/profiles.py`
- Create: `src/joy_m2/audit/pipeline.py`
- Modify: `src/joy_m2/audit/__init__.py`
- Create: `tests/unit/test_audit_pipeline.py`

**Interfaces:**
- Consumes: `AuditRequest`, `AuditContract`, `AuditedRecord`,
  `Task4Compatibility`, `ReleaseCompatibility`, `AuditResult`, `AuditedBatch`,
  and input exceptions from Task 2.
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
self.assertEqual(result.answer_status_counts, {"source_provided": 347, "ai_solved_verified": 71, "missing_from_source": 34})
self.assertEqual(result.require_passed().records, result.records)
```

Run:

```bash
$task8_python -m unittest -v tests.unit.test_audit_pipeline.Task6AuditContractTests
```

Expected: FAIL because `audit_batch` is not implemented.

- [ ] **Step 2: Implement fatal input validation and explicit candidate loading**

Before producing records, independently require the candidate JSON, baseline
database, and asset root to exist with the correct kinds; compute the candidate
SHA-256 for evidence, verify the V1.17 baseline against its `ArtifactRef`, decode
the exact 452-record JSON container, and open baseline SQLite read-only only to
seed duplicate references and validate the protected baseline. Map missing
files to `InputMissingError`, invalid SQLite/JSON to `InputFormatError`, and
baseline hash mismatch to `BaselineMismatchError`. The Task 6 SQLite join and
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

- [ ] **Step 5: Add failure aggregation tests**

Create temporary candidate JSON values with two exact duplicates, a missing
image reference, an invalid tag, and an empty non-missing answer; keep the
protected baseline read-only. Assert all relevant issue codes are present in one
result and `require_passed()` raises `AuditBlockedError` without any output
database.

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
- Create: `src/joy_m2/release/transformers.py`
- Modify: `src/joy_m2/release/__init__.py`
- Create: `tests/unit/test_v117_release_transformer.py`

**Interfaces:**
- Consumes: a V1.17 `AuditedBatch` returned by `require_passed()` and an explicit
  `V117ReleaseDecision`.
- Produces: `transform_v117_release(...) -> V117ReleaseBatch` with direct,
  ordered audit-envelope retention.

- [ ] **Step 1: Write failing contract and boundary tests**

Assert exact decision/record/batch field types, rejection of a failed or V1.18
batch, no clock/environment/registry/`ApprovalRecord` dependency, and one direct
`AuditedRecord` child per output record. Assert neither compatibility carrier on
the retained `AuditedRecord` is changed.

- [ ] **Step 2: Implement the minimal deterministic transformer**

Apply only the seven protected V1.17 historical operations frozen above. Create
release-stage `PublicationEvidence`, `ReleaseCompatibility`, and schema value on
the direct wrapper. Preserve input order and cardinality. Do not serialize JSON
or access files/databases.

- [ ] **Step 3: Prove source-order and record equivalence**

Compare all 45 transformed records against the protected legacy oracle,
including 1-based `source_order`, 53/55-field mapping, Task 4 key presence,
publication values, and final byte-equivalence after the approved serializer.
Position alone is not accepted as proof; the oracle comparison is required.

- [ ] **Step 4: Commit the transformer separately**

```bash
git add src/joy_m2/release/transformers.py src/joy_m2/release/__init__.py tests/unit/test_v117_release_transformer.py
git diff --cached --check
git commit -m "feat: add V1.17 release transformer"
```

---

### Task 4: Implement Transactional V1.17 and V1.18 Database Builds

**Files:**
- Create: `src/joy_m2/db/profiles.py`
- Create: `src/joy_m2/db/pipeline.py`
- Modify: `src/joy_m2/db/__init__.py`
- Create: `tests/integration/test_db_pipeline.py`

**Interfaces:**
- Consumes: V1.18 `AuditedBatch` or V1.17 `V117ReleaseBatch`, `ReleaseSpec`,
  `DatabaseContract`, and `DatabaseBuildRequest`.
- Produces: `build_database(request) -> DatabaseArtifact` and `verify_database(path, contract) -> VerificationReport`.

- [ ] **Step 1: Write the failing V1.18 byte-equivalence test**

Audit the 452 candidates with Task 3, build to a new temporary path, and assert:

```python
self.assertEqual(sha256(output_db), "fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7")
self.assertEqual(output_db.read_bytes(), (ROOT / "releases/V1.18/Joy_M2_Complete_Question_DB_V1_18.sqlite3").read_bytes())
```

Also assert `user_version=118`, integrity `ok`, foreign-key errors 0, 497 total rows, 452 rows with `source_order>45`, and 45 byte/logically unchanged V1.17 rows.

Run and expect an import failure:

```bash
$task8_python -m unittest -v tests.integration.test_db_pipeline.V118DatabaseBuildTests
```

- [ ] **Step 2: Implement protected baseline validation**

Validate the source path, V1.17 hash, manifest binding, integrity, foreign keys, 45 V2 rows, and 497 compatibility-view rows before creating the output parent or file. Map each failure to the specified input/database exception.

- [ ] **Step 3: Implement the V1.18 transaction**

Copy the baseline to a temporary database in the target parent, set `foreign_keys=ON` and `journal_mode=DELETE`, begin one immediate transaction, insert all typed rows and tags in stable order, rebuild taxonomy from ordered distinct values, update metadata/import run, set `user_version=118`, commit, check integrity/foreign keys, and run `VACUUM` exactly where the legacy profile requires it.

Use the exact `DB_TABLE_COLUMNS` order from the oracle as a named constant in `profiles.py`; every JSON-valued cell uses the approved canonical JSON serializer.

- [ ] **Step 4: Make publication of the database atomic**

Run final read-only verification against the temporary file. Only after PASS, use `Path.replace(output_path)` when `output_path` does not exist. On any exception, remove only the known temporary file and leave `output_path` absent.

- [ ] **Step 5: Add duplicate, foreign-key, integrity, and conflict tests**

Inject a duplicate ID, an unknown `source_id`, a malformed baseline, and an existing output path. Assert `AuditBlockedError`, `ForeignKeyViolationError`, `DatabaseIntegrityError` or `BaselineMismatchError`, and `OutputConflictError` as applicable. After each failure assert the original target bytes are absent or unchanged.

- [ ] **Step 6: Add V1.17 build support and equivalence**

Implement the schema-creation profile from Task 5, accepting only the
`V117ReleaseBatch` produced by Task 3A and copying its already-decided
publication values without creating or rewriting them. Include V2 tables,
constraints, indexes, metadata, taxonomy, import run, selectable view,
`user_version=117`, and `VACUUM`. Assert the temporary output database bytes
equal the protected V1.17 database and the V1.16 historical tables are logically
unchanged. Assert an audit-stage `AuditedBatch` is rejected for V1.17 before
output creation.

- [ ] **Step 7: Run database and audit suites**

```bash
$task8_python -m unittest -v tests.integration.test_db_pipeline tests.unit.test_audit_pipeline
```

Expected: PASS.

- [ ] **Step 8: Commit database migration**

```bash
git add src/joy_m2/db tests/integration/test_db_pipeline.py
git diff --cached --check
git commit -m "feat: add transactional database pipeline"
```

---

### Task 5: Implement Deterministic Database and Audit-Evidence Exports

**Files:**
- Create: `src/joy_m2/export/formats.py`
- Create: `src/joy_m2/export/pipeline.py`
- Modify: `src/joy_m2/export/__init__.py`
- Create: `tests/integration/test_export_pipeline.py`

**Interfaces:**
- Consumes: `DatabaseArtifact`, the original `AuditResult`, its directly
  corresponding `AuditedBatch | V117ReleaseBatch`, `ExportContract`, and a
  current staging output directory.
- Produces: `export_database(request) -> DerivedArtifacts` and `verify_exports(request) -> VerificationReport`.

- [ ] **Step 1: Write failing serializer tests**

Assert canonical JSON bytes, evidence JSON bytes, CSV BOM/CRLF, LF-only text, and exactly one trailing newline:

```python
self.assertEqual(canonical_json_bytes({"中": [2, 1]}), b'{"\xe4\xb8\xad":[2,1]}')
self.assertEqual(evidence_json_bytes({"b": 1, "a": "中"}), '{\n  "a": "中",\n  "b": 1\n}\n'.encode())
```

Run:

```bash
$task8_python -m unittest -v tests.integration.test_export_pipeline.FormatContractTests
```

Expected: FAIL because `formats.py` does not exist.

- [ ] **Step 2: Implement exact format primitives**

Use `json.dumps(ensure_ascii=False, sort_keys=True, separators=(",", ":"))` for canonical JSON and `indent=2` plus one LF for evidence JSON. Open CSV with `encoding="utf-8-sig", newline=""` and set `lineterminator="\r\n"`. Normalize generated Markdown/report/state text to LF before writing and append exactly one final LF.

- [ ] **Step 3: Write failing V1.18 export equivalence tests**

Build a temporary V1.18 database through Task 4, retain the exact Task 3
`AuditResult` and `AuditedBatch`, and export all V1.18 profile files. Compare
CSV, knowledge Markdown, audit JSON, audit report, import report, and
project-state bytes to their `releases/V1.18/` counterparts. Assert CSV rows
equal every SQLite cell after NULL-to-empty conversion, Markdown contains 497
unique headings plus 34 missing-source markers, and the audit report bytes encode
the existing `AuditReport` without exporter-side recounting.

- [ ] **Step 4: Implement `export_database`**

Before opening an output, enforce the frozen count/order/direct-envelope
relationship between `audit_result` and `record_batch`. Read only the supplied
`DatabaseArtifact` for CSV/Markdown and database-derived summaries; never reopen
source JSON. Query CSV by `question_id`, Markdown by `source_order`, and database
summaries with explicit `ORDER BY`. Serialize records from the supplied matching
batch and serialize the supplied `AuditReport` without re-auditing or
recounting. Refuse any mismatch, target outside the current staging run, or
existing output file before partial writes.

- [ ] **Step 5: Implement `verify_exports`**

Return individual checks for expected file set, CSV BOM, CSV column/value
equality, row count, Markdown unique headings, missing-answer markers, audit JSON
parseability, batch/report count and order agreement, and deterministic
re-export hashes. Return FAIL for artifact mismatches and raise only when the
verification cannot execute.

- [ ] **Step 6: Add V1.17 export profile tests**

Pass the exact original V1.17 `AuditResult` and Task 3A `V117ReleaseBatch`.
Assert V1.17 CSV, knowledge Markdown, report, project state, approved JSON, and
taxonomy JSON bytes equal the protected legacy Task 5 release artifacts, and
that a reordered, truncated, or unrelated release batch is rejected before
writing.

- [ ] **Step 7: Run export, database, and legacy tests**

```bash
$task8_python -m unittest -v tests.integration.test_export_pipeline tests.integration.test_db_pipeline
(cd legacy/task5_work && $task8_python -m unittest -v test_task5_import.py)
```

Expected: PASS.

- [ ] **Step 8: Commit deterministic exporters**

```bash
git add src/joy_m2/export tests/integration/test_export_pipeline.py
git diff --cached --check
git commit -m "feat: add deterministic SQLite exports"
```

---

### Task 6: Implement Hashing, Verification, and Deterministic Packaging

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

- [ ] **Step 2: Implement hashing and manifest primitives**

Expose:

```python
sha256_bytes(value: bytes) -> str
sha256_file(path: Path) -> str
write_manifest(path: Path, payload: Mapping[str, object]) -> ArtifactRef
write_sha256sums(path: Path, protected: tuple[ArtifactRef, ...]) -> ArtifactRef
```

Sort by POSIX relative path. Reject duplicate paths, absolute archive paths, `..`, and attempts to include the sums file or ZIP in the protected set.

- [ ] **Step 3: Write failing deterministic ZIP tests**

Build the same payload twice and assert identical bytes. Inspect every `ZipInfo` for fixed timestamp, `create_system=3`, regular-file `0644`, DEFLATE, sorted names, no directory entries, and the contract root.

- [ ] **Step 4: Implement deterministic ZIP creation**

Use `ZipInfo(name, date_time=(1980, 1, 1, 0, 0, 0))`, `external_attr=0o100644 << 16`, `create_system=3`, `ZIP_DEFLATED`, and `compresslevel=9`. Read every source as bytes, iterate by sorted archive name, and reject undeclared or missing inputs before opening the output ZIP.

- [ ] **Step 5: Write failing structured verification tests**

Start with a valid temporary release, then separately corrupt a protected byte, remove a sums entry, add an undeclared file, alter CSV, remove a Markdown heading, and break the audit report. Assert each fully executable case returns `VerificationReport(status="FAIL")` with its own failed check. Assert missing manifest or malformed JSON raises the appropriate input exception.

- [ ] **Step 6: Implement candidate and release verification**

Combine independent checks for manifest artifacts, sums file-set closure, file hashes, SQLite integrity/foreign keys/counts, CSV exact mirror, Markdown coverage, audit count/status, baseline hash, package metadata, and extracted-package self-verification. Do not call builder functions from verifier code.

- [ ] **Step 7: Run release primitive tests**

```bash
$task8_python -m unittest -v tests.unit.test_release_primitives
```

Expected: PASS.

- [ ] **Step 8: Commit release primitives**

```bash
git add src/joy_m2/release tests/unit/test_release_primitives.py
git diff --cached --check
git commit -m "feat: add deterministic release primitives"
```

---

### Task 7: Implement Atomic Candidate Builds and Approval-Bound Promotion

**Files:**
- Create: `src/joy_m2/release/pipeline.py`
- Modify: `src/joy_m2/release/__init__.py`
- Create: `tests/integration/test_release_pipeline.py`

**Interfaces:**
- Consumes: `CandidateBuildRequest`, low-level audit/db/export/release APIs, `ApprovalRecord`, `PipelineConfig`.
- Produces: `build_candidate(request) -> CandidateRelease` and `promote_candidate(candidate, approval, config) -> FormalRelease`.

- [ ] **Step 1: Write failing atomic candidate tests**

In a temporary repository-shaped root, assert a successful build appears only at `data/staging/<run_id>/` after all checks pass. Inject an export failure and assert the valid run directory never appears; diagnostics may exist only under `.failed/<run_id>/` with a non-formal status.

Run:

```bash
$task8_python -m unittest -v tests.integration.test_release_pipeline.CandidateBuildTests
```

Expected: FAIL because `build_candidate` is absent.

- [ ] **Step 2: Implement `build_candidate` orchestration**

Preflight every input and output conflict before creating the hidden temporary
run. Call `audit_batch()` and retain its `AuditResult`; require a passed batch;
for V1.17 only call `transform_v117_release()` with the explicit historical
decision, while V1.18 passes the `AuditedBatch` unchanged. Pass that batch to
`build_database()`, then pass the database artifact, original audit result, and
same matching batch to `export_database()`. Collect its audit evidence
artifacts, write manifest/sums, build the ZIP, and call `verify_candidate()`.
Release must not encode audit JSON or recompute report statistics. If candidate
status is not `PASS`, raise `PipelineError` with the failed check names;
otherwise atomically rename the hidden run to `<run_id>`.

Catch `PipelineError` only to write deterministic failure metadata and relocate
the known temporary run under `.failed/<request.run_id>`; re-raise the original
typed exception. A failed audit may persist its existing `AuditResult` and
`AuditReport` as diagnostics, but must not call transformer/database or produce
normal candidate artifacts.

- [ ] **Step 3: Add output conflict and stale candidate tests**

Assert existing run, ZIP, formal target, or declared artifact produces `OutputConflictError` without changing existing bytes. Mutate a candidate after its verification and assert both `verify_candidate` and promotion reject it.

- [ ] **Step 4: Write failing approval tests**

Cover wrong version, wrong candidate manifest hash, wrong approver, empty scope, invalid approval timestamp, failed candidate verification, and real V1.18 target protection. Every case must leave the temporary `releases/` tree unchanged.

- [ ] **Step 5: Implement `promote_candidate`**

Require a fresh candidate PASS; validate approval version, exact candidate manifest hash, `approved_by == "Joy"`, a timezone-aware ISO timestamp, and non-empty scope. Build a formal temporary directory inside `releases/`, add approval evidence, record both candidate-manifest and approval-evidence hashes in the formal manifest, regenerate sums and ZIP, independently verify, then atomically rename to the non-existing target.

Never delete or replace an existing release. Clean up only the known unexposed promotion temporary directory on failure.

- [ ] **Step 6: Add a successful promotion test in a temporary repository**

Promote a small synthetic PASS candidate into a temporary `releases/V9.99/`. Assert the final directory appeared atomically, contains approval evidence and formal manifest binding, verifies PASS, and rejects a second promotion with `OutputConflictError`. Do not exercise promotion against the real workspace.

- [ ] **Step 7: Run release integration and primitive tests**

```bash
$task8_python -m unittest -v tests.integration.test_release_pipeline tests.unit.test_release_primitives
```

Expected: PASS.

- [ ] **Step 8: Commit safe orchestration**

```bash
git add src/joy_m2/release tests/integration/test_release_pipeline.py
git diff --cached --check
git commit -m "feat: add safe release orchestration"
```

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
