from __future__ import annotations

from contextlib import ExitStack, contextmanager
from dataclasses import FrozenInstanceError, MISSING, fields, is_dataclass
import builtins
import hashlib
import importlib
import importlib.util
import inspect
import io
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest import mock
import zipfile
from typing import get_type_hints


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.errors import PipelineError
from joy_m2.ingest.adapter import adapt_mmd_package
from joy_m2.ingest.adapter_models import MmdAdapterBlockedError, MmdAdapterIssue


PARSER_MODULE = "joy_m2.ingest.mmd_parser"
NOT_IMPLEMENTED_MESSAGE = "Task 9B adapter behavior is not implemented"
HEX_ZERO = "0" * 64


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


class ParserRedCase(unittest.TestCase):
    """B4/D3-only harness; D4-D7 assertions live in the integration module."""

    def _fail_at_public_scaffold(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "source.mmd"
            source_bytes = b"plain MMD source\n"
            source_path.write_bytes(source_bytes)
            selection_manifest_path = root / "selection.json"
            selection_manifest_path.write_text(
                _canonical_json(
                    {
                        "schema_version": "task9b-mmd-adapter-v1",
                        "batch_id": "TASK9B-PARSER-D3",
                        "source_kind": "mmd",
                        "source_sha256": _sha256(source_bytes),
                        "primary_member": source_path.name,
                        "answer_member": None,
                        "source_id": "TASK9B-PARSER-D3-SOURCE",
                        "chapter": "向量及其应用",
                        "expected_candidate_count": 0,
                        "selections": [],
                    }
                ),
                encoding="utf-8",
            )
            output_dir = root / "data" / "staging" / "adapted"
            try:
                adapt_mmd_package(
                    selection_manifest_path,
                    source_path,
                    output_dir,
                    PipelineConfig(root),
                )
            except NotImplementedError as exc:
                self.assertEqual(str(exc), NOT_IMPLEMENTED_MESSAGE)
                self.assertFalse(output_dir.exists())
                self.fail(f"adapter behavior RED: {exc}")
            self.fail("parser module is absent but the fixed adapter scaffold did not fail")

    def parser_module(self):
        if importlib.util.find_spec(PARSER_MODULE) is None:
            self._fail_at_public_scaffold()
        return importlib.import_module(PARSER_MODULE)

    def source_member(self, relative_path: str, content: bytes):
        module = self.parser_module()
        return module._SourceMember(relative_path, _sha256(content), content)

    def parse_document(self, primary: bytes, answer: bytes | None = None):
        module = self.parser_module()
        primary_member = module._SourceMember(
            "source/primary.mmd",
            _sha256(primary),
            primary,
        )
        answer_member = None
        if answer is not None:
            answer_member = module._SourceMember(
                "source/answer.mmd",
                _sha256(answer),
                answer,
            )
        with self.forbid_parser_io(module):
            return module._parse_source_document(primary_member, answer_member)

    @contextmanager
    def forbid_parser_io(self, module):
        """Forbid common filesystem/archive routes, including imported aliases."""

        forbidden = {
            "builtins.open": builtins.open,
            "io.open": io.open,
            "os.open": os.open,
            "os.stat": os.stat,
            "os.lstat": os.lstat,
            "os.listdir": os.listdir,
            "os.scandir": os.scandir,
            "os.walk": os.walk,
            "os.readlink": os.readlink,
            "os.access": os.access,
            "os.mkdir": os.mkdir,
            "os.makedirs": os.makedirs,
            "os.remove": os.remove,
            "os.unlink": os.unlink,
            "os.rename": os.rename,
            "os.replace": os.replace,
            "zipfile.ZipFile": zipfile.ZipFile,
            "zipfile.is_zipfile": zipfile.is_zipfile,
            "Path.open": Path.open,
            "Path.read_bytes": Path.read_bytes,
            "Path.read_text": Path.read_text,
            "Path.write_bytes": Path.write_bytes,
            "Path.write_text": Path.write_text,
            "Path.stat": Path.stat,
            "Path.lstat": Path.lstat,
            "Path.exists": Path.exists,
            "Path.is_file": Path.is_file,
            "Path.is_dir": Path.is_dir,
            "Path.resolve": Path.resolve,
            "Path.iterdir": Path.iterdir,
            "Path.glob": Path.glob,
            "Path.rglob": Path.rglob,
            "Path.mkdir": Path.mkdir,
            "Path.touch": Path.touch,
            "Path.unlink": Path.unlink,
            "Path.rename": Path.rename,
            "Path.replace": Path.replace,
        }

        def blocked(label: str):
            def call(*_args, **_kwargs):
                raise AssertionError(f"private parser performed forbidden I/O via {label}")

            return call

        targets = {
            "builtins.open": "builtins.open",
            "io.open": "io.open",
            "os.open": "os.open",
            "os.stat": "os.stat",
            "os.lstat": "os.lstat",
            "os.listdir": "os.listdir",
            "os.scandir": "os.scandir",
            "os.walk": "os.walk",
            "os.readlink": "os.readlink",
            "os.access": "os.access",
            "os.mkdir": "os.mkdir",
            "os.makedirs": "os.makedirs",
            "os.remove": "os.remove",
            "os.unlink": "os.unlink",
            "os.rename": "os.rename",
            "os.replace": "os.replace",
            "zipfile.ZipFile": "zipfile.ZipFile",
            "zipfile.is_zipfile": "zipfile.is_zipfile",
        }
        path_methods = (
            "open",
            "read_bytes",
            "read_text",
            "write_bytes",
            "write_text",
            "stat",
            "lstat",
            "exists",
            "is_file",
            "is_dir",
            "resolve",
            "iterdir",
            "glob",
            "rglob",
            "mkdir",
            "touch",
            "unlink",
            "rename",
            "replace",
        )
        with ExitStack() as stack:
            for target, label in targets.items():
                stack.enter_context(mock.patch(target, new=blocked(label)))
            for name in path_methods:
                stack.enter_context(
                    mock.patch.object(Path, name, new=blocked(f"Path.{name}"))
                )
            # A parser that imported an I/O function directly before the guard must
            # not evade it. Patch only exact known aliases, not arbitrary callables.
            for name, value in tuple(vars(module).items()):
                for label, original in forbidden.items():
                    if value is original and name not in {
                        "Path",
                        "PurePath",
                        "PurePosixPath",
                    }:
                        stack.enter_context(
                            mock.patch.object(module, name, new=blocked(label))
                        )
                        break
            yield

    def assert_parser_issue(
        self,
        primary: bytes,
        *,
        reason: str,
        field: str = "primary_member",
        answer: bytes | None = None,
        code: str = "mmd_parse_failed",
        expected_locator: str | None = None,
        expected_proposed_id: str | None = None,
        expected_evidence: dict[str, object] | None = None,
    ):
        with self.assertRaises(MmdAdapterBlockedError) as caught:
            self.parse_document(primary, answer)
        self.assertEqual(len(caught.exception.issues), 1)
        issue = caught.exception.issues[0]
        self.assertEqual(
            (
                issue.code,
                issue.severity,
                issue.proposed_question_id,
                issue.field,
            ),
            (code, "blocking", expected_proposed_id, field),
        )
        if expected_locator is not None:
            self.assertEqual(issue.source_locator, expected_locator)
        evidence = json.loads(issue.evidence)
        self.assertEqual(evidence["reason"], reason)
        self.assertEqual(issue.evidence, _canonical_json(evidence))
        if code == "mmd_parse_failed":
            self.assertEqual(
                set(evidence),
                {"end_byte", "member", "reason", "start_byte"},
            )
            self.assertEqual(
                evidence["member"],
                "source/answer.mmd" if field == "answer_member" else "source/primary.mmd",
            )
            for name in ("start_byte", "end_byte"):
                self.assertTrue(
                    evidence[name] is None or type(evidence[name]) is int,
                    f"{name} must be an exact int or null",
                )
        elif code == "archive_member_unsafe":
            self.assertEqual(set(evidence), {"raw_target_sha256", "reason"})
            self.assertRegex(evidence["raw_target_sha256"], r"^[0-9a-f]{64}$")
        self.assertNotIn("/tmp/", issue.source_locator)
        self.assertNotIn(str(Path.cwd()), issue.source_locator)
        self.assertNotIn("/tmp/", issue.evidence)
        if expected_evidence is not None:
            self.assertEqual(evidence, expected_evidence)
        return issue

    def assert_question_numbers(
        self,
        source: str,
        expected_numbers: tuple[str, ...],
        expected_sections: tuple[str, ...],
    ):
        document = self.parse_document(source.encode("utf-8"))
        self.assertEqual(
            tuple(question.source_question_number for question in document.questions),
            expected_numbers,
        )
        self.assertEqual(
            tuple(question.source_section for question in document.questions),
            expected_sections,
        )
        return document


class PrivateParserContractTests(ParserRedCase):
    def test_private_parse_seam_has_exact_signature_annotations_and_export_boundary(self):
        module = self.parser_module()
        function = module._parse_source_document
        signature = inspect.signature(function)
        parameters = tuple(signature.parameters.values())
        hints = get_type_hints(function, vars(module), vars(module))
        self.assertEqual(tuple(value.name for value in parameters), ("primary_member", "answer_member"))
        self.assertEqual(
            tuple(value.kind for value in parameters),
            (
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
                inspect.Parameter.POSITIONAL_OR_KEYWORD,
            ),
        )
        self.assertIs(parameters[0].default, inspect.Parameter.empty)
        self.assertIsNone(parameters[1].default)
        self.assertIs(hints["primary_member"], module._SourceMember)
        self.assertEqual(hints["answer_member"], module._SourceMember | None)
        self.assertIs(hints["return"], module._SourceDocument)
        exported = tuple(getattr(module, "__all__", ()))
        self.assertNotIn("_parse_source_document", exported)
        for name in (
            "_SourceMember",
            "_SourceSpan",
            "_SourceImageRef",
            "_SourceQuestion",
            "_SourceDocument",
        ):
            self.assertNotIn(name, exported)

    def test_five_private_carriers_have_exact_fields_types_no_defaults_and_are_frozen(self):
        module = self.parser_module()
        expected = {
            "_SourceMember": (
                (("relative_path", str), ("sha256", str), ("content", bytes)),
            ),
            "_SourceSpan": (
                (
                    ("member_path", str),
                    ("start_byte", int),
                    ("end_byte", int),
                    ("role", str),
                    ("language", str),
                ),
            ),
            "_SourceImageRef": (
                (
                    ("source_order", int),
                    ("token_span", module._SourceSpan),
                    ("raw_target", str),
                    ("resolved_member", str | None),
                ),
            ),
            "_SourceQuestion": (
                (
                    ("source_order", int),
                    ("source_question_number", str),
                    ("source_section", str),
                    ("fragment_span", module._SourceSpan),
                    ("text_spans", tuple[module._SourceSpan, ...]),
                    ("solution_spans", tuple[module._SourceSpan, ...]),
                    ("explanation_spans", tuple[module._SourceSpan, ...]),
                    ("image_refs", tuple[module._SourceImageRef, ...]),
                ),
            ),
            "_SourceDocument": (
                (
                    ("primary_member", str),
                    ("members", tuple[module._SourceMember, ...]),
                    ("questions", tuple[module._SourceQuestion, ...]),
                ),
            ),
        }
        for name, (field_contract,) in expected.items():
            with self.subTest(carrier=name):
                carrier = getattr(module, name)
                self.assertTrue(is_dataclass(carrier))
                self.assertTrue(carrier.__dataclass_params__.frozen)
                self.assertEqual(
                    tuple(field.name for field in fields(carrier)),
                    tuple(field_name for field_name, _ in field_contract),
                )
                self.assertEqual(get_type_hints(carrier, vars(module), vars(module)), dict(field_contract))
                self.assertTrue(
                    all(
                        field.default is MISSING and field.default_factory is MISSING
                        for field in fields(carrier)
                    )
                )
        member = module._SourceMember("source/a.mmd", _sha256(b"x"), b"x")
        with self.assertRaises(FrozenInstanceError):
            member.relative_path = "source/b.mmd"

    def test_carriers_validate_exact_paths_sha_indices_offsets_roles_and_languages(self):
        module = self.parser_module()
        content = b"x"
        content_sha = _sha256(content)
        for path in ("/a.mmd", "C:/a.mmd", "source\\a.mmd", "source/../a.mmd", "source//a.mmd"):
            with self.subTest(path=path), self.assertRaises(PipelineError):
                module._SourceMember(path, content_sha, content)
        for sha in ("A" * 64, "0" * 63, None):
            with self.subTest(sha=sha), self.assertRaises(PipelineError):
                module._SourceMember("source/a.mmd", sha, content)
        with self.assertRaises(PipelineError):
            module._SourceMember("source/a.mmd", HEX_ZERO, content)
        with self.assertRaises(PipelineError):
            module._SourceMember("source/a.mmd", content_sha, bytearray(b"x"))

        for start, end in ((True, 1), (0, True), (-1, 1), (1, 1), (2, 1)):
            with self.subTest(start=start, end=end), self.assertRaises(PipelineError):
                module._SourceSpan("source/a.mmd", start, end, "question", "en")
        for role in ("text", "answer", ""):
            with self.subTest(role=role), self.assertRaises(PipelineError):
                module._SourceSpan("source/a.mmd", 0, 1, role, "en")
        for language in ("english", "chinese", ""):
            with self.subTest(language=language), self.assertRaises(PipelineError):
                module._SourceSpan("source/a.mmd", 0, 1, "question", language)
        with self.assertRaises(PipelineError):
            module._SourceSpan("source/../a.mmd", 0, 1, "question", "en")

    def test_carriers_canonicalize_tuples_without_aliasing_and_enforce_order(self):
        module = self.parser_module()
        content_a = b"A"
        content_b = b"B"
        member_a = module._SourceMember("source/a.mmd", _sha256(content_a), content_a)
        member_b = module._SourceMember("source/b.mmd", _sha256(content_b), content_b)
        span_a = module._SourceSpan("source/a.mmd", 0, 1, "question", "en")
        span_b = module._SourceSpan("source/b.mmd", 0, 1, "question", "zh")
        question_a = module._SourceQuestion(0, "1", "例題", span_a, [span_a], [], [], [])
        question_b = module._SourceQuestion(1, "2", "例題", span_b, [span_b], [], [], [])
        members = [member_b, member_a]
        questions = [question_b, question_a]
        document = module._SourceDocument("source/a.mmd", members, questions)
        members.clear()
        questions.clear()
        self.assertEqual(document.members, (member_a, member_b))
        self.assertEqual(document.questions, (question_a, question_b))
        self.assertIs(type(document.members), tuple)
        self.assertIs(type(document.questions), tuple)
        self.assertIs(type(question_a.text_spans), tuple)
        self.assertIs(type(question_a.solution_spans), tuple)
        self.assertIs(type(question_a.explanation_spans), tuple)
        self.assertIs(type(question_a.image_refs), tuple)

    def test_question_canonicalizes_span_and_image_occurrence_order_without_aliasing(self):
        module = self.parser_module()
        content = b"abcdefghij"
        fragment = module._SourceSpan("source/a.mmd", 0, 10, "question", "und")
        first = module._SourceSpan("source/a.mmd", 0, 2, "question", "en")
        second = module._SourceSpan("source/a.mmd", 2, 4, "question", "zh")
        image_zero_span = module._SourceSpan("source/a.mmd", 4, 5, "image_token", "shared")
        image_one_span = module._SourceSpan("source/a.mmd", 5, 6, "image_token", "shared")
        image_zero = module._SourceImageRef(0, image_zero_span, "./images/a.jpg", None)
        image_one = module._SourceImageRef(1, image_one_span, "./images/b.jpg", None)
        text_spans = [second, first]
        image_refs = [image_one, image_zero]
        question = module._SourceQuestion(
            0,
            "1",
            "例題",
            fragment,
            text_spans,
            [],
            [],
            image_refs,
        )
        text_spans.clear()
        image_refs.clear()
        self.assertEqual(question.text_spans, (first, second))
        self.assertEqual(question.image_refs, (image_zero, image_one))
        document = module._SourceDocument(
            "source/a.mmd",
            [module._SourceMember("source/a.mmd", _sha256(content), content)],
            [question],
        )
        self.assertEqual(document.questions[0], question)

    def test_carriers_reject_out_of_bounds_undeclared_and_invalid_image_references(self):
        module = self.parser_module()
        member = module._SourceMember("source/a.mmd", _sha256(b"abc"), b"abc")
        good = module._SourceSpan("source/a.mmd", 0, 3, "question", "en")
        bad_bounds = module._SourceSpan("source/a.mmd", 0, 4, "question", "en")
        undeclared = module._SourceSpan("source/missing.mmd", 0, 1, "question", "en")
        image_span = module._SourceSpan("source/a.mmd", 0, 1, "image_token", "shared")
        for source_order in (True, -1, "0"):
            with self.subTest(source_order=source_order), self.assertRaises(PipelineError):
                module._SourceImageRef(source_order, image_span, "./images/a.jpg", None)
        with self.assertRaises(PipelineError):
            module._SourceImageRef(0, good, "./images/a.jpg", None)
        for raw_target, resolved_member in ((None, None), ("./images/a.jpg", 1)):
            with self.subTest(raw_target=raw_target, resolved_member=resolved_member), self.assertRaises(PipelineError):
                module._SourceImageRef(0, image_span, raw_target, resolved_member)
        with self.assertRaises(PipelineError):
            module._SourceImageRef(0, image_span, "./images/a.jpg", "images/../a.jpg")
        image_ref = module._SourceImageRef(
            0,
            image_span,
            "./images/a.jpg",
            "images/a.jpg",
        )
        image_question = module._SourceQuestion(
            0,
            "1",
            "例題",
            good,
            [module._SourceSpan("source/a.mmd", 1, 3, "question", "en")],
            [],
            [],
            [image_ref],
        )
        with self.assertRaises(PipelineError):
            module._SourceDocument("source/a.mmd", [member], [image_question])
        for invalid in (bad_bounds, undeclared):
            question = module._SourceQuestion(0, "1", "例題", invalid, [invalid], [], [], [])
            with self.subTest(span=invalid), self.assertRaises(PipelineError):
                module._SourceDocument("source/a.mmd", [member], [question])

    def test_document_rejects_missing_primary_duplicate_orders_and_noncontiguous_orders(self):
        module = self.parser_module()
        member = module._SourceMember("source/a.mmd", _sha256(b"abc"), b"abc")
        span = module._SourceSpan("source/a.mmd", 0, 3, "question", "en")

        def question(order: int):
            return module._SourceQuestion(order, str(order + 1), "例題", span, [span], [], [], [])

        with self.assertRaises(PipelineError):
            module._SourceDocument("source/missing.mmd", [member], [])
        with self.assertRaises(PipelineError):
            module._SourceDocument("source/a.mmd", [member, member], [])
        for values in ([question(0), question(0)], [question(1)], [question(0), question(2)]):
            with self.subTest(values=values), self.assertRaises(PipelineError):
                module._SourceDocument("source/a.mmd", [member], values)

    def test_question_rejects_invalid_scalar_tuple_item_and_occurrence_order_values(self):
        module = self.parser_module()
        fragment = module._SourceSpan("source/a.mmd", 0, 3, "question", "und")
        text = module._SourceSpan("source/a.mmd", 0, 1, "question", "en")
        image_span = module._SourceSpan("source/a.mmd", 1, 2, "image_token", "shared")
        image_ref = module._SourceImageRef(0, image_span, "./images/a.jpg", None)
        valid = (0, "1", "例題", fragment, [text], [], [], [image_ref])
        for index, invalid in ((0, True), (0, -1), (1, 1), (2, None), (3, image_span)):
            values = list(valid)
            values[index] = invalid
            with self.subTest(index=index, invalid=invalid), self.assertRaises(PipelineError):
                module._SourceQuestion(*values)
        for index, invalid in ((4, [object()]), (5, [text]), (6, [text]), (7, [object()])):
            values = list(valid)
            values[index] = invalid
            with self.subTest(index=index), self.assertRaises(PipelineError):
                module._SourceQuestion(*values)
        duplicate_ref = module._SourceImageRef(0, image_span, "./images/b.jpg", None)
        values = list(valid)
        values[7] = [image_ref, duplicate_ref]
        with self.assertRaises(PipelineError):
            module._SourceQuestion(*values)
        order_one_only = module._SourceImageRef(
            1,
            image_span,
            "./images/b.jpg",
            None,
        )
        values = list(valid)
        values[7] = [order_one_only]
        with self.assertRaises(PipelineError):
            module._SourceQuestion(*values)
        image_two_span = module._SourceSpan(
            "source/a.mmd",
            2,
            3,
            "image_token",
            "shared",
        )
        order_two = module._SourceImageRef(
            2,
            image_two_span,
            "./images/c.jpg",
            None,
        )
        values = list(valid)
        values[7] = [image_ref, order_two]
        with self.assertRaises(PipelineError):
            module._SourceQuestion(*values)


class ParserIoIsolationTests(ParserRedCase):
    def test_parser_io_guard_selftest_catches_builtins_io_os_pathlib_and_zipfile_routes(self):
        class EmptyModule:
            pass

        EmptyModule.stat_alias = os.stat
        EmptyModule.open_alias = builtins.open
        EmptyModule.is_zipfile_alias = zipfile.is_zipfile

        probes = (
            ("builtins.open", lambda: builtins.open("probe", "rb")),
            ("io.open", lambda: io.open("probe", "rb")),
            ("os.open", lambda: os.open("probe", os.O_RDONLY)),
            ("os.stat", lambda: os.stat("probe")),
            ("os.listdir", lambda: os.listdir(".")),
            ("Path.open", lambda: Path("probe").open("rb")),
            ("Path.read_bytes", lambda: Path("probe").read_bytes()),
            ("Path.resolve", lambda: Path("probe").resolve()),
            ("Path.iterdir", lambda: next(Path(".").iterdir())),
            ("zipfile.ZipFile", lambda: zipfile.ZipFile("probe.zip")),
            ("zipfile.is_zipfile", lambda: zipfile.is_zipfile("probe.zip")),
            ("direct os.stat alias", lambda: EmptyModule.stat_alias("probe")),
            ("direct builtins.open alias", lambda: EmptyModule.open_alias("probe", "rb")),
            ("direct zipfile.is_zipfile alias", lambda: EmptyModule.is_zipfile_alias("probe.zip")),
        )
        for label, probe in probes:
            with self.subTest(route=label):
                with self.assertRaisesRegex(AssertionError, "private parser performed forbidden I/O"):
                    with self.forbid_parser_io(EmptyModule):
                        probe()

    def test_private_parser_consumes_source_members_without_any_filesystem_or_archive_io(self):
        source = "例題 1\nEnglish vector.\n中文向量。\n".encode("utf-8")
        document = self.parse_document(source)
        self.assertEqual(len(document.questions), 1)


class ParserGrammarTests(ParserRedCase):
    def test_exact_example_markers_accept_every_1_to_11_spelling_and_spacing_form(self):
        for keyword in ("例題", "例题"):
            for number in range(1, 12):
                for separator in ("", " "):
                    with self.subTest(keyword=keyword, number=number, separator=separator):
                        document = self.assert_question_numbers(
                            f"{keyword}{separator}{number}\nEnglish.\n中文。\n",
                            (str(number),),
                            (keyword,),
                        )
                        self.assertEqual(document.questions[0].source_order, 0)

    def test_example_marker_rejects_out_of_range_spacing_indent_fullwidth_and_inline_prose(self):
        invalid_lines = (
            "例題 0",
            "例題 12",
            "例題  1",
            " 例題 1",
            "\v例題 1",
            "例題 １",
            "例題（1）",
            "例題 1 prose",
        )
        for line in invalid_lines:
            with self.subTest(line=line):
                self.assert_parser_issue(
                    f"{line}\nEnglish.\n中文。\n".encode("utf-8"),
                    reason="unsupported_grammar",
                )

    def test_exact_exercise_markers_accept_every_q1_to_q6_plain_and_bracketed_form(self):
        for number in range(1, 7):
            for template in ("Q{number}）", "\\item[Q{number}）]"):
                for suffix in ("\nEnglish.\n", " English.\n"):
                    marker = template.format(number=number)
                    with self.subTest(number=number, marker=marker, suffix=suffix):
                        self.assert_question_numbers(
                            f"應試練習\n{marker}{suffix}中文。\n",
                            (f"Q{number}",),
                            ("應試練習",),
                        )

    def test_exercise_marker_rejects_q0_q7_spacing_no_space_fullwidth_indent_and_vertical_tab(self):
        invalid_lines = (
            "Q0） English",
            "Q7） English",
            "Q1）English",
            "Q1）  English",
            "Q１） English",
            "Ｑ1） English",
            "Q（1） English",
            "Q1) English",
            " Q1） English",
            "\vQ1） English",
            "\\item[Q1）]English",
            "\\item[Q1）]  English",
        )
        for line in invalid_lines:
            with self.subTest(line=line):
                self.assert_parser_issue(
                    f"應試練習\n{line}\n中文。\n".encode("utf-8"),
                    reason="unsupported_grammar",
                )

    def test_exercise_marker_can_be_marker_only_or_one_space_plus_nonempty_prose(self):
        document = self.assert_question_numbers(
            "應試練習\nQ1）\nEnglish.\n中文。\nQ2） English.\n中文。\n",
            ("Q1", "Q2"),
            ("應試練習", "應試練習"),
        )
        first = document.questions[0]
        self.assertTrue(first.fragment_span.start_byte < first.fragment_span.end_byte)

    def test_exercise_section_state_repeats_resets_and_is_cleared_by_next_example(self):
        document = self.assert_question_numbers(
            "應試練習\nQ1） English.\n中文。\n"
            "應試練習\nQ2） English.\n中文。\n"
            "例題 3\nEnglish.\n中文。\n",
            ("Q1", "Q2", "3"),
            ("應試練習", "應試練習", "例題"),
        )
        self.assertEqual(tuple(question.source_order for question in document.questions), (0, 1, 2))
        self.assert_parser_issue(
            "應試練習\nQ1） English.\n中文。\n例題 2\nEnglish.\n中文。\nQ2） English.\n中文。\n".encode("utf-8"),
            reason="missing_section",
        )

    def test_q_marker_without_active_exercise_section_is_missing_section(self):
        source = "Q1） English.\n中文。\n".encode("utf-8")
        end = len("Q1）".encode("utf-8"))
        self.assert_parser_issue(
            source,
            reason="missing_section",
            expected_locator=f"source/primary.mmd#bytes=0:{end}",
            expected_evidence={
                "end_byte": end,
                "member": "source/primary.mmd",
                "reason": "missing_section",
                "start_byte": 0,
            },
        )

    def test_complete_question_keeps_nested_itemize_and_subparts_inside_parent(self):
        source = (
            "例題 1\nEnglish stem.\n中文題幹。\n"
            "\\begin{itemize}\n\\item[(a)] Part A\n\\item[(i)] Part i\n\\end{itemize}\n"
            "例題 2\nEnglish next.\n中文下一題。\n"
        ).encode("utf-8")
        document = self.parse_document(source)
        self.assertEqual(len(document.questions), 2)
        first = document.questions[0]
        fragment = source[first.fragment_span.start_byte:first.fragment_span.end_byte]
        self.assertIn(b"\\item[(a)]", fragment)
        self.assertIn(b"\\item[(i)]", fragment)
        self.assertNotIn("例題 2".encode("utf-8"), fragment)

    def test_local_solution_marker_closes_fragment_and_answer_body_uses_exact_boundaries(self):
        source = "例題 1\r\nEnglish.\r\n中文。\r\n題解 ：\r\nanswer  \r\n\r\n".encode("utf-8")
        document = self.parse_document(source)
        question = document.questions[0]
        marker_start = source.index("題解 ：".encode("utf-8"))
        self.assertEqual(
            (question.fragment_span.start_byte, question.fragment_span.end_byte),
            (0, marker_start),
        )
        rendered_solution = b"".join(
            source[span.start_byte:span.end_byte] for span in question.solution_spans
        ).decode("utf-8").replace("\r\n", "\n").replace("\r", "\n")
        self.assertEqual(rendered_solution, "answer  \n\n")
        self.assertEqual(question.explanation_spans, ())

    def test_multiple_local_solution_markers_keep_distinct_bodies_and_exclude_markers(self):
        source = (
            "例題 1\nEnglish.\n中文。\n"
            "題解：\nfirst answer\n"
            "題解 ：\nsecond answer\n"
            "例題 2\nNext.\n下一題。\n"
        ).encode("utf-8")
        document = self.parse_document(source)
        first = document.questions[0]
        bodies = tuple(
            source[span.start_byte:span.end_byte]
            for span in first.solution_spans
        )
        self.assertEqual(bodies, (b"first answer\n", b"second answer\n"))
        self.assertTrue(all("題解".encode("utf-8") not in body for body in bodies))
        self.assertEqual(first.explanation_spans, ())

    def test_separate_answer_accepts_zero_or_multiple_empty_lines_after_exact_marker(self):
        primary = "例題 1\nEnglish.\n中文。\n例題 2\nEnglish.\n中文。\n".encode("utf-8")
        for blanks in ("", "\n\n"):
            with self.subTest(blank_count=len(blanks)):
                answer = f"例題 1\n{blanks}題解：\nsolution one\n例題 2\n題解 ：\nsolution two\n".encode("utf-8")
                document = self.parse_document(primary, answer)
                self.assertEqual(len(document.questions), 2)
                self.assertEqual(
                    tuple(question.explanation_spans for question in document.questions),
                    ((), ()),
                )
                solution = b"".join(
                    answer[span.start_byte:span.end_byte]
                    for span in document.questions[0].solution_spans
                ).decode("utf-8")
                self.assertEqual(solution, "solution one\n")

    def test_separate_answer_heading_alias_is_unsupported_grammar(self):
        primary = "例題 1\nEnglish.\n中文。\n".encode("utf-8")
        for heading in ("答案 1", "解答 1", "Answer 1", "例題 1："):
            with self.subTest(heading=heading):
                answer = f"{heading}\n題解：\nsolution\n".encode("utf-8")
                self.assert_parser_issue(
                    primary,
                    answer=answer,
                    field="answer_member",
                    reason="unsupported_grammar",
                )

    def test_reference_and_immediate_dse_metadata_are_shared_spans(self):
        variants = (
            "例題 1\n參考\nDSE 2020 Paper 1\nEnglish.\n中文。\n",
            "例題 1\n參考 DSE 2021 Paper 2\nEnglish.\n中文。\n",
            "例題 1\nDSE 2022 Paper 1\nEnglish.\n中文。\n",
        )
        for source_text in variants:
            with self.subTest(source=source_text.splitlines()[1]):
                source = source_text.encode("utf-8")
                document = self.parse_document(source)
                question = document.questions[0]
                shared = b"".join(
                    source[span.start_byte:span.end_byte]
                    for span in question.text_spans
                    if span.language == "shared"
                ).decode("utf-8")
                self.assertIn(source_text.splitlines()[1], shared)

    def test_exact_fragment_span_and_sha_use_original_utf8_bytes_without_newline_normalization(self):
        source = "例題 1\r\nEnglish $x$  \r中文向量。\n題解：\r\nanswer\n".encode("utf-8")
        document = self.parse_document(source)
        question = document.questions[0]
        fragment = source[:source.index("題解：".encode("utf-8"))]
        observed = source[question.fragment_span.start_byte:question.fragment_span.end_byte]
        self.assertEqual(observed, fragment)
        self.assertEqual(_sha256(observed), hashlib.sha256(fragment).hexdigest())

    def test_text_and_image_spans_are_nonoverlapping_byte_complete_fragment_partition(self):
        source = "例題 1\nEnglish $x+y$. 中文。\n![](./images/a.jpg)\n".encode("utf-8")
        document = self.parse_document(source)
        question = document.questions[0]
        spans = sorted(
            (*question.text_spans, *(ref.token_span for ref in question.image_refs)),
            key=lambda span: span.start_byte,
        )
        self.assertEqual(spans[0].start_byte, question.fragment_span.start_byte)
        self.assertEqual(spans[-1].end_byte, question.fragment_span.end_byte)
        for previous, current in zip(spans, spans[1:]):
            self.assertEqual(previous.end_byte, current.start_byte)
        rebuilt = b"".join(source[span.start_byte:span.end_byte] for span in spans)
        self.assertEqual(
            rebuilt,
            source[question.fragment_span.start_byte:question.fragment_span.end_byte],
        )

    def test_inline_display_itemize_reference_and_image_tokens_are_atomic_shared_constructs(self):
        source = (
            "例題 1\n參考 DSE 2020\nEnglish $x+中文$ text.\n"
            "$$\n\\vec{a}+\\vec{b}\n$$\n"
            "\\begin{itemize}\n\\item[(a)] 中文部分\n\\end{itemize}\n"
            "![](./images/a.jpg)\n"
        ).encode("utf-8")
        document = self.parse_document(source)
        question = document.questions[0]
        math = b"$x+" + "中文".encode("utf-8") + b"$"
        display = b"$$\n\\vec{a}+\\vec{b}\n$$\n"
        shared_payloads = tuple(
            source[span.start_byte:span.end_byte]
            for span in question.text_spans
            if span.language == "shared"
        )
        self.assertIn(math, shared_payloads)
        self.assertIn(display, shared_payloads)
        self.assertEqual(len(question.image_refs), 1)
        self.assertEqual(question.image_refs[0].raw_target, "./images/a.jpg")
        self.assertEqual(question.image_refs[0].resolved_member, None)

    def test_empty_item_bracket_prefix_is_one_structural_shared_span(self):
        source = (
            "例題 1\nEnglish.\n"
            "\\begin{itemize}\n\\item[] 考慮向量。\n\\end{itemize}\n"
        ).encode("utf-8")
        document = self.parse_document(source)
        prefix = b"\\item[]"
        start = source.index(prefix)
        matching = tuple(
            span
            for span in document.questions[0].text_spans
            if (span.start_byte, span.end_byte) == (start, start + len(prefix))
        )
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].language, "shared")

    def test_complete_display_math_hides_marker_section_and_solution_lexemes_from_boundaries(self):
        source = (
            "例題 1\n"
            "$$\n"
            "例題 2\n"
            "應試練習\n"
            "Q1） not a question\n"
            "題解：\n"
            "$$\n"
            "English after display.\n中文。\n"
            "例題 2\nNext.\n下一題。\n"
        ).encode("utf-8")
        document = self.parse_document(source)
        self.assertEqual(
            tuple(question.source_question_number for question in document.questions),
            ("1", "2"),
        )
        first = document.questions[0]
        display = (
            b"$$\n"
            + "例題 2\n應試練習\nQ1） not a question\n題解：\n".encode("utf-8")
            + b"$$\n"
        )
        self.assertIn(
            display,
            tuple(
                source[span.start_byte:span.end_byte]
                for span in first.text_spans
                if span.language == "shared"
            ),
        )
        self.assertEqual(first.solution_spans, ())

    def test_empty_physical_line_and_lf_are_shared_not_inherited_prose_language(self):
        source = "例題 1\nEnglish prose.\n\n中文。\n".encode("utf-8")
        document = self.parse_document(source)
        blank_lf = source.index(b"\n\n") + 1
        matching = tuple(
            span
            for span in document.questions[0].text_spans
            if (span.start_byte, span.end_byte) == (blank_lf, blank_lf + 1)
        )
        self.assertEqual(len(matching), 1)
        self.assertEqual(matching[0].language, "shared")

    def test_line_terminator_after_atomic_token_belongs_to_final_non_image_text(self):
        source = "例題 1\nEnglish $x$ tail\n中文。\n".encode("utf-8")
        document = self.parse_document(source)
        tail_end = source.index(b" tail") + len(b" tail")
        matching = tuple(
            span
            for span in document.questions[0].text_spans
            if span.start_byte <= tail_end < span.end_byte
        )
        self.assertEqual(len(matching), 1)
        self.assertTrue(
            source[matching[0].start_byte:matching[0].end_byte].endswith(b" tail\n")
        )
        self.assertEqual(matching[0].language, "en")

    def test_escaped_dollar_does_not_open_inline_math(self):
        source = "例題 1\nCost \\$5 and vector.\n中文。\n".encode("utf-8")
        document = self.parse_document(source)
        self.assertEqual(len(document.questions), 1)

    def test_non_whole_line_display_delimiter_is_unsupported_grammar(self):
        self.assert_parser_issue(
            "例題 1\nEnglish $$x+y$$ prose.\n中文。\n".encode("utf-8"),
            reason="unsupported_grammar",
        )

    def test_malformed_itemize_is_unsupported_grammar(self):
        malformed = (
            "例題 1\n\\begin{itemize}\n\\item[(a)] no end\n",
            "例題 1\n\\end{itemize}\n",
            "例題 1\n\\begin{itemize} trailing\n\\end{itemize}\n",
        )
        for source in malformed:
            with self.subTest(source=source.splitlines()[1]):
                self.assert_parser_issue(source.encode("utf-8"), reason="unsupported_grammar")

    def test_unclosed_inline_and_display_math_are_unclosed_token(self):
        cases = (
            ("例題 1\nEnglish $x+y.\n中文。\n", "$x+y."),
            ("例題 1\n$$\n\\vec{a}\n", "$$\n\\vec{a}\n"),
        )
        for source_text, offending_text in cases:
            with self.subTest(source=source_text):
                source = source_text.encode("utf-8")
                offending = offending_text.encode("utf-8")
                start = source.index(offending)
                end = start + len(offending)
                self.assert_parser_issue(
                    source,
                    reason="unclosed_token",
                    expected_locator=f"source/primary.mmd#bytes={start}:{end}",
                    expected_evidence={
                        "end_byte": end,
                        "member": "source/primary.mmd",
                        "reason": "unclosed_token",
                        "start_byte": start,
                    },
                )

    def test_incomplete_image_tokens_are_unsupported_grammar(self):
        for token in ("![](./images/a.jpg", "![](./images/a.jpg]", "![x](./images/a.jpg)"):
            with self.subTest(token=token):
                self.assert_parser_issue(
                    f"例題 1\nEnglish. 中文。\n{token}\n".encode("utf-8"),
                    reason="unsupported_grammar",
                )

    def test_safe_but_nonapproved_image_target_is_unsupported_grammar(self):
        for target in ("images/a.jpg", "./assets/a.jpg", "a.jpg"):
            with self.subTest(target=target):
                source = f"例題 1\nEnglish. 中文。\n![]({target})\n".encode("utf-8")
                token = f"![]({target})".encode("utf-8")
                start = source.index(token)
                end = start + len(token)
                self.assert_parser_issue(
                    source,
                    reason="unsupported_grammar",
                    expected_locator=f"source/primary.mmd#bytes={start}:{end}",
                    expected_evidence={
                        "end_byte": end,
                        "member": "source/primary.mmd",
                        "reason": "unsupported_grammar",
                        "start_byte": start,
                    },
                )


