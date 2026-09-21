# V1.22 Next-Version Candidate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Carry the approved 2019 HKDSE transcription through a V1.22 canonical package and authoritative read-only preflight over frozen V1.21/591, stopping before real import.

**Architecture:** Add fixed V1.22 sibling carriers, loader, preflight, writer profiles, writer and verifier. Extend only the existing HKDSE adapter entry point and append-only package surface; synthetic first/second-generation tests close the parent chain before any real operational preflight.

**Tech Stack:** Existing project Python runtime; standard-library dataclasses, pathlib, hashlib, json, sqlite3, tempfile and unittest; existing PipelineConfig and shared evidence models. No dependency additions.

**Spec:** `docs/superpowers/specs/2026-09-21-v122-next-version-candidate-design.md`, approved clarification commit `f51aaceaf08359747983a4dbccdb3b5ad0ee9cea`.

**Status:** APPROVED — V1.22 IMPLEMENTATION PLAN. User approved Native / Inline Execution; implementation checkpoints are recorded in the verification report.

## Global Constraints

- The Design is approved. This Plan must be written, reviewed and committed before implementation; writing this Plan does not execute any task below.
- Formal V1.18/497, V1.19/502, V1.20/543 and V1.21/591 remain byte-identical. `releases/V1.22/` remains absent.
- Baseline: exact V1.21 SQLite SHA `93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a`, 10063872 bytes; manifest SHA `a04f7ee7b67991427bffd3e5a3de70a310d0889fdf8f0535649840a44baf3a40`, 7913 bytes; release digest `f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3`.
- Target: exactly V1.22. Formal view: `formal_complete_questions_v121`; baseline schema `task11-v121-formal-v1`; baseline manifest schema `task11-v121-formal-manifest-v1`.
- First parent artifact may be absent, but authority parent digest MUST be `7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7`. Writer and verifier each reconstruct the frozen genesis projection, not merely trust supplied matching digests.
- Generation 000002+ requires the exact verified previous V1.22 candidate digest and its parent verification request. No old genesis, absent-parent reset, reordered prefix or stale approval.
- No real 2019 writer invocation, fabricated real approval, formal release creation, promotion, later-year ingestion, generic version framework, new parser/OCR, CLI, dependency, fixture corpus or project script.
- The approved 2019 digest `3139b39d7c42d17fbc28870d00127dd2792943860ef615a2c950d528f98b6829` remains valid. Preserve `保留不給 1M 若遺漏檢驗` and source typo `藉 (b)(ii)` exactly; do not alter taxonomy, difficulty or any source/approval artifact.
- Task 9A manifest/candidate, sixteen-code taxonomy, normalization, provenance and error boundaries stay frozen. Do not search, open or hash an actual V1.16 ZIP.
- Every behavior group requires valid RED before its production implementation. Import/setup/fixture/environment errors are not RED. No weakened assertions or hash changes to make GREEN.
- All implementation edits are restricted to the closed file map below. User review of this Plan is distinct from the completed Design approval.

## Review Focus

1. No parent artifact is mistaken for no parent authority: explicit genesis report/approval binding and independently rejected forged matching digests (Tasks 1, 3, 4).
2. Formal V1.21 already contains 2015–2018: index all 591 exactly once, detect a duplicate from those additions, never recount inherited candidate tables (Tasks 3, 4).
3. V1.22 target selection changes source bytes or accepts forged transcription: compare all four non-manifest payloads and reject invalid approval without output (Task 2).
4. A second generation resets to genesis, uses stale package authority or cleans the parent on failure: verified full-prefix chain and fault-injected preservation tests (Task 4).
5. New exports or version substitutions silently alter historical API/schema/bytes: exact old prefix plus 18 names, read-only historical replay and preserved formal metadata (Tasks 1, 4, 5).

## Closed file map and responsibilities

Paths are repository-relative; execute from the existing isolated worktree on `task8b/pipeline-migration`. Do not create or switch branches at an internal checkpoint.

