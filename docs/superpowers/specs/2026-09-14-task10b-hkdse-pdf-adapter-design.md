# Task 10B HKDSE PP/MS PDF Source Adapter Design

Status: APPROVED FOR AUTONOMOUS IMPLEMENTATION

Date: 2026-09-14 (Asia/Shanghai)

## 1. Purpose

Task 10B adds one source-specific, append-only adapter for verified HKDSE M2
Question Paper and Marking Scheme PDFs described by
`joy_m2_staging_batch_v1`. It turns machine extraction proposals into a
deterministic transcription-review artifact. Only an exact, separately
approved transcription may be projected into the existing V1.20 canonical
package and Task 10A preflight.

The authority chain is:

```text
verified staging bytes + verified PP/MS PDF bytes
-> extraction pass A + independent extraction pass B
-> deterministic comparison and review proposal
-> USER APPROVED PDF TRANSCRIPTION BATCH
-> verified transcription
-> existing V1.20 canonical package
-> Task 10A preflight
-> later USER APPROVED IMPORT BATCH gate
```

Machine extraction, OCR, layout analysis, and an `AUTO-AGREE` comparison are
never database authority by themselves.

## 2. Frozen formal authority

- Current formal release is V1.19 with 502 complete questions.
- Formal V1.19 SQLite SHA-256 is
  `5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff`.
- V1.18 remains byte-frozen at 497 complete questions with SQLite SHA-256
  `fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7`.
- No formal V1.20 release exists.
- Task 9A, Task 9B MMD, Task 9C, Task 9D, and Task 10A contracts remain
  unchanged.
- Task 10B creates no database and no `releases/V1.20/` artifact.

## 3. Supported input and non-goals

V1 accepts exactly:

1. a strict `joy_m2_staging_batch_v1` JSON object;
2. one HKDSE M2 PP PDF whose SHA-256 and page count equal the staging
   declaration;
3. one HKDSE M2 MS PDF whose SHA-256 and page count equal the staging
   declaration;
4. two exact extraction-pass JSON artifacts bound to the same three source
   digests.

The staging file provides proposal anchors only: year, section, question
number, marks, PP/MS page spans, taxonomy proposals, and provenance. One
staging row remains one complete question; subparts are never split into
database records.

V1 does not implement generic PDF ingestion, arbitrary document OCR,
handwriting OCR, textbook parsing, question generation, mathematical
correction, database writing, promotion, or a plugin/workflow framework.

## 4. Extraction boundary

Extraction is deliberately separated from authority establishment.

- `embedded_text` is the first route. The adapter can create an extraction
  pass by reading only declared page spans from the verified PDFs.
- `layout_ocr` is permitted only for pages whose embedded layer is
  insufficient. Its output enters through the same strict pass schema.
- `visual_review` is an allowed independent proposal method for an operator or
  review tool inspecting rendered source pages.
- An extraction pass is untrusted proposal data even when it is complete.
- Absolute paths, temporary roots, executable names, timestamps, OCR runtime
  versions, confidence scores, and physical filesystem discovery order do not
  enter semantic identity.

The maintained adapter does not embed a generic OCR engine. Layout/OCR tools
produce an exact Task 10B pass JSON; the adapter validates its source binding,
structure, and content before comparison. This keeps OCR replaceable and
prevents an OCR runtime from becoming authority.

## 5. Public models

All carriers are exact frozen dataclasses with no defaults.

```python
@dataclass(frozen=True)
class HkdsePdfPageSpan:
    start_page: int
    end_page: int

@dataclass(frozen=True)
class HkdsePdfExtractionRecord:
    staging_id: str
    question_pages: HkdsePdfPageSpan
    ms_pages: HkdsePdfPageSpan
    question_text_original: str
    official_ms_original: str
    subparts: tuple[str, ...]
    marks: int
    figure_references: tuple[str, ...]
    question_method: str
    ms_method: str

@dataclass(frozen=True)
class HkdsePdfExtractionPass:
    pass_id: str
    staging_sha256: str
    pp_sha256: str
    ms_sha256: str
    records: tuple[HkdsePdfExtractionRecord, ...]

@dataclass(frozen=True)
class HkdsePdfTranscriptionIssue:
    code: str
    severity: str
    staging_id: str | None
    field: str
    evidence: str

@dataclass(frozen=True)
class HkdsePdfTranscriptionRecord:
    staging_id: str
    year: int
    section: str
    question_number: int
    question_pages: HkdsePdfPageSpan
    ms_pages: HkdsePdfPageSpan
    question_text_original: str
    official_ms_original: str
    subparts: tuple[str, ...]
    marks: int
    figure_references: tuple[str, ...]
    question_methods: tuple[str, ...]
    ms_methods: tuple[str, ...]
    status: str
    review_reasons: tuple[str, ...]
    module_proposal: str
    topic_proposal: str
    difficulty_proposal: int
    tag_proposals: tuple[str, ...]

@dataclass(frozen=True)
class HkdsePdfTranscriptionBatch:
    batch_id: str
    staging_sha256: str
    pp_sha256: str
    ms_sha256: str
    records: tuple[HkdsePdfTranscriptionRecord, ...]
    issues: tuple[HkdsePdfTranscriptionIssue, ...]
    transcription_digest: str
    artifact_root: Path
    transcription_path: Path
    review_path: Path

@dataclass(frozen=True)
class HkdsePdfTranscriptionApproval:
    batch_id: str
    transcription_digest: str
    approval_text: str

@dataclass(frozen=True)
class VerifiedHkdsePdfTranscriptionBatch:
    proposal: HkdsePdfTranscriptionBatch
    approval: HkdsePdfTranscriptionApproval
    records: tuple[HkdsePdfTranscriptionRecord, ...]
```

