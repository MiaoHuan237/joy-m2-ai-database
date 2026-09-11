# Task 9B Mathpix MMD Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Convert one explicitly selected Mathpix MMD or MMD.ZIP source into a deterministic canonical staging package that the frozen Task 9A preflight consumes unchanged.

**Architecture:** Strict manifest decoding (D0) precedes all source access. Safe source/archive inventory and bounded integrity streaming (D1–D2) precede a fixture-scoped deterministic parser (D3), explicit selection and mapping (D4–D7), and atomic publication of the exact Task 9A package. Task 9B is staging-only and never reads or writes a database.

**Tech Stack:** Python 3.12 standard library (`dataclasses`, `pathlib`, `json`, `hashlib`, `zipfile`, `tempfile`, `shutil`, `unicodedata`, `unittest`). No dependency addition is authorized.

**Spec:** `docs/superpowers/specs/2026-09-07-task9b-mmd-adapter-design.md`

## Current plan status

Task 9B Design authority is independently reviewed and committed at
`d19baa812213c8015dbb63a9ce3f431eaa077f42`. Task 9A is `CLOSED / PASS` at
`6fec37c45346b1680fb0bf0676c38e515c18cacd` with 41/41 integration tests.
Task 9B implementation is `NOT STARTED`. This Plan must pass independent review
and be committed before B1 or any production implementation begins.

## Global constraints

- Work only on branch `task8b/pipeline-migration` in its existing worktree.
- The only production files authorized are:

  ```text
  src/joy_m2/ingest/adapter_models.py
  src/joy_m2/ingest/archive.py
  src/joy_m2/ingest/mmd_parser.py
  src/joy_m2/ingest/adapter.py
  ```

- The only test files authorized are:

  ```text
  tests/unit/test_mmd_adapter_models.py
  tests/unit/test_mmd_archive.py
  tests/unit/test_mmd_parser.py
  tests/integration/test_mmd_adapter.py
  ```

- Fixture writes are restricted to:

  ```text
  tests/fixtures/task9b/representative/**
  tests/fixtures/task9b/golden/**
  tests/fixtures/task9b/security/**
  ```

- Do not modify Task 9A files, `src/joy_m2/ingest/__init__.py`, `src/joy_m2/models.py`, configuration, errors, database/export/release code, CLI, project scripts, Design authority, frozen data, `data/`, `releases/`, or `legacy/`.
- V1.18 remains byte-identical at SHA-256 `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7` and 497 complete questions.
- Task 9A manifest, candidate, normalization, sixteen-code issue taxonomy, digest, approval string, and zero-write behavior remain unchanged.
- Task 9B may write only a new descendant of `PipelineConfig.staging_root`; no V1.19 database artifact, formal import, writer, or promotion is authorized.
- Do not search for, read, or re-hash the historical V1.16 ZIP.
- Do not use `extractall()`, implicit source discovery, encoding guessing, parser recovery, filesystem ordering, random IDs, timestamps, or absolute paths as authority.
- Every behavior implementation follows valid RED first. The behavior RED gate must establish all three behavior groups before any archive/parser/mapping/package behavior is added.
- At every checkpoint run Task 9A 41/41 and the V1.18 validator. Record collected/PASS/FAIL/ERROR/exit code for focused RED/GREEN evidence.
- Independent review must report zero Critical and zero Important findings before a checkpoint commit or phase advancement.
- If the representative source cannot be safely minimized, its source/use authorization becomes unclear, or required evidence is missing, stop under the security/access policy rather than inventing data.

## Public and private boundaries

The sole public adapter API is exact:

```python
def adapt_mmd_package(
    selection_manifest_path: Path,
    source_path: Path,
    output_dir: Path,
    config: PipelineConfig,
) -> AdaptedImportPackage:
    ...
```

The only public Task 9B carriers are `MmdSelection`, `MmdAdapterManifest`,
`AdaptedImportPackage`, `MmdAdapterIssue`, and `MmdAdapterBlockedError`.
Internal helpers and the five exact frozen Source IR carriers remain private and
underscore-prefixed. No package-level `__all__` migration is authorized.

Use this runtime in commands when `python` is unavailable:

```bash
PY=/Users/miaohuanjoy/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
```

---

## Task 0: Commit this implementation Plan

**Files:**

