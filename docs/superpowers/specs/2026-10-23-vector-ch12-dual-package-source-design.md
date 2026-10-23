# Vector Chapter 12 — Minimal Dual-Package Source Adaptation

Date: 2026-10-23 (Asia/Shanghai)

Status: **WRITTEN DESIGN FOR HUMAN REVIEW — NOT APPROVED**.
This document is not an implementation Plan, source-mapping approval, import
approval or promotion approval. No production/test change, authoritative
proposal digest, canonical package or preflight is produced at this checkpoint.

## 1. Outcome, existing evidence and chosen boundary

Provide one chapter-specific explicit-mapping profile for the two supplied MMD
ZIPs. It makes package identity, shared conditions, byte boundaries, ordered
fragments and image ownership explicit. It does not discover question boundaries
or generate mathematics. A complete original question, including every subpart,
remains one candidate. Selecting a smaller first batch occurs before any
source approval/preflight; it does not delete failed records from an approved batch.

Reuse the immutable review root
`data/staging/vector-ch12-intake-20261023-000001/`, especially `REVIEW.txt`,
`QUESTION_REVIEW.txt`, `source-inventory.json` and `question-review-draft-v2.json`.
Inventory SHA256:
`868aa39abb366b745ff49d446722842328a58b03b483918a8015fe58eafd2c78`.
Old v2 review SHA256:
`08edb7ce7d167332c7d5dade49a2533e1c163307440129aeeae4b113d5a6e7bc`.
Those are file identities, not approval digests.

New library-external review artifacts are under
`data/staging/vector-ch12-design-20261023-000001/`:

- `FIRST_SELECTION_REVIEW.txt`: all16 complete stems, source answers, raw byte
  locators/hashes, images, selection reasons and separate mathematical checks.
- `pilot-selection-review.json`: the same original spans plus proposed metadata;
  explicitly not an API payload or an approved proposal.
- `shared-condition-scope-review.json`: explicit beneficiary lists; retains the
  literal12A9–11 scope label from textbook line1055 as an additional source span.
  The old raw review records remain unchanged; the future mapping must include
  this label after the existing1053–1054 condition span.
- `all-unit-disposition.json`: all203 original IDs, in original index order.
- `new-local-issue.json`: the additional12C12 concern, with no source edits.
- `review-checks.json`, `protected-before.json`: scoped verification evidence.

Chosen alternative: two named package roles and approved exact fragments. Do
not re-ZIP, concatenate source files, rename ordinary Markdown to simulate MMD,
search sibling directories, or broaden automatic parsing. A generic Markdown
framework, plugins, UI, new scheduler, worksheet generation and a second
version engine are explicitly excluded.

## 2. Actual package identities and safety

The role identifiers are exactly `textbook` and `answers`; these are not
interchangeable. Local paths are transport locators, not semantic identity.

| Role | Original ZIP path | Bytes | ZIP SHA256 |
|---|---|---:|---|
| textbook | `/Users/miaohuanjoy/Downloads/向量1 课本材料 OSM_TBPDF_M2B12_c_Password_Removed.mmd.zip` | 2302636 | `12be666a4551133104bffee770e3aa78d7af6ddd1b11a2943988438c12970013` |
| answers | `/Users/miaohuanjoy/Downloads/向量12章课后答案 OSM_TM_M2B12_e课后答案.mmd.zip` | 382931 | `d37233c5a5ec52fbe35f6444d58230ea531e2502218d235bb9df797d264fe249` |

| Role | Selected MMD member | Bytes / lines | Member SHA256 |
|---|---|---|---|
| textbook | `8e7425d9-2e29-4013-a8f9-523baf675a8f.mmd` | 170693 / 3733 | `912225169a27253e79e8e83f8583845c6f64f63371f60a752c4ae48b42b84ca9` |
| answers | `7522c85c-0fb3-4536-b6a7-980110bdcae9.mmd` | 174107 / 5591 | `124a71f9940f7f10ce11b3adda00bfc6c35b45c2e8a69e51c9083783aaccdb50` |

