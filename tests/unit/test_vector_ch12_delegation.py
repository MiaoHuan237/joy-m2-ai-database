"""Independent synthetic grant evidence, never usable with the real public pin."""
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
import zipfile
import copy
from unittest.mock import patch

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


class SourceEvidenceTests(unittest.TestCase):
    def setUp(self):
        from tests.fixtures.vector_ch12.mapping_fixture import fixture
        self.mapping, self.members=fixture()
        self.review=dict(schema_version='vector-ch12-independent-content-review-v1',
            executor_id='/root',reviewer_id='/root/independent-review',
            mapping_sha256=digest(raw(self.mapping)),question_ids=[q['question_id'] for q in self.mapping['questions']],
            critical=0,important=0,conditions_complete=True,source_unchanged=True,
            images_owned=True,answers_truthful=True,evidence=['Synthetic independent source check'],limitations=[])
        self.index={'records':[dict(proposed_question_id=q['question_id'],
            source_section=q['source_section'],source_question_number=q['source_question_number'],
            question_spans=[dict(source_role='textbook',member='source.mmd',start_byte=s,end_byte=e)])
            for q,(s,e) in zip(self.mapping['questions'],((5,9),(10,14)))]}

    def test_review_binds_exact_mapping_order_and_separate_reviewer(self):
        subject._validate_review(self.review,self.mapping)
        subject._validate_source_anchors(self.mapping,self.index)

    def test_review_rejects_unresolved_findings_self_review_missing_or_inexact_scope(self):
        for key,value in (('important',1),('critical',True),('reviewer_id','/root'),
                          ('mapping_sha256','0'*64),('question_ids',[]),('evidence',[]),
                          ('conditions_complete',False),('source_unchanged',False),
                          ('images_owned',False),('answers_truthful',False)):
            review=copy.deepcopy(self.review);review[key]=value
            with self.subTest(key=key),self.assertRaises(ImportApprovalError):
                subject._validate_review(review,self.mapping)
        review=copy.deepcopy(self.review);del review['reviewer_id']
        with self.assertRaises(ImportApprovalError): subject._validate_review(review,self.mapping)

    def test_same_id_with_another_question_span_cannot_claim_scope(self):
        mapping=copy.deepcopy(self.mapping)
        mapping['questions'][0]['question_pieces'][1]['span']=mapping['questions'][1]['question_pieces'][1]['span']
        with self.assertRaises(ImportApprovalError): subject._validate_source_anchors(mapping,self.index)

    def test_own_source_piece_cannot_extend_into_next_unit(self):
        mapping=copy.deepcopy(self.mapping)
        mapping['questions'][0]['question_pieces'][1]['span']['end_byte']=14
        with self.assertRaises(ImportApprovalError): subject._validate_source_anchors(mapping,self.index)

    def test_shared_condition_alone_does_not_identify_a_complete_question(self):
        mapping=copy.deepcopy(self.mapping)
        mapping['questions'][0]['question_pieces']=mapping['questions'][0]['question_pieces'][:1]
        with self.assertRaises(ImportApprovalError): subject._validate_source_anchors(mapping,self.index)

    def test_decision_actor_is_explicit_and_not_a_human_approval_string(self):
        from joy_m2.ingest.vector_ch12_delegated_models import ChapterSourceDecision
        p=dict(schema_version='vector-ch12-delegated-source-decision-v1',
               actor='codex_under_chapter_delegation',grant_sha256='a'*64,
               mapping=self.mapping,review=self.review)
        decision=ChapterSourceDecision(raw(p))
        self.assertEqual(decision.decision_sha256,digest(raw(p)))
        self.assertEqual(decision.mapping_sha256,digest(raw(self.mapping)))
        p['actor']='USER APPROVED SOURCE MAPPING OSM-M2B12-C '+decision.mapping_sha256
        with self.assertRaises(ImportApprovalError): ChapterSourceDecision(raw(p))


