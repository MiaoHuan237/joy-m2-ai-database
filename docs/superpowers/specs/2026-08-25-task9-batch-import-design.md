# Task 9 Batch Import Workflow Recovery Design

Status: `TASK 9A TDD SCAFFOLD SEQUENCING REMEDIATION IN REVIEW`

Date: 2026-08-25 (Asia/Shanghai)

## 1. Purpose and boundary

Task 9 restores a maintained, preflight-first workflow for future DSE M2
complete-question batches. This design round imports no questions and authorizes
no database write, CLI, App/API, worksheet feature, Task 8C, or promotion.

Task 8B remains `CLOSED / PASS`. Task 9 preserves these authorities:

- SQLite is the sole formal source of truth.
- `releases/V1.18/` and `data/baselines/V1.18/` are immutable.
- One complete question is one record; subparts stay inside it.
- Existing IDs, source/text/answer identity, difficulty, tags, images,
  corrections, selection state, and compatibility objects cannot change.
- Upload is not approval. Formal changes require a new version, migration,
  audit report, Joy approval, hashes, verification, and rollback package.

## 2. Recovered baseline

- branch: `task8b/pipeline-migration`
- HEAD: `2f14a99cde2199945194cdc57bd6f3d622a3fea1`
- upstream: `origin/task8b/pipeline-migration`, ahead/behind `0/0`
- pre-design worktree/staging/untracked: clean / clean / 0
- formal version: `V1.18`
- approved next import target identity: `V1.19` (preflight identity only)
- formal SQLite:
  `releases/V1.18/Joy_M2_Complete_Question_DB_V1_18.sqlite3`
- sole complete-question truth table: `complete_questions_v2`, 497 rows
- compatibility table `questions`: 1,517 rows; this is not the business count
- answer identities: 392 `source_provided`, 71 `ai_solved_verified`, 34
  `missing_from_source`
- integrity: `ok`; foreign-key errors: 0

All 497 formal rows have unique `question_id`, `source_order`, and
`source_fragment_hash`. They are the protected baseline for Task 9.

## 3. Current real path

The Task 8B path is:

```text
explicit frozen-profile candidate JSON
→ AuditRequest file/baseline preflight
→ exact V1.17 or V1.18 parsing
→ audit and AuditResult / AuditedBatch
→ temporary SQLite copy and profile-specific database build
→ database verification → export → candidate verification
→ separate Joy-bound promotion
```

This is deterministic historical replay/release, not a general upload path.
There is no maintained implementation for:

```text
source package → source parser → split proposal → enrichment proposal
→ import preflight → report-bound import approval → incremental insert
```

`audit_batch()` and `build_database()` are frozen to V1.17/V1.18 shapes,
counts, baselines, metadata, and import-run identities. Release public contracts
also reject future versions. They cannot silently serve Task 9.

## 4. Capability classification

### A. EXISTING — CAN BE REUSED

- `ArtifactRef`, audit evidence/results, deterministic issues, and PASS gate.
- exact normalized-text duplicate primitive.
- asset-root containment and missing-image checks.
- `AuditedQuestion` content vocabulary and answer-identity rules.
- atomic database pattern: temporary baseline copy, `BEGIN IMMEDIATE`,
  integrity/FK verification, atomic replace, cleanup.
- deterministic exports, hashes, manifests, ZIP, and verification.
- `data/staging/` as disposable candidate space.

### B. EXISTING — NEEDS ADAPTATION

- audit profiles and baseline/count validation;
- duplicate checks, which need ID/source/fragment/image identity coverage;
- image handling, which lacks input inventory, hash-bound copy, and rollback;
- database metadata/import run/count logic, currently version-coupled;
- export/release, reusable only after a future-version contract is approved.

### C. MISSING

- typed import manifest and package inventory;
- MMD, MMD.ZIP, PDF, and Mathpix parsers;
- complete-question split and enrichment draft models;
- deterministic import preflight report and report-bound approval;
- incremental identity index and existing-row preservation report;
- future-version database profile/writer and import report;
- formal policy for teacher notes and common errors.

### D. LEGACY ONLY

- fixed Task 5/6 builders and version-coupled import runs;
- historical MMD/Mathpix provenance in existing records;
- compatibility fields `questions.common_errors` and
  `questions.teaching_advice`.

Legacy remains an oracle and must not be imported by Task 9 production.

## 5. Current supported inputs

Maintained code accepts only:

- UTF-8 JSON record arrays with exact frozen V1.17/V1.18 profiles;
- explicit baseline SQLite/manifest `ArtifactRef` values;
- an explicit asset root for referenced-image existence checks.

It does not parse `.mmd`, `.mmd.zip`, PDF, Mathpix archives,
`IMPORT_MANIFEST.md`, or arbitrary source/answer/notes layouts. Release ZIP
support is packaging, not ingestion.

## 6. Formal fields

The current V2 formal row supports:

```text
question_id, source_id, source_question_number, source_section, source_file,
source_member, source_sha256, source_member_sha256, source_fragment_hash,
source_page, solution_source_file, solution_source_member,
solution_source_member_sha256, question_text_original, question_text_zh,
question_text_zh_reviewed, question_latex, marks_total, year,
image_paths_json, solution_original, solution_verified, answer_status,
answer_verification_status, official_marking_available, primary_type,
tags_json, difficulty_level, difficulty_evidence,
difficulty_dimensions_json, old_difficulty, old_difficulty_label,
old_tags_json, question_review_status, formula_review_status,
image_review_status, answer_review_status, correction_status,
corrections_json, duplicate_status, duplicate_reference,
duplicate_evidence, audit_notes, review_checks_json, unresolved_issues_json,
record_status, joy_approval, audited_at, approved_at, schema_version,
selectable, source_heading, task4_processed_at, task4_resolution, source_order
```

| Requirement | Current representation |
|---|---|
| source identity | source IDs/locations and source/member/fragment hashes |
| source English/original | `question_text_original` |
| reviewed Chinese | `question_text_zh`, `question_text_zh_reviewed` |
| answer/explanation | solution fields plus answer identity/status |
| Level 1–5 | difficulty level/evidence/dimensions |
| type/topic | one `primary_type` and controlled tags |
| module | project-level M2 invariant; **NOT CURRENTLY A FORMAL ROW FIELD** |
| subtopic | only controlled tags; **NOT A DEDICATED FORMAL FIELD** |
| teacher notes | **NOT CURRENTLY A FORMAL V2 FIELD** |
| common errors | **NOT CURRENTLY A FORMAL V2 FIELD** |
| images | `image_paths_json` and image review status |

`audit_notes` is audit evidence, not generic teacher notes. Legacy columns do
not authorize maintained writes or a schema expansion.

## 7. Missing answers

Existing authority permits `missing_from_source` records. Both solution fields
stay empty; student selection remains permitted; teacher output discloses the
status. A later independent solution requires separate review and cannot be
called a source/official answer. Task 9 must not reclassify the existing 34
records or change the V1.18 complete/incomplete definition. Task 9A separately
reports answer present, `missing_from_source`, explanation missing, and
enrichment incomplete. AI may later propose an answer/explanation, but a
proposal is never source-authenticated evidence.

## 8. Recommended architecture

Options considered:

1. **Maintained ingest front end (recommended):** a small `joy_m2.ingest`
   boundary produces a canonical draft and preflight report, then a separately
   approved future profile adapts the existing database authority.
2. Wrap the V1.18 replay profile: rejected because counts/metadata/baselines
   would be false and frozen authority would blur.
3. Restore legacy builders: rejected because it creates a second writer and
   hidden-path authority.

Recommended flow:

```text
explicit source package + import_manifest.json
→ deterministic inventory/digests
→ explicitly supported adapter
→ complete-question drafts
→ compact baseline identity/duplicate checks
→ immutable ImportPreflightReport
→ USER APPROVED IMPORT BATCH <batch_id> <preflight_sha256> V1.19
→ maintained audit
→ temporary baseline copy and one transaction
→ post-import verification/exports
→ candidate only; promotion remains separate
```

