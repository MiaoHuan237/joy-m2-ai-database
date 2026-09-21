"""Source-specific HKDSE M2 PP/MS PDF transcription adapter."""

from __future__ import annotations

from dataclasses import dataclass, replace
import errno
import hashlib
import io
import json
import os
from pathlib import Path
import re
import shutil
import stat
import tempfile

from pypdf import PdfReader

from joy_m2.config import PipelineConfig
from joy_m2.errors import ConfigurationError, OutputConflictError, PipelineError
from joy_m2.ingest.hkdse_pdf_models import (
    HkdsePdfAdapterBlockedError,
    HkdsePdfExtractionPass,
    HkdsePdfExtractionRecord,
    HkdsePdfPageSpan,
    HkdsePdfTranscriptionBatch,
    HkdsePdfTranscriptionApproval,
    HkdsePdfTranscriptionIssue,
    HkdsePdfTranscriptionRecord,
    VerifiedHkdsePdfTranscriptionBatch,
)
from joy_m2.ingest.writer_profiles import atomic_rename_no_replace
from joy_m2.ingest.models import ImportFileEvidence
from joy_m2.ingest.v120_manifest import load_v120_import_manifest
from joy_m2.ingest.v120_models import V120AdaptedImportPackage, V120BatchImportManifest
from joy_m2.ingest.v121_manifest import load_v121_import_manifest
from joy_m2.ingest.v121_models import V121AdaptedImportPackage, V121BatchImportManifest


_SHA256 = re.compile(r"[0-9a-f]{64}")
_STAGING_TOP = (
    "schema",
    "batch_id",
    "created_utc",
    "status",
    "database_release_target",
    "source_pair",
    "capture_policy",
    "dedup_policy",
    "summary",
    "records",
    "formal_import_performed",
)
_SOURCE_PAIR = ("pp", "ms")
_SOURCE = (
    "role",
    "file_name",
    "library_file_id",
    "sha256",
    "page_count",
    "original_file_retained",
    "content_layer",
    "ocr_used_for_indexing_only",
)
_CAPTURE_POLICY = (
    "complete_questions_not_subparts",
    "originals_preserved_via_library_file_ids",
    "OCR_is_non_authoritative",
    "official_marking_scheme_linked",
    "bilingual_duplicates_count_once",
)
_DEDUP_POLICY = (
    "exam_identity_is_canonical",
    "do_not_create_a_second_mother_question_when_seen_in_topic_collections",
    "retain_all_source_relationships",
    "formal_import_requires_authoritative_fingerprint_check",
)
_SUMMARY = (
    "complete_questions",
    "total_marks",
    "module_distribution",
    "difficulty_distribution",
)
_STAGING_RECORD = (
    "staging_id",
    "dedup_key_proposal",
    "source_question_no",
    "section",
    "marks",
    "question_kind",
    "module",
    "module_name",
    "topic_proposal",
    "subtopic_proposal",
    "difficulty_proposal",
    "proposed_tags",
    "question_capture",
    "answer_capture",
    "provenance",
    "dedup_status",
    "potential_duplicate_sources",
    "review_required",
)
_QUESTION_CAPTURE = (
    "pp_pages",
    "exact_original_retained",
    "text_transcription_status",
    "completeness_unit",
)
_ANSWER_CAPTURE = (
    "ms_pages",
    "answer_status",
    "exact_original_retained",
    "scoring_steps_retained",
    "mapping_method",
)
_PROVENANCE = (
    "source_type",
    "source_name",
    "language",
    "canonical_exam_identity",
)
_PAGES = ("start", "end")
_PASS_TOP = (
    "schema_version",
    "pass_id",
    "staging_sha256",
    "pp_sha256",
    "ms_sha256",
    "records",
)
_PASS_RECORD = (
    "staging_id",
    "question_pages",
    "ms_pages",
    "question_text_original",
    "official_ms_original",
    "subparts",
    "marks",
    "figure_references",
    "question_method",
    "ms_method",
)
_PASS_PAGES = ("start_page", "end_page")


class _PairsObject:
    def __init__(self, pairs):
        self.pairs = tuple(pairs)


@dataclass(frozen=True)
class _PdfIdentity:
    role: str
    file_name: str
    sha256: str
    page_count: int


@dataclass(frozen=True)
class _StagingRecord:
    staging_id: str
    year: int
    section: str
    question_number: int
    marks: int
    question_pages: HkdsePdfPageSpan
    ms_pages: HkdsePdfPageSpan
    module_proposal: str
    topic_proposal: str
    difficulty_proposal: int
    tag_proposals: tuple[str, ...]


@dataclass(frozen=True)
class _StagingBatch:
    batch_id: str
    staging_sha256: str
    pp: _PdfIdentity
    ms: _PdfIdentity
    records: tuple[_StagingRecord, ...]


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _fatal(code: str, field: str, evidence: dict[str, object]) -> HkdsePdfTranscriptionIssue:
    return HkdsePdfTranscriptionIssue(
        code=code,
        severity="blocking",
        staging_id=None,
        field=field,
        evidence=_canonical_json(evidence),
    )


def _block(code: str, field: str, reason: str, **values: object):
    raise HkdsePdfAdapterBlockedError(
        (_fatal(code, field, {"reason": reason, **values}),)
    )


