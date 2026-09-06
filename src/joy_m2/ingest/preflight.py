import hashlib
import json
from pathlib import Path
import sqlite3
import unicodedata

from joy_m2.errors import PipelineError
from joy_m2.export.formats import canonical_json_bytes
from joy_m2.models import ArtifactRef

from .models import (
    _ANSWER,
    _TAG_DIFFICULTY,
    _canonical_relative,
    _require_sha,
    _require_str,
    _string_tuple,
    _validate_payload_evidence,
    BatchImportManifest,
    ImportAdaptation,
    ImportCandidate,
    ImportFileEvidence,
    ImportIssue,
    ImportPreflightReport,
    ImportPreflightResult,
    as_plain_dict,
)


_RAW_CANDIDATE_FIELDS = frozenset(
    {
        "proposed_question_id",
        "source_id",
        "source_question_number",
        "source_section",
        "source_fragment_hash",
        "question_text_original",
        "question_text_zh",
        "translation_status",
        "translation_evidence",
        "solution_original",
        "solution_verified",
        "answer_status",
        "explanation_text",
        "explanation_status",
        "explanation_evidence",
        "image_paths",
        "image_roles",
        "primary_type",
        "tags",
        "tag_status",
        "difficulty_level",
        "difficulty_status",
        "enrichment_status",
    }
)
_UNSUPPORTED_SOURCE_FORMATS = (
    (".mmd.zip", "mmd_zip"),
    (".mmd", "mmd"),
    (".pdf", "pdf"),
)
_APPROVED_ISSUE_CODES = frozenset(
    {
        "missing_image",
        "orphan_image",
        "unsupported_source_format",
        "unknown_primary_type",
        "unknown_tag",
        "malformed_candidate_json",
        "invalid_candidate_top_level",
        "invalid_candidate_record",
        "duplicate_exact",
        "duplicate_ambiguous",
        "collision_candidate_id",
        "collision_source_locator",
        "collision_fragment_sha256",
        "collision_normalized_text_sha256",
        "collision_image_sha256",
        "file_integrity_mismatch",
    }
)
_ASCII_LINE_WHITESPACE = " \t\v\f"


def _normalize_original_text(value: str) -> str:
    if type(value) is not str:
        raise PipelineError("question_text_original must be a string")
    normalized = unicodedata.normalize("NFC", value).replace("\r\n", "\n").replace("\r", "\n")
    lines = []
    for line in normalized.split("\n"):
        stripped = line.strip(_ASCII_LINE_WHITESPACE)
        collapsed = " ".join(part for part in _split_ascii_whitespace(stripped) if part)
        lines.append(collapsed)
    while lines and lines[0] == "":
        lines.pop(0)
    while lines and lines[-1] == "":
        lines.pop()
    return "\n".join(lines)


def _split_ascii_whitespace(value: str) -> tuple[str, ...]:
    parts: list[str] = []
    start = 0
    for index, character in enumerate(value):
        if character in _ASCII_LINE_WHITESPACE:
            if start != index:
                parts.append(value[start:index])
            start = index + 1
    if start != len(value):
        parts.append(value[start:])
    return tuple(parts)


def _normalized_text_sha256(value: str) -> str:
    return hashlib.sha256(_normalize_original_text(value).encode("utf-8")).hexdigest()


def _source_locator(record: dict[str, object]) -> tuple[str, str, str]:
    values = tuple(record[name] for name in ("source_id", "source_question_number", "source_section"))
    if any(type(value) is not str or not value for value in values):
        raise PipelineError("candidate source locator is invalid")
    return values