## 9. Minimal typed manifest

No maintained import manifest exists. Task 9 proposes canonical
`import_manifest.json`; Markdown is a derived report, not machine authority.

Exact ordered fields:

```text
schema_version, batch_id, project, module, chapter, target_release_version,
candidate_records, source_files, answer_files, image_files,
teacher_notes_files, common_errors_files, language_policy, split_policy,
difficulty_policy, tag_policy, answer_policy, explanation_policy
```

Frozen Task 9A policies:

- schema: `task9-import-manifest-v1`
- project/module: `Joy M2 AI Database` / `M2`
- split: `one_complete_question_per_record`
- difficulty: `joy_level_1_5`
- tags: `controlled_primary_type_and_tags`
- answers: `preserve_source_answer_identity`
- language: `preserve_source_and_store_reviewed_chinese_separately`
- explanation: `source_or_independently_verified_with_identity`

The explanation policy defines what may later be treated as authoritative. It
does not erase an AI proposal: Task 9A may carry `ai_proposed` evidence, but it
remains unverified/incomplete and cannot be relabeled source-present or verified.

`target_release_version` is exactly `"V1.19"`. `null`, V1.18, and every other
value are rejected. Task 9A validates only this target identity: it does not
authorize a V1.19 schema/profile, `PRAGMA user_version` change, database build,
release artifact, or promotion. The loader never invents or increments a
version.

Each file entry is a canonical package-relative POSIX path, lowercase SHA-256,
size, and kind. `ImportFileEvidence.relative_path` is the only file-location
value admitted to typed evidence, reports, or the approval digest. A resolved
filesystem `Path` may be used transiently for containment and byte checks, but
an absolute path, cwd-relative spelling, package-root path, repository root, or
temporary root is never retained as evidence.
Exact Task 9A kinds by manifest group are `candidate_json`, `source`, `answer`,
`image`, `teacher_notes`, and `common_errors`; a file kind must match its group.
Absolute paths, `..`, symlink escape, duplicate paths, undeclared files, and
identity mismatches block. Task 9A parses only a canonical JSON record array.
MMD/MMD.ZIP/PDF may be inventoried but remain unsupported blockers.

Teacher/common-error files are import evidence/enrichment metadata. Task 9A
preserves, hashes, references, and reports their availability, but never maps
them to nonexistent SQLite columns or silently discards them. Formal storage is
deferred to separate schema authority.

## 10. Identity and duplicate policy

Each draft contains an explicit `proposed_question_id`; final IDs are never
derived from mutable text, cwd, discovery order, or AI titles. Approval locks
the proposed ID and preflight digest.

Task 9A represents each canonical candidate in one immutable `ImportCandidate`
carrier with this exact field order and runtime types:

```python
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
```

The exact translation and explanation provenance vocabulary is
`source_present | ai_proposed | verified | missing`. For translation,
`question_text_zh` is the payload; for explanation, `explanation_text` is the
separate payload. `missing` requires an empty payload and `None` evidence;
every other status requires a non-empty payload and non-empty stable evidence.
The two evidence values are canonical
package-relative source locators, content-bound AI proposal identifiers, or
approved review-evidence identifiers with these exact forms:

```text
source:<canonical-relative-path>#<non-empty-stable-locator>
ai-proposal-sha256:<lowercase-64-hex-of-UTF-8-payload>
verified-review-sha256:<lowercase-64-hex-of-approved-review-evidence>
```

They may not contain absolute paths, runtime session/conversation identifiers,
or inferred source authority. A `source:` reference must resolve to declared
input evidence; the two digest forms are identity references, not permission to
perform AI generation or verification.

`source_present` is available only when the input package supplies matching
source evidence. AI output initially has only `ai_proposed` authority,
regardless of quality. Only a future independently approved review action may
produce `verified`; Task 9A carries and validates that status but performs no AI
generation or verification. `answer_status` remains independent and retains
`source_provided | ai_solved_verified | missing_from_source`.
`missing_from_source` still requires both solution fields empty and never
silently grants source authority to an explanation; an AI explanation must be
`ai_proposed`. The answer solution fields and `explanation_text` are independent
payloads; Task 9A never derives either provenance from the other. Changing any
translation/explanation payload, evidence, or status is approval-relevant.

The carrier is preflight evidence only and cannot become a database row or
publication decision. Formal, import-only, and unsupported fields remain
explicitly classified.

`normalized_text_sha256` is derived only from the exact raw/carrier field
`question_text_original`; callers never supply it as authority. The unique
normalization algorithm is:

1. require `type(question_text_original) is str`;
2. apply Unicode NFC normalization;
3. replace CRLF with LF, then replace remaining CR with LF;
4. split on LF;
5. on each line, trim leading and trailing ASCII whitespace characters
   `U+0020`, `U+0009`, `U+000B`, and `U+000C`, then collapse each non-empty
   run of those characters inside the line to one `U+0020` space;
6. remove only leading and trailing empty lines, preserving every interior
   empty line and therefore preserving line-break structure;
7. join the remaining lines with exactly one LF and add no trailing LF.

The algorithm never lowercases, removes punctuation, changes LaTeX delimiters,
rewrites mathematical symbols, or performs semantic rewriting. Its digest is
exactly
`SHA-256(normalized_text.encode("utf-8")).hexdigest()`. Consequently CRLF/LF,
NFC/NFD, harmless surrounding ASCII whitespace, and repeated intra-line ASCII
spaces normalize identically. Case, punctuation, mathematical-symbol,
substantive-word, line-order, and semantic line-break changes remain distinct.

Candidate semantic order is exactly the canonical manifest-declared order:
first the order of `candidate_records` entries, then record-array order inside
each referenced canonical JSON file. If the declared semantic order is
`[q3, q1, q2]`, `ImportPreflightResult.candidates`, report candidate/proposed-ID
projections, duplicate classifications, image projections, and digest payload
retain `[q3, q1, q2]`. Task 9A never reorders candidates by filename, ID, hash,
filesystem traversal, or dictionary iteration. File inventory/evidence is a
separate authority and is canonicalized by `relative_path`; changing
filesystem discovery order cannot change candidate order or the digest.

Preflight reads compact indexes from SQLite, not 497 full records into an AI
prompt:

- `question_id`;
- `(source_id, source_question_number, source_section)`;
- `source_fragment_hash`;
- deterministic normalized-original-text digest;
- declared image digests where present;
- complete `source_order` set.

Blockers include baseline/batch ID collision, fragment/text exact duplicate,
source-locator conflict, image path with different bytes, and mutation of any
protected baseline row or dependent tag/correction identity. Adaptation is not
intrinsic question data and therefore never adds `duplicate_status`,
`duplicate_reference`, or `duplicate_evidence` to `ImportCandidate` or the
canonical raw-record field set. It is separate read-only preflight evidence:

```python
@dataclass(frozen=True)
class ImportAdaptation:
    candidate_id: str
    reference_question_id: str
    adaptation_kind: str
    evidence: str
    reason: str
```

All five fields have exact runtime type `str`, no defaults, and must be
non-empty. The only Task 9A `adaptation_kind` is exactly `"adapted"`; any future
taxonomy requires separate authority. `evidence` and `reason` are
path-independent stable values, never filesystem or runtime locators.

Task 9A derives an adaptation only from deterministic baseline comparison. The
candidate proposed ID must not collide; its stable source locator and
`source_fragment_hash` must both resolve uniquely to the same one baseline
question; its normalized-original-text digest must differ from that reference;
and no identity signal may resolve to a different question. The exact Task 9A
reason is `stable_source_identity_matches_with_transformed_text`. Evidence binds
the matched locator/fragment signals plus candidate and reference normalized-
text digests in this exact path-independent form:

```text
matched=source_locator+source_fragment_hash;candidate_normalized_text_sha256=<lowercase-64-hex>;reference_normalized_text_sha256=<lowercase-64-hex>
```

Semantic similarity alone is never evidence.