| Action | Exact path | Responsibility / owning task |
|---|---|---|
| NEW | `src/joy_m2/ingest/v122_models.py` | 13 frozen counterparts; Task 1 |
| NEW | `src/joy_m2/ingest/v122_manifest.py` | Strict 18-field loader; Task 1 |
| NEW | `src/joy_m2/ingest/v122_preflight.py` | Read-only genesis and verified-parent preflight; Tasks 3–4 |
| NEW | `src/joy_m2/ingest/v122_writer_profiles.py` | Fixed DDL, canonical projection and 24 checks; Task 4 |
| NEW | `src/joy_m2/ingest/v122_writer.py` | Synthetic-tested append-only builder; Task 4 |
| NEW | `src/joy_m2/ingest/v122_verification.py` | Independent read-only verifier; Task 4 |
| MODIFIED | `src/joy_m2/ingest/hkdse_pdf_adapter.py` | Append V1.22 imports/bridge only; Tasks 1–2 |
| MODIFIED | `src/joy_m2/ingest/__init__.py` | Append 13 carriers and 5 functions; Task 1 |
| NEW | `tests/unit/test_v122_models.py` | Models, loader and API scaffolds; Task 1 |
| NEW | `tests/integration/test_v122_hkdse_bridge.py` | Canonical/source fidelity; Task 2 |
| NEW | `tests/integration/test_v122_preflight.py` | Genesis and parent indexing; Tasks 3–4 |
| NEW | `tests/integration/test_v122_candidate.py` | Writer/verifier/chain tests; Task 4 |
| NEW | `tests/regression/test_v122_historical_replay.py` | Historical/frozen replay; Task 5 |
| MODIFIED | `tests/unit/test_v119_writer_models.py` | Append exact new export names only; Task 1 |
| MODIFIED | `tests/unit/test_v119_promotion_models.py` | Append exact new export names only; Task 1 |
| MODIFIED | `tests/regression/test_v119_historical_replay.py` | Append exact new export names only; Task 1 |
| MODIFIED | `PROJECT_STATE.md` | Current checkpoint, never grant import authority |
| NEW | `docs/reports/V122_CANDIDATE_AUTHORITY_VERIFICATION.md` | RED/GREEN/review/frozen evidence; Tasks 1–6 |
| EXISTING | `docs/superpowers/specs/2026-09-21-v122-next-version-candidate-design.md` | Committed Design; do not redesign during implementation |
| NEW | `docs/superpowers/plans/2026-09-21-v122-next-version-candidate.md` | This Plan |

This is exactly Design §10's 20-path scope, including the already-created Design. Test helper functions live inside the listed tests, not a new helper/fixture module. Existing fixture inputs may be copied into isolated temporary roots; originals remain read-only. The three historical test edits must not change any behavioral assertion. No shared/historical production module may be edited.

## Commands, authority references and dependency order

Read Design §§1–11 and `PROJECT_STATE.md` first. The normative V121 counterparts are frozen at `2c23402225c68e6dc0796547f68c47e5884e4d78`; inspect with `git show <commit>:<path>` rather than assuming historical Plan prose is executable. In particular, **do not add `approve_v122_import`**: approval is `V122ImportApproval` plus `V122ApprovedBatch`.

