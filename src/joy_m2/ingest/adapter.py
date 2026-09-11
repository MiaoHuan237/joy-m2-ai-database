import hashlib
import json
from dataclasses import replace
import os
from pathlib import Path
from pathlib import PurePosixPath
import re
import shutil
import tempfile
import unicodedata

from joy_m2.config import PipelineConfig
from joy_m2.errors import (
    ConfigurationError,
    InputMissingError,
    OutputConflictError,
)
from joy_m2.ingest.models import BatchImportManifest, ImportFileEvidence

from .adapter_models import (
    AdaptedImportPackage,
    MmdAdapterBlockedError,
    MmdAdapterIssue,
    MmdAdapterManifest,
    MmdSelection,
)
from .archive import read_selected_source
from .mmd_parser import (
    _SourceDocument,
    _SourceMember,
    _SourceQuestion,
    _SourceSpan,
    _parse_answers,
    _parse_source_document_with_inventory,
)


_TOP_FIELDS = (
    "schema_version",
    "batch_id",
    "source_kind",
    "source_sha256",
    "primary_member",
    "answer_member",
    "source_id",
    "chapter",
    "expected_candidate_count",
    "selections",
)
_SELECTION_FIELDS = (
    "proposed_question_id",
    "kind",
    "number",
    "source_section",
    "language_layout",
    "answer_mapping",
    "answer_number",
    "expected_image_members",
    "primary_type",
    "tags",
    "tag_status",
    "difficulty_level",
    "difficulty_status",
)
_ENUMS = {
    "source_kind": ("mmd", "mmd_zip"),
    "kind": ("example", "exercise"),
    "language_layout": ("english_then_chinese", "interleaved_bilingual"),
    "answer_mapping": ("source_answer", "missing_from_source"),
    "tag_status": ("source_provided", "proposed", "missing"),
    "difficulty_status": ("source_provided", "proposed", "missing"),
}
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
_SHA256 = re.compile(r"[0-9a-f]{64}")
_ABSOLUTE_DRIVE = re.compile(r"[A-Za-z]:[\\/]")
_MEMBER_DRIVE = re.compile(r"[A-Za-z]:")
_IDENTIFIER = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")


class _PairsObject:
    def __init__(self, pairs):
        self.pairs = tuple(pairs)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _issue(field: str, actual: object, expected: object, reason: str) -> MmdAdapterIssue:
    return MmdAdapterIssue(
        code="source_contract_mismatch",
        severity="blocking",
        proposed_question_id=None,
        source_locator="",
        field=field,
        evidence=_canonical_json(
            {"actual": actual, "expected": expected, "reason": reason}
        ),
    )


def _is_path_like(value: str) -> bool:
    return (
        PurePosixPath(value).is_absolute()
        or value.startswith("\\\\")
        or _ABSOLUTE_DRIVE.match(value) is not None
    )


def _safe_scalar(value: str) -> str:
    if _is_path_like(value):
        return hashlib.sha256(value.encode("utf-8")).hexdigest()
    return value


def _key_path(parent: str, key: str) -> str:
    if _is_path_like(key):
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return f"{parent}[~key-sha256:{digest}]"
    if _IDENTIFIER.fullmatch(key) is not None:
        return f"{parent}.{key}"
    return f"{parent}[{_canonical_json(key)}]"


def _json_type(value: object) -> str:
    if value is None:
        return "null"
    if type(value) is bool:
        return "boolean"
    if type(value) is int:
        return "integer"
    if type(value) is float:
        return "number"
    if type(value) is str:
        return "string"
    if type(value) is list:
        return "array"
    if type(value) in {dict, _PairsObject}:
        return "object"
    raise TypeError("strict JSON decoder produced an unsupported runtime value")


def _duplicate_issues(value: object, path: str = "$" ) -> list[MmdAdapterIssue]:
    issues: list[MmdAdapterIssue] = []
    if type(value) is _PairsObject:
        seen: set[str] = set()
        for key, child in value.pairs:
            child_path = _key_path(path, key)
            if key in seen:
                issues.append(_issue(child_path, "duplicate", "unique", "duplicate_key"))
            else:
                seen.add(key)
            issues.extend(_duplicate_issues(child, child_path))
    elif type(value) is list:
        for index, child in enumerate(value):
            issues.extend(_duplicate_issues(child, f"{path}[{index}]"))
    return issues


def _ordinary_json(value: object) -> object:
    if type(value) is _PairsObject:
        return {key: _ordinary_json(child) for key, child in value.pairs}
    if type(value) is list:
        return [_ordinary_json(child) for child in value]
    return value


def _canonical_member(value: str, *, image: bool) -> bool:
    if (
        not value
        or _is_path_like(value)
        or _MEMBER_DRIVE.match(value) is not None
        or "\\" in value
    ):
        return False
    if any(unicodedata.category(character) == "Cc" for character in value):
        return False
    if unicodedata.normalize("NFC", value) != value:
        return False
    parts = value.split("/")
    if any(part in {"", ".", ".."} for part in parts):
        return False
    path = PurePosixPath(value)
    if path.as_posix() != value:
        return False
    if image:
        return len(parts) >= 2 and parts[0] == "images" and path.suffix in _IMAGE_SUFFIXES
    return path.suffix == ".mmd"