- Create: `docs/superpowers/plans/2026-09-11-task9b-mmd-adapter-implementation.md`

- [ ] **Step 1: Validate Plan/Design consistency**

Check exact API, carriers, four production files, four test files, fixture
roots, nine diagnostics, D0–D7 ordering, B0–B9 sequence, frozen boundaries,
and exit gates against the committed Design.

- [ ] **Step 2: Obtain strict read-only independent review**

Require explicit findings by Critical/Important/Minor. Remediate and re-review
until Critical=0 and Important=0.

- [ ] **Step 3: Run the docs checkpoint gates**

```bash
git diff --check
$PY -m unittest -v tests.integration.test_ingest_preflight
$PY releases/V1.18/verify_task6_release.py releases/V1.18
git status --short
```

Expected: 41/41 PASS; validator `PASS`; only this Plan is changed; no staged
file before explicit staging.

- [ ] **Step 4: Commit and ordinary-push the Plan**

```bash
git add -- docs/superpowers/plans/2026-09-11-task9b-mmd-adapter-implementation.md
git diff --cached --name-only
git diff --cached --check
git commit -m "docs: add Task 9B implementation plan"
git diff-tree --check HEAD^ HEAD
git push
```

Verify local/upstream HEAD equality and ahead/behind `0/0`.

---

## Task 1: B1 representative and independent golden fixtures

**Files:**

- Create: `tests/fixtures/task9b/representative/selection.json`
- Create: `tests/fixtures/task9b/representative/vector.mmd`
- Create: the four selected question-image files beneath `tests/fixtures/task9b/representative/images/`
- Create: `tests/fixtures/task9b/representative/separate-answer-selection.json`
- Create: `tests/fixtures/task9b/representative/separate-answer.mmd.zip`
- Create: the exact canonical Task 9A tree beneath `tests/fixtures/task9b/golden/`

The external source is read-only evidence:

```text
数学M2王-向量及其应用.mmd.zip
SHA-256 59cef92aefc0f9b2d66db199b8cb7c72306bb61c1ff9554f3ca57da16b51ff52
primary 9027aeb0-3964-4138-a178-1092ea22ec8a.mmd
primary SHA-256 649f9df7bf2c63232c4e96d8cd07977822b5cdadc49f718038806a7542b71a97
```

The representative fixture retains only the reviewed 17 complete-question
region (examples 1–11, then exercises Q1–Q6) and these selected image members:

```text
images/9027aeb0-3964-4138-a178-1092ea22ec8a-32_438_671_1398_659.jpg
images/9027aeb0-3964-4138-a178-1092ea22ec8a-37_573_1010_888_568.jpg
images/9027aeb0-3964-4138-a178-1092ea22ec8a-38_337_837_334_606.jpg
images/9027aeb0-3964-4138-a178-1092ea22ec8a-39_527_784_342_678.jpg
```

Do not copy the outer archive, the four unselected chapter illustrations, a
formal database artifact, or any unreviewed question corpus.

- [ ] **Step 1: Verify external evidence before copying reviewed subsets**

Use metadata-only inventory plus bounded reads. Confirm the outer/member hashes,
one directory, eight STORED JPEG members, one STORED MMD member, 88,140 MMD
bytes, LF-only UTF-8, 1,997 lines, and the exact 17 marker sequence. Abort on
any mismatch.

- [ ] **Step 2: Author the minimal representative fixture**

Preserve selected MMD and image bytes exactly. The main selection contains 17
`MmdSelection` objects in semantic source order. Examples use
`answer_mapping="source_answer"`, `answer_number=null`; exercises use
`answer_mapping="missing_from_source"`, `answer_number=null`. Example 11 and
Q1–Q3 declare their exact expected image members. Explicit type/tags/difficulty
metadata must satisfy the approved carrier contract and must not be inferred by
production.

The separate-answer fixture is a small, deterministically packaged archive with
one primary member, one answer member, one question occurrence, and non-`None`
`answer_number`; its selection manifest binds the exact checked-in ZIP SHA. It
exists only to lock the approved same-ZIP answer-member path and is not the
17-question golden authority. Build it with fixed member order, timestamp,
permissions, `create_system`, and STORED compression, then independently
inspect its two raw members and metadata.

- [ ] **Step 3: Independently author the golden canonical package**