Use the following shell setup for all test commands below (no file creation):

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=src
JOY_PY=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
git status --short
git branch --show-current
git rev-parse HEAD
```

The dependency sequence is:

```text
Task 1: model RED/GREEN -> API-existence RED/minimal scaffolds -> loader RED/GREEN
Task 2: bridge behavior RED/GREEN
Task 3: genesis-only preflight behavior RED/GREEN
Task 4A: first-generation writer/verifier RED -> first-generation GREEN
Task 4B1: verified-parent preflight RED -> parent-preflight GREEN
Task 4B2: valid B approval -> multi-batch writer/verifier RED -> extension GREEN
Task 5: complete gates + independent implementation review + engineering commit
Task 6: exact real canonical/preflight only -> human import gate
```

Task 1 scaffolds make imports safe, not behavior complete. Parent-dependent tests belong to Task 4: do not build a nonexistent parent in Task 3 setup and mislabel setup errors as RED. No runtime import cycle: models/profiles are leaves; verifier must not import writer/preflight; preflight may call verifier; writer may call verifier and reconstruct approved authority. Reuse version-neutral pure helpers only where they introduce no version authority.

### Task 1: Exact models, minimal public surface, strict manifest loader

**Files:** `tests/unit/test_v122_models.py`, `v122_models.py`, `v122_manifest.py`, minimal function scaffolds in `v122_preflight.py`, `v122_writer.py`, `v122_verification.py`, appended bridge scaffold/imports in `hkdse_pdf_adapter.py`, `ingest/__init__.py`, and only export expectations in the three historical tests above. All source basenames here are under `src/joy_m2/ingest/`.

**Interfaces produced:** Thirteen exact Design §4 carriers, manifest 18 fields/report 34/contract 25; all nested V121 types become V122 counterparts, shared types unchanged. All five public signatures from Design §§6–8 are importable by the end of this task. Functions remain non-behavioral scaffolds except the loader.

- [ ] Add an API-existence test using `importlib.util.find_spec("joy_m2.ingest.v122_models")` and `self.assertIsNotNone(...)`, with no top-level import of the absent module. Run `"$JOY_PY" -m unittest -v tests.unit.test_v122_models`; require an assertion FAIL, not import ERROR.
- [ ] Create only the empty module. Add exact model contract tests, importing the module in test bodies and checking a carrier exists before constructing it. Port the valid model fixtures from `tests/unit/test_v121_models.py`, substituting only Design §§2/5's fixed values and V122 nested types. Run again: missing carriers/fields are valid contract RED. Do not implement models before this run.

Minimum exact-field/no-default example (imports are inside the test module after it is safely importable):

```python
def test_effective_state_exact_contract(self):
    from dataclasses import MISSING, fields, FrozenInstanceError
    from joy_m2.ingest import v122_models as m
    from joy_m2.models import ArtifactRef
    from pathlib import Path
    cls = getattr(m, "V122EffectiveState", None)
    self.assertIsNotNone(cls, "V122EffectiveState contract missing")
    self.assertEqual(tuple(f.name for f in fields(cls)), (
        "baseline_database", "candidate_digest", "batch_ledger",
        "candidate_count", "projected_question_count",
    ))
    self.assertTrue(all(f.default is MISSING and f.default_factory is MISSING
                        for f in fields(cls)))
    state = cls(ArtifactRef(Path("/tmp/v122-baseline.sqlite3"),
        "93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a",
        10063872, "sqlite"),
        "7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7",
        [], 0, 591)
    self.assertEqual(state.batch_ledger, ())
    with self.assertRaises(FrozenInstanceError):
        state.candidate_count = 1
```

- [ ] For all 13 types, freeze the V121 field matrix and resolved type hints with only explicit nested-type substitution; assert frozen/no defaults/exact types, list-to-tuple copying/no mutable alias, invalid nested carriers, count closure, bool-as-int rejection, exact strings and approval statement. Negative genesis state cases: null, empty, old V120/V121 or arbitrary SHA. Standalone approvals can represent later-generation digests; reject wrong genesis context at state/binding/writer/verifier boundaries, not by incorrectly forcing every approval to genesis.
- [ ] Implement `v122_models.py` from the pinned counterpart without changing shared models. Set fixed literals to Design §§2/5 only; preserve old baseline metadata inside copied objects. Run model GREEN and unchanged `tests.unit.test_v121_models`.
- [ ] Add five public API-existence/signature tests with `getattr` assertions, plus final exact `__all__`: preserve the entire committed prefix and append the 13 Design-listed names then the five functions in their exact order. Run RED before exporting. Update only the three historical exact-export expected tuples in the same test-first step; never weaken them to subset checks.
- [ ] Add annotated function scaffolds and append imports/exports. For example:

```python
def preflight_v122_import(
    request: V122PreflightRequest, config: PipelineConfig,
) -> V122ImportPreflightResult:
    raise NotImplementedError("V1.22 preflight behavior not implemented")
