# V1.23 Promotion Readiness Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans
> for the recommended Native / Inline execution, after human Plan approval and
> execution authorization. Use a separate reviewer for independent review.
> Checkboxes are implementation steps, not authority to start them now.

**Status:** WRITTEN PLAN — PENDING HUMAN REVIEW. Implementation NOT STARTED.
Prepared: 2026-10-19 (Asia/Shanghai); filename follows the approved Design.

**Goal:** Produce two byte-identical, independently verified non-formal V1.23
release-equivalent trees containing 639 preserved records plus 38 approved
source records, then stop for exact release-digest approval without publishing.

**Architecture:** Three fixed-version promotion sibling modules, following the
pinned V1.22 counterpart with only the approved role-specific deltas. Independent
verifier and test oracle reconstruct their own DDL, projections and identities;
neither derives correctness from the new builder. No generic version engine.

**Tech Stack:** Existing Python standard library, unittest, SQLite, SHA-256,
canonical JSON and existing atomic no-replace primitive; no new dependencies.

**Spec:** `docs/superpowers/specs/2026-10-14-v123-promotion-readiness-design.md`.
Human-approved source: commit `1c66a8e9daaaa991fc72b3ca891d87251051831b`,
SHA-256 `dac063c914b2a7003295d1306d39b0390329f408bace59c9f14d0e943e943541`.
The subsequent Design header records approval only; sections 1–10 are unchanged.

## Global Constraints

- Formal baseline stays V1.22 / 639; selected V1.23 generation is 000003 only.
  677 is a record count, not 677 distinct original questions. Exclude 2024.
- No actual publication, real candidate writer, transcription, source mutation,
  default-query/pointer change, scheduler change, new adapter, historical cleanup,
  V1.24 or backup-service development. Do not create real `releases/V1.23/`.
- No historical production/API/digest/approval change or global version replace.
  Preserve all historical tables and metadata except Design §6's output-only delta.
- Preserve dirty `AGENTS.md` bytes/index state; never stage, commit, stash or reset it.
- Keep the existing `task8b/pipeline-migration` worktree. No force/rebase/amend,
  squash, merge or new branch/worktree. Ordinary explicit task commit/push only.
- All behavior must have valid assertion RED before its minimal GREEN. Import,
  syntax, fixture/setup and unavailable dependency errors never count as RED.
- Real release/SQLite/semantic/manifest identities do not yet exist. Compute them
  only after authorized real dry-runs; never predict them or create real approval.
- A busy existing process lock delays input recovery; never invoke `run_cycle`,
  pending-intent recovery, or a writer to obtain read-only promotion inputs.

## Review Focus

1. A self-consistent forged baseline schema/hash envelope must fail (Tasks 2–3).
2. Inherited historical candidate rows must not leak into formal counts (Tasks 3–4).
3. Malformed JSON versus parsed-invalid values, including bool-as-int and missing
   files, must preserve the exception/structured-FAIL boundary (Task 3).
4. Symlink/alias/overlap paths and rename races must never overwrite or clean an
   unowned/changed tree (Tasks 4–5).
5. Approval-like generated metadata must not authorize real publication; inherited
   source/PDF references must not be relabelled or materialized as images (Tasks 4–5).

## Pinned counterpart and closed file map

Read at commit `716ab3ae1536d788be0bd2107a4e7aed8b64ac19`:
`src/joy_m2/ingest/v122_promotion_models.py`, `v122_promotion.py`,
`v122_promotion_verification.py`, and
`docs/superpowers/specs/2026-09-27-v122-promotion-readiness-design.md`.
Detailed shape reference: `2026-09-19-v121-formal-promotion-readiness-design.md`
§§5–12 in the same specs directory. Apply only approved Design §§2–6 deltas.
The V1.22 tests are pattern references, not an oracle obtained from production.

NEW production:

- `src/joy_m2/ingest/v123_promotion_models.py`: exact six immutable public carriers.
- `src/joy_m2/ingest/v123_promotion.py`: deterministic builder and gated publisher.
- `src/joy_m2/ingest/v123_promotion_verification.py`: independent read-only verifier.

