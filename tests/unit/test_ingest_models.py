from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, MISSING
from pathlib import Path
import hashlib
import json
import sys
import tempfile
import unittest
from typing import get_type_hints

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.errors import PipelineError
from joy_m2.models import ArtifactRef
import joy_m2.ingest.models as ingest_models
from joy_m2.ingest.models import (
    BatchImportManifest,
    ImportCandidate,
    ImportFileEvidence,
    ImportIssue,
    ImportPreflightReport,
    ImportPreflightResult,
)
from joy_m2.ingest.manifest import load_import_manifest


HEX_A = "a" * 64
HEX_B = "b" * 64


def file_evidence(path: str = "records/questions.json", kind: str = "candidate_json", **overrides):
    values = dict(relative_path=path, sha256=HEX_A, size_bytes=12, kind=kind)
    values.update(overrides)
    return ImportFileEvidence(**values)


def candidate(**overrides):
    zh = "中文题目"
    explanation = "Explanation"
    values = dict(
        proposed_question_id="NEW-Q1",
        source_id="SOURCE-1",
        source_question_number="1",
        source_section="Section A",
        source_fragment_hash=HEX_A,
        normalized_text_sha256=HEX_B,
        question_text_original="Differentiate x^2.",
        question_text_zh=zh,
        translation_status="ai_proposed",
        translation_evidence="ai-proposal-sha256:" + hashlib.sha256(zh.encode()).hexdigest(),
        solution_original="2x",
        solution_verified="2x",
        answer_status="source_provided",
        explanation_text=explanation,
        explanation_status="ai_proposed",
        explanation_evidence="ai-proposal-sha256:" + hashlib.sha256(explanation.encode()).hexdigest(),
        image_paths=(), image_sha256s=(), image_roles=(),
        primary_type="微分的应用", tags=("differentiation",),
        tag_status="source_provided", difficulty_level=2,
        difficulty_status="source_provided", enrichment_status="complete",
    )
    values.update(overrides)
    return ImportCandidate(**values)


def manifest(**overrides):
    values = dict(
        schema_version="task9-import-manifest-v1", batch_id="batch-001",
        project="Joy M2 AI Database", module="M2", chapter="Differentiation",
        target_release_version="V1.19", candidate_records=(file_evidence(),),
        source_files=(), answer_files=(), image_files=(), teacher_notes_files=(),
        common_errors_files=(),
        language_policy="preserve_source_and_store_reviewed_chinese_separately",
        split_policy="one_complete_question_per_record",
        difficulty_policy="joy_level_1_5",
        tag_policy="controlled_primary_type_and_tags",
        answer_policy="preserve_source_answer_identity",
        explanation_policy="source_or_independently_verified_with_identity",
    )
    values.update(overrides)
    return BatchImportManifest(**values)


def report(**overrides):
    values = dict(
        batch_id="batch-001", status="READY FOR USER IMPORT APPROVAL",
        preflight_sha256=HEX_A, manifest_sha256=HEX_B,
        baseline_version="V1.18", before_count=497,
        target_release_version="V1.19", detected_count=1,
        new_candidate_count=1, duplicate_count=0, rejected_count=0,
        ambiguous_count=0, approved_count=0, projected_after_count=498,
        readable_files=("records/questions.json",), unreadable_files=(),
        unsupported_files=(), teacher_notes_file_count=0,
        common_errors_file_count=0, ambiguous_splits=(), missing_answers=(),
        missing_explanations=(), incomplete_enrichments=(), missing_images=(),
        orphan_images=(), level_counts=((2, 1),), proposed_ids=("NEW-Q1",),
        warnings=(), blocking_errors=(),
    )
    if "adaptations" in {field.name for field in fields(ImportPreflightReport)}:
        values["adaptations"] = ()
    values.update(overrides)
    return ImportPreflightReport(**values)


