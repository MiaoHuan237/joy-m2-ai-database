# V1.23 Minimal Candidate Roll-Forward / HKDSE 2023

Date: 2026-10-09

Status: APPROVED — V1.23 WRITTEN DESIGN; PLAN REVIEW / EXECUTION APPROVAL PENDING

## 1. Approved direction, not implementation approval

The user approved this written Design and authorized preparation and independent
review of its implementation Plan. The fixed V1.22/639 -> V1.23 direction and
written Design gates are complete; do not request them again. Obtain human Plan
review and execution-method confirmation before implementation. This Design
approval does not authorize a real batch import or promotion.

The goal is usable PP/MS material, not historical cleanup. Keep existing
multi-source records, the 24 audited historical pairs, and all historical
approvals. Their cleanup is not an entry condition. The 639 baseline count is
a formal-record count, not a claim of 639 semantically distinct original exams.
No real import, promotion, 2024/2025 processing, or V1.24 work is authorized.

The normative implementation counterpart is the six `v122_*` candidate modules
and HKDSE V1.22 bridge at `d006c502fd30bb9c655ed8c4694148c16b036f56`, under
`2026-09-21-v122-next-version-candidate-design.md` and its reviewed Plan.
Historical normalization, classification, digest projection and replay semantics
are preserved, not inferred from a broad label such as "dedup".

## 2. Frozen baseline identity

Read the published V1.22 release and verify exact identities before preflight,
candidate build or candidate verification. No reconstruction of formal data.

```text
release_version = V1.22
release_status = published
release_model = append-only-multi-batch-promotion
question_count = 639
database_schema = task12-v122-formal-v1
manifest_schema = task12-v122-formal-manifest-v1
formal_view = formal_complete_questions_v122
SQLite path = releases/V1.22/Joy_M2_Complete_Question_DB_V1_22.sqlite3
SQLite SHA-256 = a474846a5b1d10a0fe48a259522fbb327747319f4a114452bf9f294405d8d9e0
SQLite size_bytes = 10510336
manifest path = releases/V1.22/manifest.json
manifest SHA-256 = 441e00ac1536b959b40b6177bd17a6f14632a287f85145e202a51bcf137ddc8b
manifest size_bytes = 7915
release digest = 89a592abf52507cc0325f9c6f30ee2c74d4ec55fdcef988fdae6cb12f5a3073b
semantic SHA-256 = 964cceff64cdeaedf663d1f9be98aaaf6adf3ffe2cddf6a18447ea141948a1c4
```

These values were read from actual files, formal manifest and read-only SQLite.
Use an escaped `Path.as_uri()` SQLite URI with `mode=ro`, query-only operation,
integrity/FK checks and exact metadata. Read rows 1..639 once through the formal
view, all published/selectable with unique record IDs. Never use the older
591-row view or add inherited candidate tables again: the 2019–2022 48 records
are already included in 639. Preserve all inherited schema, metadata, rows,
source-image identity and historical approval content in candidate copies.

V1.18–V1.22 formal bytes, all prior generations, raw sources, mapping,
transcription and approval artifacts remain immutable. Daily formal querying
still selects V1.22/639. Do not create `releases/V1.23/` or change a pointer.

## 3. Minimal approach and alternatives

Choose fixed V1.23 sibling modules with the existing multi-batch mechanism.
This is the smallest approach that preserves independent version identities,
stale-parent rejection and append verification without rewriting history.
Reuse already-version-neutral helpers only when their behavior is truly free
of baseline/schema/version constants. No hidden calls to a V1.22 reader with
monkey-patched constants. No historical-module generalization or blind global
replacement. A configurable future-version engine is explicitly rejected.
Appending to the published V1.22 lineage is also rejected.

The two independent tracks are:

1. Written Design -> human approval -> written/reviewed Plan -> execution
   authorization -> RED/GREEN -> independent implementation review -> gates.
2. Existing Task 10B source reuse -> complete 2023 proposal and taxonomy checks
   -> exact human transcription approval. This track does not wait for track 1.

Only when both tracks pass may an approved transcription enter the V1.23 bridge
and parent-bound preflight. Real candidate writing waits for a third, exact
batch-import approval. Engineering approval never substitutes for either data
approval. No two workers write the same proposal or engineering file.

