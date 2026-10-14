import copy
import hashlib
import json
from pathlib import Path
import tempfile
import shutil
import unittest

from pypdf import PdfWriter
from joy_m2.config import PipelineConfig
from joy_m2.ingest.automation import canonical, sha
from joy_m2.ingest.publisher_mock import inspect_proposal, build_package


class PublisherMockTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.config = PipelineConfig(self.root)
        shutil.copytree(Path(__file__).resolve().parents[2]/'releases/V1.22',self.root/'releases/V1.22')
        self.inputs = {k:self.root/(k+'.json' if k in ('staging','proposal') else k+'.pdf')
                       for k in ('staging','proposal','pp','ms')}
        for role in ('pp','ms'):
            writer = PdfWriter()
            writer.add_blank_page(width=600, height=800)
            writer.write(self.inputs[role])
        rows = [{'staging_id':f'MOCK-C1-2025-26-Q{i:02d}', 'question_pages':[1],
                 'solution_pages':[1], 'marks':5 if i<13 else 40,
                 'difficulty_proposal':3} for i in range(1,14)]
        self.draft = {'batch_id':'MOCK-SYNTHETIC', 'records':rows}
        self.inputs['staging'].write_text(canonical(self.draft))
        self.payload = {'schema_version':'oxford-mock-transcription-v1',
            'batch_id':'MOCK-SYNTHETIC', 'source_type':'publisher_mock',
            'source_id':'OXFORD-M2-2025-26-C-SET1', 'publisher':'Oxford',
            'session':'2025/26', 'paper':'C Set 1', 'module':'M2', 'language':'zh-Hant',
            'staging_sha256':sha(self.inputs['staging']),
            'sources':{k:{'sha256':sha(self.inputs[k]),'page_count':1} for k in ('pp','ms')},
            'records':[{**r,'question_number':str(i), 'question_text_original':f'合成測試 {i}：求 {i}+1。',
                'publisher_ms_original':f'{i}+1={i+1}。[5分]', 'ms_evidence_level':'full_publisher_ms',
                'primary_type':'向量','tags':['algebra'],
                'review':{k:True for k in ('question','subparts','formula','marks','figures','solution')},
                'review_notes':'Synthetic evidence only, not real publisher text.',
                'requires_figure':False,'issues':[]} for i,r in enumerate(rows,1)]}
        self.save()

    def save(self):
        self.payload.pop('transcription_digest',None)
        self.payload['transcription_digest'] = hashlib.sha256(canonical(self.payload).encode()).hexdigest()
        self.inputs['proposal'].write_text(canonical(self.payload))

    def inspect(self):
        return inspect_proposal(self.inputs,self.config)

    def test_valid_source_preserves_identity_and_waits_for_exact_approval(self):
        result = self.inspect()
        self.assertIsInstance(result,dict)
        self.assertEqual(result['status'],'AWAITING_TRANSCRIPTION_APPROVAL')
        self.assertIn(self.payload['transcription_digest'],result['required_approval'])
        self.assertEqual(result['record_count'],13)

    def test_outline_and_missing_are_not_approval_eligible(self):
        for level in ('outline','missing'):
            with self.subTest(level=level):
                self.payload['records'][0]['ms_evidence_level']=level
                self.save()
                result=self.inspect()
                self.assertIsInstance(result,dict)
                self.assertEqual(result['status'],'REVIEW_REQUIRED')
                self.assertTrue(result['issues'])

    def test_source_change_rejected_even_if_proposal_digest_valid(self):
        self.inputs['ms'].write_bytes(self.inputs['ms'].read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'identity'):
            self.inspect()

    def test_order_and_difficulty_cannot_silently_change(self):
        original=copy.deepcopy(self.payload)
        for change in ('order','difficulty'):
            with self.subTest(change=change):
                self.payload=copy.deepcopy(original)
                if change=='order': self.payload['records'].reverse()
                else: self.payload['records'][0]['difficulty_proposal']=4
                self.save()
                with self.assertRaises(ValueError): self.inspect()

    def test_unreviewed_content_and_needed_figure_block(self):
        self.payload['records'][0]['review']['solution']=False
        self.payload['records'][1]['requires_figure']=True
        self.save()
        result=self.inspect()
        self.assertIsInstance(result,dict)
        self.assertEqual(result['status'],'REVIEW_REQUIRED')

    def test_tampered_digest_rejected(self):
        self.payload['records'][0]['question_text_original']='changed'
        self.inputs['proposal'].write_text(canonical(self.payload))
        with self.assertRaisesRegex(ValueError,'digest'): self.inspect()

    def test_profile_cannot_claim_hkdse(self):
        self.payload['source_type']='hkdse'
        self.save()
        with self.assertRaises(ValueError): self.inspect()

    def test_boolean_marks_and_page_out_of_range_rejected(self):
        original=copy.deepcopy(self.payload)
        for key,value in (('marks',True),('question_pages',[2])):
            with self.subTest(key=key):
                self.payload=copy.deepcopy(original)
                self.payload['records'][0][key]=value
                self.save()
                with self.assertRaises(ValueError): self.inspect()

    def test_no_canonical_without_exact_approval(self):
        with self.assertRaises(ValueError):
            build_package(self.inputs,'APPROVED',self.root/'data/staging/package',self.config)
