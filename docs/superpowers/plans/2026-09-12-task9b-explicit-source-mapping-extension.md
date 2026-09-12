# Task 9B Explicit Source Mapping Extension Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a deterministic, human-approved explicit source-mapping mode that converts otherwise ambiguous Mathpix MMD/MMD.ZIP sources into the existing Task 9B Source IR and canonical Task 9A package without changing parser mode, Task 9A, Task 9C, or frozen data.

**Architecture:** Keep `adapt_mmd_package()` as Mode A and add a module-scoped `joy_m2.ingest.source_mapping` surface for Mode B. A line-oriented advisory draft is converted to a canonical byte-span mapping and review report; a separately typed exact approval then authorizes validation, Source IR construction, and reuse of the existing canonical package renderer. Both modes converge at the five existing private Source IR carriers.

**Tech Stack:** Python 3.12 standard library, frozen dataclasses, strict duplicate-aware JSON decoding, `hashlib`, `zipfile`, `pathlib`, `unittest`.

**Spec:** `docs/superpowers/specs/2026-09-07-task9b-mmd-adapter-design.md`, especially section 21.

## Global Constraints

- Work only on branch `task8b/pipeline-migration`; do not merge, rebase, squash, force-push, or create a PR.
- Do not modify Task 9A, Task 9C, `src/joy_m2/ingest/__init__.py`, database/release code, `data/`, `releases/`, `legacy/`, or frozen artifacts.
- Do not add a tenth Task 9B diagnostic code or change the exact 22-name root `joy_m2.ingest.__all__`.
- Do not copy the external `0918` archive into the repository or use it as test authority.
- Do not change any production behavior before all four extension RED groups below are valid.
- A valid RED must be caused by missing extension behavior, never import setup, fixture construction, environment, or syntax failure.
- Every destination is a new strict descendant of `PipelineConfig.staging_root`; failure leaves no partial destination.
- V1.18 stays at SHA-256 `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7` and 497 questions.
- Task 9A remains 41/41 GREEN, existing Task 9B remains 214/214 GREEN, Task 9C remains 71/71 GREEN, `releases/V1.19/` remains absent, and formal imported questions remain zero.

---

## File map

**Production**

- `src/joy_m2/ingest/source_mapping.py` — new Mode B public carriers, strict draft/mapping decoders, deterministic proposal publication, approval validation, span/coverage/image diagnostics, and explicit adapter orchestration.
- `src/joy_m2/ingest/adapter_models.py` — extend only `MmdSelection.language_layout` carrier values with `source_chinese` and `source_english`.
- `src/joy_m2/ingest/adapter.py` — mode-specific selection-manifest language allow-list and reuse-safe source-only/explanation render/package helpers.
- `src/joy_m2/ingest/mmd_parser.py` — one private lexer entry point for an already-authoritative mapped question span; no boundary discovery changes.

**Tests and fixtures**

- `tests/unit/test_mmd_adapter_models.py` — exact public-carrier language enum and Mode A compatibility controls.
- `tests/unit/test_mmd_source_mapping.py` — exact module surface, public carriers, strict JSON schemas, line-to-byte conversion, approval, stages, diagnostics, atomicity, and determinism.
- `tests/integration/test_mmd_explicit_mapping.py` — Source IR/package projection, answer/explanation/image behavior, Task 9A equivalence, Mode A preservation, repeat, and cross-root determinism.
- `tests/fixtures/task9b/explicit/source.mmd` — minimal synthetic ambiguous/repeated-label source.
- `tests/fixtures/task9b/explicit/images/diagram.jpg` — minimal deterministic opaque image bytes.

**Authority and closure**

- `docs/superpowers/specs/2026-09-07-task9b-mmd-adapter-design.md` — already committed executable authority.
- `docs/superpowers/plans/2026-09-12-task9b-explicit-source-mapping-extension.md` — this implementation plan.
- `PROJECT_STATE.md` — update only after implementation review passes.
- `docs/reports/TASK9B_VERIFICATION.md` — append exact extension evidence only after implementation review passes.

---

### Task 0: Plan authority checkpoint

**Files:**

