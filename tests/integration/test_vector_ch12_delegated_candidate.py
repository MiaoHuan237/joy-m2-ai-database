"""Chapter-only delegated candidate tests; synthetic content, no real approval."""
from dataclasses import fields
from hashlib import sha256
import json
import unittest

from joy_m2.errors import PipelineError
from joy_m2.ingest.vector_ch12_delegated_models import (
    ChapterSourceDecision, ChapterImportDecision, chapter_contract,
)
from tests.unit.test_vector_ch12_delegation import SourceEvidenceTests, raw, digest
from joy_m2.ingest.v124_models import V124ImportApproval, V124CandidateContract


class DelegatedCarrierTests(unittest.TestCase):
    def source(self):
        fixture=SourceEvidenceTests();fixture.setUp()
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
