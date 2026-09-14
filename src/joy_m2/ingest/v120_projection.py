"""Private V1.20 target-projection boundary."""

import json
import errno
from pathlib import Path
import shutil
import tempfile

from .adapter import _canonical_json, _file_evidence, _source_map_payload
from .adapter_models import MmdAdapterManifest, MmdSelection
from .mmd_parser import _SourceDocument, _SourceMember, _SourceQuestion
from .v120_models import V120AdaptedImportPackage, V120BatchImportManifest
from .writer_profiles import atomic_rename_no_replace
from joy_m2.errors import OutputConflictError


def _manifest_payload(manifest: V120BatchImportManifest) -> dict[str, object]:
    def evidence(values: tuple) -> list[dict[str, object]]:
        return [
            {
                "relative_path": item.relative_path,
                "sha256": item.sha256,
                "size_bytes": item.size_bytes,
                "kind": item.kind,
            }
            for item in values
        ]

    return {
        "schema_version": manifest.schema_version,
        "batch_id": manifest.batch_id,
        "project": manifest.project,
        "module": manifest.module,
        "chapter": manifest.chapter,
        "target_release_version": manifest.target_release_version,
        "candidate_records": evidence(manifest.candidate_records),
        "source_files": evidence(manifest.source_files),
        "answer_files": evidence(manifest.answer_files),
        "image_files": evidence(manifest.image_files),
        "teacher_notes_files": evidence(manifest.teacher_notes_files),
        "common_errors_files": evidence(manifest.common_errors_files),
        "language_policy": manifest.language_policy,
        "split_policy": manifest.split_policy,
        "difficulty_policy": manifest.difficulty_policy,
        "tag_policy": manifest.tag_policy,
        "answer_policy": manifest.answer_policy,
        "explanation_policy": manifest.explanation_policy,
    }


def _project_v120_package(
    output_dir: Path,
    manifest: MmdAdapterManifest,
    document: _SourceDocument,
    bindings: tuple[tuple[MmdSelection, _SourceQuestion], ...],
    candidates: tuple[dict[str, object], ...],
    primary: _SourceMember,
    answer: _SourceMember | None,
    image_bytes: dict[str, bytes],
) -> V120AdaptedImportPackage:
    candidates_bytes = (_canonical_json(list(candidates)) + "\n").encode("utf-8")
    source_map_bytes = _canonical_json(
        _source_map_payload(manifest, document, bindings, answer, image_bytes)
    ).encode("utf-8")
    selected_images = tuple(
        dict.fromkeys(
            image
            for selection, _question in bindings
            for image in selection.expected_image_members
            if image in image_bytes
        )
    )
    answer_bytes = answer.content if answer is not None else None
    batch_manifest = V120BatchImportManifest(
        schema_version="task10-v120-import-manifest-v1",
        batch_id=manifest.batch_id,
        project="Joy M2 AI Database",
        module="M2",
        chapter=manifest.chapter,
        target_release_version="V1.20",
        candidate_records=(
            _file_evidence("records/candidates.json", candidates_bytes, "candidate_json"),
        ),
        source_files=(
            _file_evidence("source/original.mmd.txt", primary.content, "source"),
            _file_evidence("source/source-map.json", source_map_bytes, "source"),
        ),
        answer_files=(
            (_file_evidence("answers/answer.mmd.txt", answer_bytes, "answer"),)
            if answer_bytes is not None
            else ()
        ),
        image_files=tuple(
            _file_evidence(path, image_bytes[path], "image") for path in selected_images
        ),
        teacher_notes_files=(),
        common_errors_files=(),
        language_policy="preserve_source_and_store_reviewed_chinese_separately",
        split_policy="one_complete_question_per_record",
        difficulty_policy="joy_level_1_5",
        tag_policy="controlled_primary_type_and_tags",
        answer_policy="preserve_source_answer_identity",
        explanation_policy="source_or_independently_verified_with_identity",
    )
    manifest_bytes = (
        json.dumps(
            _manifest_payload(batch_manifest),
            ensure_ascii=False,
            separators=(",", ":"),
            allow_nan=False,
        )
        + "\n"
    ).encode("utf-8")
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    temporary_root = Path(
        tempfile.mkdtemp(prefix=f".{output_dir.name}-", dir=output_dir.parent)
    )
    try:
        files: list[tuple[str, bytes]] = [
            ("records/candidates.json", candidates_bytes),
            ("source/original.mmd.txt", primary.content),
            ("source/source-map.json", source_map_bytes),
        ]
        if answer_bytes is not None:
            files.append(("answers/answer.mmd.txt", answer_bytes))
        files.extend((path, image_bytes[path]) for path in selected_images)
        files.append(("import_manifest.json", manifest_bytes))
        for relative_path, content in files:
            target = temporary_root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        package = V120AdaptedImportPackage(
            output_dir,
            output_dir / "import_manifest.json",
            batch_manifest,
        )
        try:
            atomic_rename_no_replace(temporary_root, output_dir)
        except OSError as exc:
            if exc.errno not in (errno.EEXIST, errno.ENOTEMPTY):
                raise
            raise OutputConflictError("output path already exists") from exc
        return package
    finally:
        if temporary_root.exists():
            shutil.rmtree(temporary_root)
