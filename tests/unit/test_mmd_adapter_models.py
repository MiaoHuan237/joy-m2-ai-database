from __future__ import annotations

import importlib
import importlib.util
import json
from dataclasses import MISSING, FrozenInstanceError, fields, is_dataclass
from pathlib import Path, PurePosixPath
import sys
import unittest
from typing import get_type_hints


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.errors import InputFormatError, PipelineError
from joy_m2.ingest.models import BatchImportManifest


MODULE_NAME = "joy_m2.ingest.adapter_models"
HEX_A = "a" * 64
HEX_B = "b" * 64
ISSUE_CODES = (
    "source_contract_mismatch",
    "unsupported_source_format",
    "archive_integrity_invalid",
    "archive_member_unsafe",
    "mmd_parse_failed",
    "selection_not_unique",
    "candidate_count_mismatch",
    "language_mapping_ambiguous",
    "image_binding_invalid",
)
BLOCKED_MESSAGE = "MMD adapter blocked by source diagnostics"


def adapter_models(test_case: unittest.TestCase):
    spec = importlib.util.find_spec(MODULE_NAME)
    test_case.assertIsNotNone(
        spec,
        "Task 9B adapter_models module must exist before public contracts can pass",
    )
    return importlib.import_module(MODULE_NAME)


def selection(module, **overrides):
    values = dict(
        proposed_question_id="M2-NEW-001",
        kind="example",
        number="1",
        source_section="例題",
        language_layout="english_then_chinese",
        answer_mapping="source_answer",
        answer_number=None,
        expected_image_members=["images/vector.jpg"],
        primary_type="向量",
        tags=["vector", "geometry"],
        tag_status="source_provided",
        difficulty_level=2,
        difficulty_status="source_provided",
    )
    values.update(overrides)
    return module.MmdSelection(**values)


def adapter_manifest(module, **overrides):
    values = dict(
        schema_version="task9b-mmd-adapter-v1",
        batch_id="batch-mmd-001",
        source_kind="mmd_zip",
        source_sha256=HEX_A,
        primary_member="source/main.mmd",
        answer_member=None,
        source_id="MATHPIX-M2-VECTORS",
        chapter="向量及其应用",
        expected_candidate_count=1,
        selections=[selection(module)],
    )
    values.update(overrides)
    return module.MmdAdapterManifest(**values)


