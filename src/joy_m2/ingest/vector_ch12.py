"""Explicit chapter 12 dual-package source profile; no real writer."""
from __future__ import annotations

from dataclasses import dataclass, replace
from contextlib import ExitStack, closing
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import re
import math
import sqlite3
import stat
import shutil
import tempfile
from typing import TYPE_CHECKING
import zipfile
import zlib

from joy_m2.config import PipelineConfig
from joy_m2.errors import (PipelineError, ConfigurationError, OutputConflictError,
                           InputMissingError, InputFormatError)
from joy_m2.ingest.source_mapping import SourceMappingApproval
from joy_m2.ingest import archive
from joy_m2.ingest.adapter_models import MmdAdapterBlockedError
from joy_m2.ingest.source_mapping import _read_input, _decode_object, _preflight_destination
from joy_m2.ingest.writer_profiles import atomic_rename_no_replace

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
    inputs = (textbook_path, answers_path, draft_path)
    _check_arguments(inputs, proposal_dir, config)
    raw = _read_input(draft_path, 'source mapping draft')
    mapping = _decode_object(raw)
    _validate_shape(mapping)
    members = _read_packages(textbook_path, answers_path, mapping)
    _validate_mapping(mapping, members, config)
    _validate_images(mapping, members)
    mapping_bytes = _canonical(mapping)
    binding = _sha(_canonical({'profile': mapping['profile'], 'packages': mapping['packages']}))
    digest = _sha(mapping_bytes)
    lines = ['# Vector chapter12 source mapping review', '', 'UNAPPROVED — source mapping approval required.',
             f"Batch: {mapping['batch_id']}", f"Source: {mapping['source_id']}",
             f'Mapping SHA256: {digest}', f'Input binding SHA256: {binding}',
             f'Textbook: {textbook_path.resolve()}', f'Answers: {answers_path.resolve()}',
             f"Complete mapped units: {len(mapping['questions'])}",
             'This count is not an authoritative net-new classification.', '']
    for q in mapping['questions']:
        pieces = _expand_question_pieces(q['question_pieces'], mapping['shared_conditions'])
        lines += [f"## {q['semantic_order']}. {q['question_id']}",
                  f"Original: {q['source_section']} / {q['source_question_number']}",
                  'Answer coverage: ' + _canonical(q['answer_evidence']).decode(),
                  'Metadata: ' + _canonical(q['metadata']).decode(), '', '### Source question',
                  _render_spans([p['span'] for p in pieces], members), '', '### Source answer',
                  _render_spans(q['solution_spans'], members), '', '### Independent explanation',
                  _render_spans(q['explanation_spans'], members) or 'MISSING — no independent source evidence',
                  '', '### Image evidence', _canonical(q['image_bindings']).decode(), '']
    lines += ['## Preserved unit dispositions',
              *[f"{r['question_id']} — {r['disposition']}: {r['reason']}" for r in mapping['unit_dispositions']],
              '', 'Approval required (not received):',
              f"USER APPROVED SOURCE MAPPING {mapping['source_id']} {digest}", '']
    files = {'source_mapping.json': mapping_bytes, 'SOURCE_MAPPING_REVIEW.md': '\n'.join(lines).encode('utf-8')}
    def recheck():
        _recheck_inputs(inputs, raw, mapping)
    _publish_files(proposal_dir, config, files, recheck)
    return VectorCh12Proposal(proposal_dir, proposal_dir/'source_mapping.json',
        proposal_dir/'SOURCE_MAPPING_REVIEW.md', mapping['source_id'], binding, digest, len(mapping['questions']))


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
            raw = _read_archive_snapshot(path, role)
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
    from .v124_models import V124AdaptedImportPackage
    from .v124_manifest import load_v124_import_manifest
    inputs = (textbook_path, answers_path, mapping_path)
    _check_arguments(inputs, output_dir, config)
    raw = _read_input(mapping_path, 'source mapping')
    mapping = _decode_object(raw)
    _validate_shape(mapping)
    members = _read_packages(textbook_path, answers_path, mapping)
    _validate_mapping(mapping, members, config)
    _validate_images(mapping, members)
    _validate_approval(mapping, approval)
    files = _canonical_files(mapping, members)
    validated = []
    def validate(root):
        validated.append(load_v124_import_manifest(root/'import_manifest.json'))
    def recheck():
        _recheck_inputs(inputs, raw, mapping)
        _validate_approval(mapping, approval)
    _publish_files(output_dir, config, files, recheck, validate)
    return V124AdaptedImportPackage(output_dir, output_dir/'import_manifest.json', validated[0])


@dataclass(frozen=True)
class _CompositeContent:
    question_pieces: tuple[dict, ...]
    question_text: str
    solution_text: str
    explanation_text: str