def _wrong_type(
    issues: list[MmdAdapterIssue],
    payload: dict[str, object],
    name: str,
    path: str,
    expected: object,
    accepted,
) -> bool:
    if name not in payload:
        return False
    value = payload[name]
    if not accepted(value):
        issues.append(_issue(path, _json_type(value), expected, "wrong_type"))
        return False
    return True


def _validate_selection(
    payload: dict[str, object],
    index: int,
    issues: list[MmdAdapterIssue],
) -> dict[str, bool]:
    base = f"$.selections[{index}]"
    required = set(_SELECTION_FIELDS)
    for name in required - set(payload):
        issues.append(_issue(f"{base}.{name}", "missing", "present", "missing_key"))
    for name in set(payload) - required:
        issues.append(_issue(_key_path(base, name), "present", "absent", "extra_key"))

    valid: dict[str, bool] = {}
    string_fields = (
        "proposed_question_id",
        "kind",
        "number",
        "source_section",
        "language_layout",
        "answer_mapping",
        "primary_type",
        "tag_status",
        "difficulty_status",
    )
    for name in string_fields:
        valid[name] = _wrong_type(
            issues,
            payload,
            name,
            f"{base}.{name}",
            "string",
            lambda value: type(value) is str,
        )
    valid["answer_number"] = _wrong_type(
        issues,
        payload,
        "answer_number",
        f"{base}.answer_number",
        ["string", "null"],
        lambda value: value is None or type(value) is str,
    )
    valid["expected_image_members"] = _wrong_type(
        issues,
        payload,
        "expected_image_members",
        f"{base}.expected_image_members",
        "array",
        lambda value: type(value) is list,
    )
    valid["tags"] = _wrong_type(
        issues,
        payload,
        "tags",
        f"{base}.tags",
        "array",
        lambda value: type(value) is list,
    )
    valid["difficulty_level"] = _wrong_type(
        issues,
        payload,
        "difficulty_level",
        f"{base}.difficulty_level",
        ["integer", "null"],
        lambda value: value is None or type(value) is int,
    )

    for name in ("proposed_question_id", "number", "source_section", "primary_type"):
        if valid.get(name) and payload[name] == "":
            issues.append(_issue(f"{base}.{name}", "", "non_empty_string", "invalid_value"))
            valid[name] = False
    if valid.get("answer_number") and payload["answer_number"] == "":
        issues.append(
            _issue(f"{base}.answer_number", "", "non_empty_string", "invalid_value")
        )
        valid["answer_number"] = False
    for name in ("kind", "language_layout", "answer_mapping", "tag_status", "difficulty_status"):
        if valid.get(name) and payload[name] not in _ENUMS[name]:
            value = payload[name]
            assert type(value) is str
            issues.append(
                _issue(
                    f"{base}.{name}",
                    _safe_scalar(value),
                    list(_ENUMS[name]),
                    "invalid_value",
                )
            )
            valid[name] = False

    if valid.get("difficulty_level") and payload["difficulty_level"] is not None:
        level = payload["difficulty_level"]
        assert type(level) is int
        if not 1 <= level <= 5:
            issues.append(
                _issue(
                    f"{base}.difficulty_level",
                    level,
                    "integer_1_to_5",
                    "invalid_value",
                )
            )
            valid["difficulty_level"] = False

    if valid.get("expected_image_members"):
        members = payload["expected_image_members"]
        assert type(members) is list
        valid_members: list[str] = []
        items_valid = True
        for member_index, member in enumerate(members):
            item_path = f"{base}.expected_image_members[{member_index}]"
            if type(member) is not str:
                issues.append(_issue(item_path, _json_type(member), "string", "wrong_type"))
                items_valid = False
            elif not _canonical_member(member, image=True):
                issues.append(
                    _issue(
                        item_path,
                        hashlib.sha256(member.encode("utf-8")).hexdigest(),
                        "canonical_nfc_posix_images_member",
                        "invalid_value",
                    )
                )
                items_valid = False
            else:
                if member in valid_members:
                    issues.append(
                        _issue(
                            f"{base}.expected_image_members",
                            hashlib.sha256(member.encode("utf-8")).hexdigest(),
                            "unique_items",
                            "invalid_value",
                        )
                    )
                    items_valid = False
                valid_members.append(member)
        valid["expected_image_members"] = items_valid

    if valid.get("tags"):
        tags = payload["tags"]
        assert type(tags) is list
        items_valid = True
        for tag_index, tag in enumerate(tags):
            item_path = f"{base}.tags[{tag_index}]"
            if type(tag) is not str:
                issues.append(_issue(item_path, _json_type(tag), "string", "wrong_type"))
                items_valid = False
            elif not tag:
                issues.append(_issue(item_path, "", "non_empty_string", "invalid_value"))
                items_valid = False
        valid["tags"] = items_valid
    return valid