A proposed-ID collision makes the adaptation predicate false. For that
candidate, `collision_candidate_id` therefore emits no `ImportAdaptation`,
classifies the candidate `rejected`, and makes the report BLOCKED. Likewise, if
the approved identity signals reach competing references, no adaptation is
emitted; the candidate follows the approved `duplicate_ambiguous` or applicable
blocking-collision path instead.

If the normalized text also matches the single reference, the relationship is
an exact duplicate, not an adaptation. Signals resolving to multiple references
are ambiguous and blocking/rejected. Adaptation is non-blocking
warning-classification evidence only in `report.adaptations` and remains
distinct from both issues and duplicate counts. An adaptation with no
independent candidate-bound blocker may remain
`READY FOR USER IMPORT APPROVAL`. An approved independent candidate-bound
blocker may coexist only when it does not negate the unique-reference adaptation
predicate. In that case the candidate is rejected/BLOCKED while the
adaptation evidence is retained. The representative coexistence case is an
independently conflicting additional image binding described below, not a
proposed-ID collision or competing identity reference.

Adaptation does not project an `ImportIssue`: there is no
`ImportIssue(code="adaptation", ...)`. Its sole authoritative carrier is
`ImportPreflightReport.adaptations`; it is neither a blocking issue nor a
duplicate classification. With no independent candidate-bound blocker, the
candidate remains
`new_candidate`, `issues` may be empty, and the report may remain
`READY FOR USER IMPORT APPROVAL`. `report.warnings` does not copy adaptation
evidence and, because Task 9A currently approves no separate warning issue
code, is the exact empty sequence for adaptation-only input. Any future warning
taxonomy requires separate authority.

All non-adaptation duplicate/collision diagnostics use this closed
duplicate/collision blocking taxonomy; it is not the complete set of Task 9A
blocking `ImportIssue` codes. No runtime-selected code or field spelling is
permitted:

| code | severity | field |
| --- | --- | --- |
| `duplicate_exact` | `blocking` | `candidate` |
| `collision_candidate_id` | `blocking` | `proposed_question_id` |
| `collision_source_locator` | `blocking` | `source_locator` |
| `collision_fragment_sha256` | `blocking` | `source_fragment_hash` |
| `collision_normalized_text_sha256` | `blocking` | `normalized_text_sha256` |
| `collision_image_sha256` | `blocking` | `image_sha256s` |
| `duplicate_ambiguous` | `blocking` | `duplicate` |

Their `ImportIssue.evidence` is never prose. It is the UTF-8 string obtained by
decoding `canonical_json_bytes(exact_object)` with no trailing LF. Object keys
are sorted by that maintained serializer, separators are compact, Unicode is
not ASCII-escaped, and all arrays use the semantic orders below. Absolute
paths, timestamps, machine data, session data, and unordered representations
are forbidden. The exact per-code objects are:

- `duplicate_exact`: `candidate_id`, `reference_question_id`,
  `normalized_text_sha256`.
- `collision_candidate_id`: `candidate_id`, `reference_question_id`,
  `candidate_fragment_sha256`, `reference_fragment_sha256`.
- `collision_source_locator`: `candidate_id`, `candidate_source_locator`,
  `candidate_fragment_sha256`, `reference_question_id`,
  `reference_source_locator`, `reference_fragment_sha256`. Each locator is the
  JSON array `[source_id, source_question_number, source_section]` in that exact
  order.
- `collision_fragment_sha256`: `candidate_id`, `candidate_source_locator`,
  `reference_question_id`, `reference_source_locator`,
  `source_fragment_sha256`; locator arrays use the same exact order.
- `collision_normalized_text_sha256`: `candidate_id`,
  `reference_question_id`, `normalized_text_sha256`.
- `collision_image_sha256`: `candidate_id`, `candidate_image_path`,
  `candidate_image_role`, `candidate_image_sha256`, `reference_question_id`,
  `reference_image_path`, `reference_image_role`, `reference_image_sha256`.
  Both paths are logical canonical relative paths.
- `duplicate_ambiguous`: `candidate_id`, `matches`. `matches` is an array
  stable-sorted by `reference_question_id`; every element has exactly
  `reference_question_id` and `signals`, and `signals` is the sorted unique
  array drawn from `candidate_id`, `source_locator`, `source_fragment_sha256`,
  `normalized_text_sha256`, and `image_sha256`.

Issue ordering remains exactly `(proposed_question_id or "", code, field,
evidence)`. The canonical evidence string makes equal logical diagnostics sort
identically across roots and runtimes. Adaptation remains only the separately
frozen warning-classification evidence in `report.adaptations`; it never enters
`issues`, `duplicate_classifications`, or a blocking duplicate/collision code.

### Non-duplicate blocking import issues

The duplicate/collision taxonomy above retains its existing triggers, fields,
evidence, severity, precedence, suppression, and coexistence rules. It contains
seven codes. The separate closed non-duplicate taxonomy below contains eight
codes. Together they are the complete fifteen-code Task 9A blocking
`ImportIssue` authority; no other blocking code is approved:

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

Every evidence string is exactly
`canonical_json_bytes(exact_object).decode("utf-8")`, with no trailing LF and
the existing sorted-key, compact, `ensure_ascii=False`, path-independent rules.
Evidence excludes absolute paths, package/baseline/cwd/temp/repository roots,
timestamps, parser or validation prose, runtime type names, machine/session
data, and unordered values.

`malformed_candidate_json` is emitted when an approved
`manifest.candidate_records` file cannot be decoded and parsed by the strict
UTF-8 JSON parser. It excludes deferred MMD/MMD.ZIP/PDF inputs, parsed JSON with
the wrong top level, and invalid records within a valid array. Its evidence is
exactly `{relative_path}`.

`invalid_candidate_top_level` is emitted when candidate JSON parses but its top
level is not the approved JSON array. Its evidence is exactly
`{relative_path, expected}`, where `expected` is exactly `"array"`; runtime type
names are forbidden.

`invalid_candidate_record` is emitted once for every zero-based array element
that cannot construct the exact typed `ImportCandidate`, including wrong or
missing keys, wrong scalar/container runtime types, invalid status/payload or
difficulty combinations, and malformed enrichment disclosure. Its evidence is
exactly `{relative_path, record_index}`; `record_index` is an exact non-negative
`int` and `bool` is forbidden. Because no typed candidate exists, its
`proposed_question_id` is always `None`, even when an untrusted record happened
to contain a string resembling an ID. Multiple invalid records are not merged.

The three candidate-input issues above, `missing_image`, `orphan_image`, and
`unsupported_source_format` are package/pre-candidate or file-level blockers.
They create no placeholder candidate or formal candidate ID, do not directly
change any successfully constructed candidate's classification, and add
nothing to detected/new/duplicate/rejected counts. Counts include only
successfully constructed typed candidates. They nevertheless enter `issues`
and make the final report `BLOCKED — IMPORT PREFLIGHT FAILED`.

The complete package/pre-candidate blocker set is exactly
`malformed_candidate_json`, `invalid_candidate_top_level`,
`invalid_candidate_record`, `missing_image`, `orphan_image`, and
`unsupported_source_format`. The complete candidate-bound blocker set is
exactly `unknown_primary_type`, `unknown_tag`, and the seven approved
duplicate/collision codes. No package/pre-candidate issue claims formal
candidate identity or changes a successfully constructed candidate's
classification.

Candidate processing has this exact order: parse the raw record; validate its
exact structure, runtime types, candidate ID, status/payload combinations,
basic fields, taxonomy-field structure and vocabulary membership, and positional
`(relative_path, role)` image bindings; check that every declared binding has
approved manifest/package image evidence supplying an actual SHA-256; only then
construct the exact typed `ImportCandidate`. An unknown but correctly typed
taxonomy value does not prevent typed construction when image evidence is
complete; its candidate-bound taxonomy issue is emitted only after that
construction. Candidate-level taxonomy issue emission, duplicate/collision
matching, adaptation, and classification occur only after construction.