def _canonical_files(mapping, members):
    """Project only approved source semantics; no transport or review identity."""
    member_rows, files, questions, records = [], {}, [], []
    for package, path in zip(mapping['packages'], ('source/original.mmd.txt', 'answers/answer.mmd.txt')):
        key = (package['role'], package['selected_member'])
        raw = members[key]; files[path] = raw
        member_rows.append(dict(package_role=key[0], member=key[1], sha256=_sha(raw),
                                size_bytes=len(raw), canonical_path=path))
    staged_images = set()
    for q in mapping['questions']:
        pieces = tuple(_expand_question_pieces(q['question_pieces'], mapping['shared_conditions']))
        content = _CompositeContent(pieces, _render_spans([p['span'] for p in pieces], members),
            _render_spans(q['solution_spans'], members), _render_spans(q['explanation_spans'], members))
        questions.append(dict(q, question_pieces=list(pieces),
            rendered_question_sha256=_sha(content.question_text.encode()),
            rendered_solution_sha256=_sha(content.solution_text.encode()),
            rendered_explanation_sha256=_sha(content.explanation_text.encode())))
        for binding in q['image_bindings']:
            key = (binding['image_package_role'], binding['image_member'])
            if key not in staged_images:
                staged_images.add(key)
                raw = members[key]; path = binding['canonical_path']; files[path] = raw
                member_rows.append(dict(package_role=key[0], member=key[1], sha256=_sha(raw),
                                        size_bytes=len(raw), canonical_path=path))
        metadata = q['metadata']
        image_paths, image_roles = _image_projection(q)
        evidence = f"source:source/source-map.json#{q['question_id']}"
        records.append(dict(proposed_question_id=q['question_id'], source_id=mapping['source_id'],
            source_section=q['source_section'], source_question_number=q['source_question_number'],
            source_fragment_hash=_sha(content.question_text.encode()),
            question_text_original=content.question_text, question_text_zh=content.question_text,
            translation_status='source_present', translation_evidence=evidence,
            solution_original=content.solution_text, solution_verified='',
            answer_status='missing_from_source' if q['answer_evidence']['level'] == 'missing' else 'source_provided',
            explanation_text=content.explanation_text,
            explanation_status='source_present' if q['explanation_spans'] else 'missing',
            explanation_evidence=evidence if q['explanation_spans'] else None,
            image_paths=image_paths, image_roles=image_roles, primary_type=metadata['primary_type'],
            tags=metadata['tags'], tag_status='proposed' if metadata['tags'] else 'missing',
            difficulty_level=metadata['difficulty_level'],
            difficulty_status='proposed' if metadata['difficulty_level'] is not None else 'missing',
            enrichment_status='complete' if q['explanation_spans'] and metadata['tags']
                and metadata['difficulty_level'] is not None else 'incomplete'))
    source_map = dict(schema_version='vector-ch12-canonical-source-map-v1',
        **{k: mapping[k] for k in ('profile', 'source_id', 'answer_source_id', 'chapter')},
        members=member_rows, questions=questions)
    files['source/source-map.json'] = _canonical(source_map)
    files['records/candidates.json'] = _canonical(records) + b'\n'
    files['teacher_notes/source-coverage.json'] = _canonical(dict(
        schema_version='vector-ch12-source-coverage-v1', questions=[
            dict(question_id=q['question_id'], answer_evidence=q['answer_evidence']) for q in mapping['questions']]))
    def evidence(path, kind):
        return dict(relative_path=path, sha256=_sha(files[path]), size_bytes=len(files[path]), kind=kind)
    manifest = dict(schema_version='task14-v124-import-manifest-v1', batch_id=mapping['batch_id'],
        project='Joy M2 AI Database', module='M2', chapter=str(mapping['chapter']), target_release_version='V1.24',
        candidate_records=[evidence('records/candidates.json', 'candidate_json')],
        source_files=[evidence('source/original.mmd.txt', 'source'), evidence('source/source-map.json', 'source')],
        answer_files=[evidence('answers/answer.mmd.txt', 'answer')],
        image_files=[evidence(r['canonical_path'], 'image') for r in member_rows[2:]],
        teacher_notes_files=[evidence('teacher_notes/source-coverage.json', 'teacher_notes')], common_errors_files=[],
        language_policy='preserve_source_and_store_reviewed_chinese_separately',
        split_policy='one_complete_question_per_record', difficulty_policy='joy_level_1_5',
        tag_policy='controlled_primary_type_and_tags', answer_policy='preserve_source_answer_identity',
        explanation_policy='source_or_independently_verified_with_identity')
    files['import_manifest.json'] = json.dumps(manifest, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode() + b'\n'
    return files


def _validate_mapping(mapping: dict, members: dict[tuple[str, str], bytes],
                      config: PipelineConfig | None = None) -> None:
    _keys(mapping, 'schema_version profile batch_id source_id answer_source_id chapter packages '
          'shared_conditions questions unit_dispositions unselected_spans unselected_image_members')
    for field, expected in [('schema_version', 'vector-ch12-dual-source-mapping-v1'),
                            ('profile', 'OSM-M2B12-C-E'), ('source_id', 'OSM-M2B12-C'),
                            ('answer_source_id', 'OSM-M2B12-E-ANSWERS'), ('chapter', 12)]:
        if type(mapping[field]) is not type(expected) or mapping[field] != expected:
            _fail(field, 'profile_identity')
    _string(mapping['batch_id'], 'batch_id')
    for field in ('packages', 'shared_conditions', 'questions', 'unit_dispositions',
                  'unselected_spans', 'unselected_image_members'):
        if type(mapping[field]) is not list:
            _fail(field, 'expected_array')
    if len(mapping['packages']) != 2:
        _fail('packages', 'two_roles_required')
    selected = set()
    for role, package in zip(('textbook', 'answers'), mapping['packages']):
        _keys(package, 'role zip_sha256 zip_size_bytes selected_member member_sha256 member_size_bytes')
        if package['role'] != role:
            _fail('packages', 'role_order')
        _hash(package['zip_sha256']); _hash(package['member_sha256'])
        _integer(package['zip_size_bytes'], 1); _integer(package['member_size_bytes'], 1)
        _string(package['selected_member'], 'selected_member')
        name, reason = archive._safe_member_name(package['selected_member'], directory=False)
        if (reason or name != package['selected_member'] or not name.endswith('.mmd')
                or archive._is_allowed_metadata(name)):
            _fail('packages', 'selected_member_invalid')
        key = (role, name); selected.add(key)
        if key not in members or len(members[key]) != package['member_size_bytes'] or _sha(members[key]) != package['member_sha256']:
            _fail('packages', 'member_identity')
    owners = {key: [] for key in selected}

    def own(span):
        _span_bytes(span, members)
        key = (span['package_role'], span['member'])
        if key not in selected:
            _fail('span', 'content_not_selected_mmd')
        owners[key].append((span['start_byte'], span['end_byte']))

    conditions = {}
    for condition in mapping['shared_conditions']:
        _keys(condition, 'condition_id spans applies_to')
        cid = condition['condition_id']; _string(cid, 'condition_id')
        if cid in conditions:
            _fail('shared_conditions', 'duplicate_condition')
        _strings(condition['applies_to'], 'applies_to', nonempty=True)
        if type(condition['spans']) is not list or not condition['spans']:
            _fail('shared_conditions', 'empty_spans')
        for span in condition['spans']:
            own(span)
            if span['package_role'] != 'textbook':
                _fail('shared_conditions', 'question_from_answer')
        conditions[cid] = condition
    used = {cid: [] for cid in conditions}
    ids = []
    occurrences = []
    bound_images = set()
    question_issues = []
    for order, q in enumerate(mapping['questions'], 1):
        try:
            _keys(q, 'semantic_order question_id source_section source_question_number question_pieces '
                  'solution_spans explanation_spans image_bindings answer_evidence metadata')
            if type(q['semantic_order']) is not int or q['semantic_order'] != order:
                _fail('semantic_order', 'noncontiguous')
            for field in ('question_id', 'source_section', 'source_question_number'):
                _string(q[field], field)
            if not re.fullmatch(r'[1-9][0-9]*', q['source_question_number']):
                _fail('source_question_number', 'not_complete_number')
            expected_id = f"{mapping['source_id']}-{q['source_section']}-Q{int(q['source_question_number']):02}"
            if q['question_id'] != expected_id or q['question_id'] in ids:
                _fail('question_id', 'unstable_or_duplicate_identity', 'selection_not_unique')
            ids.append(q['question_id'])
            for field in ('question_pieces', 'solution_spans', 'explanation_spans', 'image_bindings'):
                if type(q[field]) is not list:
                    _fail(field, 'expected_array')
            direct = []
            for piece in q['question_pieces']:
                if type(piece) is not dict:
                    _fail('question_pieces', 'expected_object')
                if piece.get('kind') == 'shared':
                    _keys(piece, 'kind condition_id')
                    cid = piece['condition_id']
                    if type(cid) is not str or cid not in conditions or q['question_id'] in used[cid]:
                        _fail('question_pieces', 'unknown_or_repeated_shared')
                    used[cid].append(q['question_id'])
                elif piece.get('kind') == 'source':
                    _keys(piece, 'kind span'); span = piece['span']; own(span)
                    if span['package_role'] != 'textbook':
                        _fail('question_pieces', 'question_from_answer')
                    direct.append(span)
                else:
                    _fail('question_pieces', 'unknown_piece_kind')
            if not direct:
                _fail('question_pieces', 'missing_ask')
            occurrences.append(direct[0]['start_byte'])
            for field in ('solution_spans', 'explanation_spans'):
                for span in q[field]:
                    own(span)
            expanded = _expand_question_pieces(q['question_pieces'], mapping['shared_conditions'])
            text = _render_spans([p['span'] for p in expanded], members)
            _render_spans(q['solution_spans'], members)
            _render_spans(q['explanation_spans'], members)
            _validate_answer_evidence(q, text)
        except MmdAdapterBlockedError as exc:
            qid = q.get('question_id') if type(q) is dict else None
            qid = qid if type(qid) is str and qid else None
            question_issues.extend(replace(issue, proposed_question_id=qid) for issue in exc.issues)
    if question_issues:
        raise MmdAdapterBlockedError(tuple(question_issues))
    if occurrences != sorted(set(occurrences)):
        _fail('questions', 'source_occurrence_order')
    for cid, condition in conditions.items():
        if used[cid] != condition['applies_to']:
            _fail('shared_conditions', 'beneficiary_mismatch')
    ledger = mapping['unit_dispositions']
    if len(ledger) != 203:
        _fail('unit_dispositions', '203_units_required', 'candidate_count_mismatch')
    ledger_ids = []; selected_ids = []
    for row in ledger:
        _keys(row, 'question_id disposition reason')
        _string(row['question_id'], 'question_id'); _string(row['reason'], 'reason')
        if row['question_id'] in ledger_ids:
            _fail('unit_dispositions', 'duplicate_id')
        ledger_ids.append(row['question_id'])
        if row['disposition'] not in ('proposed_selection', 'later_processing', 'review_required', 'outside_first_vector_batch'):
            _fail('unit_dispositions', 'unknown_disposition')
        if row['disposition'] == 'proposed_selection':
            selected_ids.append(row['question_id'])
    if selected_ids != ids:
        _fail('unit_dispositions', 'selection_or_order_mismatch', 'candidate_count_mismatch')
    for item in mapping['unselected_spans']:
        _keys(item, 'span reason'); _string(item['reason'], 'reason'); own(item['span'])
    for key, intervals in owners.items():
        previous = 0
        raw = members[key]
        for start, end in sorted(intervals):
            if start < previous:
                _fail('coverage', 'overlapping_ownership')
            if raw[previous:start].decode('utf-8').strip():
                _fail('coverage', 'unowned_nonwhitespace')
            previous = end
        if raw[previous:].decode('utf-8').strip():
            _fail('coverage', 'unowned_nonwhitespace')
    # Stage 5 must not hide a prior span/coverage defect. Collect inspectable
    # semantic issues only after structural ownership has closed.
    tags = _controlled_tags(config)
    semantic_issues = []
    for q in mapping['questions']:
        try:
            metadata = q['metadata']
            _keys(metadata, 'primary_type tags difficulty_level marks question_language answer_language')
            if metadata['primary_type'] != '向量':
                _fail('metadata', 'controlled_primary_type')
            _strings(metadata['tags'], 'tags')
            if not set(metadata['tags']) <= tags:
                _fail('tags', 'unknown_controlled_tag')
            if metadata['difficulty_level'] is not None:
                _fail('difficulty_level', 'profile_requires_missing_difficulty')
            if metadata['marks'] is not None:
                value = metadata['marks']
                if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                    _fail('marks', 'invalid_marks')
            if metadata['question_language'] != 'zh-Hant' or metadata['answer_language'] not in ('en', 'zh-Hant'):
                _fail('metadata', 'unsupported_language_roles', 'language_mapping_ambiguous')
            for binding in q['image_bindings']:
                if type(binding) is not dict or type(binding.get('image_package_role')) is not str or type(binding.get('image_member')) is not str:
                    _fail('image_bindings', 'invalid_binding', 'image_binding_invalid')
                bound_images.add((binding['image_package_role'], binding['image_member']))
        except MmdAdapterBlockedError as exc:
            semantic_issues.extend(replace(issue, proposed_question_id=q['question_id']) for issue in exc.issues)
    if semantic_issues:
        raise MmdAdapterBlockedError(tuple(semantic_issues))
    ignored_images = set()
    for row in mapping['unselected_image_members']:
        _keys(row, 'package_role member sha256 reason')
        for field in ('package_role', 'member', 'reason'): _string(row[field], field)
        key = (row['package_role'], row['member'])
        if key in ignored_images or key in bound_images or key not in members or _sha(members[key]) != row['sha256']:
            _fail('unselected_image_members', 'invalid_image_accounting', 'image_binding_invalid')
        ignored_images.add(key)
    images = {key for key in members if PurePosixPath(key[1]).suffix in archive._IMAGE_SUFFIXES}
    if images != ignored_images | bound_images:
        _fail('image_bindings', 'unaccounted_image', 'image_binding_invalid')


def _render_spans(spans: list[dict], members: dict[tuple[str, str], bytes]) -> str:
    parts = []
    for span in spans:
        raw = _span_bytes(span, members)
        _check_boundaries(members[(span['package_role'], span['member'])],
                          span['start_byte'], span['end_byte'])
        parts.append(raw.decode('utf-8').replace('\r\n', '\n').replace('\r', '\n'))
    return '\n'.join(parts)


def _expand_question_pieces(pieces: list[dict], shared: list[dict]) -> list[dict]:
    conditions = {c['condition_id']: c['spans'] for c in shared}
    expanded = []
    for piece in pieces:
        if piece['kind'] == 'shared':
            if piece['condition_id'] not in conditions:
                _fail('question_pieces', 'unknown_shared')
            expanded.extend({'kind': 'source', 'span': dict(span)}
                            for span in conditions[piece['condition_id']])
        else:
            expanded.append({'kind': 'source', 'span': dict(piece['span'])})
    return expanded


def _check_boundaries(raw: bytes, start: int, end: int) -> None:
    """Only protect lexical atoms; never discover questions or repair source."""
    protected = []
    # An unmatched math opener still protects its remainder. Never use a
    # missing closer as permission to discard part of the expression.
    opening = None
    closers = {b'$': b'$', b'$$': b'$$', br'\(': br'\)', br'\[': br'\]'}
    for token in re.finditer(rb'(?<!\\)(?:\$\$|\$)|\\[()[\]]', raw):
        value = token.group()
        if opening is None and value in closers:
            opening = (token.start(), closers[value])
        elif opening is not None and value == opening[1]:
            protected.append((opening[0], token.end())); opening = None
    if opening is not None:
        protected.append((opening[0], len(raw)))
    for env in re.finditer(rb'\\begin\{(align\*?|equation\*?|gather\*?|displaymath)\}', raw):
        closer = b'\\end{' + env.group(1) + b'}'
        finish = raw.find(closer, env.end())
        protected.append((env.start(), len(raw) if finish < 0 else finish + len(closer)))
    # Protect a base together with a literal TeX script, including nested
    # braced arguments. This does not evaluate or repair the mathematics.
    for script in re.finditer(rb'(?<!\\)[_^]', raw):
        left = max(0, script.start() - 1)
        cursor = script.end()
        while cursor < len(raw) and raw[cursor] in b' \t': cursor += 1
        if cursor < len(raw) and raw[cursor] == ord('{'):
            depth = 1; cursor += 1
            while cursor < len(raw) and depth:
                if raw[cursor] == ord('\\'): cursor += 2; continue
                if raw[cursor] == ord('{'): depth += 1
                elif raw[cursor] == ord('}'): depth -= 1
                cursor += 1
        else:
            atom = re.match(rb'\\[A-Za-z]+|[^\s]', raw[cursor:])
            cursor += atom.end() if atom else 0
        protected.append((left, cursor))
    for pattern in (rb'!\[[^\]\r\n]*\]\([^\r\n]*?\)',
                    rb'\\\[[\s\S]*?\\\]', rb'\\\([\s\S]*?\\\)',
                    rb'(?<!\\)\$\$[\s\S]*?(?<!\\)\$\$',
                    rb'(?<![\\$])\$(?!\$)[\s\S]*?(?<!\\)\$(?!\$)',
                    rb'\\(?:begin)\{(?:align\*?|equation\*?|gather\*?|displaymath)\}[\s\S]*?'
                    rb'\\end\{(?:align\*?|equation\*?|gather\*?|displaymath)\}',
                    rb'[A-Za-z0-9_]+(?:\.[0-9]+)?'):
        protected.extend((m.start(), m.end()) for m in re.finditer(pattern, raw))
    for match in re.finditer(rb'\\[A-Za-z]+\*?', raw):
        finish = match.end()
        # Consecutive optional/mandatory command arguments belong to the atom.
        cursor = finish
        while cursor < len(raw):
            while cursor < len(raw) and raw[cursor] in b' \t': cursor += 1
            if cursor >= len(raw) or raw[cursor] not in b'[{': break
            opening = raw[cursor]; closing_byte = ord(']') if opening == ord('[') else ord('}')
            depth = 1; cursor += 1
            while cursor < len(raw) and depth:
                if raw[cursor] == ord('\\'):
                    cursor += 2; continue
                if raw[cursor] == opening: depth += 1
                elif raw[cursor] == closing_byte: depth -= 1
                cursor += 1
            if depth:
                # Do not permit a boundary in an unterminated command argument.
                finish = len(raw); break
            finish = cursor
        protected.append((match.start(), finish))
        protected.append((match.start(), _tex_argument_end(raw, match.start())))
    if any(left < boundary < right for boundary in (start, end) for left, right in protected):
        _fail('span', 'cut_inside_token_or_formula', 'mmd_parse_failed')


def _tex_argument_end(raw, cursor):
    """Finite lexical arities only; no mathematical interpretation or repair."""
    while cursor < len(raw) and raw[cursor] in b' \t\r\n': cursor += 1
    if cursor == len(raw): return cursor
    if raw[cursor] == ord('{'):
        depth = 1; cursor += 1
        while cursor < len(raw) and depth:
            if raw[cursor] == ord('\\'): cursor += 2; continue
            if raw[cursor] == ord('{'): depth += 1
            elif raw[cursor] == ord('}'): depth -= 1
            cursor += 1
        return min(cursor, len(raw))
    command = re.match(rb'\\[A-Za-z]+\*?', raw[cursor:])
    if not command: return cursor + 1
    cursor += command.end()
    arity = (2 if command.group() in (br'\frac', br'\dfrac', br'\tfrac', br'\binom',
                                      br'\dbinom', br'\tbinom', br'\overset', br'\underset')
             else 1 if command.group() in (br'\vec', br'\hat', br'\bar', br'\dot', br'\ddot',
                br'\overline', br'\underline', br'\sqrt', br'\mathbf', br'\mathrm',
                br'\mathit', br'\overrightarrow', br'\text') else 0)
    if command.group() == br'\sqrt':
        optional = re.match(rb'\s*\[[^\]]*\]', raw[cursor:])
        if optional: cursor += optional.end()
    for _ in range(arity): cursor = _tex_argument_end(raw, cursor)
    return cursor


def _validate_images(mapping: dict, members: dict[tuple[str, str], bytes]) -> None:
    issues = []
    for q in mapping['questions']:
        try:
            _validate_image_rows(dict(mapping, questions=[q]), members)
        except MmdAdapterBlockedError as exc:
            issues.extend(replace(issue, proposed_question_id=q['question_id']) for issue in exc.issues)
    if issues:
        raise MmdAdapterBlockedError(tuple(issues))


def _validate_image_rows(mapping: dict, members: dict[tuple[str, str], bytes]) -> None:
    for q in mapping['questions']:
        content = {'question': [p['span'] for p in _expand_question_pieces(
            q['question_pieces'], mapping['shared_conditions'])],
            'solution': q['solution_spans'], 'explanation': q['explanation_spans']}
        expected = []
        for role, spans in content.items():
            for span in spans:
                raw = _span_bytes(span, members)
                for start, end, target in _image_tokens(raw):
                    expected.append((role, span['package_role'], span['member'],
                                     start + span['start_byte'], end + span['start_byte'], target))
        actual = []
        for order, b in enumerate(q['image_bindings'], 1):
            _keys(b, 'semantic_order content_role token_span raw_target image_package_role image_member '
                  'image_sha256 canonical_path')
            if type(b['semantic_order']) is not int or b['semantic_order'] != order:
                _fail('image_bindings', 'semantic_order', 'image_binding_invalid')
            for field in ('content_role', 'raw_target', 'image_package_role', 'image_member', 'canonical_path'):
                _string(b[field], field)
            token = b['token_span']; raw = _span_bytes(token, members)
            parsed = _image_tokens(raw)
            if parsed != [(0, len(raw), b['raw_target'])]:
                _fail('image_bindings', 'token_identity', 'image_binding_invalid')
            actual.append((b['content_role'], token['package_role'], token['member'],
                           token['start_byte'], token['end_byte'], b['raw_target']))
            target = b['raw_target'][2:] if b['raw_target'].startswith('./') else b['raw_target']
            # No URL, absolute path, traversal, Unicode alias or cross-role fallback.
            name, reason = archive._safe_member_name(target, directory=False)
            if reason or name != target or ':' in target or PurePosixPath(target).suffix not in archive._IMAGE_SUFFIXES:
                _fail('image_bindings', 'unsafe_target', 'image_binding_invalid')
            resolved = (PurePosixPath(token['member']).parent / target).as_posix()
            key = (token['package_role'], resolved)
            if (b['image_package_role'] != key[0] or b['image_member'] != key[1]
                    or key not in members or _sha(members[key]) != b['image_sha256']
                    or b['canonical_path'] != f'images/{key[0]}/{key[1]}'):
                _fail('image_bindings', 'binding_identity', 'image_binding_invalid')
        if actual != expected or len(set(actual)) != len(actual):
            _fail('image_bindings', 'token_ownership_or_order', 'image_binding_invalid')


def _image_projection(question: dict) -> tuple[list[str], list[str]]:
    pairs = list(dict.fromkeys((b['canonical_path'], b['content_role'])
                              for b in question['image_bindings']))
    return [p for p, _ in pairs], [r for _, r in pairs]


def _validate_approval(mapping: dict, approval: SourceMappingApproval) -> None:
    if type(approval) is not SourceMappingApproval:
        raise TypeError('approval must be an exact SourceMappingApproval')
    digest = _sha(_canonical(mapping))
    if (approval.source_id != mapping['source_id'] or approval.mapping_sha256 != digest
            or approval.approval_text != f"USER APPROVED SOURCE MAPPING {mapping['source_id']} {digest}"):
        _fail('approval', 'exact_source_mapping_identity')


def _canonical(value) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(',', ':'), allow_nan=False).encode('utf-8')


