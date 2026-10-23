"""Explicit chapter 12 dual-package source profile; no real writer."""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import ExitStack
import hashlib
import io
from pathlib import Path, PurePosixPath
import re
from typing import TYPE_CHECKING
import zipfile
import zlib

from joy_m2.config import PipelineConfig
from joy_m2.errors import PipelineError
from joy_m2.ingest.source_mapping import SourceMappingApproval
from joy_m2.ingest import archive
from joy_m2.ingest.adapter_models import MmdAdapterBlockedError
from joy_m2.ingest.source_mapping import _read_input

if TYPE_CHECKING:
    from joy_m2.ingest.v124_models import V124AdaptedImportPackage


@dataclass(frozen=True)
class VectorCh12Proposal:
    proposal_root: Path
    mapping_path: Path
    review_path: Path
    source_id: str
    input_binding_sha256: str
    mapping_sha256: str
    candidate_count: int

    def __post_init__(self):
        for name in ('proposal_root', 'mapping_path', 'review_path'):
            if not isinstance(getattr(self, name), Path):
                raise PipelineError(f'{name} must be a Path')
        if self.mapping_path != self.proposal_root/'source_mapping.json':
            raise PipelineError('mapping_path must be inside proposal_root')
        if self.review_path != self.proposal_root/'SOURCE_MAPPING_REVIEW.md':
            raise PipelineError('review_path must be inside proposal_root')
        if type(self.source_id) is not str or not self.source_id:
            raise PipelineError('source_id must be nonempty')
        for name in ('input_binding_sha256', 'mapping_sha256'):
            value = getattr(self, name)
            if type(value) is not str or re.fullmatch('[0-9a-f]{64}', value) is None:
                raise PipelineError(f'{name} must be SHA256')
        if type(self.candidate_count) is not int or self.candidate_count < 0:
            raise PipelineError('candidate_count must be nonnegative integer')


def propose_vector_ch12_mapping(textbook_path: Path, answers_path: Path,
                               draft_path: Path, proposal_dir: Path,
                               config: PipelineConfig) -> VectorCh12Proposal:
    raise NotImplementedError("chapter12 proposal not implemented")