- Review: `docs/superpowers/specs/2026-09-07-task9b-mmd-adapter-design.md`
- Review and commit: `docs/superpowers/plans/2026-09-12-task9b-explicit-source-mapping-extension.md`

**Interfaces:**

- Consumes: independently approved and committed Design section 21.
- Produces: independently approved, committed Plan before any test or production change.

- [ ] **Step 1: Obtain read-only independent Plan review**

Require the reviewer to compare file scope, APIs, exact types, four-RED order,
M0-M7 stages, diagnostics, fixtures, gates, commits, and human stops against the
Design. Critical and Important findings must both be zero.

- [ ] **Step 2: Commit only this Plan**

Verify `git diff --check`, stage this Plan explicitly, and commit:

```text
docs: plan Task 9B explicit source mapping
```

Verify its parent, one-file commit scope, `git diff-tree --check HEAD^ HEAD`,
clean staging, and clean worktree. Task 1 may not start from an unreviewed or
uncommitted Plan.

---

### Task 1: Establish all four RED groups before production

**Files:**

- Create: `tests/fixtures/task9b/explicit/source.mmd`
- Create: `tests/fixtures/task9b/explicit/images/diagram.jpg`
- Modify: `tests/unit/test_mmd_adapter_models.py`
- Create: `tests/unit/test_mmd_source_mapping.py`
- Create: `tests/integration/test_mmd_explicit_mapping.py`

**Interfaces:**

- Consumes: committed Design section 21 and the existing Task 9B test helpers.
- Produces: four independently runnable, behavior-focused RED groups; no production change.

- [ ] **Step 1: Add a minimal synthetic fixture**

Create a UTF-8 MMD fixture containing two complete mapped questions with the same visible label, one repeated image reference, one explicit solution, one explicit explanation, one missing solution, a heading, and footer text. The question boundaries must not depend on the frozen Mode A marker grammar. Store a small fixed byte payload at `images/diagram.jpg`; tests treat it as opaque bytes.

Use these exact fixture bytes, with LF after every shown line including the
last:

```text
Worksheet heading
Repeat A
Find $x+1$.
![](./images/diagram.jpg)
Solution evidence
2
Explanation evidence
Because $1+1=2$.
Repeat A
State $y$.
![](./images/diagram.jpg)

Footer branding
```

The opaque image file is exactly the UTF-8 bytes `fixture-image-v1\n`. The
valid draft maps question 1 to lines 2-4, solution to 5-6, explanation to 7-8,
question 2 to lines 9-11, and ignores lines 1 and 13 with non-empty reasons.
The blank line 12 is the whitespace-only coverage control.

- [ ] **Step 2: Add shared test builders with exact JSON bytes**

In `test_mmd_source_mapping.py`, define helpers that:

```python
def canonical_json(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")
```

Build a valid Mode B selection manifest with `source_kind="mmd"`, the fixture SHA, `expected_candidate_count=2`, two unique proposed IDs, `language_layout="source_english"`, one `source_answer`, one `missing_from_source`, and the same expected image member in both selections. Build the line draft with exact section 21.2 keys and inclusive 1-based lines.

- [ ] **Step 3: RED group 1 — public carriers/API and mode-specific language**

Add a failure-safe import helper so a missing new module is an assertion FAIL,
not a loader ERROR:

```python
def source_mapping_module(testcase: unittest.TestCase):
    try:
        return importlib.import_module("joy_m2.ingest.source_mapping")
    except ModuleNotFoundError:
        testcase.fail("explicit source-mapping API is not implemented")
```

Every test calls a behavior-specific wrapper such as
`require_api(self, "propose_mmd_source_mapping")`. If the module or requested
name is absent, that individual test calls `self.fail()` with the exact missing
behavior name; the test is therefore collected as FAIL, not ERROR or skip.
Once the surface exists, the same test continues through its full production
call and all behavior assertions. No test class has a module-level import of
the new surface, and no test-local fake implementation is permitted.

Use only the returned module's four approved names. Lock exact
`source_mapping.__all__`, exact frozen dataclass field order/no
defaults/runtime validation, approval single-line text, digest validation, and
`candidate_count` bool rejection. Wrap the two new `MmdSelection` constructions
so the current `PipelineError` becomes `self.fail("source-only carrier value is
not implemented")`, never an uncaught ERROR. Add an integration negative
control proving Mode A `adapt_mmd_package()` rejects both source-only values at
D0 without reading the source.