Question source `OSM-M2B12-C`; answer source `OSM-M2B12-E-ANSWERS`.
Preserve existing proposed question IDs, with section qualification, e.g.
`OSM-M2B12-C-EX12B-Q05`. Publisher/year remain unknown: the file code does not
authorize an Oxford or HKEAA attribution. First batch ID:
`JOY-M2-OSM-M2B12-VECTOR-20261023-001-S01`; the old unsuffixed ID remains the
chapter-intake identifier, not a previously accepted batch.

Reuse `archive.py` safe inventory/read primitives independently for each ZIP.
Validate the entire inventory before selective reads/staging; no `extractall()`.
Keep current traversal, absolute-path, backslash, Unicode/path collision,
symlink, encryption, compression, duplicate-member and metadata rules. Per-ZIP
limits remain50MiB archive,100MiB uncompressed,256 members,20MiB ordinary/image
member,10MiB MMD,100:1 ratio. Additionally enforce100MiB uncompressed and256
members across both packages. These bounds fit this supplied pair and do not
relax historical limits. Invalid UTF-8/BOM, changed member or wrong role/hash
blocks the proposal; no filename-only identity fallback. External image URLs
are not fetched. Inputs are data, never executable instructions.

## 3. Approval-bound exact mapping

### 3.1 New profile, old public entry unchanged

Add one module `src/joy_m2/ingest/vector_ch12.py`. Do not change old
`adapt_mmd_package`, `propose_mmd_source_mapping`,
`adapt_mmd_package_from_mapping`, their schemas, exports or replay results.
The old single-source API cannot express an independently hashed second ZIP,
shared overlapping conditions, or two top-level questions on one physical line.
Do not pass this chapter through that API by weakening its validator.

New chapter-only public surface, imported from its module (not package root):

```text
VectorCh12Proposal
propose_vector_ch12_mapping(textbook_path, answers_path, draft_path,
                           proposal_dir, config) -> VectorCh12Proposal
adapt_vector_ch12_from_mapping(textbook_path, answers_path, mapping_path,
                              approval, output_dir, config)
                              -> V124AdaptedImportPackage
```

All paths are `Path`; config is the existing `PipelineConfig`. Approval is the
unchanged `SourceMappingApproval`. `VectorCh12Proposal` is a frozen carrier
with ordered fields `proposal_root:Path`, `mapping_path:Path`, `review_path:Path`,
`source_id:str`, `input_binding_sha256:str`, `mapping_sha256:str`,
`candidate_count:int`. Its paths are exactly `source_mapping.json` and
`SOURCE_MAPPING_REVIEW.md` inside a new proposal root; no single-source SHA is
mislabelled as a combined ZIP identity. No writer is called by either function.

Both proposal and adaptation re-read and verify the two original identities.
Adaptation also validates the mapping structure/coverage and exact approval,
not merely a caller-provided digest. No implicit approvals or automatic
selection from the remaining chapter units.

### 3.2 Exact schema and ordering

The new strict schema is `vector-ch12-dual-source-mapping-v1`, not a revision
to the old Mode B schema. Reject duplicate/unknown/missing keys, bool-as-int,
NaN/Infinity, invalid ranges and unknown enum values. The draft contains the
same semantic fields as the mapping, without trusting any supplied digest.
The final proposal computes and validates all identities from source bytes.

Top-level exact keys:

```text
schema_version, profile, batch_id, source_id, answer_source_id, chapter,
packages, shared_conditions, questions, unit_dispositions,
unselected_spans, unselected_image_members
```

