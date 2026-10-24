"""Chapter-only delegated candidate tests; synthetic content, no real approval."""
from dataclasses import fields
from hashlib import sha256
import json
import unittest

from joy_m2.errors import PipelineError
from joy_m2.ingest.vector_ch12_delegated_models import (
    ChapterSourceDecision, ChapterImportDecision, chapter_contract,
)
from tests.unit import test_vector_ch12_delegation as fixtures
raw, digest = fixtures.raw, fixtures.digest
from joy_m2.ingest.v124_models import V124ImportApproval, V124CandidateContract


class ChapterCandidateTests(unittest.TestCase):
    def test_successful_receipt_replay_verifies_without_writer_or_mutation(self):
        from unittest.mock import patch
        from joy_m2.ingest import v124_writer as writer
        from joy_m2.ingest.vector_ch12_delegated_models import ChapterVerificationRequest
        from dataclasses import asdict
        f=self.fixture;request=self.request();artifact=writer.build_chapter_candidate(request,f.config)
        manifest=json.loads(artifact.manifest.path.read_bytes())
        before={str(p.relative_to(request.output_dir)):p.read_bytes() for p in request.output_dir.rglob('*') if p.is_file()}
        receipt=dict(candidate_dir=str(request.output_dir),candidate_digest=artifact.state.candidate_digest,
            batch_id=self.decision.batch_id,target_release_version='V1.24',generation='000001',
            batch_ledger=manifest['batch_ledger'],counts=manifest['counts'],approval=asdict(self.decision),
            artifacts={k:dict(sha256=digest(v),size_bytes=len(v)) for k,v in before.items()})
        path=f.config.staging_root/'REAL_BATCH_IMPORT_RECEIPT.json';path.write_bytes(raw(receipt))
        verification=ChapterVerificationRequest(request.output_dir,request.approved_batches,request.contract)
        with patch.object(writer,'_build_candidate',side_effect=AssertionError('must not write')) as build:
            self.assertEqual(writer.resume_chapter_checkpoint(verification,path,f.config),receipt)
            self.assertEqual(writer.resume_chapter_checkpoint(verification,path,f.config),receipt)
            self.assertEqual(build.call_count,0)
        self.assertEqual(path.read_bytes(),raw(receipt))
        self.assertEqual(before,{str(p.relative_to(request.output_dir)):p.read_bytes() for p in request.output_dir.rglob('*') if p.is_file()})
        receipt['candidate_digest']='a'*64;path.write_bytes(raw(receipt))
        with self.assertRaises(PipelineError):writer.resume_chapter_checkpoint(verification,path,f.config)

    def test_revoked_grant_cannot_create_new_chapter_preflight(self):
        from joy_m2.ingest.v124_preflight import preflight_chapter_import
        from joy_m2.ingest.vector_ch12_delegated_models import ChapterPreflightRequest
        f=self.fixture;(f.scope.parent/'REVOKED').write_bytes(b'')
        request=ChapterPreflightRequest(self.package.manifest,self.package.package_root,
            self.result.effective_state.baseline_database,None,chapter_contract())
        with self.assertRaises(PipelineError):preflight_chapter_import(request,f.config)

    def request(self, name='generation-000001'):
        from joy_m2.ingest.vector_ch12_delegated_models import ChapterApprovedBatch,ChapterBuildRequest
        return ChapterBuildRequest((ChapterApprovedBatch(self.result,self.package.package_root,self.decision),),
            self.fixture.config.staging_root/name,chapter_contract())

    def test_writer_rejects_busy_existing_cycle_lock(self):
        import fcntl
        from joy_m2.ingest.v124_writer import build_chapter_candidate
        f=self.fixture;runtime=f.root/'data/staging/auto-ingestion';runtime.mkdir(parents=True)
        with (runtime/'cycle.lock').open('a') as lock:
            fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            with self.assertRaises(PipelineError):build_chapter_candidate(self.request(),f.config)
        self.assertFalse(self.request().output_dir.exists())

    def test_stale_genesis_cannot_replay_to_a_second_output(self):
        from joy_m2.ingest.v124_writer import build_chapter_candidate
        f=self.fixture
        first=build_chapter_candidate(self.request(),f.config)
        before=first.database.path.read_bytes()
        with self.assertRaises(PipelineError):
            build_chapter_candidate(self.request('replayed-elsewhere'),f.config)
        self.assertEqual(first.database.path.read_bytes(),before)

    def test_revocation_during_final_verification_prevents_rename_and_cleans_private(self):
        from unittest.mock import patch
        from joy_m2.ingest import v124_verification as verification
        from joy_m2.ingest.v124_writer import build_chapter_candidate
        f=self.fixture;verify=verification.verify_chapter_candidate;calls=[]
        def revoke(request,config):
            result=verify(request,config);calls.append(1)
            if len(calls)==2:(f.scope.parent/'REVOKED').write_bytes(b'withdrawn during verification')
            return result
        with patch.object(verification,'verify_chapter_candidate',side_effect=revoke):
            with self.assertRaises(PipelineError):build_chapter_candidate(self.request(),f.config)
        self.assertFalse(self.request().output_dir.exists())
        self.assertEqual(list(f.config.staging_root.glob('.generation-000001.tmp-*')),[])

    def test_revocation_after_acceptance_does_not_destroy_historical_verification(self):
        from joy_m2.ingest.v124_writer import build_chapter_candidate
        from joy_m2.ingest.v124_verification import verify_chapter_candidate
        from joy_m2.ingest.vector_ch12_delegated_models import ChapterVerificationRequest
        f=self.fixture;request=self.request();artifact=build_chapter_candidate(request,f.config)
        (f.scope.parent/'REVOKED').write_bytes(b'')
        result=verify_chapter_candidate(ChapterVerificationRequest(request.output_dir,request.approved_batches,
            request.contract),f.config)
        self.assertEqual(result.status,'PASS')
        with self.assertRaises(PipelineError):build_chapter_candidate(self.request('new'),f.config)

    def test_mixed_manual_prefix_retains_exact_digest_and_bytes(self):
        from joy_m2.ingest import v124_models as m,vector_ch12_delegated_models as d
        from joy_m2.ingest.v124_preflight import preflight_v124_import,preflight_chapter_import
        from joy_m2.ingest.v124_writer import build_v124_candidate,build_chapter_candidate
        from joy_m2.ingest.vector_ch12_delegation import decide_chapter_import
        from tests.integration.test_v124_preflight import _contract
        f=self.fixture;source,package=self.subset(5)
        first=preflight_v124_import(m.V124PreflightRequest(package.manifest,package.package_root,
            self.result.effective_state.baseline_database,None,_contract()),f.config)
        r=first.report
        # Synthetic fixture only; this string is never used on real sources.
        approval=m.V124ImportApproval(r.batch_id,r.preflight_sha256,'V1.24',r.parent_candidate_digest,
            f'USER APPROVED IMPORT BATCH {r.batch_id} {r.preflight_sha256} V1.24 PARENT {r.parent_candidate_digest}')
        batch=m.V124ApprovedBatch(first,package.package_root,approval)
        out=f.config.staging_root/'manual-prefix'
        artifact=build_v124_candidate(m.V124CandidateBuildRequest((batch,),out,_contract()),f.config)
        before={str(p.relative_to(out)):p.read_bytes() for p in out.rglob('*') if p.is_file()}
        source2,package2=self.subset(6)
        parent=m.V124CandidateVerificationRequest(out,(batch,),_contract())
        second=preflight_chapter_import(d.ChapterPreflightRequest(package2.manifest,package2.package_root,
            self.result.effective_state.baseline_database,parent,chapter_contract()),f.config)
        decision=decide_chapter_import(source2,second,package2.package_root,f.config,
            tuple(c.proposed_question_id for c in first.candidates))
        batch2=d.ChapterApprovedBatch(second,package2.package_root,decision)
        output=build_chapter_candidate(d.ChapterBuildRequest((batch,batch2),f.config.staging_root/'mixed',chapter_contract()),f.config)
        self.assertEqual(output.state.batch_ledger[1].parent_candidate_digest,artifact.state.candidate_digest)
        self.assertEqual(before,{str(p.relative_to(out)):p.read_bytes() for p in out.rglob('*') if p.is_file()})
        for p in (out/'authority').rglob('*.json'):
            self.assertEqual(p.read_bytes(),(output.database.path.parent/p.relative_to(out)).read_bytes())

    def test_tampered_or_untrusted_decisions_do_not_pass_independent_verifier(self):
        import copy
        from joy_m2.ingest.v124_writer import build_chapter_candidate
        from joy_m2.ingest.v124_verification import verify_chapter_candidate
        from joy_m2.ingest.vector_ch12_delegated_models import ChapterVerificationRequest
        f=self.fixture;request=self.request();artifact=build_chapter_candidate(request,f.config)
        for name,value in (('grant_sha256','f'*64),('statement','USER APPROVED '+self.decision.statement)):
            bad=copy.deepcopy(request.approved_batches[0]);object.__setattr__(bad.approval,name,value)
            forged=object.__new__(ChapterVerificationRequest)
            for k,v in dict(candidate_dir=request.output_dir,approved_batches=(bad,),contract=chapter_contract()).items():
                object.__setattr__(forged,k,v)
            with self.subTest(name=name):
                try: report=verify_chapter_candidate(forged,f.config)
                except PipelineError: pass
                else: self.assertEqual(report.status,'FAIL')

    def test_no_replace_and_changed_canonical_are_rejected(self):
        from joy_m2.ingest.v124_writer import build_chapter_candidate
        f=self.fixture;request=self.request();artifact=build_chapter_candidate(request,f.config)
        before=artifact.database.path.read_bytes()
        with self.assertRaises(PipelineError):build_chapter_candidate(request,f.config)
        self.assertEqual(artifact.database.path.read_bytes(),before)
        path=self.package.package_root/'import_manifest.json';path.write_bytes(path.read_bytes()+b' ')
        with self.assertRaises(PipelineError):build_chapter_candidate(self.request('altered'),f.config)

    def setUp(self):
        import shutil
        from unittest.mock import patch
        from joy_m2.ingest import vector_ch12_delegation as delegation
        from joy_m2.ingest.vector_ch12 import adapt_vector_ch12_delegated
        from joy_m2.ingest.v124_preflight import preflight_v124_import
        from joy_m2.ingest.v124_models import V124PreflightRequest
        from joy_m2.models import ArtifactRef
        from tests.integration.test_v124_preflight import BASELINE,BASELINE_SHA,BASELINE_SIZE,_contract
        self.fixture=fixtures.SourceDecisionIntegrationTests()
        self.fixture.setUp();self.addCleanup(self.fixture.doCleanups)
        f=self.fixture
        formal=f.formal/'Joy_M2_Complete_Question_DB_V1_23.sqlite3'
        shutil.copyfile(BASELINE,formal);shutil.copyfile(BASELINE.parent/'manifest.json',f.formal/'manifest.json')
        for name in ('SHA256SUMS.txt','rollback.json'):
            shutil.copyfile(BASELINE.parent/name,f.formal/name)
        f.record['baseline'].update(sqlite_sha256=BASELINE_SHA,manifest_sha256=digest((f.formal/'manifest.json').read_bytes()))
        f.persist();patch.object(delegation,'SCOPE_SHA256',f.pin).start()
        self.source=delegation.decide_chapter_source(f.mapping_path,f.review_path,f.config)
        f.config.staging_root.mkdir(parents=True,exist_ok=True)
        self.package=adapt_vector_ch12_delegated(self.source,f.config.staging_root/'canonical',f.config)
        self.result=preflight_v124_import(V124PreflightRequest(self.package.manifest,self.package.package_root,
            ArtifactRef(formal,BASELINE_SHA,BASELINE_SIZE,'sqlite'),None,_contract()),f.config)
        self.assertEqual(self.result.report.status,'READY FOR USER IMPORT APPROVAL')
        self.decision=delegation.decide_chapter_import(self.source,self.result,self.package.package_root,f.config,())

    def test_first_delegated_candidate_has_honest_authority_and_independent_verification(self):
        from joy_m2.ingest.vector_ch12_delegated_models import (
            ChapterApprovedBatch,ChapterBuildRequest,ChapterVerificationRequest)
        from joy_m2.ingest.v124_writer import build_chapter_candidate
        from joy_m2.ingest.v124_verification import verify_chapter_candidate
        f=self.fixture
        batch=ChapterApprovedBatch(self.result,self.package.package_root,self.decision)
        output=f.config.staging_root/'generation-000001'
        artifact=build_chapter_candidate(ChapterBuildRequest((batch,),output,chapter_contract()),f.config)
        self.assertEqual(artifact.state.projected_question_count,679)
        verification=verify_chapter_candidate(ChapterVerificationRequest(output,(batch,),chapter_contract()),f.config)
        self.assertEqual(verification.status,'PASS')
        self.assertTrue(all(c.passed for c in verification.checks))
        manifest=json.loads(artifact.manifest.path.read_bytes())
        self.assertEqual(manifest['schema_version'],'task14-v124-ch12-candidate-manifest-v1')
        self.assertEqual(manifest['batch_ledger'][0]['approval']['statement'],self.decision.statement)

    def subset(self,number):
        import copy
        from joy_m2.ingest import vector_ch12_delegation as delegation
        from joy_m2.ingest.vector_ch12 import adapt_vector_ch12_delegated
        f=self.fixture;m=copy.deepcopy(f.mapping)
        chosen=[q for q in m['questions'] if q['source_question_number']==str(number)]
        discarded=[q for q in m['questions'] if q not in chosen]
        m['questions']=chosen;chosen[0]['semantic_order']=1
        m['batch_id']=f'SYNTHETIC-CH12-{number}'
        for shared in m['shared_conditions']:shared['applies_to']=[chosen[0]['question_id']]
        for q in discarded:
            m['unselected_spans'] += [dict(span=p['span'],reason='Other synthetic natural group')
                for p in q['question_pieces'] if p['kind']=='source']
            m['unselected_spans'] += [dict(span=s,reason='Other synthetic answer') for s in q['solution_spans']]
        for unit in m['unit_dispositions']:
            unit['disposition']='proposed_selection' if unit['question_id']==chosen[0]['question_id'] else 'later_processing'
        review=copy.deepcopy(f.review);review['mapping_sha256']=digest(raw(m));review['question_ids']=[chosen[0]['question_id']]
        mp=f.root/f'mapping-{number}.json';rp=f.root/f'review-{number}.json'
        mp.write_bytes(raw(m));rp.write_bytes(raw(review))
        source=delegation.decide_chapter_source(mp,rp,f.config)
        package=adapt_vector_ch12_delegated(source,f.config.staging_root/f'package-{number}',f.config)
        return source,package

    def test_verified_delegated_parent_can_preflight_next_natural_group(self):
        from joy_m2.ingest.vector_ch12_delegated_models import (
            ChapterApprovedBatch,ChapterBuildRequest,ChapterVerificationRequest,ChapterPreflightRequest)
        from joy_m2.ingest.v124_writer import build_chapter_candidate
        from joy_m2.ingest.v124_preflight import preflight_v124_import,preflight_chapter_import
        from joy_m2.ingest.v124_models import V124PreflightRequest
        from joy_m2.ingest import vector_ch12_delegation as delegation
        from tests.integration.test_v124_preflight import _contract
        f=self.fixture
        source,package=self.subset(5)
        first=preflight_v124_import(V124PreflightRequest(package.manifest,package.package_root,
            self.result.effective_state.baseline_database,None,_contract()),f.config)
        decision=delegation.decide_chapter_import(source,first,package.package_root,f.config,())
        batch=ChapterApprovedBatch(first,package.package_root,decision)
        output=f.config.staging_root/'generation-000001'
        artifact=build_chapter_candidate(ChapterBuildRequest((batch,),output,chapter_contract()),f.config)
        source2,package2=self.subset(6)
        parent=ChapterVerificationRequest(output,(batch,),chapter_contract())
        second=preflight_chapter_import(ChapterPreflightRequest(package2.manifest,package2.package_root,
            self.result.effective_state.baseline_database,parent,chapter_contract()),f.config)
        self.assertEqual(second.report.status,'READY FOR USER IMPORT APPROVAL')
        self.assertEqual(second.report.parent_candidate_digest,artifact.state.candidate_digest)
        self.assertEqual(second.report.before_count,678)
        self.assertEqual(second.report.new_candidate_count,1)
        decision2=delegation.decide_chapter_import(source2,second,package2.package_root,f.config,
            tuple(c.proposed_question_id for c in first.candidates))
        batch2=ChapterApprovedBatch(second,package2.package_root,decision2)
        artifact2=build_chapter_candidate(ChapterBuildRequest((batch,batch2),
            f.config.staging_root/'generation-000002',chapter_contract()),f.config)
        self.assertEqual(artifact2.state.candidate_count,2)
        self.assertEqual(artifact2.verification_report.status,'PASS')


