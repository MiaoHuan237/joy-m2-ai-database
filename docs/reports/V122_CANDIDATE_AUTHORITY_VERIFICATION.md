# Execution ledger — plan: docs/superpowers/plans/2026-09-21-v122-next-version-candidate.md

## Authority and boundaries

Design clarification: f51aaceaf08359747983a4dbccdb3b5ad0ee9cea.
Plan: 2e67696bd6ab12a6716360f4b868af7fbad160c1; user approved Native / Inline Execution.
Docs remote checkpoint verified at 2e67696bd6ab12a6716360f4b868af7fbad160c1.
No real V1.22 writer, release, 2020 ingestion, or formal baseline mutation is authorized.

Ruling: Keep the inline execution ledger in this approved report and scratch evidence
under tmp/pdfs/task12-v122-hkdse-2019 instead of the skill's default scratch directory.
The Design's closed file scope takes precedence; cost if wrong is record relocation only.

## Interface pre-flight

| Producer → consumer | Shared contract | Resolution |
|---|---|---|
| Task 1 → 2 / 3 / 4 | 13 carriers, strict loader, five safe API scaffolds | Exact frozen V122 counterparts; scaffolds do not claim behavior |
| Task 2 → 6 | Verified transcription → five-file package | Four non-manifest payloads unchanged |
| Task 3 → 4A | Genesis preflight + synthetic approval | Parent artifact absent, authority digest mandatory |
| Task 4A → 4B1 | Verified first generation | Parent-dependent RED prohibited until first-generation GREEN |
| Task 4B1 → 4B2 | Valid second-batch preflight / approval | Multi-batch RED prohibited until parent-preflight GREEN |
| Task 4 → 5 → 6 | Independent verification, review, committed engineering | Critical/Important zero before real preflight |

## Progress

- Task 1: models/loader/API complete; base 2e67696bd6ab12a6716360f4b868af7fbad160c1.
- Tasks 2 / 3 / 4A / 4B1 / 4B2: implemented in dependency order; evidence below.
- Task 5: pending final regression/review. Task 6: not started.

## Task 1 evidence

- Missing model module: 1 collected / 1 assertion FAIL / 0 ERROR.
- Empty importable model module: 14 collected / 1 PASS / 13 assertion FAIL /
  0 ERROR. Assertions were moved out of setup and rerun before production;
  the earlier setup assertion run is not counted as contract RED.
- Models implemented: new + historical models 29/29 PASS.
- API/surface RED: 2 test methods / 6 failed assertions (five subcases), 0 ERROR.
- Annotated nonbehavioral scaffolds: 16/16 PASS.
- Strict loader RED: 4 methods / 11 failed assertions, 0 ERROR; all fail because
  the intentional loader stub lacks behavior, not imports/fixtures.
- Loader implemented: models/API/loader plus historical model/surface/replay
  tests 57/57 PASS before additional frozen/copy/genesis lock.
- No real source processing or candidate write.

Final Task 1 gate: 58/58 PASS, 0 skips/expected failures; commit 1fbbc0d.
Baseline maintained suite (started before edits): 1005/1005 PASS, 0 errors,
skips or expected failures, 253.860 seconds.

## Task 2 evidence

Base 1fbbc0d. Synthetic bridge RED: 9 methods, 1 API PASS, 12 failed
assertions including subcases; 0 ERROR. Only deliberate missing behavior.
Bridge implementation is a fixed V122 sibling; existing four payload helpers
and old bridge bodies remain unchanged.
Task 2 GREEN: 9 new + 7 old bridge + 50 Task 10B = 66/66 PASS.
The first combined GREEN command misspelled an integration module; its
import ERROR is not RED or a passing gate. The corrected command passed.
No real 2019 proposal, source, approval or candidate was changed.

Task 2 complete: commit be360e8.

## Task 3 evidence

