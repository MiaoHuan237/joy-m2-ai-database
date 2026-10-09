# V1.23 Minimal Candidate Roll-Forward Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans for the recommended Native / Inline Execution, or superpowers:subagent-driven-development if explicitly selected instead. Execute task-by-task only after human Plan approval and execution-method confirmation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add the approved fixed V1.23 candidate boundary over formal V1.22/639, then consume the already-approved 2023 transcription for canonical output and read-only preflight, stopping before real import.

**Architecture:** Six version-specific sibling modules preserve the proven multi-batch candidate mechanism. The existing HKDSE adapter gains one append-only bridge; its old entry points, shared contracts and historical replay remain unchanged. Synthetic first-generation GREEN precedes verified-parent preflight RED, which precedes multi-batch writer/verifier RED.

**Tech Stack:** Existing Python runtime, standard-library dataclasses/pathlib/json/hashlib/sqlite3/tempfile/unittest and existing Joy M2 types; no dependencies, CLI, services or generic future-version framework.

**Spec:** `docs/superpowers/specs/2026-10-09-v123-next-version-candidate-design.md`, explicitly human-approved after checkpoint `f185b2e068720b3d6437272f73d1bfdc31b270f9`. Normative V122 source counterpart: `d006c502fd30bb9c655ed8c4694148c16b036f56`.

**Status:** WRITTEN PLAN — PENDING HUMAN REVIEW AND EXECUTION CONFIRMATION. Implementation NOT STARTED. Human Design and 2023 transcription approvals are already complete; do not request them again.

## Global Constraints

- Baseline exactly V1.22 / 639 published/selectable records, not 639 proven-distinct originals. Read `formal_complete_questions_v122` once; do not read only 591 or recount inherited candidate tables.
- SQLite `releases/V1.22/Joy_M2_Complete_Question_DB_V1_22.sqlite3`: SHA `a474846a5b1d10a0fe48a259522fbb327747319f4a114452bf9f294405d8d9e0`, size 10510336. Manifest `releases/V1.22/manifest.json`: SHA `441e00ac1536b959b40b6177bd17a6f14632a287f85145e202a51bcf137ddc8b`, size 7915.
- Release digest `89a592abf52507cc0325f9c6f30ee2c74d4ec55fdcef988fdae6cb12f5a3073b`; semantic SHA `964cceff64cdeaedf663d1f9be98aaaf6adf3ffe2cddf6a18447ea141948a1c4`; baseline DB schema `task12-v122-formal-v1`, manifest schema `task12-v122-formal-manifest-v1`.
- Target V1.23 only. Genesis exactly `ea3b7db78210e045761784a2e415387c1b17f13b5aedde484ca2ae248a45eec7`. A missing parent artifact never permits a missing authority digest. Generation 000002+ binds the verified immediate predecessor, not genesis.
- Design §6 freezes all `task13-v123-*` serialization names, four `task13_v123_*` tables, `task13_candidate_questions_v123`, private `user_version=123`, first addition aggregate_order=640, file names and genesis JSON. No inherited object is renamed.
- Formal V1.18–V1.22, old generations and all source/approval evidence remain byte-identical. No `releases/V1.23/`, query-pointer change, historical cleanup, 2024/2025 ingestion, V1.24, promotion or real writer invocation.
- Existing sixteen-code taxonomy, normalization, duplicate/collision precedence, count semantics, API names/order, hashes and replay are frozen. Fuller MS does not authorize an old-row update or override a blocker. No altered IDs/fingerprints to force acceptance.
- Preserve all inherited image columns and view ancestry. Q6 uses approved PDF SHA/page/region references; the bridge does NOT generate canonical image bytes. Preserve existing incomplete-enrichment semantics; no hidden image-projection extension.
- Test inputs are isolated synthetic packages. Never invent an approval for real 2023. The 2023 approval below is transcription approval only.
- Read-only SQLite uses an absolute resolved `Path.as_uri()` plus `?mode=ro&immutable=1`, `uri=True` and query-only operation. Write only owned isolated synthetic candidate copies during implementation.
- Preserve the user's dirty AGENTS.md exactly; never stage/stash/reset/overwrite it. Only exact in-scope task paths may be committed. Ordinary push only; no history rewriting, merge, PR or tag.

## Review Focus