def _read_packages(textbook_path: Path, answers_path: Path, mapping: dict
                   ) -> dict[tuple[str, str], bytes]:
    """Validate both complete inventories before reading selected member bytes.

    The archives are opened from bounded immutable snapshots, not reopened paths.
    Metadata is validated/CRC checked but never included as source content.
    """
    snapshots = {}
    issues = []
    inventories = []
    total_size = total_members = 0
    with ExitStack() as stack:
        for role, path, declared in zip(('textbook', 'answers'),
                                        (textbook_path, answers_path), mapping['packages']):
            if path.is_file() and path.stat().st_size > archive._ARCHIVE_LIMIT:
                raise MmdAdapterBlockedError((archive._archive_issue('archive_size'),))
            raw = _read_input(path, role)
            if len(raw) > archive._ARCHIVE_LIMIT:
                raise MmdAdapterBlockedError((archive._archive_issue('archive_size'),))
            if (declared['role'] != role or len(raw) != declared['zip_size_bytes']
                    or hashlib.sha256(raw).hexdigest() != declared['zip_sha256']):
                raise MmdAdapterBlockedError((archive._issue('source_contract_mismatch',
                    'packages', {'role': role, 'reason': 'zip_identity'}),))
            try:
                z = stack.enter_context(zipfile.ZipFile(io.BytesIO(raw)))
                infos = z.infolist()
            except (ValueError, zipfile.BadZipFile) as exc:
                raise MmdAdapterBlockedError((archive._archive_issue('zip_structure'),)) from exc
            total_members += len(infos)
            total_size += sum(i.file_size for i in infos)
            names = {}
            seen_raw, seen_nfc, seen_fold = set(), set(), set()
            for info in infos:
                name, reason = archive._safe_member_name(info.orig_filename,
                    directory=archive._is_directory_entry(info))
                if reason:
                    issues.append(archive._member_issue(info.orig_filename, reason))
                    continue
                for seen, key, collision in ((seen_raw, info.orig_filename, 'duplicate'),
                    (seen_nfc, name, 'nfc_collision'), (seen_fold, name.casefold(), 'casefold_collision')):
                    if key in seen:
                        issues.append(archive._member_issue(info.orig_filename, collision))
                    seen.add(key)
                for reason in (archive._entry_type_reason(info), archive._hidden_reason(name)):
                    if reason:
                        issues.append(archive._member_issue(info.orig_filename, reason))
                if not archive._is_directory_entry(info):
                    suffix = PurePosixPath(name).suffix.casefold()
                    if suffix == '.zip':
                        issues.append(archive._member_issue(info.orig_filename, 'nested_archive'))
                    if (suffix == '.mmd' and name != declared['selected_member']
                            and not archive._is_allowed_metadata(name)):
                        issues.append(archive._member_issue(info.orig_filename, 'second_mmd'))
                    names[name] = info
                if info.flag_bits & 1:
                    issues.append(archive._archive_issue('encrypted', member=name))
                if info.compress_type not in archive._ALLOWED_COMPRESSION:
                    issues.append(archive._archive_issue('compression', member=name))
                reason, limit = archive._effective_size_rule(name)
                if info.file_size > limit:
                    issues.append(archive._archive_issue(reason, member=name))
                if info.file_size / max(info.compress_size, 1) > archive._RATIO_LIMIT:
                    issues.append(archive._archive_issue('compression_ratio', member=name))
            if declared['selected_member'] not in names:
                issues.append(archive._issue('selection_not_unique', 'packages',
                    {'role': role, 'reason': 'selected_member_missing'}))
            inventories.append((role, declared, z, names))
        if total_members > archive._MEMBER_COUNT_LIMIT:
            issues.append(archive._archive_issue('combined_member_count', actual=total_members,
                                                limit=archive._MEMBER_COUNT_LIMIT))
        if total_size > archive._TOTAL_LIMIT:
            issues.append(archive._archive_issue('combined_total_uncompressed', actual=total_size,
                                                limit=archive._TOTAL_LIMIT))
        if issues:
            raise MmdAdapterBlockedError(tuple(issues))
        observed_total = 0
        # CRC validation also covers unselected members; no source output exists yet.
        for role, declared, z, names in inventories:
            for name, info in names.items():
                try:
                    observed = archive._stream_member_to_eof(z, info)
                except (OSError, EOFError, RuntimeError, zipfile.BadZipFile, zlib.error) as exc:
                    raise MmdAdapterBlockedError((archive._archive_issue('crc_or_decompression',
                                                  member=name),)) from exc
                observed_total += observed
                _, limit = archive._effective_size_rule(name)
                if (observed != info.file_size or observed > limit
                        or observed / max(info.compress_size, 1) > archive._RATIO_LIMIT):
                    raise MmdAdapterBlockedError((archive._archive_issue('observed_size', member=name),))
        if observed_total > archive._TOTAL_LIMIT:
            raise MmdAdapterBlockedError((archive._archive_issue('combined_observed_size'),))
        for role, declared, z, names in inventories:
            for name, info in names.items():
                if archive._is_allowed_metadata(name):
                    continue
                if name != declared['selected_member'] and PurePosixPath(name).suffix not in archive._IMAGE_SUFFIXES:
                    continue
                content = archive._read_member(z, info)
                if name == declared['selected_member']:
                    if (len(content) != declared['member_size_bytes']
                            or hashlib.sha256(content).hexdigest() != declared['member_sha256']):
                        raise MmdAdapterBlockedError((archive._issue('source_contract_mismatch',
                            'packages', {'role': role, 'reason': 'member_identity'}),))
                    try:
                        content.decode('utf-8')
                        if content.startswith(b'\xef\xbb\xbf'):
                            raise ValueError('BOM')
                    except (UnicodeDecodeError, ValueError) as exc:
                        raise MmdAdapterBlockedError((archive._issue('source_contract_mismatch',
                            'packages', {'role': role, 'reason': 'utf8_or_bom'}),)) from exc
                snapshots[(role, name)] = content
    return snapshots


def adapt_vector_ch12_from_mapping(textbook_path: Path, answers_path: Path,
                                  mapping_path: Path, approval: SourceMappingApproval,
                                  output_dir: Path, config: PipelineConfig
                                  ) -> V124AdaptedImportPackage:
    raise NotImplementedError("chapter12 canonical bridge not implemented")
