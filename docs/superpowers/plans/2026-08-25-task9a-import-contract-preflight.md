# Task 9A Import Contract and Read-Only Preflight Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a typed import manifest and deterministic read-only preflight boundary for one canonical JSON complete-question batch without modifying SQLite or release artifacts.

**Architecture:** A new `joy_m2.ingest` package owns import-package contracts, manifest decoding, inventory/digest checks, compact baseline identity lookup, and preflight reporting. It reads frozen V1.18 with SQLite `mode=ro` and neither calls nor duplicates database/export/release writers.

**Tech Stack:** Python 3.12 standard library (`dataclasses`, `pathlib`, `json`, `hashlib`, `sqlite3`, `unittest`).

**Spec:** `docs/superpowers/specs/2026-08-25-task9-batch-import-design.md`

## Global Constraints

- Implementation requires explicit authorization after independent review.
- Exact scope is the six files listed below; no other file is authorized.
- V1.18 remains 497 complete questions and is opened read-only.
- `target_release_version` is exactly `V1.19`; this is identity validation only.
- One complete question remains one record; subparts are never split.
- Canonical UTF-8 JSON is the only parsed question input in Task 9A.
- MMD, MMD.ZIP, and PDF are unsupported blockers.
- Teacher/common-error files are evidence only; no schema projection is allowed.
- Typed evidence, reports, issues, and `preflight_sha256` use canonical package-
  relative paths only; absolute roots, cwd, and temporary paths are forbidden.
- `package_root` is an explicit transient runtime `Path` passed separately to
  manifest loading and preflight; it is never retained in a carrier, report,
  digest, or approval identity, and no implicit root discovery is permitted.
- Candidate semantic order is manifest-declared `candidate_records` order,
  followed by record-array order inside each canonical JSON file.
- Translation/explanation provenance is approval-relevant and distinguishes
  `source_present`, `ai_proposed`, `verified`, and `missing`.
- Do not add dependencies, CLI, `__main__.py`, project scripts, pipeline modules,
  staging writes, formal writes, or release behavior.
- Task 3 remains blocked until the TDD scaffold sequencing remediation passes
  independent review and implementation is explicitly resumed. V1.19
  serialization/profile, writer, formal release, and promotion authority remain
  deferred to Task 9C.

---

## Files and responsibilities

- Create `src/joy_m2/ingest/models.py`: immutable manifest/evidence/issue/report/result carriers.
- Create `src/joy_m2/ingest/manifest.py`: exact JSON parsing and package identity checks.
- Create `src/joy_m2/ingest/preflight.py`: read-only baseline index, candidate checks, and report closure.
- Create `src/joy_m2/ingest/__init__.py`: exact public exports.
- Create `tests/unit/test_ingest_models.py`: shapes, validation, immutability, manifest negatives.
- Create `tests/integration/test_ingest_preflight.py`: baseline, duplicate, report, and zero-mutation controls.

Public APIs:

```python
def load_import_manifest(path: Path, package_root: Path) -> BatchImportManifest

def preflight_import(
    manifest: BatchImportManifest,
    package_root: Path,
    baseline_database: ArtifactRef,
) -> ImportPreflightResult
```

The parameter order and `Path` annotation are exact. Runtime validation uses
the existing repository convention `isinstance(package_root, Path)`, accepting
the platform concrete `PosixPath`/`WindowsPath`; strings and all non-Path values
are rejected without conversion. It must exist, be a directory, and resolve
safely. No additional runtime authority parameter is allowed.

Caller flow is explicit:

```text
package_root
→ load_import_manifest(manifest_path, package_root)
→ manifest
→ preflight_import(manifest, package_root, baseline_database)
```

The root is only a locator for path-aware containment, existence/readability
checks, and reading/hashing manifest-declared candidate/source/image bytes.
Neither API may infer it from cwd, repository layout, manifest parent,
environment variables, global registries, or hidden maps. It never becomes a
field of any of the six public carriers and is excluded from canonical report,
digest, and approval projections.

Exact `joy_m2.ingest.__all__`:

```python
(
    "BatchImportManifest",
    "ImportCandidate",
    "ImportFileEvidence",
    "ImportIssue",
    "ImportPreflightReport",
    "ImportPreflightResult",
    "load_import_manifest",
    "preflight_import",
)
```