A record that fails validation before the image-evidence check emits only
`invalid_candidate_record`; it emits no `missing_image`, unknown-taxonomy,
duplicate/collision, or adaptation result. A missing/wrong-type
`primary_type` is invalid-candidate-record input, while an exact `str` outside
the approved vocabulary is eligible for `unknown_primary_type` only if the
record later constructs a typed candidate. A malformed `tags` container or
non-string member is invalid-candidate-record input, while valid strings outside
the vocabulary are eligible for one `unknown_tag` issue with a sorted unique
`unknown_tags` array only after typed candidate construction.

`missing_image` is a pre-candidate/package-level issue. It is emitted once for
each structurally valid raw-record binding whose canonical relative path has no
approved manifest/package image evidence capable of supplying the required
actual SHA-256. The record's candidate ID must already be an exact valid,
non-empty `str`, but remains raw locating evidence rather than formal candidate
identity: `ImportIssue.proposed_question_id` is exactly `None`, while evidence
is exactly `{candidate_id, relative_path, role}`. Its private signal must retain
`("missing_image", raw_candidate_id, relative_path, role)` or an exactly
equivalent private carrier; the raw candidate ID in that signal/evidence may
not be `None`, and C5 must never guess `role`.

Because no actual image SHA-256 exists, a missing-image record does not
construct `ImportCandidate`. It creates no candidate classification, adaptation,
duplicate/collision result, or candidate count and does not enter C5 matching.
Do not use a `None`, empty, or placeholder digest; do not delete the missing
binding and pretend the candidate is complete; and do not introduce an
incomplete public candidate carrier. The public frozen 25-field
`ImportCandidate` remains unchanged: `image_paths`, `image_sha256s`, and
`image_roles` have equal lengths and every image SHA is a valid lowercase
64-character SHA-256. An existing complete same-path/role image with a
candidate/reference SHA conflict remains `collision_image_sha256`, not
`missing_image`.

`orphan_image` is emitted once for each manifest `image_files` entry whose
canonical `relative_path` is absent from the set of canonical relative paths in
valid image bindings of successfully constructed typed candidates. Matching is
path-only: manifest image evidence has no independent role authority. Invalid
record references do not bind an image. Its evidence is exactly
`{relative_path, sha256}`; no role is invented. This is distinct from a valid
raw binding whose absent image evidence prevents typed candidate construction,
so the same logical fact cannot be both missing and orphan.

`unsupported_source_format` is package/file-level. It is emitted for a declared
input/source path whose canonical relative path has one of the Task 9A deferred
source suffixes. ASCII-lowercase that logical path and match longest first:
`.mmd.zip -> "mmd_zip"`, `.mmd -> "mmd"`, `.pdf -> "pdf"`. Its evidence is
exactly `{relative_path, format}`. Task 9A identifies but never parses these
files. Malformed canonical candidate JSON is instead
`malformed_candidate_json`.

`unknown_primary_type` has evidence exactly `{candidate_id, value}` and permits
no correction, mapping, or inference. `unknown_tag` has evidence exactly
`{candidate_id, unknown_tags}` and is emitted at most once per candidate;
`unknown_tags` is the sorted unique JSON array of unknown valid strings.

Non-duplicate blockers neither suppress one another nor suppress independent
issues from other successfully constructed candidates. Candidate-bound
`unknown_primary_type` and `unknown_tag` make that typed candidate `rejected`;
a retained exact-duplicate reference/evidence or adaptation does not also add
the candidate to duplicate/new counts. A clean duplicate plus an independent
package-level blocker remains classified and counted once as duplicate while
the report is BLOCKED. Candidate-level `duplicate_exact` plus unknown taxonomy
retains duplicate evidence but is classified and counted only as rejected. A
missing-image record never reaches duplicate/collision classification.

Adaptation is fixed as follows. Its unique reference is established only for a
successfully constructed typed candidate. A missing-image record never creates
or retains `ImportAdaptation` and never enters candidate matching. Unknown
taxonomy may retain an independently established adaptation, classify that
typed candidate rejected, and block the report. Package-level `orphan_image` or an independent
`unsupported_source_format` retains an otherwise-valid adaptation and its
candidate's `new_candidate` classification/count while blocking the report. If
an input exists only in an unsupported format and no typed candidate is
constructed, no placeholder candidate or adaptation exists.

All fifteen codes share the existing global ordering exactly as
`(proposed_question_id or "", code, field, evidence)` and the existing `issues`
projection of the 12-key digest payload. There is no `report_only_blockers`,
`package_blockers`, `validation_blockers`, second ordering, or thirteenth
top-level key. Any membership, code, field, or evidence change changes the
final `preflight_sha256`; any blocking issue makes C6 close the report as
BLOCKED. `report.blocking_errors`, where rendered, is only a deterministic
derived projection of `issues`, never independent blocker authority.

The current C4 private raw-signal inventory is exactly the eight non-duplicate
codes above and has no ninth blocking signal. Before C5, after this docs change
passes review and is committed, a separately authorized **C4 signal-shape
alignment checkpoint** must adjust only private signal construction so that:

- malformed/top-level signals retain canonical `relative_path`;
- invalid-record signals retain canonical `relative_path` plus zero-based exact
  integer `record_index` and never claim a candidate ID;
- missing-image signals retain valid raw `candidate_id`, canonical
  `relative_path`, and `role` after structural/basic validation but before, and
  without, typed candidate construction;
- invalid candidates never emit missing-image or later candidate-level signals;
- missing-image records construct no typed candidate and never reach C5
  matching, duplicate/collision, adaptation, or classification;
- orphan reference detection uses canonical relative-path matching only.

That checkpoint must not classify candidates, construct `ImportIssue`, or
construct the report/result. Only after its independent review and checkpoint
commit may a separately authorized C5 convert all eight private signals to the
formal non-duplicate issues. The existing integration test
`test_candidate_json_parsing_accepts_only_exact_canonical_record_objects` locks
the three candidate-input issues as structured BLOCKED results, not
`PipelineError`. `missing_image` is the same structured `ImportIssue`/BLOCKED
boundary and is not an early `PipelineError`.
`test_missing_orphan_images_and_unknown_taxonomy_are_blockers`
locks the first, second, fourth, and fifth semantic/package codes, and
`test_unsupported_mmd_mmd_zip_and_pdf_are_blockers` locks the third. No new
public API is authorized. API/carrier/root/baseline boundary errors remain
eligible for early `PipelineError`; safely read package-internal candidate
content errors use the formal issues above. Any future raw blocking signal
without approved code, field, evidence, scope, count, and digest semantics is a
new authority gap and must stop implementation.

Duplicate/collision issue emission is also closed. Evaluate each candidate against the compact
baseline indexes, collect the reference IDs reached by the approved identity
signals, and apply this precedence in order:

1. If the signals reach more than one distinct reference and no unique result
   survives the rules below, emit only `duplicate_ambiguous` for those competing
   references and classify the candidate `rejected` with `ambiguous=true`.
2. For one reference, `duplicate_exact` requires equality of the stable source
   locator `(source_id, source_question_number, source_section)`,
   `source_fragment_hash`, `normalized_text_sha256`, and the complete declared
   image identity tuple `(logical relative path, role, sha256)`; `size_bytes` is
   file-integrity evidence and is not part of image identity. An empty image
   tuple equals only an empty image tuple. It classifies the candidate
   `duplicate` only when no independent candidate-bound blocker exists and suppresses
   `collision_candidate_id`,
   `collision_source_locator`, `collision_fragment_sha256`,
   `collision_normalized_text_sha256`, and `collision_image_sha256` produced by
   those same constituent signals against that same reference.
3. The already-approved adaptation predicate is evaluated next. When one unique
   reference has equal locator and fragment digest, a different normalized-text
   digest, no proposed-ID collision, and no signal reaching a second reference,
   retain the exact adaptation carrier and suppress only the same-reference
   locator and fragment constituent collisions that establish the adaptation.
   An independent blocker may coexist only when it does not invalidate that
   unique adapted reference. The approved representative is an additional image
   binding at the same logical path/role whose different SHA independently emits
   `collision_image_sha256`: locator/fragment/normalized signals still identify
   the single adapted reference, the adaptation is retained, and the candidate
   is rejected/BLOCKED. A proposed-ID collision, `duplicate_ambiguous` from a
   competing identity reference, or any other predicate that negates adaptation
   identity prevents the adaptation carrier from being created.