`HkdsePdfTranscriptionBatch` exposes derived read-only count properties for
`total_questions`, `auto_agree_count`, `review_required_count`,
`question_complete_count`, `ms_complete_count`, `figure_question_count`,
`formula_mismatch_count`, `page_boundary_ambiguity_count`, and
`missing_content_count`. These values are derived from the frozen records and
issues and are not caller-controlled authority fields.

## 6. Exact model validation

- Page numbers and question numbers are exact positive integers; `bool` is
  rejected. Page spans are inclusive and `start_page <= end_page`.
- `pass_id` is exactly `A` or `B`.
- Extraction methods are exactly `embedded_text`, `layout_ocr`, or
  `visual_review`.
- Record status is exactly `PROPOSED`, `VERIFIED`, or `REVIEW_REQUIRED`.
- Extraction records preserve strings byte-for-byte after strict UTF-8 JSON
  decoding. The adapter performs no Unicode normalization, whitespace
  collapse, trimming, mathematical rewriting, or LaTeX rewriting.
- Tuple-valued inputs accept only list/tuple, copy into independent tuples,
  preserve semantic order, and reject wrong element types.
- SHA fields are lowercase 64-hex digests.
- `evidence` is canonical JSON without absolute paths.
- Extraction-pass staging IDs are exact, unique, and in staging manifest
  semantic order.
- The final issue order uses stable sorting by
  `(staging_id or "", code, field, evidence)`.

## 7. Strict staging and PDF validation

The loader rejects malformed JSON, duplicate keys, wrong/extra fields, wrong
runtime types, wrong fixed values, duplicate staging IDs, count/mark closure
failure, invalid page spans, and any source declaration inconsistent with the
record set.

Before any output directory is created, the adapter verifies:

- staging SHA-256;
- PDF `%PDF-` signature and regular-file status;
- PP/MS SHA-256 against the staging declarations;
- PP/MS page counts against the staging declarations;
- every declared PP/MS page span is inside its PDF;
- the two extraction passes bind the same staging/PP/MS digests;
- pass record identity and order equal staging;
- every pass page span stays inside the bound PDF.

Staging page spans and marks are proposal anchors, not fatal identity. A pass
page-span or mark disagreement with staging or the other pass remains
representable as `page_boundary_ambiguity` or `mark_mismatch` in the review
batch. It must not be rejected before comparison.

Fatal source/contract errors raise `HkdsePdfAdapterBlockedError` and produce no
output. Reviewable transcription discrepancies remain structured issues in a
review batch.

## 8. Issue taxonomy

Exact issue codes are:

```text
staging_contract_mismatch
pdf_identity_mismatch
pdf_page_mismatch
extraction_pass_invalid
question_text_missing
official_ms_missing
question_text_mismatch
official_ms_mismatch
subpart_mismatch
mark_mismatch
figure_mismatch
formula_mismatch
page_boundary_ambiguity
```

The first four are fatal `blocking` diagnostics. The remaining nine have
severity `review_required` and are included in the transcription artifact and
review report. There is no warning channel and no silent repair.

## 9. Two-pass comparison

For each staging row, the adapter compares pass A with pass B using exact
stored strings and ordered tuples. Newline representation in JSON is decoded
normally, but no further normalization is allowed.

A record is `PROPOSED` only when:

- question text and official MS text are both non-empty;
- question text, official MS text, subparts, marks, figures, and page spans
  agree exactly across passes;