- [ ] **Step 4: Run RED group 1**

Run:

```bash
PY=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
$PY -m unittest \
  tests.unit.test_mmd_adapter_models \
  tests.unit.test_mmd_source_mapping.PublicContractTests \
  tests.integration.test_mmd_explicit_mapping.ModeACompatibilityTests
```

Expected: existing tests import and pass; new tests produce assertion FAILs
only because source-only carrier values and the new module/API/carriers do not
exist. ERROR must remain zero. Record collected/PASS/FAIL/ERROR/exit code and
each contract gap.

- [ ] **Step 5: RED group 2 — proposal and strict decoding**

Add tests for valid deterministic proposal bytes plus strict draft failures: missing/non-regular/unreadable input exception boundaries, invalid UTF-8, BOM, invalid JSON, duplicate key, non-object, missing/extra key, wrong exact type including bool-as-int, invalid enum/path/range/order/duplicate, CR/LF source ID, and source-free mapping/selection disagreement. Lock line-to-byte conversion through physical line terminators, canonical mapping key sets/types/order, canonical JSON without LF, mapping digest, review path/name/content headings, atomic destination cleanup, and no source read after an M0 blocker.

- [ ] **Step 6: Run RED group 2**

Run:

```bash
PY=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
$PY -m unittest tests.unit.test_mmd_source_mapping.ProposalContractTests
```

Expected: every proposal test is independently collected. The behavior-specific
wrapper converts an absent proposal API into that test's named assertion FAIL;
if the surface already exists, the call reaches and fails its exact
proposal/decoder assertion. ERROR and skip must remain zero. No shared setup,
fixture, loader, or test-local fake is an accepted RED.

- [ ] **Step 7: RED group 3 — canonical mapping validation and approval**

Add independent negative controls for wrong outer source SHA, wrong primary/answer member SHA, invalid member, zero/reversed/out-of-range span, wrong question/answer member, overlap, duplicate proposed ID, count/ID/number/section mismatch, missing/non-matching approval, unaccounted non-whitespace, unbound/ignored/bound-and-ignored image states, unsafe and malformed image targets, invalid UTF-8, unclosed atomic token, and stable multi-issue ordering. Add positive controls for repeated display labels at distinct spans, a zero-solution `missing_from_source` record, one image reused by two questions but staged once, and explicit ignored footer/resource decisions. Add Mode B controls for valid `english_then_chinese`, valid `interleaved_bilingual`, and invalid bilingual transitions producing the exact M5 `language_mapping_ambiguous` envelope.

- [ ] **Step 8: Run RED group 3**

Run:

```bash
PY=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
$PY -m unittest tests.unit.test_mmd_source_mapping.MappingValidationTests
```

Expected: every mapping-validation test is independently collected and fails
through its named API assertion or its exact validation assertion. Failures are
missing Mode B validation/approval behavior. Record every expected
code/field/evidence/stage and confirm ERROR=0, skip=0, and no environment or
construction failure.

- [ ] **Step 9: RED group 4 — Source IR, canonical package, equivalence, determinism**

Add integration tests that approve a valid mapping and lock:

- physical `source_order` derived from span order while candidate arrays follow semantic order;
- whole-question preservation with no subpart split;
- source-only English/Chinese projection;
- both existing bilingual layouts inside Mode B, including exact Chinese
  projection and M5 diagnostic behavior;
- solution array-order rendering and independent explanation evidence pointer;
- missing-answer representation;
- image byte identity and stage-once reuse;
- unchanged Task 9A 18-field manifest and 23 caller-supplied candidate fields;
- unchanged `source/source-map.json` schema;
- Task 9A preflight candidate/issues/count/status/report/digest equality for equivalent Mode A and Mode B fixtures;
- same-root repeat and independent-root byte equality;
- no `source_mapping.json`, approval text, outer ZIP SHA, paths, timestamps, or review notes in the canonical package.

- [ ] **Step 10: Run RED group 4**