class IngestModelTests(unittest.TestCase):
    def test_import_adaptation_exact_contract(self):
        adaptation_type = getattr(ingest_models, "ImportAdaptation", None)
        self.assertIsNotNone(adaptation_type, "ImportAdaptation must exist")
        expected = (
            "candidate_id",
            "reference_question_id",
            "adaptation_kind",
            "evidence",
            "reason",
        )
        self.assertEqual(tuple(field.name for field in fields(adaptation_type)), expected)
        self.assertEqual(
            get_type_hints(adaptation_type),
            {name: str for name in expected},
        )
        self.assertTrue(
            all(
                field.default is MISSING and field.default_factory is MISSING
                for field in fields(adaptation_type)
            )
        )
        value = adaptation_type(
            "NEW-Q1",
            "V118-Q1",
            "adapted",
            "stable evidence",
            "stable reason",
        )
        with self.assertRaises(FrozenInstanceError):
            value.reason = "changed"

    def test_import_adaptation_rejects_empty_wrong_type_and_unapproved_kind(self):
        adaptation_type = getattr(ingest_models, "ImportAdaptation", None)
        self.assertIsNotNone(adaptation_type, "ImportAdaptation must exist")
        valid = {
            "candidate_id": "NEW-Q1",
            "reference_question_id": "V118-Q1",
            "adaptation_kind": "adapted",
            "evidence": "stable evidence",
            "reason": "stable reason",
        }
        for field_name in valid:
            for invalid in ("", None, True, 1):
                with self.subTest(field=field_name, invalid=invalid):
                    values = dict(valid)
                    values[field_name] = invalid
                    with self.assertRaises(PipelineError):
                        adaptation_type(**values)
        with self.assertRaises(PipelineError):
            adaptation_type(**dict(valid, adaptation_kind="transformed"))

    def test_report_adaptations_field_order_type_and_alias_isolation(self):
        adaptation_type = getattr(ingest_models, "ImportAdaptation", None)
        self.assertIsNotNone(adaptation_type, "ImportAdaptation must exist")
        report_fields = tuple(field.name for field in fields(ImportPreflightReport))
        proposed_index = report_fields.index("proposed_ids")
        self.assertEqual(
            report_fields[proposed_index : proposed_index + 3],
            ("proposed_ids", "adaptations", "warnings"),
        )
        self.assertEqual(
            get_type_hints(ImportPreflightReport)["adaptations"],
            tuple[adaptation_type, ...],
        )
        ordered = (
            adaptation_type("A", "1", "adapted", "a", "a"),
            adaptation_type("A", "1", "adapted", "a", "z"),
            adaptation_type("A", "1", "adapted", "z", "a"),
            adaptation_type("A", "2", "adapted", "a", "a"),
            adaptation_type("B", "1", "adapted", "a", "a"),
        )
        source = list(reversed(ordered))
        value = report(adaptations=source)
        source.clear()
        self.assertEqual(value.adaptations, ordered)
        with self.assertRaises(PipelineError):
            report(adaptations=[object()])

    def test_preflight_result_does_not_duplicate_adaptation_authority(self):
        self.assertNotIn(
            "adaptations",
            tuple(field.name for field in fields(ImportPreflightResult)),
        )

    def test_exact_fields_order_no_defaults_and_frozen(self):
        expected = {
            ImportFileEvidence: ("relative_path", "sha256", "size_bytes", "kind"),
            BatchImportManifest: ("schema_version", "batch_id", "project", "module", "chapter", "target_release_version", "candidate_records", "source_files", "answer_files", "image_files", "teacher_notes_files", "common_errors_files", "language_policy", "split_policy", "difficulty_policy", "tag_policy", "answer_policy", "explanation_policy"),
            ImportCandidate: ("proposed_question_id", "source_id", "source_question_number", "source_section", "source_fragment_hash", "normalized_text_sha256", "question_text_original", "question_text_zh", "translation_status", "translation_evidence", "solution_original", "solution_verified", "answer_status", "explanation_text", "explanation_status", "explanation_evidence", "image_paths", "image_sha256s", "image_roles", "primary_type", "tags", "tag_status", "difficulty_level", "difficulty_status", "enrichment_status"),
            ImportIssue: ("code", "severity", "proposed_question_id", "field", "evidence"),
            ImportPreflightReport: ("batch_id", "status", "preflight_sha256", "manifest_sha256", "baseline_version", "before_count", "target_release_version", "detected_count", "new_candidate_count", "duplicate_count", "rejected_count", "ambiguous_count", "approved_count", "projected_after_count", "readable_files", "unreadable_files", "unsupported_files", "teacher_notes_file_count", "common_errors_file_count", "ambiguous_splits", "missing_answers", "missing_explanations", "incomplete_enrichments", "missing_images", "orphan_images", "level_counts", "proposed_ids", "adaptations", "warnings", "blocking_errors"),
            ImportPreflightResult: ("manifest", "baseline_database", "candidates", "issues", "report"),
        }
        instances = [file_evidence(), manifest(), candidate(), ImportIssue("z", "warning", None, "f", "e"), report()]
        baseline = ArtifactRef(Path("baseline.sqlite3"), HEX_A, 1, "sqlite")
        instances.append(ImportPreflightResult(manifest(), baseline, [candidate()], [], report()))
        for cls, names in expected.items():
            self.assertEqual(tuple(f.name for f in fields(cls)), names)
            self.assertTrue(all(f.default is MISSING and f.default_factory is MISSING for f in fields(cls)))
        for value in instances:
            with self.assertRaises(FrozenInstanceError):
                setattr(value, next(iter(value.__dict__)), "changed")

    def test_file_evidence_and_manifest_validation(self):
        self.assertEqual(manifest(candidate_records=[file_evidence()]).candidate_records, (file_evidence(),))
        for bad in ("A" * 64, "a" * 63, 3):
            with self.assertRaises(PipelineError):
                ImportFileEvidence("a.json", bad, 1, "candidate_json")
        for kwargs in ({"size_bytes": True}, {"relative_path": "/a.json"}, {"kind": "pdf"}):
            with self.assertRaises(PipelineError):
                file_evidence(**kwargs)
        for target in (None, "V1.18", "V1.20", 119):
            with self.assertRaises(PipelineError):
                manifest(target_release_version=target)

    def test_candidate_status_payload_and_tuple_invariants(self):
        paths = ["images/a.png"]
        value = candidate(image_paths=paths, image_sha256s=[HEX_A], image_roles=["question"])
        paths.append("images/b.png")
        self.assertEqual(value.image_paths, ("images/a.png",))
        self.assertEqual(value.tags, ("differentiation",))
        bad_cases = (
            {"translation_status": "missing"},
            {"translation_status": "missing", "question_text_zh": "", "translation_evidence": "x"},
            {"explanation_status": "missing"},
            {"answer_status": "missing_from_source"},
            {"difficulty_level": True}, {"difficulty_level": 6},
            {"image_paths": ("a",), "image_sha256s": (), "image_roles": ()},
            {"tag_status": "unknown"}, {"enrichment_status": "done"},
        )
        for kwargs in bad_cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(PipelineError):
                candidate(**kwargs)
        missing = candidate(question_text_zh="", translation_status="missing", translation_evidence=None,
                            explanation_text="", explanation_status="missing", explanation_evidence=None,
                            solution_original="", solution_verified="", answer_status="missing_from_source",
                            tags=(), tag_status="missing", difficulty_level=None,
                            difficulty_status="missing", enrichment_status="incomplete")
        self.assertEqual(missing.translation_status, "missing")

    def test_provenance_evidence_is_content_bound(self):
        for status, evidence in (
            ("source_present", "source:sources/book.json#q1"),
            ("verified", "verified-review-sha256:" + HEX_A),
        ):
            self.assertEqual(candidate(translation_status=status, translation_evidence=evidence).translation_status, status)
        for evidence in ("ai-proposal-sha256:" + HEX_A, "source:/tmp/book#q1", "session:123"):
            with self.assertRaises(PipelineError):
                candidate(translation_evidence=evidence)

    def test_report_closure_and_result_sorting(self):
        for kwargs in (
            {"detected_count": 2}, {"projected_after_count": 499},
            {"approved_count": 1}, {"ambiguous_count": 1},
            {"before_count": True}, {"status": "PASS"},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(PipelineError):
                report(**kwargs)
        i1 = ImportIssue("b", "warning", "Q2", "f", "e")
        i2 = ImportIssue("a", "blocking", "Q1", "f", "e")
        baseline = ArtifactRef(Path("baseline.sqlite3"), HEX_A, 1, "sqlite")
        result = ImportPreflightResult(manifest(), baseline, [candidate()], [i1, i2], report())
        self.assertEqual(result.issues, (i2, i1))
        self.assertEqual(result.candidates, (candidate(),))


def _write_manifest_package(root: Path, *, target="V1.19", mutate=None):
    files = {
        "records/questions.json": b"[]\n",
        "sources/book.txt": b"source\n",
        "answers/book.txt": b"answer\n",
        "images/figure.png": b"PNG",
        "notes/teacher.txt": b"notes\n",
        "notes/errors.txt": b"errors\n",
    }
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)

    def entry(relative, kind):
        content = files[relative]
        return {"relative_path": relative, "sha256": hashlib.sha256(content).hexdigest(), "size_bytes": len(content), "kind": kind}

    payload = {
        "schema_version": "task9-import-manifest-v1", "batch_id": "batch-001",
        "project": "Joy M2 AI Database", "module": "M2", "chapter": "Differentiation",
        "target_release_version": target,
        "candidate_records": [entry("records/questions.json", "candidate_json")],
        "source_files": [entry("sources/book.txt", "source")],
        "answer_files": [entry("answers/book.txt", "answer")],
        "image_files": [entry("images/figure.png", "image")],
        "teacher_notes_files": [entry("notes/teacher.txt", "teacher_notes")],
        "common_errors_files": [entry("notes/errors.txt", "common_errors")],
        "language_policy": "preserve_source_and_store_reviewed_chinese_separately",
        "split_policy": "one_complete_question_per_record",
        "difficulty_policy": "joy_level_1_5",
        "tag_policy": "controlled_primary_type_and_tags",
        "answer_policy": "preserve_source_answer_identity",
        "explanation_policy": "source_or_independently_verified_with_identity",
    }
    if mutate:
        mutate(payload)
    manifest_path = root / "import_manifest.json"
    manifest_path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    return manifest_path, payload


