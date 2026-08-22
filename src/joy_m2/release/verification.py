"""Independent non-mutating Release artifact verification."""

from __future__ import annotations

import json
from pathlib import Path
import re
import zipfile

from ..errors import InputFormatError, InputMissingError, PipelineError
from ..models import ReleaseContract, VerificationCheck, VerificationReport
from .hashing import sha256_file


_DIGEST = re.compile(r"[0-9a-f]{64}")
_V117_BASELINE_V116_ZIP_SHA256 = (
    "5f73f541f5c2da5bf3e5540daf7dbfb40566a339eaee79ef3e25d8eabd0404ae"
)
_V117_FIELDS = (
    "approved_question_count",
    "baseline_v116_sqlite_sha256",
    "baseline_v116_zip_sha256",
    "release_model",
    "remaining_unmigrated_complete_questions",
    "task4_candidate_sha256",
)
_V118_FIELDS = (
    "baseline_v117_sqlite_sha256",
    "complete_question_count",
    "legacy_compatibility_retained",
    "task6_imported_question_count",
)


def _check(name: str, passed: bool, detail: str) -> VerificationCheck:
    return VerificationCheck(name=name, passed=passed, detail=detail)


def _load_manifest(root: Path, contract: ReleaseContract) -> tuple[Path, object]:
    manifest = root / contract.manifest_filename
    if not manifest.is_file():
        raise InputMissingError(f"release manifest does not exist: {manifest}")
    try:
        value = json.loads(manifest.read_text(encoding="utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise InputFormatError("release manifest is not valid UTF-8 JSON") from error
    return manifest, value


def _load_sums(path: Path) -> tuple[dict[str, str], bool]:
    if not path.is_file():
        return {}, False
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeError:
        return {}, False
    values: dict[str, str] = {}
    valid = bool(lines)
    for line in lines:
        if "  " not in line:
            valid = False
            continue
        digest, relative = line.split("  ", 1)
        relative_path = Path(relative)
        if (
            _DIGEST.fullmatch(digest) is None
            or not relative
            or relative_path.is_absolute()
            or ".." in relative_path.parts
            or relative in values
        ):
            valid = False
            continue
        values[relative_path.as_posix()] = digest
    if tuple(values) != tuple(sorted(values)):
        valid = False
    return values, valid


def _is_digest(value: object) -> bool:
    return type(value) is str and _DIGEST.fullmatch(value) is not None


def _manifest_schema_checks(
    manifest: dict[str, object],
    contract: ReleaseContract,
) -> tuple[VerificationCheck, ...]:
    release_status = manifest.get("release_status")
    required = set(contract.manifest_required_fields)
    if contract.profile == "V1.17":
        required.update(_V117_FIELDS)
    elif contract.profile == "V1.18":
        required.update(_V118_FIELDS)
    frozen_profile = contract.profile in {"V1.17", "V1.18"}
    if release_status == "formal" and frozen_profile:
        required.update(("approved_at", "approved_by"))

    required_fields_valid = all(field in manifest for field in required)
    common_types_valid = (
        type(manifest.get("artifact_sha256")) is dict
        and type(manifest.get("release_version")) is str
        and type(release_status) is str
        and type(manifest.get("schema_version")) is str
    )
    if release_status == "formal" and frozen_profile:
        common_types_valid = common_types_valid and (
            type(manifest.get("approved_at")) is str
            and bool(manifest.get("approved_at"))
            and type(manifest.get("approved_by")) is str
            and bool(manifest.get("approved_by"))
        )

    digest_fields: tuple[str, ...] = tuple(
        field
        for field in (
            "approval_sha256",
            "candidate_manifest_sha256",
            "baseline_v116_sqlite_sha256",
            "baseline_v116_zip_sha256",
            "task4_candidate_sha256",
            "baseline_v117_sqlite_sha256",
        )
        if field in manifest
    )
    digest_types_valid = all(type(manifest[field]) is str for field in digest_fields)
    digest_format_valid = all(_is_digest(manifest[field]) for field in digest_fields)

    profile_types_valid = True
    profile_fields_valid = True
    if contract.profile == "V1.17":
        profile_types_valid = (
            type(manifest.get("approved_question_count")) is int
            and type(manifest.get("remaining_unmigrated_complete_questions")) is int
            and type(manifest.get("release_model")) is str
        )
        profile_fields_valid = (
            manifest.get("approved_question_count") == 45
            and manifest.get("remaining_unmigrated_complete_questions") == 452
            and manifest.get("release_model") == "transitional-dual-layer"
            and manifest.get("baseline_v116_zip_sha256")
            == _V117_BASELINE_V116_ZIP_SHA256
            and not any(field in manifest for field in _V118_FIELDS)
        )
    elif contract.profile == "V1.18":
        profile_types_valid = (
            type(manifest.get("complete_question_count")) is int
            and type(manifest.get("task6_imported_question_count")) is int
            and type(manifest.get("legacy_compatibility_retained")) is bool
        )
        profile_fields_valid = (
            manifest.get("complete_question_count") == 497
            and manifest.get("task6_imported_question_count") == 452
            and manifest.get("legacy_compatibility_retained") is True
            and not any(field in manifest for field in _V117_FIELDS)
        )

    field_types_valid = (
        common_types_valid and profile_types_valid and digest_types_valid
    )
    approved_values_valid = (
        manifest.get("release_version") == contract.profile
        and type(release_status) is str
        and release_status in {"candidate", "formal"}
        and manifest.get("schema_version") == "complete-question-v1.0"
    )
    return (
        _check(
            "manifest_required_fields",
            required_fields_valid,
            "manifest must contain every contract and frozen-profile field",
        ),
        _check(
            "manifest_field_types",
            field_types_valid,
            "manifest scalar and container fields must use exact frozen types",
        ),
        _check(
            "manifest_digest_format",
            digest_format_valid,
            "manifest digest scalars must be lowercase SHA-256 values",
        ),
        _check(
            "manifest_profile_fields",
            approved_values_valid and profile_fields_valid,
            "manifest values and profile-specific fields must match the frozen profile",
        ),
    )


def _verify_zip(
    root: Path,
    path: Path,
    archive_root: str,
    expected_files: set[str],
) -> bool:
    try:
        with zipfile.ZipFile(path) as archive:
            infos = archive.infolist()
            expected_names = [
                f"{archive_root}/{name}" for name in sorted(expected_files)
            ]
            if [info.filename for info in infos] != expected_names:
                return False
            for info, relative in zip(infos, sorted(expected_files)):
                if (
                    info.date_time != (1980, 1, 1, 0, 0, 0)
                    or info.create_system != 3
                    or info.external_attr >> 16 != 0o100644
                    or info.compress_type != zipfile.ZIP_DEFLATED
                    or info.is_dir()
                    or archive.read(info) != (root / relative).read_bytes()
                ):
                    return False
    except (OSError, KeyError, zipfile.BadZipFile):
        return False
    return True


def verify_release(root: Path, contract: ReleaseContract) -> VerificationReport:
    """Verify manifest, sums, protected payload and required deterministic ZIP."""

    if not isinstance(root, Path) or type(contract) is not ReleaseContract:
        raise PipelineError("release verification requires a Path and ReleaseContract")
    root = root.resolve()
    manifest_path, manifest = _load_manifest(root, contract)
    if type(manifest) is not dict:
        return VerificationReport(
            status="FAIL",
            checks=(
                VerificationCheck(
                    "manifest_structure",
                    False,
                    "release manifest JSON payload must contain an object",
                ),
            ),
        )
    checks: list[VerificationCheck] = list(
        _manifest_schema_checks(manifest, contract)
    )
    release_status = manifest.get("release_status")
    candidate_archive = root / contract.candidate_zip_filename
    formal_archive = root / contract.formal_zip_filename
    archive_matches_status = (
        release_status == "candidate"
        and candidate_archive.is_file()
        and not formal_archive.exists()
    ) or (
        release_status == "formal"
        and formal_archive.is_file()
        and not candidate_archive.exists()
    )
    manifest_identity = (
        manifest.get("release_version") == contract.profile
        and manifest.get("schema_version") == "complete-question-v1.0"
        and archive_matches_status
    )
    checks.append(
        _check(
            "manifest_identity",
            manifest_identity,
            "manifest version, schema, status, and archive must match the contract",
        )
    )
    artifacts = manifest.get("artifact_sha256")
    artifacts_valid = type(artifacts) is dict and all(
        type(name) is str
        and bool(name)
        and not Path(name).is_absolute()
        and ".." not in Path(name).parts
        and type(digest) is str
        and _DIGEST.fullmatch(digest) is not None
        for name, digest in (artifacts.items() if type(artifacts) is dict else ())
    )
    checks.append(
        _check(
            "manifest_artifact_map",
            artifacts_valid,
            "artifact_sha256 must be a string-to-digest mapping",
        )
    )
    expected_hash_payload = (
        set(artifacts) | {contract.manifest_filename}
        if artifacts_valid
        else set()
    )

    sums_path = root / contract.sha256sums_filename
    sums, sums_valid = _load_sums(sums_path)
    checks.append(
        _check(
            "sha256sums_format",
            sums_valid,
            "SHA256SUMS must use sorted digest-two-space-relative-path lines",
        )
    )
    artifact_hash_closure = sums_valid and artifacts_valid and (
        set(sums) == expected_hash_payload
    )
    checks.append(
        _check(
            "artifact_hash_closure",
            artifact_hash_closure,
            "SHA256SUMS payload must exactly equal manifest artifacts plus manifest",
        )
    )
    sums_identity = sums_valid and all(
        (root / relative).is_file()
        and sha256_file(root / relative) == digest
        for relative, digest in sums.items()
    )
    checks.append(
        _check(
            "sha256sums_identity",
            sums_identity,
            "every sums entry must match exact file bytes",
        )
    )
    manifest_hash_identity = sums.get(contract.manifest_filename) == sha256_file(
        manifest_path
    )
    checks.append(
        _check(
            "manifest_in_hash_closure",
            manifest_hash_identity,
            "manifest must be protected by SHA256SUMS",
        )
    )
    artifact_identity = artifacts_valid and all(
        (root / name).is_file() and sha256_file(root / name) == digest
        for name, digest in artifacts.items()
    )
    checks.append(
        _check(
            "manifest_artifact_identity",
            artifact_identity,
            "manifest artifact digests must match exact file bytes",
        )
    )

    required_zip_name = (
        contract.candidate_zip_filename
        if release_status == "candidate"
        else contract.formal_zip_filename
        if release_status == "formal"
        else None
    )
    required_archive = required_zip_name is not None and (
        root / required_zip_name
    ).is_file()
    checks.append(
        _check(
            "required_archive",
            required_archive,
            "candidate/formal status requires exactly its declared ZIP",
        )
    )
    actual_files = {
        path.relative_to(root).as_posix()
        for path in root.rglob("*")
        if path.is_file()
    }
    expected_non_zip = expected_hash_payload | {contract.sha256sums_filename}
    expected_files = (
        expected_non_zip | {required_zip_name}
        if required_zip_name is not None
        else expected_non_zip
    )
    file_set_valid = artifact_hash_closure and actual_files == expected_files
    checks.append(
        _check(
            "declared_file_set",
            file_set_valid,
            "release files must exactly equal the manifest/sums closure and required ZIP",
        )
    )
    checks.append(
        _check(
            "deterministic_zip",
            required_archive
            and _verify_zip(
                root,
                root / required_zip_name,
                contract.archive_root,
                expected_non_zip,
            ),
            "ZIP contents and metadata must match the declared release files",
        )
    )
    return VerificationReport(
        status="PASS" if all(check.passed for check in checks) else "FAIL",
        checks=tuple(checks),
    )