`profile=OSM-M2B12-C-E`, `chapter=12`. `packages` is ordered textbook then
answers; each entry has `role, zip_sha256, zip_size_bytes, selected_member,
member_sha256, member_size_bytes`. Original absolute paths stay in the readable
review, outside the hashed mapping. Each span has exactly
`package_role, member, start_byte, end_byte, raw_sha256`; half-open UTF-8 byte
offsets index the unmodified member, not normalized text. Lines are derived
display evidence, never authoritative coordinates. Verify UTF-8 boundaries
and raw slice SHA independently.

`shared_conditions` entries have `condition_id, spans, applies_to`.
Spans are ordered; applies_to is an ordered list of complete question IDs in
source order. An identical span may be reused only through that condition ID.
No accidental partial overlaps or copied answer-to-question fragments.

Each `questions` entry has exactly:

```text
semantic_order, question_id, source_section, source_question_number,
question_pieces, solution_spans, explanation_spans, image_bindings,
answer_evidence, metadata
```

Orders are contiguous1..N, preserving source occurrence order. A question
piece is either `{kind:"shared",condition_id:<id>}` or
`{kind:"source",span:<span>}`. Resolve these in declared order, never sort
fragments by byte address to render them. Every listed shared condition must
appear exactly once in each beneficiary's question pieces and nowhere else.
Missing beneficiary/context, duplicate insertion, unknown reference or unused
condition is blocking. Scope comes from literal source statements (e.g.
`［第5—6題］`), recorded in the shared fragment and checked in human review;
the code does not infer a scope from mathematical similarity.

Top-level identity is `(source_id, source_section, source_question_number)`;
question_id must be its stable existing ID. Repeated Q1 across12A/12B is valid;
duplicate qualified identity is not. Same-line12B5/6 are distinct explicit byte
slices, not regex-discovered subquestions. Retain every subpart inside each.

`answer_evidence` has `level, covered_subparts, missing_subparts, limitation`.
Levels: `worked_solution`, `final_answers_only`, `partial`, `missing`.
Subparts are literal labels from the complete question (or `whole` for an
unnumbered single ask), not independent records. Lists are disjoint; together
they account for all asks in source order. A full answer key is not a worked
solution. `partial` requires a nonempty missing list and limitation; `missing`
requires empty solution_spans/covered_subparts and all asks in missing_subparts.
For complete coverage, missing_subparts is empty. Mathematical ambiguity stays
in the review disposition rather than being relabelled complete.

`metadata` has `primary_type,tags,difficulty_level,marks,question_language,
answer_language`; primary_type=`向量`, controlled tags only, no inferred Joy
Level or marks. Marks remain review/source-map information, not a new raw
candidate field. Languages retain source text, including zh-Hant stem and
English answers. Independent explanations require independently mapped source
spans; solution prose alone does not grant explanation provenance.

`unit_dispositions` has exactly one entry per old203 indexed IDs, in old index
order: `question_id,disposition,reason`, with
`proposed_selection|later_processing|review_required|outside_first_vector_batch`.
Selected IDs equal questions exactly. This is a review ledger, not database
taxonomy. No final eligible count is inferred for unselected records.

Every non-whitespace byte of both selected MMD members is accounted for by
unique source/shared/answer/explanation/image-token ownership or an explicit
`unselected_spans` entry `{span,reason}`. Shared reuse counts once for physical
coverage. Overlap is only permitted for image tokens nested in their own
content span and the explicit shared-reference reuse. Nonselected page/list
wrappers, theory, worked samples, annotations and later questions receive
honest reasons, not silent deletion. Every safe image member is bound or in
`unselected_image_members` (`package_role,member,sha256,reason`); no image is
assumed unnecessary just because outside a question's line interval.

### 3.3 Hash domains, approval and change handling

Canonical JSON for the mapping and source-map: UTF-8, ensure_ascii=False,
sorted object keys, compact separators, allow_nan=False, no trailing LF.
Array order is semantic as defined above; do not sort question pieces or
solution spans. `input_binding_sha256` is SHA256 of canonical JSON containing
`profile` and the ordered `packages` list. `mapping_sha256` is SHA256 of the
entire strict mapping object, including package roles/outerZIP hashes,
selection, metadata, coverage, dispositions and ignored material declarations.

