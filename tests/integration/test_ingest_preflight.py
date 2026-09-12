from __future__ import annotations

from dataclasses import asdict, replace
import hashlib
import importlib
import inspect
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from joy_m2.errors import PipelineError
from joy_m2.export.formats import canonical_json_bytes
from joy_m2.models import ArtifactRef
from joy_m2.ingest.models import (
    BatchImportManifest,
    ImportCandidate,
    ImportFileEvidence,
    ImportPreflightResult,
)
from joy_m2.ingest.preflight import preflight_import


BASELINE_PATH = ROOT / "releases/V1.18/Joy_M2_Complete_Question_DB_V1_18.sqlite3"
BASELINE_SHA256 = "fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7"
BASELINE_SIZE = 9_363_456
MANIFEST_SHA256 = "b5a0ae6597028c48c6f7cdc81bd7e67d61dd369cbf96d7c6a4e96efd73984c5d"
PREFLIGHT_SHA256 = "087574a8af6fe28ac65a5b5810794952044cb5f0778ed3492d1e7819a4be33c2"
NORMALIZED_TEXT = "Solve x + 1 = 2.\nShow work."
NORMALIZED_SHA256 = "4e33fd8a11eba010d219e342864522608cede6843138f4b40bf2f50346b01b29"
REFERENCE_TEXT_SHA256 = "04c2b5df26e1f6440412a97203a7a2894819069c9a878493389dcb53f8d9180a"
REFERENCE_ID = "M2QD-DA-EXAMPLE-Q1"
REFERENCE_SOURCE_ID = "M2QD-DIFFERENTIATION-APPLICATIONS"
REFERENCE_NUMBER = "EXAMPLE-Q1"
REFERENCE_SECTION = "教材例题"
REFERENCE_FRAGMENT = "7ca9b7902bf8efd929145e64c5d4a1aa11b2da06028e4e2123026a09da640e89"
REFERENCE_TEXT = (
    "Consider the curve $C: y=26-\\frac{108}{x}$ ,where $0<x<20$ .\n"
    "(a) Find $\\frac{d y}{d x}$ .\n"
    "(b) If a tangent $L$ to $C$ passes through the point（ 10,20 ）,find the equation of $L$ ."
)
DUPLICATE_EVIDENCE = (
    '{"candidate_id":"TASK9-DUP-001","normalized_text_sha256":'
    '"04c2b5df26e1f6440412a97203a7a2894819069c9a878493389dcb53f8d9180a",'
    '"reference_question_id":"M2QD-DA-EXAMPLE-Q1"}'
)
IMAGE_REFERENCE_ID = "M2QD-DA-PARTB-Q4"
IMAGE_SOURCE_ID = "M2QD-DIFFERENTIATION-APPLICATIONS"
IMAGE_NUMBER = "PARTB-Q4"
IMAGE_SECTION = "乙部特训"
IMAGE_FRAGMENT = "7340583de6e3d8cd7d284d578d63484f07f5e8beb7809c41cb25bc848f5eff61"
IMAGE_PATH = "extracted_reference/source_images/M2QD_DA_PARTB_Q4_Figure1.jpg"
IMAGE_ROLE = "required_question_figure"
IMAGE_SHA256 = "eeddd1592eba7c505e3ac6fb484da4fa695b328dce5de4888ea340936869b9ae"


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _baseline_ref(path: Path = BASELINE_PATH) -> ArtifactRef:
    data = path.read_bytes()
    return ArtifactRef(path, _sha(data), len(data), "sqlite")


def _raw_candidate(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "proposed_question_id": "TASK9-NEW-001",
        "source_id": "TASK9-SOURCE",
        "source_question_number": "1",
        "source_section": "Canonical JSON",
        "source_fragment_hash": "1" * 64,
        "question_text_original": "Find x if x + 1 = 2.",
        "answer_status": "source_provided",
        "solution_original": "x = 1",
        "solution_verified": "x = 1",
        "image_paths": [],
        "primary_type": "切线与法线",
        "tags": [],
        "difficulty_level": 2,
        "question_text_zh": "求 x。",
        "translation_status": "source_present",
        "translation_evidence": "source:source/source.txt#translation-1",
        "explanation_text": "Subtract one.",
        "explanation_status": "source_present",
        "explanation_evidence": "source:source/source.txt#explanation-1",
        "image_roles": [],
        "tag_status": "missing",
        "difficulty_status": "source_provided",
        "enrichment_status": "complete",
    }
    values.update(overrides)
    return values


def _file_evidence(relative_path: str, data: bytes, kind: str) -> ImportFileEvidence:
    return ImportFileEvidence(relative_path, _sha(data), len(data), kind)


def _write(root: Path, relative_path: str, data: bytes) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def _package(
    root: Path,
    *,
    record_groups: tuple[tuple[str, list[dict[str, object]]], ...] | None = None,
    images: dict[str, bytes] | None = None,
    source_path: str = "source/source.txt",
) -> BatchImportManifest:
    if record_groups is None:
        record_groups = (("records/candidates.json", [_raw_candidate()]),)
    image_values = {} if images is None else dict(images)
    candidate_evidence = []
    for relative_path, records in record_groups:
        data = canonical_json_bytes(records) + b"\n"
        _write(root, relative_path, data)
        candidate_evidence.append(_file_evidence(relative_path, data, "candidate_json"))
    source = b"canonical source evidence\n"
    answer = b"canonical answer evidence\n"
    teacher = b"teacher note\n"
    errors = b"common error\n"
    _write(root, source_path, source)
    _write(root, "answers/answer.txt", answer)
    _write(root, "teacher-notes/notes.txt", teacher)
    _write(root, "common-errors/errors.txt", errors)
    image_evidence = []
    for relative_path, data in image_values.items():
        _write(root, relative_path, data)
        image_evidence.append(_file_evidence(relative_path, data, "image"))
    return BatchImportManifest(
        schema_version="task9-import-manifest-v1",
        batch_id="TASK9-BATCH-001",
        project="Joy M2 AI Database",
        module="M2",
        chapter="Task 9A",
        target_release_version="V1.19",
        candidate_records=tuple(candidate_evidence),
        source_files=(_file_evidence(source_path, source, "source"),),
        answer_files=(_file_evidence("answers/answer.txt", answer, "answer"),),
        image_files=tuple(image_evidence),
        teacher_notes_files=(
            _file_evidence("teacher-notes/notes.txt", teacher, "teacher_notes"),
        ),
        common_errors_files=(
            _file_evidence("common-errors/errors.txt", errors, "common_errors"),
        ),
        language_policy="preserve_source_and_store_reviewed_chinese_separately",
        split_policy="one_complete_question_per_record",
        difficulty_policy="joy_level_1_5",
        tag_policy="controlled_primary_type_and_tags",
        answer_policy="preserve_source_answer_identity",
        explanation_policy="source_or_independently_verified_with_identity",
    )