## 4. Existing acceptance semantics: disclose before implementation

The normative predicates and ordering are `v122_preflight.py::_is_exact_duplicate`,
`_collision_issues`, `_classify`, `_report_values` at the counterpart commit.
Retain all sixteen issue codes; add no "same exam" or "source supplement" code.

Reference matching uses record ID, `(source_id, source_question_number,
source_section)`, raw source-fragment SHA, normalized question-text SHA and
image path/role/hash bindings. It does not implement a semantic year/question
equivalence engine. Answer text/marking-scheme completeness is not an exact-
duplicate identity predicate. Human evidence of the same original and machine
classification must therefore be reported separately.

| Input situation | Existing outcome, assuming no other blocker | What it does NOT authorize |
|---|---|---|
| Exact source locator + fragment SHA + normalized SHA + ordered image identity against one baseline/accepted-parent record | `duplicate`, with blocking `duplicate_exact`; the batch is BLOCKED, not READY with a skipped row | No update of old MS, images or source associations even if the submitted answer is fuller |
| Same source locator but changed fragment/text/image identity | Structured collision, normally `rejected` | No overwrite/correction or collision bypass |
| Different truthful source locator, but same raw or normalized question hash | Matching collision, normally `rejected`; multiple nonexact matches can be ambiguous/rejected | Different source alone does not force acceptance |
| Same original identified by page evidence, but independently transcribed truthful source and no matching indexed identity signal | May be `new_candidate` after all other checks | This means a new stored record, NOT proof of a new original question |
| One formal-baseline match, same locator and fragment, different normalized text, no candidate-ID signal | Existing `ImportAdaptation(kind="adapted")`; may remain `new_candidate` if no independent blocker | No invented raw hash, no old-record mutation, no extra count beyond the candidate record |
| Genuinely new original with no signal match and all checks satisfied | `new_candidate` | No automatic import approval |

Exactness requires a formal-baseline or already-accepted-parent reference,
not an earlier unaccepted record in the current package. More than one exact
reference, or multiple matches with none exact, is `duplicate_ambiguous` and
`rejected`. A single exact match does not hide collisions with other references.
Candidate-associated blockers retain the counterpart's per-record rejection
semantics even for an otherwise exact match. Package-level initial issues
block the batch without necessarily changing a record's `duplicate`
classification; an unreadable/untrusted candidate file can instead prevent
its records from being loaded. Preserve these existing count/classification
boundaries rather than treating every package issue as a record rejection.
Do not deduplicate the already-published baseline to simplify these indexes.
All emitted preflight issues retain their blocking severity. In particular a
mixed batch containing an exact duplicate does not silently import the rest;
the current batch remains blocked. Do not autonomously remove that input row
or treat approval as an override. Report the preserved classification and
request only the affected source/disposition decision when necessary.

### 4.1 The actual 2023 case

The source audit confirms the twelve existing `2023-Q1`–`2023-Q12` records
correspond to the supplied Chinese PP. They are not twelve newly discovered
original questions. Original user staging already declares IDs
`HKDSE-2023-M2-Q01`–`HKDSE-2023-M2-Q12`; retain those source-declared IDs and
truthful PP/MS provenance. Do not rename records, alter legitimate transcription
to defeat a match, forge fragments, or suppress issues to force `new_candidate`.

Until the approved implementation runs authoritative preflight there is no
classification count. After approval/implementation, preserve that result and
add a human-facing source-reconciliation table (report only, not digest/schema):
new stored records; already-known originals with another source; proposed
content/evidence supplementation; genuinely previously unrepresented originals.
For this audited 2023 paper, twelve originals are already represented; do not
describe `new_candidate_count` as twelve new originals. Do not predeclare that
count or projected total.

The current writer appends accepted candidate rows; it has no operation that
attaches a second source or replaces an answer inside an existing formal row.
`duplicate` inputs do not install their fuller MS into an old record. If 2023
is blocked by a preserved collision or the desired outcome is an in-place
source/answer supplement, report the exact affected IDs/signals and stop at the
frozen-authority gate. The minimal subsequent decision is whether to keep this
source package as external teaching evidence or separately specify a narrowly
scoped source-association/correction operation. This Design chooses neither
such operation and does not authorize modifying dedup. No whole-library cleanup
is required. A READY append of a truthful additional source remains subject to
the exact import approval showing its known-original relationship.

