# F6 Selected Source Batch / V1.24 Minimal Candidate Bridge

Date: 2026-10-20 (Asia/Shanghai)

Status: APPROVED — WRITTEN DESIGN (2026-10-20).
Human approval binds commit b480a608df851dde318719f4fbf88bffb1489658 and file
SHA-256 7ef92371a9876fc9b0ee100324de4b489f99ba491696ea46f8edf8b4192e13fc.
Technical sections 1–7 are unchanged. Implementation Plan is written and pending
human review/execution confirmation; implementation remains NOT STARTED.

## 1. Outcome and authority

Joy authorized the two missing entry conditions: a truthful school-mock source
mapping with an explicitly selected complete-question sub-batch, and a new
candidate lifecycle after published V1.23. Prioritize F6 Q1, Q3, Q6 and Q8.
Keep the other eight questions and their unresolved evidence, without making
them a prerequisite for processing this independent sub-batch.

Reduce review interruptions by completing source comparison, mathematical
checks, controlled taxonomy and engineering verification autonomously. Present
one exact transcription decision for the selected batch, then one exact import
decision after actual preflight. This does not cancel either approval or grant
promotion. Four selected records are not a forecast of four net-new originals.
The currently published database remains V1.23 / 677 records.

This written Design closes both necessary interfaces in one review. After its
approval, write/review one implementation Plan and request execution-method
confirmation. Do not treat direction approval as approval of unwritten
artifacts. No product code is authorized by this document's pending status.

### Chosen minimum and alternatives

- **Chosen:** one source-specific F6 adapter and fixed V1.24 candidate siblings,
  using the existing preflight/writer/verifier semantics and version-neutral
  helpers. Selection is explicit BEFORE transcription approval, never a
  post-preflight deletion of rejected rows.
- **Rejected:** relabel F6 as Oxford/HKDSE, append to published V1.23, change an
  ID/hash to avoid collision, or approve the old 12-row draft as a four-row batch.
- **Deferred:** generic source plugins, automatic approval, arbitrary partial
  batch salvage, a scheduler change, source-correction framework and promotion.
  No V1.25, historical cleanup or new dependency.

Normative engineering counterparts are the six `src/joy_m2/ingest/v123_*`
candidate modules and `publisher_mock.py` at commit
`2f45dc98f8b37c9d007891f72ad165fd5f265fed`. The latter is an interface/layout
reference only: its Oxford profile and behavior MUST NOT be widened or edited.
The candidate classification contract is also documented in sections 4–8 of
`2026-10-09-v123-next-version-candidate-design.md`; its historical operational
instructions are not new execution authority.

## 2. Frozen formal baseline and next-version identity

Fresh read-only checks found the following actual files and query counts:

```text
baseline_release_version = V1.23
baseline_question_count = 677
baseline_database_schema = task13-v123-formal-v1
baseline_manifest_schema = task13-v123-formal-manifest-v1
baseline_view = formal_complete_questions_v123
database = releases/V1.23/Joy_M2_Complete_Question_DB_V1_23.sqlite3
database_size_bytes = 10928128
database_sha256 = 28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd
manifest = releases/V1.23/manifest.json
manifest_size_bytes = 6728
manifest_sha256 = 54d192436e761c9bfe810510b77a902c5ae659bebdfbc4da8475aac271be8498
release_digest = 84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc
semantic_sha256 = 531e7cf69eec75096f500e2de62dcb0eba0ad68d4d0663dc3bd5faa84e7e1c6d
view rows / unique IDs / published-selectable = 677 / 677 / 677
metadata table = release_metadata_v2
```

Use escaped `Path.as_uri()` with `mode=ro` and query-only connections. Validate
exact baseline bytes, manifest, metadata, SQLite integrity/FK and view identity.
Never read an older view for current taxonomy/counts or add inherited candidate
tables to the formal view count. Preserve all inherited schema/rows/images,
source identities and approval history. The 38 previously promoted source
records are already inside 677.