def _check_arguments(inputs, output, config):
    if any(not isinstance(path, Path) for path in (*inputs, output)):
        raise TypeError('all input/output paths must be pathlib.Path')
    if type(config) is not PipelineConfig:
        raise TypeError('config must be an exact PipelineConfig')
    _preflight_destination(output, config)
    target = output.resolve()
    for path in inputs:
        source = path.resolve()
        if source == target or source.is_relative_to(target) or target.is_relative_to(source):
            raise ConfigurationError('output overlaps input evidence')
        if path.name in ('source_mapping.json', 'SOURCE_MAPPING_REVIEW.md') and target.is_relative_to(source.parent):
            raise ConfigurationError('output overlaps proposal evidence root')


def _validate_shape(mapping):
    # Fail schema/identity declarations before touching either archive.
    _keys(mapping, 'schema_version profile batch_id source_id answer_source_id chapter packages '
          'shared_conditions questions unit_dispositions unselected_spans unselected_image_members')
    for field, expected in [('schema_version', 'vector-ch12-dual-source-mapping-v1'),
            ('profile', 'OSM-M2B12-C-E'), ('source_id', 'OSM-M2B12-C'),
            ('answer_source_id', 'OSM-M2B12-E-ANSWERS'), ('chapter', 12)]:
        if type(mapping[field]) is not type(expected) or mapping[field] != expected:
            _fail(field, 'profile_identity')
    _string(mapping['batch_id'], 'batch_id')
    for field in ('packages', 'shared_conditions', 'questions', 'unit_dispositions',
                  'unselected_spans', 'unselected_image_members'):
        if type(mapping[field]) is not list:
            _fail(field, 'expected_array')
    if len(mapping['packages']) != 2:
        _fail('packages', 'two_roles_required')
    for role, p in zip(('textbook', 'answers'), mapping['packages']):
        _keys(p, 'role zip_sha256 zip_size_bytes selected_member member_sha256 member_size_bytes')
        if p['role'] != role: _fail('packages', 'role_order')
        _hash(p['zip_sha256']); _hash(p['member_sha256'])
        _integer(p['zip_size_bytes'], 1); _integer(p['member_size_bytes'], 1)
        _string(p['selected_member'], 'selected_member')
        name, reason = archive._safe_member_name(p['selected_member'], directory=False)
        if reason or name != p['selected_member'] or archive._is_allowed_metadata(name):
            _fail('packages', 'selected_member_invalid')
        if not name.endswith('.mmd'):
            _fail('packages', 'selected_format', 'unsupported_source_format')


