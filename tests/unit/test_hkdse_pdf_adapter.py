from __future__ import annotations

import hashlib
import importlib
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest

from pypdf import PdfWriter


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.errors import OutputConflictError, PipelineError
from joy_m2.ingest.hkdse_pdf_models import HkdsePdfAdapterBlockedError


FIXTURE = ROOT / "tests" / "fixtures" / "task10b"
MODULE_NAME = "joy_m2.ingest.hkdse_pdf_adapter"


def adapter(test_case: unittest.TestCase):
    spec = importlib.util.find_spec(MODULE_NAME)
    test_case.assertIsNotNone(
        spec,
        "Task 10B hkdse_pdf_adapter must exist before adapter behavior can pass",
    )
    return importlib.import_module(MODULE_NAME)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )


class AdapterCase(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        for name in ("data/staging", "data/baselines", "releases"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.config = PipelineConfig(self.root)
        self.pp = self.root / "pp.pdf"
        self.ms = self.root / "ms.pdf"
        self._pdf(self.pp, 2)
        self._pdf(self.ms, 1)
        self.staging = self.root / "staging.json"
        self.pass_a = self.root / "pass-a.json"
        self.pass_b = self.root / "pass-b.json"
        self.output = self.root / "data" / "staging" / "review"
        self._write_valid_inputs()

    def tearDown(self):
        self.temporary.cleanup()

    def _pdf(self, path: Path, pages: int) -> None:
        writer = PdfWriter()
        for _ in range(pages):
            writer.add_blank_page(width=612, height=792)
        with path.open("wb") as stream:
            writer.write(stream)

    def _write_valid_inputs(self) -> None:
        staging = json.loads((FIXTURE / "staging.json").read_text(encoding="utf-8"))
        staging["source_pair"]["pp"]["sha256"] = sha(self.pp)
        staging["source_pair"]["ms"]["sha256"] = sha(self.ms)
        write_json(self.staging, staging)
        staging_sha = sha(self.staging)
        for fixture, target, pass_id in (
            ("pass-a.json", self.pass_a, "A"),
            ("pass-b.json", self.pass_b, "B"),
        ):
            value = json.loads((FIXTURE / fixture).read_text(encoding="utf-8"))
            value.update(
                pass_id=pass_id,
                staging_sha256=staging_sha,
                pp_sha256=sha(self.pp),
                ms_sha256=sha(self.ms),
            )
            write_json(target, value)

    def propose(self):
        module = adapter(self)
        return module.propose_hkdse_pdf_transcription(
            self.staging,
            self.pp,
            self.ms,
            self.pass_a,
            self.pass_b,
            self.output,
            self.config,
        )


class HkdsePdfSourceValidationTests(AdapterCase):
    def test_valid_source_reaches_transcription_proposal(self):
        with self.assertRaisesRegex(NotImplementedError, "comparison"):
            self.propose()

    def test_pdf_sha_mismatch_blocks_before_output(self):
        staging = json.loads(self.staging.read_text(encoding="utf-8"))
        staging["source_pair"]["pp"]["sha256"] = "0" * 64
        write_json(self.staging, staging)
        with self.assertRaises(HkdsePdfAdapterBlockedError) as captured:
            self.propose()
        self.assertEqual(captured.exception.issues[0].code, "pdf_identity_mismatch")
        self.assertFalse(self.output.exists())

    def test_pdf_page_count_mismatch_blocks_before_output(self):
        staging = json.loads(self.staging.read_text(encoding="utf-8"))
        staging["source_pair"]["ms"]["page_count"] = 2
        write_json(self.staging, staging)
        with self.assertRaises(HkdsePdfAdapterBlockedError) as captured:
            self.propose()
        self.assertIn("pdf_page_mismatch", tuple(issue.code for issue in captured.exception.issues))
        self.assertFalse(self.output.exists())

    def test_invalid_pdf_signature_is_rejected_as_source_identity_failure(self):
        self.pp.write_bytes(b"not a pdf")
        staging = json.loads(self.staging.read_text(encoding="utf-8"))
        staging["source_pair"]["pp"]["sha256"] = sha(self.pp)
        write_json(self.staging, staging)
        with self.assertRaises(HkdsePdfAdapterBlockedError) as captured:
            self.propose()
        self.assertEqual(captured.exception.issues[0].code, "pdf_identity_mismatch")

    def test_staging_duplicate_keys_and_wrong_count_are_fatal(self):
        self.staging.write_text('{"schema":"joy_m2_staging_batch_v1","schema":"duplicate"}\n')
        with self.assertRaises(HkdsePdfAdapterBlockedError) as captured:
            self.propose()
        self.assertEqual(captured.exception.issues[0].code, "staging_contract_mismatch")
        self.assertFalse(self.output.exists())

        self._write_valid_inputs()
        staging = json.loads(self.staging.read_text(encoding="utf-8"))
        staging["summary"]["complete_questions"] = 2
        write_json(self.staging, staging)
        with self.assertRaises(HkdsePdfAdapterBlockedError):
            self.propose()

    def test_pass_source_identity_order_and_marks_must_match_staging(self):
        for mutation in ("digest", "order", "marks"):
            with self.subTest(mutation=mutation):
                self._write_valid_inputs()
                value = json.loads(self.pass_b.read_text(encoding="utf-8"))
                if mutation == "digest":
                    value["pp_sha256"] = "f" * 64
                elif mutation == "order":
                    value["records"][0]["staging_id"] = "HKDSE-2012-M2-Q99"
                else:
                    value["records"][0]["marks"] = 4
                write_json(self.pass_b, value)
                with self.assertRaises(HkdsePdfAdapterBlockedError) as captured:
                    self.propose()
                self.assertIn(
                    "extraction_pass_invalid",
                    tuple(issue.code for issue in captured.exception.issues),
                )
                self.assertFalse(self.output.exists())

    def test_pass_loader_rejects_duplicate_keys_and_extra_fields(self):
        module = adapter(self)
        self.pass_a.write_text('{"schema_version":"x","schema_version":"y"}\n')
        with self.assertRaises(HkdsePdfAdapterBlockedError):
            module.load_hkdse_pdf_extraction_pass(self.pass_a)
        self._write_valid_inputs()
        value = json.loads(self.pass_a.read_text(encoding="utf-8"))
        value["absolute_path"] = "/private/source.pdf"
        write_json(self.pass_a, value)
        with self.assertRaises(HkdsePdfAdapterBlockedError):
            module.load_hkdse_pdf_extraction_pass(self.pass_a)

    def test_output_must_be_new_strict_staging_descendant(self):
        module = adapter(self)
        with self.assertRaises(PipelineError):
            module.propose_hkdse_pdf_transcription(
                self.staging,
                self.pp,
                self.ms,
                self.pass_a,
                self.pass_b,
                self.root / "outside",
                self.config,
            )
        self.output.mkdir()
        with self.assertRaises(OutputConflictError):
            self.propose()


if __name__ == "__main__":
    unittest.main()
