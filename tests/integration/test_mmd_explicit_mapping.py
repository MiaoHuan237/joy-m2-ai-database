from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.errors import InputMissingError
from joy_m2.ingest.adapter import adapt_mmd_package
from joy_m2.ingest.adapter_models import MmdAdapterBlockedError
from joy_m2.ingest.preflight import preflight_import
from joy_m2.models import ArtifactRef
from tests.unit.test_mmd_source_mapping import (
    IMAGE_BYTES,
    SOURCE_BYTES,
    SOURCE_ID,
    canonical_json,
    require_api,
    valid_draft,
    valid_manifest,
    write_answer_archive_case,
    write_image_archive_case,
    write_mapping_case,
)


BASELINE = ROOT / "releases/V1.18/Joy_M2_Complete_Question_DB_V1_18.sqlite3"
RAW_CANDIDATE_FIELDS = {
    "proposed_question_id", "source_id", "source_question_number",
    "source_section", "source_fragment_hash", "question_text_original",
    "question_text_zh", "translation_status", "translation_evidence",
    "solution_original", "solution_verified", "answer_status",
    "explanation_text", "explanation_status", "explanation_evidence",
    "image_paths", "image_roles", "primary_type", "tags", "tag_status",
    "difficulty_level", "difficulty_status", "enrichment_status",
}
MANIFEST_FIELDS = (
    "schema_version", "batch_id", "project", "module", "chapter",
    "target_release_version", "candidate_records", "source_files",
    "answer_files", "image_files", "teacher_notes_files",
    "common_errors_files", "language_policy", "split_policy",
    "difficulty_policy", "tag_policy", "answer_policy",
    "explanation_policy",
)


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _baseline_ref() -> ArtifactRef:
    data = BASELINE.read_bytes()
    return ArtifactRef(BASELINE, _sha256(data), len(data), "sqlite")


