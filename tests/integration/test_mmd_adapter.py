import builtins
import copy
from contextlib import ExitStack, contextmanager
from dataclasses import fields
import hashlib
import importlib
import importlib.util
import inspect
import io
import json
import os
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.errors import (
    ConfigurationError,
    InputMissingError,
    OutputConflictError,
    PipelineError,
)
from joy_m2.ingest.adapter import adapt_mmd_package
from joy_m2.ingest.adapter_models import (
    AdaptedImportPackage,
    MmdAdapterBlockedError,
    MmdAdapterIssue,
)
from joy_m2.ingest.manifest import load_import_manifest
from joy_m2.ingest.models import BatchImportManifest
from joy_m2.ingest.preflight import preflight_import
from joy_m2.models import ArtifactRef


MODULE_NAME = "joy_m2.ingest.adapter"
NOT_IMPLEMENTED_MESSAGE = "Task 9B adapter behavior is not implemented"
FIXTURE_ROOT = ROOT / "tests/fixtures/task9b"
REPRESENTATIVE_ROOT = FIXTURE_ROOT / "representative"
GOLDEN_ROOT = FIXTURE_ROOT / "golden"
BASELINE_PATH = ROOT / "releases/V1.18/Joy_M2_Complete_Question_DB_V1_18.sqlite3"
MANIFEST_FIELDS = (
    "schema_version",
    "batch_id",
    "project",
    "module",
    "chapter",
    "target_release_version",
    "candidate_records",
    "source_files",
    "answer_files",
    "image_files",
    "teacher_notes_files",
    "common_errors_files",
    "language_policy",
    "split_policy",
    "difficulty_policy",
    "tag_policy",
    "answer_policy",
    "explanation_policy",
)
FILE_EVIDENCE_FIELDS = ("relative_path", "sha256", "size_bytes", "kind")
RAW_CANDIDATE_FIELDS = {
    "proposed_question_id",
    "source_id",
    "source_question_number",
    "source_section",
    "source_fragment_hash",
    "question_text_original",
    "question_text_zh",
    "translation_status",
    "translation_evidence",
    "solution_original",
    "solution_verified",
    "answer_status",
    "explanation_text",
    "explanation_status",
    "explanation_evidence",
    "image_paths",
    "image_roles",
    "primary_type",
    "tags",
    "tag_status",
    "difficulty_level",
    "difficulty_status",
    "enrichment_status",
}


def _sha256(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _opaque_key_field(key: str, *, parent: str = "$") -> str:
    return f"{parent}[~key-sha256:{_sha256(key.encode('utf-8'))}]"


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _baseline_ref() -> ArtifactRef:
    content = BASELINE_PATH.read_bytes()
    return ArtifactRef(BASELINE_PATH, _sha256(content), len(content), "sqlite")


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in sorted(root.rglob("*"))
        if path.is_file()
    }


def _tree_state(root: Path) -> tuple[tuple[str, str, object], ...]:
    """Capture files, directories, and symlinks without normalizing the tree."""
    if not root.exists() and not root.is_symlink():
        return ()
    state: list[tuple[str, str, object]] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            state.append((relative, "symlink", os.readlink(path)))
        elif path.is_dir():
            state.append((relative, "directory", None))
        else:
            state.append((relative, "file", path.read_bytes()))
    return tuple(state)


def _minimal_selection(
    *,
    proposed_question_id: str = "TASK9B-INTEGRATION-01",
    number: str = "1",
    answer_mapping: str = "missing_from_source",
    answer_number: str | None = None,
    expected_image_members: list[str] | None = None,
) -> dict[str, object]:
    return {
        "proposed_question_id": proposed_question_id,
        "kind": "example",
        "number": number,
        "source_section": "例題",
        "language_layout": "english_then_chinese",
        "answer_mapping": answer_mapping,
        "answer_number": answer_number,
        "expected_image_members": expected_image_members or [],
        "primary_type": "向量",
        "tags": ["向量"],
        "tag_status": "proposed",
        "difficulty_level": 3,
        "difficulty_status": "proposed",
    }


def _minimal_manifest(
    source_bytes: bytes,
    *,
    source_kind: str = "mmd",
    source_sha256: str | None = None,
    primary_member: str = "source.mmd",
    answer_member: str | None = None,
    selections: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    selected = selections if selections is not None else [_minimal_selection()]
    return {
        "schema_version": "task9b-mmd-adapter-v1",
        "batch_id": "TASK9B-INTEGRATION-RED",
        "source_kind": source_kind,
        "source_sha256": source_sha256 or _sha256(source_bytes),
        "primary_member": primary_member,
        "answer_member": answer_member,
        "source_id": "TASK9B-INTEGRATION-SOURCE",
        "chapter": "向量及其应用",
        "expected_candidate_count": len(selected),
        "selections": selected,
    }


def adapter_module(test_case: unittest.TestCase):
    spec = importlib.util.find_spec(MODULE_NAME)
    test_case.assertIsNotNone(
        spec,
        "Task 9B adapter module must exist before its public API can pass",
    )
    return importlib.import_module(MODULE_NAME)


class AdapterApiTests(unittest.TestCase):
    def test_adapt_mmd_package_has_the_exact_approved_signature(self):
        module = adapter_module(self)
        function = getattr(module, "adapt_mmd_package", None)
        self.assertIsNotNone(function, "adapt_mmd_package must exist")

        signature = inspect.signature(function)
        parameters = tuple(signature.parameters.values())
        self.assertEqual(
            tuple(parameter.name for parameter in parameters),
            ("selection_manifest_path", "source_path", "output_dir", "config"),
        )
        self.assertEqual(
            tuple(parameter.annotation for parameter in parameters),
            (Path, Path, Path, PipelineConfig),
        )
        self.assertTrue(
            all(
                parameter.kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
                and parameter.default is inspect.Parameter.empty
                for parameter in parameters
            )
        )
        self.assertIs(signature.return_annotation, AdaptedImportPackage)

    def test_empty_selection_builds_an_empty_canonical_package(self):
        module = adapter_module(self)
        function = getattr(module, "adapt_mmd_package", None)
        self.assertIsNotNone(function, "adapt_mmd_package must exist")

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_bytes = b"plain MMD source\n"
            selection_manifest_path = root / "selection.json"
            source_path = root / "source.mmd"
            output_dir = root / "data" / "staging" / "adapted"
            config = PipelineConfig(root)
            source_path.write_bytes(source_bytes)
            selection_manifest_path.write_text(
                _canonical_json(
                    _minimal_manifest(source_bytes, selections=[])
                ),
                encoding="utf-8",
            )

            package = function(
                selection_manifest_path,
                source_path,
                output_dir,
                config,
            )

            self.assertIs(type(package), AdaptedImportPackage)
            self.assertEqual(package.package_root, output_dir)
            self.assertEqual(
                json.loads((output_dir / "records/candidates.json").read_text()),
                [],
            )
            self.assertTrue((output_dir / "import_manifest.json").is_file())


class AdapterIntegrationRedCase(unittest.TestCase):
    def invoke_behavior(
        self,
        selection_path: Path,
        source_path: Path,
        output_dir: Path,
        config: PipelineConfig,
    ) -> AdaptedImportPackage:
        try:
            return adapt_mmd_package(
                selection_path,
                source_path,
                output_dir,
                config,
            )
        except NotImplementedError as exc:
            self.assertEqual(str(exc), NOT_IMPLEMENTED_MESSAGE)
            self.fail(f"adapter behavior RED: {exc}")

    @contextmanager
    def assert_source_untouched(
        self,
        source_path: Path,
        *,
        unreadable_path: Path | None = None,
    ):
        accesses: list[str] = []
        unreadable_attempts: list[str] = []
        module = adapter_module(self)
        originals = {
            "builtins.open": builtins.open,
            "io.open": io.open,
            "os.open": os.open,
            "os.stat": os.stat,
            "os.lstat": os.lstat,
            "os.access": os.access,
            "Path.open": Path.open,
            "Path.read_bytes": Path.read_bytes,
            "Path.resolve": Path.resolve,
            "Path.stat": Path.stat,
            "Path.lstat": Path.lstat,
            "zipfile.is_zipfile": zipfile.is_zipfile,
        }

        def is_target(value: object) -> bool:
            return isinstance(value, (str, bytes, os.PathLike)) and Path(value) == source_path

        def guarded(label: str, original):
            def call(path, *args, **kwargs):
                if is_target(path):
                    accesses.append(label)
                    raise AssertionError(f"D0 accessed source through {label}")
                if (
                    unreadable_path is not None
                    and isinstance(path, (str, bytes, os.PathLike))
                    and Path(path) == unreadable_path
                    and label
                    in {
                        "builtins.open",
                        "io.open",
                        "os.open",
                        "Path.open",
                        "Path.read_bytes",
                    }
                ):
                    unreadable_attempts.append(label)
                    raise PermissionError("selection manifest is unreadable")
                return original(path, *args, **kwargs)

            return call

        targets = {
            "builtins.open": "builtins.open",
            "io.open": "io.open",
            "os.open": "os.open",
            "os.stat": "os.stat",
            "os.lstat": "os.lstat",
            "os.access": "os.access",
            "zipfile.is_zipfile": "zipfile.is_zipfile",
        }
        path_methods = ("open", "read_bytes", "resolve", "stat", "lstat")
        with ExitStack() as stack:
            for target, label in targets.items():
                stack.enter_context(patch(target, new=guarded(label, originals[label])))
            for name in path_methods:
                label = f"Path.{name}"
                stack.enter_context(
                    patch.object(Path, name, new=guarded(label, originals[label]))
                )
            for name, value in tuple(vars(module).items()):
                for label, original in originals.items():
                    if value is original and name != "Path":
                        stack.enter_context(
                            patch.object(module, name, new=guarded(label, original))
                        )
                        break
            yield unreadable_attempts
        self.assertEqual(accesses, [])

    @contextmanager
    def observe_fs_mutations(self):
        mutations: list[str] = []
        original_builtins_open = builtins.open
        original_io_open = io.open
        original_os_open = os.open
        original_os_mkdir = os.mkdir
        original_os_makedirs = os.makedirs
        original_os_rename = os.rename
        original_os_replace = os.replace
        original_path_open = Path.open
        original_path_write_bytes = Path.write_bytes
        original_path_write_text = Path.write_text
        original_path_touch = Path.touch
        original_path_mkdir = Path.mkdir
        original_path_rename = Path.rename
        original_path_replace = Path.replace

        def stream_open(label: str, original):
            def call(path, *args, **kwargs):
                mode = args[0] if args else kwargs.get("mode", "r")
                if any(token in mode for token in "wax+"):
                    mutations.append(label)
                return original(path, *args, **kwargs)

            return call

        def descriptor_open(path, flags, *args, **kwargs):
            if flags & (
                os.O_WRONLY
                | os.O_RDWR
                | os.O_CREAT
                | os.O_TRUNC
                | os.O_APPEND
            ):
                mutations.append("os.open")
            return original_os_open(path, flags, *args, **kwargs)

        def mutation(label: str, original):
            def call(*args, **kwargs):
                mutations.append(label)
                return original(*args, **kwargs)

            return call

        with (
            patch("builtins.open", new=stream_open("builtins.open", original_builtins_open)),
            patch("io.open", new=stream_open("io.open", original_io_open)),
            patch("os.open", new=descriptor_open),
            patch("os.mkdir", new=mutation("os.mkdir", original_os_mkdir)),
            patch("os.makedirs", new=mutation("os.makedirs", original_os_makedirs)),
            patch("os.rename", new=mutation("os.rename", original_os_rename)),
            patch("os.replace", new=mutation("os.replace", original_os_replace)),
            patch.object(Path, "open", new=stream_open("Path.open", original_path_open)),
            patch.object(
                Path,
                "write_bytes",
                new=mutation("Path.write_bytes", original_path_write_bytes),
            ),
            patch.object(
                Path,
                "write_text",
                new=mutation("Path.write_text", original_path_write_text),
            ),
            patch.object(Path, "touch", new=mutation("Path.touch", original_path_touch)),
            patch.object(Path, "mkdir", new=mutation("Path.mkdir", original_path_mkdir)),
            patch.object(Path, "rename", new=mutation("Path.rename", original_path_rename)),
            patch.object(Path, "replace", new=mutation("Path.replace", original_path_replace)),
        ):
            yield mutations

    @contextmanager
    def assert_historical_v116_zip_untouched(self):
        accesses: list[str] = []
        originals = {
            "builtins.open": builtins.open,
            "io.open": io.open,
            "os.open": os.open,
            "os.stat": os.stat,
            "os.lstat": os.lstat,
            "Path.open": Path.open,
            "Path.read_bytes": Path.read_bytes,
            "Path.read_text": Path.read_text,
            "Path.stat": Path.stat,
            "Path.lstat": Path.lstat,
            "zipfile.ZipFile": zipfile.ZipFile,
            "zipfile.is_zipfile": zipfile.is_zipfile,
        }

        def is_historical_zip(value: object) -> bool:
            if not isinstance(value, (str, bytes, os.PathLike)):
                return False
            path = Path(value)
            return "V1.16" in path.parts and path.suffix.lower() == ".zip"

        def guarded(label: str, original):
            def call(path, *args, **kwargs):
                if is_historical_zip(path):
                    accesses.append(label)
                    raise AssertionError(f"Task 9B accessed V1.16 ZIP through {label}")
                return original(path, *args, **kwargs)

            return call

        targets = {
            "builtins.open": "builtins.open",
            "io.open": "io.open",
            "os.open": "os.open",
            "os.stat": "os.stat",
            "os.lstat": "os.lstat",
            "zipfile.ZipFile": "zipfile.ZipFile",
            "zipfile.is_zipfile": "zipfile.is_zipfile",
        }
        path_methods = ("open", "read_bytes", "read_text", "stat", "lstat")
        with ExitStack() as stack:
            for target, label in targets.items():
                stack.enter_context(patch(target, new=guarded(label, originals[label])))
            for name in path_methods:
                label = f"Path.{name}"
                stack.enter_context(
                    patch.object(Path, name, new=guarded(label, originals[label]))
                )
            for module_name, module in tuple(sys.modules.items()):
                if module is None or not module_name.startswith("joy_m2.ingest"):
                    continue
                for name, value in tuple(vars(module).items()):
                    for label, original in originals.items():
                        if value is original and name not in {"Path", "zipfile"}:
                            stack.enter_context(
                                patch.object(module, name, new=guarded(label, original))
                            )
                            break
            yield
        self.assertEqual(accesses, [])

    def d0_issues(self, selection_bytes: bytes) -> tuple[MmdAdapterIssue, ...]:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path = root / "selection.json"
            selection_path.write_bytes(selection_bytes)
            source_path = root / "source.mmd"
            output_dir = root / "data/staging/adapted"
            with self.assert_source_untouched(source_path):
                with self.assertRaises(MmdAdapterBlockedError) as caught:
                    self.invoke_behavior(
                        selection_path,
                        source_path,
                        output_dir,
                        PipelineConfig(root),
                    )
            self.assertFalse(source_path.exists())
            self.assertFalse(output_dir.exists())
            return caught.exception.issues

    def assert_exact_d0_issue(
        self,
        issue: MmdAdapterIssue,
        *,
        field: str,
        actual: object,
        expected: object,
        reason: str,
    ) -> None:
        evidence = {"actual": actual, "expected": expected, "reason": reason}
        self.assertEqual(
            (
                issue.code,
                issue.severity,
                issue.proposed_question_id,
                issue.source_locator,
                issue.field,
                issue.evidence,
            ),
            (
                "source_contract_mismatch",
                "blocking",
                None,
                "",
                field,
                _canonical_json(evidence),
            ),
        )
        for runtime_root in (str(ROOT), str(Path(tempfile.gettempdir()))):
            self.assertNotIn(runtime_root, issue.field)
            self.assertNotIn(runtime_root, issue.evidence)

    def assert_d0_issue(
        self,
        selection_bytes: bytes,
        *,
        field: str,
        actual: object,
        expected: object,
        reason: str,
    ) -> None:
        issues = self.d0_issues(selection_bytes)
        self.assertEqual(len(issues), 1)
        self.assert_exact_d0_issue(
            issues[0],
            field=field,
            actual=actual,
            expected=expected,
            reason=reason,
        )

    def assert_d0_issues(
        self,
        selection_bytes: bytes,
        *,
        expected: tuple[tuple[str, object, object, str], ...],
    ) -> None:
        issues = self.d0_issues(selection_bytes)
        self.assertEqual(len(issues), len(expected))
        self.assertEqual(
            issues,
            tuple(
                sorted(
                    issues,
                    key=lambda issue: (
                        issue.source_locator,
                        issue.proposed_question_id or "",
                        issue.code,
                        issue.field,
                        issue.evidence,
                    ),
                )
            ),
        )
        for issue, (field, actual, expected_value, reason) in zip(issues, expected):
            self.assert_exact_d0_issue(
                issue,
                field=field,
                actual=actual,
                expected=expected_value,
                reason=reason,
            )

    def write_plain_input(
        self,
        root: Path,
        primary: bytes,
        selections: list[dict[str, object]],
        *,
        images: dict[str, bytes] | None = None,
    ) -> tuple[Path, Path, Path, PipelineConfig]:
        source_path = root / "source.mmd"
        source_path.write_bytes(primary)
        for relative_path, content in (images or {}).items():
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        selection_path = root / "selection.json"
        selection_path.write_text(
            _canonical_json(_minimal_manifest(primary, selections=selections)),
            encoding="utf-8",
        )
        return (
            selection_path,
            source_path,
            root / "data/staging/adapted",
            PipelineConfig(root),
        )

    def write_zip_input(
        self,
        root: Path,
        primary: bytes,
        selections: list[dict[str, object]],
        *,
        answer: bytes | None = None,
        images: dict[str, bytes] | None = None,
        member_order: tuple[str, ...] | None = None,
        timestamp: tuple[int, int, int, int, int, int] = (1980, 1, 1, 0, 0, 0),
        permissions: int = 0o100644,
        archive_comment: bytes = b"",
    ) -> tuple[Path, Path, Path, PipelineConfig]:
        member_bytes = {
            "source.mmd": primary,
            **({"answer.mmd": answer} if answer is not None else {}),
            **(images or {}),
        }
        ordered = member_order or tuple(member_bytes)
        self.assertEqual(set(ordered), set(member_bytes))
        source_path = root / "source.mmd.zip"
        with zipfile.ZipFile(source_path, "w") as archive:
            archive.comment = archive_comment
            for member in ordered:
                info = zipfile.ZipInfo(member, date_time=timestamp)
                info.create_system = 3
                info.external_attr = permissions << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, member_bytes[member])
        payload = _minimal_manifest(
            primary,
            source_kind="mmd_zip",
            source_sha256=_sha256(source_path.read_bytes()),
            answer_member="answer.mmd" if answer is not None else None,
            selections=selections,
        )
        selection_path = root / "selection.json"
        selection_path.write_text(_canonical_json(payload), encoding="utf-8")
        return (
            selection_path,
            source_path,
            root / "data/staging/adapted",
            PipelineConfig(root),
        )

    def run_representative(self, root: Path) -> AdaptedImportPackage:
        return self.invoke_behavior(
            REPRESENTATIVE_ROOT / "selection.json",
            REPRESENTATIVE_ROOT / "vector.mmd",
            root / "data/staging/adapted",
            PipelineConfig(root),
        )

    def read_candidate_payload(self, package: AdaptedImportPackage) -> list[dict[str, object]]:
        content = (package.package_root / "records/candidates.json").read_bytes()
        payload = json.loads(content)
        self.assertIs(type(payload), list)
        self.assertEqual(content, (_canonical_json(payload) + "\n").encode("utf-8"))
        return payload

    def read_source_map(self, package: AdaptedImportPackage) -> dict[str, object]:
        content = (package.package_root / "source/source-map.json").read_bytes()
        payload = json.loads(content)
        self.assertIs(type(payload), dict)
        self.assertEqual(content, _canonical_json(payload).encode("utf-8"))
        self.assertFalse(content.endswith(b"\n"))
        return payload

    def assert_span(self, span: object, *, text: bool = False) -> None:
        self.assertIs(type(span), dict)
        keys = ("end_byte", "language", "member", "start_byte") if text else (
            "end_byte", "member", "start_byte"
        )
        self.assertEqual(tuple(span), keys)
        self.assertIs(type(span["member"]), str)
        self.assertIs(type(span["start_byte"]), int)
        self.assertIs(type(span["end_byte"]), int)
        self.assertLess(span["start_byte"], span["end_byte"])
        if text:
            self.assertIn(span["language"], {"en", "zh", "shared", "und"})

    def assert_manifest_and_tree_binding(self, package: AdaptedImportPackage) -> None:
        manifest_path = package.package_root / "import_manifest.json"
        content = manifest_path.read_bytes()
        payload = json.loads(content)
        self.assertEqual(tuple(payload), MANIFEST_FIELDS)
        self.assertEqual(
            content,
            (
                json.dumps(
                    payload,
                    ensure_ascii=False,
                    separators=(",", ":"),
                    allow_nan=False,
                )
                + "\n"
            ).encode("utf-8"),
        )
        groups = {
            "candidate_records": "candidate_json",
            "source_files": "source",
            "answer_files": "answer",
            "image_files": "image",
            "teacher_notes_files": "teacher_notes",
            "common_errors_files": "common_errors",
        }
        declared: list[str] = []
        for group, kind in groups.items():
            self.assertIs(type(payload[group]), list)
            for evidence in payload[group]:
                self.assertIs(type(evidence), dict)
                self.assertEqual(tuple(evidence), FILE_EVIDENCE_FIELDS)
                self.assertIs(type(evidence["relative_path"]), str)
                self.assertRegex(evidence["sha256"], r"^[0-9a-f]{64}$")
                self.assertIs(type(evidence["size_bytes"]), int)
                self.assertIs(type(evidence["kind"]), str)
                self.assertEqual(evidence["kind"], kind)
                artifact = package.package_root / evidence["relative_path"]
                artifact_bytes = artifact.read_bytes()
                self.assertEqual(_sha256(artifact_bytes), evidence["sha256"])
                self.assertEqual(len(artifact_bytes), evidence["size_bytes"])
                declared.append(evidence["relative_path"])
        self.assertEqual(len(declared), len(set(declared)))
        actual = set(_tree_bytes(package.package_root)) - {"import_manifest.json"}
        self.assertEqual(actual, set(declared))
        self.assertEqual(package.manifest_path, manifest_path)
        self.assertEqual(
            package.manifest,
            load_import_manifest(manifest_path, package.package_root),
        )


