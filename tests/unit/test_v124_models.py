"""Fixed V1.24 module-local boundary, no F6 source or real approval."""
import importlib
import importlib.util
import inspect
import unittest
"""Test-first contracts for the fixed V1.24 candidate boundary."""
import unittest
class V124ManifestTests(unittest.TestCase):
    def snapshot(self):
        return tuple((p.relative_to(self.root).as_posix(), p.read_bytes())
                     for p in sorted(self.root.rglob("*")) if p.is_file())

    def reject_unchanged(self):
        before = self.snapshot()
        with self.assertRaises(PipelineError):
            self.load()
        self.assertEqual(self.snapshot(), before)

    def test_malformed_utf8(self):
        self.path.write_bytes(b"\xff")
        self.reject_unchanged()

    def test_malformed_json(self):
        self.path.write_text("{")
        self.reject_unchanged()

    def test_nonfinite_json(self):
        original = self.path.read_text()
        for value in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(value=value):
                self.path.write_text(original.replace('"chapter": "Algebra"', '"chapter": ' + value))
                # Fixture chapter need not be Algebra; replace via its actual JSON value.
                import json
                text = original.replace(json.dumps(self.payload["chapter"]), value, 1)
                self.path.write_text(text)
                self.reject_unchanged()

    def test_wrong_schema(self):
        self.payload["schema_version"] = "task13-v123-import-manifest-v1"
        self.write()
        self.reject_unchanged()

    def test_wrong_target(self):
        self.payload["target_release_version"] = "V1.23"
        self.write()
        self.reject_unchanged()

    def test_nested_duplicate_keys(self):
        self.path.write_text(self.path.read_text().replace('"relative_path":', '"sha256": "forged", "relative_path":', 1))
        self.reject_unchanged()

    def test_bool_size(self):
        self.payload["candidate_records"][0]["size_bytes"] = True
        self.write()
        self.reject_unchanged()

    def test_unsafe_paths(self):
        for value in ("/tmp/escape", "../escape", "a\\b", "a/./b"):
            with self.subTest(value=value):
                self.payload["candidate_records"][0]["relative_path"] = value
                self.write()
                self.reject_unchanged()

    def test_duplicate_member(self):
        self.payload["candidate_records"].append(self.payload["candidate_records"][0].copy())
        self.write()
        self.reject_unchanged()

    def test_missing_inventory(self):
        (self.root / self.payload["candidate_records"][0]["relative_path"]).unlink()
        self.reject_unchanged()

    def test_bad_size(self):
        self.payload["candidate_records"][0]["size_bytes"] += 1
        self.write()
        self.reject_unchanged()

    def test_nested_entry_order(self):
        entry = self.payload["candidate_records"][0]
        entry["relative_path"] = entry.pop("relative_path")
        self.write()
        self.reject_unchanged()

    def setUp(self):
        import tempfile, shutil, json
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name) / "package"
        shutil.copytree(Path(__file__).resolve().parents[2] / "tests/fixtures/task10a/v120-batch-a", self.root)
        self.path = self.root / "import_manifest.json"
        self.payload = json.loads(self.path.read_text())
        self.payload["schema_version"] = "task14-v124-import-manifest-v1"
        self.payload["target_release_version"] = "V1.24"
        self.write()

    def write(self):
        import json
        self.path.write_text(json.dumps(self.payload, ensure_ascii=False) + "\n", encoding="utf-8")

    def load(self):
        from joy_m2.ingest.v124_manifest import load_v124_import_manifest
        try:
            return load_v124_import_manifest(self.path)
        except NotImplementedError:
            self.fail("strict V1.24 loader behavior missing")

    def test_valid_exact_manifest(self):
        result = self.load()
        self.assertEqual(result.target_release_version, "V1.24")
        self.assertEqual(tuple(x.relative_path for x in result.candidate_records),
                         tuple(x["relative_path"] for x in self.payload["candidate_records"]))
        self.assertEqual(len(fields(result)), 18)

    def test_duplicate_json_key_rejected(self):
        self.path.write_text(self.path.read_text().replace('{"schema_version":', '{"batch_id":"forged","schema_version":', 1))
        with self.assertRaises(PipelineError):
            self.load()

    def test_missing_extra_wrong_type_and_group_rejected(self):
        import copy
        original = copy.deepcopy(self.payload)
        for mutation in ("missing", "extra", "wrong_type", "group_type", "kind", "escape", "order", "digest"):
            with self.subTest(mutation=mutation):
                self.payload = copy.deepcopy(original)
                if mutation == "missing":
                    del self.payload["batch_id"]
                elif mutation == "extra":
                    self.payload["unapproved"] = 1
                elif mutation == "wrong_type":
                    self.payload["batch_id"] = True
                elif mutation == "group_type":
                    self.payload["candidate_records"] = {}
                elif mutation == "kind":
                    self.payload["candidate_records"][0]["kind"] = "image"
                elif mutation == "escape":
                    self.payload["candidate_records"][0]["relative_path"] = "../outside.json"
                elif mutation == "order":
                    self.payload["schema_version"] = self.payload.pop("schema_version")
                else:
                    self.payload["candidate_records"][0]["sha256"] = "0" * 64
                self.write()
                with self.assertRaises(PipelineError):
                    self.load()

    def test_inventory_closure_and_symlinks_rejected(self):
        rogue = self.root / "rogue.txt"
        rogue.write_text("rogue")
        with self.assertRaises(PipelineError):
            self.load()
        rogue.unlink()
        rogue.symlink_to(self.path)
        with self.assertRaises(PipelineError):
            self.load()


