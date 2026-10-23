# Vector Chapter 12 Dual-Package Source Adaptation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use `superpowers:executing-plans` for the selected Native / Inline execution. Follow the checkboxes in dependency order; a separate reviewer performs the final independent review. This written Plan is NOT yet implementation authorization.

**Goal:** Implement the approved chapter-only dual-package mapping and, after the existing V1.24 dependency is verified, its canonical bridge; stop at exact human source-mapping approval before processing real data authoritatively.

**Architecture:** One source module owns explicit package-qualified spans, shared conditions, coverage and images. It reuses historical safe primitives without changing their contracts. The existing V1.24 engine remains an external dependency, not a second engine or an implicit F6 task.

**Tech Stack:** Existing Python standard library, frozen dataclasses, unittest, ZIP/UTF-8/SHA-256/JSON, existing PipelineConfig and atomic no-replace primitive. No dependencies or package-root exports.

**Spec:** `docs/superpowers/specs/2026-10-23-vector-ch12-dual-package-source-design.md`, human-approved technical content at commit `934290f45c2acc9e84adc8f9ee86c9dd120e3514`, file SHA-256 `d20b7e29ebf6ef2f39bfdaf0831ea3acc34298e64c3a0a1086253b4254072879`. Only approval/checkpoint wording is synchronized now.

## Global constraints and execution environment

- Work only in `/Users/miaohuanjoy/Desktop/joy-m2-ai-database-current/.worktrees/task8b-pipeline-migration`; recover actual HEAD, never reset to a quoted checkpoint.
- Preserve formal V1.18–V1.23, historical candidates, original ZIPs, old203-unit evidence and the user's unstaged AGENTS.md byte-for-byte. Never stage/stash/reset AGENTS.md.
- Existing formal V1.23 has677 records, SQLite SHA `28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd`, release digest `84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc`. No formal write, candidate writer or promotion in this Plan.
- No re-OCR, re-indexing203 units, generated answers, estimated difficulty, new taxonomy, scheduler changes, generic Markdown framework or historical contract edits.
- Implement only after this Plan receives explicit human review/execution authorization. Synthetic approvals are only for independently authored fixtures, never real source input.
- A missing module/import/setup/fixture is not behavioral RED. Establish an importable scaffold and valid fixture first; retain actual assertion-failure evidence, then implement minimum GREEN. Do not count skipped/unrun integration as passed.
- Use these environment variables for the commands below (no dependency installation):

```bash
export JOY_PY=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=src:.
```

## Review focus

1. Cross-package basename equality must never substitute for package identity or image ownership: Tasks2,5.
2. Shared bytes reused by two complete questions must be rendered twice but physically owned once: Tasks3,4.
3. ZIP transport changes must invalidate approval without leaking into canonical semantic bytes: Tasks6,7.
4. A source key/partial solution must not silently become a full worked solution or independent explanation: Tasks3,7,9.
5. A changed input or competing output appearing during publication must leave old output intact: Tasks6,7.

## Closed file map

| Path | Responsibility |
|---|---|
| `src/joy_m2/ingest/vector_ch12.py` | Only new production file: two entrypoints, one public frozen carrier, private validation/composition/bridge |
| `tests/unit/test_vector_ch12_mapping.py` | Carrier, exact schema/coverage, rendering, approval and diagnostic assertions |
| `tests/integration/test_vector_ch12_adapter.py` | Real ZIP safety, atomic proposal/package, real V1.24 loader/preflight integration |
| `tests/regression/test_vector_ch12_compatibility.py` | Historical outputs/API/digests and deterministic replay |
| `tests/fixtures/vector_ch12/` | Small synthetic source bytes, hand-authored spans/expected JSON/bytes; no real chapter dump |
| Design; this Plan; `docs/reports/VECTOR_CH12_SOURCE_ADAPTATION.md`; `PROJECT_STATE.md` | Authorized docs/checkpoints only |