Create exactly:

```text
import_manifest.json
records/candidates.json
source/original.mmd.txt
source/source-map.json
images/<four selected members>
```

The golden package is authored from the Design rules, not by an adapter helper.
It preserves raw bytes, exact spans/digests, 23 caller-supplied candidate fields,
18 ordered manifest fields, source-map schema, file groups, and canonical JSON
byte conventions. Examples have source answers; exercises have empty solutions
and `missing_from_source`; explanations remain missing.

- [ ] **Step 4: Verify fixture integrity independently**

Run a standalone read-only script/test oracle that checks fixture allowlist,
hashes, 17 marker/order/count facts, four selected images, canonical JSON bytes,
no absolute paths, no outer ZIP SHA in golden output, and no extra files. Load
the golden manifest with frozen Task 9A and run `preflight_import`; record its
candidates/issues/counts/status/report/digest for later B7 comparison.

- [ ] **Step 5: Review and commit fixtures before behavior tests**

Require independent review for minimization, source fidelity, provenance,
expected package independence, absence of sensitive/unreviewed material, and
scope. Then:

```bash
git add -- tests/fixtures/task9b/representative tests/fixtures/task9b/golden
git diff --cached --name-only
git diff --cached --check
git commit -m "test: add reviewed Task 9B fixtures"
git diff-tree --check HEAD^ HEAD
git push
```

No production or behavior-test file enters this checkpoint.

---

## Task 2: B2 public carrier RED to GREEN

**Files:**

- Create: `tests/unit/test_mmd_adapter_models.py`
- Create: `src/joy_m2/ingest/adapter_models.py`

- [ ] **Step 1: Write exact public-contract RED tests**

Use `importlib.util.find_spec`/controlled import assertions so a missing module
is an intentional assertion failure, not an import/setup ERROR. Lock exact
dataclass fields/order/type hints/no defaults/frozen semantics:

```python
MmdSelection(
    proposed_question_id, kind, number, source_section, language_layout,
    answer_mapping, answer_number, expected_image_members, primary_type, tags,
    tag_status, difficulty_level, difficulty_status,
)

MmdAdapterManifest(
    schema_version, batch_id, source_kind, source_sha256, primary_member,
    answer_member, source_id, chapter, expected_candidate_count, selections,
)

AdaptedImportPackage(package_root, manifest_path, manifest)

MmdAdapterIssue(
    code, severity, proposed_question_id, source_locator, field, evidence,
)
```

Also lock `MmdAdapterBlockedError(InputFormatError)`, its exact `issues` tuple,
stable five-field issue sort, equal-key stability, fixed message, all enum and
cross-field rules, path grammar, tuple alias isolation, exact-int rejection of
`bool`, and `AdaptedImportPackage.manifest_path == package_root /
"import_manifest.json"`.

- [ ] **Step 2: Prove focused RED**

```bash
$PY -m unittest -v tests.unit.test_mmd_adapter_models
```

Expected: collected normally, zero ERROR, failures only because the Task 9B
module/types do not exist.

- [ ] **Step 3: Implement only the immutable contracts**

Implement the five exact public carriers and their validation in
`adapter_models.py`. Use exact runtime types where the Design requires them,
defensive tuple copies without deduplication/reordering, canonical NFC POSIX
path validation, exact lowercase SHA validation, and stable issue sorting. Do
not read any file or implement adapter behavior.

- [ ] **Step 4: Run carrier GREEN and frozen regressions**

```bash
$PY -m unittest -v tests.unit.test_mmd_adapter_models
$PY -m unittest -v tests.integration.test_ingest_preflight
$PY releases/V1.18/verify_task6_release.py releases/V1.18
git diff --check
```

Expected: all carrier tests PASS; Task 9A 41/41; validator PASS.

---

## Task 3: B2 API-existence RED and no-behavior scaffold

**Files:**

- Create: `tests/integration/test_mmd_adapter.py`
- Create: `src/joy_m2/ingest/adapter.py`

- [ ] **Step 1: Write API-shape RED**

Test the exact four parameter names/order/annotations and
`AdaptedImportPackage` return annotation. Verify there is no second answer
package parameter and no implicit root parameter. A controlled missing-module
assertion must FAIL without producing import ERROR.

- [ ] **Step 2: Prove API RED**

