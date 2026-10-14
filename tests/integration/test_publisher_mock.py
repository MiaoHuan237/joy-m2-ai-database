from pathlib import Path
import unittest
from unittest.mock import patch
from joy_m2.ingest.automation import canonical, read_json, run_cycle
from joy_m2.ingest.publisher_mock import build_package
from tests.unit import test_publisher_mock as fixture


class PublisherFlowTests(unittest.TestCase):
    setUp=fixture.PublisherMockTests.setUp
    save=fixture.PublisherMockTests.save
    def settings(self):
        path=self.root/'runner.json'
        path.write_text(canonical({'inventory_roots':[],'receipts':[], 'jobs':[{
            'source_id':'MOCK-SYNTHETIC','kind':'publisher_mock',
            'inputs':{k:str(v) for k,v in self.inputs.items()},
            'transcription_approval':str(self.root/'transcription-approval.txt'),
            'import_approval':str(self.root/'import-approval.txt')}]}))
        return path

    def cycle(self):
        return run_cycle(self.settings(),self.root)

    def test_exact_approval_continuation_and_real_existing_writer_idempotence(self):
        waiting=self.cycle()['jobs'][0]['result']
        self.assertEqual(waiting['status'],'AWAITING_TRANSCRIPTION_APPROVAL',waiting)
        self.assertFalse((self.root/'data/staging/auto-ingestion/packages').exists())
        (self.root/'transcription-approval.txt').write_text(waiting['required_approval'])
        ready=self.cycle()['jobs'][0]['result']
        self.assertEqual(ready['status'],'AWAITING_IMPORT_APPROVAL',ready)
        self.assertEqual(ready['report']['new_candidate_count'],13)
        (self.root/'import-approval.txt').write_text(ready['required_approval'])
        accepted=self.cycle()['jobs'][0]['result']
        self.assertEqual(accepted['status'],'ACCEPTED',accepted)
        self.assertEqual(accepted['verification_status'],'PASS')
        repeated=self.cycle()['jobs'][0]['result']
        self.assertEqual(accepted['candidate_digest'],repeated['candidate_digest'])
        self.assertTrue(self.cycle()['no_change'])

    def test_outline_cannot_pass_with_approval_and_unchanged_run_skips(self):
        self.payload['records'][0]['ms_evidence_level']='outline'
        self.save()
        (self.root/'transcription-approval.txt').write_text(
            f"USER APPROVED PDF TRANSCRIPTION BATCH MOCK-SYNTHETIC {self.payload['transcription_digest']}")
        result=self.cycle()['jobs'][0]['result']
        self.assertEqual(result['status'],'REVIEW_REQUIRED',result)
        self.assertIn('issues',result)
        with patch('joy_m2.ingest.publisher_mock.inspect_proposal',side_effect=AssertionError('must skip')):
            self.assertTrue(self.cycle()['no_change'])

    def test_path_independent_canonical_and_publisher_provenance(self):
        waiting=self.cycle()['jobs'][0]['result']
        self.assertEqual(waiting['status'],'AWAITING_TRANSCRIPTION_APPROVAL',waiting)
        roots=[self.root/'data/staging'/n for n in ('first','second')]
        for root in roots: build_package(self.inputs,waiting['required_approval'],root,self.config)
        def files(root): return {str(p.relative_to(root)):p.read_bytes() for p in root.rglob('*') if p.is_file()}
        self.assertEqual(files(roots[0]),files(roots[1]))
        source=read_json(roots[0]/'source/source-map.json')
        self.assertEqual(source['source_type'],'publisher_mock')
        self.assertEqual(source['publisher'],'Oxford')
        rows=read_json(roots[0]/'records/candidates.json')
        self.assertEqual(rows[0]['source_id'],'OXFORD-M2-2025-26-C-SET1')
        self.assertEqual(rows[0]['solution_original'],self.payload['records'][0]['publisher_ms_original'])
        self.assertEqual(rows[0]['answer_status'],'source_provided')
        with self.assertRaises(Exception): build_package(self.inputs,waiting['required_approval'],roots[0],self.config)

    def test_receipt_failure_resumes_same_candidate_not_duplicate(self):
        from joy_m2.ingest import automation_v123 as backend
        waiting=self.cycle()['jobs'][0]['result']
        self.assertEqual(waiting['status'],'AWAITING_TRANSCRIPTION_APPROVAL',waiting)
        (self.root/'transcription-approval.txt').write_text(waiting['required_approval'])
        ready=self.cycle()['jobs'][0]['result']
        (self.root/'import-approval.txt').write_text(ready['required_approval'])
        original=backend.save_json
        def fail(path,value):
            if Path(path).parent.name=='receipts': raise OSError('synthetic interrupted receipt')
            return original(path,value)
        with patch.object(backend,'save_json',side_effect=fail):
            self.assertEqual(self.cycle()['jobs'][0]['result']['status'],'FAILED')
        result=self.cycle()['jobs'][0]['result']
        self.assertEqual(result['status'],'ACCEPTED',result)
        self.assertEqual(len(list((self.root/'data/staging/auto-ingestion/candidates').iterdir())),1)