After implementation and a real validated proposal, the unchanged mapping
approval syntax will bind `source_id + mapping_sha256`. This also binds this
selection/batch and both input packages. A changed answer pack, metadata,
question scope or source bytes requires a new actual proposal and approval.
There is no usable approval digest or approval statement at this Design stage.

Outer ZIP SHA/size certify the received transport and enter mapping approval;
they do **not** enter canonical content, source-map, raw candidate fragment
hash or preflight digest. Canonical identity uses selected raw MMD/image bytes,
member-qualified spans, rendered content and approved semantic metadata.
Thus ZIP recompression/order/timestamps require renewed source-input approval,
but identical members/mapping semantics produce byte-identical canonical output.
Changing even unselected MMD bytes changes the staged full raw-member identity;
it is not claimed to be canonical-invariant. Review reasons, disposition of
unselected units, absolute paths, clocks, temporary roots and approval text
are omitted from canonical content, while selected answer limitations remain.
Historical single-source hash definitions remain untouched.

## 4. Deterministic composition, IR and images

Read exact span bytes and decode strict UTF-8. Normalize only CRLF/CR to LF.
For each of question, solution and independent explanation, join its ordered
fragments with **one inserted LF**, without trimming any fragment or collapsing
existing blank lines. An empty array renders empty text. Shared pieces expand
their own span array by the same rule before insertion. Do not translate,
repair LaTeX, reorder equations or normalize mathematical notation.

Raw list commands such as `\\item` or unmatched page-level itemize wrappers
may survive a source fragment. The output is source-preserving MMD text, not
a promised compilable LaTeX handout. The profile must not use the old automatic
lexer to demand a different question shape. A cut must not divide a UTF-8
character, image token, math delimiter pair, command argument or formula atom;
ambiguous formula boundaries are held for explicit source review, not repaired
with fabricated braces or mathematical terms. Future teaching export may
format presentation separately without changing these approved source bytes.

Reuse `_SourceMember`, `_SourceSpan`, `_SourceImageRef` and path/hash/JSON
primitives where their existing constraints hold. A profile-private frozen
composite-question projection keeps ordered fragment references and shared
conditions. Do not force multi-fragment input into the old single
`fragment_span`, change old `_SourceQuestion` sorting, or alter old IR behavior.
No second public/general IR framework.

Image bindings have `semantic_order,content_role,token_span,raw_target,
image_package_role,image_member,image_sha256,canonical_path`.
content_role is `question|solution|explanation`, separately from package role.
The whole token span must occur in the declared content pieces; its target
must match exactly. Its relative target resolves inside the **same package as
the token**, unless a future separately approved profile explicitly supports
cross-package image references; this profile does not guess cross-package
fallback. Staging path is `images/<package_role>/<full safe original member>`.
For example `images/textbook/images/<name>.jpg`; no basename flattening.
Same-named files across packages cannot collide. Duplicate same-role bindings
stage the bytes once but retain each token's ownership.

Copy images byte-identically and verify SHA. Preserve source token text rather
than rewriting it. Source-map resolves each original token to its namespaced
canonical image; a consumer must use that map, not guess the path from basename.
Candidate image_paths/roles contain the bound canonical paths/content roles in
first occurrence order (question, solution, explanation), unique by path/role.
Missing or unsafe necessary image blocks that question's mapping, never silently
omits it. No redraw, OCR or replacement image generation.

This first batch has one necessary original image, attached to12A1:
`textbook::images/8e7425d9-2e29-4013-a8f9-523baf675a8f-23_234_411_1619_1530.jpg`,
SHA `338001bc38d986aa461907e6316d7b116495d134a174cfa2cba7747c76d9f541`.
The rectangle A/B/C/D and diagonal intersection E were visually checked.
The old198 references are a prior inventory measure, not this batch's image
count or an assertion that all chapter image semantics are reviewed.

