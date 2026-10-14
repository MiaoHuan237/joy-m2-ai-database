import fcntl
import json
from pathlib import Path
import sqlite3
import tempfile
import unittest

from joy_m2.ingest.automation import run_cycle


class AutoIngestionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.inputs = self.root / 'incoming'
        self.inputs.mkdir()
        self.config = self.root / 'config.json'
        self.payload = {'inventory_roots': [str(self.inputs)], 'receipts': [], 'jobs': []}

    def run_cycle(self):
        self.config.write_text(json.dumps(self.payload))
        return run_cycle(self.config, self.root)

    def draft(self, name='A'):
        path = self.inputs / (name + '.json')
        path.write_text(json.dumps({'batch_id': name, 'records': [{'question_text_original': 'x'}]}))
        return path

    def test_discovery_and_no_change_do_not_process_twice(self):
        self.draft()
        first = self.run_cycle()
        self.assertEqual(first.get('discovered'), 1)
        self.assertEqual(first['inventory'][0]['record_count'], 1)
        second = self.run_cycle()
        self.assertTrue(second['no_change'])
        self.assertEqual(second['processed'], 0)
        self.assertEqual(second['model_calls'], 0)

    def test_duplicate_files_share_content_not_new_questions(self):
        path = self.draft()
        (self.inputs / 'copy.json').write_bytes(path.read_bytes())
        report = self.run_cycle()
        self.assertEqual(report.get('unique_contents'), 1)
        self.assertIsNone(report['new_questions'])

    def test_changes_and_missing_file_are_visible(self):
        path = self.draft()
        self.run_cycle()
        path.write_text('{"batch_id":"A","records":[]}')
        self.assertEqual(self.run_cycle().get('changed'), 1)
        path.unlink()
        self.assertEqual(self.run_cycle()['missing'], 1)

    def test_bad_json_isolated_from_good_file(self):
        self.draft()
        (self.inputs / 'bad.json').write_text('{')
        report = self.run_cycle()
        self.assertEqual(report.get('discovered'), 2)
        self.assertEqual(sum(bool(x['error']) for x in report['inventory']), 1)

    def test_unsupported_profile_review_is_durable(self):
        path = self.draft()
        self.payload['jobs'] = [{'source_id': 'A', 'kind': 'structured_draft', 'inputs': {'staging': str(path)}}]
        first = self.run_cycle()
        self.assertEqual(first.get('pending_review'), 1)
        self.assertEqual(first['jobs'][0]['result']['status'], 'REVIEW_REQUIRED')
        second = self.run_cycle()
        self.assertEqual(second['processed'], 0)
        with sqlite3.connect(self.root / 'data/staging/auto-ingestion/state.sqlite3') as db:
            self.assertEqual(db.execute('SELECT count(*) FROM jobs').fetchone()[0], 1)

    def test_missing_input_retries_three_times_then_waits(self):
        self.payload['jobs'] = [{'source_id': 'A', 'kind': 'structured_draft', 'inputs': {'staging': str(self.inputs/'absent.json')}}]
        for _ in range(3):
            self.assertEqual(self.run_cycle().get('processed'), 1)
        self.assertEqual(self.run_cycle()['processed'], 0)
        self.draft('absent')
        self.assertEqual(self.run_cycle()['processed'], 1)

    def test_repository_lock_prevents_second_runner(self):
        runtime = self.root / 'data/staging/auto-ingestion'
        runtime.mkdir(parents=True)
        with (runtime/'cycle.lock').open('a') as handle:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.assertEqual(self.run_cycle().get('status'), 'BUSY')
        self.assertNotEqual(self.run_cycle()['status'], 'BUSY')

    def test_symlink_runtime_rejected_without_touching_target(self):
        stage = self.root/'data/staging'
        stage.mkdir(parents=True)
        (stage/'auto-ingestion').symlink_to(self.inputs, target_is_directory=True)
        with self.assertRaises(ValueError):
            self.run_cycle()
        self.assertEqual(list(self.inputs.iterdir()), [])

    def test_same_source_twice_in_config_rejected(self):
        path = self.draft()
        job = {'source_id': 'A', 'kind': 'structured_draft', 'inputs': {'staging': str(path)}}
        self.payload['jobs'] = [job, job]
        with self.assertRaises(ValueError):
            self.run_cycle()

    def test_no_arbitrary_processor_execution(self):
        path = self.draft()
        self.payload['jobs'] = [{'source_id': 'A', 'kind': 'shell', 'inputs': {'staging': str(path)}, 'command': 'touch forbidden'}]
        report = self.run_cycle()
        self.assertEqual(report.get('pending_review'), 1)
        self.assertFalse((self.root/'forbidden').exists())

    def test_draft_assessment_keeps_outline_distinct_from_complete_ms(self):
        path = self.draft()
        path.write_text(json.dumps({'batch_id':'A','records':[{'question_text_original':'x', 'solution_outline_zh':'summary','final_answer':'1'}]}))
        self.payload['jobs'] = [{'source_id':'A','kind':'structured_draft','inputs':{'staging':str(path)}}]
        result = self.run_cycle()['jobs'][0]['result']
        self.assertEqual(result.get('record_count'), 1)
        self.assertEqual(result['official_ms_verified_count'], 0)
        self.assertEqual(result['answer_outline_count'], 1)

    def test_inventory_baseline_does_not_create_unreviewed_jobs(self):
        self.draft()
        result = self.run_cycle()
        self.assertEqual(result['processed'], 0)
        self.assertEqual(result['inventory'][0]['state'], 'DISCOVERED_NOT_APPROVED')

    def test_new_pdf_detected_without_parser_or_model(self):
        (self.inputs/'source.pdf').write_bytes(b'%PDF test inventory only')
        report = self.run_cycle()
        self.assertEqual(report['discovered'], 1)
        self.assertEqual(report['inventory'][0]['state'], 'SOURCE_NOT_PARSED')
        self.assertIsNone(report['inventory'][0]['record_count'])
