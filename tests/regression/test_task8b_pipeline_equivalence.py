from __future__ import annotations

import contextlib
from dataclasses import replace
import hashlib
import importlib
import json
from pathlib import Path
import sqlite3
import sys
import tempfile
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
LEGACY = ROOT / "legacy"
V117_ORACLE = LEGACY / "outputs/25757421d1d8/Task5_V1.17_正式入库"
V118_FROZEN = ROOT / "releases/V1.18"
V118_BASELINE = ROOT / "data/baselines/V1.18"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from joy_m2.release import build_candidate, verify_candidate
from joy_m2.audit.pipeline import audit_batch
from tests.integration.test_db_pipeline import (
    REQUIRED_TABLES,
    REQUIRED_VIEWS,
    V116_DATABASE,
    V117_DATABASE,
)
from tests.integration.test_release_pipeline import candidate_request


V117_CORE_NAMES = (
    "Joy_M2_Complete_Question_DB_V1_17.sqlite3",
    "Joy_M2_Complete_Questions_V1_17.csv",
    "complete_questions_45_approved_v1_17.json",
    "differentiation_application_taxonomy_v1_1.json",
    "Joy_M2_微分应用45题_知识文档_V1.17.md",
    "Joy_M2_V1.17_正式入库报告.md",
    "PROJECT_STATE.md",
)
V117_LEGACY_KEYS = {
    "Joy_M2_Complete_Question_DB_V1_17.sqlite3": "sqlite",
    "Joy_M2_Complete_Questions_V1_17.csv": "csv",
    "complete_questions_45_approved_v1_17.json": "approved_json",
    "differentiation_application_taxonomy_v1_1.json": "taxonomy",
    "Joy_M2_微分应用45题_知识文档_V1.17.md": "knowledge",
    "Joy_M2_V1.17_正式入库报告.md": "report",
    "PROJECT_STATE.md": "project_state",
}
V118_CORE_NAMES = (
    "Joy_M2_Complete_Question_DB_V1_18.sqlite3",
    "Joy_M2_Complete_Questions_V1_18.csv",
    "complete_questions_452_task6_audited.json",
    "task6_audit_report.json",
    "Joy_M2_完整题497题_知识文档_V1.18.md",
    "Joy_M2_V1.18_正式入库报告.md",
    "PROJECT_STATE.md",
)
V118_LEGACY_KEYS = {
    "Joy_M2_Complete_Question_DB_V1_18.sqlite3": "db",
    "Joy_M2_Complete_Questions_V1_18.csv": "csv",
    "complete_questions_452_task6_audited.json": "audit",
    "task6_audit_report.json": "audit_report",
    "Joy_M2_完整题497题_知识文档_V1.18.md": "knowledge",
    "Joy_M2_V1.18_正式入库报告.md": "report",
    "PROJECT_STATE.md": "state",
}
EXPECTED_CANDIDATE_FILES = {
    "V1.17": set(V117_CORE_NAMES)
    | {"task4_audit_report.json", "manifest.json", "SHA256SUMS.txt"},
    "V1.18": set(V118_CORE_NAMES) | {"manifest.json", "SHA256SUMS.txt"},
}
V117_HISTORICAL_ZIP_SHA256 = (
    "5f73f541f5c2da5bf3e5540daf7dbfb40566a339eaee79ef3e25d8eabd0404ae"
)
SQLITE_ATTRIBUTION = "deterministic SQLite hash attribution"
FROZEN_ARTIFACT_ATTRIBUTION = "frozen artifact byte-equivalence attribution"
KNOWN_FRESH_LEGACY_MISMATCHES = {
    "V1.17": {
        "Joy_M2_Complete_Question_DB_V1_17.sqlite3": SQLITE_ATTRIBUTION,
        "Joy_M2_V1.17_正式入库报告.md": FROZEN_ARTIFACT_ATTRIBUTION,
    },
    "V1.18": {
        "Joy_M2_Complete_Question_DB_V1_18.sqlite3": SQLITE_ATTRIBUTION,
        "Joy_M2_V1.18_正式入库报告.md": FROZEN_ARTIFACT_ATTRIBUTION,
    },
}
EXPECTED_COMPATIBILITY_OBJECTS = {
    "V1.17": {
        "identity": {
            "release_version": "V1.17",
            "schema_version": "complete-question-v1.0",
            "release_status": "candidate",
        },
        "release_version": "V1.17",
        "artifact_mapping": {
            "Joy_M2_Complete_Question_DB_V1_17.sqlite3": (
                "58f32e547c4ff0cdd2ae25a9368ea288cbaa70af52869b779d698233aee93fab"
            ),
            "Joy_M2_Complete_Questions_V1_17.csv": (
                "308728abb9936cd0feb84ac7e30922833b60565a2942656311aa9e23aed1e2ba"
            ),
            "complete_questions_45_approved_v1_17.json": (
                "f8d4ab5db3275308c570ad44c09f5c784267f26c38552193725c683f5fc0edbc"
            ),
            "differentiation_application_taxonomy_v1_1.json": (
                "6010077380a772bbf856b9b2ee4ccf970308113005079a06da8486ac0b2c7926"
            ),
            "Joy_M2_微分应用45题_知识文档_V1.17.md": (
                "b98cd00688cb5cfaf8b89a10f10e5cbdead085a1914e0c874ba6d9004a1a3ee2"
            ),
            "Joy_M2_V1.17_正式入库报告.md": (
                "cbe8ba91ea9dcca7501408a4bbf480a6c04ba845acf7c94a7d46766e3fddcb31"
            ),
            "PROJECT_STATE.md": (
                "9294622f3c436b8ebfe791f6ccc6f3415b658856896db0eaa14f17577bb805ba"
            ),
        },
        "protected_hashes": {
            "Joy_M2_Complete_Question_DB_V1_17.sqlite3": (
                "58f32e547c4ff0cdd2ae25a9368ea288cbaa70af52869b779d698233aee93fab"
            ),
            "Joy_M2_Complete_Questions_V1_17.csv": (
                "308728abb9936cd0feb84ac7e30922833b60565a2942656311aa9e23aed1e2ba"
            ),
            "complete_questions_45_approved_v1_17.json": (
                "f8d4ab5db3275308c570ad44c09f5c784267f26c38552193725c683f5fc0edbc"
            ),
            "differentiation_application_taxonomy_v1_1.json": (
                "6010077380a772bbf856b9b2ee4ccf970308113005079a06da8486ac0b2c7926"
            ),
            "Joy_M2_微分应用45题_知识文档_V1.17.md": (
                "b98cd00688cb5cfaf8b89a10f10e5cbdead085a1914e0c874ba6d9004a1a3ee2"
            ),
            "Joy_M2_V1.17_正式入库报告.md": (
                "cbe8ba91ea9dcca7501408a4bbf480a6c04ba845acf7c94a7d46766e3fddcb31"
            ),
            "PROJECT_STATE.md": (
                "9294622f3c436b8ebfe791f6ccc6f3415b658856896db0eaa14f17577bb805ba"
            ),
            "task4_audit_report.json": (
                "32a52db55abe9b27f363a3b1251f7ec03c98aa10e3563ffc07e0c7b0a7d3f2c3"
            ),
        },
        "historical_compatibility_scalars": {
            "baseline_v116_sqlite_sha256": (
                "d647244f54e9e54b25ec4885f16c47171c7521552876a5fa925a16d65d8c7714"
            ),
            "baseline_v116_zip_sha256": V117_HISTORICAL_ZIP_SHA256,
            "task4_candidate_sha256": (
                "5145b3da050d510cf6cf052a66cddf20ce2939ae3879618d3341f8399f48b97d"
            ),
        },
    },
    "V1.18": {
        "identity": {
            "release_version": "V1.18",
            "schema_version": "complete-question-v1.0",
            "release_status": "candidate",
        },
        "release_version": "V1.18",
        "artifact_mapping": {
            "Joy_M2_Complete_Question_DB_V1_18.sqlite3": (
                "fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7"
            ),
            "Joy_M2_Complete_Questions_V1_18.csv": (
                "94e4b8060f80c485b6cd4c20d0cd9bbe7c4b0939f289ad38762900f9bceec2c5"
            ),
            "complete_questions_452_task6_audited.json": (
                "8cfb90179a0d79db0af86612874536c334191a30a340c70e1bc269d8eae76c83"
            ),
            "task6_audit_report.json": (
                "e26fd867fb6293d44f59acaaa536c583a651822ae5162c3ea415e282d64f3a84"
            ),
            "Joy_M2_完整题497题_知识文档_V1.18.md": (
                "0117cc647bb27f1dcfc3cb6d3d40384e2cfa6cc8ad96a4eaf1848ebc245ecf7f"
            ),
            "Joy_M2_V1.18_正式入库报告.md": (
                "cabd7e4b5127bb8b999f8147458440901d491897376789e9c61e3ea4e5e6de0b"
            ),
            "PROJECT_STATE.md": (
                "a6ee879f5d432491cc5dd639abe485090d4cd63bc0ddc2d3376f503af0e63f09"
            ),
        },
        "protected_hashes": {
            "Joy_M2_Complete_Question_DB_V1_18.sqlite3": (
                "fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7"
            ),
            "Joy_M2_Complete_Questions_V1_18.csv": (
                "94e4b8060f80c485b6cd4c20d0cd9bbe7c4b0939f289ad38762900f9bceec2c5"
            ),
            "complete_questions_452_task6_audited.json": (
                "8cfb90179a0d79db0af86612874536c334191a30a340c70e1bc269d8eae76c83"
            ),
            "task6_audit_report.json": (
                "e26fd867fb6293d44f59acaaa536c583a651822ae5162c3ea415e282d64f3a84"
            ),
            "Joy_M2_完整题497题_知识文档_V1.18.md": (
                "0117cc647bb27f1dcfc3cb6d3d40384e2cfa6cc8ad96a4eaf1848ebc245ecf7f"
            ),
            "Joy_M2_V1.18_正式入库报告.md": (
                "cabd7e4b5127bb8b999f8147458440901d491897376789e9c61e3ea4e5e6de0b"
            ),
            "PROJECT_STATE.md": (
                "a6ee879f5d432491cc5dd639abe485090d4cd63bc0ddc2d3376f503af0e63f09"
            ),
        },
        "historical_compatibility_scalars": {
            "baseline_v117_sqlite_sha256": (
                "58f32e547c4ff0cdd2ae25a9368ea288cbaa70af52869b779d698233aee93fab"
            ),
        },
    },
}
LEGACY_COMPATIBILITY_TABLES = (
    "question_topics",
    "questions",
    "sources",
    "topics",
)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    if not root.exists():
        return {}
    return {
        path.relative_to(root).as_posix(): sha256(path)
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def logical_digest(database_path: Path, object_name: str) -> str:
    with sqlite3.connect(database_path) as database:
        columns = tuple(
            row[1]
            for row in database.execute(
                f'PRAGMA table_info("{object_name}")'
            ).fetchall()
        )
        rows = database.execute(f'SELECT * FROM "{object_name}"').fetchall()
    normalized_rows = sorted(
        json.dumps(row, ensure_ascii=False, separators=(",", ":"), default=str)
        for row in rows
    )
    payload = json.dumps(
        {"columns": columns, "rows": normalized_rows},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def database_objects(database_path: Path) -> tuple[set[str], set[str]]:
    with sqlite3.connect(database_path) as database:
        rows = database.execute(
            "SELECT type, name FROM sqlite_master WHERE type IN ('table', 'view')"
        ).fetchall()
    return (
        {name for kind, name in rows if kind == "table"},
        {name for kind, name in rows if kind == "view"},
    )


@contextlib.contextmanager
def legacy_import_path(path: Path):
    sys.path.insert(0, str(path))
    try:
        yield
    finally:
        sys.path.remove(str(path))


class Task8BPipelineEquivalenceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.frozen_release_before = tree_hashes(V118_FROZEN)
        cls.frozen_baseline_before = tree_hashes(V118_BASELINE)
        cls.temporary = tempfile.TemporaryDirectory()
        cls.root = Path(cls.temporary.name)

        with legacy_import_path(LEGACY / "task5_work"):
            cls.task5_builder = importlib.import_module("build_task5_release")
        with legacy_import_path(LEGACY):
            cls.task6_builder = importlib.import_module(
                "task6_work.build_task6_release"
            )

        cls.legacy_v117_root = cls.root / "legacy-v117"
        cls.legacy_v117 = cls.task5_builder.build_release(cls.legacy_v117_root)
        cls.legacy_v118_root = cls.root / "legacy-v118"
        cls.legacy_v118 = cls.task6_builder.build_release(
            V117_ORACLE,
            cls.legacy_v118_root,
            LEGACY,
        )

        cls.maintained: dict[str, tuple[object, object]] = {}
        cls.requests: dict[str, object] = {}
        cls.audit_results: dict[str, object] = {}
        cls.hash_mapping: dict[str, dict[str, dict[str, str]]] = {}
        cls.compatibility_objects: dict[str, dict[str, object]] = {}
        for profile in ("V1.17", "V1.18"):
            builds = []
            for label in ("first", "second"):
                maintained_root = cls.root / f"maintained-{profile}-{label}"
                maintained_root.mkdir()
                request = candidate_request(
                    maintained_root,
                    profile,
                    run_id="task8-equivalence",
                )
                if profile == "V1.18":
                    request = replace(
                        request,
                        export_contract=replace(
                            request.export_contract,
                            knowledge_markdown_filename=(
                                "Joy_M2_完整题497题_知识文档_V1.18.md"
                            ),
                        ),
                    )
                if label == "first":
                    cls.requests[profile] = request
                    cls.audit_results[profile] = audit_batch(request.audit_request)
                builds.append(build_candidate(request))
            cls.maintained[profile] = (builds[0], builds[1])

    @classmethod
    def tearDownClass(cls) -> None:
        cls.temporary.cleanup()

    def tearDown(self) -> None:
        self.assertEqual(tree_hashes(V118_FROZEN), self.frozen_release_before)
        self.assertEqual(tree_hashes(V118_BASELINE), self.frozen_baseline_before)

    def _assert_core_authority(
        self,
        profile: str,
        names: tuple[str, ...],
        legacy: dict[str, Path],
        legacy_keys: dict[str, str],
        approved_root: Path,
    ) -> None:
        first, second = self.maintained[profile]
        first_root = first.candidate_zip.path.parent
        second_root = second.candidate_zip.path.parent
        observed_mismatches: dict[str, str] = {}
        mapping: dict[str, dict[str, str]] = {}
        for name in names:
            approved_hash = sha256(approved_root / name)
            maintained_hash = sha256(first_root / name)
            fresh_legacy_hash = sha256(legacy[legacy_keys[name]])
            classification = "MATCH"
            if fresh_legacy_hash != maintained_hash:
                classification = KNOWN_FRESH_LEGACY_MISMATCHES[profile].get(
                    name,
                    "UNAPPROVED MISMATCH",
                )
                observed_mismatches[name] = classification
            mapping[name] = {
                "approved_frozen_or_reference": approved_hash,
                "maintained_generated": maintained_hash,
                "fresh_legacy_comparison": fresh_legacy_hash,
                "fresh_legacy_classification": classification,
            }
            with self.subTest(profile=profile, name=name):
                self.assertEqual(maintained_hash, approved_hash)
                self.assertEqual(sha256(second_root / name), maintained_hash)
        self.assertEqual(
            observed_mismatches,
            KNOWN_FRESH_LEGACY_MISMATCHES[profile],
        )
        self.hash_mapping[profile] = mapping

    def _assert_candidate_archive(self, profile: str) -> None:
        first, second = self.maintained[profile]
        contract = first.release_contract
        expected_relative = EXPECTED_CANDIDATE_FILES[profile]
        expected_names = [
            f"{contract.archive_root}/{name}"
            for name in sorted(expected_relative)
        ]
        with zipfile.ZipFile(first.candidate_zip.path) as archive:
            infos = archive.infolist()
        self.assertEqual([info.filename for info in infos], expected_names)
        self.assertEqual(
            expected_relative,
            {reference.path.name for reference in first.artifacts},
        )
        for info in infos:
            with self.subTest(profile=profile, archive_entry=info.filename):
                self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                self.assertEqual(info.create_system, 3)
                self.assertEqual(info.external_attr >> 16, 0o100644)
                self.assertEqual(info.compress_type, zipfile.ZIP_DEFLATED)
        self.assertEqual(first.candidate_zip.sha256, second.candidate_zip.sha256)
        self.assertEqual(
            first.candidate_zip.path.read_bytes(),
            second.candidate_zip.path.read_bytes(),
        )

    def test_v118_maintained_outputs_match_frozen_authority(self) -> None:
        first, second = self.maintained["V1.18"]
        first_root = first.candidate_zip.path.parent

        self.assertEqual(verify_candidate(first).status, "PASS")
        self._assert_core_authority(
            "V1.18",
            V118_CORE_NAMES,
            self.legacy_v118,
            V118_LEGACY_KEYS,
            V118_FROZEN,
        )

        manifest = json.loads(
            (first_root / first.release_contract.manifest_filename).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["release_version"], "V1.18")
        self.assertEqual(manifest["release_status"], "candidate")
        self.assertNotIn("baseline_v116_zip_sha256", manifest)
        self.assertEqual(
            set(manifest["artifact_sha256"]),
            set(V118_CORE_NAMES),
        )
        self.assertIs(first.release_contract, self.requests["V1.18"].release_contract)
        self.assertIsNone(self.requests["V1.18"].v117_release_decision)
        self.assertTrue(
            all(
                record.question.publication_evidence.record_status == "audit_passed"
                for record in self.audit_results["V1.18"].records
            )
        )
        with sqlite3.connect(first_root / V118_CORE_NAMES[0]) as database:
            statuses = database.execute(
                "SELECT DISTINCT record_status FROM complete_questions_v2 "
                "WHERE source_order > 45"
            ).fetchall()
        self.assertEqual(statuses, [("published",)])
        self._assert_candidate_archive("V1.18")

    def test_v117_maintained_outputs_match_protected_authority(self) -> None:
        first, second = self.maintained["V1.17"]
        first_root = first.candidate_zip.path.parent

        self.assertEqual(verify_candidate(first).status, "PASS")
        self._assert_core_authority(
            "V1.17",
            V117_CORE_NAMES,
            self.legacy_v117,
            V117_LEGACY_KEYS,
            V117_ORACLE,
        )

        manifest = json.loads(
            (first_root / first.release_contract.manifest_filename).read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(manifest["release_version"], "V1.17")
        self.assertEqual(
            manifest["baseline_v116_zip_sha256"],
            V117_HISTORICAL_ZIP_SHA256,
        )
        self.assertEqual(
            set(manifest["artifact_sha256"]),
            set(V117_CORE_NAMES) | {"task4_audit_report.json"},
        )
        self.assertIs(first.release_contract, self.requests["V1.17"].release_contract)
        self.assertIsNotNone(self.requests["V1.17"].v117_release_decision)
        self.assertFalse(
            hasattr(self.requests["V1.17"].audit_request, "baseline_release_archive")
        )
        audit_request = self.requests["V1.17"].audit_request
        self.assertNotEqual(audit_request.candidate_path.suffix, ".zip")
        self.assertNotEqual(audit_request.baseline_database.path.suffix, ".zip")
        self.assertNotEqual(audit_request.asset_root.suffix, ".zip")
        self._assert_candidate_archive("V1.17")

    def test_frozen_hashes_and_compatibility_objects_are_preserved(self) -> None:
        self._assert_core_authority(
            "V1.17",
            V117_CORE_NAMES,
            self.legacy_v117,
            V117_LEGACY_KEYS,
            V117_ORACLE,
        )
        self._assert_core_authority(
            "V1.18",
            V118_CORE_NAMES,
            self.legacy_v118,
            V118_LEGACY_KEYS,
            V118_FROZEN,
        )
        profile_baselines = {
            "V1.17": V116_DATABASE,
            "V1.18": V117_DATABASE,
        }
        for profile, baseline in profile_baselines.items():
            candidate = self.maintained[profile][0]
            database_path = candidate.candidate_zip.path.parent / (
                f"Joy_M2_Complete_Question_DB_{profile.replace('.', '_')}.sqlite3"
            )
            tables, views = database_objects(database_path)
            with self.subTest(profile=profile, objects="schema"):
                self.assertTrue(set(REQUIRED_TABLES) <= tables)
                self.assertTrue(set(REQUIRED_VIEWS) <= views)
            for table in LEGACY_COMPATIBILITY_TABLES:
                with self.subTest(profile=profile, table=table):
                    self.assertEqual(
                        logical_digest(database_path, table),
                        logical_digest(baseline, table),
                    )

            manifest_path = (
                candidate.candidate_zip.path.parent
                / candidate.release_contract.manifest_filename
            )
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            historical_scalars = {
                key: value
                for key, value in manifest.items()
                if key.startswith("baseline_") or key == "task4_candidate_sha256"
            }
            self.compatibility_objects[profile] = {
                "identity": {
                    "release_version": manifest["release_version"],
                    "schema_version": manifest["schema_version"],
                    "release_status": manifest["release_status"],
                },
                "release_version": profile,
                "artifact_mapping": {
                    name: values["maintained_generated"]
                    for name, values in self.hash_mapping[profile].items()
                },
                "protected_hashes": dict(manifest["artifact_sha256"]),
                "historical_compatibility_scalars": historical_scalars,
            }
            self.assertEqual(
                self.compatibility_objects[profile],
                EXPECTED_COMPATIBILITY_OBJECTS[profile],
            )
            self.assertEqual(manifest["release_version"], profile)
            self.assertEqual(manifest["release_status"], "candidate")
            self.assertEqual(
                self.compatibility_objects[profile]["artifact_mapping"],
                {
                    name: sha256(
                        (V117_ORACLE if profile == "V1.17" else V118_FROZEN)
                        / name
                    )
                    for name in (
                        V117_CORE_NAMES if profile == "V1.17" else V118_CORE_NAMES
                    )
                },
            )

        self.assertEqual(
            self.compatibility_objects["V1.17"][
                "historical_compatibility_scalars"
            ]["baseline_v116_zip_sha256"],
            V117_HISTORICAL_ZIP_SHA256,
        )
        self.assertNotIn(
            "baseline_v116_zip_sha256",
            self.compatibility_objects["V1.18"][
                "historical_compatibility_scalars"
            ],
        )

        self.assertEqual(tree_hashes(V118_FROZEN), self.frozen_release_before)
        self.assertEqual(tree_hashes(V118_BASELINE), self.frozen_baseline_before)


if __name__ == "__main__":
    unittest.main()