def _manifest_projection(manifest: BatchImportManifest) -> dict[str, object]:
    projection: dict[str, object] = {}
    for name in (
        "schema_version", "batch_id", "project", "module", "chapter",
        "target_release_version", "candidate_records", "source_files",
        "answer_files", "image_files", "teacher_notes_files",
        "common_errors_files", "language_policy", "split_policy",
        "difficulty_policy", "tag_policy", "answer_policy",
        "explanation_policy",
    ):
        value = getattr(manifest, name)
        projection[name] = [asdict(item) for item in value] if isinstance(value, tuple) else value
    return projection


def _manifest_digest(manifest: BatchImportManifest) -> str:
    return _sha(canonical_json_bytes(_manifest_projection(manifest)) + b"\n")


def _literal_records() -> list[dict[str, object]]:
    first = _raw_candidate(
        proposed_question_id="TASK9-NEW-001",
        source_id=REFERENCE_SOURCE_ID,
        source_question_number=REFERENCE_NUMBER,
        source_section=REFERENCE_SECTION,
        source_fragment_hash=REFERENCE_FRAGMENT,
        question_text_original="  Solve   x + 1 = 2.\r\nShow work.  ",
        question_text_zh="求解 x + 1 = 2，并写出步骤。",
        translation_status="ai_proposed",
        translation_evidence="ai-proposal-sha256:e970c7b1f1c075668394b0519806a72283566a7a13b565700d1b2fc733baf7af",
        explanation_text="Subtract 1 from both sides.",
        explanation_evidence="source:source/literal.txt#new-explanation",
        solution_original="x = 1",
        solution_verified="x = 1",
        image_paths=["images/diagram.png"],
        image_roles=["question"],
        primary_type="代数",
        tags=["一元一次方程"],
        tag_status="source_provided",
        difficulty_level=1,
    )
    second = _raw_candidate(
        proposed_question_id="TASK9-DUP-001",
        source_id=REFERENCE_SOURCE_ID,
        source_question_number=REFERENCE_NUMBER,
        source_section=REFERENCE_SECTION,
        source_fragment_hash=REFERENCE_FRAGMENT,
        question_text_original=REFERENCE_TEXT,
        question_text_zh="考虑曲线并求指定切线。",
        translation_evidence="source:source/literal.txt#dup-translation",
        explanation_text="使用导数斜率与点斜式。",
        explanation_evidence="source:source/literal.txt#dup-explanation",
        solution_original="见冻结来源解答。",
        solution_verified="见冻结来源解答。",
        primary_type="切线与法线",
        tags=["过指定点的切线", "切点未知"],
        tag_status="source_provided",
        difficulty_level=3,
    )
    return [first, second]


def _literal_package(root: Path) -> BatchImportManifest:
    records = canonical_json_bytes(_literal_records()) + b"\n"
    source = b"literal source evidence\n"
    answer = b"literal answer evidence\n"
    image = bytes.fromhex("89504e470d0a1a0a5441534b392d4c49544552414c2d494d414745")
    teacher = b"literal teacher note\n"
    errors = b"literal common error\n"
    files = {
        "records/candidates.json": (records, "candidate_json"),
        "source/literal.txt": (source, "source"),
        "answers/answer.txt": (answer, "answer"),
        "images/diagram.png": (image, "image"),
        "teacher-notes/notes.txt": (teacher, "teacher_notes"),
        "common-errors/errors.txt": (errors, "common_errors"),
    }
    for path, (data, _) in files.items():
        _write(root, path, data)
    manifest = BatchImportManifest(
        "task9-import-manifest-v1", "TASK9-LITERAL-BATCH-001",
        "Joy M2 AI Database", "M2", "Literal Oracle", "V1.19",
        (_file_evidence("records/candidates.json", records, "candidate_json"),),
        (_file_evidence("source/literal.txt", source, "source"),),
        (_file_evidence("answers/answer.txt", answer, "answer"),),
        (_file_evidence("images/diagram.png", image, "image"),),
        (_file_evidence("teacher-notes/notes.txt", teacher, "teacher_notes"),),
        (_file_evidence("common-errors/errors.txt", errors, "common_errors"),),
        "preserve_source_and_store_reviewed_chinese_separately",
        "one_complete_question_per_record", "joy_level_1_5",
        "controlled_primary_type_and_tags", "preserve_source_answer_identity",
        "source_or_independently_verified_with_identity",
    )
    assert len(records) == 2148
    assert _sha(records) == "6c1ca2a9518701a452218700f181cecbaef4161614cf5b317f075adf7761aa27"
    assert _manifest_digest(manifest) == MANIFEST_SHA256
    return manifest