1. A 639-row formal view includes inherited candidate tables: test exact rows/order/image JSON preservation and collisions against 2019–2022 additions, not just old 591 (Tasks 3, 4A, 5).
2. Equal forged report/approval strings conceal wrong genesis: writer and verifier independently reconstruct the canonical projection and fail at their own boundary (Tasks 1, 3, 4A).
3. More complete answers conceal duplicate or package-level issues: keep exact-duplicate BLOCKED semantics, per-record classification versus batch blocking, and known-original reporting (Tasks 3, 4B1, 6).
4. Parent setup fails before the intended second-generation operation: prerequisite assertions and separately executed 4A/4B1/4B2 REDs prove each behavior; append failure preserves parents (Tasks 4A–4B2).
5. Truthful figure references or relocated package paths are mistaken for image files or changed content: exact four non-manifest projections, figure-locator retention, two-root equality and escaped SQLite paths (Tasks 2, 3, 4A, 6).

## Closed file map / Design correspondence

Work from the existing isolated `task8b/pipeline-migration` worktree. These are exactly Design §10's 23 paths; no new helper module or fixture directory. Source basenames below all live under `src/joy_m2/ingest/`.

| Action | Path | Responsibility / task |
|---|---|---|
| NEW | `src/joy_m2/ingest/v123_models.py` | 13 frozen counterparts; 1 |
| NEW | `src/joy_m2/ingest/v123_manifest.py` | strict loader; 1 |
| NEW | `src/joy_m2/ingest/v123_preflight.py` | genesis then verified-parent preflight; 3, 4B1 |
| NEW | `src/joy_m2/ingest/v123_writer_profiles.py` | fixed genesis/DDL/projection/checks; 3, 4A, 4B2 |
| NEW | `src/joy_m2/ingest/v123_writer.py` | first-generation then full-prefix build; 4A, 4B2 |
| NEW | `src/joy_m2/ingest/v123_verification.py` | independent verifier; 4A, 4B2 |
| MODIFY | `src/joy_m2/ingest/hkdse_pdf_adapter.py` | V123 bridge/imports only; 1, 2 |
| MODIFY | `src/joy_m2/ingest/__init__.py` | exact 18-name suffix; 1 |
| NEW | `tests/unit/test_v123_models.py` | models/API/strict loader; 1 |
| NEW | `tests/integration/test_v123_hkdse_bridge.py` | synthetic approved carrier and fidelity; 2 |
| NEW | `tests/integration/test_v123_preflight.py` | genesis and classification; 3 |
| NEW | `tests/integration/test_v123_candidate.py` | first build, parent preflight, multibatch; 4A–4B2 |
| NEW | `tests/regression/test_v123_historical_replay.py` | historical preservation and replay; 5 |
| MODIFY | `tests/unit/test_v119_writer_models.py` | exact export expectation only; 1 |
| MODIFY | `tests/unit/test_v119_promotion_models.py` | exact export expectation only; 1 |
| MODIFY | `tests/regression/test_v119_historical_replay.py` | exact export expectation only; 1 |
| MODIFY | `tests/unit/test_v121_promotion_models.py` | exact prefix/suffix migration only; 1 |
| MODIFY | `tests/unit/test_v122_models.py` | exact prefix/suffix migration only; 1 |
| MODIFY | `tests/unit/test_v122_promotion_models.py` | exact prefix/suffix migration only; 1 |
| MODIFY | `PROJECT_STATE.md` | current phase / actual gates; all |
| NEW | `docs/reports/V123_CANDIDATE_AUTHORITY_VERIFICATION.md` | RED/GREEN/review/operational evidence; 1–6 |
| EXISTING | `docs/superpowers/specs/2026-10-09-v123-next-version-candidate-design.md` | approved contract; progress sync only |
| NEW | `docs/superpowers/plans/2026-10-09-v123-next-version-candidate.md` | this reviewed execution sequence |

Historical test edits must retain EVERY old export and exact order, then append the exact new suffix. Replace stale absolute-tail assumptions with full historical-prefix/new-suffix equality, not subset tests. No behavior/hash/order assertions elsewhere may change. Test helpers remain in these listed new test files; copy existing synthetic fixtures into temporary roots, never edit their originals.

## Verified operational input — already approved, do not retranscribe

Repository root for relative paths below:
`/Users/miaohuanjoy/Desktop/joy-m2-ai-database-current/.worktrees/task8b-pipeline-migration`.

Let `E = data/staging/task10b-hkdse-2023/source-review-000001` (a documentation path abbreviation, not a new configuration field).

