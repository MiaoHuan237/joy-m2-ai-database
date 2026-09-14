# Task 10B HKDSE PP/MS PDF Source Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a source-specific, deterministic HKDSE M2 PP/MS PDF transcription-review adapter whose exact human-approved output can later enter the existing V1.20 canonical preflight without modifying any formal database.

**Architecture:** Strict source and extraction-pass loaders bind staging JSON to exact PP/MS PDF identities. Two independent proposal passes are compared without mathematical normalization, atomically published as a review artifact, and elevated to a verified carrier only through a separate digest-bound approval. A final bridge accepts only that verified carrier and writes the existing V1.20 canonical package shape under staging.

**Tech Stack:** Python 3.12, stdlib dataclasses/hashlib/json/pathlib/tempfile, `pypdf>=6.10,<7`, unittest, existing `PipelineConfig`, existing Task 9A carriers, existing Task 10A V1.20 carriers.

**Spec:** `docs/superpowers/specs/2026-09-14-task10b-hkdse-pdf-adapter-design.md`

## Global Constraints

- Support only `joy_m2_staging_batch_v1` plus explicitly SHA-bound HKDSE M2 PP/MS PDFs.
- Preserve one complete staging record per question; never split subparts.
- Machine extraction, layout OCR, and exact pass agreement remain proposal evidence.
- Never rewrite question text, formulas, official MS steps, marks, or figure labels.
- Approval is exactly `USER APPROVED PDF TRANSCRIPTION BATCH <batch_id> <transcription_digest>`.
- Transcription approval is not import approval and grants no database or release write.
- Formal V1.19/502 and frozen V1.18/497 remain byte-identical.
- No real V1.20 candidate, authoritative fingerprint, or Task 10A preflight occurs before the 2012 transcription gate.
- Real PDFs and generated pilot artifacts remain ignored staging/tmp content.

---

### Task 1: Dependency and exact public model contracts

**Files:**
- Modify: `pyproject.toml`
- Create: `src/joy_m2/ingest/hkdse_pdf_models.py`
- Modify: `src/joy_m2/ingest/__init__.py`
- Create: `tests/unit/test_hkdse_pdf_models.py`

**Interfaces:**
- Consumes: `PipelineError`, `V120AdaptedImportPackage`.
- Produces: the eight exact frozen Task 10B carriers and `HkdsePdfAdapterBlockedError`.

- [ ] **Step 1: Write exact carrier RED tests**

Create field-matrix tests using `dataclasses.fields`, `get_type_hints`, and
`FrozenInstanceError` for every carrier. Lock exact enum values, SHA syntax,
positive integer semantics, tuple copying/order, path relationships, derived
batch counts, issue ordering, and approval text.

```python
def test_page_span_rejects_bool_and_inverted_range(self):
    with self.assertRaises(PipelineError):
        HkdsePdfPageSpan(True, 2)
    with self.assertRaises(PipelineError):
        HkdsePdfPageSpan(3, 2)

def test_transcription_approval_binds_exact_statement(self):
    value = HkdsePdfTranscriptionApproval(
        "JOY-M2-HKDSE-2012-PP-MS",
        "a" * 64,
        "USER APPROVED PDF TRANSCRIPTION BATCH "
        "JOY-M2-HKDSE-2012-PP-MS " + "a" * 64,
    )
    self.assertEqual(value.transcription_digest, "a" * 64)
```

- [ ] **Step 2: Run model tests and verify RED**

Run:

```bash
python -m unittest -v tests.unit.test_hkdse_pdf_models
```

Expected: tests import successfully through an existence helper and fail only
because the Task 10B module/carriers are absent.

- [ ] **Step 3: Add the PDF dependency and minimal models**

Add exactly `pypdf>=6.10,<7` to project dependencies. Implement validation
helpers and the exact dataclasses from the Design. `HkdsePdfAdapterBlockedError`
stores an exact tuple of fatal `HkdsePdfTranscriptionIssue` values and uses the
fixed message `HKDSE PDF adapter blocked by source diagnostics`.

```python
class HkdsePdfAdapterBlockedError(PipelineError):
    def __init__(self, issues: tuple[HkdsePdfTranscriptionIssue, ...]):
        self.issues = tuple(sorted(issues, key=_issue_key))
        super().__init__("HKDSE PDF adapter blocked by source diagnostics")
```

