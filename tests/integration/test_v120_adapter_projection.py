from __future__ import annotations

import importlib
import importlib.util
import inspect
import errno
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.errors import ConfigurationError, OutputConflictError, PipelineError
from joy_m2.ingest.adapter import adapt_mmd_package, adapt_mmd_package_v120
from joy_m2.ingest.source_mapping import SourceMappingApproval
from joy_m2.ingest.v120_models import (
    V120AdaptedImportPackage,
    V120BatchImportManifest,
)
from joy_m2.ingest.source_mapping import (
    adapt_mmd_package_from_mapping,
    adapt_mmd_package_from_mapping_v120,
)
from tests.unit.test_mmd_source_mapping import (
    SOURCE_ID,
    canonical_json,
    canonical_mapping,
    make_case,
    sha256,
    write_image_archive_case,
)


def _require_module(testcase: unittest.TestCase, name: str):
    testcase.assertIsNotNone(
        importlib.util.find_spec(name),
        f"{name} must exist before its V1.20 API can pass",
    )
    return importlib.import_module(name)


def _assert_signature(
    testcase: unittest.TestCase,
    function: object,
    names: tuple[str, ...],
    annotations: tuple[object, ...],
    return_annotation: object,
) -> None:
    testcase.assertTrue(callable(function))
    signature = inspect.signature(function)
    parameters = tuple(signature.parameters.values())
    testcase.assertEqual(tuple(item.name for item in parameters), names)
    testcase.assertEqual(tuple(item.annotation for item in parameters), annotations)
    testcase.assertTrue(
        all(
            item.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
            and item.default is inspect.Parameter.empty
            for item in parameters
        )
    )
    testcase.assertIs(signature.return_annotation, return_annotation)


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _v120_manifest_bytes(files: dict[str, tuple[bytes, str]]) -> bytes:
    def evidence(kind: str) -> list[dict[str, object]]:
        return [
            {
                "relative_path": path,
                "sha256": hashlib.sha256(content).hexdigest(),
                "size_bytes": len(content),
                "kind": file_kind,
            }
            for path, (content, file_kind) in files.items()
            if file_kind == kind
        ]

    payload = {
        "schema_version": "task10-v120-import-manifest-v1",
        "batch_id": "TASK10A-PROJECTION-01",
        "project": "Joy M2 AI Database",
        "module": "M2",
        "chapter": "Projection fixture",
        "target_release_version": "V1.20",
        "candidate_records": evidence("candidate_json"),
        "source_files": evidence("source"),
        "answer_files": evidence("answer"),
        "image_files": evidence("image"),
        "teacher_notes_files": evidence("teacher_notes"),
        "common_errors_files": evidence("common_errors"),
        "language_policy": "preserve_source_and_store_reviewed_chinese_separately",
        "split_policy": "one_complete_question_per_record",
        "difficulty_policy": "joy_level_1_5",
        "tag_policy": "controlled_primary_type_and_tags",
        "answer_policy": "preserve_source_answer_identity",
        "explanation_policy": "source_or_independently_verified_with_identity",
    }
    return (
        json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        + "\n"
    ).encode("utf-8")


def _write_v120_package(root: Path) -> Path:
    files = {
        "records/candidates.json": (b"[]\n", "candidate_json"),
        "source/original.mmd.txt": (b"source\n", "source"),
    }
    for path, (content, _kind) in files.items():
        target = root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    path = root / "import_manifest.json"
    path.write_bytes(_v120_manifest_bytes(files))
    return path