class V124ApiTests(unittest.TestCase):
    def test_modules_and_exact_signatures(self):
        import joy_m2.ingest as package
        before = package.__all__
        expected = {'manifest': ('load_v124_import_manifest', ('path',)),
                    'preflight': ('preflight_v124_import', ('request', 'config')),
                    'writer': ('build_v124_candidate', ('request', 'config')),
                    'verification': ('verify_v124_candidate', ('request', 'config'))}
        for suffix in ('models', 'manifest', 'writer_profiles', 'preflight', 'writer', 'verification'):
            name = 'joy_m2.ingest.v124_' + suffix
            self.assertIsNotNone(importlib.util.find_spec(name), f'missing module-local API {name}')
            module = importlib.import_module(name)
            if suffix in expected:
                fn, parameters = expected[suffix]
                self.assertTrue(hasattr(module, fn))
                self.assertEqual(tuple(inspect.signature(getattr(module, fn)).parameters), parameters)
        from joy_m2.ingest import v124_preflight, v124_writer_profiles
        self.assertEqual(tuple(inspect.signature(v124_preflight._formal_indexes).parameters), ('path',))
        self.assertEqual(tuple(inspect.signature(v124_writer_profiles._genesis_digest).parameters), ())
        self.assertEqual(package.__all__, before)
        self.assertFalse(any('v124' in name.lower() for name in package.__all__))


class V124PrimitiveTests(unittest.TestCase):
    def test_independent_literal_genesis_and_ddl_namespace(self):
        import hashlib, json
        from joy_m2.ingest import v124_writer_profiles as p
        projection = dict(baseline_database_sha256='28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd',
            baseline_question_count=677,
            baseline_release_digest='84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc',
            baseline_release_version='V1.23', candidate_count=0,
            schema='task14-v124-genesis-v1', target_release_version='V1.24')
        expected = hashlib.sha256((json.dumps(projection, ensure_ascii=False,
            sort_keys=True, separators=(',', ':'), allow_nan=False) + '\n').encode()).hexdigest()
        self.assertEqual(expected, '797ed06ca5833bac060c1603cada38a6f2aa9eb080a40d9dc892bba9a549773a')
        try: actual = p._genesis_digest()
        except NotImplementedError: self.fail('genesis reconstruction missing')
        self.assertEqual(actual, expected)
        self.assertTrue(hasattr(p, 'TASK14_SCHEMA_SQL'), 'DDL declarations missing')
        ddl = '\n'.join(p.TASK14_SCHEMA_SQL)
        for fragment in ('task14_v124_batch_ledger_v1', 'task14_v124_candidates_v1',
                'task14_v124_images_v1', 'task14_v124_taxonomy_v1', 'task14_candidate_questions_v124',
                'aggregate_order >= 678', 'formal_complete_questions_v123'):
            self.assertIn(fragment, ddl)
        self.assertEqual(len(p.CHECK_NAMES), 24)
        self.assertIn('v123_preservation', p.CHECK_NAMES)
        self.assertNotIn('v122_preservation', p.CHECK_NAMES)

from dataclasses import fields, replace
import importlib
import inspect
from pathlib import Path
import sys
import unittest
from typing import get_type_hints

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from joy_m2.errors import ImportApprovalError, PipelineError
from joy_m2.ingest.models import (
    BatchImportManifest,
    ImportAdaptation,
    ImportCandidate,
    ImportFileEvidence,
    ImportIssue,
    ImportPreflightReport,
    ImportPreflightResult,
)
from joy_m2.ingest.promotion_models import (
    ReleasePromotionApproval,
    V119PromotionArtifacts,
    V119PromotionBuildRequest,
    V119PromotionContract,
    V119PromotionVerificationRequest,
    V119PublicationRequest,
)
from joy_m2.ingest.writer_models import (
    ImportApproval,
    V119CandidateArtifacts,
    V119VerificationRequest,
    V119WriteRequest,
    V119WriterContract,
)
from joy_m2.models import ArtifactRef, VerificationReport


SHA_A = "a" * 64
SHA_B = "b" * 64
SHA_C = "c" * 64
GENESIS = "797ed06ca5833bac060c1603cada38a6f2aa9eb080a40d9dc892bba9a549773a"
BASELINE_SHA = "28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd"
BASELINE_MANIFEST_SHA = "54d192436e761c9bfe810510b77a902c5ae659bebdfbc4da8475aac271be8498"
BASELINE_RELEASE_DIGEST = "84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc"