- [ ] **Step 4: Export the approved append-only surface**

Append the carriers and five APIs to `joy_m2.ingest.__all__` without changing
the existing prefix order or exporting private helpers.

- [ ] **Step 5: Run model GREEN and existing public-surface regressions**

```bash
python -m unittest -v tests.unit.test_hkdse_pdf_models
python -m unittest -v tests.unit.test_ingest_models tests.unit.test_mmd_adapter_models tests.unit.test_v120_models
```

- [ ] **Step 6: Commit the model checkpoint**

```bash
git add pyproject.toml src/joy_m2/ingest/hkdse_pdf_models.py src/joy_m2/ingest/__init__.py tests/unit/test_hkdse_pdf_models.py
git commit -m "feat: add HKDSE PDF adapter contracts"
```

### Task 2: Strict staging, PDF, and extraction-pass loaders

**Files:**
- Create: `src/joy_m2/ingest/hkdse_pdf_adapter.py`
- Create: `tests/unit/test_hkdse_pdf_adapter.py`
- Create: `tests/fixtures/task10b/staging.json`
- Create: `tests/fixtures/task10b/pass-a.json`
- Create: `tests/fixtures/task10b/pass-b.json`

**Interfaces:**
- Consumes: exact Task 10B public carriers and `PipelineConfig`.
- Produces: strict private staging carrier, `load_hkdse_pdf_extraction_pass()`, and fatal source validation.

- [ ] **Step 1: Write loader RED tests**

Lock strict UTF-8, no BOM, finite JSON, duplicate-key rejection, exact keys,
exact runtime types, fixed staging policy values, unique record IDs, count and
mark closure, page bounds, source roles, PDF signature, exact SHA, exact page
count, regular files, and no output on failure.

```python
def test_pdf_sha_mismatch_blocks_before_output(self):
    with self.assertRaises(HkdsePdfAdapterBlockedError) as captured:
        propose_hkdse_pdf_transcription(
            self.staging, self.wrong_pp, self.ms,
            self.pass_a, self.pass_b, self.output, self.config,
        )
    self.assertEqual(captured.exception.issues[0].code, "pdf_identity_mismatch")
    self.assertFalse(self.output.exists())
```

- [ ] **Step 2: Run loader tests and verify RED**

```bash
python -m unittest -v tests.unit.test_hkdse_pdf_adapter.HkdsePdfSourceValidationTests
```

Expected: valid fixtures load far enough to call the absent strict loader;
negative controls fail because source validation is not implemented.

- [ ] **Step 3: Implement strict decoding and source preflight**

Use `object_pairs_hook` to preserve duplicate-key evidence. Hash files by
streaming chunks, validate `%PDF-`, and use `pypdf.PdfReader` only after SHA
binding. Construct all fatal issues without absolute paths in evidence.

```python
def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()
```

- [ ] **Step 4: Implement exact extraction-pass loader**

Decode `task10b-hkdse-pdf-extraction-pass-v1`, validate exact top/record keys,
construct typed records, enforce A/B pass IDs at the proposal boundary, and
reject extra/missing/duplicate IDs before comparison.

- [ ] **Step 5: Run loader GREEN and diff checks**

```bash
python -m unittest -v tests.unit.test_hkdse_pdf_adapter.HkdsePdfSourceValidationTests
git diff --check
```

- [ ] **Step 6: Commit loader checkpoint**

```bash
git add src/joy_m2/ingest/hkdse_pdf_adapter.py tests/unit/test_hkdse_pdf_adapter.py tests/fixtures/task10b
git commit -m "feat: validate HKDSE PDF source evidence"
```

### Task 3: Embedded-text extraction pass

**Files:**
- Modify: `src/joy_m2/ingest/hkdse_pdf_adapter.py`
- Modify: `tests/unit/test_hkdse_pdf_adapter.py`

**Interfaces:**
- Consumes: verified staging/PDF preflight.
- Produces: `extract_hkdse_pdf_embedded_pass(...) -> HkdsePdfExtractionPass` and canonical pass JSON.