```

Use the exact Design signature for loader, bridge, builder and verifier as well. Import their declared types, but do not add file I/O, validation, DDL, a default PASS, empty result or hidden fallback. Existence GREEN does not count as behavior GREEN.

- [ ] Establish loader behavior RED using a temporary copy of `tests/fixtures/task10a/v120-batch-a`; change only manifest target/schema to V1.22/task12. Call the scaffold in the test body; catch only its `NotImplementedError` and `self.fail("strict loader behavior missing")`, never catch setup/import errors. Add duplicate JSON key, missing/extra field, wrong exact type, invalid file group/kind, unsafe path and semantic ordering controls with specific `InputFormatError`/existing counterpart exceptions. Require all expected missing-behavior failures before implementation.
- [ ] Implement `load_v122_import_manifest(path: Path) -> V122BatchImportManifest` using the pinned strict loader semantics. Run models/loader/public-surface GREEN and affected historical tests. Record actual counts/RED reasons in the verification report; update state and checkpoint with explicit approved paths only: `feat: add V1.22 candidate contracts`. Report remaining scaffolds as incomplete, never READY for real operations.

### Task 2: Verified HKDSE bridge, source-preserving canonical package

**Files:** `tests/integration/test_v122_hkdse_bridge.py`, `src/joy_m2/ingest/hkdse_pdf_adapter.py` (new V1.22 entry point/imports only).

**Interface:** `adapt_verified_hkdse_pdf_transcription_v122(verified: VerifiedHkdsePdfTranscriptionBatch, output_dir: Path, config: PipelineConfig) -> V122AdaptedImportPackage`; uses the Task 1 loader/carriers, not preflight/writer.

- [ ] Build synthetic verified input using the existing `tests.unit.test_hkdse_pdf_adapter.AdapterCase` setup/proposal and `HkdsePdfTranscriptionApproval`, as in the pinned V121 bridge tests. No real 2019 input or altered approval. Add tests before bridge behavior; call bridge in the test body, not setup, and translate only the deliberate scaffold `NotImplementedError` to an assertion FAIL.
- [ ] Lock five files exactly: `import_manifest.json`, `records/candidates.json`, `source/transcription.json`, `source/source-map.json`, `answers/official-ms.json`. Test loader equality, target/schema, verified-only input, reconstructed approval digest, forged carrier rejection and no output on rejection.

The behavior test must include the following comparison, with `self.verified`, `self.root`, `self.config` from the synthetic setup above:

```python
def test_only_manifest_target_changes(self):
    from joy_m2.ingest import hkdse_pdf_adapter as adapter
    old = adapter.adapt_verified_hkdse_pdf_transcription_v121(
        self.verified, self.root / "data/staging/old", self.config)
    try:
        new = adapter.adapt_verified_hkdse_pdf_transcription_v122(
            self.verified, self.root / "data/staging/new", self.config)
    except NotImplementedError:
        self.fail("V1.22 canonical bridge behavior missing")
    for name in ("records/candidates.json", "source/transcription.json",
                 "source/source-map.json", "answers/official-ms.json"):
        self.assertEqual((old.package_root / name).read_bytes(),
                         (new.package_root / name).read_bytes(), name)
    self.assertEqual(new.manifest.target_release_version, "V1.22")
```

- [ ] Add independent-root full-byte equality, existing-output no-replace, symlink/path escape, source/evidence overlap, and injected `atomic_rename_no_replace` failure tests. Assert no partial output/owned temp residue and unchanged source/formal tree hashes.
- [ ] Run `"$JOY_PY" -m unittest -v tests.integration.test_v122_hkdse_bridge`, recording valid behavior RED. Implement only the new bridge using existing source-preserving payload helpers plus V122 manifest/carrier. Do not change the four payload projections or old bridge functions.
- [ ] Require focused GREEN plus unchanged Task 10B (`tests.unit.test_hkdse_pdf_models tests.unit.test_hkdse_pdf_adapter tests.integration.test_hkdse_pdf_adapter`) 50/50 and V121 bridge tests. Record scope/evidence and commit `feat: add V1.22 HKDSE canonical bridge`.

### Task 3: Read-only genesis preflight

**Files:** `tests/integration/test_v122_preflight.py`, `src/joy_m2/ingest/v122_preflight.py`.

**Interface:** `preflight_v122_import(request: V122PreflightRequest, config: PipelineConfig) -> V122ImportPreflightResult`. The request fields stay exactly `manifest, package_root, baseline_database, parent_candidate, contract`; there is no new optional digest parameter. A missing parent artifact maps to mandatory genesis authority in returned report/state.

- [ ] Define test-only `_contract()` with all 25 exact Design §5 values. Define `_make_package(parent: Path)` by copying the existing synthetic fixture into `parent/package`, changing just manifest schema/target; `_request(package: Path)` loads it with the strict loader, exact baseline `ArtifactRef`, `None`, and that contract. `_fingerprint(root)` returns sorted `(relative_path, SHA256, size)` tuples. Keep helpers in this test file for Task 4 imports. Validate fixture construction independently before claiming behavior RED.
- [ ] Add the literal canonical genesis oracle independently of production:

```python
def expected_genesis():
    import hashlib, json
    payload = {
        "baseline_database_sha256": "93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a",
        "baseline_question_count": 591,
        "baseline_release_digest": "f69f7068312c8a1afe754871acc027c322b7f2a401ab87312400f39b27301fb3",
        "baseline_release_version": "V1.21", "candidate_count": 0,
        "schema": "task12-v122-genesis-v1", "target_release_version": "V1.22",
    }
    encoded = (json.dumps(payload, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False) + "\n").encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()