- pass marks equal the staging mark allocation;
- no review issue exists for the record.

Otherwise it is `REVIEW_REQUIRED`. Text mismatch involving mathematical signal
characters additionally emits `formula_mismatch`; the adapter never chooses
the more plausible formula. Pass A is displayed as the proposed transcription
while the report separately shows pass B and the exact discrepancy reasons.

`VERIFIED` is never emitted by extraction or comparison. It is created only by
the exact approval boundary after every record is `PROPOSED`.

## 10. Figures

Figure references are explicit ordered source locators such as
`pp:<sha256>#page=8#region=figure-1`. They bind the verified source PDF and page
without copying a large page render into Git. A pass disagreement, missing
declared figure, or uncertain boundary emits `figure_mismatch` or
`page_boundary_ambiguity`. Task 10B does not redraw or synthesize figures.

Later canonical projection may stage a reviewed crop only when its exact bytes
are present and bound; V1 does not infer a crop from OCR output.

## 11. Transcription artifact and digest

The proposal operation atomically creates exactly:

```text
<output_dir>/transcription.json
<output_dir>/extraction-pass-a.json
<output_dir>/extraction-pass-b.json
<output_dir>/PDF_TRANSCRIPTION_REVIEW.md
```

The two pass files are canonical copies, not path references. The transcription
artifact contains exact fixed key order-independent canonical JSON plus one LF.
Its semantic payload includes schema version
`task10b-hkdse-pdf-transcription-v1`, batch ID, all three source digests,
records, and ordered issues. It excludes artifact paths and runtime metadata.
`transcription_digest` is SHA-256 of the canonical semantic payload before the
digest field is added. Rebuilding under another approved staging root produces
identical artifact bytes and digest.

The review report shows batch metrics and one compact section per question:
year/question, PP/MS pages, question preview, subparts, marks, MS preview/step
summary, methods, agreement status, figure status, taxonomy proposals, and
review reasons. Full text remains in `transcription.json`.

## 12. Approval boundary

The exact approval syntax is:

```text
USER APPROVED PDF TRANSCRIPTION BATCH <batch_id> <transcription_digest>
```

`approve_hkdse_pdf_transcription()` requires exact batch/digest/statement
binding and rejects any proposal with a `REVIEW_REQUIRED` record or any issue.
It returns a new frozen verified carrier whose copied records have status
`VERIFIED`. It does not edit the proposal artifacts.

Changing the staging bytes, either PDF, either pass, any transcription text,
mapping, marks, figure references, taxonomy proposal, or issue list changes
the digest and invalidates the approval.

This approval is not `USER APPROVED IMPORT BATCH`; it grants no database write
or promotion authority.

## 13. Public API

The append-only root package surface adds exactly:

```python
def extract_hkdse_pdf_embedded_pass(
    staging_manifest_path: Path,
    pp_pdf_path: Path,
    ms_pdf_path: Path,
    pass_id: str,
    output_path: Path,
    config: PipelineConfig,
) -> HkdsePdfExtractionPass

def load_hkdse_pdf_extraction_pass(path: Path) -> HkdsePdfExtractionPass

def propose_hkdse_pdf_transcription(
    staging_manifest_path: Path,
    pp_pdf_path: Path,
    ms_pdf_path: Path,
    pass_a_path: Path,
    pass_b_path: Path,
    output_dir: Path,
    config: PipelineConfig,
) -> HkdsePdfTranscriptionBatch

def approve_hkdse_pdf_transcription(
    proposal: HkdsePdfTranscriptionBatch,
    approval: HkdsePdfTranscriptionApproval,
) -> VerifiedHkdsePdfTranscriptionBatch

def adapt_verified_hkdse_pdf_transcription_v120(
    verified: VerifiedHkdsePdfTranscriptionBatch,
    output_dir: Path,
    config: PipelineConfig,
) -> V120AdaptedImportPackage
```

No raw OCR text can be passed directly to approval or canonical projection.
The bridge accepts only an exact verified carrier produced by the approval API.

## 14. Embedded extraction

The embedded extractor reads only declared page spans from already verified
PDFs through `pypdf`. It records full page-layer text as proposal material.
When a page contains more than one staging question and deterministic
question-local segmentation is unavailable, it leaves that record text empty
and marks the page boundary as ambiguous rather than assigning another
question's content. The MS side follows the same rule.

`pypdf>=6.10,<7` is the only new Python dependency. It is required for strict
page-count validation and embedded-layer extraction; OCR remains outside the
package dependency graph.

## 15. V1.20 canonical bridge

The bridge creates the existing `task10-v120-import-manifest-v1` package
atomically inside `PipelineConfig.staging_root`:

