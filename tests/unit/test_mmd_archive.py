from contextlib import contextmanager
import builtins
import hashlib
import io
import json
import os
from pathlib import Path
import stat
import struct
import sys
import tempfile
import unittest
from unittest import mock
import warnings
import zipfile


ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from joy_m2.config import PipelineConfig
from joy_m2.errors import InputFormatError, InputMissingError
from joy_m2.ingest.adapter import adapt_mmd_package
from joy_m2.ingest.adapter_models import MmdAdapterBlockedError


HEX_ZERO = "0" * 64
MIB = 1024 * 1024


def _observe_bytes(
    record: dict[str, object],
    expected: bytes | None,
    value,
    *,
    start: int,
    end: int,
    unbounded: bool = False,
):
    if not isinstance(value, bytes):
        raise AssertionError("archive/source content must be read as bytes")
    record["read_calls"] = int(record["read_calls"]) + 1
    intervals = record["intervals"]
    assert isinstance(intervals, list)
    observed_end = start + len(value)
    if end != observed_end or start < 0:
        record["content_matches"] = False
    if expected is not None:
        if observed_end > len(expected) or expected[start:observed_end] != value:
            record["content_matches"] = False
        if end == len(expected) and (value or unbounded or start == len(expected)):
            record["eof"] = True
    elif not value or unbounded:
        record["eof"] = True
    if value:
        intervals.append((start, observed_end))
    return value


class _ObservedBinaryStream:
    def __init__(self, stream, expected: bytes | None, record: dict[str, object]):
        self._stream = stream
        self._expected = expected
        self._record = record

    def _observe(self, value, *, start: int, end: int, unbounded: bool = False):
        return _observe_bytes(
            self._record,
            self._expected,
            value,
            start=start,
            end=end,
            unbounded=unbounded,
        )

    def read(self, size: int = -1):
        start = self._stream.tell()
        value = self._stream.read(size)
        return self._observe(
            value,
            start=start,
            end=self._stream.tell(),
            unbounded=size < 0,
        )

    def read1(self, size: int = -1):
        start = self._stream.tell()
        value = self._stream.read1(size)
        return self._observe(
            value,
            start=start,
            end=self._stream.tell(),
            unbounded=size < 0,
        )

    def readinto(self, buffer):
        start = self._stream.tell()
        count = self._stream.readinto(buffer)
        data = bytes(memoryview(buffer)[:count]) if count else b""
        self._observe(data, start=start, end=self._stream.tell())
        return count

    def readinto1(self, buffer):
        start = self._stream.tell()
        count = self._stream.readinto1(buffer)
        data = bytes(memoryview(buffer)[:count]) if count else b""
        self._observe(data, start=start, end=self._stream.tell())
        return count

    def readline(self, size: int = -1):
        start = self._stream.tell()
        value = self._stream.readline(size)
        return self._observe(value, start=start, end=self._stream.tell())

    def readlines(self, hint: int = -1):
        start = self._stream.tell()
        values = self._stream.readlines(hint)
        for value in values:
            end = start + len(value)
            self._observe(value, start=start, end=end)
            start = end
        if not values:
            self._observe(b"", start=start, end=self._stream.tell())
        return values

    def __iter__(self):
        return self

    def __next__(self):
        start = self._stream.tell()
        value = self._stream.readline()
        if not value:
            self._observe(b"", start=start, end=self._stream.tell())
            raise StopIteration
        return self._observe(value, start=start, end=self._stream.tell())

    def seek(self, offset: int, whence: int = os.SEEK_SET):
        return self._stream.seek(offset, whence)

    def tell(self):
        return self._stream.tell()

    def __enter__(self):
        self._stream.__enter__()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return self._stream.__exit__(exc_type, exc_value, traceback)

    def __getattr__(self, name):
        return getattr(self._stream, name)


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(MIB), b""):
            digest.update(chunk)
    return digest.hexdigest()