| Input | Actual path / identity |
|---|---|
| Batch | `JOY-M2-HKDSE-2023-PP-MS`; 12 complete questions / 100 marks |
| Approved proposal | `E/transcription-proposal-000001/transcription.json` |
| Semantic transcription digest | `3a3a223a23f694083469281c64be5c5402152c557e3bc36654d400ce5143d618` |
| Proposal file SHA | `4c9df20019c54876f01e9c0a58352fceb07ed78d9d14246e3bd8288fcab6f700` (not the semantic digest) |
| Received approval | `E/TRANSCRIPTION_APPROVAL.json`, exact three-field receipt |
| Approved metadata | `E/input/source-corrected-staging-v2.json`; SHA `351462b3e45d4ea0f5b84b400d28aa0431bf3c0a830b16aff8a2eda7940a7490` |
| Source review | `E/FULL_TRANSCRIPTION_REVIEW.md`, `E/evidence/independent-review-final.json` |
| Aligned reviewed passes | `E/extraction-passes/reconciled-a.json`, `E/extraction-passes/reconciled-b.json` |
| Original metadata (preserved) | `/Users/miaohuanjoy/Desktop/joy-m2-ai-database-current/data/staging/joy_m2_hkdse_2023_pp_ms_staging.json`; SHA `4114f8671f9503070b7495925502bc21049d32fb33dd85096916bff9bd304b64` |
| Original PP | `/Users/miaohuanjoy/Desktop/M2/M2 Past Paper/M2_2023-pp.pdf`; SHA `ec60f6d978a44b7e3ce2e20e704ed6307655efeafa984a88e6567b0254275dfd` |
| Original MS | `/Users/miaohuanjoy/Desktop/M2/M2 Past Paper/M2-ms/M2_2023-ms.pdf`; SHA `5a8b56914dee3931d4e1f826b721360ad0a59c33056dba01caf272140a0f7d97` |

Received human statement, NOT an import approval:

```text
USER APPROVED PDF TRANSCRIPTION BATCH JOY-M2-HKDSE-2023-PP-MS 3a3a223a23f694083469281c64be5c5402152c557e3bc36654d400ce5143d618
```

The stored proposal stays PROPOSED as historical evidence; the existing approval API returns a VERIFIED carrier without altering those bytes. Independent review has resolved Q6 figures, Q7 shared condition/taxonomy, Q10 notation and full MS; zero review issues/unknown vocabulary. Pass B records reviewed reconciliation, not blind independent OCR. Do not rerun transcription, recreate a proposal or seek the same approval. Only semantic payload change triggers reapproval, not simply Plan/target creation.

## Public interfaces and dependency contract

13 exact models in Design §5 order, with field counts:
`V123BatchImportManifest(18)`, `V123AdaptedImportPackage(3)`,
`V123BatchLedgerEntry(9)`, `V123EffectiveState(5)`, `V123PreflightRequest(5)`,
`V123ImportPreflightReport(34)`, `V123ImportPreflightResult(5)`,
`V123ImportApproval(5)`, `V123ApprovedBatch(3)`, `V123CandidateContract(25)`,
`V123CandidateBuildRequest(3)`, `V123CandidateVerificationRequest(3)`,
`V123CandidateArtifacts(8)`.
Freeze every field name/order, runtime type, no-default rule, tuple isolation and validation from the pinned V122 counterpart; substitute only V123 nested types and Design constants. Use explicit expected field tuples in tests, not a dynamic expectation generated from the new implementation.

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

Append these five functions after the thirteen carriers, after the ENTIRE existing package surface including nine V122 promotion names. No `approve_v123_import`: exact approval is a `V123ImportApproval` inside `V123ApprovedBatch`.
Models/profiles are leaves; verifier does not import/call writer or preflight. Preflight may call verifier; writer may reconstruct preflight and call verifier. Reuse version-neutral pure helpers without moving historical code or monkey-patching version constants.