```text
import_manifest.json
records/candidates.json
source/transcription.json
source/source-map.json
answers/official-ms.json
```

Candidate order equals staging record order. Each candidate preserves the
complete approved question in `question_text_original`, the official MS in
`solution_original`, `answer_status="source_provided"`, source-derived Chinese
as `question_text_zh` with `translation_status="source_present"`, and no
invented explanation. `source_fragment_hash` is SHA-256 of the exact approved
question UTF-8 bytes. Taxonomy remains `proposed`. Figures remain explicit
source references unless reviewed crop bytes are separately supplied; missing
canonical image bytes keep the candidate incomplete rather than fabricating an
image.

The source map binds staging/PP/MS/transcription digests, question/page/MS
mapping, and the approved transcription digest. It contains no absolute path.
The bridge never queries a database and never computes duplicate status. Task
10A preflight remains the sole effective-state fingerprint/collision authority.

## 16. Atomicity and safety

- All outputs must be strict staging descendants and must not already exist.
- Inputs and outputs may not overlap.
- Symlinked output ancestors and non-regular inputs are rejected.
- Source identity validation precedes any output creation.
- Publication uses a private sibling temporary directory and no-replace rename;
  failure removes only the owned temporary directory.
- No `extractall()`, PDF mutation, database write, formal release write, or
  source-file rewrite is allowed.

## 17. Pilot and human gate

The implementation supports 2012-2014, but the first real run processes only
2012 (14 questions). It generates extraction proposals and a review batch,
then stops with:

```text
USER DECISION REQUIRED — PDF TRANSCRIPTION REVIEW
```

The report must include question/MS completion, auto-agree,
review-required, formula mismatch, figure, missing-content counts, source
digests, transcription digest, artifact paths, maintained tests, and frozen
V1.18/V1.19 verification.

No real canonical package, authoritative fingerprint, Task 10A preflight,
candidate database, or release is created before the exact transcription
approval. After a later approval, Task 10A preflight must bind the then-current
V1.20 effective parent; a changed parent requires a fresh preflight but not new
OCR.

## 18. Approved file scope

Task 10B may modify only:

```text
pyproject.toml
PROJECT_STATE.md
docs/superpowers/specs/2026-09-14-task10b-hkdse-pdf-adapter-design.md
docs/superpowers/plans/2026-09-14-task10b-hkdse-pdf-adapter.md
docs/reports/TASK10B_VERIFICATION.md
src/joy_m2/ingest/__init__.py
src/joy_m2/ingest/hkdse_pdf_models.py
src/joy_m2/ingest/hkdse_pdf_adapter.py
tests/unit/test_hkdse_pdf_models.py
tests/unit/test_hkdse_pdf_adapter.py
tests/integration/test_hkdse_pdf_adapter.py
tests/fixtures/task10b/**
```

Real PDFs, rendered pages, OCR output, extraction passes, transcription review
artifacts, and canonical pilot output remain ignored staging/tmp data and are
never committed.

## 19. TDD and verification

RED groups are established before the corresponding production behavior:

1. exact public models and package-surface RED;
2. strict staging/PDF/pass validation RED;
3. two-pass comparison, issue ordering, digest, and review artifact RED;
4. approval-gate RED;
5. approved canonical bridge RED;
6. determinism, atomicity, and no-write RED.

Each RED must fail for missing Task 10B behavior, not syntax, import, setup, or
fixture error. Focused GREEN is followed by maintained Task 9A, Task 9B, Task
9C, Task 9D, Task 10A, V1.18 validator, formal V1.19 verifier, and diff checks.

Independent review requires Critical 0 and Important 0 for source fidelity,
PP/MS provenance, digest closure, gate non-bypass, deterministic output,
frozen-data preservation, and scope containment.

## 20. Decision register

- Source scope: APPROVED - HKDSE M2 PP/MS plus `joy_m2_staging_batch_v1` only.
- Extraction authority: APPROVED - all machine output remains proposal data.
- OCR dependency: APPROVED - external exact pass artifact; no generic OCR
  runtime in maintained dependencies.
- Embedded PDF dependency: APPROVED - `pypdf>=6.10,<7` only.
- Two-pass comparison: APPROVED - exact comparison, conservative review route.
- Figure evidence: APPROVED - explicit PDF/page locator; no redraw or synthesis.
- Transcription approval: APPROVED - separate exact batch/digest statement.
- Canonical bridge: APPROVED - verified carrier only, existing V1.20 manifest.
- Pilot: APPROVED - 2012 first, stop before canonicalization.
- Database/release mutation: FORBIDDEN.