4. Otherwise apply each blocking collision predicate independently. One
   candidate may therefore have multiple issues when predicates concern
   different references or unrelated independent blockers. Any independent
   candidate-bound blocker makes the final classification `rejected`, even when
   a `duplicate_exact` issue is retained. A package/file-level blocker leaves
   candidate classification unchanged. Each candidate is counted in exactly
   one of `new_candidate`, `duplicate`, or `rejected`.

The exact predicate/precedence table is:

| code | trigger | suppresses | can coexist with | classification result |
| --- | --- | --- | --- | --- |
| `duplicate_exact` | one reference has equal stable locator, fragment digest, normalized-text digest, and complete `(relative_path, role, sha256)` image tuple | all same-reference constituent ID/locator/fragment/text/image collision issues | unrelated blockers against other identities | `duplicate`, `ambiguous=false` with no independent candidate-bound blocker; a candidate-bound blocker retains this issue/evidence and classifies `rejected`, while a package/file-level blocker leaves it `duplicate` |
| `collision_candidate_id` | `proposed_question_id` equals an existing or earlier-batch question ID but the candidate is not its exact duplicate | nothing | any independent blocking collision, including against another reference; never `ImportAdaptation` for the same candidate | `rejected`, `ambiguous=false` unless the multi-reference rule applies |
| `collision_source_locator` | the stable locator equals a reference locator but at least one of fragment, normalized text, or complete image identity differs, and adaptation did not suppress it | nothing | ID, fragment, normalized-text, or image collisions | `rejected`, `ambiguous=false` unless the multi-reference rule applies |
| `collision_fragment_sha256` | `source_fragment_hash` equals a reference digest but the candidate is neither exact duplicate nor approved adaptation of that reference | nothing | independent ID, locator, normalized-text, or image collisions | `rejected`, `ambiguous=false` unless the multi-reference rule applies |
| `collision_normalized_text_sha256` | normalized-text digest equals a reference digest but exact duplicate is false | nothing; it never creates adaptation | independent ID, locator, fragment, or image collisions | `rejected`, `ambiguous=false` unless the multi-reference rule applies |
| `collision_image_sha256` | equal logical relative image path and role bind different SHA-256; equal path/role/SHA is the same image regardless of redundant declared size | nothing | every independent blocker | `rejected`, `ambiguous=false` unless the multi-reference rule applies |
| `duplicate_ambiguous` | approved signals reach multiple competing references and precedence cannot select one unique duplicate/adaptation | all constituent per-reference duplicate/collision issues for those competing references | unrelated non-identity blockers only; never `ImportAdaptation` for the same candidate | `rejected`, `ambiguous=true` |

The separate non-issue adaptation precedence row is:

| carrier | trigger | suppresses | can coexist with | cannot coexist with | final classification |
| --- | --- | --- | --- | --- | --- |
| `ImportAdaptation` | one unique adapted reference; equal locator and fragment digest; different normalized-text digest; not exact duplicate; no proposed-ID collision; no competing identity reference | only the same-reference locator/fragment constituent signals that establish this adaptation | independent blockers that do not invalidate the unique adapted reference, represented by an additional same-reference image path/role binding with conflicting SHA | `collision_candidate_id`; `duplicate_ambiguous` caused by competing identity; any blocker whose predicate negates adaptation identity | `new_candidate` with no candidate-bound blocker; an approved coexisting candidate-bound blocker makes it `rejected`, while a package/file-level blocker retains `new_candidate`; retain the adaptation and blocker in both cases |

For the same candidate, `collision_candidate_id` and `ImportAdaptation` are
mutually exclusive because the ID collision directly falsifies the adaptation
predicate. `duplicate_ambiguous` caused by competing identity references and
`ImportAdaptation` are also mutually exclusive. The blocking-code table's other
references to ID coexistence describe collisions coexisting with other blocking
issues, never an ID collision coexisting with an adaptation.

For a non-ambiguous rejected candidate that also has one unique
`duplicate_exact` relationship, `duplicate_classifications` retains that
duplicate reference ID and exact evidence while setting `classification` to
`rejected`; the independent blocking issues state why it is rejected. If the
duplicate reference is not unique, use the existing ambiguous rule: reference
is `null`, `duplicate_ambiguous` supplies evidence, and classification is
`rejected`. Thus `duplicate_exact` alone increments only `duplicate_count`;
with an independent candidate-bound blocker it increments only
`rejected_count`, while a package/file-level blocker leaves it counted as
duplicate. Adaptation alone increments only `new_candidate_count`. An
adaptation plus an approved independent candidate-bound blocker that preserves
the unique adapted reference increments only `rejected_count` while retaining
the adaptation carrier; a package/file-level blocker retains the new-candidate
count. Apparent adaptation signals plus an ID collision or competing reference
also increment only `rejected_count`, but emit no adaptation.

Image integrity and collision are separate. A declared `size_bytes` that does
not match actual bytes is handled by the existing package/file-evidence
integrity validation and blocks preflight without emitting
`collision_image_sha256`; it does not add an eighth duplicate/collision code.
Image collision identity uses only logical path, role, and SHA-256, and its
existing evidence object therefore needs no size fields.

Tests must lock the overlap cases: exact duplicate with equal locator/fragment/
text/image and no independent candidate-bound blocker yields only
`duplicate_exact` and final `duplicate`; exact duplicate plus an independent
candidate-bound blocker yields final
`rejected` while retaining both issues and the unique duplicate reference/
evidence; exact duplicate against reference A plus an independent
candidate-bound blocker
against reference B also yields final `rejected`; multiple competing duplicate
references yield `duplicate_ambiguous` and final `rejected`; adaptation-only
retains the adaptation and remains `new_candidate`/READY; adaptation plus an
independent additional-image SHA blocker retains the adaptation and image issue
but is rejected/BLOCKED; adaptation-like locator/fragment/text signals plus a
proposed-ID collision emit no adaptation and yield `collision_candidate_id`/
rejected/BLOCKED; adaptation-like signals reaching competing references emit no
adaptation and yield the approved ambiguous/rejected path; exact duplicate emits
no adaptation; equal normalized text with different locator and fragment yields
`collision_normalized_text_sha256`; equal image path/role/SHA and bytes is not a
collision; equal image path/role with different SHA/bytes is
`collision_image_sha256`; and equal SHA with incorrect declared size is a
package/file-integrity failure, not `collision_image_sha256`.

## 11. Preflight and approval

Preflight is strictly read-only: it writes neither staging material nor formal
artifacts and never opens SQLite in write mode. `data/`, `releases/`, `legacy/`,
formal image assets, and the V1.18 SQLite must have identical inventories and
hashes before and after Task 9A.

The exact public APIs and parameter order are:

```python
def load_import_manifest(
    path: Path,
    package_root: Path,
) -> BatchImportManifest

def preflight_import(
    manifest: BatchImportManifest,
    package_root: Path,
    baseline_database: ArtifactRef,
) -> ImportPreflightResult
```

`package_root` is an explicit transient runtime locator, not typed authority.
Its annotation is exactly `Path` and its runtime contract follows the existing
repository convention `isinstance(value, Path)` (therefore accepting the
platform concrete `PosixPath`/`WindowsPath`); strings and all non-Path values
are rejected rather than converted. The root must exist, be a directory, and
resolve safely. The caller retains it explicitly across the call chain:

```text
package_root
→ load_import_manifest(manifest_path, package_root)
→ manifest
→ preflight_import(manifest, package_root, baseline_database)
```

