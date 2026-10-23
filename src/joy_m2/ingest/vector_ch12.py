"""Explicit chapter 12 dual-package source profile; no real writer."""
from __future__ import annotations

from dataclasses import dataclass
from contextlib import ExitStack, closing
import hashlib
import io
from pathlib import Path, PurePosixPath
import re
import math
import sqlite3
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


def _validate_mapping(mapping: dict, members: dict[tuple[str, str], bytes]) -> None:
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
    tags = _controlled_tags()
    for order, q in enumerate(mapping['questions'], 1):
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
            _fail('question_id', 'unstable_or_duplicate_identity')
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
        metadata = q['metadata']
        _keys(metadata, 'primary_type tags difficulty_level marks question_language answer_language')
        if metadata['primary_type'] != '向量':
            _fail('metadata', 'controlled_primary_type')
        _strings(metadata['tags'], 'tags')
        if not set(metadata['tags']) <= tags:
            _fail('tags', 'unknown_controlled_tag')
        if metadata['difficulty_level'] is not None:
            _integer(metadata['difficulty_level'], 1, 5)
        if metadata['marks'] is not None:
            value = metadata['marks']
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                _fail('marks', 'invalid_marks')
        for field in ('question_language', 'answer_language'):
            _string(metadata[field], field)
        for binding in q['image_bindings']:
            # Exact token ownership is validated by the image phase.
            if type(binding) is not dict or type(binding.get('image_package_role')) is not str or type(binding.get('image_member')) is not str:
                _fail('image_bindings', 'invalid_binding', 'image_binding_invalid')
            bound_images.add((binding['image_package_role'], binding['image_member']))
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
        _fail('unit_dispositions', 'selection_or_order_mismatch')
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
    if any(left < boundary < right for boundary in (start, end) for left, right in protected):
        _fail('span', 'cut_inside_token_or_formula', 'mmd_parse_failed')


def _fail(field, reason, code='source_contract_mismatch'):
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
    _keys(span, 'package_role member start_byte end_byte raw_sha256')
    _string(span['package_role'], 'package_role'); _string(span['member'], 'member')
    key = (span['package_role'], span['member'])
    if key not in members:
        _fail('span', 'unknown_member')
    _integer(span['start_byte'], 0); _integer(span['end_byte'], span['start_byte'] + 1, len(members[key]))
    _hash(span['raw_sha256'])
    raw = members[key][span['start_byte']:span['end_byte']]
    if _sha(raw) != span['raw_sha256']:
        _fail('span', 'raw_identity')
    try:
        raw.decode('utf-8')
    except UnicodeDecodeError:
        _fail('span', 'utf8_boundary', 'mmd_parse_failed')
    return raw


def _controlled_tags():
    # Read the existing controlled vocabulary, not question-body tag guesses.
    path = Path(__file__).resolve().parents[3]/'releases/V1.23/Joy_M2_Complete_Question_DB_V1_23.sqlite3'
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
    # Literal list/line labels only: no inference from mathematics or answer text.
    asks = list(dict.fromkeys(re.findall(r'(?:\\item\[|(?m:^)[ \t]*)([（(](?:[a-z]|[ivx]+)[）)])', text))) or ['whole']
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
