"""Behavior contract for V1.20 multi-batch import preflight."""

from __future__ import annotations

import importlib
import importlib.util
import inspect
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
from types import SimpleNamespace
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.errors import PipelineError
from joy_m2.ingest.models import ImportCandidate
from joy_m2.ingest.v120_manifest import load_v120_import_manifest
from joy_m2.ingest.v120_models import (
    V120ApprovedBatch,
    V120CandidateContract,
    V120CandidateVerificationRequest,
    V120EffectiveState,
    V120ImportApproval,
    V120ImportPreflightReport,
    V120ImportPreflightResult,
    V120PreflightRequest,
)
from joy_m2.ingest.v120_preflight import preflight_v120_import
from joy_m2.models import ArtifactRef


FIXTURES = ROOT / "tests/fixtures/task10a"
BASELINE = ROOT / "releases/V1.19/Joy_M2_Complete_Question_DB_V1_19.sqlite3"
V118 = ROOT / "releases/V1.18/Joy_M2_Complete_Question_DB_V1_18.sqlite3"
BASELINE_SHA = "5a7f1ca01c29dc638fb592c668ea9f597551f94d73001898587b187bdbe490ff"
BASELINE_SIZE = 9_478_144
BASELINE_MANIFEST_SHA = "cd048408df5e062592d5ed8553b3461860c876b0264660ab65c78c428584a510"
BASELINE_RELEASE_DIGEST = "7246d099028e350ea5074524a808c9eb87e83e3df218349040eaf20f0109a69d"
GENESIS = "4ff624aca875b0191fe8a617516d2919c6d700ce69c5a3b5d236adcf7ecc59f1"
SHARED_IMAGE_SHA = "88709ade5a0e95cbfbb8280ee4995231fe3b36888e0a0af57110d2e231120ce7"
A_MANIFEST_SHA = "ea2fe2214a4596019c2703d9ca9cafb5e52cda4085dc61b9abc8b41e8b162a10"
A_PREFLIGHT_SHA = "0a6c4a652d4bcaf1ddb2765c59accdbe1f2f4a1d129bd2c8e056777e4125e700"
REFERENCE_ID = "M2QD-DA-EXAMPLE-Q1"
REFERENCE_SOURCE_ID = "M2QD-DIFFERENTIATION-APPLICATIONS"
REFERENCE_NUMBER = "EXAMPLE-Q1"
REFERENCE_SECTION = "教材例题"
REFERENCE_FRAGMENT = "7ca9b7902bf8efd929145e64c5d4a1aa11b2da06028e4e2123026a09da640e89"
REFERENCE_NORMALIZED = "04c2b5df26e1f6440412a97203a7a2894819069c9a878493389dcb53f8d9180a"
IMAGE_REFERENCE_ID = "M2QD-DA-PARTB-Q4"
IMAGE_SOURCE_ID = "M2QD-DIFFERENTIATION-APPLICATIONS"
IMAGE_NUMBER = "PARTB-Q4"
IMAGE_SECTION = "乙部特训"
FORMAL_IMAGE_PATH = "extracted_reference/source_images/M2QD_DA_PARTB_Q4_Figure1.jpg"
FORMAL_IMAGE_ROLE = "required_question_figure"
FORMAL_IMAGE_SHA = "eeddd1592eba7c505e3ac6fb484da4fa695b328dce5de4888ea340936869b9ae"


