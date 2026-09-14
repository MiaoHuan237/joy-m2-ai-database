"""Explicit source-mapping authority for ambiguous Task 9B MMD inputs."""

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import tempfile

from joy_m2.config import PipelineConfig
from joy_m2.errors import (
    ConfigurationError,
    InputFormatError,
    InputMissingError,
    OutputConflictError,
    PipelineError,
)

from .adapter import (
    _PairsObject,
    _canonical_json,
    _canonical_member,
    _decode_manifest,
    _duplicate_issues,
    _issue,
    _json_type,
    _key_path,
    _language_issues,
    _map_candidates,
    _mapping_issue,
    _ordinary_json,
    _publish_package,
)
from .adapter_models import (
    AdaptedImportPackage,
    MmdAdapterBlockedError,
    MmdAdapterIssue,
    MmdAdapterManifest,
    MmdSelection,
)
from .v120_models import V120AdaptedImportPackage
from .archive import _is_allowed_metadata, read_selected_source
from .mmd_parser import (
    _SourceDocument,
    _SourceImageRef,
    _SourceMember,
    _SourceQuestion,
    _SourceSpan,
    _image_target_safety_issues,
    _lex_mapped_question,
)


_SHA256 = re.compile(r"[0-9a-f]{64}")
_MODE_B_LAYOUTS = (
    "english_then_chinese",
    "interleaved_bilingual",
    "source_chinese",
    "source_english",
)
_DRAFT_TOP = (
    "schema_version",
    "source_id",
    "chapter",
    "mapping_mode",
    "questions",
    "ignored_line_spans",
    "ignored_image_members",
)
_DRAFT_QUESTION = (
    "semantic_order",
    "proposed_question_id",
    "source_question_number",
    "source_section",
    "question_line_span",
    "solution_line_spans",
    "explanation_line_spans",
    "image_bindings",
    "ambiguity_note",
)
_LINE_SPAN = ("member", "line_start", "line_end")
_DRAFT_IMAGE = ("semantic_order", "source_line", "raw_target", "selected_member", "role")
_IGNORED_LINE = (*_LINE_SPAN, "reason")
_IGNORED_IMAGE = ("member", "reason")
_MAPPING_TOP = (
    "schema_version",
    "mapping_mode",
    "source_kind",
    "source_sha256",
    "primary_member",
    "primary_member_sha256",
    "answer_member",
    "answer_member_sha256",
    "source_id",
    "chapter",
    "questions",
    "ignored_spans",
    "ignored_image_members",
)
_MAPPING_QUESTION = (
    "semantic_order",
    "proposed_question_id",
    "source_question_number",
    "source_section",
    "question_span",
    "solution_spans",
    "explanation_spans",
    "image_bindings",
)
_BYTE_SPAN = ("member", "start_byte", "end_byte")
_MAPPING_IMAGE = (
    "semantic_order",
    "token_span",
    "raw_target",
    "selected_member",
    "canonical_path",
    "role",
)


def _require_path(value: object, name: str) -> Path:
    if not isinstance(value, Path):
        raise PipelineError(f"{name} must be a Path")
    return value


def _require_source_id(value: object) -> str:
    if type(value) is not str or not value or "\r" in value or "\n" in value:
        raise PipelineError("source_id must be a single-line non-empty string")
    return value


def _require_sha256(value: object, name: str) -> str:
    if type(value) is not str or _SHA256.fullmatch(value) is None:
        raise PipelineError(f"{name} must be a lowercase SHA-256 digest")
    return value


@dataclass(frozen=True)
class SourceMappingProposal:
    proposal_root: Path
    mapping_path: Path
    review_path: Path
    source_id: str
    source_sha256: str
    mapping_sha256: str
    candidate_count: int

    def __post_init__(self) -> None:
        proposal_root = _require_path(self.proposal_root, "proposal_root")
        mapping_path = _require_path(self.mapping_path, "mapping_path")
        review_path = _require_path(self.review_path, "review_path")
        if mapping_path != proposal_root / "source_mapping.json":
            raise PipelineError("mapping_path must name source_mapping.json under proposal_root")
        if review_path != proposal_root / "SOURCE_MAPPING_REVIEW.md":
            raise PipelineError("review_path must name SOURCE_MAPPING_REVIEW.md under proposal_root")
        _require_source_id(self.source_id)
        _require_sha256(self.source_sha256, "source_sha256")
        _require_sha256(self.mapping_sha256, "mapping_sha256")
        if type(self.candidate_count) is not int or self.candidate_count < 0:
            raise PipelineError("candidate_count must be an exact non-negative integer")


@dataclass(frozen=True)
class SourceMappingApproval:
    source_id: str
    mapping_sha256: str
    approval_text: str

    def __post_init__(self) -> None:
        source_id = _require_source_id(self.source_id)
        mapping_sha256 = _require_sha256(self.mapping_sha256, "mapping_sha256")
        if type(self.approval_text) is not str:
            raise PipelineError("approval_text must be an exact string")
        expected = f"USER APPROVED SOURCE MAPPING {source_id} {mapping_sha256}"
        if self.approval_text != expected:
            raise PipelineError("approval_text does not exactly bind source_id and mapping_sha256")


def _read_input(path: Path, label: str) -> bytes:
    if not path.exists():
        raise InputMissingError(f"{label} does not exist")
    if not path.is_file():
        raise InputFormatError(f"{label} must be a regular file")
    try:
        with path.open("rb") as stream:
            return stream.read()
    except OSError as exc:
        raise InputFormatError(f"{label} is not readable") from exc


def _decode_object(raw: bytes) -> dict[str, object]:
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise MmdAdapterBlockedError(
            (_issue("$", "undecodable_utf8", "strict_utf8", "invalid_utf8"),)
        ) from exc
    if text.startswith("\ufeff"):
        raise MmdAdapterBlockedError((_issue("$", "utf8_bom", "no_bom", "utf8_bom"),))
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
    duplicates = _duplicate_issues(decoded)
    if duplicates:
        raise MmdAdapterBlockedError(tuple(duplicates))
    if type(decoded) is not _PairsObject:
        raise MmdAdapterBlockedError((_issue("$", _json_type(decoded), "object", "non_object"),))
    result = _ordinary_json(decoded)
    assert type(result) is dict
    return result


def _exact_keys(
    value: object,
    fields: tuple[str, ...],
    path: str,
    issues: list[MmdAdapterIssue],
) -> dict[str, object] | None:
    if type(value) is not dict:
        issues.append(_issue(path, _json_type(value), "object", "wrong_type"))
        return None
    required = set(fields)
    for name in required - set(value):
        issues.append(_issue(_key_path(path, name), "missing", "present", "missing_key"))
    for name in set(value) - required:
        issues.append(_issue(_key_path(path, name), "present", "absent", "extra_key"))
    return value


def _type(
    value: dict[str, object],
    name: str,
    path: str,
    expected: object,
    accepted,
    issues: list[MmdAdapterIssue],
) -> bool:
    if name not in value:
        return False
    item = value[name]
    if not accepted(item):
        issues.append(_issue(f"{path}.{name}", _json_type(item), expected, "wrong_type"))
        return False
    return True