def _read_bytes(path: object, label: str) -> bytes:
    if not isinstance(path, Path):
        raise TypeError(f"{label} must be a pathlib.Path")
    if path.is_symlink():
        _block("staging_contract_mismatch", label, "not_regular_file")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
        with os.fdopen(descriptor, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                _block("staging_contract_mismatch", label, "not_regular_file")
            return stream.read()
    except OSError:
        _block("staging_contract_mismatch", label, "unreadable_file")


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _decode_strict_object(raw: bytes, field: str, code: str) -> dict[str, object]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        _block(code, field, "invalid_utf8")
    if text.startswith("\ufeff"):
        _block(code, field, "utf8_bom")
    try:
        value = json.loads(
            text,
            object_pairs_hook=_PairsObject,
            parse_constant=lambda token: (_ for _ in ()).throw(ValueError(token)),
        )
    except (ValueError, json.JSONDecodeError):
        _block(code, field, "invalid_json")
    if _has_duplicate_keys(value):
        _block(code, field, "duplicate_key")
    value = _ordinary(value)
    if type(value) is not dict:
        _block(code, field, "wrong_top_level_type")
    return value


def _has_duplicate_keys(value: object) -> bool:
    if type(value) is _PairsObject:
        keys = tuple(key for key, _ in value.pairs)
        return len(set(keys)) != len(keys) or any(
            _has_duplicate_keys(child) for _, child in value.pairs
        )
    if type(value) is list:
        return any(_has_duplicate_keys(item) for item in value)
    return False


def _ordinary(value: object) -> object:
    if type(value) is _PairsObject:
        return {key: _ordinary(child) for key, child in value.pairs}
    if type(value) is list:
        return [_ordinary(child) for child in value]
    return value


def _exact_keys(value: object, expected: tuple[str, ...], field: str, code: str) -> dict[str, object]:
    if type(value) is not dict or set(value) != set(expected):
        _block(code, field, "exact_keys_mismatch")
    return value


def _string(value: object, field: str, code: str, *, allow_empty: bool = False) -> str:
    if type(value) is not str or (not allow_empty and not value):
        _block(code, field, "wrong_string_type")
    return value


def _positive_int(value: object, field: str, code: str) -> int:
    if type(value) is not int or value <= 0:
        _block(code, field, "wrong_positive_integer")
    return value


def _boolean(value: object, field: str, code: str) -> bool:
    if type(value) is not bool:
        _block(code, field, "wrong_boolean_type")
    return value


def _span(value: object, field: str, *, pass_shape: bool = False) -> HkdsePdfPageSpan:
    expected = _PASS_PAGES if pass_shape else _PAGES
    item = _exact_keys(value, expected, field, "extraction_pass_invalid" if pass_shape else "staging_contract_mismatch")
    start_name, end_name = expected
    return HkdsePdfPageSpan(
        _positive_int(item[start_name], f"{field}.{start_name}", "extraction_pass_invalid" if pass_shape else "staging_contract_mismatch"),
        _positive_int(item[end_name], f"{field}.{end_name}", "extraction_pass_invalid" if pass_shape else "staging_contract_mismatch"),
    )


def _string_list(value: object, field: str, code: str) -> tuple[str, ...]:
    if type(value) is not list or any(type(item) is not str or not item for item in value):
        _block(code, field, "wrong_string_array")
    return tuple(value)


def _source_identity(value: object, name: str, expected_role: str) -> _PdfIdentity:
    item = _exact_keys(value, _SOURCE, f"$.source_pair.{name}", "staging_contract_mismatch")
    role = _string(item["role"], f"$.source_pair.{name}.role", "staging_contract_mismatch")
    if role != expected_role:
        _block("staging_contract_mismatch", f"$.source_pair.{name}.role", "wrong_fixed_value")
    digest = _string(item["sha256"], f"$.source_pair.{name}.sha256", "staging_contract_mismatch")
    if _SHA256.fullmatch(digest) is None:
        _block("staging_contract_mismatch", f"$.source_pair.{name}.sha256", "invalid_sha256")
    _string(item["library_file_id"], f"$.source_pair.{name}.library_file_id", "staging_contract_mismatch")
    _string(item["content_layer"], f"$.source_pair.{name}.content_layer", "staging_contract_mismatch")
    if _boolean(item["original_file_retained"], f"$.source_pair.{name}.original_file_retained", "staging_contract_mismatch") is not True:
        _block("staging_contract_mismatch", f"$.source_pair.{name}.original_file_retained", "wrong_fixed_value")
    if _boolean(item["ocr_used_for_indexing_only"], f"$.source_pair.{name}.ocr_used_for_indexing_only", "staging_contract_mismatch") is not True:
        _block("staging_contract_mismatch", f"$.source_pair.{name}.ocr_used_for_indexing_only", "wrong_fixed_value")
    return _PdfIdentity(
        role,
        _string(item["file_name"], f"$.source_pair.{name}.file_name", "staging_contract_mismatch"),
        digest,
        _positive_int(item["page_count"], f"$.source_pair.{name}.page_count", "staging_contract_mismatch"),
    )


def _load_staging(path: Path) -> _StagingBatch:
    raw = _read_bytes(path, "staging_manifest_path")
    payload = _exact_keys(
        _decode_strict_object(raw, "staging_manifest_path", "staging_contract_mismatch"),
        _STAGING_TOP,
        "$",
        "staging_contract_mismatch",
    )
    fixed = {
        "schema": "joy_m2_staging_batch_v1",
        "status": "staging_only",
        "database_release_target": "post-V1.18 (formal import not performed)",
    }
    for name, expected in fixed.items():
        if payload[name] != expected:
            _block("staging_contract_mismatch", f"$.{name}", "wrong_fixed_value")
    _string(payload["created_utc"], "$.created_utc", "staging_contract_mismatch")
    if _boolean(payload["formal_import_performed"], "$.formal_import_performed", "staging_contract_mismatch") is not False:
        _block("staging_contract_mismatch", "$.formal_import_performed", "wrong_fixed_value")
    source_pair = _exact_keys(payload["source_pair"], _SOURCE_PAIR, "$.source_pair", "staging_contract_mismatch")
    pp = _source_identity(source_pair["pp"], "pp", "question_paper")
    ms = _source_identity(source_pair["ms"], "ms", "marking_scheme")
    capture = _exact_keys(payload["capture_policy"], _CAPTURE_POLICY, "$.capture_policy", "staging_contract_mismatch")
    dedup = _exact_keys(payload["dedup_policy"], _DEDUP_POLICY, "$.dedup_policy", "staging_contract_mismatch")
    if any(_boolean(capture[name], f"$.capture_policy.{name}", "staging_contract_mismatch") is not True for name in _CAPTURE_POLICY):
        _block("staging_contract_mismatch", "$.capture_policy", "wrong_fixed_value")
    if any(_boolean(dedup[name], f"$.dedup_policy.{name}", "staging_contract_mismatch") is not True for name in _DEDUP_POLICY):
        _block("staging_contract_mismatch", "$.dedup_policy", "wrong_fixed_value")
    summary = _exact_keys(payload["summary"], _SUMMARY, "$.summary", "staging_contract_mismatch")
    if type(summary["module_distribution"]) is not dict or type(summary["difficulty_distribution"]) is not dict:
        _block("staging_contract_mismatch", "$.summary", "wrong_distribution_type")
    if type(payload["records"]) is not list:
        _block("staging_contract_mismatch", "$.records", "wrong_array_type")
    records: list[_StagingRecord] = []
    for index, raw_record in enumerate(payload["records"]):
        base = f"$.records[{index}]"
        item = _exact_keys(raw_record, _STAGING_RECORD, base, "staging_contract_mismatch")
        question_capture = _exact_keys(item["question_capture"], _QUESTION_CAPTURE, f"{base}.question_capture", "staging_contract_mismatch")
        answer_capture = _exact_keys(item["answer_capture"], _ANSWER_CAPTURE, f"{base}.answer_capture", "staging_contract_mismatch")
        provenance = _exact_keys(item["provenance"], _PROVENANCE, f"{base}.provenance", "staging_contract_mismatch")
        for name in ("dedup_key_proposal", "module_name"):
            _string(item[name], f"{base}.{name}", "staging_contract_mismatch")
        if item["subtopic_proposal"] is not None and type(item["subtopic_proposal"]) is not str:
            _block("staging_contract_mismatch", f"{base}.subtopic_proposal", "wrong_type")
        if item["question_kind"] != "public_exam_question" or item["dedup_status"] != "pending_authoritative_database_fingerprint_check":
            _block("staging_contract_mismatch", base, "wrong_fixed_value")
        if _boolean(item["review_required"], f"{base}.review_required", "staging_contract_mismatch") is not False:
            _block("staging_contract_mismatch", f"{base}.review_required", "wrong_fixed_value")
        _string_list(item["potential_duplicate_sources"], f"{base}.potential_duplicate_sources", "staging_contract_mismatch")
        if (
            _boolean(question_capture["exact_original_retained"], f"{base}.question_capture.exact_original_retained", "staging_contract_mismatch") is not True
            or question_capture["text_transcription_status"] != "not_generated"
            or question_capture["completeness_unit"] != "whole question including all subparts"
        ):
            _block("staging_contract_mismatch", f"{base}.question_capture", "wrong_fixed_value")
        if (
            _boolean(answer_capture["exact_original_retained"], f"{base}.answer_capture.exact_original_retained", "staging_contract_mismatch") is not True
            or _boolean(answer_capture["scoring_steps_retained"], f"{base}.answer_capture.scoring_steps_retained", "staging_contract_mismatch") is not True
            or answer_capture["answer_status"] != "official_marking_scheme"
        ):
            _block("staging_contract_mismatch", f"{base}.answer_capture", "wrong_fixed_value")
        _string(answer_capture["mapping_method"], f"{base}.answer_capture.mapping_method", "staging_contract_mismatch")
        for name in _PROVENANCE:
            _string(provenance[name], f"{base}.provenance.{name}", "staging_contract_mismatch")
        match = re.fullmatch(r"HKDSE-(\d{4})-M2-Q(\d{2})", _string(item["staging_id"], f"{base}.staging_id", "staging_contract_mismatch"))
        if match is None:
            _block("staging_contract_mismatch", f"{base}.staging_id", "invalid_identity")
        number = _positive_int(item["source_question_no"], f"{base}.source_question_no", "staging_contract_mismatch")
        if number != int(match.group(2)):
            _block("staging_contract_mismatch", f"{base}.source_question_no", "identity_mismatch")
        difficulty = _positive_int(item["difficulty_proposal"], f"{base}.difficulty_proposal", "staging_contract_mismatch")
        if difficulty > 5:
            _block("staging_contract_mismatch", f"{base}.difficulty_proposal", "out_of_range")
        records.append(
            _StagingRecord(
                item["staging_id"],
                int(match.group(1)),
                _string(item["section"], f"{base}.section", "staging_contract_mismatch"),
                number,
                _positive_int(item["marks"], f"{base}.marks", "staging_contract_mismatch"),
                _span(question_capture["pp_pages"], f"{base}.question_capture.pp_pages"),
                _span(answer_capture["ms_pages"], f"{base}.answer_capture.ms_pages"),
                _string(item["module"], f"{base}.module", "staging_contract_mismatch"),
                _string(item["topic_proposal"], f"{base}.topic_proposal", "staging_contract_mismatch"),
                difficulty,
                _string_list(item["proposed_tags"], f"{base}.proposed_tags", "staging_contract_mismatch"),
            )
        )
    identifiers = tuple(record.staging_id for record in records)
    if len(set(identifiers)) != len(identifiers):
        _block("staging_contract_mismatch", "$.records", "duplicate_staging_id")
    if _positive_int(summary["complete_questions"], "$.summary.complete_questions", "staging_contract_mismatch") != len(records):
        _block("staging_contract_mismatch", "$.summary.complete_questions", "count_closure")
    if _positive_int(summary["total_marks"], "$.summary.total_marks", "staging_contract_mismatch") != sum(record.marks for record in records):
        _block("staging_contract_mismatch", "$.summary.total_marks", "mark_closure")
    return _StagingBatch(
        _string(payload["batch_id"], "$.batch_id", "staging_contract_mismatch"),
        _sha_bytes(raw),
        pp,
        ms,
        tuple(records),
    )


def _validate_pdf(path: Path, identity: _PdfIdentity, label: str) -> PdfReader:
    raw = _read_bytes(path, f"{label}_pdf_path")
    if not raw.startswith(b"%PDF-"):
        _block("pdf_identity_mismatch", label, "invalid_pdf_signature")
    actual = _sha_bytes(raw)
    if actual != identity.sha256:
        _block("pdf_identity_mismatch", label, "sha256_mismatch", expected=identity.sha256, actual=actual)
    try:
        reader = PdfReader(io.BytesIO(raw), strict=True)
        count = len(reader.pages)
    except Exception:
        _block("pdf_identity_mismatch", label, "unreadable_pdf")
    if count != identity.page_count:
        _block("pdf_page_mismatch", label, "page_count_mismatch", expected=identity.page_count, actual=count)
    return reader


def load_hkdse_pdf_extraction_pass(path: Path) -> HkdsePdfExtractionPass:
    raw = _read_bytes(path, "extraction_pass_path")
    payload = _exact_keys(
        _decode_strict_object(raw, "extraction_pass_path", "extraction_pass_invalid"),
        _PASS_TOP,
        "$",
        "extraction_pass_invalid",
    )
    if payload["schema_version"] != "task10b-hkdse-pdf-extraction-pass-v1":
        _block("extraction_pass_invalid", "$.schema_version", "wrong_fixed_value")
    if type(payload["records"]) is not list:
        _block("extraction_pass_invalid", "$.records", "wrong_array_type")
    records: list[HkdsePdfExtractionRecord] = []
    for index, raw_record in enumerate(payload["records"]):
        base = f"$.records[{index}]"
        item = _exact_keys(raw_record, _PASS_RECORD, base, "extraction_pass_invalid")
        records.append(
            HkdsePdfExtractionRecord(
                staging_id=_string(item["staging_id"], f"{base}.staging_id", "extraction_pass_invalid"),
                question_pages=_span(item["question_pages"], f"{base}.question_pages", pass_shape=True),
                ms_pages=_span(item["ms_pages"], f"{base}.ms_pages", pass_shape=True),
                question_text_original=_string(item["question_text_original"], f"{base}.question_text_original", "extraction_pass_invalid", allow_empty=True),
                official_ms_original=_string(item["official_ms_original"], f"{base}.official_ms_original", "extraction_pass_invalid", allow_empty=True),
                subparts=_string_list(item["subparts"], f"{base}.subparts", "extraction_pass_invalid"),
                marks=_positive_int(item["marks"], f"{base}.marks", "extraction_pass_invalid"),
                figure_references=_string_list(item["figure_references"], f"{base}.figure_references", "extraction_pass_invalid"),
                question_method=_string(item["question_method"], f"{base}.question_method", "extraction_pass_invalid"),
                ms_method=_string(item["ms_method"], f"{base}.ms_method", "extraction_pass_invalid"),
            )
        )
    try:
        return HkdsePdfExtractionPass(
            _string(payload["pass_id"], "$.pass_id", "extraction_pass_invalid"),
            _string(payload["staging_sha256"], "$.staging_sha256", "extraction_pass_invalid"),
            _string(payload["pp_sha256"], "$.pp_sha256", "extraction_pass_invalid"),
            _string(payload["ms_sha256"], "$.ms_sha256", "extraction_pass_invalid"),
            tuple(records),
        )
    except PipelineError as exc:
        _block("extraction_pass_invalid", "$", "typed_contract_mismatch", message=str(exc))


def _validate_pass(pass_value: HkdsePdfExtractionPass, staging: _StagingBatch, pass_id: str) -> None:
    if (
        pass_value.pass_id != pass_id
        or pass_value.staging_sha256 != staging.staging_sha256
        or pass_value.pp_sha256 != staging.pp.sha256
        or pass_value.ms_sha256 != staging.ms.sha256
    ):
        _block("extraction_pass_invalid", f"pass_{pass_id.lower()}", "source_identity_mismatch")
    expected = tuple(record.staging_id for record in staging.records)
    actual = tuple(record.staging_id for record in pass_value.records)
    if actual != expected:
        _block("extraction_pass_invalid", f"pass_{pass_id.lower()}.records", "staging_mapping_mismatch")
    if any(
        record.question_pages.end_page > staging.pp.page_count
        or record.ms_pages.end_page > staging.ms.page_count
        for record in pass_value.records
    ):
        _block(
            "extraction_pass_invalid",
            f"pass_{pass_id.lower()}.records",
            "page_span_out_of_bounds",
        )


def _validate_output(output_dir: object, config: object) -> Path:
    if not isinstance(output_dir, Path):
        raise TypeError("output_dir must be a pathlib.Path")
    if type(config) is not PipelineConfig:
        raise TypeError("config must be an exact PipelineConfig")
    lexical = output_dir.absolute()
    lexical_staging = next(
        (
            ancestor
            for ancestor in lexical.parents
            if ancestor.resolve(strict=False) == config.staging_root
        ),
        None,
    )
    if lexical_staging is not None:
        relative = lexical.relative_to(lexical_staging)
        current = lexical_staging
        for part in relative.parts[:-1]:
            current = current / part
            if current.is_symlink():
                raise ConfigurationError("output ancestors must not be symlinks")
    resolved = config.require_staging_output(output_dir)
    if resolved == config.staging_root:
        raise ConfigurationError("output must be a strict staging descendant")
    if output_dir.exists() or output_dir.is_symlink():
        raise OutputConflictError("output path already exists")
    return resolved


def _pass_record_payload(record: HkdsePdfExtractionRecord) -> dict[str, object]:
    return {
        "staging_id": record.staging_id,
        "question_pages": {
            "start_page": record.question_pages.start_page,
            "end_page": record.question_pages.end_page,
        },
        "ms_pages": {
            "start_page": record.ms_pages.start_page,
            "end_page": record.ms_pages.end_page,
        },
        "question_text_original": record.question_text_original,
        "official_ms_original": record.official_ms_original,
        "subparts": list(record.subparts),
        "marks": record.marks,
        "figure_references": list(record.figure_references),
        "question_method": record.question_method,
        "ms_method": record.ms_method,
    }


def _pass_payload(value: HkdsePdfExtractionPass) -> dict[str, object]:
    return {
        "schema_version": "task10b-hkdse-pdf-extraction-pass-v1",
        "pass_id": value.pass_id,
        "staging_sha256": value.staging_sha256,
        "pp_sha256": value.pp_sha256,
        "ms_sha256": value.ms_sha256,
        "records": [_pass_record_payload(record) for record in value.records],
    }


def _atomic_write_file(output_path: Path, content: bytes) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output_path.name}-",
        dir=output_path.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, output_path)
        except FileExistsError as exc:
            raise OutputConflictError("output path already exists") from exc
    finally:
        temporary.unlink(missing_ok=True)


