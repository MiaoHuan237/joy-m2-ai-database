from __future__ import annotations

import hashlib
import importlib
import json
from pathlib import Path
import sys
import tempfile
from types import MappingProxyType
import unittest
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


from joy_m2 import errors, models


V117_BASELINE_V116_ZIP_SHA256 = (
    "5f73f541f5c2da5bf3e5540daf7dbfb40566a339eaee79ef3e25d8eabd0404ae"
)


def require_callable(test: unittest.TestCase, module_name: str, name: str):
    try:
        module = importlib.import_module(module_name)
    except ModuleNotFoundError:
        module = None
    value = getattr(module, name, None) if module is not None else None
    test.assertTrue(callable(value), f"missing approved Release primitive: {module_name}.{name}")
    return value


def artifact(path: Path, kind: str) -> models.ArtifactRef:
    data = path.read_bytes()
    return models.ArtifactRef(
        path=path,
        sha256=hashlib.sha256(data).hexdigest(),
        size_bytes=len(data),
        kind=kind,
    )


def write_test_zip(
    path: Path,
    root: Path,
    files: tuple[Path, ...],
    archive_root: str,
    *,
    timestamp: tuple[int, int, int, int, int, int] = (1980, 1, 1, 0, 0, 0),
    permissions: int = 0o100644,
    create_system: int = 3,
    compression: int = zipfile.ZIP_DEFLATED,
) -> None:
    with zipfile.ZipFile(
        path,
        "w",
        compression=compression,
        compresslevel=9 if compression == zipfile.ZIP_DEFLATED else None,
    ) as archive:
        for source in sorted(files, key=lambda value: value.relative_to(root).as_posix()):
            relative = source.relative_to(root).as_posix()
            info = zipfile.ZipInfo(f"{archive_root}/{relative}", timestamp)
            info.create_system = create_system
            info.external_attr = permissions << 16
            info.compress_type = compression
            archive.writestr(
                info,
                source.read_bytes(),
                compress_type=compression,
                compresslevel=9 if compression == zipfile.ZIP_DEFLATED else None,
            )


def write_formal_fixture(
    root: Path,
    contract: models.ReleaseContract,
    *,
    manifest_overrides: dict[str, object] | None = None,
    manifest_remove: tuple[str, ...] = (),
    sums_extra: bool = False,
    zip_files: tuple[str, ...] | None = None,
    zip_timestamp: tuple[int, int, int, int, int, int] = (1980, 1, 1, 0, 0, 0),
    zip_permissions: int = 0o100644,
    zip_create_system: int = 3,
    zip_compression: int = zipfile.ZIP_DEFLATED,
) -> tuple[Path, Path, Path, Path]:
    payload = root / "payload.txt"
    payload.write_bytes(b"payload\n")
    manifest_value: dict[str, object] = {
        "approved_at": "2026-08-08T21:00:00+08:00",
        "approved_by": "Joy",
        "release_version": contract.profile,
        "release_status": "formal",
        "schema_version": "complete-question-v1.0",
        "artifact_sha256": {
            payload.name: hashlib.sha256(payload.read_bytes()).hexdigest()
        },
    }
    if contract.profile == "V1.17":
        manifest_value.update(
            {
                "approved_question_count": 45,
                "baseline_v116_sqlite_sha256": "d" * 64,
                "baseline_v116_zip_sha256": V117_BASELINE_V116_ZIP_SHA256,
                "release_model": "transitional-dual-layer",
                "remaining_unmigrated_complete_questions": 452,
                "task4_candidate_sha256": "c" * 64,
            }
        )
    elif contract.profile == "V1.18":
        manifest_value.update(
            {
                "baseline_v117_sqlite_sha256": "b" * 64,
                "complete_question_count": 497,
                "legacy_compatibility_retained": True,
                "task6_imported_question_count": 452,
            }
        )
    if manifest_overrides:
        manifest_value.update(manifest_overrides)
    for field in manifest_remove:
        manifest_value.pop(field, None)
    manifest = root / contract.manifest_filename
    manifest.write_text(
        json.dumps(manifest_value, sort_keys=True, indent=2) + "\n",
        encoding="utf-8",
    )
    sums = root / contract.sha256sums_filename
    entries = {
        manifest.name: hashlib.sha256(manifest.read_bytes()).hexdigest(),
        payload.name: hashlib.sha256(payload.read_bytes()).hexdigest(),
    }
    rogue = root / "rogue.txt"
    if sums_extra:
        rogue.write_bytes(b"rogue\n")
        entries[rogue.name] = hashlib.sha256(rogue.read_bytes()).hexdigest()
    sums.write_text(
        "".join(f"{digest}  {name}\n" for name, digest in sorted(entries.items())),
        encoding="utf-8",
    )
    formal_zip = root / contract.formal_zip_filename
    selected_names = zip_files or tuple(sorted((*entries, sums.name)))
    write_test_zip(
        formal_zip,
        root,
        tuple(root / name for name in selected_names),
        contract.archive_root,
        timestamp=zip_timestamp,
        permissions=zip_permissions,
        create_system=zip_create_system,
        compression=zip_compression,
    )
    return payload, manifest, sums, formal_zip