## Commands / RED evidence protocol

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=src
JOY_PY=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
git status --short
git branch --show-current
git rev-parse HEAD
```

Every behavior group: write the named tests -> run and record collected/PASS/FAIL/ERROR/skip/expectedFailure/exit code and precise assertion/failure location -> minimum production -> same tests GREEN. Only an explicit missing-API assertion is an API-existence RED, not behavior RED. Import/setup/fixture errors are never accepted. For callable scaffolds, catch ONLY `NotImplementedError` around the operation under test and turn it into `self.fail("<specific behavior> not implemented")`; prerequisite helpers must already succeed. Never catch arbitrary exceptions to manufacture RED. Preservation tests may be GREEN immediately but do not authorize new production behavior.

In this Plan, READY is shorthand for the exact report status
`READY FOR USER IMPORT APPROVAL`; tests assert that literal and zero blocking
errors, not the shortened word. Preserve exact counterpart exception classes.

Use independently selectable unittest classes below. Do not create later dependent tests in shared setUp or claim unexecuted assertions failed. Keep later behavior absent until its own RED. Each GREEN group gets focused regression and a scoped review before a task-only checkpoint commit under autonomy; exact paths only, no `git add .`. Native execution owns implementation; final independent whole-diff review is mandatory.

## Task 1 — Models / minimal API scaffolds, then strict loader

**Files:** `test_v123_models.py`; the six new source modules as needed for import-safe scaffolds; append imports/bridge scaffold in `hkdse_pdf_adapter.py`, suffix in `ingest/__init__.py`; six historical export-test paths; report/state.

**Interfaces:** Produces all 13 exact carriers and five importable signatures. Only the loader has behavior at this task's exit; preflight/bridge/build/verify remain `NotImplementedError` scaffolds.

- [ ] Add `V123ApiTests.test_model_module_exists` using `importlib.util.find_spec` + `assertIsNotNone`; no top-level import of missing code. Run `"$JOY_PY" -m unittest -v tests.unit.test_v123_models.V123ApiTests`; record assertion RED, then create only the import-safe module.
- [ ] Add `V123ModelContractTests`: each class exists before use; assert exact field tuples/counts/type hints/defaults/frozen behavior; list-to-independent-tuple; reject bool-as-int and wrong nested V122/parallel carriers. Assert fixed profile/baseline values and exact five-part import approval text including PARENT. Run that class RED; implement only models; run GREEN.
- [ ] Extend API tests to exact function parameter/return annotations and entire literal historical `__all__` prefix plus 18-name suffix; assert no aliases/duplicates. Run RED. Add only the five minimal scaffolds/exports, then migrate the six listed historical surface expectations exactly; run new API/model tests and those six full modules GREEN. No old behavior assertions may change.
- [ ] Add `V123ManifestLoaderTests.test_valid_exact_manifest` and independently collected invalid cases: malformed UTF-8/JSON, NaN/Infinity, wrong schema/target, missing/extra fields, duplicate keys at each object depth, wrong type/group/order, bool size, unsafe/absolute/dotdot/backslash/symlink paths, duplicate member identity, missing/extra inventory and bad hash/size. Assert counterpart input exception and unchanged package. Run loader tests RED at the callable loader, then implement `load_v123_import_manifest` in `v123_manifest.py` using the pinned V122 loader semantics and V123 identities; run all unit tests GREEN.
- [ ] Record fresh counts/review, inspect scope and commit only Task 1 paths as `feat: add V1.23 candidate contracts and strict loader`. API scaffolds are explicitly not implemented behavior.

## Task 2 — Canonical bridge

**Files:** `tests/integration/test_v123_hkdse_bridge.py`, append-only bridge/imports in `hkdse_pdf_adapter.py`, report/state.
**Consumes:** Task 1 loader/models and existing `approve_hkdse_pdf_transcription` using isolated synthetic transcription fixtures.
**Produces:** the exact V123 bridge signature above; five-file canonical package accepted by Task 1 loader.

- [ ] Add `V123HkdseBridgeTests.test_exact_five_file_projection`: synthetic approval creates `import_manifest.json`, `records/candidates.json`, `source/transcription.json`, `source/source-map.json`, `answers/official-ms.json` only. Assert V1.23 target/schema and all four NON-manifest bytes exactly equal the existing V122 bridge for the same synthetic verified carrier in separate roots.
- [ ] Add independent tests for forged approved-carrier content/digest, proposal instead of verified carrier, output exists, symlink/escape/source/formal overlap, no partial output on rejection; preserve counterpart exception types. `test_pdf_figures_do_not_become_canonical_images` asserts exact PDF locators retained, zero fabricated image assets and unchanged incomplete-enrichment fields. Test all subparts/MS/marks/taxonomy/difficulty survive and no record is silently dropped as duplicate-looking.
- [ ] Run `"$JOY_PY" -m unittest -v tests.integration.test_v123_hkdse_bridge` RED, with synthetic Task10B approval already succeeding. Implement only `adapt_verified_hkdse_pdf_transcription_v123` and required imports; reuse the existing neutral projection/safety helpers, no edits inside old bridges.
- [ ] Run bridge GREEN plus Task 1 and Task10B suites; compare two-root relative sets/bytes. Record scoped review and commit `feat: bridge approved HKDSE transcription to V1.23`.

## Task 3 — Genesis-only authoritative preflight

**Files:** `tests/integration/test_v123_preflight.py`, `v123_preflight.py`, genesis/profile constants in `v123_writer_profiles.py`, report/state.
**Consumes:** Task 1 loader, exact formal V1.22, parent artifact `None`.
**Produces:** `preflight_v123_import` for genesis context only, returning V123 result/report/effective state bound to the literal genesis. Non-genesis branch remains a scaffold until 4B1.

- [ ] Inside the new test module define `_contract() -> V123CandidateContract`, `_make_package(parent: Path) -> Path`, `_request(package: Path) -> V123PreflightRequest`, `_fingerprint(root: Path) -> tuple`. Port the existing V122 test helpers, using temporary copies of `tests/fixtures/task10a/v120-batch-a` and exact Design values only. Keep helpers local; no parent is constructed here. A package-load smoke assertion must pass before recording behavioral RED.
- [ ] Add `V123GenesisPreflightTests.test_complete_639_baseline_and_genesis`: actual result before_count=639, effective-state candidate_count=0/projected=639/empty ledger, report/state parent exactly genesis, normalized candidates/issues match predecessor classifier semantics. A one-record synthetic net-new input projects 640; this is NOT the real 2023 prediction.
- [ ] Add baseline negative cases for SHA/size/manifest/schema/version/view/count/unique IDs/selectability, readonly escaped roots (spaces, `#`, Unicode), malformed payload exception vs representable structured issues. Preserve both exception and batch/record classifications. Verify source/formal snapshots unchanged.
- [ ] Add `test_fuller_ms_exact_duplicate_stays_blocked`, `test_truthful_second_source_matching_hash_collides`, `test_nonmatching_identity_is_not_proof_of_new_original`, `test_single_baseline_adaptation_predicates`, `test_multiple_matches_ambiguous`, `test_package_blocker_preserves_record_classification` and `test_mixed_duplicate_blocks_batch`. Use isolated source-identity-controlled fixtures without changing formal rows. Assert actual issue codes/severity/classifications/counts from Design §4 and pinned `_classify`, including preflight `_load_candidates` omission behavior, NOT strict public manifest-loader behavior. For structured file-integrity tests, load a valid manifest/request BEFORE altering a declared file, then call preflight directly; do not rerun `_request`'s strict loader on the corrupted file and mislabel its setup exception as preflight RED. Include matching formal records from the 2019–2022 inherited layers and historical image references, not just pre-2019 rows.
- [ ] Add `test_canonical_genesis_projection` requiring exactly Design §6 sorted compact UTF-8 JSON plus LF -> literal genesis; no cwd/time/path. First-context None/empty/old-version digest are rejected by their owning carrier/context. Independently compare two relocated package roots for identical report/digest.
- [ ] Run `"$JOY_PY" -m unittest -v tests.integration.test_v123_preflight` RED. Implement only baseline reader, preserved classification/report/digest and fixed `_genesis_digest() -> str` in profiles. No candidate DDL/writer/parent preflight yet. Run GREEN plus Tasks 1–2; record scope/review and commit `feat: add V1.23 genesis preflight`.