def _read_archive_snapshot(path, role):
    if not path.exists():
        raise InputMissingError(f'{role} source missing')
    if not path.is_file():
        raise InputFormatError(f'{role} source is not a regular file')
    try:
        with path.open('rb') as stream:
            raw = stream.read(archive._ARCHIVE_LIMIT + 1)
    except OSError as exc:
        raise InputFormatError(f'{role} source cannot be read') from exc
    if len(raw) > archive._ARCHIVE_LIMIT:
        raise MmdAdapterBlockedError((archive._archive_issue('archive_size'),))
    return raw


def _recheck_inputs(inputs, draft_raw, mapping):
    for path, p in zip(inputs[:2], mapping['packages']):
        raw = _read_archive_snapshot(path, p['role'])
        if len(raw) != p['zip_size_bytes'] or _sha(raw) != p['zip_sha256']:
            _fail('packages', 'input_changed_before_publication')
    if _read_input(inputs[2], 'mapping') != draft_raw:
        _fail('mapping', 'input_changed_before_publication')


def _publish_files(output, config, files, recheck, validate=None):
    _preflight_destination(output, config)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=f'.{output.name}-', dir=output.parent))
    owned = temporary.stat()
    try:
        for name, content in files.items():
            target = temporary/name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        if validate is not None:
            validate(temporary)
        recheck()
        _preflight_destination(output, config)
        current = temporary.lstat()
        if ((current.st_dev, current.st_ino) != (owned.st_dev, owned.st_ino)
                or not stat.S_ISDIR(current.st_mode)):
            _fail('output', 'private_snapshot_owner_changed')
        actual = {}
        for path in temporary.rglob('*'):
            if path.is_symlink():
                _fail('output', 'private_snapshot_symlink')
            if path.is_file():
                actual[path.relative_to(temporary).as_posix()] = path.read_bytes()
        if actual != files:
            _fail('output', 'private_snapshot_bytes_changed')
        try:
            atomic_rename_no_replace(temporary, output)
        except FileExistsError as exc:
            raise OutputConflictError('output path already exists') from exc
    finally:
        # A concurrent actor may rename our directory and replace its old path.
        # Remove only the inode allocated by this invocation, never that replacement.
        for candidate in output.parent.iterdir():
            if candidate == output:
                continue
            try:
                current = candidate.lstat()
                if (current.st_dev, current.st_ino) == (owned.st_dev, owned.st_ino) and stat.S_ISDIR(current.st_mode):
                    shutil.rmtree(candidate)
            except FileNotFoundError:
                pass