## Task 1: Immutable carriers

**Files:**
- Create: `tests/unit/test_ingest_models.py`
- Create: `src/joy_m2/ingest/models.py`

**Interfaces:** Produces the six typed carriers consumed by manifest/preflight.

- [ ] **Step 1: Write exact-shape RED tests**

Lock exact fields, order, and runtime types:

```python
@dataclass(frozen=True)
class ImportFileEvidence:
    relative_path: str
    sha256: str
    size_bytes: int
    kind: str

@dataclass(frozen=True)
class BatchImportManifest:
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

@dataclass(frozen=True)
class ImportCandidate:
    proposed_question_id: str
    source_id: str
    source_question_number: str
    source_section: str
    source_fragment_hash: str
    normalized_text_sha256: str
    question_text_original: str
    question_text_zh: str
    translation_status: str
    translation_evidence: str | None
    solution_original: str
    solution_verified: str
    answer_status: str
    explanation_text: str
    explanation_status: str
    explanation_evidence: str | None
    image_paths: tuple[str, ...]
    image_sha256s: tuple[str, ...]
    image_roles: tuple[str, ...]
    primary_type: str
    tags: tuple[str, ...]
    tag_status: str
    difficulty_level: int | None
    difficulty_status: str
    enrichment_status: str

@dataclass(frozen=True)
class ImportIssue:
    code: str
    severity: str
    proposed_question_id: str | None
    field: str
    evidence: str

@dataclass(frozen=True)
class ImportPreflightReport:
    batch_id: str
    status: str
    preflight_sha256: str
    manifest_sha256: str
    baseline_version: str
    before_count: int
    target_release_version: str
    detected_count: int
    new_candidate_count: int
    duplicate_count: int
    rejected_count: int
    ambiguous_count: int
    approved_count: int
    projected_after_count: int
    readable_files: tuple[str, ...]
    unreadable_files: tuple[str, ...]
    unsupported_files: tuple[str, ...]
    teacher_notes_file_count: int
    common_errors_file_count: int
    ambiguous_splits: tuple[str, ...]
    missing_answers: tuple[str, ...]
    missing_explanations: tuple[str, ...]
    incomplete_enrichments: tuple[str, ...]
    missing_images: tuple[str, ...]
    orphan_images: tuple[str, ...]
    level_counts: tuple[tuple[int, int], ...]
    proposed_ids: tuple[str, ...]
    warnings: tuple[str, ...]
    blocking_errors: tuple[str, ...]

@dataclass(frozen=True)
class ImportPreflightResult:
    manifest: BatchImportManifest
    baseline_database: ArtifactRef
    candidates: tuple[ImportCandidate, ...]
    issues: tuple[ImportIssue, ...]
    report: ImportPreflightReport
```

`ImportPreflightResult.baseline_database` is the sole typed baseline ArtifactRef.
The report's baseline version/count, manifest target, and the digest-only
baseline logical identity are one-way deterministic projections, not parallel
evidence carriers. No projection contains `baseline_database.path`, and no
projection may reconstruct an `ArtifactRef`.

Test frozen assignment rejection, tuple copying/no alias, exact runtime types,
lowercase SHA-256, non-negative counts, deterministic issues, and arithmetic:

```python
detected_count == new_candidate_count + duplicate_count + rejected_count
projected_after_count == before_count + new_candidate_count
approved_count == 0
ambiguous_count <= rejected_count
```

`new_candidate_count` means candidates eligible for user approval after
duplicate/rejection classification. `projected_after_count` is the count if the
unchanged eligible set is later approved; Task 9A performs no approval or write.

`target_release_version` has exact runtime type `str` and value `"V1.19"`;
independently reject `None`, V1.18, V1.20, and arbitrary strings. Test
`candidates` as an exact tuple of `ImportCandidate`, including defensive copies
of image paths/digests/roles and tags. Each image path, digest, and role tuple
must have equal length and positional binding. Freeze status vocabularies:

```text
answer_status: source_provided | ai_solved_verified | missing_from_source
translation_status: source_present | ai_proposed | verified | missing
explanation_status: source_present | ai_proposed | verified | missing
tag_status: source_provided | proposed | missing
difficulty_status: source_provided | proposed | missing
enrichment_status: complete | incomplete
```