def _canonical(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _contract() -> V120CandidateContract:
    return V120CandidateContract(
        "V1.20", "V1.19", 502, BASELINE_SHA, BASELINE_SIZE,
        BASELINE_MANIFEST_SHA, 3242, BASELINE_RELEASE_DIGEST,
        "task10-v120-import-manifest-v1", "task10-v120-preflight-v1",
        "task10-v120-import-approval-v1", "task10-v120-candidate-manifest-v1",
        "task10-v120-candidate-v1", "task10-v120-candidate-identity-v1",
        "task10-v120-rollback-v1", 120, "Joy_M2_V1.20_candidate.sqlite3",
        "candidate_manifest.json", "SHA256SUMS", "rollback.json",
        "authority/batches", "images/sha256", "formal_complete_questions_v119",
        (
            "task10_v120_batch_ledger_v1", "task10_v120_candidates_v1",
            "task10_v120_images_v1", "task10_v120_taxonomy_v1",
        ),
        ("task10_candidate_questions_v120",),
    )


def _baseline_ref(path: Path = BASELINE) -> ArtifactRef:
    return ArtifactRef(path, BASELINE_SHA, BASELINE_SIZE, "sqlite")


def _fixture(letter: str):
    root = FIXTURES / f"v120-batch-{letter}"
    return root, load_v120_import_manifest(root / "import_manifest.json")


def _request(letter: str, *, parent: V120CandidateVerificationRequest | None = None):
    root, manifest = _fixture(letter)
    return V120PreflightRequest(manifest, root, _baseline_ref(), parent, _contract())


def _fingerprint(root: Path) -> tuple[tuple[str, str, int], ...]:
    return tuple(
        (
            path.relative_to(root).as_posix(),
            _sha(path.read_bytes()),
            path.stat().st_size,
        )
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )


def _staging_temp() -> tempfile.TemporaryDirectory:
    staging = ROOT / "data/staging"
    staging.mkdir(parents=True, exist_ok=True)
    return tempfile.TemporaryDirectory(prefix="task10a-parent-red-", dir=staging)


def _copy_with_physical_order(
    source: Path,
    destination: Path,
    *,
    reverse: bool,
) -> tuple[str, ...]:
    destination.mkdir(parents=True)
    files = sorted((path for path in source.rglob("*") if path.is_file()), reverse=reverse)
    for path in files:
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
    return tuple(path.relative_to(source).as_posix() for path in files)


def _rewrite_record(root: Path, updates: dict[str, object]) -> None:
    record_path = root / "records/candidates.json"
    records = json.loads(record_path.read_text(encoding="utf-8"))
    records[0].update(updates)
    record_bytes = json.dumps(
        records, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8") + b"\n"
    record_path.write_bytes(record_bytes)
    manifest_path = root / "import_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["candidate_records"][0]["sha256"] = _sha(record_bytes)
    manifest["candidate_records"][0]["size_bytes"] = len(record_bytes)
    manifest_path.write_bytes(
        json.dumps(
            manifest, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ).encode("utf-8") + b"\n"
    )


def _rewrite_candidate_payload(root: Path, payload: object | bytes) -> None:
    record_path = root / "records/candidates.json"
    if type(payload) is bytes:
        record_bytes = payload
    else:
        record_bytes = json.dumps(
            payload, ensure_ascii=False, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8") + b"\n"
    record_path.write_bytes(record_bytes)
    manifest_path = root / "import_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["candidate_records"][0]["sha256"] = _sha(record_bytes)
    manifest["candidate_records"][0]["size_bytes"] = len(record_bytes)
    manifest_path.write_bytes(
        json.dumps(
            manifest, ensure_ascii=False, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8") + b"\n"
    )


def _add_declared_file(
    root: Path,
    group: str,
    relative_path: str,
    kind: str,
    data: bytes,
) -> None:
    path = root / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    manifest_path = root / "import_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest[group].append({
        "relative_path": relative_path,
        "sha256": _sha(data),
        "size_bytes": len(data),
        "kind": kind,
    })
    manifest_path.write_bytes(
        json.dumps(
            manifest, ensure_ascii=False, separators=(",", ":"), allow_nan=False,
        ).encode("utf-8") + b"\n"
    )


def _rename_declared_image(root: Path, new_relative_path: str) -> None:
    manifest_path = root / "import_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    old_relative_path = manifest["image_files"][0]["relative_path"]
    old_path = root / old_relative_path
    new_path = root / new_relative_path
    new_path.parent.mkdir(parents=True, exist_ok=True)
    old_path.rename(new_path)
    manifest["image_files"][0]["relative_path"] = new_relative_path
    manifest_path.write_bytes(
        json.dumps(
            manifest, ensure_ascii=False, separators=(",", ":"), allow_nan=False
        ).encode("utf-8") + b"\n"
    )


def _remove_declared_images(root: Path) -> None:
    manifest_path = root / "import_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for item in manifest["image_files"]:
        (root / item["relative_path"]).unlink()
    manifest["image_files"] = []
    manifest_path.write_bytes(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
    )


def _replace_declared_image_bytes(root: Path, data: bytes) -> None:
    manifest_path = root / "import_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    evidence = manifest["image_files"][0]
    (root / evidence["relative_path"]).write_bytes(data)
    evidence["sha256"] = _sha(data)
    evidence["size_bytes"] = len(data)
    manifest_path.write_bytes(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
    )


def _reverse_manifest_image_inventory(root: Path) -> None:
    manifest_path = root / "import_manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["image_files"].reverse()
    manifest_path.write_bytes(
        json.dumps(manifest, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8") + b"\n"
    )


def _literal_a_candidate() -> dict[str, object]:
    return {
        "proposed_question_id": "TASK10-A-001",
        "source_id": "TASK10-SOURCE-A",
        "source_question_number": "A1",
        "source_section": "Synthetic batch A",
        "source_fragment_hash": "a" * 64,
        "normalized_text_sha256": "a44e747ec06cd38e0862ceb6c9f88ca7646b55a8e9964a1568ccbab8e4e91339",
        "question_text_original": "Solve 2x + 3 = 11.",
        "question_text_zh": "解方程 2x + 3 = 11。",
        "translation_status": "source_present",
        "translation_evidence": "source:source/source.txt#translation-A1",
        "solution_original": "x = 4",
        "solution_verified": "x = 4",
        "answer_status": "source_provided",
        "explanation_text": "Subtract 3, then divide by 2.",
        "explanation_status": "source_present",
        "explanation_evidence": "source:source/source.txt#explanation-A1",
        "image_paths": ["images/shared.svg"],
        "image_sha256s": [SHARED_IMAGE_SHA],
        "image_roles": ["question"],
        "primary_type": "代数",
        "tags": ["一元一次方程"],
        "tag_status": "source_provided",
        "difficulty_level": 1,
        "difficulty_status": "source_provided",
        "enrichment_status": "complete",
    }


def _literal_a_payload() -> dict[str, object]:
    files = [
        {"relative_path": "answers/answer.txt", "sha256": "5a5352d4fa05957bb21db0c224e9a2f094b774536c7c1e08442b980eed17bf87", "size_bytes": 33, "kind": "answer"},
        {"relative_path": "images/shared.svg", "sha256": SHARED_IMAGE_SHA, "size_bytes": 92, "kind": "image"},
        {"relative_path": "records/candidates.json", "sha256": "700effd5a5eafb61e96b1c8ab70ae52eb8b5bbe30200f3df64d8ab4b2c4d1b8d", "size_bytes": 906, "kind": "candidate_json"},
        {"relative_path": "source/source.txt", "sha256": "b9dbc7c79d0617f333033e2b27aa92e153378aeb8bfa7baea98d825fef89720c", "size_bytes": 39, "kind": "source"},
    ]
    report = {
        "batch_id": "TASK10-A", "status": "READY FOR USER IMPORT APPROVAL",
        "manifest_sha256": A_MANIFEST_SHA, "baseline_version": "V1.19",
        "baseline_release_digest": BASELINE_RELEASE_DIGEST,
        "baseline_question_count": 502, "target_release_version": "V1.20",
        "parent_candidate_digest": GENESIS, "parent_batch_count": 0,
        "before_count": 502, "detected_count": 1, "new_candidate_count": 1,
        "duplicate_count": 0, "rejected_count": 0, "ambiguous_count": 0,
        "approved_count": 0, "projected_after_count": 503,
        "readable_files": [item["relative_path"] for item in files],
        "unreadable_files": [], "unsupported_files": [],
        "teacher_notes_file_count": 0, "common_errors_file_count": 0,
        "ambiguous_splits": [], "missing_answers": [], "missing_explanations": [],
        "incomplete_enrichments": [], "missing_images": [], "orphan_images": [],
        "level_counts": [[1, 1]], "proposed_ids": ["TASK10-A-001"],
        "adaptations": [], "warnings": [], "blocking_errors": [],
    }
    return {
        "schema": "task10-v120-preflight-v1",
        "batch_id": "TASK10-A", "target_release_version": "V1.20",
        "baseline": {
            "release_version": "V1.19", "question_count": 502,
            "database_schema": "task9-v119-formal-v1",
            "sqlite": {"sha256": BASELINE_SHA, "size_bytes": BASELINE_SIZE, "kind": "sqlite"},
            "manifest": {"sha256": BASELINE_MANIFEST_SHA, "size_bytes": 3242, "kind": "manifest"},
            "release_digest": BASELINE_RELEASE_DIGEST,
        },
        "parent_state": {"candidate_digest": GENESIS, "batch_count": 0, "candidate_count": 0, "projected_question_count": 502},
        "manifest_policies": {
            "schema_version": "task10-v120-import-manifest-v1", "project": "Joy M2 AI Database",
            "module": "M2", "chapter": "Synthetic batch A",
            "language_policy": "preserve_source_and_store_reviewed_chinese_separately",
            "split_policy": "one_complete_question_per_record", "difficulty_policy": "joy_level_1_5",
            "tag_policy": "controlled_primary_type_and_tags", "answer_policy": "preserve_source_answer_identity",
            "explanation_policy": "source_or_independently_verified_with_identity",
        },
        "candidate_record_order": ["records/candidates.json"], "file_evidence": files,
        "candidates": [_literal_a_candidate()], "issues": [],
        "duplicate_classifications": [{"candidate_id": "TASK10-A-001", "classification": "new_candidate", "reference_question_id": None, "evidence": None}],
        "image_evidence": [{"proposed_question_id": "TASK10-A-001", "relative_path": "images/shared.svg", "sha256": SHARED_IMAGE_SHA, "size_bytes": 92, "kind": "image", "role": "question"}],
        "report": report,
    }


def _plain_candidate(candidate: ImportCandidate) -> dict[str, object]:
    return {
        name: list(value) if isinstance(value, tuple) else value
        for name in (
            "proposed_question_id", "source_id", "source_question_number", "source_section",
            "source_fragment_hash", "normalized_text_sha256", "question_text_original",
            "question_text_zh", "translation_status", "translation_evidence", "solution_original",
            "solution_verified", "answer_status", "explanation_text", "explanation_status",
            "explanation_evidence", "image_paths", "image_sha256s", "image_roles", "primary_type",
            "tags", "tag_status", "difficulty_level", "difficulty_status", "enrichment_status",
        )
        for value in (getattr(candidate, name),)
    }


def _plain_value(value: object) -> object:
    if isinstance(value, tuple):
        return [_plain_value(item) for item in value]
    if hasattr(value, "__dict__"):
        return {name: _plain_value(item) for name, item in value.__dict__.items()}
    return value


def _literal_a_approved_batch() -> V120ApprovedBatch:
    root, manifest = _fixture("a")
    candidate = ImportCandidate(**_literal_a_candidate())
    payload = _literal_a_payload()
    report_values = dict(payload["report"])
    report_values["preflight_sha256"] = A_PREFLIGHT_SHA
    report = V120ImportPreflightReport(**report_values)
    state = V120EffectiveState(_baseline_ref(), GENESIS, (), 0, 502)
    result = V120ImportPreflightResult(manifest, state, (candidate,), (), report)
    approval = V120ImportApproval(
        "TASK10-A", A_PREFLIGHT_SHA, "V1.20", GENESIS,
        f"USER APPROVED IMPORT BATCH TASK10-A {A_PREFLIGHT_SHA} V1.20 PARENT {GENESIS}",
    )
    return V120ApprovedBatch(result, root, approval)


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
    testcase.assertEqual(tuple(parameter.name for parameter in parameters), names)
    testcase.assertEqual(tuple(parameter.annotation for parameter in parameters), annotations)
    testcase.assertTrue(
        all(
            parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
            and parameter.default is inspect.Parameter.empty
            for parameter in parameters
        )
    )
    testcase.assertIs(signature.return_annotation, return_annotation)


class V120PreflightApiTests(unittest.TestCase):
    def test_preflight_module_exposes_only_the_exact_versioned_api(self) -> None:
        module = _require_module(self, "joy_m2.ingest.v120_preflight")
        self.assertEqual(module.__all__, ("preflight_v120_import",))
        _assert_signature(
            self,
            getattr(module, "preflight_v120_import", None),
            ("request", "config"),
            (V120PreflightRequest, PipelineConfig),
            V120ImportPreflightResult,
        )

    def test_bypassed_frozen_request_and_config_are_rejected_at_entry(self) -> None:
        forged_contract = _request("a")
        object.__setattr__(
            forged_contract,
            "contract",
            SimpleNamespace(**forged_contract.contract.__dict__),
        )
        forged_package = _request("a")
        object.__setattr__(forged_package, "package_root", str(forged_package.package_root))
        forged_config = PipelineConfig(ROOT)
        object.__setattr__(forged_config, "staging_root", Path("/tmp/forged-staging"))

        for label, request, config in (
            ("contract", forged_contract, PipelineConfig(ROOT)),
            ("package_root", forged_package, PipelineConfig(ROOT)),
            ("config", _request("a"), forged_config),
        ):
            with self.subTest(label=label), self.assertRaises(PipelineError):
                preflight_v120_import(request, config)


class V120GenesisPreflightTests(unittest.TestCase):
    """Phase C/E REDs: exact V1.19 genesis state and first READY batch."""

    def test_first_batch_closes_exact_genesis_state_counts_and_read_only_boundary(self) -> None:
        request = _request("a")
        before_fixture = _fingerprint(request.package_root)
        before_baseline = _fingerprint(BASELINE.parent)
        result = preflight_v120_import(request, PipelineConfig(ROOT))
        self.assertEqual(result.effective_state.candidate_digest, GENESIS)
        self.assertEqual(result.effective_state.batch_ledger, ())
        self.assertEqual(result.effective_state.candidate_count, 0)
        self.assertEqual(result.effective_state.projected_question_count, 502)
        self.assertEqual(result.report.parent_batch_count, 0)
        self.assertEqual(result.report.before_count, 502)
        self.assertEqual(result.report.projected_after_count, 503)
        self.assertEqual(result.report.status, "READY FOR USER IMPORT APPROVAL")
        self.assertEqual(_fingerprint(request.package_root), before_fixture)
        self.assertEqual(_fingerprint(BASELINE.parent), before_baseline)

    def test_first_batch_matches_independent_literal_manifest_and_13_key_preflight_oracles(self) -> None:
        payload = _literal_a_payload()
        self.assertEqual(len(payload), 13)
        self.assertEqual(_sha(_canonical(payload) + b"\n"), A_PREFLIGHT_SHA)
        result = preflight_v120_import(_request("a"), PipelineConfig(ROOT))
        self.assertEqual(result.report.manifest_sha256, A_MANIFEST_SHA)
        self.assertEqual(result.report.preflight_sha256, A_PREFLIGHT_SHA)
        self.assertEqual(len(result.candidates), 1)
        self.assertEqual(_plain_candidate(result.candidates[0]), _literal_a_candidate())
        self.assertEqual(result.issues, ())
        actual_report = dict(_plain_value(result.report))
        actual_report.pop("preflight_sha256")
        self.assertEqual(actual_report, payload["report"])

    def test_equivalent_fixture_bytes_under_different_roots_have_identical_authority(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            first = temporary / "first"
            second = temporary / "unrelated/deep/second"
            _copy_with_physical_order(FIXTURES / "v120-batch-a", first, reverse=True)
            _copy_with_physical_order(FIXTURES / "v120-batch-a", second, reverse=True)
            first_manifest = load_v120_import_manifest(first / "import_manifest.json")
            second_manifest = load_v120_import_manifest(second / "import_manifest.json")
            first_result = preflight_v120_import(
                V120PreflightRequest(first_manifest, first, _baseline_ref(), None, _contract()),
                PipelineConfig(ROOT),
            )
            second_result = preflight_v120_import(
                V120PreflightRequest(second_manifest, second, _baseline_ref(), None, _contract()),
                PipelineConfig(ROOT),
            )
        self.assertEqual(first_result.report.manifest_sha256, A_MANIFEST_SHA)
        self.assertEqual(first_result.report.preflight_sha256, A_PREFLIGHT_SHA)
        self.assertEqual(first_result, second_result)

    def test_dual_image_physical_creation_order_is_nonsemantic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            first = temporary / "first-c"
            reordered = temporary / "reordered-c"
            forward_order = _copy_with_physical_order(
                FIXTURES / "v120-batch-c", first, reverse=False,
            )
            reverse_order = _copy_with_physical_order(
                FIXTURES / "v120-batch-c", reordered, reverse=True,
            )
            self.assertEqual(forward_order, tuple(reversed(reverse_order)))
            self.assertEqual(
                (first / "import_manifest.json").read_bytes(),
                (reordered / "import_manifest.json").read_bytes(),
            )
            first_manifest = load_v120_import_manifest(first / "import_manifest.json")
            reordered_manifest = load_v120_import_manifest(reordered / "import_manifest.json")
            self.assertEqual(
                tuple(item.relative_path for item in first_manifest.image_files),
                ("images/shared-c1.svg", "images/shared-c2.svg"),
            )
            self.assertEqual(
                tuple(item.relative_path for item in reordered_manifest.image_files),
                ("images/shared-c1.svg", "images/shared-c2.svg"),
            )
            first_result = preflight_v120_import(
                V120PreflightRequest(first_manifest, first, _baseline_ref(), None, _contract()),
                PipelineConfig(ROOT),
            )
            reordered_result = preflight_v120_import(
                V120PreflightRequest(reordered_manifest, reordered, _baseline_ref(), None, _contract()),
                PipelineConfig(ROOT),
            )
        self.assertEqual(first_result.report.manifest_sha256, reordered_result.report.manifest_sha256)
        self.assertEqual(first_result.report.preflight_sha256, reordered_result.report.preflight_sha256)
        self.assertEqual(first_result.candidates, reordered_result.candidates)

    def test_dual_image_manifest_inventory_order_is_semantic(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            temporary = Path(directory)
            original = temporary / "original-c"
            reordered = temporary / "reordered-c"
            original_creation = _copy_with_physical_order(
                FIXTURES / "v120-batch-c", original, reverse=False,
            )
            reordered_creation = _copy_with_physical_order(
                FIXTURES / "v120-batch-c", reordered, reverse=False,
            )
            self.assertEqual(original_creation, reordered_creation)
            _reverse_manifest_image_inventory(reordered)
            original_manifest = load_v120_import_manifest(original / "import_manifest.json")
            reordered_manifest = load_v120_import_manifest(reordered / "import_manifest.json")
            self.assertEqual(
                tuple(item.relative_path for item in original_manifest.image_files),
                ("images/shared-c1.svg", "images/shared-c2.svg"),
            )
            self.assertEqual(
                tuple(item.relative_path for item in reordered_manifest.image_files),
                ("images/shared-c2.svg", "images/shared-c1.svg"),
            )
            self.assertNotEqual(
                (original / "import_manifest.json").read_bytes(),
                (reordered / "import_manifest.json").read_bytes(),
            )
            original_result = preflight_v120_import(
                V120PreflightRequest(
                    original_manifest, original, _baseline_ref(), None, _contract(),
                ),
                PipelineConfig(ROOT),
            )
            reordered_result = preflight_v120_import(
                V120PreflightRequest(
                    reordered_manifest, reordered, _baseline_ref(), None, _contract(),
                ),
                PipelineConfig(ROOT),
            )
        self.assertNotEqual(
            original_result.report.manifest_sha256,
            reordered_result.report.manifest_sha256,
        )
        self.assertNotEqual(
            original_result.report.preflight_sha256,
            reordered_result.report.preflight_sha256,
        )

    def test_exact_v119_sha_size_release_digest_and_502_row_formal_view_are_required(self) -> None:
        with sqlite3.connect(BASELINE) as connection:
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM formal_complete_questions_v119").fetchone(),
                (502,),
            )
        with tempfile.TemporaryDirectory() as directory:
            altered = Path(directory) / "altered.sqlite3"
            data = BASELINE.read_bytes()
            altered.write_bytes(data[:-1] + bytes((data[-1] ^ 1,)))
            for locator in (V118, altered):
                with self.subTest(locator=locator.name):
                    request = _request("a")
                    forged = V120PreflightRequest(
                        request.manifest, request.package_root,
                        ArtifactRef(locator, BASELINE_SHA, BASELINE_SIZE, "sqlite"),
                        None, request.contract,
                    )
                    with self.assertRaises(PipelineError):
                        preflight_v120_import(forged, PipelineConfig(ROOT))

    def test_wrong_manifest_identity_and_release_digest_cannot_reach_ready(self) -> None:
        for target, value in (
            ("manifest", "task9-import-manifest-v1"),
            ("release_digest", "0" * 64),
            ("required_view", "complete_questions_v2"),
        ):
            request = _request("a")
            if target == "manifest":
                object.__setattr__(request.manifest, "schema_version", value)
            elif target == "release_digest":
                object.__setattr__(request.contract, "baseline_release_digest", value)
            else:
                object.__setattr__(request.contract, "required_baseline_view", value)
            with self.subTest(target=target):
                with self.assertRaises(PipelineError):
                    preflight_v120_import(request, PipelineConfig(ROOT))

    def test_disk_manifest_bool_cannot_equal_typed_integer_evidence(self) -> None:
        """Catches Python bool/int equality bypassing manifest authority binding."""
        with tempfile.TemporaryDirectory() as directory:
            package = Path(directory) / "package"
            shutil.copytree(FIXTURES / "v120-batch-a", package)
            answer_path = package / "answers/answer.txt"
            answer_path.write_bytes(b"x")
            manifest_path = package / "import_manifest.json"
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload["answer_files"][0]["sha256"] = _sha(b"x")
            payload["answer_files"][0]["size_bytes"] = 1
            manifest_path.write_bytes(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode("utf-8") + b"\n"
            )
            manifest = load_v120_import_manifest(manifest_path)
            payload["answer_files"][0]["size_bytes"] = True
            manifest_path.write_bytes(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode("utf-8") + b"\n"
            )

            with self.assertRaises(PipelineError):
                preflight_v120_import(
                    V120PreflightRequest(
                        manifest,
                        package,
                        _baseline_ref(),
                        None,
                        _contract(),
                    ),
                    PipelineConfig(ROOT),
                )


class V120FormalBaselineCollisionTests(unittest.TestCase):
    """Phase E/G REDs: all seven collision signals apply to formal V1.19."""

    _REFERENCE_TEXT = (
        "Consider the curve $C: y=26-\\frac{108}{x}$ ,where $0<x<20$ .\n"
        "(a) Find $\\frac{d y}{d x}$ .\n"
        "(b) If a tangent $L$ to $C$ passes through the point（ 10,20 ）,find the equation of $L$ ."
    )

    def _collision_result(self, updates: dict[str, object]):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "package"
        shutil.copytree(FIXTURES / "v120-batch-a", root)
        if "image_paths" in updates:
            if updates["image_paths"]:
                _rename_declared_image(root, updates["image_paths"][0])
            else:
                _remove_declared_images(root)
        _rewrite_record(root, updates)
        manifest = load_v120_import_manifest(root / "import_manifest.json")
        return preflight_v120_import(
            V120PreflightRequest(manifest, root, _baseline_ref(), None, _contract()),
            PipelineConfig(ROOT),
        )

    def test_formal_duplicate_and_scalar_collision_codes_remain_the_closed_task9_taxonomy(self) -> None:
        cases = {
            "duplicate_exact": {
                "source_id": REFERENCE_SOURCE_ID,
                "source_question_number": REFERENCE_NUMBER, "source_section": REFERENCE_SECTION,
                "source_fragment_hash": REFERENCE_FRAGMENT,
                "question_text_original": self._REFERENCE_TEXT,
                "image_paths": [], "image_roles": [],
            },
            "duplicate_ambiguous": {
                "source_id": IMAGE_SOURCE_ID, "source_question_number": IMAGE_NUMBER,
                "source_section": IMAGE_SECTION, "source_fragment_hash": REFERENCE_FRAGMENT,
                "question_text_original": self._REFERENCE_TEXT,
                "image_paths": [], "image_roles": [],
            },
            "collision_candidate_id": {"proposed_question_id": "M2QD-DA-EXAMPLE-Q1"},
            "collision_source_locator": {
                "source_id": "M2QD-DIFFERENTIATION-APPLICATIONS",
                "source_question_number": "EXAMPLE-Q1", "source_section": "教材例题",
            },
            "collision_fragment_sha256": {
                "source_fragment_hash": "7ca9b7902bf8efd929145e64c5d4a1aa11b2da06028e4e2123026a09da640e89",
            },
            "collision_normalized_text_sha256": {"question_text_original": self._REFERENCE_TEXT},
        }
        approved_codes = {
            "duplicate_exact", "duplicate_ambiguous", "collision_candidate_id",
            "collision_source_locator", "collision_fragment_sha256",
            "collision_normalized_text_sha256", "collision_image_sha256",
            "missing_image", "orphan_image", "unsupported_source_format",
            "unknown_primary_type", "unknown_tag", "malformed_candidate_json",
            "invalid_candidate_top_level", "invalid_candidate_record",
            "file_integrity_mismatch",
        }
        self.assertEqual(len(approved_codes), 16)
        with sqlite3.connect(BASELINE) as connection:
            exact = connection.execute(
                "SELECT source_id, source_question_number, source_section, source_fragment_hash, "
                "question_text_original, source_image_paths_json FROM formal_complete_questions_v119 "
                "WHERE question_id=?",
                (REFERENCE_ID,),
            ).fetchone()
            competing = connection.execute(
                "SELECT source_id, source_question_number, source_section FROM formal_complete_questions_v119 "
                "WHERE question_id=?",
                (IMAGE_REFERENCE_ID,),
            ).fetchone()
        self.assertEqual(exact[:4], (REFERENCE_SOURCE_ID, REFERENCE_NUMBER, REFERENCE_SECTION, REFERENCE_FRAGMENT))
        self.assertEqual(exact[4], self._REFERENCE_TEXT)
        self.assertEqual(json.loads(exact[5]), [])
        self.assertEqual(_sha(exact[4].encode("utf-8")), REFERENCE_NORMALIZED)
        self.assertEqual(competing, (IMAGE_SOURCE_ID, IMAGE_NUMBER, IMAGE_SECTION))
        for expected_code, updates in cases.items():
            with self.subTest(expected_code=expected_code):
                result = self._collision_result(updates)
                self.assertIn(expected_code, {issue.code for issue in result.issues})
                self.assertTrue({issue.code for issue in result.issues} <= approved_codes)
                self.assertEqual(result.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")

    def test_formal_image_identity_collision_is_blocking(self) -> None:
        with sqlite3.connect(BASELINE) as connection:
            formal_images = json.loads(connection.execute(
                "SELECT source_image_paths_json FROM formal_complete_questions_v119 "
                "WHERE question_id=?",
                (IMAGE_REFERENCE_ID,),
            ).fetchone()[0])
        self.assertEqual(formal_images, [{
            "path": FORMAL_IMAGE_PATH,
            "role": FORMAL_IMAGE_ROLE,
            "sha256": FORMAL_IMAGE_SHA,
        }])
        self.assertNotEqual(SHARED_IMAGE_SHA, FORMAL_IMAGE_SHA)
        result = self._collision_result({
            "image_paths": [FORMAL_IMAGE_PATH],
            "image_roles": [FORMAL_IMAGE_ROLE],
        })
        self.assertIn("collision_image_sha256", {issue.code for issue in result.issues})
        self.assertEqual(result.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")


class V120ReviewRemediationTests(unittest.TestCase):
    """Review-driven REDs for frozen Task 9A taxonomy and occurrence semantics."""

    _ISSUE_CODES = {
        "missing_image", "orphan_image", "unsupported_source_format",
        "unknown_primary_type", "unknown_tag", "malformed_candidate_json",
        "invalid_candidate_top_level", "invalid_candidate_record",
        "duplicate_exact", "duplicate_ambiguous", "collision_candidate_id",
        "collision_source_locator", "collision_fragment_sha256",
        "collision_normalized_text_sha256", "collision_image_sha256",
        "file_integrity_mismatch",
    }

    def _copy_a(self) -> Path:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name) / "package"
        shutil.copytree(FIXTURES / "v120-batch-a", root)
        return root

    def _result(
        self,
        root: Path,
        manifest=None,
    ) -> V120ImportPreflightResult:
        if manifest is None:
            manifest = load_v120_import_manifest(root / "import_manifest.json")
        try:
            return preflight_v120_import(
                V120PreflightRequest(
                    manifest, root, _baseline_ref(), None, _contract(),
                ),
                PipelineConfig(ROOT),
            )
        except PipelineError as exc:
            self.fail(f"preflight must classify this as a structured issue: {exc}")

    def test_issue_taxonomy_is_the_exact_frozen_task9a_sixteen_codes(self) -> None:
        module = importlib.import_module("joy_m2.ingest.v120_preflight")
        self.assertEqual(module._ISSUE_CODES, self._ISSUE_CODES)
        self.assertEqual(len(module._ISSUE_CODES), 16)

    def test_unknown_primary_type_and_tag_are_blocking_occurrence_issues(self) -> None:
        root = self._copy_a()
        _rewrite_record(root, {
            "primary_type": "NOT-A-CONTROLLED-PRIMARY-TYPE",
            "tags": ["NOT-A-CONTROLLED-TAG"],
        })
        result = self._result(root)
        self.assertEqual(
            {issue.code for issue in result.issues},
            {"unknown_primary_type", "unknown_tag"},
        )
        self.assertEqual(result.report.new_candidate_count, 0)
        self.assertEqual(result.report.rejected_count, 1)
        self.assertEqual(result.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")

    def test_only_frozen_task9a_taxonomy_compatibility_additions_are_accepted(self) -> None:
        compatible_root = self._copy_a()
        _rewrite_record(compatible_root, {
            "primary_type": "代数",
            "tags": ["一元一次方程"],
        })
        compatible = self._result(compatible_root)
        self.assertNotIn("unknown_primary_type", {
            issue.code for issue in compatible.issues
        })
        self.assertNotIn("unknown_tag", {issue.code for issue in compatible.issues})

        unapproved_root = self._copy_a()
        _rewrite_record(unapproved_root, {
            "primary_type": "函数",
            "tags": ["直线"],
        })
        unapproved = self._result(unapproved_root)
        self.assertEqual(
            {issue.code for issue in unapproved.issues},
            {"unknown_primary_type", "unknown_tag"},
        )

    def test_orphan_missing_and_unsupported_files_use_frozen_codes(self) -> None:
        orphan_root = self._copy_a()
        _add_declared_file(
            orphan_root, "image_files", "images/orphan.svg", "image", b"orphan\n",
        )
        orphan = self._result(orphan_root)
        self.assertIn("orphan_image", {issue.code for issue in orphan.issues})
        self.assertEqual(orphan.report.orphan_images, ("images/orphan.svg",))

        missing_root = self._copy_a()
        _rewrite_record(missing_root, {
            "image_paths": ["images/not-declared.svg"],
            "image_roles": ["question"],
        })
        missing = self._result(missing_root)
        self.assertIn("missing_image", {issue.code for issue in missing.issues})
        self.assertEqual(missing.report.missing_images, ("images/not-declared.svg",))

        unsupported_root = self._copy_a()
        _add_declared_file(
            unsupported_root, "source_files", "source/extra.mmd", "source", b"mmd\n",
        )
        unsupported = self._result(unsupported_root)
        self.assertIn("unsupported_source_format", {
            issue.code for issue in unsupported.issues
        })
        self.assertEqual(unsupported.report.unsupported_files, ("source/extra.mmd",))

    def test_safe_file_integrity_mismatch_is_structured_and_excluded(self) -> None:
        root = self._copy_a()
        manifest = load_v120_import_manifest(root / "import_manifest.json")
        changed = b"changed answer bytes\n"
        (root / "answers/answer.txt").write_bytes(changed)
        result = self._result(root, manifest)
        issues = [issue for issue in result.issues if issue.code == "file_integrity_mismatch"]
        self.assertEqual(len(issues), 1)
        self.assertIsNone(issues[0].proposed_question_id)
        self.assertEqual(issues[0].field, "file_integrity")
        evidence = json.loads(issues[0].evidence)
        self.assertEqual(evidence["relative_path"], "answers/answer.txt")
        self.assertEqual(evidence["actual_sha256"], _sha(changed))
        self.assertEqual(result.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")

    def test_malformed_top_level_and_record_failures_are_structured(self) -> None:
        cases = (
            (b"{not-json\n", "malformed_candidate_json"),
            ({"candidate": "not-an-array"}, "invalid_candidate_top_level"),
            ([{}], "invalid_candidate_record"),
        )
        for payload, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                root = self._copy_a()
                _rewrite_candidate_payload(root, payload)
                result = self._result(root)
                self.assertIn(expected_code, {issue.code for issue in result.issues})
                self.assertTrue({issue.code for issue in result.issues} <= self._ISSUE_CODES)
                self.assertEqual(result.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")

    def test_invalid_record_is_classified_before_its_missing_image(self) -> None:
        root = self._copy_a()
        _rewrite_record(root, {
            "difficulty_level": 0,
            "image_paths": ["images/not-declared.svg"],
            "image_roles": ["question"],
        })
        result = self._result(root)
        codes = {issue.code for issue in result.issues}
        self.assertIn("invalid_candidate_record", codes)
        self.assertNotIn("missing_image", codes)
        self.assertEqual(result.report.missing_images, ())

    def test_missing_image_report_preserves_candidate_occurrence_order(self) -> None:
        root = self._copy_a()
        original = json.loads((root / "records/candidates.json").read_text())[0]
        first = dict(original)
        first.update({
            "proposed_question_id": "TASK10-MISSING-Z",
            "image_paths": ["images/z-first.svg"],
            "image_roles": ["question"],
        })
        second = dict(original)
        second.update({
            "proposed_question_id": "TASK10-MISSING-A",
            "image_paths": ["images/a-second.svg"],
            "image_roles": ["question"],
        })
        _rewrite_candidate_payload(root, [first, second])
        result = self._result(root)
        missing_issues = [
            issue for issue in result.issues if issue.code == "missing_image"
        ]
        self.assertEqual(
            tuple(json.loads(issue.evidence)["candidate_id"] for issue in missing_issues),
            ("TASK10-MISSING-A", "TASK10-MISSING-Z"),
        )
        self.assertEqual(
            result.report.missing_images,
            ("images/z-first.svg", "images/a-second.svg"),
        )

    def test_same_batch_duplicate_id_is_occurrence_aware_and_rejected(self) -> None:
        root = self._copy_a()
        record = json.loads((root / "records/candidates.json").read_text())[0]
        _rewrite_candidate_payload(root, [record, dict(record)])
        result = self._result(root)
        self.assertIn("collision_candidate_id", {issue.code for issue in result.issues})
        self.assertEqual(result.report.detected_count, 2)
        self.assertEqual(result.report.new_candidate_count, 1)
        self.assertEqual(result.report.duplicate_count, 0)
        self.assertEqual(result.report.rejected_count, 1)

    def test_exact_duplicate_plus_other_reference_collision_is_rejected(self) -> None:
        root = self._copy_a()
        _remove_declared_images(root)
        _rewrite_record(root, {
            "proposed_question_id": IMAGE_REFERENCE_ID,
            "source_id": REFERENCE_SOURCE_ID,
            "source_question_number": REFERENCE_NUMBER,
            "source_section": REFERENCE_SECTION,
            "source_fragment_hash": REFERENCE_FRAGMENT,
            "question_text_original": V120FormalBaselineCollisionTests._REFERENCE_TEXT,
            "image_paths": [],
            "image_roles": [],
        })
        result = self._result(root)
        codes = {issue.code for issue in result.issues}
        self.assertIn("duplicate_exact", codes)
        self.assertIn("collision_candidate_id", codes)
        self.assertEqual(result.report.duplicate_count, 0)
        self.assertEqual(result.report.rejected_count, 1)

    def test_adaptation_and_image_collision_coexist_and_block(self) -> None:
        root = self._copy_a()
        with sqlite3.connect(BASELINE) as connection:
            fragment = connection.execute(
                "SELECT source_fragment_hash FROM formal_complete_questions_v119 "
                "WHERE question_id=?",
                (IMAGE_REFERENCE_ID,),
            ).fetchone()[0]
        _rename_declared_image(root, FORMAL_IMAGE_PATH)
        _rewrite_record(root, {
            "source_id": IMAGE_SOURCE_ID,
            "source_question_number": IMAGE_NUMBER,
            "source_section": IMAGE_SECTION,
            "source_fragment_hash": fragment,
            "image_paths": [FORMAL_IMAGE_PATH],
            "image_roles": [FORMAL_IMAGE_ROLE],
        })
        result = self._result(root)
        self.assertEqual(len(result.report.adaptations), 1)
        self.assertEqual(
            result.report.adaptations[0].reference_question_id,
            IMAGE_REFERENCE_ID,
        )
        self.assertIn("collision_image_sha256", {issue.code for issue in result.issues})
        self.assertEqual(result.report.new_candidate_count, 0)
        self.assertEqual(result.report.rejected_count, 1)

    def test_ambiguous_count_tracks_occurrences_not_duplicate_ids(self) -> None:
        root = self._copy_a()
        _remove_declared_images(root)
        original = json.loads((root / "records/candidates.json").read_text())[0]
        occurrence_id = "TASK10-OCCURRENCE-ID"
        first = dict(original)
        first.update({
            "proposed_question_id": occurrence_id,
            "image_paths": [],
            "image_roles": [],
        })
        second = dict(first)
        second.update({
            "source_id": IMAGE_SOURCE_ID,
            "source_question_number": IMAGE_NUMBER,
            "source_section": IMAGE_SECTION,
            "source_fragment_hash": REFERENCE_FRAGMENT,
            "question_text_original": V120FormalBaselineCollisionTests._REFERENCE_TEXT,
        })
        _rewrite_candidate_payload(root, [first, second])
        result = self._result(root)
        self.assertIn("duplicate_ambiguous", {issue.code for issue in result.issues})
        self.assertEqual(result.report.detected_count, 2)
        self.assertEqual(result.report.new_candidate_count, 1)
        self.assertEqual(result.report.rejected_count, 1)
        self.assertEqual(result.report.ambiguous_count, 1)
        self.assertEqual(result.report.ambiguous_splits, (occurrence_id,))


class V120SecondBatchTests(unittest.TestCase):
    """Phase F REDs: verified parent state, accumulation, and stale authority."""

    def _parent_request(self, root: Path, prefix_length: int = 1):
        from tests.integration.test_v120_candidate import _approved_prefix, _write_parent_oracle

        return _write_parent_oracle(
            root / f"independent-parent-{prefix_length}",
            _approved_prefix()[:prefix_length],
        )

    def test_second_batch_uses_verified_parent_digest_ledger_prefix_and_503_before_count(self) -> None:
        with _staging_temp() as directory:
            parent = self._parent_request(Path(directory))
            result = preflight_v120_import(_request("b", parent=parent), PipelineConfig(ROOT))
        self.assertEqual(result.report.parent_batch_count, 1)
        self.assertEqual(result.report.before_count, 503)
        self.assertEqual(result.report.new_candidate_count, 1)
        self.assertEqual(result.report.projected_after_count, 504)
        self.assertEqual(result.effective_state.candidate_count, 1)
        self.assertEqual(result.effective_state.projected_question_count, 503)
        self.assertEqual(len(result.effective_state.batch_ledger), 1)

    def test_reusing_an_accepted_batch_id_is_rejected_before_preflight(self) -> None:
        with _staging_temp() as directory:
            root = Path(directory)
            parent = self._parent_request(root)
            package = root / "reused-batch-id"
            shutil.copytree(FIXTURES / "v120-batch-b", package)
            manifest_path = package / "import_manifest.json"
            payload = json.loads(manifest_path.read_text(encoding="utf-8"))
            payload["batch_id"] = "TASK10-A"
            manifest_path.write_bytes(
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    allow_nan=False,
                ).encode("utf-8") + b"\n"
            )
            manifest = load_v120_import_manifest(manifest_path)

            with self.assertRaises(PipelineError):
                preflight_v120_import(
                    V120PreflightRequest(
                        manifest,
                        package,
                        _baseline_ref(),
                        parent,
                        _contract(),
                    ),
                    PipelineConfig(ROOT),
                )

    def test_second_batch_rejects_a_parent_that_fails_independent_verification(self) -> None:
        with _staging_temp() as directory:
            parent = self._parent_request(Path(directory))
            sums = parent.candidate_dir / "SHA256SUMS"
            sums.write_bytes(sums.read_bytes() + b"\n")
            before = _fingerprint(parent.candidate_dir)

            with self.assertRaises(PipelineError):
                preflight_v120_import(
                    _request("b", parent=parent),
                    PipelineConfig(ROOT),
                )

            self.assertEqual(_fingerprint(parent.candidate_dir), before)

    def test_equivalent_parent_generation_roots_do_not_change_preflight_authority(self) -> None:
        with _staging_temp() as directory:
            root = Path(directory)
            first_parent = self._parent_request(root / "one")
            second_parent = self._parent_request(root / "two")
            self.assertEqual(
                _fingerprint(first_parent.candidate_dir),
                _fingerprint(second_parent.candidate_dir),
            )
            first = preflight_v120_import(_request("b", parent=first_parent), PipelineConfig(ROOT))
            second = preflight_v120_import(_request("b", parent=second_parent), PipelineConfig(ROOT))
        self.assertEqual(first.effective_state.candidate_digest, second.effective_state.candidate_digest)
        self.assertEqual(first.report.preflight_sha256, second.report.preflight_sha256)

    def test_semantic_parent_state_change_invalidates_a_stale_preflight(self) -> None:
        with _staging_temp() as directory:
            root = Path(directory)
            parent_a = self._parent_request(root / "a", 1)
            parent_ab = self._parent_request(root / "ab", 2)
            digest_a = json.loads((parent_a.candidate_dir / "candidate_manifest.json").read_text())["candidate_digest"]
            digest_ab = json.loads((parent_ab.candidate_dir / "candidate_manifest.json").read_text())["candidate_digest"]
            self.assertNotEqual(digest_a, digest_ab)
            stale = preflight_v120_import(_request("c", parent=parent_a), PipelineConfig(ROOT))
            current = preflight_v120_import(_request("c", parent=parent_ab), PipelineConfig(ROOT))
        self.assertNotEqual(stale.effective_state.candidate_digest, current.effective_state.candidate_digest)
        self.assertNotEqual(stale.report.preflight_sha256, current.report.preflight_sha256)


class V120ThirdBatchPreflightTests(unittest.TestCase):
    """Phase G REDs: semantic A/B/C order and collisions with prior V1.20 rows."""

    def test_third_batch_uses_semantic_abc_parent_prefix_without_filesystem_sorting(self) -> None:
        with _staging_temp() as directory:
            root = Path(directory)
            from tests.integration.test_v120_candidate import _approved_prefix, _write_parent_oracle
            request = _write_parent_oracle(
                root / "independent-parent-ab", _approved_prefix()[:2],
            )
            self.assertEqual(
                tuple(item.approval.batch_id for item in request.approved_batches),
                ("TASK10-A", "TASK10-B"),
            )
            manifest = json.loads((request.candidate_dir / "candidate_manifest.json").read_text())
            self.assertEqual(tuple(item["ordinal"] for item in manifest["batch_ledger"]), (1, 2))
            self.assertEqual(
                manifest["batch_ledger"][1]["parent_candidate_digest"],
                "7e612d0a44f29ace7efb4fa2b2cb8bfe12b8f437132b5f8365d6c1561c95bd65",
            )
            result = preflight_v120_import(_request("c", parent=request), PipelineConfig(ROOT))
        self.assertEqual(result.report.parent_batch_count, 2)
        self.assertEqual(result.report.before_count, 504)
        self.assertEqual(result.report.projected_after_count, 505)
        self.assertEqual(tuple(entry.batch_id for entry in result.effective_state.batch_ledger), ("TASK10-A", "TASK10-B"))

    def test_cross_batch_id_source_fragment_text_and_image_collisions_are_blocking(self) -> None:
        from tests.integration.test_v120_candidate import _approved_prefix

        approved_a, approved_b, _ = _approved_prefix()
        candidate_a = approved_a.preflight_result.candidates[0]
        candidate_b = approved_b.preflight_result.candidates[0]
        self.assertNotEqual(candidate_a.proposed_question_id, candidate_b.proposed_question_id)
        self.assertNotEqual(candidate_a.source_fragment_hash, candidate_b.source_fragment_hash)
        self.assertNotEqual(candidate_a.normalized_text_sha256, candidate_b.normalized_text_sha256)
        self.assertEqual(candidate_a.image_sha256s, candidate_b.image_sha256s)
        cases = {
            "duplicate_exact": {
                "source_id": "TASK10-SOURCE-A", "source_question_number": "A1",
                "source_section": "Synthetic batch A", "source_fragment_hash": "a" * 64,
                "question_text_original": "Solve 2x + 3 = 11.",
                "image_paths": ["images/shared.svg"], "image_roles": ["question"],
            },
            "collision_candidate_id": {"proposed_question_id": "TASK10-A-001"},
            "collision_source_locator": {"source_id": "TASK10-SOURCE-A", "source_question_number": "A1", "source_section": "Synthetic batch A"},
            "collision_fragment_sha256": {"source_fragment_hash": "a" * 64},
            "collision_normalized_text_sha256": {"question_text_original": "Solve 2x + 3 = 11."},
            "collision_image_sha256": {"image_paths": ["images/shared.svg"], "image_roles": ["question"]},
            "duplicate_ambiguous": {
                "source_id": "TASK10-SOURCE-A", "source_question_number": "A1",
                "source_section": "Synthetic batch A", "source_fragment_hash": "b" * 64,
                "question_text_original": "Factor x squared minus 9.",
            },
        }
        expectations = {
            "duplicate_exact": (
                "TASK10-B-001", "candidate",
                {
                    "candidate_id": "TASK10-B-001",
                    "normalized_text_sha256": _sha(b"Solve 2x + 3 = 11."),
                    "reference_question_id": "TASK10-A-001",
                },
                (0, 1, 0, 0, 503, 503),
            ),
            "collision_candidate_id": (
                "TASK10-A-001", "proposed_question_id",
                {
                    "candidate_id": "TASK10-A-001",
                    "candidate_fragment_sha256": "b" * 64,
                    "reference_fragment_sha256": "a" * 64,
                    "reference_question_id": "TASK10-A-001",
                },
                (0, 0, 1, 0, 503, 503),
            ),
            "collision_source_locator": (
                "TASK10-B-001", "source_locator",
                {
                    "candidate_id": "TASK10-B-001",
                    "candidate_source_locator": [
                        "TASK10-SOURCE-A", "A1", "Synthetic batch A",
                    ],
                    "candidate_fragment_sha256": "b" * 64,
                    "reference_question_id": "TASK10-A-001",
                    "reference_source_locator": [
                        "TASK10-SOURCE-A", "A1", "Synthetic batch A",
                    ],
                    "reference_fragment_sha256": "a" * 64,
                },
                (0, 0, 1, 0, 503, 503),
            ),
            "collision_fragment_sha256": (
                "TASK10-B-001", "source_fragment_hash",
                {
                    "candidate_id": "TASK10-B-001",
                    "candidate_source_locator": [
                        "TASK10-SOURCE-B", "B1", "Synthetic batch B",
                    ],
                    "reference_question_id": "TASK10-A-001",
                    "reference_source_locator": [
                        "TASK10-SOURCE-A", "A1", "Synthetic batch A",
                    ],
                    "source_fragment_sha256": "a" * 64,
                },
                (0, 0, 1, 0, 503, 503),
            ),
            "collision_normalized_text_sha256": (
                "TASK10-B-001", "normalized_text_sha256",
                {
                    "candidate_id": "TASK10-B-001",
                    "normalized_text_sha256": _sha(b"Solve 2x + 3 = 11."),
                    "reference_question_id": "TASK10-A-001",
                },
                (0, 0, 1, 0, 503, 503),
            ),
            "collision_image_sha256": (
                "TASK10-B-001", "image_sha256s",
                {
                    "candidate_id": "TASK10-B-001",
                    "candidate_image_path": "images/shared.svg",
                    "candidate_image_role": "question",
                    "candidate_image_sha256": _sha(
                        b"different cross-batch image bytes\n"
                    ),
                    "reference_question_id": "TASK10-A-001",
                    "reference_image_path": "images/shared.svg",
                    "reference_image_role": "question",
                    "reference_image_sha256": SHARED_IMAGE_SHA,
                },
                (0, 0, 1, 0, 503, 503),
            ),
            "duplicate_ambiguous": (
                "TASK10-C-001", "duplicate",
                {
                    "candidate_id": "TASK10-C-001",
                    "matches": [
                        {
                            "reference_question_id": "TASK10-A-001",
                            "signals": ["source_locator"],
                        },
                        {
                            "reference_question_id": "TASK10-B-001",
                            "signals": [
                                "normalized_text_sha256",
                                "source_fragment_sha256",
                            ],
                        },
                    ],
                },
                (0, 0, 1, 1, 504, 504),
            ),
        }
        ambiguous = cases["duplicate_ambiguous"]
        self.assertEqual(
            (ambiguous["source_id"], ambiguous["source_question_number"], ambiguous["source_section"]),
            (candidate_a.source_id, candidate_a.source_question_number, candidate_a.source_section),
        )
        self.assertEqual(ambiguous["source_fragment_hash"], candidate_b.source_fragment_hash)
        self.assertEqual(ambiguous["question_text_original"], candidate_b.question_text_original)
        for expected_code, updates in cases.items():
            with self.subTest(expected_code=expected_code), _staging_temp() as directory:
                root = Path(directory)
                package = root / "package"
                fixture_letter = "c" if expected_code == "duplicate_ambiguous" else "b"
                parent_length = 2 if expected_code == "duplicate_ambiguous" else 1
                shutil.copytree(FIXTURES / f"v120-batch-{fixture_letter}", package)
                if "image_paths" in updates and updates["image_paths"]:
                    _rename_declared_image(package, updates["image_paths"][0])
                if expected_code == "collision_image_sha256":
                    _replace_declared_image_bytes(package, b"different cross-batch image bytes\n")
                _rewrite_record(package, updates)
                from tests.integration.test_v120_candidate import _approved_prefix, _write_parent_oracle
                parent = _write_parent_oracle(
                    root / "independent-parent", _approved_prefix()[:parent_length],
                )
                manifest = load_v120_import_manifest(package / "import_manifest.json")
                if expected_code == "collision_image_sha256":
                    record = json.loads((package / "records/candidates.json").read_text())[0]
                    self.assertEqual((record["image_paths"][0], record["image_roles"][0]), ("images/shared.svg", "question"))
                    self.assertNotEqual(manifest.image_files[0].sha256, candidate_a.image_sha256s[0])
                request = V120PreflightRequest(
                    manifest, package, _baseline_ref(),
                    parent, _contract(),
                )
                result = preflight_v120_import(request, PipelineConfig(ROOT))
                candidate_id, field, evidence, counts = expectations[expected_code]
                self.assertEqual(
                    tuple(
                        (issue.proposed_question_id, issue.code, issue.field, issue.evidence)
                        for issue in result.issues
                    ),
                    ((candidate_id, expected_code, field, _canonical(evidence).decode("utf-8")),),
                )
                self.assertEqual(result.report.blocking_errors, (expected_code,))
                self.assertEqual(
                    (
                        result.report.new_candidate_count,
                        result.report.duplicate_count,
                        result.report.rejected_count,
                        result.report.ambiguous_count,
                        result.report.before_count,
                        result.report.projected_after_count,
                    ),
                    counts,
                )
                self.assertEqual(result.report.detected_count, 1)
                self.assertEqual(result.report.status, "BLOCKED — IMPORT PREFLIGHT FAILED")

    def test_cross_batch_multi_issue_order_and_evidence_are_exact(self) -> None:
        from tests.integration.test_v120_candidate import _approved_prefix, _write_parent_oracle

        with _staging_temp() as directory:
            root = Path(directory)
            package = root / "package"
            shutil.copytree(FIXTURES / "v120-batch-b", package)
            _rewrite_record(package, {
                "source_id": "TASK10-SOURCE-A",
                "source_question_number": "A1",
                "source_section": "Synthetic batch A",
                "source_fragment_hash": "a" * 64,
            })
            parent = _write_parent_oracle(
                root / "independent-parent", _approved_prefix()[:1],
            )
            manifest = load_v120_import_manifest(package / "import_manifest.json")
            result = preflight_v120_import(
                V120PreflightRequest(
                    manifest, package, _baseline_ref(), parent, _contract(),
                ),
                PipelineConfig(ROOT),
            )

        locator = ["TASK10-SOURCE-A", "A1", "Synthetic batch A"]
        self.assertEqual(
            tuple(
                (issue.code, issue.field, issue.evidence)
                for issue in result.issues
            ),
            (
                (
                    "collision_fragment_sha256",
                    "source_fragment_hash",
                    _canonical({
                        "candidate_id": "TASK10-B-001",
                        "candidate_source_locator": locator,
                        "reference_question_id": "TASK10-A-001",
                        "reference_source_locator": locator,
                        "source_fragment_sha256": "a" * 64,
                    }).decode("utf-8"),
                ),
                (
                    "collision_source_locator",
                    "source_locator",
                    _canonical({
                        "candidate_id": "TASK10-B-001",
                        "candidate_source_locator": locator,
                        "candidate_fragment_sha256": "a" * 64,
                        "reference_question_id": "TASK10-A-001",
                        "reference_source_locator": locator,
                        "reference_fragment_sha256": "a" * 64,
                    }).decode("utf-8"),
                ),
            ),
        )
        self.assertEqual(
            (
                result.report.detected_count,
                result.report.new_candidate_count,
                result.report.duplicate_count,
                result.report.rejected_count,
                result.report.ambiguous_count,
                result.report.before_count,
                result.report.projected_after_count,
            ),
            (1, 0, 0, 1, 0, 503, 503),
        )
        self.assertEqual(
            result.report.blocking_errors,
            ("collision_fragment_sha256", "collision_source_locator"),
        )


if __name__ == "__main__":
    unittest.main()