class StrictSelectionManifestIntegrationRedTests(AdapterIntegrationRedCase):
    def test_d0_rejects_invalid_utf8_bom_invalid_json_and_non_object_without_source_access(self):
        cases = (
            ("invalid_utf8", b"\xff", "$", "undecodable_utf8", "strict_utf8", "invalid_utf8"),
            ("utf8_bom", b"\xef\xbb\xbf{}", "$", "utf8_bom", "no_bom", "utf8_bom"),
            ("invalid_json", b"{", "$", "invalid_json_syntax", "json_object", "invalid_json"),
            ("non_object_list", b"[]", "$", "array", "object", "non_object"),
            ("non_object_null", b"null", "$", "null", "object", "non_object"),
        )
        for label, selection_bytes, field, actual, expected, reason in cases:
            with self.subTest(case=label):
                self.assert_d0_issue(
                    selection_bytes,
                    field=field,
                    actual=actual,
                    expected=expected,
                    reason=reason,
                )

    def test_d0_selection_manifest_missing_nonregular_and_unreadable_boundaries_are_exact(self):
        valid_bytes = _canonical_json(_minimal_manifest(b"source")).encode("utf-8")
        for label in ("missing", "nonregular", "unreadable"):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                selection_path = root / "selection.json"
                source_path = root / "source.mmd"
                output_dir = root / "data/staging/adapted"
                if label == "nonregular":
                    selection_path.mkdir()
                elif label == "unreadable":
                    selection_path.write_bytes(valid_bytes)
                with (
                    self.assert_source_untouched(
                        source_path,
                        unreadable_path=selection_path if label == "unreadable" else None,
                    ) as unreadable_attempts,
                    self.observe_fs_mutations() as mutations,
                ):
                    if label == "missing":
                        with self.assertRaises(InputMissingError) as caught:
                            self.invoke_behavior(
                                selection_path,
                                source_path,
                                output_dir,
                                PipelineConfig(root),
                            )
                        self.assertIs(type(caught.exception), InputMissingError)
                    else:
                        with self.assertRaises(MmdAdapterBlockedError) as caught:
                            self.invoke_behavior(
                                selection_path,
                                source_path,
                                output_dir,
                                PipelineConfig(root),
                            )
                        self.assertEqual(len(caught.exception.issues), 1)
                        if label == "nonregular":
                            self.assert_exact_d0_issue(
                                caught.exception.issues[0],
                                field="$",
                                actual="non_regular_file",
                                expected="regular_file",
                                reason="wrong_type",
                            )
                        else:
                            self.assert_exact_d0_issue(
                                caught.exception.issues[0],
                                field="$",
                                actual="unreadable_file",
                                expected="readable",
                                reason="invalid_value",
                            )
                self.assertEqual(mutations, [])
                self.assertFalse(output_dir.exists())
                if label == "unreadable":
                    self.assertTrue(unreadable_attempts)

    def test_d0_rejects_duplicate_keys_at_top_and_nested_object_depth(self):
        payload = _minimal_manifest(b"source")
        encoded = _canonical_json(payload)
        cases = (
            (
                "top",
                encoded.replace(
                    '"batch_id":"TASK9B-INTEGRATION-RED"',
                    '"batch_id":"TASK9B-INTEGRATION-RED","batch_id":"DUPLICATE"',
                    1,
                ).encode("utf-8"),
                "$.batch_id",
            ),
            (
                "nested",
                encoded.replace(
                    '"number":"1"',
                    '"number":"1","number":"2"',
                    1,
                ).encode("utf-8"),
                "$.selections[0].number",
            ),
        )
        for label, selection_bytes, field in cases:
            with self.subTest(depth=label):
                self.assert_d0_issue(
                    selection_bytes,
                    field=field,
                    actual="duplicate",
                    expected="unique",
                    reason="duplicate_key",
                )

    def test_d0_opaque_paths_cover_path_like_extra_and_duplicate_keys_at_both_depths(self):
        base = _minimal_manifest(b"source")
        encoded = _canonical_json(base)
        key_kinds = (
            ("posix", "/Users/private/task9b-posix-secret"),
            ("unc", r"\\server\share\task9b-unc-secret"),
            ("drive", r"C:\private\task9b-drive-secret"),
        )
        for key_kind, raw_key in key_kinds:
            literal = _canonical_json(raw_key)
            for depth in ("top", "nested"):
                parent = "$" if depth == "top" else "$.selections[0]"
                extra = copy.deepcopy(base)
                target = extra if depth == "top" else extra["selections"][0]
                target[raw_key] = 1
                duplicate = (
                    encoded.replace(
                        "{",
                        "{" + literal + ":1," + literal + ":2,",
                        1,
                    )
                    if depth == "top"
                    else encoded.replace(
                        '"selections":[{',
                        '"selections":[{' + literal + ":1," + literal + ":2,",
                        1,
                    )
                )
                for reason, selection_bytes, actual, expected in (
                    (
                        "extra_key",
                        _canonical_json(extra).encode("utf-8"),
                        "present",
                        "absent",
                    ),
                    (
                        "duplicate_key",
                        duplicate.encode("utf-8"),
                        "duplicate",
                        "unique",
                    ),
                ):
                    with self.subTest(
                        key_kind=key_kind,
                        depth=depth,
                        reason=reason,
                    ):
                        issues = self.d0_issues(selection_bytes)
                        self.assertEqual(len(issues), 1)
                        self.assert_exact_d0_issue(
                            issues[0],
                            field=_opaque_key_field(raw_key, parent=parent),
                            actual=actual,
                            expected=expected,
                            reason=reason,
                        )
                        self.assertNotIn(raw_key, issues[0].field)
                        self.assertNotIn(raw_key, issues[0].evidence)

    def test_d0_opaque_paths_recurse_through_arbitrarily_nested_unknown_objects(self):
        base = _canonical_json(_minimal_manifest(b"source"))
        raw_key = r"\\server\share\task9b-deep-secret"
        literal = _canonical_json(raw_key)
        selection_bytes = base.replace(
            "{",
            '{"unknown":{"level_one":{"level_two":{'
            + literal
            + ":1,"
            + literal
            + ":2}}},",
            1,
        ).encode("utf-8")
        issues = self.d0_issues(selection_bytes)
        self.assertEqual(len(issues), 1)
        self.assert_exact_d0_issue(
            issues[0],
            field=_opaque_key_field(
                raw_key,
                parent="$.unknown.level_one.level_two",
            ),
            actual="duplicate",
            expected="unique",
            reason="duplicate_key",
        )
        self.assertNotIn(raw_key, issues[0].field)
        self.assertNotIn(raw_key, issues[0].evidence)

    def test_d0_path_like_invalid_enum_and_constant_scalars_use_only_sha256(self):
        base = _minimal_manifest(b"source")
        cases = (
            (
                "posix_constant",
                "/Users/private/task9b-schema-secret",
                "$.schema_version",
                "task9b-mmd-adapter-v1",
                lambda value, raw: value.__setitem__("schema_version", raw),
            ),
            (
                "unc_enum",
                r"\\server\share\task9b-source-kind-secret",
                "$.source_kind",
                ["mmd", "mmd_zip"],
                lambda value, raw: value.__setitem__("source_kind", raw),
            ),
            (
                "drive_enum",
                r"C:\private\task9b-selection-kind-secret",
                "$.selections[0].kind",
                ["example", "exercise"],
                lambda value, raw: value["selections"][0].__setitem__("kind", raw),
            ),
        )
        for label, raw_value, field, expected, mutate in cases:
            with self.subTest(case=label):
                payload = copy.deepcopy(base)
                mutate(payload, raw_value)
                issues = self.d0_issues(_canonical_json(payload).encode("utf-8"))
                self.assertEqual(len(issues), 1)
                self.assert_exact_d0_issue(
                    issues[0],
                    field=field,
                    actual=_sha256(raw_value.encode("utf-8")),
                    expected=expected,
                    reason="invalid_value",
                )
                self.assertNotIn(raw_value, issues[0].field)
                self.assertNotIn(raw_value, issues[0].evidence)

    def test_d0_preserves_duplicate_multiplicity_before_stable_final_sort(self):
        base = _canonical_json(_minimal_manifest(b"source"))
        selection_bytes = base.replace(
            "{",
            '{"alpha":1,"beta":1,"alpha":2,"beta":2,"alpha":3,',
            1,
        ).encode("utf-8")
        self.assert_d0_issues(
            selection_bytes,
            expected=(
                ("$.alpha", "duplicate", "unique", "duplicate_key"),
                ("$.alpha", "duplicate", "unique", "duplicate_key"),
                ("$.beta", "duplicate", "unique", "duplicate_key"),
            ),
        )

    def test_d0_rejects_missing_extra_and_wrong_runtime_types_at_both_schema_levels(self):
        source = b"source"
        base = _minimal_manifest(source)

        def changed(mutator):
            value = copy.deepcopy(base)
            mutator(value)
            return _canonical_json(value).encode("utf-8")

        cases = (
            ("missing_top", changed(lambda value: value.pop("chapter")), "$.chapter", "missing_key"),
            (
                "extra_top",
                changed(lambda value: value.__setitem__("unexpected", 1)),
                "$.unexpected",
                "extra_key",
            ),
            (
                "selections_not_array",
                changed(lambda value: value.__setitem__("selections", {})),
                "$.selections",
                "wrong_type",
            ),
            (
                "bool_count",
                changed(lambda value: value.__setitem__("expected_candidate_count", True)),
                "$.expected_candidate_count",
                "wrong_type",
            ),
            (
                "missing_selection_key",
                changed(lambda value: value["selections"][0].pop("number")),
                "$.selections[0].number",
                "missing_key",
            ),
            (
                "extra_selection_key",
                changed(lambda value: value["selections"][0].__setitem__("extra", 1)),
                "$.selections[0].extra",
                "extra_key",
            ),
            (
                "selection_kind_bool",
                changed(lambda value: value["selections"][0].__setitem__("kind", True)),
                "$.selections[0].kind",
                "wrong_type",
            ),
            (
                "images_not_array",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "expected_image_members", "images/a.jpg"
                    )
                ),
                "$.selections[0].expected_image_members",
                "wrong_type",
            ),
            (
                "tags_not_array",
                changed(lambda value: value["selections"][0].__setitem__("tags", {})),
                "$.selections[0].tags",
                "wrong_type",
            ),
            (
                "difficulty_bool",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "difficulty_level", True
                    )
                ),
                "$.selections[0].difficulty_level",
                "wrong_type",
            ),
            (
                "schema_version_not_string",
                changed(lambda value: value.__setitem__("schema_version", 1)),
                "$.schema_version",
                "wrong_type",
            ),
            (
                "batch_id_not_string",
                changed(lambda value: value.__setitem__("batch_id", None)),
                "$.batch_id",
                "wrong_type",
            ),
            (
                "source_kind_not_string",
                changed(lambda value: value.__setitem__("source_kind", True)),
                "$.source_kind",
                "wrong_type",
            ),
            (
                "source_sha_not_string",
                changed(lambda value: value.__setitem__("source_sha256", 1)),
                "$.source_sha256",
                "wrong_type",
            ),
            (
                "primary_member_not_string",
                changed(lambda value: value.__setitem__("primary_member", None)),
                "$.primary_member",
                "wrong_type",
            ),
            (
                "answer_member_wrong_type",
                changed(lambda value: value.__setitem__("answer_member", 1)),
                "$.answer_member",
                "wrong_type",
            ),
            (
                "source_id_not_string",
                changed(lambda value: value.__setitem__("source_id", [])),
                "$.source_id",
                "wrong_type",
            ),
            (
                "chapter_not_string",
                changed(lambda value: value.__setitem__("chapter", True)),
                "$.chapter",
                "wrong_type",
            ),
            (
                "selection_not_object",
                changed(lambda value: value.__setitem__("selections", ["selection"])),
                "$.selections[0]",
                "wrong_type",
            ),
            (
                "proposed_id_not_string",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "proposed_question_id", 1
                    )
                ),
                "$.selections[0].proposed_question_id",
                "wrong_type",
            ),
            (
                "number_not_string",
                changed(lambda value: value["selections"][0].__setitem__("number", 1)),
                "$.selections[0].number",
                "wrong_type",
            ),
            (
                "section_not_string",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "source_section", None
                    )
                ),
                "$.selections[0].source_section",
                "wrong_type",
            ),
            (
                "layout_not_string",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "language_layout", 1
                    )
                ),
                "$.selections[0].language_layout",
                "wrong_type",
            ),
            (
                "answer_mapping_not_string",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "answer_mapping", False
                    )
                ),
                "$.selections[0].answer_mapping",
                "wrong_type",
            ),
            (
                "answer_number_wrong_type",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "answer_number", []
                    )
                ),
                "$.selections[0].answer_number",
                "wrong_type",
            ),
            (
                "image_member_not_string",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "expected_image_members", [1]
                    )
                ),
                "$.selections[0].expected_image_members[0]",
                "wrong_type",
            ),
            (
                "primary_type_not_string",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "primary_type", None
                    )
                ),
                "$.selections[0].primary_type",
                "wrong_type",
            ),
            (
                "tag_not_string",
                changed(lambda value: value["selections"][0].__setitem__("tags", [1])),
                "$.selections[0].tags[0]",
                "wrong_type",
            ),
            (
                "tag_status_not_string",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "tag_status", None
                    )
                ),
                "$.selections[0].tag_status",
                "wrong_type",
            ),
            (
                "difficulty_status_not_string",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "difficulty_status", 1
                    )
                ),
                "$.selections[0].difficulty_status",
                "wrong_type",
            ),
        )
        exact_evidence = {
            "missing_top": ("missing", "present"),
            "extra_top": ("present", "absent"),
            "selections_not_array": ("object", "array"),
            "bool_count": ("boolean", "integer"),
            "missing_selection_key": ("missing", "present"),
            "extra_selection_key": ("present", "absent"),
            "selection_kind_bool": ("boolean", "string"),
            "images_not_array": ("string", "array"),
            "tags_not_array": ("object", "array"),
            "difficulty_bool": ("boolean", ["integer", "null"]),
            "schema_version_not_string": ("integer", "string"),
            "batch_id_not_string": ("null", "string"),
            "source_kind_not_string": ("boolean", "string"),
            "source_sha_not_string": ("integer", "string"),
            "primary_member_not_string": ("null", "string"),
            "answer_member_wrong_type": ("integer", ["string", "null"]),
            "source_id_not_string": ("array", "string"),
            "chapter_not_string": ("boolean", "string"),
            "selection_not_object": ("string", "object"),
            "proposed_id_not_string": ("integer", "string"),
            "number_not_string": ("integer", "string"),
            "section_not_string": ("null", "string"),
            "layout_not_string": ("integer", "string"),
            "answer_mapping_not_string": ("boolean", "string"),
            "answer_number_wrong_type": ("array", ["string", "null"]),
            "image_member_not_string": ("integer", "string"),
            "primary_type_not_string": ("null", "string"),
            "tag_not_string": ("integer", "string"),
            "tag_status_not_string": ("null", "string"),
            "difficulty_status_not_string": ("integer", "string"),
        }
        for label, selection_bytes, field, reason in cases:
            with self.subTest(case=label):
                actual, expected = exact_evidence[label]
                self.assert_d0_issue(
                    selection_bytes,
                    field=field,
                    actual=actual,
                    expected=expected,
                    reason=reason,
                )

    def test_d0_object_key_order_is_nonsemantic_while_selection_array_order_is_preserved(self):
        primary = "例題 1\nEnglish.\n中文。\n".encode("utf-8")
        payload = _minimal_manifest(primary)
        payload["selections"][0] = dict(reversed(tuple(payload["selections"][0].items())))
        payload = dict(reversed(tuple(payload.items())))
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "source.mmd"
            source_path.write_bytes(primary)
            selection_path = root / "selection.json"
            selection_path.write_text(
                json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )
            package = self.invoke_behavior(
                selection_path,
                source_path,
                root / "data/staging/adapted",
                PipelineConfig(root),
            )
            candidates = self.read_candidate_payload(package)
        self.assertEqual(
            [candidate["proposed_question_id"] for candidate in candidates],
            ["TASK9B-INTEGRATION-01"],
        )

    def test_d0_uses_the_exact_json_type_ladder_and_rejects_nonfinite_constants_as_json_syntax(self):
        base = _canonical_json(_minimal_manifest(b"source"))
        original = '"schema_version":"task9b-mmd-adapter-v1"'
        typed_cases = (
            ("integer", "1", "integer"),
            ("decimal_number", "1.0", "number"),
            ("exponent_number", "1e0", "number"),
            ("negative_zero", "-0.0", "number"),
            ("boolean", "true", "boolean"),
        )
        for label, literal, actual_type in typed_cases:
            with self.subTest(case=label):
                self.assert_d0_issue(
                    base.replace(original, f'"schema_version":{literal}', 1).encode("utf-8"),
                    field="$.schema_version",
                    actual=actual_type,
                    expected="string",
                    reason="wrong_type",
                )
        for literal in ("NaN", "Infinity", "-Infinity"):
            with self.subTest(nonfinite=literal):
                self.assert_d0_issue(
                    base.replace(original, f'"schema_version":{literal}', 1).encode("utf-8"),
                    field="$",
                    actual="invalid_json_syntax",
                    expected="json_object",
                    reason="invalid_json",
                )

    def test_d0_rejects_every_manifest_and_selection_value_validation_family(self):
        source = b"source"
        base = _minimal_manifest(source)

        def changed(mutator):
            value = copy.deepcopy(base)
            mutator(value)
            return _canonical_json(value).encode("utf-8")

        cases = (
            (
                "schema_version",
                changed(lambda value: value.__setitem__("schema_version", "task9b-v2")),
                "$.schema_version",
                "invalid_value",
            ),
            (
                "source_kind",
                changed(lambda value: value.__setitem__("source_kind", "zip")),
                "$.source_kind",
                "invalid_value",
            ),
            (
                "source_sha256",
                changed(lambda value: value.__setitem__("source_sha256", "A" * 64)),
                "$.source_sha256",
                "invalid_value",
            ),
            (
                "source_sha256_length",
                changed(lambda value: value.__setitem__("source_sha256", "a" * 63)),
                "$.source_sha256",
                "invalid_value",
            ),
            (
                "source_sha256_non_hex",
                changed(lambda value: value.__setitem__("source_sha256", "g" * 64)),
                "$.source_sha256",
                "invalid_value",
            ),
            (
                "batch_id_empty",
                changed(lambda value: value.__setitem__("batch_id", "")),
                "$.batch_id",
                "invalid_value",
            ),
            (
                "source_id_empty",
                changed(lambda value: value.__setitem__("source_id", "")),
                "$.source_id",
                "invalid_value",
            ),
            (
                "chapter_empty",
                changed(lambda value: value.__setitem__("chapter", "")),
                "$.chapter",
                "invalid_value",
            ),
            (
                "primary_member_empty",
                changed(lambda value: value.__setitem__("primary_member", "")),
                "$.primary_member",
                "invalid_value",
            ),
            (
                "primary_member_absolute",
                changed(lambda value: value.__setitem__("primary_member", "/source.mmd")),
                "$.primary_member",
                "invalid_value",
            ),
            (
                "primary_member_dot",
                changed(lambda value: value.__setitem__("primary_member", "./source.mmd")),
                "$.primary_member",
                "invalid_value",
            ),
            (
                "primary_member_parent",
                changed(lambda value: value.__setitem__("primary_member", "../source.mmd")),
                "$.primary_member",
                "invalid_value",
            ),
            (
                "primary_member_backslash",
                changed(lambda value: value.__setitem__("primary_member", r"dir\source.mmd")),
                "$.primary_member",
                "invalid_value",
            ),
            (
                "primary_member_empty_component",
                changed(lambda value: value.__setitem__("primary_member", "dir//source.mmd")),
                "$.primary_member",
                "invalid_value",
            ),
            (
                "primary_member_non_nfc",
                changed(lambda value: value.__setitem__("primary_member", "e\u0301.mmd")),
                "$.primary_member",
                "invalid_value",
            ),
            (
                "primary_member_suffix",
                changed(lambda value: value.__setitem__("primary_member", "source.MMD")),
                "$.primary_member",
                "invalid_value",
            ),
            (
                "answer_member_suffix",
                changed(
                    lambda value: (
                        value.__setitem__("source_kind", "mmd_zip"),
                        value.__setitem__("answer_member", "answer.txt"),
                    )
                ),
                "$.answer_member",
                "invalid_value",
            ),
            (
                "negative_candidate_count",
                changed(lambda value: value.__setitem__("expected_candidate_count", -1)),
                "$.expected_candidate_count",
                "invalid_value",
            ),
            (
                "proposed_id_empty",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "proposed_question_id", ""
                    )
                ),
                "$.selections[0].proposed_question_id",
                "invalid_value",
            ),
            (
                "kind",
                changed(lambda value: value["selections"][0].__setitem__("kind", "worked")),
                "$.selections[0].kind",
                "invalid_value",
            ),
            (
                "number_empty",
                changed(lambda value: value["selections"][0].__setitem__("number", "")),
                "$.selections[0].number",
                "invalid_value",
            ),
            (
                "source_section_empty",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "source_section", ""
                    )
                ),
                "$.selections[0].source_section",
                "invalid_value",
            ),
            (
                "language_layout",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "language_layout", "bilingual"
                    )
                ),
                "$.selections[0].language_layout",
                "invalid_value",
            ),
            (
                "answer_mapping",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "answer_mapping", "derived_answer"
                    )
                ),
                "$.selections[0].answer_mapping",
                "invalid_value",
            ),
            (
                "answer_number_empty",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "answer_number", ""
                    )
                ),
                "$.selections[0].answer_number",
                "invalid_value",
            ),
            (
                "image_member_absolute",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "expected_image_members", ["/images/a.jpg"]
                    )
                ),
                "$.selections[0].expected_image_members[0]",
                "invalid_value",
            ),
            (
                "image_member_wrong_root",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "expected_image_members", ["assets/a.jpg"]
                    )
                ),
                "$.selections[0].expected_image_members[0]",
                "invalid_value",
            ),
            (
                "image_member_dot",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "expected_image_members", ["images/./a.jpg"]
                    )
                ),
                "$.selections[0].expected_image_members[0]",
                "invalid_value",
            ),
            (
                "image_member_parent",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "expected_image_members", ["images/../a.jpg"]
                    )
                ),
                "$.selections[0].expected_image_members[0]",
                "invalid_value",
            ),
            (
                "image_member_backslash",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "expected_image_members", [r"images\a.jpg"]
                    )
                ),
                "$.selections[0].expected_image_members[0]",
                "invalid_value",
            ),
            (
                "image_member_empty_component",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "expected_image_members", ["images//a.jpg"]
                    )
                ),
                "$.selections[0].expected_image_members[0]",
                "invalid_value",
            ),
            (
                "image_member_non_nfc",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "expected_image_members", ["images/e\u0301.jpg"]
                    )
                ),
                "$.selections[0].expected_image_members[0]",
                "invalid_value",
            ),
            (
                "image_member_suffix",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "expected_image_members", ["images/a.JPG"]
                    )
                ),
                "$.selections[0].expected_image_members[0]",
                "invalid_value",
            ),
            (
                "primary_type_empty",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "primary_type", ""
                    )
                ),
                "$.selections[0].primary_type",
                "invalid_value",
            ),
            (
                "tag_empty",
                changed(lambda value: value["selections"][0].__setitem__("tags", [""])),
                "$.selections[0].tags[0]",
                "invalid_value",
            ),
            (
                "tag_status",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "tag_status", "verified"
                    )
                ),
                "$.selections[0].tag_status",
                "invalid_value",
            ),
            (
                "difficulty_level_low",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "difficulty_level", 0
                    )
                ),
                "$.selections[0].difficulty_level",
                "invalid_value",
            ),
            (
                "difficulty_level_high",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "difficulty_level", 6
                    )
                ),
                "$.selections[0].difficulty_level",
                "invalid_value",
            ),
            (
                "difficulty_status",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "difficulty_status", "verified"
                    )
                ),
                "$.selections[0].difficulty_status",
                "invalid_value",
            ),
        )
        exact_evidence = {
            "schema_version": ("task9b-v2", "task9b-mmd-adapter-v1"),
            "source_kind": ("zip", ["mmd", "mmd_zip"]),
            "source_sha256": (_sha256(("A" * 64).encode("utf-8")), "lowercase_hex_64"),
            "source_sha256_length": (_sha256(("a" * 63).encode("utf-8")), "lowercase_hex_64"),
            "source_sha256_non_hex": (_sha256(("g" * 64).encode("utf-8")), "lowercase_hex_64"),
            "batch_id_empty": ("", "non_empty_string"),
            "source_id_empty": ("", "non_empty_string"),
            "chapter_empty": ("", "non_empty_string"),
            "primary_member_empty": (_sha256(b""), "canonical_nfc_posix_mmd_member"),
            "primary_member_absolute": (_sha256(b"/source.mmd"), "canonical_nfc_posix_mmd_member"),
            "primary_member_dot": (_sha256(b"./source.mmd"), "canonical_nfc_posix_mmd_member"),
            "primary_member_parent": (_sha256(b"../source.mmd"), "canonical_nfc_posix_mmd_member"),
            "primary_member_backslash": (_sha256(r"dir\source.mmd".encode("utf-8")), "canonical_nfc_posix_mmd_member"),
            "primary_member_empty_component": (_sha256(b"dir//source.mmd"), "canonical_nfc_posix_mmd_member"),
            "primary_member_non_nfc": (_sha256("e\u0301.mmd".encode("utf-8")), "canonical_nfc_posix_mmd_member"),
            "primary_member_suffix": (_sha256(b"source.MMD"), "canonical_nfc_posix_mmd_member"),
            "answer_member_suffix": (_sha256(b"answer.txt"), "canonical_nfc_posix_mmd_member"),
            "negative_candidate_count": (-1, "non_negative_integer"),
            "proposed_id_empty": ("", "non_empty_string"),
            "kind": ("worked", ["example", "exercise"]),
            "number_empty": ("", "non_empty_string"),
            "source_section_empty": ("", "non_empty_string"),
            "language_layout": (
                "bilingual",
                ["english_then_chinese", "interleaved_bilingual"],
            ),
            "answer_mapping": (
                "derived_answer",
                ["source_answer", "missing_from_source"],
            ),
            "answer_number_empty": ("", "non_empty_string"),
            "image_member_absolute": (_sha256(b"/images/a.jpg"), "canonical_nfc_posix_images_member"),
            "image_member_wrong_root": (_sha256(b"assets/a.jpg"), "canonical_nfc_posix_images_member"),
            "image_member_dot": (_sha256(b"images/./a.jpg"), "canonical_nfc_posix_images_member"),
            "image_member_parent": (_sha256(b"images/../a.jpg"), "canonical_nfc_posix_images_member"),
            "image_member_backslash": (_sha256(r"images\a.jpg".encode("utf-8")), "canonical_nfc_posix_images_member"),
            "image_member_empty_component": (_sha256(b"images//a.jpg"), "canonical_nfc_posix_images_member"),
            "image_member_non_nfc": (_sha256("images/e\u0301.jpg".encode("utf-8")), "canonical_nfc_posix_images_member"),
            "image_member_suffix": (_sha256(b"images/a.JPG"), "canonical_nfc_posix_images_member"),
            "primary_type_empty": ("", "non_empty_string"),
            "tag_empty": ("", "non_empty_string"),
            "tag_status": ("verified", ["source_provided", "proposed", "missing"]),
            "difficulty_level_low": (0, "integer_1_to_5"),
            "difficulty_level_high": (6, "integer_1_to_5"),
            "difficulty_status": ("verified", ["source_provided", "proposed", "missing"]),
        }
        for label, selection_bytes, field, reason in cases:
            with self.subTest(case=label):
                actual, expected = exact_evidence[label]
                self.assert_d0_issue(
                    selection_bytes,
                    field=field,
                    actual=actual,
                    expected=expected,
                    reason=reason,
                )

    def test_d0_distinguishes_invalid_image_elements_from_valid_duplicate_members(self):
        invalid = _minimal_manifest(b"source")
        invalid["selections"][0]["expected_image_members"] = ["bad.gif", "bad.gif"]
        invalid_digest = _sha256(b"bad.gif")
        self.assert_d0_issues(
            _canonical_json(invalid).encode("utf-8"),
            expected=(
                (
                    "$.selections[0].expected_image_members[0]",
                    invalid_digest,
                    "canonical_nfc_posix_images_member",
                    "invalid_value",
                ),
                (
                    "$.selections[0].expected_image_members[1]",
                    invalid_digest,
                    "canonical_nfc_posix_images_member",
                    "invalid_value",
                ),
            ),
        )

        valid = _minimal_manifest(b"source")
        valid["selections"][0]["expected_image_members"] = [
            "images/a.jpg",
            "images/a.jpg",
        ]
        self.assert_d0_issues(
            _canonical_json(valid).encode("utf-8"),
            expected=(
                (
                    "$.selections[0].expected_image_members",
                    _sha256(b"images/a.jpg"),
                    "unique_items",
                    "invalid_value",
                ),
            ),
        )

    def test_d0_rejects_every_source_free_cross_field_validation_family(self):
        source = b"source"
        base = _minimal_manifest(source)

        def changed(mutator):
            value = copy.deepcopy(base)
            mutator(value)
            return _canonical_json(value).encode("utf-8")

        def duplicate_ids(value):
            value["selections"].append(copy.deepcopy(value["selections"][0]))
            value["expected_candidate_count"] = 2

        cases = (
            (
                "plain_answer_member",
                changed(lambda value: value.__setitem__("answer_member", "answer.mmd")),
                "$.answer_member",
                "cross_field_violation",
            ),
            (
                "plain_primary_filename",
                changed(lambda value: value.__setitem__("primary_member", "other.mmd")),
                "$.primary_member",
                "cross_field_violation",
            ),
            (
                "primary_equals_answer",
                changed(
                    lambda value: (
                        value.__setitem__("source_kind", "mmd_zip"),
                        value.__setitem__("answer_member", "source.mmd"),
                    )
                ),
                "$.answer_member",
                "cross_field_violation",
            ),
            (
                "candidate_count",
                changed(lambda value: value.__setitem__("expected_candidate_count", 2)),
                "$.expected_candidate_count",
                "cross_field_violation",
            ),
            (
                "duplicate_id",
                changed(duplicate_ids),
                "$.selections[1].proposed_question_id",
                "cross_field_violation",
            ),
            (
                "source_answer_number_without_answer_member",
                changed(
                    lambda value: value["selections"][0].update(
                        answer_mapping="source_answer",
                        answer_number="1",
                    )
                ),
                "$.selections[0].answer_number",
                "cross_field_violation",
            ),
            (
                "missing_tag_status_with_tags",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "tag_status", "missing"
                    )
                ),
                "$.selections[0].tags",
                "cross_field_violation",
            ),
            (
                "nonmissing_tag_status_without_tags",
                changed(lambda value: value["selections"][0].__setitem__("tags", [])),
                "$.selections[0].tags",
                "cross_field_violation",
            ),
            (
                "missing_difficulty_status_with_level",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "difficulty_status", "missing"
                    )
                ),
                "$.selections[0].difficulty_level",
                "cross_field_violation",
            ),
            (
                "nonmissing_difficulty_status_without_level",
                changed(
                    lambda value: value["selections"][0].__setitem__(
                        "difficulty_level", None
                    )
                ),
                "$.selections[0].difficulty_level",
                "cross_field_violation",
            ),
        )
        exact_evidence = {
            "plain_answer_member": ("present", "null_when_source_kind_mmd"),
            "plain_primary_filename": (
                _sha256(b"other.mmd"),
                _sha256(b"source.mmd"),
            ),
            "primary_equals_answer": (
                "same_as_primary_member",
                "different_from_primary_member",
            ),
            "candidate_count": (2, 1),
            "duplicate_id": (
                _sha256(b"TASK9B-INTEGRATION-01"),
                "unique_proposed_question_id",
            ),
            "source_answer_number_without_answer_member": (
                "present",
                "null_without_answer_member",
            ),
            "missing_tag_status_with_tags": (1, 0),
            "nonmissing_tag_status_without_tags": (0, "positive_length"),
            "missing_difficulty_status_with_level": (3, None),
            "nonmissing_difficulty_status_without_level": (None, "integer_1_to_5"),
        }
        for label, selection_bytes, field, reason in cases:
            with self.subTest(case=label):
                actual, expected = exact_evidence[label]
                self.assert_d0_issue(
                    selection_bytes,
                    field=field,
                    actual=actual,
                    expected=expected,
                    reason=reason,
                )

    def test_d0_missing_answer_number_collects_both_exact_applicable_rows_in_sort_order(self):
        payload = _minimal_manifest(b"source")
        payload["selections"][0]["answer_number"] = "1"
        self.assert_d0_issues(
            _canonical_json(payload).encode("utf-8"),
            expected=(
                (
                    "$.selections[0].answer_number",
                    "present",
                    "null_when_missing_from_source",
                    "cross_field_violation",
                ),
                (
                    "$.selections[0].answer_number",
                    "present",
                    "null_without_answer_member",
                    "cross_field_violation",
                ),
            ),
        )

    def test_d0_collects_two_independent_blockers_in_exact_stable_order(self):
        payload = _minimal_manifest(b"source")
        payload["batch_id"] = ""
        payload["source_id"] = ""
        self.assert_d0_issues(
            _canonical_json(payload).encode("utf-8"),
            expected=(
                ("$.batch_id", "", "non_empty_string", "invalid_value"),
                ("$.source_id", "", "non_empty_string", "invalid_value"),
            ),
        )