```bash
$PY -m unittest -v tests.integration.test_mmd_adapter.AdapterApiTests
```

- [ ] **Step 3: Add the minimum scaffold**

Create `adapter.py` with only the exact annotated function. Every call raises
`NotImplementedError("Task 9B adapter behavior is not implemented")` before
filesystem access or output creation.

- [ ] **Step 4: Run API GREEN and no-behavior boundary test**

The signature test must PASS and an invocation test must prove the fixed
`NotImplementedError`, no source read, and no output.

---

## Task 4: Establish the complete behavior RED gate

**Files:**

- Create: `tests/unit/test_mmd_archive.py`
- Create: `tests/unit/test_mmd_parser.py`
- Modify: `tests/integration/test_mmd_adapter.py`

No production file may change during this Task.

- [ ] **Step 1: Establish archive/safety RED**

Add independent controls for D0 source-free failure, D1 kind/digest and archive
metadata, D2 streaming/CRC, path normalization/collisions/types/hidden entries,
resource limits, encryption/compression, selected-member existence, second MMD,
nested archive, ignore-after-safety behavior, plain-MMD adjacent images, and
stage precedence/multiplicity. Include deletion-sensitive cases for every
absolute/backslash/drive/UNC/traversal/dot/empty/escape rule; raw duplicate,
NFC, and casefold collision; hidden, symlink, special, executable, nested,
second-MMD, encryption, compression, ZIP structure, CRC, and decompression
rule; each 50/100/20/10 MiB, 256-member, and 100:1 boundary; both selected-
member-missing paths; and ignore-after-validation metadata/unselected images.
Patch source access to prove D0 blockers do not touch `source_path`; patch ZIP
member reads to prove D1 blockers stop D2.

- [ ] **Step 2: Establish parser/mapping RED**

Add independent controls for the exact marker grammar, exercise section state,
complete-question/subpart boundaries, local/separate solutions, empty
explanation grammar, UTF-8 byte spans, fragment SHA, atomic constructs,
unsupported/unclosed syntax, both bilingual layouts, same-line `en -> zh`,
byte-complete partitioning, rendering, stable locators, and each unsafe image
target reason. Lock all nine diagnostic codes, exact field/evidence/reason
schemas, five-key stable ordering and equal-key stability, D0–D7 stop behavior,
same-stage multiplicity, no downstream consequence noise, and no host-path
leakage before any production behavior exists.

- [ ] **Step 3: Establish integration/equivalence RED**

Add controls for strict JSON/BOM/duplicate keys/key sets/runtime types, exact
selection order and count, source agreement, image present/missing/binding,
23-field raw candidates, source-map schema/bytes, 18-field Task 9A manifest,
same-member/separate/missing answers, atomic publication/cleanup, output
containment/conflict, deterministic roots/ZIP order/metadata, and golden Task
9A equivalence. The pre-production RED must already assert identical candidates,
issues, counts/status, duplicate classifications, adaptations, report, and
`preflight_sha256` between adapter output and the independently authored golden
package. It must also lock byte-identical candidate/source-map/manifest/raw/
image/package trees across different absolute roots, output/temp roots, ZIP
physical member orders, timestamps, and irrelevant container metadata, while
proving that semantic selection-array reorder changes output. D0 REDs must
assert every reason's exact logical `field` and exact canonical
`actual`/`expected`/`reason` evidence bytes from Design section 11.1, including
independently determinable same-stage multiplicity and the unchanged five-field
stable ordering; checking only the three-key schema or reason token is not a
valid D0 RED. The literal D0 oracle must independently cover JSON `1`, `1.0`,
`1e0`, `-0.0`, and `true` type tokens; strict `NaN`, `Infinity`, and `-Infinity`
rejection; top-level and nested absolute POSIX/UNC/drive-key opaque path
segments for both extra and duplicate keys; and the distinction between a
repeated valid image member and repeated individually invalid `bad.gif`
members.

- [ ] **Step 4: Validate all three RED groups before production**

```bash
$PY -m unittest -v tests.unit.test_mmd_archive
$PY -m unittest -v tests.unit.test_mmd_parser
$PY -m unittest -v tests.integration.test_mmd_adapter
```