Historical archive/parser/adapter/source_mapping/version files are read/reuse-only. Use existing `archive.py` inventory/read/path primitives where their preconditions hold and `writer_profiles.atomic_rename_no_replace`; no calls to the historical hard-coded V1.19 publisher. Any necessary historical modification requires a scope decision, not an opportunistic fix here.

## A / B / C dependency gate — verified on 2026-10-23

**A — source profile:** Tasks1–6 below need no V1.24 runtime. A may become GREEN independently, without claiming canonical integration or emitting a real approval request before the engineering exit gate.

**B — existing shared version layer:** The F6/V1.24 Design is approved at `b480a608df851dde318719f4fbf88bffb1489658`; its Plan is committed at `02d8c0d531066c104afbe39ca03938743e9d88d1`. Chat and current PROJECT_STATE record Native/Inline approval. The old Plan's pending-review footer is historical wording, not a new approval requirement. Read both existing documents; do not amend or execute them under this chapter Plan.

At recovery, none of `v124_models.py`, `v124_manifest.py`, `v124_writer_profiles.py`, `v124_preflight.py`, `v124_writer.py`, `v124_verification.py` exists under `src/joy_m2/ingest/`. The expected `docs/reports/F6_V124_CANDIDATE_VERIFICATION.md` and F6/V1.24 runtime evidence roots are absent. No V1.24 executable GREEN is claimed; historical V1.23 results are not substitutes.

Required external deliverables correspond to version portions of existing Plan Tasks1–2,5–9: real models/strict loader, baseline/genesis, first-generation verifier/writer, verified-parent preflight, multi-batch verifier/writer, historical gates and review. F6 source Tasks3–4 and real-data Tasks10–11 are NOT functional prerequisites for the textbook. This document neither changes that Plan's execution sequence nor grants work in its files; its authorized owner must deliver the shared layer separately.

**C — textbook canonical integration:** Task7 is blocked until B has actual modules and fresh, independently checked version-gate evidence. Recheck B at execution time. Require the genuine `V124AdaptedImportPackage`, `load_v124_import_manifest`, `preflight_v124_import`, candidate verifier and verified-parent behavior, not a fake carrier, rewritten historical constants or mocked preflight. If absent, retain A's successful work and report the exact external dependency; do not label C GREEN or start a second V1.24 implementation.

The V1.24 manifest schema is `task14-v124-import-manifest-v1`; baseline is formal V1.23/677. Its frozen genesis is `797ed06ca5833bac060c1603cada38a6f2aa9eb080a40d9dc892bba9a549773a`. Genesis projection uses its existing LF-terminated canonical bytes; chapter mapping JSON has NO trailing LF. No artifact parent on generation1 still means a required genesis digest; subsequent real preflight uses the then-current verified V1.24 parent, never V1.23 generation3.

## Task 1 — Importable API and frozen proposal carrier

**Files:** new production module and unit test file; synthetic fixture directory only as needed.
**Interfaces:** `VectorCh12Proposal`; `propose_vector_ch12_mapping(textbook_path:Path, answers_path:Path, draft_path:Path, proposal_dir:Path, config:PipelineConfig) -> VectorCh12Proposal`; `adapt_vector_ch12_from_mapping(textbook_path:Path, answers_path:Path, mapping_path:Path, approval:SourceMappingApproval, output_dir:Path, config:PipelineConfig) -> V124AdaptedImportPackage`.

- [ ] Add a minimal importable module/scaffold. Deferred annotations/TYPE_CHECKING and a bridge-local import may defer the real V124 type until Task7; do not define a surrogate type. Placeholder entrypoints must fail explicitly, never return fake success.
- [ ] Write `CarrierTests`: exact ordered fields are `proposal_root, mapping_path, review_path, source_id, input_binding_sha256, mapping_sha256, candidate_count`; types are `Path,Path,Path,str,str,str,int`. Assert mutation raises FrozenInstanceError, paths are exactly root/source_mapping.json and root/SOURCE_MAPPING_REVIEW.md, and invalid field values cannot yield a valid carrier. Freeze only this approved public shape.
- [ ] Run `"$JOY_PY" -B -m unittest -v tests.unit.test_vector_ch12_mapping.CarrierTests`; record a genuine carrier-contract assertion RED, not a missing symbol.
- [ ] Implement the frozen carrier, exact argument checks and entrypoint signatures. Keep all supporting projections private; reuse valid old IR types without changing old single-span ordering.
- [ ] Rerun CarrierTests to GREEN; verify historical package `__all__` unchanged.
- [ ] Explicitly stage only the above task files and commit `feat: scaffold chapter12 source mapping API`.

