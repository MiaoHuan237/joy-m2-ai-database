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
- Historical Stage 3A/Stage 3B entry work is completed. C1 is GREEN; C2 is
  GREEN; C3 is GREEN; C4 is GREEN; C4 SIGNAL-SHAPE ALIGNMENT is COMPLETED /
  GREEN; the C5
  classification layer is COMPLETED / GREEN; and C6 is blocked/not implemented.
  Current authority is TASK 9A FILE-INTEGRITY AUTHORITY REVISION IN REVIEW.
  The completed C4 SIGNAL-SHAPE ALIGNMENT is distinct from the not-yet-executed
  FILE-INTEGRITY SIGNAL ALIGNMENT.
  The fresh integration baseline is
  37 collected, 8 PASS methods, 29 RED methods, 58 failure instances, 0 ERROR,
  and 0 skip. The only current entry is the file-integrity authority review,
  followed after PASS by docs commit, test-only integrity migration with
  independent valid size-only and SHA-only REDs, separately authorized FILE-
  INTEGRITY SIGNAL ALIGNMENT, advancement to the C6-only RED stop, independent
  FILE-INTEGRITY SIGNAL ALIGNMENT review, and later C6 final closure.
  V1.19 serialization/profile, writer, formal release, and promotion authority
  remain deferred to Task 9C.

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
field of any of the seven public carriers and is excluded from canonical report,
digest, and approval projections.