- [ ] **Step 1: Write embedded extraction RED tests**

Create tiny PDFs in test temporary roots with `pypdf.PdfWriter`. Lock declared
page-only reads, deterministic semantic order, empty output when safe
question-local segmentation is unavailable, staging-bound page spans, atomic
no-replace output, and path-independent canonical bytes.

```python
def test_embedded_pass_never_assigns_shared_page_text_to_two_questions(self):
    result = extract_hkdse_pdf_embedded_pass(
        self.shared_page_staging, self.pp, self.ms,
        "A", self.output, self.config,
    )
    self.assertEqual(
        tuple(record.question_text_original for record in result.records),
        ("", ""),
    )
```

- [ ] **Step 2: Run extraction tests and verify RED**

```bash
python -m unittest -v tests.unit.test_hkdse_pdf_adapter.HkdsePdfEmbeddedExtractionTests
```

Expected: failures identify the missing embedded extraction API/behavior.

- [ ] **Step 3: Implement conservative embedded extraction**

Extract text only when one staging record uniquely owns the declared page
span. Preserve returned text exactly, except pypdf's decoded string boundary.
Do not trim, normalize, segment heuristically, infer subparts, or invent figure
references. Record empty text for ambiguous shared pages.

- [ ] **Step 4: Publish canonical pass JSON atomically**

Write canonical UTF-8 JSON plus one LF through an owned temporary sibling and
no-replace rename. Return the typed pass only after reopening and exact
round-trip validation.

- [ ] **Step 5: Run extraction GREEN**

```bash
python -m unittest -v tests.unit.test_hkdse_pdf_adapter.HkdsePdfEmbeddedExtractionTests
```

- [ ] **Step 6: Commit extraction checkpoint**

```bash
git add src/joy_m2/ingest/hkdse_pdf_adapter.py tests/unit/test_hkdse_pdf_adapter.py
git commit -m "feat: extract conservative HKDSE PDF text passes"
```

### Task 4: Two-pass comparison, digest, and review artifacts

**Files:**
- Modify: `src/joy_m2/ingest/hkdse_pdf_adapter.py`
- Modify: `tests/unit/test_hkdse_pdf_adapter.py`
- Create: `tests/integration/test_hkdse_pdf_adapter.py`

**Interfaces:**
- Consumes: verified staging/PDF source plus exact A/B pass files.
- Produces: `propose_hkdse_pdf_transcription(...) -> HkdsePdfTranscriptionBatch`.

- [ ] **Step 1: Write comparison and issue RED tests**

Lock exact agreement, missing text/MS, question/MS text mismatches, subpart,
mark, figure, formula, and page-boundary issues. Prove stable issue ordering and
that no formula normalization converts a mismatch into agreement.

```python
def test_minus_sign_disagreement_requires_formula_review(self):
    batch = self.propose(question_a="x - 1", question_b="x − 1")
    self.assertEqual(batch.records[0].status, "REVIEW_REQUIRED")
    self.assertIn("formula_mismatch", tuple(issue.code for issue in batch.issues))
```

- [ ] **Step 2: Write review/digest/determinism RED tests**

Lock exact four-file output, canonical JSON plus LF, digest reconstruction,
absence of absolute/temp paths and runtime metadata, compact report sections,
metrics, output conflict, cleanup, and byte equality across two roots.

```python
def test_equivalent_roots_produce_identical_semantic_artifacts(self):
    first = self.propose_at(self.root_a)
    second = self.propose_at(self.root_b)
    self.assertEqual(first.transcription_digest, second.transcription_digest)
    self.assertEqual(first.transcription_path.read_bytes(), second.transcription_path.read_bytes())
```

- [ ] **Step 3: Run both RED groups before production changes**

```bash
python -m unittest -v \
  tests.unit.test_hkdse_pdf_adapter.HkdsePdfComparisonTests \
  tests.integration.test_hkdse_pdf_adapter.HkdsePdfProposalIntegrationTests
```

Expected: both groups fail only because proposal comparison/publication is
absent.

- [ ] **Step 4: Implement exact comparison and canonical semantic payload**

Compare raw strings and ordered tuples. Use pass A as the displayed proposal
only while retaining pass B in copied pass artifacts and explicit issues.
Compute the digest from the exact semantic payload before adding the digest
field. Derive metrics from frozen records/issues.