def _owned_pages(records: tuple[_StagingRecord, ...], name: str) -> dict[int, int]:
    counts: dict[int, int] = {}
    for record in records:
        span = getattr(record, name)
        for page_number in range(span.start_page, span.end_page + 1):
            counts[page_number] = counts.get(page_number, 0) + 1
    return counts


def _embedded_text(reader: PdfReader, span: HkdsePdfPageSpan, owners: dict[int, int]) -> str:
    page_numbers = tuple(range(span.start_page, span.end_page + 1))
    if any(owners[number] != 1 for number in page_numbers):
        return ""
    values: list[str] = []
    for number in page_numbers:
        value = reader.pages[number - 1].extract_text()
        values.append(value if type(value) is str else "")
    return "\f".join(values)


def extract_hkdse_pdf_embedded_pass(
    staging_manifest_path: Path,
    pp_pdf_path: Path,
    ms_pdf_path: Path,
    pass_id: str,
    output_path: Path,
    config: PipelineConfig,
) -> HkdsePdfExtractionPass:
    resolved_output = _validate_output(output_path, config)
    staging = _load_staging(staging_manifest_path)
    pp_reader = _validate_pdf(pp_pdf_path, staging.pp, "pp")
    ms_reader = _validate_pdf(ms_pdf_path, staging.ms, "ms")
    if pass_id not in {"A", "B"}:
        raise PipelineError("pass_id must be exactly A or B")
    pp_owners = _owned_pages(staging.records, "question_pages")
    ms_owners = _owned_pages(staging.records, "ms_pages")
    records = tuple(
        HkdsePdfExtractionRecord(
            staging_id=record.staging_id,
            question_pages=record.question_pages,
            ms_pages=record.ms_pages,
            question_text_original=_embedded_text(
                pp_reader, record.question_pages, pp_owners
            ),
            official_ms_original=_embedded_text(ms_reader, record.ms_pages, ms_owners),
            subparts=(),
            marks=record.marks,
            figure_references=(),
            question_method="embedded_text",
            ms_method="embedded_text",
        )
        for record in staging.records
    )
    result = HkdsePdfExtractionPass(
        pass_id,
        staging.staging_sha256,
        staging.pp.sha256,
        staging.ms.sha256,
        records,
    )
    content = (_canonical_json(_pass_payload(result)) + "\n").encode("utf-8")
    _atomic_write_file(resolved_output, content)
    reconstructed = load_hkdse_pdf_extraction_pass(resolved_output)
    if reconstructed != result:
        resolved_output.unlink(missing_ok=True)
        raise PipelineError("embedded pass did not round-trip exactly")
    return result