def _decode_manifest(selection_manifest_path: Path, source_path: Path) -> MmdAdapterManifest:
    if not selection_manifest_path.exists():
        raise InputMissingError("selection manifest does not exist")
    if not selection_manifest_path.is_file():
        raise MmdAdapterBlockedError(
            (_issue("$", "non_regular_file", "regular_file", "wrong_type"),)
        )
    try:
        with selection_manifest_path.open("rb") as stream:
            raw = stream.read()
    except OSError as exc:
        raise MmdAdapterBlockedError(
            (_issue("$", "unreadable_file", "readable", "invalid_value"),)
        ) from exc
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MmdAdapterBlockedError(
            (_issue("$", "undecodable_utf8", "strict_utf8", "invalid_utf8"),)
        ) from exc
    if text.startswith("\ufeff"):
        raise MmdAdapterBlockedError(
            (_issue("$", "utf8_bom", "no_bom", "utf8_bom"),)
        )
    try:
        decoded = json.loads(
            text,
            object_pairs_hook=_PairsObject,
            parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)),
        )
    except (ValueError, json.JSONDecodeError) as exc:
        raise MmdAdapterBlockedError(
            (_issue("$", "invalid_json_syntax", "json_object", "invalid_json"),)
        ) from exc

    duplicate_issues = _duplicate_issues(decoded)
    if duplicate_issues:
        raise MmdAdapterBlockedError(tuple(duplicate_issues))
    if type(decoded) is not _PairsObject:
        raise MmdAdapterBlockedError(
            (_issue("$", _json_type(decoded), "object", "non_object"),)
        )
    payload = _ordinary_json(decoded)
    assert type(payload) is dict
    issues: list[MmdAdapterIssue] = []
    required = set(_TOP_FIELDS)
    for name in required - set(payload):
        issues.append(_issue(f"$.{name}", "missing", "present", "missing_key"))
    for name in set(payload) - required:
        issues.append(_issue(_key_path("$", name), "present", "absent", "extra_key"))

    valid: dict[str, bool] = {}
    for name in (
        "schema_version",
        "batch_id",
        "source_kind",
        "source_sha256",
        "primary_member",
        "source_id",
        "chapter",
    ):
        valid[name] = _wrong_type(
            issues,
            payload,
            name,
            f"$.{name}",
            "string",
            lambda value: type(value) is str,
        )
    valid["answer_member"] = _wrong_type(
        issues,
        payload,
        "answer_member",
        "$.answer_member",
        ["string", "null"],
        lambda value: value is None or type(value) is str,
    )
    valid["expected_candidate_count"] = _wrong_type(
        issues,
        payload,
        "expected_candidate_count",
        "$.expected_candidate_count",
        "integer",
        lambda value: type(value) is int,
    )
    valid["selections"] = _wrong_type(
        issues,
        payload,
        "selections",
        "$.selections",
        "array",
        lambda value: type(value) is list,
    )

    if valid.get("schema_version") and payload["schema_version"] != "task9b-mmd-adapter-v1":
        value = payload["schema_version"]
        assert type(value) is str
        issues.append(
            _issue(
                "$.schema_version",
                _safe_scalar(value),
                "task9b-mmd-adapter-v1",
                "invalid_value",
            )
        )
        valid["schema_version"] = False
    for name in ("batch_id", "source_id", "chapter"):
        if valid.get(name) and payload[name] == "":
            issues.append(_issue(f"$.{name}", "", "non_empty_string", "invalid_value"))
            valid[name] = False
    if valid.get("source_kind") and payload["source_kind"] not in _ENUMS["source_kind"]:
        value = payload["source_kind"]
        assert type(value) is str
        issues.append(
            _issue(
                "$.source_kind",
                _safe_scalar(value),
                list(_ENUMS["source_kind"]),
                "invalid_value",
            )
        )
        valid["source_kind"] = False
    if valid.get("source_sha256"):
        value = payload["source_sha256"]
        assert type(value) is str
        if _SHA256.fullmatch(value) is None:
            issues.append(
                _issue(
                    "$.source_sha256",
                    hashlib.sha256(value.encode("utf-8")).hexdigest(),
                    "lowercase_hex_64",
                    "invalid_value",
                )
            )
            valid["source_sha256"] = False
    for name in ("primary_member", "answer_member"):
        if valid.get(name) and payload[name] is not None:
            value = payload[name]
            assert type(value) is str
            if not _canonical_member(value, image=False):
                issues.append(
                    _issue(
                        f"$.{name}",
                        hashlib.sha256(value.encode("utf-8")).hexdigest(),
                        "canonical_nfc_posix_mmd_member",
                        "invalid_value",
                    )
                )
                valid[name] = False
    if valid.get("expected_candidate_count"):
        value = payload["expected_candidate_count"]
        assert type(value) is int
        if value < 0:
            issues.append(
                _issue(
                    "$.expected_candidate_count",
                    value,
                    "non_negative_integer",
                    "invalid_value",
                )
            )
            valid["expected_candidate_count"] = False

    selection_validity: list[dict[str, bool] | None] = []
    if valid.get("selections"):
        selections = payload["selections"]
        assert type(selections) is list
        for index, selection in enumerate(selections):
            if type(selection) is not dict:
                issues.append(
                    _issue(
                        f"$.selections[{index}]",
                        _json_type(selection),
                        "object",
                        "wrong_type",
                    )
                )
                selection_validity.append(None)
            else:
                selection_validity.append(_validate_selection(selection, index, issues))

    if valid.get("source_kind") and valid.get("answer_member"):
        if payload["source_kind"] == "mmd" and payload["answer_member"] is not None:
            issues.append(
                _issue(
                    "$.answer_member",
                    "present",
                    "null_when_source_kind_mmd",
                    "cross_field_violation",
                )
            )
    if valid.get("source_kind") and valid.get("primary_member"):
        if payload["source_kind"] == "mmd" and payload["primary_member"] != source_path.name:
            issues.append(
                _issue(
                    "$.primary_member",
                    hashlib.sha256(payload["primary_member"].encode("utf-8")).hexdigest(),
                    hashlib.sha256(source_path.name.encode("utf-8")).hexdigest(),
                    "cross_field_violation",
                )
            )
    if valid.get("primary_member") and valid.get("answer_member"):
        if payload["answer_member"] is not None and payload["answer_member"] == payload["primary_member"]:
            issues.append(
                _issue(
                    "$.answer_member",
                    "same_as_primary_member",
                    "different_from_primary_member",
                    "cross_field_violation",
                )
            )
    if valid.get("expected_candidate_count") and valid.get("selections"):
        if payload["expected_candidate_count"] != len(payload["selections"]):
            issues.append(
                _issue(
                    "$.expected_candidate_count",
                    payload["expected_candidate_count"],
                    len(payload["selections"]),
                    "cross_field_violation",
                )
            )

    seen_ids: set[str] = set()
    if valid.get("selections"):
        for index, selection in enumerate(payload["selections"]):
            selection_valid = selection_validity[index]
            if type(selection) is not dict or selection_valid is None:
                continue
            if selection_valid.get("proposed_question_id"):
                proposed_id = selection["proposed_question_id"]
                assert type(proposed_id) is str
                if proposed_id in seen_ids:
                    issues.append(
                        _issue(
                            f"$.selections[{index}].proposed_question_id",
                            hashlib.sha256(proposed_id.encode("utf-8")).hexdigest(),
                            "unique_proposed_question_id",
                            "cross_field_violation",
                        )
                    )
                seen_ids.add(proposed_id)
            if selection_valid.get("answer_mapping") and selection_valid.get("answer_number"):
                if selection["answer_mapping"] == "missing_from_source" and selection["answer_number"] is not None:
                    issues.append(
                        _issue(
                            f"$.selections[{index}].answer_number",
                            "present",
                            "null_when_missing_from_source",
                            "cross_field_violation",
                        )
                    )
                if valid.get("answer_member") and payload["answer_member"] is None and selection["answer_number"] is not None:
                    issues.append(
                        _issue(
                            f"$.selections[{index}].answer_number",
                            "present",
                            "null_without_answer_member",
                            "cross_field_violation",
                        )
                    )
            if selection_valid.get("tag_status") and selection_valid.get("tags"):
                tag_count = len(selection["tags"])
                if selection["tag_status"] == "missing" and tag_count:
                    issues.append(
                        _issue(
                            f"$.selections[{index}].tags",
                            tag_count,
                            0,
                            "cross_field_violation",
                        )
                    )
                elif selection["tag_status"] != "missing" and not tag_count:
                    issues.append(
                        _issue(
                            f"$.selections[{index}].tags",
                            0,
                            "positive_length",
                            "cross_field_violation",
                        )
                    )
            if selection_valid.get("difficulty_status") and selection_valid.get("difficulty_level"):
                level = selection["difficulty_level"]
                if selection["difficulty_status"] == "missing" and level is not None:
                    issues.append(
                        _issue(
                            f"$.selections[{index}].difficulty_level",
                            level,
                            None,
                            "cross_field_violation",
                        )
                    )
                elif selection["difficulty_status"] != "missing" and level is None:
                    issues.append(
                        _issue(
                            f"$.selections[{index}].difficulty_level",
                            None,
                            "integer_1_to_5",
                            "cross_field_violation",
                        )
                    )

    if issues:
        raise MmdAdapterBlockedError(tuple(issues))

    typed_selections = tuple(
        MmdSelection(*(selection[name] for name in _SELECTION_FIELDS))
        for selection in payload["selections"]
    )
    return MmdAdapterManifest(
        *(payload[name] if name != "selections" else typed_selections for name in _TOP_FIELDS)
    )