## Task 4A — First-generation writer and independent verifier

**Files:** `tests/integration/test_v123_candidate.py`, `v123_writer_profiles.py`, `v123_writer.py`, `v123_verification.py`, report/state.
**Consumes:** GREEN genesis preflight, single synthetic V123ApprovedBatch with exact genesis approval; does NOT require parent preflight.
**Produces:** `build_v123_candidate` and `verify_v123_candidate` for exactly one approved batch; a verified real-format synthetic parent usable by 4B1.

- [ ] Define local test helpers `_make_named_package(parent: Path, name: str) -> Path` from existing synthetic A/B fixtures; `_approved(package: Path, config: PipelineConfig, parent: V123CandidateVerificationRequest | None = None) -> V123ApprovedBatch`; `_tree(root: Path) -> tuple`. `_approved` must assert READY and correct parent BEFORE approval construction; only synthetic batch IDs allowed in these writer tests. Non-None branch is not used until 4B1 GREEN. Reuse Task 3 helpers, no new file.
- [ ] Add `V123FirstGenerationTests`: single A yields candidate_count=1/projected=640, ledger ordinal1, first aggregate_order640, private user_version123, candidate/selectable0, all639 formal rows preserved. Compare inherited schema SQL, metadata/table rows and four image columns exactly; only new four tables/one view and private user_version may differ. Do not re-add inherited candidates.
- [ ] Test independent reconstruction at BOTH boundaries: writer and verifier each call fixed genesis reconstruction and bind report AND approval. None/empty/omitted/bad target/old genesis and forged matching valid-length digests cannot pass; changing canonical projection count/schema also fails. Use well-formed forged carrier tests to reach context validation; constructor errors alone do not prove writer/verifier rejection.
- [ ] Assert all24 counterpart check names/order, only `v121_preservation` -> `v122_preservation`. Independently exercise malformed input-context exceptions versus parsed corruption FAIL; manifest/SHA/ArtifactRef/rollback/image/extra-file closure; SQLite/schema/FK/ledger/count/digest corruption. Missing checks must fail corresponding controls, not merely rely on a builder's previous PASS.
- [ ] Test two-root byte-identical ALL candidate artifacts and relative ArtifactRef identities; readonly verifier never repairs. Test existing destination, symlink/formal/source overlap, injected failure before atomic no-replace publication and owned-temp-only cleanup. Snapshot source/formal bytes before/after each failure.
- [ ] Run `"$JOY_PY" -m unittest -v tests.integration.test_v123_candidate.V123FirstGenerationTests` RED at writer/verifier, not setup. Then implement fixed DDL/projection, one-batch writer and independent verifier only. No multi-batch port hidden in this GREEN. Run class plus Tasks 1–3 GREEN; record checkpoint `feat: add V1.23 first-generation candidate verification` after scoped review.

