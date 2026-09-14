"""Independent literal oracles for the Task 10A candidate verifier."""

from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import re
import sys
import unittest


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.errors import InputFormatError
from tests.integration.test_v120_candidate import (
    ABC_CANDIDATE_DIGEST,
    AB_CANDIDATE_DIGEST,
    A_CANDIDATE_DIGEST,
    _CHECK_NAMES,
    _EXACT_V120_SCHEMA,
    _approved_prefix,
    _candidate_identity_payload,
    _canonical_file,
)


def _profiles(testcase: unittest.TestCase):
    name = "joy_m2.ingest.v120_writer_profiles"
    testcase.assertIsNotNone(
        importlib.util.find_spec(name),
        "the private V1.20 writer/verifier primitives module must exist",
    )
    return importlib.import_module(name)


class V120WriterPrimitiveTests(unittest.TestCase):
    def test_collision_normalization_preserves_non_ascii_whitespace(self) -> None:
        """Catches writer normalization drifting from historical Task 9 authority."""
        from joy_m2.ingest.preflight import _normalized_text_sha256 as historical
        from joy_m2.ingest.v120_verification import _normalized_text_sha256 as verifier
        from joy_m2.ingest.v120_writer import _normalized_text_sha256 as writer

        source = "  alpha\u00a0beta\t gamma  "
        expected = hashlib.sha256("alpha\u00a0beta gamma".encode("utf-8")).hexdigest()
        self.assertEqual(historical(source), expected)
        self.assertEqual(verifier(source), expected)
        self.assertEqual(writer(source), expected)

    def test_exact_ordered_check_contract_and_canonical_helpers(self) -> None:
        module = _profiles(self)
        self.assertEqual(module.CHECK_NAMES, _CHECK_NAMES)
        self.assertEqual(
            module.canonical_json_bytes({"z": 1, "a": "向量"}),
            b'{"a":"\xe5\x90\x91\xe9\x87\x8f","z":1}',
        )
        self.assertEqual(
            module.canonical_json_file_bytes({"z": 1, "a": "向量"}),
            b'{"a":"\xe5\x90\x91\xe9\x87\x8f","z":1}\n',
        )
        self.assertEqual(module.sha256_bytes(b"Task 10A\n"), hashlib.sha256(b"Task 10A\n").hexdigest())
        self.assertTrue(module.is_sha256("0" * 64))
        self.assertFalse(module.is_sha256("A" * 64))
        self.assertFalse(module.is_sha256(True))

    def test_exact_normalized_ddl_matches_the_five_design_objects(self) -> None:
        module = _profiles(self)
        self.assertEqual(len(module.TASK10_SCHEMA_SQL), 5)
        actual = tuple(module.normalized_sql(value) for value in module.TASK10_SCHEMA_SQL)
        expected = tuple(module.normalized_sql(value) for _, _, value in _EXACT_V120_SCHEMA)
        self.assertEqual(actual, expected)
        self.assertTrue(all(" DEFAULT " not in f" {value.upper()} " for value in actual))

    def test_relative_path_rejects_absolute_dot_parent_backslash_and_non_string(self) -> None:
        module = _profiles(self)
        self.assertEqual(module.relative_path("authority/batches/000001/TASK10-A/preflight.json"),
                         "authority/batches/000001/TASK10-A/preflight.json")
        for value in ("", ".", "../escape", "a/../b", "/absolute", "a\\b", True, Path("x")):
            with self.subTest(value=value), self.assertRaises(InputFormatError):
                module.relative_path(value)

    def test_candidate_digest_oracle_is_literal_ordered_and_path_independent(self) -> None:
        prefixes = _approved_prefix()
        expected = (
            A_CANDIDATE_DIGEST,
            AB_CANDIDATE_DIGEST,
            ABC_CANDIDATE_DIGEST,
        )
        for length, digest in enumerate(expected, start=1):
            with self.subTest(length=length):
                payload = _candidate_identity_payload(prefixes[:length])
                self.assertEqual(tuple(payload), (
                    "schema", "baseline", "target_release_version", "batch_ledger",
                    "candidate_projection", "image_projection", "counts",
                ))
                for image in payload["image_projection"]:
                    self.assertEqual(tuple(image), (
                        "batch_ordinal", "batch_id", "proposed_question_id", "image_order",
                        "source_relative_path", "candidate_relative_path", "sha256",
                        "size_bytes", "kind", "role",
                    ))
                    self.assertIs(type(image["batch_ordinal"]), int)
                    self.assertIs(type(image["image_order"]), int)
                    self.assertIs(type(image["size_bytes"]), int)
                self.assertEqual(
                    hashlib.sha256(_canonical_file(payload)).hexdigest(), digest,
                )
                moved = json.loads(json.dumps(payload, ensure_ascii=False))
                self.assertNotIn("package_root", json.dumps(moved, ensure_ascii=False))
                self.assertNotIn("candidate_dir", json.dumps(moved, ensure_ascii=False))
                self.assertEqual(hashlib.sha256(_canonical_file(moved)).hexdigest(), digest)


if __name__ == "__main__":
    unittest.main()