## Task 2 — Strict dual inventory and immutable byte snapshot

**Files:** vector_ch12.py; integration file; small fixture pairs.
**Interfaces:** private `_read_packages(textbook_path:Path, answers_path:Path, mapping:dict) -> dict[tuple[str,str],bytes]` returns validated selected-MMD/image snapshots keyed by role/member. It consumes exact Design§3.2 package declarations, never discovers an adjacent answer file.

- [ ] Independently author ZIP fixtures with distinct contents but identical `source.mmd`/`images/shared.png` names in both roles. Construct archives with stdlib zipfile, not production helpers; byte literals are the expected contents. Hash using hashlib only, not a production digest routine.
- [ ] Write `DualInventoryTests`: swapped/wrong ZIP, altered selected member, bad ZIP SHA/size, same basename, missing selected member, unsafe paths/symlinks/encryption/Unicode collisions, duplicate entries, unsupported compression, metadata rules, CRC failure, invalid UTF-8/BOM and limit boundaries. Assert cross-role names are distinct; same-role collisions fail; no output is created. Mock metadata only for resource-limit unit inputs, not proof of real archive/bridge behavior.
- [ ] Run `"$JOY_PY" -B -m unittest -v tests.integration.test_vector_ch12_adapter.DualInventoryTests`; first valid inventory assertion must fail behaviorally before GREEN.
- [ ] Implement complete inventory validation before selective reads, per-ZIP50/100/20/10MiB,256 members,100:1 and combined100MiB/256 members. Reuse safe primitives; keep any necessary glue chapter-private. No extractall or executing source content. Preserve the validated snapshot for later rendering/publication.
- [ ] Rerun DualInventoryTests, including exact boundary and one-over cases, to GREEN; source bytes/hashes remain unchanged.
- [ ] Commit only module, integration tests and their fixture files: `feat: validate chapter12 dual package identities`.

## Task 3 — Strict mapping, disposition and coverage validation

**Files:** vector_ch12.py; unit file; synthetic mapping fixtures.
**Interfaces:** private `_validate_mapping(mapping:dict, members:dict[tuple[str,str],bytes]) -> None`; no canonical output. Consume all exact schemas in Design§3.2; reject extras, omissions, duplicate JSON keys, bool-as-int, NaN/Infinity, unknown enums and invalid ranges.

- [ ] Write `MappingTests` with manually specified slices/IDs/expected errors: same-line complete5/6 stay two records; (a)/(b)/(i) remain inside one record; Q1 in12A versus12B is valid but repeated qualified identity or replacement ID is not. Verify contiguous semantic order and original occurrence order without sorting rendering fragments.
- [ ] Add shared-condition tests: missing beneficiary, undeclared/unused condition, duplicate insertion, wrong scope, copied shared bytes outside a reference and partial overlap all fail. Literal source scope and explicit beneficiary list must agree with review evidence; no inferred scope from mathematics.
- [ ] Add exact coverage tests: each non-whitespace source byte owned once, except nested image tokens and shared physical ownership; gap/unjustified overlap fails. Every image member is bound or explicitly declared unselected. All203 existing IDs/order/dispositions are preserved, selected IDs equal questions. Use a small synthetic text payload with a separately authored203-ID disposition fixture, not203 real bodies; real-ID/order consistency is checked against retained intake evidence during Task9.
- [ ] Add `AnswerCoverageTests`: four levels remain distinct; covered/missing literal asks disjoint and exhaustive; partial requires limitation/missing asks; missing requires no solution spans. Selected held/missing-ask records fail the selected/held consistency check; code does not claim to discover mathematical completeness from an answer. Human review remains the source-content authority. Unknown controlled tags fail; unknown difficulty/marks remain null, not guesses.
- [ ] Run `"$JOY_PY" -B -m unittest -v tests.unit.test_vector_ch12_mapping.MappingTests tests.unit.test_vector_ch12_mapping.AnswerCoverageTests`; record valid-schema behavior REDs before implementing validators.
- [ ] Implement only strict field/identity/order/coverage checks. Preserve `worked_solution|final_answers_only|partial|missing` as mapping evidence, not new candidate enums or diagnostics.
- [ ] Rerun both classes GREEN; commit `feat: validate chapter12 exact mapping coverage`.

