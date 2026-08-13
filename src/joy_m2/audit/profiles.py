"""Exact external record profiles for the maintained audit boundary."""

from __future__ import annotations

from collections.abc import Callable

from ..errors import InputFormatError, PipelineError
from ..models import (
    AuditedQuestion,
    AuditedRecord,
    Correction,
    PublicationEvidence,
    QuestionImage,
    ReleaseCompatibility,
    Task4Compatibility,
)


V117_AUDIT_BASE_FIELDS = (
    "question_id",
    "source_id",
    "source_question_number",
    "source_section",
    "source_file",
    "source_member",
    "source_sha256",
    "source_member_sha256",
    "source_fragment_hash",
    "source_page",
    "solution_source_file",
    "solution_source_member",
    "solution_source_member_sha256",
    "question_text_original",
    "question_text_zh",
    "question_latex",
    "marks_total",
    "image_paths",
    "solution_original",
    "solution_verified",
    "answer_status",
    "answer_verification_status",
    "official_marking_available",
    "primary_type",
    "tags",
    "difficulty_level",
    "difficulty_evidence",
    "old_difficulty",
    "old_difficulty_label",
    "old_tags",
    "question_review_status",
    "formula_review_status",
    "image_review_status",
    "answer_review_status",
    "correction_status",
    "corrections",
    "duplicate_status",
    "duplicate_reference",
    "duplicate_evidence",
    "audit_notes",
    "record_status",
    "joy_approval",
    "audited_at",
    "approved_at",
    "schema_version",
    "source_heading",
    "question_text_zh_reviewed",
    "difficulty_dimensions",
    "unresolved_issues",
    "review_checks",
)

V117_TASK4_COMPATIBILITY_FIELDS = (
    "task4_resolution",
    "task4_processed_at",
)

V118_FIELDS = (
    "answer_review_status",
    "answer_status",
    "answer_verification_status",
    "approved_at",
    "audit_notes",
    "audited_at",
    "correction_status",
    "corrections",
    "difficulty_dimensions",
    "difficulty_evidence",
    "difficulty_level",
    "duplicate_evidence",
    "duplicate_reference",
    "duplicate_status",
    "formal_release_version",
    "formula_review_status",
    "image_paths",
    "image_review_status",
    "joy_approval",
    "marks_total",
    "official_marking_available",
    "old_difficulty",
    "old_difficulty_label",
    "old_tags",
    "primary_type",
    "question_id",
    "question_latex",
    "question_review_status",
    "question_text_original",
    "question_text_zh",
    "question_text_zh_reviewed",
    "record_status",
    "review_checks",
    "schema_version",
    "selectable",
    "solution_original",
    "solution_source_file",
    "solution_source_member",
    "solution_source_member_sha256",
    "solution_verified",
    "source_file",
    "source_fragment_hash",
    "source_heading",
    "source_id",
    "source_member",
    "source_member_sha256",
    "source_order",
    "source_page",
    "source_question_number",
    "source_section",
    "source_sha256",
    "tags",
    "unresolved_issues",
    "year",
)

CORRECTION_FIELDS = (
    "field",
    "error_origin",
    "original",
    "corrected",
    "reason",
    "evidence",
)

V117_IMAGE_FIELDS = ("path", "sha256", "role")

STRING_FIELDS = (
    "answer_review_status",
    "answer_status",
    "answer_verification_status",
    "approved_at",
    "audit_notes",
    "audited_at",
    "correction_status",
    "difficulty_evidence",
    "duplicate_evidence",
    "duplicate_reference",
    "duplicate_status",
    "formal_release_version",
    "formula_review_status",
    "image_review_status",
    "joy_approval",
    "old_difficulty_label",
    "primary_type",
    "question_id",
    "question_latex",
    "question_review_status",
    "question_text_original",
    "question_text_zh",
    "question_text_zh_reviewed",
    "record_status",
    "schema_version",
    "solution_original",
    "solution_source_file",
    "solution_source_member",
    "solution_source_member_sha256",
    "solution_verified",
    "source_file",
    "source_fragment_hash",
    "source_heading",
    "source_id",
    "source_member",
    "source_member_sha256",
    "source_page",
    "source_question_number",
    "source_section",
    "source_sha256",
)


def _fail(detail: str) -> InputFormatError:
    return InputFormatError(detail)