class DelegatedCarrierTests(unittest.TestCase):
    def source(self):
        fixture=fixtures.SourceEvidenceTests();fixture.setUp()
        return ChapterSourceDecision(raw(dict(schema_version='vector-ch12-delegated-source-decision-v1',
            actor='codex_under_chapter_delegation',grant_sha256='a'*64,
            mapping=fixture.mapping,review=fixture.review)))

    def decision(self):
        source=self.source()
        statement=(f'CHAPTER DELEGATED IMPORT BATCH SYNTHETIC-CH12 {"b"*64} '
            f'V1.24 PARENT {"c"*64} GRANT {"a"*64} SOURCE {source.decision_sha256}')
        return ChapterImportDecision('SYNTHETIC-CH12','b'*64,'V1.24','c'*64,
            statement,'a'*64,source.payload.decode(),raw({'import_manifest.json':
                {'sha256':'d'*64,'size_bytes':42}}).decode())

    def test_delegated_identity_is_explicit_and_old_human_interface_rejects_it(self):
        decision=self.decision()
        self.assertTrue(decision.statement.startswith('CHAPTER DELEGATED IMPORT BATCH '))
        with self.assertRaises(PipelineError):
            V124ImportApproval(decision.batch_id,decision.preflight_sha256,'V1.24',
                               decision.parent_candidate_digest,decision.statement)

    def test_new_candidate_schema_cannot_be_mislabelled_as_manual_contract(self):
        contract=chapter_contract()
        self.assertEqual(contract.candidate_identity_schema,'task14-v124-ch12-candidate-identity-v1')
        with self.assertRaises(PipelineError):
            V124CandidateContract(**{f.name:getattr(contract,f.name) for f in fields(contract)})
