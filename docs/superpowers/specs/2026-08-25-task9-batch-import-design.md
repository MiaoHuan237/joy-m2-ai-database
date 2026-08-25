# Task 9 Batch Import Workflow Recovery Design

Status: `TASK 9 AUTHORITY DEFINED — PENDING INDEPENDENT REVIEW`

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
protected baseline row or dependent tag/correction identity. An adaptation is
a warning/manual decision and must carry `duplicate_status="adapted"`, a stable
reference, and evidence. Semantic similarity never replaces deterministic
checks.

## 11. Preflight and approval

Preflight is strictly read-only: it writes neither staging material nor formal
artifacts and never opens SQLite in write mode. `data/`, `releases/`, `legacy/`,
formal image assets, and the V1.18 SQLite must have identical inventories and
hashes before and after Task 9A.

The report includes package inventory/readability, input hashes, baseline
identity (`V1.18`, 497 rows) and `before_count`, target identity (`V1.19`),
candidate IDs/count, duplicates, rejections, ambiguous splits/collisions,
missing answers/explanations/images, orphan images, enrichment completeness,
teacher/common-error evidence availability, tag and Level distributions,
warnings, blockers, proposed IDs, and exact projected counts:

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

The canonical `task9-preflight-v1` digest object has exactly these top-level
keys:

```text
schema, batch_id, target_release_version, baseline, manifest_policies,
candidate_record_order, file_evidence, candidates, issues,
duplicate_classifications, image_evidence, report
```

- `schema` is `task9-preflight-v1`; target is exactly `V1.19`.
- `manifest_policies` projects manifest schema/project/module/chapter and the
  exact fields `schema_version`, `project`, `module`, `chapter`,
  `language_policy`, `split_policy`, `difficulty_policy`, `tag_policy`,
  `answer_policy`, and `explanation_policy`.
- `candidate_record_order` is the manifest-declared tuple of canonical relative
  candidate-record paths.
- `file_evidence` is every manifest file entry projected as
  `(relative_path, sha256, size_bytes, kind)` and sorted by exactly
  `relative_path`; duplicate paths are already invalid and paths are canonical
  package-relative POSIX strings.
- `candidates` contains every exact `ImportCandidate` field in manifest-
  declared semantic order, including translation/explanation payloads,
  evidence, and provenance statuses.
- `issues` contains every exact `ImportIssue` field in the existing stable
  order `(proposed_question_id, code, field, evidence)`. File diagnostics may
  use only a canonical relative path plus a stable source locator; absolute
  paths, cwd, user names, OS roots, and runtime temporary directories are
  forbidden.
- `duplicate_classifications` has one entry per candidate in candidate order:
  `(proposed_question_id, classification, ambiguous)`, where classification is
  exactly `new_candidate | duplicate | rejected` and `ambiguous` is an exact
  boolean. These values close against report counts and issues.
- `image_evidence` is ordered by candidate order and then declared image tuple
  position, projecting `(proposed_question_id, relative_path, sha256, role,
  size_bytes, kind)` from candidate bindings plus declared file evidence.
- `report` contains every `ImportPreflightReport` field except
  `preflight_sha256`; all path-bearing report values use canonical relative
  paths and all report/count closure values are included. File lists use
  canonical `relative_path` order; candidate/proposed-ID/missing/ambiguous lists
  use candidate order; `level_counts` uses ascending Level; warnings and
  blockers retain the corresponding issue order.

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

Task 9A has no remaining authority blocker. Before Task 9C writer
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
candidate reorder/digest semantics. The Plan's 24-item RED inventory is the
exact implementation gate for these requirements. GREEN requires Task 9A tests
plus Public Models, Audit, Database, Release, Task 7, Task 8 equivalence, and
V1.18 validator gates.

Task 9A requires independent review and explicit implementation authorization.

## 19. Classification

The current architecture and Task 9A authority are sufficiently recovered and
defined for independent review. No implementation, import, writer, candidate
database, release artifact, or promotion has started. Task 9C retains the
explicit downstream authority decisions listed in section 15.

`READY FOR TASK 9 AUTHORITY INDEPENDENT REVIEW`