- [ ] **Step 5: Implement atomic artifacts and compact Markdown report**

Validate all inputs before creating the output. Write the four approved files
in a private sibling, fsync file content when practical, then publish with
no-replace rename. Remove only the owned private tree on failure.

- [ ] **Step 6: Run unified proposal GREEN**

```bash
python -m unittest -v \
  tests.unit.test_hkdse_pdf_adapter.HkdsePdfComparisonTests \
  tests.integration.test_hkdse_pdf_adapter.HkdsePdfProposalIntegrationTests
git diff --check
```

- [ ] **Step 7: Commit proposal checkpoint**

```bash
git add src/joy_m2/ingest/hkdse_pdf_adapter.py tests/unit/test_hkdse_pdf_adapter.py tests/integration/test_hkdse_pdf_adapter.py
git commit -m "feat: add deterministic PDF transcription review"
```

### Task 5: Transcription approval gate

**Files:**
- Modify: `src/joy_m2/ingest/hkdse_pdf_adapter.py`
- Modify: `tests/unit/test_hkdse_pdf_adapter.py`

**Interfaces:**
- Consumes: exact proposal and exact approval.
- Produces: `approve_hkdse_pdf_transcription(...) -> VerifiedHkdsePdfTranscriptionBatch`.

- [ ] **Step 1: Write gate RED tests**

Lock correct approval success and rejection for wrong batch, digest, statement,
parallel carrier, altered record, any issue, any `REVIEW_REQUIRED` record, and
caller-constructed invalid envelope. Prove extraction cannot emit `VERIFIED`.

```python
def test_review_required_proposal_cannot_be_approved(self):
    proposal = self.review_required_proposal()
    approval = self.approval_for(proposal)
    with self.assertRaises(PipelineError):
        approve_hkdse_pdf_transcription(proposal, approval)
```

- [ ] **Step 2: Run gate tests and verify RED**

```bash
python -m unittest -v tests.unit.test_hkdse_pdf_adapter.HkdsePdfApprovalTests
```

- [ ] **Step 3: Implement minimal non-bypass approval**

Reconstruct the proposal semantic payload, verify its digest, require zero
issues/all `PROPOSED`, validate exact approval identity, and return copied
records with only `status` changed to `VERIFIED`. Do no file I/O.

- [ ] **Step 4: Run approval GREEN and proposal regressions**

```bash
python -m unittest -v tests.unit.test_hkdse_pdf_adapter tests.integration.test_hkdse_pdf_adapter
```

- [ ] **Step 5: Commit approval checkpoint**

```bash
git add src/joy_m2/ingest/hkdse_pdf_adapter.py tests/unit/test_hkdse_pdf_adapter.py
git commit -m "feat: gate HKDSE PDF transcription approval"
```

### Task 6: Verified V1.20 canonical bridge

**Files:**
- Modify: `src/joy_m2/ingest/hkdse_pdf_adapter.py`
- Modify: `tests/integration/test_hkdse_pdf_adapter.py`

**Interfaces:**
- Consumes: exact `VerifiedHkdsePdfTranscriptionBatch`.
- Produces: `adapt_verified_hkdse_pdf_transcription_v120(...) -> V120AdaptedImportPackage`.

- [ ] **Step 1: Write bridge RED tests**

Lock exact verified-only input, V1.20 manifest fields, candidate order and
23-field payload, complete-question preservation, official-MS provenance,
taxonomy proposal status, source/transcription/source-map/answer evidence,
path independence, atomic no-replace output, and absence of DB reads/writes.

```python
def test_unapproved_proposal_cannot_reach_v120_package(self):
    with self.assertRaises(TypeError):
        adapt_verified_hkdse_pdf_transcription_v120(
            self.proposal, self.output, self.config
        )
```

- [ ] **Step 2: Run bridge tests and verify RED**

```bash
python -m unittest -v tests.integration.test_hkdse_pdf_adapter.HkdsePdfCanonicalBridgeTests
```

- [ ] **Step 3: Implement minimal canonical projection**

