"""Deterministic byte encoders for maintained export artifacts."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable, Mapping, Sequence


def canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def evidence_json_bytes(value: object) -> bytes:
    return (
        json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    ).encode("utf-8")


def csv_bytes(
    fieldnames: Sequence[str],
    rows: Iterable[Mapping[str, object]],
) -> bytes:
    handle = io.StringIO(newline="")
    writer = csv.DictWriter(
        handle,
        fieldnames=tuple(fieldnames),
        lineterminator="\r\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return handle.getvalue().encode("utf-8-sig")


def text_bytes(value: str) -> bytes:
    normalized = value.replace("\r\n", "\n").replace("\r", "\n")
    return (normalized.rstrip("\n") + "\n").encode("utf-8")