Exact `joy_m2.ingest.__all__`:

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
)
```

## Task 1: Immutable carriers

**Files:**
- Create: `tests/unit/test_ingest_models.py`
- Create: `src/joy_m2/ingest/models.py`

**Interfaces:** Produces the seven typed carriers consumed by manifest/preflight.

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
class ImportAdaptation:
    candidate_id: str
    reference_question_id: str
    adaptation_kind: str
    evidence: str
    reason: str

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
    adaptations: tuple[ImportAdaptation, ...]
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

`ImportAdaptation` is separate read-only preflight classification evidence, not
intrinsic `ImportCandidate` data and not a future formal row field. Its five
fields have exact runtime type `str`, no defaults, and must be non-empty;
`adaptation_kind` is exactly `"adapted"`. Do not add `duplicate_status`,
`duplicate_reference`, or `duplicate_evidence` to `ImportCandidate` or the
canonical raw-record field set. `ImportPreflightResult` does not repeat the
adaptation tuple: the single maintained authority is
`ImportPreflightReport.adaptations`, placed immediately after `proposed_ids` and
before `warnings`.

Adaptation does not project an `ImportIssue`; `code="adaptation"` is forbidden
in `issues`. Its only authoritative carrier is
`ImportPreflightReport.adaptations`, and it is neither a blocking issue nor a
duplicate classification. Without an independent candidate-bound blocker, the
candidate
remains `new_candidate`, `issues` may be empty, and the report may remain READY.
`report.warnings` does not copy adaptation evidence and, because Task 9A
currently approves no separate warning issue code, is exactly empty for an
adaptation-only input. Any future warning taxonomy needs separate authority.

Freeze the closed duplicate/collision blocking issue taxonomy and exact field
mapping. It is not the complete set of Task 9A blocking `ImportIssue` codes:

| code | severity | field |
| --- | --- | --- |
| `duplicate_exact` | `blocking` | `candidate` |
| `collision_candidate_id` | `blocking` | `proposed_question_id` |
| `collision_source_locator` | `blocking` | `source_locator` |
| `collision_fragment_sha256` | `blocking` | `source_fragment_hash` |
| `collision_normalized_text_sha256` | `blocking` | `normalized_text_sha256` |
| `collision_image_sha256` | `blocking` | `image_sha256s` |
| `duplicate_ambiguous` | `blocking` | `duplicate` |

Evidence is the no-LF UTF-8 string from
`canonical_json_bytes(exact_object).decode("utf-8")`, never free prose. Exact
objects are:

- `duplicate_exact`: `candidate_id`, `reference_question_id`,
  `normalized_text_sha256`;
- `collision_candidate_id`: `candidate_id`, `reference_question_id`,
  `candidate_fragment_sha256`, `reference_fragment_sha256`;
- `collision_source_locator`: `candidate_id`, `candidate_source_locator`,
  `candidate_fragment_sha256`, `reference_question_id`,
  `reference_source_locator`, `reference_fragment_sha256`, with each locator
  the exact array `[source_id, source_question_number, source_section]`;
- `collision_fragment_sha256`: `candidate_id`, `candidate_source_locator`,
  `reference_question_id`, `reference_source_locator`,
  `source_fragment_sha256`, with the same locator array order;
- `collision_normalized_text_sha256`: `candidate_id`,
  `reference_question_id`, `normalized_text_sha256`;
- `collision_image_sha256`: `candidate_id`, `candidate_image_path`,
  `candidate_image_role`, `candidate_image_sha256`, `reference_question_id`,
  `reference_image_path`, `reference_image_role`, `reference_image_sha256`;
- `duplicate_ambiguous`: `candidate_id`, `matches`, where `matches` is sorted
  by `reference_question_id` and each exact object contains
  `reference_question_id` plus a sorted unique `signals` array drawn from
  `candidate_id`, `source_locator`, `source_fragment_sha256`,
  `normalized_text_sha256`, and `image_sha256`.

All paths in evidence are canonical logical relative paths. The serializer
fixes sorted keys, compact separators, and `ensure_ascii=False`; evidence has no
absolute/runtime path, timestamp, machine/session value, unordered set repr, or
trailing LF. Stable-sort issues by exactly
`(proposed_question_id or "", code, field, evidence)`. Adaptation remains only
the separate warning-classification evidence in `report.adaptations`; it never
enters `issues`, `duplicate_classifications`, or a blocking duplicate/collision
code.

Freeze eight existing non-duplicate blocking codes alongside the unchanged
seven-code duplicate/collision taxonomy, and add exactly one file-integrity
code. These three sets are the complete sixteen-code Task 9A blocking
`ImportIssue` authority; no other blocking code is approved:

The independent 37-method / 29-RED blocker scan found no other structured-
BLOCKED condition lacking an approved `ImportIssue` code. This preserves the
closed sixteen-code inventory and does not authorize a seventeenth code.

| code | severity | field | `proposed_question_id` | exact evidence object |
| --- | --- | --- | --- | --- |
| `missing_image` | `blocking` | `images` | `None` | `{candidate_id, relative_path, role}` |
| `orphan_image` | `blocking` | `images` | `None` | `{relative_path, sha256}` |
| `unsupported_source_format` | `blocking` | `source_format` | `None` | `{relative_path, format}` |
| `unknown_primary_type` | `blocking` | `primary_type` | candidate ID | `{candidate_id, value}` |
| `unknown_tag` | `blocking` | `tags` | candidate ID | `{candidate_id, unknown_tags}` |
| `malformed_candidate_json` | `blocking` | `candidate_records` | `None` | `{relative_path}` |
| `invalid_candidate_top_level` | `blocking` | `candidate_records` | `None` | `{relative_path, expected}` |
| `invalid_candidate_record` | `blocking` | `candidate_records` | `None` | `{relative_path, record_index}` |
| `file_integrity_mismatch` | `blocking` | `file_integrity` | `None` | `{relative_path, expected_sha256, actual_sha256, expected_size_bytes, actual_size_bytes}` |

`file_integrity_mismatch` applies only after a manifest-declared package path
passes containment, existence, regular-file, and readability checks and its raw
bytes are read. Emit it when actual byte length differs from declared
`size_bytes` or `sha256(actual_bytes)` differs from declared `sha256`. Missing,
unreadable, non-regular, and escaping paths remain existing C1 early
`PipelineError` cases. The exact evidence always contains all five keys even
when only one comparison differs. Both sizes are exact non-negative `int`
values with `bool` forbidden, both digests are lowercase 64-character
hexadecimal SHA-256 values, and the path is canonical and package-relative.
A mutated carrier with a wrong metadata runtime type, malformed declared
digest, invalid kind, or invalid relative path cannot form this exact evidence
and remains an API/carrier-contract `PipelineError`; the structured issue is
only the comparison failure between valid declared scalars and actual readable
bytes.

Once a file has this issue, its bytes are untrusted and cannot feed candidate
parsing, provenance, image evidence, matching, adaptation, or classification.
Do not parse an integrity-failed `candidate_records` file and do not additionally
emit `malformed_candidate_json`, `invalid_candidate_top_level`, or
`invalid_candidate_record`. Do not construct a candidate that declares an
integrity-failed image, and do not also call that image `missing_image`; that
record enters no candidate count. Likewise, do not construct a candidate whose
`source:` translation or explanation evidence names an integrity-failed source
file. Because Task 9A has no per-candidate association for answer,
teacher-note, or common-error files, their integrity failures block the package
without invalidating otherwise independent typed candidates. Do not infer an
unrepresented dependency. Therefore a clean duplicate plus an unrelated
teacher-note integrity mismatch remains duplicate while the report is BLOCKED.
An adaptation also remains for an unrelated failed file, while an integrity-
failed image or source evidence required by that candidate prevents both the
candidate and adaptation from being constructed.

The canonical `file_evidence` projection remains the declared manifest
inventory, not a claim that every file passed consumption-time integrity. A
failed file's expected and actual identities occur only in its formal issue.
It remains a readable path in report inventory, but its bytes are excluded from
downstream authority.

Every evidence string is exactly
`canonical_json_bytes(exact_object).decode("utf-8")`, with no trailing LF and
the existing sorted-key, compact, `ensure_ascii=False`, path-independent rules.
Exclude absolute paths, package/baseline/cwd/temp/repository roots, timestamps,
parser or validation prose, runtime type names, machine/session data, and
unordered values.

`malformed_candidate_json` means an approved `candidate_records` file cannot be
decoded and parsed as strict UTF-8 JSON. It excludes deferred MMD/MMD.ZIP/PDF,
parsed wrong-top-level JSON, and an invalid element within a valid array. Its
exact evidence is `{relative_path}`. `invalid_candidate_top_level` means JSON
parsed but the top level is not the approved array; its exact evidence is
`{relative_path, expected}` with `expected="array"` exactly.

`invalid_candidate_record` is one issue for each zero-based array element that
cannot construct the exact typed `ImportCandidate`: wrong/missing keys, wrong
scalar or container types, invalid status/payload or difficulty combinations,
or malformed enrichment disclosure. Its exact evidence is
`{relative_path, record_index}`; the index is an exact non-negative `int`, with
`bool` forbidden. Its `proposed_question_id` is always `None`, including when
the untrusted record contains a string resembling an ID. Do not merge distinct
invalid indexes.

The three candidate-input issues, `missing_image`, `orphan_image`, and
`unsupported_source_format` are package/pre-candidate or file-level blockers.
They create no placeholder candidate or formal candidate ID, do not directly
change a successfully constructed candidate classification, and add nothing to
detected/new/duplicate/rejected counts. Candidate counts include only
successfully constructed typed candidates. Every package/file-level issue still
enters `issues` and makes the C6 report BLOCKED.

The complete package/pre-candidate blocker set is exactly
`malformed_candidate_json`, `invalid_candidate_top_level`,
`invalid_candidate_record`, `missing_image`, `orphan_image`, and
`unsupported_source_format`, plus `file_integrity_mismatch`. The complete
candidate-bound blocker set is
exactly `unknown_primary_type`, `unknown_tag`, and the seven approved
duplicate/collision codes. No package/pre-candidate issue claims formal
candidate identity or changes a successfully constructed candidate's
classification.

Process each candidate source record in this exact order: parse the raw record;
validate its exact structure, runtime types, candidate ID,
status/payload combinations, basic fields, taxonomy-field structure and
vocabulary membership, and positional `(relative_path, role)` image bindings;
verify that every binding has approved manifest/package image evidence
supplying an actual SHA-256; only then construct the exact typed
`ImportCandidate`. An unknown but correctly typed taxonomy value does not
prevent typed construction when image evidence is complete; emit its
candidate-bound taxonomy issue only after that construction. Perform all
candidate-level taxonomy issue emission, duplicate/collision matching,
adaptation, and classification only after construction.

A record that fails validation before image-evidence checking emits only
`invalid_candidate_record`: no missing-image, unknown-taxonomy,
duplicate/collision, or adaptation signal. A missing or wrong-type
`primary_type` is invalid-candidate-record input; an exact `str` outside the
vocabulary is eligible for `unknown_primary_type` only if the record later
constructs a typed candidate. A malformed `tags` container or non-string member
is invalid-candidate-record input; valid unknown strings are eligible for one
`unknown_tag` issue with a sorted unique `unknown_tags` array only after typed
candidate construction.

Treat `missing_image` as a pre-candidate/package-level issue. Emit it once for
each structurally valid raw-record binding whose canonical relative path has no
approved manifest/package image evidence capable of supplying the required
actual SHA-256. The raw record ID must already be an exact valid, non-empty
`str`, but it is locating evidence rather than formal candidate identity:
`ImportIssue.proposed_question_id` is exactly `None`, and evidence is exactly
`{candidate_id, relative_path, role}`. The private signal must retain
`("missing_image", raw_candidate_id, relative_path, role)` or an exactly
equivalent carrier. Its raw candidate ID may not be `None`, and C5 must not
guess `role`.

A missing-image record constructs no `ImportCandidate`, creates no candidate
classification, adaptation, duplicate/collision result, or candidate count,
and never enters C5 matching. Do not use a `None`, empty, or placeholder digest;
do not delete the missing binding and pretend the candidate is complete; and do
not introduce an incomplete public candidate carrier. Preserve the public
frozen 25-field `ImportCandidate`: `image_paths`, `image_sha256s`, and
`image_roles` remain equal-length tuples and every image SHA remains a valid
lowercase 64-character SHA-256. A complete same-path/role image with a
candidate/reference SHA conflict remains `collision_image_sha256`, not
`missing_image`.

For `orphan_image`, compare each manifest image's canonical `relative_path`
against the canonical relative paths in valid image bindings of successfully
constructed typed candidates. This reference identity is path-only because the
manifest carrier has no independent role authority. Invalid record references
do not bind an image. Emit one issue for each unbound manifest image with exact
evidence `{relative_path, sha256}` and no invented role.

For `unsupported_source_format`, ASCII-lowercase the canonical logical path and
match deferred source suffixes longest first: `.mmd.zip -> "mmd_zip"`,
`.mmd -> "mmd"`, `.pdf -> "pdf"`. Its exact evidence is
`{relative_path, format}`. Task 9A identifies but does not parse those files;
malformed canonical candidate JSON is `malformed_candidate_json` instead.
`unknown_primary_type` evidence is `{candidate_id, value}` with no correction,
mapping, or inference. `unknown_tag` evidence is
`{candidate_id, unknown_tags}` and is emitted at most once per candidate with a
sorted unique array of unknown valid strings.

Non-duplicate blockers do not suppress one another or independent issues from
other successfully constructed candidates. Candidate-bound
`unknown_primary_type` and `unknown_tag` make the typed candidate rejected and
count it only as rejected; retain any independently established duplicate
reference or adaptation evidence. A clean duplicate plus an independent
package-level blocker remains duplicate and increments only duplicate count
while the report is BLOCKED. A duplicate plus a candidate-level taxonomy
blocker retains the duplicate evidence but is rejected and increments only
rejected count. A missing-image record never reaches duplicate/collision
classification.

The adaptation interaction is exact. Its unique reference is established only
for a successfully constructed typed candidate. A missing-image record creates
or retains no `ImportAdaptation` and never enters candidate matching. Unknown
taxonomy may retain an independently established adaptation and issue, reject
that typed candidate, and block the report.
Package-level `orphan_image` or an independent `unsupported_source_format`
retains an otherwise-valid adaptation and the candidate's `new_candidate`
classification/count while blocking the report. An input available only in an
unsupported format constructs no candidate, placeholder, or adaptation.

Stable-sort all sixteen issue codes by exactly
`(proposed_question_id or "", code, field, evidence)` and project them through
the existing `issues` member of the 12-key digest payload. There is no
`report_only_blockers`, `package_blockers`, `validation_blockers`, second
ordering, or thirteenth key. Any membership, code, field, or evidence change
changes the final digest; any blocking issue makes C6 report BLOCKED.
`report.blocking_errors`, where rendered, is a deterministic derived projection
of `issues`, not independent blocker authority.

**HISTORICAL COMPLETED RECORD — NO CURRENT EXECUTION EFFECT.** The C4 private
raw-signal inventory remained exactly these eight non-duplicate codes and had
no ninth C4 blocking signal. The separately approved C1 file-integrity signal
does not alter that historical inventory. The separately authorized **C4
SIGNAL-SHAPE ALIGNMENT** was implemented and remained limited to private raw-
signal construction:

- malformed/top-level signals retained canonical `relative_path`;
- invalid-record signals retained canonical `relative_path` and a zero-based
  exact integer `record_index`, never a candidate ID;
- missing-image signals retained valid raw `candidate_id`, canonical
  `relative_path`, and `role` after structural/basic validation but before, and
  without, typed candidate construction;
- invalid candidates emitted no missing-image or later candidate-level signals;
- missing-image records constructed no typed candidate and never reached C5
  matching, duplicate/collision, adaptation, or classification;
- orphan detection used canonical relative-path matching only.

That checkpoint did not classify candidates, construct `ImportIssue`, or
construct report/result. Its independent verification passed, its checkpoint
was committed, and C5 was subsequently authorized and implemented to convert
all eight private signals.
`test_candidate_json_parsing_accepts_only_exact_canonical_record_objects` locks
the three candidate-input codes as structured BLOCKED results, not
`PipelineError`. `test_missing_orphan_images_and_unknown_taxonomy_are_blockers`
locks the first, second, fourth, and fifth semantic/package codes;
`test_unsupported_mmd_mmd_zip_and_pdf_are_blockers` locks the third. No new
public API is authorized. API/carrier/root/baseline boundary errors and package
containment/missing/unreadable/non-regular file failures remain eligible for
early `PipelineError`; readable package-file size/SHA identity mismatch is the
single exception and uses `file_integrity_mismatch`. Safely read package-
internal candidate content errors use formal issues. Any future blocking raw signal without
approved code, field, evidence, scope, count, and digest semantics is a new
authority gap and must stop implementation.

Freeze issue predicates and precedence before behavior tests:

1. Signals resolving to multiple competing reference IDs with no unique result
   emit only `duplicate_ambiguous` for those references; constituent
   per-reference issues are suppressed and classification is rejected/
   ambiguous.
2. For one reference, `duplicate_exact` requires equal stable source locator,
   `source_fragment_hash`, `normalized_text_sha256`, and the complete declared
   image tuple `(logical relative path, role, sha256)` (empty equals only empty);
   `size_bytes` is integrity evidence and is excluded from image identity. It
   classifies duplicate only when no independent candidate-bound blocker exists and suppresses
   candidate-ID, locator, fragment,
   normalized-text, and image constituent issues against that same reference.
3. The approved adaptation predicate then suppresses only the same-reference
   locator/fragment constituent collisions that form its unique stable source
   match. An independent blocker may coexist only when it does not invalidate
   that unique adapted reference. The approved representative is an additional
   same-reference image path/role binding with a conflicting SHA: it independently
   emits `collision_image_sha256`, retains the adaptation, and rejects/blocks the
   candidate. A proposed-ID collision, competing-reference
   `duplicate_ambiguous`, or any blocker that negates adaptation identity prevents
   creation of the adaptation carrier.
4. Otherwise collect every independently true collision. One candidate may have
   multiple blockers for unrelated signals or different references. Any
   independent candidate-bound blocker makes the final classification
   `rejected`, including when a `duplicate_exact` issue is retained. A
   package/file-level blocker leaves candidate classification unchanged; each
   candidate contributes to exactly one of new/duplicate/rejected counts.

The exact predicate/precedence table is:

| code | trigger | suppresses | can coexist with | classification result |
| --- | --- | --- | --- | --- |
| `duplicate_exact` | one reference has equal stable locator, fragment digest, normalized-text digest, and complete `(relative_path, role, sha256)` image tuple | all same-reference constituent ID/locator/fragment/text/image collisions | unrelated blockers against other identities | `duplicate`, `ambiguous=false` without an independent candidate-bound blocker; a candidate-bound blocker retains this issue/evidence and classifies `rejected`, while a package/file-level blocker leaves it `duplicate` |
| `collision_candidate_id` | proposed ID equals an existing/earlier-batch ID but is not its exact duplicate | nothing | any independent blocking collision; never `ImportAdaptation` for the same candidate | `rejected`, `ambiguous=false` unless multi-reference |
| `collision_source_locator` | locator equals but fragment, normalized text, or complete image identity differs, and adaptation did not suppress it | nothing | independent ID/fragment/text/image collisions | `rejected`, `ambiguous=false` unless multi-reference |
| `collision_fragment_sha256` | fragment digest equals but neither exact duplicate nor approved adaptation applies | nothing | independent ID/locator/text/image collisions | `rejected`, `ambiguous=false` unless multi-reference |
| `collision_normalized_text_sha256` | normalized text equals but exact duplicate is false | nothing; never creates adaptation | independent ID/locator/fragment/image collisions | `rejected`, `ambiguous=false` unless multi-reference |
| `collision_image_sha256` | equal logical path/role binds different SHA-256; equal path/role/SHA is the same image regardless of redundant declared size | nothing | every independent blocker | `rejected`, `ambiguous=false` unless multi-reference |
| `duplicate_ambiguous` | competing signals reach multiple references without one unique result | constituent per-reference duplicate/collision issues | unrelated non-identity blockers only; never `ImportAdaptation` for the same candidate | `rejected`, `ambiguous=true` |

The separate non-issue adaptation precedence row is:

| carrier | trigger | suppresses | can coexist with | cannot coexist with | final classification |
| --- | --- | --- | --- | --- | --- |
| `ImportAdaptation` | one unique adapted reference; equal locator and fragment digest; different normalized-text digest; not exact duplicate; no proposed-ID collision; no competing identity reference | only same-reference locator/fragment constituent signals establishing the adaptation | independent blockers that preserve the unique adapted reference, represented by an additional same-reference image path/role binding with conflicting SHA | `collision_candidate_id`; competing-reference `duplicate_ambiguous`; every blocker whose predicate negates adaptation identity | `new_candidate` without a candidate-bound blocker; an approved coexisting candidate-bound blocker makes it `rejected`, while a package/file-level blocker retains `new_candidate`; retain the adaptation and blocker in both cases |

For one candidate, `collision_candidate_id` cannot coexist with
`ImportAdaptation`: the collision makes the adaptation predicate false.
Competing-reference `duplicate_ambiguous` likewise cannot coexist with an
adaptation. Any ID coexistence described in the blocking-code rows is between
blocking issues and does not authorize an ID collision plus adaptation.

For a non-ambiguous rejection that retains one unique `duplicate_exact`
relationship, `duplicate_classifications` uses `classification="rejected"`
while retaining that duplicate reference ID and evidence; independent issues
record the rejection reason. If the duplicate reference is not unique, retain
the existing ambiguous rule with null reference and `duplicate_ambiguous`
evidence. Consequently duplicate-only increments only duplicate count;
duplicate plus a candidate-bound blocker increments only rejected count, while
duplicate plus a package/file-level blocker remains duplicate; adaptation-only
increments only new count; adaptation plus an approved independent
candidate-bound blocker that preserves the unique adapted reference increments
only rejected count while retaining `report.adaptations`, whereas a package/
file-level blocker retains the new count. Adaptation-like signals plus an ID
collision or competing reference increment only rejected count and emit no
adaptation.

Treat image metadata integrity separately from image collision. A declared
image whose actual bytes differ from its own declared size or SHA emits
`file_integrity_mismatch`, never `collision_image_sha256`, and its untrusted
manifest SHA is not used in candidate/reference matching. Same path/role with
matching actual and declared SHA but incorrect declared size is therefore a
file-integrity issue. `collision_image_sha256` remains limited to two
independently valid image identities with the same logical path/role and
different approved SHA values; its evidence schema remains size-free.

Add independent overlap REDs for: duplicate-only producing final duplicate;
duplicate plus an independent candidate-bound blocker producing final rejected
while retaining the duplicate issue/reference/evidence; duplicate reference A
plus a candidate-bound blocker against reference B producing rejected;
competing duplicate references producing
ambiguous/rejected; adaptation-only producing new/READY; adaptation plus an
independent additional-image SHA blocker retaining adaptation and image issue but
producing rejected/BLOCKED; adaptation-like signals plus proposed-ID collision
producing no adaptation and candidate-ID collision/rejected/BLOCKED;
adaptation-like signals plus competing references producing no adaptation and
ambiguous/rejected; exact duplicate producing no adaptation;
equal normalized text with different locator/fragment producing normalized
collision; equal image path/role/SHA and bytes producing no collision; equal
image path/role with different SHA/bytes producing image collision; and equal
SHA with incorrect declared size producing `file_integrity_mismatch` but not
`collision_image_sha256`.

After this authority remediation passes independent review and is committed,
do not modify production. First require a **test-only file-integrity migration
checkpoint** that changes only `tests/integration/test_ingest_preflight.py`.
Narrowly split/migrate
`test_preflight_rechecks_every_consumed_package_file_hash_size_and_existence`
and, only if necessary, a directly reused file-integrity fixture/helper.
Containment, missing, unreadable, and non-regular failures remain
`PipelineError`. The size-only fixture must keep actual and declared SHA equal
while declaring a different size. The SHA-only fixture must keep actual and
declared sizes equal while using different same-length bytes. Both must expect
a structured `ImportPreflightResult` with `file_integrity_mismatch`; the wrong-
image-size test retains its existing authority and must also require no
`collision_image_sha256`. Do not modify duplicate, adaptation, count, oracle,
or unrelated behavior tests.

Run this migration before any production change. Valid RED requires successful
imports and fixture construction, an actual call through the approved API to
the current integrity gate, and a failure caused only by current `PipelineError`
versus the expected structured result. Fixture, syntax, import, setup, or
unrelated validation failures are invalid RED. Report the exact failure; keep
the production SHA byte-identical; confirm missing-file and unaffected Group
1/2/C1 tests remain GREEN and ERROR count is zero; then stop. This is an
authority migration of superseded expectations, not weakened coverage.

Only a later explicit authorization may start the **FILE-INTEGRITY SIGNAL
ALIGNMENT checkpoint**. It changes only
`src/joy_m2/ingest/preflight.py`; tests remain byte-identical. Safe-read
size/SHA mismatch becomes the exact private signal
`("file_integrity_mismatch", relative_path, expected_sha256, actual_sha256,
expected_size_bytes, actual_size_bytes)` or a semantically identical carrier.
Exclude corrupted bytes from downstream authority; preserve missing,
unreadable, non-regular, and containment `PipelineError`; construct no formal
issue, report, result, classification, count, or final digest; and add no public
API. Private helper invocation or temporary in-process diagnostics may verify
the signal and exclusion but must leave no debug file.

After FILE-INTEGRITY SIGNAL ALIGNMENT, the migrated size-only and SHA-only
public tests must advance beyond the old `PipelineError` but remain RED solely
at `NotImplementedError` or
the exact approved C6 stop. This is the alignment checkpoint's success
condition; public structured-result GREEN is explicitly forbidden before C6.
Independently review production scope, all six signal values, corrupted-byte
exclusion, missing-boundary preservation, test immutability, and the changed
RED failure point.

C6 final closure may be authorized only after authority docs are committed,
the test-only migration is committed or checkpointed under the approved
workflow, both valid REDs are recorded, FILE-INTEGRITY SIGNAL ALIGNMENT is
implemented and reviewed, the remaining RED is solely C6 result closure, and maintained/frozen
gates PASS. C6 alone converts the private signal to the formal issue and constructs
counts, status, report, result, exact 12-key payload, and final digest. Only C6
makes size-only, SHA-only, and wrong-image-size structured tests GREEN; then run
full integration 37/37, maintained/frozen gates, final independent review, and
the separately authorized implementation commit.

The issue uses the existing global issue ordering and existing `issues` member
of the exact 12-key digest payload. Do not add `integrity_errors`,
`file_errors`, `validation_errors`, a thirteenth key, or any other parallel
authority. Changing relative path, either digest, either size, or issue
membership changes the final digest. The literal happy-path fixture contains no
integrity mismatch, so its frozen `manifest_sha256` remains
`b5a0ae6597028c48c6f7cdc81bd7e67d61dd369cbf96d7c6a4e96efd73984c5d`
and its frozen final `preflight_sha256` remains
`087574a8af6fe28ac65a5b5810794952044cb5f0778ed3492d1e7819a4be33c2`.

Add an ordering RED containing several issues with both
`proposed_question_id=None` and `proposed_question_id="Q001"`. It must sort by
exactly `(issue.proposed_question_id or "", issue.code, issue.field,
issue.evidence)` without a `None`/`str` `TypeError`.

Test frozen assignment rejection, tuple copying/no alias, exact runtime types,
lowercase SHA-256, non-negative counts, deterministic issues, and arithmetic:

```python
detected_count == new_candidate_count + duplicate_count + rejected_count
projected_after_count == before_count + new_candidate_count
approved_count == 0
ambiguous_count <= rejected_count
```

`detected_count` and all three classification counts include only records that
successfully construct the exact typed `ImportCandidate`. Malformed,
wrong-top-level, invalid-record, missing-image, orphan-image, and unsupported-
format package/pre-candidate facts block through `issues` and add no candidate
count.

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

Derive `normalized_text_sha256` only from the exact input field
`question_text_original`; it is never accepted as caller authority. Require an
exact `str`, apply Unicode NFC, normalize CRLF and CR to LF, and split on LF.
For each line, trim leading/trailing `U+0020`, `U+0009`, `U+000B`, and `U+000C`
and collapse every internal run of those ASCII whitespace characters to one
`U+0020`. Remove only leading/trailing empty lines, preserve all interior empty
lines, join with LF, and append no trailing LF. Do not lowercase, strip
punctuation, change LaTeX delimiters or mathematical symbols, or perform
semantic rewriting. Compute exactly
`sha256(normalized_text.encode("utf-8")).hexdigest()`.

Add independent controls proving equal digests for CRLF/LF, NFC/NFD, harmless
surrounding ASCII whitespace, and repeated intra-line ASCII spaces. Prove
different digests for case, punctuation, mathematical-symbol, substantive-word,
line-order, and semantic line-break changes. These expected digests are
calculated in the test from the literal algorithm above, never captured from
production.

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

## Historical completed Task 2A: Adaptation model remediation checkpoint

**HISTORICAL COMPLETED — NO CURRENT EXECUTION EFFECT.** This historical section
records a completed TDD checkpoint only. It has no current execution authority.
If any historical wording conflicts with the current-status section, the
current-status and current FILE-INTEGRITY RED-first sequence control.

Task 1–2 are already committed at
`dd1cfed2cf3d09caf9136d3c9e2cc8d487186221`; that history was not rewritten.
The separately authorized adaptation-model checkpoint modified only:

- `tests/unit/test_ingest_models.py`
- `src/joy_m2/ingest/models.py`

That checkpoint added RED tests for exact `ImportAdaptation` fields/order/types/
no-defaults, frozen semantics, non-empty values, exact
`adaptation_kind="adapted"`, tuple copy/no-alias behavior, exact report-field
placement, and rejection of every unapproved kind/type, then completed minimum
GREEN, independent review, and commit. `manifest.py` and
canonical raw-record fields remain unchanged; adaptations are produced by
deterministic preflight comparison.
The final nine-name `joy_m2.ingest.__all__` was already frozen above but was not
implemented during this two-file model checkpoint; its implementation remains
deferred to the separately governed Task 5 creation of `ingest/__init__.py`.

## Historical completed Task 3: Baseline and candidate identity

**HISTORICAL COMPLETED TASK — NO LONGER CURRENT EXECUTION AUTHORITY.** This
historical section records completed TDD checkpoints only. It has no current
execution authority. If any historical wording conflicts with the current-
status section, the current-status and current FILE-INTEGRITY RED-first sequence
control.

**HISTORICAL EXECUTION RESULT:** Stage 3A was completed; the Stage 3B behavior
RED gate was completed; and dependency-aware GREEN checkpoints C1–C5 were
subsequently completed. Current execution has advanced beyond this section.

**Historical files created:**
- `tests/integration/test_ingest_preflight.py`
- `src/joy_m2/ingest/preflight.py`

**Historical interface result:** Produced `preflight_import()` and compact
private indexes.

- [x] **HISTORICAL COMPLETED Step 3.1: API-existence and exact-signature test written**

Before `src/joy_m2/ingest/preflight.py` existed, the focused test required the
exact function name, parameter names/order/annotations, return annotation, and
no extra runtime authority parameter:

```python
def preflight_import(
    manifest: BatchImportManifest,
    package_root: Path,
    baseline_database: ArtifactRef,
) -> ImportPreflightResult
```

This was the only RED group for which module missing, symbol missing, or exact
signature unavailable was valid. It was an API-existence RED, not a behavior
RED.

- [x] **HISTORICAL COMPLETED Step 3.2: API RED run and recorded**

The focused integration test was run and failed specifically because the
approved API/signature did not yet exist. Syntax, fixture, and unrelated setup
errors were invalid.

- [x] **HISTORICAL COMPLETED Step 3.3: Minimal importable scaffold created**

After the API RED was recorded, `src/joy_m2/ingest/preflight.py` was created
with exactly the required imports, approved signature, and immediate scaffold
exception:

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

The scaffold validated no root, resolved/read/hashed no file, parsed no
candidate, constructed no evidence/issues/report, and computed no digest.

- [x] **HISTORICAL COMPLETED Step 3.4: Import/signature test GREEN recorded**

Module/symbol import and exact signature equality passed. Task 3 remained RED;
scaffold importability was test infrastructure, not behavior GREEN.

- [x] **HISTORICAL COMPLETED Step 3.5: Root type and validity RED tests added**

With the scaffold importable, independent calls were added for a non-Path
runtime value, nonexistent root, and root that was a file. Each test reached
`preflight_import()` and failed with scaffold `NotImplementedError`, proving the
approved typed failure behavior had not yet been implemented. No cwd/default
fallback was permitted.

- [x] **HISTORICAL COMPLETED Step 3.6: Root-validation RED run and recorded**

The run demonstrated successful import, exact-signature GREEN, valid fixtures,
an actual function call, and behavior RED only from scaffold/missing root
validation.

- [x] **HISTORICAL COMPLETED Step 3.7: Containment and symlink RED tests added**

Independent calls were added for an absolute declared child path, `..`,
normalization escape, and an in-root symlink resolving outside the root. The
tests required path-aware resolved containment and rejected a string-prefix
check as insufficient.

- [x] **HISTORICAL COMPLETED Step 3.8: Containment RED run and recorded**

Every case imported and reached the scaffold. Module/symbol/import, syntax,
fixture, setup, or environment errors were invalid behavior REDs.

- [x] **HISTORICAL COMPLETED Step 3.9: Root-contamination and cross-root RED tests added**

A targeted test proved that the absolute root never occurred in typed evidence,
issue evidence, report serialization, canonical digest payload, or approval
identity. A separate test copied one equivalent package beneath two distinct
absolute roots and required identical file evidence, candidate tuple, issue
tuple, report authority, and `preflight_sha256`.

- [x] **HISTORICAL COMPLETED Step 3.10: Authority behavior REDs run and recorded**

Both groups imported and called the scaffold successfully, then failed with
`NotImplementedError` or their specific missing behavior. Cross-root equality
did not replace the targeted root-string contamination assertion.

- [x] **HISTORICAL COMPLETED Step 3.11: Baseline/zero-mutation RED tests added**

The tests snapshotted V1.18 SQLite, `releases/`, `data/`, `legacy/`, and existing
formal image assets before/after. They asserted exact SQLite `ArtifactRef`,
`mode=ro`, baseline version V1.18, count 497, target V1.19, integrity `ok`, zero
FK errors, V1.18 metadata, compact ID/source-locator/fragment/text/image/
source-order indexes, and no created, deleted, or modified file.

- [x] **HISTORICAL COMPLETED Step 3.12: Candidate-identity RED tests added**

Canonical records were required to decode into exact `ImportCandidate` values
from these input identity/content keys:

```text
proposed_question_id, source_id, source_question_number, source_section,
source_fragment_hash, question_text_original, answer_status,
solution_original, solution_verified, image_paths, primary_type, tags,
difficulty_level, question_text_zh, translation_status, translation_evidence,
explanation_text, explanation_status, explanation_evidence, image_roles,
tag_status, difficulty_status, enrichment_status
```

The tests covered non-object/malformed records, duplicate proposed ID, missing identity,
wrong exact types, empty original, non-null Level outside 1–5, invalid status,
inconsistent missing/proposed tag or difficulty status, non-empty
solution fields for `missing_from_source`, every invalid translation/explanation
payload-status-evidence combination, false source authentication of AI
proposals, missing explanation disclosure, and incomplete enrichment
disclosure. Independent source-provided, AI-proposed, verified, and missing
fixtures were added for both translation and explanation. Task 9A fixtures
carried stable proposal/review evidence; production invoked no AI and performed
no verification. The tests verified that derived normalized-text and image
digests were deterministic and could not be supplied as caller authority.

Candidate order was exactly manifest `candidate_records` order followed by
record-array order within each file. A manifest order `[q3, q1, q2]` produced
that exact candidate tuple without sorting by path, proposed ID, hash,
filesystem traversal, or dictionary insertion effects. The tests independently
shuffled private filesystem discovery order while holding the manifest fixed
and required the same candidate tuple. They explicitly reordered the manifest
and required the candidate tuple to reflect that semantic change.

- [x] **HISTORICAL COMPLETED Step 3.13: Complete behavior RED gate verified**

```bash
python -m unittest -v tests.integration.test_ingest_preflight
```

The complete gate required successful imports, exact-signature GREEN, valid
fixtures, and actual calls reaching the scaffold. Root type/validity,
containment/symlink, contamination/cross-root, baseline/zero-mutation, and
candidate-identity groups were all RED because their production behavior was
absent. Production behavior replaced the scaffold only after that gate.

- [x] **HISTORICAL COMPLETED Step 3.14: Minimum behavior implemented group by group**

The first consumption-boundary group, before baseline SQLite access,
candidate/source/image reads, hashing, or candidate construction, required
`type(manifest) is BatchImportManifest` and
`manifest.target_release_version == "V1.19"`. It independently rejected wrong
runtime types, V1.18, V1.17, arbitrary future versions, `None`, and `""`, and
proved with mocked/spied readers that rejection occurred before any baseline or
package I/O. Prior loader validation was not trusted as a substitute. Invalid
input constructed no result, and a result manifest/report target mismatch was
forbidden.

The implementation validated the explicit root again at the consumption
boundary, resolved every manifest relative path against that root with path-
aware containment, reread and hashed the bytes consumed by preflight, and read
only required baseline columns. It parsed candidates without retaining the root
or constructing publication evidence, `AuditedRecord`, database rows, or output
files.

The completed implementation used one approved behavior group at a time:
`RED → minimum behavior GREEN → focused tests → successive RED group`. It did not
replace the scaffold with the complete preflight in one pass.
`NotImplementedError` was valid only at the scaffold checkpoint and disappeared
from the completed C1–C5 runtime paths.

- [x] **HISTORICAL COMPLETED Step 3.15: Focused GREEN run**

The integration and model modules passed at the completed checkpoint.

### Current post-C5 FILE-INTEGRITY execution authority

**CURRENT AUTHORITY — NOT A HISTORICAL TASK 3 REPLAY.** The post-C5 file-
integrity authority refines the C1 `preflight_import()` consumption rule without
rewriting the historical C1 GREEN result or the Task 2
`load_import_manifest()` inventory-validation contract. C1 remains GREEN for
containment, missing, unreadable, and non-regular `PipelineError`. Its current
readable size/SHA behavior still raises `PipelineError` and is `SUPERSEDED
TARGET BEHAVIOR — PENDING RED-FIRST MIGRATION`. The target is a private
`file_integrity_mismatch` signal with no downstream use of corrupted bytes,
followed only later by C6 formal issue/result closure. The mandatory method is
test-only RED first, separately authorized FILE-INTEGRITY SIGNAL ALIGNMENT
second, public tests still RED only at the C6 stop, and C6 GREEN last.

## Historical completed Task 4: Duplicate/content/image controls

**HISTORICAL COMPLETED TASK EXECUTION RECORD — NO CURRENT EXECUTION EFFECT.**
The normative behavior clauses below remain frozen contract requirements. All
Task 4 checklist execution was completed and is not a current next step.

**Files:**
- Modify: `tests/integration/test_ingest_preflight.py`
- Modify: `src/joy_m2/ingest/preflight.py`

- [x] **HISTORICAL COMPLETED Step 1: Independent negative controls added**

The completed negative-control set included one test per baseline/batch ID
collision, fragment collision, normalized-text
collision, conflicting source locator, missing image, image path/digest conflict,
orphan image, unknown primary type/tag, unsupported MMD/MMD.ZIP/PDF, and
malformed item.
Test `missing_from_source` succeeds only with empty solutions. Test adaptations
require stable reference/evidence and remain non-blocking warning-classification
evidence in `report.adaptations`, not issues or exact-duplicate bypasses. The
deterministic Task 9A rule is exact:

- proposed ID collision is blocking and never adaptation;
- source locator and `source_fragment_hash` must both resolve uniquely to the
  same one baseline `reference_question_id`;
- candidate and reference normalized-original-text digests must differ;
- no identity signal may resolve to another question;
- `adaptation_kind` is `"adapted"`, reason is exactly
  `stable_source_identity_matches_with_transformed_text`, and evidence is exactly
  `matched=source_locator+source_fragment_hash;candidate_normalized_text_sha256=<lowercase-64-hex>;reference_normalized_text_sha256=<lowercase-64-hex>`.

Therefore a proposed-ID collision or any competing-reference identity signal
makes the adaptation predicate false. The candidate emits no `ImportAdaptation`
and follows `collision_candidate_id`, `duplicate_ambiguous`, or the exact
applicable blocking-collision path. The only approved adaptation-plus-blocker
representative is an independent additional image binding at the same logical
path/role with a conflicting SHA. Locator/fragment/normalized signals still
identify the one adapted reference, while the additional image evidence emits
`collision_image_sha256`; retain both that issue and the adaptation, classify the
candidate rejected, and block the report.

If normalized text also matches the one reference, classify exact duplicate.
Multiple reference IDs are ambiguous/blocking. Stable-sort adaptations by
exactly `(candidate_id, reference_question_id, adaptation_kind, evidence,
reason)`.

The completed checkpoint also added these independent RED controls:

1. adaptation only produces the exact report carrier, produces no
   `ImportIssue` or `report.warnings` entry, and status remains
   `READY FOR USER IMPORT APPROVAL`;
2. adaptation evidence/kind/reference/reason mutation changes
   `preflight_sha256`;
3. adaptation plus the independent additional-image SHA blocker retains the
   adaptation and `collision_image_sha256`, rejects the candidate, and blocks the
   report;
4. adaptation-like signals plus a proposed-ID collision emit no adaptation,
   emit `collision_candidate_id`, reject the candidate, and block the report;
5. adaptation-like signals reaching competing references emit no adaptation and
   follow the approved ambiguous/rejected path;
6. exact duplicate is never classified as adaptation;
7. an adaptation-only candidate has an empty issue set, remains
   `new_candidate`, and is READY.

- [x] **HISTORICAL COMPLETED Step 2: Behavior RED proved**

The integration tests were run, and each new test failed for its missing
production check before implementation.

- [x] **HISTORICAL COMPLETED Step 2.5: C4 SIGNAL-SHAPE ALIGNMENT — COMPLETED / GREEN**

**HISTORICAL COMPLETED STEP — NO CURRENT EXECUTION EFFECT.** This checkpoint was
completed. The non-duplicate authority docs passed review and were
committed, the checkpoint received explicit authorization, and private raw-
signal construction was aligned to preserve the exact shapes frozen above:
canonical relative paths for malformed/top-level input; relative path plus a
zero-based exact integer index for invalid records; valid raw candidate ID,
relative path, and role for missing images after structural/basic validation
but before, and without, typed candidate construction; and path-only orphan
reference identity. Invalid records emitted no missing-image or later
candidate-level signal. Missing-image records constructed no typed candidate
and did not reach C5 matching, duplicate/collision, adaptation, or
classification. The checkpoint did not classify candidates or construct
`ImportIssue`, report, or result. Its independent review passed, the checkpoint
was committed, and C5 was subsequently authorized and implemented.

- [x] **HISTORICAL COMPLETED Step 3: Deterministic issue collection implemented**

The implementation collected every per-record issue and stable-sorted by exactly:

```python
(issue.proposed_question_id or "", issue.code, issue.field, issue.evidence)
```

It did not silently deduplicate records or issues.

After the C4 SIGNAL-SHAPE ALIGNMENT checkpoint passed independent review and
was committed, C5 received explicit authorization and converted all eight C4
raw signals into the exact formal non-duplicate issues above. The existing
`test_candidate_json_parsing_accepts_only_exact_canonical_record_objects` locks
`malformed_candidate_json`, `invalid_candidate_top_level`, and
`invalid_candidate_record` as structured BLOCKED results. The existing
`missing_image` behavior is likewise a structured `ImportIssue`/BLOCKED result,
not an early `PipelineError`. The existing
`test_missing_orphan_images_and_unknown_taxonomy_are_blockers` locks
`missing_image`, `orphan_image`, `unknown_primary_type`, and `unknown_tag`; the
existing `test_unsupported_mmd_mmd_zip_and_pdf_are_blockers` locks
`unsupported_source_format`. These use the existing `ImportIssue` carrier and
require no new public API. If another C4 raw signal needs an issue but has no
approved code, field, evidence object, scope, count, and digest semantics, stop
with an authority gap rather than inventing a code.

Issue `evidence` that identifies an input file is limited to a canonical
package-relative path plus stable source locator. Reject/normalize away any
absolute path, cwd, package/temp root, machine user, OS root, or runtime
directory before constructing authority/report evidence.

Exact and ambiguous collisions remain blocking issues. Never merge candidates
automatically.

- [x] **HISTORICAL COMPLETED Step 4: Focused GREEN passed**

Both Task 9A test modules passed at that completed checkpoint.

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

Derive `manifest_sha256` from typed logical authority, never from source
manifest bytes:

```python
sha256(
    canonical_json_bytes(manifest_logical_projection) + b"\n"
).hexdigest()
```

The exact projection contains `schema_version`, `batch_id`, `project`, `module`,
`chapter`, `target_release_version`, `candidate_records`, `source_files`,
`answer_files`, `image_files`, `teacher_notes_files`, `common_errors_files`,
`language_policy`, `split_policy`, `difficulty_policy`, `tag_policy`,
`answer_policy`, and `explanation_policy`. Every file-array entry is the exact
object `relative_path`, `sha256`, `size_bytes`, `kind`; all six arrays retain
their approved manifest semantic order. Use the maintained UTF-8 canonical JSON
serializer with sorted object keys, compact separators and
`ensure_ascii=False`; exact-type validation excludes NaN/Infinity. Append
exactly one LF byte. Zero LF, platform newline, or two LF is invalid. Exclude
absolute paths, `package_root`, cwd, temporary/repository roots, runtime
metadata, repr, and memory identity.

Before production digest work, add an independent literal manifest oracle that
constructs this projection by hand and compares the exact SHA-256. Mutating the
target version, any policy scalar, or `candidate_records` order must change the
digest. Separately mutate one representative file entry's `relative_path`,
`sha256`, `size_bytes`, and `kind`; every mutation must change the digest. The
same exact four-field projection rule covers all six file groups. Changing a
logical relative path is digest-relevant, while moving an otherwise identical
logical manifest beneath another absolute root is not.

Lock `preflight_sha256` to SHA-256 over a canonical object with exactly these
top-level keys:

```text
schema, batch_id, target_release_version, baseline, manifest_policies,
candidate_record_order, file_evidence, candidates, issues,
duplicate_classifications, image_evidence, report
```

The projections are exact. Every dataclass/carrier becomes a named-key JSON
object, never a positional array; only an authority field that is itself a
sequence becomes an array. Optional absence is `null`, empty sequences/mappings
are `[]`/`{}`, legal empty text is `""`, and no key is omitted instead of
`null`. Booleans encode as JSON booleans, exact integers as JSON numbers; bool
cannot satisfy int and floats/NaN/Infinity are forbidden.

- `schema=task9-preflight-v1`; `batch_id` is the manifest string; target is
  `V1.19`.
- `baseline` has exactly `release_version`, `schema_version`, `question_count`,
  `sha256`, `size_bytes`, `kind`.
- `manifest_policies` has exactly `schema_version`, `project`, `module`,
  `chapter`, `language_policy`, `split_policy`, `difficulty_policy`,
  `tag_policy`, `answer_policy`, `explanation_policy`.
- `candidate_record_order` is the manifest-ordered array of canonical relative
  path strings.
- `file_evidence` is sorted by `relative_path`; every entry is the exact object
  `{relative_path, sha256, size_bytes, kind}` with no extra/root key.
- `candidates` is in manifest semantic order. Every entry is the exact object
  with keys `proposed_question_id`, `source_id`, `source_question_number`,
  `source_section`, `source_fragment_hash`, `normalized_text_sha256`,
  `question_text_original`, `question_text_zh`, `translation_status`,
  `translation_evidence`, `solution_original`, `solution_verified`,
  `answer_status`, `explanation_text`, `explanation_status`,
  `explanation_evidence`, `image_paths`, `image_sha256s`, `image_roles`,
  `primary_type`, `tags`, `tag_status`, `difficulty_level`,
  `difficulty_status`, `enrichment_status`.
- `issues` contains exact objects `{code, severity, proposed_question_id, field,
  evidence}` stable-sorted by `(proposed_question_id or "", code, field,
  evidence)`.
- `duplicate_classifications` is in candidate order. Each exact object is
  `{candidate_id, classification, reference_question_id, evidence}`;
  classification is `new_candidate | duplicate | rejected`, and the reference/
  evidence values are both `null` for new candidates. Duplicate uses its unique
  reference and `duplicate_exact` evidence. A non-ambiguous rejection that
  retains one unique `duplicate_exact` relationship retains that duplicate
  reference/evidence. Every other non-ambiguous rejection uses the first
  blocking issue evidence under approved issue order and that issue's unique
  reference when its schema contains one, otherwise `null`; an ambiguous
  rejection uses `null` reference plus `duplicate_ambiguous` evidence.
  Adaptation never appears here.
- `image_evidence` is candidate order then declared image position. Each exact
  object is `{proposed_question_id, relative_path, sha256, size_bytes, kind,
  role}` with logical path and no formal destination/root.
- `report` has every `ImportPreflightReport` key except `preflight_sha256`:
  `batch_id`, `status`, `manifest_sha256`, `baseline_version`, `before_count`,
  `target_release_version`, `detected_count`, `new_candidate_count`,
  `duplicate_count`, `rejected_count`, `ambiguous_count`, `approved_count`,
  `projected_after_count`, `readable_files`, `unreadable_files`,
  `unsupported_files`, `teacher_notes_file_count`, `common_errors_file_count`,
  `ambiguous_splits`, `missing_answers`, `missing_explanations`,
  `incomplete_enrichments`, `missing_images`, `orphan_images`, `level_counts`,
  `proposed_ids`, `adaptations`, `warnings`, `blocking_errors`. File lists use
  relative-path order; candidate/proposed/missing/ambiguous arrays use candidate
  order; `level_counts` is an ascending array of two-integer arrays; blocker
  arrays retain issue order. `warnings` contains only approved warning issue
  codes; Task 9A currently has none, so adaptations do not add entries and an
  adaptation-only fixture uses `[]`. Each adaptation is the exact object
  `{candidate_id, reference_question_id, adaptation_kind, evidence, reason}`
  sorted by `(candidate_id, reference_question_id, adaptation_kind, evidence,
  reason)`.

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

- Construct at least one frozen fixture containing non-empty candidates,
  provenance, issues, image evidence, duplicate/adaptation evidence, and count
  closure. Build the exact approved 12-key expected payload independently from
  fixture authority, serialize it with `canonical_json_bytes`, and compare its
  digest with the production result.
- Do not capture a production payload and hash it back as expected. Do not use a
  production projection helper as the sole expected oracle. Only the maintained
  canonical serializer may be shared.
- Mutation-lock every critical projection: removing or changing `issues`,
  `image_evidence`, `candidates`, provenance, duplicate classifications,
  adaptations, counts, or baseline projection must fail at least one test.
  Explicitly demonstrate `issues` deletion and `image_evidence` deletion each
  fail independently.

- Use the following complete literal two-candidate oracle over the frozen
  497-row baseline. These exact file bytes are inputs (the image literal is
  hexadecimal); SHA-256 and size are shown so no production helper is needed:

  | relative path | exact bytes | SHA-256 | size | kind |
  | --- | --- | --- | ---: | --- |
  | `records/candidates.json` | canonical JSON block below plus one LF | `6c1ca2a9518701a452218700f181cecbaef4161614cf5b317f075adf7761aa27` | 2148 | `candidate_json` |
  | `source/literal.txt` | `literal source evidence\n` | `a24b2e6c1a00a35cc9b513831e223de4990d5e6ed62d89700e32772bfca37c29` | 24 | `source` |
  | `answers/answer.txt` | `literal answer evidence\n` | `d5eaf1ac88ec856434544d132e09b6ff4008e38c2599f8f58d84a90b5fc5dd0d` | 24 | `answer` |
  | `images/diagram.png` | hex `89504e470d0a1a0a5441534b392d4c49544552414c2d494d414745` | `a7b6855df3f8ceacabbf61e15afa4a33af7a652f8df8dae79b1d1b5fd8c87851` | 27 | `image` |
  | `teacher-notes/notes.txt` | `literal teacher note\n` | `4268dcf4d4b1d694b06c37edf71a52baecf0d80b5c57dc652d0c6a6e1f8650f5` | 21 | `teacher_notes` |
  | `common-errors/errors.txt` | `literal common error\n` | `1cfe2bd273ee917428a23d5aab07c63deaf20c03ca61dbbaebbe028b070f1bf0` | 21 | `common_errors` |

  The exact `records/candidates.json` bytes are the UTF-8 bytes of this one-line
  canonical JSON array followed by one LF; it contains every approved caller-
  supplied raw-record key and intentionally omits only the two derived fields
  `normalized_text_sha256` and `image_sha256s`:

  ```json
  [{"answer_status":"source_provided","difficulty_level":1,"difficulty_status":"source_provided","enrichment_status":"complete","explanation_evidence":"source:source/literal.txt#new-explanation","explanation_status":"source_present","explanation_text":"Subtract 1 from both sides.","image_paths":["images/diagram.png"],"image_roles":["question"],"primary_type":"代数","proposed_question_id":"TASK9-NEW-001","question_text_original":"  Solve   x + 1 = 2.\r\nShow work.  ","question_text_zh":"求解 x + 1 = 2，并写出步骤。","solution_original":"x = 1","solution_verified":"x = 1","source_fragment_hash":"7ca9b7902bf8efd929145e64c5d4a1aa11b2da06028e4e2123026a09da640e89","source_id":"M2QD-DIFFERENTIATION-APPLICATIONS","source_question_number":"EXAMPLE-Q1","source_section":"教材例题","tag_status":"source_provided","tags":["一元一次方程"],"translation_evidence":"ai-proposal-sha256:e970c7b1f1c075668394b0519806a72283566a7a13b565700d1b2fc733baf7af","translation_status":"ai_proposed"},{"answer_status":"source_provided","difficulty_level":3,"difficulty_status":"source_provided","enrichment_status":"complete","explanation_evidence":"source:source/literal.txt#dup-explanation","explanation_status":"source_present","explanation_text":"使用导数斜率与点斜式。","image_paths":[],"image_roles":[],"primary_type":"切线与法线","proposed_question_id":"TASK9-DUP-001","question_text_original":"Consider the curve $C: y=26-\\frac{108}{x}$ ,where $0<x<20$ .\n(a) Find $\\frac{d y}{d x}$ .\n(b) If a tangent $L$ to $C$ passes through the point（ 10,20 ）,find the equation of $L$ .","question_text_zh":"考虑曲线并求指定切线。","solution_original":"见冻结来源解答。","solution_verified":"见冻结来源解答。","source_fragment_hash":"7ca9b7902bf8efd929145e64c5d4a1aa11b2da06028e4e2123026a09da640e89","source_id":"M2QD-DIFFERENTIATION-APPLICATIONS","source_question_number":"EXAMPLE-Q1","source_section":"教材例题","tag_status":"source_provided","tags":["过指定点的切线","切点未知"],"translation_evidence":"source:source/literal.txt#dup-translation","translation_status":"source_present"}]
  ```

  `TASK9-NEW-001.question_text_original` is exactly
  `"  Solve   x + 1 = 2.\r\nShow work.  "`. The approved normalization yields
  exactly `"Solve x + 1 = 2.\nShow work."` and
  `normalized_text_sha256=4e33fd8a11eba010d219e342864522608cede6843138f4b40bf2f50346b01b29`.
  `TASK9-DUP-001` uses the literal frozen reference text embedded in the payload
  below and has
  `normalized_text_sha256=04c2b5df26e1f6440412a97203a7a2894819069c9a878493389dcb53f8d9180a`.

  The complete logical manifest projection is this literal JSON object:

  ```json
  {"answer_files":[{"kind":"answer","relative_path":"answers/answer.txt","sha256":"d5eaf1ac88ec856434544d132e09b6ff4008e38c2599f8f58d84a90b5fc5dd0d","size_bytes":24}],"answer_policy":"preserve_source_answer_identity","batch_id":"TASK9-LITERAL-BATCH-001","candidate_records":[{"kind":"candidate_json","relative_path":"records/candidates.json","sha256":"6c1ca2a9518701a452218700f181cecbaef4161614cf5b317f075adf7761aa27","size_bytes":2148}],"chapter":"Literal Oracle","common_errors_files":[{"kind":"common_errors","relative_path":"common-errors/errors.txt","sha256":"1cfe2bd273ee917428a23d5aab07c63deaf20c03ca61dbbaebbe028b070f1bf0","size_bytes":21}],"difficulty_policy":"joy_level_1_5","explanation_policy":"source_or_independently_verified_with_identity","image_files":[{"kind":"image","relative_path":"images/diagram.png","sha256":"a7b6855df3f8ceacabbf61e15afa4a33af7a652f8df8dae79b1d1b5fd8c87851","size_bytes":27}],"language_policy":"preserve_source_and_store_reviewed_chinese_separately","module":"M2","project":"Joy M2 AI Database","schema_version":"task9-import-manifest-v1","source_files":[{"kind":"source","relative_path":"source/literal.txt","sha256":"a24b2e6c1a00a35cc9b513831e223de4990d5e6ed62d89700e32772bfca37c29","size_bytes":24}],"split_policy":"one_complete_question_per_record","tag_policy":"controlled_primary_type_and_tags","target_release_version":"V1.19","teacher_notes_files":[{"kind":"teacher_notes","relative_path":"teacher-notes/notes.txt","sha256":"4268dcf4d4b1d694b06c37edf71a52baecf0d80b5c57dc652d0c6a6e1f8650f5","size_bytes":21}]}
  ```

  Its expected `manifest_sha256` over those canonical bytes plus one LF is
  `b5a0ae6597028c48c6f7cdc81bd7e67d61dd369cbf96d7c6a4e96efd73984c5d`.
  The exact `duplicate_exact` evidence string is
  `{"candidate_id":"TASK9-DUP-001","normalized_text_sha256":"04c2b5df26e1f6440412a97203a7a2894819069c9a878493389dcb53f8d9180a","reference_question_id":"M2QD-DA-EXAMPLE-Q1"}`.

  The complete expected 12-key payload is the following literal JSON. This is
  not a template: every key and value participates exactly as written.

  ```json
  {
    "baseline":{"kind":"sqlite","question_count":497,"release_version":"V1.18","schema_version":"complete-question-v1.0","sha256":"fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7","size_bytes":9363456},
    "batch_id":"TASK9-LITERAL-BATCH-001",
    "candidate_record_order":["records/candidates.json"],
    "candidates":[
      {"answer_status":"source_provided","difficulty_level":1,"difficulty_status":"source_provided","enrichment_status":"complete","explanation_evidence":"source:source/literal.txt#new-explanation","explanation_status":"source_present","explanation_text":"Subtract 1 from both sides.","image_paths":["images/diagram.png"],"image_roles":["question"],"image_sha256s":["a7b6855df3f8ceacabbf61e15afa4a33af7a652f8df8dae79b1d1b5fd8c87851"],"normalized_text_sha256":"4e33fd8a11eba010d219e342864522608cede6843138f4b40bf2f50346b01b29","primary_type":"代数","proposed_question_id":"TASK9-NEW-001","question_text_original":"  Solve   x + 1 = 2.\r\nShow work.  ","question_text_zh":"求解 x + 1 = 2，并写出步骤。","solution_original":"x = 1","solution_verified":"x = 1","source_fragment_hash":"7ca9b7902bf8efd929145e64c5d4a1aa11b2da06028e4e2123026a09da640e89","source_id":"M2QD-DIFFERENTIATION-APPLICATIONS","source_question_number":"EXAMPLE-Q1","source_section":"教材例题","tag_status":"source_provided","tags":["一元一次方程"],"translation_evidence":"ai-proposal-sha256:e970c7b1f1c075668394b0519806a72283566a7a13b565700d1b2fc733baf7af","translation_status":"ai_proposed"},
      {"answer_status":"source_provided","difficulty_level":3,"difficulty_status":"source_provided","enrichment_status":"complete","explanation_evidence":"source:source/literal.txt#dup-explanation","explanation_status":"source_present","explanation_text":"使用导数斜率与点斜式。","image_paths":[],"image_roles":[],"image_sha256s":[],"normalized_text_sha256":"04c2b5df26e1f6440412a97203a7a2894819069c9a878493389dcb53f8d9180a","primary_type":"切线与法线","proposed_question_id":"TASK9-DUP-001","question_text_original":"Consider the curve $C: y=26-\\frac{108}{x}$ ,where $0<x<20$ .\n(a) Find $\\frac{d y}{d x}$ .\n(b) If a tangent $L$ to $C$ passes through the point（ 10,20 ）,find the equation of $L$ .","question_text_zh":"考虑曲线并求指定切线。","solution_original":"见冻结来源解答。","solution_verified":"见冻结来源解答。","source_fragment_hash":"7ca9b7902bf8efd929145e64c5d4a1aa11b2da06028e4e2123026a09da640e89","source_id":"M2QD-DIFFERENTIATION-APPLICATIONS","source_question_number":"EXAMPLE-Q1","source_section":"教材例题","tag_status":"source_provided","tags":["过指定点的切线","切点未知"],"translation_evidence":"source:source/literal.txt#dup-translation","translation_status":"source_present"}
    ],
    "duplicate_classifications":[{"candidate_id":"TASK9-NEW-001","classification":"new_candidate","evidence":null,"reference_question_id":null},{"candidate_id":"TASK9-DUP-001","classification":"duplicate","evidence":"{\"candidate_id\":\"TASK9-DUP-001\",\"normalized_text_sha256\":\"04c2b5df26e1f6440412a97203a7a2894819069c9a878493389dcb53f8d9180a\",\"reference_question_id\":\"M2QD-DA-EXAMPLE-Q1\"}","reference_question_id":"M2QD-DA-EXAMPLE-Q1"}],
    "file_evidence":[{"kind":"answer","relative_path":"answers/answer.txt","sha256":"d5eaf1ac88ec856434544d132e09b6ff4008e38c2599f8f58d84a90b5fc5dd0d","size_bytes":24},{"kind":"common_errors","relative_path":"common-errors/errors.txt","sha256":"1cfe2bd273ee917428a23d5aab07c63deaf20c03ca61dbbaebbe028b070f1bf0","size_bytes":21},{"kind":"image","relative_path":"images/diagram.png","sha256":"a7b6855df3f8ceacabbf61e15afa4a33af7a652f8df8dae79b1d1b5fd8c87851","size_bytes":27},{"kind":"candidate_json","relative_path":"records/candidates.json","sha256":"6c1ca2a9518701a452218700f181cecbaef4161614cf5b317f075adf7761aa27","size_bytes":2148},{"kind":"source","relative_path":"source/literal.txt","sha256":"a24b2e6c1a00a35cc9b513831e223de4990d5e6ed62d89700e32772bfca37c29","size_bytes":24},{"kind":"teacher_notes","relative_path":"teacher-notes/notes.txt","sha256":"4268dcf4d4b1d694b06c37edf71a52baecf0d80b5c57dc652d0c6a6e1f8650f5","size_bytes":21}],
    "image_evidence":[{"kind":"image","proposed_question_id":"TASK9-NEW-001","relative_path":"images/diagram.png","role":"question","sha256":"a7b6855df3f8ceacabbf61e15afa4a33af7a652f8df8dae79b1d1b5fd8c87851","size_bytes":27}],
    "issues":[{"code":"duplicate_exact","evidence":"{\"candidate_id\":\"TASK9-DUP-001\",\"normalized_text_sha256\":\"04c2b5df26e1f6440412a97203a7a2894819069c9a878493389dcb53f8d9180a\",\"reference_question_id\":\"M2QD-DA-EXAMPLE-Q1\"}","field":"candidate","proposed_question_id":"TASK9-DUP-001","severity":"blocking"}],
    "manifest_policies":{"answer_policy":"preserve_source_answer_identity","chapter":"Literal Oracle","difficulty_policy":"joy_level_1_5","explanation_policy":"source_or_independently_verified_with_identity","language_policy":"preserve_source_and_store_reviewed_chinese_separately","module":"M2","project":"Joy M2 AI Database","schema_version":"task9-import-manifest-v1","split_policy":"one_complete_question_per_record","tag_policy":"controlled_primary_type_and_tags"},
    "report":{"adaptations":[{"adaptation_kind":"adapted","candidate_id":"TASK9-NEW-001","evidence":"matched=source_locator+source_fragment_hash;candidate_normalized_text_sha256=4e33fd8a11eba010d219e342864522608cede6843138f4b40bf2f50346b01b29;reference_normalized_text_sha256=04c2b5df26e1f6440412a97203a7a2894819069c9a878493389dcb53f8d9180a","reason":"stable_source_identity_matches_with_transformed_text","reference_question_id":"M2QD-DA-EXAMPLE-Q1"}],"ambiguous_count":0,"ambiguous_splits":[],"approved_count":0,"baseline_version":"V1.18","batch_id":"TASK9-LITERAL-BATCH-001","before_count":497,"blocking_errors":["duplicate_exact"],"common_errors_file_count":1,"detected_count":2,"duplicate_count":1,"incomplete_enrichments":[],"level_counts":[[1,1],[3,1]],"manifest_sha256":"b5a0ae6597028c48c6f7cdc81bd7e67d61dd369cbf96d7c6a4e96efd73984c5d","missing_answers":[],"missing_explanations":[],"missing_images":[],"new_candidate_count":1,"orphan_images":[],"projected_after_count":498,"proposed_ids":["TASK9-NEW-001","TASK9-DUP-001"],"readable_files":["answers/answer.txt","common-errors/errors.txt","images/diagram.png","records/candidates.json","source/literal.txt","teacher-notes/notes.txt"],"rejected_count":0,"status":"BLOCKED — IMPORT PREFLIGHT FAILED","target_release_version":"V1.19","teacher_notes_file_count":1,"unreadable_files":[],"unsupported_files":[],"warnings":[]},
    "schema":"task9-preflight-v1",
    "target_release_version":"V1.19"
  }
  ```

  Canonicalize that exact object with the approved UTF-8/sorted-key/compact/
  `ensure_ascii=False` serializer and append exactly one LF. Its independently
  precomputed expected `preflight_sha256` is
  `087574a8af6fe28ac65a5b5810794952044cb5f0778ed3492d1e7819a4be33c2`.
  The expected issue array is exactly the one object shown: the
  `duplicate_exact` blocker for `TASK9-DUP-001`. The adaptation for
  `TASK9-NEW-001` exists only in `report.adaptations`, does not enter `issues`
  or `report.warnings`, and the equal locator/fragment/text constituent signals
  produce no additional collision issue.

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

### Historical completed Task 9A RED gate inventory

**HISTORICAL COMPLETED PHASE — NO LONGER CURRENT EXECUTION AUTHORITY.** The
focused TDD sequence established all 28 contracts before their respective
minimum implementation steps; import/setup/fixture/environment failures were
not valid RED evidence:

The preliminary Stage 3A API-existence RED is a separate testability gate and
does not replace, merge, or delete any item below. Stage 3B establishes the
applicable behavior REDs only after the importable scaffold exists.

1. exact seven-carrier fields/order/types/frozen semantics;
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
24. manifest-declared candidate reorder semantics and digest change;
25. exact manifest runtime type and V1.19 target rejected before any I/O;
26. exact adaptation/duplicate/ambiguous precedence and adaptation-only READY;
27. exact public `ImportAdaptation`/report field/order/digest binding;
28. independent 12-key digest oracle and critical-projection mutation locks.

## Historical Task 3 Stage 3B entry policy

**HISTORICAL COMPLETED PHASE — NO LONGER CURRENT EXECUTION AUTHORITY.**

Task 1–2 and the adaptation-model checkpoint were completed and committed.
Stage 3A then established the API/signature RED and created the exact
immediate-`NotImplementedError` scaffold in
`src/joy_m2/ingest/preflight.py`, and made the single signature test GREEN.
The subsequent Stage 3B restart established the behavior suite and proceeded
dependency group by dependency group. These are completed historical TDD audit
records and must not be replayed as the current entry. The production asset is
no longer the immediate scaffold. C1 is GREEN; C2 is GREEN; C3 is GREEN; C4 is
GREEN; C4 SIGNAL-SHAPE ALIGNMENT is COMPLETED / GREEN; the C5 classification
layer is COMPLETED / GREEN; and C6 remains BLOCKED / NOT IMPLEMENTED.
`src/joy_m2/ingest/__init__.py` still does not exist and remains deferred to
Task 5.

The fresh integration baseline is 37 collected, 8 PASS methods, 29 RED methods,
58 failure instances, 0 ERROR, and 0 skip. The only current entry is the file-
integrity authority review and the RED-first sequence frozen above; no Stage 3A
or Stage 3B restart is authorized.

This docs remediation authorizes no behavior RED, production change, import,
writer, V1.19 artifact, promotion, or Task 9B/9C/9D work.

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

- [ ] **Step 4: Complete the remaining Task 3 gates before commit authorization**

The remaining current gates are exactly: file-integrity authority review PASS;
docs commit; test-only migration with valid size-only/SHA-only structured REDs;
separately authorized FILE-INTEGRITY SIGNAL ALIGNMENT; verification that both public
tests advance beyond `PipelineError` but remain RED only at the C6 stop;
independent FILE-INTEGRITY SIGNAL ALIGNMENT review; C6 final-closure
authorization; complete focused
37/37 GREEN; maintained/frozen gates; and final independent implementation
review. Completed Stage 3A/Stage 3B work is not rerun. Only after these gates and
explicit commit authorization may the completed Task 9A implementation stage
exactly six files and use:

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

Current checkpoint: Task 1–2 and the adaptation model are completed/committed;
historical Stage 3A/Stage 3B entry work is completed; C1 is `GREEN`; C2 is
`GREEN`; C3 is `GREEN`; C4 is `GREEN`; C4 SIGNAL-SHAPE ALIGNMENT is `COMPLETED
/ GREEN`; the C5 classification layer is `COMPLETED / GREEN`; and C6 is
`BLOCKED / NOT IMPLEMENTED`. The
completed C4 SIGNAL-SHAPE ALIGNMENT is distinct from the not-yet-executed
FILE-INTEGRITY SIGNAL ALIGNMENT. Current integration baseline:
37 collected, 8 PASS methods, 29 RED methods, 58 failure instances, 0 ERROR,
0 skip. The 16-code taxonomy is closed; only its file-integrity execution
sequence is in authority review. No writer, V1.19 artifact, imported question,
or promotion exists.

The sole current next sequence is: authority review PASS; docs commit; test-only
integrity migration; independent valid size-only RED; independent valid SHA-only
RED; separately authorized FILE-INTEGRITY SIGNAL ALIGNMENT; public RED
advancement to the C6-only stop; independent FILE-INTEGRITY SIGNAL ALIGNMENT
review; C6 authorization and formal closure; 37/37 GREEN; maintained/frozen
gates; final independent review; implementation commit.

`READY FOR TASK 9A FILE-INTEGRITY AUTHORITY REVISION REVIEW`