## 5. Selection, answer truth and preserved remainder

First proposed selection:16 complete questions, all subparts retained. Question
and answer member line numbers below are display locators; exact byte slices,
raw SHA and full original text/answers are in the attached review artifacts.

| Order | Original section / question | Textbook lines | Answer lines | Purpose / source answer coverage |
|---:|---|---|---|---|
| 1 | 12A1 | 993–1002 | 1171–1176 | equal/negative vectors; four judgments, result key only; necessary image |
| 2 | 12A9 | shared1053–1054 + scope1055;1057 | 1357–1372 | nonparallel coefficient comparison; full source steps |
| 3 | 12A10 | shared1053–1054 + scope1055;1058 | 1373–1380 | same shared conditions; full source steps |
| 4 | 12A11 | shared1053–1054 + scope1055;1059 | 1381–1400 | two coefficient equations; full source steps |
| 5 | 12B3 | shared1536;1538–1541 | 1998–2017 | position vectors/division; both subparts |
| 6 | 12B4 | shared1536;1542–1547 | 2018–2037 | ratio conversion/division; both subparts |
| 7 | 12B5 | shared1548;1550 bytes67784:67812 | 2038–2048 | position vector rearrangement; whole question |
| 8 | 12B6 | shared1548;1550 bytes67812:67832 | 2049–2058 | midpoint rearrangement; distinct whole question |
| 9 | 12C2 | 2316–2318 | 2788–2803 | i/j addition and scalar multiplication; both subparts |
| 10 | 12C3 | 2319–2321 | 2804–2851 | position/displacement; both subparts and source alternatives |
| 11 | 12C8 | 2340–2342 | 2959–2976 | magnitude/unit vector; both nonzero vectors |
| 12 | 12C9 | 2343–2345 | 2977–2992 | spatial position/linear combination; both subparts |
| 13 | 12C10 | 2346–2350 | 2993–3014 | spatial midpoints; both subparts |
| 14 | 12C13 | 2361–2365 | 3065–3083 | displacement/magnitude/unit vector; all asks |
| 15 | 12C17 | 2378 | 3135–3146 | nonzero scalar multiple proves parallel lines |
| 16 | 12C18 | 2379–2381 | 3147–3159 | scalar multiple proves collinearity |

These16 have readable complete asks and matching source answers for all asks;
15 contain worked source steps and1 a complete judgment key. They are not
approved, canonical or proven net-new. This is local mathematical/source
correspondence review, not certification of an unseen original publisher PDF.
All16 have primary_type=`向量`, difficulty=NULL/missing and marks unknown.
No independent explanation evidence is claimed. Existing controlled tags used:
`vector,plane-vector,space-vector,coefficient-comparison,section-formula,
unit-vector,parallel,collinear`; each question's actual subset is in the review.
Position vector, magnitude and scalar multiplication are teaching descriptors,
not newly invented controlled tags. Do not label dimension-agnostic p/q
exercises as definitively plane or spatial just to fill metadata.

Overlapping teaching coverage: addition/scalar5, position8, division5,
magnitude2, unit2, parallel1, collinear1; plane-specific4, spatial5, other7
dimension-agnostic. These are overlapping content descriptors, not additive
question counts or predicted preflight classifications.

All203 old units retained:16 proposed_selection +163 later_processing +16
review_required +8 prerequisite outside_first_vector_batch =203. The16 review
items include content defects and unresolved mapping/layout review, not16
proven mathematical errors. Old notes and local resolutions are preserved.
All other195-vector content remains eligible for later *review*, including
dot/cross products if actually present; the pilot does not impose a permanent
basic-vector-only scope.

Specific holds:

- Examples19/23: missing asks/conditions; no answer-based reconstruction.
- Example3: retain all question text and available(b) solution; mark(a) solution
  absent. Partial source material stays library-external until explicitly mapped
  and approved with its limitation; never label it a complete worked solution.