def _literal_digest_payload() -> dict[str, object]:
    candidates = _literal_records()
    candidates[0] = dict(
        candidates[0],
        normalized_text_sha256=NORMALIZED_SHA256,
        image_sha256s=["a7b6855df3f8ceacabbf61e15afa4a33af7a652f8df8dae79b1d1b5fd8c87851"],
    )
    candidates[1] = dict(
        candidates[1],
        normalized_text_sha256=REFERENCE_TEXT_SHA256,
        image_sha256s=[],
    )
    adaptation = {
        "candidate_id": "TASK9-NEW-001",
        "reference_question_id": REFERENCE_ID,
        "adaptation_kind": "adapted",
        "evidence": (
            "matched=source_locator+source_fragment_hash;"
            f"candidate_normalized_text_sha256={NORMALIZED_SHA256};"
            f"reference_normalized_text_sha256={REFERENCE_TEXT_SHA256}"
        ),
        "reason": "stable_source_identity_matches_with_transformed_text",
    }
    file_evidence = [
        {"relative_path": "answers/answer.txt", "sha256": "d5eaf1ac88ec856434544d132e09b6ff4008e38c2599f8f58d84a90b5fc5dd0d", "size_bytes": 24, "kind": "answer"},
        {"relative_path": "common-errors/errors.txt", "sha256": "1cfe2bd273ee917428a23d5aab07c63deaf20c03ca61dbbaebbe028b070f1bf0", "size_bytes": 21, "kind": "common_errors"},
        {"relative_path": "images/diagram.png", "sha256": "a7b6855df3f8ceacabbf61e15afa4a33af7a652f8df8dae79b1d1b5fd8c87851", "size_bytes": 27, "kind": "image"},
        {"relative_path": "records/candidates.json", "sha256": "6c1ca2a9518701a452218700f181cecbaef4161614cf5b317f075adf7761aa27", "size_bytes": 2148, "kind": "candidate_json"},
        {"relative_path": "source/literal.txt", "sha256": "a24b2e6c1a00a35cc9b513831e223de4990d5e6ed62d89700e32772bfca37c29", "size_bytes": 24, "kind": "source"},
        {"relative_path": "teacher-notes/notes.txt", "sha256": "4268dcf4d4b1d694b06c37edf71a52baecf0d80b5c57dc652d0c6a6e1f8650f5", "size_bytes": 21, "kind": "teacher_notes"},
    ]
    issue = {
        "code": "duplicate_exact", "severity": "blocking",
        "proposed_question_id": "TASK9-DUP-001", "field": "candidate",
        "evidence": DUPLICATE_EVIDENCE,
    }
    return {
        "schema": "task9-preflight-v1",
        "batch_id": "TASK9-LITERAL-BATCH-001",
        "target_release_version": "V1.19",
        "baseline": {
            "release_version": "V1.18", "schema_version": "complete-question-v1.0",
            "question_count": 497, "sha256": BASELINE_SHA256,
            "size_bytes": BASELINE_SIZE, "kind": "sqlite",
        },
        "manifest_policies": {
            "schema_version": "task9-import-manifest-v1", "project": "Joy M2 AI Database",
            "module": "M2", "chapter": "Literal Oracle",
            "language_policy": "preserve_source_and_store_reviewed_chinese_separately",
            "split_policy": "one_complete_question_per_record",
            "difficulty_policy": "joy_level_1_5",
            "tag_policy": "controlled_primary_type_and_tags",
            "answer_policy": "preserve_source_answer_identity",
            "explanation_policy": "source_or_independently_verified_with_identity",
        },
        "candidate_record_order": ["records/candidates.json"],
        "file_evidence": file_evidence,
        "candidates": candidates,
        "issues": [issue],
        "duplicate_classifications": [
            {"candidate_id": "TASK9-NEW-001", "classification": "new_candidate", "reference_question_id": None, "evidence": None},
            {"candidate_id": "TASK9-DUP-001", "classification": "duplicate", "reference_question_id": REFERENCE_ID, "evidence": DUPLICATE_EVIDENCE},
        ],
        "image_evidence": [
            {"proposed_question_id": "TASK9-NEW-001", "relative_path": "images/diagram.png", "sha256": "a7b6855df3f8ceacabbf61e15afa4a33af7a652f8df8dae79b1d1b5fd8c87851", "size_bytes": 27, "kind": "image", "role": "question"},
        ],
        "report": {
            "batch_id": "TASK9-LITERAL-BATCH-001",
            "status": "BLOCKED — IMPORT PREFLIGHT FAILED",
            "manifest_sha256": MANIFEST_SHA256,
            "baseline_version": "V1.18", "before_count": 497,
            "target_release_version": "V1.19", "detected_count": 2,
            "new_candidate_count": 1, "duplicate_count": 1, "rejected_count": 0,
            "ambiguous_count": 0, "approved_count": 0, "projected_after_count": 498,
            "readable_files": [item["relative_path"] for item in file_evidence],
            "unreadable_files": [], "unsupported_files": [],
            "teacher_notes_file_count": 1, "common_errors_file_count": 1,
            "ambiguous_splits": [], "missing_answers": [], "missing_explanations": [],
            "incomplete_enrichments": [], "missing_images": [], "orphan_images": [],
            "level_counts": [[1, 1], [3, 1]],
            "proposed_ids": ["TASK9-NEW-001", "TASK9-DUP-001"],
            "adaptations": [adaptation], "warnings": [],
            "blocking_errors": ["duplicate_exact"],
        },
    }


def _tree_fingerprint(path: Path) -> tuple[tuple[str, str, int, str], ...]:
    entries: list[tuple[str, str, int, str]] = []
    for item in sorted(path.rglob("*"), key=lambda value: value.relative_to(path).as_posix()):
        relative_path = item.relative_to(path).as_posix()
        if item.is_symlink():
            target = item.readlink().as_posix().encode("utf-8")
            entries.append((relative_path, "symlink", len(target), _sha(target)))
        elif item.is_dir():
            entries.append((relative_path, "directory", 0, ""))
        elif item.is_file():
            data = item.read_bytes()
            entries.append((relative_path, "file", len(data), _sha(data)))
        else:
            entries.append((relative_path, "other", 0, ""))
    return tuple(entries)


