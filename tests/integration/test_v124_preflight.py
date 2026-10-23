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
from joy_m2.errors import PipelineError
from dataclasses import replace
from unittest import mock
from joy_m2.ingest.v124_manifest import load_v124_import_manifest
from joy_m2.ingest.v124_models import (
    V124CandidateContract,
    V124PreflightRequest,
)
from joy_m2.models import ArtifactRef
from tests.integration.test_v120_preflight import (
    REFERENCE_FRAGMENT,
    REFERENCE_NUMBER,
    REFERENCE_SECTION,
    REFERENCE_SOURCE_ID,
    _rewrite_record,
)


FIXTURE = ROOT / "tests/fixtures/task10a/v120-batch-a"
BASELINE = ROOT / "releases/V1.23/Joy_M2_Complete_Question_DB_V1_23.sqlite3"
BASELINE_SHA = "28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd"
BASELINE_SIZE = 10_928_128
BASELINE_MANIFEST_SHA = "54d192436e761c9bfe810510b77a902c5ae659bebdfbc4da8475aac271be8498"
BASELINE_RELEASE_DIGEST = "84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc"
GENESIS = "797ed06ca5833bac060c1603cada38a6f2aa9eb080a40d9dc892bba9a549773a"


def _contract() -> V124CandidateContract:
    return V124CandidateContract(
        "V1.24", "V1.23", 677, BASELINE_SHA, BASELINE_SIZE,
        BASELINE_MANIFEST_SHA, 6728, BASELINE_RELEASE_DIGEST,
        "task14-v124-import-manifest-v1", "task14-v124-preflight-v1",
        "task14-v124-import-approval-v1", "task14-v124-candidate-manifest-v1",
        "task14-v124-candidate-v1", "task14-v124-candidate-identity-v1",
        "task14-v124-rollback-v1", 124, "Joy_M2_V1.24_candidate.sqlite3",
        "candidate_manifest.json", "SHA256SUMS", "rollback.json",
        "authority/batches", "images/sha256", "formal_complete_questions_v123",
        (
            "task14_v124_batch_ledger_v1", "task14_v124_candidates_v1",
            "task14_v124_images_v1", "task14_v124_taxonomy_v1",
        ),
        ("task14_candidate_questions_v124",),
    )


def _fingerprint(root: Path) -> tuple[tuple[str, str, int], ...]:
    return tuple(
        (
            path.relative_to(root).as_posix(),
            hashlib.sha256(path.read_bytes()).hexdigest(),
            path.stat().st_size,
        )
        for path in sorted(root.rglob("*"))
        if path.is_file()
    )


def _make_package(parent: Path) -> Path:
    root = parent / "package"
    shutil.copytree(FIXTURE, root)
    manifest_path = root / "import_manifest.json"
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    payload["schema_version"] = "task14-v124-import-manifest-v1"
    payload["target_release_version"] = "V1.24"
    manifest_path.write_text(
        json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return root


def _request(package: Path, parent=None) -> V124PreflightRequest:
    return V124PreflightRequest(
        load_v124_import_manifest(package / "import_manifest.json"),
        package,
        ArtifactRef(BASELINE, BASELINE_SHA, BASELINE_SIZE, "sqlite"),
        parent,
        _contract(),
    )


class V124BaselineTests(unittest.TestCase):
    def reader(self, path):
        from joy_m2.ingest.v124_preflight import _formal_indexes
        try: return _formal_indexes(path)
        except NotImplementedError: self.fail('exact V123 formal baseline loader missing')

    def test_current_formal_677_not_inherited_candidate_double_count(self):
        before = _fingerprint(BASELINE.parent)
        indexes, primary, tags = self.reader(BASELINE)
        self.assertEqual(len(indexes['references']), 677)
        self.assertIn('向量', primary); self.assertIn('vector', tags)
        for qid in ('HKDSE-2023-M2-Q01', 'HKDSE-2025-M2-Q01'):
            self.assertIn(qid, indexes['references'])
        self.assertEqual(_fingerprint(BASELINE.parent), before)

    def test_reserved_uri_and_images_exact(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)/'資料 #% space'; root.mkdir()
            target = root/BASELINE.name
            shutil.copyfile(BASELINE, target)
            shutil.copyfile(BASELINE.parent/'manifest.json', root/'manifest.json')
            indexes, _, _ = self.reader(target)
            self.assertEqual(indexes, self.reader(BASELINE)[0])
            self.assertEqual(hashlib.sha256(target.read_bytes()).hexdigest(), BASELINE_SHA)

    def test_missing_path_no_creation_and_identity_tampering(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/'absent.sqlite3'
            with self.assertRaises(PipelineError): self.reader(path)
            self.assertFalse(path.exists())
            path.write_bytes(b'invalid database')
            with self.assertRaises(PipelineError): self.reader(path)

    def test_manifest_identity_is_required(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)/BASELINE.name
            shutil.copyfile(BASELINE, path)
            (path.parent/'manifest.json').write_text('{}')
            with self.assertRaises(PipelineError): self.reader(path)

    def test_inner_metadata_view_and_selectability_checks(self):
        from joy_m2.ingest import v124_preflight as p
        # Patch only expected byte identity of isolated corrupt copies, never a historical reader.
        self.assertTrue(hasattr(p, '_BASELINE_SHA'), 'baseline constants scaffold required')
        for sql in ["UPDATE release_metadata_v2 SET value='wrong' WHERE key='schema_version'",
                    'DROP VIEW formal_complete_questions_v123']:
            with self.subTest(sql=sql), tempfile.TemporaryDirectory() as folder:
                path = Path(folder)/BASELINE.name
                shutil.copyfile(BASELINE, path)
                shutil.copyfile(BASELINE.parent/'manifest.json', path.parent/'manifest.json')
                with sqlite3.connect(path) as con: con.execute(sql)
                with mock.patch.object(p, '_BASELINE_SHA', hashlib.sha256(path.read_bytes()).hexdigest()), \
                     mock.patch.object(p, '_BASELINE_SIZE', path.stat().st_size):
                    with self.assertRaises(PipelineError): self.reader(path)