def _review_issue(
    code: str,
    staging_id: str,
    field: str,
    evidence: dict[str, object],
) -> HkdsePdfTranscriptionIssue:
    return HkdsePdfTranscriptionIssue(
        code=code,
        severity="review_required",
        staging_id=staging_id,
        field=field,
        evidence=_canonical_json(evidence),
    )


def _text_evidence(first: str, second: str) -> dict[str, object]:
    return {
        "pass_a_length": len(first),
        "pass_a_sha256": _sha_bytes(first.encode("utf-8")),
        "pass_b_length": len(second),
        "pass_b_sha256": _sha_bytes(second.encode("utf-8")),
    }


def _span_payload(span: HkdsePdfPageSpan) -> dict[str, int]:
    return {"start_page": span.start_page, "end_page": span.end_page}


def _record_payload(record: HkdsePdfTranscriptionRecord) -> dict[str, object]:
    return {
        "staging_id": record.staging_id,
        "year": record.year,
        "section": record.section,
        "question_number": record.question_number,
        "question_pages": _span_payload(record.question_pages),
        "ms_pages": _span_payload(record.ms_pages),
        "question_text_original": record.question_text_original,
        "official_ms_original": record.official_ms_original,
        "subparts": list(record.subparts),
        "marks": record.marks,
        "figure_references": list(record.figure_references),
        "question_methods": list(record.question_methods),
        "ms_methods": list(record.ms_methods),
        "status": record.status,
        "review_reasons": list(record.review_reasons),
        "module_proposal": record.module_proposal,
        "topic_proposal": record.topic_proposal,
        "difficulty_proposal": record.difficulty_proposal,
        "tag_proposals": list(record.tag_proposals),
    }


def _issue_payload(issue: HkdsePdfTranscriptionIssue) -> dict[str, object]:
    return {
        "code": issue.code,
        "severity": issue.severity,
        "staging_id": issue.staging_id,
        "field": issue.field,
        "evidence": json.loads(issue.evidence),
    }


def _transcription_payload(
    staging: _StagingBatch,
    records: tuple[HkdsePdfTranscriptionRecord, ...],
    issues: tuple[HkdsePdfTranscriptionIssue, ...],
) -> dict[str, object]:
    return {
        "schema_version": "task10b-hkdse-pdf-transcription-v1",
        "batch_id": staging.batch_id,
        "staging_sha256": staging.staging_sha256,
        "pp_sha256": staging.pp.sha256,
        "ms_sha256": staging.ms.sha256,
        "records": [_record_payload(record) for record in records],
        "issues": [_issue_payload(issue) for issue in issues],
    }


def _proposal_semantic_payload(
    proposal: HkdsePdfTranscriptionBatch,
) -> dict[str, object]:
    return {
        "schema_version": "task10b-hkdse-pdf-transcription-v1",
        "batch_id": proposal.batch_id,
        "staging_sha256": proposal.staging_sha256,
        "pp_sha256": proposal.pp_sha256,
        "ms_sha256": proposal.ms_sha256,
        "records": [_record_payload(record) for record in proposal.records],
        "issues": [_issue_payload(issue) for issue in proposal.issues],
    }


_MATH_SIGNAL = re.compile(r"[0-9=+\-\u2212\u00d7\u00f7/^_∫√<>≤≥()\[\]{}']")