class V124ModelTests(unittest.TestCase):
    """Each test names a public-contract mutation it prevents."""

    def test_nested_old_version_and_parallel_carriers_rejected(self):
        from joy_m2.ingest.v123_models import V123ImportApproval
        old = V123ImportApproval("batch", SHA_B, "V1.23", SHA_A,
            f"USER APPROVED IMPORT BATCH batch {SHA_B} V1.23 PARENT {SHA_A}")
        approval = self._approval()
        entry = self.module.V124BatchLedgerEntry(1, approval.batch_id, GENESIS,
            SHA_B, SHA_C, approval, 1, 1, 678)
        for invalid in (old, object(), None, dict(approval.__dict__)):
            with self.subTest(invalid=type(invalid).__name__), self.assertRaises(PipelineError):
                replace(entry, approval=invalid)
        objects = ((self._result(), "manifest"), (self._result(), "effective_state"),
                   (self._result(), "report"), (self._approved_batch(), "preflight_result"))
        for obj, name in objects:
            with self.subTest(field=name), self.assertRaises(PipelineError):
                replace(obj, **{name: dict(getattr(obj, name).__dict__)})

    def test_all_constructed_models_frozen_and_mutable_inputs_isolated(self):
        from dataclasses import FrozenInstanceError, MISSING
        for obj in (self._manifest(), self._state(), self._result(), self._report(),
                    self._approval(), self._approved_batch(), self._contract()):
            for field in fields(obj):
                self.assertIs(field.default, MISSING)
                self.assertIs(field.default_factory, MISSING)
                with self.assertRaises(FrozenInstanceError):
                    setattr(obj, field.name, getattr(obj, field.name))
                value = getattr(obj, field.name)
                if type(value) is tuple:
                    mutable = list(value)
                    copied = replace(obj, **{field.name: mutable})
                    mutable.append(object())
                    self.assertEqual(getattr(copied, field.name), value)

    def setUp(self) -> None:
        self.module = importlib.import_module("joy_m2.ingest.v124_models")
        self.assertIsNotNone(getattr(self.module, "V124CandidateContract", None), "V124 model contract missing")

    def _artifact(self, kind: str = "sqlite") -> ArtifactRef:
        return ArtifactRef(Path("/tmp/v124-baseline.sqlite3"), BASELINE_SHA, 10928128, kind)

    def test_frozen_tuple_copy_and_invalid_genesis(self):
        from dataclasses import FrozenInstanceError, MISSING
        state = self._state()
        with self.assertRaises(FrozenInstanceError):
            state.candidate_count = 1
        ledger = []
        copied = self.module.V124EffectiveState(self._artifact(), GENESIS, ledger, 0, 677)
        ledger.append(object())
        self.assertEqual(copied.batch_ledger, ())
        for digest in (None, "", "331192032f184a44ed383e6dacc2f06fbacb60ad94414298fcb935ff56cb5906", "4ff624aca875b0191fe8a617516d2919c6d700ce69c5a3b5d236adcf7ecc59f1", "0" * 64):
            with self.subTest(digest=digest), self.assertRaises(PipelineError):
                self.module.V124EffectiveState(self._artifact(), digest, [], 0, 677)
        for name, carrier in vars(self.module).items():
            if name.startswith("V124") and isinstance(carrier, type):
                self.assertTrue(all(f.default is MISSING and f.default_factory is MISSING for f in fields(carrier)))

    def _evidence(self, path: str, kind: str) -> ImportFileEvidence:
        return ImportFileEvidence(path, SHA_A, 1, kind)

    def _manifest(self):
        return self.module.V124BatchImportManifest(
            "task14-v124-import-manifest-v1", "batch.01-A", "Joy M2 AI Database", "M2", "Algebra",
            "V1.24", [self._evidence("candidates/a.json", "candidate_json")],
            [self._evidence("source/a.mmd", "source")], [self._evidence("answers/a.md", "answer")],
            [self._evidence("images/a.png", "image")], [], [],
            "preserve_source_and_store_reviewed_chinese_separately", "one_complete_question_per_record",
            "joy_level_1_5", "controlled_primary_type_and_tags", "preserve_source_answer_identity",
            "source_or_independently_verified_with_identity",
        )

    def _candidate(self, question_id: str = "V124-Q-1") -> ImportCandidate:
        return ImportCandidate(
            question_id, "source", "1", "section", SHA_A, SHA_B, "Question", "",
            "missing", None, "", "", "missing_from_source", "", "missing", None,
            [], [], [], "algebra", [], "missing", None, "missing", "incomplete",
        )

    def _report(self, manifest=None, *, status: str = "READY FOR USER IMPORT APPROVAL"):
        manifest = manifest or self._manifest()
        return self.module.V124ImportPreflightReport(
            manifest.batch_id, status, SHA_B, SHA_C, "V1.23", BASELINE_RELEASE_DIGEST, 677,
            "V1.24", GENESIS, 0, 677, 1, 1, 0, 0, 0, 0, 678,
            [], [], [], 0, 0, [], [], [], [], [], [], [(1, 1)], ["V124-Q-1"], [], [], [],
        )

    def _state(self):
        return self.module.V124EffectiveState(self._artifact(), GENESIS, [], 0, 677)

    def _result(self, manifest=None):
        manifest = manifest or self._manifest()
        return self.module.V124ImportPreflightResult(manifest, self._state(), [self._candidate()], [], self._report(manifest))

    def _contract(self):
        return self.module.V124CandidateContract(
            "V1.24", "V1.23", 677, BASELINE_SHA, 10928128, BASELINE_MANIFEST_SHA, 6728,
            BASELINE_RELEASE_DIGEST, "task14-v124-import-manifest-v1", "task14-v124-preflight-v1",
            "task14-v124-import-approval-v1", "task14-v124-candidate-manifest-v1",
            "task14-v124-candidate-v1", "task14-v124-candidate-identity-v1", "task14-v124-rollback-v1",
            124, "Joy_M2_V1.24_candidate.sqlite3", "candidate_manifest.json", "SHA256SUMS", "rollback.json",
            "authority/batches", "images/sha256", "formal_complete_questions_v123",
            ["task14_v124_batch_ledger_v1", "task14_v124_candidates_v1", "task14_v124_images_v1", "task14_v124_taxonomy_v1"],
            ["task14_candidate_questions_v124"],
        )

    def _approval(self, manifest=None):
        manifest = manifest or self._manifest()
        return self.module.V124ImportApproval(
            manifest.batch_id, SHA_B, "V1.24", GENESIS,
            f"USER APPROVED IMPORT BATCH {manifest.batch_id} {SHA_B} V1.24 PARENT {GENESIS}",
        )

    def _approved_batch(self):
        manifest = self._manifest()
        return self.module.V124ApprovedBatch(self._result(manifest), Path("/tmp/package"), self._approval(manifest))

    def test_exact_public_field_envelopes_are_frozen_and_default_free(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v124_models"), "V124CandidateContract", None), "V124 model contract missing")
        expected = {
            "V124BatchImportManifest": ("schema_version", "batch_id", "project", "module", "chapter", "target_release_version", "candidate_records", "source_files", "answer_files", "image_files", "teacher_notes_files", "common_errors_files", "language_policy", "split_policy", "difficulty_policy", "tag_policy", "answer_policy", "explanation_policy"),
            "V124AdaptedImportPackage": ("package_root", "manifest_path", "manifest"),
            "V124BatchLedgerEntry": ("ordinal", "batch_id", "parent_candidate_digest", "preflight_sha256", "manifest_sha256", "approval", "batch_candidate_count", "cumulative_candidate_count", "projected_question_count"),
            "V124EffectiveState": ("baseline_database", "candidate_digest", "batch_ledger", "candidate_count", "projected_question_count"),
            "V124PreflightRequest": ("manifest", "package_root", "baseline_database", "parent_candidate", "contract"),
            "V124ImportPreflightReport": ("batch_id", "status", "preflight_sha256", "manifest_sha256", "baseline_version", "baseline_release_digest", "baseline_question_count", "target_release_version", "parent_candidate_digest", "parent_batch_count", "before_count", "detected_count", "new_candidate_count", "duplicate_count", "rejected_count", "ambiguous_count", "approved_count", "projected_after_count", "readable_files", "unreadable_files", "unsupported_files", "teacher_notes_file_count", "common_errors_file_count", "ambiguous_splits", "missing_answers", "missing_explanations", "incomplete_enrichments", "missing_images", "orphan_images", "level_counts", "proposed_ids", "adaptations", "warnings", "blocking_errors"),
            "V124ImportPreflightResult": ("manifest", "effective_state", "candidates", "issues", "report"),
            "V124ImportApproval": ("batch_id", "preflight_sha256", "target_release_version", "parent_candidate_digest", "statement"),
            "V124ApprovedBatch": ("preflight_result", "package_root", "approval"),
            "V124CandidateContract": ("profile", "baseline_release_version", "baseline_question_count", "baseline_database_sha256", "baseline_database_size_bytes", "baseline_manifest_sha256", "baseline_manifest_size_bytes", "baseline_release_digest", "canonical_manifest_schema", "preflight_schema", "approval_schema", "candidate_manifest_schema", "candidate_database_schema", "candidate_identity_schema", "rollback_schema", "expected_user_version", "database_filename", "manifest_filename", "sha256s_filename", "rollback_filename", "authority_root", "image_root", "required_baseline_view", "required_candidate_tables", "required_candidate_views"),
            "V124CandidateBuildRequest": ("approved_batches", "output_dir", "contract"),
            "V124CandidateVerificationRequest": ("candidate_dir", "approved_batches", "contract"),
            "V124CandidateArtifacts": ("database", "manifest", "sha256sums", "rollback", "batch_authorities", "images", "state", "verification_report"),
        }
        for name, field_names in expected.items():
            carrier = getattr(self.module, name)
            self.assertEqual(tuple(field.name for field in fields(carrier)), field_names)
            self.assertTrue(getattr(carrier, "__dataclass_params__").frozen)
            self.assertTrue(all(field.default.__class__.__name__ == "_MISSING_TYPE" for field in fields(carrier)))

    def test_exact_annotations_and_signatures_cover_versioned_and_historical_models(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v124_models"), "V124CandidateContract", None), "V124 model contract missing")
        v124 = self.module
        historical_fields = {
            BatchImportManifest: ("schema_version", "batch_id", "project", "module", "chapter", "target_release_version", "candidate_records", "source_files", "answer_files", "image_files", "teacher_notes_files", "common_errors_files", "language_policy", "split_policy", "difficulty_policy", "tag_policy", "answer_policy", "explanation_policy"),
            ImportPreflightReport: ("batch_id", "status", "preflight_sha256", "manifest_sha256", "baseline_version", "before_count", "target_release_version", "detected_count", "new_candidate_count", "duplicate_count", "rejected_count", "ambiguous_count", "approved_count", "projected_after_count", "readable_files", "unreadable_files", "unsupported_files", "teacher_notes_file_count", "common_errors_file_count", "ambiguous_splits", "missing_answers", "missing_explanations", "incomplete_enrichments", "missing_images", "orphan_images", "level_counts", "proposed_ids", "adaptations", "warnings", "blocking_errors"),
            ImportApproval: ("batch_id", "preflight_sha256", "target_release_version", "statement"),
            V119WriterContract: ("profile", "candidate_manifest_schema", "candidate_database_schema", "expected_user_version", "database_filename", "manifest_filename", "sha256s_filename", "rollback_filename", "image_root", "required_baseline_tables", "required_candidate_tables", "required_candidate_views"),
            V119WriteRequest: ("preflight_result", "package_root", "approval", "output_dir", "contract"),
            V119VerificationRequest: ("candidate_dir", "preflight_result", "approval", "contract"),
            V119CandidateArtifacts: ("database", "manifest", "sha256sums", "rollback", "images", "verification_report"),
            V119PromotionContract: ("profile", "release_manifest_schema", "formal_database_schema", "promotion_identity_schema", "rollback_schema", "expected_user_version", "database_filename", "manifest_filename", "sha256s_filename", "rollback_filename", "image_root", "promoted_table", "promotion_table", "formal_view"),
            V119PromotionBuildRequest: ("candidate", "output_dir", "contract"),
            V119PromotionVerificationRequest: ("release_dir", "candidate", "contract"),
            ReleasePromotionApproval: ("release_version", "release_digest", "statement"),
            V119PublicationRequest: ("dry_run_dir", "candidate", "approval", "contract"),
            V119PromotionArtifacts: ("database", "manifest", "sha256sums", "rollback", "images", "release_digest", "verification_report"),
        }
        expected = {
            v124.V124BatchImportManifest: (str, str, str, str, str, str, tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], str, str, str, str, str, str),
            v124.V124AdaptedImportPackage: (Path, Path, v124.V124BatchImportManifest),
            v124.V124BatchLedgerEntry: (int, str, str, str, str, v124.V124ImportApproval, int, int, int),
            v124.V124EffectiveState: (ArtifactRef, str, tuple[v124.V124BatchLedgerEntry, ...], int, int),
            v124.V124PreflightRequest: (v124.V124BatchImportManifest, Path, ArtifactRef, v124.V124CandidateVerificationRequest | None, v124.V124CandidateContract),
            v124.V124ImportPreflightReport: (str, str, str, str, str, str, int, str, str, int, int, int, int, int, int, int, int, int, tuple[str, ...], tuple[str, ...], tuple[str, ...], int, int, tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[tuple[int, int], ...], tuple[str, ...], tuple[ImportAdaptation, ...], tuple[str, ...], tuple[str, ...]),
            v124.V124ImportPreflightResult: (v124.V124BatchImportManifest, v124.V124EffectiveState, tuple[ImportCandidate, ...], tuple[ImportIssue, ...], v124.V124ImportPreflightReport),
            v124.V124ImportApproval: (str, str, str, str, str),
            v124.V124ApprovedBatch: (v124.V124ImportPreflightResult, Path, v124.V124ImportApproval),
            v124.V124CandidateContract: (str, str, int, str, int, str, int, str, str, str, str, str, str, str, str, int, str, str, str, str, str, str, str, tuple[str, ...], tuple[str, ...]),
            v124.V124CandidateBuildRequest: (tuple[v124.V124ApprovedBatch, ...], Path, v124.V124CandidateContract),
            v124.V124CandidateVerificationRequest: (Path, tuple[v124.V124ApprovedBatch, ...], v124.V124CandidateContract),
            v124.V124CandidateArtifacts: (ArtifactRef, ArtifactRef, ArtifactRef, ArtifactRef, tuple[ArtifactRef, ...], tuple[ArtifactRef, ...], v124.V124EffectiveState, VerificationReport),
            BatchImportManifest: (str, str, str, str, str, str, tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], tuple[ImportFileEvidence, ...], str, str, str, str, str, str),
            ImportPreflightReport: (str, str, str, str, str, int, str, int, int, int, int, int, int, int, tuple[str, ...], tuple[str, ...], tuple[str, ...], int, int, tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[str, ...], tuple[tuple[int, int], ...], tuple[str, ...], tuple[ImportAdaptation, ...], tuple[str, ...], tuple[str, ...]),
            ImportApproval: (str, str, str, str),
            V119WriterContract: (str, str, str, int, str, str, str, str, str, tuple[str, ...], tuple[str, ...], tuple[str, ...]),
            V119WriteRequest: (ImportPreflightResult, Path, ImportApproval, Path, V119WriterContract),
            V119VerificationRequest: (Path, ImportPreflightResult, ImportApproval, V119WriterContract),
            V119CandidateArtifacts: (ArtifactRef, ArtifactRef, ArtifactRef, ArtifactRef, tuple[ArtifactRef, ...], VerificationReport),
            V119PromotionContract: (str, str, str, str, str, int, str, str, str, str, str, str, str, str),
            V119PromotionBuildRequest: (V119VerificationRequest, Path, V119PromotionContract),
            V119PromotionVerificationRequest: (Path, V119VerificationRequest, V119PromotionContract),
            ReleasePromotionApproval: (str, str, str),
            V119PublicationRequest: (Path, V119VerificationRequest, ReleasePromotionApproval, V119PromotionContract),
            V119PromotionArtifacts: (ArtifactRef, ArtifactRef, ArtifactRef, ArtifactRef, tuple[ArtifactRef, ...], str, VerificationReport),
        }
        for carrier, annotations in expected.items():
            with self.subTest(carrier=carrier.__name__):
                hints = get_type_hints(carrier)
                field_names = historical_fields.get(carrier, tuple(field.name for field in fields(carrier)))
                self.assertEqual(tuple(hints), field_names)
                self.assertEqual(tuple(hints.values()), annotations)
                signature = inspect.signature(carrier)
                self.assertEqual(tuple(signature.parameters), field_names)
                self.assertTrue(all(parameter.default is inspect.Parameter.empty for parameter in signature.parameters.values()))

    def test_manifest_canonicalizes_evidence_and_rejects_v124_envelope_violations(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v124_models"), "V124CandidateContract", None), "V124 model contract missing")
        manifest = self._manifest()
        self.assertIsInstance(manifest.candidate_records, tuple)
        for batch_id in (".batch", "batch/one", "batch\\one", "batch\n1", "批次", "a" * 129):
            values = list(self._manifest().__dict__.values())
            values[1] = batch_id
            with self.assertRaises(PipelineError):
                self.module.V124BatchImportManifest(*values)
        values = list(self._manifest().__dict__.values())
        values[7] = [self._evidence("candidates/a.json", "source")]
        with self.assertRaises(PipelineError):
            self.module.V124BatchImportManifest(*values)

    def test_adapted_package_and_preflight_request_require_exact_types_and_paths(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v124_models"), "V124CandidateContract", None), "V124 model contract missing")
        manifest = self._manifest()
        package = self.module.V124AdaptedImportPackage(Path("."), Path("manifest.json"), manifest)
        self.assertTrue(package.package_root.is_absolute())
        self.assertTrue(package.manifest_path.is_absolute())
        request = self.module.V124PreflightRequest(manifest, Path("."), self._artifact(), None, self._contract())
        self.assertTrue(request.package_root.is_absolute())
        with self.assertRaises(PipelineError):
            self.module.V124PreflightRequest(manifest, ".", self._artifact(), None, self._contract())

    def test_ledger_and_state_enforce_genesis_contiguity_and_count_closure(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v124_models"), "V124CandidateContract", None), "V124 model contract missing")
        approval = self._approval()
        entry = self.module.V124BatchLedgerEntry(1, approval.batch_id, GENESIS, SHA_B, SHA_C, approval, 1, 1, 678)
        state = self.module.V124EffectiveState(self._artifact(), SHA_A, [entry], 1, 678)
        self.assertEqual(state.batch_ledger, (entry,))
        for ordinal, count, projected in ((0, 1, 678), (1, True, 678), (1, 1, 677)):
            with self.assertRaises(PipelineError):
                self.module.V124BatchLedgerEntry(ordinal, approval.batch_id, GENESIS, SHA_B, SHA_C, approval, count, 1, projected)
        with self.assertRaises(PipelineError):
            self.module.V124EffectiveState(self._artifact(), GENESIS, [], 1, 678)
        with self.assertRaises(PipelineError):
            self.module.V124EffectiveState(self._artifact(), SHA_A, [entry], 0, 677)
        non_genesis = self.module.V124ImportApproval(
            approval.batch_id, SHA_B, "V1.24", SHA_A,
            f"USER APPROVED IMPORT BATCH {approval.batch_id} {SHA_B} V1.24 PARENT {SHA_A}",
        )
        with self.assertRaises(PipelineError):
            self.module.V124BatchLedgerEntry(1, approval.batch_id, SHA_A, SHA_B, SHA_C, non_genesis, 1, 1, 678)

    def test_report_closes_counts_and_fixed_v124_identity(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v124_models"), "V124CandidateContract", None), "V124 model contract missing")
        report = self._report()
        self.assertEqual(report.projected_after_count, 678)
        self.assertIsInstance(report.proposed_ids, tuple)
        values = list(report.__dict__.values())
        values[4] = "V1.18"
        with self.assertRaises(PipelineError):
            self.module.V124ImportPreflightReport(*values)
        values = list(report.__dict__.values())
        values[11] = 2
        with self.assertRaises(PipelineError):
            self.module.V124ImportPreflightReport(*values)
        values = list(report.__dict__.values())
        values[17] = 677
        with self.assertRaises(PipelineError):
            self.module.V124ImportPreflightReport(*values)

    def test_result_preserves_candidate_order_and_canonicalizes_issue_order(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v124_models"), "V124CandidateContract", None), "V124 model contract missing")
        manifest = self._manifest()
        first, second = self._candidate("z"), self._candidate("a")
        report = self._report(manifest)
        issue_z = ImportIssue("code-z", "warning", "z", "field", "evidence")
        issue_a = ImportIssue("code-a", "warning", "a", "field", "evidence")
        result = self.module.V124ImportPreflightResult(manifest, self._state(), [first, second], [issue_z, issue_a], report)
        self.assertEqual(result.candidates, (first, second))
        self.assertEqual(result.issues, (issue_a, issue_z))
        with self.assertRaises(PipelineError):
            self.module.V124ImportPreflightResult(manifest, self._state(), [first], ["not an issue"], report)

    def test_approval_is_parent_bound_and_uses_existing_approval_error(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v124_models"), "V124CandidateContract", None), "V124 model contract missing")
        approval = self._approval()
        self.assertEqual(approval.statement, f"USER APPROVED IMPORT BATCH {approval.batch_id} {SHA_B} V1.24 PARENT {GENESIS}")
        with self.assertRaises(ImportApprovalError):
            self.module.V124ImportApproval("batch 1", SHA_B, "V1.24", GENESIS, approval.statement)
        with self.assertRaises(ImportApprovalError):
            self.module.V124ImportApproval(approval.batch_id, SHA_B.upper(), "V1.24", GENESIS, approval.statement)
        with self.assertRaises(ImportApprovalError):
            self.module.V124ImportApproval(approval.batch_id, SHA_B, "V1.23", GENESIS, approval.statement)

    def test_approved_batch_binds_ready_result_to_exact_approval(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v124_models"), "V124CandidateContract", None), "V124 model contract missing")
        approved = self._approved_batch()
        self.assertTrue(approved.package_root.is_absolute())
        result = self._result()
        mismatched = self.module.V124ImportApproval("other", SHA_B, "V1.24", GENESIS, f"USER APPROVED IMPORT BATCH other {SHA_B} V1.24 PARENT {GENESIS}")
        with self.assertRaises(ImportApprovalError):
            self.module.V124ApprovedBatch(result, Path("."), mismatched)

    def test_contract_is_exact_and_rejects_bool_and_tuple_changes(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v124_models"), "V124CandidateContract", None), "V124 model contract missing")
        contract = self._contract()
        self.assertEqual(contract.required_candidate_tables, ("task14_v124_batch_ledger_v1", "task14_v124_candidates_v1", "task14_v124_images_v1", "task14_v124_taxonomy_v1"))
        values = list(contract.__dict__.values())
        values[15] = True
        with self.assertRaises(PipelineError):
            self.module.V124CandidateContract(*values)
        values = list(contract.__dict__.values())
        values[-1] = []
        with self.assertRaises(PipelineError):
            self.module.V124CandidateContract(*values)

    def test_build_and_verification_requests_require_a_nonempty_ordered_prefix(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v124_models"), "V124CandidateContract", None), "V124 model contract missing")
        approved = self._approved_batch()
        build = self.module.V124CandidateBuildRequest([approved], Path("."), self._contract())
        verify = self.module.V124CandidateVerificationRequest(Path("."), [approved], self._contract())
        self.assertEqual(build.approved_batches, (approved,))
        self.assertEqual(verify.approved_batches, (approved,))
        for request, path in ((self.module.V124CandidateBuildRequest, Path(".")), (self.module.V124CandidateVerificationRequest, Path("."))):
            with self.assertRaises(PipelineError):
                request([], path, self._contract())

    def test_candidate_artifacts_require_exact_kinds_and_stable_destination_order(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v124_models"), "V124CandidateContract", None), "V124 model contract missing")
        report = VerificationReport("PASS", ())
        state = self._state()
        database = ArtifactRef(Path("/tmp/db"), SHA_A, 1, "sqlite")
        manifest = ArtifactRef(Path("/tmp/manifest"), SHA_A, 1, "manifest")
        sums = ArtifactRef(Path("/tmp/sums"), SHA_A, 1, "sha256sums")
        rollback = ArtifactRef(Path("/tmp/rollback"), SHA_A, 1, "rollback")
        preflight = ArtifactRef(Path("/tmp/authority/1/preflight.json"), SHA_A, 1, "preflight")
        approval = ArtifactRef(Path("/tmp/authority/1/approval.json"), SHA_A, 1, "approval")
        image = ArtifactRef(Path("/tmp/images/a"), SHA_A, 1, "image")
        artifacts = self.module.V124CandidateArtifacts(database, manifest, sums, rollback, [approval, preflight], [image], state, report)
        self.assertEqual(artifacts.batch_authorities, (approval, preflight))
        with self.assertRaises(PipelineError):
            self.module.V124CandidateArtifacts(manifest, manifest, sums, rollback, [], [], state, report)
        for position, malformed in (
            (0, ArtifactRef(Path("/tmp/db"), "BAD", 1, "sqlite")),
            (1, ArtifactRef(Path("/tmp/manifest"), SHA_A, True, "manifest")),
            (4, [ArtifactRef(Path("/tmp/authority/1/preflight.json"), "BAD", 1, "preflight")]),
            (5, [ArtifactRef(Path("/tmp/images/a"), SHA_A, True, "image")]),
        ):
            values = [database, manifest, sums, rollback, [approval, preflight], [image], state, report]
            values[position] = malformed
            with self.subTest(position=position), self.assertRaises(PipelineError):
                self.module.V124CandidateArtifacts(*values)

    def test_historical_v119_contracts_remain_closed_to_v124(self) -> None:
        self.assertIsNotNone(getattr(importlib.import_module("joy_m2.ingest.v124_models"), "V124CandidateContract", None), "V124 model contract missing")
        self.assertEqual(BatchImportManifest.__dataclass_fields__["target_release_version"].type, "str")
        with self.assertRaises(PipelineError):
            BatchImportManifest(
                "task9-import-manifest-v1", "batch", "Joy M2 AI Database", "M2", "chapter", "V1.24",
                [], [], [], [], [], [], "preserve_source_and_store_reviewed_chinese_separately",
                "one_complete_question_per_record", "joy_level_1_5", "controlled_primary_type_and_tags",
                "preserve_source_answer_identity", "source_or_independently_verified_with_identity",
            )
        self.assertEqual(V119WriterContract.__dataclass_fields__["profile"].type, "str")
        self.assertEqual(V119PromotionContract.__dataclass_fields__["profile"].type, "str")
        self.assertNotIn("V1.24", repr(V119WriterContract))
        with self.assertRaises(PipelineError):
            V119WriterContract(
                "V1.24", "task13-v123-candidate-manifest-v1", "task13-v123-candidate-v1", 119,
                "Joy_M2_V1.23_candidate.sqlite3", "candidate_manifest.json", "SHA256SUMS",
                "rollback.json", "images/sha256", (), (), (),
            )
        with self.assertRaises(PipelineError):
            V119PromotionContract(
                "V1.24", "task13-v123-formal-manifest-v1", "task13-v123-formal-v1",
                "task13-v123-promotion-identity-v1", "task13-v123-formal-rollback-v1", 119,
                "Joy_M2_Complete_Question_DB_V1_19.sqlite3", "manifest.json", "SHA256SUMS.txt",
                "rollback.json", "images/sha256", "task9_promoted_questions_v1",
                "task9_promotion_v1", "formal_complete_questions_v123",
            )
        historical_report = ImportPreflightReport(
            "batch", "READY FOR USER IMPORT APPROVAL", SHA_A, SHA_B, "V1.18", 497,
            "V1.19", 0, 0, 0, 0, 0, 0, 497, (), (), (), 0, 0, (), (), (), (), (), (),
            (), (), (), (), (),
        )
        with self.assertRaises(PipelineError):
            replace(historical_report, target_release_version="V1.24")
        with self.assertRaises(PipelineError):
            V119WriteRequest(self._result(), Path("."), object(), Path("."), object())
        with self.assertRaises(PipelineError):
            V119PromotionBuildRequest(
                self.module.V124CandidateVerificationRequest(Path("."), [self._approved_batch()], self._contract()),
                Path("."), object(),
            )
