"""Chapter coexistence checks using unchanged, independently authored old goldens."""
import unittest

from tests.integration import test_mmd_adapter as original
from tests.unit import test_mmd_source_mapping as explicit


class HistoricalCompatibilityTests(unittest.TestCase):
    def replay(self, case):
        result = unittest.TestResult()
        case.run(result)
        self.assertEqual(result.testsRun, 1)
        self.assertFalse(result.errors or result.failures, result.errors + result.failures)
        self.assertFalse(result.skipped or result.expectedFailures)

    def test_old_complete_tree_matches_independent_golden(self):
        self.replay(original.CanonicalPackageIntegrationRedTests(
            'test_representative_complete_tree_is_byte_identical_to_independent_golden'))

    def test_old_candidates_issues_counts_report_digest_unchanged(self):
        self.replay(original.DeterminismAndGoldenEquivalenceIntegrationRedTests(
            'test_adapter_and_independent_golden_match_every_task9a_authority_dimension'))

    def test_old_explicit_mapping_exports_and_signatures_unchanged(self):
        for name in ('test_module_has_exact_public_surface', 'test_public_functions_have_exact_signatures'):
            self.replay(explicit.PublicContractTests(name))
        import joy_m2.ingest as package
        self.assertFalse(any(name in getattr(package, '__all__', ()) for name in (
            'VectorCh12Proposal', 'propose_vector_ch12_mapping', 'adapt_vector_ch12_from_mapping')))