MODIFIED production: `src/joy_m2/ingest/__init__.py`, append nine exports only.

NEW tests:

- `tests/unit/test_v123_promotion_models.py`: fields/types/frozen/API contract.
- `tests/unit/test_v123_promotion_primitives.py`: literal DDL/identity oracles.
- `tests/integration/test_v123_promotion.py`: independent fixture, verifier,
  builder, isolated publication and failure-boundary controls; private helpers
  stay here rather than creating another fixture/helper module.

MODIFIED tests, exact historical prefix/suffix alignment only:

- `tests/unit/test_v119_writer_models.py`
- `tests/unit/test_v119_promotion_models.py`
- `tests/unit/test_v121_promotion_models.py`
- `tests/unit/test_v122_models.py`
- `tests/unit/test_v122_promotion_models.py`
- `tests/unit/test_v123_models.py`
- `tests/regression/test_v119_historical_replay.py`

Additionally `tests/regression/test_v123_historical_replay.py`: replace only its
obsolete no-promotion-export assertion and perpetual real-target absence with
the exact appended surface and Design §8 lifecycle gate/controls. Preserve all
historical hashes, source approval checks and candidate-writer formal rejection.

DOC scope: approved Design header, this Plan, `PROJECT_STATE.md`, and later
`docs/reports/V123_PROMOTION_READINESS.md` (implementation evidence, not created
as a false completion report at this Plan checkpoint).
Ignored execution artifacts only: `data/staging/task13-v123-promotion-readiness/**`
and `tmp/pdfs/task13-v123-promotion-readiness/**`; existing backup CLI may create
an explicit new archive in `dist/backups/` and isolated restore below `tmp/`.
No other tracked files, historical production edits or new backup tooling.

## Fixed input register and protected roots

All relative paths resolve under the existing worktree:
`/Users/miaohuanjoy/Desktop/joy-m2-ai-database-current/.worktrees/task8b-pipeline-migration`.
Design §2 supplies the exact SHA/size oracle; freshly matched at Plan preparation:

| File | Bytes | SHA-256 |
|---|---:|---|
| `releases/V1.22/Joy_M2_Complete_Question_DB_V1_22.sqlite3` | 10510336 | `a474846a5b1d10a0fe48a259522fbb327747319f4a114452bf9f294405d8d9e0` |
| `releases/V1.22/manifest.json` | 7915 | `441e00ac1536b959b40b6177bd17a6f14632a287f85145e202a51bcf137ddc8b` |
| selected candidate `Joy_M2_V1.23_candidate.sqlite3` | 10764288 | `b7e2247e004cc4c91c339693de4f106edef11bb7067e34b52887547a8006cb01` |
| selected `candidate_manifest.json` | 5664 | `febe70a572b82783bf6199679bf1a2024294d98b44b4fbe047a2349a3830a076` |

Baseline release digest:
`89a592abf52507cc0325f9c6f30ee2c74d4ec55fdcef988fdae6cb12f5a3073b`.
Selected candidate digest:
`c5c51df58d64349d58bd71469fe67a72cced56e77369126d6fec66bb2fcc955a`.

Receipt paths in order:

1. `data/staging/task13-v123-hkdse-2023/REAL_BATCH_IMPORT_RECEIPT.json`
2. `data/staging/task13-v123-hkdse-2025/REAL_BATCH_IMPORT_RECEIPT.json`
3. `data/staging/auto-ingestion/receipts/000003.json`

Candidate roots in that order:

1. `data/staging/task13-v123-hkdse-2023/candidate-generation-000001`
2. `data/staging/task13-v123-hkdse-2025/candidate-generation-000002`
3. `data/staging/auto-ingestion/candidates/8531b270990b350afbbcdc16eff2fddf63a1f33d7a451402199344eae2447a20`

Canonical package roots in that order:

