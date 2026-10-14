import json
import hashlib
from pathlib import Path
import tempfile
import shutil
import unittest
from unittest.mock import patch

from joy_m2.ingest.automation import run_cycle
from tests.integration.test_v123_candidate import _make_named_package
from tests.unit.test_hkdse_pdf_adapter import AdapterCase


class AutoIngestionIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        # Isolated test copy; never edit the formal source.
        self.repo = Path(__file__).resolve().parents[2]
        shutil.copytree(self.repo/'releases/V1.22', self.root/'releases/V1.22')
        self.package = _make_named_package(self.root, 'A')
        self.config = self.root/'config.json'
        self.approval = self.root/'approval.txt'
        self.settings = {'inventory_roots': [], 'receipts': [],
                         'jobs': [{'source_id': 'TASK10-A', 'kind': 'v123_canonical',
                                   'inputs': {'package': str(self.package)},
                                   'import_approval': str(self.approval)}]}

    def cycle(self):
        self.config.write_text(json.dumps(self.settings))
        return run_cycle(self.config, self.root)

    def ready(self):
        first = self.cycle()
        result = first['jobs'][0]['result']
        self.assertEqual(result['status'], 'AWAITING_IMPORT_APPROVAL', result)
        return result

    def test_real_preflight_requires_exact_approval(self):
        ready = self.ready()
        self.assertEqual(ready['report']['new_candidate_count'], 1)
        self.assertEqual(ready['report']['parent_candidate_digest'], 'ea3b7db78210e045761784a2e415387c1b17f13b5aedde484ca2ae248a45eec7')
        self.assertFalse(list((self.root/'data/staging/auto-ingestion').glob('candidates/*')))

    def test_approval_resume_then_repeat_is_not_another_append(self):
        ready = self.ready()
        self.approval.write_text(ready['required_approval'])
        accepted = self.cycle()['jobs'][0]['result']
        self.assertEqual(accepted['status'], 'ACCEPTED', accepted)
        self.assertEqual(accepted['verification_status'], 'PASS')
        repeated = self.cycle()['jobs'][0]['result']
        self.assertEqual(repeated['candidate_digest'], accepted['candidate_digest'])
        self.assertEqual(repeated['status'], 'ACCEPTED')
        self.assertEqual(len(list((self.root/'data/staging/auto-ingestion/candidates').iterdir())), 1)