V1.24 is a candidate target only. Its fixed substitutions in the V1.23
counterparts are:

```text
profile / target_release_version = V1.24
baseline_release_version / count = V1.23 / 677
canonical_manifest_schema = task14-v124-import-manifest-v1
preflight_schema = task14-v124-preflight-v1
approval_schema = task14-v124-import-approval-v1
candidate_manifest_schema = task14-v124-candidate-manifest-v1
candidate_database_schema = task14-v124-candidate-v1
candidate_identity_schema = task14-v124-candidate-identity-v1
rollback_schema = task14-v124-rollback-v1
expected_user_version = 124
database_filename = Joy_M2_V1.24_candidate.sqlite3
manifest_filename = candidate_manifest.json
sha256s_filename = SHA256SUMS
rollback_filename = rollback.json
authority_root = authority/batches
image_root = images/sha256
required_baseline_view = formal_complete_questions_v123
required_candidate_tables =
  task14_v124_batch_ledger_v1
  task14_v124_candidates_v1
  task14_v124_images_v1
  task14_v124_taxonomy_v1
required_candidate_views = task14_candidate_questions_v124
first new aggregate_order = 678
```

`task14` is solely this version's serialization namespace. Preserve counterpart
DDL columns, ordering, constraints and relationships with the explicit new
identities and counts above. Do not rename or modify inherited schema objects.

Genesis is SHA-256 of the following object serialized as UTF-8, sorted keys,
compact separators, `ensure_ascii=False`, `allow_nan=False`, and one trailing LF:

```json
{"baseline_database_sha256":"28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd","baseline_question_count":677,"baseline_release_digest":"84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc","baseline_release_version":"V1.23","candidate_count":0,"schema":"task14-v124-genesis-v1","target_release_version":"V1.24"}
```

Read-only calculation gives:
`797ed06ca5833bac060c1603cada38a6f2aa9eb080a40d9dc892bba9a549773a`.
This is a proposed contract's genesis identity, not an import/preflight/release
digest and not evidence of an existing candidate.

For generation 000001, no parent artifact means `parent_candidate=None`; the
authority-level parent digest MUST still be this exact genesis. Writer and
independent verifier each reconstruct it. Missing/empty/None digest, older
genesis, or equal forged approval/preflight strings are invalid. Generation
000002+ binds the exact independently verified previous V1.24 prefix. Never
reuse published V1.23's last candidate digest as a V1.24 parent.

## 3. Fixed F6 source and selected-question authority

Read-only original staging:
`/Users/miaohuanjoy/Desktop/joy-m2-ai-database-current/data/staging/joy_m2_f6_mock_2015_16_0428_staging.json`.

```text
parent_source_batch_id = JOY-M2-STG-F6-MOCK-2015-16-0428-20260905
original_staging_sha256 = 91f40b558d54513de35780825f08314aeb27954b90c284060e1690a8e2116253
original question IDs = F6-MOCK-1516-Q01 ... F6-MOCK-1516-Q12
original count / marks = 12 / 100
school = HKSYCIA Wong Tai Shan Memorial College
session = 2015-2016
paper = Form 6 Mock Examination M2
language = en
source_type = school_mock
proposed source_id = HKSYCIA-WTS-M2-MOCK-2015-16
selected batch_id = JOY-M2-STG-F6-MOCK-2015-16-0428-20260905-Q01-Q03-Q06-Q08
```

The source ID is a NEW explicit mapping proposed by this Design; original
staging has no dedicated source ID. It is not a discovered pre-existing value.
The same paper must retain this source ID if later held questions become
eligible; batch selection must not become a new source identity.

Existing source review root, relative to the current worktree:
`data/staging/f6-mock-1516-source-review-20261020-000001/`.
Its `review-draft.json` SHA is
`39f63346ad66077154253c909a365983545b5452de58adf6f57414069c8505bf`.
Retain this entire unapproved draft and its original evidence unchanged.