Freeze exact payload/provenance consistency:

- `translation_status=missing` requires empty `question_text_zh` and
  `translation_evidence=None`; every other translation status requires a
  non-empty `question_text_zh` and non-empty stable evidence.
- `explanation_status=missing` requires empty `explanation_text` and
  `explanation_evidence=None`; every other explanation status requires a
  non-empty `explanation_text` and non-empty stable evidence.
- `source_present` evidence must identify matching input source;
  `ai_proposed` evidence must be a content-bound proposal identifier; and
  `verified` evidence must identify the approved independent review.

Evidence strings use exactly one of:

```text
source:<canonical-relative-path>#<non-empty-stable-locator>
ai-proposal-sha256:<lowercase-64-hex-of-UTF-8-payload>
verified-review-sha256:<lowercase-64-hex-of-approved-review-evidence>
```

Require a `source:` reference to resolve to declared input evidence and require
the proposal digest to match its payload. Reject absolute paths and runtime
session/conversation identifiers. The verified digest carries an already
approved review identity; Task 9A does not create that review.
`source_present` is valid only with matching input source evidence. AI output
initially has only `ai_proposed` authority; Task 9A performs no AI generation or
verification and may only carry `verified` with independently approved review
evidence. `missing_from_source` requires both solution fields empty and does
not silently authenticate an explanation. The answer solution fields and
`explanation_text` are independent payloads and cannot infer one another's
provenance. Missing translation/explanation and incomplete enrichment are
reported, not filled.

- [ ] **Step 2: Prove model RED**

Run:

```bash
python -m unittest -v tests.unit.test_ingest_models
```

Expected: failure only because `joy_m2.ingest.models` is absent. Syntax/setup
errors are invalid RED.

- [ ] **Step 3: Implement minimum carriers**

Use frozen dataclasses, `type(...) is ...`, defensive tuple copies, and Python
stable sorting. Add no defaults, aliases, file I/O, or database behavior.

- [ ] **Step 4: Run model GREEN**

Require every collected test PASS, skip=0, expectedFailure=0.

## Task 2: Typed manifest and inventory

**Files:**
- Modify: `tests/unit/test_ingest_models.py`
- Create: `src/joy_m2/ingest/manifest.py`

**Interfaces:** Produces `load_import_manifest()`.

- [ ] **Step 1: Add manifest RED tests**

Using `TemporaryDirectory`, test exact top-level fields/order and policy values,
UTF-8 object input, relative POSIX paths, and declared file identity. Add
independent negatives for absolute path, `..`, symlink escape, duplicate path,
missing/directory/unreadable file, wrong exact type/kind, SHA mismatch, size
mismatch, undeclared package file, malformed JSON, wrong top level, and a
candidate-record kind other than `candidate_json`. Lock
`target_release_version` to exact
`"V1.19"`; reject null and every other version. Prove teacher-note and
common-error entries retain their exact path/hash/size/kind evidence and are
reported without schema projection or silent discard.

Use exact group kinds: `candidate_json`, `source`, `answer`, `image`,
`teacher_notes`, and `common_errors`. Reject a valid kind placed in the wrong
group as well as an unknown kind.

Lock `ImportFileEvidence.relative_path` to normalized canonical package-
relative POSIX spelling before construction. The loader may resolve a private
filesystem path for containment/readability checks, but typed evidence and
report values may never retain the absolute package root, cwd, or temporary
root. Preserve `candidate_records` tuple order exactly as declared; file
inventory/evidence serialization later uses the independent canonical order
`relative_path`.

- [ ] **Step 2: Validate manifest RED**

Run the unit module. Existing model tests stay GREEN; new failures must be
missing manifest behavior.

- [ ] **Step 3: Implement minimum loader**

Decode standard JSON, enforce exact order/values, prove containment, stream
SHA-256, compare size, and construct immutable evidence. Do not discover cwd or
repo paths and do not write normalized output. The loader may read declared
bytes for its existing inventory identity checks, but it does not parse
candidate records, construct `ImportCandidate`, or retain `package_root`.

- [ ] **Step 4: Run focused GREEN**

Require the unit module PASS.

## Task 3: Baseline and candidate identity

**Files:**
- Create: `tests/integration/test_ingest_preflight.py`
- Create: `src/joy_m2/ingest/preflight.py`

