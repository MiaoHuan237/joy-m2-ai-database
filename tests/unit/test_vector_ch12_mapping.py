from dataclasses import FrozenInstanceError, fields
from pathlib import Path
import unittest

from joy_m2.errors import PipelineError
from joy_m2.ingest import vector_ch12 as profile
from joy_m2.ingest.adapter_models import MmdAdapterBlockedError
from tests.fixtures.vector_ch12.mapping_fixture import fixture
import copy
import hashlib


class CarrierTests(unittest.TestCase):
    def values(self):
        root = Path('/synthetic/proposal')
        return dict(proposal_root=root, mapping_path=root/'source_mapping.json',
                    review_path=root/'SOURCE_MAPPING_REVIEW.md', source_id='OSM-M2B12-C',
                    input_binding_sha256='a'*64, mapping_sha256='b'*64, candidate_count=2)

    def test_proposal_identity_cannot_be_mutated(self):
        value = profile.VectorCh12Proposal(**self.values())
        self.assertEqual(tuple(f.name for f in fields(value)), tuple(self.values()))
        with self.assertRaises(FrozenInstanceError):
            value.mapping_sha256 = 'c'*64

    def test_invalid_identity_count_or_paths_cannot_be_carried(self):
        for field, bad in [('mapping_path', Path('/other/source_mapping.json')),
                           ('review_path', Path('/other/review.md')), ('source_id', ''),
                           ('mapping_sha256', 'invalid'), ('input_binding_sha256', 'A'*64),
                           ('candidate_count', True), ('candidate_count', -1),
                           ('proposal_root', '/synthetic/proposal')]:
            with self.subTest(field=field, value=bad):
                values = self.values(); values[field] = bad
                with self.assertRaises(PipelineError):
                    profile.VectorCh12Proposal(**values)


class MappingTests(unittest.TestCase):
    def setUp(self):
        self.mapping, self.members = fixture()

    def check(self):
        return profile._validate_mapping(self.mapping, self.members)

    def reject(self):
        with self.assertRaises(MmdAdapterBlockedError):
            self.check()

    def test_valid_same_line_complete_records(self):
        self.assertIsNone(self.check())
        self.assertEqual(len(self.mapping['questions']), 2)

    def test_section_qualified_same_number_is_not_duplicate(self):
        old_ids = [q['question_id'] for q in self.mapping['questions']]
        new_ids = ['OSM-M2B12-C-EX12B-Q05', 'OSM-M2B12-C-EX12C-Q05']
        for q, section, new in zip(self.mapping['questions'], ['EX12B', 'EX12C'], new_ids):
            q.update(source_section=section, source_question_number='5', question_id=new)
        for row in self.mapping['unit_dispositions']:
            if row['question_id'] in old_ids:
                row['question_id'] = new_ids[old_ids.index(row['question_id'])]
        self.mapping['shared_conditions'][0]['applies_to'] = new_ids
        self.assertIsNone(self.check())

    def test_strict_fields_types_orders_and_ids(self):
        mutations = [('extra', lambda m: m.update(extra=True)),
            ('missing', lambda m: m.pop('profile')),
            ('bool', lambda m: m.update(chapter=True)),
            ('order', lambda m: m['questions'][0].update(semantic_order=True)),
            ('id', lambda m: m['questions'][0].update(question_id='replacement')),
            ('same_id', lambda m: m['questions'][1].update(question_id=m['questions'][0]['question_id'])),
            ('reverse', lambda m: m['questions'].reverse()),
            ('package_order', lambda m: m['packages'].reverse()),
            ('digest', lambda m: m['packages'][0].update(zip_sha256='X'*64))]
        for name, change in mutations:
            with self.subTest(name=name):
                self.mapping, self.members = fixture(); change(self.mapping); self.reject()

    def test_shared_missing_duplicate_wrong_scope_unknown_or_unused(self):
        for mode in ['missing', 'duplicate', 'scope', 'unknown', 'unused']:
            with self.subTest(mode=mode):
                self.mapping, self.members = fixture()
                pieces = self.mapping['questions'][0]['question_pieces']
                if mode == 'missing': pieces.pop(0)
                elif mode == 'duplicate': pieces.insert(0, copy.deepcopy(pieces[0]))
                elif mode == 'scope': self.mapping['shared_conditions'][0]['applies_to'].pop()
                elif mode == 'unknown': pieces[0]['condition_id'] = 'absent'
                else: self.mapping['shared_conditions'].append(dict(condition_id='unused', spans=[], applies_to=[]))
                self.reject()

    def test_gap_overlap_raw_hash_and_unaccounted_images(self):
        for mode in ['gap', 'overlap', 'sha', 'image']:
            with self.subTest(mode=mode):
                self.mapping, self.members = fixture()
                span = self.mapping['questions'][0]['question_pieces'][1]['span']
                if mode == 'gap':
                    span['end_byte'] = 8; span['raw_sha256'] = hashlib.sha256(b'5. ').hexdigest()
                elif mode == 'overlap':
                    self.mapping['unselected_spans'].append(dict(span=copy.deepcopy(span), reason='overlap'))
                elif mode == 'sha': span['raw_sha256'] = '0'*64
                else: self.members[('textbook', 'images/lost.png')] = b'image'
                self.reject()

    def test_disposition_cardinality_selection_and_hold(self):
        for mode in ['missing', 'duplicate', 'held', 'unlisted_selection']:
            with self.subTest(mode=mode):
                self.mapping, self.members = fixture(); ledger = self.mapping['unit_dispositions']
                if mode == 'missing': ledger.pop()
                elif mode == 'duplicate': ledger[-1] = copy.deepcopy(ledger[0])
                elif mode == 'held': ledger[4]['disposition'] = 'review_required'
                else: ledger[0]['disposition'] = 'proposed_selection'
                self.reject()

    def test_metadata_no_guesses_or_unknown_vocabulary(self):
        for field, value in [('tags', ['imagined-tag']), ('difficulty_level', True),
                             ('difficulty_level', 6), ('marks', float('nan')),
                             ('primary_type', '三角函数')]:
            with self.subTest(field=field):
                self.mapping, self.members = fixture()
                self.mapping['questions'][0]['metadata'][field] = value
                self.reject()