def _tree(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _reversed_case(testcase: unittest.TestCase, root: Path):
    manifest = valid_manifest()
    manifest["selections"] = list(reversed(manifest["selections"]))
    draft = valid_draft()
    draft["questions"] = list(reversed(draft["questions"]))
    for index, question in enumerate(draft["questions"]):
        question["semantic_order"] = index
    return write_mapping_case(testcase, root, manifest=manifest, draft=draft)


def _minimal_bilingual_equivalence_case(
    testcase: unittest.TestCase,
    root: Path,
    *,
    language_layout: str = "english_then_chinese",
):
    function = require_api(testcase, "adapt_mmd_package_from_mapping")
    source_bytes = "例題1\nEnglish prompt.\n中文題目。\n".encode("utf-8")
    source_path = root / "source.mmd"
    source_path.write_bytes(source_bytes)
    selection = valid_manifest(source_bytes)
    selection["batch_id"] = "TASK9B-MINIMAL-BILINGUAL"
    selection["expected_candidate_count"] = 1
    selected = dict(selection["selections"][0])
    selected.update(
        proposed_question_id="TASK9B-MINIMAL-BILINGUAL-01",
        kind="example",
        number="1",
        source_section="例題",
        language_layout=language_layout,
        answer_mapping="missing_from_source",
        answer_number=None,
        expected_image_members=[],
    )
    selection["selections"] = [selected]
    selection_path = root / "selection.json"
    selection_path.write_bytes(canonical_json(selection))
    mode_a = adapt_mmd_package(
        selection_path,
        source_path,
        root / "data/staging/mode-a",
        PipelineConfig(root),
    )
    source_map = json.loads(
        (mode_a.package_root / "source/source-map.json").read_bytes()
    )
    source_question = source_map["questions"][0]
    mapping = {
        "schema_version": "task9b-source-mapping-v1",
        "mapping_mode": "explicit",
        "source_kind": "mmd",
        "source_sha256": selection["source_sha256"],
        "primary_member": "source.mmd",
        "primary_member_sha256": _sha256(source_bytes),
        "answer_member": None,
        "answer_member_sha256": None,
        "source_id": selection["source_id"],
        "chapter": selection["chapter"],
        "questions": [
            {
                "semantic_order": 0,
                "proposed_question_id": source_question["proposed_question_id"],
                "source_question_number": source_question["source_question_number"],
                "source_section": source_question["source_section"],
                "question_span": source_question["fragment"],
                "solution_spans": source_question["solution_spans"],
                "explanation_spans": source_question["explanation_spans"],
                "image_bindings": [],
            }
        ],
        "ignored_spans": [],
        "ignored_image_members": [],
    }
    mapping_path = root / "source_mapping.json"
    mapping_bytes = canonical_json(mapping)
    mapping_path.write_bytes(mapping_bytes)
    digest = _sha256(mapping_bytes)
    approval_type = require_api(testcase, "SourceMappingApproval")
    approval = approval_type(selection["source_id"], digest, f"USER APPROVED SOURCE MAPPING {selection['source_id']} {digest}")
    mode_b = function(
        selection_path,
        mapping_path,
        approval,
        source_path,
        root / "data/staging/mode-b",
        PipelineConfig(root),
    )
    return mode_a, mode_b


class ModeACompatibilityTests(unittest.TestCase):
    def test_mode_a_does_not_apply_mode_b_source_id_line_break_rule(self):
        for source_id in ("MODE-A\rSOURCE", "MODE-A\nSOURCE"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source_path = root / "source.mmd"
                manifest = valid_manifest()
                manifest["source_id"] = source_id
                for selection in manifest["selections"]:
                    selection["language_layout"] = "english_then_chinese"
                selection_path = root / "selection.json"
                selection_path.write_bytes(canonical_json(manifest))
                output = root / "data/staging/output"
                try:
                    adapt_mmd_package(
                        selection_path,
                        source_path,
                        output,
                        PipelineConfig(root),
                    )
                except InputMissingError:
                    pass
                except MmdAdapterBlockedError:
                    self.fail("Mode A must not inherit the Mode B-only source_id rule")
                else:
                    self.fail("the missing source must be reached after Mode A manifest decoding")
                self.assertFalse(output.exists())

    def test_mode_a_rejects_source_only_layouts_at_d0_before_source_access(self):
        for language_layout in ("source_chinese", "source_english"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source_path = root / "source.mmd"
                manifest = valid_manifest()
                manifest["selections"][0]["language_layout"] = language_layout
                selection_path = root / "selection.json"
                selection_path.write_bytes(canonical_json(manifest))
                output = root / "data/staging/output"
                with self.subTest(language_layout=language_layout), self.assertRaises(MmdAdapterBlockedError) as caught:
                    adapt_mmd_package(selection_path, source_path, output, PipelineConfig(root))
                issue = next(issue for issue in caught.exception.issues if issue.field == "$.selections[0].language_layout")
                self.assertEqual(
                    json.loads(issue.evidence),
                    {
                        "actual": language_layout,
                        "expected": ["english_then_chinese", "interleaved_bilingual"],
                        "reason": "invalid_value",
                    },
                )
                self.assertFalse(source_path.exists())
                self.assertFalse(output.exists())


class ExplicitMappingPackageTests(unittest.TestCase):
    def _build(self, root: Path, *, reversed_order: bool = False):
        if reversed_order:
            invoke = _reversed_case(self, root)
        else:
            invoke = write_mapping_case(self, root)
        package = invoke()
        mapping_bytes = (root / "source_mapping.json").read_bytes()
        proposal = SimpleNamespace(mapping_sha256=_sha256(mapping_bytes))
        return proposal, package

    def test_physical_source_order_is_independent_of_semantic_candidate_order(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            _, package = self._build(Path(directory), reversed_order=True)
            candidates = json.loads((package.package_root / "records/candidates.json").read_text(encoding="utf-8"))
            source_map = json.loads((package.package_root / "source/source-map.json").read_text(encoding="utf-8"))
            self.assertEqual([item["proposed_question_id"] for item in candidates], ["EXPLICIT-001", "EXPLICIT-002"])
            self.assertEqual([item["proposed_question_id"] for item in source_map["questions"]], ["EXPLICIT-001", "EXPLICIT-002"])
            self.assertEqual([item["source_order"] for item in source_map["questions"]], [1, 0])

    def test_whole_question_answer_explanation_and_image_bytes_are_preserved(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            _, package = self._build(Path(directory))
            candidates = json.loads((package.package_root / "records/candidates.json").read_text(encoding="utf-8"))
            first, second = candidates
            self.assertEqual(first["question_text_original"], "Repeat A\nFind $x+1$.\n![](./images/diagram.jpg)\n")
            self.assertEqual(first["question_text_zh"], "")
            self.assertEqual(first["translation_status"], "missing")
            self.assertIsNone(first["translation_evidence"])
            self.assertEqual(first["solution_original"], "Solution evidence\n2\n")
            self.assertEqual(first["explanation_text"], "Explanation evidence\nBecause $1+1=2$.\n")
            self.assertEqual(second["answer_status"], "missing_from_source")
            self.assertEqual(second["solution_original"], "")
            self.assertEqual((package.package_root / "images/diagram.jpg").read_bytes(), IMAGE_BYTES)

    def test_canonical_manifest_candidate_and_source_map_schemas_remain_unchanged(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            _, package = self._build(Path(directory))
            manifest = json.loads(package.manifest_path.read_text(encoding="utf-8"))
            candidates = json.loads((package.package_root / "records/candidates.json").read_text(encoding="utf-8"))
            source_map = json.loads((package.package_root / "source/source-map.json").read_text(encoding="utf-8"))
            self.assertEqual(tuple(manifest), MANIFEST_FIELDS)
            self.assertTrue(all(set(value) == RAW_CANDIDATE_FIELDS for value in candidates))
            self.assertEqual(set(source_map), {"schema_version", "batch_id", "source_id", "primary_member", "members", "questions"})
            self.assertTrue(
                all(
                    set(question)
                    == {
                        "proposed_question_id", "source_order",
                        "source_question_number", "source_section", "fragment",
                        "text_spans", "solution_spans", "explanation_spans",
                        "image_references",
                    }
                    for question in source_map["questions"]
                )
            )
            self.assertTrue(
                all(
                    set(reference)
                    == {
                        "source_order", "token_span", "raw_target",
                        "selected_member", "canonical_path", "sha256", "role",
                    }
                    for question in source_map["questions"]
                    for reference in question["image_references"]
                )
            )

    def test_mapping_approval_and_review_authority_do_not_leak_into_package(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            proposal, package = self._build(Path(directory))
            tree = _tree(package.package_root)
            self.assertNotIn("source_mapping.json", tree)
            self.assertNotIn("SOURCE_MAPPING_REVIEW.md", tree)
            combined = b"".join(tree.values())
            self.assertNotIn(proposal.mapping_sha256.encode("ascii"), combined)
            self.assertNotIn(b"USER APPROVED SOURCE MAPPING", combined)
            self.assertNotIn(str(Path(directory)).encode("utf-8"), combined)

    def test_repeat_and_independent_root_outputs_are_byte_identical(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        outputs = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                _, package = self._build(root)
                outputs.append(_tree(package.package_root))
        self.assertEqual(outputs[0], outputs[1])

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            invoke = write_mapping_case(self, root)
            first = invoke("same-root-one")
            second = invoke("same-root-two")
            self.assertEqual(_tree(first.package_root), _tree(second.package_root))

    def test_source_chinese_projects_exact_source_without_translation(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        manifest = valid_manifest()
        for selected in manifest["selections"]:
            selected["language_layout"] = "source_chinese"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = write_mapping_case(self, root, manifest=manifest)()
            candidates = json.loads((package.package_root / "records/candidates.json").read_bytes())
            source_map = json.loads((package.package_root / "source/source-map.json").read_bytes())
            for index, candidate in enumerate(candidates):
                self.assertEqual(candidate["question_text_zh"], candidate["question_text_original"])
                self.assertEqual(candidate["translation_status"], "source_present")
                fragment = source_map["questions"][index]["fragment"]
                self.assertEqual(
                    candidate["translation_evidence"],
                    f"source:source/original.mmd.txt#source.mmd#bytes={fragment['start_byte']}:{fragment['end_byte']}",
                )

    def test_solution_and_explanation_spans_render_in_declared_array_order(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        draft = valid_draft()
        draft["questions"][0]["solution_line_spans"] = [
            {"member": "source.mmd", "line_start": 6, "line_end": 6},
            {"member": "source.mmd", "line_start": 5, "line_end": 5},
        ]
        draft["questions"][0]["explanation_line_spans"] = [
            {"member": "source.mmd", "line_start": 8, "line_end": 8},
            {"member": "source.mmd", "line_start": 7, "line_end": 7},
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            package = write_mapping_case(self, root, draft=draft)()
            candidates = json.loads((package.package_root / "records/candidates.json").read_bytes())
            source_map = json.loads((package.package_root / "source/source-map.json").read_bytes())
        self.assertEqual(candidates[0]["solution_original"], "2\nSolution evidence\n")
        self.assertEqual(
            candidates[0]["explanation_text"],
            "Because $1+1=2$.\nExplanation evidence\n",
        )
        self.assertGreater(
            source_map["questions"][0]["solution_spans"][0]["start_byte"],
            source_map["questions"][0]["solution_spans"][1]["start_byte"],
        )
        self.assertGreater(
            source_map["questions"][0]["explanation_spans"][0]["start_byte"],
            source_map["questions"][0]["explanation_spans"][1]["start_byte"],
        )

    def test_selected_answer_member_is_rendered_and_staged_by_the_valid_zip_path(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            _, invoke = write_answer_archive_case(self, root)
            package = invoke()
            candidates = json.loads((package.package_root / "records/candidates.json").read_bytes())
            manifest = json.loads(package.manifest_path.read_bytes())
            staged_answer = (package.package_root / "answers/answer.mmd.txt").read_bytes()
        self.assertEqual(candidates[0]["solution_original"], "Answer A\n")
        self.assertEqual(candidates[0]["answer_status"], "source_provided")
        self.assertEqual(
            [item["relative_path"] for item in manifest["answer_files"]],
            ["answers/answer.mmd.txt"],
        )
        self.assertEqual(staged_answer, b"Answer A\n")

    def test_mode_a_and_mode_b_have_exact_package_and_task9a_equivalence(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            mode_a, mode_b = _minimal_bilingual_equivalence_case(self, root)
            selection_payload = json.loads((root / "selection.json").read_bytes())
            self.assertEqual(
                {item["language_layout"] for item in selection_payload["selections"]},
                {"english_then_chinese"},
            )
            self.assertEqual(_tree(mode_a.package_root), _tree(mode_b.package_root))
            result_a = preflight_import(mode_a.manifest, mode_a.package_root, _baseline_ref())
            result_b = preflight_import(mode_b.manifest, mode_b.package_root, _baseline_ref())
            self.assertEqual(result_a.candidates, result_b.candidates)
            self.assertEqual(result_a.issues, result_b.issues)
            self.assertEqual(result_a.report, result_b.report)
            self.assertEqual(result_a.report.preflight_sha256, result_b.report.preflight_sha256)

    def test_mapping_review_notes_and_ignored_reasons_do_not_change_package_identity(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        outputs = []
        for reason in ("approved heading", "different approved heading wording"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                draft = valid_draft()
                draft["ignored_line_spans"][0]["reason"] = reason
                package = write_mapping_case(self, root, draft=draft)()
                outputs.append(_tree(package.package_root))
        self.assertEqual(outputs[0], outputs[1])

    def test_outer_zip_digest_order_and_timestamp_do_not_enter_package_identity(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        results = []
        for timestamp, reversed_order in (
            ((2024, 1, 2, 3, 4, 6), False),
            ((2025, 6, 8, 9, 10, 12), True),
        ):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                outer_sha, invoke = write_image_archive_case(
                    self,
                    root,
                    timestamp=timestamp,
                    reverse_order=reversed_order,
                )
                package = invoke()
                tree = _tree(package.package_root)
                self.assertNotIn(outer_sha.encode("ascii"), b"".join(tree.values()))
                results.append((outer_sha, tree))
        self.assertNotEqual(results[0][0], results[1][0])
        self.assertEqual(results[0][1], results[1][1])

    def test_task9a_preflight_is_deterministic_for_equivalent_mode_b_packages(self):
        require_api(self, "adapt_mmd_package_from_mapping")
        results = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as directory:
                _, package = self._build(Path(directory))
                result = preflight_import(package.manifest, package.package_root, _baseline_ref())
                results.append(
                    (
                        result.candidates,
                        result.issues,
                        result.report.status,
                        result.report.detected_count,
                        result.report.preflight_sha256,
                    )
                )
        self.assertEqual(results[0], results[1])


if __name__ == "__main__":
    unittest.main()