class ManifestLoaderTests(unittest.TestCase):
    def test_loads_exact_manifest_and_preserves_semantic_candidate_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            second = root / "records/second.json"
            second.parent.mkdir(parents=True, exist_ok=True)
            second.write_bytes(b"[]\n")
            def add_second(payload):
                payload["candidate_records"].insert(0, {
                    "relative_path": "records/second.json",
                    "sha256": hashlib.sha256(b"[]\n").hexdigest(),
                    "size_bytes": 3, "kind": "candidate_json",
                })
            path, _ = _write_manifest_package(root, mutate=add_second)
            loaded = load_import_manifest(path, root)
            self.assertEqual(tuple(x.relative_path for x in loaded.candidate_records),
                             ("records/second.json", "records/questions.json"))
            self.assertEqual(loaded.teacher_notes_files[0].kind, "teacher_notes")
            self.assertEqual(loaded.common_errors_files[0].kind, "common_errors")

    def test_rejects_malformed_wrong_top_level_and_wrong_field_order(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, payload = _write_manifest_package(root)
            for raw in ("{", "[]"):
                path.write_text(raw, encoding="utf-8")
                with self.assertRaises(PipelineError):
                    load_import_manifest(path, root)
            path.write_text(json.dumps(dict(reversed(tuple(payload.items())))), encoding="utf-8")
            with self.assertRaises(PipelineError):
                load_import_manifest(path, root)

    def test_rejects_target_kind_hash_size_and_exact_type_mismatches(self):
        mutations = (
            lambda p: p.__setitem__("target_release_version", "V1.18"),
            lambda p: p["source_files"][0].__setitem__("kind", "answer"),
            lambda p: p["source_files"][0].__setitem__("sha256", HEX_A),
            lambda p: p["source_files"][0].__setitem__("size_bytes", True),
            lambda p: p["source_files"][0].__setitem__("relative_path", "/tmp/book.txt"),
            lambda p: p["source_files"][0].__setitem__("relative_path", "sources/../book.txt"),
        )
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path, _ = _write_manifest_package(root, mutate=mutation)
                with self.assertRaises(PipelineError):
                    load_import_manifest(path, root)

    def test_rejects_missing_directory_symlink_and_undeclared_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, _ = _write_manifest_package(root)
            (root / "sources/book.txt").unlink()
            with self.assertRaises(PipelineError):
                load_import_manifest(path, root)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path, _ = _write_manifest_package(root)
            (root / "extra.bin").write_bytes(b"extra")
            with self.assertRaises(PipelineError):
                load_import_manifest(path, root)
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as outside:
            root = Path(directory)
            path, payload = _write_manifest_package(root)
            target = Path(outside) / "outside.txt"; target.write_bytes(b"source\n")
            (root / "sources/book.txt").unlink(); (root / "sources/book.txt").symlink_to(target)
            with self.assertRaises(PipelineError):
                load_import_manifest(path, root)

    def test_rejects_duplicate_paths_and_directory_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def duplicate(payload):
                payload["answer_files"] = [dict(payload["source_files"][0], kind="answer")]
            path, _ = _write_manifest_package(root, mutate=duplicate)
            with self.assertRaises(PipelineError):
                load_import_manifest(path, root)


if __name__ == "__main__":
    unittest.main()