## Task 4 — Deterministic fragments and shared expansion

**Files:** vector_ch12.py; unit file; expected byte fixtures.
**Interfaces:** private `_render_spans(spans:list[dict], members:dict[tuple[str,str],bytes]) -> str` and `_expand_question_pieces(pieces:list[dict], shared:list[dict]) -> list[dict]`. Expanded pieces are `{kind:"source",span:<original span>}` in semantic order; no shared IDs remain in canonical question_pieces.

- [ ] Write `RenderingTests` with independent exact bytes. For synthetic member `b'S\r\nC\r5. a 6. b'`, shared spans are `[0,3)` and `[3,5)`; whole-question spans are `[5,9)` and `[10,14)`. The only uncovered byte9 is whitespace. Shared reference plus first question expands to three source pieces, rendering exactly `b'S\n\nC\n\n5. a'`; second renders `b'S\n\nC\n\n6. b'`. Do not trim the repeated newlines. Source-map retains each original raw span SHA, not the rendered SHA.
- [ ] Add CR-only, empty fragment arrays, leading/trailing whitespace, reversed declared discontiguous order and non-ASCII tests. Example raw `b'A\r\n'` and `b'B\rC'` render `b'A\n\nB\nC'`. Assert raw-slice SHA differs from normalized/rendered-question SHA where bytes differ; historical source_fragment_hash behavior is untouched.
- [ ] Add cuts inside a UTF-8 codepoint, image token, math delimiter pair, command argument and formula atom; all block. Whole intact LaTeX tokens and raw page-level list wrappers survive byte-for-byte except newline normalization. Ambiguous formula boundaries are review errors, not repaired LaTeX. Use a narrow chapter-private boundary validator, not an automatic question/parser grammar.
- [ ] Run `"$JOY_PY" -B -m unittest -v tests.unit.test_vector_ch12_mapping.RenderingTests`; capture exact-byte RED then implement expansion/normalization/joins and boundary checks.
- [ ] Rerun GREEN; independently compare fixture byte literals, spans and SHA via stdlib rather than regenerating expected values with these functions.
- [ ] Commit `feat: compose chapter12 source fragments deterministically`.

## Task 5 — Images, namespace and content-role ownership

**Files:** vector_ch12.py; unit/integration files; tiny original synthetic images.
**Interfaces:** private `_validate_images(mapping:dict, members:dict[tuple[str,str],bytes]) -> None`; validated bindings drive later image copies/source-map. Preserve exact Design§4 binding fields and original image tokens.

- [ ] Write `ImageTests`: token range outside declared content, raw_target mismatch, absent/changed/unsafe target, cross-package fallback and wrong content role fail. Verify target relative resolution uses its token's member/package, not a basename dictionary.
- [ ] Concrete fixture: textbook/images/shared.png appears twice in question text and once in source solution text within textbook; answers/images/shared.png has different bytes and an answer token. Retain all four token bindings. Stage two files, not four; candidate pairs in first-occurrence content-role order are `(images/textbook/images/shared.png,question)`, `(images/textbook/images/shared.png,solution)`, `(images/answers/images/shared.png,solution)`. Do not deduplicate away roles. Verify the solution token is really owned by a mapped solution span, not reclassified question text.
- [ ] Run `"$JOY_PY" -B -m unittest -v tests.unit.test_vector_ch12_mapping.ImageTests`; capture ownership/dedup behavioral RED.
- [ ] Implement exact namespace `images/<package_role>/<full safe original member>`, unique staged bytes per role/member, unique candidate pairs per path/content-role and complete per-token source-map evidence. No token rewrite, redraw or remote fetch.
- [ ] Rerun GREEN; commit `feat: bind chapter12 image ownership`.