def _require_exact_fields(record: object, expected: tuple[str, ...]) -> dict:
    if type(record) is not dict:
        raise _fail("audit profile record must be a JSON object")
    if tuple(record) != expected:
        raise _fail("audit profile record fields or field order do not match")
    return record


def _require_type(value: object, expected: type, field: str) -> None:
    if type(value) is not expected:
        raise _fail(f"{field} has an invalid JSON type")


def _require_optional_int(value: object, field: str) -> None:
    if value is not None and type(value) is not int:
        raise _fail(f"{field} must be an integer or null")


def _require_string_list(value: object, field: str) -> tuple[str, ...]:
    _require_type(value, list, field)
    if any(type(item) is not str for item in value):
        raise _fail(f"{field} must contain only strings")
    return tuple(value)


def _require_string_keyed_object(
    value: object,
    field: str,
    value_check: Callable[[object], bool],
) -> tuple[tuple[str, object], ...]:
    _require_type(value, dict, field)
    if any(type(key) is not str or not value_check(item) for key, item in value.items()):
        raise _fail(f"{field} contains an invalid entry")
    return tuple(value.items())


def _parse_corrections(value: object) -> tuple[Correction, ...]:
    _require_type(value, list, "corrections")
    parsed = []
    for item in value:
        item = _require_exact_fields(item, CORRECTION_FIELDS)
        if any(type(item[field]) is not str for field in CORRECTION_FIELDS):
            raise _fail("correction fields must be strings")
        parsed.append(Correction(**item))
    return tuple(parsed)


def _common_question_values(
    record: dict,
    *,
    year: int | None,
    image_paths: tuple[QuestionImage, ...],
    tags: tuple[str, ...],
    old_tags: tuple[str, ...],
    unresolved_issues: tuple[str, ...],
    difficulty_dimensions: tuple[tuple[str, object], ...],
    review_checks: tuple[tuple[str, object], ...],
) -> dict:
    return {
        "question_id": record["question_id"],
        "source_id": record["source_id"],
        "source_question_number": record["source_question_number"],
        "source_section": record["source_section"],
        "source_file": record["source_file"],
        "source_member": record["source_member"],
        "source_sha256": record["source_sha256"],
        "source_member_sha256": record["source_member_sha256"],
        "source_fragment_hash": record["source_fragment_hash"],
        "source_page": record["source_page"],
        "solution_source_file": record["solution_source_file"],
        "solution_source_member": record["solution_source_member"],
        "solution_source_member_sha256": record["solution_source_member_sha256"],
        "question_text_original": record["question_text_original"],
        "question_text_zh": record["question_text_zh"],
        "question_text_zh_reviewed": record["question_text_zh_reviewed"],
        "question_latex": record["question_latex"],
        "marks_total": record["marks_total"],
        "year": year,
        "image_paths": image_paths,
        "solution_original": record["solution_original"],
        "solution_verified": record["solution_verified"],
        "answer_status": record["answer_status"],
        "answer_verification_status": record["answer_verification_status"],
        "official_marking_available": record["official_marking_available"],
        "primary_type": record["primary_type"],
        "tags": tags,
        "difficulty_level": record["difficulty_level"],
        "difficulty_evidence": record["difficulty_evidence"],
        "difficulty_dimensions": difficulty_dimensions,
        "old_difficulty": record["old_difficulty"],
        "old_difficulty_label": record["old_difficulty_label"],
        "old_tags": old_tags,
        "question_review_status": record["question_review_status"],
        "formula_review_status": record["formula_review_status"],
        "image_review_status": record["image_review_status"],
        "answer_review_status": record["answer_review_status"],
        "correction_status": record["correction_status"],
        "corrections": _parse_corrections(record["corrections"]),
        "duplicate_status": record["duplicate_status"],
        "duplicate_reference": record["duplicate_reference"],
        "duplicate_evidence": record["duplicate_evidence"],
        "audit_notes": record["audit_notes"],
        "review_checks": review_checks,
        "unresolved_issues": unresolved_issues,
        "publication_evidence": PublicationEvidence(
            record_status=record["record_status"],
            joy_approval=record["joy_approval"],
            approved_at=record["approved_at"],
        ),
        "audited_at": record["audited_at"],
        "schema_version": record["schema_version"],
        "source_heading": record["source_heading"],
    }