def _image_tokens(raw: bytes) -> list[tuple[int, int, str]]:
    pattern = rb'!\[[^\]\r\n]*\]\(([^\r\n]*?)\)|\\includegraphics(?:\[[^\]\r\n]*\])?\{([^}\r\n]*)\}'
    return [(m.start(), m.end(), (m.group(1) if m.group(1) is not None else m.group(2)).decode('utf-8'))
            for m in re.finditer(pattern, raw)]


def _fail(field, reason, code='source_contract_mismatch'):
    if code == 'source_contract_mismatch' and field in ('shared_conditions', 'question_pieces', 'coverage', 'answer_evidence'):
        code = 'mmd_parse_failed'
    raise MmdAdapterBlockedError((archive._issue(code, field, {'reason': reason}),))


def _sha(raw):
    return hashlib.sha256(raw).hexdigest()


def _keys(value, names):
    if type(value) is not dict or set(value) != set(names.split()):
        _fail('schema', 'exact_keys')


def _string(value, field):
    if type(value) is not str or not value.strip():
        _fail(field, 'nonempty_string_required')


def _strings(value, field, nonempty=False):
    if type(value) is not list or (nonempty and not value):
        _fail(field, 'array_required')
    for item in value: _string(item, field)
    if len(set(value)) != len(value):
        _fail(field, 'duplicate_values')