## Task 6 — Real proposal mechanism, approval and atomic safety (A exit)

**Files:** vector_ch12.py; unit/integration files; fixture expectations.
**Interfaces:** finish `propose_vector_ch12_mapping`; private `_validate_approval(mapping:dict, approval:SourceMappingApproval) -> None`; reuse unchanged SourceMappingApproval. This is real executable proposal behavior on synthetic inputs, not real user approval.

- [ ] Write `ProposalTests` / `ApprovalTests`: proposal contains only source_mapping.json and SOURCE_MAPPING_REVIEW.md; carrier agrees with both files. Independent JSON serialization is UTF-8/ensure_ascii=False/sort_keys=True/separators=(',',':')/allow_nan=False with no LF. input_binding_sha256 hashes `{profile,packages}`; mapping_sha256 hashes the entire strict mapping. Absolute transport paths appear only in readable review. Do not trust caller-supplied hashes over actual bytes.
- [ ] Test changed roles, selection, metadata, coverage/dispositions and answer ZIP invalidate bound approval; wrong source/digest/literal or no approval never emits canonical. Recompressed same members require a new synthetic approval; no real batch signature is fabricated. Approval literal remains the existing `USER APPROVED SOURCE MAPPING <source_id> <mapping_sha256>`.
- [ ] Write `PublicationSafetyTests` for proposal: staging-root/source/review/approval overlap, symlink/existing destination, destination race, input changes before publication, injected I/O failure. Output absent or existing bytes unchanged, own temp removed only; source/draft unchanged. No generic directory deletion.
- [ ] Run `"$JOY_PY" -B -m unittest -v tests.unit.test_vector_ch12_mapping.ApprovalTests tests.integration.test_vector_ch12_adapter.ProposalTests tests.integration.test_vector_ch12_adapter.PublicationSafetyTests`; capture real assertion REDs, then implement no-replace same-filesystem temp publication with immediately revalidated identity and validated input snapshot.
- [ ] Rerun GREEN; no real proposal generated yet. Commit `feat: publish chapter12 mapping proposals atomically`.

### Frozen diagnostic routing / short-circuit oracle

This is a reason-to-existing-code routing table, not a new enum or diagnostic API. Use MmdAdapterIssue/MmdAdapterBlockedError. Preserve existing path/type/I/O exception boundaries: TypeError for wrong public argument types, ConfigurationError for invalid staging location, OutputConflictError for existing output, InputMissingError for absent input, InputFormatError for unreadable input. As in source_mapping._decode_object, malformed JSON/invalid UTF-8/BOM raises MmdAdapterBlockedError with source_contract_mismatch, not a plain replacement exception. Invalid SourceMappingApproval construction retains its existing PipelineError; a valid carrier bound to the wrong mapping is a blocking identity mismatch. Unsupported OS atomic rename remains OSError, not fabricated success.

| Stage, stop before later stage on failure | Existing diagnostic for validly parsed but blocked input |
|---|---|
| 1. Arguments/destination/input readability | Existing exception boundary above |
| 2. Mapping shape + package role/identity declarations | source_contract_mismatch for wrong schema/type/hash/role/approval identity; mmd_parse_failed for invalid content span structure |
| 3. Complete ZIP inventory, then selected reads | archive_member_unsafe for path/type/collision; archive_integrity_invalid for structure/CRC/limits; unsupported_source_format for non-supported source format |
| 4. Exact bytes/identity, then spans/coverage/rendering | source_contract_mismatch for changed ZIP/member or invalid UTF-8/BOM; selection_not_unique for duplicate qualified selection; candidate_count_mismatch for selected/disposition count disagreement; mmd_parse_failed for scope/gaps/cuts/answer-coverage errors |
| 5. Image/semantic evidence | image_binding_invalid for ownership/target/bytes; language_mapping_ambiguous for language-role ambiguity; source_contract_mismatch for unsupported metadata values |
| 6. Exact approval (adapt only), then temp/canonical publication | source_contract_mismatch for approval mismatch; existing path/I/O exceptions otherwise |