def parse_v117_record(record: object) -> AuditedRecord:
    if type(record) is not dict:
        raise _fail("audit profile record must be a JSON object")
    fields = tuple(record)
    allowed_fields = {
        V117_AUDIT_BASE_FIELDS,
        V117_AUDIT_BASE_FIELDS + V117_TASK4_COMPATIBILITY_FIELDS,
    }
    if fields not in allowed_fields:
        raise _fail("V1.17 record fields or field order do not match")

    string_fields = (
        set(V117_AUDIT_BASE_FIELDS)
        - {
            "approved_at",
            "corrections",
            "difficulty_dimensions",
            "image_paths",
            "marks_total",
            "official_marking_available",
            "old_tags",
            "review_checks",
            "tags",
            "unresolved_issues",
        }
    )
    string_fields -= {"difficulty_level", "old_difficulty"}
    for field in string_fields:
        _require_type(record[field], str, field)
    _require_optional_int(record["marks_total"], "marks_total")
    for field in ("difficulty_level", "old_difficulty"):
        _require_type(record[field], int, field)
    _require_type(record["official_marking_available"], bool, "official_marking_available")
    if record["approved_at"] is not None:
        raise _fail("V1.17 approved_at must be null")
    if record["record_status"] != "audit_passed" or record["unresolved_issues"] != []:
        raise _fail("V1.17 record is not eligible for Task 2 audit")
    if record["joy_approval"] != "":
        raise _fail("V1.17 joy_approval must be empty")
    if record["schema_version"] != "complete-question-v1.0-draft":
        raise _fail("V1.17 schema_version must be the audit-stage draft")

    images_value = record["image_paths"]
    _require_type(images_value, list, "image_paths")
    images = []
    for image in images_value:
        image = _require_exact_fields(image, V117_IMAGE_FIELDS)
        if type(image["path"]) is not str or not image["path"]:
            raise _fail("V1.17 image path must be a non-empty string")
        for field in ("sha256", "role"):
            if image[field] is not None and type(image[field]) is not str:
                raise _fail(f"V1.17 image {field} must be a string or null")
        try:
            images.append(QuestionImage(**image))
        except PipelineError as error:
            raise _fail("V1.17 image values are invalid") from error

    tags = _require_string_list(record["tags"], "tags")
    old_tags = _require_string_list(record["old_tags"], "old_tags")
    unresolved_issues = _require_string_list(
        record["unresolved_issues"], "unresolved_issues"
    )
    difficulty_dimensions = _require_string_keyed_object(
        record["difficulty_dimensions"],
        "difficulty_dimensions",
        lambda value: type(value) is int,
    )
    review_checks = _require_string_keyed_object(
        record["review_checks"],
        "review_checks",
        lambda value: type(value) is str,
    )
    question = AuditedQuestion(
        **_common_question_values(
            record,
            year=None,
            image_paths=tuple(images),
            tags=tags,
            old_tags=old_tags,
            unresolved_issues=unresolved_issues,
            difficulty_dimensions=difficulty_dimensions,
            review_checks=review_checks,
        )
    )
    has_compatibility = fields == (
        V117_AUDIT_BASE_FIELDS + V117_TASK4_COMPATIBILITY_FIELDS
    )
    for field in V117_TASK4_COMPATIBILITY_FIELDS:
        if has_compatibility and record[field] is not None and type(record[field]) is not str:
            raise _fail(f"{field} must be a string or null")
    return AuditedRecord(
        question=question,
        task4_compatibility=Task4Compatibility(
            task4_resolution_present=has_compatibility,
            task4_resolution=record.get("task4_resolution"),
            task4_processed_at_present=has_compatibility,
            task4_processed_at=record.get("task4_processed_at"),
        ),
        release_compatibility=None,
    )