Run:

```bash
PY=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
$PY -m unittest tests.integration.test_mmd_explicit_mapping
```

Expected: every integration test is independently collected and fails through
its named explicit-adapter assertion or exact package/equivalence assertion.
ERROR and skip remain zero. Failures are missing explicit adapter behavior,
not Task 9A or existing package behavior.

- [ ] **Step 11: Validate the global RED gate**

Run all four commands again and record exact outcomes. Inspect:

```bash
git status --short
git diff --name-only
```

Expected: only the approved test/fixture files differ; none of the four production files differ. If any RED is accidental, repair the test/fixture before continuing. Do not weaken a contract assertion.

- [ ] **Step 12: Obtain the independent all-RED checkpoint**

Give a read-only reviewer the committed Design/Plan, test/fixture diff, all four
commands, collected/PASS/FAIL/ERROR/skip/exit counts, and per-test missing
behavior reasons. Require confirmation that every test is individually
collected, every expected failure is an assertion against its own target
behavior/API, no test-local fake substitutes for production, ERROR=0, skip=0,
and no production file differs. Critical and Important findings must be zero.
Task 2 is forbidden until this independent RED checkpoint passes.

---

### Task 2: Implement public carriers and mode-specific manifest decoding

**Files:**

- Modify: `src/joy_m2/ingest/adapter_models.py`
- Modify: `src/joy_m2/ingest/adapter.py`
- Create: `src/joy_m2/ingest/source_mapping.py`
- Test: `tests/unit/test_mmd_adapter_models.py`
- Test: `tests/unit/test_mmd_source_mapping.py`

**Interfaces:**

- Consumes: exact section 21.1 carrier/API contracts.
- Produces: `SourceMappingProposal`, `SourceMappingApproval`, module exact `__all__`, and a mode-specific private selection decoder.

- [ ] **Step 1: Add the two public frozen carriers**

Implement exactly:

```python
@dataclass(frozen=True)
class SourceMappingProposal:
    proposal_root: Path
    mapping_path: Path
    review_path: Path
    source_id: str
    source_sha256: str
    mapping_sha256: str
    candidate_count: int

@dataclass(frozen=True)
class SourceMappingApproval:
    source_id: str
    mapping_sha256: str
    approval_text: str
```

Validate exact paths/digests/non-boolean count, path identities, single-line source ID, and exact approval text. Export only the four Design names from `source_mapping.py`; do not edit root `ingest.__init__.py`.

- [ ] **Step 2: Extend only the typed carrier enum**

Change `_LANGUAGE_LAYOUTS` in `adapter_models.py` to exactly the four Design values. Do not modify another carrier field or validation.

- [ ] **Step 3: Parameterize the private selection decoder**

Change the private signature to the one exact form:

```python
def _decode_manifest(
    selection_manifest_path: Path,
    source_path: Path,
    *,
    allowed_language_layouts: tuple[str, ...],
) -> MmdAdapterManifest:
    ...
```

`adapt_mmd_package()` passes exactly
`("english_then_chinese", "interleaved_bilingual")`; both Mode B APIs pass
exactly those two followed by `("source_chinese", "source_english")` in that
order. Preserve D0 exact evidence and source-not-read behavior. No boolean mode
flag or implicit default is permitted.

- [ ] **Step 4: Run the carrier/API focused tests**

Run:

```bash
PY=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
$PY -m unittest tests.unit.test_mmd_adapter_models \
  tests.unit.test_mmd_source_mapping.PublicContractTests
```

Expected: group 1 GREEN; groups 2-4 remain behavior RED.

---

### Task 3: Implement the M0-M3 strict mapping foundation

**Files:**

- Modify: `src/joy_m2/ingest/source_mapping.py`
- Test: `tests/unit/test_mmd_source_mapping.py`

**Interfaces:**

- Consumes: strict draft/mapping bytes, explicit-mode selection metadata, and safely read source bytes.
- Produces: decoded exact-schema objects, bytewise physical-line tables, validated M0-M3 spans/identity, and canonical sidecar bytes for Task 4; it does not publish a proposal yet.

- [ ] **Step 1: Implement strict duplicate-aware JSON primitives**

