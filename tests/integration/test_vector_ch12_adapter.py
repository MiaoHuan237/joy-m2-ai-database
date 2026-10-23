"""Independent small ZIP fixtures; no production-generated expected bytes."""
import hashlib
import io
from pathlib import Path
import stat
import struct
import tempfile
import unittest
import warnings
import json
import shutil
import sqlite3
import zipfile
from unittest.mock import patch

from joy_m2.ingest import archive, vector_ch12 as profile
from joy_m2.ingest.adapter_models import MmdAdapterBlockedError
from joy_m2.config import PipelineConfig
from joy_m2.errors import ConfigurationError, OutputConflictError, InputMissingError
from joy_m2.ingest.writer_profiles import atomic_rename_no_replace
from tests.fixtures.vector_ch12.mapping_fixture import fixture


def sha(data):
    return hashlib.sha256(data).hexdigest()


def zip_bytes(entries, compression=zipfile.ZIP_STORED):
    stream = io.BytesIO()
    with warnings.catch_warnings():
        warnings.simplefilter('ignore', UserWarning)
        with zipfile.ZipFile(stream, 'w', compression=compression) as z:
            for name, content in entries:
                z.writestr(name, content)
    return stream.getvalue()


class DualInventoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.paths = [self.root/'textbook.zip', self.root/'answers.zip']
        self.contents = [b'1. question\r\n', b'1. answer\n']
        self.mapping = {'packages': []}
        for role, path, content in zip(('textbook', 'answers'), self.paths, self.contents):
            data = zip_bytes([('source.mmd', content), ('images/shared.png', role.encode())])
            path.write_bytes(data)
            self.mapping['packages'].append(dict(role=role, zip_sha256=sha(data),
                zip_size_bytes=len(data), selected_member='source.mmd',
                member_sha256=sha(content), member_size_bytes=len(content)))

    def replace(self, entries, compression=zipfile.ZIP_STORED):
        data = zip_bytes(entries, compression)
        self.paths[0].write_bytes(data)
        self.mapping['packages'][0].update(zip_sha256=sha(data), zip_size_bytes=len(data))

    def read(self):
        return profile._read_packages(*self.paths, self.mapping)

    def blocked(self, code=None):
        with self.assertRaises(MmdAdapterBlockedError) as raised:
            self.read()
        if code:
            self.assertIn(code, [x.code for x in raised.exception.issues])

    def test_distinct_roles_preserve_same_named_members_and_sources(self):
        before = [p.read_bytes() for p in self.paths]
        self.assertEqual(self.read(), {('textbook', 'source.mmd'): self.contents[0],
            ('answers', 'source.mmd'): self.contents[1],
            ('textbook', 'images/shared.png'): b'textbook',
            ('answers', 'images/shared.png'): b'answers'})
        self.assertEqual([p.read_bytes() for p in self.paths], before)
        self.assertEqual(set(p.name for p in self.root.iterdir()), {'textbook.zip', 'answers.zip'})

    def test_archive_snapshot_read_is_bounded_even_after_stat(self):
        original_open = Path.open
        sizes = []
        class ReadWitness:
            def __init__(self, stream): self.stream = stream
            def __enter__(self): return self
            def __exit__(self, *args): self.stream.close()
            def read(self, size=-1):
                sizes.append(size)
                return self.stream.read(size)
        def opened(path, *args, **kwargs):
            stream = original_open(path, *args, **kwargs)
            return ReadWitness(stream) if path in self.paths else stream
        with patch.object(Path, 'open', opened):
            self.assertEqual(len(self.read()), 4)
        self.assertTrue(sizes)
        self.assertTrue(all(0 < size <= archive._ARCHIVE_LIMIT + 1 for size in sizes), sizes)

    def test_identity_changes_and_swapped_packages_rejected(self):
        self.paths.reverse()
        self.blocked('source_contract_mismatch')
        self.paths.reverse()
        for key, bad in [('zip_sha256', '0'*64), ('zip_size_bytes', 1),
                         ('member_sha256', '0'*64), ('member_size_bytes', 1)]:
            with self.subTest(key=key):
                old = self.mapping['packages'][0][key]
                self.mapping['packages'][0][key] = bad
                self.blocked('source_contract_mismatch')
                self.mapping['packages'][0][key] = old

    def test_missing_or_extra_mmd(self):
        self.replace([('images/x.png', b'x')])
        self.blocked('selection_not_unique')
        self.replace([('source.mmd', self.contents[0]), ('extra.mmd', b'x')])
        self.blocked('archive_member_unsafe')

    def test_unsafe_paths_types_and_hidden_files(self):
        for name in ['../x', '/x', 'C:/x', 'a\\b', 'a//b', '.secret', 'x.zip']:
            with self.subTest(name=name):
                self.replace([('source.mmd', self.contents[0]), (name, b'x')])
                self.blocked('archive_member_unsafe')
        for mode in [stat.S_IFLNK | 0o777, stat.S_IFIFO | 0o600, stat.S_IFREG | 0o755]:
            info = zipfile.ZipInfo('unsafe'); info.create_system = 3
            info.external_attr = mode << 16
            self.replace([('source.mmd', self.contents[0]), (info, b'x')])
            self.blocked('archive_member_unsafe')

    def test_duplicate_nfc_and_casefold_collisions(self):
        for names in [('a.png', 'a.png'), ('é.png', 'e\u0301.png'), ('A.png', 'a.png')]:
            with self.subTest(names=names):
                self.replace([('source.mmd', self.contents[0]), *[(n, b'x') for n in names]])
                self.blocked('archive_member_unsafe')

    def test_metadata_is_ignored_but_validated(self):
        self.replace([('source.mmd', self.contents[0]), ('.DS_Store', b'x'),
                      ('__MACOSX/._source.mmd', b'x')])
        self.assertEqual(self.read()[('textbook', 'source.mmd')], self.contents[0])
        self.assertNotIn(('textbook', '.DS_Store'), self.read())
        self.replace([('source.mmd', self.contents[0]), ('__MACOSX/../escape', b'x')])
        self.blocked('archive_member_unsafe')

    def test_crc_encryption_compression_and_invalid_zip(self):
        original = self.paths[0].read_bytes()
        for kind in ['crc', 'encryption', 'structure']:
            data = bytearray(original)
            if kind == 'crc':
                start = 30 + len('source.mmd')
                data[start] ^= 1
            elif kind == 'encryption':
                struct.pack_into('<H', data, 6, 1)
                offset = data.index(b'PK\x01\x02')
                struct.pack_into('<H', data, offset + 8, 1)
            else:
                data = bytearray(b'not a zip')
            self.paths[0].write_bytes(data)
            self.mapping['packages'][0].update(zip_sha256=sha(data), zip_size_bytes=len(data))
            self.blocked('archive_integrity_invalid')
        self.replace([('source.mmd', self.contents[0])], zipfile.ZIP_BZIP2)
        self.blocked('archive_integrity_invalid')

    def test_mmd_encoding(self):
        for content in [b'\xff', b'\xef\xbb\xbf1. text']:
            self.replace([('source.mmd', content)])
            self.mapping['packages'][0].update(member_sha256=sha(content), member_size_bytes=len(content))
            self.blocked('source_contract_mismatch')

    def test_combined_count_limit_and_inventory_precedes_reads(self):
        # Scaled limits exercise exact boundary without 100 MiB test allocations.
        with patch.object(archive, '_MEMBER_COUNT_LIMIT', 4):
            self.assertEqual(len(self.read()), 4)
        with patch.object(archive, '_MEMBER_COUNT_LIMIT', 3), \
             patch.object(archive, '_read_member', side_effect=AssertionError('read too early')):
            self.blocked('archive_integrity_invalid')

    def test_size_and_ratio_boundaries(self):
        total = sum(len(c) for c in self.contents) + len(b'textbookanswers')
        for constant, exact in [('_TOTAL_LIMIT', total),
                                ('_ARCHIVE_LIMIT', max(p.stat().st_size for p in self.paths)),
                                ('_MMD_LIMIT', len(self.contents[0])), ('_IMAGE_LIMIT', 8),
                                ('_RATIO_LIMIT', 1)]:
            with self.subTest(constant=constant), patch.object(archive, constant, exact):
                self.assertEqual(len(self.read()), 4)
            with self.subTest(over=constant), patch.object(archive, constant, exact - 1):
                self.blocked('archive_integrity_invalid')