def _check_plain_d3_resource_targets(
    target_records: tuple[tuple[str, str, int, int], ...],
    source_path: Path,
) -> None:
    root = source_path.parent.resolve(strict=False)
    issues: list[MmdAdapterIssue] = []
    for member_path, raw_target, start_byte, end_byte in target_records:
        canonical_member = raw_target[2:]
        expected = root.joinpath(*PurePosixPath(canonical_member).parts)
        resolved = (source_path.parent / canonical_member).resolve(strict=False)
        if not resolved.is_relative_to(root) or resolved != expected:
            issues.append(
                MmdAdapterIssue(
                    "archive_member_unsafe",
                    "blocking",
                    None,
                    f"{member_path}#bytes={start_byte}:{end_byte}",
                    "raw_target",
                    _canonical_json(
                        {
                            "raw_target_sha256": hashlib.sha256(
                                raw_target.encode("utf-8")
                            ).hexdigest(),
                            "reason": "image_target_normalized_escape",
                        }
                    ),
                )
            )
    if issues:
        raise MmdAdapterBlockedError(tuple(issues))


def _locator(question: _SourceQuestion) -> str:
    span = question.fragment_span
    return f"{span.member_path}#bytes={span.start_byte}:{span.end_byte}"


def _question_kind(question: _SourceQuestion) -> str:
    return "example" if question.source_section in {"例題", "例题"} else "exercise"