`load_import_manifest()` reads and parses the manifest, validates containment,
constructs the exact manifest carrier, and validates canonical declared paths.
Its existing Task 2 inventory checks may read declared bytes to verify file
identity, but it does not parse candidate records, construct candidates, or
retain `package_root`. `preflight_import()` independently resolves the
manifest-declared relative paths beneath the explicit root, rechecks the bytes
it consumes, reads canonical candidate/source/image evidence, constructs
candidates, and produces issues, report, and digest.

`preflight_import()` is an independent consumption boundary. Before opening or
reading the baseline, resolving/reading/hashing any package file, or constructing
a candidate, it requires `type(manifest) is BatchImportManifest` and
`manifest.target_release_version == "V1.19"`. It never trusts prior loader
validation as a substitute. V1.18, V1.17, arbitrary future values, `None`, an
empty string, and wrong runtime types are rejected before I/O, and no result may
be constructed whose manifest and report target identities differ.

Every declared path is joined to the resolved root and then resolved before
use. The resolved path must be contained within the resolved root by a path-
aware containment check; string-prefix checks are insufficient. Absolute
paths, `..`, normalization escape, nonexistent/non-directory roots, and symlink
escape are rejected. Neither function may discover a root through cwd,
repository lookup, manifest-parent inference, environment variables, global
registries, or hidden maps.

The locator is never stored in `BatchImportManifest`, `ImportFileEvidence`,
`ImportCandidate`, `ImportAdaptation`, `ImportIssue`, `ImportPreflightReport`, or
`ImportPreflightResult`; no locator/context carrier is introduced.
`ImportAdaptation` carries only logical comparison evidence and never the root.
The locator is
also excluded from approval identity and every canonical report/digest
projection. Two byte- and semantics-equivalent packages under different
absolute roots must yield identical typed file evidence, candidates, issues,
report authority, and `preflight_sha256`, and neither absolute root may appear
in canonical report or digest serialization.

`ImportAdaptation` is a public typed preflight carrier, following the repository
convention that public typed carriers are exported. The exact final
`joy_m2.ingest.__all__` order is:

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

The report includes package inventory/readability, input hashes, baseline
identity (`V1.18`, 497 rows) and `before_count`, target identity (`V1.19`),
candidate IDs/count, duplicates, rejections, ambiguous splits/collisions,
missing answers/explanations/images, orphan images, enrichment completeness,
teacher/common-error evidence availability, tag and Level distributions,
warnings, blockers, proposed IDs, and
`adaptations: tuple[ImportAdaptation, ...]`. The exact report field is placed
immediately after `proposed_ids` and before `warnings`; `ImportPreflightResult`
does not repeat adaptation authority. Adaptations are stable-sorted by exactly
`(candidate_id, reference_question_id, adaptation_kind, evidence, reason)`.
The report also carries these exact projected counts:

```text
before_count
detected_count
new_candidate_count
duplicates
rejected
approved = 0 before approval
projected_after_count = before_count + new_candidate_count
```

The classifications are disjoint and close exactly:

```text
detected_count = new_candidate_count + duplicates + rejected
```

`detected_count` and all three classification counts include only records that
successfully construct the exact typed `ImportCandidate`. Malformed,
wrong-top-level, invalid-record, missing-image, orphan-image, and unsupported-
format package/pre-candidate facts block through `issues` and do not add a
candidate count.

After a future approved write, the import report records the actual
`after_count = before_count + approved`; Task 9A never produces that write-time
value.

Its conclusion is exactly:

- `READY FOR USER IMPORT APPROVAL`, or
- `BLOCKED — IMPORT PREFLIGHT FAILED`.

Errors are collected per item, but one blocker prevents the entire write; no
partial formal import is allowed.

Approval is exact and digest-bound:

```text
USER APPROVED IMPORT BATCH <batch_id> <preflight_sha256> <target_release_version>
```

For the present authority, the final token is exactly `V1.19`.

Any input, ID, enrichment, report, or target-version change invalidates it.
Moving an otherwise identical package to a different absolute root does not:
approval remains bound only to `(batch_id, preflight_sha256, V1.19)` and never
to `package_root`.

`preflight_sha256` is path-independent. Equivalent canonical packages and
baseline bytes placed under different absolute roots must produce the same
manifest/file/candidate/issue values, report authority, and digest. The result
may retain the caller's sole typed baseline `ArtifactRef`, whose explicit path
can differ across roots, but that carrier is never serialized because
`ArtifactRef.path` is resolved and absolute. The sole
typed baseline carrier remains `ImportPreflightResult.baseline_database`; the
digest uses only this one-way logical projection:

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

Preflight first validates the exact baseline kind as `sqlite`, lowercase digest,
exact integer size, bytes, schema/version, and count. The projection contains no
path and is not a second typed carrier or reverse-reconstruction source.

`manifest_sha256` is not the hash of source `import_manifest.json` bytes,
because `preflight_import()` consumes the typed `BatchImportManifest`, not the
raw file. It is exactly

```python
sha256(
    canonical_json_bytes(manifest_logical_projection) + b"\n"
).hexdigest()
```

`manifest_logical_projection` contains all and only the approved manifest
fields: `schema_version`, `batch_id`, `project`, `module`, `chapter`,
`target_release_version`, `candidate_records`, `source_files`, `answer_files`,
`image_files`, `teacher_notes_files`, `common_errors_files`, `language_policy`,
`split_policy`, `difficulty_policy`, `tag_policy`, `answer_policy`, and
`explanation_policy`. Each of the six file arrays preserves its approved
manifest semantic order and projects every entry as the exact object
`relative_path`, `sha256`, `size_bytes`, `kind`. The maintained serializer
provides UTF-8, sorted object keys, compact separators, `ensure_ascii=False`,
and exact-type validation excludes NaN/Infinity before encoding; arrays are
never sorted by the serializer. Exactly one LF byte is appended: neither zero
LF, platform newline, nor two LF is valid. The projection excludes absolute
paths, `package_root`, cwd, temporary/repository roots, runtime metadata,
object repr, and memory identity. A target-version or policy-scalar change, a
`candidate_records` reorder, or a change to any file entry's `relative_path`,
`sha256`, `size_bytes`, or `kind` changes `manifest_sha256`. The same four-field
projection rule applies to all six file arrays. Changing only the absolute
package root while retaining every logical relative value does not change the
digest.

The canonical `task9-preflight-v1` digest object has exactly these top-level
keys:

```text
schema, batch_id, target_release_version, baseline, manifest_policies,
candidate_record_order, file_evidence, candidates, issues,
duplicate_classifications, image_evidence, report
```

Every typed carrier/dataclass is projected as a JSON object with named keys,
never as a positional array. A field whose authority is a tuple/list is a JSON
array. Optional absence is JSON `null`; empty sequences and mappings are `[]`
and `{}`; legal empty text is `""`; no key may be omitted in place of `null`.
Booleans are JSON `true`/`false`, exact integers are JSON numbers, `bool` never
satisfies an integer contract, and floats/NaN/Infinity are forbidden.

The nested representations are exact:

- `schema` is the string `task9-preflight-v1`; `batch_id` is the manifest
  string; `target_release_version` is exactly `V1.19`.
- `baseline` is the exact six-key object `release_version`, `schema_version`,
  `question_count`, `sha256`, `size_bytes`, `kind` shown above.
- `manifest_policies` is the exact ten-key object `schema_version`, `project`,
  `module`, `chapter`, `language_policy`, `split_policy`, `difficulty_policy`,
  `tag_policy`, `answer_policy`, `explanation_policy`.
- `candidate_record_order` is the JSON array of canonical relative-path strings
  in manifest-declared order.
- `file_evidence` is an array sorted by exactly `relative_path`; each entry is
  the exact object `{relative_path, sha256, size_bytes, kind}`. It contains every
  manifest entry and no absolute/root or extra key.
