from dataclasses import fields, replace

import hashlib

import json

from pathlib import Path

import sqlite3

import unicodedata

from joy_m2.config import PipelineConfig

from joy_m2.errors import PipelineError

from joy_m2.ingest.models import (
    ImportAdaptation,
    ImportCandidate,
    ImportFileEvidence,
    ImportIssue,
)

from joy_m2.models import ArtifactRef, VerificationReport

from .v124_models import (
    V124BatchLedgerEntry,
    V124BatchImportManifest,
    V124CandidateContract,
    V124CandidateVerificationRequest,
    V124EffectiveState,
    V124ImportPreflightReport,
    V124ImportPreflightResult,
    V124PreflightRequest,
)

from .v124_writer_profiles import _genesis_digest

from .v124_verification import verify_v124_candidate

_GENESIS = "797ed06ca5833bac060c1603cada38a6f2aa9eb080a40d9dc892bba9a549773a"

_BASELINE_SHA = "28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd"

_BASELINE_SIZE = 10_928_128

_BASELINE_MANIFEST_SHA = "54d192436e761c9bfe810510b77a902c5ae659bebdfbc4da8475aac271be8498"

_BASELINE_MANIFEST_SIZE = 6_728

_BASELINE_RELEASE_DIGEST = "84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc"

def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()

def _normalize(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value).replace("\r\n", "\n").replace("\r", "\n")
    lines: list[str] = []
    for line in normalized.split("\n"):
        stripped = line.strip(" \t\v\f")
        parts: list[str] = []
        start = 0
        for index, character in enumerate(stripped):
            if character in " \t\v\f":
                if start != index:
                    parts.append(stripped[start:index])
                start = index + 1
        if start != len(stripped):
            parts.append(stripped[start:])
        lines.append(" ".join(parts))
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)

def _parse_array(value: object, name: str) -> tuple[object, ...]:
    if value is None:
        return ()
    if type(value) is not str:
        raise PipelineError(f"formal {name} is invalid")
    try:
        decoded = json.loads(value)
    except json.JSONDecodeError as exc:
        raise PipelineError(f"formal {name} is invalid") from exc
    if type(decoded) is not list:
        raise PipelineError(f"formal {name} must be an array")
    return tuple(decoded)

def _formal_indexes(path: Path) -> tuple[dict[str, object], frozenset[str], frozenset[str]]:
    try:
        data = path.read_bytes()
        manifest = (path.parent / 'manifest.json').read_bytes()
    except OSError as exc:
        raise PipelineError("baseline database cannot be read") from exc
    if len(manifest) != _BASELINE_MANIFEST_SIZE or _sha(manifest) != _BASELINE_MANIFEST_SHA:
        raise PipelineError('baseline manifest does not match V1.23')
    if len(data) != _BASELINE_SIZE or _sha(data) != _BASELINE_SHA:
        raise PipelineError("baseline database bytes do not match V1.23")
    connection: sqlite3.Connection | None = None
    try:
        connection = sqlite3.connect(f"{path.resolve(strict=True).as_uri()}?mode=ro&immutable=1", uri=True)
        connection.execute("PRAGMA query_only=ON")
        if connection.execute("PRAGMA integrity_check").fetchone() != ("ok",):
            raise PipelineError("baseline integrity check failed")
        if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
            raise PipelineError("baseline foreign-key check failed")
        metadata = dict(connection.execute(
            "SELECT key,value FROM release_metadata_v2 WHERE key IN ('release_version','schema_version')"
        ))
        if metadata != {"release_version": "V1.23", "schema_version": "task13-v123-formal-v1"}:
            raise PipelineError("baseline metadata does not match V1.23")
        rows = connection.execute(
            "SELECT formal_order,question_id,source_id,source_question_number,source_section,"
            "source_fragment_hash,normalized_text_sha256,question_text_original,"
            "source_image_paths_json,source_image_sha256s_json,source_image_roles_json,"
            "primary_type,tags_json,record_status,selectable FROM formal_complete_questions_v123 ORDER BY formal_order"
        ).fetchall()
        if len(rows) != 677 or tuple(row[0] for row in rows) != tuple(range(1, 678)):
            raise PipelineError("formal V1.23 view must contain exact rows 1..677")
        if any(row[13] != "published" or row[14] != 1 for row in rows):
            raise PipelineError("formal V1.23 rows must be published/selectable")
        references: dict[str, dict[str, object]] = {}
        locator_index: dict[object, list[str]] = {}
        fragment_index: dict[object, list[str]] = {}
        normalized_index: dict[object, list[str]] = {}
        image_binding_index: dict[object, list[str]] = {}
        image_identity_index: dict[object, list[str]] = {}
        primary_types: set[str] = set()
        tags: set[str] = set()
        for row in rows:
            paths = _parse_array(row[8], "image paths")
            digests = _parse_array(row[9], "image digests")
            roles = _parse_array(row[10], "image roles")
            if all(type(item) is dict for item in paths):
                try:
                    images = tuple(
                        (item["path"], item["role"], item["sha256"])
                        for item in paths
                        if set(item) == {"path", "role", "sha256"}
                    )
                except (KeyError, TypeError) as exc:
                    raise PipelineError("formal image identity is invalid") from exc
                if len(images) != len(paths):
                    raise PipelineError("formal image identity is invalid")
            elif all(type(item) is str for item in paths):
                images = tuple(zip(paths, roles, digests, strict=True)) if digests or roles else tuple(
                    (item, None, None) for item in paths
                )
            else:
                raise PipelineError("formal image identity is invalid")
            reference = {
                "question_id": row[1], "locator": (row[2], row[3], row[4]),
                "fragment": row[5], "normalized": row[6] or _sha(_normalize(row[7]).encode("utf-8")),
                "images": images, "baseline": True,
            }
            references[row[1]] = reference
            locator_index.setdefault(reference["locator"], []).append(row[1])
            fragment_index.setdefault(reference["fragment"], []).append(row[1])
            normalized_index.setdefault(reference["normalized"], []).append(row[1])
            for image_path, role, digest in images:
                if role is None or digest is None:
                    continue
                image_binding_index.setdefault((image_path, role), []).append(row[1])
                image_identity_index.setdefault((image_path, role, digest), []).append(row[1])
            primary_types.add(row[11])
            tags.update(_parse_array(row[12], "tags"))
        if len(references) != 677:
            raise PipelineError("formal V1.23 question IDs must be unique")
        indexes = {
            "references": references,
            "question_id": {question_id: (question_id,) for question_id in references},
            "source_locator": {
                key: tuple(sorted(values)) for key, values in locator_index.items()
            },
            "source_fragment_sha256": {
                key: tuple(sorted(values)) for key, values in fragment_index.items()
            },
            "normalized_text_sha256": {
                key: tuple(sorted(values)) for key, values in normalized_index.items()
            },
            "image_binding": {
                key: tuple(sorted(values)) for key, values in image_binding_index.items()
            },
            "image_identity": {
                key: tuple(sorted(values)) for key, values in image_identity_index.items()
            },
        }
        return indexes, frozenset(primary_types), frozenset(tags)
    except PipelineError:
        raise
    except (OSError, sqlite3.Error, ValueError, TypeError) as exc:
        raise PipelineError("baseline database cannot be validated read-only") from exc
    finally:
        if connection is not None:
            connection.close()


def preflight_v124_import(request: V124PreflightRequest, config: PipelineConfig) -> V124ImportPreflightResult:
    raise NotImplementedError('genesis preflight pending')
