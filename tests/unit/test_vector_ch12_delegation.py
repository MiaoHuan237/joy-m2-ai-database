"""Independent synthetic grant evidence, never usable with the real public pin."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from joy_m2.errors import ImportApprovalError
from joy_m2.ingest import vector_ch12_delegation as subject


def raw(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':')).encode()


def digest(value):
    return sha256(value).hexdigest()


class GrantTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.scope = self.root / subject.SCOPE_RELATIVE
        self.scope.parent.mkdir(parents=True)
        self.user = b'SYNTHETIC TEST DELEGATION, NOT A REAL USER APPROVAL'
        (self.scope.parent / 'USER_AUTHORIZATION.txt').write_bytes(self.user)
        self.formal = self.root / 'releases/V1.23'
        self.formal.mkdir(parents=True)
        (self.formal/'Joy_M2_Complete_Question_DB_V1_23.sqlite3').write_bytes(b'synthetic baseline bytes')
        (self.formal/'manifest.json').write_bytes(b'synthetic manifest bytes')
        self.ids = [f'OSM-M2B12-C-EX12B-Q{i:02}' for i in range(1, 118)]
        self.record = dict(
            source_id='OSM-M2B12-C', answer_source_id='OSM-M2B12-E-ANSWERS', target='V1.24',
            user_authorization_file='USER_AUTHORIZATION.txt', user_authorization_sha256=digest(self.user),
            authorized_question_ids=self.ids, later_processing_question_ids=self.ids[14:],
            S04_exact_human_mapping={'question_ids':self.ids[:14]},
            excluded_held_ids=[f'held-{i}' for i in range(44)],
            excluded_prerequisite_ids=[f'prerequisite-{i}' for i in range(8)],
            excluded_accepted_ids=[f'accepted-{i}' for i in range(34)],
            baseline=dict(version='V1.23',record_count=677,
                sqlite_sha256=digest(b'synthetic baseline bytes'),
                manifest_sha256=digest(b'synthetic manifest bytes')),
            packages=[])
        for role in ('textbook','answers'):
            p = self.root / f'{role}.zip'
            with zipfile.ZipFile(p,'w') as z:
                z.writestr('shared-name.mmd', role.encode())
            self.record['packages'].append(dict(role=role,path=str(p),
                zip_sha256=digest(p.read_bytes()),zip_size_bytes=p.stat().st_size,
                selected_mmd=dict(member='shared-name.mmd',sha256=digest(role.encode()),size_bytes=len(role))))
        for name in ('inventory','progress'):
            p=self.root/f'{name}.json'; p.write_bytes(raw({'fixture':name}))
            self.record[f'{name}_path']=str(p)
            self.record[f'{name}_sha256']=digest(p.read_bytes())
        self.persist()

    def persist(self):
        self.scope.write_bytes(raw(self.record))
        self.pin=digest(self.scope.read_bytes())

    def load(self, live=True):
        return subject._load_grant(self.root,self.scope,self.pin,digest(self.user),live=live)

    def selection(self, ids=None):
        ids = self.ids[:2] if ids is None else ids
        return dict(source_id='OSM-M2B12-C',answer_source_id='OSM-M2B12-E-ANSWERS',
            packages=[dict(role=p['role'], zip_sha256=p['zip_sha256'],zip_size_bytes=p['zip_size_bytes'],
                selected_member=p['selected_mmd']['member'],member_sha256=p['selected_mmd']['sha256'],
                member_size_bytes=p['selected_mmd']['size_bytes']) for p in self.record['packages']],
            questions=[dict(question_id=q,source_section='EX12B',source_question_number=str(int(q.rsplit('Q',1)[1])),
                            semantic_order=i) for i,q in enumerate(ids,1)])

    def test_valid_live_scope_selects_only_ordered_unaccepted_ids(self):
        grant=self.load()
        self.assertEqual(subject.validate_selection(grant,self.selection(),()), tuple(self.ids[:2]))

    def test_public_entry_rejects_self_asserted_synthetic_grant(self):
        with self.assertRaises(ImportApprovalError):
            subject.load_chapter_grant(self.root,live=True)

    def test_scope_or_user_change_fails_even_with_same_path(self):
        for path in (self.scope,self.scope.parent/'USER_AUTHORIZATION.txt'):
            old=path.read_bytes();path.write_bytes(old+b'changed')
            with self.assertRaises(ImportApprovalError): self.load()
            path.write_bytes(old)

    def test_revocation_blocks_new_work_but_preserves_historical_verification(self):
        (self.scope.parent/'REVOKED').write_bytes(b'')
        with self.assertRaises(ImportApprovalError): self.load()
        self.assertEqual(self.load(live=False).scope_sha256,self.pin)

    def test_later_release_invalidates_live_grant_even_when_old_baseline_unchanged(self):
        (self.root/'releases/V1.24').mkdir()
        with self.assertRaises(ImportApprovalError): self.load()
        self.assertEqual(self.load(live=False).scope_sha256,self.pin)

    def test_changed_input_or_formal_or_inventory_fails(self):
        for path in (Path(self.record['packages'][0]['path']), self.formal/'manifest.json',
                     Path(self.record['inventory_path'])):
            old=path.read_bytes();path.write_bytes(old+b'x')
            with self.assertRaises(ImportApprovalError): self.load()
            path.write_bytes(old)

    def test_symlinked_grant_rejected(self):
        moved=self.scope.with_name('moved.json'); self.scope.rename(moved);self.scope.symlink_to(moved)
        with self.assertRaises(ImportApprovalError): self.load()

    def test_empty_duplicate_reverse_or_previously_accepted_selection_rejected(self):
        grant=self.load()
        for ids, accepted in (([],()),([self.ids[0],self.ids[0]],()),(self.ids[1::-1],()),
                              (self.ids[:1],self.ids[:1])):
            with self.subTest(ids=ids,accepted=accepted), self.assertRaises(ImportApprovalError):
                subject.validate_selection(grant,self.selection(ids),accepted)

    def test_held_prerequisite_new_source_or_false_number_rejected(self):
        grant=self.load()
        for key, value in (('question_id','held-0'),('question_id','prerequisite-0'),
                           ('question_id','unknown'),('source_question_number','2'),('source_section','EX12C')):
            mapping=self.selection(self.ids[:1]);mapping['questions'][0][key]=value
            with self.subTest(key=key,value=value), self.assertRaises(ImportApprovalError):
                subject.validate_selection(grant,mapping,())
        mapping=self.selection();mapping['source_id']='OTHER'
        with self.assertRaises(ImportApprovalError): subject.validate_selection(grant,mapping,())

    def test_mapping_package_must_equal_grant_not_only_member_basename(self):
        grant=self.load();mapping=self.selection()
        mapping['packages'].reverse()
        with self.assertRaises(ImportApprovalError): subject.validate_selection(grant,mapping,())

    def test_grant_partition_must_be_disjoint(self):
        self.record['excluded_held_ids'][0]=self.ids[0];self.persist()
        with self.assertRaises(ImportApprovalError): self.load()

    def test_missing_file_or_nonboolean_live_flag_fails_closed(self):
        with self.assertRaises(ImportApprovalError): self.load(live='yes')
        self.scope.unlink()
        with self.assertRaises(ImportApprovalError): self.load()