- Quiz12.3/12.4 and12C31: preserve observed conflicting formula fragments; the
  supplied MMD does not establish whether the book or conversion is wrong.
  Do not silently correct or request the same existing image again.
- New12C12(b): source unit-vector derivation ends with an additional denominator5
  after already dividing coefficients by5 (answers3037–3064). Preserve original,
  hold separately; no proposed source correction without original-page evidence.
- Existing DRILL6/7/13 layout notes retain earlier local image/context resolutions;
  not selected in this pilot and not falsely upgraded to approved mappings.
- Pure result tables are `final_answers_only`; missing requested proof is
  `partial`, not a complete solution merely because a final number exists.

Missing-source solution projects to empty solution fields and
`missing_from_source`. Existing but partial/final-only source solution projects
to `source_provided` with its exact coverage/limitation retained in source-map
and teacher-notes evidence; that status means provenance, not full worked-MS
coverage. No new answer enum, fabricated solution or independent explanation.
For partial content, mapping approval must explicitly expose missing subparts;
unresolved question content cannot enter the selected set at all. The first16
contain no such partial solution. Preflight's existing missing-answer counter
is not redefined to mean incomplete-worked-solution count.

## 6. Canonical output and the existing V1.24 boundary

Formal V1.23 remains677 records, database SHA
`28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd`,
release digest
`84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc`.

Read the existing approved F6/V1.24 Design
`2026-10-20-f6-selected-batch-v124-candidate-design.md` and committed Plan
`2026-10-20-f6-selected-batch-v124-candidate.md`. The user approved that Plan
and Native/Inline execution in chat. At this checkpoint the six V1.24 modules
and F6 source implementation are not present in the worktree: written approval
is not implementation or executable availability.

Reusable *version* contract: frozen V1.23 baseline verification, strict V1.24
manifest loader, independent genesis, effective-state preflight, exact parent
approval, atomic ordered generations and independent verifier. Genesis is
`797ed06ca5833bac060c1603cada38a6f2aa9eb080a40d9dc892bba9a549773a`.
F6's school identity, four selected questions and source-approval bridge are
F6-only, not a textbook permit. This Design proposes only this chapter's source
bridge into the same version contract. It does not replace its implementation
Plan, start a second V1.24 engine or grant real import authority.

After both this source implementation and the existing V1.24 implementation
are approved/verified, and after exact chapter mapping approval, generate only:

```text
import_manifest.json
records/candidates.json
source/original.mmd.txt
source/source-map.json
answers/answer.mmd.txt
teacher_notes/source-coverage.json
images/<package_role>/<original member>  [only selected bound images]
```

Both raw selected MMD members are staged byte-identically once. `source_files`
contains original.mmd.txt and source-map.json; `answer_files` contains the raw
answer member. Candidate/image/teacher_notes groups contain the corresponding
files above; common_errors_files is empty. No ZIP or approval sidecar is placed
inside canonical inventory. The strict18-field V1.24 manifest and exact ordered
file-evidence fields use the existing V1.24 contract, target V1.24 and
`task14-v124-import-manifest-v1`. Do not emit V1.19/V1.23 then rewrite its version.
Do not use the old adapter's hard-coded V1.19 publisher for this bridge.

`source-map.json` schema=`vector-ch12-canonical-source-map-v1`, exact keys:
`schema_version,profile,source_id,answer_source_id,chapter,members,questions`.
Members in role order contain `package_role,member,sha256,size_bytes,
canonical_path`; no outer ZIP identity. Questions contain exactly the selected
mapping question fields from§3.2, but shared pieces are expanded to ordered
source spans and each includes `rendered_question_sha256,
rendered_solution_sha256,rendered_explanation_sha256`. Source/package-qualified
raw span and token/image evidence remains; no unselected-unit or review-comment
data. Source-map members include the two MMDs followed by selected image members
in deterministic first-binding order. Same raw image is listed once per role.
`teacher_notes/source-coverage.json` has `schema_version` fixed to
`vector-ch12-source-coverage-v1` and `questions`: ordered objects containing
`question_id,answer_evidence`. This preserves limitations as structured evidence,
not generated teaching explanations or a new taxonomy. Same canonical JSON
rules as§3.3 apply. All file bytes/size/SHA are manifest-bound.