def _validate_candidate_record_before_images(
    record: object,
    source_paths: frozenset[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if type(record) is not dict or frozenset(record) != _RAW_CANDIDATE_FIELDS:
        raise PipelineError("candidate record must be an exact canonical object")
    if type(record["image_paths"]) is not list or type(record["image_roles"]) is not list:
        raise PipelineError("candidate image paths and roles must be JSON arrays")
    if type(record["tags"]) is not list:
        raise PipelineError("candidate tags must be a JSON array")

    for name in (
        "proposed_question_id",
        "source_id",
        "source_question_number",
        "source_section",
        "question_text_original",
        "primary_type",
    ):
        _require_str(record[name], name)
    _require_sha(record["source_fragment_hash"], "source_fragment_hash")
    _normalized_text_sha256(record["question_text_original"])
    for name in (
        "question_text_zh",
        "solution_original",
        "solution_verified",
        "explanation_text",
    ):
        _require_str(record[name], name, nonempty=False)

    image_paths = _string_tuple(record["image_paths"], "image_paths", paths=True)
    image_roles = _string_tuple(record["image_roles"], "image_roles")
    if len(image_paths) != len(image_roles):
        raise PipelineError("candidate image paths and roles must have equal length")
    tags = _string_tuple(record["tags"], "tags")

    if record["answer_status"] not in _ANSWER:
        raise PipelineError("answer_status is invalid")
    if record["answer_status"] == "missing_from_source" and (
        record["solution_original"] or record["solution_verified"]
    ):
        raise PipelineError("missing_from_source requires empty solution fields")
    for name, payload_name, evidence_name in (
        ("translation", "question_text_zh", "translation_evidence"),
        ("explanation", "explanation_text", "explanation_evidence"),
    ):
        _validate_payload_evidence(
            record[f"{name}_status"],
            record[payload_name],
            record[evidence_name],
            name,
        )
    if record["tag_status"] not in _TAG_DIFFICULTY:
        raise PipelineError("tag_status is invalid")
    if (record["tag_status"] == "missing") != (len(tags) == 0):
        raise PipelineError("tag_status must match tag availability")
    if record["difficulty_status"] not in _TAG_DIFFICULTY:
        raise PipelineError("difficulty_status is invalid")
    difficulty_level = record["difficulty_level"]
    if difficulty_level is not None and (
        type(difficulty_level) is not int or not 1 <= difficulty_level <= 5
    ):
        raise PipelineError("difficulty_level must be an integer from 1 to 5 or None")
    if (record["difficulty_status"] == "missing") != (difficulty_level is None):
        raise PipelineError("difficulty_status must match difficulty availability")
    if record["enrichment_status"] not in {"complete", "incomplete"}:
        raise PipelineError("enrichment_status is invalid")

    for status_name, evidence_name in (
        ("translation_status", "translation_evidence"),
        ("explanation_status", "explanation_evidence"),
    ):
        if record[status_name] == "source_present":
            evidence = record[evidence_name]
            source_path = evidence[7:].split("#", 1)[0]
            if source_path not in source_paths:
                raise PipelineError(
                    "source-present provenance must resolve to declared source evidence"
                )
    _source_locator(record)
    return image_paths, image_roles


def _candidate_from_record(
    record: object,
    image_files: dict[str, ImportFileEvidence],
    source_paths: frozenset[str],
) -> tuple[ImportCandidate, tuple[str, str, str]]:
    if type(record) is not dict or frozenset(record) != _RAW_CANDIDATE_FIELDS:
        raise PipelineError("candidate record must be an exact canonical object")
    if type(record["image_paths"]) is not list or type(record["image_roles"]) is not list:
        raise PipelineError("candidate image paths and roles must be JSON arrays")
    if type(record["tags"]) is not list:
        raise PipelineError("candidate tags must be a JSON array")

    image_paths = tuple(record["image_paths"])
    image_roles = tuple(record["image_roles"])
    if len(image_paths) != len(image_roles):
        raise PipelineError("candidate image paths and roles must have equal length")
    image_sha256s = tuple(image_files[path].sha256 for path in image_paths)
    candidate = ImportCandidate(
        proposed_question_id=record["proposed_question_id"],
        source_id=record["source_id"],
        source_question_number=record["source_question_number"],
        source_section=record["source_section"],
        source_fragment_hash=record["source_fragment_hash"],
        normalized_text_sha256=_normalized_text_sha256(record["question_text_original"]),
        question_text_original=record["question_text_original"],
        question_text_zh=record["question_text_zh"],
        translation_status=record["translation_status"],
        translation_evidence=record["translation_evidence"],
        solution_original=record["solution_original"],
        solution_verified=record["solution_verified"],
        answer_status=record["answer_status"],
        explanation_text=record["explanation_text"],
        explanation_status=record["explanation_status"],
        explanation_evidence=record["explanation_evidence"],
        image_paths=image_paths,
        image_sha256s=image_sha256s,
        image_roles=image_roles,
        primary_type=record["primary_type"],
        tags=tuple(record["tags"]),
        tag_status=record["tag_status"],
        difficulty_level=record["difficulty_level"],
        difficulty_status=record["difficulty_status"],
        enrichment_status=record["enrichment_status"],
    )
    for status, evidence in (
        (candidate.translation_status, candidate.translation_evidence),
        (candidate.explanation_status, candidate.explanation_evidence),
    ):
        if status == "source_present":
            source_path = evidence[7:].split("#", 1)[0]
            if source_path not in source_paths:
                raise PipelineError("source-present provenance must resolve to declared source evidence")
    return candidate, _source_locator(record)


def _depends_on_untrusted_file(
    record: object,
    untrusted_paths: frozenset[str],
) -> bool:
    if type(record) is not dict:
        return False
    image_paths = record.get("image_paths")
    if type(image_paths) is list and any(
        type(path) is str and path in untrusted_paths for path in image_paths
    ):
        return True
    for status_name, evidence_name in (
        ("translation_status", "translation_evidence"),
        ("explanation_status", "explanation_evidence"),
    ):
        evidence = record.get(evidence_name)
        if (
            record.get(status_name) == "source_present"
            and type(evidence) is str
            and evidence.startswith("source:")
            and "#" in evidence[7:]
            and evidence[7:].split("#", 1)[0] in untrusted_paths
        ):
            return True
    return False


def _prepare_candidate_layer(
    manifest: BatchImportManifest,
    package_bytes: dict[str, bytes],
    primary_types: frozenset[str],
    tags: frozenset[str],
    untrusted_paths: frozenset[str],
    initial_signals: tuple[tuple[object, ...], ...],
) -> tuple[
    tuple[ImportCandidate, ...],
    tuple[ImportFileEvidence, ...],
    tuple[dict[str, object], ...],
    tuple[tuple[str, str, str], ...],
    tuple[tuple[object, ...], ...],
]:
    candidates: list[ImportCandidate] = []
    locators: list[tuple[str, str, str]] = []
    signals = list(initial_signals)
    image_files = {
        item.relative_path: item
        for item in manifest.image_files
        if item.relative_path not in untrusted_paths
    }
    source_paths = frozenset(
        item.relative_path
        for item in manifest.source_files
        if item.relative_path not in untrusted_paths
    )

    for file_evidence in manifest.candidate_records:
        if file_evidence.relative_path in untrusted_paths:
            continue
        try:
            payload = json.loads(package_bytes[file_evidence.relative_path].decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            signals.append(("malformed_candidate_json", file_evidence.relative_path))
            continue
        if type(payload) is not list:
            signals.append(("invalid_candidate_top_level", file_evidence.relative_path))
            continue
        for record_index, record in enumerate(payload):
            if _depends_on_untrusted_file(record, untrusted_paths):
                continue
            try:
                image_paths, image_roles = _validate_candidate_record_before_images(
                    record,
                    source_paths,
                )
            except (KeyError, PipelineError, TypeError):
                signals.append(
                    (
                        "invalid_candidate_record",
                        file_evidence.relative_path,
                        record_index,
                    )
                )
                continue

            missing_bindings = tuple(
                (path, role)
                for path, role in zip(image_paths, image_roles)
                if path not in image_files
            )
            if missing_bindings:
                for path, role in missing_bindings:
                    signals.append(
                        ("missing_image", record["proposed_question_id"], path, role)
                    )
                continue

            try:
                candidate, locator = _candidate_from_record(record, image_files, source_paths)
            except (KeyError, PipelineError, TypeError):
                signals.append(
                    (
                        "invalid_candidate_record",
                        file_evidence.relative_path,
                        record_index,
                    )
                )
                continue
            candidate_index = len(candidates)
            candidates.append(candidate)
            locators.append(locator)
            if candidate.primary_type not in primary_types:
                signals.append(
                    (
                        "unknown_primary_type",
                        candidate_index,
                        candidate.proposed_question_id,
                        candidate.primary_type,
                    )
                )
            unknown_tags = tuple(sorted(set(candidate.tags) - tags))
            if unknown_tags:
                signals.append(
                    (
                        "unknown_tag",
                        candidate_index,
                        candidate.proposed_question_id,
                        unknown_tags,
                    )
                )

    bound_images = {path for candidate in candidates for path in candidate.image_paths}
    for relative_path in sorted(set(image_files) - bound_images):
        signals.append(("orphan_image", relative_path, image_files[relative_path].sha256))
    for evidence in sorted(
        (
            item
            for group in (
                manifest.candidate_records,
                manifest.source_files,
                manifest.answer_files,
                manifest.image_files,
                manifest.teacher_notes_files,
                manifest.common_errors_files,
            )
            for item in group
        ),
        key=lambda item: item.relative_path,
    ):
        normalized_path = evidence.relative_path.lower()
        for suffix, source_format in _UNSUPPORTED_SOURCE_FORMATS:
            if normalized_path.endswith(suffix):
                signals.append(
                    ("unsupported_source_format", evidence.relative_path, source_format)
                )
                break

    image_evidence = tuple(
        {
            "proposed_question_id": candidate.proposed_question_id,
            "relative_path": relative_path,
            "sha256": image_files[relative_path].sha256,
            "size_bytes": image_files[relative_path].size_bytes,
            "kind": image_files[relative_path].kind,
            "role": role,
        }
        for candidate in candidates
        for relative_path, role in zip(candidate.image_paths, candidate.image_roles)
        if relative_path in image_files
    )
    file_evidence = tuple(
        sorted(
            (
                item
                for group in (
                    manifest.candidate_records,
                    manifest.source_files,
                    manifest.answer_files,
                    manifest.image_files,
                    manifest.teacher_notes_files,
                    manifest.common_errors_files,
                )
                for item in group
            ),
            key=lambda item: item.relative_path,
        )
    )
    return tuple(candidates), file_evidence, image_evidence, tuple(locators), tuple(signals)


def _file_projection(evidence: ImportFileEvidence) -> dict[str, object]:
    return {
        "relative_path": evidence.relative_path,
        "sha256": evidence.sha256,
        "size_bytes": evidence.size_bytes,
        "kind": evidence.kind,
    }


def _manifest_projection(manifest: BatchImportManifest) -> dict[str, object]:
    return {
        "schema_version": manifest.schema_version,
        "batch_id": manifest.batch_id,
        "project": manifest.project,
        "module": manifest.module,
        "chapter": manifest.chapter,
        "target_release_version": manifest.target_release_version,
        "candidate_records": [_file_projection(item) for item in manifest.candidate_records],
        "source_files": [_file_projection(item) for item in manifest.source_files],
        "answer_files": [_file_projection(item) for item in manifest.answer_files],
        "image_files": [_file_projection(item) for item in manifest.image_files],
        "teacher_notes_files": [
            _file_projection(item) for item in manifest.teacher_notes_files
        ],
        "common_errors_files": [
            _file_projection(item) for item in manifest.common_errors_files
        ],
        "language_policy": manifest.language_policy,
        "split_policy": manifest.split_policy,
        "difficulty_policy": manifest.difficulty_policy,
        "tag_policy": manifest.tag_policy,
        "answer_policy": manifest.answer_policy,
        "explanation_policy": manifest.explanation_policy,
    }


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _evidence(value: dict[str, object]) -> str:
    return _canonical_json_bytes(value).decode("utf-8")


def _blocking_issue(
    code: str,
    proposed_question_id: str | None,
    field: str,
    evidence: dict[str, object],
) -> ImportIssue:
    return ImportIssue(
        code=code,
        severity="blocking",
        proposed_question_id=proposed_question_id,
        field=field,
        evidence=_evidence(evidence),
    )


def _issues_from_raw_signals(
    raw_signals: tuple[tuple[object, ...], ...],
) -> tuple[ImportIssue, ...]:
    issues: list[ImportIssue] = []
    for signal in raw_signals:
        code = signal[0]
        if code == "malformed_candidate_json":
            _, relative_path = signal
            issues.append(
                _blocking_issue(
                    code,
                    None,
                    "candidate_records",
                    {"relative_path": relative_path},
                )
            )
        elif code == "invalid_candidate_top_level":
            _, relative_path = signal
            issues.append(
                _blocking_issue(
                    code,
                    None,
                    "candidate_records",
                    {"relative_path": relative_path, "expected": "array"},
                )
            )
        elif code == "invalid_candidate_record":
            _, relative_path, record_index = signal
            issues.append(
                _blocking_issue(
                    code,
                    None,
                    "candidate_records",
                    {"relative_path": relative_path, "record_index": record_index},
                )
            )
        elif code == "missing_image":
            _, candidate_id, relative_path, role = signal
            issues.append(
                _blocking_issue(
                    code,
                    None,
                    "images",
                    {
                        "candidate_id": candidate_id,
                        "relative_path": relative_path,
                        "role": role,
                    },
                )
            )
        elif code == "orphan_image":
            _, relative_path, sha256 = signal
            issues.append(
                _blocking_issue(
                    code,
                    None,
                    "images",
                    {"relative_path": relative_path, "sha256": sha256},
                )
            )
        elif code == "unsupported_source_format":
            _, relative_path, source_format = signal
            issues.append(
                _blocking_issue(
                    code,
                    None,
                    "source_format",
                    {"relative_path": relative_path, "format": source_format},
                )
            )
        elif code == "unknown_primary_type":
            _, _, candidate_id, value = signal
            issues.append(
                _blocking_issue(
                    code,
                    candidate_id,
                    "primary_type",
                    {"candidate_id": candidate_id, "value": value},
                )
            )
        elif code == "unknown_tag":
            _, _, candidate_id, unknown_tags = signal
            issues.append(
                _blocking_issue(
                    code,
                    candidate_id,
                    "tags",
                    {"candidate_id": candidate_id, "unknown_tags": unknown_tags},
                )
            )
        elif code == "file_integrity_mismatch":
            (
                _,
                relative_path,
                expected_sha256,
                actual_sha256,
                expected_size_bytes,
                actual_size_bytes,
            ) = signal
            issues.append(
                _blocking_issue(
                    code,
                    None,
                    "file_integrity",
                    {
                        "relative_path": relative_path,
                        "expected_sha256": expected_sha256,
                        "actual_sha256": actual_sha256,
                        "expected_size_bytes": expected_size_bytes,
                        "actual_size_bytes": actual_size_bytes,
                    },
                )
            )
        else:
            raise PipelineError("C4 produced an unapproved blocking signal")
    return tuple(issues)


def _baseline_images(value: object) -> tuple[tuple[str, str | None, str | None], ...]:
    if type(value) is not str:
        raise PipelineError("baseline image identity must be JSON text")
    try:
        payload = json.loads(value)
    except json.JSONDecodeError as exc:
        raise PipelineError("baseline image identity is malformed") from exc
    if type(payload) is not list:
        raise PipelineError("baseline image identity must be an array")
    identities: list[tuple[str, str | None, str | None]] = []
    for item in payload:
        if type(item) is str:
            identities.append((_canonical_relative(item, "baseline image path"), None, None))
            continue
        if type(item) is not dict or frozenset(item) != {"path", "role", "sha256"}:
            raise PipelineError("baseline image identity entry is invalid")
        identities.append(
            (
                _canonical_relative(item["path"], "baseline image path"),
                _require_str(item["role"], "baseline image role"),
                _require_sha(item["sha256"], "baseline image sha256"),
            )
        )
    return tuple(identities)


def _append_index(index: dict[object, list[str]], key: object, question_id: str) -> None:
    index.setdefault(key, []).append(question_id)


def _build_baseline_indexes(
    rows: tuple[tuple[object, ...], ...],
) -> dict[str, object]:
    references: dict[str, dict[str, object]] = {}
    locator_index: dict[object, list[str]] = {}
    fragment_index: dict[object, list[str]] = {}
    normalized_index: dict[object, list[str]] = {}
    image_binding_index: dict[object, list[str]] = {}
    image_identity_index: dict[object, list[str]] = {}

    for row in rows:
        (
            question_id,
            source_id,
            source_question_number,
            source_section,
            source_fragment_sha256,
            question_text_original,
            image_paths_json,
            _,
        ) = row
        question_id = _require_str(question_id, "baseline question_id")
        locator = (
            _require_str(source_id, "baseline source_id"),
            _require_str(source_question_number, "baseline source_question_number"),
            _require_str(source_section, "baseline source_section"),
        )
        source_fragment_sha256 = _require_sha(
            source_fragment_sha256,
            "baseline source_fragment_hash",
        )
        normalized_text_sha256 = _normalized_text_sha256(
            _require_str(question_text_original, "baseline question_text_original")
        )
        images = _baseline_images(image_paths_json)
        reference = {
            "question_id": question_id,
            "locator": locator,
            "source_fragment_sha256": source_fragment_sha256,
            "normalized_text_sha256": normalized_text_sha256,
            "images": images,
            "baseline": True,
        }
        references[question_id] = reference
        _append_index(locator_index, locator, question_id)
        _append_index(fragment_index, source_fragment_sha256, question_id)
        _append_index(normalized_index, normalized_text_sha256, question_id)
        for path, role, sha256 in images:
            if role is None or sha256 is None:
                continue
            _append_index(image_binding_index, (path, role), question_id)
            _append_index(image_identity_index, (path, role, sha256), question_id)

    return {
        "references": references,
        "question_id": {question_id: (question_id,) for question_id in references},
        "source_locator": {
            key: tuple(sorted(values)) for key, values in locator_index.items()
        },
        "source_fragment_sha256": {
            key: tuple(sorted(values)) for key, values in fragment_index.items()
        },
        "normalized_text_sha256": {
            key: tuple(sorted(values)) for key, values in normalized_index.items()
        },
        "image_binding": {
            key: tuple(sorted(values)) for key, values in image_binding_index.items()
        },
        "image_identity": {
            key: tuple(sorted(values)) for key, values in image_identity_index.items()
        },
    }


def _candidate_reference(candidate: ImportCandidate) -> dict[str, object]:
    return {
        "question_id": candidate.proposed_question_id,
        "locator": (
            candidate.source_id,
            candidate.source_question_number,
            candidate.source_section,
        ),
        "source_fragment_sha256": candidate.source_fragment_hash,
        "normalized_text_sha256": candidate.normalized_text_sha256,
        "images": tuple(
            zip(candidate.image_paths, candidate.image_roles, candidate.image_sha256s)
        ),
        "baseline": False,
    }


def _candidate_images(candidate: ImportCandidate) -> tuple[tuple[str, str, str], ...]:
    return tuple(zip(candidate.image_paths, candidate.image_roles, candidate.image_sha256s))


def _is_exact_duplicate(candidate: ImportCandidate, reference: dict[str, object]) -> bool:
    return bool(reference["baseline"]) and (
        (
            candidate.source_id,
            candidate.source_question_number,
            candidate.source_section,
        )
        == reference["locator"]
        and candidate.source_fragment_hash == reference["source_fragment_sha256"]
        and candidate.normalized_text_sha256 == reference["normalized_text_sha256"]
        and _candidate_images(candidate) == reference["images"]
    )


def _duplicate_issue(candidate: ImportCandidate, reference: dict[str, object]) -> ImportIssue:
    return _blocking_issue(
        "duplicate_exact",
        candidate.proposed_question_id,
        "candidate",
        {
            "candidate_id": candidate.proposed_question_id,
            "reference_question_id": reference["question_id"],
            "normalized_text_sha256": candidate.normalized_text_sha256,
        },
    )


def _candidate_id_issue(
    candidate: ImportCandidate,
    reference: dict[str, object],
) -> ImportIssue:
    return _blocking_issue(
        "collision_candidate_id",
        candidate.proposed_question_id,
        "proposed_question_id",
        {
            "candidate_id": candidate.proposed_question_id,
            "reference_question_id": reference["question_id"],
            "candidate_fragment_sha256": candidate.source_fragment_hash,
            "reference_fragment_sha256": reference["source_fragment_sha256"],
        },
    )


def _image_collision_issues(
    candidate: ImportCandidate,
    reference: dict[str, object],
) -> tuple[ImportIssue, ...]:
    issues: list[ImportIssue] = []
    reference_bindings = {
        (path, role): sha256
        for path, role, sha256 in reference["images"]
        if role is not None and sha256 is not None
    }
    for path, role, sha256 in _candidate_images(candidate):
        reference_sha256 = reference_bindings.get((path, role))
        if reference_sha256 is None or reference_sha256 == sha256:
            continue
        issues.append(
            _blocking_issue(
                "collision_image_sha256",
                candidate.proposed_question_id,
                "image_sha256s",
                {
                    "candidate_id": candidate.proposed_question_id,
                    "candidate_image_path": path,
                    "candidate_image_role": role,
                    "candidate_image_sha256": sha256,
                    "reference_question_id": reference["question_id"],
                    "reference_image_path": path,
                    "reference_image_role": role,
                    "reference_image_sha256": reference_sha256,
                },
            )
        )
    return tuple(issues)


def _collision_issues(
    candidate: ImportCandidate,
    reference: dict[str, object],
    signals: frozenset[str],
) -> tuple[ImportIssue, ...]:
    issues: list[ImportIssue] = []
    candidate_locator = (
        candidate.source_id,
        candidate.source_question_number,
        candidate.source_section,
    )
    reference_locator = reference["locator"]
    if "candidate_id" in signals:
        issues.append(_candidate_id_issue(candidate, reference))
    if "source_locator" in signals and (
        candidate.source_fragment_hash != reference["source_fragment_sha256"]
        or candidate.normalized_text_sha256 != reference["normalized_text_sha256"]
        or _candidate_images(candidate) != reference["images"]
    ):
        issues.append(
            _blocking_issue(
                "collision_source_locator",
                candidate.proposed_question_id,
                "source_locator",
                {
                    "candidate_id": candidate.proposed_question_id,
                    "candidate_source_locator": candidate_locator,
                    "candidate_fragment_sha256": candidate.source_fragment_hash,
                    "reference_question_id": reference["question_id"],
                    "reference_source_locator": reference_locator,
                    "reference_fragment_sha256": reference["source_fragment_sha256"],
                },
            )
        )
    if "source_fragment_sha256" in signals:
        issues.append(
            _blocking_issue(
                "collision_fragment_sha256",
                candidate.proposed_question_id,
                "source_fragment_hash",
                {
                    "candidate_id": candidate.proposed_question_id,
                    "candidate_source_locator": candidate_locator,
                    "reference_question_id": reference["question_id"],
                    "reference_source_locator": reference_locator,
                    "source_fragment_sha256": candidate.source_fragment_hash,
                },
            )
        )
    if "normalized_text_sha256" in signals:
        issues.append(
            _blocking_issue(
                "collision_normalized_text_sha256",
                candidate.proposed_question_id,
                "normalized_text_sha256",
                {
                    "candidate_id": candidate.proposed_question_id,
                    "reference_question_id": reference["question_id"],
                    "normalized_text_sha256": candidate.normalized_text_sha256,
                },
            )
        )
    issues.extend(_image_collision_issues(candidate, reference))
    return tuple(issues)


def _ambiguous_issue(
    candidate: ImportCandidate,
    matches: dict[str, set[str]],
) -> ImportIssue:
    return _blocking_issue(
        "duplicate_ambiguous",
        candidate.proposed_question_id,
        "duplicate",
        {
            "candidate_id": candidate.proposed_question_id,
            "matches": [
                {
                    "reference_question_id": reference_question_id,
                    "signals": sorted(matches[reference_question_id]),
                }
                for reference_question_id in sorted(matches)
            ],
        },
    )


def _adaptation(
    candidate: ImportCandidate,
    reference: dict[str, object],
) -> ImportAdaptation:
    return ImportAdaptation(
        candidate_id=candidate.proposed_question_id,
        reference_question_id=reference["question_id"],
        adaptation_kind="adapted",
        evidence=(
            "matched=source_locator+source_fragment_hash;"
            f"candidate_normalized_text_sha256={candidate.normalized_text_sha256};"
            "reference_normalized_text_sha256="
            f"{reference['normalized_text_sha256']}"
        ),
        reason="stable_source_identity_matches_with_transformed_text",
    )


def _classification(
    candidate: ImportCandidate,
    classification: str,
    issue: ImportIssue | None = None,
    reference_question_id: str | None = None,
) -> dict[str, object]:
    return {
        "candidate_id": candidate.proposed_question_id,
        "classification": classification,
        "reference_question_id": reference_question_id,
        "evidence": None if issue is None else issue.evidence,
    }


def _c5_candidate_layer(
    candidates: tuple[ImportCandidate, ...],
    raw_signals: tuple[tuple[object, ...], ...],
    baseline_indexes: dict[str, object],
) -> tuple[
    tuple[ImportIssue, ...],
    tuple[ImportAdaptation, ...],
    tuple[dict[str, object], ...],
]:
    issues: list[ImportIssue] = list(_issues_from_raw_signals(raw_signals))
    candidate_signal_issues: dict[int, list[ImportIssue]] = {}
    for signal in raw_signals:
        if signal[0] in {"unknown_primary_type", "unknown_tag"}:
            candidate_signal_issues.setdefault(signal[1], []).extend(
                _issues_from_raw_signals((signal,))
            )
    adaptations: list[ImportAdaptation] = []
    classifications: list[dict[str, object]] = []
    references: dict[str, dict[str, object]] = baseline_indexes["references"]
    prior_candidates: dict[str, ImportCandidate] = {}

    for candidate_index, candidate in enumerate(candidates):
        existing_candidate_issues = candidate_signal_issues.get(candidate_index, [])
        new_candidate_issues: list[ImportIssue] = []
        candidate_locator = (
            candidate.source_id,
            candidate.source_question_number,
            candidate.source_section,
        )
        candidate_images = _candidate_images(candidate)
        match_references = dict(references)
        matches: dict[str, set[str]] = {}

        def add_matches(index_name: str, key: object, signal: str) -> None:
            index = baseline_indexes[index_name]
            for question_id in index.get(key, ()):
                matches.setdefault(question_id, set()).add(signal)

        add_matches("question_id", candidate.proposed_question_id, "candidate_id")
        add_matches("source_locator", candidate_locator, "source_locator")
        add_matches(
            "source_fragment_sha256",
            candidate.source_fragment_hash,
            "source_fragment_sha256",
        )
        add_matches(
            "normalized_text_sha256",
            candidate.normalized_text_sha256,
            "normalized_text_sha256",
        )
        for path, role, sha256 in candidate_images:
            add_matches("image_binding", (path, role), "image_sha256")
            add_matches("image_identity", (path, role, sha256), "image_sha256")

        prior = prior_candidates.get(candidate.proposed_question_id)
        if prior is not None:
            prior_reference = _candidate_reference(prior)
            reference_id = prior.proposed_question_id
            match_references.setdefault(reference_id, prior_reference)
            matches.setdefault(reference_id, set()).add("candidate_id")

        exact_references = [
            match_references[question_id]
            for question_id in sorted(matches)
            if _is_exact_duplicate(candidate, match_references[question_id])
        ]
        exact_issue: ImportIssue | None = None
        ambiguous_issue: ImportIssue | None = None
        adaptation: ImportAdaptation | None = None

        if len(exact_references) > 1:
            ambiguous_issue = _ambiguous_issue(candidate, matches)
            new_candidate_issues.append(ambiguous_issue)
        elif len(exact_references) == 1:
            exact_reference = exact_references[0]
            exact_issue = _duplicate_issue(candidate, exact_reference)
            new_candidate_issues.append(exact_issue)
            for question_id in sorted(matches):
                reference = match_references[question_id]
                if reference["question_id"] == exact_reference["question_id"]:
                    continue
                new_candidate_issues.extend(
                    _collision_issues(candidate, reference, frozenset(matches[question_id]))
                )
        elif len(matches) > 1:
            ambiguous_issue = _ambiguous_issue(candidate, matches)
            new_candidate_issues.append(ambiguous_issue)
        elif len(matches) == 1:
            question_id = next(iter(matches))
            reference = match_references[question_id]
            signals = frozenset(matches[question_id])
            is_adaptation = (
                bool(reference["baseline"])
                and candidate_locator == reference["locator"]
                and candidate.source_fragment_hash == reference["source_fragment_sha256"]
                and candidate.normalized_text_sha256
                != reference["normalized_text_sha256"]
                and "candidate_id" not in signals
            )
            if is_adaptation:
                adaptation = _adaptation(candidate, reference)
                adaptations.append(adaptation)
                new_candidate_issues.extend(_image_collision_issues(candidate, reference))
            else:
                new_candidate_issues.extend(
                    _collision_issues(candidate, reference, signals)
                )

        candidate_issues = sorted(
            existing_candidate_issues + new_candidate_issues,
            key=lambda issue: (
                issue.proposed_question_id or "",
                issue.code,
                issue.field,
                issue.evidence,
            ),
        )
        issues.extend(new_candidate_issues)
        independent_blockers = [
            issue for issue in candidate_issues if issue.code != "duplicate_exact"
        ]
        if ambiguous_issue is not None:
            classifications.append(
                _classification(candidate, "rejected", ambiguous_issue)
            )
        elif exact_issue is not None:
            classifications.append(
                _classification(
                    candidate,
                    "rejected" if independent_blockers else "duplicate",
                    exact_issue,
                    exact_references[0]["question_id"],
                )
            )
        elif independent_blockers:
            first_issue = independent_blockers[0]
            evidence_object = json.loads(first_issue.evidence)
            reference_question_id = evidence_object.get("reference_question_id")
            classifications.append(
                _classification(
                    candidate,
                    "rejected",
                    first_issue,
                    reference_question_id,
                )
            )
        else:
            classifications.append(_classification(candidate, "new_candidate"))

        prior_candidates.setdefault(candidate.proposed_question_id, candidate)

    return (
        tuple(
            sorted(
                issues,
                key=lambda issue: (
                    issue.proposed_question_id or "",
                    issue.code,
                    issue.field,
                    issue.evidence,
                ),
            )
        ),
        tuple(
            sorted(
                adaptations,
                key=lambda item: (
                    item.candidate_id,
                    item.reference_question_id,
                    item.adaptation_kind,
                    item.evidence,
                    item.reason,
                ),
            )
        ),
        tuple(classifications),
    )


def _manifest_sha256(manifest: BatchImportManifest) -> str:
    return hashlib.sha256(_canonical_json_bytes(_manifest_projection(manifest)) + b"\n").hexdigest()


def _file_integrity_signal(
    evidence: ImportFileEvidence,
    actual_bytes: bytes,
) -> tuple[object, ...] | None:
    actual_sha256 = hashlib.sha256(actual_bytes).hexdigest()
    actual_size_bytes = len(actual_bytes)
    if actual_size_bytes == evidence.size_bytes and actual_sha256 == evidence.sha256:
        return None
    return (
        "file_integrity_mismatch",
        evidence.relative_path,
        evidence.sha256,
        actual_sha256,
        evidence.size_bytes,
        actual_size_bytes,
    )


def _report_values(
    manifest: BatchImportManifest,
    candidates: tuple[ImportCandidate, ...],
    issues: tuple[ImportIssue, ...],
    adaptations: tuple[ImportAdaptation, ...],
    classifications: tuple[dict[str, object], ...],
    file_evidence: tuple[ImportFileEvidence, ...],
    raw_signals: tuple[tuple[object, ...], ...],
) -> dict[str, object]:
    if any(issue.code not in _APPROVED_ISSUE_CODES for issue in issues):
        raise PipelineError("preflight produced an unapproved issue code")
    classification_counts = {
        name: sum(item["classification"] == name for item in classifications)
        for name in ("new_candidate", "duplicate", "rejected")
    }
    ambiguous_evidence = frozenset(
        issue.evidence
        for issue in issues
        if issue.code == "duplicate_ambiguous"
    )
    ambiguous_occurrences = tuple(
        item["classification"] == "rejected"
        and item["reference_question_id"] is None
        and item["evidence"] in ambiguous_evidence
        for item in classifications
    )
    level_counts = tuple(
        (level, sum(candidate.difficulty_level == level for candidate in candidates))
        for level in range(1, 6)
        if any(candidate.difficulty_level == level for candidate in candidates)
    )

    def issue_paths(code: str) -> tuple[str, ...]:
        return tuple(
            json.loads(issue.evidence)["relative_path"]
            for issue in issues
            if issue.code == code
        )

    return {
        "batch_id": manifest.batch_id,
        "status": (
            "BLOCKED — IMPORT PREFLIGHT FAILED"
            if any(issue.severity == "blocking" for issue in issues)
            else "READY FOR USER IMPORT APPROVAL"
        ),
        "manifest_sha256": _manifest_sha256(manifest),
        "baseline_version": "V1.18",
        "before_count": 497,
        "target_release_version": manifest.target_release_version,
        "detected_count": len(candidates),
        "new_candidate_count": classification_counts["new_candidate"],
        "duplicate_count": classification_counts["duplicate"],
        "rejected_count": classification_counts["rejected"],
        "ambiguous_count": sum(ambiguous_occurrences),
        "approved_count": 0,
        "projected_after_count": 497 + classification_counts["new_candidate"],
        "readable_files": tuple(item.relative_path for item in file_evidence),
        "unreadable_files": (),
        "unsupported_files": tuple(sorted(issue_paths("unsupported_source_format"))),
        "teacher_notes_file_count": len(manifest.teacher_notes_files),
        "common_errors_file_count": len(manifest.common_errors_files),
        "ambiguous_splits": tuple(
            candidate.proposed_question_id
            for candidate, is_ambiguous in zip(candidates, ambiguous_occurrences)
            if is_ambiguous
        ),
        "missing_answers": tuple(
            candidate.proposed_question_id
            for candidate in candidates
            if candidate.answer_status == "missing_from_source"
        ),
        "missing_explanations": tuple(
            candidate.proposed_question_id
            for candidate in candidates
            if candidate.explanation_status == "missing"
        ),
        "incomplete_enrichments": tuple(
            candidate.proposed_question_id
            for candidate in candidates
            if candidate.enrichment_status == "incomplete"
        ),
        "missing_images": tuple(
            signal[2] for signal in raw_signals if signal[0] == "missing_image"
        ),
        "orphan_images": tuple(sorted(issue_paths("orphan_image"))),
        "level_counts": level_counts,
        "proposed_ids": tuple(candidate.proposed_question_id for candidate in candidates),
        "adaptations": adaptations,
        "warnings": (),
        "blocking_errors": tuple(
            issue.code for issue in issues if issue.severity == "blocking"
        ),
    }


def _preflight_payload(
    manifest: BatchImportManifest,
    baseline_database: ArtifactRef,
    candidates: tuple[ImportCandidate, ...],
    issues: tuple[ImportIssue, ...],
    classifications: tuple[dict[str, object], ...],
    file_evidence: tuple[ImportFileEvidence, ...],
    image_evidence: tuple[dict[str, object], ...],
    report_values: dict[str, object],
) -> dict[str, object]:
    return {
        "schema": "task9-preflight-v1",
        "batch_id": manifest.batch_id,
        "target_release_version": manifest.target_release_version,
        "baseline": {
            "release_version": "V1.18",
            "schema_version": "complete-question-v1.0",
            "question_count": 497,
            "sha256": baseline_database.sha256,
            "size_bytes": baseline_database.size_bytes,
            "kind": baseline_database.kind,
        },
        "manifest_policies": {
            "schema_version": manifest.schema_version,
            "project": manifest.project,
            "module": manifest.module,
            "chapter": manifest.chapter,
            "language_policy": manifest.language_policy,
            "split_policy": manifest.split_policy,
            "difficulty_policy": manifest.difficulty_policy,
            "tag_policy": manifest.tag_policy,
            "answer_policy": manifest.answer_policy,
            "explanation_policy": manifest.explanation_policy,
        },
        "candidate_record_order": [
            item.relative_path for item in manifest.candidate_records
        ],
        "file_evidence": [as_plain_dict(item) for item in file_evidence],
        "candidates": [as_plain_dict(candidate) for candidate in candidates],
        "issues": [as_plain_dict(issue) for issue in issues],
        "duplicate_classifications": list(classifications),
        "image_evidence": list(image_evidence),
        "report": {
            name: (
                [as_plain_dict(item) for item in value]
                if name == "adaptations"
                else value
            )
            for name, value in report_values.items()
        },
    }


def preflight_import(
    manifest: BatchImportManifest,
    package_root: Path,
    baseline_database: ArtifactRef,
) -> ImportPreflightResult:
    if type(manifest) is not BatchImportManifest:
        raise PipelineError("manifest must be a BatchImportManifest")
    if manifest.target_release_version != "V1.19":
        raise PipelineError("target_release_version must equal 'V1.19'")
    if not isinstance(package_root, Path):
        raise PipelineError("package_root must be a Path")
    if not package_root.exists():
        raise PipelineError("package_root must exist")
    if not package_root.is_dir():
        raise PipelineError("package_root must be a directory")

    try:
        resolved_root = package_root.resolve()
    except (OSError, RuntimeError) as exc:
        raise PipelineError("package_root cannot be resolved safely") from exc

    declared_groups = (
        manifest.candidate_records,
        manifest.source_files,
        manifest.answer_files,
        manifest.image_files,
        manifest.teacher_notes_files,
        manifest.common_errors_files,
    )
    package_bytes: dict[str, bytes] = {}
    integrity_signals: list[tuple[object, ...]] = []
    untrusted_paths: set[str] = set()
    for group in declared_groups:
        for evidence in group:
            if type(evidence.relative_path) is not str:
                raise PipelineError("declared package path must be a string")
            declared_path = Path(evidence.relative_path)
            if declared_path.is_absolute() or ".." in declared_path.parts:
                raise PipelineError("declared package path must remain relative")
            try:
                resolved_path = (package_root / declared_path).resolve()
                resolved_path.relative_to(resolved_root)
            except (OSError, RuntimeError, ValueError) as exc:
                raise PipelineError("declared package path escapes package_root") from exc

            try:
                if not resolved_path.exists():
                    raise PipelineError("declared package file must exist")
                if not resolved_path.is_file():
                    raise PipelineError("declared package path must be a regular file")
                actual_bytes = resolved_path.read_bytes()
            except PipelineError:
                raise
            except (OSError, RuntimeError) as exc:
                raise PipelineError("declared package file cannot be read") from exc

            integrity_signal = _file_integrity_signal(evidence, actual_bytes)
            if integrity_signal is not None:
                integrity_signals.append(integrity_signal)
                untrusted_paths.add(evidence.relative_path)
                continue
            package_bytes[evidence.relative_path] = actual_bytes

    if type(baseline_database) is not ArtifactRef:
        raise PipelineError("baseline_database must be an ArtifactRef")
    if baseline_database.kind != "sqlite":
        raise PipelineError("baseline_database kind must be 'sqlite'")
    if (
        type(baseline_database.sha256) is not str
        or len(baseline_database.sha256) != 64
        or any(character not in "0123456789abcdef" for character in baseline_database.sha256)
    ):
        raise PipelineError("baseline_database sha256 must be a lowercase SHA-256 digest")
    if type(baseline_database.size_bytes) is not int or baseline_database.size_bytes < 0:
        raise PipelineError("baseline_database size_bytes must be a non-negative integer")
    if not isinstance(baseline_database.path, Path):
        raise PipelineError("baseline_database path must be a Path")

    try:
        baseline_path = baseline_database.path.resolve()
        if not baseline_path.exists():
            raise PipelineError("baseline database file must exist")
        if not baseline_path.is_file():
            raise PipelineError("baseline database path must be a regular file")
        baseline_bytes = baseline_path.read_bytes()
    except PipelineError:
        raise
    except (OSError, RuntimeError) as exc:
        raise PipelineError("baseline database file cannot be read") from exc

    if len(baseline_bytes) != baseline_database.size_bytes:
        raise PipelineError("baseline database size does not match ArtifactRef")
    if hashlib.sha256(baseline_bytes).hexdigest() != baseline_database.sha256:
        raise PipelineError("baseline database SHA-256 does not match ArtifactRef")

    connection = None
    try:
        connection = sqlite3.connect(f"{baseline_path.as_uri()}?mode=ro", uri=True)
        integrity = connection.execute("PRAGMA integrity_check").fetchone()
        if integrity != ("ok",):
            raise PipelineError("baseline database integrity check failed")
        if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise PipelineError("baseline database foreign-key check failed")

        metadata = dict(
            connection.execute(
                "SELECT key, value FROM release_metadata_v2 "
                "WHERE key IN ('release_version', 'schema_version')"
            )
        )
        if metadata.get("release_version") != "V1.18":
            raise PipelineError("baseline database release_version must be 'V1.18'")
        if metadata.get("schema_version") != "complete-question-v1.0":
            raise PipelineError(
                "baseline database schema_version must be 'complete-question-v1.0'"
            )

        rows = connection.execute(
            "SELECT question_id, source_id, source_question_number, source_section, "
            "source_fragment_hash, question_text_original, image_paths_json, source_order "
            "FROM complete_questions_v2 ORDER BY source_order"
        ).fetchall()
        if len(rows) != 497:
            raise PipelineError("baseline database must contain exactly 497 complete questions")
        if tuple(row[7] for row in rows) != tuple(range(1, 498)):
            raise PipelineError("baseline database source_order must be exactly 1 through 497")
        if len({row[0] for row in rows}) != 497:
            raise PipelineError("baseline database question_id values must be unique")
        if len({row[4] for row in rows}) != 497:
            raise PipelineError("baseline database source_fragment_hash values must be unique")
        if any(
            type(value) is not str or not value
            for row in rows
            for value in row[1:4]
        ):
            raise PipelineError("baseline database source identity is invalid")
        baseline_indexes = _build_baseline_indexes(tuple(rows))
        taxonomy_rows = connection.execute(
            "SELECT taxonomy_kind, value FROM complete_question_taxonomy_v2 "
            "ORDER BY taxonomy_kind, sort_order, value"
        ).fetchall()
        primary_types = frozenset(
            value for kind, value in taxonomy_rows if kind == "primary_type"
        ) | {"代数"}
        tags = frozenset(value for kind, value in taxonomy_rows if kind == "tag") | {
            "一元一次方程"
        }
    except PipelineError:
        raise
    except sqlite3.Error as exc:
        raise PipelineError("baseline database cannot be validated read-only") from exc
    finally:
        if connection is not None:
            connection.close()
    candidates, file_evidence, image_evidence, _, raw_signals = _prepare_candidate_layer(
        manifest,
        package_bytes,
        primary_types,
        tags,
        frozenset(untrusted_paths),
        tuple(sorted(integrity_signals, key=lambda signal: signal[1:])),
    )
    issues, adaptations, classifications = _c5_candidate_layer(
        candidates,
        raw_signals,
        baseline_indexes,
    )
    report_values = _report_values(
        manifest,
        candidates,
        issues,
        adaptations,
        classifications,
        file_evidence,
        raw_signals,
    )
    payload = _preflight_payload(
        manifest,
        baseline_database,
        candidates,
        issues,
        classifications,
        file_evidence,
        image_evidence,
        report_values,
    )
    preflight_sha256 = hashlib.sha256(canonical_json_bytes(payload) + b"\n").hexdigest()
    report = ImportPreflightReport(
        preflight_sha256=preflight_sha256,
        **report_values,
    )
    return ImportPreflightResult(
        manifest=manifest,
        baseline_database=baseline_database,
        candidates=candidates,
        issues=issues,
        report=report,
    )