def _mapping_issue(
    code: str,
    selection: MmdSelection | None,
    locator: str,
    field: str,
    evidence: dict[str, object],
) -> MmdAdapterIssue:
    return MmdAdapterIssue(
        code,
        "blocking",
        selection.proposed_question_id if selection is not None else None,
        locator,
        field,
        _canonical_json(evidence),
    )


def _bind_selections(
    manifest: MmdAdapterManifest,
    document: _SourceDocument,
    answer: _SourceMember | None,
) -> tuple[tuple[MmdSelection, _SourceQuestion], ...]:
    issues: list[MmdAdapterIssue] = []
    bindings: list[tuple[MmdSelection, _SourceQuestion]] = []
    answer_occurrences = _parse_answers(answer, []) if answer is not None else {}

    for selection in manifest.selections:
        expected = (selection.kind, selection.number, selection.source_section)
        exact = tuple(
            question
            for question in document.questions
            if (
                _question_kind(question),
                question.source_question_number,
                question.source_section,
            )
            == expected
        )
        if len(exact) != 1:
            if not exact:
                counterfactuals = []
                for question in document.questions:
                    actual = (
                        _question_kind(question),
                        question.source_question_number,
                        question.source_section,
                    )
                    different = tuple(
                        index for index, values in enumerate(zip(actual, expected))
                        if values[0] != values[1]
                    )
                    if len(different) == 1:
                        counterfactuals.append((question, different[0], actual))
                if len(counterfactuals) == 1:
                    question, index, actual = counterfactuals[0]
                    field = ("kind", "number", "source_section")[index]
                    issues.append(
                        _mapping_issue(
                            "source_contract_mismatch",
                            selection,
                            _locator(question),
                            field,
                            {
                                "actual": actual[index],
                                "expected": expected[index],
                                "reason": "source_occurrence_mismatch",
                            },
                        )
                    )
                    continue
            issues.append(
                _mapping_issue(
                    "selection_not_unique",
                    selection,
                    "",
                    "selection",
                    {
                        "canonical_number": selection.number,
                        "match_count": len(exact),
                        "reason": "question_occurrence",
                    },
                )
            )
            continue

        question = exact[0]
        if selection.answer_mapping == "source_answer":
            if selection.answer_number is None:
                local_marker_count = _local_solution_marker_count(document, question)
                match_count = (
                    local_marker_count
                    if local_marker_count != 1
                    else len(question.solution_spans)
                )
                if match_count != 1:
                    issues.append(
                        _mapping_issue(
                            "selection_not_unique",
                            selection,
                            _locator(question),
                            "answer_mapping",
                            {
                                "canonical_number": selection.number,
                                "match_count": match_count,
                                "reason": "local_solution",
                            },
                        )
                    )
                    continue
            else:
                matches = tuple(
                    span for span in answer_occurrences.get(selection.answer_number, ())
                    if span[0] < span[1]
                )
                if len(matches) != 1:
                    issues.append(
                        _mapping_issue(
                            "selection_not_unique",
                            selection,
                            _locator(question) if matches else "",
                            "answer_number",
                            {
                                "canonical_number": selection.answer_number,
                                "match_count": len(matches),
                                "reason": "answer_occurrence",
                            },
                        )
                    )
                    continue
                assert answer is not None
                start_byte, end_byte = matches[0]
                question = replace(
                    question,
                    solution_spans=(
                        _SourceSpan(
                            answer.relative_path,
                            start_byte,
                            end_byte,
                            "solution",
                            "und",
                        ),
                    ),
                )
        bindings.append((selection, question))

    if issues:
        raise MmdAdapterBlockedError(tuple(issues))
    return tuple(bindings)


def _physical_ranges(content: bytes, start: int, end: int):
    position = start
    while position < end:
        line_start = position
        while position < end and content[position] not in {10, 13}:
            position += 1
        if position < end:
            if content[position] == 13 and position + 1 < end and content[position + 1] == 10:
                position += 2
            else:
                position += 1
        yield line_start, position


def _local_solution_marker_count(
    document: _SourceDocument,
    question: _SourceQuestion,
) -> int:
    members = {member.relative_path: member for member in document.members}
    primary = members[document.primary_member]
    questions = document.questions
    end = (
        questions[question.source_order + 1].fragment_span.start_byte
        if question.source_order + 1 < len(questions)
        else len(primary.content)
    )
    count = 0
    in_display_math = False
    for start, line_end in _physical_ranges(
        primary.content,
        question.fragment_span.end_byte,
        end,
    ):
        line = primary.content[start:line_end]
        if line.endswith(b"\r\n"):
            line = line[:-2]
        elif line.endswith((b"\r", b"\n")):
            line = line[:-1]
        if line == b"$$":
            in_display_math = not in_display_math
            continue
        if in_display_math:
            continue
        if line in {"題解：".encode("utf-8"), "題解 ：".encode("utf-8")}:
            count += 1
    return count