class ParserDiagnosticTests(ParserRedCase):
    def test_invalid_utf8_uses_exact_d3_schema_and_no_locator(self):
        self.assert_parser_issue(
            b"\xff",
            reason="invalid_utf8",
            expected_locator="",
            expected_evidence={
                "end_byte": None,
                "member": "source/primary.mmd",
                "reason": "invalid_utf8",
                "start_byte": None,
            },
        )

    def test_primary_and_answer_invalid_utf8_emit_both_issues_before_line_parsing(self):
        module = self.parser_module()
        primary = self.source_member("source/primary.mmd", b"\xff")
        answer = self.source_member("source/answer.mmd", b"\xfe")
        with mock.patch.object(
            module,
            "_physical_lines",
            side_effect=AssertionError("line parsing must not start after decode failures"),
        ) as physical_lines:
            with self.assertRaises(MmdAdapterBlockedError) as caught:
                module._parse_source_document(primary, answer)
        physical_lines.assert_not_called()
        self.assertEqual(len(caught.exception.issues), 2)
        self.assertEqual(
            tuple(issue.field for issue in caught.exception.issues),
            ("answer_member", "primary_member"),
        )
        self.assertEqual(
            tuple(json.loads(issue.evidence)["reason"] for issue in caught.exception.issues),
            ("invalid_utf8", "invalid_utf8"),
        )

    def test_cross_member_and_cross_code_d3_issues_use_exact_stable_five_key_order(self):
        primary = (
            "題解：\n"
            "例題 1\nEnglish $unclosed\n中文。\n"
            "例題 2\nEnglish. 中文。\n![](/absolute.jpg)\n"
        ).encode("utf-8")
        answer = "invalid answer heading\n".encode("utf-8")
        with self.assertRaises(MmdAdapterBlockedError) as caught:
            self.parse_document(primary, answer)
        observed = caught.exception.issues
        exact_key = lambda issue: (
            issue.source_locator,
            issue.proposed_question_id or "",
            issue.code,
            issue.field,
            issue.evidence,
        )
        self.assertEqual(observed, tuple(sorted(observed, key=exact_key)))
        self.assertEqual(
            tuple((issue.code, issue.field) for issue in observed),
            (
                ("mmd_parse_failed", "answer_member"),
                ("mmd_parse_failed", "primary_member"),
                ("mmd_parse_failed", "primary_member"),
                ("archive_member_unsafe", "raw_target"),
            ),
        )
        self.assertEqual(
            tuple(json.loads(issue.evidence)["reason"] for issue in observed),
            (
                "unsupported_grammar",
                "broken_boundary",
                "unclosed_token",
                "image_target_absolute",
            ),
        )

    def test_broken_question_answer_boundary_is_exact_d3_reason(self):
        source = "題解：\nanswer before question\n".encode("utf-8")
        end = len("題解：".encode("utf-8"))
        self.assert_parser_issue(
            source,
            reason="broken_boundary",
            expected_locator=f"source/primary.mmd#bytes=0:{end}",
            expected_evidence={
                "end_byte": end,
                "member": "source/primary.mmd",
                "reason": "broken_boundary",
                "start_byte": 0,
            },
        )

    def test_defensive_unreachable_d3_reasons_have_exact_schema_without_fabricated_fixtures(self):
        # The approved marker rules are disjoint and validated SourceMember bytes
        # cannot naturally carry an invalid parser-created span. Lock these two
        # defensive diagnostics without pretending that a valid source triggers them.
        for reason in ("ambiguous_section", "invalid_span"):
            with self.subTest(reason=reason):
                evidence = {
                    "end_byte": None,
                    "member": "source/primary.mmd",
                    "reason": reason,
                    "start_byte": None,
                }
                issue = MmdAdapterIssue(
                    "mmd_parse_failed",
                    "blocking",
                    None,
                    "",
                    "primary_member",
                    _canonical_json(evidence),
                )
                self.assertEqual(
                    (
                        issue.code,
                        issue.severity,
                        issue.proposed_question_id,
                        issue.source_locator,
                        issue.field,
                        json.loads(issue.evidence),
                    ),
                    (
                        "mmd_parse_failed",
                        "blocking",
                        None,
                        "",
                        "primary_member",
                        evidence,
                    ),
                )

    def test_unsafe_image_targets_use_all_nine_ordered_single_reason_codes(self):
        cases = (
            ("C:/images/a.jpg", "image_target_drive_or_unc"),
            ("//server/share/a.jpg", "image_target_drive_or_unc"),
            ("\\\\server\\share\\a.jpg", "image_target_drive_or_unc"),
            ("/images/a.jpg", "image_target_absolute"),
            ("./images\\a.jpg", "image_target_backslash"),
            ("./images/../a.jpg", "image_target_traversal"),
            ("./images//a.jpg", "image_target_dot_or_empty_component"),
            ("./images/cafe\u0301.jpg", "image_target_nfc_collision"),
            ("./images/A.jpg", "image_target_casefold_collision"),
            ("./images/a\x00.jpg", "image_target_canonicalization"),
        )
        collision_suffix = {
            "image_target_nfc_collision": "![](./images/café.jpg)\n",
            "image_target_casefold_collision": "![](./images/a.jpg)\n",
        }
        for target, reason in cases:
            with self.subTest(target=target, reason=reason):
                source_text = (
                    "例題 1\nEnglish. 中文。\n"
                    f"![]({target})\n"
                    f"{collision_suffix.get(reason, '')}"
                )
                source = source_text.encode("utf-8")
                token = f"![]({target})".encode("utf-8")
                start = source.index(token)
                end = start + len(token)
                self.assert_parser_issue(
                    source,
                    reason=reason,
                    code="archive_member_unsafe",
                    field="raw_target",
                    expected_locator=f"source/primary.mmd#bytes={start}:{end}",
                    expected_evidence={
                        "raw_target_sha256": _sha256(target.encode("utf-8")),
                        "reason": reason,
                    },
                )

    def test_lone_nfd_target_is_canonicalization_but_nfc_collision_has_precedence(self):
        nfd_target = "./images/cafe\u0301.jpg"
        self.assert_parser_issue(
            f"例題 1\nEnglish. 中文。\n![]({nfd_target})\n".encode("utf-8"),
            reason="image_target_canonicalization",
            code="archive_member_unsafe",
            field="raw_target",
        )

        source = (
            "例題 1\nEnglish. 中文。\n"
            f"![]({nfd_target})\n"
            "![](./images/café.jpg)\n"
        ).encode("utf-8")
        with self.assertRaises(MmdAdapterBlockedError) as caught:
            self.parse_document(source)
        self.assertEqual(len(caught.exception.issues), 1)
        issue = caught.exception.issues[0]
        self.assertEqual((issue.code, issue.field), ("archive_member_unsafe", "raw_target"))
        self.assertEqual(json.loads(issue.evidence)["reason"], "image_target_nfc_collision")

    def test_casefold_collision_suppresses_lower_priority_canonicalization_for_whole_group(self):
        first_target = "./images/A\x00.jpg"
        second_target = "./images/a\x00.jpg"
        source = (
            "例題 1\nEnglish. 中文。\n"
            f"![]({first_target})\n"
            f"![]({second_target})\n"
        ).encode("utf-8")
        first_token = f"![]({first_target})".encode("utf-8")
        first_start = source.index(first_token)
        first_end = first_start + len(first_token)

        with self.assertRaises(MmdAdapterBlockedError) as caught:
            self.parse_document(source)

        self.assertEqual(len(caught.exception.issues), 1)
        issue = caught.exception.issues[0]
        self.assertEqual(
            (
                issue.code,
                issue.severity,
                issue.proposed_question_id,
                issue.source_locator,
                issue.field,
                json.loads(issue.evidence),
            ),
            (
                "archive_member_unsafe",
                "blocking",
                None,
                f"source/primary.mmd#bytes={first_start}:{first_end}",
                "raw_target",
                {
                    "raw_target_sha256": _sha256(first_target.encode("utf-8")),
                    "reason": "image_target_casefold_collision",
                },
            ),
        )

    def test_empty_leading_and_trailing_image_tail_forms_are_dot_or_empty_component(self):
        for target in (
            "./images/",
            "./images//a.jpg",
            "./images/./a.jpg",
            "./images/a.jpg/",
        ):
            with self.subTest(target=target):
                self.assert_parser_issue(
                    f"例題 1\nEnglish. 中文。\n![]({target})\n".encode("utf-8"),
                    code="archive_member_unsafe",
                    field="raw_target",
                    reason="image_target_dot_or_empty_component",
                )

    def test_drive_or_unc_precedes_backslash_traversal_and_other_target_threats(self):
        target = "C:\\..\\a.jpg"
        self.assert_parser_issue(
            f"例題 1\nEnglish. 中文。\n![]({target})\n".encode("utf-8"),
            code="archive_member_unsafe",
            field="raw_target",
            reason="image_target_drive_or_unc",
        )

    def test_plain_resource_normalization_escape_uses_exact_d3_reason(self):
        source_bytes = "例題 1\nEnglish. 中文。\n![](./images/link/a.jpg)\n".encode("utf-8")
        image_token = b"![](./images/link/a.jpg)"
        token_start = source_bytes.index(image_token)
        token_end = token_start + len(image_token)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside"
            outside.mkdir()
            (outside / "a.jpg").write_bytes(b"image")
            images = root / "images"
            images.mkdir()
            (images / "link").symlink_to(outside, target_is_directory=True)
            source = root / "source.mmd"
            source.write_bytes(source_bytes)
            selection = {
                "schema_version": "task9b-mmd-adapter-v1",
                "batch_id": "TASK9B-PARSER-D3",
                "source_kind": "mmd",
                "source_sha256": _sha256(source.read_bytes()),
                "primary_member": "source.mmd",
                "answer_member": None,
                "source_id": "TASK9B-PARSER-D3-SOURCE",
                "chapter": "向量及其应用",
                "expected_candidate_count": 0,
                "selections": [],
            }
            selection_path = root / "selection.json"
            selection_path.write_text(_canonical_json(selection), encoding="utf-8")
            try:
                adapt_mmd_package(
                    selection_path,
                    source,
                    root / "data" / "staging" / "adapted",
                    PipelineConfig(root),
                )
            except NotImplementedError as exc:
                self.assertEqual(str(exc), NOT_IMPLEMENTED_MESSAGE)
                self.fail(f"adapter behavior RED: {exc}")
            except MmdAdapterBlockedError as exc:
                self.assertEqual(len(exc.issues), 1)
                issue = exc.issues[0]
                self.assertEqual(
                    (issue.code, issue.severity, issue.proposed_question_id, issue.field),
                    ("archive_member_unsafe", "blocking", None, "raw_target"),
                )
                self.assertEqual(
                    issue.source_locator,
                    f"source.mmd#bytes={token_start}:{token_end}",
                )
                self.assertEqual(
                    issue.evidence,
                    _canonical_json({
                        "raw_target_sha256": _sha256(b"./images/link/a.jpg"),
                        "reason": "image_target_normalized_escape",
                    }),
                )
            else:
                self.fail("normalization-escaping image target was accepted")

    def test_multiple_independent_d3_issues_are_collected_without_d4_d7_noise(self):
        source = (
            "例題 1\nEnglish $unclosed\n中文。\n"
            "例題 2\nEnglish. 中文。\n![](/absolute.jpg)\n"
        ).encode("utf-8")
        with self.assertRaises(MmdAdapterBlockedError) as caught:
            self.parse_document(source)
        self.assertEqual(
            tuple(issue.code for issue in caught.exception.issues),
            ("mmd_parse_failed", "archive_member_unsafe"),
        )
        self.assertEqual(
            tuple(json.loads(issue.evidence)["reason"] for issue in caught.exception.issues),
            ("unclosed_token", "image_target_absolute"),
        )
        self.assertTrue(all(issue.proposed_question_id is None for issue in caught.exception.issues))
        self.assertTrue(all(issue.field in {"primary_member", "raw_target"} for issue in caught.exception.issues))


if __name__ == "__main__":
    unittest.main()