| Role | Actual identity | Size / pages |
|---|---|---|
| PP | `6abad9a0a484439f774fe0be66dda3c8915826c43b9dd3070dcaa34d83f61d95` | 1144625 bytes / 19 |
| School solution PDF | `06b42853791168d843745c5150a23edcab0aa8739b87bcf593a433f55c6e1731` | 263387 bytes / 15 |
| PP archive | `5447e1faf93cdfe16afe63eb7104da3b024743aaf8b5d5bb25edf282f321dc7c` | transport evidence, not canonical question identity |

PP is the byte-identical extracted member
`考前冲刺小组课final版本/0428 F6M2 模拟英文卷3（部分名词翻译） 水印.pdf`
of the already-authorized `考前冲刺小组课final版本.zip`.
Use the existing extracted copy under the review root's `sources/`; do not
extract the archive again. School solutions remain at
`/Users/miaohuanjoy/Desktop/AI做题库相关原材料/补课不同专题材料/0428 F6 M2模拟卷 答案.pdf`.
No new source-directory scan is required.

| Original ID | PP file/printed pages | MS file/printed page; printed question | Marks | Difficulty proposal | Controlled primary type |
|---|---|---|---:|---:|---|
| F6-MOCK-1516-Q01 | 2 | 1; Q1 | 4 | 2 | 基本原理求导 |
| F6-MOCK-1516-Q03 | 4 | 3; Q3 | 6 | 3 | 切线与法线 |
| F6-MOCK-1516-Q06 | 7 | 7; Q7 | 6 | 3 | 向量 |
| F6-MOCK-1516-Q08 | 10,11 | 8; Q8 | 8 | 4 | 线性方程组 |

Selection order is exactly Q01,Q03,Q06,Q08, four complete questions / 24 marks.
Keep all subparts. Do not renumber Q6 to match the misprinted MS Q7. The actual
vector content establishes that pairing; record both numbers explicitly.
Q8 source solution omits an explicit reciprocal-variable definition but supplies
its algebra and final result. Preserve this as a review note, not an invented
source step or a claim of verbatim extra explanation. No selected question
requires a diagram. Original page PNGs are evidence, not canonical image files.

Held IDs are exactly Q02,Q04,Q05,Q07,Q09,Q10,Q11,Q12, with their reasons in
`REVIEW.md` and `review-draft.json` (branch/interval conditions, source mistakes,
or missing deduction). They are NOT deleted, accepted, counted as imported, or
silently reclassified. No amendment to the old draft/approval payload occurs.
Later processing requires a separately reviewed proposal and exact approval.
This first implementation accepts only the fixed four-question selection; it
does not introduce a general automatic salvage engine.

## 4. F6 proposal and approval contract

Add internal module `src/joy_m2/ingest/f6_school_mock.py`, with:

```python
inspect_proposal(inputs: dict[str, Path], config: PipelineConfig) -> dict
build_package(
    inputs: dict[str, Path], approval_text: str,
    output_dir: Path, config: PipelineConfig,
) -> Path
```

Do not register a new job in the automatic runner or change its configuration.
Call these module-local entry points within the existing operational workflow.
No new CLI, service, database schema for workflow state, or package-wide export.

`inputs` has exactly `proposal`, `staging`, `review`, `pp`, `ms`. All are regular
files without symlink components. Proposal is strict JSON (duplicate keys and
non-finite values rejected). The exact top-level fields are:

```text
schema_version = f6-school-mock-transcription-v1
source_type, source_id, school, session, paper, module=M2, language
batch_id, parent_source_batch_id
staging_sha256, review_sha256
sources, selection, records, transcription_digest
```

Profile/identities equal section 3. `sources` has exactly `pp` and `ms`; each
has `sha256`, `size_bytes`, `page_count` with actual values above. Check bytes,
PDF signature and page count. Archive path/member remains in retained review
evidence, not as an operational absolute path in the semantic proposal.