1. `data/staging/task13-v123-hkdse-2023/preflight-20261012-000001/canonical-a`
2. `data/staging/task13-v123-hkdse-2025/preflight-20261013-000001/canonical-a`
3. `data/staging/auto-ingestion/packages/2038db4f3486aae8a92ec0e38acc338f9c0c2782a5b245301cca85792a29928f`

Protect all files in formal `releases/V1.18` through `V1.22`, all candidate roots
and packages above, and source/approval roots `data/staging/task10b-hkdse-2023`,
`data/staging/task10b-hkdse-2024`, `data/staging/task10b-hkdse-2025`, and
`data/staging/oxford-c1-review-20261014`. The following additional actual protected
roots were enumerated from local candidate-manifest paths, the two historical
receipt inventories and existing archive manifest metadata at Plan preparation:

```text
data/staging/task9c-v119-candidate
data/staging/task9c-v119-real-0918-interval-candidate
data/staging/task10a-v120-real-candidate-000001-hkdse-2012
data/staging/task10a-v120-real-candidate-000002-hkdse-2013
data/staging/task10a-v120-real-candidate-000003-hkdse-2014
data/staging/task11-v121-hkdse-2015
data/staging/task11-v121-hkdse-2016
data/staging/task11-v121-hkdse-2017
data/staging/task11-v121-hkdse-2018
data/staging/task12-v122-hkdse-2019
data/staging/task12-v122-hkdse-2020
data/staging/task12-v122-hkdse-2021
data/staging/task12-v122-hkdse-2022
data/staging/task13-v123-hkdse-2023
data/staging/task13-v123-hkdse-2025
data/staging/task10b-hkdse-2019
data/staging/task10b-hkdse-2020
data/staging/task10b-hkdse-2021
data/staging/task10b-hkdse-2022
data/staging/auto-ingestion/candidates
data/staging/auto-ingestion/packages
data/staging/auto-ingestion/receipts
```

The external source files actually referenced by those inventories are:

```text
/Users/miaohuanjoy/Desktop/M2/M2 Past Paper/M2_2021-pp.pdf
/Users/miaohuanjoy/Desktop/M2/M2 Past Paper/M2_2022-pp.pdf
/Users/miaohuanjoy/Desktop/M2/M2 Past Paper/M2_2023-pp.pdf
/Users/miaohuanjoy/Desktop/M2/M2 Past Paper/M2_2024-pp.pdf
/Users/miaohuanjoy/Desktop/M2/M2 Past Paper/M2_2025-pp.pdf
/Users/miaohuanjoy/Desktop/M2/M2 Past Paper/M2-ms/M2_2021-ms.pdf
/Users/miaohuanjoy/Desktop/M2/M2 Past Paper/M2-ms/M2_2022-ms.pdf
/Users/miaohuanjoy/Desktop/M2/M2 Past Paper/M2-ms/M2_2023-ms.pdf
/Users/miaohuanjoy/Desktop/M2/M2 Past Paper/M2-ms/M2_2024-ms.pdf
/Users/miaohuanjoy/Desktop/M2/M2 Past Paper/M2-ms/M2_2025-ms.pdf
/Users/miaohuanjoy/Desktop/AI做题库相关原材料/补课不同专题材料/DSE2025-26_M2_Mockpaper_C_set11764492491.pdf
/Users/miaohuanjoy/Desktop/AI做题库相关原材料/补课不同专题材料/DSE2025-26_M2_Mockpaper_C_set1_sol1764492524.pdf
/Users/miaohuanjoy/Desktop/joy-m2-ai-database-current/data/staging/joy_m2_hkdse_2021_pp_ms_staging.json
/Users/miaohuanjoy/Desktop/joy-m2-ai-database-current/data/staging/joy_m2_hkdse_2022_pp_ms_staging.json
/Users/miaohuanjoy/Desktop/joy-m2-ai-database-current/data/staging/joy_m2_hkdse_2023_pp_ms_staging.json
/Users/miaohuanjoy/Desktop/joy-m2-ai-database-current/data/staging/joy_m2_hkdse_2024_pp_ms_staging.json
/Users/miaohuanjoy/Desktop/joy-m2-ai-database-current/data/staging/joy_m2_hkdse_2025_pp_ms_staging.json
/Users/miaohuanjoy/Desktop/joy-m2-ai-database-current/data/staging/joy_m2_mock_2025_26_c_set1_staging.json
```