def batch_manifest() -> BatchImportManifest:
    return BatchImportManifest(
        schema_version="task9-import-manifest-v1",
        batch_id="batch-mmd-001",
        project="Joy M2 AI Database",
        module="M2",
        chapter="向量及其应用",
        target_release_version="V1.19",
        candidate_records=(),
        source_files=(),
        answer_files=(),
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


def issue(module, **overrides):
    values = dict(
        code="source_contract_mismatch",
        severity="blocking",
        proposed_question_id=None,
        source_locator="",
        field="$.source_kind",
        evidence='{"actual":"mmd","expected":"mmd_zip","reason":"invalid_value"}',
    )
    values.update(overrides)
    return module.MmdAdapterIssue(**values)


class MmdAdapterPublicContractTests(unittest.TestCase):
    def test_exact_dataclass_fields_type_hints_no_defaults_and_frozen(self):
        module = adapter_models(self)
        expected = {
            module.MmdSelection: (
                (
                    "proposed_question_id", "kind", "number", "source_section",
                    "language_layout", "answer_mapping", "answer_number",
                    "expected_image_members", "primary_type", "tags", "tag_status",
                    "difficulty_level", "difficulty_status",
                ),
                {
                    "proposed_question_id": str,
                    "kind": str,
                    "number": str,
                    "source_section": str,
                    "language_layout": str,
                    "answer_mapping": str,
                    "answer_number": str | None,
                    "expected_image_members": tuple[str, ...],
                    "primary_type": str,
                    "tags": tuple[str, ...],
                    "tag_status": str,
                    "difficulty_level": int | None,
                    "difficulty_status": str,
                },
            ),
            module.MmdAdapterManifest: (
                (
                    "schema_version", "batch_id", "source_kind", "source_sha256",
                    "primary_member", "answer_member", "source_id", "chapter",
                    "expected_candidate_count", "selections",
                ),
                {
                    "schema_version": str,
                    "batch_id": str,
                    "source_kind": str,
                    "source_sha256": str,
                    "primary_member": str,
                    "answer_member": str | None,
                    "source_id": str,
                    "chapter": str,
                    "expected_candidate_count": int,
                    "selections": tuple[module.MmdSelection, ...],
                },
            ),
            module.AdaptedImportPackage: (
                ("package_root", "manifest_path", "manifest"),
                {
                    "package_root": Path,
                    "manifest_path": Path,
                    "manifest": BatchImportManifest,
                },
            ),
            module.MmdAdapterIssue: (
                (
                    "code", "severity", "proposed_question_id", "source_locator",
                    "field", "evidence",
                ),
                {
                    "code": str,
                    "severity": str,
                    "proposed_question_id": str | None,
                    "source_locator": str,
                    "field": str,
                    "evidence": str,
                },
            ),
        }
        instances = (
            selection(module),
            adapter_manifest(module),
            module.AdaptedImportPackage(
                Path("/tmp/package"),
                Path("/tmp/package/import_manifest.json"),
                batch_manifest(),
            ),
            issue(module),
        )
        for carrier, (field_names, hints) in expected.items():
            with self.subTest(carrier=carrier.__name__):
                self.assertTrue(is_dataclass(carrier))
                self.assertEqual(tuple(field.name for field in fields(carrier)), field_names)
                self.assertEqual(get_type_hints(carrier), hints)
                self.assertTrue(
                    all(
                        field.default is MISSING and field.default_factory is MISSING
                        for field in fields(carrier)
                    )
                )
        for value in instances:
            with self.subTest(instance=type(value).__name__), self.assertRaises(
                FrozenInstanceError
            ):
                setattr(value, fields(value)[0].name, "changed")

    def test_selection_accepts_exact_values_and_defensively_preserves_tuple_order(self):
        module = adapter_models(self)
        images = ["images/z.jpg", "images/a.png"]
        tags = ["vector", "vector", "geometry"]
        value = selection(
            module,
            kind="exercise",
            number="Q1",
            source_section="應試練習",
            language_layout="interleaved_bilingual",
            answer_mapping="missing_from_source",
            expected_image_members=images,
            tags=tags,
            tag_status="proposed",
            difficulty_level=5,
            difficulty_status="proposed",
        )
        images.reverse()
        tags.clear()
        self.assertEqual(value.expected_image_members, ("images/z.jpg", "images/a.png"))
        self.assertEqual(value.tags, ("vector", "vector", "geometry"))

    def test_selection_rejects_invalid_string_types_and_enum_values(self):
        module = adapter_models(self)
        required_strings = (
            "proposed_question_id", "number", "source_section", "primary_type"
        )
        for field_name in required_strings:
            for invalid in ("", None, True, 1):
                with self.subTest(field=field_name, invalid=invalid), self.assertRaises(
                    PipelineError
                ):
                    selection(module, **{field_name: invalid})
        for field_name, invalid in (
            ("kind", "Example"),
            ("language_layout", "bilingual"),
            ("answer_mapping", "generated_answer"),
            ("tag_status", "verified"),
            ("difficulty_status", "verified"),
        ):
            with self.subTest(field=field_name), self.assertRaises(PipelineError):
                selection(module, **{field_name: invalid})
        for field_name in (
            "kind", "language_layout", "answer_mapping", "tag_status",
            "difficulty_status",
        ):
            for invalid in ("", None, True, 1):
                with self.subTest(field=field_name, invalid=invalid), self.assertRaises(
                    PipelineError
                ):
                    selection(module, **{field_name: invalid})

    def test_selection_enforces_answer_tag_and_difficulty_cross_fields(self):
        module = adapter_models(self)
        self.assertEqual(
            selection(module, answer_mapping="source_answer", answer_number="Q1").answer_number,
            "Q1",
        )
        for invalid in ("", True, 1):
            with self.subTest(answer_number=invalid), self.assertRaises(PipelineError):
                selection(module, answer_number=invalid)
        with self.assertRaises(PipelineError):
            selection(
                module,
                answer_mapping="missing_from_source",
                answer_number="Q1",
            )
        for values in (
            {"tags": [], "tag_status": "source_provided"},
            {"tags": ["vector"], "tag_status": "missing"},
            {"tags": [""], "tag_status": "source_provided"},
            {"tags": [1], "tag_status": "source_provided"},
            {"tags": "vector", "tag_status": "source_provided"},
        ):
            with self.subTest(values=values), self.assertRaises(PipelineError):
                selection(module, **values)
        for values in (
            {"difficulty_level": None, "difficulty_status": "source_provided"},
            {"difficulty_level": 2, "difficulty_status": "missing"},
            {"difficulty_level": True, "difficulty_status": "source_provided"},
            {"difficulty_level": 0, "difficulty_status": "source_provided"},
            {"difficulty_level": 6, "difficulty_status": "source_provided"},
            {"difficulty_level": 2.0, "difficulty_status": "source_provided"},
        ):
            with self.subTest(values=values), self.assertRaises(PipelineError):
                selection(module, **values)
        missing = selection(
            module,
            tags=[],
            tag_status="missing",
            difficulty_level=None,
            difficulty_status="missing",
        )
        self.assertEqual(missing.tags, ())
        self.assertIsNone(missing.difficulty_level)

    def test_selection_enforces_canonical_unique_lowercase_image_paths(self):
        module = adapter_models(self)
        value = selection(
            module,
            expected_image_members=["images/向量.jpeg", "images/diagram.png"],
        )
        self.assertEqual(
            value.expected_image_members,
            ("images/向量.jpeg", "images/diagram.png"),
        )
        invalid_paths = (
            "",
            "/images/a.jpg",
            "//server/images/a.jpg",
            "C:/images/a.jpg",
            "images\\a.jpg",
            "../images/a.jpg",
            "images/./a.jpg",
            "images//a.jpg",
            "images/e\u0301.jpg",
            "images/a.JPG",
            "images/a.gif",
        )
        for invalid in invalid_paths:
            with self.subTest(path=invalid), self.assertRaises(PipelineError):
                selection(module, expected_image_members=[invalid])
        for invalid_container in ("images/a.jpg", {"images/a.jpg"}, 1):
            with self.subTest(container=invalid_container), self.assertRaises(PipelineError):
                selection(module, expected_image_members=invalid_container)
        with self.assertRaises(PipelineError):
            selection(
                module,
                expected_image_members=["images/a.jpg", "images/a.jpg"],
            )

    def test_selection_requires_every_image_member_beneath_images_root(self):
        module = adapter_models(self)
        for invalid in ("diagram.png", "other/a.jpg"):
            with self.subTest(path=invalid), self.assertRaises(PipelineError):
                selection(module, expected_image_members=[invalid])

    def test_manifest_accepts_exact_values_and_defensively_preserves_selection_order(self):
        module = adapter_models(self)
        first = selection(module, proposed_question_id="M2-NEW-002", number="2")
        second = selection(module, proposed_question_id="M2-NEW-001", number="1")
        declared = [first, second]
        value = adapter_manifest(
            module,
            expected_candidate_count=2,
            selections=declared,
        )
        declared.reverse()
        self.assertEqual(value.selections, (first, second))

    def test_manifest_rejects_invalid_scalars_enums_sha_and_count(self):
        module = adapter_models(self)
        for field_name in ("batch_id", "source_id", "chapter"):
            for invalid in ("", None, True, 1):
                with self.subTest(field=field_name, invalid=invalid), self.assertRaises(
                    PipelineError
                ):
                    adapter_manifest(module, **{field_name: invalid})
        for values in (
            {"schema_version": "task9b-mmd-adapter-v2"},
            {"schema_version": 1},
            {"source_kind": "zip"},
            {"source_kind": True},
            {"source_sha256": HEX_A.upper()},
            {"source_sha256": "a" * 63},
            {"source_sha256": 1},
            {"expected_candidate_count": True},
            {"expected_candidate_count": -1},
            {"expected_candidate_count": 1.0},
            {"expected_candidate_count": 0},
        ):
            with self.subTest(values=values), self.assertRaises(PipelineError):
                adapter_manifest(module, **values)
        empty = adapter_manifest(
            module,
            expected_candidate_count=0,
            selections=[],
        )
        self.assertEqual(empty.selections, ())

    def test_manifest_enforces_member_paths_suffixes_and_source_kind_rules(self):
        module = adapter_models(self)
        plain = adapter_manifest(
            module,
            source_kind="mmd",
            primary_member="main.mmd",
            answer_member=None,
        )
        self.assertEqual(plain.primary_member, "main.mmd")
        with_answer = adapter_manifest(
            module,
            answer_member="answers/solutions.mmd",
            selections=[selection(module, answer_number="1")],
        )
        self.assertEqual(with_answer.answer_member, "answers/solutions.mmd")
        invalid_members = (
            "",
            "/source/main.mmd",
            "//server/source/main.mmd",
            "C:/source/main.mmd",
            "source\\main.mmd",
            "../source/main.mmd",
            "source/./main.mmd",
            "source//main.mmd",
            "source/e\u0301.mmd",
            "source/main.MMD",
            "source/main.md",
        )
        for field_name in ("primary_member", "answer_member"):
            for invalid in invalid_members:
                with self.subTest(field=field_name, value=invalid), self.assertRaises(
                    PipelineError
                ):
                    adapter_manifest(module, **{field_name: invalid})
        for values in (
            {"source_kind": "mmd", "primary_member": "main.mmd", "answer_member": "answer.mmd"},
            {"primary_member": "source/main.mmd", "answer_member": "source/main.mmd"},
            {"selections": [selection(module, answer_number="1")], "answer_member": None},
        ):
            with self.subTest(values=values), self.assertRaises(PipelineError):
                adapter_manifest(module, **values)

    def test_manifest_requires_exact_selection_instances_and_unique_ids(self):
        module = adapter_models(self)
        duplicate = selection(module)
        for invalid in ("selection", {duplicate}, (item for item in [duplicate]), 1):
            with self.subTest(container=type(invalid).__name__), self.assertRaises(PipelineError):
                adapter_manifest(module, selections=invalid)
        with self.assertRaises(PipelineError):
            adapter_manifest(module, selections=[object()])
        with self.assertRaises(PipelineError):
            adapter_manifest(
                module,
                expected_candidate_count=2,
                selections=[duplicate, duplicate],
            )

    def test_adapted_package_requires_paths_exact_manifest_and_canonical_manifest_path(self):
        module = adapter_models(self)
        manifest = batch_manifest()
        root = Path("/tmp/task9b-package")
        value = module.AdaptedImportPackage(
            root,
            root / "import_manifest.json",
            manifest,
        )
        self.assertEqual(value.package_root, root)
        self.assertIs(value.manifest, manifest)
        for values in (
            (str(root), root / "import_manifest.json", manifest),
            (root, str(root / "import_manifest.json"), manifest),
            (PurePosixPath("/tmp/task9b-package"), root / "import_manifest.json", manifest),
            (root, root / "other.json", manifest),
            (root, root / "import_manifest.json", object()),
        ):
            with self.subTest(values=values), self.assertRaises(PipelineError):
                module.AdaptedImportPackage(*values)

    def test_issue_enforces_exact_codes_blocking_severity_and_field_types(self):
        module = adapter_models(self)
        for code in ISSUE_CODES:
            self.assertEqual(issue(module, code=code).code, code)
        for values in (
            {"code": "unknown"},
            {"code": ""},
            {"code": 1},
            {"severity": "warning"},
            {"severity": ""},
            {"severity": True},
            {"proposed_question_id": ""},
            {"proposed_question_id": True},
            {"source_locator": None},
            {"field": ""},
            {"field": True},
        ):
            with self.subTest(values=values), self.assertRaises(PipelineError):
                issue(module, **values)

    def test_issue_enforces_canonical_locator_and_canonical_json_object_evidence(self):
        module = adapter_models(self)
        value = issue(
            module,
            proposed_question_id="M2-NEW-001",
            source_locator="source/main.mmd#bytes=12:30",
            evidence=json.dumps(
                {"actual": "mmd", "expected": "mmd_zip", "reason": "invalid_value"},
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ),
        )
        self.assertEqual(value.source_locator, "source/main.mmd#bytes=12:30")
        invalid_locators = (
            "source/main.mmd",
            "/source/main.mmd#bytes=0:1",
            "source\\main.mmd#bytes=0:1",
            "source/../main.mmd#bytes=0:1",
            "source/e\u0301.mmd#bytes=0:1",
            "source/main.mmd#bytes=2:2",
            "source/main.mmd#bytes=-1:2",
        )
        for invalid in invalid_locators:
            with self.subTest(locator=invalid), self.assertRaises(PipelineError):
                issue(module, source_locator=invalid)
        invalid_evidence = (
            "",
            "[]",
            '{"b":1,"a":2}',
            '{"actual": "mmd"}',
            '{"actual":NaN}',
            '{"actual":"/tmp/runtime-source.mmd"}',
            1,
        )
        for invalid in invalid_evidence:
            with self.subTest(evidence=invalid), self.assertRaises(PipelineError):
                issue(module, evidence=invalid)

    def test_public_paths_reject_bare_dot_nul_newline_and_tab(self):
        module = adapter_models(self)
        path_tails = (".", "\x00", "line\nfeed", "horizontal\ttab")
        for tail in path_tails:
            image_path = tail if tail == "." else f"images/{tail}.jpg"
            member_path = tail if tail == "." else f"source/{tail}.mmd"
            locator_path = tail if tail == "." else f"source/{tail}.mmd"
            with self.subTest(carrier="selection", value=repr(image_path)), self.assertRaises(
                PipelineError
            ):
                selection(module, expected_image_members=[image_path])
            with self.subTest(carrier="primary_member", value=repr(member_path)), self.assertRaises(
                PipelineError
            ):
                adapter_manifest(module, primary_member=member_path)
            with self.subTest(carrier="answer_member", value=repr(member_path)), self.assertRaises(
                PipelineError
            ):
                adapter_manifest(module, answer_member=member_path)
            with self.subTest(carrier="source_locator", value=repr(locator_path)), self.assertRaises(
                PipelineError
            ):
                issue(module, source_locator=f"{locator_path}#bytes=0:1")

    def test_public_paths_reject_unicode_cc_but_not_line_separator(self):
        module = adapter_models(self)
        for control in ("\u0080", "\u0085", "\u009f"):
            image_path = f"images/control{control}.jpg"
            member_path = f"source/control{control}.mmd"
            with self.subTest(carrier="selection", codepoint=ord(control)), self.assertRaises(
                PipelineError
            ):
                selection(module, expected_image_members=[image_path])
            with self.subTest(carrier="primary_member", codepoint=ord(control)), self.assertRaises(
                PipelineError
            ):
                adapter_manifest(module, primary_member=member_path)
            with self.subTest(carrier="answer_member", codepoint=ord(control)), self.assertRaises(
                PipelineError
            ):
                adapter_manifest(module, answer_member=member_path)
            with self.subTest(carrier="source_locator", codepoint=ord(control)), self.assertRaises(
                PipelineError
            ):
                issue(module, source_locator=f"{member_path}#bytes=0:1")

        separator = "\u2028"
        image_path = f"images/line{separator}separator.jpg"
        member_path = f"source/line{separator}separator.mmd"
        self.assertEqual(
            selection(module, expected_image_members=[image_path]).expected_image_members,
            (image_path,),
        )
        self.assertEqual(
            adapter_manifest(module, primary_member=member_path).primary_member,
            member_path,
        )
        self.assertEqual(
            adapter_manifest(module, answer_member=member_path).answer_member,
            member_path,
        )
        self.assertEqual(
            issue(module, source_locator=f"{member_path}#bytes=0:1").source_locator,
            f"{member_path}#bytes=0:1",
        )

    def test_issue_evidence_rejects_absolute_paths_in_mapping_keys_recursively(self):
        module = adapter_models(self)
        payloads = (
            {"/tmp/source.mmd": "value"},
            {"outer": {"/tmp/source.mmd": "value"}},
            {"C:\\runtime\\source.mmd": "value"},
            {"outer": {"C:/runtime/source.mmd": "value"}},
            {"\\\\server\\share\\source.mmd": "value"},
            {"outer": {"\\\\server\\share\\source.mmd": "value"}},
        )
        for payload in payloads:
            evidence = json.dumps(
                payload,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            )
            with self.subTest(evidence=evidence), self.assertRaises(PipelineError):
                issue(module, evidence=evidence)

    def test_blocked_error_is_exact_input_format_subclass_with_fixed_message(self):
        module = adapter_models(self)
        self.assertTrue(issubclass(module.MmdAdapterBlockedError, InputFormatError))
        self.assertEqual(
            get_type_hints(module.MmdAdapterBlockedError),
            {"issues": tuple[module.MmdAdapterIssue, ...]},
        )
        first = issue(module, code="unsupported_source_format", field="source_kind")
        error = module.MmdAdapterBlockedError([first])
        self.assertEqual(error.issues, (first,))
        self.assertEqual(str(error), BLOCKED_MESSAGE)
        self.assertEqual(error.args, (BLOCKED_MESSAGE,))
        self.assertNotIn(first.evidence, str(error))
        for invalid in ([], (), "issue", [object()]):
            with self.subTest(invalid=invalid), self.assertRaises(PipelineError):
                module.MmdAdapterBlockedError(invalid)

    def test_blocked_error_defensively_applies_stable_exact_five_field_sort(self):
        module = adapter_models(self)
        ordered = (
            issue(module, source_locator="", proposed_question_id=None, code="archive_integrity_invalid", field="archive", evidence="{}"),
            issue(module, source_locator="", proposed_question_id="A", code="source_contract_mismatch", field="a", evidence='{"z":1}'),
            issue(module, source_locator="", proposed_question_id="A", code="source_contract_mismatch", field="a", evidence="{}"),
            issue(module, source_locator="", proposed_question_id="A", code="source_contract_mismatch", field="z", evidence="{}"),
            issue(module, source_locator="a.mmd#bytes=0:1", proposed_question_id=None, code="archive_integrity_invalid", field="archive", evidence="{}"),
        )
        equal_first = issue(module, evidence="{}")
        equal_second = issue(module, evidence="{}")
        source = [equal_second, *reversed(ordered), equal_first]
        error = module.MmdAdapterBlockedError(source)
        source.clear()
        self.assertEqual(
            error.issues,
            (ordered[0], equal_second, equal_first, *ordered[1:]),
        )
        self.assertIs(error.issues[1], equal_second)
        self.assertIs(error.issues[2], equal_first)


if __name__ == "__main__":
    unittest.main()