class _ProposalCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.config = PipelineConfig(self.root)
        self.config.staging_root.mkdir(parents=True)
        formal = self.config.releases_root/'V1.23/Joy_M2_Complete_Question_DB_V1_23.sqlite3'
        formal.parent.mkdir(parents=True)
        shutil.copyfile(Path(__file__).resolve().parents[2]/'releases/V1.23'/formal.name, formal)
        self.mapping, self.members = fixture()
        self.paths = [self.root/'textbook.zip', self.root/'answers.zip']
        for role, path, declared in zip(('textbook', 'answers'), self.paths, self.mapping['packages']):
            data = zip_bytes([('source.mmd', self.members[(role, 'source.mmd')])])
            path.write_bytes(data)
            declared.update(zip_sha256=sha(data), zip_size_bytes=len(data))
        self.draft = self.root/'draft.json'; self.save()
        self.output = self.config.staging_root/'proposal'

    def save(self):
        self.raw = json.dumps(self.mapping, ensure_ascii=False, sort_keys=True,
                              separators=(',', ':'), allow_nan=False).encode()
        self.draft.write_bytes(self.raw)

    def propose(self):
        return profile.propose_vector_ch12_mapping(*self.paths, self.draft, self.output, self.config)


class ProposalTests(_ProposalCase):
    def test_vocabulary_comes_from_configured_readonly_formal_database(self):
        uris = []
        original = sqlite3.connect
        def witnessed(database, *args, **kwargs):
            uris.append(database)
            return original(database, *args, **kwargs)
        with patch.object(profile.sqlite3, 'connect', side_effect=witnessed):
            self.propose()
        expected = (self.config.releases_root/'V1.23/Joy_M2_Complete_Question_DB_V1_23.sqlite3').as_uri()
        self.assertEqual(uris, [expected + '?mode=ro'])

    def test_exact_files_json_hashes_and_readable_source_paths(self):
        result = self.propose()
        self.assertIsInstance(result, profile.VectorCh12Proposal)
        self.assertEqual(set(p.name for p in self.output.iterdir()),
                         {'source_mapping.json', 'SOURCE_MAPPING_REVIEW.md'})
        self.assertEqual(result.mapping_path.read_bytes(), self.raw)
        self.assertEqual(result.mapping_sha256, sha(self.raw))
        expected = json.dumps(dict(profile='OSM-M2B12-C-E', packages=self.mapping['packages']),
            ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()
        self.assertEqual(result.input_binding_sha256, sha(expected))
        self.assertEqual(result.candidate_count, 2)
        review = result.review_path.read_text()
        for p in self.paths:
            self.assertIn(str(p), review); self.assertNotIn(str(p).encode(), self.raw)
        self.assertIn(result.mapping_sha256, review)
        self.assertIn('final_answers_only', review)

    def test_double_run_different_roots_exact_mapping(self):
        first = self.propose()
        self.output = self.config.staging_root/'second'
        second = self.propose()
        self.assertIsInstance(first, profile.VectorCh12Proposal)
        self.assertEqual(first.mapping_sha256, second.mapping_sha256)
        self.assertEqual(first.review_path.read_bytes(), second.review_path.read_bytes())


class PublicationSafetyTests(_ProposalCase):
    def test_root_formal_and_existing_destinations(self):
        for dest in [self.config.staging_root, self.config.releases_root/'no']:
            self.output = dest
            with self.assertRaises(ConfigurationError): self.propose()
        self.output = self.config.staging_root/'proposal'; self.output.mkdir()
        (self.output/'sentinel').write_bytes(b'keep')
        with self.assertRaises(OutputConflictError): self.propose()
        self.assertEqual((self.output/'sentinel').read_bytes(), b'keep')

    def test_argument_missing_input_and_symlink_boundaries(self):
        with self.assertRaises(TypeError):
            profile.propose_vector_ch12_mapping(str(self.paths[0]), self.paths[1], self.draft,
                                                self.output, self.config)
        self.output.symlink_to(self.root/'not-created')
        with self.assertRaises((OutputConflictError, ConfigurationError)): self.propose()
        self.output = self.config.staging_root/'another'
        self.paths[0] = self.root/'absent.zip'
        with self.assertRaises(InputMissingError): self.propose()

    def test_io_failure_and_destination_race_leave_no_own_temp(self):
        before = {p: p.read_bytes() for p in [*self.paths, self.draft]}
        with patch.object(profile, 'atomic_rename_no_replace', side_effect=OSError('injected')):
            with self.assertRaises(OSError): self.propose()
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.config.staging_root.iterdir()), [])
        def racing(source, dest):
            dest.mkdir(); (dest/'sentinel').write_bytes(b'other actor')
            atomic_rename_no_replace(source, dest)
        with patch.object(profile, 'atomic_rename_no_replace', side_effect=racing):
            with self.assertRaises(OutputConflictError): self.propose()
        self.assertEqual((self.output/'sentinel').read_bytes(), b'other actor')
        self.assertEqual(list(self.config.staging_root.iterdir()), [self.output])
        self.assertEqual({p: p.read_bytes() for p in before}, before)

    def test_input_change_during_temp_write_prevents_publication(self):
        original = Path.write_bytes
        def write(path, data):
            result = original(path, data)
            if path.name == 'SOURCE_MAPPING_REVIEW.md':
                original(self.paths[1], b'changed input')
            return result
        with patch.object(Path, 'write_bytes', write):
            with self.assertRaises(MmdAdapterBlockedError): self.propose()
        self.assertFalse(self.output.exists())
        self.assertEqual(list(self.config.staging_root.iterdir()), [])

    def test_cleanup_does_not_remove_replaced_private_directory(self):
        foreign = []
        def replaced(source, destination):
            source.rename(source.with_name(source.name + '-moved'))
            source.mkdir(); (source/'sentinel').write_bytes(b'foreign')
            foreign.append(source)
            raise OSError('private directory replaced')
        with patch.object(profile, 'atomic_rename_no_replace', side_effect=replaced):
            with self.assertRaises(OSError): self.propose()
        self.assertTrue((foreign[0]/'sentinel').exists(), 'must never delete a different owner')
        self.assertEqual((foreign[0]/'sentinel').read_bytes(), b'foreign')


