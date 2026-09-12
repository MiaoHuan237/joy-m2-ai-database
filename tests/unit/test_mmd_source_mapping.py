from __future__ import annotations

from dataclasses import FrozenInstanceError, MISSING, fields, is_dataclass
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from typing import get_type_hints
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.errors import (
    ConfigurationError,
    InputFormatError,
    InputMissingError,
    OutputConflictError,
    PipelineError,
)
from joy_m2.ingest.adapter_models import (
    AdaptedImportPackage,
    MmdAdapterBlockedError,
    MmdAdapterIssue,
)


FIXTURE_ROOT = ROOT / "tests/fixtures/task9b/explicit"
SOURCE_BYTES = (FIXTURE_ROOT / "source.mmd").read_bytes()
IMAGE_BYTES = (FIXTURE_ROOT / "images/diagram.jpg").read_bytes()
SOURCE_ID = "TASK9B-EXPLICIT-FIXTURE"
HEX_A = "a" * 64
HEX_B = "b" * 64


def canonical_json(payload: object) -> bytes:
    return json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def blocking_issue(
    field: str,
    evidence: dict[str, object],
    *,
    code: str = "source_contract_mismatch",
    proposed_question_id: str | None = None,
    source_locator: str = "",
) -> MmdAdapterIssue:
    return MmdAdapterIssue(
        code,
        "blocking",
        proposed_question_id,
        source_locator,
        field,
        canonical_json(evidence).decode("utf-8"),
    )


def stable_issues(*issues: MmdAdapterIssue) -> tuple[MmdAdapterIssue, ...]:
    return tuple(
        sorted(
            issues,
            key=lambda issue: (
                issue.source_locator,
                issue.proposed_question_id or "",
                issue.code,
                issue.field,
                issue.evidence,
            ),
        )
    )


def source_mapping_module(testcase: unittest.TestCase):
    try:
        return importlib.import_module("joy_m2.ingest.source_mapping")
    except ModuleNotFoundError:
        testcase.fail("explicit source-mapping API is not implemented")


def require_api(testcase: unittest.TestCase, name: str):
    try:
        module = importlib.import_module("joy_m2.ingest.source_mapping")
    except ModuleNotFoundError:
        testcase.fail(f"explicit source-mapping behavior is missing: {name}")
    value = getattr(module, name, None)
    testcase.assertIsNotNone(value, f"explicit source-mapping behavior is missing: {name}")
    return value


def selection(
    proposed_question_id: str,
    number: str,
    *,
    answer_mapping: str,
    language_layout: str = "source_english",
) -> dict[str, object]:
    return {
        "proposed_question_id": proposed_question_id,
        "kind": "example",
        "number": number,
        "source_section": "Worksheet",
        "language_layout": language_layout,
        "answer_mapping": answer_mapping,
        "answer_number": None,
        "expected_image_members": ["images/diagram.jpg"],
        "primary_type": "代数",
        "tags": ["练习"],
        "tag_status": "proposed",
        "difficulty_level": 2,
        "difficulty_status": "proposed",
    }


def valid_manifest(source_bytes: bytes = SOURCE_BYTES) -> dict[str, object]:
    return {
        "schema_version": "task9b-mmd-adapter-v1",
        "batch_id": "TASK9B-EXPLICIT-BATCH",
        "source_kind": "mmd",
        "source_sha256": sha256(source_bytes),
        "primary_member": "source.mmd",
        "answer_member": None,
        "source_id": SOURCE_ID,
        "chapter": "Explicit fixture",
        "expected_candidate_count": 2,
        "selections": [
            selection("EXPLICIT-002", "A", answer_mapping="source_answer"),
            selection("EXPLICIT-001", "A", answer_mapping="missing_from_source"),
        ],
    }


def line_span(start: int, end: int) -> dict[str, object]:
    return {"member": "source.mmd", "line_start": start, "line_end": end}


def valid_draft() -> dict[str, object]:
    return {
        "schema_version": "task9b-source-mapping-draft-v1",
        "source_id": SOURCE_ID,
        "chapter": "Explicit fixture",
        "mapping_mode": "explicit",
        "questions": [
            {
                "semantic_order": 0,
                "proposed_question_id": "EXPLICIT-002",
                "source_question_number": "A",
                "source_section": "Worksheet",
                "question_line_span": line_span(2, 4),
                "solution_line_spans": [line_span(5, 6)],
                "explanation_line_spans": [line_span(7, 8)],
                "image_bindings": [
                    {
                        "semantic_order": 0,
                        "source_line": 4,
                        "raw_target": "./images/diagram.jpg",
                        "selected_member": "images/diagram.jpg",
                        "role": "question",
                    }
                ],
                "ambiguity_note": "first repeated label",
            },
            {
                "semantic_order": 1,
                "proposed_question_id": "EXPLICIT-001",
                "source_question_number": "A",
                "source_section": "Worksheet",
                "question_line_span": line_span(9, 11),
                "solution_line_spans": [],
                "explanation_line_spans": [],
                "image_bindings": [
                    {
                        "semantic_order": 0,
                        "source_line": 11,
                        "raw_target": "./images/diagram.jpg",
                        "selected_member": "images/diagram.jpg",
                        "role": "question",
                    }
                ],
                "ambiguity_note": "second repeated label",
            },
        ],
        "ignored_line_spans": [
            {**line_span(1, 1), "reason": "worksheet heading"},
            {**line_span(13, 13), "reason": "worksheet footer"},
        ],
        "ignored_image_members": [],
    }


def make_case(
    root: Path,
    *,
    manifest: dict[str, object] | None = None,
    draft: dict[str, object] | None = None,
    source_bytes: bytes = SOURCE_BYTES,
) -> tuple[Path, Path, Path, Path, PipelineConfig]:
    source_path = root / "source.mmd"
    source_path.write_bytes(source_bytes)
    image_path = root / "images/diagram.jpg"
    image_path.parent.mkdir(parents=True)
    image_path.write_bytes(IMAGE_BYTES)
    selection_path = root / "selection.json"
    selection_path.write_bytes(canonical_json(manifest or valid_manifest(source_bytes)))
    draft_path = root / "draft.json"
    draft_path.write_bytes(canonical_json(draft or valid_draft()))
    proposal_dir = root / "data/staging/proposal"
    return selection_path, source_path, draft_path, proposal_dir, PipelineConfig(root)


def propose(testcase: unittest.TestCase, root: Path, **overrides):
    function = require_api(testcase, "propose_mmd_source_mapping")
    selection_path, source_path, draft_path, proposal_dir, config = make_case(
        root, **overrides
    )
    return function(selection_path, source_path, draft_path, proposal_dir, config)


def approval_for(testcase: unittest.TestCase, proposal):
    approval_type = require_api(testcase, "SourceMappingApproval")
    return approval_type(
        proposal.source_id,
        proposal.mapping_sha256,
        f"USER APPROVED SOURCE MAPPING {proposal.source_id} {proposal.mapping_sha256}",
    )


def physical_line_offsets(content: bytes) -> tuple[tuple[int, int], ...]:
    lines: list[tuple[int, int]] = []
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
        lines.append((start, position))
    return tuple(lines)


def canonical_mapping(
    *,
    source_bytes: bytes = SOURCE_BYTES,
    manifest: dict[str, object] | None = None,
    draft: dict[str, object] | None = None,
) -> dict[str, object]:
    manifest = manifest or valid_manifest(source_bytes)
    draft = draft or valid_draft()
    offsets = physical_line_offsets(source_bytes)

    def convert(span: dict[str, object]) -> dict[str, object]:
        start = span["line_start"]
        end = span["line_end"]
        assert type(start) is int and type(end) is int
        return {
            "member": span["member"],
            "start_byte": offsets[start - 1][0],
            "end_byte": offsets[end - 1][1],
        }

    questions: list[dict[str, object]] = []
    for question in draft["questions"]:
        question_span = convert(question["question_line_span"])
        bindings: list[dict[str, object]] = []
        for binding in question["image_bindings"]:
            source_line = binding["source_line"]
            assert type(source_line) is int
            line_start, line_end = offsets[source_line - 1]
            token = f"![]({binding['raw_target']})".encode("utf-8")
            relative = source_bytes[line_start:line_end].find(token)
            token_start = line_start + (relative if relative >= 0 else 0)
            token_end = token_start + (len(token) if relative >= 0 else line_end - line_start)
            bindings.append(
                {
                    "semantic_order": binding["semantic_order"],
                    "token_span": {
                        "member": "source.mmd",
                        "start_byte": token_start,
                        "end_byte": token_end,
                    },
                    "raw_target": binding["raw_target"],
                    "selected_member": binding["selected_member"],
                    "canonical_path": (
                        binding["raw_target"][2:]
                        if binding["raw_target"].startswith("./")
                        else binding["raw_target"]
                    ),
                    "role": binding["role"],
                }
            )
        questions.append(
            {
                "semantic_order": question["semantic_order"],
                "proposed_question_id": question["proposed_question_id"],
                "source_question_number": question["source_question_number"],
                "source_section": question["source_section"],
                "question_span": question_span,
                "solution_spans": [convert(span) for span in question["solution_line_spans"]],
                "explanation_spans": [convert(span) for span in question["explanation_line_spans"]],
                "image_bindings": bindings,
            }
        )
    ignored_spans = [
        {**convert(span), "reason": span["reason"]}
        for span in draft["ignored_line_spans"]
    ]
    ignored_spans.sort(key=lambda value: (value["member"], value["start_byte"], value["end_byte"], value["reason"]))
    ignored_images = [dict(value) for value in draft["ignored_image_members"]]
    ignored_images.sort(key=lambda value: (value["member"], value["reason"]))
    return {
        "schema_version": "task9b-source-mapping-v1",
        "mapping_mode": "explicit",
        "source_kind": manifest["source_kind"],
        "source_sha256": manifest["source_sha256"],
        "primary_member": manifest["primary_member"],
        "primary_member_sha256": sha256(source_bytes),
        "answer_member": manifest["answer_member"],
        "answer_member_sha256": None,
        "source_id": manifest["source_id"],
        "chapter": manifest["chapter"],
        "questions": questions,
        "ignored_spans": ignored_spans,
        "ignored_image_members": ignored_images,
    }


def write_mapping_case(
    testcase: unittest.TestCase,
    root: Path,
    *,
    mutation=None,
    source_bytes: bytes = SOURCE_BYTES,
    manifest: dict[str, object] | None = None,
    draft: dict[str, object] | None = None,
    approval_source_id: str | None = None,
    approval_digest: str | None = None,
):
    function = require_api(testcase, "adapt_mmd_package_from_mapping")
    selection_path, source_path, _draft_path, _proposal_dir, config = make_case(
        root,
        source_bytes=source_bytes,
        manifest=manifest,
        draft=draft,
    )
    payload = canonical_mapping(source_bytes=source_bytes, manifest=manifest, draft=draft)
    if mutation is not None:
        mutation(payload)
    mapping_path = root / "source_mapping.json"
    mapping_bytes = canonical_json(payload)
    mapping_path.write_bytes(mapping_bytes)
    digest = sha256(mapping_bytes)
    # The typed approval cannot carry an invalid mapping source_id; keep the
    # independently valid selection authority so malformed mapping IDs reach
    # the mapping decoder's M0 diagnostics.
    source_id = SOURCE_ID
    approval_type = require_api(testcase, "SourceMappingApproval")
    actual_source_id = approval_source_id if approval_source_id is not None else source_id
    actual_digest = approval_digest if approval_digest is not None else digest
    approval = approval_type(
        actual_source_id,
        actual_digest,
        f"USER APPROVED SOURCE MAPPING {actual_source_id} {actual_digest}",
    )
    return lambda output_name="package": function(
        selection_path,
        mapping_path,
        approval,
        source_path,
        root / f"data/staging/{output_name}",
        config,
    )


def adapt_from_mapping(testcase: unittest.TestCase, root: Path):
    invoke = write_mapping_case(testcase, root)
    result = invoke()
    mapping_path = root / "source_mapping.json"
    mapping_bytes = mapping_path.read_bytes()
    proposal_type = require_api(testcase, "SourceMappingProposal")
    proposal_root = root / "data/staging/proposal-input"
    proposal = proposal_type(
        proposal_root,
        proposal_root / "source_mapping.json",
        proposal_root / "SOURCE_MAPPING_REVIEW.md",
        SOURCE_ID,
        sha256(SOURCE_BYTES),
        sha256(mapping_bytes),
        2,
    )
    return proposal, result


def adapt_from_proposal(testcase: unittest.TestCase, root: Path):
    proposal = propose(testcase, root)
    function = require_api(testcase, "adapt_mmd_package_from_mapping")
    output = root / "data/staging/package"
    result = function(
        root / "selection.json",
        proposal.mapping_path,
        approval_for(testcase, proposal),
        root / "source.mmd",
        output,
        PipelineConfig(root),
    )
    return proposal, result


def mutate_mapping(testcase: unittest.TestCase, root: Path, mutation):
    return write_mapping_case(testcase, root, mutation=mutation)


def invoke_mapping_bytes(
    testcase: unittest.TestCase,
    root: Path,
    mapping_bytes: bytes,
):
    function = require_api(testcase, "adapt_mmd_package_from_mapping")
    selection_path, source_path, _draft_path, _proposal_dir, config = make_case(root)
    mapping_path = root / "source_mapping.json"
    mapping_path.write_bytes(mapping_bytes)
    digest = sha256(mapping_bytes)
    approval_type = require_api(testcase, "SourceMappingApproval")
    approval = approval_type(
        SOURCE_ID,
        digest,
        f"USER APPROVED SOURCE MAPPING {SOURCE_ID} {digest}",
    )
    return lambda: function(
        selection_path,
        mapping_path,
        approval,
        source_path,
        root / "data/staging/package",
        config,
    )