- `candidates` is in manifest semantic order. Every entry is the exact 25-key
  `ImportCandidate` object: `proposed_question_id`, `source_id`,
  `source_question_number`, `source_section`, `source_fragment_hash`,
  `normalized_text_sha256`, `question_text_original`, `question_text_zh`,
  `translation_status`, `translation_evidence`, `solution_original`,
  `solution_verified`, `answer_status`, `explanation_text`,
  `explanation_status`, `explanation_evidence`, `image_paths`,
  `image_sha256s`, `image_roles`, `primary_type`, `tags`, `tag_status`,
  `difficulty_level`, `difficulty_status`, `enrichment_status`.
- `issues` contains exact objects `{code, severity, proposed_question_id, field,
  evidence}` and is stable-sorted by exactly
  `(proposed_question_id or "", code, field, evidence)`. File diagnostics use
  only a canonical relative path plus stable source locator; runtime paths and
  roots are forbidden.
- `duplicate_classifications` is in candidate order. Each exact object has
  `{candidate_id, classification, reference_question_id, evidence}`;
  `classification` is `new_candidate | duplicate | rejected`. The last two keys
  are both `null` for `new_candidate`. For `duplicate`, they are the unique
  reference ID and the `duplicate_exact` evidence. For a non-ambiguous
  `rejected` candidate that retains one unique `duplicate_exact` relationship,
  those same duplicate reference/evidence values are retained. Every other
  non-ambiguous rejection uses the first blocking issue's evidence under
  approved issue order and that issue's unique reference when its schema has
  one, otherwise `null`. For ambiguous rejection, reference is `null` and
  evidence is the `duplicate_ambiguous` evidence. Adaptations are never stored
  here.
- `image_evidence` is ordered by candidate order and then declared image
  position. Every exact object has `{proposed_question_id, relative_path,
  sha256, size_bytes, kind, role}` and is derived from candidate binding plus
  declared logical file evidence, never a destination or runtime path.
- `report` is one exact object containing every `ImportPreflightReport` field
  except `preflight_sha256`: `batch_id`, `status`, `manifest_sha256`,
  `baseline_version`, `before_count`, `target_release_version`,
  `detected_count`, `new_candidate_count`, `duplicate_count`, `rejected_count`,
  `ambiguous_count`, `approved_count`, `projected_after_count`,
  `readable_files`, `unreadable_files`, `unsupported_files`,
  `teacher_notes_file_count`, `common_errors_file_count`, `ambiguous_splits`,
  `missing_answers`, `missing_explanations`, `incomplete_enrichments`,
  `missing_images`, `orphan_images`, `level_counts`, `proposed_ids`,
  `adaptations`, `warnings`, `blocking_errors`. File lists use relative-path
  order; candidate/proposed-ID/missing/ambiguous lists use candidate order;
  `level_counts` is an array of exact two-integer arrays in ascending Level;
  blockers retain issue order. `warnings` contains only approved warning issue
  codes; Task 9A currently has none, so adaptation does not add an entry and an
  adaptation-only fixture uses `[]`. Each adaptation is the exact object
  `{candidate_id, reference_question_id, adaptation_kind, evidence, reason}`
  sorted by `(candidate_id, reference_question_id, adaptation_kind, evidence,
  reason)`. This binds adaptation changes without a thirteenth top-level key.

Encode that object using the maintained deterministic JSON convention:
`joy_m2.export.formats.canonical_json_bytes(payload) + b"\n"`, reusing the
existing helper without modifying Export (UTF-8, sorted keys, compact `,`/`:`
separators, `ensure_ascii=False`, exactly one trailing LF). Task 9A exact-type
validation excludes floats and therefore NaN before encoding; tuple/list order
follows the contracts above, and no dict/set iteration may supply array order.
The payload never includes timestamps, absolute paths, package/temp/repository
roots, cwd, memory addresses, session IDs, AI conversation identifiers, or the
digest itself.

Changing candidate manifest order changes the ordered candidate projections
and digest. Merely changing filesystem discovery order, cwd, or absolute root
does not. This makes approval bind exactly
`(batch_id, preflight_sha256, V1.19)`.

Digest regression authority is independent of production. At least one frozen
fixture contains non-empty candidates, provenance, issues, image evidence,
duplicate/adaptation evidence, and count closure. Tests construct the approved
12-key payload independently and may reuse only the canonical serializer, not a
production-captured payload or production projection helper as the expected
oracle. Removing or changing `issues`, `image_evidence`, `candidates`,
provenance, duplicate classifications, adaptations, counts, or baseline
projection must fail at least one regression; adaptation evidence mutation must
change `preflight_sha256`.

The minimum independent literal oracle fixture is a two-candidate batch over
the frozen 497-row baseline: `TASK9-NEW-001` is a new candidate with non-empty
translation/explanation provenance, one declared image and one exact
`ImportAdaptation`; `TASK9-DUP-001` is an exact duplicate of the frozen
reference `M2QD-DA-EXAMPLE-Q1`. It therefore has non-empty candidate,
provenance, image, adaptation, duplicate-classification and issue projections:
one adaptation in `report.adaptations` plus one `duplicate_exact` blocking
issue, with no adaptation issue and an empty `report.warnings`. Counts
are exactly `before=497`, `detected=2`, `new=1`, `duplicate=1`, `rejected=0`,
`ambiguous=0`, `approved=0`, and `projected_after=498`. Test literals provide
all source text/evidence/image bytes and compute their hashes only with the
formulae above. The test constructs the full 12-key expected payload without a
production projection helper and separately proves that deleting `issues` or
`image_evidence`, or mutating candidates, provenance, duplicate
classifications, adaptations, counts, or baseline projection, cannot match the
production digest.

The Task 9A Plan is the executable literal-oracle authority: it records the
complete raw candidate/file bytes, full 18-field manifest object, normalized
text and digest, complete named-key 12-key payload, exact one-issue outcome, and
independently precomputed manifest/preflight SHA-256 values. A reviewer can copy
those literals and recompute both digests without importing or inspecting
`ingest.preflight` or any future production projection helper.

Import approval and formal promotion are separate authorities. Import approval
only permits a later maintained writer to produce a V1.19 candidate. It never
authorizes `promote_candidate()`, publication, or a write under
`releases/V1.19/`; formal promotion always requires a later explicit approval.

## 12. Transaction and verification

A later approved writer must verify baseline SQLite/manifest identities, copy
the baseline to a temporary staging database, start one immediate transaction,
insert only approved rows/dependencies, append a hash-bound import run, rebuild
new-version taxonomy/metadata, commit, verify, and atomically publish only a
candidate SQLite. Failure rolls back and removes temporary output.

Verification covers inserted/duplicate/rejected and before/after counts,
existing 497 canonical row/tag/correction hashes, source/answer/stable IDs,
schema/FK integrity, image hashes/bindings, approval/import-run binding,
deterministic exports, and the untouched V1.18 validator. New SQLite bytes may
change; existing-row preservation is logical, while V1.18 bytes remain frozen.

## 13. Images

- declare relative path, digest, size, media kind, and question role;
- verify containment, readability, hash, reference, orphans, and collisions;
- a future writer may let identical bytes share one staged asset; different
  bytes cannot share a destination;
- future writer assets use deterministic content-addressed candidate names;
- existing V1.18 image paths and identities never change;
- a future writer may copy only into a temporary candidate tree inside its
  rollback scope;
- missing required image blocks.

Task 9A performs only inventory, relative-path/containment checks, SHA-256,
size/kind/role checks, proposed question binding, missing/orphan detection, and
duplicate/collision detection. It never copies, moves, renames, or chooses a
formal destination. Future serialization/destination is deferred to Task 9C
writer authority; Task 9B may define only adapter-side extraction and canonical
evidence mapping. Neither deferred decision blocks Task 9A.

## 14. Efficient operation and batch size

Stage A performs deterministic inventory, digesting, parsing, and compact
baseline lookup. Stage B uses AI only for translation, Level, controlled tags,
explanation review, and teacher/common-error mapping proposals. Stage C performs
deterministic validation, approval binding, write, export, and verification.

AI receives the current batch, taxonomy, and compact duplicate matches, not all
497 full records. Canonical JSON/JSONL and hash indexes are reusable.