def _language_issues(
    selection: MmdSelection,
    question: _SourceQuestion,
    primary: _SourceMember,
) -> tuple[MmdAdapterIssue, ...]:
    lines: list[tuple[int, int, set[str]]] = []
    for start, end in _physical_ranges(
        primary.content,
        question.fragment_span.start_byte,
        question.fragment_span.end_byte,
    ):
        languages = {
            span.language
            for span in question.text_spans
            if span.start_byte < end and span.end_byte > start
            and span.language in {"en", "zh", "und"}
        }
        if languages:
            lines.append((start, end, languages))

    def issue(reason: str, start: int, end: int) -> MmdAdapterIssue:
        return _mapping_issue(
            "language_mapping_ambiguous",
            selection,
            f"{question.fragment_span.member_path}#bytes={start}:{end}",
            "language_layout",
            {
                "end_byte": end,
                "layout": selection.language_layout,
                "reason": reason,
                "start_byte": start,
            },
        )

    for start, end, languages in lines:
        if selection.language_layout == "interleaved_bilingual" and "und" in languages:
            return (issue("und_prose", start, end),)

    if not lines:
        return (
            issue(
                "missing_en",
                question.fragment_span.start_byte,
                question.fragment_span.end_byte,
            ),
        )

    if selection.language_layout == "english_then_chinese":
        for start, end, languages in lines:
            if "und" in languages:
                return (issue("und_prose", start, end),)
            if "en" in languages:
                break
            if "zh" in languages:
                return (issue("missing_en", start, end),)

    has_en = any("en" in languages for _, _, languages in lines)
    has_zh = any("zh" in languages for _, _, languages in lines)
    if not has_en:
        start, end, _ = lines[0]
        return (issue("missing_en", start, end),)
    if not has_zh:
        start, end, _ = next(line for line in lines if "en" in line[2])
        return (issue("missing_zh", start, end),)
    if selection.language_layout == "english_then_chinese":
        entered_zh = False
        for start, end, languages in lines:
            if entered_zh and "en" in languages:
                return (issue("invalid_transition", start, end),)
            if "zh" in languages:
                entered_zh = True
    return ()


def _normalize_newlines(value: bytes) -> str:
    return value.decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")


def _render_spans(document: _SourceDocument, spans) -> str:
    members = {member.relative_path: member.content for member in document.members}
    return _normalize_newlines(
        b"".join(
            members[span.member_path][span.start_byte:span.end_byte]
            for span in spans
        )
    )


def _render_zh(document: _SourceDocument, question: _SourceQuestion) -> str:
    if not any(span.language == "zh" for span in question.text_spans):
        return ""
    members = {member.relative_path: member.content for member in document.members}
    spans = sorted(
        (*question.text_spans, *(reference.token_span for reference in question.image_refs)),
        key=lambda span: (span.start_byte, span.end_byte),
    )
    pieces: list[str] = []
    omitted_en = False
    for span in spans:
        if span.language not in {"zh", "shared"}:
            omitted_en = omitted_en or span.language == "en"
            continue
        text = _normalize_newlines(
            members[span.member_path][span.start_byte:span.end_byte]
        )
        if omitted_en and pieces and text and not pieces[-1].endswith("\n") and not text.startswith("\n"):
            pieces.append("\n")
        pieces.append(text)
        omitted_en = False
    return "".join(pieces)