Reuse the base adapter's canonical type/path/evidence conventions. Define exact field tuples for every draft and mapping object. Reject BOM/non-finite constants/duplicates/subclasses/bool-as-int and collect all independently determinable M0 schema issues. Implement the Design section 21.3 exact cross-field envelopes for semantic orders, duplicate solution/explanation spans, canonical ignored-array ordering, and the answer-member/digest pair; do not invent alternate fields, tokens, or hashes.

- [ ] **Step 2: Implement safe input and destination preflight**

Check exact argument types, strict staging descendant, pre-existing output, selection manifest, and draft before source access. Preserve the selection manifest's structured D0 boundary; use `InputMissingError`/`InputFormatError` for draft as frozen.

- [ ] **Step 3: Reuse the committed archive boundary**

Call the existing selection decoder in explicit mode and `read_selected_source()` rather than adding ZIP extraction. Preserve D1/D2 issue ownership, bounded reads, CRC/ratio checks, and outer source SHA validation.

- [ ] **Step 4: Convert inclusive lines to exact byte spans**

Build physical-line offset tables bytewise by scanning only CR, LF, and CRLF;
do not decode MMD here. Convert each declared range from the first byte of
`line_start` through the terminator of `line_end`, or EOF. Validate
role/member/order/geometry/overlap and preserve declared solution/explanation
render order. Strict UTF-8 remains exclusively M4.

- [ ] **Step 5: Build canonical sidecar bytes without publication**

Populate the exact thirteen-key canonical mapping, derive member SHA values,
sort ignored arrays as specified, serialize with sorted compact JSON and no LF,
and hash those bytes. Keep the result private and in memory. M4 lexical
validation, M5/M6 warnings, review rendering, and atomic proposal publication
remain forbidden until Task 4.

- [ ] **Step 6: Run only the M0-M3 strict-decoding subset**

Run:

```bash
PY=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
$PY -m unittest tests.unit.test_mmd_source_mapping.StrictDecodingTests
```

Expected: M0-M3 strict schema/type/line/span/identity tests PASS with no skip or
expected failure. Proposal publication tests remain RED until Task 4.

---

### Task 4: Implement approved-mapping validation and Source IR construction

**Files:**

- Modify: `src/joy_m2/ingest/source_mapping.py`
- Modify: `src/joy_m2/ingest/mmd_parser.py`
- Test: `tests/unit/test_mmd_source_mapping.py`

**Interfaces:**

- Consumes: exact canonical mapping bytes, `SourceMappingApproval`, selected source bytes, and the existing five private Source IR carriers.
- Produces: atomic `SourceMappingProposal`, validated `_SourceDocument`, and binding tuple in mapping semantic order.

- [ ] **Step 1: Decode mapping and bind approval at M0**

Validate exact canonical bytes/schema, mapping SHA, approval source ID/digest/text, selection count/order/ID/number/section, and solution/answer cross-fields before source access. Emit only the matrix code/field/evidence projections.

- [ ] **Step 2: Validate source/member identity and all spans**

After D1/D2, compare source/member names and digests. Validate each span once, member roles, question disjointness, containment partition, semantic-owner overlap, and stable issue ordering. Derive physical `source_order` by sorting question spans, never from semantic order.

- [ ] **Step 3: Add an already-authoritative span lexer**

At M4, first strict-decode both the selected primary and the optional selected
answer member in canonical member order, collecting the exact independent
`mmd_parse_failed/invalid_utf8` rows. Only if both decode facts pass, call one
private `mmd_parser.py` helper with the primary `_SourceMember`, one validated
question interval, and language layout. Reuse existing atomic/image primitives
to return exact text spans plus safe image-token records without discovering or
changing the question boundary. Emit the M4 rows for unclosed/unsupported
atomic/image syntax and unsafe target precedence; the answer member is decoded
but is never passed through the question lexer.

- [ ] **Step 4: Validate image and coverage closure**

Bind every source token once, allow a member to serve multiple questions, stage a present member once, keep representable missing members as `None`, enforce ignored/bound mutual exclusion, and emit proposal warning versus approved blocker behavior. Compute uncovered intervals using only ASCII bytes `09/0A/0B/0C/0D/20` as whitespace.