def _integer(value, minimum, maximum=None):
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        _fail('integer', 'invalid_range_or_type')


def _hash(value):
    if type(value) is not str or re.fullmatch('[0-9a-f]{64}', value) is None:
        _fail('sha256', 'invalid_sha256')


def _span_bytes(span, members):
    if type(span) is not dict or set(span) != set('package_role member start_byte end_byte raw_sha256'.split()):
        _fail('span', 'exact_keys', 'mmd_parse_failed')
    if (type(span['package_role']) is not str or type(span['member']) is not str
            or not span['package_role'] or not span['member']):
        _fail('span', 'invalid_locator', 'mmd_parse_failed')
    key = (span['package_role'], span['member'])
    if key not in members:
        _fail('span', 'unknown_member')
    if (type(span['start_byte']) is not int or type(span['end_byte']) is not int
            or not 0 <= span['start_byte'] < span['end_byte'] <= len(members[key])):
        _fail('span', 'invalid_range_or_type', 'mmd_parse_failed')
    _hash(span['raw_sha256'])
    raw = members[key][span['start_byte']:span['end_byte']]
    if _sha(raw) != span['raw_sha256']:
        _fail('span', 'raw_identity')
    try:
        raw.decode('utf-8')
    except UnicodeDecodeError:
        _fail('span', 'utf8_boundary', 'mmd_parse_failed')
    return raw


