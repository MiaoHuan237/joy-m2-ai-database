"""Test-owned literal two-question oracle; never imports the implementation."""
import copy
import hashlib
import json


def expected_files(mapping):
    def canonical(value):
        return json.dumps(value, ensure_ascii=False, sort_keys=True,
                          separators=(',', ':'), allow_nan=False).encode()
    def sha(raw): return hashlib.sha256(raw).hexdigest()
    source = b'S\r\nC\r5. a 6. b'
    answer = b'5. yes\n6. no'
    def span(role, start, end):
        data = source if role == 'textbook' else answer
        return dict(package_role=role, member='source.mmd', start_byte=start,
                    end_byte=end, raw_sha256=sha(data[start:end]))
    questions = []
    records = []
    for index, (start, end, text, solution) in enumerate([
        (5, 9, 'S\n\nC\n\n5. a', '5. yes'),
        (10, 14, 'S\n\nC\n\n6. b', '6. no'),
    ]):
        q = copy.deepcopy(mapping['questions'][index])
        q['question_pieces'] = [dict(kind='source', span=s) for s in [
            span('textbook', 0, 3), span('textbook', 3, 5), span('textbook', start, end)]]
        q.update(rendered_question_sha256=sha(text.encode()),
                 rendered_solution_sha256=sha(solution.encode()), rendered_explanation_sha256=sha(b''))
        questions.append(q)
        qid = f'OSM-M2B12-C-EX12A-Q{index + 5:02}'
        records.append(dict(proposed_question_id=qid, source_id='OSM-M2B12-C',
            source_section='EX12A', source_question_number=str(index + 5),
            source_fragment_hash=sha(text.encode()), question_text_original=text,
            question_text_zh=text, translation_status='source_present',
            translation_evidence=f'source:source/source-map.json#{qid}',
            solution_original=solution, solution_verified='', answer_status='source_provided',
            explanation_text='', explanation_status='missing', explanation_evidence=None,
            image_paths=[], image_roles=[], primary_type='向量', tags=['vector'],
            tag_status='proposed', difficulty_level=None, difficulty_status='missing',
            enrichment_status='incomplete'))
    source_map = dict(schema_version='vector-ch12-canonical-source-map-v1',
        profile='OSM-M2B12-C-E', source_id='OSM-M2B12-C', answer_source_id='OSM-M2B12-E-ANSWERS',
        chapter=12, members=[
            dict(package_role='textbook', member='source.mmd', sha256=sha(source), size_bytes=len(source), canonical_path='source/original.mmd.txt'),
            dict(package_role='answers', member='source.mmd', sha256=sha(answer), size_bytes=len(answer), canonical_path='answers/answer.mmd.txt'),
        ], questions=questions)
    files = {'source/original.mmd.txt': source, 'answers/answer.mmd.txt': answer,
        'records/candidates.json': canonical(records) + b'\n',
        'source/source-map.json': canonical(source_map),
        'teacher_notes/source-coverage.json': canonical(dict(schema_version='vector-ch12-source-coverage-v1',
            questions=[dict(question_id=q['question_id'], answer_evidence=q['answer_evidence']) for q in questions]))}
    def evidence(path, kind):
        return dict(relative_path=path, sha256=sha(files[path]), size_bytes=len(files[path]), kind=kind)
    manifest = dict(schema_version='task14-v124-import-manifest-v1', batch_id='SYNTHETIC-CH12',
        project='Joy M2 AI Database', module='M2', chapter='12', target_release_version='V1.24',
        candidate_records=[evidence('records/candidates.json', 'candidate_json')],
        source_files=[evidence('source/original.mmd.txt', 'source'), evidence('source/source-map.json', 'source')],
        answer_files=[evidence('answers/answer.mmd.txt', 'answer')], image_files=[],
        teacher_notes_files=[evidence('teacher_notes/source-coverage.json', 'teacher_notes')], common_errors_files=[],
        language_policy='preserve_source_and_store_reviewed_chinese_separately',
        split_policy='one_complete_question_per_record', difficulty_policy='joy_level_1_5',
        tag_policy='controlled_primary_type_and_tags', answer_policy='preserve_source_answer_identity',
        explanation_policy='source_or_independently_verified_with_identity')
    files['import_manifest.json'] = json.dumps(manifest, ensure_ascii=False,
        separators=(',', ':'), allow_nan=False).encode() + b'\n'
    return files