## Task 4B1 — Verified-parent preflight

**Files:** `tests/integration/test_v123_candidate.py`, `v123_preflight.py`, report/state. No multi-batch writer extension.
**Consumes:** 4A GREEN builder/verifier to create synthetic A and a V123CandidateVerificationRequest. The request includes its candidate directory, ordered approved batches and fixed contract, matching the exact model.
**Produces:** preflight over full effective state: 639 + all accepted parent additions; exact verified parent digest/order in B report and state.

- [ ] Add `V123ParentPreflightTests`: assert A first builds and verifies PASS before the operation under test; snapshot A. Fresh B preflight before_count=640, projected641 for one synthetic new record, parent=A digest != genesis, exact ordered ledger. Include B duplicate/collision against A and retained formal-layer references; accepted-parent taxonomy participates in effective state.
- [ ] Test tampered/wrong-version parent, parent request/manifest mismatch, missing closure, stale supplied state and genesis reset refusal. Unsafe/unverifiable parent is context failure, not a fabricated READY report. Prove all parent bytes unchanged and equivalent roots identical.
- [ ] Run only that class; prerequisite success is required and missing parent-preflight is the precise RED site. Implement verified-parent indexing/report/digest using the independent 4A verifier; run class and 4A GREEN. Record scoped review/checkpoint `feat: bind V1.23 preflight to verified parent state`.

## Task 4B2 — Multi-batch writer/verifier

**Files:** `tests/integration/test_v123_candidate.py`, `v123_writer.py`, `v123_verification.py`, supporting fixed profiles only if required, report/state.
**Consumes:** 4A verified A and 4B1 valid READY B result/approval bound to A; no missing prerequisite may be counted as this RED.
**Produces:** full ordered-prefix rebuild/verification into a NEW immutable generation; previous outputs never modified.

- [ ] Add `V123MultiBatchTests`: explicitly assert A verify PASS, B before640/parent=A, B exact approval, THEN build prefix(A,B). Require count2/projected641, contiguous ledger and unique IDs, B parent=A, unchanged A and formal639. Add a third synthetic preflight after(A,B) to prove indexes contain the complete accepted prefix, not only the last batch.
- [ ] Independently test stale B genesis preflight/approval after A, reordered/truncated/substituted prefix, changed package bytes, duplicate batch ID, old-version approvals, missing/reset parent, forged counts, collision authority, and append failure leaving A intact. Do not treat API access to an old immutable generation as a global latest oracle: operational latest-parent recovery remains mandatory under Design §8.
- [ ] Run `"$JOY_PY" -m unittest -v tests.integration.test_v123_candidate.V123MultiBatchTests` RED only after 4B1 GREEN; then implement multi-batch prefix closure in writer/verifier. Verify two roots byte-identical, no-replace boundary and failure cleanup; run all candidate/preflight tests and Tasks 1–2 GREEN.
- [ ] Record separate 4A/4B1/4B2 failure sites/counts and scoped review; commit `feat: accumulate verified V1.23 candidate batches`. Synthetic success grants no real import approval.

## Task 5 — Historical regression / independent implementation review