def _rewrite_manifest(path: Path, payload: dict[str, object]) -> None:
    path.write_bytes(
        (
            json.dumps(payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
            + "\n"
        ).encode("utf-8")
    )


def _manifest_payload(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_bytes())
    assert type(payload) is dict
    return payload


def _write_zip_case(
    root: Path,
    *,
    source_relative_path: str,
    member_order: tuple[str, ...],
    timestamp: tuple[int, int, int, int, int, int],
    permissions: int,
    comment: bytes,
) -> tuple[Path, Path, Path, PipelineConfig]:
    primary = "例題 1\nEnglish.\n中文。\n![](./images/a.jpg)\n".encode("utf-8")
    members = {"source.mmd": primary, "images/a.jpg": b"deterministic image bytes"}
    source_path = root / source_relative_path
    source_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(source_path, "w") as archive:
        archive.comment = comment
        for member in member_order:
            info = zipfile.ZipInfo(member, date_time=timestamp)
            info.create_system = 3
            info.external_attr = permissions << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, members[member])
    selection = {
        "schema_version": "task9b-mmd-adapter-v1",
        "batch_id": "TASK10A-V120-ZIP",
        "source_kind": "mmd_zip",
        "source_sha256": hashlib.sha256(source_path.read_bytes()).hexdigest(),
        "primary_member": "source.mmd",
        "answer_member": None,
        "source_id": "TASK10A-V120-ZIP-SOURCE",
        "chapter": "向量及其应用",
        "expected_candidate_count": 1,
        "selections": [
            {
                "proposed_question_id": "TASK10A-V120-ZIP-01",
                "kind": "example",
                "number": "1",
                "source_section": "例題",
                "language_layout": "english_then_chinese",
                "answer_mapping": "missing_from_source",
                "answer_number": None,
                "expected_image_members": ["images/a.jpg"],
                "primary_type": "向量",
                "tags": ["向量"],
                "tag_status": "proposed",
                "difficulty_level": 3,
                "difficulty_status": "proposed",
            }
        ],
    }
    selection_path = root / "selection" / "selection.json"
    selection_path.parent.mkdir(parents=True, exist_ok=True)
    selection_path.write_bytes(canonical_json(selection))
    output = root / "data" / "staging" / "canonical-output"
    return selection_path, source_path, output, PipelineConfig(root)


CANONICAL_REPRESENTATIVE_V120_MANIFEST = (
    '{"schema_version":"task10-v120-import-manifest-v1","batch_id":"TASK9B-FIXTURE-VECTOR-17","project":"Joy M2 AI Database","module":"M2","chapter":"向量及其应用","target_release_version":"V1.20","candidate_records":[{"relative_path":"records/candidates.json","sha256":"2f63c6d9c50ed0ce76262333ece9c586aecd8f3bfab20fb7905aa0713dee5ba8","size_bytes":122015,"kind":"candidate_json"}],"source_files":[{"relative_path":"source/original.mmd.txt","sha256":"e4939185bc847192b869d90de6ae55df75c0637f0490ea2a4238f8d238c2ce19","size_bytes":76606,"kind":"source"},{"relative_path":"source/source-map.json","sha256":"258d5469a79ba62f7f66e2f121090d5782e2e1a59b54f2db6b1509c91e02bfde","size_bytes":182646,"kind":"source"}],"answer_files":[],"image_files":[{"relative_path":"images/9027aeb0-3964-4138-a178-1092ea22ec8a-32_438_671_1398_659.jpg","sha256":"71a3a938f1ea2cc7efb7ad7bad417092f73387d8e980cb46f2311b4c3edcc589","size_bytes":16201,"kind":"image"},{"relative_path":"images/9027aeb0-3964-4138-a178-1092ea22ec8a-37_573_1010_888_568.jpg","sha256":"7188c2605404fb34c92e09760eabc1ab5e1a59361c36687e925f24fe0370f416","size_bytes":28284,"kind":"image"},{"relative_path":"images/9027aeb0-3964-4138-a178-1092ea22ec8a-38_337_837_334_606.jpg","sha256":"8f254204d1cec17d48ee85f5e446fc10bc95534bfd5f18b17b314dcfb1b91fa4","size_bytes":15566,"kind":"image"},{"relative_path":"images/9027aeb0-3964-4138-a178-1092ea22ec8a-39_527_784_342_678.jpg","sha256":"5ead20afca0dcac305b6b3766a275578a07d9cf413ca98e930651e7cfe5d7d09","size_bytes":23398,"kind":"image"}],"teacher_notes_files":[],"common_errors_files":[],"language_policy":"preserve_source_and_store_reviewed_chinese_separately","split_policy":"one_complete_question_per_record","difficulty_policy":"joy_level_1_5","tag_policy":"controlled_primary_type_and_tags","answer_policy":"preserve_source_answer_identity","explanation_policy":"source_or_independently_verified_with_identity"}\n'
).encode("utf-8")