Within an inspectable stage collect issues; do not parse/render unsafe bytes to collect later errors. Add `DiagnosticTests` proving a ZIP-limit+mapping-content defect returns archive-stage issues only, and a valid ZIP+bad image never publishes. Stable ordering is `(source_locator, proposed_question_id or '', code, field, evidence)`; evidence must not contain runtime absolute paths. Execute DiagnosticTests within Task6 GREEN, using the same unittest prefix. No new code outside the existing nine.

## Task 7 — Real V1.24 canonical bridge (C; external B prerequisite)

**Files:** vector_ch12.py; integration file; independently authored expected canonical files under fixtures only.
**Interfaces:** finish adapt_vector_ch12_from_mapping returning the actual V124AdaptedImportPackage; consume actual `load_v124_import_manifest(Path)` and `preflight_v124_import(V124PreflightRequest, PipelineConfig)`. Read the actual V124 carrier fields/signatures and verified version report before writing this task's tests; contract mismatch is a dependency issue, not permission to edit the version layer.

- [ ] Verify B modules and synthetic version tests/review exist and passed. Record their commit, commands, logs and real first/verified-parent availability. Otherwise stop C; A remains reusable. Do not import a placeholder and call its failure a bridge RED.
- [ ] Independently construct expected manifest18 fields, candidates23 fields, source-map and coverage JSON from literal source fixture bytes. Expected results may use hashlib/json stdlib but never the bridge, renderer or production builder as oracle. PipelineConfig.releases_root locates frozen formal V1.23; read its existing controlled vocabulary read-only (not merely distinct tags in its records) and use formal_complete_questions_v123 for current formal records. A can do this without B; C cross-checks the genuine V124 loader/preflight. Config has no taxonomy accessor; historical V123 preflight reads V1.22 and is not a current-baseline substitute. Add no config field or fabricated API.
- [ ] Write `CanonicalBridgeTests`: exact raw MMD copies once each; source-map members textbook then answers then bound images by first binding; shared pieces expanded as Task4; raw and rendered hashes both exact. Fields equal Design§6, including source Chinese, untouched English solutions, empty solution_verified, truthful answer level, no inferred explanation, proposed/missing tags, difficulty null/missing and unchanged enrichment formula.
- [ ] Assert canonical inventory is exactly import_manifest.json, records/candidates.json, source/original.mmd.txt, source/source-map.json, answers/answer.mmd.txt, teacher_notes/source-coverage.json plus bound images. Six groups declare all payload files with byte/size/SHA closure; manifest is the authority file, not recursively its own hash entry. common_errors_files is empty. No ZIP, approval sidecar or undeclared output.
- [ ] Write `V124IntegrationTests`: actual strict loader accepts target/schema; actual preflight validates synthetic package against frozen formal V1.23 and against an independently verified synthetic V1.24 parent built by the already-tested version layer. Assert report uses genuine version carrier, actual genesis/current parent, exact projected counts for the fixture, honest missing-enrichment counts and source/image resolution. Never assert real16 are new. No stub/monkeypatch of loader/preflight/verifier and no real writer. Synthetic parent construction stays isolated under staging.
- [ ] Run `"$JOY_PY" -B -m unittest -v tests.integration.test_vector_ch12_adapter.CanonicalBridgeTests tests.integration.test_vector_ch12_adapter.V124IntegrationTests`; valid dependencies must reach the missing bridge behavior/incorrect-byte assertion for RED. Implement direct V1.24 projection with actual carrier; rerun GREEN.
- [ ] Extend PublicationSafetyTests to adaptation, including mapping_path/source-file changes before publish and conflicting output created after validation. Approval is the frozen SourceMappingApproval value received by the API, not an additional file input. Revalidate its binding against the unchanged mapping/source snapshot immediately before publication; publish only snapshot bytes, preserve existing output and clean own temporary files. Source/review/approval evidence locations remain protected against output overlap; do not invent or implicitly read an approval file.
- [ ] Write/run `CanonicalDeterminismTests`: two independent roots compare complete relative path->bytes maps, not just digest/semantic equality. Recompress/reorder ZIPs: old approval fails; fresh valid synthetic mapping approval yields all canonical files byte-identical. Changed unselected MMD bytes must change full raw-member canonical identity. Selected limitations remain canonical; transport paths/ZIP hashes/unselected review reasons do not.
- [ ] Run all unit/integration chapter tests GREEN, then commit `feat: bridge chapter12 mapping into verified V1.24` with only module/tests/fixtures. No real canonical or preflight at this point.