class MmdArchiveSafetyTests(unittest.TestCase):
    def assert_behavior(self, callback):
        try:
            return callback()
        except NotImplementedError as exc:
            self.fail(f"adapter behavior RED: {exc}")

    def write_plain_source(
        self,
        root: Path,
        *,
        name: str = "source.mmd",
        content: bytes = b"plain MMD source\n",
    ) -> Path:
        source_path = root / name
        source_path.write_bytes(content)
        return source_path

    def write_zip_source(
        self,
        root: Path,
        *,
        name: str = "source.mmd.zip",
        members: dict[str, bytes] | None = None,
    ) -> Path:
        source_path = root / name
        with zipfile.ZipFile(source_path, "w") as archive:
            for member_name, content in (members or {"primary.mmd": b"source\n"}).items():
                info = zipfile.ZipInfo(member_name, date_time=(1980, 1, 1, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                info.compress_type = zipfile.ZIP_DEFLATED
                archive.writestr(info, content)
        return source_path

    def write_zip_entries(
        self,
        root: Path,
        entries: list[tuple[str, bytes, int]],
        *,
        name: str = "source.mmd.zip",
    ) -> Path:
        source_path = root / name
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(source_path, "w") as archive:
                for member_name, content, mode in entries:
                    info = zipfile.ZipInfo(
                        member_name,
                        date_time=(1980, 1, 1, 0, 0, 0),
                    )
                    info.create_system = 3
                    info.external_attr = mode << 16
                    info.compress_type = zipfile.ZIP_STORED
                    archive.writestr(info, content)
        return source_path

    def write_selection_manifest(
        self,
        root: Path,
        source_path: Path,
        *,
        source_kind: str,
        source_sha256: str | None = None,
        primary_member: str | None = None,
        answer_member: str | None = None,
        selections: list[dict[str, object]] | None = None,
    ) -> Path:
        manifest_path = root / "selection.json"
        payload = {
            "schema_version": "task9b-mmd-adapter-v1",
            "batch_id": "TASK9B-ARCHIVE-RED",
            "source_kind": source_kind,
            "source_sha256": source_sha256
            or _file_sha256(source_path),
            "primary_member": primary_member
            or (source_path.name if source_kind == "mmd" else "primary.mmd"),
            "answer_member": answer_member,
            "source_id": "TASK9B-ARCHIVE-RED-SOURCE",
            "chapter": "向量及其应用",
            "expected_candidate_count": len(selections or []),
            "selections": selections or [],
        }
        manifest_path.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        return manifest_path

    def invoke_adapter(
        self,
        root: Path,
        selection_manifest_path: Path,
        source_path: Path,
    ):
        return self.assert_behavior(
            lambda: adapt_mmd_package(
                selection_manifest_path,
                source_path,
                root / "data" / "staging" / "adapted",
                PipelineConfig(root),
            )
        )

    def assert_blocked_issue(
        self,
        root: Path,
        selection_manifest_path: Path,
        source_path: Path,
        *,
        code: str,
        field: str,
        reason: str,
        expected_evidence: dict[str, object] | None = None,
    ) -> None:
        with self.assertRaises(MmdAdapterBlockedError) as caught:
            self.invoke_adapter(root, selection_manifest_path, source_path)
        self.assertEqual(len(caught.exception.issues), 1)
        issue = caught.exception.issues[0]
        self.assertEqual(
            (
                issue.code,
                issue.severity,
                issue.proposed_question_id,
                issue.source_locator,
                issue.field,
            ),
            (code, "blocking", None, "", field),
        )
        evidence = json.loads(issue.evidence)
        self.assertEqual(evidence.get("reason"), reason)
        self.assertEqual(
            issue.evidence,
            json.dumps(
                evidence,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )
        expected_keys = {
            "source_contract_mismatch": {"actual", "expected", "reason"},
            "unsupported_source_format": {"actual", "expected", "reason"},
            "archive_integrity_invalid": {"actual", "limit", "member", "reason"},
        }
        self.assertEqual(set(evidence), expected_keys[code])
        if expected_evidence is not None:
            self.assertEqual(evidence, expected_evidence)
        if reason == "zip_structure":
            self.assertIsNone(evidence["actual"])
            self.assertIsNone(evidence["limit"])
            self.assertIsNone(evidence["member"])

    def assert_archive_member_reason(
        self,
        root: Path,
        source_path: Path,
        *,
        reason: str,
        member_names: tuple[str, ...],
    ) -> None:
        selection_manifest_path = self.write_selection_manifest(
            root,
            source_path,
            source_kind="mmd_zip",
            primary_member="primary.mmd",
        )
        with self.assertRaises(MmdAdapterBlockedError) as caught:
            self.invoke_adapter(root, selection_manifest_path, source_path)

        self.assertEqual(len(caught.exception.issues), len(member_names))
        expected_evidence = tuple(
            sorted(
                json.dumps(
                    {
                        "member_name_sha256": hashlib.sha256(name.encode("utf-8")).hexdigest(),
                        "reason": reason,
                    },
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                for name in member_names
            )
        )
        observed_evidence = []
        for issue in caught.exception.issues:
            self.assertEqual(issue.severity, "blocking")
            self.assertEqual(issue.proposed_question_id, None)
            self.assertEqual(issue.source_locator, "")
            self.assertEqual(issue.code, "archive_member_unsafe")
            self.assertEqual(issue.field, "archive_member")
            evidence = json.loads(issue.evidence)
            self.assertEqual(set(evidence), {"member_name_sha256", "reason"})
            self.assertEqual(evidence["reason"], reason)
            self.assertRegex(evidence["member_name_sha256"], r"^[0-9a-f]{64}$")
            self.assertEqual(
                issue.evidence,
                json.dumps(
                    evidence,
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                ),
            )
            observed_evidence.append(issue.evidence)
        self.assertEqual(tuple(observed_evidence), expected_evidence)

    def assert_archive_integrity_reason(
        self,
        root: Path,
        source_path: Path,
        *,
        reason: str,
        member: str = "primary.mmd",
    ) -> None:
        selection_manifest_path = self.write_selection_manifest(
            root,
            source_path,
            source_kind="mmd_zip",
            primary_member="primary.mmd",
        )
        with self.assertRaises(MmdAdapterBlockedError) as caught:
            self.invoke_adapter(root, selection_manifest_path, source_path)

        self.assertEqual(len(caught.exception.issues), 1)
        issue = caught.exception.issues[0]
        self.assertEqual(issue.severity, "blocking")
        self.assertEqual(issue.proposed_question_id, None)
        self.assertEqual(issue.source_locator, "")
        self.assertEqual(issue.code, "archive_integrity_invalid")
        self.assertEqual(issue.field, "archive")
        evidence = json.loads(issue.evidence)
        self.assertEqual(set(evidence), {"actual", "limit", "member", "reason"})
        self.assertEqual(evidence["reason"], reason)
        self.assertEqual(
            issue.evidence,
            json.dumps(
                evidence,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )
        expected_by_reason = {
            "encrypted": {
                "actual": True,
                "limit": None,
                "member": member,
                "reason": "encrypted",
            },
            "compression": {
                "actual": 99,
                "limit": [zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED],
                "member": member,
                "reason": "compression",
            },
            "crc": {
                "actual": None,
                "limit": None,
                "member": member,
                "reason": "crc",
            },
            "decompression": {
                "actual": None,
                "limit": None,
                "member": member,
                "reason": "decompression",
            },
        }
        self.assertEqual(evidence, expected_by_reason[reason])

    def capture_blocked_issues(
        self,
        root: Path,
        selection_manifest_path: Path,
        source_path: Path,
    ):
        with self.assertRaises(MmdAdapterBlockedError) as caught:
            self.invoke_adapter(root, selection_manifest_path, source_path)
        return caught.exception.issues

    def assert_limit_boundary(
        self,
        root: Path,
        selection_manifest_path: Path,
        source_path: Path,
        *,
        reason: str,
        exceeds: bool,
        expected_actual: int | float,
        expected_limit: int | float,
        expected_member: str | None,
    ) -> None:
        issues = self.capture_blocked_issues(
            root,
            selection_manifest_path,
            source_path,
        )
        reasons = tuple(json.loads(issue.evidence).get("reason") for issue in issues)
        if exceeds:
            self.assertIn(reason, reasons)
            matching = [
                issue
                for issue in issues
                if json.loads(issue.evidence).get("reason") == reason
            ]
            self.assertEqual(len(matching), 1)
            for issue in matching:
                self.assertEqual(issue.severity, "blocking")
                self.assertEqual(issue.proposed_question_id, None)
                self.assertEqual(issue.source_locator, "")
                self.assertEqual(issue.code, "archive_integrity_invalid")
                self.assertEqual(issue.field, "archive")
                self.assertEqual(
                    set(json.loads(issue.evidence)),
                    {"actual", "limit", "member", "reason"},
                )
                expected_evidence = {
                    "actual": expected_actual,
                    "limit": expected_limit,
                    "member": expected_member,
                    "reason": reason,
                }
                self.assertEqual(json.loads(issue.evidence), expected_evidence)
                self.assertEqual(
                    issue.evidence,
                    json.dumps(
                        expected_evidence,
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                )
        else:
            self.assertNotIn(reason, reasons)
            self.assertTrue(issues, "the deliberate later-stage blocker disappeared")

    def assert_selected_member_missing(
        self,
        root: Path,
        selection_manifest_path: Path,
        source_path: Path,
        *,
        field: str,
        member: str,
    ) -> None:
        with self.assertRaises(MmdAdapterBlockedError) as caught:
            self.invoke_adapter(root, selection_manifest_path, source_path)

        self.assertEqual(len(caught.exception.issues), 1)
        issue = caught.exception.issues[0]
        self.assertEqual(issue.code, "selection_not_unique")
        self.assertEqual(issue.severity, "blocking")
        self.assertEqual(issue.proposed_question_id, None)
        self.assertEqual(issue.source_locator, "")
        self.assertEqual(issue.field, field)
        expected = {"member": member, "reason": "selected_member_missing"}
        self.assertEqual(json.loads(issue.evidence), expected)
        self.assertEqual(
            issue.evidence,
            json.dumps(
                expected,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ),
        )

    def patch_first_zip_entry_metadata(
        self,
        source_path: Path,
        *,
        flag_bits_or: int = 0,
        compression: int | None = None,
    ) -> None:
        payload = bytearray(source_path.read_bytes())
        local = payload.index(b"PK\x03\x04")
        central = payload.index(b"PK\x01\x02")
        if flag_bits_or:
            struct.pack_into(
                "<H",
                payload,
                local + 6,
                struct.unpack_from("<H", payload, local + 6)[0] | flag_bits_or,
            )
            struct.pack_into(
                "<H",
                payload,
                central + 8,
                struct.unpack_from("<H", payload, central + 8)[0] | flag_bits_or,
            )
        if compression is not None:
            struct.pack_into("<H", payload, local + 8, compression)
            struct.pack_into("<H", payload, central + 10, compression)
        source_path.write_bytes(payload)

    def patch_zip_entry_metadata(
        self,
        source_path: Path,
        *,
        index: int,
        flag_bits_or: int = 0,
        compression: int | None = None,
        compressed_size: int | None = None,
        uncompressed_size: int | None = None,
    ) -> None:
        payload = bytearray(source_path.read_bytes())

        def signature_offsets(signature: bytes) -> list[int]:
            offsets = []
            cursor = 0
            while True:
                try:
                    cursor = payload.index(signature, cursor)
                except ValueError:
                    return offsets
                offsets.append(cursor)
                cursor += len(signature)

        local_offsets = signature_offsets(b"PK\x03\x04")
        central_offsets = signature_offsets(b"PK\x01\x02")
        self.assertLess(index, len(local_offsets))
        self.assertLess(index, len(central_offsets))
        local = local_offsets[index]
        central = central_offsets[index]
        if flag_bits_or:
            struct.pack_into(
                "<H",
                payload,
                local + 6,
                struct.unpack_from("<H", payload, local + 6)[0] | flag_bits_or,
            )
            struct.pack_into(
                "<H",
                payload,
                central + 8,
                struct.unpack_from("<H", payload, central + 8)[0] | flag_bits_or,
            )
        if compression is not None:
            struct.pack_into("<H", payload, local + 8, compression)
            struct.pack_into("<H", payload, central + 10, compression)
        if compressed_size is not None:
            struct.pack_into("<I", payload, local + 18, compressed_size)
            struct.pack_into("<I", payload, central + 20, compressed_size)
        if uncompressed_size is not None:
            struct.pack_into("<I", payload, local + 22, uncompressed_size)
            struct.pack_into("<I", payload, central + 24, uncompressed_size)
        source_path.write_bytes(payload)

    def patch_zip_member_name(
        self,
        source_path: Path,
        *,
        original: str,
        replacement: str,
    ) -> None:
        original_bytes = original.encode("utf-8")
        replacement_bytes = replacement.encode("utf-8")
        self.assertEqual(len(original_bytes), len(replacement_bytes))
        payload = source_path.read_bytes()
        self.assertEqual(payload.count(original_bytes), 2)
        source_path.write_bytes(payload.replace(original_bytes, replacement_bytes))

    def corrupt_first_zip_member_payload(
        self,
        source_path: Path,
        *,
        replace_all: bool,
    ) -> None:
        payload = bytearray(source_path.read_bytes())
        local = payload.index(b"PK\x03\x04")
        compressed_size = struct.unpack_from("<I", payload, local + 18)[0]
        name_size = struct.unpack_from("<H", payload, local + 26)[0]
        extra_size = struct.unpack_from("<H", payload, local + 28)[0]
        data_start = local + 30 + name_size + extra_size
        self.assertGreater(compressed_size, 0)
        if replace_all:
            payload[data_start : data_start + compressed_size] = b"\x00" * compressed_size
        else:
            payload[data_start] ^= 0xFF
        source_path.write_bytes(payload)

    def patch_zip_central_sizes(
        self,
        source_path: Path,
        sizes: list[tuple[int, int]],
    ) -> None:
        payload = bytearray(source_path.read_bytes())
        offset = 0
        observed = 0
        while True:
            try:
                central = payload.index(b"PK\x01\x02", offset)
            except ValueError:
                break
            if observed >= len(sizes):
                break
            compressed_size, uncompressed_size = sizes[observed]
            struct.pack_into("<I", payload, central + 20, compressed_size)
            struct.pack_into("<I", payload, central + 24, uncompressed_size)
            name_size = struct.unpack_from("<H", payload, central + 28)[0]
            extra_size = struct.unpack_from("<H", payload, central + 30)[0]
            comment_size = struct.unpack_from("<H", payload, central + 32)[0]
            offset = central + 46 + name_size + extra_size + comment_size
            observed += 1
        self.assertEqual(observed, len(sizes))
        source_path.write_bytes(payload)

    def prepend_zip_to_exact_size(self, source_path: Path, size_bytes: int) -> None:
        zip_bytes = source_path.read_bytes()
        self.assertLessEqual(len(zip_bytes), size_bytes)
        with source_path.open("wb") as stream:
            prefix_size = size_bytes - len(zip_bytes)
            if prefix_size:
                stream.seek(prefix_size - 1)
                stream.write(b"\x00")
            stream.write(zip_bytes)
        self.assertEqual(source_path.stat().st_size, size_bytes)

    def minimal_selection(self, image_member: str) -> dict[str, object]:
        return {
            "proposed_question_id": "TASK9B-ARCHIVE-RED-EXAMPLE-01",
            "kind": "example",
            "number": "1",
            "source_section": "例題",
            "language_layout": "english_then_chinese",
            "answer_mapping": "missing_from_source",
            "answer_number": None,
            "expected_image_members": [image_member],
            "primary_type": "向量",
            "tags": [],
            "tag_status": "missing",
            "difficulty_level": None,
            "difficulty_status": "missing",
        }

    def observed_binary_stream(
        self,
        stream,
        expected: bytes,
        records: list[dict[str, object]],
    ) -> _ObservedBinaryStream:
        record: dict[str, object] = {
            "intervals": [],
            "content_matches": True,
            "eof": False,
            "read_calls": 0,
        }
        records.append(record)
        return _ObservedBinaryStream(stream, expected, record)

    def assert_complete_read_passes(
        self,
        records: list[dict[str, object]],
        expected: bytes,
        *,
        minimum: int,
        label: str,
    ) -> None:
        complete = []
        for record in records:
            cursor = 0
            intervals = record["intervals"]
            assert isinstance(intervals, list)
            for start, end in sorted(intervals):
                if start > cursor:
                    break
                cursor = max(cursor, end)
            if (
                int(record["read_calls"]) > 0
                and record["eof"] is True
                and record["content_matches"] is True
                and cursor >= len(expected)
            ):
                complete.append(record)
        self.assertGreaterEqual(
            len(complete),
            minimum,
            f"{label} was not fully read through EOF for {minimum} required pass(es)",
        )

    @contextmanager
    def observe_exact_file_reads(self, target: Path, expected: bytes):
        records: list[dict[str, object]] = []
        descriptor_records: dict[int, dict[str, object]] = {}
        real_builtin_open = builtins.open
        real_io_open = io.open
        real_os_open = os.open
        real_os_read = os.read
        real_os_lseek = os.lseek
        real_os_close = os.close

        def is_target(value) -> bool:
            return isinstance(value, (str, bytes, os.PathLike)) and Path(value) == target

        def observed_stream_open(original):
            def call(path, *args, **kwargs):
                stream = original(path, *args, **kwargs)
                if is_target(path):
                    return self.observed_binary_stream(stream, expected, records)
                return stream

            return call

        def observed_os_open(path, flags, *args, **kwargs):
            descriptor = real_os_open(path, flags, *args, **kwargs)
            if is_target(path):
                record: dict[str, object] = {
                    "intervals": [],
                    "content_matches": True,
                    "eof": False,
                    "read_calls": 0,
                }
                records.append(record)
                descriptor_records[descriptor] = record
            return descriptor

        def observed_os_read(descriptor, size):
            record = descriptor_records.get(descriptor)
            start = (
                real_os_lseek(descriptor, 0, os.SEEK_CUR)
                if record is not None
                else None
            )
            value = real_os_read(descriptor, size)
            if record is not None:
                assert start is not None
                _observe_bytes(
                    record,
                    expected,
                    value,
                    start=start,
                    end=real_os_lseek(descriptor, 0, os.SEEK_CUR),
                )
            return value

        def observed_os_close(descriptor):
            descriptor_records.pop(descriptor, None)
            return real_os_close(descriptor)

        with (
            mock.patch("builtins.open", new=observed_stream_open(real_builtin_open)),
            mock.patch("io.open", new=observed_stream_open(real_io_open)),
            mock.patch("os.open", new=observed_os_open),
            mock.patch("os.read", new=observed_os_read),
            mock.patch("os.close", new=observed_os_close),
        ):
            yield records

    def assert_reaches_downstream_boundary(
        self,
        root: Path,
        selection_manifest_path: Path,
        source_path: Path,
        *,
        expect_zip_member_stream: bool,
        expected_plain_bytes: bytes | None = None,
    ) -> None:
        metadata_accesses = {"count": 0}
        source_read_passes: list[dict[str, object]] = []
        downstream_not_implemented = None
        real_member_open = zipfile.ZipFile.open
        real_builtin_open = builtins.open
        real_io_open = io.open
        real_os_open = os.open
        real_os_read = os.read
        real_os_lseek = os.lseek
        real_os_close = os.close
        real_os_stat = os.stat
        real_os_lstat = os.lstat
        real_os_access = os.access
        expected_source_bytes = source_path.read_bytes()
        source_fd_records: dict[int, dict[str, object]] = {}
        expected_zip_members: dict[str, bytes] = {}
        if expect_zip_member_stream:
            with zipfile.ZipFile(source_path) as archive:
                expected_zip_members = {
                    info.filename: archive.read(info)
                    for info in archive.infolist()
                    if not info.is_dir()
                }
        zip_member_read_passes: dict[str, list[dict[str, object]]] = {
            member: [] for member in expected_zip_members
        }

        def observes_source(value) -> bool:
            return isinstance(value, (str, bytes, os.PathLike)) and Path(value) == source_path

        def observed_source_open(original):
            def call(target, *args, **kwargs):
                stream = original(target, *args, **kwargs)
                if observes_source(target):
                    return self.observed_binary_stream(
                        stream,
                        expected_source_bytes,
                        source_read_passes,
                    )
                return stream

            return call

        def observed_metadata_access(original):
            def call(target, *args, **kwargs):
                if observes_source(target):
                    metadata_accesses["count"] += 1
                return original(target, *args, **kwargs)

            return call

        def observed_os_open(target, flags, *args, **kwargs):
            descriptor = real_os_open(target, flags, *args, **kwargs)
            if observes_source(target):
                record: dict[str, object] = {
                    "intervals": [],
                    "content_matches": True,
                    "eof": False,
                    "read_calls": 0,
                }
                source_read_passes.append(record)
                source_fd_records[descriptor] = record
            return descriptor

        def observed_os_read(descriptor, size):
            record = source_fd_records.get(descriptor)
            start = (
                real_os_lseek(descriptor, 0, os.SEEK_CUR)
                if record is not None
                else None
            )
            value = real_os_read(descriptor, size)
            if record is not None:
                assert start is not None
                _observe_bytes(
                    record,
                    expected_source_bytes,
                    value,
                    start=start,
                    end=real_os_lseek(descriptor, 0, os.SEEK_CUR),
                )
            return value

        def observed_os_close(descriptor):
            source_fd_records.pop(descriptor, None)
            return real_os_close(descriptor)

        def observed_member_open(archive, member, *args, **kwargs):
            stream = real_member_open(archive, member, *args, **kwargs)
            info = member if isinstance(member, zipfile.ZipInfo) else archive.getinfo(member)
            expected = expected_zip_members.get(info.filename)
            if expected is None:
                return stream
            return self.observed_binary_stream(
                stream,
                expected,
                zip_member_read_passes[info.filename],
            )

        with (
            mock.patch("builtins.open", new=observed_source_open(real_builtin_open)),
            mock.patch("io.open", new=observed_source_open(real_io_open)),
            mock.patch("os.open", new=observed_os_open),
            mock.patch("os.read", new=observed_os_read),
            mock.patch("os.close", new=observed_os_close),
            mock.patch("os.stat", new=observed_metadata_access(real_os_stat)),
            mock.patch("os.lstat", new=observed_metadata_access(real_os_lstat)),
            mock.patch("os.access", new=observed_metadata_access(real_os_access)),
            mock.patch.object(zipfile.ZipFile, "open", new=observed_member_open),
        ):
            try:
                result = adapt_mmd_package(
                    selection_manifest_path,
                    source_path,
                    root / "data" / "staging" / "adapted",
                    PipelineConfig(root),
                )
            except NotImplementedError as exc:
                self.assertEqual(str(exc), "Task 9B adapter behavior is not implemented")
                downstream_not_implemented = exc
            except MmdAdapterBlockedError as exc:
                self.assertTrue(exc.issues)
                self.assertTrue(
                    all(issue.code == "mmd_parse_failed" for issue in exc.issues),
                    "a source-kind continue row may only stop at the later parser layer",
                )
            else:
                self.assertIsNotNone(result)

        if not source_read_passes and downstream_not_implemented is not None:
            self.fail(f"adapter behavior RED: {downstream_not_implemented}")
        self.assertTrue(source_read_passes, "D1 never opened the actual source bytes")
        if expected_plain_bytes is not None:
            self.assert_complete_read_passes(
                source_read_passes,
                expected_plain_bytes,
                minimum=1,
                label="D1 plain source kind/hash input",
            )
        if expect_zip_member_stream:
            for member, expected in expected_zip_members.items():
                self.assert_complete_read_passes(
                    zip_member_read_passes[member],
                    expected,
                    minimum=1,
                    label=f"D2 regular member {member}",
                )

    def reach_post_archive_boundary(
        self,
        root: Path,
        selection_manifest_path: Path,
        source_path: Path,
    ) -> NotImplementedError | None:
        try:
            adapt_mmd_package(
                selection_manifest_path,
                source_path,
                root / "data" / "staging" / "adapted",
                PipelineConfig(root),
            )
        except NotImplementedError as exc:
            self.assertEqual(str(exc), "Task 9B adapter behavior is not implemented")
            return exc
        except MmdAdapterBlockedError as exc:
            self.assertTrue(exc.issues)
            self.assertTrue(
                all(issue.code == "mmd_parse_failed" for issue in exc.issues),
                "the archive-safe invalid source may block only at downstream D3",
            )
            return None
        self.fail("the deliberately invalid MMD unexpectedly produced a final package")

    @contextmanager
    def assert_source_untouched(self, source_path: Path):
        accesses: list[str] = []
        original_builtin_open = builtins.open
        original_io_open = io.open
        original_os_open = os.open
        original_os_stat = os.stat
        original_os_lstat = os.lstat
        original_os_access = os.access
        original_open = Path.open
        original_read_bytes = Path.read_bytes
        original_resolve = Path.resolve
        original_stat = Path.stat
        original_lstat = Path.lstat
        original_is_zipfile = zipfile.is_zipfile

        def is_target(value) -> bool:
            return isinstance(value, (str, bytes, os.PathLike)) and Path(value) == source_path

        def guarded(name, original):
            def call(path, *args, **kwargs):
                if is_target(path):
                    accesses.append(name)
                    raise AssertionError(f"D0 accessed source through {name}")
                return original(path, *args, **kwargs)

            return call

        with (
            mock.patch("builtins.open", guarded("builtins.open", original_builtin_open)),
            mock.patch("io.open", guarded("io.open", original_io_open)),
            mock.patch("os.open", guarded("os.open", original_os_open)),
            mock.patch("os.stat", guarded("os.stat", original_os_stat)),
            mock.patch("os.lstat", guarded("os.lstat", original_os_lstat)),
            mock.patch("os.access", guarded("os.access", original_os_access)),
            mock.patch.object(Path, "open", guarded("Path.open", original_open)),
            mock.patch.object(
                Path,
                "read_bytes",
                guarded("Path.read_bytes", original_read_bytes),
            ),
            mock.patch.object(
                Path,
                "resolve",
                guarded("Path.resolve", original_resolve),
            ),
            mock.patch.object(Path, "stat", guarded("Path.stat", original_stat)),
            mock.patch.object(Path, "lstat", guarded("Path.lstat", original_lstat)),
            mock.patch(
                "zipfile.is_zipfile",
                guarded("zipfile.is_zipfile", original_is_zipfile),
            ),
        ):
            yield
        self.assertEqual(accesses, [])

    def test_source_access_guard_detects_every_forbidden_d0_route(self):
        with tempfile.TemporaryDirectory() as directory:
            source_path = Path(directory) / "guarded-source.mmd"
            routes = (
                ("builtins.open", lambda: builtins.open(source_path, "rb")),
                ("io.open", lambda: io.open(source_path, "rb")),
                ("os.open", lambda: os.open(source_path, os.O_RDONLY)),
                ("os.stat", lambda: os.stat(source_path)),
                ("os.lstat", lambda: os.lstat(source_path)),
                ("os.access", lambda: os.access(source_path, os.F_OK)),
                ("Path.open", lambda: source_path.open("rb")),
                ("Path.read_bytes", lambda: source_path.read_bytes()),
                ("Path.resolve", lambda: source_path.resolve()),
                ("Path.stat", lambda: source_path.stat()),
                ("Path.lstat", lambda: source_path.lstat()),
                ("zipfile.is_zipfile", lambda: zipfile.is_zipfile(source_path)),
            )
            for label, route in routes:
                with self.subTest(route=label):
                    with self.assertRaisesRegex(AssertionError, "D0 accessed source"):
                        with self.assert_source_untouched(source_path):
                            route()

    def test_byte_read_probe_accepts_prefix_rewind_and_rejects_partial_read(self):
        expected = b"prefix then rewind and complete read"
        complete_records: list[dict[str, object]] = []
        complete_stream = self.observed_binary_stream(
            io.BytesIO(expected),
            expected,
            complete_records,
        )

        self.assertEqual(complete_stream.read(6), expected[:6])
        self.assertEqual(complete_stream.seek(0), 0)
        self.assertEqual(complete_stream.read(), expected)
        self.assert_complete_read_passes(
            complete_records,
            expected,
            minimum=1,
            label="prefix plus rewind probe self-test",
        )

        partial_records: list[dict[str, object]] = []
        partial_stream = self.observed_binary_stream(
            io.BytesIO(expected),
            expected,
            partial_records,
        )
        self.assertEqual(partial_stream.read(6), expected[:6])
        with self.assertRaisesRegex(AssertionError, "was not fully read through EOF"):
            self.assert_complete_read_passes(
                partial_records,
                expected,
                minimum=1,
                label="partial-read probe self-test",
            )

    @contextmanager
    def assert_no_staging_writes(self, root: Path):
        before = {
            path.relative_to(root).as_posix()
            for path in root.rglob("*")
        }
        real_builtin_open = builtins.open
        real_io_open = io.open
        real_os_open = os.open
        real_mkdir = os.mkdir
        real_makedirs = os.makedirs
        real_rename = os.rename
        real_replace = os.replace

        def is_path(value) -> bool:
            return isinstance(value, (str, bytes, os.PathLike))

        def guarded_stream_open(original):
            def call(path, *args, **kwargs):
                mode = args[0] if args else kwargs.get("mode", "r")
                if is_path(path) and any(token in mode for token in "wax+"):
                    raise AssertionError("B1-C attempted a temp/output stream write")
                return original(path, *args, **kwargs)

            return call

        def guarded_os_open(path, flags, *args, **kwargs):
            write_flags = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND
            if is_path(path) and flags & write_flags:
                raise AssertionError("B1-C attempted a temp/output os.open write")
            return real_os_open(path, flags, *args, **kwargs)

        def guarded_create(original):
            def call(path, *args, **kwargs):
                if is_path(path):
                    raise AssertionError("B1-C attempted temp/output directory creation")
                return original(path, *args, **kwargs)

            return call

        def guarded_move(original):
            def call(source, destination, *args, **kwargs):
                if is_path(source) or is_path(destination):
                    raise AssertionError("B1-C attempted temp/output rename publication")
                return original(source, destination, *args, **kwargs)

            return call

        with (
            mock.patch("builtins.open", new=guarded_stream_open(real_builtin_open)),
            mock.patch("io.open", new=guarded_stream_open(real_io_open)),
            mock.patch("os.open", new=guarded_os_open),
            mock.patch("os.mkdir", new=guarded_create(real_mkdir)),
            mock.patch("os.makedirs", new=guarded_create(real_makedirs)),
            mock.patch("os.rename", new=guarded_move(real_rename)),
            mock.patch("os.replace", new=guarded_move(real_replace)),
        ):
            try:
                yield
            finally:
                after = {
                    path.relative_to(root).as_posix()
                    for path in root.rglob("*")
                }
                self.assertEqual(
                    after,
                    before,
                    "B1-C left a temporary or output filesystem change",
                )

    def test_staging_write_guard_detects_raw_temp_file_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            temp_target = root / ".adapted.tmp"
            with self.assertRaisesRegex(AssertionError, "temp/output stream write"):
                with self.assert_no_staging_writes(root):
                    builtins.open(temp_target, "wb")

    def test_missing_selection_manifest_stops_before_source_access(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "source-must-not-be-touched.mmd"
            output_dir = root / "data" / "staging" / "adapted"

            with self.assert_source_untouched(source_path):
                with self.assertRaises(InputMissingError):
                    self.invoke_adapter(root, root / "missing-selection.json", source_path)

            self.assertFalse(source_path.exists())
            self.assertFalse(output_dir.exists())

    def test_invalid_d0_manifest_stops_before_source_access(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            selection_manifest_path = root / "selection.json"
            selection_manifest_path.write_bytes(b"[]")
            source_path = root / "source-must-not-be-touched.mmd"

            with self.assert_source_untouched(source_path):
                self.assert_blocked_issue(
                    root,
                    selection_manifest_path,
                    source_path,
                    code="source_contract_mismatch",
                    field="$",
                    reason="non_object",
                )

            self.assertFalse(source_path.exists())
            self.assertFalse((root / "data" / "staging" / "adapted").exists())

    def test_missing_and_nonregular_sources_use_input_exceptions(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for label, make_source, expected_exception in (
                ("missing", lambda path: None, InputMissingError),
                ("directory", lambda path: path.mkdir(), InputFormatError),
            ):
                with self.subTest(source=label):
                    source_path = root / label / "source.mmd"
                    source_path.parent.mkdir(parents=True)
                    make_source(source_path)
                    selection_manifest_path = self.write_selection_manifest(
                        source_path.parent,
                        source_path,
                        source_kind="mmd",
                        source_sha256=HEX_ZERO,
                    )
                    with self.assertRaises(expected_exception):
                        self.invoke_adapter(root, selection_manifest_path, source_path)
                    self.assertFalse((root / "data" / "staging" / "adapted").exists())

    def test_unreadable_source_uses_input_format_exception(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_plain_source(root)
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd",
            )
            real_builtin_open = builtins.open
            real_io_open = io.open
            real_os_open = os.open

            def deny_exact_source(original):
                def call(target, *args, **kwargs):
                    if isinstance(target, (str, bytes, os.PathLike)) and Path(target) == source_path:
                        raise PermissionError("synthetic unreadable source")
                    return original(target, *args, **kwargs)

                return call

            with (
                mock.patch("builtins.open", new=deny_exact_source(real_builtin_open)),
                mock.patch("io.open", new=deny_exact_source(real_io_open)),
                mock.patch("os.open", new=deny_exact_source(real_os_open)),
                self.assertRaises(InputFormatError),
            ):
                self.invoke_adapter(root, selection_manifest_path, source_path)

            self.assertFalse((root / "data" / "staging" / "adapted").exists())

    def test_zip_directory_entry_is_allowed_for_inventory_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_entries(
                root,
                [
                    ("images/", b"", stat.S_IFDIR | 0o755),
                    _PRIMARY,
                ],
            )
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
            )
            opened_members: list[str] = []
            real_member_open = zipfile.ZipFile.open

            def observed_member_open(archive, member, *args, **kwargs):
                name = member.filename if isinstance(member, zipfile.ZipInfo) else member
                opened_members.append(name)
                return real_member_open(archive, member, *args, **kwargs)

            with (
                mock.patch.object(zipfile.ZipFile, "open", new=observed_member_open),
                self.assert_no_staging_writes(root),
            ):
                downstream_stop = self.reach_post_archive_boundary(
                    root,
                    selection_manifest_path,
                    source_path,
                )

            if "primary.mmd" not in opened_members and downstream_stop is not None:
                self.fail(f"adapter behavior RED: {downstream_stop}")
            self.assertNotIn("images/", opened_members)
            self.assertGreaterEqual(opened_members.count("primary.mmd"), 2)

    def test_zip_directory_with_unspecified_unix_kind_is_inventory_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_entries(
                root,
                [("primary.mmd", b"source\n", _REGULAR), ("images/", b"", 0)],
            )
            with zipfile.ZipFile(source_path) as archive:
                info = archive.getinfo("images/")
                self.assertEqual(info.create_system, 3)
                self.assertEqual(stat.S_IFMT(info.external_attr >> 16), 0)
                self.assertTrue(info.is_dir())
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
            )
            opened_members: list[str] = []
            real_member_open = zipfile.ZipFile.open

            def observed_member_open(archive, member, *args, **kwargs):
                name = member.filename if isinstance(member, zipfile.ZipInfo) else member
                opened_members.append(name)
                return real_member_open(archive, member, *args, **kwargs)

            with mock.patch.object(zipfile.ZipFile, "open", new=observed_member_open):
                package = self.invoke_adapter(
                    root,
                    selection_manifest_path,
                    source_path,
                )

            self.assertEqual(
                package.package_root,
                root / "data" / "staging" / "adapted",
            )
            self.assertNotIn("images/", opened_members)
            self.assertGreaterEqual(opened_members.count("primary.mmd"), 2)
            self.assertFalse((package.package_root / "images").exists())

    def test_actual_source_kind_uses_the_exact_six_row_decision_matrix(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            cases = []

            zip_match = self.write_zip_source(
                root,
                name="zip-match.bin",
                members={"primary.mmd": b"\xff"},
            )
            cases.append(
                (
                    "valid ZIP declared mmd_zip continues to inventory",
                    zip_match,
                    "mmd_zip",
                    "primary.mmd",
                    True,
                    None,
                )
            )

            zip_mismatch = self.write_zip_source(
                root,
                name="zip-disguised-as.mmd",
                members={"zip-disguised-as.mmd": b"source\n"},
            )
            cases.append(
                (
                    "valid ZIP declared mmd",
                    zip_mismatch,
                    "mmd",
                    zip_mismatch.name,
                    False,
                    (
                        "source_contract_mismatch",
                        "$.source_kind",
                        "declared_source_kind_mismatch",
                        {
                            "actual": "mmd_zip",
                            "expected": "mmd",
                            "reason": "declared_source_kind_mismatch",
                        },
                    ),
                )
            )

            plain_match = self.write_plain_source(
                root, name="plain-match.mmd", content=b"\xff"
            )
            cases.append(
                (
                    "plain bytes declared mmd continue to strict decode",
                    plain_match,
                    "mmd",
                    plain_match.name,
                    False,
                    None,
                )
            )

            plain_mismatch = self.write_plain_source(
                root, name="plain-mismatch.bin", content=b"plain MMD source\n"
            )
            cases.append(
                (
                    "plain bytes declared mmd_zip",
                    plain_mismatch,
                    "mmd_zip",
                    "primary.mmd",
                    False,
                    (
                        "source_contract_mismatch",
                        "$.source_kind",
                        "declared_source_kind_mismatch",
                        {
                            "actual": "mmd",
                            "expected": "mmd_zip",
                            "reason": "declared_source_kind_mismatch",
                        },
                    ),
                )
            )

            false_zip = self.write_plain_source(
                root, name="false-zip.bin", content=b"PK-not-a-valid-zip"
            )
            cases.append(
                (
                    "false ZIP probe with PK prefix",
                    false_zip,
                    "mmd_zip",
                    "primary.mmd",
                    False,
                    (
                        "archive_integrity_invalid",
                        "archive",
                        "zip_structure",
                        {
                            "actual": None,
                            "limit": None,
                            "member": None,
                            "reason": "zip_structure",
                        },
                    ),
                )
            )

            pdf = self.write_plain_source(
                root, name="pdf-disguised-as.mmd", content=b"%PDF-not-supported"
            )
            cases.append(
                (
                    "exact PDF prefix",
                    pdf,
                    "mmd",
                    pdf.name,
                    False,
                    (
                        "unsupported_source_format",
                        "source_kind",
                        "top_level_format",
                        {
                            "actual": "pdf",
                            "expected": ["mmd", "mmd_zip"],
                            "reason": "top_level_format",
                        },
                    ),
                )
            )

            for index, (
                label,
                source_path,
                source_kind,
                primary_member,
                expect_zip_member_stream,
                expected,
            ) in enumerate(cases):
                with self.subTest(row=label):
                    case_root = root / f"case-{index}"
                    case_root.mkdir()
                    selection_manifest_path = self.write_selection_manifest(
                        case_root,
                        source_path,
                        source_kind=source_kind,
                        primary_member=primary_member,
                    )
                    if expected is None:
                        self.assert_reaches_downstream_boundary(
                            root,
                            selection_manifest_path,
                            source_path,
                            expect_zip_member_stream=expect_zip_member_stream,
                            expected_plain_bytes=(
                                b"\xff" if not expect_zip_member_stream else None
                            ),
                        )
                    else:
                        self.assert_blocked_issue(
                            root,
                            selection_manifest_path,
                            source_path,
                            code=expected[0],
                            field=expected[1],
                            reason=expected[2],
                            expected_evidence=expected[3] if len(expected) == 4 else None,
                        )

    def test_source_digest_mismatch_is_an_independent_d1_blocker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_bytes = b"plain MMD source bytes for exact D1 digest\n"
            source_path = self.write_plain_source(root, content=source_bytes)
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd",
                source_sha256=HEX_ZERO,
            )

            with self.observe_exact_file_reads(
                source_path,
                source_bytes,
            ) as source_read_passes:
                self.assert_blocked_issue(
                    root,
                    selection_manifest_path,
                    source_path,
                    code="source_contract_mismatch",
                    field="$.source_sha256",
                    reason="source_digest_mismatch",
                    expected_evidence={
                        "actual": hashlib.sha256(source_bytes).hexdigest(),
                        "expected": HEX_ZERO,
                        "reason": "source_digest_mismatch",
                    },
                )
            self.assert_complete_read_passes(
                source_read_passes,
                source_bytes,
                minimum=1,
                label="D1 plain source kind/hash bytes before digest blocker",
            )

    def test_d1_blocker_prevents_zip_member_content_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_source(
                root,
                name="source.mmd",
                members={"source.mmd": b"member content must not be read\n"},
            )
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd",
                primary_member=source_path.name,
            )

            with mock.patch.object(zipfile.ZipFile, "open") as member_open, mock.patch.object(
                zipfile.ZipFile, "read"
            ) as member_read:
                self.assert_blocked_issue(
                    root,
                    selection_manifest_path,
                    source_path,
                    code="source_contract_mismatch",
                    field="$.source_kind",
                    reason="declared_source_kind_mismatch",
                    expected_evidence={
                        "actual": "mmd_zip",
                        "expected": "mmd",
                        "reason": "declared_source_kind_mismatch",
                    },
                )

            member_open.assert_not_called()
            member_read.assert_not_called()

    def test_encrypted_member_is_rejected_during_metadata_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_source(root)
            self.patch_first_zip_entry_metadata(source_path, flag_bits_or=0x1)

            self.assert_archive_integrity_reason(
                root,
                source_path,
                reason="encrypted",
            )

    def test_unsupported_compression_is_rejected_during_metadata_preflight(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_source(root)
            self.patch_first_zip_entry_metadata(source_path, compression=99)

            self.assert_archive_integrity_reason(
                root,
                source_path,
                reason="compression",
            )

    def test_ignored_os_metadata_with_unsafe_path_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            member = "__MACOSX/../escape"
            source_path = self.write_zip_entries(
                root,
                [_PRIMARY, (member, b"metadata", _REGULAR)],
            )
            self.assert_archive_member_reason(
                root,
                source_path,
                reason="traversal",
                member_names=(member,),
            )

    def test_ignored_os_metadata_with_unsafe_type_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            member = "__MACOSX/._link"
            source_path = self.write_zip_entries(
                root,
                [_PRIMARY, (member, b"target", stat.S_IFLNK | 0o777)],
            )
            self.assert_archive_member_reason(
                root,
                source_path,
                reason="symlink",
                member_names=(member,),
            )

    def test_ignored_os_metadata_with_encryption_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            member = "__MACOSX/._metadata"
            source_path = self.write_zip_entries(
                root,
                [(member, b"metadata", _REGULAR), _PRIMARY],
            )
            self.patch_first_zip_entry_metadata(source_path, flag_bits_or=0x1)
            self.assert_archive_integrity_reason(
                root,
                source_path,
                reason="encrypted",
                member=member,
            )

    def test_ignored_os_metadata_with_unsupported_compression_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            member = "__MACOSX/._metadata"
            source_path = self.write_zip_entries(
                root,
                [(member, b"metadata", _REGULAR), _PRIMARY],
            )
            self.patch_first_zip_entry_metadata(source_path, compression=99)
            self.assert_archive_integrity_reason(
                root,
                source_path,
                reason="compression",
                member=member,
            )

    def test_missing_selected_primary_member_stops_before_d2(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_source(
                root,
                members={"images/unselected.jpg": b"image"},
            )
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
            )

            with mock.patch.object(zipfile.ZipFile, "open") as member_open:
                self.assert_selected_member_missing(
                    root,
                    selection_manifest_path,
                    source_path,
                    field="primary_member",
                    member="primary.mmd",
                )
            member_open.assert_not_called()

    def test_missing_selected_answer_member_stops_before_d2(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_source(root)
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
                answer_member="answer.mmd",
            )

            with mock.patch.object(zipfile.ZipFile, "open") as member_open:
                self.assert_selected_member_missing(
                    root,
                    selection_manifest_path,
                    source_path,
                    field="answer_member",
                    member="answer.mmd",
                )
            member_open.assert_not_called()

    def test_metadata_safety_blocker_stops_all_member_reads(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_entries(
                root,
                [_PRIMARY, ("images/.hidden.jpg", b"image", _REGULAR)],
            )

            with mock.patch.object(zipfile.ZipFile, "open") as member_open, mock.patch.object(
                zipfile.ZipFile, "read"
            ) as member_read:
                self.assert_archive_member_reason(
                    root,
                    source_path,
                    reason="hidden",
                    member_names=("images/.hidden.jpg",),
                )

            member_open.assert_not_called()
            member_read.assert_not_called()

    def test_stored_member_crc_corruption_is_rejected_in_d2(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_entries(
                root,
                [("primary.mmd", b"source bytes", _REGULAR)],
            )
            self.corrupt_first_zip_member_payload(source_path, replace_all=False)

            self.assert_archive_integrity_reason(
                root,
                source_path,
                reason="crc",
                member="primary.mmd",
            )

    def test_deflated_member_decompression_failure_is_rejected_in_d2(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_bytes = hashlib.shake_256(
                b"task9b-d2-decompression-fixture"
            ).digest(4096)
            source_path = self.write_zip_source(
                root,
                members={"primary.mmd": source_bytes},
            )
            with zipfile.ZipFile(source_path) as archive:
                info = archive.getinfo("primary.mmd")
                self.assertEqual(info.compress_type, zipfile.ZIP_DEFLATED)
                self.assertLessEqual(
                    info.file_size / max(info.compress_size, 1),
                    100,
                )
            self.corrupt_first_zip_member_payload(source_path, replace_all=True)

            self.assert_archive_integrity_reason(
                root,
                source_path,
                reason="decompression",
            )

    def test_zip_processing_never_extracts_members_to_the_filesystem(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_source(
                root,
                members={"primary.mmd": b"\xff"},
            )
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
            )

            with mock.patch.object(
                zipfile.ZipFile,
                "extractall",
                side_effect=AssertionError("extractall() is forbidden"),
            ) as extract_all, mock.patch.object(
                zipfile.ZipFile,
                "extract",
                side_effect=AssertionError("extract-first processing is forbidden"),
            ) as extract_one, self.assert_no_staging_writes(root):
                self.assert_reaches_downstream_boundary(
                    root,
                    selection_manifest_path,
                    source_path,
                    expect_zip_member_stream=True,
                )

            extract_all.assert_not_called()
            extract_one.assert_not_called()

    def test_ignored_os_metadata_is_crc_streamed_before_it_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_entries(
                root,
                [
                    (".DS_Store", b"metadata bytes", _REGULAR),
                    _PRIMARY,
                ],
            )
            self.corrupt_first_zip_member_payload(source_path, replace_all=False)

            self.assert_archive_integrity_reason(
                root,
                source_path,
                reason="crc",
                member=".DS_Store",
            )

    def test_unselected_image_is_crc_streamed_before_it_is_ignored(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_entries(
                root,
                [
                    ("images/unselected.jpg", b"unselected image", _REGULAR),
                    _PRIMARY,
                ],
            )
            self.corrupt_first_zip_member_payload(source_path, replace_all=False)

            self.assert_archive_integrity_reason(
                root,
                source_path,
                reason="crc",
                member="images/unselected.jpg",
            )

    def test_safe_metadata_and_unselected_images_are_streamed_but_not_staged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            expected_members = {
                "primary.mmd": b"\xff",
                "__MACOSX/._metadata": b"metadata",
                ".DS_Store": b"metadata",
                "images/._resource.jpg": b"metadata",
                "images/selected.jpg": b"selected-image",
                "images/unselected.jpg": b"unselected",
            }
            source_path = self.write_zip_entries(
                root,
                [
                    (member, content, _REGULAR)
                    for member, content in expected_members.items()
                ],
            )
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
                selections=[self.minimal_selection("images/selected.jpg")],
            )

            member_read_passes: dict[str, list[dict[str, object]]] = {
                member: [] for member in expected_members
            }
            real_member_open = zipfile.ZipFile.open

            def observed_member_open(archive, member, *args, **kwargs):
                name = member.filename if isinstance(member, zipfile.ZipInfo) else member
                stream = real_member_open(archive, member, *args, **kwargs)
                self.assertIn(name, expected_members)
                return self.observed_binary_stream(
                    stream,
                    expected_members[name],
                    member_read_passes[name],
                )

            with mock.patch.object(
                zipfile.ZipFile,
                "open",
                new=observed_member_open,
            ):
                downstream_stop = self.reach_post_archive_boundary(
                    root,
                    selection_manifest_path,
                    source_path,
                )

            for member in expected_members:
                if not member_read_passes[member] and downstream_stop is not None:
                    self.fail(f"adapter behavior RED: {downstream_stop}")
                self.assert_complete_read_passes(
                    member_read_passes[member],
                    expected_members[member],
                    minimum=1,
                    label=f"D2 regular member {member}",
                )

            for member in (
                "__MACOSX/._metadata",
                ".DS_Store",
                "images/._resource.jpg",
                "images/unselected.jpg",
            ):
                self.assertEqual(
                    len(member_read_passes[member]),
                    1,
                    f"{member} must have one complete D2 pass and no B1-C pass",
                )
            for member in ("primary.mmd", "images/selected.jpg"):
                self.assert_complete_read_passes(
                    member_read_passes[member],
                    expected_members[member],
                    minimum=2,
                    label=f"D2 plus B1-C selected member {member}",
                )
            self.assertFalse((root / "data" / "staging" / "adapted").exists())

    def test_plain_mmd_reads_only_explicit_adjacent_images_without_recursive_discovery(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_plain_source(root, content=b"\xff")
            image_root = root / "images"
            image_root.mkdir()
            selected = image_root / "selected.jpg"
            selected_bytes = b"selected-adjacent-image-bytes"
            selected.write_bytes(selected_bytes)
            nested = image_root / "nested" / "unselected.jpg"
            nested.parent.mkdir()
            nested.write_bytes(b"must not be discovered")
            unselected = image_root / "unselected.jpg"
            unselected.write_bytes(b"must not be discovered")
            second_mmd = root / "second.mmd"
            second_mmd.write_bytes(b"must not be discovered")
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd",
                selections=[self.minimal_selection("images/selected.jpg")],
            )

            selected_read_passes: list[dict[str, object]] = []
            forbidden = {nested, unselected, second_mmd}
            real_builtin_open = builtins.open
            real_io_open = io.open
            real_os_open = os.open
            real_os_read = os.read
            real_os_lseek = os.lseek
            real_os_close = os.close
            real_os_stat = os.stat
            real_os_lstat = os.lstat
            real_os_access = os.access
            real_scandir = os.scandir
            real_listdir = os.listdir
            real_iterdir = Path.iterdir
            real_glob = Path.glob
            real_rglob = Path.rglob
            real_resolve = Path.resolve
            selected_fd_records: dict[int, dict[str, object]] = {}

            def observe_stream_or_reject(original):
                def call(target, *args, **kwargs):
                    if isinstance(target, (str, bytes, os.PathLike)):
                        path = Path(target)
                        if path in forbidden:
                            raise AssertionError(f"unexpected adjacent-resource access: {path.name}")
                    stream = original(target, *args, **kwargs)
                    if isinstance(target, (str, bytes, os.PathLike)):
                        path = Path(target)
                        if path == selected:
                            return self.observed_binary_stream(
                                stream,
                                selected_bytes,
                                selected_read_passes,
                            )
                    return stream

                return call

            def reject_metadata_access(original):
                def call(target, *args, **kwargs):
                    if isinstance(target, (str, bytes, os.PathLike)) and Path(target) in forbidden:
                        raise AssertionError(
                            f"unexpected adjacent-resource access: {Path(target).name}"
                        )
                    return original(target, *args, **kwargs)

                return call

            def observed_os_open(target, flags, *args, **kwargs):
                if isinstance(target, (str, bytes, os.PathLike)) and Path(target) in forbidden:
                    raise AssertionError(
                        f"unexpected adjacent-resource access: {Path(target).name}"
                    )
                descriptor = real_os_open(target, flags, *args, **kwargs)
                if isinstance(target, (str, bytes, os.PathLike)) and Path(target) == selected:
                    record: dict[str, object] = {
                        "intervals": [],
                        "content_matches": True,
                        "eof": False,
                        "read_calls": 0,
                    }
                    selected_read_passes.append(record)
                    selected_fd_records[descriptor] = record
                return descriptor

            def observed_os_read(descriptor, size):
                record = selected_fd_records.get(descriptor)
                start = (
                    real_os_lseek(descriptor, 0, os.SEEK_CUR)
                    if record is not None
                    else None
                )
                value = real_os_read(descriptor, size)
                if record is not None:
                    assert start is not None
                    _observe_bytes(
                        record,
                        selected_bytes,
                        value,
                        start=start,
                        end=real_os_lseek(descriptor, 0, os.SEEK_CUR),
                    )
                return value

            def observed_os_close(descriptor):
                selected_fd_records.pop(descriptor, None)
                return real_os_close(descriptor)

            def reject_enumeration(original):
                def call(target, *args, **kwargs):
                    if isinstance(target, (str, bytes, os.PathLike)) and Path(target) in {
                        root,
                        image_root,
                        nested.parent,
                    }:
                        raise AssertionError("plain-MMD resource discovery is forbidden")
                    return original(target, *args, **kwargs)

                return call

            with (
                mock.patch("builtins.open", new=observe_stream_or_reject(real_builtin_open)),
                mock.patch("io.open", new=observe_stream_or_reject(real_io_open)),
                mock.patch("os.open", new=observed_os_open),
                mock.patch("os.read", new=observed_os_read),
                mock.patch("os.close", new=observed_os_close),
                mock.patch("os.stat", new=reject_metadata_access(real_os_stat)),
                mock.patch("os.lstat", new=reject_metadata_access(real_os_lstat)),
                mock.patch("os.access", new=reject_metadata_access(real_os_access)),
                mock.patch("os.scandir", new=reject_enumeration(real_scandir)),
                mock.patch("os.listdir", new=reject_enumeration(real_listdir)),
                mock.patch.object(Path, "iterdir", new=reject_enumeration(real_iterdir)),
                mock.patch.object(Path, "glob", new=reject_enumeration(real_glob)),
                mock.patch.object(Path, "rglob", new=reject_enumeration(real_rglob)),
                mock.patch.object(Path, "resolve", new=reject_metadata_access(real_resolve)),
            ):
                downstream_stop = self.reach_post_archive_boundary(
                    root,
                    selection_manifest_path,
                    source_path,
                )

            if not selected_read_passes and downstream_stop is not None:
                self.fail(f"adapter behavior RED: {downstream_stop}")
            self.assert_complete_read_passes(
                selected_read_passes,
                selected_bytes,
                minimum=1,
                label="B1-C explicitly selected adjacent image",
            )
            self.assertFalse((root / "data" / "staging" / "adapted").exists())

    def test_d1_emits_all_independent_member_issues_then_stops_before_d2(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_entries(
                root,
                [
                    _PRIMARY,
                    ("images/.hidden.jpg", b"hidden", _REGULAR),
                    ("images/executable.jpg", b"executable", stat.S_IFREG | 0o755),
                ],
            )
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
            )

            with mock.patch.object(zipfile.ZipFile, "open") as member_open:
                issues = self.capture_blocked_issues(
                    root,
                    selection_manifest_path,
                    source_path,
                )

            self.assertEqual(len(issues), 2)
            expected_evidence = tuple(
                sorted(
                    json.dumps(
                        {
                            "member_name_sha256": hashlib.sha256(
                                member.encode("utf-8")
                            ).hexdigest(),
                            "reason": reason,
                        },
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    )
                    for member, reason in (
                        ("images/.hidden.jpg", "hidden"),
                        ("images/executable.jpg", "executable"),
                    )
                )
            )
            self.assertEqual(tuple(issue.evidence for issue in issues), expected_evidence)
            for issue in issues:
                self.assertEqual(
                    (
                        issue.code,
                        issue.severity,
                        issue.proposed_question_id,
                        issue.source_locator,
                        issue.field,
                    ),
                    ("archive_member_unsafe", "blocking", None, "", "archive_member"),
                )
                self.assertEqual(
                    issue.evidence,
                    json.dumps(
                        json.loads(issue.evidence),
                        ensure_ascii=False,
                        sort_keys=True,
                        separators=(",", ":"),
                    ),
                )
            member_open.assert_not_called()

    def test_raw_orig_filename_nul_is_rejected_and_controls_issue_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw_name = "images/nul\x00escape.jpg"
            source_path = self.write_zip_entries(
                root,
                [_PRIMARY, ("images/nulXescape.jpg", b"image", _REGULAR)],
            )
            self.patch_zip_member_name(
                source_path,
                original="images/nulXescape.jpg",
                replacement=raw_name,
            )
            with zipfile.ZipFile(source_path) as archive:
                info = archive.infolist()[1]
                self.assertEqual(info.orig_filename, raw_name)
                self.assertEqual(info.filename, "images/nul")

            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
            )
            issues = self.capture_blocked_issues(
                root,
                selection_manifest_path,
                source_path,
            )

            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0].code, "archive_member_unsafe")
            self.assertEqual(
                json.loads(issues[0].evidence),
                {
                    "member_name_sha256": hashlib.sha256(
                        raw_name.encode("utf-8")
                    ).hexdigest(),
                    "reason": "normalized_escape",
                },
            )

    def test_d0_drive_relative_primary_member_is_a_structured_blocker(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_source(root)
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
            )
            payload = json.loads(selection_manifest_path.read_text(encoding="utf-8"))
            payload["primary_member"] = "C:relative.mmd"
            selection_manifest_path.write_text(
                json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )

            with self.assert_source_untouched(source_path):
                issues = self.capture_blocked_issues(
                    root,
                    selection_manifest_path,
                    source_path,
                )

            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0].code, "source_contract_mismatch")
            self.assertEqual(issues[0].field, "$.primary_member")
            self.assertEqual(
                json.loads(issues[0].evidence),
                {
                    "actual": hashlib.sha256(b"C:relative.mmd").hexdigest(),
                    "expected": "canonical_nfc_posix_mmd_member",
                    "reason": "invalid_value",
                },
            )

    def test_d0_drive_relative_nonpath_scalar_and_unknown_key_stay_literal(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_source(root)
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
            )
            payload = json.loads(selection_manifest_path.read_text(encoding="utf-8"))
            payload["source_kind"] = "C:relative"
            payload["C:key"] = "present"
            selection_manifest_path.write_text(
                json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
                encoding="utf-8",
            )

            with self.assert_source_untouched(source_path):
                issues = self.capture_blocked_issues(
                    root,
                    selection_manifest_path,
                    source_path,
                )

            self.assertEqual(len(issues), 2)
            by_field = {issue.field: json.loads(issue.evidence) for issue in issues}
            self.assertEqual(
                by_field,
                {
                    '$["C:key"]': {
                        "actual": "present",
                        "expected": "absent",
                        "reason": "extra_key",
                    },
                    "$.source_kind": {
                        "actual": "C:relative",
                        "expected": ["mmd", "mmd_zip"],
                        "reason": "invalid_value",
                    },
                },
            )

    def test_zip_drive_relative_member_is_drive_or_unc(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_entries(
                root,
                [_PRIMARY, ("C:relative.jpg", b"image", _REGULAR)],
            )
            self.assert_archive_member_reason(
                root,
                source_path,
                reason="drive_or_unc",
                member_names=("C:relative.jpg",),
            )

    def test_zip_backslash_unc_is_drive_or_unc_before_backslash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            member = "\\\\server\\share.jpg"
            source_path = self.write_zip_entries(
                root,
                [_PRIMARY, (member, b"image", _REGULAR)],
            )
            self.assert_archive_member_reason(
                root,
                source_path,
                reason="drive_or_unc",
                member_names=(member,),
            )

    def test_trailing_slash_does_not_mask_symlink_or_special_unix_type(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entries = (
                ("links/symlink/", b"", stat.S_IFLNK | 0o777, "symlink"),
                ("special/fifo/", b"", stat.S_IFIFO | 0o644, "special"),
            )
            source_path = self.write_zip_entries(
                root,
                [_PRIMARY] + [(name, content, mode) for name, content, mode, _ in entries],
            )
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
            )
            issues = self.capture_blocked_issues(
                root,
                selection_manifest_path,
                source_path,
            )

            expected = sorted(
                (
                    hashlib.sha256(name.encode("utf-8")).hexdigest(),
                    reason,
                )
                for name, _, _, reason in entries
            )
            observed = sorted(
                (
                    json.loads(issue.evidence)["member_name_sha256"],
                    json.loads(issue.evidence)["reason"],
                )
                for issue in issues
            )
            self.assertEqual(observed, expected)

    def test_directory_mode_without_trailing_slash_is_special_before_d2(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            member = "primary.mmd"
            source_path = self.write_zip_entries(
                root,
                [(member, b"must not reach D2", stat.S_IFDIR | 0o755)],
            )
            with zipfile.ZipFile(source_path) as archive:
                info = archive.getinfo(member)
                self.assertFalse(info.is_dir())
                self.assertTrue(stat.S_ISDIR(info.external_attr >> 16))
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member=member,
            )

            member_open_calls = []
            original_member_open = zipfile.ZipFile.open

            def observed_member_open(archive, *args, **kwargs):
                member_open_calls.append(args[0])
                return original_member_open(archive, *args, **kwargs)

            with mock.patch.object(
                zipfile.ZipFile,
                "open",
                new=observed_member_open,
            ):
                issues = self.capture_blocked_issues(
                    root,
                    selection_manifest_path,
                    source_path,
                )

            self.assertEqual(len(issues), 1)
            self.assertEqual(issues[0].code, "archive_member_unsafe")
            self.assertEqual(
                json.loads(issues[0].evidence),
                {
                    "member_name_sha256": hashlib.sha256(
                        member.encode("utf-8")
                    ).hexdigest(),
                    "reason": "special",
                },
            )
            self.assertEqual(member_open_calls, [])

    def test_directory_still_gets_encryption_compression_and_ratio_checks(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_entries(
                root,
                [_PRIMARY, ("metadata/", b"", stat.S_IFDIR | 0o755)],
            )
            self.patch_zip_entry_metadata(
                source_path,
                index=1,
                flag_bits_or=0x1,
                compression=99,
                compressed_size=1,
                uncompressed_size=101,
            )
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
            )
            issues = self.capture_blocked_issues(
                root,
                selection_manifest_path,
                source_path,
            )

            observed = {
                json.loads(issue.evidence)["reason"]: json.loads(issue.evidence)
                for issue in issues
            }
            self.assertEqual(set(observed), {"encrypted", "compression", "compression_ratio"})
            self.assertEqual(observed["encrypted"]["member"], "metadata/")
            self.assertEqual(observed["compression"]["member"], "metadata/")
            self.assertEqual(observed["compression_ratio"]["member"], "metadata/")
            self.assertEqual(observed["compression_ratio"]["actual"], 101.0)

    def test_hidden_executable_member_emits_both_independent_issues(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            member = "images/.run.jpg"
            source_path = self.write_zip_entries(
                root,
                [_PRIMARY, (member, b"image", stat.S_IFREG | 0o755)],
            )
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
            )
            issues = self.capture_blocked_issues(
                root,
                selection_manifest_path,
                source_path,
            )

            expected_hash = hashlib.sha256(member.encode("utf-8")).hexdigest()
            self.assertEqual(
                sorted(
                    (
                        json.loads(issue.evidence)["member_name_sha256"],
                        json.loads(issue.evidence)["reason"],
                    )
                    for issue in issues
                ),
                [(expected_hash, "executable"), (expected_hash, "hidden")],
            )

    def test_type_issue_does_not_mask_independent_metadata_issues(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            member = "images/link.jpg"
            source_path = self.write_zip_entries(
                root,
                [_PRIMARY, (member, b"target", stat.S_IFLNK | 0o777)],
            )
            self.patch_zip_entry_metadata(
                source_path,
                index=1,
                flag_bits_or=0x1,
                compression=99,
                compressed_size=1,
                uncompressed_size=101,
            )
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
            )
            issues = self.capture_blocked_issues(
                root,
                selection_manifest_path,
                source_path,
            )

            observed = [
                (issue.code, json.loads(issue.evidence)["reason"])
                for issue in issues
            ]
            self.assertEqual(
                sorted(observed),
                sorted(
                    (
                        ("archive_member_unsafe", "symlink"),
                        ("archive_integrity_invalid", "encrypted"),
                        ("archive_integrity_invalid", "compression"),
                        ("archive_integrity_invalid", "compression_ratio"),
                    )
                ),
            )

    def test_plain_adjacent_resource_symlink_escape_is_a_d1_normalized_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outside = root / "outside.jpg"
            outside.write_bytes(b"outside")
            source_path = self.write_plain_source(root)
            image_path = root / "images" / "selected.jpg"
            image_path.parent.mkdir()
            image_path.symlink_to(outside)
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd",
                selections=[self.minimal_selection("images/selected.jpg")],
            )

            issues = self.capture_blocked_issues(
                root,
                selection_manifest_path,
                source_path,
            )
            self.assertIn(
                "normalized_escape",
                {json.loads(issue.evidence).get("reason") for issue in issues},
            )
            normalized_escape = [
                issue
                for issue in issues
                if json.loads(issue.evidence).get("reason") == "normalized_escape"
            ]
            self.assertTrue(normalized_escape)
            self.assertTrue(
                all(issue.code == "archive_member_unsafe" for issue in normalized_escape)
            )
            expected_evidence = {
                "member_name_sha256": hashlib.sha256(
                    b"images/selected.jpg"
                ).hexdigest(),
                "reason": "normalized_escape",
            }
            self.assertTrue(
                all(
                    (
                        issue.severity,
                        issue.proposed_question_id,
                        issue.source_locator,
                        issue.field,
                        json.loads(issue.evidence),
                    )
                    == (
                        "blocking",
                        None,
                        "",
                        "archive_member",
                        expected_evidence,
                    )
                    for issue in normalized_escape
                )
            )


_REGULAR = stat.S_IFREG | 0o644
_PRIMARY = ("primary.mmd", b"\xff", _REGULAR)

_MEMBER_SAFETY_CASES = {
    "absolute_path": ([ _PRIMARY, ("/escape.jpg", b"x", _REGULAR)], "absolute"),
    "backslash_path": ([ _PRIMARY, ("images\\escape.jpg", b"x", _REGULAR)], "backslash"),
    "drive_path": ([ _PRIMARY, ("C:/escape.jpg", b"x", _REGULAR)], "drive_or_unc"),
    "unc_path": ([ _PRIMARY, ("//server/share.jpg", b"x", _REGULAR)], "drive_or_unc"),
    "parent_traversal": ([ _PRIMARY, ("images/../escape.jpg", b"x", _REGULAR)], "traversal"),
    "dot_component": ([ _PRIMARY, ("images/./escape.jpg", b"x", _REGULAR)], "dot_or_empty_component"),
    "empty_component": ([ _PRIMARY, ("images//escape.jpg", b"x", _REGULAR)], "dot_or_empty_component"),
    "hidden_component": ([ _PRIMARY, ("images/.secret.jpg", b"x", _REGULAR)], "hidden"),
    "symlink": ([ _PRIMARY, ("images/link.jpg", b"target", stat.S_IFLNK | 0o777)], "symlink"),
    "character_device": ([ _PRIMARY, ("images/char-device.jpg", b"", stat.S_IFCHR | 0o644)], "special"),
    "block_device": ([ _PRIMARY, ("images/block-device.jpg", b"", stat.S_IFBLK | 0o644)], "special"),
    "fifo": ([ _PRIMARY, ("images/fifo.jpg", b"", stat.S_IFIFO | 0o644)], "special"),
    "socket": ([ _PRIMARY, ("images/socket.jpg", b"", stat.S_IFSOCK | 0o644)], "special"),
    "other_special": ([ _PRIMARY, ("images/whiteout.jpg", b"", stat.S_IFWHT | 0o644)], "special"),
    "executable": ([ _PRIMARY, ("images/run.jpg", b"x", stat.S_IFREG | 0o755)], "executable"),
    "nested_archive": ([ _PRIMARY, ("nested.ZIP", b"PK", _REGULAR)], "nested_archive"),
    "unselected_second_mmd": ([ _PRIMARY, ("second.mmd", b"x", _REGULAR)], "second_mmd"),
    "raw_duplicate": ([ _PRIMARY, ("images/a.jpg", b"a", _REGULAR), ("images/a.jpg", b"b", _REGULAR)], "duplicate"),
    "nfc_collision": ([ _PRIMARY, ("images/caf\u00e9.jpg", b"a", _REGULAR), ("images/cafe\u0301.jpg", b"b", _REGULAR)], "nfc_collision"),
    "casefold_collision": ([ _PRIMARY, ("images/A.jpg", b"a", _REGULAR), ("images/a.jpg", b"b", _REGULAR)], "casefold_collision"),
}


def _member_safety_test(entries, reason):
    def test(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_entries(root, entries)
            self.assert_archive_member_reason(
                root,
                source_path,
                reason=reason,
                member_names=tuple(entry[0] for entry in entries[1:]),
            )

    return test


def _raw_archive_limit_test(exceeds: bool):
    def test(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_entries(
                root,
                [("__MACOSX/metadata.bin", b"x", _REGULAR)],
            )
            self.prepend_zip_to_exact_size(source_path, 50 * MIB + int(exceeds))
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
            )
            self.assert_limit_boundary(
                root,
                selection_manifest_path,
                source_path,
                reason="archive_size",
                exceeds=exceeds,
                expected_actual=50 * MIB + int(exceeds),
                expected_limit=50 * MIB,
                expected_member=None,
            )

    return test


def _member_count_limit_test(exceeds: bool):
    def test(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            count = 256 + int(exceeds)
            entries = [
                (f"directories/d{index:03d}/", b"", stat.S_IFDIR | 0o755)
                for index in range(count)
            ]
            source_path = self.write_zip_entries(root, entries)
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
            )
            self.assert_limit_boundary(
                root,
                selection_manifest_path,
                source_path,
                reason="member_count",
                exceeds=exceeds,
                expected_actual=count,
                expected_limit=256,
                expected_member=None,
            )

    return test


def _single_member_size_limit_test(
    *,
    reason: str,
    member_name: str,
    limit_mib: int,
    selected_primary: bool,
):
    def factory(exceeds: bool):
        def test(self):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source_path = self.write_zip_entries(
                    root,
                    [(member_name, b"x", _REGULAR)],
                )
                declared_size = limit_mib * MIB + int(exceeds)
                safe_compressed_size = (declared_size + 99) // 100
                self.patch_zip_central_sizes(
                    source_path,
                    [(safe_compressed_size, declared_size)],
                )
                selection_manifest_path = self.write_selection_manifest(
                    root,
                    source_path,
                    source_kind="mmd_zip",
                    primary_member="primary.mmd",
                    answer_member="answer.mmd" if selected_primary else None,
                )
                self.assert_limit_boundary(
                    root,
                    selection_manifest_path,
                    source_path,
                    reason=reason,
                    exceeds=exceeds,
                    expected_actual=declared_size,
                    expected_limit=limit_mib * MIB,
                    expected_member=member_name,
                )

        return test

    return factory


def _total_uncompressed_limit_test(exceeds: bool):
    def test(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            entries = [
                (f"__MACOSX/metadata-{index}.bin", b"x", _REGULAR)
                for index in range(7)
            ]
            source_path = self.write_zip_entries(root, entries)
            uncompressed_sizes = [16 * MIB] * 6 + [4 * MIB + int(exceeds)]
            declared_sizes = [
                ((size + 99) // 100, size) for size in uncompressed_sizes
            ]
            self.patch_zip_central_sizes(source_path, declared_sizes)
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
            )
            self.assert_limit_boundary(
                root,
                selection_manifest_path,
                source_path,
                reason="total_uncompressed",
                exceeds=exceeds,
                expected_actual=100 * MIB + int(exceeds),
                expected_limit=100 * MIB,
                expected_member=None,
            )

    return test


def _compression_ratio_limit_test(exceeds: bool):
    def test(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_zip_entries(
                root,
                [("__MACOSX/metadata.bin", b"x", _REGULAR)],
            )
            self.patch_zip_central_sizes(
                source_path,
                [(1, 100 + int(exceeds))],
            )
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd_zip",
                primary_member="primary.mmd",
            )
            self.assert_limit_boundary(
                root,
                selection_manifest_path,
                source_path,
                reason="compression_ratio",
                exceeds=exceeds,
                expected_actual=100.0 + int(exceeds),
                expected_limit=100,
                expected_member="__MACOSX/metadata.bin",
            )

    return test


def _plain_mmd_size_limit_test(exceeds: bool):
    def test(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = root / "source.mmd"
            with source_path.open("wb") as stream:
                stream.truncate(10 * MIB + int(exceeds))
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd",
                source_sha256=HEX_ZERO,
            )
            self.assert_limit_boundary(
                root,
                selection_manifest_path,
                source_path,
                reason="mmd_size",
                exceeds=exceeds,
                expected_actual=10 * MIB + int(exceeds),
                expected_limit=10 * MIB,
                expected_member="source.mmd",
            )

    return test


def _plain_adjacent_image_size_limit_test(exceeds: bool):
    def test(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_plain_source(root)
            image_path = root / "images" / "selected.jpg"
            image_path.parent.mkdir()
            with image_path.open("wb") as stream:
                stream.truncate(20 * MIB + int(exceeds))
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd",
                source_sha256=HEX_ZERO,
                selections=[self.minimal_selection("images/selected.jpg")],
            )
            self.assert_limit_boundary(
                root,
                selection_manifest_path,
                source_path,
                reason="image_size",
                exceeds=exceeds,
                expected_actual=20 * MIB + int(exceeds),
                expected_limit=20 * MIB,
                expected_member="images/selected.jpg",
            )

    return test


def _plain_adjacent_total_size_limit_test(exceeds: bool):
    def test(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source_path = self.write_plain_source(root)
            image_root = root / "images"
            image_root.mkdir()
            image_sizes = [16 * MIB] * 6 + [4 * MIB + int(exceeds)]
            image_members = []
            for index, size in enumerate(image_sizes):
                member = f"images/selected-{index}.jpg"
                image_members.append(member)
                with (root / member).open("wb") as stream:
                    stream.truncate(size)
            selection = self.minimal_selection(image_members[0])
            selection["expected_image_members"] = image_members
            selection_manifest_path = self.write_selection_manifest(
                root,
                source_path,
                source_kind="mmd",
                source_sha256=HEX_ZERO,
                selections=[selection],
            )
            self.assert_limit_boundary(
                root,
                selection_manifest_path,
                source_path,
                reason="total_uncompressed",
                exceeds=exceeds,
                expected_actual=100 * MIB + int(exceeds),
                expected_limit=100 * MIB,
                expected_member=None,
            )

    return test


for _case_name, (_entries, _reason) in _MEMBER_SAFETY_CASES.items():
    setattr(
        MmdArchiveSafetyTests,
        f"test_archive_rejects_{_case_name}",
        _member_safety_test(_entries, _reason),
    )


for _label, _factory in {
    "raw_archive_50_mib": _raw_archive_limit_test,
    "member_count_256": _member_count_limit_test,
    "total_uncompressed_100_mib": _total_uncompressed_limit_test,
    "compression_ratio_100_to_1": _compression_ratio_limit_test,
    "plain_mmd_10_mib": _plain_mmd_size_limit_test,
    "plain_adjacent_image_20_mib": _plain_adjacent_image_size_limit_test,
    "plain_adjacent_images_total_100_mib": _plain_adjacent_total_size_limit_test,
}.items():
    setattr(
        MmdArchiveSafetyTests,
        f"test_limit_accepts_inclusive_{_label}",
        _factory(False),
    )
    setattr(
        MmdArchiveSafetyTests,
        f"test_limit_rejects_{_label}_plus_one",
        _factory(True),
    )


for _label, _reason, _member_name, _limit_mib, _selected_primary in (
    ("generic_member_20_mib", "member_size", "__MACOSX/metadata.bin", 20, False),
    ("mmd_member_10_mib", "mmd_size", "primary.mmd", 10, True),
    ("image_member_20_mib", "image_size", "images/unselected.jpg", 20, False),
):
    _factory = _single_member_size_limit_test(
        reason=_reason,
        member_name=_member_name,
        limit_mib=_limit_mib,
        selected_primary=_selected_primary,
    )
    setattr(
        MmdArchiveSafetyTests,
        f"test_limit_accepts_inclusive_{_label}",
        _factory(False),
    )
    setattr(
        MmdArchiveSafetyTests,
        f"test_limit_rejects_{_label}_plus_one",
        _factory(True),
    )


if __name__ == "__main__":
    unittest.main()