class AutoTranscriptionTests(AdapterCase):
    def setUp(self):
        super().setUp()
        repo = Path(__file__).resolve().parents[2]
        shutil.copytree(repo/'releases/V1.22', self.root/'releases/V1.22')
        self.settings_path = self.root/'runner.json'
        self.approval_path = self.root/'transcription-approval.txt'
        self.settings = {'inventory_roots': [], 'receipts': [], 'jobs': [{
            'source_id': 'JOY-M2-HKDSE-2012-PP-MS', 'kind': 'hkdse_pdf',
            'inputs': {'staging': str(self.staging), 'pp': str(self.pp), 'ms': str(self.ms),
                       'pass_a': str(self.pass_a), 'pass_b': str(self.pass_b)},
            'transcription_approval': str(self.approval_path)}]}
        self.settings_path.write_text(json.dumps(self.settings))

    def valid_taxonomy(self):
        staging = json.loads(self.staging.read_text())
        staging['records'][0]['module'] = '向量'
        staging['records'][0]['proposed_tags'] = ['algebra']
        self.staging.write_text(json.dumps(staging))
        for path in (self.pass_a, self.pass_b):
            payload = json.loads(path.read_text())
            payload['staging_sha256'] = hashlib.sha256(self.staging.read_bytes()).hexdigest()
            path.write_text(json.dumps(payload))

    def test_transcription_waits_then_resumes_without_reextracting(self):
        self.valid_taxonomy()
        first = run_cycle(self.settings_path, self.root)['jobs'][0]['result']
        self.assertEqual(first['status'], 'AWAITING_TRANSCRIPTION_APPROVAL', first)
        before = Path(first['proposal_path']).read_bytes()
        self.approval_path.write_text(first['required_approval'])
        after = run_cycle(self.settings_path, self.root)['jobs'][0]['result']
        self.assertEqual(after['status'], 'REVIEW_REQUIRED', after)
        self.assertIn('collision_candidate_id', after['report']['blocking_errors'])
        self.assertEqual(before, Path(first['proposal_path']).read_bytes())

    def test_cached_proposal_must_match_current_source_pass_payload(self):
        from joy_m2.ingest.automation import canonical
        self.valid_taxonomy()
        first = run_cycle(self.settings_path, self.root)['jobs'][0]['result']
        path = Path(first['proposal_path'])
        payload = json.loads(path.read_text())
        payload.pop('transcription_digest')
        payload['records'][0]['question_text_original'] += ' changed condition'
        payload['transcription_digest'] = hashlib.sha256(canonical(payload).encode()).hexdigest()
        path.write_text(canonical(payload))
        result = run_cycle(self.settings_path, self.root)['jobs'][0]['result']
        self.assertEqual(result['status'], 'FAILED')
        self.assertIn('proposal', result['reason'])

    def test_cached_package_must_match_approved_proposal(self):
        self.valid_taxonomy()
        first = run_cycle(self.settings_path, self.root)['jobs'][0]['result']
        self.approval_path.write_text(first['required_approval'])
        run_cycle(self.settings_path, self.root)
        package = next((self.root/'data/staging/auto-ingestion/packages').iterdir())
        target = package/'records/candidates.json'
        target.write_bytes(target.read_bytes() + b' ')
        from joy_m2.ingest.automation_v123 import V123Operations
        operations = V123Operations(self.root.resolve(), (self.root/'data/staging/auto-ingestion').resolve(), [])
        with self.assertRaisesRegex(ValueError, 'canonical'):
            operations.transcription(self.settings['jobs'][0])

    def test_local_issue_cannot_be_cleared_by_approval(self):
        payload = json.loads(self.pass_b.read_text())
        payload['records'][0]['official_ms_original'] = ''
        self.pass_b.write_text(json.dumps(payload))
        result = run_cycle(self.settings_path, self.root)['jobs'][0]['result']
        self.assertEqual(result['status'], 'REVIEW_REQUIRED', result)
        self.assertTrue(result['issues'])

    def test_unknown_taxonomy_is_reviewed_before_transcription_approval(self):
        result = run_cycle(self.settings_path, self.root)['jobs'][0]['result']
        self.assertEqual(result['status'], 'REVIEW_REQUIRED')
        self.assertIn('taxonomy_issues', result)

    def test_unchanged_proposal_next_cycle_skips_consolidation(self):
        self.valid_taxonomy()
        run_cycle(self.settings_path, self.root)
        with patch('joy_m2.ingest.hkdse_pdf_adapter.propose_hkdse_pdf_transcription') as proposal:
            result = run_cycle(self.settings_path, self.root)
        self.assertEqual(result['processed'], 0)
        proposal.assert_not_called()
        self.assertTrue(result['no_change'])