def _map_candidates(
    manifest: MmdAdapterManifest,
    document: _SourceDocument,
    bindings: tuple[tuple[MmdSelection, _SourceQuestion], ...],
) -> tuple[dict[str, object], ...]:
    members = {member.relative_path: member.content for member in document.members}
    primary = next(
        member
        for member in document.members
        if member.relative_path == document.primary_member
    )
    issues: list[MmdAdapterIssue] = []
    for selection, question in bindings:
        issues.extend(_language_issues(selection, question, primary))
    if issues:
        raise MmdAdapterBlockedError(tuple(issues))

    for selection, question in bindings:
        actual_images = tuple(reference.raw_target[2:] for reference in question.image_refs)
        if actual_images != selection.expected_image_members:
            for index, reference in enumerate(question.image_refs):
                canonical = reference.raw_target[2:]
                if index >= len(selection.expected_image_members) or selection.expected_image_members[index] != canonical:
                    issues.append(
                        _mapping_issue(
                            "image_binding_invalid",
                            selection,
                            (
                                f"{reference.token_span.member_path}#bytes="
                                f"{reference.token_span.start_byte}:{reference.token_span.end_byte}"
                            ),
                            "expected_image_members",
                            {
                                "matches": [canonical],
                                "raw_target": reference.raw_target,
                                "reason": "selection_conflict",
                            },
                        )
                    )
            for expected_member in selection.expected_image_members[len(actual_images):]:
                issues.append(
                    _mapping_issue(
                        "image_binding_invalid",
                        selection,
                        _locator(question),
                        "expected_image_members",
                        {
                            "expected_member": expected_member,
                            "matches": [],
                            "raw_target": None,
                            "reason": "selection_surplus",
                        },
                    )
                )
    if issues:
        raise MmdAdapterBlockedError(tuple(issues))

    candidates: list[dict[str, object]] = []
    for selection, question in bindings:
        fragment = members[question.fragment_span.member_path][
            question.fragment_span.start_byte:question.fragment_span.end_byte
        ]
        has_zh = any(span.language == "zh" for span in question.text_spans)
        zh_spans = tuple(span for span in question.text_spans if span.language == "zh")
        source_answer = selection.answer_mapping == "source_answer"
        solution = _render_spans(document, question.solution_spans) if source_answer else ""
        translation_evidence = None
        if has_zh:
            translation_evidence = (
                "source:source/original.mmd.txt#"
                f"{question.fragment_span.member_path}#bytes="
                f"{zh_spans[0].start_byte}:{zh_spans[-1].end_byte}"
            )
        enrichment = (
            has_zh
            and False
            and selection.tag_status != "missing"
            and selection.difficulty_status != "missing"
        )
        candidates.append(
            {
                "proposed_question_id": selection.proposed_question_id,
                "source_id": manifest.source_id,
                "source_question_number": question.source_question_number,
                "source_section": question.source_section,
                "source_fragment_hash": hashlib.sha256(fragment).hexdigest(),
                "question_text_original": _normalize_newlines(fragment),
                "question_text_zh": _render_zh(document, question),
                "translation_status": "source_present" if has_zh else "missing",
                "translation_evidence": translation_evidence,
                "solution_original": solution,
                "solution_verified": "",
                "answer_status": "source_provided" if source_answer else "missing_from_source",
                "explanation_text": "",
                "explanation_status": "missing",
                "explanation_evidence": None,
                "image_paths": list(selection.expected_image_members),
                "image_roles": ["question"] * len(selection.expected_image_members),
                "primary_type": selection.primary_type,
                "tags": list(selection.tags),
                "tag_status": selection.tag_status,
                "difficulty_level": selection.difficulty_level,
                "difficulty_status": selection.difficulty_status,
                "enrichment_status": "complete" if enrichment else "incomplete",
            }
        )
    return tuple(candidates)


def _span_payload(span: _SourceSpan, *, include_language: bool = False) -> dict[str, object]:
    payload: dict[str, object] = {
        "member": span.member_path,
        "start_byte": span.start_byte,
        "end_byte": span.end_byte,
    }
    if include_language:
        payload["language"] = span.language
    return payload


def _source_map_payload(
    manifest: MmdAdapterManifest,
    document: _SourceDocument,
    bindings: tuple[tuple[MmdSelection, _SourceQuestion], ...],
    answer: _SourceMember | None,
    image_bytes: dict[str, bytes],
) -> dict[str, object]:
    members = {member.relative_path: member for member in document.members}
    primary = members[document.primary_member]
    member_payloads: list[dict[str, object]] = [
        {
            "source_member": primary.relative_path,
            "staged_path": "source/original.mmd.txt",
            "sha256": primary.sha256,
            "size_bytes": len(primary.content),
            "role": "primary",
        }
    ]
    if answer is not None:
        member_payloads.append(
            {
                "source_member": answer.relative_path,
                "staged_path": "answers/answer.mmd.txt",
                "sha256": answer.sha256,
                "size_bytes": len(answer.content),
                "role": "answer",
            }
        )

    questions: list[dict[str, object]] = []
    for selection, question in bindings:
        image_references = []
        for reference in question.image_refs:
            canonical_path = reference.raw_target[2:]
            content = (
                image_bytes.get(reference.resolved_member)
                if reference.resolved_member is not None
                else None
            )
            image_references.append(
                {
                    "source_order": reference.source_order,
                    "token_span": _span_payload(reference.token_span),
                    "raw_target": reference.raw_target,
                    "selected_member": reference.resolved_member,
                    "canonical_path": canonical_path,
                    "sha256": hashlib.sha256(content).hexdigest() if content is not None else None,
                    "role": "question",
                }
            )
        questions.append(
            {
                "proposed_question_id": selection.proposed_question_id,
                "source_order": question.source_order,
                "source_question_number": question.source_question_number,
                "source_section": question.source_section,
                "fragment": _span_payload(question.fragment_span),
                "text_spans": [
                    _span_payload(span, include_language=True)
                    for span in question.text_spans
                ],
                "solution_spans": [
                    _span_payload(span) for span in question.solution_spans
                ],
                "explanation_spans": [
                    _span_payload(span) for span in question.explanation_spans
                ],
                "image_references": image_references,
            }
        )
    return {
        "schema_version": "task9b-source-map-v1",
        "batch_id": manifest.batch_id,
        "source_id": manifest.source_id,
        "primary_member": document.primary_member,
        "members": member_payloads,
        "questions": questions,
    }


def _file_evidence(
    relative_path: str,
    content: bytes,
    kind: str,
) -> ImportFileEvidence:
    return ImportFileEvidence(
        relative_path,
        hashlib.sha256(content).hexdigest(),
        len(content),
        kind,
    )