`selection` has exactly `selected_ids`, `held_ids`. Both are unique ordered
string arrays; their disjoint union equals all original IDs and order in the
original draft. Each array preserves original question order. The fixed values
are section 3. No implicit discovered-file order or fallback selection.

Each selected record has exactly:

```text
staging_id, question_number, solution_printed_question_number
question_pages, solution_pages, marks, difficulty_proposal
question_text_original, school_ms_original, ms_evidence_level
primary_type, tags, review, review_notes, requires_figure, issues
```

Field types/validation follow the Oxford counterpart's corresponding fields,
except for the explicitly different profile, selection count, source labels and
MS number mapping here. Exact integers reject booleans; page arrays are
nonempty, ascending, unique and in range. Marks/difficulty/pages/IDs equal the
selected original draft rows, with printed MS question numbers from section 3.
`question_number` remains original decimal string 1,3,6,8. Difficulty proposals
remain 2,3,3,4; do not recalibrate.

`review` contains six Boolean keys: question,subparts,formula,marks,figures,
solution. `review_notes` is nonempty text; `issues` is an array of nonempty
strings (may be empty). `ms_evidence_level` is exactly one of
`full_school_ms`, `outline`, `missing`. These are source-adapter review fields,
not new Task 9A issue codes.

Reuse reviewed question content without mathematical rewriting. For the fixed
review artifact, question text equals `question_readable_transcription`.
School solution equals the existing readable-source-solution text before the
single terminal `\n\n原页：` reference paragraph; for Q8, additionally move the
separate paragraph beginning `\n\n来源在(b)省略` into `review_notes`. These are
explicit removals of editor/source-link annotations only, not source mathematics.
Validate the expected separators and source fields; missing/unexpected structure
blocks preparation, rather than using a broad text-cleaning heuristic.
Store all removed annotations in review notes/source mapping. Never inject the
independent corrections for held records into `school_ms_original`.

Taxonomy equals the review draft's `primary_type_proposal_controlled` and
`tags_proposal_controlled` for each selected row, validated against the frozen
formal V1.23 vocabulary. Any changed content/taxonomy must be represented in a
new reviewed artifact and a new approval-bound proposal, not an unrecorded
override of this pinned pilot input.

The digest is SHA-256 of canonical JSON of the entire proposal excluding only
`transcription_digest`: UTF-8, sorted keys, compact separators,
`ensure_ascii=False`, `allow_nan=False`, **no trailing LF** (Oxford convention).
It binds selection and held IDs, source/review/staging hashes, all content,
taxonomy, review notes and mapping. No absolute runtime paths/timestamps.
Relocating unchanged input bytes cannot change this digest.

Inspection returns exactly: `status`, `record_count`, `marks`, `source_type`,
`transcription_digest`, `proposal_path`, `issues`; append `required_approval`
only when eligible. Issue entries have `id` and `reasons`. This return is an
operational report, not a Task 9A issue taxonomy. Status is `REVIEW_REQUIRED`
if any selected row has an issue, incomplete review, invalid controlled value,
missing/non-full school solution, or required unsupported figure; otherwise
`AWAITING_TRANSCRIPTION_APPROVAL`. Structural/identity failures raise
`ValueError` as in the counterpart. Malformed JSON/I/O/PDF exceptions retain
their original boundary and may not produce an eligible status.

Eligible approval is exactly:

```text
USER APPROVED PDF TRANSCRIPTION BATCH <selected_batch_id> <transcription_digest>
```

`build_package` reconstructs the proposal digest, identity and eligibility and
requires the actual exact approval. An approved parent 12-row batch, different
selection, historical Oxford/HKDSE approval, missing approval or altered notes
cannot approve this sub-batch. Persist the real received text as evidence;
never copy a request template into a received-approval file.

## 5. School-source canonical mapping