def write_answer_archive_case(
    testcase: unittest.TestCase,
    root: Path,
    mutation=None,
    *,
    answer_bytes: bytes = b"Answer A\n",
):
    function = require_api(testcase, "adapt_mmd_package_from_mapping")
    source_path = root / "source.mmd.zip"
    image_member = "images/diagram.jpg"
    with zipfile.ZipFile(source_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("source.mmd", SOURCE_BYTES)
        archive.writestr("answer.mmd", answer_bytes)
        archive.writestr(image_member, IMAGE_BYTES)
    archive_bytes = source_path.read_bytes()
    manifest = valid_manifest()
    manifest["source_kind"] = "mmd_zip"
    manifest["source_sha256"] = sha256(archive_bytes)
    manifest["answer_member"] = "answer.mmd"
    manifest["selections"][0]["answer_number"] = "A1"
    selection_path = root / "selection.json"
    selection_path.write_bytes(canonical_json(manifest))
    mapping = canonical_mapping(manifest=manifest)
    mapping["source_sha256"] = sha256(archive_bytes)
    mapping["answer_member"] = "answer.mmd"
    mapping["answer_member_sha256"] = sha256(answer_bytes)
    mapping["questions"][0]["solution_spans"] = [
        {"member": "answer.mmd", "start_byte": 0, "end_byte": len(answer_bytes)}
    ]
    mapping["ignored_spans"].append(
        {
            "member": "source.mmd",
            "start_byte": 65,
            "end_byte": 85,
            "reason": "primary answer material superseded by selected answer member",
        }
    )
    mapping["ignored_spans"].sort(
        key=lambda value: (value["member"], value["start_byte"], value["end_byte"], value["reason"])
    )
    if mutation is not None:
        mutation(mapping)
    mapping_path = root / "source_mapping.json"
    mapping_bytes = canonical_json(mapping)
    mapping_path.write_bytes(mapping_bytes)
    digest = sha256(mapping_bytes)
    approval_type = require_api(testcase, "SourceMappingApproval")
    approval = approval_type(
        SOURCE_ID,
        digest,
        f"USER APPROVED SOURCE MAPPING {SOURCE_ID} {digest}",
    )
    return mapping, lambda: function(
        selection_path,
        mapping_path,
        approval,
        source_path,
        root / "data/staging/package",
        PipelineConfig(root),
    )


def write_image_archive_case(
    testcase: unittest.TestCase,
    root: Path,
    *,
    timestamp: tuple[int, int, int, int, int, int] = (2024, 1, 2, 3, 4, 6),
    reverse_order: bool = False,
    mapping_mutation=None,
    extra_members: tuple[tuple[str, bytes], ...] = (),
):
    function = require_api(testcase, "adapt_mmd_package_from_mapping")
    source_path = root / "source.mmd.zip"
    members = [
        ("source.mmd", SOURCE_BYTES),
        ("images/diagram.jpg", IMAGE_BYTES),
        ("images/unused-a.jpg", b"approved-ignored-image-a\n"),
        ("images/unused-b.jpg", b"approved-ignored-image-b\n"),
        *extra_members,
    ]
    if reverse_order:
        members.reverse()
    with zipfile.ZipFile(source_path, "w") as archive:
        for member, content in members:
            info = zipfile.ZipInfo(member, timestamp)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.create_system = 3
            info.external_attr = 0o100644 << 16
            archive.writestr(info, content)
    source_archive = source_path.read_bytes()
    manifest = valid_manifest()
    manifest["source_kind"] = "mmd_zip"
    manifest["source_sha256"] = sha256(source_archive)
    selection_path = root / "selection.json"
    selection_path.write_bytes(canonical_json(manifest))
    mapping = canonical_mapping(manifest=manifest)
    mapping["source_sha256"] = sha256(source_archive)
    mapping["ignored_image_members"] = [
        {"member": "images/unused-a.jpg", "reason": "approved unused resource A"},
        {"member": "images/unused-b.jpg", "reason": "approved unused resource B"},
    ]
    if mapping_mutation is not None:
        mapping_mutation(mapping)
    mapping_path = root / "source_mapping.json"
    mapping_bytes = canonical_json(mapping)
    mapping_path.write_bytes(mapping_bytes)
    digest = sha256(mapping_bytes)
    approval_type = require_api(testcase, "SourceMappingApproval")
    approval = approval_type(
        SOURCE_ID,
        digest,
        f"USER APPROVED SOURCE MAPPING {SOURCE_ID} {digest}",
    )
    return sha256(source_archive), lambda output_name="package": function(
        selection_path,
        mapping_path,
        approval,
        source_path,
        root / f"data/staging/{output_name}",
        PipelineConfig(root),
    )


class PublicContractTests(unittest.TestCase):
    def test_module_has_exact_public_surface(self):
        module = source_mapping_module(self)
        self.assertEqual(
            module.__all__,
            (
                "SourceMappingProposal",
                "SourceMappingApproval",
                "propose_mmd_source_mapping",
                "adapt_mmd_package_from_mapping",
            ),
        )

    def test_public_functions_have_exact_signatures(self):
        module = source_mapping_module(self)
        proposal_type = require_api(self, "SourceMappingProposal")
        expected = {
            "propose_mmd_source_mapping": (
                ("selection_manifest_path", "source_path", "draft_path", "proposal_dir", "config"),
                (Path, Path, Path, Path, PipelineConfig),
                proposal_type,
            ),
            "adapt_mmd_package_from_mapping": (
                (
                    "selection_manifest_path",
                    "source_mapping_path",
                    "approval",
                    "source_path",
                    "output_dir",
                    "config",
                ),
                (
                    Path,
                    Path,
                    require_api(self, "SourceMappingApproval"),
                    Path,
                    Path,
                    PipelineConfig,
                ),
                AdaptedImportPackage,
            ),
        }
        for name, (names, annotations, return_type) in expected.items():
            function = require_api(self, name)
            signature = inspect.signature(function)
            parameters = tuple(signature.parameters.values())
            self.assertEqual(tuple(value.name for value in parameters), names)
            self.assertEqual(tuple(value.annotation for value in parameters), annotations)
            self.assertTrue(all(value.default is inspect.Parameter.empty for value in parameters))
            self.assertTrue(
                all(
                    value.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
                    for value in parameters
                )
            )
            self.assertIs(signature.return_annotation, return_type)

    def test_private_manifest_decoder_uses_only_the_approved_allow_list_parameter(self):
        module = importlib.import_module("joy_m2.ingest.adapter")
        signature = inspect.signature(module._decode_manifest)
        self.assertEqual(
            tuple(signature.parameters),
            ("selection_manifest_path", "source_path", "allowed_language_layouts"),
        )
        parameter = signature.parameters["allowed_language_layouts"]
        self.assertIs(parameter.kind, inspect.Parameter.KEYWORD_ONLY)
        self.assertIs(parameter.default, inspect.Parameter.empty)

    def test_proposal_is_exact_frozen_no_default_carrier(self):
        carrier = require_api(self, "SourceMappingProposal")
        self.assertTrue(is_dataclass(carrier))
        self.assertEqual(
            tuple(value.name for value in fields(carrier)),
            (
                "proposal_root",
                "mapping_path",
                "review_path",
                "source_id",
                "source_sha256",
                "mapping_sha256",
                "candidate_count",
            ),
        )
        self.assertTrue(all(value.default is MISSING for value in fields(carrier)))
        self.assertEqual(
            get_type_hints(carrier),
            {
                "proposal_root": Path,
                "mapping_path": Path,
                "review_path": Path,
                "source_id": str,
                "source_sha256": str,
                "mapping_sha256": str,
                "candidate_count": int,
            },
        )
        root = Path("proposal")
        value = carrier(root, root / "source_mapping.json", root / "SOURCE_MAPPING_REVIEW.md", SOURCE_ID, HEX_A, HEX_B, 2)
        with self.assertRaises(FrozenInstanceError):
            value.source_id = "changed"

    def test_proposal_rejects_invalid_path_digest_and_count_values(self):
        carrier = require_api(self, "SourceMappingProposal")
        root = Path("proposal")
        valid = [root, root / "source_mapping.json", root / "SOURCE_MAPPING_REVIEW.md", SOURCE_ID, HEX_A, HEX_B, 2]
        invalid = (
            (0, "proposal"),
            (1, root / "wrong.json"),
            (2, root / "wrong.md"),
            (3, ""),
            (3, "bad\rsource-id"),
            (3, "bad\nsource-id"),
            (4, "A" * 64),
            (5, "x" * 64),
            (6, True),
            (6, -1),
        )
        for index, replacement in invalid:
            values = list(valid)
            values[index] = replacement
            with self.subTest(index=index, replacement=replacement), self.assertRaises(PipelineError):
                carrier(*values)

    def test_approval_is_exact_frozen_validated_carrier(self):
        carrier = require_api(self, "SourceMappingApproval")
        self.assertEqual(tuple(value.name for value in fields(carrier)), ("source_id", "mapping_sha256", "approval_text"))
        self.assertTrue(all(value.default is MISSING for value in fields(carrier)))
        self.assertEqual(get_type_hints(carrier), {"source_id": str, "mapping_sha256": str, "approval_text": str})
        text = f"USER APPROVED SOURCE MAPPING {SOURCE_ID} {HEX_A}"
        value = carrier(SOURCE_ID, HEX_A, text)
        with self.assertRaises(FrozenInstanceError):
            value.approval_text = "changed"
        for source_id in ("bad\rid", "bad\nid"):
            matching_text = f"USER APPROVED SOURCE MAPPING {source_id} {HEX_A}"
            with self.subTest(source_id=repr(source_id)), self.assertRaises(PipelineError):
                carrier(source_id, HEX_A, matching_text)
        for values in (
            (SOURCE_ID, HEX_A, text + "\n"),
            (SOURCE_ID, HEX_A, "wrong"),
            (SOURCE_ID, HEX_A.upper(), text),
        ):
            with self.subTest(values=values), self.assertRaises(PipelineError):
                carrier(*values)


class StrictDecodingTests(unittest.TestCase):
    def test_valid_draft_converts_inclusive_lines_to_exact_raw_byte_spans(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proposal = propose(self, root)
            payload = json.loads(proposal.mapping_path.read_text(encoding="utf-8"))
            lines = SOURCE_BYTES.splitlines(keepends=True)
            offsets = [0]
            for line in lines:
                offsets.append(offsets[-1] + len(line))
            first = payload["questions"][0]
            self.assertEqual(first["question_span"], {"member": "source.mmd", "start_byte": offsets[1], "end_byte": offsets[4]})
            self.assertEqual(first["solution_spans"], [{"member": "source.mmd", "start_byte": offsets[4], "end_byte": offsets[6]}])
            self.assertEqual(first["explanation_spans"], [{"member": "source.mmd", "start_byte": offsets[6], "end_byte": offsets[8]}])

    def test_draft_json_is_strict_utf8_no_bom_duplicate_aware_and_object_only(self):
        function = require_api(self, "propose_mmd_source_mapping")
        bad_bytes = (b"\xef\xbb\xbf{}", b"{", b"[]", b'{"schema_version":1,"schema_version":2}', b"\xff")
        for index, raw in enumerate(bad_bytes):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                selection_path, source_path, draft_path, proposal_dir, config = make_case(root)
                draft_path.write_bytes(raw)
                with self.subTest(index=index), self.assertRaises(MmdAdapterBlockedError):
                    function(selection_path, source_path, draft_path, proposal_dir, config)
                self.assertFalse(proposal_dir.exists())

    def test_draft_exact_top_level_schema_and_bool_as_int(self):
        function = require_api(self, "propose_mmd_source_mapping")
        mutations = (
            lambda value: value.pop("chapter"),
            lambda value: value.__setitem__("extra", 1),
            lambda value: value.__setitem__("questions", {}),
            lambda value: value["questions"][0].__setitem__("semantic_order", True),
            lambda value: value["questions"][0]["question_line_span"].__setitem__("line_start", 0),
        )
        for index, mutation in enumerate(mutations):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                draft = valid_draft()
                mutation(draft)
                selection_path, source_path, draft_path, proposal_dir, config = make_case(root, draft=draft)
                with self.subTest(index=index), self.assertRaises(MmdAdapterBlockedError):
                    function(selection_path, source_path, draft_path, proposal_dir, config)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft = valid_draft()
            draft["questions"][0]["semantic_order"] = True
            selection_path, source_path, draft_path, proposal_dir, config = make_case(root, draft=draft)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                function(selection_path, source_path, draft_path, proposal_dir, config)
            issue = next(issue for issue in caught.exception.issues if issue.field == "$.questions[0].semantic_order")
            self.assertEqual(issue.code, "source_contract_mismatch")
            self.assertEqual(
                json.loads(issue.evidence),
                {"actual": "boolean", "expected": "integer", "reason": "wrong_type"},
            )

    def test_source_free_selection_disagreement_blocks_before_source_access(self):
        function = require_api(self, "propose_mmd_source_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path, source_path, draft_path, proposal_dir, config = make_case(root)
            draft = valid_draft()
            draft["questions"][0]["proposed_question_id"] = "WRONG"
            draft_path.write_bytes(canonical_json(draft))
            source_path.unlink()
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                function(selection_path, source_path, draft_path, proposal_dir, config)
            issue = caught.exception.issues[0]
            self.assertEqual(issue.code, "source_contract_mismatch")
            self.assertEqual(issue.field, "$.questions[0].proposed_question_id")
            self.assertEqual(
                json.loads(issue.evidence),
                {
                    "actual": "WRONG",
                    "expected": "EXPLICIT-002",
                    "reason": "mapping_selection_mismatch",
                },
            )
            self.assertFalse(proposal_dir.exists())

    def test_draft_source_line_zero_is_m0_and_does_not_read_source(self):
        function = require_api(self, "propose_mmd_source_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft = valid_draft()
            draft["questions"][0]["image_bindings"][0]["source_line"] = 0
            selection_path, source_path, draft_path, proposal_dir, config = make_case(
                root,
                draft=draft,
            )
            source_path.unlink()
            try:
                function(
                    selection_path,
                    source_path,
                    draft_path,
                    proposal_dir,
                    config,
                )
            except MmdAdapterBlockedError as caught:
                self.assertEqual(len(caught.issues), 1)
                issue = caught.issues[0]
                self.assertEqual(issue.code, "source_contract_mismatch")
                self.assertEqual(
                    issue.field,
                    "$.questions[0].image_bindings[0].source_line",
                )
                self.assertEqual(
                    json.loads(issue.evidence),
                    {
                        "actual": 0,
                        "expected": "positive_integer",
                        "reason": "invalid_value",
                    },
                )
            except InputMissingError as caught:
                self.fail(f"draft source_line validation read the source: {caught}")
            else:
                self.fail("draft source_line=0 was accepted")
            self.assertFalse(proposal_dir.exists())

    def test_crlf_and_cr_physical_lines_convert_without_newline_normalization(self):
        function = require_api(self, "propose_mmd_source_mapping")
        for separator in (b"\r\n", b"\r"):
            source_bytes = SOURCE_BYTES.replace(b"\n", separator)
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                selection_path, source_path, draft_path, proposal_dir, config = make_case(
                    root,
                    source_bytes=source_bytes,
                    manifest=valid_manifest(source_bytes),
                )
                proposal = function(selection_path, source_path, draft_path, proposal_dir, config)
                payload = json.loads(proposal.mapping_path.read_bytes())
                offsets = physical_line_offsets(source_bytes)
                self.assertEqual(
                    payload["questions"][0]["question_span"],
                    {
                        "member": "source.mmd",
                        "start_byte": offsets[1][0],
                        "end_byte": offsets[3][1],
                    },
                )

    def test_every_nested_draft_object_uses_an_exact_key_set(self):
        function = require_api(self, "propose_mmd_source_mapping")
        mutations = (
            lambda value: value["questions"][0].__setitem__("extra", 1),
            lambda value: value["questions"][0].pop("ambiguity_note"),
            lambda value: value["questions"][0]["question_line_span"].__setitem__("extra", 1),
            lambda value: value["questions"][0]["question_line_span"].pop("member"),
            lambda value: value["questions"][0]["image_bindings"][0].__setitem__("extra", 1),
            lambda value: value["questions"][0]["image_bindings"][0].pop("role"),
            lambda value: value["ignored_line_spans"][0].__setitem__("extra", 1),
            lambda value: value["ignored_image_members"].append({"member": "images/other.jpg", "reason": "unused", "extra": 1}),
        )
        for index, mutation in enumerate(mutations):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                draft = valid_draft()
                mutation(draft)
                selection_path, source_path, draft_path, proposal_dir, config = make_case(root, draft=draft)
                with self.subTest(index=index), self.assertRaises(MmdAdapterBlockedError) as caught:
                    function(selection_path, source_path, draft_path, proposal_dir, config)
                self.assertTrue(all(issue.code == "source_contract_mismatch" for issue in caught.exception.issues))
                self.assertFalse(proposal_dir.exists())

    def test_draft_enums_paths_orders_duplicates_and_cross_fields_are_strict(self):
        function = require_api(self, "propose_mmd_source_mapping")
        mutations = (
            lambda value: value.__setitem__("mapping_mode", "parsed"),
            lambda value: value["questions"][0]["question_line_span"].__setitem__("member", "../source.mmd"),
            lambda value: value["questions"][1].__setitem__("semantic_order", 2),
            lambda value: value["questions"][1].__setitem__("proposed_question_id", "EXPLICIT-002"),
            lambda value: value["questions"][1].__setitem__("source_question_number", "WRONG"),
            lambda value: value["questions"][1].__setitem__("source_section", "WRONG"),
            lambda value: value["questions"][1].__setitem__("solution_line_spans", [line_span(9, 9)]),
            lambda value: value["questions"][0]["image_bindings"][0].__setitem__("semantic_order", 1),
            lambda value: value["questions"][0]["image_bindings"][0].__setitem__("role", "solution"),
            lambda value: value["ignored_line_spans"].append(dict(value["ignored_line_spans"][0])),
        )
        for index, mutation in enumerate(mutations):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                draft = valid_draft()
                mutation(draft)
                selection_path, source_path, draft_path, proposal_dir, config = make_case(root, draft=draft)
                with self.subTest(index=index), self.assertRaises(MmdAdapterBlockedError):
                    function(selection_path, source_path, draft_path, proposal_dir, config)

    def test_cr_or_lf_source_id_is_rejected_at_m0_before_source_access(self):
        function = require_api(self, "propose_mmd_source_mapping")
        for source_id in ("BAD\rID", "BAD\nID"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                draft = valid_draft()
                draft["source_id"] = source_id
                selection_path, source_path, draft_path, proposal_dir, config = make_case(root, draft=draft)
                source_path.unlink()
                with self.subTest(source_id=repr(source_id)), self.assertRaises(MmdAdapterBlockedError) as caught:
                    function(selection_path, source_path, draft_path, proposal_dir, config)
                self.assertEqual(
                    caught.exception.issues,
                    (
                        blocking_issue(
                            "$.source_id",
                            {
                                "actual": sha256(source_id.encode("utf-8")),
                                "expected": "single_line_non_empty",
                                "reason": "invalid_value",
                            },
                        ),
                    ),
                )
                self.assertFalse(proposal_dir.exists())

    def test_selection_manifest_cr_or_lf_source_id_blocks_proposal_before_source_access(self):
        function = require_api(self, "propose_mmd_source_mapping")
        for source_id in ("BAD\rID", "BAD\nID"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                manifest = valid_manifest()
                manifest["source_id"] = source_id
                selection_path, source_path, draft_path, proposal_dir, config = make_case(
                    root,
                    manifest=manifest,
                )
                source_path.unlink()
                with self.subTest(source_id=repr(source_id)), self.assertRaises(MmdAdapterBlockedError) as caught:
                    function(selection_path, source_path, draft_path, proposal_dir, config)
                self.assertEqual(
                    caught.exception.issues,
                    (
                        blocking_issue(
                            "$.source_id",
                            {
                                "actual": sha256(source_id.encode("utf-8")),
                                "expected": "single_line_non_empty",
                                "reason": "invalid_value",
                            },
                        ),
                    ),
                )
                self.assertFalse(proposal_dir.exists())


class ProposalContractTests(StrictDecodingTests):
    def test_valid_proposal_is_deterministic_across_independent_roots(self):
        require_api(self, "propose_mmd_source_mapping")
        results = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                proposal = propose(self, root)
                results.append((proposal.mapping_path.read_bytes(), proposal.review_path.read_bytes(), proposal.mapping_sha256))
        self.assertEqual(results[0], results[1])

    def test_valid_proposal_has_exact_paths_digest_count_and_canonical_json(self):
        require_api(self, "propose_mmd_source_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proposal = propose(self, root)
            self.assertEqual(proposal.proposal_root, root / "data/staging/proposal")
            self.assertEqual(proposal.mapping_path, proposal.proposal_root / "source_mapping.json")
            self.assertEqual(proposal.review_path, proposal.proposal_root / "SOURCE_MAPPING_REVIEW.md")
            self.assertEqual(proposal.source_id, SOURCE_ID)
            self.assertEqual(proposal.source_sha256, sha256(SOURCE_BYTES))
            self.assertEqual(proposal.mapping_sha256, sha256(proposal.mapping_path.read_bytes()))
            self.assertEqual(proposal.candidate_count, 2)
            payload = json.loads(proposal.mapping_path.read_bytes())
            self.assertEqual(proposal.mapping_path.read_bytes(), canonical_json(payload))

    def test_proposal_mapping_has_exact_nested_schema_types_and_orders(self):
        function = require_api(self, "propose_mmd_source_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "source.mmd.zip"
            with zipfile.ZipFile(source_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("source.mmd", SOURCE_BYTES)
                archive.writestr("images/diagram.jpg", IMAGE_BYTES)
                archive.writestr("images/unused.jpg", b"ignored-resource\n")
            manifest = valid_manifest()
            manifest["source_kind"] = "mmd_zip"
            manifest["source_sha256"] = sha256(source_path.read_bytes())
            draft = valid_draft()
            draft["ignored_image_members"] = [
                {"member": "images/unused.jpg", "reason": "approved ignored resource"}
            ]
            selection_path = root / "selection.json"
            selection_path.write_bytes(canonical_json(manifest))
            draft_path = root / "draft.json"
            draft_path.write_bytes(canonical_json(draft))
            proposal = function(
                selection_path,
                source_path,
                draft_path,
                root / "data/staging/proposal",
                PipelineConfig(root),
            )
            payload = json.loads(proposal.mapping_path.read_bytes())
        self.assertEqual(
            set(payload),
            {
                "schema_version", "mapping_mode", "source_kind", "source_sha256",
                "primary_member", "primary_member_sha256", "answer_member",
                "answer_member_sha256", "source_id", "chapter", "questions",
                "ignored_spans", "ignored_image_members",
            },
        )
        self.assertEqual(payload["schema_version"], "task9b-source-mapping-v1")
        self.assertEqual(payload["mapping_mode"], "explicit")
        for name in (
            "schema_version", "mapping_mode", "source_kind", "source_sha256",
            "primary_member", "primary_member_sha256", "source_id", "chapter",
        ):
            self.assertIs(type(payload[name]), str, name)
        self.assertRegex(payload["source_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(payload["primary_member_sha256"], r"^[0-9a-f]{64}$")
        self.assertIsNone(payload["answer_member"])
        self.assertIsNone(payload["answer_member_sha256"])
        self.assertIs(type(payload["questions"]), list)
        self.assertEqual(
            [question["semantic_order"] for question in payload["questions"]],
            [0, 1],
        )
        for question in payload["questions"]:
            self.assertEqual(
                set(question),
                {
                    "semantic_order", "proposed_question_id", "source_question_number",
                    "source_section", "question_span", "solution_spans",
                    "explanation_spans", "image_bindings",
                },
            )
            self.assertIs(type(question["semantic_order"]), int)
            for name in ("proposed_question_id", "source_question_number", "source_section"):
                self.assertIs(type(question[name]), str)
            span_values = [question["question_span"]]
            for name in ("solution_spans", "explanation_spans"):
                self.assertIs(type(question[name]), list)
                span_values.extend(question[name])
            for span in span_values:
                self.assertEqual(set(span), {"member", "start_byte", "end_byte"})
                self.assertIs(type(span["member"]), str)
                self.assertIs(type(span["start_byte"]), int)
                self.assertIs(type(span["end_byte"]), int)
            self.assertIs(type(question["image_bindings"]), list)
            for binding in question["image_bindings"]:
                self.assertEqual(
                    set(binding),
                    {
                        "semantic_order", "token_span", "raw_target", "selected_member",
                        "canonical_path", "role",
                    },
                )
                self.assertEqual(set(binding["token_span"]), {"member", "start_byte", "end_byte"})
                self.assertIs(type(binding["semantic_order"]), int)
                self.assertIs(type(binding["token_span"]["member"]), str)
                self.assertIs(type(binding["token_span"]["start_byte"]), int)
                self.assertIs(type(binding["token_span"]["end_byte"]), int)
                for name in ("raw_target", "selected_member", "canonical_path", "role"):
                    self.assertIs(type(binding[name]), str, name)
        self.assertIs(type(payload["ignored_spans"]), list)
        self.assertEqual(
            payload["ignored_spans"],
            sorted(
                payload["ignored_spans"],
                key=lambda span: (span["member"], span["start_byte"], span["end_byte"], span["reason"]),
            ),
        )
        self.assertTrue(
            all(set(span) == {"member", "start_byte", "end_byte", "reason"} for span in payload["ignored_spans"])
        )
        for span in payload["ignored_spans"]:
            self.assertIs(type(span["member"]), str)
            self.assertIs(type(span["start_byte"]), int)
            self.assertIs(type(span["end_byte"]), int)
            self.assertIs(type(span["reason"]), str)
        self.assertIs(type(payload["ignored_image_members"]), list)
        self.assertEqual(
            payload["ignored_image_members"],
            [{"member": "images/unused.jpg", "reason": "approved ignored resource"}],
        )
        for entry in payload["ignored_image_members"]:
            self.assertEqual(set(entry), {"member", "reason"})
            self.assertIs(type(entry["member"]), str)
            self.assertIs(type(entry["reason"]), str)

    def test_review_contains_required_identity_questions_and_no_runtime_root(self):
        require_api(self, "propose_mmd_source_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proposal = propose(self, root)
            review = proposal.review_path.read_text(encoding="utf-8")
            for expected in (SOURCE_ID, proposal.mapping_sha256, "EXPLICIT-002", "EXPLICIT-001", "first repeated label", "second repeated label"):
                self.assertIn(expected, review)
            self.assertNotIn(str(root), review)

    def test_review_contains_answer_digest_and_solution_explanation_previews(self):
        require_api(self, "propose_mmd_source_mapping")
        with tempfile.TemporaryDirectory() as directory:
            proposal = propose(self, Path(directory))
            review = proposal.review_path.read_text(encoding="utf-8")
            self.assertIn("Answer SHA-256: NONE", review)
            self.assertIn('Solution preview: "Solution evidence\\n2\\n"', review)
            self.assertIn('Explanation preview: "Explanation evidence\\nBecause $1+1=2$.\\n"', review)
            self.assertIn("Solution preview: MISSING", review)
            self.assertIn("Explanation preview: MISSING", review)

    def test_proposal_rejects_selection_image_surplus_before_package_stage(self):
        function = require_api(self, "propose_mmd_source_mapping")
        source_bytes = SOURCE_BYTES.replace(
            b"![](./images/diagram.jpg)",
            b"No source image token here",
        )
        manifest = valid_manifest(source_bytes)
        draft = valid_draft()
        for question in draft["questions"]:
            question["image_bindings"] = []
        draft["ignored_image_members"] = [
            {"member": "images/diagram.jpg", "reason": "resource not referenced by source"}
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path, source_path, draft_path, proposal_dir, config = make_case(
                root,
                source_bytes=source_bytes,
                manifest=manifest,
                draft=draft,
            )
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                function(selection_path, source_path, draft_path, proposal_dir, config)
            self.assertTrue(
                any(
                    issue.code == "image_binding_invalid"
                    and json.loads(issue.evidence).get("reason") == "selection_surplus"
                    for issue in caught.exception.issues
                )
            )
            self.assertFalse(proposal_dir.exists())

    def test_advisory_ambiguity_note_changes_review_only_not_mapping_identity(self):
        require_api(self, "propose_mmd_source_mapping")
        results = []
        for note in ("first human note", "second human note"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                draft = valid_draft()
                draft["questions"][0]["ambiguity_note"] = note
                proposal = propose(self, root, draft=draft)
                results.append(
                    (
                        proposal.mapping_path.read_bytes(),
                        proposal.mapping_sha256,
                        proposal.review_path.read_bytes(),
                    )
                )
        self.assertEqual(results[0][0], results[1][0])
        self.assertEqual(results[0][1], results[1][1])
        self.assertNotEqual(results[0][2], results[1][2])

    def test_proposal_rejects_selection_source_digest_mismatch_with_exact_m1_issue(self):
        function = require_api(self, "propose_mmd_source_mapping")
        manifest = valid_manifest()
        manifest["source_sha256"] = HEX_A
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path, source_path, draft_path, proposal_dir, config = make_case(
                root,
                manifest=manifest,
            )
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                function(selection_path, source_path, draft_path, proposal_dir, config)
            self.assertEqual(
                caught.exception.issues,
                (
                    blocking_issue(
                        "$.source_sha256",
                        {
                            "actual": sha256(SOURCE_BYTES),
                            "expected": HEX_A,
                            "reason": "source_digest_mismatch",
                        },
                    ),
                ),
            )
            self.assertFalse(proposal_dir.exists())

    def test_proposal_rejects_undeclared_span_member_with_exact_m3_issue(self):
        function = require_api(self, "propose_mmd_source_mapping")
        draft = valid_draft()
        draft["questions"][0]["question_line_span"]["member"] = "answer.mmd"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path, source_path, draft_path, proposal_dir, config = make_case(
                root,
                draft=draft,
            )
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                function(selection_path, source_path, draft_path, proposal_dir, config)
            self.assertEqual(
                caught.exception.issues,
                (
                    blocking_issue(
                        "$.questions[0].question_line_span",
                        {
                            "actual": {
                                "end_byte": None,
                                "member": "answer.mmd",
                                "start_byte": None,
                            },
                            "expected": "non_empty_in_bounds_half_open_span",
                            "reason": "invalid_span",
                        },
                        proposed_question_id="EXPLICIT-002",
                    ),
                ),
            )
            self.assertFalse(proposal_dir.exists())

    def test_proposal_rejects_out_of_range_line_span_with_exact_m3_issue(self):
        function = require_api(self, "propose_mmd_source_mapping")
        draft = valid_draft()
        draft["questions"][0]["question_line_span"] = line_span(99, 99)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path, source_path, draft_path, proposal_dir, config = make_case(
                root,
                draft=draft,
            )
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                function(selection_path, source_path, draft_path, proposal_dir, config)
            self.assertEqual(
                caught.exception.issues,
                (
                    blocking_issue(
                        "$.questions[0].question_line_span",
                        {
                            "actual": {
                                "end_byte": None,
                                "member": "source.mmd",
                                "start_byte": None,
                            },
                            "expected": "non_empty_in_bounds_half_open_span",
                            "reason": "invalid_span",
                        },
                        proposed_question_id="EXPLICIT-002",
                    ),
                ),
            )
            self.assertFalse(proposal_dir.exists())

    def test_proposal_rejects_semantic_owner_overlap_with_exact_m3_issue(self):
        function = require_api(self, "propose_mmd_source_mapping")
        draft = valid_draft()
        draft["questions"][1]["question_line_span"] = line_span(3, 4)
        draft["questions"][1]["image_bindings"] = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path, source_path, draft_path, proposal_dir, config = make_case(
                root,
                draft=draft,
            )
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                function(selection_path, source_path, draft_path, proposal_dir, config)
            earlier = {"member": "source.mmd", "start_byte": 18, "end_byte": 65}
            later = {"member": "source.mmd", "start_byte": 27, "end_byte": 65}
            self.assertEqual(
                caught.exception.issues,
                (
                    blocking_issue(
                        "$.questions[1].question_line_span",
                        {
                            "actual": later,
                            "expected": earlier,
                            "reason": "span_ownership_overlap",
                        },
                        proposed_question_id="EXPLICIT-001",
                        source_locator="source.mmd#bytes=27:65",
                    ),
                ),
            )
            self.assertFalse(proposal_dir.exists())

    def test_missing_draft_and_source_use_exact_input_exceptions(self):
        function = require_api(self, "propose_mmd_source_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path, source_path, draft_path, proposal_dir, config = make_case(root)
            draft_path.unlink()
            with self.assertRaises(InputMissingError):
                function(selection_path, source_path, draft_path, proposal_dir, config)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path, source_path, draft_path, proposal_dir, config = make_case(root)
            source_path.unlink()
            with self.assertRaises(InputMissingError):
                function(selection_path, source_path, draft_path, proposal_dir, config)

    def test_non_regular_draft_and_source_use_input_format_error(self):
        function = require_api(self, "propose_mmd_source_mapping")
        for target in ("draft", "source"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                selection_path, source_path, draft_path, proposal_dir, config = make_case(root)
                path = draft_path if target == "draft" else source_path
                path.unlink()
                path.mkdir()
                with self.subTest(target=target), self.assertRaises(InputFormatError) as caught:
                    function(selection_path, source_path, draft_path, proposal_dir, config)
                self.assertIs(type(caught.exception), InputFormatError)

    def test_unreadable_draft_and_source_use_exact_input_format_error(self):
        function = require_api(self, "propose_mmd_source_mapping")
        original_open = Path.open
        for target_name in ("draft", "source"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                selection_path, source_path, draft_path, proposal_dir, config = make_case(root)
                target = draft_path if target_name == "draft" else source_path
                attempts: list[Path] = []

                def guarded_open(path, *args, **kwargs):
                    if path == target:
                        attempts.append(path)
                        raise PermissionError("approved unreadable-input simulation")
                    return original_open(path, *args, **kwargs)

                with patch.object(Path, "open", new=guarded_open):
                    with self.subTest(target=target_name), self.assertRaises(InputFormatError) as caught:
                        function(selection_path, source_path, draft_path, proposal_dir, config)
                self.assertIs(type(caught.exception), InputFormatError)
                self.assertTrue(attempts)
                self.assertFalse(proposal_dir.exists())

    def test_destination_must_be_new_strict_staging_descendant(self):
        function = require_api(self, "propose_mmd_source_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path, source_path, draft_path, proposal_dir, config = make_case(root)
            with self.assertRaises(ConfigurationError):
                function(selection_path, source_path, draft_path, root / "outside", config)
            proposal_dir.mkdir(parents=True)
            with self.assertRaises(OutputConflictError):
                function(selection_path, source_path, draft_path, proposal_dir, config)

    def test_wrong_api_argument_types_raise_type_error(self):
        function = require_api(self, "propose_mmd_source_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = list(make_case(root))
            for index in range(5):
                values = list(args)
                values[index] = str(values[index])
                with self.subTest(index=index), self.assertRaises(TypeError):
                    function(*values)

    def test_proposal_reports_unmapped_and_unbound_warnings_without_publishing_package(self):
        function = require_api(self, "propose_mmd_source_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "source.mmd.zip"
            with zipfile.ZipFile(source_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                archive.writestr("source.mmd", SOURCE_BYTES)
                archive.writestr("images/diagram.jpg", IMAGE_BYTES)
                archive.writestr("images/unbound.jpg", b"unbound-image\n")
            manifest = valid_manifest()
            manifest["source_kind"] = "mmd_zip"
            manifest["source_sha256"] = sha256(source_path.read_bytes())
            draft = valid_draft()
            draft["ignored_line_spans"] = []
            selection_path = root / "selection.json"
            selection_path.write_bytes(canonical_json(manifest))
            draft_path = root / "draft.json"
            draft_path.write_bytes(canonical_json(draft))
            proposal = function(
                selection_path,
                source_path,
                draft_path,
                root / "data/staging/proposal",
                PipelineConfig(root),
            )
            review = proposal.review_path.read_text(encoding="utf-8")
            self.assertIn("UNMAPPED_NON_WHITESPACE source.mmd#bytes=", review)
            self.assertIn("UNBOUND_IMAGE images/unbound.jpg", review)
            self.assertNotIn("import_manifest.json", {path.name for path in proposal.proposal_root.iterdir()})

    def test_failed_proposal_leaves_no_partial_destination(self):
        function = require_api(self, "propose_mmd_source_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            draft = valid_draft()
            draft["questions"][0]["question_line_span"] = line_span(0, 4)
            selection_path, source_path, draft_path, proposal_dir, config = make_case(root, draft=draft)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                function(selection_path, source_path, draft_path, proposal_dir, config)
            issue = next(issue for issue in caught.exception.issues if issue.field == "$.questions[0].question_line_span")
            self.assertEqual(issue.code, "source_contract_mismatch")
            self.assertEqual(json.loads(issue.evidence)["reason"], "invalid_span")
            self.assertFalse(proposal_dir.exists())

    def test_invalid_bilingual_projection_blocks_proposal_at_m5(self):
        function = require_api(self, "propose_mmd_source_mapping")
        manifest = valid_manifest()
        manifest["selections"][0]["language_layout"] = "english_then_chinese"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path, source_path, draft_path, proposal_dir, config = make_case(root, manifest=manifest)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                function(selection_path, source_path, draft_path, proposal_dir, config)
            self.assertTrue(any(issue.code == "language_mapping_ambiguous" for issue in caught.exception.issues))
            self.assertFalse(proposal_dir.exists())


class MappingValidationTests(unittest.TestCase):
    def test_m0_missing_nested_keys_emit_only_the_primary_missing_fact(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        mutations = (
            lambda value: value["questions"][0].pop("question_span"),
            lambda value: value["questions"][0]["image_bindings"][0].pop("token_span"),
            lambda value: value["ignored_spans"][0].pop("member"),
        )
        expected_paths = (
            "$.questions[0].question_span",
            "$.questions[0].image_bindings[0].token_span",
            "$.ignored_spans[0].member",
        )
        for mutation, expected_path in zip(mutations, expected_paths):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.subTest(expected_path=expected_path), self.assertRaises(
                    MmdAdapterBlockedError
                ) as caught:
                    mutate_mapping(self, root, mutation)()
                self.assertEqual(len(caught.exception.issues), 1)
                issue = caught.exception.issues[0]
                self.assertEqual(issue.field, expected_path)
                self.assertEqual(
                    json.loads(issue.evidence),
                    {"actual": "missing", "expected": "present", "reason": "missing_key"},
                )

    def test_bound_and_ignored_image_is_source_free_for_draft_and_mapping(self):
        function = require_api(self, "propose_mmd_source_mapping")
        draft = valid_draft()
        draft["ignored_image_members"] = [
            {"member": "images/diagram.jpg", "reason": "contradicts binding"}
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path, source_path, draft_path, proposal_dir, config = make_case(
                root,
                draft=draft,
            )
            source_path.unlink()
            with self.subTest(carrier="draft"):
                try:
                    function(selection_path, source_path, draft_path, proposal_dir, config)
                except MmdAdapterBlockedError as caught:
                    self.assertTrue(
                        any(
                            issue.code == "source_contract_mismatch"
                            and issue.field == "$.ignored_image_members[0].member"
                            and json.loads(issue.evidence).get("reason")
                            == "cross_field_violation"
                            for issue in caught.issues
                        )
                    )
                except InputMissingError as caught:
                    self.fail(f"draft source-free closure read the source: {caught}")
                else:
                    self.fail("draft bound-and-ignored image was accepted")

        def bind_and_ignore(value):
            value["ignored_image_members"] = [
                {"member": "images/diagram.jpg", "reason": "contradicts binding"}
            ]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invoke = mutate_mapping(self, root, bind_and_ignore)
            (root / "source.mmd").unlink()
            with self.subTest(carrier="mapping"):
                try:
                    invoke()
                except MmdAdapterBlockedError as caught:
                    self.assertTrue(
                        any(
                            issue.code == "source_contract_mismatch"
                            and issue.field == "$.ignored_image_members[0].member"
                            and json.loads(issue.evidence).get("reason")
                            == "cross_field_violation"
                            for issue in caught.issues
                        )
                    )
                except InputMissingError as caught:
                    self.fail(f"mapping source-free closure read the source: {caught}")
                else:
                    self.fail("mapping bound-and-ignored image was accepted")

    def test_selected_image_member_must_equal_the_token_canonical_path(self):
        function = require_api(self, "propose_mmd_source_mapping")
        manifest = valid_manifest()
        draft = valid_draft()
        manifest["selections"][0]["expected_image_members"] = ["images/other.jpg"]
        draft["questions"][0]["image_bindings"][0]["selected_member"] = "images/other.jpg"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path, source_path, draft_path, proposal_dir, config = make_case(
                root,
                manifest=manifest,
                draft=draft,
            )
            (root / "images/other.jpg").write_bytes(b"other-image\n")
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                function(selection_path, source_path, draft_path, proposal_dir, config)
            issue = next(
                issue
                for issue in caught.exception.issues
                if issue.code == "image_binding_invalid"
                and json.loads(issue.evidence).get("reason") == "selection_conflict"
            )
            self.assertEqual(issue.proposed_question_id, "EXPLICIT-002")
            self.assertFalse(proposal_dir.exists())

    def test_mode_b_cross_question_casefold_target_collision_blocks_at_m4(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        first = "./images/A.jpg"
        second = "./images/a.jpg"
        source_bytes = SOURCE_BYTES.replace(
            b"./images/diagram.jpg", first.encode("utf-8"), 1
        ).replace(b"./images/diagram.jpg", second.encode("utf-8"), 1)
        manifest = valid_manifest(source_bytes)
        draft = valid_draft()
        for index, raw_target in enumerate((first, second)):
            manifest["selections"][index]["expected_image_members"] = [raw_target[2:]]
            binding = draft["questions"][index]["image_bindings"][0]
            binding["raw_target"] = raw_target
            binding["selected_member"] = None
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                write_mapping_case(
                    self,
                    root,
                    source_bytes=source_bytes,
                    manifest=manifest,
                    draft=draft,
                )()
            self.assertEqual(len(caught.exception.issues), 1)
            issue = caught.exception.issues[0]
            self.assertEqual(issue.code, "archive_member_unsafe")
            self.assertEqual(
                json.loads(issue.evidence).get("reason"),
                "image_target_casefold_collision",
            )
            self.assertFalse((root / "data/staging/package").exists())

    def test_mode_b_cross_question_nfc_target_collision_blocks_at_m4(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        first = "./images/cafe\u0301.jpg"
        second = "./images/caf\u00e9.jpg"
        source_bytes = SOURCE_BYTES.replace(
            b"./images/diagram.jpg", first.encode("utf-8"), 1
        ).replace(b"./images/diagram.jpg", second.encode("utf-8"), 1)
        manifest = valid_manifest(source_bytes)
        draft = valid_draft()
        for index, raw_target in enumerate((first, second)):
            canonical = raw_target[2:]
            if index == 0:
                canonical = "images/caf\u00e9.jpg"
            manifest["selections"][index]["expected_image_members"] = [canonical]
            binding = draft["questions"][index]["image_bindings"][0]
            binding["raw_target"] = raw_target
            binding["selected_member"] = None
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                write_mapping_case(
                    self,
                    root,
                    source_bytes=source_bytes,
                    manifest=manifest,
                    draft=draft,
                    mutation=lambda value: value["questions"][0][
                        "image_bindings"
                    ][0].__setitem__("canonical_path", "images/caf\u00e9.jpg"),
                )()
            self.assertEqual(len(caught.exception.issues), 1)
            issue = caught.exception.issues[0]
            self.assertEqual(issue.code, "archive_member_unsafe")
            self.assertEqual(
                json.loads(issue.evidence).get("reason"),
                "image_target_nfc_collision",
            )

    def test_mode_b_target_to_safe_inventory_casefold_collision_blocks_at_m4(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        raw_target = "./images/A.jpg"
        source_bytes = SOURCE_BYTES.replace(
            b"./images/diagram.jpg", raw_target.encode("utf-8"), 1
        )
        manifest = valid_manifest(source_bytes)
        draft = valid_draft()
        manifest["selections"][0]["expected_image_members"] = ["images/a.jpg"]
        binding = draft["questions"][0]["image_bindings"][0]
        binding["raw_target"] = raw_target
        binding["selected_member"] = "images/a.jpg"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invoke = write_mapping_case(
                self,
                root,
                source_bytes=source_bytes,
                manifest=manifest,
                draft=draft,
            )
            (root / "images/a.jpg").write_bytes(b"lowercase-image\n")
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                invoke()
            self.assertEqual(len(caught.exception.issues), 1)
            self.assertEqual(
                json.loads(caught.exception.issues[0].evidence).get("reason"),
                "image_target_casefold_collision",
            )

    def test_non_character_boundary_span_is_a_structured_m4_blocker(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        source_bytes = "\u00e9 question\n".encode("utf-8")
        manifest = valid_manifest(source_bytes)
        manifest["expected_candidate_count"] = 1
        manifest["selections"] = [
            selection("EXPLICIT-002", "A", answer_mapping="missing_from_source")
        ]
        manifest["selections"][0]["expected_image_members"] = []
        draft = valid_draft()
        draft["questions"] = [
            {
                "semantic_order": 0,
                "proposed_question_id": "EXPLICIT-002",
                "source_question_number": "A",
                "source_section": "Worksheet",
                "question_line_span": line_span(1, 1),
                "solution_line_spans": [],
                "explanation_line_spans": [],
                "image_bindings": [],
                "ambiguity_note": "invalid UTF-8 byte boundary",
            }
        ]
        draft["ignored_line_spans"] = []
        draft["ignored_image_members"] = []

        def split_scalar(value):
            value["questions"][0]["question_span"]["start_byte"] = 1

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            try:
                write_mapping_case(
                    self,
                    root,
                    source_bytes=source_bytes,
                    manifest=manifest,
                    draft=draft,
                    mutation=split_scalar,
                )()
            except MmdAdapterBlockedError as caught:
                issues = caught.issues
            except UnicodeDecodeError as caught:
                self.fail(f"non-character boundary leaked UnicodeDecodeError: {caught}")
            else:
                self.fail("non-character boundary span was accepted")
            issue = next(
                issue
                for issue in issues
                if issue.code == "mmd_parse_failed"
                and json.loads(issue.evidence).get("reason") == "invalid_utf8"
            )
            self.assertEqual(issue.field, "primary_member")

    def test_standalone_subpart_cannot_be_published_as_a_complete_question(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        source_bytes = (
            b"Complete stem\n"
            b"\\begin{itemize}\n"
            b"\\item[(a)] Part A\n"
            b"\\item[(b)] Part B\n"
            b"\\end{itemize}\n"
        )
        manifest = valid_manifest(source_bytes)
        manifest["expected_candidate_count"] = 1
        manifest["selections"] = [
            selection("EXPLICIT-002", "A", answer_mapping="missing_from_source")
        ]
        manifest["selections"][0]["expected_image_members"] = []
        draft = valid_draft()
        draft["questions"] = [
            {
                "semantic_order": 0,
                "proposed_question_id": "EXPLICIT-002",
                "source_question_number": "A",
                "source_section": "Worksheet",
                "question_line_span": line_span(3, 3),
                "solution_line_spans": [],
                "explanation_line_spans": [],
                "image_bindings": [],
                "ambiguity_note": "standalone subpart is forbidden",
            }
        ]
        draft["ignored_line_spans"] = [
            {**line_span(1, 2), "reason": "excluded stem and open wrapper"},
            {**line_span(4, 5), "reason": "excluded sibling and close wrapper"},
        ]
        draft["ignored_image_members"] = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                write_mapping_case(
                    self,
                    root,
                    source_bytes=source_bytes,
                    manifest=manifest,
                    draft=draft,
                )()
            self.assertTrue(
                any(
                    issue.code == "mmd_parse_failed"
                    and json.loads(issue.evidence).get("reason") == "unsupported_grammar"
                    for issue in caught.exception.issues
                )
            )

    def test_stem_plus_one_subpart_cannot_publish_when_sibling_is_ignored(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        source_bytes = (
            b"Complete stem\n"
            b"\\item[(a)] Part A\n"
            b"\\item[(b)] Part B\n"
        )
        manifest = valid_manifest(source_bytes)
        manifest["expected_candidate_count"] = 1
        manifest["selections"] = [
            selection("EXPLICIT-002", "A", answer_mapping="missing_from_source")
        ]
        manifest["selections"][0]["expected_image_members"] = []
        draft = valid_draft()
        draft["questions"] = [
            {
                "semantic_order": 0,
                "proposed_question_id": "EXPLICIT-002",
                "source_question_number": "A",
                "source_section": "Worksheet",
                "question_line_span": line_span(1, 2),
                "solution_line_spans": [],
                "explanation_line_spans": [],
                "image_bindings": [],
                "ambiguity_note": "sibling subpart is outside the proposed question",
            }
        ]
        draft["ignored_line_spans"] = [
            {**line_span(3, 3), "reason": "invalid attempted sibling omission"}
        ]
        draft["ignored_image_members"] = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                write_mapping_case(
                    self,
                    root,
                    source_bytes=source_bytes,
                    manifest=manifest,
                    draft=draft,
                )()
            self.assertTrue(
                any(
                    issue.code == "mmd_parse_failed"
                    and json.loads(issue.evidence).get("reason")
                    == "unsupported_grammar"
                    for issue in caught.exception.issues
                )
            )
            self.assertFalse((root / "data/staging/package").exists())

    def test_root_level_safe_image_is_not_mode_b_bindable_inventory(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, invoke = write_image_archive_case(
                self,
                root,
                extra_members=(("orphan.jpg", b"root-level-resource\n"),),
            )
            try:
                result = invoke()
            except MmdAdapterBlockedError as caught:
                self.fail(
                    "root-level safe image incorrectly entered Mode B image inventory: "
                    f"{caught.issues}"
                )
            self.assertTrue(result.package_root.is_dir())
            self.assertFalse((result.package_root / "orphan.jpg").exists())

    def test_mode_a_preserves_nfc_group_priority_over_overlapping_casefold_group(self):
        module = importlib.import_module("joy_m2.ingest.mmd_parser")
        source_bytes = (
            "例題 1\n"
            "English. 中文。\n"
            "![](./images/cafe\u0301.jpg)\n"
            "![](./images/café.jpg)\n"
            "![](./images/CAFE\u0301.jpg)\n"
        ).encode("utf-8")
        primary = module._SourceMember(
            "source/primary.mmd",
            sha256(source_bytes),
            source_bytes,
        )
        with self.assertRaises(MmdAdapterBlockedError) as caught:
            module._parse_source_document(primary, None)
        self.assertEqual(
            [json.loads(issue.evidence)["reason"] for issue in caught.exception.issues],
            ["image_target_nfc_collision", "image_target_canonicalization"],
        )

    def test_mode_a_preserves_primary_before_answer_for_collision_locator(self):
        module = importlib.import_module("joy_m2.ingest.mmd_parser")
        primary_bytes = (
            "例題 1\nEnglish. 中文。\n![](./images/A.jpg)\n"
        ).encode("utf-8")
        answer_bytes = (
            "例題 1\n題解：\n![](./images/a.jpg)\n"
        ).encode("utf-8")
        primary = module._SourceMember(
            "z-primary.mmd",
            sha256(primary_bytes),
            primary_bytes,
        )
        answer = module._SourceMember(
            "a-answer.mmd",
            sha256(answer_bytes),
            answer_bytes,
        )
        with self.assertRaises(MmdAdapterBlockedError) as caught:
            module._parse_source_document(primary, answer)
        self.assertEqual(len(caught.exception.issues), 1)
        issue = caught.exception.issues[0]
        token = b"![](./images/A.jpg)"
        start = primary_bytes.index(token)
        self.assertEqual(
            issue.source_locator,
            f"z-primary.mmd#bytes={start}:{start + len(token)}",
        )
        self.assertEqual(
            json.loads(issue.evidence)["reason"],
            "image_target_casefold_collision",
        )

    def test_safe_os_metadata_is_not_an_image_inventory_candidate(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, invoke = write_image_archive_case(
                self,
                root,
                extra_members=(("__MACOSX/images/._ghost.jpg", b"metadata\n"),),
            )
            try:
                result = invoke()
            except MmdAdapterBlockedError as caught:
                self.fail(f"safe OS metadata entered image inventory: {caught.issues}")
            self.assertTrue(result.package_root.is_dir())
            self.assertFalse(
                (result.package_root / "__MACOSX/images/._ghost.jpg").exists()
            )

    def test_enrichment_uses_the_exact_four_presence_fields(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        complete_manifest = valid_manifest()
        for selected in complete_manifest["selections"]:
            selected["language_layout"] = "source_chinese"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = write_mapping_case(
                self,
                root,
                manifest=complete_manifest,
            )()
            candidates = json.loads(
                (result.package_root / "records/candidates.json").read_bytes()
            )
            self.assertEqual(candidates[0]["enrichment_status"], "complete")
            self.assertEqual(candidates[1]["enrichment_status"], "incomplete")

        missing_cases = (
            ("translation", lambda selected: selected.__setitem__("language_layout", "source_english")),
            (
                "tags",
                lambda selected: (
                    selected.__setitem__("tags", []),
                    selected.__setitem__("tag_status", "missing"),
                ),
            ),
            (
                "difficulty",
                lambda selected: (
                    selected.__setitem__("difficulty_level", None),
                    selected.__setitem__("difficulty_status", "missing"),
                ),
            ),
        )
        for name, mutation in missing_cases:
            manifest = valid_manifest()
            for selected in manifest["selections"]:
                selected["language_layout"] = "source_chinese"
            mutation(manifest["selections"][0])
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                result = write_mapping_case(self, root, manifest=manifest)()
                candidates = json.loads(
                    (result.package_root / "records/candidates.json").read_bytes()
                )
            with self.subTest(missing=name):
                self.assertEqual(candidates[0]["enrichment_status"], "incomplete")

    def test_question_review_preview_preserves_newline_characters(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            proposal = propose(self, root)
            review = proposal.review_path.read_text(encoding="utf-8")
        self.assertIn(
            'Question preview: "Repeat A\\nFind $x+1$.\\n![](./images/diagram.jpg)\\n"',
            review,
        )

    def test_canonical_mapping_bytes_are_strict_utf8_no_bom_duplicate_aware_and_object_only(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        invalid = (
            b"\xff",
            b"\xef\xbb\xbf{}",
            b"{",
            b"[]",
            b'{"schema_version":1,"schema_version":2}',
        )
        for index, raw in enumerate(invalid):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.subTest(index=index), self.assertRaises(MmdAdapterBlockedError) as caught:
                    invoke_mapping_bytes(self, root, raw)()
                self.assertTrue(all(issue.code == "source_contract_mismatch" for issue in caught.exception.issues))
                self.assertFalse((root / "data/staging/package").exists())

    def test_canonical_mapping_requires_exact_top_and_nested_schemas(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        mutations = (
            lambda value: value.pop("chapter"),
            lambda value: value.__setitem__("extra", 1),
            lambda value: value["questions"][0].pop("source_section"),
            lambda value: value["questions"][0].__setitem__("extra", 1),
            lambda value: value["questions"][0]["question_span"].pop("member"),
            lambda value: value["questions"][0]["question_span"].__setitem__("extra", 1),
            lambda value: value["questions"][0]["image_bindings"][0].pop("role"),
            lambda value: value["questions"][0]["image_bindings"][0].__setitem__("extra", 1),
            lambda value: value["ignored_spans"][0].pop("reason"),
        )
        for index, mutation in enumerate(mutations):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.subTest(index=index), self.assertRaises(MmdAdapterBlockedError):
                    mutate_mapping(self, root, mutation)()

    def test_canonical_mapping_rejects_bool_as_int_wrong_arrays_and_noncanonical_bytes(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        mutations = (
            lambda value: value["questions"][0].__setitem__("semantic_order", True),
            lambda value: value["questions"][0]["question_span"].__setitem__("start_byte", True),
            lambda value: value.__setitem__("questions", {}),
            lambda value: value["questions"][0].__setitem__("solution_spans", {}),
            lambda value: value["questions"][0].__setitem__("image_bindings", {}),
            lambda value: value.__setitem__("ignored_spans", {}),
        )
        for index, mutation in enumerate(mutations):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.subTest(index=index), self.assertRaises(MmdAdapterBlockedError):
                    mutate_mapping(self, root, mutation)()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            payload = canonical_mapping()
            noncanonical = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")
            with self.assertRaises(MmdAdapterBlockedError):
                invoke_mapping_bytes(self, root, noncanonical)()

    def test_canonical_mapping_image_scalars_are_closed_at_m0(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        cases = (
            (
                lambda value: value["questions"][0]["image_bindings"][0].__setitem__("raw_target", ""),
                "$.questions[0].image_bindings[0].raw_target",
                "non_empty_string",
            ),
            (
                lambda value: value["questions"][0]["image_bindings"][0].__setitem__("canonical_path", ""),
                "$.questions[0].image_bindings[0].canonical_path",
                "non_empty_string",
            ),
            (
                lambda value: value["questions"][0]["image_bindings"][0].__setitem__("canonical_path", "images/diagram.gif"),
                "$.questions[0].image_bindings[0].canonical_path",
                "canonical_nfc_posix_images_member",
            ),
        )
        for mutation, field, expected in cases:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.subTest(field=field, expected=expected), self.assertRaises(MmdAdapterBlockedError) as caught:
                    mutate_mapping(self, root, mutation)()
                issues = [issue for issue in caught.exception.issues if issue.field == field]
                self.assertEqual(len(issues), 1)
                self.assertEqual(
                    json.loads(issues[0].evidence)["reason"],
                    "invalid_value",
                )
                self.assertEqual(json.loads(issues[0].evidence)["expected"], expected)

    def test_ignored_span_rejects_empty_reason(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                mutate_mapping(
                    self,
                    root,
                    lambda value: value["ignored_spans"][0].__setitem__("reason", ""),
                )()
            self.assertTrue(
                any(issue.field == "$.ignored_spans[0].reason" for issue in caught.exception.issues)
            )
            self.assertFalse((root / "data/staging/package").exists())

    def test_ignored_span_mixed_wrong_types_return_structured_blocker(self):
        require_api(self, "adapt_mmd_package_from_mapping")

        def mixed_wrong_types(value):
            value["ignored_spans"].append(
                {
                    "member": 7,
                    "start_byte": "bad",
                    "end_byte": False,
                    "reason": "invalid typed entry",
                }
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            try:
                mutate_mapping(self, root, mixed_wrong_types)()
            except MmdAdapterBlockedError as caught:
                self.assertTrue(caught.issues)
                self.assertTrue(
                    any(issue.field.startswith("$.ignored_spans") for issue in caught.issues)
                )
            except Exception as caught:
                self.fail(
                    f"mixed wrong types leaked {type(caught).__name__} instead of a structured blocker"
                )
            else:
                self.fail("mixed wrong types were accepted")
            self.assertFalse((root / "data/staging/package").exists())

    def test_canonical_mapping_rejects_nonfinite_json_constants_exactly(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        for token in (b"NaN", b"Infinity", b"-Infinity"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                raw = canonical_json(canonical_mapping()).replace(
                    b'"semantic_order":0',
                    b'"semantic_order":' + token,
                    1,
                )
                with self.subTest(token=token), self.assertRaises(MmdAdapterBlockedError) as caught:
                    invoke_mapping_bytes(self, root, raw)()
                self.assertEqual(len(caught.exception.issues), 1)
                issue = caught.exception.issues[0]
                self.assertEqual(issue.code, "source_contract_mismatch")
                self.assertEqual(issue.field, "$")
                self.assertEqual(
                    json.loads(issue.evidence),
                    {
                        "actual": "invalid_json_syntax",
                        "expected": "json_object",
                        "reason": "invalid_json",
                    },
                )

    def test_canonical_sequence_pair_and_duplicate_span_rules_are_enforced(self):
        require_api(self, "adapt_mmd_package_from_mapping")

        def duplicate_solution(value):
            value["questions"][0]["solution_spans"].append(
                dict(value["questions"][0]["solution_spans"][0])
            )

        def duplicate_explanation(value):
            value["questions"][0]["explanation_spans"].append(
                dict(value["questions"][0]["explanation_spans"][0])
            )

        canonical_ignored_spans = canonical_mapping()["ignored_spans"]
        reversed_ignored_spans = list(reversed(canonical_ignored_spans))
        cases = (
            (
                lambda value: value["questions"][1].__setitem__("semantic_order", 3),
                blocking_issue(
                    "$.questions[1].semantic_order",
                    {"actual": 3, "expected": 1, "reason": "cross_field_violation"},
                ),
            ),
            (
                lambda value: value["questions"][0]["image_bindings"][0].__setitem__("semantic_order", 2),
                blocking_issue(
                    "$.questions[0].image_bindings[0].semantic_order",
                    {"actual": 2, "expected": 0, "reason": "cross_field_violation"},
                ),
            ),
            (
                duplicate_solution,
                blocking_issue(
                    "$.questions[0].solution_spans",
                    {"actual": 2, "expected": "unique_items", "reason": "cross_field_violation"},
                ),
            ),
            (
                duplicate_explanation,
                blocking_issue(
                    "$.questions[0].explanation_spans",
                    {"actual": 2, "expected": "unique_items", "reason": "cross_field_violation"},
                ),
            ),
            (
                lambda value: value.__setitem__("ignored_spans", reversed_ignored_spans),
                blocking_issue(
                    "$.ignored_spans",
                    {
                        "actual": sha256(canonical_json(reversed_ignored_spans)),
                        "expected": sha256(canonical_json(canonical_ignored_spans)),
                        "reason": "cross_field_violation",
                    },
                ),
            ),
            (
                lambda value: value.update(answer_member="answer.mmd", answer_member_sha256=None),
                blocking_issue(
                    "$.answer_member_sha256",
                    {
                        "actual": "null",
                        "expected": "lowercase_hex_64_when_answer_member_present",
                        "reason": "cross_field_violation",
                    },
                ),
            ),
            (
                lambda value: value.update(answer_member=None, answer_member_sha256=HEX_A),
                blocking_issue(
                    "$.answer_member_sha256",
                    {
                        "actual": "present",
                        "expected": "null_when_answer_member_null",
                        "reason": "cross_field_violation",
                    },
                ),
            ),
        )
        for mutation, expected_issue in cases:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.subTest(field=expected_issue.field), self.assertRaises(MmdAdapterBlockedError) as caught:
                    mutate_mapping(self, root, mutation)()
                self.assertEqual(caught.exception.issues, (expected_issue,))

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            canonical_ignored_images = [
                {"member": "images/unused-a.jpg", "reason": "approved unused resource A"},
                {"member": "images/unused-b.jpg", "reason": "approved unused resource B"},
            ]
            reversed_ignored_images = list(reversed(canonical_ignored_images))
            _, invoke = write_image_archive_case(
                self,
                root,
                mapping_mutation=lambda value: value.__setitem__(
                    "ignored_image_members",
                    reversed_ignored_images,
                ),
            )
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                invoke()
            self.assertEqual(
                caught.exception.issues,
                (
                    blocking_issue(
                        "$.ignored_image_members",
                        {
                            "actual": sha256(canonical_json(reversed_ignored_images)),
                            "expected": sha256(canonical_json(canonical_ignored_images)),
                            "reason": "cross_field_violation",
                        },
                    ),
                ),
            )

    def test_m0_emits_every_independent_schema_issue_with_exact_envelopes(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        payload = canonical_mapping()
        payload["schema_version"] = "wrong-schema"
        payload["extra"] = 1
        payload.pop("chapter")
        payload["questions"][0]["semantic_order"] = True
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                invoke_mapping_bytes(self, root, canonical_json(payload))()
        expected = stable_issues(
            blocking_issue(
                "$.schema_version",
                {
                    "actual": "wrong-schema",
                    "expected": "task9b-source-mapping-v1",
                    "reason": "invalid_value",
                },
            ),
            blocking_issue(
                "$.extra",
                {"actual": "present", "expected": "absent", "reason": "extra_key"},
            ),
            blocking_issue(
                "$.chapter",
                {"actual": "missing", "expected": "present", "reason": "missing_key"},
            ),
            blocking_issue(
                "$.questions[0].semantic_order",
                {"actual": "boolean", "expected": "integer", "reason": "wrong_type"},
            ),
        )
        self.assertEqual(caught.exception.issues, expected)

    def test_missing_and_nonregular_mapping_use_exact_input_exceptions(self):
        function = require_api(self, "adapt_mmd_package_from_mapping")
        approval_type = require_api(self, "SourceMappingApproval")
        approval = approval_type(
            SOURCE_ID,
            HEX_A,
            f"USER APPROVED SOURCE MAPPING {SOURCE_ID} {HEX_A}",
        )
        for state in ("missing", "directory"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                selection_path, source_path, _draft_path, _proposal_dir, config = make_case(root)
                mapping_path = root / "mapping.json"
                if state == "directory":
                    mapping_path.mkdir()
                expected = InputMissingError if state == "missing" else InputFormatError
                with self.subTest(state=state), self.assertRaises(expected) as caught:
                    function(selection_path, mapping_path, approval, source_path, root / "data/staging/package", config)
                self.assertIs(type(caught.exception), expected)

    def test_unreadable_mapping_uses_exact_input_format_error(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        original_open = Path.open
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invoke = write_mapping_case(self, root)
            mapping_path = root / "source_mapping.json"
            attempts: list[Path] = []

            def guarded_open(path, *args, **kwargs):
                if path == mapping_path:
                    attempts.append(path)
                    raise PermissionError("approved unreadable-mapping simulation")
                return original_open(path, *args, **kwargs)

            with patch.object(Path, "open", new=guarded_open):
                with self.assertRaises(InputFormatError) as caught:
                    invoke()
            self.assertIs(type(caught.exception), InputFormatError)
            self.assertTrue(attempts)
            self.assertFalse((root / "data/staging/package").exists())

    def test_unreadable_source_uses_exact_input_format_error(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        original_open = Path.open
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invoke = write_mapping_case(self, root)
            source_path = root / "source.mmd"
            attempts: list[Path] = []

            def guarded_open(path, *args, **kwargs):
                if path == source_path:
                    attempts.append(path)
                    raise PermissionError("approved unreadable-source simulation")
                return original_open(path, *args, **kwargs)

            with patch.object(Path, "open", new=guarded_open):
                with self.assertRaises(InputFormatError) as caught:
                    invoke()
            self.assertIs(type(caught.exception), InputFormatError)
            self.assertTrue(attempts)
            self.assertFalse((root / "data/staging/package").exists())

    def test_nonregular_source_uses_exact_input_format_error(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invoke = write_mapping_case(self, root)
            source_path = root / "source.mmd"
            source_path.unlink()
            source_path.mkdir()
            with self.assertRaises(InputFormatError) as caught:
                invoke()
            self.assertIs(type(caught.exception), InputFormatError)
            self.assertFalse((root / "data/staging/package").exists())

    def test_preexisting_output_is_rejected_without_mutation(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invoke = write_mapping_case(self, root)
            output = root / "data/staging/package"
            output.mkdir(parents=True)
            sentinel = output / "sentinel.txt"
            sentinel.write_bytes(b"preserve-existing-output\n")
            with self.assertRaises(OutputConflictError) as caught:
                invoke()
            self.assertIs(type(caught.exception), OutputConflictError)
            self.assertEqual(sentinel.read_bytes(), b"preserve-existing-output\n")

    def test_approved_mapping_blocker_leaves_no_partial_destination(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invoke = mutate_mapping(
                self,
                root,
                lambda value: value.__setitem__("source_sha256", HEX_A),
            )
            output = root / "data/staging/package"
            with self.assertRaises(MmdAdapterBlockedError):
                invoke()
            self.assertFalse(output.exists())

    def test_approved_adapter_argument_output_and_source_preconditions_are_exact(self):
        function = require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invoke = write_mapping_case(self, root)
            mapping_path = root / "source_mapping.json"
            mapping_bytes = mapping_path.read_bytes()
            digest = sha256(mapping_bytes)
            approval_type = require_api(self, "SourceMappingApproval")
            approval = approval_type(SOURCE_ID, digest, f"USER APPROVED SOURCE MAPPING {SOURCE_ID} {digest}")
            args = [root / "selection.json", mapping_path, approval, root / "source.mmd", root / "data/staging/package", PipelineConfig(root)]
            for index in range(6):
                values = list(args)
                values[index] = object()
                with self.subTest(index=index), self.assertRaises(TypeError):
                    function(*values)
            with self.assertRaises(ConfigurationError):
                function(*args[:4], root / "outside", args[5])
            args[3].unlink()
            with self.assertRaises(InputMissingError):
                function(*args)
            self.assertFalse((root / "data/staging/package").exists())

    def test_selection_manifest_cr_or_lf_source_id_blocks_approved_adapter_before_source_access(self):
        function = require_api(self, "adapt_mmd_package_from_mapping")
        approval_type = require_api(self, "SourceMappingApproval")
        for source_id in ("BAD\rID", "BAD\nID"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                manifest = valid_manifest()
                manifest["source_id"] = source_id
                selection_path, source_path, _draft_path, _proposal_dir, config = make_case(
                    root,
                    manifest=manifest,
                )
                mapping_path = root / "source_mapping.json"
                mapping_bytes = canonical_json(canonical_mapping())
                mapping_path.write_bytes(mapping_bytes)
                mapping_digest = sha256(mapping_bytes)
                approval = approval_type(
                    SOURCE_ID,
                    mapping_digest,
                    f"USER APPROVED SOURCE MAPPING {SOURCE_ID} {mapping_digest}",
                )
                output = root / "data/staging/package"
                source_path.unlink()
                with self.subTest(source_id=repr(source_id)), self.assertRaises(MmdAdapterBlockedError) as caught:
                    function(
                        selection_path,
                        mapping_path,
                        approval,
                        source_path,
                        output,
                        config,
                    )
                self.assertEqual(
                    caught.exception.issues,
                    (
                        blocking_issue(
                            "$.source_id",
                            {
                                "actual": sha256(source_id.encode("utf-8")),
                                "expected": "single_line_non_empty",
                                "reason": "invalid_value",
                            },
                        ),
                    ),
                )
                self.assertFalse(output.exists())

    def test_exact_approval_is_required_and_binds_source_and_digest(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        cases = (("OTHER", None), (None, HEX_A))
        for index, (source_id, digest) in enumerate(cases):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                invoke = write_mapping_case(
                    self,
                    root,
                    approval_source_id=source_id,
                    approval_digest=digest,
                )
                with self.subTest(index=index):
                    with self.assertRaises(MmdAdapterBlockedError) as caught:
                        invoke(f"out-{index}")
                    expected_field = "approval.source_id" if source_id is not None else "approval.mapping_sha256"
                    expected_reason = "approval_source_id_mismatch" if source_id is not None else "approval_mapping_digest_mismatch"
                    issue = caught.exception.issues[0]
                    self.assertEqual(issue.field, expected_field)
                    self.assertEqual(json.loads(issue.evidence)["reason"], expected_reason)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            function = require_api(self, "adapt_mmd_package_from_mapping")
            make_case(root)
            mapping_path = root / "source_mapping.json"
            mapping_path.write_bytes(canonical_json(canonical_mapping()))
            with self.assertRaises(TypeError):
                function(root / "selection.json", mapping_path, None, root / "source.mmd", root / "data/staging/package", PipelineConfig(root))

    def test_mapping_source_id_line_break_and_member_paths_are_rejected_at_m0(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        cases = (
            (lambda value: value.__setitem__("source_id", "BAD\nID"), "$.source_id"),
            (lambda value: value.__setitem__("primary_member", "../source.mmd"), "$.primary_member"),
            (
                lambda value: value["questions"][0]["question_span"].__setitem__("member", "/source.mmd"),
                "$.questions[0].question_span.member",
            ),
            (
                lambda value: value["ignored_image_members"].append({"member": "../image.jpg", "reason": "bad"}),
                "$.ignored_image_members[0].member",
            ),
        )
        for index, (mutation, field) in enumerate(cases):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.subTest(index=index), self.assertRaises(MmdAdapterBlockedError) as caught:
                    mutate_mapping(self, root, mutation)()
                issue = next(issue for issue in caught.exception.issues if issue.field == field)
                self.assertEqual(issue.code, "source_contract_mismatch")
                self.assertEqual(json.loads(issue.evidence)["reason"], "invalid_value")

    def test_wrong_outer_and_member_digests_are_rejected(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        mutations = (
            lambda value: value.__setitem__("source_sha256", HEX_A),
            lambda value: value.__setitem__("primary_member_sha256", HEX_B),
        )
        for index, mutation in enumerate(mutations):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                invoke = mutate_mapping(self, root, mutation)
                with self.subTest(index=index), self.assertRaises(MmdAdapterBlockedError) as caught:
                    invoke()
                issue = caught.exception.issues[0]
                self.assertEqual(issue.code, "source_contract_mismatch")
                self.assertIn(issue.field, {"$.source_sha256", "$.primary_member_sha256"})
                self.assertIn(json.loads(issue.evidence)["reason"], {"mapping_source_digest_mismatch", "mapping_primary_digest_mismatch"})

    def test_wrong_outer_zip_digest_has_its_exact_m3_blocker(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            actual_archive_sha, invoke = write_image_archive_case(
                self,
                root,
                mapping_mutation=lambda value: value.__setitem__("source_sha256", HEX_A),
            )
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                invoke()
            self.assertEqual(
                caught.exception.issues,
                (
                    blocking_issue(
                        "$.source_sha256",
                        {
                            "actual": HEX_A,
                            "expected": actual_archive_sha,
                            "reason": "mapping_source_digest_mismatch",
                        },
                    ),
                ),
            )

    def test_answer_member_digest_and_solution_member_ownership_are_rejected(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, invoke = write_answer_archive_case(
                self,
                root,
                lambda value: value.__setitem__("answer_member_sha256", HEX_A),
            )
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                invoke()
            issue = next(issue for issue in caught.exception.issues if issue.field == "$.answer_member_sha256")
            self.assertEqual(json.loads(issue.evidence)["reason"], "mapping_answer_digest_mismatch")

        def wrong_solution_owner(value):
            value["questions"][0]["solution_spans"][0].update(
                member="source.mmd", start_byte=169, end_byte=170
            )
            value["ignored_spans"].append(
                {
                    "member": "answer.mmd",
                    "start_byte": 0,
                    "end_byte": 9,
                    "reason": "invalidly ignored selected answer material",
                }
            )
            value["ignored_spans"].sort(
                key=lambda item: (item["member"], item["start_byte"], item["end_byte"], item["reason"])
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, invoke = write_answer_archive_case(
                self,
                root,
                wrong_solution_owner,
            )
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                invoke()
            issue = next(
                issue for issue in caught.exception.issues
                if issue.field == "$.questions[0].solution_spans[0].member"
            )
            self.assertEqual(issue.code, "source_contract_mismatch")
            self.assertEqual(
                json.loads(issue.evidence),
                {
                    "actual": "source.mmd",
                    "expected": "answer.mmd",
                    "reason": "cross_field_violation",
                },
            )

    def test_selected_answer_member_must_be_strict_utf8(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, invoke = write_answer_archive_case(self, root, answer_bytes=b"\xff")
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                invoke()
            self.assertEqual(
                caught.exception.issues,
                (
                    blocking_issue(
                        "answer_member",
                        {
                            "end_byte": None,
                            "member": "answer.mmd",
                            "reason": "invalid_utf8",
                            "start_byte": None,
                        },
                        code="mmd_parse_failed",
                    ),
                ),
            )

    def test_zero_reversed_out_of_range_and_wrong_member_spans_are_rejected(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        cases = (
            (lambda value: value["questions"][0]["question_span"].update(start_byte=0, end_byte=0), "$.questions[0].question_span"),
            (lambda value: value["questions"][0]["question_span"].update(start_byte=20, end_byte=10), "$.questions[0].question_span"),
            (lambda value: value["questions"][0]["question_span"].update(start_byte=0, end_byte=999999), "$.questions[0].question_span"),
            (lambda value: value["questions"][0]["question_span"].update(member="answer.mmd"), "$.questions[0].question_span"),
        )
        for index, (mutation, field) in enumerate(cases):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                invoke = mutate_mapping(self, root, mutation)
                with self.subTest(index=index), self.assertRaises(MmdAdapterBlockedError) as caught:
                    invoke()
                issue = next(
                    issue for issue in caught.exception.issues
                    if issue.field == field
                    and json.loads(issue.evidence).get("reason") == "invalid_span"
                )
                self.assertIs(type(issue), MmdAdapterIssue)

    def test_overlapping_question_and_semantic_owner_spans_are_rejected(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        def overlap(value):
            value["questions"][1]["question_span"] = dict(value["questions"][0]["question_span"])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                mutate_mapping(self, root, overlap)()
            issue = next(
                issue for issue in caught.exception.issues
                if issue.field == "$.questions[1].question_span"
                and json.loads(issue.evidence).get("reason") == "span_ownership_overlap"
            )
            self.assertEqual(issue.code, "source_contract_mismatch")

    def test_overlap_uses_semantic_owner_order_not_byte_order(self):
        require_api(self, "adapt_mmd_package_from_mapping")

        def reverse_byte_order(value):
            value["questions"][0]["question_span"].update(start_byte=120, end_byte=170)
            value["questions"][0]["solution_spans"] = [
                {"member": "source.mmd", "start_byte": 40, "end_byte": 50}
            ]
            value["questions"][0]["explanation_spans"] = [
                {"member": "source.mmd", "start_byte": 50, "end_byte": 60}
            ]
            value["questions"][1]["question_span"].update(start_byte=100, end_byte=150)

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                mutate_mapping(self, root, reverse_byte_order)()
            issue = next(
                issue
                for issue in caught.exception.issues
                if json.loads(issue.evidence).get("reason") == "span_ownership_overlap"
            )
            self.assertEqual(issue.proposed_question_id, "EXPLICIT-001")
            self.assertEqual(issue.field, "$.questions[1].question_span")
            self.assertEqual(
                json.loads(issue.evidence),
                {
                    "actual": {
                        "member": "source.mmd",
                        "start_byte": 100,
                        "end_byte": 150,
                    },
                    "expected": {
                        "member": "source.mmd",
                        "start_byte": 120,
                        "end_byte": 170,
                    },
                    "reason": "span_ownership_overlap",
                },
            )

    def test_overlap_binds_candidate_when_later_owner_is_ignored(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        expected_span = dict(
            canonical_mapping()["questions"][0]["explanation_spans"][0]
        )

        def ignored_overlaps_candidate(value):
            value["ignored_spans"][0] = {
                **dict(value["questions"][0]["explanation_spans"][0]),
                "reason": "invalid ignored overlap",
            }
            value["ignored_spans"].sort(
                key=lambda span: (
                    span["member"],
                    span["start_byte"],
                    span["end_byte"],
                    span["reason"],
                )
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                mutate_mapping(self, root, ignored_overlaps_candidate)()
            issue = next(
                issue
                for issue in caught.exception.issues
                if issue.field.startswith("$.ignored_spans[")
                and json.loads(issue.evidence).get("reason") == "span_ownership_overlap"
            )
            self.assertEqual(issue.proposed_question_id, "EXPLICIT-002")
            self.assertEqual(
                json.loads(issue.evidence),
                {
                    "actual": expected_span,
                    "expected": expected_span,
                    "reason": "span_ownership_overlap",
                },
            )

    def test_question_solution_explanation_and_ignored_owner_overlaps_are_each_rejected(self):
        require_api(self, "adapt_mmd_package_from_mapping")

        def question_solution(value):
            value["questions"][0]["solution_spans"] = [dict(value["questions"][0]["question_span"])]

        def solution_explanation(value):
            value["questions"][0]["explanation_spans"] = [dict(value["questions"][0]["solution_spans"][0])]

        def explanation_ignored(value):
            value["ignored_spans"][0] = {
                **dict(value["questions"][0]["explanation_spans"][0]),
                "reason": "invalid overlapping ignored owner",
            }
            value["ignored_spans"].sort(
                key=lambda span: (span["member"], span["start_byte"], span["end_byte"], span["reason"])
            )

        for label, mutation in (
            ("question_solution", question_solution),
            ("solution_explanation", solution_explanation),
            ("explanation_ignored", explanation_ignored),
        ):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.subTest(label=label), self.assertRaises(MmdAdapterBlockedError) as caught:
                    mutate_mapping(self, root, mutation)()
                overlaps = [
                    issue for issue in caught.exception.issues
                    if json.loads(issue.evidence).get("reason") == "span_ownership_overlap"
                ]
                self.assertTrue(overlaps, label)

    def test_duplicate_id_count_number_section_and_answer_cross_fields_are_rejected(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        cases = (
            (
                lambda value: value["questions"].pop(),
                "candidate_count_mismatch", "expected_candidate_count", "candidate_count", 2,
            ),
            (
                lambda value: value["questions"][0].__setitem__("proposed_question_id", "WRONG"),
                "source_contract_mismatch", "$.questions[0].proposed_question_id", "mapping_selection_mismatch", "EXPLICIT-002",
            ),
            (
                lambda value: value["questions"][0].__setitem__("source_question_number", "WRONG"),
                "source_contract_mismatch", "$.questions[0].source_question_number", "mapping_selection_mismatch", "A",
            ),
            (
                lambda value: value["questions"][0].__setitem__("source_section", "WRONG"),
                "source_contract_mismatch", "$.questions[0].source_section", "mapping_selection_mismatch", "Worksheet",
            ),
            (
                lambda value: value["questions"][0].__setitem__("solution_spans", []),
                "source_contract_mismatch", "$.questions[0].solution_spans", "cross_field_violation", "positive_length",
            ),
            (
                lambda value: value["questions"][1].__setitem__(
                    "solution_spans",
                    [{"member": "source.mmd", "start_byte": 169, "end_byte": 170}],
                ),
                "source_contract_mismatch", "$.questions[1].solution_spans", "cross_field_violation", 0,
            ),
        )
        for index, (mutation, code, field, reason, expected) in enumerate(cases):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.subTest(index=index), self.assertRaises(MmdAdapterBlockedError) as caught:
                    mutate_mapping(self, root, mutation)()
                issue = next(
                    issue for issue in caught.exception.issues
                    if issue.code == code
                    and issue.field == field
                    and json.loads(issue.evidence).get("reason") == reason
                    and json.loads(issue.evidence).get("expected") == expected
                )
                self.assertIs(type(issue), MmdAdapterIssue)

    def test_duplicate_proposed_id_uses_the_frozen_hashed_cross_field_envelope(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        duplicate_id = "EXPLICIT-002"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                mutate_mapping(
                    self,
                    root,
                    lambda value: value["questions"][1].__setitem__(
                        "proposed_question_id", duplicate_id
                    ),
                )()
            issue = next(
                issue for issue in caught.exception.issues
                if issue.code == "source_contract_mismatch"
                and issue.field == "$.questions[1].proposed_question_id"
                and json.loads(issue.evidence).get("reason") == "cross_field_violation"
            )
        self.assertEqual(
            json.loads(issue.evidence),
            {
                "actual": sha256(duplicate_id.encode("utf-8")),
                "expected": "unique_proposed_question_id",
                "reason": "cross_field_violation",
            },
        )

    def test_unaccounted_non_whitespace_blocks_approved_consumption(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                mutate_mapping(self, root, lambda value: value.__setitem__("ignored_spans", []))()
            coverage = [issue for issue in caught.exception.issues if issue.field == "coverage"]
            self.assertTrue(coverage)
            self.assertTrue(all(json.loads(issue.evidence)["reason"] == "unaccounted_non_whitespace" for issue in coverage))

    def test_m6_uses_only_the_frozen_ascii_whitespace_byte_set(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        ascii_whitespace_source = SOURCE_BYTES.replace(b"\n\nFooter branding", b"\n\x09\x0b\x0c\x0d\nFooter branding")
        ascii_manifest = valid_manifest(ascii_whitespace_source)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = write_mapping_case(
                self,
                root,
                source_bytes=ascii_whitespace_source,
                manifest=ascii_manifest,
            )()
            self.assertTrue(result.package_root.is_dir())

        non_ascii_whitespace = SOURCE_BYTES.replace(b"\n\nFooter branding", "\n\u00a0\nFooter branding".encode("utf-8"))
        non_ascii_manifest = valid_manifest(non_ascii_whitespace)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                write_mapping_case(
                    self,
                    root,
                    source_bytes=non_ascii_whitespace,
                    manifest=non_ascii_manifest,
                )()
            self.assertTrue(any(issue.field == "coverage" for issue in caught.exception.issues))

    def test_bound_and_ignored_image_is_rejected(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                mutate_mapping(self, root, lambda value: value.__setitem__("ignored_image_members", [{"member": "images/diagram.jpg", "reason": "wrongly ignored"}]))()
            issues = [
                issue
                for issue in caught.exception.issues
                if issue.code == "source_contract_mismatch"
                and issue.field == "$.ignored_image_members[0].member"
            ]
            self.assertTrue(issues)
            self.assertTrue(
                all(
                    json.loads(issue.evidence).get("reason")
                    == "cross_field_violation"
                    for issue in issues
                )
            )

    def test_approved_ignored_inventory_resource_is_not_staged(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, invoke = write_image_archive_case(self, root)
            result = invoke()
            self.assertTrue((result.package_root / "images/diagram.jpg").is_file())
            self.assertFalse((result.package_root / "images/unused-a.jpg").exists())
            self.assertFalse((result.package_root / "images/unused-b.jpg").exists())

    def test_unbound_and_missing_ignored_image_states_have_exact_reasons(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        def unbound(value):
            for question in value["questions"]:
                question["image_bindings"] = []

        def missing_ignored(value):
            value["ignored_image_members"] = [{"member": "images/missing.jpg", "reason": "unused"}]

        for mutation, reason in (
            (unbound, "unaccounted_inventory_image"),
            (missing_ignored, "ignored_member_missing"),
        ):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.assertRaises(MmdAdapterBlockedError) as caught:
                    mutate_mapping(self, root, mutation)()
                issue = next(
                    issue for issue in caught.exception.issues
                    if issue.code == "image_binding_invalid"
                    and issue.field == "ignored_image_members"
                    and json.loads(issue.evidence).get("reason") == reason
                )
                self.assertIs(type(issue), MmdAdapterIssue)

    def test_each_source_image_token_must_have_exactly_one_binding(self):
        require_api(self, "adapt_mmd_package_from_mapping")

        def missing_binding(value):
            value["questions"][0]["image_bindings"] = []

        def duplicate_binding(value):
            value["questions"][0]["image_bindings"].append(
                dict(value["questions"][0]["image_bindings"][0])
            )
            value["questions"][0]["image_bindings"][1]["semantic_order"] = 1

        for mutation, reason in (
            (missing_binding, "ambiguous_reference"),
            (duplicate_binding, "duplicate_token_binding"),
        ):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                with self.subTest(reason=reason), self.assertRaises(MmdAdapterBlockedError) as caught:
                    mutate_mapping(self, root, mutation)()
                issues = [
                    issue
                    for issue in caught.exception.issues
                    if issue.code == "image_binding_invalid"
                    and json.loads(issue.evidence).get("reason") == reason
                ]
                self.assertEqual(len(issues), 1)
                self.assertEqual(issues[0].field, "expected_image_members")
                self.assertFalse((root / "data/staging/package").exists())

    def test_image_token_span_must_be_inside_its_question_at_m3(self):
        require_api(self, "adapt_mmd_package_from_mapping")

        def cross_question_token(value):
            value["questions"][0]["image_bindings"][0]["token_span"] = dict(
                value["questions"][1]["image_bindings"][0]["token_span"]
            )

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mapping = canonical_mapping()
            expected_question = dict(mapping["questions"][0]["question_span"])
            offending = dict(mapping["questions"][1]["image_bindings"][0]["token_span"])
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                mutate_mapping(self, root, cross_question_token)()
            matching = [
                issue
                for issue in caught.exception.issues
                if issue.code == "source_contract_mismatch"
                and issue.field == "$.questions[0].image_bindings[0].token_span"
                and json.loads(issue.evidence).get("reason") == "wrong_span_owner"
            ]
            self.assertEqual(len(matching), 1)
            self.assertEqual(
                json.loads(matching[0].evidence),
                {
                    "actual": offending,
                    "expected": expected_question,
                    "reason": "wrong_span_owner",
                },
            )

    def test_invalid_earlier_binding_and_valid_later_binding_never_leak_pipeline_error(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        source_bytes = SOURCE_BYTES.replace(
            b"![](./images/diagram.jpg)\n",
            b"![](./images/diagram.jpg) ![](./images/other.jpg)\n",
            1,
        )
        manifest = valid_manifest(source_bytes)
        manifest["selections"][0]["expected_image_members"] = [
            "images/diagram.jpg",
            "images/other.jpg",
        ]
        draft = valid_draft()
        draft["questions"][0]["image_bindings"].append(
            {
                "semantic_order": 1,
                "source_line": 4,
                "raw_target": "./images/other.jpg",
                "selected_member": "images/other.jpg",
                "role": "question",
            }
        )

        def invalidate_first(value):
            first = value["questions"][0]["image_bindings"][0]
            first["raw_target"] = "./images/missing.jpg"
            first["canonical_path"] = "images/missing.jpg"

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invoke = write_mapping_case(
                self,
                root,
                source_bytes=source_bytes,
                manifest=manifest,
                draft=draft,
                mutation=invalidate_first,
            )
            (root / "images/other.jpg").write_bytes(b"other-image\n")
            try:
                invoke()
            except MmdAdapterBlockedError as caught:
                self.assertTrue(
                    any(issue.code == "image_binding_invalid" for issue in caught.issues)
                )
            except PipelineError as caught:
                self.fail(f"M5 leaked raw PipelineError: {caught}")
            else:
                self.fail("invalid sparse bindings were accepted")
            self.assertFalse((root / "data/staging/package").exists())

    def test_non_null_selected_member_must_exist_in_safe_inventory(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invoke = mutate_mapping(self, root, lambda value: None)
            (root / "images/diagram.jpg").unlink()
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                invoke()
            issue = next(
                issue
                for issue in caught.exception.issues
                if issue.code == "image_binding_invalid"
                and json.loads(issue.evidence).get("reason") == "selection_conflict"
            )
            self.assertEqual(issue.field, "expected_image_members")
            self.assertFalse((root / "data/staging/package").exists())

    def test_duplicate_ignored_inventory_image_has_its_own_exact_blocker(self):
        require_api(self, "adapt_mmd_package_from_mapping")

        def duplicate_ignored(value):
            value["ignored_image_members"] = [
                {"member": "images/unused-a.jpg", "reason": "approved unused resource A"},
                {"member": "images/unused-a.jpg", "reason": "approved unused resource A"},
                {"member": "images/unused-b.jpg", "reason": "approved unused resource B"},
            ]

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, invoke = write_image_archive_case(
                self,
                root,
                mapping_mutation=duplicate_ignored,
            )
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                invoke()
            issue = next(
                issue for issue in caught.exception.issues
                if issue.code == "image_binding_invalid"
                and issue.field == "ignored_image_members"
                and json.loads(issue.evidence).get("reason") == "duplicate_ignored_image"
            )
            self.assertIs(type(issue), MmdAdapterIssue)

    def test_representable_missing_image_remains_explicit_and_is_not_staged(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        def missing(value):
            for question in value["questions"]:
                question["image_bindings"][0]["selected_member"] = None

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invoke = mutate_mapping(self, root, missing)
            (root / "images/diagram.jpg").unlink()
            result = invoke()
            self.assertFalse((result.package_root / "images/diagram.jpg").exists())
            candidates = json.loads((result.package_root / "records/candidates.json").read_bytes())
            self.assertTrue(all(candidate["image_paths"] == ["images/diagram.jpg"] for candidate in candidates))

    def test_unsafe_image_target_invalid_utf8_and_unclosed_atomic_token_are_rejected(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        unsafe = SOURCE_BYTES.replace(b"./images/diagram.jpg", b"../unsafe/diagram.jpg")
        unsafe_manifest = valid_manifest(unsafe)
        unsafe_draft = valid_draft()
        for question in unsafe_draft["questions"]:
            question["image_bindings"][0]["raw_target"] = "../unsafe/diagram.jpg"
        sources = (
            (unsafe, unsafe_manifest, unsafe_draft, "archive_member_unsafe", "image_target_traversal"),
            (b"\xff" + SOURCE_BYTES[1:], valid_manifest(b"\xff" + SOURCE_BYTES[1:]), valid_draft(), "mmd_parse_failed", "invalid_utf8"),
            (SOURCE_BYTES.replace(b"$x+1$", b"$x+1 "), valid_manifest(SOURCE_BYTES.replace(b"$x+1$", b"$x+1 ")), valid_draft(), "mmd_parse_failed", "unclosed_token"),
        )
        for index, (source_bytes, manifest, draft, code, reason) in enumerate(sources):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                mutation = None
                if code == "archive_member_unsafe":
                    mutation = lambda value: [
                        binding.__setitem__("canonical_path", "images/diagram.jpg")
                        for question in value["questions"]
                        for binding in question["image_bindings"]
                    ]
                with self.subTest(index=index), self.assertRaises(MmdAdapterBlockedError) as caught:
                    write_mapping_case(self, root, source_bytes=source_bytes, manifest=manifest, draft=draft, mutation=mutation)()
                issue = next(
                    issue for issue in caught.exception.issues
                    if issue.code == code
                    and json.loads(issue.evidence).get("reason") == reason
                )
                self.assertIs(type(issue), MmdAdapterIssue)
                self.assertTrue(
                    all(other.code == code for other in caught.exception.issues),
                    "an M4 blocker must not emit downstream M5 consequences",
                )

    def test_incomplete_safe_image_envelope_is_a_deterministic_parse_blocker(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        malformed = SOURCE_BYTES.replace(
            b"![](./images/diagram.jpg)",
            b"![](./images/diagram.jpg",
        )
        manifest = valid_manifest(malformed)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                write_mapping_case(self, root, source_bytes=malformed, manifest=manifest)()
            issues = [issue for issue in caught.exception.issues if issue.code == "mmd_parse_failed"]
            self.assertTrue(issues)
            self.assertTrue(
                any(json.loads(issue.evidence).get("reason") == "unsupported_grammar" for issue in issues)
            )
            self.assertTrue(
                all(issue.code == "mmd_parse_failed" for issue in caught.exception.issues),
                "an M4 blocker must stop M5 token-binding validation",
            )

    def test_unclosed_itemize_inside_mapped_question_is_not_suppressed(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        malformed = SOURCE_BYTES.replace(b"Find $x+1$.\n", b"\\begin{itemize}\n")
        manifest = valid_manifest(malformed)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                write_mapping_case(
                    self,
                    root,
                    source_bytes=malformed,
                    manifest=manifest,
                )()
            issues = [
                issue
                for issue in caught.exception.issues
                if issue.code == "mmd_parse_failed"
                and json.loads(issue.evidence).get("reason") == "unsupported_grammar"
            ]
            self.assertTrue(issues)
            self.assertFalse((root / "data/staging/package").exists())

    def test_itemize_cannot_be_closed_by_content_outside_question_span(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        source_bytes = (
            b"Mapped question\\n"
            b"\\begin{itemize}\\n"
            b"\\item[(a)] omitted subpart\\n"
            b"\\end{itemize}\\n"
        ).replace(b"\\n", b"\n")
        manifest = valid_manifest(source_bytes)
        manifest["expected_candidate_count"] = 1
        manifest["selections"] = [
            selection("EXPLICIT-002", "A", answer_mapping="missing_from_source")
        ]
        manifest["selections"][0]["expected_image_members"] = []
        draft = valid_draft()
        draft["questions"] = [
            {
                "semantic_order": 0,
                "proposed_question_id": "EXPLICIT-002",
                "source_question_number": "A",
                "source_section": "Worksheet",
                "question_line_span": line_span(1, 2),
                "solution_line_spans": [],
                "explanation_line_spans": [],
                "image_bindings": [],
                "ambiguity_note": "subpart must stay inside question",
            }
        ]
        draft["ignored_line_spans"] = [
            {**line_span(3, 4), "reason": "invalid attempted subpart omission"}
        ]
        draft["ignored_image_members"] = [
            {"member": "images/diagram.jpg", "reason": "fixture-only resource"}
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                write_mapping_case(
                    self,
                    root,
                    source_bytes=source_bytes,
                    manifest=manifest,
                    draft=draft,
                )()
            self.assertTrue(
                any(
                    issue.code == "mmd_parse_failed"
                    and json.loads(issue.evidence).get("reason") == "unsupported_grammar"
                    for issue in caught.exception.issues
                )
            )
            self.assertFalse((root / "data/staging/package").exists())

    def test_complete_unsupported_image_envelope_is_an_m4_canonicalization_blocker(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        source_bytes = SOURCE_BYTES.replace(b"diagram.jpg", b"diagram.gif")
        manifest = valid_manifest(source_bytes)
        draft = valid_draft()
        for selected, question in zip(manifest["selections"], draft["questions"]):
            selected["expected_image_members"] = []
            question["image_bindings"] = []
        draft["ignored_image_members"] = [
            {"member": "images/diagram.jpg", "reason": "fixture-only resource"}
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                write_mapping_case(
                    self,
                    root,
                    source_bytes=source_bytes,
                    manifest=manifest,
                    draft=draft,
                )()
            self.assertTrue(caught.exception.issues)
            self.assertTrue(
                all(issue.code == "archive_member_unsafe" for issue in caught.exception.issues)
            )
            self.assertTrue(
                all(
                    json.loads(issue.evidence).get("reason") == "image_target_canonicalization"
                    for issue in caught.exception.issues
                )
            )
            self.assertFalse((root / "data/staging/package").exists())

    def test_mode_b_accepts_both_existing_bilingual_layouts(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        from tests.integration.test_mmd_explicit_mapping import (
            _minimal_bilingual_equivalence_case,
        )

        for language_layout in (
            "english_then_chinese",
            "interleaved_bilingual",
        ):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                _mode_a, package = _minimal_bilingual_equivalence_case(
                    self,
                    root,
                    language_layout=language_layout,
                )
                manifest = json.loads((root / "selection.json").read_bytes())
                candidates = json.loads(
                    (package.package_root / "records/candidates.json").read_bytes()
                )
            with self.subTest(language_layout=language_layout):
                self.assertEqual(
                    manifest["selections"][0]["language_layout"],
                    language_layout,
                )
                self.assertEqual(len(candidates), 1)
                self.assertEqual(candidates[0]["translation_status"], "source_present")

    def test_mode_b_invalid_bilingual_transition_uses_exact_m5_envelope(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        manifest = valid_manifest()
        manifest["selections"][0]["language_layout"] = "english_then_chinese"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                write_mapping_case(self, root, manifest=manifest)()
            issue = next(
                issue for issue in caught.exception.issues
                if issue.code == "language_mapping_ambiguous"
                and issue.proposed_question_id == "EXPLICIT-002"
            )
        self.assertEqual(issue.source_locator, "source.mmd#bytes=18:27")
        self.assertEqual(issue.field, "language_layout")
        self.assertEqual(
            json.loads(issue.evidence),
            {
                "end_byte": 27,
                "layout": "english_then_chinese",
                "reason": "missing_zh",
                "start_byte": 18,
            },
        )

    def test_repeated_labels_distinct_spans_and_reused_image_are_preserved(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            _, result = adapt_from_mapping(self, Path(directory))
            candidates = json.loads((result.package_root / "records/candidates.json").read_text(encoding="utf-8"))
            self.assertEqual([value["source_question_number"] for value in candidates], ["A", "A"])
            self.assertEqual(len(candidates), 2)
            self.assertEqual(tuple(path.name for path in (result.package_root / "images").iterdir()), ("diagram.jpg",))

    def test_source_only_projection_solution_explanation_and_missing_answer(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            _, result = adapt_from_mapping(self, Path(directory))
            candidates = json.loads((result.package_root / "records/candidates.json").read_text(encoding="utf-8"))
            first, second = candidates
            self.assertEqual(first["translation_status"], "missing")
            self.assertEqual(first["solution_original"], "Solution evidence\n2\n")
            self.assertEqual(first["answer_status"], "source_provided")
            self.assertEqual(first["explanation_text"], "Explanation evidence\nBecause $1+1=2$.\n")
            self.assertEqual(first["explanation_status"], "source_present")
            self.assertEqual(first["explanation_evidence"], "source:source/source-map.json#questions[0].explanation_spans")
            self.assertEqual(second["solution_original"], "")
            self.assertEqual(second["answer_status"], "missing_from_source")

    def test_multiple_mapping_issues_use_the_existing_stable_five_field_order(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        def invalid(value):
            value["source_sha256"] = HEX_A
            value["primary_member_sha256"] = HEX_B

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                mutate_mapping(self, root, invalid)()
            expected = stable_issues(
                blocking_issue(
                    "$.source_sha256",
                    {
                        "actual": HEX_A,
                        "expected": sha256(SOURCE_BYTES),
                        "reason": "mapping_source_digest_mismatch",
                    },
                ),
                blocking_issue(
                    "$.primary_member_sha256",
                    {
                        "actual": HEX_B,
                        "expected": sha256(SOURCE_BYTES),
                        "reason": "mapping_primary_digest_mismatch",
                    },
                ),
            )
            self.assertEqual(caught.exception.issues, expected)
            keys = [
                (issue.source_locator, issue.proposed_question_id or "", issue.code, issue.field, issue.evidence)
                for issue in caught.exception.issues
            ]
            self.assertEqual(keys, sorted(keys))
            self.assertTrue(all(type(issue) is MmdAdapterIssue for issue in caught.exception.issues))


if __name__ == "__main__":
    unittest.main()