class AdapterMappingBehaviorRedTests(unittest.TestCase):
    """B5/D4-D7 mapping assertions kept behind the public adapter boundary."""

    def selection(
        self,
        *,
        proposed_question_id: str = "TASK9B-MAPPING-01",
        kind: str = "example",
        number: str = "1",
        source_section: str = "例題",
        language_layout: str = "english_then_chinese",
        answer_mapping: str = "missing_from_source",
        answer_number: str | None = None,
        expected_image_members: list[str] | None = None,
    ) -> dict[str, object]:
        return {
            "proposed_question_id": proposed_question_id,
            "kind": kind,
            "number": number,
            "source_section": source_section,
            "language_layout": language_layout,
            "answer_mapping": answer_mapping,
            "answer_number": answer_number,
            "expected_image_members": expected_image_members or [],
            "primary_type": "向量",
            "tags": ["向量"],
            "tag_status": "proposed",
            "difficulty_level": 3,
            "difficulty_status": "proposed",
        }

    def write_plain_case(
        self,
        root: Path,
        primary: bytes,
        selections: list[dict[str, object]],
        *,
        images: dict[str, bytes] | None = None,
    ) -> tuple[Path, Path, Path]:
        source = root / "source.mmd"
        source.write_bytes(primary)
        for relative_path, content in (images or {}).items():
            target = root / relative_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(content)
        manifest = {
            "schema_version": "task9b-mmd-adapter-v1",
            "batch_id": "TASK9B-MAPPING-RED",
            "source_kind": "mmd",
            "source_sha256": _sha256(primary),
            "primary_member": "source.mmd",
            "answer_member": None,
            "source_id": "TASK9B-MAPPING-SOURCE",
            "chapter": "向量及其应用",
            "expected_candidate_count": len(selections),
            "selections": selections,
        }
        selection_path = root / "selection.json"
        selection_path.write_text(_canonical_json(manifest), encoding="utf-8")
        output = root / "data" / "staging" / "adapted"
        return selection_path, source, output

    def write_zip_case(
        self,
        root: Path,
        primary: bytes,
        answer: bytes,
        selections: list[dict[str, object]],
        *,
        images: dict[str, bytes] | None = None,
    ) -> tuple[Path, Path, Path]:
        source = root / "source.mmd.zip"
        members = {
            "primary.mmd": primary,
            "answer.mmd": answer,
            **(images or {}),
        }
        with zipfile.ZipFile(source, "w") as archive:
            for member_path, content in members.items():
                info = zipfile.ZipInfo(member_path, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, content)
        manifest = {
            "schema_version": "task9b-mmd-adapter-v1",
            "batch_id": "TASK9B-MAPPING-RED",
            "source_kind": "mmd_zip",
            "source_sha256": _sha256(source.read_bytes()),
            "primary_member": "primary.mmd",
            "answer_member": "answer.mmd",
            "source_id": "TASK9B-MAPPING-SOURCE",
            "chapter": "向量及其应用",
            "expected_candidate_count": len(selections),
            "selections": selections,
        }
        selection_path = root / "selection.json"
        selection_path.write_text(_canonical_json(manifest), encoding="utf-8")
        output = root / "data" / "staging" / "adapted"
        return selection_path, source, output

    def invoke(self, root: Path, selection_path: Path, source: Path, output: Path):
        try:
            return adapt_mmd_package(
                selection_path,
                source,
                output,
                PipelineConfig(root),
            )
        except NotImplementedError as exc:
            self.assertEqual(str(exc), NOT_IMPLEMENTED_MESSAGE)
            self.fail(f"adapter behavior RED: {exc}")

    def blocked_issues(
        self,
        root: Path,
        selection_path: Path,
        source: Path,
        output: Path,
    ) -> tuple[MmdAdapterIssue, ...]:
        with self.assertRaises(MmdAdapterBlockedError) as caught:
            self.invoke(root, selection_path, source, output)
        self.assertFalse(output.exists(), "a blocked mapping must not publish a partial package")
        return caught.exception.issues

    def blocked_issues_without_raw_exception(
        self,
        root: Path,
        selection_path: Path,
        source: Path,
        output: Path,
    ) -> tuple[MmdAdapterIssue, ...]:
        try:
            adapt_mmd_package(selection_path, source, output, PipelineConfig(root))
        except MmdAdapterBlockedError as exc:
            self.assertFalse(
                output.exists(),
                "a blocked mapping must not publish a partial package",
            )
            return exc.issues
        except Exception as exc:
            self.fail(
                "mapping validation must return a typed blocker instead of "
                f"raising {type(exc).__name__}: {exc}"
            )
        self.fail("the invalid mapping must raise MmdAdapterBlockedError")

    def assert_issue_envelope(
        self,
        issue: MmdAdapterIssue,
        *,
        code: str,
        proposed_question_id: str | None,
        field: str,
        evidence: dict[str, object],
        locator_empty: bool | None = None,
        expected_locator: str | None = None,
    ) -> None:
        self.assertNotEqual(
            locator_empty is None,
            expected_locator is None,
            "assert exactly one locator expectation",
        )
        self.assertIs(type(issue), MmdAdapterIssue)
        self.assertEqual(
            tuple(value.name for value in fields(type(issue))),
            (
                "code",
                "severity",
                "proposed_question_id",
                "source_locator",
                "field",
                "evidence",
            ),
        )
        self.assertEqual(
            (issue.code, issue.severity, issue.proposed_question_id, issue.field),
            (code, "blocking", proposed_question_id, field),
        )
        self.assertEqual(issue.evidence, _canonical_json(evidence))
        self.assertEqual(json.loads(issue.evidence), evidence)
        if expected_locator is not None:
            self.assertEqual(issue.source_locator, expected_locator)
        elif locator_empty:
            self.assertEqual(issue.source_locator, "")
        else:
            self.assertRegex(
                issue.source_locator,
                r"^[^/][^#]*#bytes=(0|[1-9][0-9]*):(0|[1-9][0-9]*)$",
            )
        for runtime_path in (str(Path.cwd()), str(Path(tempfile.gettempdir()))):
            self.assertNotIn(runtime_path, issue.source_locator)
            self.assertNotIn(runtime_path, issue.evidence)

    def read_candidates(self, package: AdaptedImportPackage) -> list[dict[str, object]]:
        path = package.package_root / "records" / "candidates.json"
        candidates = json.loads(path.read_text(encoding="utf-8"))
        self.assertIs(type(candidates), list)
        for candidate in candidates:
            self.assertEqual(set(candidate), RAW_CANDIDATE_FIELDS)
        return candidates

    def test_d4_question_selection_zero_and_multiple_matches_are_exact_blockers(self):
        cases = (
            (
                "zero",
                b"source\n",
                self.selection(number="2"),
                0,
            ),
            (
                "multiple",
                "例題 1\nEnglish.\n中文。\n例題 1\nEnglish again.\n中文再。\n".encode("utf-8"),
                self.selection(number="1"),
                2,
            ),
        )
        for label, primary, selected, match_count in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                args = self.write_plain_case(root, primary, [selected])
                issues = self.blocked_issues(root, *args)
                self.assertEqual(len(issues), 1)
                self.assert_issue_envelope(
                    issues[0],
                    code="selection_not_unique",
                    proposed_question_id="TASK9B-MAPPING-01",
                    field="selection",
                    evidence={
                        "canonical_number": selected["number"],
                        "match_count": match_count,
                        "reason": "question_occurrence",
                    },
                    locator_empty=True,
                )

    def test_d4_local_solution_zero_and_multiple_matches_are_exact_blockers(self):
        cases = (
            (
                "zero",
                "例題 1\nEnglish.\n中文。\n".encode("utf-8"),
                0,
            ),
            (
                "multiple",
                "例題 1\nEnglish.\n中文。\n題解：\none\n題解 ：\ntwo\n".encode("utf-8"),
                2,
            ),
        )
        selected = self.selection(answer_mapping="source_answer")
        for label, primary, match_count in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                args = self.write_plain_case(root, primary, [selected])
                issues = self.blocked_issues(root, *args)
                self.assertEqual(len(issues), 1)
                self.assert_issue_envelope(
                    issues[0],
                    code="selection_not_unique",
                    proposed_question_id="TASK9B-MAPPING-01",
                    field="answer_mapping",
                    evidence={
                        "canonical_number": "1",
                        "match_count": match_count,
                        "reason": "local_solution",
                    },
                    locator_empty=False,
                )

    def test_d4_second_local_solution_marker_is_multiple_when_first_body_is_empty(self):
        primary = "例題 1\nEnglish.\n中文。\n題解：\n題解 ：\nanswer\n".encode("utf-8")
        selected = self.selection(answer_mapping="source_answer")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary, [selected])
            issues = self.blocked_issues(root, *args)
        self.assertEqual(len(issues), 1)
        self.assert_issue_envelope(
            issues[0],
            code="selection_not_unique",
            proposed_question_id="TASK9B-MAPPING-01",
            field="answer_mapping",
            evidence={
                "canonical_number": "1",
                "match_count": 2,
                "reason": "local_solution",
            },
            locator_empty=False,
        )

    def test_d4_solution_marker_inside_display_math_is_not_a_second_local_marker(self):
        primary = (
            "例題 1\nEnglish.\n中文。\n題解：\n"
            "$$\n題解：\n$$\nsource solution\n"
        ).encode("utf-8")
        selected = self.selection(answer_mapping="source_answer")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary, [selected])
            try:
                package = self.invoke(root, *args)
            except MmdAdapterBlockedError as exc:
                self.fail(
                    "a solution marker inside atomic display math must not create "
                    f"a second local solution occurrence: {exc.issues}"
                )
            candidate = self.read_candidates(package)[0]
        self.assertEqual(
            candidate["solution_original"],
            "$$\n題解：\n$$\nsource solution\n",
        )
        self.assertEqual(candidate["answer_status"], "source_provided")

    def test_d4_separate_answer_zero_and_multiple_matches_are_exact_blockers(self):
        primary = "例題 1\nEnglish.\n中文。\n".encode("utf-8")
        cases = (
            ("zero", "例題 2\n題解：\nother\n".encode("utf-8"), 0),
            (
                "multiple",
                "例題 1\n題解：\none\n例題 1\n題解：\ntwo\n".encode("utf-8"),
                2,
            ),
        )
        selected = self.selection(answer_mapping="source_answer", answer_number="1")
        for label, answer, match_count in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                args = self.write_zip_case(root, primary, answer, [selected])
                issues = self.blocked_issues(root, *args)
                self.assertEqual(len(issues), 1)
                self.assert_issue_envelope(
                    issues[0],
                    code="selection_not_unique",
                    proposed_question_id="TASK9B-MAPPING-01",
                    field="answer_number",
                    evidence={
                        "canonical_number": "1",
                        "match_count": match_count,
                        "reason": "answer_occurrence",
                    },
                    locator_empty=match_count == 0,
                )

    def test_d4_explicit_separate_answer_number_controls_rendered_solution(self):
        primary = "例題 1\nEnglish.\n中文。\n".encode("utf-8")
        answer = "例題 2\n題解：\nanswer two\n".encode("utf-8")
        selected = self.selection(answer_mapping="source_answer", answer_number="2")
        captured: list[tuple[dict[str, object], ...]] = []

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path, source, output = self.write_zip_case(
                root,
                primary,
                answer,
                [selected],
            )
            module = adapter_module(self)
            original = module._map_candidates

            def capture(*args):
                mapped = original(*args)
                captured.append(mapped)
                return mapped

            with patch.object(module, "_map_candidates", side_effect=capture):
                try:
                    adapt_mmd_package(
                        selection_path,
                        source,
                        output,
                        PipelineConfig(root),
                    )
                except NotImplementedError as exc:
                    self.assertEqual(str(exc), NOT_IMPLEMENTED_MESSAGE)

        self.assertEqual(len(captured), 1)
        self.assertEqual(len(captured[0]), 1)
        self.assertEqual(captured[0][0]["solution_original"], "answer two\n")
        self.assertEqual(captured[0][0]["answer_status"], "source_provided")

    def test_d4_markers_inside_separate_answer_display_do_not_split_occurrence(self):
        primary = "例題 1\nEnglish.\n中文。\n".encode("utf-8")
        for embedded_marker in ("例題 2", "Q1）"):
            with self.subTest(marker=embedded_marker), tempfile.TemporaryDirectory() as directory:
                answer = (
                    "例題 1\n題解：\n$$\n"
                    f"{embedded_marker}\n"
                    "$$\nseparate solution\n"
                ).encode("utf-8")
                root = Path(directory)
                selected = self.selection(
                    answer_mapping="source_answer",
                    answer_number="1",
                )
                args = self.write_zip_case(root, primary, answer, [selected])
                try:
                    package = self.invoke(root, *args)
                except MmdAdapterBlockedError as exc:
                    self.fail(
                        "a marker inside atomic display math must not split a "
                        f"separate answer occurrence: {exc.issues}"
                    )
                candidate = self.read_candidates(package)[0]
                self.assertEqual(
                    candidate["solution_original"],
                    f"$$\n{embedded_marker}\n$$\nseparate solution\n",
                )
                self.assertEqual(candidate["answer_status"], "source_provided")

    def test_d3_unclosed_display_in_separate_answer_is_an_exact_parse_blocker(self):
        primary = "例題 1\nEnglish.\n中文。\n".encode("utf-8")
        answer = "例題 1\n題解：\n$$\nunclosed\n".encode("utf-8")
        display_start = answer.index(b"$$")
        selected = self.selection(answer_mapping="source_answer", answer_number="1")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_zip_case(root, primary, answer, [selected])
            issues = self.blocked_issues(root, *args)
        self.assertEqual(len(issues), 1)
        self.assert_issue_envelope(
            issues[0],
            code="mmd_parse_failed",
            proposed_question_id=None,
            field="answer_member",
            evidence={
                "end_byte": len(answer),
                "member": "answer.mmd",
                "reason": "unclosed_token",
                "start_byte": display_start,
            },
            expected_locator=f"answer.mmd#bytes={display_start}:{len(answer)}",
        )

    def test_d3_unclosed_display_in_local_solution_is_an_exact_parse_blocker(self):
        primary = "例題 1\nEnglish.\n中文。\n題解：\n$$\nunclosed\n".encode("utf-8")
        display_start = primary.index(b"$$")
        selected = self.selection(answer_mapping="source_answer")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary, [selected])
            issues = self.blocked_issues(root, *args)
        self.assertEqual(len(issues), 1)
        self.assert_issue_envelope(
            issues[0],
            code="mmd_parse_failed",
            proposed_question_id=None,
            field="primary_member",
            evidence={
                "end_byte": len(primary),
                "member": "source.mmd",
                "reason": "unclosed_token",
                "start_byte": display_start,
            },
            expected_locator=f"source.mmd#bytes={display_start}:{len(primary)}",
        )

    def test_d3_unclosed_inline_math_in_local_solution_is_an_exact_parse_blocker(self):
        primary = "例題 1\nEnglish.\n中文。\n題解：\n$x unclosed\n".encode("utf-8")
        inline_start = primary.index(b"$x")
        inline_end = len(primary) - 1
        selected = self.selection(answer_mapping="source_answer")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary, [selected])
            issues = self.blocked_issues(root, *args)
        self.assertEqual(len(issues), 1)
        self.assert_issue_envelope(
            issues[0],
            code="mmd_parse_failed",
            proposed_question_id=None,
            field="primary_member",
            evidence={
                "end_byte": inline_end,
                "member": "source.mmd",
                "reason": "unclosed_token",
                "start_byte": inline_start,
            },
            expected_locator=f"source.mmd#bytes={inline_start}:{inline_end}",
        )

    def test_d3_unclosed_inline_math_in_separate_answer_is_an_exact_parse_blocker(self):
        primary = "例題 1\nEnglish.\n中文。\n".encode("utf-8")
        answer = "例題 1\n題解：\n$x unclosed\n".encode("utf-8")
        inline_start = answer.index(b"$x")
        inline_end = len(answer) - 1
        selected = self.selection(answer_mapping="source_answer", answer_number="1")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_zip_case(root, primary, answer, [selected])
            issues = self.blocked_issues(root, *args)
        self.assertEqual(len(issues), 1)
        self.assert_issue_envelope(
            issues[0],
            code="mmd_parse_failed",
            proposed_question_id=None,
            field="answer_member",
            evidence={
                "end_byte": inline_end,
                "member": "answer.mmd",
                "reason": "unclosed_token",
                "start_byte": inline_start,
            },
            expected_locator=f"answer.mmd#bytes={inline_start}:{inline_end}",
        )

    def test_d3_unsafe_image_target_in_local_solution_is_an_exact_path_blocker(self):
        raw_target = "../../escape.jpg"
        primary = (
            "例題 1\nEnglish.\n中文。\n題解：\n"
            f"![]({raw_target})\n"
        ).encode("utf-8")
        token = f"![]({raw_target})".encode("utf-8")
        token_start = primary.index(token)
        token_end = token_start + len(token)
        selected = self.selection(answer_mapping="source_answer")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary, [selected])
            issues = self.blocked_issues(root, *args)
        self.assertEqual(len(issues), 1)
        self.assert_issue_envelope(
            issues[0],
            code="archive_member_unsafe",
            proposed_question_id=None,
            field="raw_target",
            evidence={
                "raw_target_sha256": _sha256(raw_target.encode("utf-8")),
                "reason": "image_target_traversal",
            },
            expected_locator=f"source.mmd#bytes={token_start}:{token_end}",
        )

    def test_d3_plain_solution_only_image_symlink_escape_is_an_exact_path_blocker(self):
        raw_target = "./images/link/a.jpg"
        primary = (
            "例題 1\nEnglish.\n中文。\n題解：\n"
            f"![]({raw_target})\n"
            "solution\n"
        ).encode("utf-8")
        token = f"![]({raw_target})".encode("utf-8")
        token_start = primary.index(token)
        token_end = token_start + len(token)
        selected = self.selection(answer_mapping="source_answer")
        with tempfile.TemporaryDirectory() as directory:
            container = Path(directory)
            root = container / "source-root"
            root.mkdir()
            args = self.write_plain_case(root, primary, [selected])
            outside = container / "outside"
            outside.mkdir()
            (outside / "a.jpg").write_bytes(b"outside-image")
            images = root / "images"
            images.mkdir()
            (images / "link").symlink_to(outside, target_is_directory=True)
            issues = self.blocked_issues(root, *args)
        self.assertEqual(len(issues), 1)
        self.assert_issue_envelope(
            issues[0],
            code="archive_member_unsafe",
            proposed_question_id=None,
            field="raw_target",
            evidence={
                "raw_target_sha256": _sha256(raw_target.encode("utf-8")),
                "reason": "image_target_normalized_escape",
            },
            expected_locator=f"source.mmd#bytes={token_start}:{token_end}",
        )

    def test_d3_incomplete_image_token_in_local_solution_is_an_exact_parse_blocker(self):
        incomplete = "![](./images/a.jpg"
        primary = (
            "例題 1\nEnglish.\n中文。\n題解：\n"
            f"{incomplete}\n"
        ).encode("utf-8")
        token = incomplete.encode("utf-8")
        token_start = primary.index(token)
        token_end = token_start + len(token)
        selected = self.selection(answer_mapping="source_answer")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary, [selected])
            issues = self.blocked_issues(root, *args)
        self.assertEqual(len(issues), 1)
        self.assert_issue_envelope(
            issues[0],
            code="mmd_parse_failed",
            proposed_question_id=None,
            field="primary_member",
            evidence={
                "end_byte": token_end,
                "member": "source.mmd",
                "reason": "unsupported_grammar",
                "start_byte": token_start,
            },
            expected_locator=f"source.mmd#bytes={token_start}:{token_end}",
        )

    def test_d4_source_occurrence_kind_number_and_section_disagreement_use_exact_schema(self):
        primary = "例題 1\nEnglish.\n中文。\n".encode("utf-8")
        cases = (
            ("kind", self.selection(kind="exercise"), "example", "exercise"),
            ("number", self.selection(number="2"), "1", "2"),
            ("source_section", self.selection(source_section="例题"), "例題", "例题"),
        )
        for field, selected, actual, expected in cases:
            with self.subTest(field=field), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                args = self.write_plain_case(root, primary, [selected])
                issues = self.blocked_issues(root, *args)
                self.assertEqual(len(issues), 1)
                self.assert_issue_envelope(
                    issues[0],
                    code="source_contract_mismatch",
                    proposed_question_id="TASK9B-MAPPING-01",
                    field=field,
                    evidence={
                        "actual": actual,
                        "expected": expected,
                        "reason": "source_occurrence_mismatch",
                    },
                    locator_empty=False,
                )

    def test_d4_failure_stops_d5_d7_consequence_noise(self):
        primary = b"source\n"
        selected = self.selection(
            number="2",
            expected_image_members=["images/b.jpg"],
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary, [selected])
            issues = self.blocked_issues(root, *args)
        self.assertEqual({issue.code for issue in issues}, {"selection_not_unique"})

    def test_d5_candidate_count_mismatch_has_package_binding_and_exact_evidence(self):
        primary = (
            "例題 1\nEnglish one.\n中文一。\n"
            "例題 2\nEnglish two.\n中文二。\n"
        ).encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary, [self.selection(number="1")])
            issues = self.blocked_issues(root, *args)
        self.assertEqual(len(issues), 1)
        self.assert_issue_envelope(
            issues[0],
            code="candidate_count_mismatch",
            proposed_question_id=None,
            field="expected_candidate_count",
            evidence={"actual": 2, "expected": 1, "reason": "candidate_count"},
            locator_empty=True,
        )

    def test_d5_failure_stops_language_and_image_mapping(self):
        primary = (
            "例題 1\n123 !!!\n![](./images/a.jpg)\n"
            "例題 2\nEnglish.\n中文。\n"
        ).encode("utf-8")
        selected = self.selection(expected_image_members=["images/b.jpg"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary, [selected])
            issues = self.blocked_issues(root, *args)
        self.assertEqual({issue.code for issue in issues}, {"candidate_count_mismatch"})

    def test_d6_all_four_language_reasons_use_exact_candidate_binding_and_schema(self):
        cases = (
            (
                "missing_en",
                "例題 1\n只有中文。\n",
                "english_then_chinese",
                "只有中文。\n",
            ),
            (
                "missing_zh",
                "例題 1\nEnglish only.\n",
                "english_then_chinese",
                "English only.\n",
            ),
            (
                "invalid_transition",
                "例題 1\nEnglish first.\n中文其後。\nEnglish again.\n",
                "english_then_chinese",
                "English again.\n",
            ),
            (
                "und_prose",
                "例題 1\n123 !!!\nEnglish.\n中文。\n",
                "interleaved_bilingual",
                "123 !!!\n",
            ),
        )
        for reason, source_text, layout, offending_text in cases:
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                selected = self.selection(language_layout=layout)
                source_bytes = source_text.encode("utf-8")
                offending_bytes = offending_text.encode("utf-8")
                start_byte = source_bytes.index(offending_bytes)
                end_byte = start_byte + len(offending_bytes)
                args = self.write_plain_case(root, source_bytes, [selected])
                issues = self.blocked_issues(root, *args)
                self.assertEqual(len(issues), 1)
                self.assert_issue_envelope(
                    issues[0],
                    code="language_mapping_ambiguous",
                    proposed_question_id="TASK9B-MAPPING-01",
                    field="language_layout",
                    evidence={
                        "end_byte": end_byte,
                        "layout": layout,
                        "reason": reason,
                        "start_byte": start_byte,
                    },
                    expected_locator=f"source.mmd#bytes={start_byte}:{end_byte}",
                )

    def test_d6_english_then_chinese_rejects_und_and_empty_prose_safely(self):
        cases = (
            (
                "und_prose",
                "例題 1\n123 !!!\nEnglish.\n中文。\n".encode("utf-8"),
                9,
                17,
            ),
            (
                "missing_en",
                "例題 1\n$x$\n".encode("utf-8"),
                0,
                len("例題 1\n$x$\n".encode("utf-8")),
            ),
        )
        for reason, primary, start_byte, end_byte in cases:
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                args = self.write_plain_case(root, primary, [self.selection()])
                issues = self.blocked_issues_without_raw_exception(root, *args)
                self.assertEqual(len(issues), 1)
                self.assert_issue_envelope(
                    issues[0],
                    code="language_mapping_ambiguous",
                    proposed_question_id="TASK9B-MAPPING-01",
                    field="language_layout",
                    evidence={
                        "end_byte": end_byte,
                        "layout": "english_then_chinese",
                        "reason": reason,
                        "start_byte": start_byte,
                    },
                    expected_locator=f"source.mmd#bytes={start_byte}:{end_byte}",
                )

    def test_d6_zip_member_order_resolves_primary_by_declared_identity(self):
        primary = (
            "例題 1\n"
            + "English long line. " * 10
            + "\n中文。\n"
        ).encode("utf-8")
        answer = "例題 1\n題解：\nanswer\n".encode("utf-8")
        selected = self.selection(answer_mapping="source_answer", answer_number="1")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path, source, output = self.write_zip_case(
                root,
                primary,
                answer,
                [selected],
            )
            try:
                adapt_mmd_package(
                    selection_path,
                    source,
                    output,
                    PipelineConfig(root),
                )
            except NotImplementedError as exc:
                self.assertEqual(str(exc), NOT_IMPLEMENTED_MESSAGE)
            except Exception as exc:
                self.fail(
                    "declared primary_member must be used instead of lexical member "
                    f"order; got {type(exc).__name__}: {exc}"
                )

    def test_d6_collects_independent_candidate_issues_in_exact_five_key_order(self):
        primary = (
            "例題 1\nEnglish only.\n"
            "例題 2\nEnglish only too.\n"
        ).encode("utf-8")
        selections = [
            self.selection(proposed_question_id="Z-ID", number="1"),
            self.selection(proposed_question_id="A-ID", number="2"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary, selections)
            issues = self.blocked_issues(root, *args)
        self.assertEqual(len(issues), 2)
        self.assertTrue(all(issue.code == "language_mapping_ambiguous" for issue in issues))
        self.assertEqual(
            issues,
            tuple(
                sorted(
                    issues,
                    key=lambda issue: (
                        issue.source_locator,
                        issue.proposed_question_id or "",
                        issue.code,
                        issue.field,
                        issue.evidence,
                    ),
                )
            ),
        )

    def test_d6_failure_stops_d7_image_binding_noise(self):
        primary = "例題 1\nEnglish only.\n![](./images/a.jpg)\n".encode("utf-8")
        selected = self.selection(expected_image_members=["images/b.jpg"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary, [selected])
            issues = self.blocked_issues(root, *args)
        self.assertEqual({issue.code for issue in issues}, {"language_mapping_ambiguous"})

    def test_d7_selection_conflict_has_exact_candidate_binding_and_schema(self):
        primary = "例題 1\nEnglish. 中文。\n![](./images/a.jpg)\n".encode("utf-8")
        image_token = b"![](./images/a.jpg)"
        token_start = primary.index(image_token)
        token_end = token_start + len(image_token)
        selected = self.selection(expected_image_members=["images/b.jpg"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(
                root,
                primary,
                [selected],
                images={"images/a.jpg": b"a", "images/b.jpg": b"b"},
            )
            issues = self.blocked_issues(root, *args)
        self.assertEqual(len(issues), 1)
        self.assert_issue_envelope(
            issues[0],
            code="image_binding_invalid",
            proposed_question_id="TASK9B-MAPPING-01",
            field="expected_image_members",
            evidence={
                "matches": ["images/a.jpg"],
                "raw_target": "./images/a.jpg",
                "reason": "selection_conflict",
            },
            expected_locator=f"source.mmd#bytes={token_start}:{token_end}",
        )

    def test_d3_image_target_casefold_collision_includes_safe_archive_inventory(self):
        primary = "例題 1\nEnglish. 中文。\n![](./images/A.jpg)\n".encode("utf-8")
        token = b"![](./images/A.jpg)"
        token_start = primary.index(token)
        token_end = token_start + len(token)
        selected = self.selection(expected_image_members=["images/A.jpg"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_zip_case(
                root,
                primary,
                b"",
                [selected],
                images={"images/a.jpg": b"present with conflicting spelling"},
            )
            issues = self.blocked_issues(root, *args)
        self.assertEqual(len(issues), 1)
        self.assert_issue_envelope(
            issues[0],
            code="archive_member_unsafe",
            proposed_question_id=None,
            field="raw_target",
            evidence={
                "raw_target_sha256": _sha256(b"./images/A.jpg"),
                "reason": "image_target_casefold_collision",
            },
            expected_locator=f"primary.mmd#bytes={token_start}:{token_end}",
        )

    def test_d3_image_target_nfc_collision_includes_safe_archive_inventory(self):
        raw_target = "./images/cafe\u0301.jpg"
        primary = f"例題 1\nEnglish. 中文。\n![]({raw_target})\n".encode("utf-8")
        token = f"![]({raw_target})".encode("utf-8")
        token_start = primary.index(token)
        token_end = token_start + len(token)
        selected = self.selection(expected_image_members=["images/café.jpg"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_zip_case(
                root,
                primary,
                b"",
                [selected],
                images={"images/café.jpg": b"present with NFC spelling"},
            )
            issues = self.blocked_issues(root, *args)
        self.assertEqual(len(issues), 1)
        self.assert_issue_envelope(
            issues[0],
            code="archive_member_unsafe",
            proposed_question_id=None,
            field="raw_target",
            evidence={
                "raw_target_sha256": _sha256(raw_target.encode("utf-8")),
                "reason": "image_target_nfc_collision",
            },
            expected_locator=f"primary.mmd#bytes={token_start}:{token_end}",
        )

    def test_d7_manifest_only_surplus_image_has_exact_question_bound_envelope(self):
        primary = "例題 1\nEnglish.\n中文。\n".encode("utf-8")
        selected = self.selection(expected_image_members=["images/ghost.jpg"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary, [selected])
            issues = self.blocked_issues(root, *args)
        self.assertEqual(len(issues), 1)
        self.assert_issue_envelope(
            issues[0],
            code="image_binding_invalid",
            proposed_question_id="TASK9B-MAPPING-01",
            field="expected_image_members",
            evidence={
                "expected_member": "images/ghost.jpg",
                "matches": [],
                "raw_target": None,
                "reason": "selection_surplus",
            },
            expected_locator=f"source.mmd#bytes=0:{len(primary)}",
        )

    def test_safe_absent_image_is_representable_not_a_task9b_issue(self):
        primary = "例題 1\nEnglish. 中文。\n![](./images/missing.jpg)\n".encode("utf-8")
        selected = self.selection(expected_image_members=["images/missing.jpg"])
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary, [selected])
            package = self.invoke(root, *args)
            candidates = self.read_candidates(package)
        self.assertEqual(candidates[0]["image_paths"], ["images/missing.jpg"])
        self.assertEqual(candidates[0]["image_roles"], ["question"])

    def test_present_image_mapping_preserves_explicit_path_role_and_bytes(self):
        primary = "例題 1\nEnglish. 中文。\n![](./images/a.jpg)\n".encode("utf-8")
        selected = self.selection(expected_image_members=["images/a.jpg"])
        image = b"exact image bytes\x00\xff"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(
                root,
                primary,
                [selected],
                images={"images/a.jpg": image},
            )
            package = self.invoke(root, *args)
            candidates = self.read_candidates(package)
            self.assertEqual((package.package_root / "images" / "a.jpg").read_bytes(), image)
        self.assertEqual(candidates[0]["image_paths"], ["images/a.jpg"])
        self.assertEqual(candidates[0]["image_roles"], ["question"])

    def test_present_image_is_bound_in_private_source_ir_before_mapping(self):
        primary = "例題 1\nEnglish. 中文。\n![](./images/a.jpg)\n".encode("utf-8")
        selected = self.selection(expected_image_members=["images/a.jpg"])
        captured_documents: list[object] = []
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(
                root,
                primary,
                [selected],
                images={"images/a.jpg": b"image"},
            )
            module = adapter_module(self)
            original = module._bind_selections

            def capture(manifest, document, answer):
                captured_documents.append(document)
                return original(manifest, document, answer)

            with patch.object(module, "_bind_selections", side_effect=capture):
                self.invoke(root, *args)

        self.assertEqual(len(captured_documents), 1)
        document = captured_documents[0]
        self.assertEqual(
            document.questions[0].image_refs[0].resolved_member,
            "images/a.jpg",
        )
        self.assertIn(
            "images/a.jpg",
            tuple(member.relative_path for member in document.members),
        )

    def test_same_member_solution_maps_answer_without_inventing_explanation(self):
        primary = "例題 1\nEnglish.\n中文。\n題解：\nsource solution  \n".encode("utf-8")
        selected = self.selection(answer_mapping="source_answer")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary, [selected])
            package = self.invoke(root, *args)
            candidate = self.read_candidates(package)[0]
        self.assertEqual(candidate["solution_original"], "source solution  \n")
        self.assertEqual(candidate["solution_verified"], "")
        self.assertEqual(candidate["answer_status"], "source_provided")
        self.assertEqual(
            (
                candidate["explanation_text"],
                candidate["explanation_status"],
                candidate["explanation_evidence"],
            ),
            ("", "missing", None),
        )

    def test_separate_member_solution_maps_answer_and_keeps_independent_raw_evidence(self):
        primary = "例題 1\nEnglish.\n中文。\n".encode("utf-8")
        answer = "例題 1\n\n題解：\nseparate solution\n".encode("utf-8")
        selected = self.selection(answer_mapping="source_answer", answer_number="1")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_zip_case(root, primary, answer, [selected])
            package = self.invoke(root, *args)
            candidate = self.read_candidates(package)[0]
            staged_answer = package.package_root / "answers" / "answer.mmd.txt"
            self.assertEqual(staged_answer.read_bytes(), answer)
        self.assertEqual(candidate["solution_original"], "separate solution\n")
        self.assertEqual(candidate["answer_status"], "source_provided")
        self.assertEqual(candidate["explanation_status"], "missing")

    def test_missing_answer_maps_empty_solution_and_independent_explanation(self):
        primary = "例題 1\nEnglish.\n中文。\n".encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary, [self.selection()])
            package = self.invoke(root, *args)
            candidate = self.read_candidates(package)[0]
        self.assertEqual(
            (
                candidate["solution_original"],
                candidate["solution_verified"],
                candidate["answer_status"],
                candidate["explanation_text"],
                candidate["explanation_status"],
                candidate["explanation_evidence"],
            ),
            ("", "", "missing_from_source", "", "missing", None),
        )
        self.assertEqual(candidate["source_fragment_hash"], _sha256(primary))

    def test_bilingual_projection_preserves_original_and_source_owned_translation(self):
        primary_text = "例題 1\r\nEnglish $x$ and 中文向量。  \r"
        selected = self.selection(language_layout="interleaved_bilingual")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary_text.encode("utf-8"), [selected])
            package = self.invoke(root, *args)
            candidate = self.read_candidates(package)[0]
        self.assertEqual(
            candidate["question_text_original"],
            primary_text.replace("\r\n", "\n").replace("\r", "\n"),
        )
        self.assertIn("中文向量。", candidate["question_text_zh"])
        self.assertIn("$x$", candidate["question_text_zh"])
        self.assertEqual(candidate["translation_status"], "source_present")
        self.assertRegex(candidate["translation_evidence"], r"^source:[^#]+#[^#]+#bytes=[0-9]+:[0-9]+$")

    def test_manifest_selection_order_controls_candidate_order_not_source_discovery_order(self):
        primary = (
            "例題 1\nEnglish one.\n中文一。\n"
            "例題 2\nEnglish two.\n中文二。\n"
        ).encode("utf-8")
        selections = [
            self.selection(proposed_question_id="SECOND-FIRST", number="2"),
            self.selection(proposed_question_id="FIRST-SECOND", number="1"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary, selections)
            package = self.invoke(root, *args)
            candidates = self.read_candidates(package)
        self.assertEqual(
            [candidate["proposed_question_id"] for candidate in candidates],
            ["SECOND-FIRST", "FIRST-SECOND"],
        )
        self.assertEqual(
            [candidate["source_question_number"] for candidate in candidates],
            ["2", "1"],
        )

    def test_mapping_blockers_never_publish_partial_output_or_leak_host_paths(self):
        primary = "例題 1\nEnglish only.\n".encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            args = self.write_plain_case(root, primary, [self.selection()])
            issues = self.blocked_issues(root, *args)
            self.assertFalse(args[2].exists())
            for issue in issues:
                self.assertNotIn(str(root), issue.source_locator)
                self.assertNotIn(str(root), issue.evidence)


class CanonicalPackageIntegrationRedTests(AdapterIntegrationRedCase):
    def test_representative_candidates_have_exact_23_fields_values_and_canonical_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.run_representative(Path(directory))
            candidates = self.read_candidate_payload(package)
            golden = json.loads(
                (GOLDEN_ROOT / "records/candidates.json").read_text(encoding="utf-8")
            )
        self.assertEqual(candidates, golden)
        self.assertEqual(len(candidates), 17)
        for candidate in candidates:
            self.assertEqual(tuple(candidate), tuple(sorted(RAW_CANDIDATE_FIELDS)))
            self.assertEqual(set(candidate), RAW_CANDIDATE_FIELDS)
            self.assertNotIn("normalized_text_sha256", candidate)
            self.assertNotIn("image_sha256s", candidate)

    def test_representative_source_map_has_every_exact_schema_type_order_and_raw_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.run_representative(Path(directory))
            source_map = self.read_source_map(package)
            candidates = self.read_candidate_payload(package)
            raw_source = (package.package_root / "source/original.mmd.txt").read_bytes()
            serialized = (package.package_root / "source/source-map.json").read_bytes()
        self.assertEqual(
            tuple(source_map),
            ("batch_id", "members", "primary_member", "questions", "schema_version", "source_id"),
        )
        self.assertEqual(source_map["schema_version"], "task9b-source-map-v1")
        self.assertIs(type(source_map["batch_id"]), str)
        self.assertIs(type(source_map["source_id"]), str)
        self.assertIs(type(source_map["primary_member"]), str)
        self.assertIs(type(source_map["members"]), list)
        self.assertEqual([member["role"] for member in source_map["members"]], ["primary"])
        for member in source_map["members"]:
            self.assertEqual(
                tuple(member),
                ("role", "sha256", "size_bytes", "source_member", "staged_path"),
            )
            self.assertTrue(all(type(member[name]) is str for name in ("role", "sha256", "source_member", "staged_path")))
            self.assertIs(type(member["size_bytes"]), int)
        self.assertIs(type(source_map["questions"]), list)
        self.assertEqual(len(source_map["questions"]), 17)
        self.assertEqual(
            [question["proposed_question_id"] for question in source_map["questions"]],
            [candidate["proposed_question_id"] for candidate in candidates],
        )
        by_id = {candidate["proposed_question_id"]: candidate for candidate in candidates}
        for semantic_order, question in enumerate(source_map["questions"]):
            self.assertEqual(
                tuple(question),
                (
                    "explanation_spans", "fragment", "image_references",
                    "proposed_question_id", "solution_spans", "source_order",
                    "source_question_number", "source_section", "text_spans",
                ),
            )
            self.assertIs(type(question["proposed_question_id"]), str)
            self.assertIs(type(question["source_order"]), int)
            self.assertIs(type(question["source_question_number"]), str)
            self.assertIs(type(question["source_section"]), str)
            self.assertEqual(semantic_order, source_map["questions"].index(question))
            self.assert_span(question["fragment"])
            for group in ("solution_spans", "explanation_spans"):
                self.assertIs(type(question[group]), list)
                for span in question[group]:
                    self.assert_span(span)
            self.assertIs(type(question["text_spans"]), list)
            for span in question["text_spans"]:
                self.assert_span(span, text=True)
            self.assertIs(type(question["image_references"]), list)
            for image_order, reference in enumerate(question["image_references"]):
                self.assertEqual(
                    tuple(reference),
                    (
                        "canonical_path", "raw_target", "role", "selected_member",
                        "sha256", "source_order", "token_span",
                    ),
                )
                self.assertEqual(reference["source_order"], image_order)
                self.assertIs(type(reference["raw_target"]), str)
                self.assertTrue(reference["selected_member"] is None or type(reference["selected_member"]) is str)
                self.assertIs(type(reference["canonical_path"]), str)
                self.assertTrue(reference["sha256"] is None or type(reference["sha256"]) is str)
                self.assertEqual(reference["role"], "question")
                self.assert_span(reference["token_span"])
            fragment = question["fragment"]
            fragment_bytes = raw_source[fragment["start_byte"]:fragment["end_byte"]]
            self.assertEqual(
                _sha256(fragment_bytes),
                by_id[question["proposed_question_id"]]["source_fragment_hash"],
            )
        representative_outer_sha = _sha256(
            (REPRESENTATIVE_ROOT / "separate-answer.mmd.zip").read_bytes()
        )
        for forbidden in (
            representative_outer_sha,
            str(ROOT),
            str(Path(tempfile.gettempdir())),
        ):
            self.assertNotIn(forbidden, serialized.decode("utf-8"))

    def test_task9a_manifest_has_exact_18_field_order_policies_groups_and_tree_binding(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.run_representative(Path(directory))
            self.assert_manifest_and_tree_binding(package)
            payload = json.loads(package.manifest_path.read_text(encoding="utf-8"))
            manifest_fields = tuple(field.name for field in fields(type(package.manifest)))
        self.assertEqual(manifest_fields, MANIFEST_FIELDS)
        self.assertEqual(
            {
                "schema_version": payload["schema_version"],
                "project": payload["project"],
                "module": payload["module"],
                "target_release_version": payload["target_release_version"],
                "language_policy": payload["language_policy"],
                "split_policy": payload["split_policy"],
                "difficulty_policy": payload["difficulty_policy"],
                "tag_policy": payload["tag_policy"],
                "answer_policy": payload["answer_policy"],
                "explanation_policy": payload["explanation_policy"],
            },
            {
                "schema_version": "task9-import-manifest-v1",
                "project": "Joy M2 AI Database",
                "module": "M2",
                "target_release_version": "V1.19",
                "language_policy": "preserve_source_and_store_reviewed_chinese_separately",
                "split_policy": "one_complete_question_per_record",
                "difficulty_policy": "joy_level_1_5",
                "tag_policy": "controlled_primary_type_and_tags",
                "answer_policy": "preserve_source_answer_identity",
                "explanation_policy": "source_or_independently_verified_with_identity",
            },
        )
        self.assertEqual(
            [[entry["relative_path"] for entry in payload[group]] for group in (
                "candidate_records", "source_files", "answer_files", "image_files",
                "teacher_notes_files", "common_errors_files",
            )],
            [
                ["records/candidates.json"],
                ["source/original.mmd.txt", "source/source-map.json"],
                [],
                [
                    "images/9027aeb0-3964-4138-a178-1092ea22ec8a-32_438_671_1398_659.jpg",
                    "images/9027aeb0-3964-4138-a178-1092ea22ec8a-37_573_1010_888_568.jpg",
                    "images/9027aeb0-3964-4138-a178-1092ea22ec8a-38_337_837_334_606.jpg",
                    "images/9027aeb0-3964-4138-a178-1092ea22ec8a-39_527_784_342_678.jpg",
                ],
                [],
                [],
            ],
        )

    def test_same_separate_and_missing_answers_have_exact_staging_and_manifest_semantics(self):
        cases = (
            (
                "same_member",
                b"\xe4\xbe\x8b\xe9\xa1\x8c 1\nEnglish.\n\xe4\xb8\xad\xe6\x96\x87\xe3\x80\x82\n\xe9\xa1\x8c\xe8\xa7\xa3\xef\xbc\x9a\nsource solution\n",
                _minimal_selection(answer_mapping="source_answer"),
                None,
                "source solution\n",
                (),
            ),
            (
                "separate_member",
                b"\xe4\xbe\x8b\xe9\xa1\x8c 1\nEnglish.\n\xe4\xb8\xad\xe6\x96\x87\xe3\x80\x82\n",
                _minimal_selection(answer_mapping="source_answer", answer_number="1"),
                b"\xe4\xbe\x8b\xe9\xa1\x8c 1\n\xe9\xa1\x8c\xe8\xa7\xa3\xef\xbc\x9a\nseparate solution\n",
                "separate solution\n",
                ("answers/answer.mmd.txt",),
            ),
            (
                "missing",
                b"\xe4\xbe\x8b\xe9\xa1\x8c 1\nEnglish.\n\xe4\xb8\xad\xe6\x96\x87\xe3\x80\x82\n",
                _minimal_selection(),
                None,
                "",
                (),
            ),
        )
        for label, primary, selection, answer, solution, answer_paths in cases:
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                args = (
                    self.write_zip_input(root, primary, [selection], answer=answer)
                    if answer is not None
                    else self.write_plain_input(root, primary, [selection])
                )
                package = self.invoke_behavior(*args)
                self.assert_manifest_and_tree_binding(package)
                candidate = self.read_candidate_payload(package)[0]
                source_map = self.read_source_map(package)
                manifest = json.loads(package.manifest_path.read_text(encoding="utf-8"))
                self.assertEqual(candidate["solution_original"], solution)
                self.assertEqual(candidate["solution_verified"], "")
                self.assertEqual(candidate["answer_status"], "source_provided" if solution else "missing_from_source")
                self.assertEqual(
                    (candidate["explanation_text"], candidate["explanation_status"], candidate["explanation_evidence"]),
                    ("", "missing", None),
                )
                self.assertEqual(
                    tuple(entry["relative_path"] for entry in manifest["answer_files"]),
                    answer_paths,
                )
                self.assertEqual(
                    tuple(entry["relative_path"] for entry in manifest["source_files"]),
                    ("source/original.mmd.txt", "source/source-map.json"),
                )
                self.assertEqual(
                    [member["role"] for member in source_map["members"]],
                    ["primary", "answer"] if answer is not None else ["primary"],
                )
                expected_members = [
                    {
                        "role": "primary",
                        "sha256": _sha256(primary),
                        "size_bytes": len(primary),
                        "source_member": "source.mmd",
                        "staged_path": "source/original.mmd.txt",
                    }
                ]
                if answer is not None:
                    expected_members.append(
                        {
                            "role": "answer",
                            "sha256": _sha256(answer),
                            "size_bytes": len(answer),
                            "source_member": "answer.mmd",
                            "staged_path": "answers/answer.mmd.txt",
                        }
                    )
                self.assertEqual(source_map["members"], expected_members)
                solution_member = "answer.mmd" if answer is not None else "source.mmd"
                solution_source = answer if answer is not None else primary
                marker = "題解：\n".encode("utf-8")
                expected_solution_spans = []
                if solution:
                    start_byte = solution_source.index(marker) + len(marker)
                    expected_solution_spans = [
                        {
                            "end_byte": len(solution_source),
                            "member": solution_member,
                            "start_byte": start_byte,
                        }
                    ]
                    self.assertEqual(
                        solution_source[start_byte:len(solution_source)],
                        solution.encode("utf-8"),
                    )
                self.assertEqual(
                    source_map["questions"][0]["solution_spans"],
                    expected_solution_spans,
                )
                self.assertEqual(
                    {
                        span["member"]
                        for span in source_map["questions"][0]["solution_spans"]
                    },
                    ({"answer.mmd"} if answer is not None else ({"source.mmd"} if solution else set())),
                )
                self.assertEqual(source_map["questions"][0]["explanation_spans"], [])
                self.assertEqual(
                    sum(
                        path == "source/original.mmd.txt"
                        for group in MANIFEST_FIELDS[6:12]
                        for path in [
                            *(entry["relative_path"] for entry in manifest[group])
                        ]
                    ),
                    1,
                )
                if answer is not None:
                    self.assertEqual(len(manifest["answer_files"]), 1)
                    answer_evidence = manifest["answer_files"][0]
                    self.assertEqual(tuple(answer_evidence), FILE_EVIDENCE_FIELDS)
                    self.assertEqual(
                        answer_evidence,
                        {
                            "relative_path": "answers/answer.mmd.txt",
                            "sha256": _sha256(answer),
                            "size_bytes": len(answer),
                            "kind": "answer",
                        },
                    )
                    self.assertEqual(
                        (package.package_root / "answers/answer.mmd.txt").read_bytes(),
                        answer,
                    )

    def test_present_and_representable_missing_images_have_distinct_exact_package_semantics(self):
        primary = "例題 1\nEnglish.\n中文。\n![](./images/a.jpg)\n".encode("utf-8")
        image = b"exact image bytes\x00\xff"
        for present in (True, False):
            with self.subTest(present=present), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                selection = _minimal_selection(expected_image_members=["images/a.jpg"])
                args = self.write_plain_input(
                    root,
                    primary,
                    [selection],
                    images={"images/a.jpg": image} if present else None,
                )
                package = self.invoke_behavior(*args)
                candidate = self.read_candidate_payload(package)[0]
                source_map = self.read_source_map(package)
                manifest = json.loads(package.manifest_path.read_text(encoding="utf-8"))
                reference = source_map["questions"][0]["image_references"][0]
                self.assertEqual(candidate["image_paths"], ["images/a.jpg"])
                self.assertEqual(candidate["image_roles"], ["question"])
                self.assertEqual(reference["canonical_path"], "images/a.jpg")
                self.assertEqual(reference["raw_target"], "./images/a.jpg")
                self.assertEqual(reference["selected_member"], "images/a.jpg" if present else None)
                self.assertEqual(reference["sha256"], _sha256(image) if present else None)
                self.assertEqual(
                    [entry["relative_path"] for entry in manifest["image_files"]],
                    ["images/a.jpg"] if present else [],
                )
                staged = package.package_root / "images/a.jpg"
                self.assertEqual(staged.exists(), present)
                if present:
                    self.assertEqual(staged.read_bytes(), image)

    def test_representative_complete_tree_is_byte_identical_to_independent_golden(self):
        baseline_before = _sha256(BASELINE_PATH.read_bytes())
        with tempfile.TemporaryDirectory() as directory:
            with self.assert_historical_v116_zip_untouched():
                package = self.run_representative(Path(directory))
            actual = _tree_bytes(package.package_root)
        self.assertEqual(actual, _tree_bytes(GOLDEN_ROOT))
        self.assertEqual(_sha256(BASELINE_PATH.read_bytes()), baseline_before)
        self.assertFalse((ROOT / "releases/V1.19").exists())
        self.assertFalse((ROOT / "data/baselines/V1.19").exists())


class OutputBoundaryAndAtomicityIntegrationRedTests(AdapterIntegrationRedCase):
    def test_exact_api_runtime_types_are_rejected_before_any_output(self):
        primary = "例題 1\nEnglish.\n中文。\n".encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path, source_path, output_dir, config = self.write_plain_input(
                root,
                primary,
                [_minimal_selection()],
            )
            cases = (
                ("selection_path", str(selection_path), source_path, output_dir, config),
                ("source_path", selection_path, str(source_path), output_dir, config),
                ("output_dir", selection_path, source_path, str(output_dir), config),
                ("config", selection_path, source_path, output_dir, object()),
            )
            for label, selection, source, output, invalid_config in cases:
                with self.subTest(argument=label), self.assertRaises(TypeError):
                    self.invoke_behavior(selection, source, output, invalid_config)
            self.assertFalse(output_dir.exists())

    def test_output_must_be_new_strict_staging_descendant_without_symlink_escape(self):
        primary = "例題 1\nEnglish.\n中文。\n".encode("utf-8")
        for label in (
            "outside",
            "staging_root",
            "releases",
            "baselines",
            "legacy",
            "frozen_images",
            "existing",
            "symlink_escape",
        ):
            with self.subTest(case=label), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                selection_path, source_path, approved, config = self.write_plain_input(
                    root,
                    primary,
                    [_minimal_selection()],
                )
                if label == "outside":
                    output = root / "outside/adapted"
                    expected = ConfigurationError
                elif label == "staging_root":
                    output = config.staging_root
                    expected = ConfigurationError
                elif label == "releases":
                    output = config.releases_root / "V1.19"
                    expected = ConfigurationError
                elif label == "baselines":
                    output = config.baselines_root / "V1.19"
                    expected = ConfigurationError
                elif label == "legacy":
                    output = root / "legacy/adapted"
                    expected = ConfigurationError
                elif label == "frozen_images":
                    output = config.releases_root / "V1.18/images"
                    expected = ConfigurationError
                elif label == "existing":
                    output = approved
                    output.mkdir(parents=True)
                    (output / "sentinel.bin").write_bytes(b"preserve exact sentinel")
                    nested = output / "nested"
                    nested.mkdir()
                    (nested / "child.bin").write_bytes(b"preserve exact child")
                    existing_before = _tree_state(output)
                    expected = OutputConflictError
                else:
                    outside = root / "outside"
                    outside.mkdir()
                    link = config.staging_root / "link"
                    link.parent.mkdir(parents=True)
                    link.symlink_to(outside, target_is_directory=True)
                    output = link / "adapted"
                    expected = ConfigurationError
                with self.observe_fs_mutations() as mutations:
                    with self.assertRaises(expected):
                        self.invoke_behavior(
                            selection_path,
                            source_path,
                            output,
                            config,
                        )
                self.assertEqual(mutations, [], "boundary rejection must precede every write")
                if label == "existing":
                    self.assertEqual(_tree_state(output), existing_before)
                else:
                    self.assertFalse(output.exists())

    def test_write_serialization_rename_and_downstream_failures_leave_no_residue(self):
        primary = "例題 1\nEnglish.\n中文。\n".encode("utf-8")

        class InjectedFailure(Exception):
            pass

        for failure_point in ("write", "serialization", "rename", "downstream"):
            with self.subTest(failure=failure_point), tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                selection_path, source_path, output_dir, config = self.write_plain_input(
                    root,
                    primary,
                    [_minimal_selection()],
                )
                triggered: list[str] = []

                def fail(*_args, **_kwargs):
                    triggered.append(failure_point)
                    raise InjectedFailure(failure_point)

                def write_guard(original, *, os_flags: bool = False):
                    def call(path, *args, **kwargs):
                        if os_flags:
                            flags = args[0] if args else kwargs.get("flags", 0)
                            writing = bool(
                                flags
                                & (
                                    os.O_WRONLY
                                    | os.O_RDWR
                                    | os.O_CREAT
                                    | os.O_TRUNC
                                    | os.O_APPEND
                                )
                            )
                        else:
                            mode = args[0] if args else kwargs.get("mode", "r")
                            writing = any(token in mode for token in "wax+")
                        try:
                            in_staging = Path(path).resolve().is_relative_to(
                                config.staging_root.resolve()
                            )
                        except TypeError:
                            in_staging = False
                        if writing and in_staging:
                            return fail(path, *args, **kwargs)
                        return original(path, *args, **kwargs)

                    return call

                with ExitStack() as stack:
                    if failure_point == "write":
                        stack.enter_context(
                            patch("builtins.open", new=write_guard(builtins.open))
                        )
                        stack.enter_context(patch("io.open", new=write_guard(io.open)))
                        stack.enter_context(
                            patch("os.open", new=write_guard(os.open, os_flags=True))
                        )
                    elif failure_point == "serialization":
                        stack.enter_context(patch("json.dumps", new=fail))
                    elif failure_point == "rename":
                        stack.enter_context(patch("os.rename", new=fail))
                        stack.enter_context(patch("os.replace", new=fail))
                        stack.enter_context(patch.object(Path, "rename", new=fail))
                        stack.enter_context(patch.object(Path, "replace", new=fail))
                    else:
                        stack.enter_context(
                            patch.object(BatchImportManifest, "__post_init__", new=fail)
                        )
                    try:
                        adapt_mmd_package(
                            selection_path,
                            source_path,
                            output_dir,
                            config,
                        )
                    except NotImplementedError as exc:
                        self.assertEqual(str(exc), NOT_IMPLEMENTED_MESSAGE)
                        self.fail(f"adapter behavior RED: {exc}")
                    except Exception:
                        pass
                    else:
                        self.fail("injected failure did not stop adapter publication")
                self.assertTrue(triggered, f"{failure_point} failure was not exercised")
                self.assertFalse(output_dir.exists())
                staging_residue = (
                    list(config.staging_root.rglob("*"))
                    if config.staging_root.exists()
                    else []
                )
                self.assertEqual(staging_residue, [])

    def test_successful_publication_uses_one_final_atomic_destination_transition(self):
        primary = "例題 1\nEnglish.\n中文。\n".encode("utf-8")
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_path, source_path, output_dir, config = self.write_plain_input(
                root,
                primary,
                [_minimal_selection()],
            )
            transitions: list[tuple[Path, Path]] = []
            original_os_rename = os.rename
            original_os_replace = os.replace

            def os_transition(original):
                def call(source, destination, *args, **kwargs):
                    source_path_value = Path(source)
                    destination_path_value = Path(destination)
                    if destination_path_value == output_dir:
                        self.assertFalse(output_dir.exists())
                        self.assertNotEqual(source_path_value, output_dir)
                        transitions.append((source_path_value, destination_path_value))
                    return original(source, destination, *args, **kwargs)

                return call

            with (
                patch("os.rename", new=os_transition(original_os_rename)),
                patch("os.replace", new=os_transition(original_os_replace)),
            ):
                package = self.invoke_behavior(
                    selection_path,
                    source_path,
                    output_dir,
                    config,
                )
            self.assertEqual(package.package_root, output_dir)
            self.assertTrue(output_dir.is_dir())
            self.assertEqual(len(transitions), 1)
            self.assertEqual({destination for _, destination in transitions}, {output_dir})
            self.assertEqual(
                [
                    path
                    for path in config.staging_root.iterdir()
                    if path.resolve() != output_dir.resolve()
                ],
                [],
            )


class DeterminismAndGoldenEquivalenceIntegrationRedTests(AdapterIntegrationRedCase):
    def test_distinct_source_output_and_temp_roots_produce_identical_representative_tree(self):
        observed: list[dict[str, bytes]] = []
        manifests: list[BatchImportManifest] = []
        preflights = []
        runtime_roots: list[str] = []
        for _ in range(2):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source_root = root / "input"
                source_root.mkdir()
                shutil.copy2(REPRESENTATIVE_ROOT / "vector.mmd", source_root / "vector.mmd")
                shutil.copy2(REPRESENTATIVE_ROOT / "selection.json", source_root / "selection.json")
                shutil.copytree(REPRESENTATIVE_ROOT / "images", source_root / "images")
                package = self.invoke_behavior(
                    source_root / "selection.json",
                    source_root / "vector.mmd",
                    root / "data/staging/another-temp-name/adapted",
                    PipelineConfig(root),
                )
                self.assert_manifest_and_tree_binding(package)
                observed.append(_tree_bytes(package.package_root))
                manifests.append(package.manifest)
                preflights.append(
                    preflight_import(
                        package.manifest,
                        package.package_root,
                        _baseline_ref(),
                    )
                )
                runtime_roots.append(str(root))
        self.assertEqual(observed[0], observed[1])
        self.assertEqual(manifests[0], manifests[1])
        self.assertEqual(preflights[0], preflights[1])
        self.assertEqual(preflights[0].report, preflights[1].report)
        self.assertEqual(
            preflights[0].report.preflight_sha256,
            preflights[1].report.preflight_sha256,
        )
        for tree in observed:
            joined = b"\n".join(tree.values())
            for runtime_root in runtime_roots:
                self.assertNotIn(runtime_root.encode("utf-8"), joined)

    def test_plain_zip_physical_order_timestamp_permissions_and_comment_are_nonsemantic(self):
        primary = "例題 1\nEnglish.\n中文。\n![](./images/a.jpg)\n".encode("utf-8")
        image = b"deterministic image bytes"
        selection = _minimal_selection(expected_image_members=["images/a.jpg"])
        trees: list[dict[str, bytes]] = []
        manifests: list[BatchImportManifest] = []
        preflights = []
        outer_hashes: list[str] = []
        configurations = (
            ("plain", None, None, None, None),
            ("zip_a", ("source.mmd", "images/a.jpg"), (1980, 1, 1, 0, 0, 0), 0o100644, b"first"),
            ("zip_b", ("images/a.jpg", "source.mmd"), (2024, 6, 7, 8, 9, 10), 0o100600, b"second"),
        )
        for label, order, timestamp, permissions, comment in configurations:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                if label == "plain":
                    args = self.write_plain_input(
                        root,
                        primary,
                        [selection],
                        images={"images/a.jpg": image},
                    )
                else:
                    args = self.write_zip_input(
                        root,
                        primary,
                        [selection],
                        images={"images/a.jpg": image},
                        member_order=order,
                        timestamp=timestamp,
                        permissions=permissions,
                        archive_comment=comment,
                    )
                    outer_hashes.append(_sha256(args[1].read_bytes()))
                package = self.invoke_behavior(*args)
                self.assert_manifest_and_tree_binding(package)
                trees.append(_tree_bytes(package.package_root))
                manifests.append(package.manifest)
                preflights.append(
                    preflight_import(
                        package.manifest,
                        package.package_root,
                        _baseline_ref(),
                    )
                )
        self.assertEqual(trees[0], trees[1])
        self.assertEqual(trees[1], trees[2])
        self.assertEqual(manifests[0], manifests[1])
        self.assertEqual(manifests[1], manifests[2])
        self.assertEqual(preflights[0], preflights[1])
        self.assertEqual(preflights[1], preflights[2])
        self.assertEqual(preflights[0].report, preflights[1].report)
        self.assertEqual(preflights[1].report, preflights[2].report)
        self.assertEqual(
            {result.report.preflight_sha256 for result in preflights},
            {preflights[0].report.preflight_sha256},
        )
        self.assertNotEqual(outer_hashes[0], outer_hashes[1])
        for tree in trees[1:]:
            joined = b"\n".join(tree.values())
            for outer_hash in outer_hashes:
                self.assertNotIn(outer_hash.encode("ascii"), joined)

    def test_filesystem_image_creation_order_does_not_change_first_reference_output_order(self):
        primary = (
            "例題 1\nEnglish.\n中文。\n"
            "![](./images/z.jpg)\n![](./images/a.jpg)\n"
        ).encode("utf-8")
        selection = _minimal_selection(
            expected_image_members=["images/z.jpg", "images/a.jpg"]
        )
        image_pairs = (("images/z.jpg", b"z"), ("images/a.jpg", b"a"))
        trees = []
        for order in (image_pairs, tuple(reversed(image_pairs))):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                args = self.write_plain_input(
                    root,
                    primary,
                    [selection],
                    images=dict(order),
                )
                package = self.invoke_behavior(*args)
                trees.append(_tree_bytes(package.package_root))
                manifest = json.loads(package.manifest_path.read_text(encoding="utf-8"))
                self.assertEqual(
                    [entry["relative_path"] for entry in manifest["image_files"]],
                    ["images/z.jpg", "images/a.jpg"],
                )
        self.assertEqual(trees[0], trees[1])

    def test_semantic_selection_reorder_changes_candidates_source_map_manifest_and_preflight(self):
        primary = (
            "例題 1\nEnglish one.\n中文一。\n"
            "例題 2\nEnglish two.\n中文二。\n"
        ).encode("utf-8")
        forward = [
            _minimal_selection(proposed_question_id="ONE", number="1"),
            _minimal_selection(proposed_question_id="TWO", number="2"),
        ]
        observed = []
        for selections in (forward, list(reversed(forward))):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                package = self.invoke_behavior(
                    *self.write_plain_input(root, primary, selections)
                )
                candidates = self.read_candidate_payload(package)
                source_map = self.read_source_map(package)
                loaded = load_import_manifest(package.manifest_path, package.package_root)
                preflight = preflight_import(loaded, package.package_root, _baseline_ref())
                observed.append(
                    (
                        [item["proposed_question_id"] for item in candidates],
                        [item["proposed_question_id"] for item in source_map["questions"]],
                        package.manifest_path.read_bytes(),
                        preflight.report.preflight_sha256,
                        (package.package_root / "source/original.mmd.txt").read_bytes(),
                    )
                )
        self.assertEqual(observed[0][0], ["ONE", "TWO"])
        self.assertEqual(observed[1][0], ["TWO", "ONE"])
        self.assertEqual(observed[0][0], observed[0][1])
        self.assertEqual(observed[1][0], observed[1][1])
        self.assertNotEqual(observed[0][2], observed[1][2])
        self.assertNotEqual(observed[0][3], observed[1][3])
        self.assertEqual(observed[0][4], observed[1][4])

    def test_adapter_and_independent_golden_match_every_task9a_authority_dimension(self):
        with tempfile.TemporaryDirectory() as directory:
            package = self.run_representative(Path(directory))
            actual_manifest = load_import_manifest(
                package.manifest_path,
                package.package_root,
            )
            actual = preflight_import(actual_manifest, package.package_root, _baseline_ref())
            golden_manifest = load_import_manifest(
                GOLDEN_ROOT / "import_manifest.json",
                GOLDEN_ROOT,
            )
            golden = preflight_import(golden_manifest, GOLDEN_ROOT, _baseline_ref())
            actual_tree = _tree_bytes(package.package_root)
        self.assertEqual(actual.candidates, golden.candidates)
        self.assertEqual(actual.issues, golden.issues)
        self.assertEqual(
            (
                actual.report.detected_count,
                actual.report.new_candidate_count,
                actual.report.duplicate_count,
                actual.report.rejected_count,
                actual.report.ambiguous_count,
                actual.report.status,
            ),
            (
                golden.report.detected_count,
                golden.report.new_candidate_count,
                golden.report.duplicate_count,
                golden.report.rejected_count,
                golden.report.ambiguous_count,
                golden.report.status,
            ),
        )
        duplicate_codes = {"duplicate_exact", "duplicate_id", "duplicate_ambiguous"}
        self.assertEqual(
            tuple(issue for issue in actual.issues if issue.code in duplicate_codes),
            tuple(issue for issue in golden.issues if issue.code in duplicate_codes),
        )
        self.assertEqual(actual.report.adaptations, golden.report.adaptations)
        self.assertEqual(actual.report, golden.report)
        self.assertEqual(actual.report.preflight_sha256, golden.report.preflight_sha256)
        self.assertEqual(actual_tree, _tree_bytes(GOLDEN_ROOT))


if __name__ == "__main__":
    unittest.main()