Create canonical candidate JSON, transcription evidence, source map, official
MS file, and exact `V120BatchImportManifest`. Candidate text and MS bytes come
only from verified records. Do not query a database or classify duplicates.

- [ ] **Step 4: Implement atomic package publication**

Use the existing staging containment and no-replace pattern. Reopen with
`load_v120_import_manifest()` before returning the exact package carrier.

- [ ] **Step 5: Run bridge and Task 10A package GREEN**

```bash
python -m unittest -v \
  tests.integration.test_hkdse_pdf_adapter.HkdsePdfCanonicalBridgeTests \
  tests.integration.test_v120_adapter_projection \
  tests.integration.test_v120_preflight
```

- [ ] **Step 6: Commit bridge checkpoint**

```bash
git add src/joy_m2/ingest/hkdse_pdf_adapter.py tests/integration/test_hkdse_pdf_adapter.py
git commit -m "feat: bridge approved PDF transcription to V1.20"
```

### Task 7: Full verification, review, docs, and 2012 real pilot

**Files:**
- Create: `docs/reports/TASK10B_VERIFICATION.md`
- Modify: `PROJECT_STATE.md`
- Real ignored output: `data/staging/task10b-hkdse-2012/**`
- Temporary ignored renders/OCR proposals: `tmp/task10b-hkdse-2012/**`

**Interfaces:**
- Consumes: committed Task 10B code and exact 2012 staging/PP/MS inputs.
- Produces: verified engineering checkpoint plus non-authoritative 2012 transcription-review artifacts.

- [ ] **Step 1: Run complete focused and maintained suites**

Use the bundled Python 3.12 runtime when `python` is unavailable.

```bash
python -m unittest -v \
  tests.unit.test_hkdse_pdf_models \
  tests.unit.test_hkdse_pdf_adapter \
  tests.integration.test_hkdse_pdf_adapter
python -m unittest discover -v -s tests
python releases/V1.18/verify_task6_release.py releases/V1.18
```

Run the formal V1.19 verifier command recorded in
`docs/reports/TASK10A_VERIFICATION.md`, then verify exact 502 count and formal
SQLite SHA. Require zero skips and zero expected failures in maintained tests.

- [ ] **Step 2: Independent implementation review and remediation**

Review exact source scope, SHA/page binding, formula fidelity, pass
independence, issue closure, digest reconstruction, gate non-bypass,
determinism, atomic cleanup, canonical bridge, and zero-write safety. Remediate
every Critical/Important finding with a failing regression test before code.
Repeat review until Critical 0 / Important 0.

- [ ] **Step 3: Commit implementation verification**

Record commands/counts, RED evidence, review findings, source-boundary proof,
and frozen hashes in `TASK10B_VERIFICATION.md`. Update `PROJECT_STATE.md` to
state implementation complete but 2012 transcription awaiting human review.

```bash
git add PROJECT_STATE.md docs/reports/TASK10B_VERIFICATION.md
git commit -m "docs: record Task 10B implementation verification"
git push
```

- [ ] **Step 4: Create 2012 pass A**

Run `extract_hkdse_pdf_embedded_pass()` against the exact 2012 staging, PP, and
MS source paths. Keep the output below
`data/staging/task10b-hkdse-2012/input-passes/`.

- [ ] **Step 5: Create independent 2012 pass B**

Render only declared 2012 pages. Use the available layout/OCR/visual route to
create exact pass-B JSON. Never infer unreadable mathematics; leave uncertain
fields empty or preserve alternatives as review evidence. Bind exact staging,
PP, and MS SHA values.

- [ ] **Step 6: Generate the real 2012 review proposal**

Call `propose_hkdse_pdf_transcription()` with the exact A/B pass files and
output `data/staging/task10b-hkdse-2012/review`. Re-hash V1.18/V1.19, verify
497/502 counts, prove `releases/V1.20/` absent, and inspect the report and full
transcription artifact.

- [ ] **Step 7: Stop at the transcription human gate**

Report exact metrics, source SHA values, transcription digest, report and full
artifact paths, maintained/frozen gates, and any review reasons. Do not call
the approval API, canonical bridge, Task 10A preflight, writer, or release API.

Required status:

```text
USER DECISION REQUIRED — PDF TRANSCRIPTION REVIEW
```