def _compare_record(
    staging: _StagingRecord,
    first: HkdsePdfExtractionRecord,
    second: HkdsePdfExtractionRecord,
) -> tuple[HkdsePdfTranscriptionRecord, tuple[HkdsePdfTranscriptionIssue, ...]]:
    issues: list[HkdsePdfTranscriptionIssue] = []

    def add(code: str, field: str, evidence: dict[str, object]) -> None:
        issues.append(_review_issue(code, staging.staging_id, field, evidence))

    for field, missing_code, mismatch_code in (
        ("question_text_original", "question_text_missing", "question_text_mismatch"),
        ("official_ms_original", "official_ms_missing", "official_ms_mismatch"),
    ):
        first_text = getattr(first, field)
        second_text = getattr(second, field)
        if not first_text or not second_text:
            add(
                missing_code,
                field,
                {"pass_a_empty": not bool(first_text), "pass_b_empty": not bool(second_text)},
            )
        elif first_text != second_text:
            evidence = _text_evidence(first_text, second_text)
            add(mismatch_code, field, evidence)
            if _MATH_SIGNAL.search(first_text) or _MATH_SIGNAL.search(second_text):
                add("formula_mismatch", field, evidence)

    for field, code in (
        ("subparts", "subpart_mismatch"),
        ("marks", "mark_mismatch"),
        ("figure_references", "figure_mismatch"),
    ):
        first_value = getattr(first, field)
        second_value = getattr(second, field)
        staging_value = getattr(staging, field, None)
        if first_value != second_value or (
            field == "marks" and first_value != staging_value
        ):
            add(
                code,
                field,
                {
                    "pass_a": list(first_value) if type(first_value) is tuple else first_value,
                    "pass_b": list(second_value) if type(second_value) is tuple else second_value,
                    **({"staging": staging_value} if field == "marks" else {}),
                },
            )

    page_values = (
        ("question_pages", first.question_pages, second.question_pages, staging.question_pages),
        ("ms_pages", first.ms_pages, second.ms_pages, staging.ms_pages),
    )
    for field, first_span, second_span, staging_span in page_values:
        if first_span != second_span or first_span != staging_span:
            add(
                "page_boundary_ambiguity",
                field,
                {
                    "pass_a": _span_payload(first_span),
                    "pass_b": _span_payload(second_span),
                    "staging": _span_payload(staging_span),
                },
            )

    ordered_issues = tuple(
        sorted(
            issues,
            key=lambda issue: (
                issue.staging_id or "",
                issue.code,
                issue.field,
                issue.evidence,
            ),
        )
    )
    reasons = tuple(sorted({issue.code for issue in ordered_issues}))
    record = HkdsePdfTranscriptionRecord(
        staging_id=staging.staging_id,
        year=staging.year,
        section=staging.section,
        question_number=staging.question_number,
        question_pages=first.question_pages,
        ms_pages=first.ms_pages,
        question_text_original=first.question_text_original,
        official_ms_original=first.official_ms_original,
        subparts=first.subparts,
        marks=first.marks,
        figure_references=first.figure_references,
        question_methods=(first.question_method, second.question_method),
        ms_methods=(first.ms_method, second.ms_method),
        status="REVIEW_REQUIRED" if ordered_issues else "PROPOSED",
        review_reasons=reasons,
        module_proposal=staging.module_proposal,
        topic_proposal=staging.topic_proposal,
        difficulty_proposal=staging.difficulty_proposal,
        tag_proposals=staging.tag_proposals,
    )
    return record, ordered_issues


def _preview(value: str) -> str:
    return value.replace("\r", "\\r").replace("\n", "\\n")[:160]


def _review_report(
    batch_id: str,
    records: tuple[HkdsePdfTranscriptionRecord, ...],
    issues: tuple[HkdsePdfTranscriptionIssue, ...],
    pass_b: HkdsePdfExtractionPass,
) -> str:
    lines = [
        "# PDF Transcription Review",
        "",
        f"Batch ID: {batch_id}",
        f"Total questions: {len(records)}",
        f"Auto agree: {sum(record.status == 'PROPOSED' for record in records)}",
        f"Review required: {sum(record.status == 'REVIEW_REQUIRED' for record in records)}",
        f"Question text complete: {sum(bool(record.question_text_original) for record in records)}",
        f"MS text complete: {sum(bool(record.official_ms_original) for record in records)}",
        f"Figure questions: {sum(bool(record.figure_references) for record in records)}",
        f"Formula mismatches: {sum(issue.code == 'formula_mismatch' for issue in issues)}",
        f"Page-boundary ambiguities: {sum(issue.code == 'page_boundary_ambiguity' for issue in issues)}",
        f"Missing content: {sum(issue.code in {'question_text_missing', 'official_ms_missing'} for issue in issues)}",
        f"Issues: {len(issues)}",
        "",
    ]
    second_by_id = {record.staging_id: record for record in pass_b.records}
    for record in records:
        second = second_by_id[record.staging_id]
        lines.extend(
            (
                f"## {record.staging_id}",
                "",
                f"Year/question: {record.year} Q{record.question_number}",
                f"PP pages: {record.question_pages.start_page}-{record.question_pages.end_page}",
                f"MS pages: {record.ms_pages.start_page}-{record.ms_pages.end_page}",
                f"Question preview (pass A): {_preview(record.question_text_original)}",
                f"Question preview (pass B): {_preview(second.question_text_original)}",
                f"Subparts: {', '.join(record.subparts) or 'none'}",
                f"Marks: {record.marks}",
                f"MS preview (pass A): {_preview(record.official_ms_original)}",
                f"MS preview (pass B): {_preview(second.official_ms_original)}",
                f"Question methods: {', '.join(record.question_methods)}",
                f"MS methods: {', '.join(record.ms_methods)}",
                f"Status: {record.status}",
                f"Figures: {', '.join(record.figure_references) or 'none'}",
                f"Taxonomy proposal: {record.module_proposal} / {record.topic_proposal} / D{record.difficulty_proposal}",
                f"Review reasons: {', '.join(record.review_reasons) or 'none'}",
                "",
            )
        )
    return "\n".join(lines)


def _write_private_file(path: Path, content: bytes) -> None:
    with path.open("xb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def propose_hkdse_pdf_transcription(
    staging_manifest_path: Path,
    pp_pdf_path: Path,
    ms_pdf_path: Path,
    pass_a_path: Path,
    pass_b_path: Path,
    output_dir: Path,
    config: PipelineConfig,
):
    resolved_output = _validate_output(output_dir, config)
    staging = _load_staging(staging_manifest_path)
    _validate_pdf(pp_pdf_path, staging.pp, "pp")
    _validate_pdf(ms_pdf_path, staging.ms, "ms")
    if any(record.question_pages.end_page > staging.pp.page_count for record in staging.records):
        _block("pdf_page_mismatch", "$.records.question_pages", "declared_page_out_of_bounds")
    if any(record.ms_pages.end_page > staging.ms.page_count for record in staging.records):
        _block("pdf_page_mismatch", "$.records.ms_pages", "declared_page_out_of_bounds")
    pass_a = load_hkdse_pdf_extraction_pass(pass_a_path)
    pass_b = load_hkdse_pdf_extraction_pass(pass_b_path)
    _validate_pass(pass_a, staging, "A")
    _validate_pass(pass_b, staging, "B")
    compared = tuple(
        _compare_record(staging_record, first, second)
        for staging_record, first, second in zip(
            staging.records, pass_a.records, pass_b.records, strict=True
        )
    )
    records = tuple(record for record, _ in compared)
    issues = tuple(
        sorted(
            (issue for _, record_issues in compared for issue in record_issues),
            key=lambda issue: (
                issue.staging_id or "",
                issue.code,
                issue.field,
                issue.evidence,
            ),
        )
    )
    semantic = _transcription_payload(staging, records, issues)
    digest = _sha_bytes(_canonical_json(semantic).encode("utf-8"))
    transcription = {**semantic, "transcription_digest": digest}
    pass_a_content = (_canonical_json(_pass_payload(pass_a)) + "\n").encode("utf-8")
    pass_b_content = (_canonical_json(_pass_payload(pass_b)) + "\n").encode("utf-8")
    transcription_content = (_canonical_json(transcription) + "\n").encode("utf-8")
    report_content = _review_report(
        staging.batch_id, records, issues, pass_b
    ).encode("utf-8")

    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(
            prefix=f".{resolved_output.name}-",
            dir=resolved_output.parent,
        )
    )
    try:
        _write_private_file(temporary / "transcription.json", transcription_content)
        _write_private_file(temporary / "extraction-pass-a.json", pass_a_content)
        _write_private_file(temporary / "extraction-pass-b.json", pass_b_content)
        _write_private_file(
            temporary / "PDF_TRANSCRIPTION_REVIEW.md", report_content
        )
        try:
            atomic_rename_no_replace(temporary, resolved_output)
        except OSError as exc:
            if exc.errno in {errno.EEXIST, errno.ENOTEMPTY}:
                raise OutputConflictError("output path already exists") from exc
            raise
    except Exception:
        shutil.rmtree(temporary, ignore_errors=True)
        raise

    return HkdsePdfTranscriptionBatch(
        batch_id=staging.batch_id,
        staging_sha256=staging.staging_sha256,
        pp_sha256=staging.pp.sha256,
        ms_sha256=staging.ms.sha256,
        records=records,
        issues=issues,
        transcription_digest=digest,
        artifact_root=resolved_output,
        transcription_path=resolved_output / "transcription.json",
        review_path=resolved_output / "PDF_TRANSCRIPTION_REVIEW.md",
    )