After source approval and verified V1.24 implementation, use the counterpart's
atomic no-replace, source-overlap and staging-root checks. Return the output
directory, whose manifest is read using `load_v124_import_manifest`.
Revalidate input identities immediately before publication; output bytes derive
from the validated snapshot. Failure cleans only owned temporary output.

Exactly five files:

```text
import_manifest.json
records/candidates.json
source/transcription.json
source/source-map.json
answers/school-ms.json
```

Manifest is the V124 18-field counterpart: candidate_json group contains the
record file, source group contains transcription then source-map, answer group
contains school-ms; other three groups empty. Chapter is `F6 Mock M2 2015-16`.
Keep all existing policy literals; target/schema are section 2.

Candidate array follows selection order and the unchanged 23 caller-supplied
Task 9A fields:

| Field(s) | Mapping |
|---|---|
| proposed_question_id | original staging_id, unchanged |
| source_id / source_question_number | fixed truthful school identity / original number |
| source_section | `Form 6 Mock Examination M2 2015-2016` (selection-independent) |
| source_fragment_hash | SHA-256 of exact UTF-8 question_text_original, no LF added |
| question_text_original | approved English question |
| question_text_zh / translation_status / translation_evidence | empty string / missing / None |
| solution_original / solution_verified / answer_status | approved school_ms_original / empty / source_provided |
| explanation_text / explanation_status / explanation_evidence | empty / missing / None |
| image_paths / image_roles | empty arrays; selected records require no diagrams |
| primary_type / tags | approved controlled values, exact order |
| tag_status | proposed |
| difficulty_level / difficulty_status | approved original suggestion / proposed |
| enrichment_status | incomplete (translation and independent explanation absent) |

Do not copy old AI/unchecked Chinese translations as source-authenticated text.
School-provided solutions are not HKEAA official MS or Oxford publisher MS.
No new translation, enrichment or independent image projection.

`source/transcription.json` is the complete approved proposal. Source-map has
exactly these top-level fields: schema_version,source_type,source_id,school,
session,paper,module,language,batch_id,parent_source_batch_id,staging_sha256,
review_sha256,sources,selection,transcription_digest,approval_text,records.
Values are copied from the approved proposal except the actual approval text,
the schema `f6-school-mock-source-map-v1`, and the record projection. Its record
projection contains staging_id,question_number,solution_printed_question_number,
question_pages,solution_pages,marks,review,review_notes,requires_figure,
ms_evidence_level,issues. Answer file has exactly source_type,school,records;
records contain staging_id,school_ms_original,pages (solution_pages).
Serialize these four content files using the proposal's canonical convention
plus one LF. Manifest encoding follows `_v120_manifest_payload` plus the
counterpart's existing JSON serialization and LF. Each manifest hash/size
binds the actual emitted bytes.

## 6. V1.24 candidate APIs, effective state and verification

Create fixed sibling modules, not a configurable future-version engine.
The thirteen dataclasses have the same fields/order/types/default rules,
validation, tuple copying and nested equivalents as their V123 counterparts:

```text
V124BatchImportManifest, V124AdaptedImportPackage, V124BatchLedgerEntry
V124EffectiveState, V124PreflightRequest, V124ImportPreflightReport
V124ImportPreflightResult, V124ImportApproval, V124ApprovedBatch
V124CandidateContract, V124CandidateBuildRequest
V124CandidateVerificationRequest, V124CandidateArtifacts
```

Entry points retain counterpart signatures with V124 carriers:

```python
load_v124_import_manifest(path: Path) -> V124BatchImportManifest
preflight_v124_import(request: V124PreflightRequest, config: PipelineConfig) -> V124ImportPreflightResult
build_v124_candidate(request: V124CandidateBuildRequest, config: PipelineConfig) -> V124CandidateArtifacts
verify_v124_candidate(request: V124CandidateVerificationRequest, config: PipelineConfig) -> VerificationReport
```