These are protection boundaries, not new ingestion or scanning authorizations.
At execution recheck resolved paths and snapshot member sizes/hashes without
changing this selected input. Keep other source/approval files identified by
the exact package manifests protected too. Reject output equal to, above or
below protected inputs; do not scan unrelated Desktop directories.
Runtime state DB/last_run are not
immutable inputs: the scheduled task may legitimately update them.

The selected candidate has ten files: SQLite, manifest, `SHA256SUMS`, rollback,
and approval/preflight JSON pairs below `authority/batches/000001/...2023...`,
`000002/...2025...`, `000003/...Oxford...`. Read the six exact relative paths,
SHA and sizes from `batch_authority_artifacts`, verify actual bytes and retain
their semantic order; Design §3 pins ledger/preflight/parent/canonical identities.
Do not replace those with file-discovery order or generated approvals.

During Plan preparation all three prefix candidates freshly passed 24/24 checks;
six authority-file SHA/size pairs matched, no later receipt was present, and
real `releases/V1.23/` was absent. These are input checks, not promotion tests.

## Commands and RED evidence convention

Use this session environment for every execution/test command below:

```bash
export PYTHONDONTWRITEBYTECODE=1
export PYTHONPATH=src:.
JOY_PY=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
```

Write logs only in the approved ignored runtime roots. For each group record
test IDs, exit status, collected count, assertion failure, zero setup/import
errors, and later GREEN. Missing API uses `getattr`/`callable` assertions, not
top-level import of absent names. Behavior scaffolds return a sentinel `None`
so the first assertion can fail on missing behavior; check type/status before
dereferencing it. Negative exception tests against no-op scaffolds fail with
`assertRaises` unmet, not an uncaught stub exception. Do not run future groups
whose fixtures or dependencies have not yet been established.

### Task 1: Exact API/model RED -> minimal model/scaffold GREEN

**Files:** new models test, three new production modules, ingest exports and
the seven exact-prefix test paths above. No behavior implementation.
**Interfaces:** six Design §5 carriers with exact counterpart fields/order,
no defaults, frozen and exact nested types. Public functions:
`build_v123_promotion(request: V123PromotionBuildRequest, config: PipelineConfig)
-> V123PromotionArtifacts`,
`verify_v123_promotion(request: V123PromotionVerificationRequest, config: PipelineConfig)
-> VerificationReport`,
`publish_v123_release(request: V123PublicationRequest, config: PipelineConfig)
-> V123PromotionArtifacts`.

- [ ] Recover Git/Design/Plan authorization; snapshot AGENTS bytes/index and the
  immutable input inventory above under the existing `cycle.lock`. A pending
  intent is reported, never recovered by promotion work. Inspect later receipts
  separately; reconstruct only the fixed first three typed approved batches with
  `load_v123_import_manifest`, `preflight_v123_import`, received approval fields
  and `verify_v123_candidate`. Do not use `V123Operations` construction because
  it can recover pending writes. Require exact Design SHA/size/chain and 24 PASS.
- [ ] Add `V123PromotionModelTests.test_exact_append_only_surface` using dynamic
  lookups: whole existing `__all__` prefix unchanged and exact nine-name suffix
  from Design §5. Add signature assertions after callable assertions.
- [ ] Run `"$JOY_PY" -B -m unittest -v tests.unit.test_v123_promotion_models`;
  require missing API assertion FAIL, not ERROR. Then add field/order/type/frozen,
  all 14 literal values, wrong historical carrier, bool user_version, digest,
  exact approval string, ArtifactRef kind/order and defensive tuple-copy tests.
  Establish each remaining model behavior RED with importable placeholders.