class ReleaseHashingTests(unittest.TestCase):
    def test_sha256_primitives_hash_exact_bytes_and_files(self) -> None:
        sha256_bytes = require_callable(self, "joy_m2.release.hashing", "sha256_bytes")
        sha256_file = require_callable(self, "joy_m2.release.hashing", "sha256_file")
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "数据.bin"
            path.write_bytes("Joy 数据\n".encode())
            expected = "49ef059a785a1e0ed3c22e9eaf2935c53b414f8da3f5910ca6cd1beb18c48a3a"
            self.assertEqual(sha256_bytes(path.read_bytes()), expected)
            self.assertEqual(sha256_file(path), expected)

    def test_manifest_is_sorted_unicode_indented_and_returns_bound_artifact(self) -> None:
        write_manifest = require_callable(self, "joy_m2.release.hashing", "write_manifest")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "manifest.json"
            payload = {"中": [2, 1], "a": "值"}
            ref = write_manifest(path, payload)
            expected = '{\n  "a": "值",\n  "中": [\n    2,\n    1\n  ]\n}\n'.encode()
            self.assertEqual(path.read_bytes(), expected)
            self.assertEqual(ref, artifact(path, "manifest"))
            proxy_path = root / "proxy.json"
            proxy_ref = write_manifest(proxy_path, MappingProxyType(payload))
            self.assertEqual(proxy_path.read_bytes(), expected)
            self.assertEqual(proxy_ref, artifact(proxy_path, "manifest"))
            with self.assertRaises(errors.PipelineError):
                write_manifest(root / "not-mapping.json", [("a", "值")])

    def test_sha256sums_is_sorted_relative_lf_and_rejects_unsafe_or_duplicate_paths(self) -> None:
        write_sums = require_callable(self, "joy_m2.release.hashing", "write_sha256sums")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "nested").mkdir()
            a = root / "a.txt"
            z = root / "nested" / "数据.json"
            a.write_bytes(b"a")
            z.write_bytes("中".encode())
            refs = (artifact(z, "json"), artifact(a, "text"))
            sums = root / "SHA256SUMS.txt"
            result = write_sums(sums, refs)
            expected = (
                f"{hashlib.sha256(b'a').hexdigest()}  a.txt\n"
                f"{hashlib.sha256('中'.encode()).hexdigest()}  nested/数据.json\n"
            ).encode()
            self.assertEqual(sums.read_bytes(), expected)
            self.assertEqual(result, artifact(sums, "sha256sums"))
            with self.assertRaises(errors.PipelineError):
                write_sums(root / "duplicate.txt", (refs[0], refs[0]))
            outside = root.parent / "outside.txt"
            outside.write_bytes(b"outside")
            self.addCleanup(outside.unlink, missing_ok=True)
            with self.assertRaises(errors.PipelineError):
                write_sums(root / "outside-sums.txt", (artifact(outside, "text"),))