## Task 8 — Historical compatibility, regression and independent review

**Files:** regression file; permitted report/Design/Plan/state docs; fixes only within the closed chapter scope.
**Interfaces:** old single-source APIs and fixture outputs remain unchanged. B owns its version engine and parent-chain tests; this task verifies chapter coexistence, not redesigns them.

- [ ] Add `HistoricalCompatibilityTests` in the prescribed regression file: compare representative single-source candidates, manifest, source-map, issues/counts/status/report/preflight digest and complete output bytes against existing independent goldens; check export prefix/order and public signatures. Do not regenerate golden expected files. Run valid fixtures first; capture a reproducible RED only for an actual new-profile regression, never intentionally break historical code to manufacture one. This protection may be GREEN immediately if no regression exists.
- [ ] Run the three chapter modules plus existing test_mmd_adapter_models, test_mmd_archive, test_mmd_parser, test_mmd_source_mapping, test_mmd_adapter and test_mmd_explicit_mapping modules. Record exact test counts/no skips; keep historical files unchanged.
- [ ] Run current maintained gates once at engineering exit using the existing F6/V1.24 Plan Task9 command: sorted tests/test_*.py modules, only the pre-existing excluded legacy-attribution module `tests.regression.test_task8b_legacy_pipeline_behavior`; no new exclusions. Run V1.18 validator and included historical formal verifiers/replay through V1.23 and the genuine V1.24 version tests. Record fresh actual counts, no expected failures, not inherited1331 results.
- [ ] Compare scoped protected snapshots (formal versions, candidate/source/approval files actually involved, originals and old review roots); inspect diff and ensure only approved paths changed. Run git diff --check. No whole-source re-audit or backup restore for ordinary docs edits.
- [ ] Request a separate read-only implementation reviewer against approved Design, Plan and complete chapter diff; include all five Review Focus items, independent fixtures, A/B/C evidence and safety boundaries. Require Critical=0/Important=0, resolve findings with valid regression RED/GREEN inside scope; do not claim self-review is independent review. Rerun affected gates after fixes, full gates if behavior changed after the full run.
- [ ] Record actual evidence in docs/reports/VECTOR_CH12_SOURCE_ADAPTATION.md and minimal PROJECT_STATE. Commit explicitly named task paths (`feat: verify chapter12 source adaptation gates`) and ordinary push; no AGENTS or staging data. Report remote failure truthfully without undoing local work; Git is not a backup of ignored data.

## Task 9 — First real mapping proposal and human gate

**Files:** new unused ignored root under data/staging/vector-ch12-mapping/; permitted report/state only if checkpoint changes. Never overwrite prior review or an existing matching proposal.