## 5. Exact versioned models and exports

Create the thirteen counterpart frozen dataclasses in `v123_models.py`, in
the following public suffix order (field counts in parentheses):

```text
V123BatchImportManifest (18)
V123AdaptedImportPackage (3)
V123BatchLedgerEntry (9)
V123EffectiveState (5)
V123PreflightRequest (5)
V123ImportPreflightReport (34)
V123ImportPreflightResult (5)
V123ImportApproval (5)
V123ApprovedBatch (3)
V123CandidateContract (25)
V123CandidateBuildRequest (3)
V123CandidateVerificationRequest (3)
V123CandidateArtifacts (8)
load_v123_import_manifest
preflight_v123_import
build_v123_candidate
verify_v123_candidate
adapt_verified_hkdse_pdf_transcription_v123
```

Exactly preserve counterpart field names/order/runtime types/no-default rules,
tuple copying and validation; substitute nested V123 carrier types and only
this document's fixed version/baseline constants. Exact integer rules reject
bool. Shared ImportCandidate/ImportAdaptation/ImportIssue/ImportFileEvidence,
ArtifactRef, VerificationReport, and Task 9A contracts remain unchanged.
Append these eighteen names after the entire current package surface, including
all nine V1.22 promotion names; no aliases or V1.23 promotion API.

## 6. Fixed target and genesis

```text
profile = V1.23
baseline_release_version = V1.22
baseline_question_count = 639
canonical_manifest_schema = task13-v123-import-manifest-v1
preflight_schema = task13-v123-preflight-v1
approval_schema = task13-v123-import-approval-v1
candidate_manifest_schema = task13-v123-candidate-manifest-v1
candidate_database_schema = task13-v123-candidate-v1
candidate_identity_schema = task13-v123-candidate-identity-v1
rollback_schema = task13-v123-rollback-v1
expected_user_version = 123
database_filename = Joy_M2_V1.23_candidate.sqlite3
manifest_filename = candidate_manifest.json
sha256s_filename = SHA256SUMS
rollback_filename = rollback.json
authority_root = authority/batches
image_root = images/sha256
required_baseline_view = formal_complete_questions_v122
required_candidate_tables = task13_v123_batch_ledger_v1,
  task13_v123_candidates_v1, task13_v123_images_v1, task13_v123_taxonomy_v1
required_candidate_views = task13_candidate_questions_v123
```

Baseline SHA/size/release constants are exactly section 2. `task13` is a fixed
serialization namespace, not another engineering project. The new DDL matches
the counterpart columns, order, constraints and relations under this explicit
new namespace, with baseline 639 and first new aggregate_order 640. Do not
rename inherited task9/task10/task11/task12 schema objects or source authority.

Genesis is SHA-256 of precisely the following UTF-8 object serialized with
sorted keys, compact separators, ensure_ascii=False, allow_nan=False and one LF:

```json
{"baseline_database_sha256":"a474846a5b1d10a0fe48a259522fbb327747319f4a114452bf9f294405d8d9e0","baseline_question_count":639,"baseline_release_digest":"89a592abf52507cc0325f9c6f30ee2c74d4ec55fdcef988fdae6cb12f5a3073b","baseline_release_version":"V1.22","candidate_count":0,"schema":"task13-v123-genesis-v1","target_release_version":"V1.23"}
```

Computed digest: `ea3b7db78210e045761784a2e415387c1b17f13b5aedde484ca2ae248a45eec7`.

First-generation `parent_candidate=None` means no parent ARTIFACT/PATH only.
The preflight report and import approval MUST still bind the exact genesis
digest above. None/empty/omitted digest, another version's genesis, or a modified
projection is invalid. Writer and independent verifier each reconstruct the
canonical genesis and compare it against preflight AND approval, rather than
merely comparing two supplied equal strings. For generation 000002+, require
the independently verified immediately preceding V1.23 generation and exact
digest/ordered prefix. Genesis cannot replace a real parent. No old V1.22
generation or import approval is a V1.23 parent/approval.

## 7. Canonical bridge and source fidelity

API signatures retain the counterpart forms, with exact V123 carriers:

```python
load_v123_import_manifest(path: Path) -> V123BatchImportManifest
adapt_verified_hkdse_pdf_transcription_v123(
    verified: VerifiedHkdsePdfTranscriptionBatch, output_dir: Path,
    config: PipelineConfig,
) -> V123AdaptedImportPackage
preflight_v123_import(request: V123PreflightRequest, config: PipelineConfig) -> V123ImportPreflightResult
build_v123_candidate(request: V123CandidateBuildRequest, config: PipelineConfig) -> V123CandidateArtifacts
verify_v123_candidate(request: V123CandidateVerificationRequest, config: PipelineConfig) -> VerificationReport
```

Bridge only exact approved Task 10B carriers after reconstructing their digest
and approval. Same five-file layout: import_manifest.json,
records/candidates.json, source/transcription.json, source/source-map.json,
answers/official-ms.json. Preserve counterpart projection byte semantics for
the same approved carrier; only the import manifest selects the new target and
schema. Do not silently omit duplicate-looking source records from the input.
Preserve complete questions/subparts, source wording, MS, marks, page locators,
raw source hashes, taxonomy and difficulty. No automatic MS enrichment.

Task 10B figure references remain exact PDF SHA/page/region references. Reviewed
local Q6 crops can accompany the transcription evidence, but the current bridge
does not automatically turn them into canonical image files. Do not claim it
does. Preserve the established incomplete-enrichment semantics when canonical
image bytes are absent. Reuse explicit source evidence for teaching; any request
to extend canonical image projection beyond the existing bridge needs a
separately reviewed scope decision, not a hidden addition to this roll-forward.

All output is atomic, no-replace, staging-only; reject symlink/path escape,
source overlap, duplicate JSON keys, wrong field/type/group/order and stale
approval. No transcription approval is reused for altered proposal content.

## 8. Effective state, digest, approval and append

Preflight checks fixed baseline bytes/manifest/metadata and builds reference
indexes from all 639 formal rows, then independently verifies the entire parent
prefix and augments indexes with its accepted candidates and taxonomy. Preserve
normalization, sixteen-code taxonomy, classification precedence and ambiguity
as rejected-subset semantics. Preserve error boundaries: unestablishable safe
input/baseline/parent authority raises the approved exception; representable
candidate/file problems produce structured blocking issues. No fake READY.

```text
before_count = 639 + verified parent V1.23 candidate_count
detected_count = new_candidate_count + duplicate_count + rejected_count
projected_after_count = before_count + new_candidate_count
```

An adaptation is evidence attached to a classified input; do not add its count
again. Preserve existing approval-count behavior and duplicate-only handling,
with no special force-import route. Preflight/digest remain path-independent:
counterpart canonical serialization of schema/target, baseline, ordered parent
chain, source/candidate/file identities, classifications, issues and report.
No cwd, absolute path, timestamp or filesystem discovery order enters identity.

The only import approval is:

```text
USER APPROVED IMPORT BATCH <batch_id> <preflight_sha256> V1.23 PARENT <parent_candidate_digest>
```

V123ImportApproval plus V123ApprovedBatch carries that exact statement and the
exact READY result. Writer reconstructs approved preflight and all earlier
accepted batches from their evidence; stale text/package/parent/target,
reordered prefix, historical approval and duplicate batch identity are rejected.
The orchestrator must freshly verify the selected latest candidate checkpoint
before consuming approval. Explicit immutable generations do not provide a
global filesystem "latest" oracle: no speculative pointer/locking service is
introduced. A changed operational parent invalidates earlier approval.

Build only after explicit real approval (isolated synthetic tests excepted).
Copy the frozen baseline into an owned private staging sibling, preserve all
inherited objects/rows, add only the four V123 tables and ordered union view,
and change only the private copy's user_version to 123. New rows remain
candidate/selectable=0. Rebuild the ordered approved V123 prefix without
modifying a prior generation. Independently verify before no-replace atomic
publication; failure cleans only owned temporary output. Parent/formal bytes
and previously accepted artifacts must remain unchanged.

The independent verifier preserves the counterpart's 24 checks and order,
renaming only `v121_preservation` to `v122_preservation`. It verifies baseline,
authority files, exact genesis/parent/approval reconstruction, preflight,
filesystem/SHA closure, ArtifactRefs, rollback, images, SQLite integrity/FK/
schema, inherited preservation, ledger, candidate projection, collision/count
closure, candidate identity, determinism and formal boundary. It never repairs.
Rollback evidence describes the new staging generation only; no deletion or
formal rollback is authorized.