Use one source package/chapter, normally 10–50 complete questions. Existing
source groups are commonly 6–45, so this bounds review, tokens, rollback, and
duplicate resolution. This is an operational recommendation, not a validation
maximum; inputs above 50 are not automatically invalid. Larger inputs should
usually split by chapter/section, never subpart.

## 15. Task 9A authority closure and deferred Task 9C decisions

Existing authority requires a new release for formal data changes but had not
previously selected its identifier or profile. The user has now selected V1.19 as
the next import target identity. Current maintained production contracts still
accept only V1.17/V1.18, so Task 9A validates V1.19 identity without creating a
profile or editing V1.18.

Task 9A authority is now closed as follows:

- frozen baseline: V1.18 / 497; target identity: V1.19;
- teacher notes/common errors: hashed import evidence only;
- images: read-only deterministic evidence only;
- import approval and formal promotion: separate checkpoints.

The explicit `package_root` transport closes the Task 3 API authority gap. The
two-stage scaffold sequencing remediation closes the remaining TDD execution
gap subject to independent review. Task 1–2 remain valid and completed; Task 3
is blocked until that review passes and implementation is explicitly resumed.
Before Task 9C writer
authorization, a separate reviewed decision must still freeze the V1.19
database/manifest profile, `PRAGMA user_version`, teacher/common-error formal
representation or exclusion, image serialization/destination, migration and
rollback artifacts, and promotion contract. These deferred Task 9C decisions
do not authorize or block read-only Task 9A.

## 16. Git and reporting

Each real import uses a batch-specific branch from an explicitly approved base.
Raw archives remain outside Git until a private LFS/archive policy exists.
Preflight implies neither commit nor formal write.

After approval, the independently reviewable batch delivery includes permitted
canonical evidence, new-version candidate artifacts, and
`docs/reports/imports/<batch_id>.md`, recording hashes, preflight, exact approval,
counts, verification, and unresolved issues. Implementation and data-import
commits stay separate. Every batch must be independently revertible.

## 17. Minimal phases

- **Task 9A — Import contract + read-only preflight:** typed manifest,
  inventory, canonical JSON identities, compact baseline indexes, duplicate
  checks, deterministic report. No SQLite write.
- **Task 9B — MMD/MMD.ZIP source adapter:** representative Mathpix fixtures and
  deterministic conversion to canonical Task 9 JSON. This is the priority
  real-world adapter so users need not hand-convert routine Mathpix packages;
  direct PDF remains deferred unless separately authorized.
- **Task 9C — V1.19 incremental writer + verification:** not started and
  deferred pending V1.19 serialization/schema authority; it must adapt the
  maintained database authority.
- **Task 9D — First real batch acceptance:** preflight, digest-bound approval,
  candidate build, verification, independent review, then separately authorized
  promotion if requested.

## 18. Exact first implementation proposal

`TASK 9A — IMPORT CONTRACT + READ-ONLY PREFLIGHT TDD`

Exact allowed files:

```text
src/joy_m2/ingest/__init__.py
src/joy_m2/ingest/models.py
src/joy_m2/ingest/manifest.py
src/joy_m2/ingest/preflight.py
tests/unit/test_ingest_models.py
tests/integration/test_ingest_preflight.py
```

All existing production/tests/docs, `data/`, `releases/`, `legacy/`, and formal
SQLite are forbidden. RED tests cover exact manifest values/types/order,
containment/digests, unsupported formats, 497-row identity, ID/source/fragment/
text/image duplicates, missing answers/images, deterministic report/counts, and
zero mutation. They also independently lock cross-absolute-root digest equality,
absence of absolute-path authority contamination, exact translation and
explanation provenance values/consistency, AI-proposed versus source authority,
candidate independence from filesystem discovery order, and manifest-declared
candidate reorder/digest semantics. The Plan's 28-item RED inventory is the
exact implementation gate for these requirements. GREEN requires Task 9A tests
plus Public Models, Audit, Database, Release, Task 7, Task 8 equivalence, and
V1.18 validator gates.

Task 3 uses two distinct RED stages. Stage 3A first records an API-existence RED
for the exact `preflight_import(manifest, package_root, baseline_database)`
signature, including exact parameter names/order/annotations, return annotation,
and absence of extra runtime authority. Module missing, symbol missing, or an
unavailable exact signature is valid only for this API-existence RED; it is not
a behavior RED.

Only after that RED is observed may `src/joy_m2/ingest/preflight.py` first be
created as a minimal importable scaffold. The scaffold contains only required
imports, the exact approved function signature, and an immediate
`NotImplementedError`. It performs no root validation, containment, file read,
parsing, hashing, candidate/issue/report construction, or digest work. Import
and exact-signature tests then become GREEN, but Task 3 remains in RED and the
scaffold is not production behavior.

Stage 3B then establishes the independent behavior REDs. Every behavior test
must import the module and symbol successfully, pass the exact-signature gate,
construct its fixtures successfully, reach the scaffold call, and fail only
with `NotImplementedError` or the specific missing behavior. These REDs cover
root runtime type, nonexistent/file roots, absolute/`..`/normalization/symlink
escape, root-authority contamination, and cross-root equivalence. Only after all
behavior REDs are observed may production behavior replace the scaffold, one
minimal RED→GREEN group at a time. `NotImplementedError` is scaffold-only and
must be absent from completed Task 3 runtime behavior and regression
expectations.

Task 9A requires independent review and explicit implementation authorization.

## 19. Task 3 authority remediation and Stage 3B entry

Task 1–2 are completed and committed at
`dd1cfed2cf3d09caf9136d3c9e2cc8d487186221`. Their history is retained. The
later model-remediation checkpoint may extend only `src/joy_m2/ingest/models.py`
and `tests/unit/test_ingest_models.py` with the exact `ImportAdaptation` carrier,
the exact `ImportPreflightReport.adaptations` field, validation/order/digest
contracts. It does not implement `joy_m2.ingest.__all__`; the already-frozen
nine-name surface is implemented and tested later when Task 5 first creates
`ingest/__init__.py`. The model checkpoint does not reopen the
manifest carrier or authorize `manifest.py` changes: adaptations are derived by
preflight comparison, not declared by canonical raw records.

The adaptation-model checkpoint is already completed and committed. Stage 3A
then correctly recorded the API/signature RED, created only
`src/joy_m2/ingest/preflight.py` as the immediate-`NotImplementedError`
scaffold, and made the one signature test GREEN. Those two current Stage 3A
assets are preserved byte-identically; `src/joy_m2/ingest/__init__.py` has not
been created. Stage 3A is `COMPLETED / GREEN` and must not be cleared, recreated,
or rerun.

Stage 3B is `NOT STARTED / BLOCKED` with behavior RED count exactly zero. Only
after this digest/taxonomy Revision 4 passes independent review, the three docs
are committed, and the user gives a new explicit Stage 3B authorization may the
existing integration test be extended with the complete approved behavior RED
suite. The suite must include exact issue ordering with both `None` and string
IDs, overlap-signal precedence, independent manifest/normalized-text/full
12-key digest oracles, all critical-projection mutation locks, file-entry
mutations, and existing boundary/zero-write contracts. Every fixture must build
successfully, reach the existing scaffold, and fail only with
`NotImplementedError` or the specific missing behavior. Production behavior may
replace the scaffold only after the applicable behavior RED group is observed.

No asset deletion, API RED replay, behavior test, implementation, import,
V1.19 artifact, writer, or promotion is authorized by this docs remediation.

## 20. Classification

Task 9A Task 1–2 and the adaptation-model checkpoint are
`COMPLETED / COMMITTED`. Task 3 Stage 3A is `COMPLETED / GREEN`; Stage 3B is
`BLOCKED — DIGEST/TAXONOMY REVISION 4 IN REVIEW`, behavior RED count is zero,
and production behavior is unimplemented. Task 9B/9C/9D remain not started, and
Task 9C retains the downstream authority decisions listed in section 15.

`READY FOR TASK 9A DIGEST/TAXONOMY AUTHORITY REVISION 4 REVIEW`