def approve_hkdse_pdf_transcription(
    proposal: HkdsePdfTranscriptionBatch,
    approval: HkdsePdfTranscriptionApproval,
) -> VerifiedHkdsePdfTranscriptionBatch:
    if type(proposal) is not HkdsePdfTranscriptionBatch:
        raise TypeError("proposal must be an exact HkdsePdfTranscriptionBatch")
    if type(approval) is not HkdsePdfTranscriptionApproval:
        raise TypeError("approval must be an exact HkdsePdfTranscriptionApproval")
    actual_digest = _sha_bytes(
        _canonical_json(_proposal_semantic_payload(proposal)).encode("utf-8")
    )
    if actual_digest != proposal.transcription_digest:
        raise PipelineError("proposal semantic payload does not match its digest")
    if proposal.issues or any(
        record.status != "PROPOSED" for record in proposal.records
    ):
        raise PipelineError("proposal still requires transcription review")
    if (
        approval.batch_id != proposal.batch_id
        or approval.transcription_digest != proposal.transcription_digest
    ):
        raise PipelineError("approval does not bind the proposal")
    verified_records = tuple(
        replace(record, status="VERIFIED") for record in proposal.records
    )
    return VerifiedHkdsePdfTranscriptionBatch(
        proposal=proposal,
        approval=approval,
        records=verified_records,
    )


def _file_evidence(
    relative_path: str, content: bytes, kind: str
) -> ImportFileEvidence:
    return ImportFileEvidence(
        relative_path=relative_path,
        sha256=_sha_bytes(content),
        size_bytes=len(content),
        kind=kind,
    )


def _v120_manifest_payload(
    manifest: V120BatchImportManifest,
) -> dict[str, object]:
    def evidence(values: tuple[ImportFileEvidence, ...]) -> list[dict[str, object]]:
        return [
            {
                "relative_path": item.relative_path,
                "sha256": item.sha256,
                "size_bytes": item.size_bytes,
                "kind": item.kind,
            }
            for item in values
        ]

    return {
        "schema_version": manifest.schema_version,
        "batch_id": manifest.batch_id,
        "project": manifest.project,
        "module": manifest.module,
        "chapter": manifest.chapter,
        "target_release_version": manifest.target_release_version,
        "candidate_records": evidence(manifest.candidate_records),
        "source_files": evidence(manifest.source_files),
        "answer_files": evidence(manifest.answer_files),
        "image_files": evidence(manifest.image_files),
        "teacher_notes_files": evidence(manifest.teacher_notes_files),
        "common_errors_files": evidence(manifest.common_errors_files),
        "language_policy": manifest.language_policy,
        "split_policy": manifest.split_policy,
        "difficulty_policy": manifest.difficulty_policy,
        "tag_policy": manifest.tag_policy,
        "answer_policy": manifest.answer_policy,
        "explanation_policy": manifest.explanation_policy,
    }


def _candidate_payload(
    batch_id: str,
    record: HkdsePdfTranscriptionRecord,
    index: int,
) -> dict[str, object]:
    transcription_locator = (
        f"source:source/transcription.json#records[{index}].question_text_original"
    )
    return {
        "proposed_question_id": record.staging_id,
        "source_id": batch_id,
        "source_question_number": str(record.question_number),
        "source_section": record.section,
        "source_fragment_hash": _sha_bytes(
            record.question_text_original.encode("utf-8")
        ),
        "question_text_original": record.question_text_original,
        "question_text_zh": record.question_text_original,
        "translation_status": "source_present",
        "translation_evidence": transcription_locator,
        "solution_original": record.official_ms_original,
        "solution_verified": "",
        "answer_status": "source_provided",
        "explanation_text": "",
        "explanation_status": "missing",
        "explanation_evidence": None,
        "image_paths": [],
        "image_roles": [],
        "primary_type": record.module_proposal,
        "tags": list(record.tag_proposals),
        "tag_status": "proposed",
        "difficulty_level": record.difficulty_proposal,
        "difficulty_status": "proposed",
        "enrichment_status": "incomplete",
    }


def _source_map_payload_v120(
    verified: VerifiedHkdsePdfTranscriptionBatch,
) -> dict[str, object]:
    proposal = verified.proposal
    return {
        "schema_version": "task10b-hkdse-pdf-source-map-v1",
        "batch_id": proposal.batch_id,
        "staging_sha256": proposal.staging_sha256,
        "pp_sha256": proposal.pp_sha256,
        "ms_sha256": proposal.ms_sha256,
        "transcription_digest": proposal.transcription_digest,
        "records": [
            {
                "staging_id": record.staging_id,
                "year": record.year,
                "section": record.section,
                "question_number": record.question_number,
                "question_pages": _span_payload(record.question_pages),
                "ms_pages": _span_payload(record.ms_pages),
                "marks": record.marks,
                "subparts": list(record.subparts),
                "figure_references": list(record.figure_references),
                "question_methods": list(record.question_methods),
                "ms_methods": list(record.ms_methods),
            }
            for record in verified.records
        ],
    }


def _answer_payload_v120(
    verified: VerifiedHkdsePdfTranscriptionBatch,
) -> dict[str, object]:
    return {
        "schema_version": "task10b-hkdse-pdf-official-ms-v1",
        "batch_id": verified.proposal.batch_id,
        "ms_sha256": verified.proposal.ms_sha256,
        "transcription_digest": verified.proposal.transcription_digest,
        "records": [
            {
                "staging_id": record.staging_id,
                "ms_pages": _span_payload(record.ms_pages),
                "marks": record.marks,
                "official_ms_original": record.official_ms_original,
            }
            for record in verified.records
        ],
    }