Base be360e8. Initial genesis behavior RED: 12 test methods, 2 PASS /
13 failed assertions including subcases / 0 ERROR, exclusively missing
preflight behavior. No parent creation was used as a prerequisite.
Schema/count fixture SQL and unrepresentable-record expected counts were
corrected after first GREEN attempt; these construction/expectation failures
are not claimed as behavior RED.
Additional sibling-manifest contract RED: valid DB plus wrong/missing sibling
manifest incorrectly accepted (2 failed assertions); fixed with exact frozen
manifest hash/size and regular-file validation.
Final genesis + unchanged V121 + Task 9A: 61/61 PASS, zero skips/xfails.
Exact 591-row index including 2015–2018 duplicate, deep schema/view/count
controls, genesis oracle, path-independent equality and zero-write verified.
Non-None parent still raises explicit NotImplementedError pending Task 4B1.

Task 3 complete: commit 72227cd.

## Task 4A evidence

Base 72227cd. First-generation RED (after correcting test wrapper construction):
14 methods / 1 API PASS / 15 failed assertions including subcases / 0 ERROR.
Earlier uncaught deliberate stubs and wrapper syntax error are NOT valid RED.
Writer/verifier/profile implementation accepts only a single approved batch;
multi-batch entry explicitly remains NotImplementedError, as does parent preflight.
New regression identified candidate SQLite readability incorrectly inferred
without reading its schema: assertion RED → candidate schema read → GREEN.
The output-path negative fixture was corrected because its initial path was
actually inside approved staging; no production rule was relaxed.
Final Task 4A + Tasks 1–3: 60/60 PASS (17 candidate tests), zero skips/xfails.
Verified 24 checks, full old SQLite schema/row preservation, first order 592,
private user_version 122, candidate selectable=0, deterministic roots, independent
genesis calls, forged matching parents, corruption and cleanup controls.
This is NOT evidence of parent-preflight or multi-batch GREEN.

## Task 4B1 / 4B2 and hardening evidence

- After 4A GREEN, parent-preflight RED: 3 methods / 3 FAIL / 0 ERROR,
  each first built and independently verified generation 1, then reached the
  explicit parent-preflight stub. Minimum parent implementation: 3/3 GREEN.
- After 4B1 GREEN, multi-batch RED: 4 methods / 5 assertion failures
  (including subcases) / 0 ERROR. Valid B preflight/approval bound generation
  1 before writer/verifier calls. Removing first-generation-only entry guards
  enabled full-prefix reconstruction; initial 4B2 GREEN: 4/4.
- Genesis mutation checks executed in memory, without source edits: removing
  writer's own boundary caused its targeted test to FAIL; removing verifier's
  own boundary caused its targeted test to FAIL (each 1 FAIL / 0 ERROR).
- Additional forged empty-prefix/nested-approval control: 1 method / 2 FAIL /
  0 ERROR (IndexError/AttributeError leaked by writer); request validation now
  precedes field access. Existing genesis checks remain independent.
- Added forged count, source-byte drift, parent-output overlap and second
  generation deterministic artifact assertions.
- The integrity-negative fixture was calibrated before claiming coverage:
  read-only SQLite in this runtime did not report the attempted CHECK/header
  mutations. Those failed fixture assertions are not production RED. Corrupting
  the synthetic candidate data b-tree page type produces a real integrity
  failure and its dedicated failed verification check (focused 1/1 GREEN).
- No real batch approval was constructed; all writer inputs are synthetic.

Final Task 4 focused regression: 153/153 PASS in 51.703s, zero skips/xfails;
25 new candidate cases + Tasks 1–3 + unchanged V120/V121 candidate suites.
Command: runtime Python -m unittest -q tests.integration.test_v122_candidate
tests.integration.test_v122_preflight tests.integration.test_v122_hkdse_bridge
tests.unit.test_v122_models tests.integration.test_v121_candidate
tests.integration.test_v120_candidate.