- [ ] **Step 5: Render and atomically publish the proposal**

After M0-M6 proposal validation, render the bounded deterministic review with
the exact warning lines, write canonical mapping plus review bytes to a sibling
temporary directory, and perform one atomic destination rename. Clean the
temporary directory on every error and return the exact
`SourceMappingProposal`.

- [ ] **Step 6: Construct exact Source IR and semantic bindings**

Instantiate only the five existing private carriers. Put document questions in physical order, build bindings in mapping semantic order, retain solution/explanation array order, and include each distinct present image member once.

- [ ] **Step 7: Run proposal and mapping validation GREEN**

Run:

```bash
PY=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
$PY -m unittest \
  tests.unit.test_mmd_source_mapping.ProposalContractTests \
  tests.unit.test_mmd_source_mapping.MappingValidationTests
```

Expected: all proposal and mapping/approval/span/image/coverage tests PASS with
exact stable diagnostics.

---

### Task 5: Reuse canonical rendering and make the explicit adapter GREEN

**Files:**

- Modify: `src/joy_m2/ingest/adapter.py`
- Modify: `src/joy_m2/ingest/source_mapping.py`
- Test: `tests/integration/test_mmd_explicit_mapping.py`

**Interfaces:**

- Consumes: validated Source IR/bindings and existing `_publish_package` contract.
- Produces: `adapt_mmd_package_from_mapping(...) -> AdaptedImportPackage` with canonical Task 9A bytes.

- [ ] **Step 1: Make shared rendering support the frozen Mode B projections**

Keep Mode A output byte-identical. Add exact `source_chinese`/`source_english` projection, solution array-order rendering, explanation array-order rendering, and the source-map explanation evidence pointer. Do not add an alternate candidate or source-map schema.

- [ ] **Step 2: Reuse the existing package publisher**

Pass the validated Mode B document/bindings/candidates/member bytes into the shared package builder. Confirm `source_mapping.json`, approval text, outer ZIP SHA, ignored reasons, proposal paths, and review Markdown are absent from the canonical package.

- [ ] **Step 3: Implement the public explicit adapter orchestrator**

Validate arguments/destination, run M0-M6 in order, call `require`-equivalent blocker handling, and enter M7 only after exact approval and complete coverage. Return the existing exact `AdaptedImportPackage`.

- [ ] **Step 4: Run integration GREEN**

Run:

```bash
PY=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
$PY -m unittest tests.integration.test_mmd_explicit_mapping
```

Expected: all Mode B package/equivalence/determinism tests PASS.

- [ ] **Step 5: Run the entire extension and base Task 9B suite**

Run:

```bash
PY=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
$PY -m unittest \
  tests.unit.test_mmd_adapter_models \
  tests.unit.test_mmd_archive \
  tests.unit.test_mmd_parser \
  tests.unit.test_mmd_source_mapping \
  tests.integration.test_mmd_adapter \
  tests.integration.test_mmd_explicit_mapping
```

Expected: all tests PASS; the original 214 remain present and GREEN; skip=0 and expectedFailure=0.

---

### Task 6: Complete regressions and independent implementation review

**Files:**

- Modify only an already-approved production/test/fixture file if an independent Critical or Important finding proves a defect.

**Interfaces:**

- Consumes: complete uncommitted extension.
- Produces: fresh regression evidence and independent review with Critical=0, Important=0.

- [ ] **Step 1: Run maintained gates**

Run:

```bash
PY=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
$PY -m unittest tests.integration.test_ingest_preflight
$PY -m unittest tests.unit.test_v119_writer_models \
  tests.unit.test_v119_writer_primitives tests.integration.test_v119_writer
$PY releases/V1.18/verify_task6_release.py releases/V1.18
git diff --check
```

Expected: Task 9A 41/41, Task 9C 71/71, validator PASS/497, and diff check PASS.

- [ ] **Step 2: Verify frozen and zero-write boundaries**

Record V1.18 SQLite SHA/count before and after; fingerprint `data/`, `releases/`, `legacy/`, and production files outside the four-file scope. Confirm `releases/V1.19/` absent, no candidate DB created, and imported questions remain zero.