class AutoIngestionRecoveryTests(AutoIngestionIntegrationTests):
    def second_job(self):
        package = _make_named_package(self.root, 'B')
        approval = self.root/'approval-b.txt'
        self.settings['jobs'].append({'source_id':'TASK10-B', 'kind':'v123_canonical',
            'inputs':{'package':str(package)}, 'import_approval':str(approval)})
        return approval

    def test_receipt_failure_blocks_second_writer_and_recovers_original(self):
        from joy_m2.ingest import automation_v123 as backend
        second = self.second_job()
        waiting = self.cycle()['jobs']
        self.approval.write_text(waiting[0]['result']['required_approval'])
        second.write_text(waiting[1]['result']['required_approval'])
        original = backend.save_json
        def fail_receipt(path, value):
            if Path(path).parent.name == 'receipts':
                raise OSError('simulated receipt disk error')
            return original(path, value)
        with patch.object(backend, 'save_json', side_effect=fail_receipt):
            broken = self.cycle()
        runtime = self.root/'data/staging/auto-ingestion'
        self.assertEqual(len(list((runtime/'candidates').iterdir())), 1)
        self.assertNotEqual(broken['jobs'][1]['result']['status'], 'ACCEPTED')
        before = {str(p):p.read_bytes() for p in (runtime/'candidates').rglob('*') if p.is_file()}
        restored = self.cycle()
        self.assertEqual(restored['jobs'][0]['result']['status'], 'ACCEPTED')
        self.assertEqual(restored['jobs'][1]['result']['status'], 'AWAITING_IMPORT_APPROVAL')
        self.assertEqual(before, {str(p):p.read_bytes() for p in (runtime/'candidates').rglob('*') if p.is_file()})

    def test_later_job_approval_request_uses_new_parent_in_same_cycle(self):
        self.second_job()
        waiting = self.cycle()['jobs']
        self.approval.write_text(waiting[0]['result']['required_approval'])
        results = self.cycle()['jobs']
        self.assertEqual(results[0]['result']['status'], 'ACCEPTED')
        self.assertEqual(results[1]['result']['report']['parent_candidate_digest'],
                         results[0]['result']['candidate_digest'])

    def test_post_verification_change_is_not_cached_as_verified(self):
        from joy_m2.ingest.automation_v123 import V123Operations
        ready = self.ready()
        self.approval.write_text(ready['required_approval'])
        original = V123Operations.process
        def tamper_after_verify(operations, job, revision):
            result = original(operations, job, revision)
            path = Path(result['candidate_dir'])/operations.contract.manifest_filename
            path.write_bytes(path.read_bytes()+b'corrupt')
            return result
        with patch.object(V123Operations, 'process', tamper_after_verify):
            self.cycle()
        result = self.cycle()['jobs'][0]['result']
        self.assertEqual(result['status'], 'FAILED', result)

    def test_unconfigured_operational_receipt_blocks_stale_parent(self):
        location = self.root/'data/staging/task13-v123-new/REAL_BATCH_IMPORT_RECEIPT.json'
        location.parent.mkdir(parents=True)
        location.write_text('{}')
        result = self.cycle()['jobs'][0]['result']
        self.assertEqual(result['status'], 'FAILED')
        self.assertIn('receipt', result['reason'])
    def test_wrong_approval_does_not_write(self):
        self.ready()
        self.approval.write_text('USER APPROVED IMPORT BATCH TASK10-A ' + '0'*64 + ' V1.23 PARENT ' + '0'*64)
        result = self.cycle()['jobs'][0]['result']
        self.assertEqual(result['status'], 'AWAITING_IMPORT_APPROVAL', result)
        self.assertIn('approval', result['reason'])
        self.assertFalse(list((self.root/'data/staging/auto-ingestion').glob('candidates/*')))

    def test_unreceipted_success_recovered_without_rebuild(self):
        ready = self.ready()
        self.approval.write_text(ready['required_approval'])
        accepted = self.cycle()['jobs'][0]['result']
        self.assertEqual(accepted['status'], 'ACCEPTED', accepted)
        runtime = self.root/'data/staging/auto-ingestion'
        before = {str(p):p.read_bytes() for p in (runtime/'candidates').rglob('*') if p.is_file()}
        # Simulate death after existing writer atomically published, before receipts/journal.
        Path(accepted['receipt_path']).unlink()
        (runtime/'state.sqlite3').unlink()
        recovered = self.cycle()['jobs'][0]['result']
        self.assertEqual(recovered['candidate_digest'], accepted['candidate_digest'])
        self.assertTrue(recovered['recovered_existing_output'])
        self.assertEqual(before, {str(p):p.read_bytes() for p in (runtime/'candidates').rglob('*') if p.is_file()})

    def test_changed_accepted_package_is_not_reimported(self):
        ready = self.ready()
        self.approval.write_text(ready['required_approval'])
        self.assertEqual(self.cycle()['jobs'][0]['result']['status'], 'ACCEPTED')
        (self.package/'unexpected.txt').write_text('changed')
        result = self.cycle()['jobs'][0]['result']
        self.assertIn(result['status'], ('REVIEW_REQUIRED', 'FAILED'))
        self.assertEqual(len(list((self.root/'data/staging/auto-ingestion/candidates').iterdir())), 1)
