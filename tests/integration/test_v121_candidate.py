from __future__ import annotations

import inspect
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.errors import (
    ImportApprovalError,
    InputFormatError,
    InputMissingError,
    OutputConflictError,
)
from joy_m2.ingest.v121_manifest import load_v121_import_manifest
from joy_m2.ingest.v121_models import (
    V121ApprovedBatch,
    V121CandidateBuildRequest,
    V121CandidateVerificationRequest,
    V121ImportApproval,
    V121PreflightRequest,
)
from joy_m2.ingest.v121_preflight import preflight_v121_import
from joy_m2.models import ArtifactRef
from joy_m2.ingest.v121_writer_profiles import CHECK_NAMES
from tests.integration.test_v121_preflight import (
    BASELINE,
    BASELINE_SHA,
    BASELINE_SIZE,
    FIXTURE,
    _contract,
    _make_package,
    _request,
)


GENESIS = "331192032f184a44ed383e6dacc2f06fbacb60ad94414298fcb935ff56cb5906"


def _make_named_package(parent: Path, name: str) -> Path:
    source = FIXTURE.parent / f"v120-batch-{name.lower()}"
    root = parent / f"package-{name.lower()}"
    shutil.copytree(source, root)
    manifest_path = root / "import_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["schema_version"] = "task11-v121-import-manifest-v1"
    payload["target_release_version"] = "V1.21"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return root


def _approved(package: Path, config: PipelineConfig, parent=None) -> V121ApprovedBatch:
    if parent is None:
        request = _request(package)
    else:
        request = V121PreflightRequest(
            load_v121_import_manifest(package / "import_manifest.json"),
            package,
            ArtifactRef(BASELINE, BASELINE_SHA, BASELINE_SIZE, "sqlite"),
            parent,
            _contract(),
        )
    result = preflight_v121_import(request, config)
    report = result.report
    approval = V121ImportApproval(
        report.batch_id,
        report.preflight_sha256,
        "V1.21",
        report.parent_candidate_digest,
        f"USER APPROVED IMPORT BATCH {report.batch_id} {report.preflight_sha256} "
        f"V1.21 PARENT {report.parent_candidate_digest}",
    )
    return V121ApprovedBatch(result, package, approval)


def _tree(root: Path) -> tuple[tuple[str, str, int], ...]:
    return tuple(
        (
            path.relative_to(root).as_posix(),
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_size,
        )
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )


class V121CandidateApiTests(unittest.TestCase):
    def test_v121_writer_and_verifier_are_public(self):
        import joy_m2.ingest as ingest

        for name in ("build_v121_candidate", "verify_v121_candidate"):
            value = getattr(ingest, name, None)
            self.assertTrue(callable(value), name)
            self.assertEqual(tuple(inspect.signature(value).parameters), ("request", "config"))