def adapt_verified_hkdse_pdf_transcription_v120(
    verified: VerifiedHkdsePdfTranscriptionBatch,
    output_dir: Path,
    config: PipelineConfig,
) -> V120AdaptedImportPackage:
    if type(verified) is not VerifiedHkdsePdfTranscriptionBatch:
        raise TypeError(
            "verified must be an exact VerifiedHkdsePdfTranscriptionBatch"
        )
    proposal = verified.proposal
    approval = getattr(verified, "approval", None)
    if type(approval) is not HkdsePdfTranscriptionApproval:
        raise PipelineError("verified transcription requires an exact approval")
    try:
        reconstructed_approval = HkdsePdfTranscriptionApproval(
            approval.batch_id,
            approval.transcription_digest,
            approval.approval_text,
        )
    except (AttributeError, PipelineError) as exc:
        raise PipelineError("verified transcription approval is invalid") from exc
    if (
        approval != reconstructed_approval
        or approval.batch_id != proposal.batch_id
        or approval.transcription_digest != proposal.transcription_digest
    ):
        raise PipelineError("verified transcription approval does not bind proposal")
    resolved_output = _validate_output(output_dir, config)
    proposal_root = proposal.artifact_root.resolve(strict=False)
    if (
        resolved_output.is_relative_to(proposal_root)
        or proposal_root.is_relative_to(resolved_output)
    ):
        raise ConfigurationError(
            "canonical output must not overlap transcription artifacts"
        )
    actual_digest = _sha_bytes(
        _canonical_json(_proposal_semantic_payload(proposal)).encode("utf-8")
    )
    if actual_digest != proposal.transcription_digest:
        raise PipelineError("verified proposal semantic payload digest is invalid")
    if proposal.issues or any(
        record.status != "PROPOSED" for record in proposal.records
    ):
        raise PipelineError("verified proposal is not approval-eligible")
    expected_records = tuple(
        replace(record, status="VERIFIED") for record in proposal.records
    )
    if verified.records != expected_records:
        raise PipelineError("verified records do not preserve the proposal")

    candidates = tuple(
        _candidate_payload(proposal.batch_id, record, index)
        for index, record in enumerate(verified.records)
    )
    candidates_bytes = (_canonical_json(list(candidates)) + "\n").encode("utf-8")
    transcription_payload = {
        **_proposal_semantic_payload(proposal),
        "transcription_digest": proposal.transcription_digest,
    }
    transcription_bytes = (
        _canonical_json(transcription_payload) + "\n"
    ).encode("utf-8")
    source_map_bytes = (
        _canonical_json(_source_map_payload_v120(verified)) + "\n"
    ).encode("utf-8")
    answer_bytes = (
        _canonical_json(_answer_payload_v120(verified)) + "\n"
    ).encode("utf-8")
    manifest = V120BatchImportManifest(
        schema_version="task10-v120-import-manifest-v1",
        batch_id=proposal.batch_id,
        project="Joy M2 AI Database",
        module="M2",
        chapter="HKDSE M2",
        target_release_version="V1.20",
        candidate_records=(
            _file_evidence(
                "records/candidates.json", candidates_bytes, "candidate_json"
            ),
        ),
        source_files=(
            _file_evidence(
                "source/transcription.json", transcription_bytes, "source"
            ),
            _file_evidence("source/source-map.json", source_map_bytes, "source"),
        ),
        answer_files=(
            _file_evidence("answers/official-ms.json", answer_bytes, "answer"),
        ),
        image_files=(),
        teacher_notes_files=(),
        common_errors_files=(),
        language_policy="preserve_source_and_store_reviewed_chinese_separately",
        split_policy="one_complete_question_per_record",
        difficulty_policy="joy_level_1_5",
        tag_policy="controlled_primary_type_and_tags",
        answer_policy="preserve_source_answer_identity",
        explanation_policy="source_or_independently_verified_with_identity",
    )
    manifest_bytes = (
        json.dumps(
            _v120_manifest_payload(manifest),
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    files = (
        ("records/candidates.json", candidates_bytes),
        ("source/transcription.json", transcription_bytes),
        ("source/source-map.json", source_map_bytes),
        ("answers/official-ms.json", answer_bytes),
        ("import_manifest.json", manifest_bytes),
    )

    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(
            prefix=f".{resolved_output.name}-", dir=resolved_output.parent
        )
    )
    try:
        for relative_path, content in files:
            target = temporary / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            _write_private_file(target, content)
        try:
            atomic_rename_no_replace(temporary, resolved_output)
        except OSError as exc:
            if exc.errno in {errno.EEXIST, errno.ENOTEMPTY}:
                raise OutputConflictError("output path already exists") from exc
            raise
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)

    loaded = load_v120_import_manifest(resolved_output / "import_manifest.json")
    if loaded != manifest:
        raise PipelineError("V1.20 package did not round-trip exactly")
    return V120AdaptedImportPackage(
        package_root=resolved_output,
        manifest_path=resolved_output / "import_manifest.json",
        manifest=loaded,
    )


def adapt_verified_hkdse_pdf_transcription_v121(
    verified: VerifiedHkdsePdfTranscriptionBatch,
    output_dir: Path,
    config: PipelineConfig,
) -> V121AdaptedImportPackage:
    if type(verified) is not VerifiedHkdsePdfTranscriptionBatch:
        raise TypeError(
            "verified must be an exact VerifiedHkdsePdfTranscriptionBatch"
        )
    proposal = verified.proposal
    approval = getattr(verified, "approval", None)
    if type(approval) is not HkdsePdfTranscriptionApproval:
        raise PipelineError("verified transcription requires an exact approval")
    try:
        reconstructed_approval = HkdsePdfTranscriptionApproval(
            approval.batch_id,
            approval.transcription_digest,
            approval.approval_text,
        )
    except (AttributeError, PipelineError) as exc:
        raise PipelineError("verified transcription approval is invalid") from exc
    if (
        approval != reconstructed_approval
        or approval.batch_id != proposal.batch_id
        or approval.transcription_digest != proposal.transcription_digest
    ):
        raise PipelineError("verified transcription approval does not bind proposal")
    resolved_output = _validate_output(output_dir, config)
    proposal_root = proposal.artifact_root.resolve(strict=False)
    if (
        resolved_output.is_relative_to(proposal_root)
        or proposal_root.is_relative_to(resolved_output)
    ):
        raise ConfigurationError(
            "canonical output must not overlap transcription artifacts"
        )
    actual_digest = _sha_bytes(
        _canonical_json(_proposal_semantic_payload(proposal)).encode("utf-8")
    )
    if actual_digest != proposal.transcription_digest:
        raise PipelineError("verified proposal semantic payload digest is invalid")
    if proposal.issues or any(
        record.status != "PROPOSED" for record in proposal.records
    ):
        raise PipelineError("verified proposal is not approval-eligible")
    expected_records = tuple(
        replace(record, status="VERIFIED") for record in proposal.records
    )
    if verified.records != expected_records:
        raise PipelineError("verified records do not preserve the proposal")

    candidates = tuple(
        _candidate_payload(proposal.batch_id, record, index)
        for index, record in enumerate(verified.records)
    )
    candidates_bytes = (_canonical_json(list(candidates)) + "\n").encode("utf-8")
    transcription_payload = {
        **_proposal_semantic_payload(proposal),
        "transcription_digest": proposal.transcription_digest,
    }
    transcription_bytes = (
        _canonical_json(transcription_payload) + "\n"
    ).encode("utf-8")
    source_map_bytes = (
        _canonical_json(_source_map_payload_v120(verified)) + "\n"
    ).encode("utf-8")
    answer_bytes = (
        _canonical_json(_answer_payload_v120(verified)) + "\n"
    ).encode("utf-8")
    manifest = V121BatchImportManifest(
        schema_version="task11-v121-import-manifest-v1",
        batch_id=proposal.batch_id,
        project="Joy M2 AI Database",
        module="M2",
        chapter="HKDSE M2",
        target_release_version="V1.21",
        candidate_records=(
            _file_evidence(
                "records/candidates.json", candidates_bytes, "candidate_json"
            ),
        ),
        source_files=(
            _file_evidence(
                "source/transcription.json", transcription_bytes, "source"
            ),
            _file_evidence("source/source-map.json", source_map_bytes, "source"),
        ),
        answer_files=(
            _file_evidence("answers/official-ms.json", answer_bytes, "answer"),
        ),
        image_files=(),
        teacher_notes_files=(),
        common_errors_files=(),
        language_policy="preserve_source_and_store_reviewed_chinese_separately",
        split_policy="one_complete_question_per_record",
        difficulty_policy="joy_level_1_5",
        tag_policy="controlled_primary_type_and_tags",
        answer_policy="preserve_source_answer_identity",
        explanation_policy="source_or_independently_verified_with_identity",
    )
    manifest_bytes = (
        json.dumps(
            _v120_manifest_payload(manifest),
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    files = (
        ("records/candidates.json", candidates_bytes),
        ("source/transcription.json", transcription_bytes),
        ("source/source-map.json", source_map_bytes),
        ("answers/official-ms.json", answer_bytes),
        ("import_manifest.json", manifest_bytes),
    )

    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(
            prefix=f".{resolved_output.name}-", dir=resolved_output.parent
        )
    )
    try:
        for relative_path, content in files:
            target = temporary / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            _write_private_file(target, content)
        try:
            atomic_rename_no_replace(temporary, resolved_output)
        except OSError as exc:
            if exc.errno in {errno.EEXIST, errno.ENOTEMPTY}:
                raise OutputConflictError("output path already exists") from exc
            raise
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)

    loaded = load_v121_import_manifest(resolved_output / "import_manifest.json")
    if loaded != manifest:
        raise PipelineError("V1.21 package did not round-trip exactly")
    return V121AdaptedImportPackage(
        package_root=resolved_output,
        manifest_path=resolved_output / "import_manifest.json",
        manifest=loaded,
    )