Expected: all modules collect; no import/setup/fixture/environment ERROR; every
behavior failure reaches the deliberate adapter `NotImplementedError`. Record
counts and reasons separately. These are the complete B3–B8 behavior assertions;
B7 and B8 may only execute and inspect them, not add behavior tests after
production. Only after all three RED groups are valid may Task 5 edit production.

---

## Task 5: B3 inventory and archive-safety GREEN

**Files:**

- Create: `src/joy_m2/ingest/archive.py`
- Modify: `src/joy_m2/ingest/adapter.py`

- [ ] **Step 1: Implement D0 strict selection decoding**

In `adapter.py`, validate API `Path`/`PipelineConfig` types and output boundary,
then read the selection manifest as strict UTF-8 without BOM. Decode with a
duplicate-key-aware pairs hook, validate exact key sets and JSON runtime types,
convert in dataclass order, and collect exact D0 `source_contract_mismatch`
issues/evidence using only the exhaustive construction and collection rules in
Design section 11.1, without copying raw invalid bytes, decoder text, or host
facts and without touching `source_path`. Preserve the missing/nonregular/
unreadable selection-manifest exception boundary.

- [ ] **Step 2: Implement the exact source-kind decision**

In `archive.py`, after D0 only: validate missing/nonregular/unreadable source;
hash raw top-level bytes; apply `is_zipfile` first, then invalid `b"PK"`, then
exact `b"%PDF-"`, else plain MMD. Compare only approved actual kind and digest
facts. Do not infer from suffix.

- [ ] **Step 3: Implement ZIP metadata preflight (B1-A)**

Canonicalize raw names to NFC POSIX privately while retaining raw names for
access. Validate all members before content reads: absolute/drive/UNC,
backslash/traversal/dot/empty/escape, raw duplicate/NFC/casefold collisions,
hidden matrix, file types, symlink/special/executable, nested archives,
encryption/compression, inclusive 50/100/20/10 MiB limits, 256 members, 100:1
ratio, and selected primary/answer existence. Collect every independently
determinable same-stage issue in canonical order.

- [ ] **Step 4: Implement bounded integrity streaming (B1-B)**

Only after metadata passes, stream every regular member—including ignored OS
metadata and unselected images—to EOF under observed bounds to validate
decompression/CRC. Collect D2 failures and stop before semantic parsing.

- [ ] **Step 5: Implement selective reads (B1-C)**

Retain only selected primary/optional answer MMD and selected image bytes.
For plain MMD, consider only the explicit primary and explicitly referenced
adjacent resources beneath `source_path.parent`; do not recurse.

- [ ] **Step 6: Run archive GREEN without weakening later RED groups**

```bash
$PY -m unittest -v tests.unit.test_mmd_archive
$PY -m unittest -v tests.unit.test_mmd_parser
$PY -m unittest -v tests.integration.test_mmd_adapter
```

Expected: archive group PASS; parser/integration remain deliberate RED. Re-run
Task 9A and V1.18 gates.

---

## Task 6: B4 parser and immutable Source IR GREEN

**Files:**

- Create: `src/joy_m2/ingest/mmd_parser.py`
- Modify: `src/joy_m2/ingest/adapter.py`

- [ ] **Step 1: Implement only the five exact private frozen IR carriers**

Implement `_SourceMember`, `_SourceSpan`, `_SourceImageRef`, `_SourceQuestion`,
and `_SourceDocument` exactly as the Design specifies. Validate exact non-bool
indices/offsets, roles/languages, span containment, canonical member references,
and deterministic ordering. Do not expose them publicly or add a general AST.

- [ ] **Step 2: Implement the fixture-driven line/state parser**

Recognize only exact example 1–11 markers, exact `應試練習` state and Q1–Q6
forms, exact solution markers, approved itemize structures, display/inline math,
and lexically complete images. Preserve top-level complete questions and nested
subparts. Implement exact question/solution/answer boundaries and separate
answer occurrence grammar. Unknown or ambiguous syntax yields exact D3/D4
issues; never guess.

- [ ] **Step 3: Implement byte spans, fragments, and basic rendering**

Track half-open offsets against original UTF-8 bytes. Hash raw fragment bytes
without normalization. Render original/solution bytes with only CRLF/CR-to-LF.
Keep explanation spans empty for V1. Emit stable canonical member locators.

- [ ] **Step 4: Implement atomic-token and raw image-target safety**