class DiagnosticTests(_ProposalCase):
    def test_inspectable_question_errors_are_collected_before_publication(self):
        self.mapping['questions'][0]['metadata']['tags'] = ['not-controlled']
        self.mapping['questions'][1]['metadata']['primary_type'] = 'not-controlled'
        self.save()
        with self.assertRaises(MmdAdapterBlockedError) as raised: self.propose()
        self.assertEqual(len(raised.exception.issues), 2)
        self.assertEqual({i.proposed_question_id for i in raised.exception.issues},
                         {q['question_id'] for q in self.mapping['questions']})
        self.assertFalse(self.output.exists())

    def test_invalid_span_structure_uses_parse_diagnostic(self):
        span = self.mapping['questions'][0]['question_pieces'][1]['span']
        span['start_byte'] = True
        self.save()
        with self.assertRaises(MmdAdapterBlockedError) as raised: self.propose()
        self.assertEqual(raised.exception.issues[0].code, 'mmd_parse_failed')

    def test_frozen_codes_for_content_selection_and_count(self):
        from copy import deepcopy
        original = deepcopy(self.mapping)
        mutations = [
            ('selection_not_unique', lambda m: m['questions'][1].update(question_id=m['questions'][0]['question_id'])),
            ('candidate_count_mismatch', lambda m: m['unit_dispositions'][0].update(disposition='proposed_selection')),
            ('mmd_parse_failed', lambda m: m['shared_conditions'][0]['applies_to'].pop()),
            ('mmd_parse_failed', lambda m: m['questions'][0]['answer_evidence'].update(covered_subparts=[])),
        ]
        for expected, change in mutations:
            self.mapping = deepcopy(original); change(self.mapping); self.save()
            with self.subTest(expected=expected), self.assertRaises(MmdAdapterBlockedError) as raised:
                self.propose()
            self.assertEqual(raised.exception.issues[0].code, expected)
            self.assertNotIn(str(self.root), raised.exception.issues[0].evidence)

    def test_archive_limit_short_circuits_content_defect(self):
        self.mapping['questions'][0]['question_pieces'][1]['span']['raw_sha256'] = '0'*64
        self.save()
        with patch.object(archive, '_MEMBER_COUNT_LIMIT', 1):
            with self.assertRaises(MmdAdapterBlockedError) as raised: self.propose()
        self.assertEqual({i.code for i in raised.exception.issues}, {'archive_integrity_invalid'})
        self.assertFalse(self.output.exists())

    def test_bad_image_and_malformed_json_never_publish(self):
        self.mapping['unselected_image_members'] = [dict(package_role='textbook', member='absent.png',
            sha256='a'*64, reason='missing')]; self.save()
        with self.assertRaises(MmdAdapterBlockedError) as raised: self.propose()
        self.assertEqual(raised.exception.issues[0].code, 'image_binding_invalid')
        for raw in [b'{', b'\xff', b'\xef\xbb\xbf{}', b'{"x":1,"x":2}', b'{"x":NaN}']:
            self.draft.write_bytes(raw)
            with self.assertRaises(MmdAdapterBlockedError) as raised: self.propose()
            self.assertEqual(raised.exception.issues[0].code, 'source_contract_mismatch')
        self.assertFalse(self.output.exists())