class V121CandidateBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(
            prefix="task11-v121-red-", dir=ROOT / "data/staging"
        )
        self.root = Path(self.temporary.name)
        self.package = _make_package(self.root)
        self.config = PipelineConfig(ROOT)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def build(self, output: Path | None = None):
        from joy_m2.ingest import build_v121_candidate

        approved = _approved(self.package, self.config)
        target = output or (self.root / "candidate")
        return approved, build_v121_candidate(
            V121CandidateBuildRequest((approved,), target, _contract()),
            self.config,
        )

    def test_first_batch_builds_verified_append_only_candidate(self):
        baseline_before = hashlib.sha256(BASELINE.read_bytes()).hexdigest()
        approved, artifacts = self.build()
        self.assertEqual(artifacts.verification_report.status, "PASS")
        self.assertEqual(artifacts.state.candidate_count, 1)
        self.assertEqual(artifacts.state.projected_question_count, 544)
        self.assertEqual(artifacts.state.batch_ledger[0].parent_candidate_digest, GENESIS)
        self.assertTrue(artifacts.database.path.is_file())
        with sqlite3.connect(artifacts.database.path) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM task11_candidate_questions_v121"
                ).fetchone()[0],
                544,
            )
        self.assertEqual(hashlib.sha256(BASELINE.read_bytes()).hexdigest(), baseline_before)
        self.assertEqual(approved.approval.parent_candidate_digest, GENESIS)

    def test_independent_verifier_passes_and_does_not_mutate(self):
        from joy_m2.ingest import verify_v121_candidate

        approved, artifacts = self.build()
        root = artifacts.database.path.parent
        before = _tree(root)
        report = verify_v121_candidate(
            V121CandidateVerificationRequest(root, (approved,), _contract()),
            self.config,
        )
        self.assertEqual(report.status, "PASS")
        self.assertEqual(tuple(check.name for check in report.checks), CHECK_NAMES)
        self.assertTrue(all(check.passed for check in report.checks))
        self.assertEqual(_tree(root), before)

    def test_manifest_tamper_returns_structured_fail_without_repair(self):
        from joy_m2.ingest import verify_v121_candidate

        approved, artifacts = self.build()
        root = artifacts.database.path.parent
        manifest = root / "candidate_manifest.json"
        manifest.write_bytes(manifest.read_bytes().replace(b'"candidate"', b'"tampered"', 1))
        before = _tree(root)
        report = verify_v121_candidate(
            V121CandidateVerificationRequest(root, (approved,), _contract()),
            self.config,
        )
        self.assertEqual(report.status, "FAIL")
        self.assertEqual(_tree(root), before)

    def test_missing_root_and_malformed_json_keep_exact_error_boundary(self):
        from joy_m2.ingest import verify_v121_candidate

        approved = _approved(self.package, self.config)
        missing = self.root / "missing"
        with self.assertRaises(InputMissingError):
            verify_v121_candidate(
                V121CandidateVerificationRequest(missing, (approved,), _contract()),
                self.config,
            )

        _, artifacts = self.build()
        root = artifacts.database.path.parent
        (root / "candidate_manifest.json").write_bytes(b"{")
        with self.assertRaises(InputFormatError):
            verify_v121_candidate(
                V121CandidateVerificationRequest(root, (approved,), _contract()),
                self.config,
            )

    def test_missing_extra_and_tampered_artifacts_are_structured_failures(self):
        from joy_m2.ingest import verify_v121_candidate

        for case in ("missing", "extra", "tampered-db"):
            with self.subTest(case=case):
                case_package = _make_package(self.root / f"source-{case}")
                approved = _approved(case_package, self.config)
                candidate_root = self.root / f"candidate-{case}"
                from joy_m2.ingest import build_v121_candidate

                artifacts = build_v121_candidate(
                    V121CandidateBuildRequest(
                        (approved,), candidate_root, _contract()
                    ),
                    self.config,
                )
                if case == "missing":
                    (candidate_root / "rollback.json").unlink()
                elif case == "extra":
                    (candidate_root / "rogue.txt").write_text("rogue", encoding="utf-8")
                else:
                    with artifacts.database.path.open("ab") as handle:
                        handle.write(b"tamper")
                before = _tree(candidate_root)
                report = verify_v121_candidate(
                    V121CandidateVerificationRequest(
                        candidate_root, (approved,), _contract()
                    ),
                    self.config,
                )
                self.assertEqual(report.status, "FAIL")
                self.assertEqual(_tree(candidate_root), before)

    def test_existing_output_is_not_replaced(self):
        approved, artifacts = self.build()
        before = _tree(artifacts.database.path.parent)
        from joy_m2.ingest import build_v121_candidate

        with self.assertRaises(OutputConflictError):
            build_v121_candidate(
                V121CandidateBuildRequest(
                    (approved,), artifacts.database.path.parent, _contract()
                ),
                self.config,
            )
        self.assertEqual(_tree(artifacts.database.path.parent), before)

    def test_wrong_parent_approval_is_rejected(self):
        approved = _approved(self.package, self.config)
        forged = object.__new__(V121ImportApproval)
        for name, value in approved.approval.__dict__.items():
            object.__setattr__(forged, name, value)
        object.__setattr__(forged, "parent_candidate_digest", "f" * 64)
        bad = object.__new__(V121ApprovedBatch)
        object.__setattr__(bad, "preflight_result", approved.preflight_result)
        object.__setattr__(bad, "package_root", approved.package_root)
        object.__setattr__(bad, "approval", forged)
        from joy_m2.ingest import build_v121_candidate

        output = self.root / "bad-candidate"
        with self.assertRaises(ImportApprovalError):
            build_v121_candidate(
                V121CandidateBuildRequest((bad,), output, _contract()), self.config
            )
        self.assertFalse(output.exists())

    def test_equivalent_roots_build_byte_identical_candidates(self):
        first_package = self.package
        second_package = _make_package(self.root / "second-source")
        from joy_m2.ingest import build_v121_candidate

        first = _approved(first_package, self.config)
        second = _approved(second_package, self.config)
        first_root = self.root / "candidate-one"
        second_root = self.root / "candidate-two"
        build_v121_candidate(
            V121CandidateBuildRequest((first,), first_root, _contract()), self.config
        )
        build_v121_candidate(
            V121CandidateBuildRequest((second,), second_root, _contract()), self.config
        )
        self.assertEqual(_tree(first_root), _tree(second_root))

    def test_second_batch_requires_verified_parent_and_appends_atomically(self):
        from joy_m2.ingest import build_v121_candidate

        approved_a = _approved(self.package, self.config)
        parent_root = self.root / "parent"
        parent = build_v121_candidate(
            V121CandidateBuildRequest((approved_a,), parent_root, _contract()),
            self.config,
        )
        package_b = _make_named_package(self.root, "b")
        parent_request = V121CandidateVerificationRequest(
            parent_root, (approved_a,), _contract()
        )
        approved_b = _approved(package_b, self.config, parent_request)
        child = build_v121_candidate(
            V121CandidateBuildRequest(
                (approved_a, approved_b), self.root / "child", _contract()
            ),
            self.config,
        )
        self.assertEqual(parent.state.projected_question_count, 544)
        self.assertEqual(child.state.projected_question_count, 545)
        self.assertEqual(len(child.state.batch_ledger), 2)
        self.assertEqual(
            child.state.batch_ledger[1].parent_candidate_digest,
            parent.state.candidate_digest,
        )


if __name__ == "__main__":
    unittest.main()