class V120AdapterProjectionApiTests(unittest.TestCase):
    def test_v120_manifest_loader_is_the_only_public_manifest_symbol(self) -> None:
        module = _require_module(self, "joy_m2.ingest.v120_manifest")
        self.assertEqual(module.__all__, ("load_v120_import_manifest",))
        _assert_signature(
            self,
            getattr(module, "load_v120_import_manifest", None),
            ("path",),
            (Path,),
            V120BatchImportManifest,
        )

    def test_v120_parser_adapter_has_the_exact_versioned_signature(self) -> None:
        module = _require_module(self, "joy_m2.ingest.adapter")
        _assert_signature(
            self,
            getattr(module, "adapt_mmd_package_v120", None),
            ("selection_manifest_path", "source_path", "output_dir", "config"),
            (Path, Path, Path, PipelineConfig),
            V120AdaptedImportPackage,
        )

    def test_v120_explicit_adapter_is_module_scoped_only(self) -> None:
        module = _require_module(self, "joy_m2.ingest.source_mapping")
        self.assertEqual(
            module.__all__,
            (
                "SourceMappingProposal",
                "SourceMappingApproval",
                "propose_mmd_source_mapping",
                "adapt_mmd_package_from_mapping",
                "adapt_mmd_package_from_mapping_v120",
            ),
        )
        _assert_signature(
            self,
            getattr(module, "adapt_mmd_package_from_mapping_v120", None),
            (
                "selection_manifest_path",
                "source_mapping_path",
                "approval",
                "source_path",
                "output_dir",
                "config",
            ),
            (Path, Path, SourceMappingApproval, Path, Path, PipelineConfig),
            V120AdaptedImportPackage,
        )

    def test_explicit_mapping_v120_name_is_not_a_root_ingest_export(self) -> None:
        ingest = importlib.import_module("joy_m2.ingest")
        name = "adapt_mmd_package_from_mapping_v120"
        self.assertNotIn(name, ingest.__all__)
        self.assertFalse(hasattr(ingest, name))