Recognize complete math/structure/image tokens before prose. Enforce the exact
nine-reason ordered image-target safety list; unsafe complete targets emit only
D3 `archive_member_unsafe`; incomplete/unsupported tokens emit only
`mmd_parse_failed`.

- [ ] **Step 5: Run parser GREEN**

```bash
$PY -m unittest -v tests.unit.test_mmd_parser
$PY -m unittest -v tests.unit.test_mmd_archive
```

Expected: parser and archive groups PASS; integration remains RED only for
mapping/package behavior. Re-run Task 9A and V1.18 gates.

---

## Task 7: B5 selection, bilingual, provenance, and image mapping GREEN

**Files:**

- Modify: `src/joy_m2/ingest/adapter.py`
- Modify: `src/joy_m2/ingest/mmd_parser.py`

- [ ] **Step 1: Bind selections at D4 and count at D5**

For each selection, first match the exact `(kind, canonical number,
source-derived section)` triple without using selection position or parser
order as identity. One exact match binds and multiple exact matches emit
`selection_not_unique`. With zero exact matches, apply the Design's sole
counterfactual rule: only one occurrence matching exactly two fields and
differing in exactly one field may bind for that field's
`source_occurrence_mismatch`; otherwise emit zero-match
`selection_not_unique` and do not guess. Preserve manifest tuple order only as
candidate semantic output order. Validate local/separate answer mapping and
source occurrence agreement. Stop D5 after D4 failure; otherwise compare
complete parsed source occurrence count with `expected_candidate_count`.

- [ ] **Step 2: Implement the exact bilingual lexer/projection at D6**

Implement Han/Latin onset ranges, atomic shared tokens, whitespace/run ownership,
single same-line `en -> zh`, and both declared layouts. Prove source-ordered
text+image spans form a byte-complete non-overlapping partition. Render
`question_text_original` and the exact `zh + shared` projection without trim,
LaTeX rewrite, or invented translation.

- [ ] **Step 3: Map answer and explanation independently**

Source answer produces exact `solution_original`, empty `solution_verified`,
and `source_provided`; missing answer produces both empty solution fields and
`missing_from_source`. Explanation remains empty/`missing`/`None` because V1 has
no distinct explanation marker. Never use solution content as explanation and
never load historical AI answers.

- [ ] **Step 4: Bind image, metadata, and provenance at D7**

Resolve only exact `![](./images/<tail>)`; retain representable missing images
as candidate `image_paths` without staged bytes or fabricated digest. Enforce
explicit `expected_image_members`, candidate/source occurrence order, byte-
identical staging identity, explicit type/tags/difficulty, Task 9A evidence
locator wrapper, and the frozen `complete/incomplete` formula.

- [ ] **Step 5: Run mapping-focused GREEN**

Run parser and integration subsets for selection, bilingual, answer,
explanation, image, metadata, and provenance. All earlier archive/parser tests
must remain GREEN. Package/publication/equivalence tests may remain RED only at
the still-unimplemented B6 boundary.

---

## Task 8: B6 canonical package and atomic publication GREEN

**Files:**

- Modify: `src/joy_m2/ingest/adapter.py`

- [ ] **Step 1: Render exact raw candidate JSON**

Emit the 23 frozen caller-supplied Task 9A fields and no derived
`normalized_text_sha256`/`image_sha256s`. Use sorted-key compact UTF-8 JSON,
`ensure_ascii=False`, `allow_nan=False`, and one trailing LF.

- [ ] **Step 2: Render exact source map**

Emit exact top-level/member/question/span/image key sets and runtime types.
Members use primary-then-answer semantic order; questions use manifest order;
spans/images use source occurrence order. Use sorted-key compact UTF-8 JSON
without trailing LF. Exclude outer ZIP SHA, runtime roots, and missing-image
fake hashes.

- [ ] **Step 3: Stage exact raw evidence and image bytes**

Write `source/original.mmd.txt` once. Write `answers/answer.mmd.txt` only for a
separate selected answer member. Copy present selected images byte-for-byte in
first-reference order with one canonical file per path. Do not stage unselected
or absent images.

- [ ] **Step 4: Construct and serialize exact Task 9A manifest**