- [ ] After engineering gates, reuse source-inventory.json, question-review-draft-v2.json and the separate first-selection/shared-scope/disposition review in the Design-listed roots. Reverify only the two actual packages/members and consumed evidence identities. Do not reconstruct203 units or re-OCR.
- [ ] Build the strict draft from retained exact spans with shared scope label included. Fixed proposed set:12A1/9/10/11;12B3/4/5/6;12C2/3/8/9/10/13/17/18. Preserve16 proposed/163 later/16 held/8 prerequisite IDs and order. Match all question/subpart/answer/image bytes to prior review; verify no new implicit source edits or metadata estimates.
- [ ] Call propose_vector_ch12_mapping only; independently recompute returned mapping/input-binding hashes using specified serialization. Confirm15 source worked solutions,1 result key, no independent explanation, one necessary image and unknown marks/difficulty; any new discrepancy stays explicit, not automatically cleared.
- [ ] Stop at **USER DECISION REQUIRED — SOURCE MAPPING APPROVAL**. Present actual batch/source IDs, exact two-package bindings, actual mapping digest, selected16 and coverage/limitations, output paths and the API's exact source-mapping approval request. No real canonical/preflight before that exact approval. No prediction of16 net-new or formal total693.

## Conditional continuation — not authorized by Plan approval alone

After actual source-mapping approval, reverify unchanged mapping and both input packages, B/C availability and current V1.24 state. Only then adapt and run real authoritative preflight against the latest independently verified parent (genesis only if truly no parent). If parent/content changes, recompute preflight and do not reuse stale import authority. If blocked, retain the complete approved selection and report precise IDs/signals; do not drop rows to force READY.

Stop at **USER DECISION REQUIRED — REAL BATCH IMPORT**, displaying actual batch_id, preflight_sha256, parent_candidate_digest, classifications/issues and projected count. The exact requested statement uses `USER APPROVED IMPORT BATCH <batch_id> <preflight_sha256> V1.24 PARENT <parent_candidate_digest>`. It is not received approval. No real writer is part of this chapter Plan; no promotion, F6 real operation or later chapter batch starts automatically.

## Design / acceptance correspondence and self-review

| Approved requirement | Plan / explicit oracle |
|---|---|
| Design§1–2 scoped inputs/safe inventory; user1–2 | Tasks1–3; swapped/hash/basename/same-line/whole-subparts fixtures |
| Design§3 strict mapping, coverage and approval; user3,6 | Tasks3,6; gaps/overlap/scope/203-ID disposition; recompression invalidation |
| Design§4 exact rendering/hashes; user4–5 | Task4 byte literals, raw-vs-rendered SHA and boundary-cut tests |
| Design§4 image ownership; user8 | Task5 four tokens/two files/three path-role pairs; Task7 source-map closure |
| Design§5 source truth; user9 | AnswerCoverageTests, Task7 candidate projection and Task9 human review |
| Design§6 V1.24/23-field/manifest; user7,12 | A/B/C gate and Task7 real loader/genesis/verified-parent preflight |
| Design§7 historical/safety; user10–11 | Task6/7 races/cleanup and Task8 unchanged goldens/API/digests |
| Design§8 selection and user gates | Task9 then conditional exact-approved continuation; real writer excluded |

Author self-review: all five Review Focus conditions have named tests; input hashes, mapping no-LF and version-genesis LF are distinct; public fields/codes stay closed; synthetic oracles are independently authored; B absence is not a fabricated test failure; C cannot be claimed on mocks; no F6 prerequisite or task expansion. This is a Plan, not executed tests or independent implementation verification.

Independent written-Plan review on2026-10-23 by separate read-only reviewer `/root/vector_ch12_plan_review`: Critical0 / Important0 / openMinor0. Two Minor wording findings were corrected and re-reviewed: taxonomy comes from frozen formal V1.23, not a nonexistent config accessor; approval is a frozen carrier, not an invented approval-file input. Reviewer inspected the complete Design/Plan and relevant existing interfaces, but did not run tests, inspect future V1.24 output or re-review source mathematics. This result is not implementation PASS or human Plan approval.

Current stop: **USER DECISION REQUIRED — VECTOR CH12 IMPLEMENTATION PLAN REVIEW**. Preserve Native / Inline as the proposed execution method; await human Plan review and implementation authorization. The first16 mapping remains unapproved.