**Interfaces:** Produces `preflight_import()` and compact private indexes.

- [ ] **Step 3.1: Write the API-existence and exact-signature test**

Before `src/joy_m2/ingest/preflight.py` exists, add a focused test that requires
the exact function name, parameter names/order/annotations, return annotation,
and no extra runtime authority parameter:

```python
def preflight_import(
    manifest: BatchImportManifest,
    package_root: Path,
    baseline_database: ArtifactRef,
) -> ImportPreflightResult
```

This is the only RED group for which module missing, symbol missing, or exact
signature unavailable is valid. It is an API-existence RED, not a behavior RED.

- [ ] **Step 3.2: Run and record the API RED**

Run the focused integration test. Require failure specifically because the
approved API/signature does not yet exist. Syntax, fixture, and unrelated setup
errors remain invalid.

- [ ] **Step 3.3: Create the minimal importable scaffold**

Only after the API RED is recorded, create
`src/joy_m2/ingest/preflight.py` with exactly the required imports, approved
signature, and immediate scaffold exception:

```python
from pathlib import Path

from joy_m2.models import ArtifactRef

from .models import BatchImportManifest, ImportPreflightResult


def preflight_import(
    manifest: BatchImportManifest,
    package_root: Path,
    baseline_database: ArtifactRef,
) -> ImportPreflightResult:
    raise NotImplementedError
```

The scaffold must not validate a root, resolve/read/hash a file, parse a
candidate, construct evidence/issues/report, or compute a digest.

- [ ] **Step 3.4: Run the import/signature test GREEN**

Require successful module/symbol import and exact signature equality. Task 3
remains RED; scaffold importability is test infrastructure, not behavior GREEN.

- [ ] **Step 3.5: Add root type and validity behavior RED tests**

With the scaffold importable, add independent calls for a non-Path runtime
value, nonexistent root, and root that is a file. Each test must reach
`preflight_import()` and fail with scaffold `NotImplementedError`, proving the
approved typed failure behavior is not yet implemented. No cwd/default fallback
is permitted.

- [ ] **Step 3.6: Run and record root-validation RED**

Require successful import, exact-signature GREEN, valid fixtures, an actual
function call, and behavior RED only from scaffold/missing root validation.

- [ ] **Step 3.7: Add containment and symlink behavior RED tests**

Add independent calls for an absolute declared child path, `..`, normalization
escape, and an in-root symlink resolving outside the root. Require path-aware
resolved containment; a string-prefix check is explicitly insufficient.

- [ ] **Step 3.8: Run and record containment RED**

Require every case to import and reach the scaffold. Module/symbol/import,
syntax, fixture, setup, or environment errors are invalid behavior REDs.

- [ ] **Step 3.9: Add root-contamination and cross-root behavior RED tests**

Add a targeted test proving the absolute root never occurs in typed evidence,
issue evidence, report serialization, canonical digest payload, or approval
identity. Separately copy one equivalent package beneath two distinct absolute
roots and require identical file evidence, candidate tuple, issue tuple, report
authority, and `preflight_sha256`.

- [ ] **Step 3.10: Run and record authority behavior REDs**

Require both groups to import and call the scaffold successfully, then fail with
`NotImplementedError` or their specific missing behavior. Cross-root equality
does not replace the targeted root-string contamination assertion.

- [ ] **Step 3.11: Add baseline/zero-mutation behavior RED tests**

Snapshot V1.18 SQLite, `releases/`, `data/`, `legacy/`, and existing formal image
assets before/after. Assert exact SQLite `ArtifactRef`,
`mode=ro`, baseline version V1.18, count 497, target V1.19, integrity `ok`, zero
FK errors, V1.18 metadata, compact ID/source-locator/fragment/text/image/
source-order indexes, and no created, deleted, or modified file.

- [ ] **Step 3.12: Add candidate identity behavior RED tests**

Canonical records decode into exact `ImportCandidate` values from these input
identity/content keys:

```text
proposed_question_id, source_id, source_question_number, source_section,
source_fragment_hash, question_text_original, answer_status,
solution_original, solution_verified, image_paths, primary_type, tags,
difficulty_level, question_text_zh, translation_status, translation_evidence,
explanation_text, explanation_status, explanation_evidence, image_roles,
tag_status, difficulty_status, enrichment_status
```