- [ ] **Step 3: Request independent implementation review**

Provide the reviewer the committed Design/Plan, complete diff, RED evidence, focused counts, maintained gates, exact real-source identity, and explicit instruction to remain read-only. Require Critical=0 and Important=0.

- [ ] **Step 4: Remediate findings test-first**

For each valid finding, add the smallest failing test in an approved test file, prove the failure, apply the smallest approved production fix, rerun focused and full gates, and request incremental re-review. Stop on any required ninth production/test file or authority conflict.

---

### Task 7: Close, commit, and push the implementation

**Files:**

- Modify: `PROJECT_STATE.md`
- Modify: `docs/reports/TASK9B_VERIFICATION.md`
- Commit: only the four approved production files, four approved test/fixture paths, and these two closure docs.

**Interfaces:**

- Consumes: independent implementation PASS and fresh full gates.
- Produces: reviewed Task 9B explicit-mapping checkpoint on `origin/task8b/pipeline-migration`.

- [ ] **Step 1: Synchronize closure evidence**

Record exact commit baseline, Design/Plan SHAs, RED evidence, final test counts, deterministic/frozen evidence, zero imports, and that mapping approval remains separate from Human Gate C. Do not declare the real source approved.

- [ ] **Step 2: Inspect exact commit scope**

Run:

```bash
git status --short
git diff --name-only
git diff --check
```

Expected: no file outside section 21.7 scope. Stage every allowed path explicitly; never use `git add .`.

- [ ] **Step 3: Commit the reviewed extension**

Use commit message:

```text
feat: add explicit MMD source mapping
```

Verify committed file set, parent, `git diff-tree --check HEAD^ HEAD`, empty staging, and clean worktree.

- [ ] **Step 4: Ordinary-push the existing branch**

Run `git push` without force options. Verify local HEAD equals `origin/task8b/pipeline-migration` and ahead/behind is `0/0`. Do not create a PR or tag.

---

### Task 8: Generate the first real proposal and stop for human review

**Files:**

- External read-only input: `/Users/miaohuanjoy/Desktop/0918 区间再现_课上补充 笔记 2.mmd.zip`
- Generated ignored staging output only: proposal directory beneath the configured Task 9 staging root.

**Interfaces:**

- Consumes: external archive SHA `d85a7d220e41375cc29b34b20173ae34d8dd2d83667a98f5fab2de5d4ccab271`, primary member `eb1509f2-5767-4c11-97a6-9179a4261200.mmd`, primary SHA `3216287f3be8ce80fafef8489cb27d20a8d81dbaa2d234b43f95ceb05b1a4d38`, one JPEG, an advisory line draft, and explicit selection metadata.
- Produces: proposal JSON/Markdown only and the Human Source-Mapping Review gate.

- [ ] **Step 1: Reconfirm real source identity without extraction**

Use bounded inventory/read APIs; confirm archive/member/image hashes, 19,462 primary bytes, 533 physical lines, and no V1.16 access.

- [ ] **Step 2: Author an advisory line mapping from semantic inspection**

Create an ignored staging draft covering complete questions, solution/explanation evidence only where source-supported, explicit ignored headings/duplicates/footer, and explicit image binding/ignore choice. Do not ask the user to count bytes and do not put proposal notes into canonical identity.

- [ ] **Step 3: Generate and independently inspect the proposal**

Run `propose_mmd_source_mapping(...)` twice in independent roots. Confirm identical mapping/review bytes, exact digest, candidate table, ignored ranges, unmapped ranges, unbound images, warnings, and no canonical package.

- [ ] **Step 4: Stop at the exact human gate**

Report source ID/SHA, mapping SHA, candidate count, concise full mapping table, ignored/unmapped blocks, image decisions, and warnings, followed by:

```text
USER DECISION REQUIRED — SOURCE MAPPING REVIEW
```

Require exactly:

```text
USER APPROVED SOURCE MAPPING <source_id> <mapping_sha256>
```

Do not call `adapt_mmd_package_from_mapping`, Task 9A preflight, Task 9C writer, database code, release code, or promotion before that approval.
