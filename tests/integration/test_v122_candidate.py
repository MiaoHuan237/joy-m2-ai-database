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
    PipelineError,
    InputFormatError,
    InputMissingError,
    OutputConflictError,
)
from joy_m2.ingest.v122_manifest import load_v122_import_manifest
from joy_m2.ingest.v122_models import (
    V122ApprovedBatch,
    V122CandidateBuildRequest,
    V122CandidateVerificationRequest,
    V122ImportApproval,
    V122PreflightRequest,
)
from joy_m2.ingest.v122_preflight import preflight_v122_import
from joy_m2.models import ArtifactRef
from joy_m2.ingest.v121_writer_profiles import CHECK_NAMES as OLD_CHECK_NAMES
CHECK_NAMES = tuple("v121_preservation" if x == "v120_preservation" else x for x in OLD_CHECK_NAMES)
from tests.integration.test_v122_preflight import (
    BASELINE,
    BASELINE_SHA,
    BASELINE_SIZE,
    FIXTURE,
    _contract,
    _make_package,
    _request,
)
from tests.integration.test_v120_preflight import _rename_declared_image, _rewrite_record


GENESIS = "7f449c4428900537f99a7118ed702da462afa0f00ae1aa38e5296dacf6099dd7"


def _make_named_package(parent: Path, name: str) -> Path:
    source = FIXTURE.parent / f"v120-batch-{name.lower()}"
    root = parent / f"package-{name.lower()}"
    shutil.copytree(source, root)
    manifest_path = root / "import_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["schema_version"] = "task12-v122-import-manifest-v1"
    payload["target_release_version"] = "V1.22"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return root


def _approved(package: Path, config: PipelineConfig, parent=None) -> V122ApprovedBatch:
    if parent is None:
        request = _request(package)
    else:
        request = V122PreflightRequest(
            load_v122_import_manifest(package / "import_manifest.json"),
            package,
            ArtifactRef(BASELINE, BASELINE_SHA, BASELINE_SIZE, "sqlite"),
            parent,
            _contract(),
        )
    result = preflight_v122_import(request, config)
    report = result.report
    approval = V122ImportApproval(
        report.batch_id,
        report.preflight_sha256,
        "V1.22",
        report.parent_candidate_digest,
        f"USER APPROVED IMPORT BATCH {report.batch_id} {report.preflight_sha256} "
        f"V1.22 PARENT {report.parent_candidate_digest}",
    )
    return V122ApprovedBatch(result, package, approval)


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


class V122CandidateApiTests(unittest.TestCase):
    def test_v122_writer_and_verifier_are_public(self):
        import joy_m2.ingest as ingest

        for name in ("build_v122_candidate", "verify_v122_candidate"):
            value = getattr(ingest, name, None)
            self.assertTrue(callable(value), name)
            self.assertEqual(tuple(inspect.signature(value).parameters), ("request", "config"))