Test non-object/malformed records, duplicate proposed ID, missing identity,
wrong exact types, empty original, non-null Level outside 1–5, invalid status,
inconsistent missing/proposed tag or difficulty status, non-empty
solution fields for `missing_from_source`, every invalid translation/explanation
payload-status-evidence combination, false source authentication of AI
proposals, missing explanation disclosure, and incomplete enrichment
disclosure. Add independent source-provided, AI-proposed, verified, and missing
fixtures for both translation and explanation. Task 9A fixtures carry stable
proposal/review evidence; production never invokes AI or performs verification.
Verify derived normalized-text and image digests are deterministic and cannot
be supplied as caller authority.

Candidate order is exactly manifest `candidate_records` order followed by
record-array order within each file. A manifest order `[q3, q1, q2]` produces
that exact candidate tuple; do not sort by path, proposed ID, hash, filesystem
traversal, or dictionary insertion effects. Independently shuffle the private
filesystem discovery order while holding the manifest fixed and require the
same candidate tuple. Explicitly reorder the manifest and require the candidate
tuple to reflect that semantic change.

- [ ] **Step 3.13: Verify the complete behavior RED gate**

```bash
python -m unittest -v tests.integration.test_ingest_preflight
```

Require successful imports, exact-signature GREEN, valid fixtures, and actual
calls reaching the scaffold. Root type/validity, containment/symlink,
contamination/cross-root, baseline/zero-mutation, and candidate-identity groups
must all be RED because their production behavior is absent. Only now may
production behavior replace the scaffold.

- [ ] **Step 3.14: Implement minimum behavior group by group**

Validate the explicit root again at the consumption boundary. Resolve every
manifest relative path against that root with path-aware containment; reread
and hash the bytes consumed by preflight; read only required baseline columns.
Parse candidates without retaining the root or constructing publication
evidence, `AuditedRecord`, database rows, or output files.

Implement one approved behavior group at a time using
`RED → minimum behavior GREEN → focused tests → next RED group`; do not replace
the scaffold with the complete preflight in one pass. `NotImplementedError` is
valid only at the scaffold checkpoint and must disappear from final Task 3
runtime behavior and regression expectations.

- [ ] **Step 3.15: Run focused GREEN**

Require integration and model modules PASS.

## Task 4: Duplicate/content/image controls

**Files:**
- Modify: `tests/integration/test_ingest_preflight.py`
- Modify: `src/joy_m2/ingest/preflight.py`

- [ ] **Step 1: Add independent negative controls**

One test per baseline/batch ID collision, fragment collision, normalized-text
collision, conflicting source locator, missing image, image path/digest conflict,
orphan image, unknown primary type/tag, unsupported MMD/MMD.ZIP/PDF, and
malformed item.
Test `missing_from_source` succeeds only with empty solutions. Test adaptations
require stable reference/evidence and remain warnings, not exact-duplicate
bypasses.

- [ ] **Step 2: Prove behavior RED**

Run integration tests. Each new test must fail for its missing production check.

- [ ] **Step 3: Implement deterministic issue collection**

Collect every per-record issue and stable-sort by exactly:

```python
(issue.proposed_question_id, issue.code, issue.field, issue.evidence)
```

Do not silently deduplicate records or issues.

Issue `evidence` that identifies an input file is limited to a canonical
package-relative path plus stable source locator. Reject/normalize away any
absolute path, cwd, package/temp root, machine user, OS root, or runtime
directory before constructing authority/report evidence.

Exact and ambiguous collisions remain blocking issues. Never merge candidates
automatically.

- [ ] **Step 4: Run focused GREEN**

Require both Task 9A test modules PASS.

## Task 5: Report closure and public surface

**Files:**
- Modify: both Task 9A test modules
- Modify: `src/joy_m2/ingest/preflight.py`
- Create: `src/joy_m2/ingest/__init__.py`

- [ ] **Step 1: Add report/public RED tests**

Lock exact `__all__`, direct imports, deterministic equality across equivalent
roots, order-independent issue output, manifest-ordered candidates, exact
counts, and status closure. A clean V1.19-targeted batch returns
`READY FOR USER IMPORT APPROVAL`; any blocker returns
`BLOCKED — IMPORT PREFLIGHT FAILED`.