Import from the owning modules. Do not append package-level `ingest.__all__`
exports in this task; no historical export-test migration is needed. No new
HKDSE/Oxford bridge is required to run this F6 pilot.

Reuse only existing genuinely version-neutral helpers (canonical bytes, SHA,
safe path/image destination, normalized SQL, atomic no-replace).
Do not call a historical formal reader with patched constants. Frozen source
adapters, models, normalization, sixteen issue codes, collision ordering,
raw-field schema and historical digest algorithms remain unchanged.

Build baseline indexes from all 677 V1.23 formal rows and augment them from the
independently verified ordered V1.24 parent prefix. Preserve exact-duplicate,
collision and adaptation predicates from the V123 counterpart. Fuller answers
alone do not bypass identity/collision. All mixed duplicate/blocker batches
stay blocked; approval never overrides a blocking issue.

```text
before = 677 + verified parent candidate_count
detected = new_candidate + duplicate + rejected
projected_after = before + new_candidate
```

Ambiguous remains a rejected subset; adaptations are not additional questions.
For this pilot, 681 is only conditional arithmetic if actual preflight accepts
all four records. Report observed classification; never predeclare READY/new.
Selection cannot be changed after preflight to silently salvage the batch.
Any subsequent subset decision creates a separately reviewed/approved payload;
it does not change old source IDs, fingerprints or accepted history.

Exact real import approval:

```text
USER APPROVED IMPORT BATCH <batch_id> <preflight_sha256> V1.24 PARENT <parent_candidate_digest>
```

Reconstruct exact READY preflight, source package and ordered approved prefix
before build; reject stale target/content/parent/prefix, duplicate batch, wrong
approval or missing evidence. Operational callers freshly recover the actual
latest verified V1.24 receipt; an immutable artifact is not a global latest
pointer. Existing cycle.lock serializes real writer operations without changing
the scheduler. An already accepted batch returns its verified receipt, not a
second append. Changed parent requires new preflight and exact import approval.

Private build copies formal V1.23, preserves all inherited objects/data, appends
only the new V124 namespace, and changes user_version only on that private copy.
New rows remain candidate/selectable=0, never published. Verify before atomic
no-replace generation publication. Failure leaves parent and formal data intact;
rollback metadata describes the new staging generation, not permission to
delete a live generation. No overwrite, live rollback or formal path permitted.

Independent verifier retains all 24 counterpart checks/order, changing only
the historical preservation check label `v122_preservation` to
`v123_preservation`. It independently reconstructs approval/genesis, parent
chain, preflight, candidate projection, baseline preservation and artifact
closure. Preserve exception/structured-failure boundaries. It cannot repair
or trust writer output as its expected oracle.

## 7. Closed engineering scope and test dependency order

Current docs checkpoint touches only this Design and PROJECT_STATE.md.
Subsequent Plan, after human written Design approval:
`docs/superpowers/plans/2026-10-20-f6-selected-batch-v124-candidate.md`.

After written Plan review and execution authorization, production scope is:

```text
NEW src/joy_m2/ingest/f6_school_mock.py
NEW src/joy_m2/ingest/v124_models.py
NEW src/joy_m2/ingest/v124_manifest.py
NEW src/joy_m2/ingest/v124_preflight.py
NEW src/joy_m2/ingest/v124_writer_profiles.py
NEW src/joy_m2/ingest/v124_writer.py
NEW src/joy_m2/ingest/v124_verification.py
NEW tests/unit/test_v124_models.py
NEW tests/integration/test_f6_school_mock.py
NEW tests/integration/test_v124_preflight.py
NEW tests/integration/test_v124_candidate.py
NEW tests/regression/test_v124_historical_replay.py
NEW docs/reports/F6_V124_CANDIDATE_VERIFICATION.md
MODIFIED PROJECT_STATE.md
```

No historical production/test change, automatic runner, config, AGENTS.md,
dependency, shared-model or formal-artifact change is included. If a proven
necessary file falls outside this list, report only that scope gap. Do not
weaken assertions or widen source matching to make tests pass.