- [ ] Implement only model validation and callable sentinels. Exact carrier
  fields mirror pinned `v122_promotion_models.py`; candidate types become exact
  V123 types. No build, verify or publish logic. Append the approved nine exports.
- [ ] Align only listed historical export expectations (whole old prefix intact).
  Rerun new model tests and the seven listed historical modules with unittest;
  require PASS, zero skip/expectedFailure. Commit explicit changed paths with
  `feat: add V1.23 promotion contracts and scaffolds` after diff/scope checks.

### Task 2: Primitive RED/GREEN and independent literal oracles

**Files:** new primitives tests and the three new production modules only.
**Interfaces:** private counterpart `_canonical_json_file_bytes(value: object)
-> bytes`, `_promotion_identity(payload: dict[str, object]) -> str`,
`_sqlite_semantic_payload(path: Path, formal_view: str) -> dict[str, object]`,
builder/verifier own DDL and identity constants. No additional public exports.

- [ ] Add `V123PromotionPrimitiveTests` cases for exact constants/check inventory,
  DDL/FK/order bounds, canonical JSON literal bytes and hash, root-independent
  semantic payload, and `test_baseline_schema_literal_oracle`.
  Assert `task12-v122-formal-v1` in BOTH baseline projections, independently of
  production constants; reject `task11-v121-formal-v1` and `task13-v123-formal-v1`.
  New schema is task13; inherited task9–12 names remain untouched. Independently
  author expected literal bytes/digests in tests with standard hashlib/json.
- [ ] Run `"$JOY_PY" -B -m unittest -v tests.unit.test_v123_promotion_primitives`;
  dynamic private-helper existence/behavior assertions must produce valid RED.
- [ ] Implement only counterpart pure primitives and literal DDL/constants,
  applying Design §§4–7 role deltas. Builder/verifier must each own their baseline
  projection and DDL; verifier imports no builder helper, constant or projection.
- [ ] Rerun primitives plus models to GREEN. Inspect literal assertions and
  inherited-name preservation; commit exact files: `feat: add V1.23 promotion primitives`.

### Task 3: Independently constructed fixture -> formal verifier RED/GREEN

**Files:** `tests/integration/test_v123_promotion.py`, new verifier only.
**Interfaces:** private test helper `selected_candidate(root: Path)
-> V123CandidateVerificationRequest` reconstructs ONLY the fixed receipt prefix;
`fixture_release(output: Path, candidate: V123CandidateVerificationRequest,
contract: V123PromotionContract) -> Path` independently serializes test artifacts.
Public output is `verify_v123_promotion(...) -> VerificationReport`.

- [ ] Implement test-only helpers using literal Design/counterpart shapes, raw
  candidate bytes and test-owned SQL/JSON/hash code. Never call/import new builder
  helpers to populate fixture or rebind corrupted fixture hashes. Assert fixture
  integrity, 639 preserved rows, exact 38 projected rows and four-file closure
  before using it as verifier input. A fixture setup failure is not behavior RED.
- [ ] Add `V123IndependentVerifierTests.test_independent_valid_fixture_reports_21_pass`:
  sentinel must fail the report-type assertion. Pin exact ordered checks:
  `release_directory, promotion_contract, candidate_verification, candidate_binding,
  manifest_contract, filesystem_closure, sha256sums_closure, artifact_references,
  rollback_contract, sqlite_readability, sqlite_integrity, sqlite_foreign_keys,
  sqlite_schema, v122_preservation, batch_ledger_closure, promotion_projection,
  formal_query, count_closure, provenance_closure, deterministic_identity,
  publication_boundary`.
- [ ] Add focused corruption tests: missing/extra keys/files; wrong types and
  bool-as-int; schema/FK/order/count/status corruption; changed baseline row;
  Oxford source/answer mutation; reordered ledger; wrong parent/approval; bad
  candidate SHA/size; unreadable SQLite; hash-consistent forged schema/projection.
  Recompute outer hashes in the test-owned oracle so semantic checks, not only
  checksum mismatch, reject forgeries. Pin specific failing check names and
  unchanged input fingerprints, not merely `status != PASS`.