The full `ArtifactRef` is forbidden from digest serialization because its path
is resolved and absolute. Derive this exact path-free baseline projection from
the sole typed `baseline_database` plus validated frozen identity:

```python
{
    "release_version": "V1.18",
    "schema_version": "complete-question-v1.0",
    "question_count": 497,
    "sha256": baseline_database.sha256,
    "size_bytes": baseline_database.size_bytes,
    "kind": baseline_database.kind,
}
```

Validate `baseline_database.kind == "sqlite"`, lowercase digest, exact integer
size, bytes, schema/version, and count before constructing the projection.

Lock `preflight_sha256` to SHA-256 over a canonical object with exactly these
top-level keys:

```text
schema, batch_id, target_release_version, baseline, manifest_policies,
candidate_record_order, file_evidence, candidates, issues,
duplicate_classifications, image_evidence, report
```

The projections are exact:

- `schema=task9-preflight-v1`; target is `V1.19`.
- `manifest_policies` contains exactly `schema_version`, `project`, `module`,
  `chapter`, `language_policy`, `split_policy`, `difficulty_policy`,
  `tag_policy`, `answer_policy`, and `explanation_policy`.
- `candidate_record_order` retains manifest-declared canonical relative paths.
- `file_evidence` projects `(relative_path, sha256, size_bytes, kind)` for every
  manifest entry, stable-sorted by exactly `relative_path`; duplicate paths are
  invalid.
- `candidates` projects every exact `ImportCandidate` field in manifest-
  declared semantic order, including provenance payload/status/evidence.
- `issues` projects every exact `ImportIssue` field in the existing exact sort
  key `(proposed_question_id, code, field, evidence)`.
- `duplicate_classifications` projects one candidate-ordered tuple
  `(proposed_question_id, classification, ambiguous)` with classification
  exactly `new_candidate | duplicate | rejected` and exact boolean ambiguity.
- `image_evidence` is candidate-order then declared-image-position order and
  projects `(proposed_question_id, relative_path, sha256, role, size_bytes,
  kind)` from candidate/file evidence.
- `report` projects every `ImportPreflightReport` field except
  `preflight_sha256`, including complete count closure. File lists use
  canonical `relative_path` order; candidate/proposed-ID/missing/ambiguous lists
  use candidate order; `level_counts` uses ascending Level; warnings and
  blockers retain the corresponding issue order.

Every path-bearing projection uses canonical package-relative POSIX paths.
Issue diagnostics may append only a stable source locator. Exclude timestamps,
absolute/package/temp/repository roots, cwd, usernames, memory addresses,
session IDs, AI conversation IDs, unordered dict/set iteration, and the digest
itself.

Encode with the maintained deterministic JSON authority:
`joy_m2.export.formats.canonical_json_bytes(payload) + b"\n"`; import and reuse
that existing helper without modifying Export files. This fixes UTF-8, sorted keys, compact
`,`/`:` separators, `ensure_ascii=False`, and exactly one LF. Exact-type
validation admits no float/NaN value, and arrays follow the ordering rules
above. Do not create a second JSON encoding convention.

Add independent RED controls:

- Copy one canonical package and the same baseline bytes beneath two different
  absolute roots. Manifest/file/candidate/issue values, report authority, and
  both digests must be equal, and neither root string may occur in report/digest
  serialization. The explicit result `baseline_database.path` may differ but is
  excluded from all canonical projections and equality assertions.
- Shuffle only filesystem discovery order while retaining manifest candidate
  order. Candidate tuple, report, and digest must remain equal.
- Change manifest semantic order from `[q1, q2]` to `[q2, q1]`. Candidate tuple
  must reflect the new order and the digest must change.
- Change a translation/explanation payload, evidence, or provenance status,
  including `ai_proposed` to `verified`; the digest must change and invalidate
  the old approval.

Any other input, candidate, issue, duplicate/image projection, count, or target
change must also alter the digest.

- [ ] **Step 2: Prove report RED**

Run both modules; only report/public behavior may fail.

- [ ] **Step 3: Implement minimum closure**

Construct immutable values only. Do not write Markdown, staging, SQLite,
exports, or release artifacts.