def test_no_parent_artifact_still_binds_exact_genesis(self):
    from joy_m2.ingest import preflight_v122_import
    request = _request(self.package)
    self.assertIsNone(request.parent_candidate)
    try:
        result = preflight_v122_import(request, self.config)
    except NotImplementedError:
        self.fail("V1.22 genesis preflight behavior missing")
    self.assertEqual(expected_genesis(),
        "7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7")
    self.assertEqual(result.report.parent_candidate_digest, expected_genesis())
    self.assertEqual(result.effective_state.candidate_digest, expected_genesis())
    self.assertEqual(result.report.parent_batch_count, 0)
    self.assertEqual(result.report.before_count, 591)
    self.assertEqual(result.report.detected_count, 1)
    self.assertEqual(result.report.new_candidate_count, 1)
    self.assertEqual(result.report.projected_after_count, 592)
```

- [ ] In test setup create only a temporary package/config root, never call unimplemented preflight. Add independent-root result/digest equality and package/formal zero-write snapshots. Add wrong baseline hash/size, sibling manifest identity, schema/view/count failures. Exercise deeper checks using an isolated modified baseline copy and narrowly patched outer hash gate, with an unmodified control; do not let an earlier hash rejection falsely claim schema/view/count coverage.
- [ ] Test duplicate against a formal V1.21 record with `formal_order > 543` (read-only query of its exact source/text/fingerprint evidence), so using an old 543-row view fails. Require one baseline index entry per `formal_order` 1..591; no inherited candidate double count.
- [ ] Port the existing readable malformed-candidate/file-integrity controls and 16-code classification behavior. Retain fatal unsafe/unavailable baseline/input boundaries and structured representable blockers. Assert issue code/order, exact count equations, ambiguity rejected-subset and adaptation-not-extra-count semantics, not merely non-READY.
- [ ] Run `"$JOY_PY" -m unittest -v tests.integration.test_v122_preflight` and confirm all intended failures are missing behavior. Implement genesis path, fixed baseline indexing, existing classifier/report/digest projection only. Non-None parent behavior remains explicitly incomplete until Task 4; never return READY by ignoring it.
- [ ] Require focused GREEN, unchanged V121 preflight and Task 9A 41/41, unchanged formal bytes. Record that parent behavior is still pending; commit `feat: add V1.22 genesis preflight`.

### Task 4: Verified parent chain, independent verifier and synthetic writer

**Files:** `tests/integration/test_v122_candidate.py`, parent cases in `tests/integration/test_v122_preflight.py`, `v122_writer_profiles.py`, `v122_writer.py`, `v122_verification.py`, parent path in `v122_preflight.py` (all source files under `src/joy_m2/ingest/`).

**Interfaces:** `build_v122_candidate(V122CandidateBuildRequest, PipelineConfig) -> V122CandidateArtifacts`; `verify_v122_candidate(V122CandidateVerificationRequest, PipelineConfig) -> VerificationReport`; Task 3 preflight with an exact `V122CandidateVerificationRequest` parent. Build/verification request fields are unchanged from Design counterparts; do not add a parent path field to the writer request. Reconstruct its full approved prefix instead.

- [ ] Add test-only `_approved(package, config, parent=None)` using fresh preflight, its exact batch/digest/parent, `V122ImportApproval` and `V122ApprovedBatch`. Use only synthetic A/B/C packages from existing task10a fixtures, in temporary staging roots; never auto-approve 2019. Both genesis and parent test prerequisites must be valid before expected failure assertions.

```python
def _approved(package, config, parent=None):
    from dataclasses import replace
    from joy_m2.ingest import (preflight_v122_import,
        V122ImportApproval, V122ApprovedBatch)
    result = preflight_v122_import(replace(_request(package),
        parent_candidate=parent), config)
    r = result.report
    approval = V122ImportApproval(r.batch_id, r.preflight_sha256, "V1.22",
        r.parent_candidate_digest,
        f"USER APPROVED IMPORT BATCH {r.batch_id} {r.preflight_sha256} "
        f"V1.22 PARENT {r.parent_candidate_digest}")
    return V122ApprovedBatch(result, package, approval)