def parse_v118_record(record: object) -> AuditedRecord:
    record = _require_exact_fields(record, V118_FIELDS)
    for field in STRING_FIELDS:
        _require_type(record[field], str, field)
    for field in ("difficulty_level", "marks_total", "source_order"):
        _require_type(record[field], int, field)
    _require_optional_int(record["old_difficulty"], "old_difficulty")
    _require_optional_int(record["year"], "year")
    for field in ("official_marking_available", "selectable"):
        _require_type(record[field], bool, field)

    image_paths = _require_string_list(record["image_paths"], "image_paths")
    if any(not path for path in image_paths):
        raise _fail("image_paths must contain only non-empty strings")
    tags = _require_string_list(record["tags"], "tags")
    old_tags = _require_string_list(record["old_tags"], "old_tags")
    unresolved_issues = _require_string_list(
        record["unresolved_issues"],
        "unresolved_issues",
    )
    difficulty_dimensions = _require_string_keyed_object(
        record["difficulty_dimensions"],
        "difficulty_dimensions",
        lambda value: type(value) in {int, str},
    )
    review_checks = _require_string_keyed_object(
        record["review_checks"],
        "review_checks",
        lambda value: type(value) in {bool, str},
    )

    question = AuditedQuestion(
        **_common_question_values(
            record,
            year=record["year"],
            image_paths=tuple(QuestionImage(path, None, None) for path in image_paths),
            tags=tags,
            old_tags=old_tags,
            unresolved_issues=unresolved_issues,
            difficulty_dimensions=difficulty_dimensions,
            review_checks=review_checks,
        )
    )
    return AuditedRecord(
        question=question,
        task4_compatibility=None,
        release_compatibility=ReleaseCompatibility(
            formal_release_version=record["formal_release_version"],
            selectable=record["selectable"],
            source_order=record["source_order"],
        ),
    )


def _corrections_value(question: AuditedQuestion) -> list[dict]:
    return [
        {field: getattr(correction, field) for field in CORRECTION_FIELDS}
        for correction in question.corrections
    ]


def _question_external_values(record: AuditedRecord) -> dict:
    question = record.question
    publication = question.publication_evidence
    return {
        field: getattr(question, field)
        for field in (
            "question_id",
            "source_id",
            "source_question_number",
            "source_section",
            "source_file",
            "source_member",
            "source_sha256",
            "source_member_sha256",
            "source_fragment_hash",
            "source_page",
            "solution_source_file",
            "solution_source_member",
            "solution_source_member_sha256",
            "question_text_original",
            "question_text_zh",
            "question_text_zh_reviewed",
            "question_latex",
            "marks_total",
            "year",
            "solution_original",
            "solution_verified",
            "answer_status",
            "answer_verification_status",
            "official_marking_available",
            "primary_type",
            "difficulty_level",
            "difficulty_evidence",
            "old_difficulty",
            "old_difficulty_label",
            "question_review_status",
            "formula_review_status",
            "image_review_status",
            "answer_review_status",
            "correction_status",
            "duplicate_status",
            "duplicate_reference",
            "duplicate_evidence",
            "audit_notes",
            "audited_at",
            "schema_version",
            "source_heading",
        )
    } | {
        "tags": list(question.tags),
        "old_tags": list(question.old_tags),
        "difficulty_dimensions": dict(question.difficulty_dimensions),
        "corrections": _corrections_value(question),
        "review_checks": dict(question.review_checks),
        "unresolved_issues": list(question.unresolved_issues),
        "record_status": publication.record_status,
        "joy_approval": publication.joy_approval,
        "approved_at": publication.approved_at,
    }


def serialize_v117_record(record: AuditedRecord) -> dict:
    if type(record) is not AuditedRecord or record.task4_compatibility is None or record.release_compatibility is not None:
        raise PipelineError("V1.17 serializer requires a V1.17 AuditedRecord")
    values = _question_external_values(record)
    values["image_paths"] = [
        {field: getattr(image, field) for field in V117_IMAGE_FIELDS}
        for image in record.question.image_paths
    ]
    result = {field: values[field] for field in V117_AUDIT_BASE_FIELDS}
    compatibility = record.task4_compatibility
    flag_pair = (
        compatibility.task4_resolution_present,
        compatibility.task4_processed_at_present,
    )
    if flag_pair not in {(False, False), (True, True)}:
        raise PipelineError("V1.17 compatibility presence flags must match")
    if flag_pair == (True, True):
        result["task4_resolution"] = compatibility.task4_resolution
        result["task4_processed_at"] = compatibility.task4_processed_at
    return result


def serialize_v118_record(record: AuditedRecord) -> dict:
    if type(record) is not AuditedRecord or record.task4_compatibility is not None or record.release_compatibility is None:
        raise PipelineError("V1.18 serializer requires a V1.18 AuditedRecord")
    values = _question_external_values(record)
    values["image_paths"] = [image.path for image in record.question.image_paths]
    compatibility = record.release_compatibility
    values.update(
        formal_release_version=compatibility.formal_release_version,
        selectable=compatibility.selectable,
        source_order=compatibility.source_order,
    )
    return {field: values[field] for field in V118_FIELDS}