- [ ] **Step 4: Run complete focused GREEN**

```bash
python -m unittest -v \
  tests.unit.test_ingest_models \
  tests.integration.test_ingest_preflight
```

Require all PASS, skip=0, expectedFailure=0.

### Task 9A complete RED gate inventory

The focused TDD sequence must establish all 24 contracts before its respective
minimum implementation step; an import/setup/fixture/environment failure is
never valid RED evidence:

The preliminary Stage 3A API-existence RED is a separate testability gate and
does not replace, merge, or delete any item below. Stage 3B establishes the
applicable behavior REDs only after the importable scaffold exists.

1. exact six-carrier fields/order/types/frozen semantics;
2. exact manifest fields/order/policy values and V1.19 target;
3. canonical relative-path containment and symlink/undeclared-file rejection;
4. file kind/SHA-256/size/readability identity;
5. unsupported MMD/MMD.ZIP/PDF blocker behavior;
6. frozen V1.18 logical identity, read-only mode, integrity, and 497 count;
7. exact candidate identity/content and derived normalized-text digest;
8. proposed-ID and baseline/batch ID collision controls;
9. source-locator/fragment/normalized-text duplicate controls;
10. image binding, missing/orphan/collision controls;
11. answer/tag/difficulty/enrichment consistency and disclosure;
12. deterministic issue key and no silent deduplication;
13. disjoint duplicate/rejected/new classifications and count closure;
14. report status, public surface, and digest-bound approval closure;
15. zero mutation of SQLite, data, releases, legacy, and formal images;
16. cross-absolute-root `preflight_sha256` equivalence;
17. no absolute-path authority/report/digest contamination;
18. translation provenance exact values;
19. translation payload/status/evidence consistency;
20. explanation provenance exact values;
21. explanation payload/status/evidence consistency;
22. AI-proposed versus source-authenticated authority distinction;
23. candidate order independence from filesystem discovery order;
24. manifest-declared candidate reorder semantics and digest change.

## Task 6: Regression and review gate

**Files:** No additional files.

- [ ] **Step 1: Run maintained gates**

```bash
python -m unittest -v tests.unit.test_pipeline_models
python -m unittest -v tests.unit.test_audit_pipeline
python -m unittest -v tests.integration.test_db_pipeline
python -m unittest -v \
  tests.unit.test_v117_release_transformer \
  tests.unit.test_release_primitives \
  tests.integration.test_release_pipeline
python -m unittest -v tests.regression.test_task7_project_initialization
python -m unittest -v tests.regression.test_task8b_pipeline_equivalence
python releases/V1.18/verify_task6_release.py releases/V1.18
git diff --check
```

Expected existing counts: Public Models 66/66, Audit 21/21, Database 14/14,
Release 48/48, Task 7 7/7, Task 8 equivalence 3/3, V1.18 validator PASS.

- [ ] **Step 2: Verify strict scope/frozen boundary**

Only the six Task 9A files may differ. Snapshot and compare before/after hashes
and inventories for V1.18 SQLite, `releases/`, `data/`, `legacy/`, and existing
formal image assets. V1.18 hashes/count 497, Task 8B docs, all existing
production modules, and every frozen artifact remain unchanged.

- [ ] **Step 3: Stop for independent review**

Report RED/GREEN evidence, supported/unsupported formats, deterministic report,
zero mutation, gates, and deferred Task 9C decisions. Do not commit, push, or
start Task 9B/9C/9D.

- [ ] **Step 4: Commit only after explicit approval**

After review PASS and commit authorization, stage exactly six files and use:

```text
feat: add batch import preflight contract
```

No raw/staging/formal artifacts or documentation enter that implementation
commit.

## Downstream hold point

This plan ends at Task 9A. Task 9B needs separately approved representative
Mathpix MMD/MMD.ZIP fixtures and adapter scope; direct PDF remains deferred.
Task 9C/9D cannot start until a separate authority freezes V1.19 database and
manifest serialization, `PRAGMA user_version`, teacher/common-error formal
representation or exclusion, image destination/serialization, migration and
rollback artifacts, and promotion contracts. Import approval and formal release
promotion remain separate checkpoints.

Task 9B may define adapter-side image extraction and canonical evidence mapping,
but it may not choose the formal image destination reserved for Task 9C writer
authority.