def _manifest_payload(manifest: BatchImportManifest) -> dict[str, object]:
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


def _publish_package(
    output_dir: Path,
    manifest: MmdAdapterManifest,
    document: _SourceDocument,
    bindings: tuple[tuple[MmdSelection, _SourceQuestion], ...],
    candidates: tuple[dict[str, object], ...],
    primary: _SourceMember,
    answer: _SourceMember | None,
    image_bytes: dict[str, bytes],
) -> AdaptedImportPackage:
    candidates_bytes = (_canonical_json(list(candidates)) + "\n").encode("utf-8")
    source_map_bytes = _canonical_json(
        _source_map_payload(manifest, document, bindings, answer, image_bytes)
    ).encode("utf-8")

    selected_images = tuple(
        dict.fromkeys(
            image
            for selection, _question in bindings
            for image in selection.expected_image_members
            if image in image_bytes
        )
    )
    answer_bytes = answer.content if answer is not None else None
    batch_manifest = BatchImportManifest(
        schema_version="task9-import-manifest-v1",
        batch_id=manifest.batch_id,
        project="Joy M2 AI Database",
        module="M2",
        chapter=manifest.chapter,
        target_release_version="V1.19",
        candidate_records=(
            _file_evidence("records/candidates.json", candidates_bytes, "candidate_json"),
        ),
        source_files=(
            _file_evidence("source/original.mmd.txt", primary.content, "source"),
            _file_evidence("source/source-map.json", source_map_bytes, "source"),
        ),
        answer_files=(
            (_file_evidence("answers/answer.mmd.txt", answer_bytes, "answer"),)
            if answer_bytes is not None
            else ()
        ),
        image_files=tuple(
            _file_evidence(path, image_bytes[path], "image")
            for path in selected_images
        ),
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
            _manifest_payload(batch_manifest),
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")

    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=output_dir.parent)
    )
    try:
        files: list[tuple[str, bytes]] = [
            ("records/candidates.json", candidates_bytes),
            ("source/original.mmd.txt", primary.content),
            ("source/source-map.json", source_map_bytes),
        ]
        if answer_bytes is not None:
            files.append(("answers/answer.mmd.txt", answer_bytes))
        files.extend((path, image_bytes[path]) for path in selected_images)
        files.append(("import_manifest.json", manifest_bytes))
        for relative_path, content in files:
            target = temporary_root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)

        package = AdaptedImportPackage(
            output_dir,
            output_dir / "import_manifest.json",
            batch_manifest,
        )
        os.replace(temporary_root, output_dir)
        return package
    finally:
        if temporary_root.exists():
            shutil.rmtree(temporary_root)


def adapt_mmd_package(
    selection_manifest_path: Path,
    source_path: Path,
    output_dir: Path,
    config: PipelineConfig,
) -> AdaptedImportPackage:
    if not isinstance(selection_manifest_path, Path):
        raise TypeError("selection_manifest_path must be a pathlib.Path")
    if not isinstance(source_path, Path):
        raise TypeError("source_path must be a pathlib.Path")
    if not isinstance(output_dir, Path):
        raise TypeError("output_dir must be a pathlib.Path")
    if type(config) is not PipelineConfig:
        raise TypeError("config must be an exact PipelineConfig")

    resolved_output = config.require_staging_output(output_dir)
    if resolved_output == config.staging_root:
        raise ConfigurationError("output path must be a strict staging descendant")
    if output_dir.exists() or output_dir.is_symlink():
        raise OutputConflictError("output path already exists")

    manifest = _decode_manifest(selection_manifest_path, source_path)
    primary_bytes, answer_bytes, image_bytes, source_inventory = read_selected_source(
        manifest,
        source_path,
    )
    primary = _SourceMember(
        manifest.primary_member,
        hashlib.sha256(primary_bytes).hexdigest(),
        primary_bytes,
    )
    answer = (
        _SourceMember(
            manifest.answer_member,
            hashlib.sha256(answer_bytes).hexdigest(),
            answer_bytes,
        )
        if manifest.answer_member is not None and answer_bytes is not None
        else None
    )
    image_members = tuple(
        _SourceMember(
            relative_path,
            hashlib.sha256(content).hexdigest(),
            content,
        )
        for relative_path, content in sorted(image_bytes.items())
    )
    document, target_records = _parse_source_document_with_inventory(
        primary,
        answer,
        source_inventory,
        image_members,
    )
    if manifest.source_kind == "mmd":
        _check_plain_d3_resource_targets(target_records, source_path)
    bindings = _bind_selections(manifest, document, answer)
    if len(document.questions) != manifest.expected_candidate_count:
        raise MmdAdapterBlockedError(
            (
                _mapping_issue(
                    "candidate_count_mismatch",
                    None,
                    "",
                    "expected_candidate_count",
                    {
                        "actual": len(document.questions),
                        "expected": manifest.expected_candidate_count,
                        "reason": "candidate_count",
                    },
                ),
            )
        )
    candidates = _map_candidates(manifest, document, bindings)
    return _publish_package(
        output_dir,
        manifest,
        document,
        bindings,
        candidates,
        primary,
        answer,
        image_bytes,
    )