def _controlled_tags(config=None):
    # Read the existing controlled vocabulary, not question-body tag guesses.
    if config is None:
        config = PipelineConfig(Path(__file__).resolve().parents[3])
    path = config.releases_root/'V1.23/Joy_M2_Complete_Question_DB_V1_23.sqlite3'
    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as connection:
        return frozenset(row[0] for row in connection.execute(
            "SELECT value FROM complete_question_taxonomy_v2 WHERE taxonomy_kind='tag'"))


def _validate_answer_evidence(q, text):
    evidence = q['answer_evidence']
    _keys(evidence, 'level covered_subparts missing_subparts limitation')
    level = evidence['level']
    if level not in ('worked_solution', 'final_answers_only', 'partial', 'missing'):
        _fail('answer_evidence', 'unknown_level')
    covered, missing = evidence['covered_subparts'], evidence['missing_subparts']
    _strings(covered, 'covered_subparts'); _strings(missing, 'missing_subparts')
    if type(evidence['limitation']) is not str:
        _fail('answer_evidence', 'limitation_type')
    # Literal labels, including same-line asks, not mathematical inference.
    # Formula regions do not turn function arguments into subpart labels.
    prose = re.sub(r'\\\[[\s\S]*?\\\]|\\\([\s\S]*?\\\)|\$\$[\s\S]*?\$\$|\$[^$]*\$', '', text)
    asks = list(dict.fromkeys(re.findall(r'(?:\\item\[|(?<!\w))([（(](?:[a-z]|[ivx]+)[）)])', prose))) or ['whole']
    if set(covered) & set(missing) or set(covered + missing) != set(asks):
        _fail('answer_evidence', 'ask_coverage')
    if covered != [x for x in asks if x in covered] or missing != [x for x in asks if x in missing]:
        _fail('answer_evidence', 'ask_order')
    if level == 'missing':
        if q['solution_spans'] or covered or missing != asks:
            _fail('answer_evidence', 'missing_has_solution')
    elif not q['solution_spans']:
        _fail('answer_evidence', 'source_answer_absent')
    elif level == 'partial':
        if not missing or not covered or not evidence['limitation'].strip():
            _fail('answer_evidence', 'partial_needs_limitation')
    elif missing:
        _fail('answer_evidence', 'complete_has_missing_asks')