The current V1.22 manifest has no newly promoted images, but inherited formal
rows still contain historical image references. Empty manifest `images` does
not authorize clearing those references. Preserve all four formal/source image
columns, their JSON encodings and the inherited view chain; validate existing
image identity according to its historical contract, not a newly invented
requirement that every historical path be re-staged under the V1.23 root.

## 9. 2023 operational preparation and stopping points

Current checkpoint: preparation and exact human transcription approval are
complete. Under `data/staging/task10b-hkdse-2023/source-review-000001/`, the
immutable proposal is `transcription-proposal-000001/transcription.json`, digest
`3a3a223a23f694083469281c64be5c5402152c557e3bc36654d400ce5143d618`; the actual
received approval is `TRANSCRIPTION_APPROVAL.json`. Corrected staging is
`input/source-corrected-staging-v2.json`, SHA
`351462b3e45d4ea0f5b84b400d28aa0431bf3c0a830b16aff8a2eda7940a7490`.
The existing approval API verifies 12 complete records / 100 marks, zero issues.
No canonical/preflight has run. The preparation rules below remain the source
contract, not instructions to repeat completed work or seek the same approval.
Reapproval is required only if the actual approved semantic payload changes.

Input identity (already present, no reupload required):

```text
batch_id = JOY-M2-HKDSE-2023-PP-MS
original staging = joy_m2_hkdse_2023_pp_ms_staging.json
staging SHA = 4114f8671f9503070b7495925502bc21049d32fb33dd85096916bff9bd304b64
PP = M2_2023-pp.pdf
PP SHA = ec60f6d978a44b7e3ce2e20e704ed6307655efeafa984a88e6567b0254275dfd
PP pages = 28
MS = M2_2023-ms.pdf
MS SHA = 5a8b56914dee3931d4e1f826b721360ad0a59c33056dba01caf272140a0f7d97
MS pages = 27
records = 12 complete questions
marks = 100
```