- [ ] Add malformed JSON -> `InputFormatError`; parsed-invalid manifest ->
  21-check structured FAIL; invalid typed request/config -> `PipelineError`;
  missing verification root -> `InputMissingError`. Retain counterpart boundaries
  for missing/corrupt candidate artifacts; no raw sqlite/type exception leakage.
- [ ] Run `"$JOY_PY" -B -m unittest -v tests.integration.test_v123_promotion.V123IndependentVerifierTests`;
  establish valid assertion RED, then implement independent verifier. It uses
  `Path.as_uri()` and read-only connections, no repairs, and requires the exact
  24-check candidate prerequisite and Design input envelope.
- [ ] Rerun verifier, primitives and model groups to GREEN; inspect that verifier
  depends only on public carriers, candidate verifier and version-neutral code.
  Commit: `feat: verify V1.23 formal projection independently`.

### Task 4: Builder RED/GREEN, projection and determinism

**Files:** new builder and integration test only.
**Interfaces:** GREEN independent verifier from Task 3; produces
`V123PromotionArtifacts` using Design §§6–7 exact metadata/artifact projection.

- [ ] Add `V123PromotionBuildTests` using the verified fixed candidate:
  `test_exact_639_plus_38_projection`, `test_oxford_publisher_solutions_preserved`,
  `test_pdf_locators_not_fake_image_files`, `test_two_builds_byte_identical`,
  `test_wrong_envelope_and_protected_overlap_rejected`, and ownership/race tests.
  Assert record IDs/order 1–677, all published/selectable1, batches12/13/13,
  field-by-field baseline639 and new38 values with ONLY approved projection
  renames/status changes; inherited candidate tables stay identical, not unioned.
- [ ] Assert exact metadata delta from Design §6 (old task12 metadata unchanged),
  user_version123, task13 ledger FK, source-provided Oxford publisher identity,
  existing empty explanations unchanged, PDF/page/region evidence unchanged,
  images empty. Only four exact files; sums bind other three, no self-entry.
- [ ] Run `"$JOY_PY" -B -m unittest -v tests.integration.test_v123_promotion.V123PromotionBuildTests`;
  require sentinel/absent output assertion RED with verifier fixture already GREEN.
- [ ] Implement builder: validate typed exact envelope and protected roots,
  private staging copy, one transaction, exact projection/metadata, canonical
  artifacts, independent verification before and after atomic no-replace rename.
  General output must be a new strict staging descendant without symlink/alias
  or bidirectional overlap with any enumerated input, formal or source root.
- [ ] Exercise faults before/after rename, existing output, identical competing
  output, and altered new tree; remove only owned unchanged output, preserve
  competitor/changed evidence. Rerun Tasks 1–4 groups to GREEN and verify two
  isolated build trees byte-for-byte (including SQLite), relative refs/hash/size,
  semantic SHA/release digest. Commit: `feat: build deterministic V1.23 promotion staging`.

### Task 5: Publication/lifecycle RED/GREEN in isolated roots only

**Files:** new builder, integration tests, `test_v123_historical_replay.py` only.
**Interfaces:** GREEN builder/verifier -> `publish_v123_release(...)`.
Real literal `APPROVED_V123_RELEASE_DIGEST = None` stays None in this task.

- [ ] Use test-owned temporary repository roots with verified copied input and
  valid built dry-run. Add `V123PublicationBoundaryTests` for absent/wrong digest,
  wrong historical approval type/version, exact isolated approval, changed private
  copy, symlink/alias source/release root, existing target, and no-replace race.
  Test-only approvals apply ONLY to isolated roots, never the real repository.
- [ ] Run `"$JOY_PY" -B -m unittest -v tests.integration.test_v123_promotion.V123PublicationBoundaryTests`;
  confirm expected output or rejection assertions fail against publish sentinel.
  Missing builder artifact is not publication RED.