Raw candidates use the unchanged23-field contract: stable source IDs/section/
number; `source_fragment_hash=SHA256(rendered question UTF-8)` for this new
composite profile; question_text_original is the deterministic composition;
question_text_zh is identical source Chinese, translation_status=source_present
with `source:source/source-map.json#<question_id>` evidence. Original source
solution goes only to solution_original; solution_verified stays empty.
Answer provenance/coverage follows§5. No translation of English answers.
explanation_text empty, explanation_evidence=None and explanation_status=missing
when no independently mapped explanation exists. Tags are approved suggested
controlled values with tag_status=proposed; missing tags use the existing
missing state. Difficulty=NULL/difficulty_status=missing. Image fields follow§4.
`enrichment_status` must be computed by the unchanged Task9A formula; with
missing difficulty/independent explanation these16 are incomplete, not rejected
merely for lacking generated enrichment. No additional candidate fields.

Exact current-parent preflight decides duplicate/collision/adaptation/new,
including possible old chapter content. No expected net-new16 is promised.
First generation has no parent artifact but binds the frozen V1.24 genesis;
later generations bind the independently verified latest candidate. Never use
published V1.23's historical candidate as a new lifecycle parent. Exact import
approval remains batch + actual preflightSHA + V1.24 + actual parent. Changed
content/parent invalidates stale preflight/approval. Real writer/promotion is
not part of the source module.

## 7. Closed future implementation scope and tests

Current checkpoint changes only this Design and minimal PROJECT_STATE status;
new ignored review artifacts are not production code, fixtures or authority.
Do not edit the user-owned AGENTS.md or previous review evidence.

After human Design/Plan/execution approval, the chapter implementation scope is:

| Class | Exact path / purpose |
|---|---|
| NEW production | `src/joy_m2/ingest/vector_ch12.py` — two entrypoints, frozen proposal carrier, private composition/coverage, direct V1.24 source bridge |
| TEST | `tests/unit/test_vector_ch12_mapping.py` — exact spans/roles/approval and rendering |
| TEST | `tests/integration/test_vector_ch12_adapter.py` — dual-source safety, canonical file closure and real V1.24 preflight interface using synthetic inputs |
| TEST | `tests/regression/test_vector_ch12_compatibility.py` — existing single-source API/hash/output invariance |
| FIXTURE | `tests/fixtures/vector_ch12/` — small independently authored synthetic MMD pairs and expected bytes, not real copyrighted chapter dumps |
| DOC | this Design; future `docs/superpowers/plans/2026-10-23-vector-ch12-dual-package-source.md`; `docs/reports/VECTOR_CH12_SOURCE_ADAPTATION.md`; PROJECT_STATE |

Historical archive/adapter/parser/mapping/version modules are reuse-only, not
modification scope. If a helper cannot be reused without changing its contract,
keep a minimal chapter-private implementation or report the exact necessary
scope amendment before changing an old module. No new dependencies, package
root exports, scanner configuration or public generic parser.

Future implementation is RED-first, prerequisite-ordered: carrier/API scaffold,
strict dual inventory and mapping validator, composition/coverage, approved
canonical bridge after V1.24 availability, then compatibility and independent
review. Missing imports/setup/fixtures are never behavioral RED. Use independently
constructed expected bytes/spans, not outputs generated by the code under test.

Required behavior tests:

1. Swapped/wrong/changed answer ZIP and member hash fail before output; no
   sibling-directory fallback; samebasename is not proof of correspondence.
