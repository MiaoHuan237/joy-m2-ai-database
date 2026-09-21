from __future__ import annotations

import hashlib
import json
from pathlib import Path
import sys
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.errors import OutputConflictError, PipelineError
from joy_m2.ingest.hkdse_pdf_models import HkdsePdfTranscriptionApproval
from joy_m2.ingest.v122_manifest import load_v122_import_manifest
from tests.unit.test_hkdse_pdf_adapter import AdapterCase, adapter


class V122HkdseBridgeApiTests(unittest.TestCase):
    def test_v122_bridge_is_public(self):
        from joy_m2.ingest import hkdse_pdf_adapter
        import joy_m2.ingest as ingest

        self.assertTrue(
            hasattr(hkdse_pdf_adapter, "adapt_verified_hkdse_pdf_transcription_v122")
        )
        self.assertTrue(callable(getattr(ingest, "adapt_verified_hkdse_pdf_transcription_v122", None)))


class V122HkdseBridgeBehaviorTests(AdapterCase):
    def setUp(self):
        super().setUp()
        self.proposal = self.propose()
        approval = HkdsePdfTranscriptionApproval(
            self.proposal.batch_id,
            self.proposal.transcription_digest,
            "USER APPROVED PDF TRANSCRIPTION BATCH "
            f"{self.proposal.batch_id} {self.proposal.transcription_digest}",
        )
        self.verified = adapter(self).approve_hkdse_pdf_transcription(
            self.proposal, approval
        )
        self.output = self.root / "data" / "staging" / "canonical-v122"

    def _invoke(self, verified, output, config):
        try:
            return adapter(self).adapt_verified_hkdse_pdf_transcription_v122(verified, output, config)
        except NotImplementedError:
            self.fail("V1.22 verified bridge behavior missing")

    def bridge(self, output=None, config=None):
        return self._invoke(
            self.verified,
            output or self.output,
            config or self.config,
        )

    def test_verified_transcription_projects_exact_v122_package(self):
        package = self.bridge()
        self.assertEqual(
            package.manifest,
            load_v122_import_manifest(package.manifest_path),
        )
        self.assertEqual(package.manifest.schema_version, "task12-v122-import-manifest-v1")
        self.assertEqual(package.manifest.target_release_version, "V1.22")
        self.assertEqual(
            {
                path.relative_to(package.package_root).as_posix()
                for path in package.package_root.rglob("*")
                if path.is_file()
            },
            {
                "import_manifest.json",
                "records/candidates.json",
                "source/transcription.json",
                "source/source-map.json",
                "answers/official-ms.json",
            },
        )

    def test_candidate_source_and_answer_bytes_preserve_v121_bridge(self):
        v122 = self.bridge()
        v121 = adapter(self).adapt_verified_hkdse_pdf_transcription_v121(
            self.verified,
            self.root / "data" / "staging" / "canonical-v121",
            self.config,
        )
        for relative in (
            "records/candidates.json",
            "source/transcription.json",
            "source/source-map.json",
            "answers/official-ms.json",
        ):
            self.assertEqual(
                (v122.package_root / relative).read_bytes(),
                (v121.package_root / relative).read_bytes(),
                relative,
            )

    def test_unapproved_or_forged_input_is_rejected(self):
        module = adapter(self)
        for value in (self.proposal, object()):
            with self.subTest(kind=type(value).__name__):
                with self.assertRaises(TypeError):
                    self._invoke(
                        value, self.output, self.config
                    )

        forged = object.__new__(type(self.verified))
        object.__setattr__(forged, "proposal", self.proposal)
        object.__setattr__(forged, "records", self.verified.records)
        with self.assertRaises(PipelineError):
            self._invoke(
                forged, self.output, self.config
            )

    def test_equivalent_roots_produce_identical_package_bytes(self):
        first = self.bridge()
        second_root = self.root / "equivalent-root"
        for name in ("data/staging", "data/baselines", "releases"):
            (second_root / name).mkdir(parents=True, exist_ok=True)
        second = self.bridge(
            second_root / "data" / "staging" / "canonical-v122",
            PipelineConfig(second_root),
        )
        first_files = {
            path.relative_to(first.package_root).as_posix(): path.read_bytes()
            for path in first.package_root.rglob("*")
            if path.is_file()
        }
        second_files = {
            path.relative_to(second.package_root).as_posix(): path.read_bytes()
            for path in second.package_root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(first_files, second_files)

    def test_bridge_is_no_replace_and_preserves_formal_roots(self):
        frozen_before = tuple(self.config.baselines_root.rglob("*"))
        releases_before = tuple(self.config.releases_root.rglob("*"))
        package = self.bridge()
        before = {
            path.relative_to(package.package_root): path.read_bytes()
            for path in package.package_root.rglob("*")
            if path.is_file()
        }
        with self.assertRaises(OutputConflictError):
            self.bridge()
        after = {
            path.relative_to(package.package_root): path.read_bytes()
            for path in package.package_root.rglob("*")
            if path.is_file()
        }
        self.assertEqual(after, before)
        self.assertEqual(tuple(self.config.baselines_root.rglob("*")), frozen_before)
        self.assertEqual(tuple(self.config.releases_root.rglob("*")), releases_before)

    def test_publish_failure_cleans_owned_temporary_tree(self):
        module = adapter(self)
        with mock.patch.object(
            module,
            "atomic_rename_no_replace",
            side_effect=OSError("publish failed"),
        ):
            with self.assertRaises(OSError):
                self.bridge()
        self.assertFalse(self.output.exists())
        self.assertEqual(tuple(self.output.parent.glob(f".{self.output.name}-*")), ())

    def test_overlap_escape_and_symlink_outputs_are_rejected_without_writes(self):
        from joy_m2.errors import ConfigurationError
        alias = self.root / "data/staging/link"
        alias.symlink_to(self.root / "outside", target_is_directory=True)
        for target in (self.proposal.artifact_root / "nested", self.root / "outside/new", alias / "new"):
            with self.subTest(target=target), self.assertRaises((ConfigurationError, OutputConflictError)):
                self._invoke(self.verified, target, self.config)
            self.assertFalse(target.exists())

    def test_approval_digest_mutation_is_rejected(self):
        from dataclasses import replace
        bad = object.__new__(type(self.verified))
        for name, value in vars(self.verified).items():
            object.__setattr__(bad, name, value)
        approval = self.verified.approval
        altered = replace(approval, transcription_digest="0" * 64,
                          approval_text=f"USER APPROVED PDF TRANSCRIPTION BATCH {approval.batch_id} {'0' * 64}")
        object.__setattr__(bad, "approval", altered)
        with self.assertRaises(PipelineError):
            self._invoke(bad, self.output, self.config)
        self.assertFalse(self.output.exists())


if __name__ == "__main__":
    unittest.main()