class PreflightBehaviorCase(unittest.TestCase):
    def _result(
        self,
        manifest: BatchImportManifest,
        root: Path,
        baseline: ArtifactRef | None = None,
    ) -> ImportPreflightResult:
        try:
            result = preflight_import(manifest, root, baseline or _baseline_ref())
        except NotImplementedError as exc:
            self.fail(f"approved preflight behavior is not implemented: {exc!r}")
        self.assertIs(type(result), ImportPreflightResult)
        return result

    def _rejected(
        self,
        manifest: object,
        root: object,
        baseline: object | None = None,
    ) -> None:
        try:
            with self.assertRaises(PipelineError):
                preflight_import(manifest, root, baseline or _baseline_ref())
        except NotImplementedError as exc:
            self.fail(f"approved rejection behavior is not implemented: {exc!r}")

    def _blocked(self, records: list[dict[str, object]]) -> ImportPreflightResult:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self._result(_package(root, record_groups=(("records/candidates.json", records),)), root)
        self.assertEqual(result.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")
        return result


class PreflightApiTests(PreflightBehaviorCase):
    def test_preflight_import_has_the_exact_approved_signature(self):
        try:
            module = importlib.import_module("joy_m2.ingest.preflight")
        except ModuleNotFoundError as exc:
            self.fail(f"approved preflight module is missing: {exc}")
        function = getattr(module, "preflight_import", None)
        self.assertIsNotNone(function, "preflight_import must exist")
        signature = inspect.signature(function)
        self.assertEqual(tuple(signature.parameters), ("manifest", "package_root", "baseline_database"))
        self.assertEqual(
            tuple(parameter.annotation for parameter in signature.parameters.values()),
            (BatchImportManifest, Path, ArtifactRef),
        )
        self.assertIs(signature.return_annotation, ImportPreflightResult)


class ConsumptionBoundaryRedTests(PreflightBehaviorCase):
    def _assert_structured_file_integrity_issue(
        self,
        manifest: BatchImportManifest,
        root: Path,
        expected_evidence: dict[str, object],
        case_name: str,
    ) -> None:
        try:
            result = preflight_import(manifest, root, _baseline_ref())
        except PipelineError as exc:
            boundary = (
                "hybrid C6 stop still satisfies PipelineError"
                if isinstance(exc, NotImplementedError)
                else "current production still exposes a PipelineError boundary"
            )
            self.fail(
                f"{case_name} expected a structured file_integrity_mismatch "
                f"result, but {boundary}: {exc}"
            )
        except NotImplementedError as exc:
            self.fail(
                f"{case_name} reached the approved C6-only stop, but C6 "
                f"formal result closure is not implemented: {exc}"
            )
        self.assertIs(type(result), ImportPreflightResult)
        integrity_issues = tuple(
            issue for issue in result.issues if issue.code == "file_integrity_mismatch"
        )
        self.assertEqual(len(integrity_issues), 1)
        issue = integrity_issues[0]
        self.assertEqual(
            (issue.severity, issue.field, issue.proposed_question_id),
            ("blocking", "file_integrity", None),
        )
        self.assertEqual(
            issue.evidence,
            json.dumps(
                expected_evidence,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )

    def test_v119_and_exact_manifest_type_are_rechecked_before_any_io(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            valid = _package(root)
            baseline = _baseline_ref()
            invalid: list[object] = []
            for target in ("V1.18", "V1.17", "V9.99", None, ""):
                value = replace(valid)
                object.__setattr__(value, "target_release_version", target)
                invalid.append(value)
            invalid.extend((None, object(), {"target_release_version": "V1.19"}))
            for value in invalid:
                with self.subTest(value=value), mock.patch.object(Path, "open") as path_open, mock.patch.object(
                    Path, "read_bytes"
                ) as read_bytes, mock.patch("sqlite3.connect") as connect:
                    self._rejected(value, root, baseline)
                    path_open.assert_not_called()
                    read_bytes.assert_not_called()
                    connect.assert_not_called()

    def test_preflight_rechecks_missing_consumed_package_file_as_pipeline_error(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = _package(root)
            candidate_path = root / manifest.candidate_records[0].relative_path
            candidate_path.unlink()
            self._rejected(manifest, root)

    def test_preflight_readable_size_mismatch_expects_structured_integrity_blocker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = _package(root)
            evidence = manifest.candidate_records[0]
            candidate_path = root / evidence.relative_path
            actual_bytes = candidate_path.read_bytes()
            actual_sha256 = _sha(actual_bytes)
            self.assertEqual(actual_sha256, evidence.sha256)
            object.__setattr__(evidence, "size_bytes", len(actual_bytes) + 1)
            self.assertNotEqual(evidence.size_bytes, len(actual_bytes))
            self._assert_structured_file_integrity_issue(
                manifest,
                root,
                {
                    "relative_path": evidence.relative_path,
                    "expected_sha256": evidence.sha256,
                    "actual_sha256": actual_sha256,
                    "expected_size_bytes": evidence.size_bytes,
                    "actual_size_bytes": len(actual_bytes),
                },
                "readable size-only mismatch",
            )

    def test_preflight_readable_sha_mismatch_expects_structured_integrity_blocker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = _package(root)
            evidence = manifest.candidate_records[0]
            candidate_path = root / evidence.relative_path
            original_bytes = candidate_path.read_bytes()
            actual_bytes = bytes([original_bytes[0] ^ 1]) + original_bytes[1:]
            self.assertEqual(len(actual_bytes), evidence.size_bytes)
            self.assertNotEqual(_sha(actual_bytes), evidence.sha256)
            candidate_path.write_bytes(actual_bytes)
            self._assert_structured_file_integrity_issue(
                manifest,
                root,
                {
                    "relative_path": evidence.relative_path,
                    "expected_sha256": evidence.sha256,
                    "actual_sha256": _sha(actual_bytes),
                    "expected_size_bytes": evidence.size_bytes,
                    "actual_size_bytes": len(actual_bytes),
                },
                "readable SHA-only mismatch",
            )

    def test_preflight_rejects_an_unreadable_declared_file(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = _package(root)
            baseline = _baseline_ref()
            candidate_path = (root / manifest.candidate_records[0].relative_path).resolve()
            original_open = Path.open

            def guarded_open(path: Path, *args: object, **kwargs: object):
                if path.resolve() == candidate_path:
                    raise PermissionError("controlled unreadable candidate")
                return original_open(path, *args, **kwargs)

            with mock.patch.object(Path, "open", guarded_open):
                self._rejected(manifest, root, baseline)

    def test_package_root_requires_a_real_directory_path_without_coercion(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = _package(root)
            file_path = root / "not-a-directory"
            file_path.write_text("x", encoding="utf-8")
            for invalid in (str(root), None, object(), root / "missing", file_path):
                with self.subTest(invalid=invalid):
                    self._rejected(manifest, invalid)

    def test_absolute_parent_normalization_and_symlink_escapes_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside_directory:
            root = Path(directory)
            outside = Path(outside_directory) / "outside.json"
            outside.write_bytes(b"[]\n")
            for invalid_path in (str(outside), "../outside.json", "records/../../outside.json"):
                with self.subTest(path=invalid_path):
                    manifest = _package(root)
                    evidence = manifest.candidate_records[0]
                    object.__setattr__(evidence, "relative_path", invalid_path)
                    self._rejected(manifest, root)
            link = root / "records/link.json"
            link.parent.mkdir(parents=True, exist_ok=True)
            link.symlink_to(outside)
            manifest = _package(root)
            evidence = manifest.candidate_records[0]
            object.__setattr__(evidence, "relative_path", "records/link.json")
            object.__setattr__(evidence, "sha256", _sha(outside.read_bytes()))
            object.__setattr__(evidence, "size_bytes", outside.stat().st_size)
            self._rejected(manifest, root)


class PathAndBaselineRedTests(PreflightBehaviorCase):
    def test_absolute_package_root_contaminates_no_authority_or_approval_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            result = self._result(_package(root), root)
            root_text = str(root)
            authority = (
                result.manifest,
                result.candidates,
                result.issues,
                result.report,
                (result.report.batch_id, result.report.preflight_sha256, result.report.target_release_version),
            )
            for value in authority:
                self.assertNotIn(root_text, repr(value))

    def test_equivalent_packages_under_different_roots_have_identical_authority(self):
        with tempfile.TemporaryDirectory() as first_directory, tempfile.TemporaryDirectory() as second_directory:
            first_root, second_root = Path(first_directory) / "package", Path(second_directory) / "package"
            first_root.mkdir()
            second_root.mkdir()
            first_baseline = Path(first_directory) / "baseline.sqlite3"
            second_baseline = Path(second_directory) / "baseline.sqlite3"
            shutil.copy2(BASELINE_PATH, first_baseline)
            shutil.copy2(BASELINE_PATH, second_baseline)
            first = self._result(_package(first_root), first_root, _baseline_ref(first_baseline))
            second = self._result(_package(second_root), second_root, _baseline_ref(second_baseline))
            self.assertEqual(first.manifest, second.manifest)
            self.assertEqual(first.candidates, second.candidates)
            self.assertEqual(first.issues, second.issues)
            self.assertEqual(first.report, second.report)
            self.assertEqual(first.report.preflight_sha256, second.report.preflight_sha256)
            self.assertNotEqual(first.baseline_database.path, second.baseline_database.path)
            self.assertNotIn(str(first.baseline_database.path), repr(first.report))
            self.assertNotIn(str(second.baseline_database.path), repr(second.report))

    def test_baseline_artifact_identity_bytes_metadata_integrity_fk_and_order_are_required(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = _package(root)
            good = _baseline_ref()
            mutations: list[ArtifactRef] = []
            for field, value in (("sha256", "0" * 64), ("size_bytes", 1), ("kind", "json")):
                ref = replace(good)
                object.__setattr__(ref, field, value)
                mutations.append(ref)
            for sql in (
                "update release_metadata_v2 set value='V9.99' where key='release_version'",
                "update release_metadata_v2 set value='wrong-schema' where key='schema_version'",
                "delete from complete_questions_v2 where source_order=497",
                "update complete_questions_v2 set source_order=9999 where source_order=497",
                "update complete_question_tags_v2 set question_id='missing' where rowid=(select min(rowid) from complete_question_tags_v2)",
            ):
                copy = root / f"baseline-{len(mutations)}.sqlite3"
                shutil.copy2(BASELINE_PATH, copy)
                connection = sqlite3.connect(copy)
                connection.execute(sql)
                connection.commit()
                connection.close()
                mutations.append(_baseline_ref(copy))
            for baseline in mutations:
                with self.subTest(baseline=baseline):
                    self._rejected(manifest, root, baseline)

    def test_baseline_sqlite_is_opened_only_with_read_only_uri_mode(self):
        original_connect = sqlite3.connect
        calls: list[tuple[object, dict[str, object]]] = []

        def recording_connect(database: object, *args: object, **kwargs: object):
            calls.append((database, dict(kwargs)))
            return original_connect(database, *args, **kwargs)

        with tempfile.TemporaryDirectory() as directory, mock.patch("sqlite3.connect", side_effect=recording_connect):
            root = Path(directory)
            self._result(_package(root), root, _baseline_ref())
        self.assertTrue(calls)
        for database, kwargs in calls:
            self.assertIn("mode=ro", str(database))
            self.assertIs(kwargs.get("uri"), True)

    def test_baseline_database_requires_the_exact_artifactref_runtime_type(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            self._rejected(_package(root), root, {"path": str(BASELINE_PATH)})


class ManifestCandidateAndProvenanceRedTests(PreflightBehaviorCase):
    def test_manifest_digest_matches_literal_oracle_and_all_semantic_mutations_change_it(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = _literal_package(root)
            self.assertEqual(_manifest_digest(manifest), MANIFEST_SHA256)
            result = self._result(manifest, root)
            self.assertEqual(result.report.manifest_sha256, MANIFEST_SHA256)
            projection = _manifest_projection(manifest)
            original = _sha(canonical_json_bytes(projection) + b"\n")
            mutations = []
            for field, value in (("target_release_version", "V1.20"), ("answer_policy", "changed")):
                changed = json.loads(json.dumps(projection))
                changed[field] = value
                mutations.append(changed)
            for field, value in (("relative_path", "records/other.json"), ("sha256", "0" * 64), ("size_bytes", 1), ("kind", "source")):
                changed = json.loads(json.dumps(projection))
                changed["candidate_records"][0][field] = value
                mutations.append(changed)
            two_entry = json.loads(json.dumps(projection))
            other_entry = dict(two_entry["candidate_records"][0])
            other_entry["relative_path"] = "records/second.json"
            other_entry["sha256"] = "9" * 64
            two_entry["candidate_records"].append(other_entry)
            reordered = json.loads(json.dumps(two_entry))
            reordered["candidate_records"].reverse()
            self.assertNotEqual(
                _sha(canonical_json_bytes(two_entry) + b"\n"),
                _sha(canonical_json_bytes(reordered) + b"\n"),
            )
            for mutation in mutations:
                self.assertNotEqual(_sha(canonical_json_bytes(mutation) + b"\n"), original)

    def test_candidate_json_parsing_accepts_only_exact_canonical_record_objects(self):
        invalid_records: tuple[object, ...] = (
            "{",
            {"not": "an array"},
            [dict(_raw_candidate(), proposed_question_id=None)],
            [{key: value for key, value in _raw_candidate().items() if key != "source_id"}],
            [dict(_raw_candidate(), unsupported_field=True)],
        )
        for payload in invalid_records:
            with self.subTest(payload=payload), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                manifest = _package(root)
                path = root / manifest.candidate_records[0].relative_path
                data = payload.encode() if isinstance(payload, str) else canonical_json_bytes(payload) + b"\n"
                path.write_bytes(data)
                evidence = manifest.candidate_records[0]
                object.__setattr__(evidence, "sha256", _sha(data))
                object.__setattr__(evidence, "size_bytes", len(data))
                result = self._result(manifest, root)
                self.assertEqual(result.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")
                self.assertTrue(result.report.blocking_errors)

    def test_candidate_exact_types_status_payloads_and_enrichment_disclosures_are_enforced(self):
        invalid = (
            {"source_fragment_hash": True}, {"question_text_original": ""},
            {"difficulty_level": True}, {"difficulty_level": 6},
            {"translation_status": "unknown"},
            {"translation_status": "missing", "question_text_zh": "not missing", "translation_evidence": None},
            {"translation_status": "ai_proposed", "translation_evidence": "source:source/source.txt#fake"},
            {"explanation_status": "missing", "explanation_text": "not missing", "explanation_evidence": None},
            {"answer_status": "missing_from_source", "solution_original": "fabricated"},
            {"tags": ["tag"], "tag_status": "missing"},
            {"difficulty_level": None, "difficulty_status": "source_provided"},
            {"image_paths": ["images/a.png"], "image_roles": []},
            {"enrichment_status": "unknown"},
        )
        for changes in invalid:
            with self.subTest(changes=changes):
                result = self._blocked([_raw_candidate(**changes)])
                self.assertTrue(result.report.blocking_errors)

    def test_duplicate_proposed_ids_are_not_silently_deduplicated(self):
        records = [_raw_candidate(proposed_question_id="SAME"), _raw_candidate(proposed_question_id="SAME", question_text_original="different")]
        result = self._blocked(records)
        self.assertEqual(len(result.candidates), 2)
        self.assertIn("collision_candidate_id", tuple(issue.code for issue in result.issues))

    def test_missing_orphan_images_and_unknown_taxonomy_are_blockers(self):
        missing = self._blocked([_raw_candidate(image_paths=["images/missing.png"], image_roles=["question"])])
        self.assertIn("images/missing.png", missing.report.missing_images)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            orphan = self._result(_package(root, images={"images/orphan.png": b"orphan"}), root)
        self.assertIn("images/orphan.png", orphan.report.orphan_images)
        self.assertEqual(orphan.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")
        for changes in ({"primary_type": "unknown-primary"}, {"tags": ["unknown-tag"], "tag_status": "source_provided"}):
            with self.subTest(changes=changes):
                self.assertEqual(self._blocked([_raw_candidate(**changes)]).report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")

    def test_missing_images_preserve_candidate_semantic_order_not_issue_order(self):
        records = [
            _raw_candidate(
                proposed_question_id="Z-CANDIDATE",
                question_text_original="Unique Z candidate.",
                source_fragment_hash="2" * 64,
                image_paths=["images/z.png"],
                image_roles=["question"],
            ),
            _raw_candidate(
                proposed_question_id="A-CANDIDATE",
                question_text_original="Unique A candidate.",
                source_fragment_hash="3" * 64,
                image_paths=["images/a.png"],
                image_roles=["question"],
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = _package(
                root,
                record_groups=(("records/candidates.json", records),),
            )
            result = preflight_import(manifest, root, _baseline_ref())

        self.assertEqual(
            tuple(issue.code for issue in result.issues),
            ("missing_image", "missing_image"),
        )
        issue_keys = tuple(
            (
                issue.proposed_question_id or "",
                issue.code,
                issue.field,
                issue.evidence,
            )
            for issue in result.issues
        )
        self.assertEqual(issue_keys, tuple(sorted(issue_keys)))
        self.assertEqual(
            result.report.missing_images,
            ("images/z.png", "images/a.png"),
        )

    def test_normalized_original_text_and_digest_use_the_exact_frozen_algorithm(self):
        record = _raw_candidate(question_text_original="  Solve   x + 1 = 2.\r\nShow work.  ")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self._result(_package(root, record_groups=(("records/candidates.json", [record]),)), root)
        self.assertEqual(result.candidates[0].question_text_original, record["question_text_original"])
        self.assertEqual(result.candidates[0].normalized_text_sha256, NORMALIZED_SHA256)
        self.assertEqual(_sha(NORMALIZED_TEXT.encode("utf-8")), NORMALIZED_SHA256)
        self.assertNotEqual(NORMALIZED_SHA256, REFERENCE_TEXT_SHA256)

    def test_candidate_order_is_manifest_then_record_order_not_discovery_order(self):
        q1 = _raw_candidate(proposed_question_id="Q1", question_text_original="one")
        q2 = _raw_candidate(proposed_question_id="Q2", question_text_original="two")
        q3 = _raw_candidate(proposed_question_id="Q3", question_text_original="three")
        groups = (("records/z.json", [q3]), ("records/a.json", [q1, q2]))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self._result(_package(root, record_groups=groups), root)
            self.assertEqual(tuple(item.proposed_question_id for item in result.candidates), ("Q3", "Q1", "Q2"))
            reordered = self._result(_package(root, record_groups=tuple(reversed(groups))), root)
            self.assertEqual(tuple(item.proposed_question_id for item in reordered.candidates), ("Q1", "Q2", "Q3"))
            self.assertNotEqual(result.report.preflight_sha256, reordered.report.preflight_sha256)

    def test_translation_provenance_accepts_four_statuses_and_rejects_false_source_authority(self):
        payloads = (
            ("source_present", "来源译文", "source:source/source.txt#translation"),
            ("ai_proposed", "AI 译文", "ai-proposal-sha256:" + _sha("AI 译文".encode())),
            ("verified", "核验译文", "verified-review-sha256:" + "2" * 64),
            ("missing", "", None),
        )
        for status, text, evidence in payloads:
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                record = _raw_candidate(question_text_zh=text, translation_status=status, translation_evidence=evidence)
                result = self._result(_package(root, record_groups=(("records/candidates.json", [record]),)), root)
                self.assertEqual(result.candidates[0].translation_status, status)
        self._blocked([_raw_candidate(question_text_zh="AI", translation_status="source_present", translation_evidence="ai-proposal-sha256:" + _sha(b"AI"))])

    def test_explanation_provenance_is_independent_from_solution_and_uses_four_statuses(self):
        payloads = (
            ("source_present", "source explanation", "source:source/source.txt#explanation"),
            ("ai_proposed", "AI explanation", "ai-proposal-sha256:" + _sha(b"AI explanation")),
            ("verified", "verified explanation", "verified-review-sha256:" + "3" * 64),
            ("missing", "", None),
        )
        for status, text, evidence in payloads:
            with self.subTest(status=status), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                record = _raw_candidate(explanation_text=text, explanation_status=status, explanation_evidence=evidence)
                result = self._result(_package(root, record_groups=(("records/candidates.json", [record]),)), root)
                self.assertEqual(result.candidates[0].explanation_status, status)
                self.assertEqual(result.candidates[0].solution_original, "x = 1")

    def test_missing_from_source_retains_empty_answers_and_never_fabricates_explanation(self):
        record = _raw_candidate(
            answer_status="missing_from_source", solution_original="", solution_verified="",
            explanation_text="", explanation_status="missing", explanation_evidence=None,
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self._result(_package(root, record_groups=(("records/candidates.json", [record]),)), root)
        candidate = result.candidates[0]
        self.assertEqual((candidate.solution_original, candidate.solution_verified), ("", ""))
        self.assertEqual((candidate.explanation_text, candidate.explanation_evidence), ("", None))
        self.assertIn(candidate.proposed_question_id, result.report.missing_answers)


class DuplicateAdaptationAndImageRedTests(PreflightBehaviorCase):
    @staticmethod
    def _reference_record(**overrides: object) -> dict[str, object]:
        values: dict[str, object] = {
            "proposed_question_id": "TASK9-CANDIDATE",
            "source_id": REFERENCE_SOURCE_ID,
            "source_question_number": REFERENCE_NUMBER,
            "source_section": REFERENCE_SECTION,
            "source_fragment_hash": REFERENCE_FRAGMENT,
            "question_text_original": REFERENCE_TEXT,
            "primary_type": "切线与法线",
        }
        values.update(overrides)
        return _raw_candidate(**values)

    def test_clean_exact_duplicate_emits_only_duplicate_exact_and_no_adaptation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self._result(_package(root, record_groups=(("records/candidates.json", [self._reference_record()]),)), root)
        self.assertEqual(tuple(issue.code for issue in result.issues), ("duplicate_exact",))
        self.assertEqual(result.report.adaptations, ())
        self.assertEqual((result.report.duplicate_count, result.report.rejected_count), (1, 0))

    def test_candidate_id_collision_invalidates_adaptation_and_blocks(self):
        record = self._reference_record(proposed_question_id=REFERENCE_ID, question_text_original="adapted text")
        result = self._blocked([record])
        self.assertIn("collision_candidate_id", tuple(issue.code for issue in result.issues))
        self.assertEqual(result.report.adaptations, ())
        self.assertEqual(result.report.rejected_count, 1)

    def test_source_fragment_and_normalized_text_collisions_are_independently_reported(self):
        cases = (
            self._reference_record(source_fragment_hash="4" * 64, question_text_original="different"),
            self._reference_record(source_id="OTHER", source_question_number="2", source_section="Other", question_text_original="different"),
            self._reference_record(source_id="OTHER", source_question_number="2", source_section="Other", source_fragment_hash="5" * 64),
        )
        expected = ("collision_source_locator", "collision_fragment_sha256", "collision_normalized_text_sha256")
        for record, code in zip(cases, expected):
            with self.subTest(code=code):
                result = self._blocked([record])
                self.assertIn(code, tuple(issue.code for issue in result.issues))

    def test_competing_reference_signals_are_ambiguous_rejected_and_have_sorted_evidence(self):
        record = self._reference_record(
            source_id=IMAGE_SOURCE_ID,
            source_question_number=IMAGE_NUMBER,
            source_section=IMAGE_SECTION,
            source_fragment_hash=REFERENCE_FRAGMENT,
        )
        result = self._blocked([record])
        self.assertEqual(tuple(issue.code for issue in result.issues), ("duplicate_ambiguous",))
        self.assertEqual(result.report.adaptations, ())
        self.assertEqual((result.report.ambiguous_count, result.report.rejected_count), (1, 1))
        matches = json.loads(result.issues[0].evidence)["matches"]
        self.assertEqual(matches, sorted(matches, key=lambda value: value["reference_question_id"]))

    def test_duplicate_id_does_not_spread_ambiguity_to_other_candidate_occurrence(self):
        records = [
            _raw_candidate(
                proposed_question_id="SAME",
                question_text_original="Unique first occurrence.",
                source_fragment_hash="2" * 64,
            ),
            _raw_candidate(
                proposed_question_id="SAME",
                source_id=IMAGE_SOURCE_ID,
                source_question_number=IMAGE_NUMBER,
                source_section=IMAGE_SECTION,
                source_fragment_hash=REFERENCE_FRAGMENT,
                question_text_original="Unique ambiguous second occurrence.",
            ),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = _package(
                root,
                record_groups=(("records/candidates.json", records),),
            )
            try:
                result = preflight_import(manifest, root, _baseline_ref())
            except PipelineError as exc:
                self.fail(
                    "duplicate-ID ambiguity must return a structured "
                    f"ImportPreflightResult, not raise PipelineError: {exc}"
                )

        self.assertIs(type(result), ImportPreflightResult)
        self.assertEqual(
            tuple(candidate.question_text_original for candidate in result.candidates),
            (
                "Unique first occurrence.",
                "Unique ambiguous second occurrence.",
            ),
        )
        self.assertEqual(result.report.proposed_ids, ("SAME", "SAME"))
        self.assertEqual(
            (
                result.report.detected_count,
                result.report.new_candidate_count,
                result.report.duplicate_count,
                result.report.rejected_count,
                result.report.ambiguous_count,
            ),
            (2, 1, 0, 1, 1),
        )
        self.assertEqual(result.report.ambiguous_splits, ("SAME",))
        self.assertEqual(
            tuple(issue.code for issue in result.issues),
            ("duplicate_ambiguous",),
        )

    def test_adaptation_only_is_new_ready_and_has_no_issue_or_warning(self):
        record = self._reference_record(question_text_original="Adapted presentation of the same source.")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self._result(_package(root, record_groups=(("records/candidates.json", [record]),)), root)
        self.assertEqual(result.issues, ())
        self.assertEqual(result.report.warnings, ())
        self.assertEqual(len(result.report.adaptations), 1)
        adaptation = result.report.adaptations[0]
        self.assertEqual(adaptation.reference_question_id, REFERENCE_ID)
        self.assertEqual(adaptation.adaptation_kind, "adapted")
        self.assertEqual(adaptation.reason, "stable_source_identity_matches_with_transformed_text")
        self.assertEqual(
            adaptation.evidence,
            "matched=source_locator+source_fragment_hash;"
            f"candidate_normalized_text_sha256={_sha(b'Adapted presentation of the same source.')};"
            f"reference_normalized_text_sha256={REFERENCE_TEXT_SHA256}",
        )
        self.assertEqual(result.report.status, "READY FOR USER IMPORT APPROVAL")
        self.assertEqual((result.report.new_candidate_count, result.report.rejected_count), (1, 0))

    def test_adaptation_and_independent_image_sha_blocker_coexist_and_block(self):
        image_bytes = b"different image bytes"
        record = _raw_candidate(
            proposed_question_id="TASK9-IMAGE-ADAPT",
            source_id=IMAGE_SOURCE_ID,
            source_question_number=IMAGE_NUMBER,
            source_section=IMAGE_SECTION,
            source_fragment_hash=IMAGE_FRAGMENT,
            question_text_original="Adapted image question text.",
            image_paths=[IMAGE_PATH], image_roles=[IMAGE_ROLE],
            primary_type="变率",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self._result(
                _package(root, record_groups=(("records/candidates.json", [record]),), images={IMAGE_PATH: image_bytes}),
                root,
            )
        self.assertEqual(len(result.report.adaptations), 1)
        self.assertIn("collision_image_sha256", tuple(issue.code for issue in result.issues))
        self.assertEqual((result.report.new_candidate_count, result.report.rejected_count), (0, 1))
        self.assertEqual(result.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")

    def test_adaptation_is_invalidated_by_id_or_competing_reference_and_exact_duplicate(self):
        cases = (
            self._reference_record(proposed_question_id=REFERENCE_ID, question_text_original="adapted"),
            self._reference_record(source_id=IMAGE_SOURCE_ID, source_question_number=IMAGE_NUMBER, source_section=IMAGE_SECTION, question_text_original="adapted"),
            self._reference_record(),
        )
        for record in cases:
            with self.subTest(record=record):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    result = self._result(_package(root, record_groups=(("records/candidates.json", [record]),)), root)
                self.assertEqual(result.report.adaptations, ())

    def test_exact_duplicate_plus_independent_id_blocker_is_rejected_but_retains_duplicate(self):
        record = self._reference_record(proposed_question_id=IMAGE_REFERENCE_ID)
        result = self._blocked([record])
        codes = tuple(issue.code for issue in result.issues)
        self.assertIn("duplicate_exact", codes)
        self.assertIn("collision_candidate_id", codes)
        self.assertEqual((result.report.duplicate_count, result.report.rejected_count), (0, 1))

    def test_image_identity_uses_path_role_sha_while_size_is_integrity_only(self):
        legacy_image = ROOT / "legacy/task5_work/v116/m2_question_bank/assets/m2qd_differentiation/M2QD_DA_PARTB_Q4_Figure1.jpg"
        matching_bytes = legacy_image.read_bytes()
        self.assertEqual(_sha(matching_bytes), IMAGE_SHA256)
        base = _raw_candidate(
            proposed_question_id="TASK9-IMAGE",
            source_id="OTHER", source_question_number="IMAGE", source_section="Other",
            source_fragment_hash="6" * 64, question_text_original="Unique image candidate.",
            image_paths=[IMAGE_PATH], image_roles=[IMAGE_ROLE], primary_type="变率",
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            same = self._result(_package(root, record_groups=(("records/candidates.json", [base]),), images={IMAGE_PATH: matching_bytes}), root)
            self.assertNotIn("collision_image_sha256", tuple(issue.code for issue in same.issues))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            different = self._result(_package(root, record_groups=(("records/candidates.json", [base]),), images={IMAGE_PATH: b"different"}), root)
            self.assertIn("collision_image_sha256", tuple(issue.code for issue in different.issues))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = _package(root, record_groups=(("records/candidates.json", [base]),), images={IMAGE_PATH: matching_bytes})
            evidence = manifest.image_files[0]
            object.__setattr__(evidence, "size_bytes", evidence.size_bytes + 1)
            result = self._result(manifest, root)
            self.assertNotIn("collision_image_sha256", tuple(issue.code for issue in result.issues))
            self.assertEqual(result.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")


class ClosureDigestAndZeroWriteRedTests(PreflightBehaviorCase):
    def test_counts_are_mutually_exclusive_and_close_with_adaptations_not_added(self):
        records = [
            _raw_candidate(proposed_question_id="NEW"),
            DuplicateAdaptationAndImageRedTests._reference_record(proposed_question_id="DUP"),
            _raw_candidate(proposed_question_id=REFERENCE_ID, question_text_original="collision"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self._result(_package(root, record_groups=(("records/candidates.json", records),)), root)
        report = result.report
        self.assertEqual(report.detected_count, report.new_candidate_count + report.duplicate_count + report.rejected_count)
        self.assertEqual(report.projected_after_count, 497 + report.new_candidate_count)
        self.assertEqual(report.detected_count, 3)

    def test_ready_and_blocked_status_follow_only_blocker_closure(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            ready = self._result(_package(root), root)
        self.assertEqual(ready.report.status, "READY FOR USER IMPORT APPROVAL")
        blocked = self._blocked([_raw_candidate(proposed_question_id=REFERENCE_ID)])
        self.assertEqual(blocked.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")

    def test_issue_and_adaptation_ordering_are_exact_and_deterministic(self):
        records = [
            _raw_candidate(proposed_question_id=IMAGE_REFERENCE_ID, question_text_original="z"),
            DuplicateAdaptationAndImageRedTests._reference_record(proposed_question_id="ADAPT", question_text_original="adapted"),
            _raw_candidate(proposed_question_id=REFERENCE_ID, question_text_original="a"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            result = self._result(_package(root, record_groups=(("records/candidates.json", records),)), root)
        issue_keys = tuple((issue.proposed_question_id or "", issue.code, issue.field, issue.evidence) for issue in result.issues)
        adaptation_keys = tuple((item.candidate_id, item.reference_question_id, item.adaptation_kind, item.evidence, item.reason) for item in result.report.adaptations)
        self.assertEqual(issue_keys, tuple(sorted(issue_keys)))
        self.assertEqual(adaptation_keys, tuple(sorted(adaptation_keys)))

    def test_independent_literal_oracle_locks_all_12_keys_issues_and_image_evidence(self):
        expected_payload = _literal_digest_payload()
        self.assertEqual(
            tuple(expected_payload),
            (
                "schema", "batch_id", "target_release_version", "baseline",
                "manifest_policies", "candidate_record_order", "file_evidence",
                "candidates", "issues", "duplicate_classifications",
                "image_evidence", "report",
            ),
        )
        self.assertEqual(_sha(canonical_json_bytes(expected_payload) + b"\n"), PREFLIGHT_SHA256)
        for removed in ("issues", "image_evidence"):
            mutation = dict(expected_payload)
            mutation.pop(removed)
            self.assertNotEqual(_sha(canonical_json_bytes(mutation) + b"\n"), PREFLIGHT_SHA256)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest = _literal_package(root)
            result = self._result(manifest, root)
        self.assertEqual(result.report.manifest_sha256, MANIFEST_SHA256)
        self.assertEqual(result.report.preflight_sha256, PREFLIGHT_SHA256)
        self.assertEqual(tuple(issue.code for issue in result.issues), ("duplicate_exact",))
        self.assertEqual(result.candidates[0].image_paths, ("images/diagram.png",))
        self.assertEqual(len(result.report.adaptations), 1)

    def test_digest_changes_for_candidate_provenance_adaptation_count_and_baseline_mutations(self):
        variants = (
            {},
            {"question_text_zh": "changed translation"},
            {"translation_status": "verified", "translation_evidence": "verified-review-sha256:" + "7" * 64},
            {"explanation_text": "changed explanation"},
            {"explanation_status": "verified", "explanation_evidence": "verified-review-sha256:" + "8" * 64},
            {"question_text_original": "changed candidate authority"},
        )
        digests = []
        for overrides in variants:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                result = self._result(_package(root, record_groups=(("records/candidates.json", [_raw_candidate(**overrides)]),)), root)
                digests.append(result.report.preflight_sha256)
        self.assertEqual(len(digests), len(set(digests)))

    def test_unsupported_mmd_mmd_zip_and_pdf_are_blockers(self):
        for suffix in ("input.mmd", "input.mmd.zip", "input.pdf"):
            with self.subTest(suffix=suffix), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                manifest = _package(root, source_path=f"source/{suffix}")
                result = self._result(manifest, root)
                self.assertIn(f"source/{suffix}", result.report.unsupported_files)
                self.assertEqual(result.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")

    def test_preflight_preserves_existing_v119_state_and_creates_no_formal_release(self):
        protected = (ROOT / "data", ROOT / "releases", ROOT / "legacy")
        before = tuple(_tree_fingerprint(path) for path in protected)
        candidate_root = ROOT / "data/staging/task9c-v119-candidate"
        candidate_existed = candidate_root.exists()
        candidate_before = _tree_fingerprint(candidate_root)
        formal_v119 = ROOT / "releases/V1.19"
        self.assertFalse(formal_v119.exists() or formal_v119.is_symlink())
        baseline_before = _sha(BASELINE_PATH.read_bytes())
        try:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                result = preflight_import(_package(root), root, _baseline_ref())
        except NotImplementedError as exc:
            result = None
            missing = exc
        else:
            missing = None
        self.assertEqual(tuple(_tree_fingerprint(path) for path in protected), before)
        self.assertEqual(candidate_root.exists(), candidate_existed)
        self.assertEqual(_tree_fingerprint(candidate_root), candidate_before)
        self.assertFalse(formal_v119.exists() or formal_v119.is_symlink())
        self.assertEqual(_sha(BASELINE_PATH.read_bytes()), baseline_before)
        self.assertEqual(sqlite3.connect(BASELINE_PATH).execute("select count(*) from complete_questions_v2").fetchone()[0], 497)
        if missing is not None:
            self.fail(f"approved zero-write preflight behavior is not implemented: {missing!r}")
        self.assertIs(type(result), ImportPreflightResult)


if __name__ == "__main__":
    unittest.main()