class DeterministicPackagingTests(unittest.TestCase):
    def test_zip_bytes_and_metadata_are_fully_deterministic(self) -> None:
        write_zip = require_callable(
            self, "joy_m2.release.packaging", "write_deterministic_zip"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = root / "payload"
            payload.mkdir()
            (payload / "nested").mkdir()
            first = payload / "a.txt"
            second = payload / "nested" / "数据.json"
            first.write_bytes(b"a\n")
            second.write_bytes("中\n".encode())
            refs = (artifact(second, "json"), artifact(first, "text"))
            one = write_zip(root / "one.zip", payload, refs, "release-root")
            two = write_zip(root / "two.zip", payload, refs, "release-root")
            self.assertEqual(one.sha256, two.sha256)
            self.assertEqual((root / "one.zip").read_bytes(), (root / "two.zip").read_bytes())
            with zipfile.ZipFile(root / "one.zip") as archive:
                infos = archive.infolist()
                self.assertEqual(
                    [info.filename for info in infos],
                    ["release-root/a.txt", "release-root/nested/数据.json"],
                )
                for info in infos:
                    self.assertEqual(info.date_time, (1980, 1, 1, 0, 0, 0))
                    self.assertEqual(info.create_system, 3)
                    self.assertEqual(info.external_attr >> 16, 0o100644)
                    self.assertEqual(info.compress_type, zipfile.ZIP_DEFLATED)
                    self.assertFalse(info.is_dir())


class ReleaseVerificationPrimitiveTests(unittest.TestCase):
    def contract(self) -> models.ReleaseContract:
        return models.ReleaseContract(
            profile="V1.18",
            approval_filename="approval.json",
            manifest_filename="manifest.json",
            sha256sums_filename="SHA256SUMS.txt",
            candidate_zip_filename="candidate.zip",
            formal_zip_filename="formal.zip",
            archive_root="release-root",
            protected_artifact_kinds=("payload", "manifest"),
            manifest_required_fields=(
                "artifact_sha256",
                "baseline_v117_sqlite_sha256",
                "complete_question_count",
                "legacy_compatibility_retained",
                "release_status",
                "release_version",
                "schema_version",
                "task6_imported_question_count",
            ),
            hash_excluded_kinds=("sha256sums", "zip"),
            zip_excluded_kinds=("zip",),
        )

    def v117_contract(self) -> models.ReleaseContract:
        return models.ReleaseContract(
            profile="V1.17",
            approval_filename="approval.json",
            manifest_filename="manifest.json",
            sha256sums_filename="SHA256SUMS.txt",
            candidate_zip_filename="candidate.zip",
            formal_zip_filename="formal.zip",
            archive_root="release-root",
            protected_artifact_kinds=("payload", "manifest"),
            manifest_required_fields=(
                "approved_question_count",
                "artifact_sha256",
                "baseline_v116_sqlite_sha256",
                "baseline_v116_zip_sha256",
                "release_model",
                "release_status",
                "release_version",
                "remaining_unmigrated_complete_questions",
                "schema_version",
                "task4_candidate_sha256",
            ),
            hash_excluded_kinds=("sha256sums", "zip"),
            zip_excluded_kinds=("zip",),
        )

    def test_v118_missing_profile_field_returns_structured_fail(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_formal_fixture(
                root,
                self.contract(),
                manifest_remove=("baseline_v117_sqlite_sha256",),
            )

            report = verify_release(root, self.contract())

            self.assertEqual(report.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "manifest_required_fields" and not check.passed
                    for check in report.checks
                )
            )

    def test_v118_wrong_profile_field_type_returns_structured_fail(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_formal_fixture(
                root,
                self.contract(),
                manifest_overrides={"baseline_v117_sqlite_sha256": 123},
            )

            report = verify_release(root, self.contract())

            self.assertEqual(report.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "manifest_field_types" and not check.passed
                    for check in report.checks
                )
            )

    def test_v118_digest_fields_require_canonical_lowercase_sha256(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        invalid_values = (123, "0" * 63, "0" * 65, "g" * 64, "A" * 64)
        for value in invalid_values:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                write_formal_fixture(
                    root,
                    self.contract(),
                    manifest_overrides={"baseline_v117_sqlite_sha256": value},
                )

                report = verify_release(root, self.contract())

                self.assertEqual(report.status, "FAIL")
                self.assertTrue(
                    any(
                        check.name == "manifest_digest_format" and not check.passed
                        for check in report.checks
                    )
                )

    def test_v118_count_and_boolean_fields_use_exact_runtime_types(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        invalid_overrides = (
            {"complete_question_count": True},
            {"task6_imported_question_count": False},
            {"legacy_compatibility_retained": 1},
        )
        for overrides in invalid_overrides:
            with self.subTest(overrides=overrides), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                write_formal_fixture(
                    root,
                    self.contract(),
                    manifest_overrides=overrides,
                )

                report = verify_release(root, self.contract())

                self.assertEqual(report.status, "FAIL")
                self.assertTrue(
                    any(
                        check.name == "manifest_field_types" and not check.passed
                        for check in report.checks
                    )
                )

    def test_common_and_v117_string_fields_use_exact_runtime_types(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        cases = (
            (self.contract(), {"release_version": 118}),
            (self.contract(), {"release_status": True}),
            (self.contract(), {"schema_version": 100}),
            (self.contract(), {"approved_at": 123}),
            (self.contract(), {"approved_by": None}),
            (self.v117_contract(), {"release_model": 117}),
        )
        for contract, overrides in cases:
            with self.subTest(overrides=overrides), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                write_formal_fixture(
                    root,
                    contract,
                    manifest_overrides=overrides,
                )

                report = verify_release(root, contract)

                self.assertEqual(report.status, "FAIL")
                self.assertTrue(
                    any(
                        check.name == "manifest_field_types" and not check.passed
                        for check in report.checks
                    )
                )

    def test_formal_unhashable_release_status_returns_structured_fail(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        for release_status in ([], {}):
            with self.subTest(release_status=release_status), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                write_formal_fixture(
                    root,
                    self.contract(),
                    manifest_overrides={"release_status": release_status},
                )
                before = {path.name: path.read_bytes() for path in root.iterdir()}

                report = verify_release(root, self.contract())

                self.assertEqual(report.status, "FAIL")
                self.assertTrue(
                    any(
                        check.name == "manifest_field_types" and not check.passed
                        for check in report.checks
                    )
                )
                self.assertEqual(
                    {path.name: path.read_bytes() for path in root.iterdir()},
                    before,
                )

    def test_profile_scalar_values_match_the_frozen_manifests(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        cases = (
            (self.contract(), {"complete_question_count": 498}),
            (self.contract(), {"task6_imported_question_count": 451}),
            (self.contract(), {"legacy_compatibility_retained": False}),
            (self.v117_contract(), {"approved_question_count": 44}),
            (
                self.v117_contract(),
                {"remaining_unmigrated_complete_questions": 451},
            ),
            (self.v117_contract(), {"release_model": "other"}),
        )
        for contract, overrides in cases:
            with self.subTest(overrides=overrides), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                write_formal_fixture(
                    root,
                    contract,
                    manifest_overrides=overrides,
                )

                report = verify_release(root, contract)

                self.assertEqual(report.status, "FAIL")
                self.assertTrue(
                    any(
                        check.name == "manifest_profile_fields" and not check.passed
                        for check in report.checks
                    )
                )

    def test_v117_historical_fields_are_required_typed_and_canonical(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        cases = (
            ({}, ("baseline_v116_zip_sha256",), "manifest_required_fields"),
            ({"baseline_v116_zip_sha256": 123}, (), "manifest_field_types"),
            ({"baseline_v116_zip_sha256": "0" * 64}, (), "manifest_profile_fields"),
            ({"baseline_v116_sqlite_sha256": "g" * 64}, (), "manifest_digest_format"),
            ({"approved_question_count": True}, (), "manifest_field_types"),
        )
        for overrides, removed, failed_check in cases:
            with self.subTest(overrides=overrides, removed=removed), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                write_formal_fixture(
                    root,
                    self.v117_contract(),
                    manifest_overrides=overrides,
                    manifest_remove=removed,
                )

                report = verify_release(root, self.v117_contract())

                self.assertEqual(report.status, "FAIL")
                self.assertTrue(
                    any(
                        check.name == failed_check and not check.passed
                        for check in report.checks
                    )
                )

    def test_profile_specific_fields_do_not_cross_profiles(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        cases = (
            (
                self.contract(),
                {"baseline_v116_zip_sha256": V117_BASELINE_V116_ZIP_SHA256},
            ),
            (self.v117_contract(), {"baseline_v117_sqlite_sha256": "b" * 64}),
        )
        for contract, overrides in cases:
            with self.subTest(profile=contract.profile), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                write_formal_fixture(
                    root,
                    contract,
                    manifest_overrides=overrides,
                )

                report = verify_release(root, contract)

                self.assertEqual(report.status, "FAIL")
                self.assertTrue(
                    any(
                        check.name == "manifest_profile_fields" and not check.passed
                        for check in report.checks
                    )
                )

    def test_verifier_returns_structured_failures_without_mutating_artifacts(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload, manifest, sums, _ = write_formal_fixture(root, self.contract())
            before = {path.name: path.read_bytes() for path in root.iterdir()}
            self.assertEqual(verify_release(root, self.contract()).status, "PASS")
            payload.write_bytes(b"tampered\n")
            report = verify_release(root, self.contract())
            self.assertEqual(report.status, "FAIL")
            self.assertTrue(any(not check.passed for check in report.checks))
            self.assertEqual(payload.read_bytes(), b"tampered\n")
            self.assertEqual(manifest.read_bytes(), before["manifest.json"])
            self.assertEqual(sums.read_bytes(), before["SHA256SUMS.txt"])

    def test_formal_verifier_rejects_wrong_manifest_identity_and_missing_zip(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        cases = (
            {"release_version": "V9.99"},
            {"schema_version": "wrong-schema"},
            {"release_status": "candidate"},
        )
        for overrides in cases:
            with self.subTest(overrides=overrides), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                write_formal_fixture(
                    root,
                    self.contract(),
                    manifest_overrides=overrides,
                )
                before = {path.name: path.read_bytes() for path in root.iterdir()}
                report = verify_release(root, self.contract())
                self.assertEqual(report.status, "FAIL")
                self.assertTrue(
                    any(
                        check.name == "manifest_identity" and not check.passed
                        for check in report.checks
                    )
                )
                self.assertEqual(
                    {path.name: path.read_bytes() for path in root.iterdir()}, before
                )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, _, _, formal_zip = write_formal_fixture(root, self.contract())
            formal_zip.unlink()
            before = {path.name: path.read_bytes() for path in root.iterdir()}
            report = verify_release(root, self.contract())
            self.assertEqual(report.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "required_archive" and not check.passed
                    for check in report.checks
                )
            )
            self.assertEqual(
                {path.name: path.read_bytes() for path in root.iterdir()}, before
            )

    def test_formal_verifier_rejects_manifest_sums_and_zip_closure_mismatches(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_formal_fixture(root, self.contract(), sums_extra=True)
            report = verify_release(root, self.contract())
            self.assertEqual(report.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "artifact_hash_closure" and not check.passed
                    for check in report.checks
                )
            )

        for zip_files in (
            ("manifest.json", "SHA256SUMS.txt"),
            ("manifest.json", "payload.txt", "SHA256SUMS.txt", "rogue.txt"),
        ):
            with self.subTest(zip_files=zip_files), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                if "rogue.txt" in zip_files:
                    (root / "rogue.txt").write_bytes(b"rogue\n")
                write_formal_fixture(
                    root,
                    self.contract(),
                    zip_files=zip_files,
                )
                if "rogue.txt" in zip_files:
                    (root / "rogue.txt").unlink()
                report = verify_release(root, self.contract())
                self.assertEqual(report.status, "FAIL")
                self.assertTrue(
                    any(
                        check.name == "deterministic_zip" and not check.passed
                        for check in report.checks
                    )
                )

    def test_formal_verifier_rejects_zip_metadata_corruption(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_formal_fixture(
                root,
                self.contract(),
                zip_timestamp=(2026, 8, 21, 12, 0, 0),
            )
            report = verify_release(root, self.contract())
            self.assertEqual(report.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "deterministic_zip" and not check.passed
                    for check in report.checks
                )
            )

    def test_formal_verifier_rejects_wrong_zip_permissions(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_formal_fixture(
                root,
                self.contract(),
                zip_permissions=0o100600,
            )
            report = verify_release(root, self.contract())
            self.assertEqual(report.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "deterministic_zip" and not check.passed
                    for check in report.checks
                )
            )

    def test_formal_verifier_rejects_wrong_zip_create_system(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_formal_fixture(
                root,
                self.contract(),
                zip_create_system=0,
            )
            report = verify_release(root, self.contract())
            self.assertEqual(report.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "deterministic_zip" and not check.passed
                    for check in report.checks
                )
            )

    def test_formal_verifier_rejects_wrong_zip_compression_method(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            write_formal_fixture(
                root,
                self.contract(),
                zip_compression=zipfile.ZIP_STORED,
            )
            report = verify_release(root, self.contract())
            self.assertEqual(report.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "deterministic_zip" and not check.passed
                    for check in report.checks
                )
            )

    def test_each_protected_artifact_corruption_and_sums_omission_is_reported(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        cases = (
            ("questions.csv", "csv", b"id\r\n1\r\n", b"id\r\n2\r\n"),
            ("knowledge.md", "markdown", b"# Questions\n", b"Questions\n"),
            ("audit.json", "json", b'{"status":"passed"}\n', b"{broken\n"),
        )
        for filename, kind, original, corrupted in cases:
            with self.subTest(filename=filename), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                payload = root / filename
                payload.write_bytes(original)
                manifest = root / "manifest.json"
                manifest.write_text(
                    json.dumps(
                        {
                            "release_version": "V1.18",
                            "release_status": "formal",
                            "schema_version": "complete-question-v1.0",
                            "artifact_sha256": {
                                filename: hashlib.sha256(original).hexdigest()
                            },
                        },
                        sort_keys=True,
                        indent=2,
                    )
                    + "\n",
                    encoding="utf-8",
                )
                sums = root / "SHA256SUMS.txt"
                sums.write_text(
                    f"{hashlib.sha256(manifest.read_bytes()).hexdigest()}  manifest.json\n"
                    f"{hashlib.sha256(original).hexdigest()}  {filename}\n",
                    encoding="utf-8",
                )
                contract = models.ReleaseContract(
                    profile="V1.18",
                    approval_filename="approval.json",
                    manifest_filename="manifest.json",
                    sha256sums_filename="SHA256SUMS.txt",
                    candidate_zip_filename="candidate.zip",
                    formal_zip_filename="formal.zip",
                    archive_root="release-root",
                    protected_artifact_kinds=(kind, "manifest"),
                    manifest_required_fields=self.contract().manifest_required_fields,
                    hash_excluded_kinds=("sha256sums", "zip"),
                    zip_excluded_kinds=("zip",),
                )
                payload.write_bytes(corrupted)
                before = {path.name: path.read_bytes() for path in root.iterdir()}
                report = verify_release(root, contract)
                self.assertEqual(report.status, "FAIL")
                self.assertTrue(any(not check.passed for check in report.checks))
                self.assertEqual(
                    {path.name: path.read_bytes() for path in root.iterdir()}, before
                )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            payload = root / "payload.txt"
            payload.write_bytes(b"payload\n")
            manifest = root / "manifest.json"
            manifest.write_text(
                json.dumps(
                    {
                        "release_version": "V1.18",
                        "release_status": "formal",
                        "schema_version": "complete-question-v1.0",
                        "artifact_sha256": {
                            payload.name: hashlib.sha256(payload.read_bytes()).hexdigest()
                        },
                    },
                    sort_keys=True,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            sums = root / "SHA256SUMS.txt"
            sums.write_text(
                f"{hashlib.sha256(manifest.read_bytes()).hexdigest()}  manifest.json\n",
                encoding="utf-8",
            )
            before = {path.name: path.read_bytes() for path in root.iterdir()}
            report = verify_release(root, self.contract())
            self.assertEqual(report.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "declared_file_set" and not check.passed
                    for check in report.checks
                )
            )
            self.assertEqual(
                {path.name: path.read_bytes() for path in root.iterdir()}, before
            )

    def test_missing_or_malformed_manifest_uses_input_error_boundary(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with self.assertRaises(errors.InputMissingError):
                verify_release(root, self.contract())
            (root / "manifest.json").write_text("{", encoding="utf-8")
            with self.assertRaises(errors.InputFormatError):
                verify_release(root, self.contract())

    def test_parsed_manifest_with_wrong_top_level_returns_structured_fail(self) -> None:
        verify_release = require_callable(
            self, "joy_m2.release.verification", "verify_release"
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            _, manifest, sums, _ = write_formal_fixture(root, self.contract())
            manifest.write_text("[]\n", encoding="utf-8")
            payload = root / "payload.txt"
            sums.write_text(
                "".join(
                    (
                        f"{hashlib.sha256(manifest.read_bytes()).hexdigest()}  manifest.json\n",
                        f"{hashlib.sha256(payload.read_bytes()).hexdigest()}  payload.txt\n",
                    )
                ),
                encoding="utf-8",
            )

            report = verify_release(root, self.contract())

            self.assertEqual(report.status, "FAIL")
            self.assertTrue(
                any(
                    check.name == "manifest_structure" and not check.passed
                    for check in report.checks
                )
            )


if __name__ == "__main__":
    unittest.main()