```

- [ ] Write first-generation writer/verifier and downstream parent/second-generation test cases, but track their RED evidence separately. Call missing operations inside test bodies and turn only scaffold `NotImplementedError` into explicit FAIL. Do not create a parent with an unimplemented writer in `setUp`. A test stopped at its first-generation build does **not** establish parent-preflight or second-generation RED. Those cases must actually reach their own missing behavior in Steps 4B1/4B2 below, after Step 4A GREEN. A test stopped inside `_approved(..., parent)` at missing parent-preflight likewise does not establish multi-batch writer/verifier RED.
- [ ] Pin exact synthetic first/second counts (591+1=592, then 593), contiguous ledger, first new aggregate order 592, candidate `selectable=0`, and private `user_version=122`. Snapshot all baseline schema objects/logical rows, including historical metadata and candidate tables; only four new tables/one view plus private user_version differ. Formal bytes do not change.
- [ ] Add explicit first-generation authority negative controls: `None`, empty, omitted field, both old genesis values, arbitrary valid SHA; verify appropriate constructor rejection for malformed carriers and independent writer/verifier rejection for forged but matching report/state/approval values. A well-formed later-generation SHA is not intrinsically invalid; first-generation context makes it wrong. Also recompute a digest after changing the frozen genesis projection's baseline count/schema and reject it. Do not just compare against a mutable supplied constant.
- [ ] Add boundary tests requiring private pure genesis reconstruction in `v122_writer_profiles.py`; writer and verifier must each invoke reconstruction at their own entry/authority boundary, compare to the literal frozen digest, and bind both report and approval. A pure shared serializer is acceptable; verifier must not consume the writer's cached decision or invoke the writer. Mutation controls must show removing either boundary check is detected by its corresponding test. Do not implement the helper until this task's RED run below.

The profile reconstruction must serialize this exact Design projection, not read it from candidate artifacts:

```python
def _genesis_digest() -> str:
    projection = {
        "baseline_database_sha256": BASELINE_SHA256,
        "baseline_question_count": 591,
        "baseline_release_digest": BASELINE_RELEASE_DIGEST,
        "baseline_release_version": "V1.21", "candidate_count": 0,
        "schema": "task12-v122-genesis-v1", "target_release_version": "V1.22",
    }
    actual = sha256_bytes(canonical_json_file_bytes(projection))
    if actual != "7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7":
        raise InputFormatError("V1.22 genesis projection mismatch")
    return actual
```

`BASELINE_SHA256`, `BASELINE_RELEASE_DIGEST`, `sha256_bytes` and `canonical_json_file_bytes` are private fixed profile constants/pure helpers, following the pinned counterpart; this adds no public API. Write the tests and verify RED before adding even this behavior.

- [ ] Lock exact 24 check names from the pinned counterpart with only `v120_preservation` renamed `v121_preservation`. Add independent controls for malformed JSON/missing context exceptions vs parsed corruption FAIL, missing/extra files, manifest/SHA/ArtifactRef/rollback/image mismatch, SQLite unreadability/integrity/FK/schema/ledger/count/digest mismatch. Assert required failed checks, final FAIL and unchanged artifact bytes; never repair in verification.
- [ ] Test generation 2 parent exactness: verify synthetic generation 1; preflight B against that verification request; assert report/approval parent equals generation 1 candidate digest, not genesis. Reordered A/B prefix, B genesis preflight reused after A, old-version parent, duplicate against A, stale package bytes and forged counts must block. Byte fingerprints of generation 1 and all formal roots remain unchanged after each failed append.
- [ ] Test no-replace output, symlink/formal/source/parent overlap and publication fault cleanup of only owned temp files. Run two independent roots and compare every candidate artifact byte, candidate/manifest/digest/SHA list and relative ArtifactRef hash/size/kind; absolute ArtifactRef paths appropriately differ. Declarative rollback cannot delete anything.
- [ ] **Step 4A — first-generation RED, then minimum first-generation GREEN:** run the explicitly selected first-generation writer/verifier/genesis-binding cases from `tests.integration.test_v122_candidate` and record valid missing-behavior RED. Only then implement the fixed DDL/profile, single-batch writer and independent verifier needed for those cases. Preserve baseline table/schema literals; no broad historical replacement. Build from the formal baseline, independently verify private output, atomic no-replace publish. Run these cases to GREEN. Non-genesis preflight and multi-batch writer/verifier extension remain unimplemented; do not port them while completing 4A.
- [ ] **Step 4B1 — parent-preflight RED then GREEN:** use the working 4A builder/verifier to create and verify synthetic generation 1. Run parent-preflight cases directly: exact parent binding, duplicate/collision against A, wrong parent and parent immutability. They must pass the first-generation prerequisite and fail at missing parent-preflight behavior. Record counts and failure sites; only then implement verified-parent indexing/report/digest in preflight and run those cases to GREEN. Do not extend the writer/verifier to multiple batches yet.
- [ ] **Step 4B2 — multi-batch/stale-parent RED then GREEN:** using 4B1 GREEN, produce a valid B preflight/approval bound to the verified generation 1 digest. Run multi-batch writer/verifier and stale/reordered-prefix controls; assert valid prerequisites before invoking the operation under test. Record actual writer/verifier behavior RED, not a failure of `_approved` or first-generation creation. Only after this valid RED may production gain full-prefix writer rebuild and multi-batch verifier closure. Import/setup errors never qualify. Run 4A, 4B1 and 4B2 together to GREEN and confirm parent bytes unchanged.
- [ ] Run all candidate and preflight tests plus Tasks 1–3 and unchanged V120/V121 candidate tests. Confirm every downstream case reached its intended assertion and 4A/4B1/4B2 signals are recorded separately. Record mutation-test evidence for genesis trust boundaries and commit `feat: add verified V1.22 candidate accumulation` only after focused regression and scoped review.

### Task 5: Historical replay, complete gates and independent review

**Files:** `tests/regression/test_v122_historical_replay.py`, `docs/reports/V122_CANDIDATE_AUTHORITY_VERIFICATION.md`, `PROJECT_STATE.md`; in-scope remediation only in the owning task files.

**Interfaces:** Read-only historical candidate/formal verifiers; no new production API. The report is evidence, not a second contract or import approval.

- [ ] Add replay assertions for byte-identical V1.18/497, V1.19/502, V1.20/543, V1.21/591; exact 591-row ordered baseline preservation, published V1.21 required and releases/V1.22 absent. Record old V119/V120/V121 manifest/preflight/approval/candidate identities and require exact replay. Existing historical test helpers use `materialize=False`; do not rebuild real historical candidates just to make a test pass.

```python
def test_v121_is_frozen_and_v122_is_not_published(self):
    import hashlib, sqlite3
    path = ROOT / "releases/V1.21/Joy_M2_Complete_Question_DB_V1_21.sqlite3"
    self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),
        "93b7676f83659c2ceaa9de978ba998ce9347a45b995bb5446ed382251f96737a")
    with sqlite3.connect(path.as_uri() + "?mode=ro&immutable=1", uri=True) as db:
        self.assertEqual(db.execute(
            "SELECT COUNT(*) FROM formal_complete_questions_v121").fetchone(), (591,))
    self.assertFalse((ROOT / "releases/V1.22").exists())