Reuse local source pages and source-reconciliation evidence, not the whole
2012–2025 inventory. Historic answers are comparison material, not authoritative
full MS. Supplement exact official steps/marking notes and alternative methods;
retain Q6's two figures with explicit source evidence; preserve Q7's condition
over all of (b); transcribe Q10 faithfully without historical escape artifacts.
Use the unchanged controlled vocabulary before the final approval proposal.
Do not automatically copy a wrong historical topic (notably Q10's vector content).

If staging page anchors/taxonomy need source-backed correction, create an
explicit new reviewed staging copy and retain original bytes. Two-pass review
must be genuine, not identical copied passes labelled independent. Use existing
Task 10B APIs for proposal/digest; preserve intermediate evidence and any earlier
proposal. Uncertain text remains a precise review item with page evidence.

Stop at PDF TRANSCRIPTION REVIEW if unresolved, or PDF TRANSCRIPTION APPROVAL
with the actual new digest when complete. No placeholder digest or fabricated
approval. Written Design approval is separately requested; neither gate implies
the other. No canonical/preflight while the implementation or transcription
approval is missing. When both exist, compare two-root package/preflight results
and stop at REAL BATCH IMPORT, showing actual counts, issues, source relationship,
parent and preflight SHA. Do not start 2024 afterwards.

## 10. Closed scope

Current Plan docs checkpoint: this Design's progress state, its implementation
Plan and PROJECT_STATE.md only; no technical-contract change. Runtime
transcription evidence is ignored under
`data/staging/task10b-hkdse-2023/source-review-000001/**`; preserve all inputs.
Written-Design approval has been received; Plan creation/review is now authorized.

After Design/Plan/execution approval, the proposed engineering scope is exactly:

```text
NEW src/joy_m2/ingest/v123_models.py
NEW src/joy_m2/ingest/v123_manifest.py
NEW src/joy_m2/ingest/v123_preflight.py
NEW src/joy_m2/ingest/v123_writer_profiles.py
NEW src/joy_m2/ingest/v123_writer.py
NEW src/joy_m2/ingest/v123_verification.py
MODIFIED src/joy_m2/ingest/hkdse_pdf_adapter.py
MODIFIED src/joy_m2/ingest/__init__.py
NEW tests/unit/test_v123_models.py
NEW tests/integration/test_v123_hkdse_bridge.py
NEW tests/integration/test_v123_preflight.py
NEW tests/integration/test_v123_candidate.py
NEW tests/regression/test_v123_historical_replay.py
MODIFIED tests/unit/test_v119_writer_models.py
MODIFIED tests/unit/test_v119_promotion_models.py
MODIFIED tests/regression/test_v119_historical_replay.py
MODIFIED tests/unit/test_v121_promotion_models.py
MODIFIED tests/unit/test_v122_models.py
MODIFIED tests/unit/test_v122_promotion_models.py
MODIFIED PROJECT_STATE.md
NEW docs/reports/V123_CANDIDATE_AUTHORITY_VERIFICATION.md
NEW docs/superpowers/specs/2026-10-09-v123-next-version-candidate-design.md
NEW docs/superpowers/plans/2026-10-09-v123-next-version-candidate.md
```

The six historical test paths allow only precise public-surface expectation
migration: preserve every historical name/order and append the eighteen names;
replace stale absolute-tail assertions with exact historical-prefix plus exact
new-suffix coverage. No subset-only weakening, changed lifecycle/hash/behavior
assertion, skip or expectedFailure. Adapter edits only append the V123 bridge
and required imports; existing source extraction, approval and bridges stay
unchanged. No other historical production module or shared model is editable.
If another necessary file is discovered, request a minimal scope decision first.

Later operational canonical/preflight evidence only under ignored
`data/staging/task13-v123-hkdse-2023/**`; real candidates there require exact
import approval. One-off scratch may use ignored tmp or system temporary roots;
no alternative maintained entry point, committed real corpus or dependency.
Synthetic tests use isolated temporary inputs, never a fake 2023 approval.

The pre-existing user edit to AGENTS.md must not be overwritten, staged,
committed, stashed or reset. Dirty unrelated files do not demand cleanup.
Explicitly stage only reviewed task-owned docs/engineering paths. Ordinary
commits/pushes only; no force, amend, rebase, squash, merge, PR or tag.

## 11. RED-first verification and reviews

Plan dependency order: exact model/API RED -> minimal model GREEN -> bridge
behavior RED/GREEN -> baseline/effective-state scaffolding RED/GREEN ->
parent-bound preflight RED/GREEN -> multi-batch writer/verifier RED/GREEN ->
independent review/remediation -> complete gates -> operational preflight gate.
Setup/import/fixture failure never proves behavior RED. A scaffold cannot
justify implementing untested later behavior. No test expectation changes just
to hide a classifier limitation.

Mandatory negative controls: exact type/default/field order, baseline SHA/size/
manifest/schema/view/count, reading 591 instead of639, counting inherited
candidate tables twice, historical/genesis/null/empty/wrong parent, forged equal
approval/preflight parent, second-generation genesis reuse, old import approval,
stale/reordered parent prefix, collisions against each inherited formal layer
including 2019–2022, fuller-answer exact duplicates, truthful second sources
with matching/nonmatching hashes, adaptation predicate boundaries, mixed
duplicate/blocker batches, source/image integrity, unsafe output, no-replace
failure and parent preservation, candidate tampering and formal-path refusal.

Positive evidence: all639 baseline rows preserved; same-original-vs-new-record
report distinction; deterministic two-root package/preflight/SQLite/artifact
identities; synthetic first/second generations; eighteen exact new exports;
historic API/digest/replay unchanged; all formal hashes unchanged.

Before implementation delivery run all current maintained gates with actual
counts, no unexpected fail/error/skip/expectedFailure, new focused suites,
Task9A, Task10B, Task7, historical replay, V1.18 validator, historical formal
verifiers through V1.22, diff/scope checks and frozen hash snapshots. Do not
re-run the full suite just to claim a docs checkpoint. Keep known legacy
attribution separate; do not add a failure category. Never search/read/hash
the actual V1.16 historical ZIP; retain its approved constant rule.

Independent Design and implementation review must report Critical=0 and
Important=0 before their respective commit/delivery; identify reviewer and
evidence, not self-review labelled independent. Human written Design review,
Plan review/execution authorization, exact transcription approval, exact real
import approval and any future promotion gate remain distinct.