class V122CandidateBehaviorTests(unittest.TestCase):
    def setUp(self) -> None:
        sandbox = ROOT / "data/staging/task12-v122-hkdse-2019"
        sandbox.mkdir(parents=True, exist_ok=True)
        self.temporary = tempfile.TemporaryDirectory(prefix="synthetic-", dir=sandbox)
        self.root = Path(self.temporary.name)
        self.package = _make_package(self.root)
        for folder in ("data/staging", "data/baselines", "releases"):
            (self.root / folder).mkdir(parents=True)
        self.config = PipelineConfig(ROOT)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def _invoke(self, fn, *args):
        try:
            return fn(*args)
        except NotImplementedError:
            self.fail("V1.22 writer/verifier behavior missing")

    def build(self, output: Path | None = None):
        from joy_m2.ingest import build_v122_candidate as _build
        build_v122_candidate = lambda *args: self._invoke(_build, *args)

        approved = _approved(self.package, self.config)
        target = output or (self.root / "data/staging/candidate")
        return approved, build_v122_candidate(
            V122CandidateBuildRequest((approved,), target, _contract()),
            self.config,
        )

    def test_first_batch_builds_verified_append_only_candidate(self):
        baseline_before = hashlib.sha256(BASELINE.read_bytes()).hexdigest()
        approved, artifacts = self.build()
        self.assertEqual(artifacts.verification_report.status, "PASS")
        self.assertEqual(artifacts.state.candidate_count, 1)
        self.assertEqual(artifacts.state.projected_question_count, 592)
        self.assertEqual(artifacts.state.batch_ledger[0].parent_candidate_digest, GENESIS)
        self.assertTrue(artifacts.database.path.is_file())
        with sqlite3.connect(artifacts.database.path) as connection:
            self.assertEqual(
                connection.execute(
                    "SELECT COUNT(*) FROM task12_candidate_questions_v122"
                ).fetchone()[0],
                592,
            )
        self.assertEqual(hashlib.sha256(BASELINE.read_bytes()).hexdigest(), baseline_before)
        self.assertEqual(approved.approval.parent_candidate_digest, GENESIS)

    def test_independent_verifier_passes_and_does_not_mutate(self):
        from joy_m2.ingest import verify_v122_candidate as _verify
        verify_v122_candidate = lambda *args: self._invoke(_verify, *args)

        approved, artifacts = self.build()
        root = artifacts.database.path.parent
        before = _tree(root)
        report = verify_v122_candidate(
            V122CandidateVerificationRequest(root, (approved,), _contract()),
            self.config,
        )
        self.assertEqual(report.status, "PASS")
        self.assertEqual(tuple(check.name for check in report.checks), CHECK_NAMES)
        self.assertTrue(all(check.passed for check in report.checks))
        self.assertEqual(_tree(root), before)

    def test_manifest_tamper_returns_structured_fail_without_repair(self):
        from joy_m2.ingest import verify_v122_candidate as _verify
        verify_v122_candidate = lambda *args: self._invoke(_verify, *args)

        approved, artifacts = self.build()
        root = artifacts.database.path.parent
        manifest = root / "candidate_manifest.json"
        manifest.write_bytes(manifest.read_bytes().replace(b'"candidate"', b'"tampered"', 1))
        before = _tree(root)
        report = verify_v122_candidate(
            V122CandidateVerificationRequest(root, (approved,), _contract()),
            self.config,
        )
        self.assertEqual(report.status, "FAIL")
        self.assertEqual(_tree(root), before)

    def test_missing_root_and_malformed_json_keep_exact_error_boundary(self):
        from joy_m2.ingest import verify_v122_candidate as _verify
        verify_v122_candidate = lambda *args: self._invoke(_verify, *args)

        approved = _approved(self.package, self.config)
        missing = self.root / "missing"
        with self.assertRaises(InputMissingError):
            verify_v122_candidate(
                V122CandidateVerificationRequest(missing, (approved,), _contract()),
                self.config,
            )

        _, artifacts = self.build()
        root = artifacts.database.path.parent
        (root / "candidate_manifest.json").write_bytes(b"{")
        with self.assertRaises(InputFormatError):
            verify_v122_candidate(
                V122CandidateVerificationRequest(root, (approved,), _contract()),
                self.config,
            )

    def test_missing_extra_and_tampered_artifacts_are_structured_failures(self):
        from joy_m2.ingest import verify_v122_candidate as _verify
        verify_v122_candidate = lambda *args: self._invoke(_verify, *args)

        for case in ("missing", "extra", "tampered-db"):
            with self.subTest(case=case):
                case_package = _make_package(self.root / f"source-{case}")
                approved = _approved(case_package, self.config)
                candidate_root = self.root / f"candidate-{case}"
                from joy_m2.ingest import build_v122_candidate as _build
                build_v122_candidate = lambda *args: self._invoke(_build, *args)

                artifacts = build_v122_candidate(
                    V122CandidateBuildRequest(
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
                report = verify_v122_candidate(
                    V122CandidateVerificationRequest(
                        candidate_root, (approved,), _contract()
                    ),
                    self.config,
                )
                self.assertEqual(report.status, "FAIL")
                self.assertEqual(_tree(candidate_root), before)

    def test_existing_output_is_not_replaced(self):
        approved, artifacts = self.build()
        before = _tree(artifacts.database.path.parent)
        from joy_m2.ingest import build_v122_candidate as _build
        build_v122_candidate = lambda *args: self._invoke(_build, *args)

        with self.assertRaises(OutputConflictError):
            build_v122_candidate(
                V122CandidateBuildRequest(
                    (approved,), artifacts.database.path.parent, _contract()
                ),
                self.config,
            )
        self.assertEqual(_tree(artifacts.database.path.parent), before)

    def test_wrong_parent_approval_is_rejected(self):
        approved = _approved(self.package, self.config)
        forged = object.__new__(V122ImportApproval)
        for name, value in approved.approval.__dict__.items():
            object.__setattr__(forged, name, value)
        object.__setattr__(forged, "parent_candidate_digest", "f" * 64)
        bad = object.__new__(V122ApprovedBatch)
        object.__setattr__(bad, "preflight_result", approved.preflight_result)
        object.__setattr__(bad, "package_root", approved.package_root)
        object.__setattr__(bad, "approval", forged)
        from joy_m2.ingest import build_v122_candidate as _build
        build_v122_candidate = lambda *args: self._invoke(_build, *args)

        output = self.root / "data/staging/bad-candidate"
        with self.assertRaises(ImportApprovalError):
            build_v122_candidate(
                V122CandidateBuildRequest((bad,), output, _contract()), self.config
            )
        self.assertFalse(output.exists())

    def test_equivalent_roots_build_byte_identical_candidates(self):
        first_package = self.package
        second_package = _make_package(self.root / "second-source")
        from joy_m2.ingest import build_v122_candidate as _build
        build_v122_candidate = lambda *args: self._invoke(_build, *args)

        first = _approved(first_package, self.config)
        second = _approved(second_package, self.config)
        first_root = self.root / "candidate-one"
        second_root = self.root / "candidate-two"
        build_v122_candidate(
            V122CandidateBuildRequest((first,), first_root, _contract()), self.config
        )
        build_v122_candidate(
            V122CandidateBuildRequest((second,), second_root, _contract()), self.config
        )
        self.assertEqual(_tree(first_root), _tree(second_root))


    def test_private_genesis_oracle_reconstructs_fixed_projection(self):
        import importlib
        self.assertIsNotNone(importlib.util.find_spec("joy_m2.ingest.v122_writer_profiles"))
        p = importlib.import_module("joy_m2.ingest.v122_writer_profiles")
        self.assertTrue(callable(getattr(p, "_genesis_digest", None)))
        self.assertEqual(p._genesis_digest(), GENESIS)
        from unittest import mock
        with mock.patch.object(p, "BASELINE_RELEASE_DIGEST", "0" * 64):
            with self.assertRaises(InputFormatError):
                p._genesis_digest()

    def test_writer_independently_calls_genesis_boundary(self):
        import joy_m2.ingest.v122_writer as writer
        self.assertTrue(callable(getattr(writer, "_genesis_digest", None)))
        from unittest import mock
        approved = _approved(self.package, self.config)
        with mock.patch.object(writer, "_genesis_digest", return_value="0" * 64) as call:
            with self.assertRaises(ImportApprovalError):
                writer.build_v122_candidate(V122CandidateBuildRequest((approved,),
                    self.root / "data/staging/wrong-genesis", _contract()), self.config)
            self.assertGreaterEqual(call.call_count, 1)

    def test_verifier_independently_calls_genesis_boundary(self):
        approved, artifacts = self.build()
        import joy_m2.ingest.v122_verification as verifier
        self.assertTrue(callable(getattr(verifier, "_genesis_digest", None)))
        from unittest import mock
        with mock.patch.object(verifier, "_genesis_digest", side_effect=[GENESIS, "0" * 64]) as call:
            result = verifier.verify_v122_candidate(V122CandidateVerificationRequest(
                artifacts.database.path.parent, (approved,), _contract()), self.config)
            self.assertEqual(result.status, "FAIL")
            self.assertFalse(next(x.passed for x in result.checks if x.name == "parent_chain"))
            self.assertEqual(call.call_count, 2)

    def test_baseline_schema_rows_metadata_remain_exactly_preserved(self):
        approved, artifacts = self.build()
        with sqlite3.connect(f"{BASELINE.as_uri()}?mode=ro", uri=True) as baseline, sqlite3.connect(artifacts.database.path) as candidate:
            rows = baseline.execute("SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY name").fetchall()
            for row in rows:
                self.assertEqual(candidate.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name=?", (row[1],)).fetchone(), row)
                if row[0] == "table":
                    quoted = '"' + row[1].replace('"','""') + '"'
                    self.assertEqual(candidate.execute("SELECT * FROM " + quoted).fetchall(),
                                     baseline.execute("SELECT * FROM " + quoted).fetchall())
            self.assertEqual(candidate.execute("PRAGMA user_version").fetchone(), (122,))
            self.assertEqual(candidate.execute("SELECT aggregate_order,record_status,selectable FROM task12_v122_candidates_v1").fetchall(), [(592,"candidate",0)])

    def test_publication_fault_cleans_only_owned_temporary_output(self):
        import joy_m2.ingest.v122_writer as writer
        self.assertTrue(hasattr(writer, "atomic_rename_no_replace"))
        from unittest import mock
        approved = _approved(self.package, self.config)
        output = self.root / "data/staging/fault"
        source = _tree(self.package)
        with mock.patch.object(writer, "atomic_rename_no_replace", side_effect=OSError("injected")):
            with self.assertRaises(PipelineError):
                writer.build_v122_candidate(V122CandidateBuildRequest((approved,), output, _contract()), self.config)
        self.assertFalse(output.exists())
        self.assertEqual(tuple(output.parent.iterdir()), ())
        self.assertEqual(_tree(self.package), source)


    def test_forged_matching_first_parent_values_rejected_by_both_boundaries(self):
        from joy_m2.ingest import build_v122_candidate, verify_v122_candidate
        approved, artifacts = self.build()
        root = artifacts.database.path.parent
        before = _tree(root)
        def clone(value, **changes):
            result = object.__new__(type(value))
            for k, v in vars(value).items():
                object.__setattr__(result, k, changes.get(k, v))
            return result
        projection = {"baseline_database_sha256":BASELINE_SHA,"baseline_question_count":592,
            "baseline_release_digest":_contract().baseline_release_digest,
            "baseline_release_version":"V1.21","candidate_count":0,
            "schema":"task12-v122-genesis-v1","target_release_version":"V1.22"}
        changed = hashlib.sha256((json.dumps(projection,sort_keys=True,separators=(",",":"))+"\n").encode()).hexdigest()
        for wrong in (None,"","331192032f184a44ed383e6dacc2f06fbacb60ad94414298fcb935ff56cb5906",
            "4ff624aca875b0191fe8a617516d2919c6d700ce69c5a3b5d236adcf7ecc59f1","a"*64,changed):
            with self.subTest(parent=wrong):
                report = clone(approved.preflight_result.report,parent_candidate_digest=wrong)
                state = clone(approved.preflight_result.effective_state,candidate_digest=wrong)
                result = clone(approved.preflight_result,report=report,effective_state=state)
                approval = clone(approved.approval,parent_candidate_digest=wrong,
                    statement=f"USER APPROVED IMPORT BATCH {report.batch_id} {report.preflight_sha256} V1.22 PARENT {wrong}")
                bad = clone(approved,preflight_result=result,approval=approval)
                output = self.root / "data/staging/forged"
                with self.assertRaises(ImportApprovalError):
                    build_v122_candidate(V122CandidateBuildRequest((bad,),output,_contract()), self.config)
                verification = verify_v122_candidate(V122CandidateVerificationRequest(root,(bad,),_contract()),self.config)
                self.assertEqual(verification.status,"FAIL")
                self.assertFalse(output.exists())
                self.assertEqual(_tree(root),before)

    def test_independent_corruption_controls_are_structured_and_read_only(self):
        from joy_m2.ingest import verify_v122_candidate
        approved, artifacts = self.build()
        original = artifacts.database.path.parent
        cases = {
            "manifest": "deterministic_identity", "sums": "sha256sums_closure",
            "rollback": "rollback_contract", "image": "image_projection",
            "unreadable": "sqlite_readability", "schema": "sqlite_schema",
            "integrity": "sqlite_integrity",
            "foreign_key": "sqlite_foreign_keys", "ledger": "batch_ledger",
            "count": "count_closure", "digest": "candidate_digest",
            "artifact_ref": "artifact_references",
        }
        for case, expected in cases.items():
            with self.subTest(case=case):
                target = self.root / "data/staging" / case
                shutil.copytree(original,target)
                db = target / _contract().database_filename
                manifest = target / "candidate_manifest.json"
                if case in ("manifest","digest","artifact_ref"):
                    payload=json.loads(manifest.read_text())
                    if case=="manifest": payload["release_status"]="published"
                    if case=="digest": payload["candidate_digest"]="0"*64
                    if case=="artifact_ref": payload["database"]["size_bytes"]+=1
                    manifest.write_text(json.dumps(payload))
                elif case=="sums": (target/"SHA256SUMS").write_bytes(b"bad\n")
                elif case=="rollback": (target/"rollback.json").write_bytes(b"{}\n")
                elif case=="image": next((target/"images").rglob("*.svg")).write_bytes(b"bad")
                elif case=="unreadable": db.write_bytes(b"not sqlite")
                elif case=="integrity":
                    with sqlite3.connect(db.as_uri() + "?mode=ro", uri=True) as check:
                        page = check.execute("SELECT rootpage FROM sqlite_master WHERE name='task12_v122_candidates_v1'").fetchone()[0]
                        size = check.execute("PRAGMA page_size").fetchone()[0]
                    content = bytearray(db.read_bytes())
                    content[(page - 1) * size] = 0  # Invalid data b-tree page type.
                    db.write_bytes(content)
                else:
                    with sqlite3.connect(db) as con:
                        con.execute("PRAGMA foreign_keys=OFF")
                        if case=="schema": con.execute("CREATE TABLE rogue(x)")
                        if case=="foreign_key": con.execute("UPDATE task12_v122_images_v1 SET batch_id='missing'")
                        if case=="ledger": con.execute("UPDATE task12_v122_batch_ledger_v1 SET manifest_sha256=?",("0"*64,))
                        if case=="count": con.execute("DELETE FROM task12_v122_candidates_v1")
                before=_tree(target)
                report=verify_v122_candidate(V122CandidateVerificationRequest(target,(approved,),_contract()),self.config)
                self.assertEqual(report.status,"FAIL")
                self.assertFalse(next(x.passed for x in report.checks if x.name==expected))
                self.assertEqual(_tree(target),before)

    def test_forged_empty_or_missing_nested_authority_rejected_without_crash(self):
        from joy_m2.ingest import build_v122_candidate
        approved = _approved(self.package, self.config)
        def clone(value, **changes):
            result = object.__new__(type(value))
            for key, item in vars(value).items():
                object.__setattr__(result, key, changes.get(key, item))
            return result
        output = self.root / "forged-carrier"
        valid = V122CandidateBuildRequest((approved,), output, _contract())
        for batches in ((), (clone(approved, approval=None),)):
            with self.subTest(batches=len(batches)):
                forged = clone(valid, approved_batches=batches)
                try:
                    build_v122_candidate(forged, self.config)
                except PipelineError:
                    pass
                except Exception as error:
                    self.fail(f"writer leaked {type(error).__name__}: {error}")
                else:
                    self.fail("writer accepted a forged carrier")
                self.assertFalse(output.exists())

    def _forged_candidates(self, approved, candidates):
        from dataclasses import replace
        from joy_m2.ingest.v122_verification import _preflight_payload
        from joy_m2.ingest.v122_writer_profiles import canonical_json_file_bytes
        result = replace(approved.preflight_result, candidates=candidates)
        report = replace(
            result.report,
            proposed_ids=tuple(c.proposed_question_id for c in candidates),
            level_counts=tuple(
                (level, sum(c.difficulty_level == level for c in candidates))
                for level in range(1, 6) if any(c.difficulty_level == level for c in candidates)
            ),
        )
        result = replace(result, report=report)
        intermediate = object.__new__(V122ApprovedBatch)
        for key, value in vars(approved).items():
            object.__setattr__(intermediate, key, result if key == "preflight_result" else value)
        digest = hashlib.sha256(canonical_json_file_bytes(_preflight_payload(intermediate))).hexdigest()
        result = replace(result, report=replace(report, preflight_sha256=digest))
        approval = replace(approved.approval, preflight_sha256=digest,
            statement=f"USER APPROVED IMPORT BATCH {report.batch_id} {digest} V1.22 PARENT {GENESIS}")
        return V122ApprovedBatch(result, approved.package_root, approval)

    def test_writer_reconstructs_candidates_from_canonical_bytes(self):
        from dataclasses import replace
        from joy_m2.ingest import build_v122_candidate
        from joy_m2.ingest.v122_preflight import _formal_indexes
        from joy_m2.ingest.v122_verification import _normalized_text_sha256
        approved = _approved(self.package, self.config)
        source = approved.preflight_result.candidates[0]
        primary = next(x for x in sorted(_formal_indexes(BASELINE)[1]) if x != source.primary_type)
        changes = (
            {"solution_original": "not the canonical answer"},
            {"question_text_original": "Not the canonical question",
             "normalized_text_sha256": _normalized_text_sha256("Not the canonical question")},
            {"primary_type": primary},
            {"source_question_number": "forged-source-number"},
            {"translation_evidence": "source:source/source.txt#forged-fragment"},
            {"difficulty_level": 2},
        )
        before = _tree(self.package)
        for index, change in enumerate(changes):
            with self.subTest(change=change):
                forged = self._forged_candidates(approved, (replace(source, **change),))
                output = self.root / f"forged-record-{index}"
                with self.assertRaises(ImportApprovalError):
                    build_v122_candidate(V122CandidateBuildRequest((forged,), output, _contract()), self.config)
                self.assertFalse(output.exists())
                self.assertEqual(_tree(self.package), before)

    def test_writer_rejects_reordered_canonical_candidates(self):
        from joy_m2.ingest import build_v122_candidate
        records_path = self.package / "records/candidates.json"
        records = json.loads(records_path.read_text(encoding="utf-8"))
        records.append(dict(
            records[0], proposed_question_id="TASK12-ORDER-002",
            source_question_number="A2", source_fragment_hash="b" * 64,
            question_text_original="Solve 7y + 2 = 37.",
        ))
        raw = (json.dumps(records, ensure_ascii=False) + "\n").encode("utf-8")
        records_path.write_bytes(raw)
        manifest_path = self.package / "import_manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["candidate_records"][0].update(
            sha256=hashlib.sha256(raw).hexdigest(), size_bytes=len(raw))
        manifest_path.write_text(json.dumps(manifest) + "\n", encoding="utf-8")
        approved = _approved(self.package, self.config)
        self.assertEqual(approved.preflight_result.report.new_candidate_count, 2)
        forged = self._forged_candidates(approved, approved.preflight_result.candidates[::-1])
        before = _tree(self.package)
        output = self.root / "forged-order"
        with self.assertRaises(ImportApprovalError):
            build_v122_candidate(V122CandidateBuildRequest((forged,), output, _contract()), self.config)
        self.assertFalse(output.exists())
        self.assertEqual(_tree(self.package), before)

    def test_verifier_independently_reconstructs_canonical_record_authority(self):
        from dataclasses import replace
        from unittest import mock
        from joy_m2.ingest import build_v122_candidate, verify_v122_candidate
        approved = _approved(self.package, self.config)
        forged = self._forged_candidates(approved, (
            replace(approved.preflight_result.candidates[0], solution_original="not canonical"),))
        output = self.root / "forged-persisted"
        # Construct hostile synthetic artifacts while bypassing only the writer's
        # package binding; the later independent verifier has no patched checks.
        with mock.patch("joy_m2.ingest.v122_verification._package_evidence_valid", return_value=True):
            build_v122_candidate(V122CandidateBuildRequest((forged,), output, _contract()), self.config)
        before = _tree(output)
        report = verify_v122_candidate(V122CandidateVerificationRequest(output, (forged,), _contract()), self.config)
        self.assertEqual(report.status, "FAIL")
        self.assertFalse(next(c.passed for c in report.checks if c.name == "batch_authority_artifacts"))
        self.assertEqual(_tree(output), before)

    def _invalid_manifest_envelopes(self):
        original = (self.package / "import_manifest.json").read_text(encoding="utf-8")
        parsed = json.loads(original)
        return (
            ("duplicate-key", original.replace("{", '{"target_release_version":"V1.21",', 1)),
            ("reordered-fields", json.dumps(dict(reversed(tuple(parsed.items())))) + "\n"),
        )

    def test_writer_rejects_stale_noncanonical_manifest_envelope(self):
        from joy_m2.ingest import build_v122_candidate
        approved = _approved(self.package, self.config)
        manifest_path = self.package / "import_manifest.json"
        cases = self._invalid_manifest_envelopes()
        for name, raw in cases:
            with self.subTest(name=name):
                manifest_path.write_text(raw, encoding="utf-8")
                with self.assertRaises(PipelineError):
                    load_v122_import_manifest(manifest_path)
                before = _tree(self.package)
                output = self.root / name
                with self.assertRaises(ImportApprovalError):
                    build_v122_candidate(V122CandidateBuildRequest((approved,), output, _contract()), self.config)
                self.assertFalse(output.exists())
                self.assertEqual(_tree(self.package), before)

    def test_verifier_rejects_stale_noncanonical_manifest_envelope(self):
        from joy_m2.ingest import verify_v122_candidate
        approved, artifacts = self.build()
        manifest_path = self.package / "import_manifest.json"
        cases = self._invalid_manifest_envelopes()
        for name, raw in cases:
            with self.subTest(name=name):
                manifest_path.write_text(raw, encoding="utf-8")
                with self.assertRaises(PipelineError):
                    load_v122_import_manifest(manifest_path)
                before = _tree(self.root)
                report = verify_v122_candidate(V122CandidateVerificationRequest(
                    artifacts.database.path.parent, (approved,), _contract()), self.config)
                self.assertEqual(report.status, "FAIL")
                self.assertFalse(next(c.passed for c in report.checks if c.name == "batch_authority_artifacts"))
                self.assertEqual(_tree(self.root), before)

    def test_uri_reserved_output_names_are_read_only_and_cleanup_safe(self):
        from unittest import mock
        from joy_m2.ingest import build_v122_candidate, verify_v122_candidate
        approved = _approved(self.package, self.config)
        for marker in ("#", "?"):
            with self.subTest(marker=marker):
                output = self.root / f"candidate{marker}1"
                try:
                    artifacts = build_v122_candidate(V122CandidateBuildRequest((approved,), output, _contract()), self.config)
                except PipelineError as error:
                    self.fail(f"valid path failed and may create stray files: {error}")
                before = _tree(self.root)
                report = verify_v122_candidate(V122CandidateVerificationRequest(output, (approved,), _contract()), self.config)
                self.assertEqual(report.status, "PASS")
                self.assertEqual(_tree(self.root), before)
                target = self.root / f"fault{marker}2"
                with mock.patch("joy_m2.ingest.v122_writer.atomic_rename_no_replace", side_effect=OSError("injected")):
                    with self.assertRaises(PipelineError):
                        build_v122_candidate(V122CandidateBuildRequest((approved,), target, _contract()), self.config)
                self.assertEqual(_tree(self.root), before)

    def test_unsafe_output_targets_and_read_only_baseline_connection(self):
        from joy_m2.ingest import build_v122_candidate
        from unittest import mock
        import joy_m2.ingest.v122_writer as writer
        approved=_approved(self.package,self.config)
        link=self.root/"data/staging/link"
        link.symlink_to(self.package,target_is_directory=True)
        for output in (self.package/"nested", link/"nested", BASELINE.parent/"forbidden", ROOT/"tmp/pdfs/task12-v122-hkdse-2019/not-staging"):
            with self.subTest(output=output),self.assertRaises(PipelineError):
                build_v122_candidate(V122CandidateBuildRequest((approved,),output,_contract()),self.config)
            self.assertFalse(output.exists())
        connect=sqlite3.connect
        calls=[]
        def audited_connect(*args,**kwargs):
            if str(BASELINE) in str(args[0]) or BASELINE.as_uri() in str(args[0]):
                calls.append(args[0])
                self.assertIn("mode=ro",str(args[0]))
                self.assertTrue(kwargs.get("uri"))
            return connect(*args,**kwargs)
        with mock.patch.object(writer.sqlite3,"connect",side_effect=audited_connect):
            self.build()
        self.assertTrue(calls)


class V122ParentPreflightTests(unittest.TestCase):
    setUp = V122CandidateBehaviorTests.setUp
    tearDown = V122CandidateBehaviorTests.tearDown
    build = V122CandidateBehaviorTests.build
    _invoke = V122CandidateBehaviorTests._invoke

    def parent_and_b(self):
        from joy_m2.ingest import verify_v122_candidate
        approved, artifacts = self.build()
        parent = V122CandidateVerificationRequest(artifacts.database.path.parent, (approved,), _contract())
        self.assertEqual(verify_v122_candidate(parent,self.config).status,"PASS")
        self.assertEqual(artifacts.state.projected_question_count,592)
        package = _make_named_package(self.root,"b")
        return approved, artifacts, parent, package

    def preflight_parent(self,package,parent):
        from dataclasses import replace
        try:
            return preflight_v122_import(replace(_request(package),parent_candidate=parent), self.config)
        except NotImplementedError:
            self.fail("verified first-generation prerequisite passed; parent preflight missing")

    def test_verified_parent_binding_counts_and_preservation(self):
        _, artifacts, parent, package = self.parent_and_b()
        before=_tree(parent.candidate_dir)
        result=self.preflight_parent(package,parent)
        self.assertEqual(result.report.status,"READY FOR USER IMPORT APPROVAL")
        self.assertEqual(result.report.parent_candidate_digest,artifacts.state.candidate_digest)
        self.assertNotEqual(result.report.parent_candidate_digest,GENESIS)
        self.assertEqual((result.report.parent_batch_count,result.report.before_count,
            result.report.new_candidate_count,result.report.projected_after_count),(1,592,1,593))
        self.assertEqual(_tree(parent.candidate_dir),before)


    def test_duplicate_and_collision_against_verified_parent(self):
        approved, artifacts, parent, package=self.parent_and_b()
        first=approved.preflight_result.candidates[0]
        _rename_declared_image(package,first.image_paths[0])
        _rewrite_record(package,{"proposed_question_id":first.proposed_question_id,
            "source_id":first.source_id,"source_question_number":first.source_question_number,
            "source_section":first.source_section,"source_fragment_hash":first.source_fragment_hash,
            "question_text_original":first.question_text_original,
            "image_paths":list(first.image_paths),"image_roles":list(first.image_roles)})
        before=_tree(parent.candidate_dir)
        result=self.preflight_parent(package,parent)
        self.assertEqual((result.report.duplicate_count,result.report.new_candidate_count),(1,0))
        self.assertIn("duplicate_exact",{i.code for i in result.issues})
        _rewrite_record(package,{"question_text_original":"Different content retaining the same candidate ID"})
        result=self.preflight_parent(package,parent)
        self.assertEqual(result.report.rejected_count,1)
        self.assertIn("collision_candidate_id",{i.code for i in result.issues})
        self.assertEqual(_tree(parent.candidate_dir),before)

    def test_corrupt_verified_parent_cannot_be_used(self):
        _, _, parent, package=self.parent_and_b()
        manifest=parent.candidate_dir/"candidate_manifest.json"
        payload=json.loads(manifest.read_text())
        payload["candidate_digest"]="0"*64
        manifest.write_text(json.dumps(payload))
        before=_tree(parent.candidate_dir)
        with self.assertRaises(PipelineError):
            self.preflight_parent(package,parent)
        self.assertEqual(_tree(parent.candidate_dir),before)


class V122MultiBatchTests(unittest.TestCase):
    setUp = V122CandidateBehaviorTests.setUp
    tearDown = V122CandidateBehaviorTests.tearDown
    _invoke = V122CandidateBehaviorTests._invoke

    def test_second_batch_requires_verified_parent_and_appends_atomically(self):
        from joy_m2.ingest import build_v122_candidate as _build
        build_v122_candidate = lambda *args: self._invoke(_build, *args)

        approved_a = _approved(self.package, self.config)
        parent_root = self.root / "parent"
        parent = build_v122_candidate(
            V122CandidateBuildRequest((approved_a,), parent_root, _contract()),
            self.config,
        )
        package_b = _make_named_package(self.root, "b")
        parent_request = V122CandidateVerificationRequest(
            parent_root, (approved_a,), _contract()
        )
        approved_b = _approved(package_b, self.config, parent_request)
        self.assertEqual(approved_b.approval.parent_candidate_digest, parent.state.candidate_digest)
        self.assertEqual(approved_b.preflight_result.report.status, "READY FOR USER IMPORT APPROVAL")
        child = build_v122_candidate(
            V122CandidateBuildRequest(
                (approved_a, approved_b), self.root / "child", _contract()
            ),
            self.config,
        )
        self.assertEqual(parent.state.projected_question_count, 592)
        self.assertEqual(child.state.projected_question_count, 593)
        self.assertEqual(len(child.state.batch_ledger), 2)
        self.assertEqual(
            child.state.batch_ledger[1].parent_candidate_digest,
            parent.state.candidate_digest,
        )
        twin = build_v122_candidate(
            V122CandidateBuildRequest((approved_a, approved_b),
                                     self.root / "child-twin", _contract()),
            self.config,
        )
        self.assertEqual(_tree(child.database.path.parent), _tree(twin.database.path.parent))
        self.assertEqual(child.state.candidate_digest, twin.state.candidate_digest)
        with self.assertRaises(PipelineError):
            build_v122_candidate(
                V122CandidateBuildRequest((approved_a, approved_b),
                                         parent_root / "nested", _contract()),
                self.config,
            )

    def test_stale_preflight_and_approval_cannot_append_and_preserve_parent(self):
        from joy_m2.ingest import build_v122_candidate as _build
        build_v122_candidate = lambda *args: self._invoke(_build, *args)

        approved_a = _approved(self.package, self.config)
        parent_a = self.root / "parent-a"
        build_v122_candidate(
            V122CandidateBuildRequest((approved_a,), parent_a, _contract()),
            self.config,
        )
        package_b = _make_named_package(self.root, "b")
        approved_b = _approved(
            package_b,
            self.config,
            V122CandidateVerificationRequest(parent_a, (approved_a,), _contract()),
        )
        parent_ab = self.root / "parent-ab"
        build_v122_candidate(
            V122CandidateBuildRequest(
                (approved_a, approved_b), parent_ab, _contract()
            ),
            self.config,
        )
        before = _tree(parent_ab)
        package_c = _make_named_package(self.root, "c")
        stale_c = _approved(
            package_c,
            self.config,
            V122CandidateVerificationRequest(parent_a, (approved_a,), _contract()),
        )
        current_c = _approved(
            _make_named_package(self.root / "current", "c"),
            self.config,
            V122CandidateVerificationRequest(
                parent_ab, (approved_a, approved_b), _contract()
            ),
        )
        self.assertNotEqual(
            stale_c.preflight_result.report.parent_candidate_digest,
            current_c.preflight_result.report.parent_candidate_digest,
        )
        self.assertNotEqual(
            stale_c.preflight_result.report.preflight_sha256,
            current_c.preflight_result.report.preflight_sha256,
        )
        output = self.root / "stale-child"
        with self.assertRaises(ImportApprovalError):
            build_v122_candidate(
                V122CandidateBuildRequest(
                    (approved_a, approved_b, stale_c), output, _contract()
                ),
                self.config,
            )
        self.assertFalse(output.exists())
        self.assertEqual(_tree(parent_ab), before)


    def test_multi_batch_verifier_rejects_nonmatching_existing_generation(self):
        from joy_m2.ingest import build_v122_candidate, verify_v122_candidate
        approved_a=_approved(self.package,self.config)
        parent_root=self.root/"parent-verify"
        parent=build_v122_candidate(V122CandidateBuildRequest((approved_a,),parent_root,_contract()),self.config)
        request=V122CandidateVerificationRequest(parent_root,(approved_a,),_contract())
        self.assertEqual(verify_v122_candidate(request,self.config).status,"PASS")
        approved_b=_approved(_make_named_package(self.root,"b"),self.config,request)
        self.assertEqual(approved_b.approval.parent_candidate_digest,parent.state.candidate_digest)
        try:
            result=verify_v122_candidate(V122CandidateVerificationRequest(parent_root,(approved_a,approved_b),_contract()),self.config)
        except NotImplementedError:
            self.fail("valid B authority reached multi-batch verifier missing behavior")
        self.assertEqual(result.status,"FAIL")

    def test_reordered_genesis_stale_package_and_forged_counts_block(self):
        from joy_m2.ingest import build_v122_candidate, verify_v122_candidate
        from dataclasses import replace
        approved_a=_approved(self.package,self.config)
        parent_root=self.root/"parent-negatives"
        parent=build_v122_candidate(V122CandidateBuildRequest((approved_a,),parent_root,_contract()),self.config)
        parent_request=V122CandidateVerificationRequest(parent_root,(approved_a,),_contract())
        self.assertEqual(verify_v122_candidate(parent_request,self.config).status,"PASS")
        package_b=_make_named_package(self.root,"b")
        b=_approved(package_b,self.config,parent_request)
        stale=_approved(package_b,self.config,None)
        self.assertNotEqual(b.approval.parent_candidate_digest,stale.approval.parent_candidate_digest)
        before=_tree(parent_root)
        for label,prefix in (("reordered",(b,approved_a)),("stale-genesis",(approved_a,stale))):
            with self.subTest(label=label):
                output=self.root/label
                try:
                    with self.assertRaises(ImportApprovalError):
                        build_v122_candidate(V122CandidateBuildRequest(prefix,output,_contract()),self.config)
                except NotImplementedError:
                    self.fail("valid B authority reached missing multi-batch writer")
                self.assertFalse(output.exists())
                self.assertEqual(_tree(parent_root),before)
        forged_report = object.__new__(type(b.preflight_result.report))
        for key, value in vars(b.preflight_result.report).items():
            object.__setattr__(forged_report, key, value + 1 if key == "new_candidate_count" else value)
        forged_result = replace(b.preflight_result, report=forged_report)
        forged_b = replace(b, preflight_result=forged_result)
        with self.assertRaises(ImportApprovalError):
            build_v122_candidate(V122CandidateBuildRequest(
                (approved_a, forged_b), self.root/"forged-counts", _contract()), self.config)
        verification = verify_v122_candidate(V122CandidateVerificationRequest(
            parent_root, (approved_a, forged_b), _contract()), self.config)
        self.assertEqual(verification.status, "FAIL")
        self.assertFalse((self.root/"forged-counts").exists())
        record=package_b/"records/candidates.json"
        record.write_bytes(record.read_bytes()+b" ")
        with self.assertRaises(ImportApprovalError):
            self._invoke(build_v122_candidate,V122CandidateBuildRequest((approved_a,b),self.root/"stale-bytes",_contract()),self.config)
        self.assertEqual(_tree(parent_root),before)