```

`ROOT = Path(__file__).resolve().parents[2]` in this test. Historical preservation assertions may be GREEN immediately: they lock unchanged behavior, not justify new production before RED.

- [ ] Run all maintained test modules with explicit zero-skip/zero-expectedFailure assertion, not a fixed historic total. The repository uses namespace test packages, so enumerate module names instead of `unittest.discover` requiring `tests/__init__.py`. Exclude only the separately attributed legacy behavior module, never a failing maintained test:

```bash
"$JOY_PY" - <<'PY'
from pathlib import Path
import unittest
legacy = Path('tests/regression/test_task8b_legacy_pipeline_behavior.py')
modules = [str(p.with_suffix('')).replace('/', '.')
           for p in sorted(Path('tests').rglob('test_*.py')) if p != legacy]
assert modules
suite = unittest.defaultTestLoader.loadTestsFromNames(modules)
result = unittest.TextTestRunner(verbosity=1).run(suite)
assert result.wasSuccessful()
assert not result.skipped and not result.expectedFailures and not result.unexpectedSuccesses
print('maintained count:', result.testsRun)
PY
"$JOY_PY" -m unittest -v tests.integration.test_ingest_preflight
"$JOY_PY" -m unittest -v tests.unit.test_hkdse_pdf_models tests.unit.test_hkdse_pdf_adapter tests.integration.test_hkdse_pdf_adapter
"$JOY_PY" -m unittest -v tests.regression.test_task7_project_initialization
"$JOY_PY" releases/V1.18/verify_task6_release.py releases/V1.18
```

Require Task 9A 41/41, Task 10B 50/50, Task 7 7/7. The new focused total must be reported accurately. Run the existing read-only formal `verify_v119_promotion`, `verify_v120_promotion` and `verify_v121_promotion` entry points with their frozen verification requests (18/21/21 checks respectively); reuse current historical replay's request reconstruction and exact approved artifacts, never a `build_*_promotion` or `publish_*_release` API. Record commands and actual output in the report. Any legacy attribution run must retain its existing categories, not be misrepresented as maintained GREEN.
- [ ] Request independent implementation review of the complete scoped diff against Design and Plan. Explicit focus: artifact-vs-digest distinction, independent genesis reconstruction, valid RED evidence, 591-row dedup, immutable 2019 source, exact API prefix, stale-parent/preservation, no real writer. Zero Critical/Important required. New findings get targeted RED → minimal fix → GREEN → re-review; no new scope by inference.
- [ ] Re-run required gates after remediation; inspect `git diff --check`, exact changed paths, original 2019 approval/evidence hashes, four formal SQLite hashes/counts and absence of real V1.22 output. Update report with RED/GREEN counts, all 24 verifier obligations, review provenance, limitations and frozen proofs; synchronize state. Explicitly stage only approved paths and commit `test: verify V1.22 candidate authority and historical replay`. Ordinary upstream push follows policy; no force/merge/rebase/squash/tag/PR.

### Task 6: Exact 2019 canonical package and read-only preflight; stop at human gate

**Files:** ignored output only `data/staging/task12-v122-hkdse-2019/**`; optional orchestration scratch `tmp/pdfs/task12-v122-hkdse-2019/**`; checkpoint evidence in the approved report and `PROJECT_STATE.md`. No operational artifact in Git.

**Interfaces:** Approved carrier from `approve_hkdse_pdf_transcription`, the Task 2 bridge and Task 3–4 preflight. Never `build_v122_candidate` for this real batch without a subsequent exact user import statement.

- [ ] After engineering is committed and independent review clean, read the original `transcription-human-resolution-000002` proposal/evidence/approval using existing Task 10B loaders; reconstruct the exact recorded approval and verified carrier. Assert batch/digest from Global Constraints, 12 whole records/100 marks, Q10(d) exact note, Q12 exact source typo, original file hashes unchanged. No OCR or source edits.
- [ ] Confirm no accepted V1.22 generation exists before selecting `parent_candidate=None`. If one now exists, do not run the first-generation path; recover and verify its exact current V1.22 authority under Design §5 before resuming. Never silently reuse genesis to override an accepted generation.
- [ ] Generate canonical packages in two fresh, non-overlapping ignored staging roots via the maintained bridge. Compare relative file sets and bytes. Run preflight against exact formal V1.21 and no parent artifact; compare results and require both report digests bind literal genesis. Never hard-code all twelve as new or projected count 603.
- [ ] Emit an approval report with batch/transcription/source/canonical/preflight/parent identities, status, before/detected/new/duplicate/rejected/ambiguous/adaptations, missing answers/explanations, primary types/tags/difficulty summaries, exact issues, image evidence and projected count. Recheck formal SHA/counts and unchanged source approvals. Record proposed staging candidate path only; do not create it.
- [ ] If blocked, report actual blockers without adjusting records/counts. If READY, stop at `USER DECISION REQUIRED — REAL BATCH IMPORT` with the **actual** preflight digest and this exact parent syntax:

```text
USER APPROVED IMPORT BATCH JOY-M2-HKDSE-2019-PP-MS <actual_preflight_sha256> V1.22 PARENT 7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7
```

The digest token is runtime output, not a pre-authorized value. No real approval construction, real candidate write, releases/V1.22, promotion or 2020 ingestion is part of this pre-approval run.

## Plan review checklist and handoff

- [x] Map Design §§1–3/9 to Global Constraints/Task 6; §4 to Task 1; §5 to Tasks 1/3/4; §6 to Tasks 1/2; §7 to Tasks 3/4; §8 to Task 4; §10 to the exact file map; §11 to Tasks 1–5.
- [x] Verify exact signatures/types and no undeclared public API; 13 carriers + 5 functions; no behavior in API scaffolds; no parent artifact/digest ambiguity.
- [x] Verify each Review Focus condition has explicit tests, all dependent REDs have importable prerequisites, and no production-first path remains.
- [x] Search for unresolved placeholders and unauthorized file/behavior expansion; check two real root comparison does not fabricate approval.
- [x] Run `git diff --check` plus new-file whitespace validation; self-review and independent technical review against committed Design. Commit scope for this planning checkpoint is only Plan/current state.
- [ ] Human Plan review/execution handoff before implementation; do not request another Design approval.

Review record (2026-09-21): read-only reviewer `v122_plan_review` identified one
Important dependency-sequencing ambiguity. It was closed by explicit 4A → 4B1 →
4B2 gates and a prohibition on counting unreached assertions as RED. Final
incremental verdict: Ready for Plan commit; Critical 0 / Important 0 / Minor 0.
This is Plan review, not implementation verification or real-import approval.