2. Same-name members/images across roles remain distinct; unsafe paths,
   within-role collisions, ZIP bomb/metadata violations and limits still reject.
3. Shared-condition omission, undeclared beneficiary, repeated insertion or
   overlap fails. Correct12B5/6-style mapping produces two self-contained whole
   questions while leaving the shared bytes single-owned for coverage.
4. Same-line two whole-question slices accepted only by exact approved ranges;
   cutting math/image/UTF-8 tokens fails; subpart/list numbering is not auto-split.
5. Same original number in distinct sections accepted; duplicate qualified ID,
   invented ID replacement, duplicate source piece or unaccounted bytes fail.
6. Missing asks like examples19/23 cannot be selected. Partial answer coverage,
   missing solution and final-answer-only tables preserve distinct review truth
   and unchanged candidate answer enums. No generated solution/explanation.
7. Selected image absent/unsafe/changed fails; original bytes/token and namespace
   correspondence verify; solution/explanation role cannot masquerade as question.
8. CRLF/CR-only normalization, LF joins, discontiguous ordering and LaTeX bytes
   have exact oracles. Two clean outputs are byte-identical across every file;
   ZIP recompression/member-order changes invalidate old input approval but,
   after fresh synthetic approval, do not change identical canonical semantics.
9. Mapping digest binds package roles/selection/metadata/coverage; altered mapping,
   wrong approval source/digest/text rejects. Missing approval never emits package.
10. Canonical six groups/exact inventory/raw23 fields load through V1.24; source
    evidence resolves, incomplete enrichment honest; real preflight rules stay
    unchanged. No implicit write/real approval from tests.
11. Original single-source representative fixtures retain exact candidates,
    source-map, manifest and preflight digests; public exports/order unchanged.
12. New output uses same-filesystem temporary construction and no-replace atomic
    publication: conflict/validation/I/O failure leaves existing output/source
    untouched and cleans only its own newly created temporary directory.
    Enforce the existing staging-root/source-overlap guards; reject output roots
    inside either original source or review/approval evidence. Revalidate the
    identities immediately before publication and emit only the validated input
    snapshot, never reread changed bytes after validation.
13. FormalV1.18–V1.23 and old candidate/source/approval identities remain unchanged;
    existing V1.24 parent-chain tests remain owned by its version Plan.

Diagnostics reuse MmdAdapterIssue/MmdAdapterBlockedError and existing nine
Task9B codes; precise new-profile reasons go in evidence, not new Task9A issue
codes. Invalid mapping/content => existing `mmd_parse_failed` or corresponding
existing manifest/image/archive code; input/path/I/O exceptions preserve existing
boundaries. Stable issue ordering uses the existing approved five-field key.

## 8. Human gates and exit

This chapter's Design approval is still required. Then create/review the
implementation Plan and obtain execution approval; do not consume the F6 Plan
approval as chapter implementation permission. Independent Design review is
separate from later independent implementation review and from human approval.

After validated implementation, generate the actual16-question selection/mapping
proposal and its actual digest for human source-mapping approval. Approval must
cover both ZIP identities, all question fragments, shared scopes, coverage,
metadata and image bindings. It is not granted by this written direction or by
review-file hashes. Only then, and only with an executable approved V1.24 entry,
run canonical generation and authoritative current-parent preflight. Stop again
for exact real import approval. Promotion remains a separate explicit gate.

The163 later units and16 review units are not discarded or silently approved;
later selections may reuse this implemented profile without re-designing it,
but each exact selected mapping needs its own approval. The8 prerequisites
remain outside this vector pilot. Unresolved source corrections need evidence
and a newly bound mapping, not a silent mathematical rewrite.

Current stop:
**USER DECISION REQUIRED — VECTOR CH12 SOURCE ADAPTATION DESIGN REVIEW**.
No Plan, implementation, canonical/preflight, writer, worksheet or promotion
is authorized by creation or commitment of this document.