- [ ] Implement counterpart exact approval binding, independent source/private
  byte identity checks, target derived only by `config.new_formal_target("V1.23")`,
  atomic no-replace and final independent verification. Fault tests cover unchanged
  owned cleanup versus changed output retained, including post-publication failure.
  Verify rollback action `remove_release_tree_if_release_digest_matches`, exact
  four-file closure and protected V1.22 identity; never execute live rollback.
- [ ] In historical replay add explicit lifecycle helper/controls: None -> real
  absence; exact approved literal -> present independently verified matching output;
  malformed/wrong digest or missing approved output -> failure. Isolated tests
  exercise both phases. Manifest/template/environment cannot supply approval.
  Replace only the obsolete export absence assertion and last real absence
  assumption; preserve synthetic candidate-writer formal rejection and all source
  checks. Confirm valid RED for each lifecycle negative control before GREEN.
- [ ] Rerun full focused tests and historical replay. Require zero skip/errors/
  expectedFailure, real target absent, AGENTS unchanged. Commit:
  `feat: gate V1.23 publication with exact lifecycle authority`.

### Task 6: Two real non-formal dry-runs and complete regression

**Files:** approved ignored runtime evidence only; no new production scope.
**Interfaces:** selected request from Task 3 -> two `build_v123_promotion` calls
and independent `verify_v123_promotion` calls. Never call real publisher.

- [ ] Reverify fixed input/approval chain and protected snapshots under the existing
  read lock protocol. Any later operational generation is reported separately.
  Reuse a previously completed exact verified dry-run rather than overwriting it;
  otherwise choose two new distinct roots below
  `data/staging/task13-v123-promotion-readiness/` (e.g. `dry-run-a-000001`,
  `dry-run-b-000001`). Never create any formal target to test readiness.
- [ ] Build twice independently, verifier 21/21 each, compare bytes of all four
  files, relative artifact path/kind/hash/size, semantic/release identities. Query
  677 unique formal IDs and all three batches with read-only URI connections;
  Oxford source `OXFORD-M2-2025-26-C-SET1` has IDs Q01–Q13 and publisher solutions
  equal to candidate values. Compare all639/all38 fields, not sample-only checks.
- [ ] Run focused tests, then serial current maintained discovery below. Do not
  use an old test count as success criterion or silently skip missing fixtures.

```bash
"$JOY_PY" -B -m unittest -v tests.unit.test_v123_promotion_models tests.unit.test_v123_promotion_primitives tests.integration.test_v123_promotion
"$JOY_PY" -B - <<'PY'
import unittest
from pathlib import Path
def leaves(suite):
    for item in suite:
        if isinstance(item, unittest.TestSuite):
            yield from leaves(item)
        else:
            yield item
excluded = 'tests.regression.test_task8b_legacy_pipeline_behavior'
modules = ['.'.join(p.with_suffix('').parts) for p in sorted(Path('tests').rglob('test_*.py'))]
modules = [name for name in modules if name != excluded]
loader = unittest.TestLoader()
tests = list(leaves(loader.loadTestsFromNames(modules)))
assert not loader.errors, loader.errors
result = unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(tests))
assert result.testsRun == len(tests) and len(tests) > 0
assert result.wasSuccessful() and not result.skipped and not result.expectedFailures
PY
"$JOY_PY" -B -m unittest -v tests.regression.test_v123_historical_replay
"$JOY_PY" -B releases/V1.18/verify_task6_release.py releases/V1.18
git diff --check
```

- [ ] Record actual discovery/failure/error/skip/expectedFailure counts. Historical
  replay executes existing formal verifiers (V1.19–V1.22) and candidate replays;
  V1.18 validator separately. Run current selected candidate verifier24/24 anew
  and compare all frozen/source/approval/candidate snapshots. Known separate
  legacy attribution9PASS/2FAIL is not a waiver for any new maintained failure.
  Explicit module discovery is intentional: the current tests directories have
  no `__init__.py`; default recursive unittest discovery can omit them. Do not
  add package markers or change tests merely to change collection behavior.

### Task 7: Independent implementation review, backup and final human gate