**Files:** `tests/regression/test_v123_historical_replay.py`, report/state and only owning-task in-scope fixes.
**Consumes:** complete GREEN Tasks 1–4B2; existing frozen replay helpers with materialization disabled.
**Produces:** independent C0/I0 verdict, fresh complete maintained results, exact scope/frozen proof, reviewed engineering checkpoint.

- [ ] Add historical tests pinning all formal18–22 bytes/counts (497,502,543,591,639), complete639 logical inheritance, API prefix and all past schemas/digests/approval chains. Reuse `tests.regression.test_v122_historical_replay.historical_requests()` for V119–121; V122 uses `tests.integration.test_v122_promotion.real_candidate()` (read-only reconstruction) and `promotion_contract()`. Never rebuild historical candidates to run replay. Assert read-only formal verifiers pass18/21/21/21 checks respectively.
- [ ] Preserve the current no-V123-publication boundary without inventing future promotion authority. In isolated roots, test refusal of formal output paths. No test should rewrite an old lifecycle guard or treat a future authorized publication as implicitly approved now. Historical lifecycle semantics remain untouched.
- [ ] Run all maintained modules with actual collected/run/FAIL/ERROR/skip/expectedFailure counts, not a copied prior total. The only excluded attribution suite remains the known legacy module; no failed maintained module may be excluded:

```bash
"$JOY_PY" - <<'PY'
from pathlib import Path
import unittest
legacy = Path('tests/regression/test_task8b_legacy_pipeline_behavior.py')
modules = [str(p.with_suffix('')).replace('/', '.')
           for p in sorted(Path('tests').rglob('test_*.py')) if p != legacy]
assert modules
suite = unittest.defaultTestLoader.loadTestsFromNames(modules)
collected = suite.countTestCases()
r = unittest.TextTestRunner(verbosity=1).run(suite)
print(dict(collected=collected, run=r.testsRun, fail=len(r.failures),
           error=len(r.errors), skip=len(r.skipped), expectedFailure=len(r.expectedFailures)))
assert r.wasSuccessful() and not r.skipped and not r.expectedFailures and not r.unexpectedSuccesses
PY
"$JOY_PY" -m unittest -v tests.integration.test_ingest_preflight
"$JOY_PY" -m unittest -v tests.unit.test_hkdse_pdf_models tests.unit.test_hkdse_pdf_adapter tests.integration.test_hkdse_pdf_adapter
"$JOY_PY" -m unittest -v tests.regression.test_task7_project_initialization tests.regression.test_v123_historical_replay
"$JOY_PY" releases/V1.18/verify_task6_release.py releases/V1.18
git diff --check
```

Task9A41, Task10B50 and Task7 7 are unchanged-suite expected counts; report fresh actuals and investigate any discrepancy. Report new V123 count separately. If legacy attribution runs, preserve known9PASS/2FAIL categories (SQLite deterministic hash and frozen byte-equivalence); do not fix or mislabel these as maintained PASS. Do not search/read/hash actual V1.16 ZIP.

- [ ] Independent whole-implementation reviewer checks Design/Plan, exact fields/exports, genuine RED sites, genesis trust boundaries, 639-row/image inheritance, full effective-state dedup, bridge fidelity, stale-parent/failure protection, readonly URIs, source approval preservation and closed paths. Require Critical0/Important0; each real defect receives targeted RED→minimal fix→GREEN→re-review. No reviewer authorization can enlarge scope.
- [ ] Rerun affected/full gates after final fixes; report exact commands/results, source snapshots, all formal/candidate hashes, no real writer and no releases/V1.23. Synchronize state/report, explicitly stage task files and commit/push normally. Inspect commit file list, diff-tree check and upstream identity; preserve dirty AGENTS. Only then may Task6 run.

## Task 6 — Reuse approved 2023 canonical + read-only preflight; stop

**Files:** ignored NEW roots under `data/staging/task13-v123-hkdse-2023/**`; report/state only for checkpoint narrative. Existing source-review root is read-only. No operational corpus/approval/PDF committed.
**Consumes:** complete reviewed V123 implementation AND the exact already-received transcription approval above.
**Produces:** actual canonical/preflight identities and human import report, NOT a candidate database.

