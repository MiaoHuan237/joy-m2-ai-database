from dataclasses import FrozenInstanceError, fields
from pathlib import Path
import unittest

from joy_m2.errors import PipelineError
from joy_m2.ingest import vector_ch12 as profile


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