**Files:** `docs/reports/V123_PROMOTION_READINESS.md`, `PROJECT_STATE.md`, in-scope
repair files only; existing ignored backup/evidence destinations.
**Interfaces:** actual dry-run identities -> reviewed readiness report, NOT approval.

- [ ] A fresh reviewer, separate from implementer, reviews all implementation and
  tests against approved Design/Plan; check oracle independence, false-PASS forgery,
  preserved fields/provenance, path/cleanup ownership and lifecycle boundaries.
  Critical/Important must both be0. Ordinary in-scope repairs require regression
  RED/GREEN and re-review; rerun affected and full gates after final code changes.
- [ ] Verify existing local archive identity/coverage from Design §10. Use only
  existing `scripts/backup_ingestion_checkpoint.py` and its explicit file-list
  interface to checkpoint required immutable inputs and verified dry-run evidence
  into a NEW non-overwriting local archive, verify manifest/member bytes and
  isolated recovery. Inspect its existing `--help` before invoking; never create
  new tooling or a live restore. Do not copy live state SQLite with sidecars as
  an inconsistent snapshot. No off-device-backup claim and no full restore at
  this earlier docs-only Plan checkpoint.
- [ ] Synchronize report/state with actual hashes, four-file closure, counts,
  ledger, baseline preservation, tests/review/backup evidence, rollback limits
  and no default-pointer change. Source-provided Oxford answers are publisher
  solutions, not HKEAA MS; PDF locators are not standalone image files.
- [ ] Explicitly stage only reviewed task files. Commit ordinary engineering/docs
  checkpoint; inspect names, `git diff-tree --check HEAD^ HEAD`, `git diff --check`
  and untouched AGENTS hash/index. Ordinary push existing branch, compare actual
  remote HEAD and ahead/behind. Network failure is reported, never force/rewrite
  history, reimport or rebuild merely to retry backup.
- [ ] Confirm real `releases/V1.23/` absent and formal querying still V1.22/639.
  Stop at `USER DECISION REQUIRED — FINAL V1.23 PROMOTION AUTHORIZATION` with
  actual release digest, SQLite/semantic/manifest SHAs, exact four target paths,
  input ledger/counts, both dry-runs, reviewer and backup results. Only now display
  `USER APPROVED RELEASE PROMOTION V1.23 <actual_release_digest>` as a required
  statement, never as received approval. Do not consume it or start ingestion.

## Coverage and current handoff

| Approved Design | Executable coverage |
|---|---|
| §§1–3 fixed scope/input/chain | input register; Task1 recovery; Tasks6–7 recheck |
| §§4–5 exact delta/API | Tasks1–2 and literal baseline-schema forgery in Task3 |
| §6 full projection | Task3 independent fixture; Task4 field equality; Task6 queries |
| §7 identity/21 checks/bytes | Tasks2–4; Task6 dual builds and full gates |
| §8 publication/lifecycle/rollback | Tasks4–5 negative controls; Task7 final gate |
| §9 closed paths | file map; explicit commit/scope checks in every task |
| §10 review/regression/backup/stop | Tasks6–7; human implementation gate below |

Current checkpoint is docs-only: self-review and separate technical Plan review,
then explicit docs commit/push. No checkbox above is completed by writing this
Plan, and no implementation/dry-run result is claimed. Human next decision:
`USER DECISION REQUIRED — V1.23 PROMOTION PLAN REVIEW`.
Recommended execution: Native / Inline, with a separate final implementation
reviewer. Implementation starts only after human Plan approval and execution
authorization; Design approval is already received and must not be requested again.

Technical review record (2026-10-19): a separate read-only reviewer checked this
Plan against the approved Design and pinned production/test counterparts.
Initial Critical0/Important0/Minor1 was resolved by explicitly enumerating the
protected paths above; targeted independent re-review reports
Critical0/Important0/Minor0, with all16 existing candidate trees covered.
This is Plan readiness for human review, not implementation certification.
No tests, real dry-runs or backup recovery were run for this docs-only review.