Runtime outputs use new ignored directories under
`data/staging/f6-mock-1516-selected/` and `data/staging/task14-v124-f6/`.
Retain existing F6 review and original staging byte-for-byte. Store actual
approvals/receipts separately; no committed real PDFs or generated databases.
Use existing local backup tooling/explicit file-list policy after approved
operational writes; Git is not a backup of ignored data.

The Plan must order valid behavioral RED then minimal GREEN:

1. Module/model API tests, minimal usable carriers/scaffolds; strict manifest.
2. Baseline loader/DDL/genesis primitives and source proposal validation.
3. F6 exact-approval canonical mapping and independent byte expectations.
4. Genesis preflight, then first-generation writer/independent verifier.
5. Verified-parent preflight, then second-generation append/replay protections.
6. Historical regression, independent implementation review and remediation.
7. Real four-question proposal gate; only after its exact approval, canonical
   and actual current-parent preflight; stop at real import approval.

Import/setup/fixture errors are not behavioral RED. No parent-preflight claim
before a valid first generation exists, no second-generation writer RED before
verified-parent preflight is usable. Use isolated synthetic approvals and PDFs
for tests, never fake a human approval for the real F6 batch. Independent
expected projections must not be produced by the writer under test.

Required focused coverage:

- exact selected/held partition; four IDs/order and 24 marks; whole-question
  retention; unauthorized selection, relabeling and source-profile rejection;
- Q6 printed-Q7 mapping; Q8 editorial note separation; English not copied into
  Chinese/source-present fields; no generated explanation or diagram;
- full versus outline/missing source solution; structural/type/duplicate-key
  errors; taxonomy; source/draft/review hash tampering; partial review;
- digest change on selection/content/notes, same bytes at different roots;
  exact approval, stale approval and parent-12-row approval rejection;
- safe paths, source overlap, symlinks, source changes during build, atomic
  no-replace, failure cleanup and deterministic five-file closure;
- 677 unique baseline rows, schema/view exactness, no double-count of inherited
  tables, all historical objects preserved and source-image JSON unchanged;
- independently reconstructed genesis, old/null/empty/wrong parent rejection;
  second-generation parent chain, stale approval and ordered prefix checks;
- same-source repeats and collisions against baseline/accepted candidates;
  preserve mixed blocker semantics, no automatic post-preflight row deletion;
- candidate tampering, duplicate batch, independently verified replay,
  byte-identical two-root candidates, parent/formal zero mutation.

Before implementation delivery run fresh focused and current maintained gates,
historical replay and formal verifiers through V1.23, V1.18 validator, protected
hash checks, diff/scope checks, and independent review with Critical=0 and
Important=0. Report actual counts, not old test totals. Docs-only checkpoints
need identity/scope/diff checks, not a full suite or repeated backup restore.

## 8. Human workload, current stop and non-goals

Written Design review is complete. Current stop:
**USER DECISION REQUIRED — F6 / V1.24 IMPLEMENTATION PLAN REVIEW**.
The written Plan is `docs/superpowers/plans/2026-10-20-f6-selected-batch-v124-candidate.md`.
No implementation, source approval digest, canonical, authoritative preflight,
real candidate write or release is created at this docs-only checkpoint.

After written Design and Plan gates, ordinary engineering/source checks proceed
without per-question review. Present the selected four-question transcription
as one batch, then the actual import result as one batch. Only precise unresolved
mathematical/source conditions or frozen-contract conflicts need extra decisions.
Held questions stay visible but do not force this eligible selection to wait.

Real candidate acceptance is NOT formal publication or teaching selectability.
A later separately authorized promotion is still required to increase formal
queryable records. This task creates neither `releases/V1.24/` nor a promotion
Design/API and never alters releases/V1.18–V1.23. Preserve 2024 evidence,
all previous approvals, candidate generations, daily scheduling and original
user AGENTS.md changes.