class SourceDecisionIntegrationTests(unittest.TestCase):
    """Only trust anchors are substituted; real ZIP, spans, taxonomy and source API."""
    def setUp(self):
        GrantTests.setUp(self)
        from tests.fixtures.vector_ch12.mapping_fixture import fixture
        from joy_m2.config import PipelineConfig
        self.mapping,self.members=fixture()
        # Adopt the independent fixture's actual source IDs, not model-generated content.
        self.ids=[q.replace('EX12B','EX12A') for q in self.ids]
        self.record['authorized_question_ids']=self.ids
        self.record['S04_exact_human_mapping']['question_ids']=self.ids[:14]
        self.record['later_processing_question_ids']=self.ids[14:]
        for role,p,mp in zip(('textbook','answers'),self.record['packages'],self.mapping['packages']):
            path=Path(p['path']);data=self.members[(role,'source.mmd')]
            with zipfile.ZipFile(path,'w') as z:z.writestr('source.mmd',data)
            p.update(zip_sha256=digest(path.read_bytes()),zip_size_bytes=path.stat().st_size,
                     selected_mmd=dict(member='source.mmd',sha256=digest(data),size_bytes=len(data)))
            mp.update(zip_sha256=p['zip_sha256'],zip_size_bytes=p['zip_size_bytes'])
        import sqlite3
        db=self.formal/'Joy_M2_Complete_Question_DB_V1_23.sqlite3'
        db.unlink()  # This is the test-owned synthetic non-SQLite placeholder.
        with sqlite3.connect(db) as connection:
            connection.execute('CREATE TABLE complete_question_taxonomy_v2(taxonomy_kind TEXT,value TEXT)')
            connection.execute("INSERT INTO complete_question_taxonomy_v2 VALUES('tag','vector')")
        self.record['baseline']['sqlite_sha256']=digest(db.read_bytes())
        self.persist()
        self.config=PipelineConfig(repo_root=self.root)
        self.mapping_path=self.root/'mapping.json';self.mapping_path.write_bytes(raw(self.mapping))
        self.review_path=self.root/'review.json'
        self.review=dict(schema_version='vector-ch12-independent-content-review-v1',executor_id='/root',
            reviewer_id='/root/reviewer',mapping_sha256=digest(raw(self.mapping)),
            question_ids=[q['question_id'] for q in self.mapping['questions']],critical=0,important=0,
            conditions_complete=True,source_unchanged=True,images_owned=True,answers_truthful=True,
            evidence=['Independent synthetic span/answer check'],limitations=['Only final answers'])
        self.review_path.write_bytes(raw(self.review))
        self.index={'records':[dict(proposed_question_id=q['question_id'],source_section='EX12A',
            source_question_number=q['source_question_number'],question_spans=[dict(source_role='textbook',
            member='source.mmd',start_byte=s,end_byte=e)]) for q,(s,e) in zip(self.mapping['questions'],((5,9),(10,14)))]}
        (self.root/subject.INDEX_RELATIVE).parent.mkdir(parents=True,exist_ok=True)
        (self.root/subject.INDEX_RELATIVE).write_bytes(raw(self.index))
        self.addCleanup(patch.stopall)
        # Patch only external trust pins for synthetic isolation. No writer is mocked.
        patch.object(subject,'SCOPE_SHA256',self.pin).start()
        patch.object(subject,'USER_SHA256',digest(self.user)).start()
        patch.object(subject,'INDEX_SHA256',digest(raw(self.index))).start()

    persist=GrantTests.persist
    load=GrantTests.load

    def test_source_decision_validates_real_inventory_mapping_and_taxonomy(self):
        decision=subject.decide_chapter_source(self.mapping_path,self.review_path,self.config)
        mapping,members=subject.validate_chapter_source_decision(decision,self.config,live=True)
        self.assertEqual(mapping,self.mapping)
        self.assertEqual(members,self.members)

    def test_changed_source_or_mapping_review_blocks_decision(self):
        decision=subject.decide_chapter_source(self.mapping_path,self.review_path,self.config)
        Path(self.record['packages'][0]['path']).write_bytes(b'changed')
        with self.assertRaises(ImportApprovalError):
            subject.validate_chapter_source_decision(decision,self.config,live=True)

    def test_delegated_adaptation_preserves_manual_canonical_bytes(self):
        from joy_m2.ingest.vector_ch12 import adapt_vector_ch12_delegated, adapt_vector_ch12_from_mapping
        from joy_m2.ingest.source_mapping import SourceMappingApproval
        decision=subject.decide_chapter_source(self.mapping_path,self.review_path,self.config)
        self.config.staging_root.mkdir(parents=True,exist_ok=True)
        delegated=self.config.staging_root/'delegated'
        manual=self.config.staging_root/'manual'
        adapt_vector_ch12_delegated(decision,delegated,self.config)
        md=digest(raw(self.mapping))
        # Synthetic exact approval is confined to the independent comparison fixture.
        approval=SourceMappingApproval('OSM-M2B12-C',md,f'USER APPROVED SOURCE MAPPING OSM-M2B12-C {md}')
        adapt_vector_ch12_from_mapping(*(Path(p['path']) for p in self.record['packages']),
            self.mapping_path,approval,manual,self.config)
        tree=lambda p:{f.relative_to(p).as_posix():f.read_bytes() for f in p.rglob('*') if f.is_file()}
        self.assertEqual(tree(delegated),tree(manual))
        closure=subject.validate_chapter_canonical(decision,delegated,self.config,live=True)
        self.assertIn('import_manifest.json',closure)
        self.assertEqual(closure['import_manifest.json']['sha256'],digest((delegated/'import_manifest.json').read_bytes()))
        (delegated/'question_records.json').write_bytes(b'forged extra file')
        with self.assertRaises(ImportApprovalError):
            subject.validate_chapter_canonical(decision,delegated,self.config,live=True)

    def test_revoked_source_decision_cannot_create_canonical(self):
        from joy_m2.ingest.vector_ch12 import adapt_vector_ch12_delegated
        decision=subject.decide_chapter_source(self.mapping_path,self.review_path,self.config)
        (self.scope.parent/'REVOKED').write_bytes(b'revoked')
        output=self.config.staging_root/'must-not-exist'
        with self.assertRaises(ImportApprovalError): adapt_vector_ch12_delegated(decision,output,self.config)
        self.assertFalse(output.exists())

    def test_import_decision_binds_actual_ready_preflight_and_canonical(self):
        import shutil
        from joy_m2.ingest.vector_ch12 import adapt_vector_ch12_delegated
        from joy_m2.ingest.v124_preflight import preflight_v124_import
        from joy_m2.ingest.v124_models import V124PreflightRequest
        from joy_m2.models import ArtifactRef
        from tests.integration.test_v124_preflight import BASELINE,BASELINE_SHA,BASELINE_SIZE,_contract
        formal=self.formal/'Joy_M2_Complete_Question_DB_V1_23.sqlite3'
        shutil.copyfile(BASELINE,formal)
        shutil.copyfile(BASELINE.parent/'manifest.json',self.formal/'manifest.json')
        self.record['baseline'].update(sqlite_sha256=BASELINE_SHA,
            manifest_sha256=digest((self.formal/'manifest.json').read_bytes()))
        self.persist();patch.object(subject,'SCOPE_SHA256',self.pin).start()
        source=subject.decide_chapter_source(self.mapping_path,self.review_path,self.config)
        self.config.staging_root.mkdir(parents=True,exist_ok=True)
        package=adapt_vector_ch12_delegated(source,self.config.staging_root/'canonical',self.config)
        result=preflight_v124_import(V124PreflightRequest(package.manifest,package.package_root,
            ArtifactRef(formal,BASELINE_SHA,BASELINE_SIZE,'sqlite'),None,_contract()),self.config)
        self.assertEqual(result.report.status,'READY FOR USER IMPORT APPROVAL')
        self.assertNotEqual(result.report.manifest_sha256,digest((package.package_root/'import_manifest.json').read_bytes()))
        decision=subject.decide_chapter_import(source,result,package.package_root,self.config,())
        self.assertEqual(decision.preflight_sha256,result.report.preflight_sha256)
        self.assertEqual(decision.parent_candidate_digest,'797ed06ca5833bac060c1603cada38a6f2aa9eb080a40d9dc892bba9a549773a')
        with self.assertRaises(ImportApprovalError):
            subject.decide_chapter_import(source,result,package.package_root,self.config,
                [self.mapping['questions'][0]['question_id']])