class AnswerCoverageTests(MappingTests):
    def test_partial_preserves_all_subparts_and_limitation(self):
        self.mapping['questions'] = self.mapping['questions'][:1]
        q = self.mapping['questions'][0]
        self.mapping['shared_conditions'] = []
        q['question_pieces'] = q['question_pieces'][1:]
        text = b'5. question\n(a) first\n(b) second\n(i) last'
        self.members[('textbook', 'source.mmd')] = text
        self.mapping['packages'][0].update(member_sha256=hashlib.sha256(text).hexdigest(), member_size_bytes=len(text))
        span = q['question_pieces'][0]['span']
        span.update(start_byte=0, end_byte=len(text), raw_sha256=hashlib.sha256(text).hexdigest())
        self.mapping['unit_dispositions'][5]['disposition'] = 'later_processing'
        answer = self.members[('answers', 'source.mmd')]
        q['solution_spans'][0].update(end_byte=len(answer), raw_sha256=hashlib.sha256(answer).hexdigest())
        q['answer_evidence'].update(level='partial', covered_subparts=['(a)'],
            missing_subparts=['(b)', '(i)'], limitation='Source gives part (a) only.')
        self.assertIsNone(self.check())
        self.assertEqual(len(self.mapping['questions']), 1)
        q['answer_evidence']['missing_subparts'].pop()
        self.reject()

    def test_four_coverage_levels_and_missing_remains_empty(self):
        q = self.mapping['questions'][0]
        for level in ['worked_solution', 'final_answers_only']:
            q['answer_evidence']['level'] = level
            self.assertIsNone(self.check())
        old = q['solution_spans']; q['solution_spans'] = []
        self.mapping['unselected_spans'] += [dict(span=s, reason='Not mapped as answer') for s in old]
        q['answer_evidence'].update(level='missing', covered_subparts=[], missing_subparts=['whole'])
        self.assertIsNone(self.check())

    def test_invalid_coverage_not_silently_completed(self):
        for change in [dict(level='official_ms'), dict(level='partial'),
                       dict(missing_subparts=['whole']), dict(covered_subparts=[]),
                       dict(level='missing')]:
            self.mapping, self.members = fixture()
            self.mapping['questions'][0]['answer_evidence'].update(change)
            with self.subTest(change=change): self.reject()


class RenderingTests(unittest.TestCase):
    def span(self, raw, start=0, end=None):
        end = len(raw) if end is None else end
        return dict(package_role='textbook', member='source.mmd', start_byte=start, end_byte=end,
                    raw_sha256=hashlib.sha256(raw[start:end]).hexdigest())

    def test_shared_expansion_exact_newlines_and_raw_hashes(self):
        mapping, members = fixture()
        q = mapping['questions'][0]
        pieces = profile._expand_question_pieces(q['question_pieces'], mapping['shared_conditions'])
        expected = [dict(kind='source', span=s) for s in mapping['shared_conditions'][0]['spans']] + [q['question_pieces'][1]]
        self.assertEqual(pieces, expected)
        text = profile._render_spans([p['span'] for p in pieces], members)
        self.assertEqual(text.encode(), b'S\n\nC\n\n5. a')
        self.assertNotEqual(hashlib.sha256(text.encode()).hexdigest(), pieces[0]['span']['raw_sha256'])

    def test_only_newlines_normalized_order_not_sorted(self):
        raw = ' A\r\nB\r中 '.encode()
        members = {('textbook', 'source.mmd'): raw}
        first, second = self.span(raw, 0, 4), self.span(raw, 4)
        self.assertEqual(profile._render_spans([first, second], members), ' A\n\nB\n中 ')
        self.assertEqual(profile._render_spans([second, first], members), 'B\n中 \n A\n')
        self.assertEqual(profile._render_spans([], members), '')

    def test_cuts_inside_protected_tokens_are_rejected_not_repaired(self):
        examples = [('中文'.encode(), 1), (b'![](images/a.png)', 8),
                    (b'$a+b$ tail', 3), (br'\frac{1}{x+1} tail', 9),
                    (br'\includegraphics[width=2cm]{images/a.png}', 18),
                    (b'123.45 + 6', 2), (br'\sqrt{x}', 3),
                    (br'\(x+y\) text', 4)]
        for raw, end in examples:
            with self.subTest(raw=raw), self.assertRaises(MmdAdapterBlockedError):
                profile._render_spans([self.span(raw, 0, end)], {('textbook', 'source.mmd'): raw})

    def test_intact_math_and_page_wrappers_preserved(self):
        raw = br'\end{itemize} $\frac{a}{b}$ \item[(a)] Find $x$.'
        self.assertEqual(profile._render_spans([self.span(raw)],
            {('textbook', 'source.mmd'): raw}).encode(), raw)