class V120AdapterProjectionBehaviorTests(unittest.TestCase):
    def test_v120_parser_adapter_rejects_a_forged_pipeline_config(self) -> None:
        """Catches forged config fields authorizing output outside staging."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "repo"
            arguments = _write_zip_case(
                root,
                source_relative_path="incoming/source.mmd.zip",
                member_order=("source.mmd", "images/a.jpg"),
                timestamp=(2024, 1, 2, 3, 4, 6),
                permissions=0o100644,
                comment=b"",
            )
            outside = Path(directory) / "outside"
            config = arguments[3]
            object.__setattr__(config, "staging_root", outside.resolve())
            output = outside / "parser-output"

            with self.assertRaises(PipelineError):
                adapt_mmd_package_v120(
                    arguments[0],
                    arguments[1],
                    output,
                    config,
                )
            self.assertFalse(output.exists())

    def test_v120_mapping_adapter_rejects_a_forged_pipeline_config(self) -> None:
        """Catches the explicit-mapping path trusting forged config fields."""
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            root = base / "repo"
            root.mkdir()
            selection_path, source_path, _draft_path, _proposal_dir, config = make_case(root)
            mapping_path = root / "source_mapping.json"
            mapping_bytes = canonical_json(canonical_mapping())
            mapping_path.write_bytes(mapping_bytes)
            mapping_digest = sha256(mapping_bytes)
            approval = SourceMappingApproval(
                SOURCE_ID,
                mapping_digest,
                f"USER APPROVED SOURCE MAPPING {SOURCE_ID} {mapping_digest}",
            )
            outside = base / "outside"
            object.__setattr__(config, "staging_root", outside.resolve())
            output = outside / "mapping-output"

            with self.assertRaises(PipelineError):
                adapt_mmd_package_from_mapping_v120(
                    selection_path,
                    mapping_path,
                    approval,
                    source_path,
                    output,
                    config,
                )
            self.assertFalse(output.exists())

    def test_parser_projection_changes_only_versioned_manifest_authority(self) -> None:
        """Catches a V1.20 projector that changes Task 9B source output bytes."""
        fixtures = ROOT / "tests/fixtures/task9b/representative"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = adapt_mmd_package(
                fixtures / "selection.json",
                fixtures / "vector.mmd",
                root / "data/staging/v119",
                PipelineConfig(root),
            )
            package = adapt_mmd_package_v120(
                fixtures / "selection.json",
                fixtures / "vector.mmd",
                root / "data/staging/v120",
                PipelineConfig(root),
            )

            self.assertIs(type(package), V120AdaptedImportPackage)
            legacy_files = _tree_bytes(legacy.package_root)
            v120_files = _tree_bytes(package.package_root)
            self.assertEqual(
                {key: value for key, value in legacy_files.items() if key != "import_manifest.json"},
                {key: value for key, value in v120_files.items() if key != "import_manifest.json"},
            )
            manifest_payload = json.loads(v120_files["import_manifest.json"])
            self.assertEqual(manifest_payload["schema_version"], "task10-v120-import-manifest-v1")
            self.assertEqual(manifest_payload["target_release_version"], "V1.20")
            self.assertEqual(
                v120_files["import_manifest.json"],
                CANONICAL_REPRESENTATIVE_V120_MANIFEST,
            )
            self.assertEqual(package.manifest_path, package.package_root / "import_manifest.json")
            loaded = importlib.import_module("joy_m2.ingest.v120_manifest").load_v120_import_manifest(package.manifest_path)
            self.assertEqual(package.manifest, loaded)

    def test_explicit_mapping_projection_matches_parser_projection_bytes(self) -> None:
        """Catches divergent V1.20 outputs between reviewed parser and mapping paths."""
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path, source_path, _draft_path, _proposal_dir, config = make_case(root)
            mapping_path = root / "source_mapping.json"
            mapping_bytes = canonical_json(canonical_mapping())
            mapping_path.write_bytes(mapping_bytes)
            approval = SourceMappingApproval(
                SOURCE_ID,
                sha256(mapping_bytes),
                f"USER APPROVED SOURCE MAPPING {SOURCE_ID} {sha256(mapping_bytes)}",
            )
            legacy = adapt_mmd_package_from_mapping(
                selection_path, mapping_path, approval, source_path,
                root / "data/staging/v119", config,
            )
            package = adapt_mmd_package_from_mapping_v120(
                selection_path, mapping_path, approval, source_path,
                root / "data/staging/v120", config,
            )

            self.assertIs(type(package), V120AdaptedImportPackage)
            legacy_files = _tree_bytes(legacy.package_root)
            v120_files = _tree_bytes(package.package_root)
            self.assertEqual(
                {key: value for key, value in legacy_files.items() if key != "import_manifest.json"},
                {key: value for key, value in v120_files.items() if key != "import_manifest.json"},
            )
            self.assertEqual(package.manifest.target_release_version, "V1.20")
            self.assertEqual(package.manifest.schema_version, "task10-v120-import-manifest-v1")

    def test_v120_manifest_loader_decodes_only_complete_v120_packages(self) -> None:
        """Catches a decoder that accepts a V1.19 manifest or loses evidence."""
        loader = importlib.import_module("joy_m2.ingest.v120_manifest").load_v120_import_manifest
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manifest_path = _write_v120_package(root)
            manifest = loader(manifest_path)
            self.assertIs(type(manifest), V120BatchImportManifest)
            self.assertEqual(manifest.batch_id, "TASK10A-PROJECTION-01")
            self.assertEqual(manifest.target_release_version, "V1.20")
            self.assertEqual(
                manifest.candidate_records[0].relative_path,
                "records/candidates.json",
            )

    def test_v120_manifest_loader_rejects_syntax_and_duplicate_keys_after_filename_validation(self) -> None:
        """Catches a decoder that stops at a filename gate instead of strict JSON."""
        loader = importlib.import_module("joy_m2.ingest.v120_manifest").load_v120_import_manifest
        cases = (
            ("invalid_utf8", b"\xff", "manifest must be valid strict UTF-8 JSON"),
            ("invalid_json", b"{", "manifest must be valid strict UTF-8 JSON"),
            (
                "top_level_duplicate",
                b'{"schema_version":"task10-v120-import-manifest-v1",'
                b'"schema_version":"task10-v120-import-manifest-v1"}',
                "manifest must not contain duplicate keys",
            ),
        )
        for label, content, message in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                path = _write_v120_package(Path(directory))
                path.write_bytes(content)
                with self.assertRaisesRegex(PipelineError, f"^{message}$"):
                    loader(path)
        with tempfile.TemporaryDirectory() as directory:
            path = _write_v120_package(Path(directory))
            path.write_bytes(
                path.read_bytes().replace(
                    b'"relative_path":"records/candidates.json",',
                    b'"relative_path":"records/candidates.json",'
                    b'"relative_path":"records/candidates.json",',
                    1,
                )
            )
            with self.assertRaisesRegex(PipelineError, "^manifest must not contain duplicate keys$"):
                loader(path)

    def test_v120_manifest_loader_rejects_exact_schema_type_and_evidence_mutations(self) -> None:
        """Catches missing strict V1.20 key, type, kind, size, or digest checks."""
        loader = importlib.import_module("joy_m2.ingest.v120_manifest").load_v120_import_manifest

        def mutate_missing(payload: dict[str, object]) -> None:
            del payload["chapter"]

        def mutate_extra(payload: dict[str, object]) -> None:
            payload["extra"] = "forbidden"

        def mutate_scalar(payload: dict[str, object]) -> None:
            payload["batch_id"] = 1

        def mutate_container(payload: dict[str, object]) -> None:
            payload["candidate_records"] = {}

        def mutate_element(payload: dict[str, object]) -> None:
            payload["candidate_records"] = [None]

        def mutate_kind(payload: dict[str, object]) -> None:
            payload["candidate_records"][0]["kind"] = "source"  # type: ignore[index]

        def mutate_sha(payload: dict[str, object]) -> None:
            payload["candidate_records"][0]["sha256"] = "0" * 64  # type: ignore[index]

        def mutate_size(payload: dict[str, object]) -> None:
            payload["candidate_records"][0]["size_bytes"] = 1  # type: ignore[index]

        cases = (
            ("missing_key", mutate_missing, "manifest must have exact ordered fields"),
            ("extra_key", mutate_extra, "manifest must have exact ordered fields"),
            ("wrong_scalar", mutate_scalar, "manifest does not satisfy V1.20 authority"),
            ("wrong_container", mutate_container, "candidate_records must be a JSON array"),
            ("wrong_element", mutate_element, "candidate_records entry must have exact ordered fields"),
            ("evidence_kind", mutate_kind, "candidate_records has the wrong file kind"),
            ("evidence_sha", mutate_sha, "declared package file SHA-256 does not match"),
            ("evidence_size", mutate_size, "declared package file size does not match"),
        )
        for label, mutation, message in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                path = _write_v120_package(Path(directory))
                payload = _manifest_payload(path)
                mutation(payload)
                _rewrite_manifest(path, payload)
                with self.assertRaisesRegex(PipelineError, f"^{message}$"):
                    loader(path)

    def test_v120_manifest_loader_rejects_single_inventory_mutations(self) -> None:
        """Catches a decoder that omits file evidence or complete inventory checks."""
        loader = importlib.import_module("joy_m2.ingest.v120_manifest").load_v120_import_manifest

        def missing(root: Path) -> None:
            (root / "records/candidates.json").unlink()

        def extra(root: Path) -> None:
            (root / "orphan.bin").write_bytes(b"orphan")

        def non_regular(root: Path) -> None:
            (root / "records/candidates.json").unlink()
            (root / "records/candidates.json").mkdir()

        def symlink(root: Path) -> None:
            target = root / "records/target.json"
            target.write_bytes(b"[]\n")
            (root / "records/candidates.json").unlink()
            (root / "records/candidates.json").symlink_to(target.name)

        cases = (
            ("missing", missing, "declared package file is missing"),
            ("extra", extra, "package inventory differs from declared manifest files"),
            ("non_regular", non_regular, "declared package file is unsafe or not a regular file"),
            ("symlink", symlink, "declared package file is unsafe or not a regular file"),
        )
        for label, mutation, message in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                path = _write_v120_package(root)
                mutation(root)
                with self.assertRaisesRegex(PipelineError, f"^{message}$"):
                    loader(path)
        legacy_manifest = ROOT / "tests/fixtures/task9b/golden/import_manifest.json"
        with self.assertRaisesRegex(PipelineError, "^manifest does not satisfy V1.20 authority$"):
            loader(legacy_manifest)

    def test_separate_answer_projection_keeps_answer_bytes_identical_to_v119(self) -> None:
        """Catches a V1.20 projector that drops or changes selected answer bytes."""
        fixtures = ROOT / "tests/fixtures/task9b/representative"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            legacy = adapt_mmd_package(
                fixtures / "separate-answer-selection.json",
                fixtures / "separate-answer.mmd.zip",
                root / "data/staging/v119",
                PipelineConfig(root),
            )
            v120 = adapt_mmd_package_v120(
                fixtures / "separate-answer-selection.json",
                fixtures / "separate-answer.mmd.zip",
                root / "data/staging/v120",
                PipelineConfig(root),
            )
            self.assertEqual(
                {key: value for key, value in _tree_bytes(legacy.package_root).items() if key != "import_manifest.json"},
                {key: value for key, value in _tree_bytes(v120.package_root).items() if key != "import_manifest.json"},
            )
            self.assertEqual(
                (v120.package_root / "answers/answer.mmd.txt").read_bytes(),
                (legacy.package_root / "answers/answer.mmd.txt").read_bytes(),
            )

    def test_v120_zip_member_metadata_and_roots_do_not_change_canonical_tree(self) -> None:
        """Catches outer-ZIP metadata or runtime roots entering V1.20 identity."""
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            left_root = base / "left-root"
            right_root = base / "right-root"
            left_args = _write_zip_case(
                left_root,
                source_relative_path="incoming/a/source.mmd.zip",
                member_order=("source.mmd", "images/a.jpg"),
                timestamp=(1980, 1, 1, 0, 0, 0),
                permissions=0o100644,
                comment=b"first",
            )
            right_args = _write_zip_case(
                right_root,
                source_relative_path="different-input/b/archive.zip",
                member_order=("images/a.jpg", "source.mmd"),
                timestamp=(2024, 6, 7, 8, 9, 10),
                permissions=0o100600,
                comment=b"second",
            )
            left = adapt_mmd_package_v120(*left_args)
            right = adapt_mmd_package_v120(*right_args)
            left_tree = _tree_bytes(left.package_root)
            right_tree = _tree_bytes(right.package_root)
            left_digest = hashlib.sha256(left_args[1].read_bytes()).hexdigest()
            right_digest = hashlib.sha256(right_args[1].read_bytes()).hexdigest()
            self.assertNotEqual(left_digest, right_digest)
            self.assertEqual(left_tree, right_tree)
            self.assertEqual(left.manifest, right.manifest)
            joined = b"\n".join(left_tree.values())
            for prohibited in (str(left_root), str(right_root), left_digest, right_digest):
                self.assertNotIn(prohibited.encode("utf-8"), joined)

    def test_v120_explicit_mapping_zip_metadata_and_roots_do_not_change_canonical_tree(self) -> None:
        """Catches ZIP metadata entering the explicit V1.20 projection identity."""
        observations: list[tuple[str, dict[str, bytes], V120BatchImportManifest]] = []
        for timestamp, reverse_order in (
            ((2024, 1, 2, 3, 4, 6), False),
            ((2025, 6, 8, 9, 10, 12), True),
        ):
            with self.subTest(timestamp=timestamp, reverse_order=reverse_order), tempfile.TemporaryDirectory() as directory:
                root = Path(directory) / "independent-root"
                root.mkdir()
                outer_digest, invoke_v119 = write_image_archive_case(
                    self,
                    root,
                    timestamp=timestamp,
                    reverse_order=reverse_order,
                )
                invoke_v119("v119")
                mapping_path = root / "source_mapping.json"
                mapping_digest = sha256(mapping_path.read_bytes())
                approval = SourceMappingApproval(
                    SOURCE_ID,
                    mapping_digest,
                    f"USER APPROVED SOURCE MAPPING {SOURCE_ID} {mapping_digest}",
                )
                package = adapt_mmd_package_from_mapping_v120(
                    root / "selection.json",
                    mapping_path,
                    approval,
                    root / "source.mmd.zip",
                    root / "data/staging/v120",
                    PipelineConfig(root),
                )
                tree = _tree_bytes(package.package_root)
                joined = b"\n".join(tree.values())
                self.assertNotIn(outer_digest.encode("ascii"), joined)
                self.assertNotIn(str(root).encode("utf-8"), joined)
                observations.append((outer_digest, tree, package.manifest))
        self.assertNotEqual(observations[0][0], observations[1][0])
        self.assertEqual(observations[0][1], observations[1][1])
        self.assertEqual(observations[0][2], observations[1][2])

    def test_v120_projection_refuses_existing_output_without_mutation(self) -> None:
        """Catches a projector that overwrites an existing staging destination."""
        fixtures = ROOT / "tests/fixtures/task9b/representative"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "data/staging/existing"
            output.mkdir(parents=True)
            sentinel = output / "keep.txt"
            sentinel.write_bytes(b"keep")
            with self.assertRaises(OutputConflictError):
                adapt_mmd_package_v120(
                    fixtures / "selection.json",
                    fixtures / "vector.mmd",
                    output,
                    PipelineConfig(root),
                )
            self.assertEqual(sentinel.read_bytes(), b"keep")
            self.assertEqual(_tree_bytes(output), {"keep.txt": b"keep"})

    def test_v120_projection_losing_no_replace_race_preserves_destination(self) -> None:
        """Catches a publication rename that replaces a newly appeared directory."""
        fixtures = ROOT / "tests/fixtures/task9b/representative"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / "data/staging/raced"

            def lose_race(_source: Path, destination: Path) -> None:
                destination.mkdir()
                (destination / "winner.txt").write_bytes(b"winner")
                raise FileExistsError(errno.EEXIST, "destination appeared")

            with mock.patch(
                "joy_m2.ingest.v120_projection.atomic_rename_no_replace",
                create=True,
                side_effect=lose_race,
            ):
                with self.assertRaises(OutputConflictError):
                    adapt_mmd_package_v120(
                        fixtures / "selection.json",
                        fixtures / "vector.mmd",
                        output,
                        PipelineConfig(root),
                    )
            self.assertEqual(_tree_bytes(output), {"winner.txt": b"winner"})