Build the exact frozen `BatchImportManifest`, six file groups, fixed policies,
path/SHA/size/kind evidence, and same-member/separate/missing answer semantics.
Serialize object fields in Task 9A dataclass order and evidence fields in
`relative_path,sha256,size_bytes,kind` order, compact UTF-8, no sorted object
keys, one trailing LF.

- [ ] **Step 5: Publish atomically**

Validate `output_dir` is a new descendant of `config.staging_root`; reject an
existing target. Build in a private sibling, fsync only if existing repository
convention requires it, rename atomically, and remove every temporary/partial
file after any failure. Return the exact `AdaptedImportPackage` with runtime
paths only in the carrier.

- [ ] **Step 6: Run unified Task 9B GREEN**

```bash
$PY -m unittest -v \
  tests.unit.test_mmd_adapter_models \
  tests.unit.test_mmd_archive \
  tests.unit.test_mmd_parser \
  tests.integration.test_mmd_adapter
```

Expected: all Task 9B focused tests PASS with zero skip/expectedFailure. Then
run Task 9A 41/41 and V1.18 validator.

---

## Task 9: B7 independent Task 9A golden equivalence

**Files:**

- No file changes. Execute the equivalence assertions established by the Task 4
  pre-production RED gate.

- [ ] **Step 1: Run adapter and golden packages independently**

Adapt the representative source under a temporary staging root. Separately
load the committed golden `import_manifest.json`. Pass each manifest/root to
unchanged `preflight_import` with the exact frozen V1.18 `ArtifactRef`.

- [ ] **Step 2: Assert complete semantic equivalence**

Assert exact equality of candidates, issues, counts/final status, duplicate
classifications, adaptations, report, and `preflight_sha256`. Also compare the
complete canonical package tree and exact bytes against the independently
authored golden package.

If an already-established equivalence assertion is RED, record that existing
focused RED and make only the minimum production correction inside the approved
four production files. Do not add or weaken a behavior test at B7.

- [ ] **Step 3: Prove Task 9A remained unchanged**

```bash
git diff --exit-code -- \
  src/joy_m2/ingest/models.py \
  src/joy_m2/ingest/manifest.py \
  src/joy_m2/ingest/preflight.py \
  tests/unit/test_ingest_models.py \
  tests/integration/test_ingest_preflight.py
$PY -m unittest -v tests.integration.test_ingest_preflight
```

Expected: no diff and 41/41 PASS.

---

## Task 10: B8 determinism, security, and full maintained gates

**Files:**

- No file changes. Execute the determinism, security, limits, diagnostics, and
  precedence assertions established by the Task 4 pre-production RED gate.

- [ ] **Step 1: Verify the pre-established determinism controls**

Run equivalent logical inputs under different absolute roots, output/temp
roots, ZIP physical member orders, timestamps, and irrelevant container
metadata. Assert identical candidate/source-map/manifest bytes, selected raw
bytes, image bytes, complete tree hashes, ArtifactRef facts, and Task 9A
preflight results. Reordering selection arrays must change semantic output.

- [ ] **Step 2: Execute every pre-established archive and path negative**

Provide deletion-sensitive controls for every Design matrix case and limit:
absolute/backslash/drive/UNC/traversal/dot/empty/escape, raw duplicate/NFC/
casefold collisions, hidden paths, symlink/special/executable, nested archive,
second MMD, encrypted/unsupported compression, structural/CRC/decompression,
50/100/20/10 MiB, 256 members, 100:1 ratio, missing selected members, and
ignore-after-validation OS metadata/unselected images.

- [ ] **Step 3: Verify the pre-established diagnostics and precedence controls**

Assert exactly nine Task 9B codes, exact field/evidence/reason schemas, five-key
stable ordering, equal-key stability, D0–D7 stop behavior, same-stage
multiplicity, no downstream consequence noise, no host path leaks, and exact
exception boundaries. For D0 specifically, reassert the literal logical fields,
canonical evidence bytes, value projections, multiplicity, and collection
prerequisites from Design section 11.1; no implementation-selected D0
`actual`/`expected` convention is permitted.

If any already-established B8 assertion is RED, record that existing focused
RED and make only the minimum production correction inside the approved four
production files. Do not first add, broaden, or weaken a behavior test at B8.

- [ ] **Step 4: Run full maintained gates**

Run fresh:

```bash
$PY -m unittest -v tests.unit.test_mmd_adapter_models tests.unit.test_mmd_archive tests.unit.test_mmd_parser tests.integration.test_mmd_adapter
$PY -m unittest -v tests.unit.test_ingest_models tests.integration.test_ingest_preflight
$PY -m unittest discover -v -s tests
$PY releases/V1.18/verify_task6_release.py releases/V1.18
git diff --check
```

Also run the currently approved Task 7, Task 8 equivalence, Release, and Task
3–6 legacy gates listed in `AGENTS.md`/`PROJECT_STATE.md`. Report exact current
counts; require zero skip and zero expectedFailure for maintained suites. Legacy
attribution may retain only its approved 9 PASS / 2 FAIL baseline categories.

- [ ] **Step 5: Verify frozen and scope boundaries**

Confirm V1.18 SHA/count, zero V1.19 artifacts/imports, no database writes, no
historical V1.16 ZIP access, no changes under `data/`, `releases/`, `legacy/`,
or unapproved production/test paths, and no CLI/package-public-surface change.

---

## Task 11: B9 final independent review and implementation checkpoint

**Files:**

- All changes must remain within the four production files, four test files,
  and previously committed approved fixture roots.

- [ ] **Step 1: Obtain final independent implementation review**

Review exact API/carriers, D0–D7, archive safety, parser/IR, bilingual mapping,
answer/explanation independence, images, provenance, canonical bytes, atomic
cleanup, golden equivalence, diagnostics, determinism, security, scope, and
frozen boundaries. Require zero Critical and zero Important findings; remediate
with valid RED and re-review as needed.

- [ ] **Step 2: Re-run fresh full gates after the final code change**

Repeat Task 9B focused, Task 9A 41/41, full maintained suite, Task 7, Task 8
equivalence, Release, Task 3–6 gates, V1.18 validator, `git diff --check`, scope,
staging, and frozen hashes. Do not rely on earlier output.

- [ ] **Step 3: Stage only the approved implementation checkpoint**

```bash
git add -- \
  src/joy_m2/ingest/adapter_models.py \
  src/joy_m2/ingest/archive.py \
  src/joy_m2/ingest/mmd_parser.py \
  src/joy_m2/ingest/adapter.py \
  tests/unit/test_mmd_adapter_models.py \
  tests/unit/test_mmd_archive.py \
  tests/unit/test_mmd_parser.py \
  tests/integration/test_mmd_adapter.py
git diff --cached --name-only
git diff --cached --check
```

The cached list must contain exactly these eight files. Fixture files must
already belong to the separate reviewed B1 commit.

- [ ] **Step 4: Commit and ordinary-push implementation**

```bash
git commit -m "feat: add deterministic Mathpix MMD adapter"
git diff-tree --check HEAD^ HEAD
git diff --check
git status --short
git push
```

Verify working tree/staging/untracked clean, local/upstream equality, and
ahead/behind `0/0`.

---

## Task 12: Close Task 9B and stop before Task 9C production

**Files:**

- Modify: `PROJECT_STATE.md`
- Create: `docs/reports/TASK9B_VERIFICATION.md`

- [ ] **Step 1: Record completion evidence**

Record Design/Plan/fixture/implementation commit SHAs, exact focused/full gate
counts, independent review, golden equivalence, frozen V1.18 SHA/count, zero
V1.19 artifacts/imports, ordinary push state, known legacy attribution only,
and no remaining Task 9B blocker.

- [ ] **Step 2: Independently review and commit docs-only closure**

Require exact scope and no reactivation of historical RED states. Commit with:

```bash
git add -- PROJECT_STATE.md docs/reports/TASK9B_VERIFICATION.md
git diff --cached --name-only
git diff --cached --check
git commit -m "docs: close Task 9B adapter checkpoint"
git diff-tree --check HEAD^ HEAD
git push
```

- [ ] **Step 3: Continue only to separately authorized Task 9C planning**

Task 9B closure grants no writer or promotion authority. Task 9C Design, Plan,
tests, in-memory/dry-run work, rollback design, and review may proceed under the
autonomy policy. Stop at HUMAN GATE B before the first real V1.19 candidate
database or formal write artifact. Task 9D real import remains behind the exact
digest-bound HUMAN GATE C, and promotion remains Gate D.
