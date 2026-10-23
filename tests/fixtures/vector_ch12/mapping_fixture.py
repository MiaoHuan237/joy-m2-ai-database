"""Tiny manually delimited source plus independently enumerated identity ledger."""
import hashlib


def fixture():
    members = {('textbook', 'source.mmd'): b'S\r\nC\r5. a 6. b',
               ('answers', 'source.mmd'): b'5. yes\n6. no'}
    def span(role, start, end):
        return dict(package_role=role, member='source.mmd', start_byte=start,
                    end_byte=end, raw_sha256=hashlib.sha256(members[(role, 'source.mmd')][start:end]).hexdigest())
    ids = [f'OSM-M2B12-C-EX12A-Q{i:02}' for i in range(1, 204)]
    mapping = dict(schema_version='vector-ch12-dual-source-mapping-v1',
        profile='OSM-M2B12-C-E', batch_id='SYNTHETIC-CH12', source_id='OSM-M2B12-C',
        answer_source_id='OSM-M2B12-E-ANSWERS', chapter=12,
        packages=[dict(role=role, zip_sha256='a'*64, zip_size_bytes=100,
                       selected_member='source.mmd', member_sha256=hashlib.sha256(data).hexdigest(),
                       member_size_bytes=len(data)) for (role, _), data in members.items()],
        shared_conditions=[dict(condition_id='shared', spans=[span('textbook', 0, 3),
            span('textbook', 3, 5)], applies_to=ids[4:6])], questions=[],
        unit_dispositions=[dict(question_id=qid, disposition='proposed_selection' if qid in ids[4:6]
            else 'later_processing', reason='Synthetic fixture only') for qid in ids],
        unselected_spans=[], unselected_image_members=[])
    for i, (start, end, astart, aend) in enumerate([(5, 9, 0, 6), (10, 14, 7, 12)], 5):
        mapping['questions'].append(dict(semantic_order=i-4, question_id=ids[i-1],
            source_section='EX12A', source_question_number=str(i),
            question_pieces=[dict(kind='shared', condition_id='shared'),
                             dict(kind='source', span=span('textbook', start, end))],
            solution_spans=[span('answers', astart, aend)], explanation_spans=[], image_bindings=[],
            answer_evidence=dict(level='final_answers_only', covered_subparts=['whole'],
                                 missing_subparts=[], limitation=''),
            metadata=dict(primary_type='向量', tags=['vector'], difficulty_level=None,
                          marks=None, question_language='zh-Hant', answer_language='en')))
    return mapping, members