__all__ = (
    "adapt_verified_hkdse_pdf_transcription_v120",
    "adapt_verified_hkdse_pdf_transcription_v121",
    "approve_hkdse_pdf_transcription",
    "extract_hkdse_pdf_embedded_pass",
    "load_hkdse_pdf_extraction_pass",
    "propose_hkdse_pdf_transcription",
)

from .v122_models import V122AdaptedImportPackage, V122BatchImportManifest
from .v122_manifest import load_v122_import_manifest


def adapt_verified_hkdse_pdf_transcription_v122(
    verified: VerifiedHkdsePdfTranscriptionBatch,
    output_dir: Path,
    config: PipelineConfig,
) -> V122AdaptedImportPackage:
    if type(verified) is not VerifiedHkdsePdfTranscriptionBatch:
        raise TypeError(
            "verified must be an exact VerifiedHkdsePdfTranscriptionBatch"
        )
    proposal = verified.proposal
    approval = getattr(verified, "approval", None)
    if type(approval) is not HkdsePdfTranscriptionApproval:
        raise PipelineError("verified transcription requires an exact approval")
    try:
        reconstructed_approval = HkdsePdfTranscriptionApproval(
            approval.batch_id,
            approval.transcription_digest,
            approval.approval_text,
        )
    except (AttributeError, PipelineError) as exc:
        raise PipelineError("verified transcription approval is invalid") from exc
    if (
        approval != reconstructed_approval
        or approval.batch_id != proposal.batch_id
        or approval.transcription_digest != proposal.transcription_digest
    ):
        raise PipelineError("verified transcription approval does not bind proposal")
    resolved_output = _validate_output(output_dir, config)
    proposal_root = proposal.artifact_root.resolve(strict=False)
    if (
        resolved_output.is_relative_to(proposal_root)
        or proposal_root.is_relative_to(resolved_output)
    ):
        raise ConfigurationError(
            "canonical output must not overlap transcription artifacts"
        )
    actual_digest = _sha_bytes(
        _canonical_json(_proposal_semantic_payload(proposal)).encode("utf-8")
    )
    if actual_digest != proposal.transcription_digest:
        raise PipelineError("verified proposal semantic payload digest is invalid")
    if proposal.issues or any(
        record.status != "PROPOSED" for record in proposal.records
    ):
        raise PipelineError("verified proposal is not approval-eligible")
    expected_records = tuple(
        replace(record, status="VERIFIED") for record in proposal.records
    )
    if verified.records != expected_records:
        raise PipelineError("verified records do not preserve the proposal")

    candidates = tuple(
        _candidate_payload(proposal.batch_id, record, index)
        for index, record in enumerate(verified.records)
    )
    candidates_bytes = (_canonical_json(list(candidates)) + "\n").encode("utf-8")
    transcription_payload = {
        **_proposal_semantic_payload(proposal),
        "transcription_digest": proposal.transcription_digest,
    }
    transcription_bytes = (
        _canonical_json(transcription_payload) + "\n"
    ).encode("utf-8")
    source_map_bytes = (
        _canonical_json(_source_map_payload_v120(verified)) + "\n"
    ).encode("utf-8")
    answer_bytes = (
        _canonical_json(_answer_payload_v120(verified)) + "\n"
    ).encode("utf-8")
    manifest = V122BatchImportManifest(
        schema_version="task12-v122-import-manifest-v1",
        batch_id=proposal.batch_id,
        project="Joy M2 AI Database",
        module="M2",
        chapter="HKDSE M2",
        target_release_version="V1.22",
        candidate_records=(
            _file_evidence(
                "records/candidates.json", candidates_bytes, "candidate_json"
            ),
        ),
        source_files=(
            _file_evidence(
                "source/transcription.json", transcription_bytes, "source"
            ),
            _file_evidence("source/source-map.json", source_map_bytes, "source"),
        ),
        answer_files=(
            _file_evidence("answers/official-ms.json", answer_bytes, "answer"),
        ),
        image_files=(),
        teacher_notes_files=(),
        common_errors_files=(),
        language_policy="preserve_source_and_store_reviewed_chinese_separately",
        split_policy="one_complete_question_per_record",
        difficulty_policy="joy_level_1_5",
        tag_policy="controlled_primary_type_and_tags",
        answer_policy="preserve_source_answer_identity",
        explanation_policy="source_or_independently_verified_with_identity",
    )
    manifest_bytes = (
        json.dumps(
            _v120_manifest_payload(manifest),
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    files = (
        ("records/candidates.json", candidates_bytes),
        ("source/transcription.json", transcription_bytes),
        ("source/source-map.json", source_map_bytes),
        ("answers/official-ms.json", answer_bytes),
        ("import_manifest.json", manifest_bytes),
    )

    resolved_output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(
        tempfile.mkdtemp(
            prefix=f".{resolved_output.name}-", dir=resolved_output.parent
        )
    )
    try:
        for relative_path, content in files:
            target = temporary / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            _write_private_file(target, content)
        try:
            atomic_rename_no_replace(temporary, resolved_output)
        except OSError as exc:
            if exc.errno in {errno.EEXIST, errno.ENOTEMPTY}:
                raise OutputConflictError("output path already exists") from exc
            raise
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)

    loaded = load_v122_import_manifest(resolved_output / "import_manifest.json")
    if loaded != manifest:
        raise PipelineError("V1.22 package did not round-trip exactly")
    return V122AdaptedImportPackage(
        package_root=resolved_output,
        manifest_path=resolved_output / "import_manifest.json",
        manifest=loaded,
    )


__all__ = (
    "adapt_verified_hkdse_pdf_transcription_v120",
    "adapt_verified_hkdse_pdf_transcription_v122",
    "approve_hkdse_pdf_transcription",
    "extract_hkdse_pdf_embedded_pass",
    "load_hkdse_pdf_extraction_pass",
    "propose_hkdse_pdf_transcription",
)