- [ ] Rehash the actual proposal, metadata, PP/MS and receipt. Reconstruct exact HkdsePdfTranscriptionRecord/PageSpan/Batch objects from saved JSON and call existing `approve_hkdse_pdf_transcription(proposal, approval)`; there is no invented public proposal loader. Assert semantic digest, 12 records/100marks and VERIFIED carrier while stored proposal remains unchanged. Do not rerun OCR/proposal generation or ask again for transcription approval.
- [ ] Recover actual V123 candidate state and any receipts before choosing parent. If none accepted exists, use no artifact but exact genesis `ea3b7db78210e045761784a2e415387c1b17f13b5aedde484ca2ae248a45eec7`; if one now exists, independently verify its complete latest lineage and bind its exact digest instead, never overwrite/reset it or silently use stale genesis. Report any conflicting operational state before proceeding.
- [ ] In two fresh no-replace roots generate packages through the Task2 bridge; compare all five files byte-for-byte. Preserve all12inputrecords, source IDs, official MS, Q6 PDF locators, Q7 shared condition and Q10 notation. State explicitly image_files remains as the existing bridge emits; PDF locators are not canonical image assets.
- [ ] Run actual V123 preflight twice with identical verified parent authority; compare candidate tuples/issues/report/digest. Report actual before/detected/new/duplicate/rejected/ambiguous/adaptations/approved counts, missing answers/explanations, taxonomy/difficulty, issues, parent, preflight SHA and projected count. Never manufacture READY or predeclare12new/651total.
- [ ] Add report-only per-ID original-source reconciliation: all12originals are already represented in formal2023-Q1..12; distinguish new stored rows from known-original additional sources, content/evidence supplementation and truly unrepresented originals. No new database code/status/taxonomy; no ID/text/hash manipulation or dropping duplicate rows.
- [ ] If blocked, identify exact IDs, signal and issue code, preserved classification and minimal source/disposition decision. Fuller MS cannot override a blocker or update an old row. No broad historical cleanup prerequisite. If READY, stop at `USER DECISION REQUIRED — REAL BATCH IMPORT` and present:

```text
USER APPROVED IMPORT BATCH JOY-M2-HKDSE-2023-PP-MS <actual_preflight_sha256> V1.23 PARENT <actual_verified_parent_digest>
```

For the first batch the parent token MUST be the literal V123 genesis above. These placeholders are runtime report values, not approval or permission to construct one. No real `V123ImportApproval`/writer call until the user supplies that exact statement; transcription approval cannot substitute. Reverify parent after any later import approval; changed parent requires fresh preflight and approval. Do not start2024/2025 or promotion.

## Self-review, scope/test traceability and handoff

| Design authority | Plan coverage |
|---|---|
| §§1–3 approval, formal639, fixed siblings | Global Constraints; Tasks1/3/4A/5 |
| §4 duplicate/adaptation/source-supplement limits | Tasks3/4B1/4B2/6 |
| §5 models/18exports | Task1 literal exact-contract tests |
| §6 namespace/genesis | Tasks1/3/4A/4B2 independent bindings |
| §7 bridge/fidelity/image limitation | Task2 and actual Task6 |
| §8 effective state/atomicity/24checks | Tasks3/4A/4B1/4B2/5 |
| §9 approved2023source and human gates | Verified input table; Task6 |
| §10 closed23paths/userAGENTS | File map; every scoped commit |
| §11 RED/review/regression | RED protocol; Tasks1–5 |

- [x] Self-review covers all Design sections, exact interfaces/types and closed23paths.
- [x] Five Review Focus risks have named owning test groups; no setup/import failure qualifies as behavior RED.
- [x] Dependency order is models/scaffolds → loader → bridge → genesis → first generation → parent preflight → multibatch → historical/review → real readonly preflight. No later stage is implemented by copying whole predecessor modules before its RED.
- [x] Already-approved transcription is reused; no fake digest or repeated transcription gate. No net-new forecast or hidden image projection.
- [x] Independent technical Plan review has zero Critical/Important; remediate in these docs only before commit.
- [ ] Human Plan review and Native / Inline Execution confirmation BEFORE implementation. Do not repeat Design approval.

Recommended method: **Native / Inline Execution**, with one owner for the closely coupled model/preflight/writer tasks, scoped checkpoint reviews and a separate final whole-implementation review. Recommendation is not execution authorization. All implementation checkboxes remain unchecked until the user approves this Plan and confirms execution.

Technical review record (2026-10-09): read-only reviewer `v123_plan_review`
independently checked the approved Design, actual predecessor interfaces,
fixtures, baseline, genesis and 2023 proposal/receipt. Final Critical 0 /
Important 0 / Minor 0. One minor test-sequencing clarification was resolved:
load a valid request before file tampering so preflight, not strict-loader setup,
owns the structured failure. No implementation or PDF retranscription was
performed by this review. Human Plan review/execution confirmation remains open.