def _invalid_scalar(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _validate_line_span(value: object, path: str, issues: list[MmdAdapterIssue]) -> bool:
    item = _exact_keys(value, _LINE_SPAN, path, issues)
    if item is None:
        return False
    ok = True
    if _type(item, "member", path, "string", lambda v: type(v) is str, issues):
        member = item["member"]
        assert type(member) is str
        if not _canonical_member(member, image=False):
            issues.append(_issue(f"{path}.member", _invalid_scalar(member), "canonical_nfc_posix_mmd_member", "invalid_value"))
            ok = False
    else:
        ok = False
    for name in ("line_start", "line_end"):
        ok = _type(item, name, path, "integer", lambda v: type(v) is int, issues) and ok
    return ok


def _validate_byte_span(value: object, path: str, issues: list[MmdAdapterIssue]) -> bool:
    item = _exact_keys(value, _BYTE_SPAN, path, issues)
    if item is None:
        return False
    ok = True
    if _type(item, "member", path, "string", lambda v: type(v) is str, issues):
        member = item["member"]
        assert type(member) is str
        if not _canonical_member(member, image=False):
            issues.append(_issue(f"{path}.member", _invalid_scalar(member), "canonical_nfc_posix_mmd_member", "invalid_value"))
            ok = False
    else:
        ok = False
    for name in ("start_byte", "end_byte"):
        ok = _type(item, name, path, "integer", lambda v: type(v) is int, issues) and ok
    return ok


def _validate_ignored_image(value: object, path: str, issues: list[MmdAdapterIssue]) -> bool:
    item = _exact_keys(value, _IGNORED_IMAGE, path, issues)
    if item is None:
        return False
    ok = True
    if _type(item, "member", path, "string", lambda v: type(v) is str, issues):
        member = item["member"]
        assert type(member) is str
        if not _canonical_member(member, image=True):
            issues.append(_issue(f"{path}.member", _invalid_scalar(member), "canonical_nfc_posix_images_member", "invalid_value"))
            ok = False
    else:
        ok = False
    if _type(item, "reason", path, "string", lambda v: type(v) is str, issues):
        if item["reason"] == "":
            issues.append(_issue(f"{path}.reason", "", "non_empty_string", "invalid_value"))
            ok = False
    else:
        ok = False
    return ok


def _validate_draft(payload: dict[str, object], manifest: MmdAdapterManifest) -> None:
    issues: list[MmdAdapterIssue] = []
    top = _exact_keys(payload, _DRAFT_TOP, "$", issues)
    assert top is not None
    valid: dict[str, bool] = {}
    for name in ("schema_version", "source_id", "chapter", "mapping_mode"):
        valid[name] = _type(top, name, "$", "string", lambda v: type(v) is str, issues)
    for name in ("questions", "ignored_line_spans", "ignored_image_members"):
        valid[name] = _type(top, name, "$", "array", lambda v: type(v) is list, issues)
    constants = {
        "schema_version": "task9b-source-mapping-draft-v1",
        "mapping_mode": "explicit",
    }
    for name, expected in constants.items():
        if valid.get(name) and top[name] != expected:
            issues.append(_issue(f"$.{name}", top[name], expected, "invalid_value"))
    if valid.get("source_id"):
        source_id = top["source_id"]
        assert type(source_id) is str
        if not source_id or "\r" in source_id or "\n" in source_id:
            actual = _invalid_scalar(source_id) if source_id else ""
            issues.append(_issue("$.source_id", actual, "single_line_non_empty", "invalid_value"))
            valid["source_id"] = False
        elif source_id != manifest.source_id:
            issues.append(_issue("$.source_id", source_id, manifest.source_id, "mapping_selection_mismatch"))
    if valid.get("chapter"):
        chapter = top["chapter"]
        assert type(chapter) is str
        if not chapter:
            issues.append(_issue("$.chapter", "", "non_empty_string", "invalid_value"))
        elif chapter != manifest.chapter:
            issues.append(_issue("$.chapter", chapter, manifest.chapter, "mapping_selection_mismatch"))

    questions = top.get("questions") if valid.get("questions") else None
    if type(questions) is list:
        if len(questions) != manifest.expected_candidate_count:
            issues.append(
                _mapping_issue(
                    "candidate_count_mismatch",
                    None,
                    "",
                    "expected_candidate_count",
                    {"actual": len(questions), "expected": manifest.expected_candidate_count, "reason": "candidate_count"},
                )
            )
        seen_ids: set[str] = set()
        for index, raw_question in enumerate(questions):
            path = f"$.questions[{index}]"
            question = _exact_keys(raw_question, _DRAFT_QUESTION, path, issues)
            if question is None:
                continue
            scalar_ok: dict[str, bool] = {}
            scalar_ok["semantic_order"] = _type(question, "semantic_order", path, "integer", lambda v: type(v) is int, issues)
            for name in ("proposed_question_id", "source_question_number", "source_section", "ambiguity_note"):
                scalar_ok[name] = _type(question, name, path, "string", lambda v: type(v) is str, issues)
            for name in ("solution_line_spans", "explanation_line_spans", "image_bindings"):
                scalar_ok[name] = _type(question, name, path, "array", lambda v: type(v) is list, issues)
            if "question_line_span" in question:
                _validate_line_span(
                    question["question_line_span"],
                    f"{path}.question_line_span",
                    issues,
                )
            if scalar_ok.get("semantic_order") and question["semantic_order"] != index:
                issues.append(_issue(f"{path}.semantic_order", question["semantic_order"], index, "cross_field_violation"))
            selection = manifest.selections[index] if index < len(manifest.selections) else None
            for name, selection_name in (
                ("proposed_question_id", "proposed_question_id"),
                ("source_question_number", "number"),
                ("source_section", "source_section"),
            ):
                if scalar_ok.get(name):
                    observed = question[name]
                    assert type(observed) is str
                    if not observed:
                        issues.append(_issue(f"{path}.{name}", "", "non_empty_string", "invalid_value"))
                    elif selection is not None and observed != getattr(selection, selection_name):
                        issues.append(
                            _mapping_issue(
                                "source_contract_mismatch",
                                selection,
                                "",
                                f"{path}.{name}",
                                {"actual": observed, "expected": getattr(selection, selection_name), "reason": "mapping_selection_mismatch"},
                            )
                        )
                if name == "proposed_question_id" and scalar_ok.get(name):
                    observed = question[name]
                    assert type(observed) is str
                    if observed in seen_ids:
                        issues.append(_issue(f"{path}.{name}", _invalid_scalar(observed), "unique_proposed_question_id", "cross_field_violation"))
                    seen_ids.add(observed)
            for array_name in ("solution_line_spans", "explanation_line_spans"):
                spans = question.get(array_name)
                if type(spans) is list:
                    for span_index, span in enumerate(spans):
                        _validate_line_span(span, f"{path}.{array_name}[{span_index}]", issues)
                    if len({_canonical_json(span) for span in spans}) != len(spans):
                        issues.append(_issue(f"{path}.{array_name}", len(spans), "unique_items", "cross_field_violation"))
            bindings = question.get("image_bindings")
            if type(bindings) is list:
                for binding_index, raw_binding in enumerate(bindings):
                    binding_path = f"{path}.image_bindings[{binding_index}]"
                    binding = _exact_keys(raw_binding, _DRAFT_IMAGE, binding_path, issues)
                    if binding is None:
                        continue
                    if _type(binding, "semantic_order", binding_path, "integer", lambda v: type(v) is int, issues) and binding["semantic_order"] != binding_index:
                        issues.append(_issue(f"{binding_path}.semantic_order", binding["semantic_order"], binding_index, "cross_field_violation"))
                    if _type(
                        binding,
                        "source_line",
                        binding_path,
                        "integer",
                        lambda v: type(v) is int,
                        issues,
                    ) and binding["source_line"] < 1:
                        issues.append(
                            _issue(
                                f"{binding_path}.source_line",
                                binding["source_line"],
                                "positive_integer",
                                "invalid_value",
                            )
                        )
                    for name in ("raw_target", "role"):
                        if _type(binding, name, binding_path, "string", lambda v: type(v) is str, issues):
                            if binding[name] == "":
                                issues.append(_issue(f"{binding_path}.{name}", "", "non_empty_string", "invalid_value"))
                    if "role" in binding and type(binding["role"]) is str and binding["role"] != "question":
                        issues.append(_issue(f"{binding_path}.role", binding["role"], "question", "invalid_value"))
                    if _type(binding, "selected_member", binding_path, ["string", "null"], lambda v: v is None or type(v) is str, issues):
                        member = binding["selected_member"]
                        if type(member) is str and not _canonical_member(member, image=True):
                            issues.append(_issue(f"{binding_path}.selected_member", _invalid_scalar(member), "canonical_nfc_posix_images_member", "invalid_value"))
            if selection is not None and type(question.get("solution_line_spans")) is list:
                spans = question["solution_line_spans"]
                if selection.answer_mapping == "missing_from_source" and spans:
                    issues.append(_mapping_issue("source_contract_mismatch", selection, "", f"{path}.solution_line_spans", {"actual": len(spans), "expected": 0, "reason": "cross_field_violation"}))
                if selection.answer_mapping == "source_answer" and not spans:
                    issues.append(_mapping_issue("source_contract_mismatch", selection, "", f"{path}.solution_line_spans", {"actual": 0, "expected": "positive_length", "reason": "cross_field_violation"}))
                required_member = manifest.answer_member if selection.answer_number is not None else manifest.primary_member
                for span_index, span in enumerate(spans):
                    if type(span) is dict and type(span.get("member")) is str and span["member"] != required_member:
                        issues.append(_mapping_issue("source_contract_mismatch", selection, "", f"{path}.solution_line_spans[{span_index}].member", {"actual": span["member"], "expected": required_member, "reason": "cross_field_violation"}))

    ignored = top.get("ignored_line_spans") if valid.get("ignored_line_spans") else None
    if type(ignored) is list:
        for index, raw_span in enumerate(ignored):
            path = f"$.ignored_line_spans[{index}]"
            span = _exact_keys(raw_span, _IGNORED_LINE, path, issues)
            if span is None:
                continue
            if all(name in span for name in _LINE_SPAN):
                _validate_line_span(
                    {name: span[name] for name in _LINE_SPAN},
                    path,
                    issues,
                )
            if _type(span, "reason", path, "string", lambda v: type(v) is str, issues) and span["reason"] == "":
                issues.append(_issue(f"{path}.reason", "", "non_empty_string", "invalid_value"))
        if len({_canonical_json(item) for item in ignored}) != len(ignored):
            issues.append(_issue("$.ignored_line_spans", len(ignored), "unique_items", "cross_field_violation"))
    ignored_images = top.get("ignored_image_members") if valid.get("ignored_image_members") else None
    if type(ignored_images) is list:
        for index, item in enumerate(ignored_images):
            _validate_ignored_image(item, f"$.ignored_image_members[{index}]", issues)
        bound_members = {
            binding["selected_member"]
            for question in questions or []
            if type(question) is dict and type(question.get("image_bindings")) is list
            for binding in question["image_bindings"]
            if type(binding) is dict
            and type(binding.get("selected_member")) is str
            and _canonical_member(binding["selected_member"], image=True)
        }
        for index, item in enumerate(ignored_images):
            if (
                type(item) is dict
                and type(item.get("member")) is str
                and _canonical_member(item["member"], image=True)
                and item["member"] in bound_members
            ):
                issues.append(
                    _issue(
                        f"$.ignored_image_members[{index}].member",
                        item["member"],
                        "not_selected_and_ignored",
                        "cross_field_violation",
                    )
                )
    if issues:
        raise MmdAdapterBlockedError(tuple(issues))


def _validate_mapping_schema(payload: dict[str, object], raw: bytes) -> None:
    issues: list[MmdAdapterIssue] = []
    top = _exact_keys(payload, _MAPPING_TOP, "$", issues)
    assert top is not None
    valid: dict[str, bool] = {}
    for name in ("schema_version", "mapping_mode", "source_kind", "source_sha256", "primary_member", "primary_member_sha256", "source_id", "chapter"):
        valid[name] = _type(top, name, "$", "string", lambda v: type(v) is str, issues)
    for name in ("answer_member", "answer_member_sha256"):
        valid[name] = _type(top, name, "$", ["string", "null"], lambda v: v is None or type(v) is str, issues)
    for name in ("questions", "ignored_spans", "ignored_image_members"):
        valid[name] = _type(top, name, "$", "array", lambda v: type(v) is list, issues)
    for name, expected in (("schema_version", "task9b-source-mapping-v1"), ("mapping_mode", "explicit")):
        if valid.get(name) and top[name] != expected:
            issues.append(_issue(f"$.{name}", top[name], expected, "invalid_value"))
    if valid.get("source_kind") and top["source_kind"] not in {"mmd", "mmd_zip"}:
        issues.append(_issue("$.source_kind", top["source_kind"], ["mmd", "mmd_zip"], "invalid_value"))
    for name in ("source_sha256", "primary_member_sha256"):
        if valid.get(name) and _SHA256.fullmatch(top[name]) is None:
            issues.append(_issue(f"$.{name}", _invalid_scalar(top[name]), "lowercase_hex_64", "invalid_value"))
    if valid.get("answer_member_sha256") and type(top["answer_member_sha256"]) is str and _SHA256.fullmatch(top["answer_member_sha256"]) is None:
        issues.append(_issue("$.answer_member_sha256", _invalid_scalar(top["answer_member_sha256"]), "lowercase_hex_64", "invalid_value"))
    for name in ("primary_member", "answer_member"):
        if valid.get(name) and type(top[name]) is str and not _canonical_member(top[name], image=False):
            issues.append(_issue(f"$.{name}", _invalid_scalar(top[name]), "canonical_nfc_posix_mmd_member", "invalid_value"))
    if valid.get("source_id"):
        value = top["source_id"]
        assert type(value) is str
        if not value or "\r" in value or "\n" in value:
            issues.append(_issue("$.source_id", _invalid_scalar(value) if value else "", "single_line_non_empty", "invalid_value"))
    if valid.get("chapter") and top["chapter"] == "":
        issues.append(_issue("$.chapter", "", "non_empty_string", "invalid_value"))
    if valid.get("answer_member") and valid.get("answer_member_sha256"):
        if top["answer_member"] is None and top["answer_member_sha256"] is not None:
            issues.append(_issue("$.answer_member_sha256", "present", "null_when_answer_member_null", "cross_field_violation"))
        elif top["answer_member"] is not None and top["answer_member_sha256"] is None:
            issues.append(_issue("$.answer_member_sha256", "null", "lowercase_hex_64_when_answer_member_present", "cross_field_violation"))

    questions = top.get("questions") if valid.get("questions") else None
    if type(questions) is list:
        seen_ids: set[str] = set()
        for index, raw_question in enumerate(questions):
            path = f"$.questions[{index}]"
            question = _exact_keys(raw_question, _MAPPING_QUESTION, path, issues)
            if question is None:
                continue
            if _type(question, "semantic_order", path, "integer", lambda v: type(v) is int, issues) and question["semantic_order"] != index:
                issues.append(_issue(f"{path}.semantic_order", question["semantic_order"], index, "cross_field_violation"))
            for name in ("proposed_question_id", "source_question_number", "source_section"):
                if _type(question, name, path, "string", lambda v: type(v) is str, issues):
                    observed = question[name]
                    assert type(observed) is str
                    if not observed:
                        issues.append(_issue(f"{path}.{name}", "", "non_empty_string", "invalid_value"))
                    if name == "proposed_question_id":
                        if observed in seen_ids:
                            issues.append(_issue(f"{path}.{name}", _invalid_scalar(observed), "unique_proposed_question_id", "cross_field_violation"))
                        seen_ids.add(observed)
            if "question_span" in question:
                _validate_byte_span(
                    question["question_span"],
                    f"{path}.question_span",
                    issues,
                )
            for array_name in ("solution_spans", "explanation_spans"):
                if _type(question, array_name, path, "array", lambda v: type(v) is list, issues):
                    spans = question[array_name]
                    assert type(spans) is list
                    for span_index, span in enumerate(spans):
                        _validate_byte_span(span, f"{path}.{array_name}[{span_index}]", issues)
                    if len({_canonical_json(span) for span in spans}) != len(spans):
                        issues.append(_issue(f"{path}.{array_name}", len(spans), "unique_items", "cross_field_violation"))
            if _type(question, "image_bindings", path, "array", lambda v: type(v) is list, issues):
                bindings = question["image_bindings"]
                assert type(bindings) is list
                for binding_index, raw_binding in enumerate(bindings):
                    binding_path = f"{path}.image_bindings[{binding_index}]"
                    binding = _exact_keys(raw_binding, _MAPPING_IMAGE, binding_path, issues)
                    if binding is None:
                        continue
                    if _type(binding, "semantic_order", binding_path, "integer", lambda v: type(v) is int, issues) and binding["semantic_order"] != binding_index:
                        issues.append(_issue(f"{binding_path}.semantic_order", binding["semantic_order"], binding_index, "cross_field_violation"))
                    if "token_span" in binding:
                        _validate_byte_span(
                            binding["token_span"],
                            f"{binding_path}.token_span",
                            issues,
                        )
                    scalar_validity = {
                        name: _type(
                            binding,
                            name,
                            binding_path,
                            "string",
                            lambda v: type(v) is str,
                            issues,
                        )
                        for name in ("raw_target", "canonical_path", "role")
                    }
                    if scalar_validity["raw_target"] and binding["raw_target"] == "":
                        issues.append(
                            _issue(
                                f"{binding_path}.raw_target",
                                "",
                                "non_empty_string",
                                "invalid_value",
                            )
                        )
                    if scalar_validity["canonical_path"]:
                        canonical_path = binding["canonical_path"]
                        if canonical_path == "":
                            issues.append(
                                _issue(
                                    f"{binding_path}.canonical_path",
                                    "",
                                    "non_empty_string",
                                    "invalid_value",
                                )
                            )
                        elif not _canonical_member(canonical_path, image=True):
                            issues.append(
                                _issue(
                                    f"{binding_path}.canonical_path",
                                    _invalid_scalar(canonical_path),
                                    "canonical_nfc_posix_images_member",
                                    "invalid_value",
                                )
                            )
                    if type(binding.get("role")) is str and binding["role"] != "question":
                        issues.append(_issue(f"{binding_path}.role", binding["role"], "question", "invalid_value"))
                    if _type(binding, "selected_member", binding_path, ["string", "null"], lambda v: v is None or type(v) is str, issues):
                        member = binding["selected_member"]
                        if type(member) is str and not _canonical_member(member, image=True):
                            issues.append(_issue(f"{binding_path}.selected_member", _invalid_scalar(member), "canonical_nfc_posix_images_member", "invalid_value"))

    ignored = top.get("ignored_spans") if valid.get("ignored_spans") else None
    if type(ignored) is list:
        for index, raw_span in enumerate(ignored):
            path = f"$.ignored_spans[{index}]"
            span = _exact_keys(raw_span, (*_BYTE_SPAN, "reason"), path, issues)
            if span is None:
                continue
            if all(name in span for name in _BYTE_SPAN):
                _validate_byte_span(
                    {name: span[name] for name in _BYTE_SPAN},
                    path,
                    issues,
                )
            if _type(span, "reason", path, "string", lambda v: type(v) is str, issues) and span["reason"] == "":
                issues.append(_issue(f"{path}.reason", "", "non_empty_string", "invalid_value"))
        canonical_ready = all(
            type(item) is dict
            and type(item.get("member")) is str
            and type(item.get("start_byte")) is int
            and type(item.get("end_byte")) is int
            and type(item.get("reason")) is str
            for item in ignored
        )
        canonical = sorted(ignored, key=lambda item: (item["member"], item["start_byte"], item["end_byte"], item["reason"])) if canonical_ready else ignored
        if canonical_ready and ignored != canonical:
            issues.append(_issue("$.ignored_spans", hashlib.sha256(_canonical_json(ignored).encode()).hexdigest(), hashlib.sha256(_canonical_json(canonical).encode()).hexdigest(), "cross_field_violation"))
    ignored_images = top.get("ignored_image_members") if valid.get("ignored_image_members") else None
    if type(ignored_images) is list:
        for index, item in enumerate(ignored_images):
            _validate_ignored_image(item, f"$.ignored_image_members[{index}]", issues)
        canonical_images_ready = all(
            type(item) is dict
            and type(item.get("member")) is str
            and type(item.get("reason")) is str
            for item in ignored_images
        )
        canonical_images = sorted(ignored_images, key=lambda item: (item["member"], item["reason"])) if canonical_images_ready else ignored_images
        if canonical_images_ready and ignored_images != canonical_images:
            issues.append(_issue("$.ignored_image_members", hashlib.sha256(_canonical_json(ignored_images).encode()).hexdigest(), hashlib.sha256(_canonical_json(canonical_images).encode()).hexdigest(), "cross_field_violation"))
    if not issues and raw != _canonical_json(payload).encode("utf-8"):
        issues.append(_issue("$", hashlib.sha256(raw).hexdigest(), hashlib.sha256(_canonical_json(payload).encode()).hexdigest(), "invalid_value"))
    if issues:
        raise MmdAdapterBlockedError(tuple(issues))


def _source_free_mapping(payload: dict[str, object], manifest: MmdAdapterManifest) -> None:
    issues: list[MmdAdapterIssue] = []
    questions = payload["questions"]
    assert type(questions) is list
    if len(questions) != manifest.expected_candidate_count:
        issues.append(_mapping_issue("candidate_count_mismatch", None, "", "expected_candidate_count", {"actual": len(questions), "expected": manifest.expected_candidate_count, "reason": "candidate_count"}))
    for index, question in enumerate(questions):
        if type(question) is not dict or index >= len(manifest.selections):
            continue
        selection = manifest.selections[index]
        for name, selection_name in (("proposed_question_id", "proposed_question_id"), ("source_question_number", "number"), ("source_section", "source_section")):
            if type(question.get(name)) is str and question[name] != getattr(selection, selection_name):
                issues.append(_mapping_issue("source_contract_mismatch", selection, "", f"$.questions[{index}].{name}", {"actual": question[name], "expected": getattr(selection, selection_name), "reason": "mapping_selection_mismatch"}))
        spans = question.get("solution_spans")
        if type(spans) is list:
            if selection.answer_mapping == "missing_from_source" and spans:
                issues.append(_mapping_issue("source_contract_mismatch", selection, "", f"$.questions[{index}].solution_spans", {"actual": len(spans), "expected": 0, "reason": "cross_field_violation"}))
            if selection.answer_mapping == "source_answer" and not spans:
                issues.append(_mapping_issue("source_contract_mismatch", selection, "", f"$.questions[{index}].solution_spans", {"actual": 0, "expected": "positive_length", "reason": "cross_field_violation"}))
            expected_member = manifest.answer_member if selection.answer_number is not None else manifest.primary_member
            for span_index, span in enumerate(spans):
                if type(span) is dict and type(span.get("member")) is str and span["member"] != expected_member:
                    issues.append(_mapping_issue("source_contract_mismatch", selection, "", f"$.questions[{index}].solution_spans[{span_index}].member", {"actual": span["member"], "expected": expected_member, "reason": "cross_field_violation"}))
    bound_members = {
        binding["selected_member"]
        for question in questions
        if type(question) is dict and type(question.get("image_bindings")) is list
        for binding in question["image_bindings"]
        if type(binding) is dict and type(binding.get("selected_member")) is str
    }
    ignored_images = payload["ignored_image_members"]
    assert type(ignored_images) is list
    for index, item in enumerate(ignored_images):
        assert type(item) is dict
        if item["member"] in bound_members:
            issues.append(
                _issue(
                    f"$.ignored_image_members[{index}].member",
                    item["member"],
                    "not_selected_and_ignored",
                    "cross_field_violation",
                )
            )
    if issues:
        raise MmdAdapterBlockedError(tuple(issues))


def _line_offsets(content: bytes) -> tuple[tuple[int, int], ...]:
    result: list[tuple[int, int]] = []
    position = 0
    while position < len(content):
        start = position
        while position < len(content) and content[position] not in {10, 13}:
            position += 1
        if position < len(content):
            if content[position] == 13 and position + 1 < len(content) and content[position + 1] == 10:
                position += 2
            else:
                position += 1
        result.append((start, position))
    return tuple(result)


def _span_dict(member: str, start: int, end: int) -> dict[str, object]:
    return {"member": member, "start_byte": start, "end_byte": end}


def _converted_span(
    line_span: dict[str, object],
    path: str,
    members: dict[str, bytes],
    selection: MmdSelection | None,
    issues: list[MmdAdapterIssue],
) -> dict[str, object] | None:
    member = line_span.get("member")
    start_line = line_span.get("line_start")
    end_line = line_span.get("line_end")
    offsets = _line_offsets(members[member]) if type(member) is str and member in members else ()
    valid = (
        type(member) is str
        and type(start_line) is int
        and type(end_line) is int
        and start_line >= 1
        and end_line >= start_line
        and end_line <= len(offsets)
    )
    if not valid:
        actual = {"end_byte": None, "member": member, "start_byte": None}
        issues.append(_mapping_issue("source_contract_mismatch", selection, "", path, {"actual": actual, "expected": "non_empty_in_bounds_half_open_span", "reason": "invalid_span"}))
        return None
    return _span_dict(member, offsets[start_line - 1][0], offsets[end_line - 1][1])


def _draft_to_mapping(
    draft: dict[str, object],
    manifest: MmdAdapterManifest,
    primary_bytes: bytes,
    answer_bytes: bytes | None,
) -> tuple[dict[str, object], tuple[str, ...]]:
    members = {manifest.primary_member: primary_bytes}
    if manifest.answer_member is not None and answer_bytes is not None:
        members[manifest.answer_member] = answer_bytes
    issues: list[MmdAdapterIssue] = []
    questions: list[dict[str, object]] = []
    notes: list[str] = []
    for index, raw_question in enumerate(draft["questions"]):
        assert type(raw_question) is dict
        selection = manifest.selections[index]
        question_span = _converted_span(raw_question["question_line_span"], f"$.questions[{index}].question_line_span", members, selection, issues)
        solution_spans = [
            value for span_index, span in enumerate(raw_question["solution_line_spans"])
            if (value := _converted_span(span, f"$.questions[{index}].solution_line_spans[{span_index}]", members, selection, issues)) is not None
        ]
        explanation_spans = [
            value for span_index, span in enumerate(raw_question["explanation_line_spans"])
            if (value := _converted_span(span, f"$.questions[{index}].explanation_line_spans[{span_index}]", members, selection, issues)) is not None
        ]
        bindings: list[dict[str, object]] = []
        for binding_index, binding in enumerate(raw_question["image_bindings"]):
            assert type(binding) is dict
            source_line = binding["source_line"]
            offsets = _line_offsets(primary_bytes)
            valid_line = type(source_line) is int and 1 <= source_line <= len(offsets)
            raw_target = binding["raw_target"]
            token = f"![]({raw_target})".encode("utf-8") if type(raw_target) is str else b""
            found = -1
            if valid_line:
                line_start, line_end = offsets[source_line - 1]
                found = primary_bytes[line_start:line_end].find(token)
            if valid_line and found >= 0:
                token_start = line_start + found
                token_end = token_start + len(token)
            else:
                token_start = line_start if valid_line else 0
                token_end = line_end if valid_line else 0
            bindings.append({
                "semantic_order": binding["semantic_order"],
                "token_span": _span_dict(manifest.primary_member, token_start, token_end),
                "raw_target": raw_target,
                "selected_member": binding["selected_member"],
                "canonical_path": raw_target[2:] if type(raw_target) is str and raw_target.startswith("./") else raw_target,
                "role": binding["role"],
            })
        questions.append({
            "semantic_order": raw_question["semantic_order"],
            "proposed_question_id": raw_question["proposed_question_id"],
            "source_question_number": raw_question["source_question_number"],
            "source_section": raw_question["source_section"],
            "question_span": question_span or _span_dict(manifest.primary_member, 0, 0),
            "solution_spans": solution_spans,
            "explanation_spans": explanation_spans,
            "image_bindings": bindings,
        })
        notes.append(raw_question["ambiguity_note"])
    ignored_spans: list[dict[str, object]] = []
    for index, raw_span in enumerate(draft["ignored_line_spans"]):
        converted = _converted_span(raw_span, f"$.ignored_line_spans[{index}]", members, None, issues)
        if converted is not None:
            ignored_spans.append({**converted, "reason": raw_span["reason"]})
    if issues:
        raise MmdAdapterBlockedError(tuple(issues))
    ignored_spans.sort(key=lambda value: (value["member"], value["start_byte"], value["end_byte"], value["reason"]))
    ignored_images = [dict(value) for value in draft["ignored_image_members"]]
    ignored_images.sort(key=lambda value: (value["member"], value["reason"]))
    return ({
        "schema_version": "task9b-source-mapping-v1",
        "mapping_mode": "explicit",
        "source_kind": manifest.source_kind,
        "source_sha256": manifest.source_sha256,
        "primary_member": manifest.primary_member,
        "primary_member_sha256": hashlib.sha256(primary_bytes).hexdigest(),
        "answer_member": manifest.answer_member,
        "answer_member_sha256": hashlib.sha256(answer_bytes).hexdigest() if answer_bytes is not None else None,
        "source_id": manifest.source_id,
        "chapter": manifest.chapter,
        "questions": questions,
        "ignored_spans": ignored_spans,
        "ignored_image_members": ignored_images,
    }, tuple(notes))


def _generic_span(value: dict[str, object]) -> tuple[str, int, int]:
    return value["member"], value["start_byte"], value["end_byte"]


def _span_locator(value: dict[str, object]) -> str:
    member, start, end = _generic_span(value)
    return f"{member}#bytes={start}:{end}"


def _validate_identity_and_spans(
    mapping: dict[str, object],
    manifest: MmdAdapterManifest,
    source_path: Path,
    primary_bytes: bytes,
    answer_bytes: bytes | None,
    *,
    draft_paths: bool = False,
) -> None:
    issues: list[MmdAdapterIssue] = []
    try:
        source_raw = _read_input(source_path, "source input")
    except (InputMissingError, InputFormatError):
        raise
    expected = {
        "source_kind": manifest.source_kind,
        "source_sha256": hashlib.sha256(source_raw).hexdigest(),
        "primary_member": manifest.primary_member,
        "primary_member_sha256": hashlib.sha256(primary_bytes).hexdigest(),
        "answer_member": manifest.answer_member,
        "answer_member_sha256": hashlib.sha256(answer_bytes).hexdigest() if answer_bytes is not None else None,
        "source_id": manifest.source_id,
        "chapter": manifest.chapter,
    }
    reasons = {
        "source_kind": "mapping_source_kind_mismatch",
        "source_sha256": "mapping_source_digest_mismatch",
        "primary_member": "mapping_primary_member_mismatch",
        "primary_member_sha256": "mapping_primary_digest_mismatch",
        "answer_member": "mapping_answer_member_mismatch",
        "answer_member_sha256": "mapping_answer_digest_mismatch",
        "source_id": "mapping_source_id_mismatch",
        "chapter": "mapping_chapter_mismatch",
    }
    for name, expected_value in expected.items():
        if mapping[name] != expected_value:
            issues.append(_issue(f"$.{name}", mapping[name], expected_value, reasons[name]))

    members = {manifest.primary_member: primary_bytes}
    if manifest.answer_member is not None and answer_bytes is not None:
        members[manifest.answer_member] = answer_bytes
    valid_spans: list[tuple[dict[str, object], str, MmdSelection | None, str]] = []
    for index, question in enumerate(mapping["questions"]):
        selection = manifest.selections[index] if index < len(manifest.selections) else None
        assert type(question) is dict
        groups = (("question_span", [question["question_span"]]), ("solution_spans", question["solution_spans"]), ("explanation_spans", question["explanation_spans"]))
        for group, spans in groups:
            for span_index, span in enumerate(spans):
                assert type(span) is dict
                rendered_group = (
                    "question_line_span"
                    if draft_paths and group == "question_span"
                    else "solution_line_spans"
                    if draft_paths and group == "solution_spans"
                    else "explanation_line_spans"
                    if draft_paths and group == "explanation_spans"
                    else group
                )
                path = f"$.questions[{index}].{rendered_group}" + (f"[{span_index}]" if group != "question_span" else "")
                member, start, end = _generic_span(span)
                valid = member in members and type(start) is int and type(end) is int and 0 <= start < end <= len(members[member])
                if not valid:
                    locator = _span_locator(span) if member in members and type(start) is int and type(end) is int and 0 <= start < end <= len(members[member]) else ""
                    issues.append(_mapping_issue("source_contract_mismatch", selection, locator, path, {"actual": span, "expected": "non_empty_in_bounds_half_open_span", "reason": "invalid_span"}))
                    continue
                if group == "question_span" and member != manifest.primary_member:
                    issues.append(_mapping_issue("source_contract_mismatch", selection, _span_locator(span), path, {"actual": member, "expected": manifest.primary_member, "reason": "wrong_span_owner"}))
                    continue
                valid_spans.append((span, path, selection, group))
        for bind_index, binding in enumerate(question["image_bindings"]):
            assert type(binding) is dict
            span = binding["token_span"]
            assert type(span) is dict
            path = f"$.questions[{index}].image_bindings[{bind_index}].token_span"
            member, start, end = _generic_span(span)
            if not (member in members and 0 <= start < end <= len(members[member])):
                issues.append(_mapping_issue("source_contract_mismatch", selection, "", path, {"actual": span, "expected": "non_empty_in_bounds_half_open_span", "reason": "invalid_span"}))
            elif member != manifest.primary_member:
                issues.append(_mapping_issue("source_contract_mismatch", selection, _span_locator(span), path, {"actual": member, "expected": manifest.primary_member, "reason": "wrong_span_owner"}))
            else:
                question_span = question["question_span"]
                question_member, question_start, question_end = _generic_span(
                    question_span
                )
                if (
                    question_member in members
                    and type(question_start) is int
                    and type(question_end) is int
                    and 0 <= question_start < question_end <= len(members[question_member])
                    and question_member == manifest.primary_member
                    and not (
                        question_start <= start < end <= question_end
                    )
                ):
                    issues.append(
                        _mapping_issue(
                            "source_contract_mismatch",
                            selection,
                            _span_locator(span),
                            path,
                            {
                                "actual": {key: span[key] for key in _BYTE_SPAN},
                                "expected": {
                                    key: question_span[key] for key in _BYTE_SPAN
                                },
                                "reason": "wrong_span_owner",
                            },
                        )
                    )

    for index, span in enumerate(mapping["ignored_spans"]):
        assert type(span) is dict
        member, start, end = _generic_span(span)
        path = f"$.ignored_line_spans[{index}]" if draft_paths else f"$.ignored_spans[{index}]"
        if not (member in members and 0 <= start < end <= len(members[member])):
            issues.append(_mapping_issue("source_contract_mismatch", None, "", path, {"actual": {key: span[key] for key in _BYTE_SPAN}, "expected": "non_empty_in_bounds_half_open_span", "reason": "invalid_span"}))
        else:
            valid_spans.append((span, path, None, "ignored"))

    owners = valid_spans
    for later_index, (later, path, selection, _group) in enumerate(owners):
        overlap = next(
            (
                earlier_owner
                for earlier_owner in owners[:later_index]
                if earlier_owner[0]["member"] == later["member"]
                and earlier_owner[0]["end_byte"] > later["start_byte"]
                and later["end_byte"] > earlier_owner[0]["start_byte"]
            ),
            None,
        )
        if overlap is not None:
            earlier, _earlier_path, earlier_selection, _earlier_group = overlap
            issues.append(_mapping_issue("source_contract_mismatch", selection or earlier_selection, _span_locator(later), path, {"actual": {key: later[key] for key in _BYTE_SPAN}, "expected": {key: earlier[key] for key in _BYTE_SPAN}, "reason": "span_ownership_overlap"}))
    if issues:
        raise MmdAdapterBlockedError(tuple(issues))


def _coverage_gaps(content: bytes, owners: list[tuple[int, int]]) -> tuple[tuple[int, int], ...]:
    covered = bytearray(len(content))
    for start, end in owners:
        covered[start:end] = b"\x01" * (end - start)
    whitespace = {9, 10, 11, 12, 13, 32}
    gaps: list[tuple[int, int]] = []
    position = 0
    while position < len(content):
        if covered[position] or content[position] in whitespace:
            position += 1
            continue
        start = position
        while position < len(content) and not covered[position] and content[position] not in whitespace:
            position += 1
        gaps.append((start, position))
    return tuple(gaps)


def _build_ir(
    mapping: dict[str, object],
    manifest: MmdAdapterManifest,
    primary_bytes: bytes,
    answer_bytes: bytes | None,
    image_bytes: dict[str, bytes],
    source_inventory: tuple[str, ...],
    *,
    approved: bool,
) -> tuple[_SourceDocument, tuple[tuple[MmdSelection, _SourceQuestion], ...], tuple[str, ...], tuple[str, ...]]:
    source_inventory = tuple(
        member for member in source_inventory if not _is_allowed_metadata(member)
    )
    primary = _SourceMember(manifest.primary_member, hashlib.sha256(primary_bytes).hexdigest(), primary_bytes)
    answer = _SourceMember(manifest.answer_member, hashlib.sha256(answer_bytes).hexdigest(), answer_bytes) if manifest.answer_member is not None and answer_bytes is not None else None
    decode_issues: list[MmdAdapterIssue] = []
    for member, field in ((primary, "primary_member"), (answer, "answer_member")):
        if member is None:
            continue
        try:
            member.content.decode("utf-8")
        except UnicodeDecodeError:
            decode_issues.append(
                _mapping_issue(
                    "mmd_parse_failed",
                    None,
                    "",
                    field,
                    {
                        "end_byte": None,
                        "member": member.relative_path,
                        "reason": "invalid_utf8",
                        "start_byte": None,
                    },
                )
            )
    if decode_issues:
        raise MmdAdapterBlockedError(tuple(decode_issues))
    contents = {manifest.primary_member: primary_bytes}
    if answer is not None:
        contents[answer.relative_path] = answer.content
    invalid_question_spans: set[int] = set()
    span_decode_issues: list[MmdAdapterIssue] = []
    for index, raw_question in enumerate(mapping["questions"]):
        for group in ("question_span", "solution_spans", "explanation_spans"):
            spans = (
                (raw_question[group],)
                if group == "question_span"
                else tuple(raw_question[group])
            )
            for span in spans:
                member = span["member"]
                start = span["start_byte"]
                end = span["end_byte"]
                try:
                    contents[member][start:end].decode("utf-8")
                except UnicodeDecodeError:
                    span_decode_issues.append(
                        _mapping_issue(
                            "mmd_parse_failed",
                            None,
                            _span_locator(span),
                            (
                                "primary_member"
                                if member == manifest.primary_member
                                else "answer_member"
                            ),
                            {
                                "end_byte": end,
                                "member": member,
                                "reason": "invalid_utf8",
                                "start_byte": start,
                            },
                        )
                    )
                    if group == "question_span":
                        invalid_question_spans.add(index)
    members = [primary]
    if answer is not None:
        members.append(answer)
    members.extend(_SourceMember(path, hashlib.sha256(content).hexdigest(), content) for path, content in sorted(image_bytes.items()))
    physical_order = {
        semantic: source_order
        for source_order, semantic in enumerate(
            sorted(range(len(mapping["questions"])), key=lambda index: (
                mapping["questions"][index]["question_span"]["member"],
                mapping["questions"][index]["question_span"]["start_byte"],
                mapping["questions"][index]["question_span"]["end_byte"],
            ))
        )
    }
    questions_by_semantic: list[_SourceQuestion] = []
    m4_issues: list[MmdAdapterIssue] = []
    m4_issues.extend(span_decode_issues)
    m5_issues: list[MmdAdapterIssue] = []
    all_targets: list[tuple[str, str, int, int]] = []
    all_bound: set[str] = set()
    for index, raw_question in enumerate(mapping["questions"]):
        selection = manifest.selections[index]
        question_m5_start = len(m5_issues)
        fragment = raw_question["question_span"]
        if index in invalid_question_spans:
            continue
        text_spans, lex_images, targets, parse_issues = _lex_mapped_question(primary, fragment["start_byte"], fragment["end_byte"], selection.language_layout)
        all_targets.extend(targets)
        m4_issues.extend(parse_issues)
        if parse_issues:
            continue
        refs: list[_SourceImageRef] = []
        bindings = raw_question["image_bindings"]
        bound_tokens: set[tuple[str, int, int]] = set()
        for binding_index, binding in enumerate(bindings):
            token = binding["token_span"]
            expected = (binding["raw_target"], token["start_byte"], token["end_byte"])
            if expected not in lex_images:
                m5_issues.append(_mapping_issue("image_binding_invalid", selection, _span_locator(token), "expected_image_members", {"matches": [], "raw_target": binding["raw_target"], "reason": "ambiguous_reference"}))
                continue
            if expected in bound_tokens:
                m5_issues.append(_mapping_issue("image_binding_invalid", selection, _span_locator(token), "expected_image_members", {"matches": [binding["canonical_path"]], "raw_target": binding["raw_target"], "reason": "duplicate_token_binding"}))
                continue
            bound_tokens.add(expected)
            selected = binding["selected_member"]
            canonical = binding["canonical_path"]
            expected_selected = selection.expected_image_members[binding_index] if binding_index < len(selection.expected_image_members) else None
            matches = sorted(path for path in source_inventory if path == canonical)
            selected_is_valid = (
                selected == expected_selected
                if expected_selected in source_inventory
                else selected is None
            )
            if (
                not selected_is_valid
                or canonical != binding["raw_target"][2:]
                or (selected is not None and selected != canonical)
            ):
                m5_issues.append(_mapping_issue("image_binding_invalid", selection, _span_locator(token), "expected_image_members", {"matches": matches, "raw_target": binding["raw_target"], "reason": "selection_conflict"}))
                continue
            if selected is not None:
                all_bound.add(selected)
            refs.append(_SourceImageRef(binding_index, _SourceSpan(token["member"], token["start_byte"], token["end_byte"], "image_token", "shared"), binding["raw_target"], selected if selected in image_bytes else None))
        for raw_target, token_start, token_end in lex_images:
            token_key = (raw_target, token_start, token_end)
            if token_key not in bound_tokens:
                canonical = raw_target[2:] if raw_target.startswith("./") else raw_target
                matches = sorted(path for path in source_inventory if path == canonical)
                m5_issues.append(
                    _mapping_issue(
                        "image_binding_invalid",
                        selection,
                        f"{manifest.primary_member}#bytes={token_start}:{token_end}",
                        "expected_image_members",
                        {
                            "matches": matches,
                            "raw_target": raw_target,
                            "reason": "ambiguous_reference",
                        },
                    )
                )
        for expected_member in selection.expected_image_members[len(lex_images):]:
            m5_issues.append(
                _mapping_issue(
                    "image_binding_invalid",
                    selection,
                    _span_locator(fragment),
                    "expected_image_members",
                    {
                        "expected_member": expected_member,
                        "matches": [],
                        "raw_target": None,
                        "reason": "selection_surplus",
                    },
                )
            )
        normalized_refs = tuple(
            _SourceImageRef(
                source_order,
                reference.token_span,
                reference.raw_target,
                reference.resolved_member,
            )
            for source_order, reference in enumerate(refs)
        )
        question = _SourceQuestion(
            physical_order[index],
            raw_question["source_question_number"],
            raw_question["source_section"],
            _SourceSpan(fragment["member"], fragment["start_byte"], fragment["end_byte"], "question", "und"),
            text_spans,
            tuple(_SourceSpan(span["member"], span["start_byte"], span["end_byte"], "solution", "und") for span in raw_question["solution_spans"]),
            tuple(_SourceSpan(span["member"], span["start_byte"], span["end_byte"], "explanation", "und") for span in raw_question["explanation_spans"]),
            normalized_refs,
        )
        if selection.language_layout in {"english_then_chinese", "interleaved_bilingual"}:
            m5_issues.extend(_language_issues(selection, question, primary))
        if len(m5_issues) == question_m5_start:
            questions_by_semantic.append(question)
    member_by_path = {member.relative_path: member for member in members}
    m4_issues.extend(
        _image_target_safety_issues(
            tuple(
                sorted(
                    all_targets,
                    key=lambda value: (value[0], value[2], value[3], value[1]),
                )
            ),
            source_inventory,
            member_by_path,
        )
    )
    if m4_issues:
        raise MmdAdapterBlockedError(tuple(m4_issues))

    ignored_entries = mapping["ignored_image_members"]
    ignored_names = [entry["member"] for entry in ignored_entries]
    image_inventory = sorted(
        path
        for path in source_inventory
        if len(PurePosixPath(path).parts) >= 2
        and PurePosixPath(path).parts[0] == "images"
        and PurePosixPath(path).suffix in {".jpg", ".jpeg", ".png"}
    )
    image_issues: list[MmdAdapterIssue] = []
    seen_ignored: set[str] = set()
    for name in ignored_names:
        if name in seen_ignored:
            image_issues.append(_mapping_issue("image_binding_invalid", None, "", "ignored_image_members", {"member": name, "reason": "duplicate_ignored_image"}))
        elif name not in image_inventory:
            image_issues.append(_mapping_issue("image_binding_invalid", None, "", "ignored_image_members", {"member": name, "reason": "ignored_member_missing"}))
        elif name in all_bound:
            image_issues.append(_mapping_issue("image_binding_invalid", None, "", "ignored_image_members", {"member": name, "reason": "bound_and_ignored"}))
        seen_ignored.add(name)
    unbound = tuple(name for name in image_inventory if name not in all_bound and name not in seen_ignored)
    if approved:
        image_issues.extend(_mapping_issue("image_binding_invalid", None, "", "ignored_image_members", {"member": name, "reason": "unaccounted_inventory_image"}) for name in unbound)
    if m5_issues or image_issues:
        raise MmdAdapterBlockedError(tuple((*m5_issues, *image_issues)))

    owners: dict[str, list[tuple[int, int]]] = {name: [] for name in contents}
    for question in mapping["questions"]:
        for span in (question["question_span"], *question["solution_spans"], *question["explanation_spans"]):
            if span["member"] in owners:
                owners[span["member"]].append((span["start_byte"], span["end_byte"]))
    for span in mapping["ignored_spans"]:
        if span["member"] in owners:
            owners[span["member"]].append((span["start_byte"], span["end_byte"]))
    gaps = tuple(f"{member}#bytes={start}:{end}" for member in sorted(contents) for start, end in _coverage_gaps(contents[member], owners[member]))
    if approved and gaps:
        raise MmdAdapterBlockedError(tuple(_mapping_issue("source_contract_mismatch", None, locator, "coverage", {"end_byte": int(locator.rsplit(":", 1)[1]), "member": locator.split("#", 1)[0], "reason": "unaccounted_non_whitespace", "start_byte": int(locator.split("=")[1].split(":")[0])}) for locator in gaps))
    document = _SourceDocument(manifest.primary_member, tuple(members), tuple(sorted(questions_by_semantic, key=lambda item: item.source_order)))
    bindings = tuple((manifest.selections[index], questions_by_semantic[index]) for index in range(len(questions_by_semantic)))
    return document, bindings, gaps, unbound


def _review_bytes(
    mapping: dict[str, object],
    mapping_sha256: str,
    notes: tuple[str, ...],
    gaps: tuple[str, ...],
    unbound: tuple[str, ...],
    primary_bytes: bytes,
    answer_bytes: bytes | None,
) -> bytes:
    members = {mapping["primary_member"]: primary_bytes}
    if mapping["answer_member"] is not None and answer_bytes is not None:
        members[mapping["answer_member"]] = answer_bytes
    offsets_by_member = {
        member: _line_offsets(content)
        for member, content in members.items()
    }

    def line_range(span: dict[str, object]) -> str:
        offsets = offsets_by_member[span["member"]]
        start = next((index + 1 for index, (a, b) in enumerate(offsets) if a <= span["start_byte"] < b), "?")
        end = next((index + 1 for index, (a, b) in enumerate(offsets) if a < span["end_byte"] <= b), "?")
        return f"{start}-{end}"

    def preview(spans: list[dict[str, object]]) -> str:
        if not spans:
            return "MISSING"
        text = "".join(
            members[span["member"]][span["start_byte"]:span["end_byte"]].decode("utf-8")
            for span in spans
        )
        return _canonical_json(text[:240])

    lines = [
        "# PROPOSED SOURCE MAPPING REVIEW",
        "",
        f"Source ID: {mapping['source_id']}",
        f"Source SHA-256: {mapping['source_sha256']}",
        f"Primary SHA-256: {mapping['primary_member_sha256']}",
        f"Answer SHA-256: {mapping['answer_member_sha256'] or 'NONE'}",
        f"Mapping SHA-256: {mapping_sha256}",
        f"Candidate count: {len(mapping['questions'])}",
        "",
    ]
    for index, question in enumerate(mapping["questions"]):
        question_preview = primary_bytes[
            question["question_span"]["start_byte"] : question["question_span"]["end_byte"]
        ].decode("utf-8")[:240]
        lines.extend([
            f"## Candidate {index + 1}: {question['proposed_question_id']}",
            f"Number: {question['source_question_number']}",
            f"Section: {question['source_section']}",
            f"Question lines: {line_range(question['question_span'])}",
            f"Question preview: {_canonical_json(question_preview)}",
            f"Solution: {', '.join(line_range(span) for span in question['solution_spans']) or 'MISSING'}",
            f"Solution preview: {preview(question['solution_spans'])}",
            f"Explanation: {', '.join(line_range(span) for span in question['explanation_spans']) or 'MISSING'}",
            f"Explanation preview: {preview(question['explanation_spans'])}",
            f"Images: {', '.join(binding['canonical_path'] for binding in question['image_bindings']) or 'NONE'}",
            f"Ambiguity note: {notes[index]}",
            "",
        ])
    lines.append("## Warnings")
    lines.extend(f"UNMAPPED_NON_WHITESPACE {gap}" for gap in gaps)
    lines.extend(f"UNBOUND_IMAGE {name}" for name in unbound)
    if not gaps and not unbound:
        lines.append("NONE")
    lines.extend(["", "## Ignored spans"])
    lines.extend(f"{_span_locator(span)} — {span['reason']}" for span in mapping["ignored_spans"])
    lines.extend(["", "## Ignored images"])
    lines.extend(f"{entry['member']} — {entry['reason']}" for entry in mapping["ignored_image_members"])
    return ("\n".join(lines) + "\n").encode("utf-8")


def _preflight_destination(output: Path, config: PipelineConfig) -> None:
    resolved = config.require_staging_output(output)
    if resolved == config.staging_root:
        raise ConfigurationError("output path must be a strict staging descendant")
    if output.exists() or output.is_symlink():
        raise OutputConflictError("output path already exists")


def propose_mmd_source_mapping(
    selection_manifest_path: Path,
    source_path: Path,
    draft_path: Path,
    proposal_dir: Path,
    config: PipelineConfig,
) -> SourceMappingProposal:
    for value, name in ((selection_manifest_path, "selection_manifest_path"), (source_path, "source_path"), (draft_path, "draft_path"), (proposal_dir, "proposal_dir")):
        if not isinstance(value, Path):
            raise TypeError(f"{name} must be a pathlib.Path")
    if type(config) is not PipelineConfig:
        raise TypeError("config must be an exact PipelineConfig")
    _preflight_destination(proposal_dir, config)
    manifest = _decode_manifest(
        selection_manifest_path,
        source_path,
        allowed_language_layouts=_MODE_B_LAYOUTS,
    )
    draft = _decode_object(_read_input(draft_path, "source-mapping draft"))
    _validate_draft(draft, manifest)
    primary_bytes, answer_bytes, image_bytes, source_inventory = read_selected_source(manifest, source_path)
    mapping, notes = _draft_to_mapping(draft, manifest, primary_bytes, answer_bytes)
    _validate_mapping_schema(mapping, _canonical_json(mapping).encode("utf-8"))
    _validate_identity_and_spans(
        mapping,
        manifest,
        source_path,
        primary_bytes,
        answer_bytes,
        draft_paths=True,
    )
    _document, _bindings, gaps, unbound = _build_ir(mapping, manifest, primary_bytes, answer_bytes, image_bytes, source_inventory, approved=False)
    mapping_bytes = _canonical_json(mapping).encode("utf-8")
    mapping_sha = hashlib.sha256(mapping_bytes).hexdigest()
    review = _review_bytes(
        mapping,
        mapping_sha,
        notes,
        gaps,
        unbound,
        primary_bytes,
        answer_bytes,
    )
    proposal_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(tempfile.mkdtemp(prefix=f".{proposal_dir.name}-", dir=proposal_dir.parent))
    try:
        (temporary_root / "source_mapping.json").write_bytes(mapping_bytes)
        (temporary_root / "SOURCE_MAPPING_REVIEW.md").write_bytes(review)
        proposal = SourceMappingProposal(proposal_dir, proposal_dir / "source_mapping.json", proposal_dir / "SOURCE_MAPPING_REVIEW.md", manifest.source_id, manifest.source_sha256, mapping_sha, len(mapping["questions"]))
        os.replace(temporary_root, proposal_dir)
        return proposal
    finally:
        if temporary_root.exists():
            shutil.rmtree(temporary_root)


def adapt_mmd_package_from_mapping(
    selection_manifest_path: Path,
    source_mapping_path: Path,
    approval: SourceMappingApproval,
    source_path: Path,
    output_dir: Path,
    config: PipelineConfig,
) -> AdaptedImportPackage:
    for value, name in ((selection_manifest_path, "selection_manifest_path"), (source_mapping_path, "source_mapping_path"), (source_path, "source_path"), (output_dir, "output_dir")):
        if not isinstance(value, Path):
            raise TypeError(f"{name} must be a pathlib.Path")
    if type(approval) is not SourceMappingApproval:
        raise TypeError("approval must be an exact SourceMappingApproval")
    if type(config) is not PipelineConfig:
        raise TypeError("config must be an exact PipelineConfig")
    _preflight_destination(output_dir, config)
    manifest = _decode_manifest(
        selection_manifest_path,
        source_path,
        allowed_language_layouts=_MODE_B_LAYOUTS,
    )
    raw = _read_input(source_mapping_path, "source mapping")
    mapping = _decode_object(raw)
    _validate_mapping_schema(mapping, raw)
    _source_free_mapping(mapping, manifest)
    digest = hashlib.sha256(raw).hexdigest()
    approval_issues: list[MmdAdapterIssue] = []
    if approval.source_id != mapping["source_id"]:
        approval_issues.append(_issue("approval.source_id", approval.source_id, mapping["source_id"], "approval_source_id_mismatch"))
    if approval.mapping_sha256 != digest:
        approval_issues.append(_issue("approval.mapping_sha256", approval.mapping_sha256, digest, "approval_mapping_digest_mismatch"))
    expected_text = f"USER APPROVED SOURCE MAPPING {mapping['source_id']} {digest}"
    if not approval_issues and approval.approval_text != expected_text:
        approval_issues.append(_issue("approval.approval_text", hashlib.sha256(approval.approval_text.encode()).hexdigest(), hashlib.sha256(expected_text.encode()).hexdigest(), "approval_text_mismatch"))
    if approval_issues:
        raise MmdAdapterBlockedError(tuple(approval_issues))
    primary_bytes, answer_bytes, image_bytes, source_inventory = read_selected_source(manifest, source_path)
    _validate_identity_and_spans(mapping, manifest, source_path, primary_bytes, answer_bytes)
    document, bindings, _gaps, _unbound = _build_ir(mapping, manifest, primary_bytes, answer_bytes, image_bytes, source_inventory, approved=True)
    candidates = _map_candidates(manifest, document, bindings)
    members = {member.relative_path: member for member in document.members}
    primary = members[manifest.primary_member]
    answer = members.get(manifest.answer_member) if manifest.answer_member is not None else None
    return _publish_package(output_dir, manifest, document, bindings, candidates, primary, answer, image_bytes)


def adapt_mmd_package_from_mapping_v120(
    selection_manifest_path: Path,
    source_mapping_path: Path,
    approval: SourceMappingApproval,
    source_path: Path,
    output_dir: Path,
    config: PipelineConfig,
) -> V120AdaptedImportPackage:
    for value, name in (
        (selection_manifest_path, "selection_manifest_path"),
        (source_mapping_path, "source_mapping_path"),
        (source_path, "source_path"),
        (output_dir, "output_dir"),
    ):
        if not isinstance(value, Path):
            raise TypeError(f"{name} must be a pathlib.Path")
    if type(approval) is not SourceMappingApproval:
        raise TypeError("approval must be an exact SourceMappingApproval")
    if type(config) is not PipelineConfig:
        raise TypeError("config must be an exact PipelineConfig")
    try:
        reconstructed_config = PipelineConfig(config.repo_root)
    except (TypeError, PipelineError) as exc:
        raise ConfigurationError("config does not satisfy PipelineConfig authority") from exc
    if reconstructed_config != config:
        raise ConfigurationError("config does not satisfy PipelineConfig authority")
    _preflight_destination(output_dir, config)
    manifest = _decode_manifest(
        selection_manifest_path,
        source_path,
        allowed_language_layouts=_MODE_B_LAYOUTS,
    )
    raw = _read_input(source_mapping_path, "source mapping")
    mapping = _decode_object(raw)
    _validate_mapping_schema(mapping, raw)
    _source_free_mapping(mapping, manifest)
    digest = hashlib.sha256(raw).hexdigest()
    approval_issues: list[MmdAdapterIssue] = []
    if approval.source_id != mapping["source_id"]:
        approval_issues.append(_issue("approval.source_id", approval.source_id, mapping["source_id"], "approval_source_id_mismatch"))
    if approval.mapping_sha256 != digest:
        approval_issues.append(_issue("approval.mapping_sha256", approval.mapping_sha256, digest, "approval_mapping_digest_mismatch"))
    expected_text = f"USER APPROVED SOURCE MAPPING {mapping['source_id']} {digest}"
    if not approval_issues and approval.approval_text != expected_text:
        approval_issues.append(_issue("approval.approval_text", hashlib.sha256(approval.approval_text.encode()).hexdigest(), hashlib.sha256(expected_text.encode()).hexdigest(), "approval_text_mismatch"))
    if approval_issues:
        raise MmdAdapterBlockedError(tuple(approval_issues))
    primary_bytes, answer_bytes, image_bytes, source_inventory = read_selected_source(manifest, source_path)
    _validate_identity_and_spans(mapping, manifest, source_path, primary_bytes, answer_bytes)
    document, bindings, _gaps, _unbound = _build_ir(mapping, manifest, primary_bytes, answer_bytes, image_bytes, source_inventory, approved=True)
    members = {member.relative_path: member for member in document.members}
    primary = members[manifest.primary_member]
    answer = members.get(manifest.answer_member) if manifest.answer_member is not None else None
    from .v120_projection import _project_v120_package

    return _project_v120_package(
        output_dir,
        manifest,
        document,
        bindings,
        _map_candidates(manifest, document, bindings),
        primary,
        answer,
        image_bytes,
    )


__all__ = (
    "SourceMappingProposal",
    "SourceMappingApproval",
    "propose_mmd_source_mapping",
    "adapt_mmd_package_from_mapping",
    "adapt_mmd_package_from_mapping_v120",
)
