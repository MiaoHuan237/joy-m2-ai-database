"""Independent read-only verifier for Task 11 V1.21 promotion trees."""

from __future__ import annotations

from contextlib import closing
from dataclasses import fields
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import re
import sqlite3

from joy_m2.config import PipelineConfig
from joy_m2.errors import InputFormatError, InputMissingError, PipelineError
from joy_m2.models import VerificationCheck, VerificationReport

from .v121_models import V121CandidateVerificationRequest
from .v121_promotion_models import V121PromotionContract, V121PromotionVerificationRequest
from .v121_verification import verify_v121_candidate


__all__ = ("verify_v121_promotion",)

BASELINE_SHA256 = "b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292"
BASELINE_RELEASE_DIGEST = "1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf"
BASELINE_SIZE = 9_768_960
BASELINE_MANIFEST_SHA256 = "19ac2e43ded74a3f3eaf75c184b5eb231c9f1b0b152f5914cd822a321b045098"
BASELINE_MANIFEST_SIZE = 6_643
CANDIDATE_DIGEST = "ecf624e3cb9fd8e7b1e0c664ddc5d51ef67f2d7f16f277c276be828eba32282c"
CANDIDATE_SHA256 = "6e27e5b5eff5a701b4671a3e12ee538eed985147d86c23edef1e9489f714a53c"
CANDIDATE_MANIFEST_SHA256 = "dc82e04639a4b54e24bbf7eceeb4ecec8a3751dfa7e8595f260b9d894d91fc83"
CANDIDATE_SIZE = 9_957_376
CANDIDATE_MANIFEST_SIZE = 6_849
CHECK_NAMES = (
    "release_directory", "promotion_contract", "candidate_verification",
    "candidate_binding", "manifest_contract", "filesystem_closure",
    "sha256sums_closure", "artifact_references", "rollback_contract",
    "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
    "sqlite_schema", "v120_preservation", "batch_ledger_closure",
    "promotion_projection", "formal_query", "count_closure",
    "provenance_closure", "deterministic_identity", "publication_boundary",
)
_ASCII_SPACE = re.compile(r"[ \t\r\n\f\v]+")
_SHA256 = re.compile(r"[0-9a-f]{64}")
_CONTRACT_VALUES = {
    "profile": "V1.21",
    "release_manifest_schema": "task11-v121-formal-manifest-v1",
    "formal_database_schema": "task11-v121-formal-v1",
    "promotion_identity_schema": "task11-v121-promotion-identity-v1",
    "rollback_schema": "task11-v121-formal-rollback-v1",
    "expected_user_version": 121,
    "database_filename": "Joy_M2_Complete_Question_DB_V1_21.sqlite3",
    "manifest_filename": "manifest.json",
    "sha256s_filename": "SHA256SUMS.txt",
    "rollback_filename": "rollback.json",
    "image_root": "images/sha256",
    "promoted_table": "task11_v121_promoted_questions_v1",
    "promotion_table": "task11_v121_promotion_v1",
    "formal_view": "formal_complete_questions_v121",
}

_PROMOTION_TABLE_SQL = """CREATE TABLE task11_v121_promotion_v1 (
    release_version TEXT PRIMARY KEY CHECK(release_version='V1.21'),
    formal_database_schema TEXT NOT NULL CHECK(formal_database_schema='task11-v121-formal-v1'),
    release_model TEXT NOT NULL CHECK(release_model='append-only-multi-batch-promotion'),
    release_status TEXT NOT NULL CHECK(release_status='published'),
    baseline_release_version TEXT NOT NULL CHECK(baseline_release_version='V1.20'),
    baseline_database_sha256 TEXT NOT NULL CHECK(baseline_database_sha256='b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292'),
    baseline_release_digest TEXT NOT NULL CHECK(baseline_release_digest='1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf'),
    baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count=543),
    candidate_digest TEXT NOT NULL CHECK(candidate_digest='ecf624e3cb9fd8e7b1e0c664ddc5d51ef67f2d7f16f277c276be828eba32282c'),
    candidate_database_sha256 TEXT NOT NULL CHECK(candidate_database_sha256='6e27e5b5eff5a701b4671a3e12ee538eed985147d86c23edef1e9489f714a53c'),
    candidate_database_size INTEGER NOT NULL CHECK(candidate_database_size=9957376),
    candidate_manifest_sha256 TEXT NOT NULL CHECK(candidate_manifest_sha256='dc82e04639a4b54e24bbf7eceeb4ecec8a3751dfa7e8595f260b9d894d91fc83'),
    candidate_manifest_size INTEGER NOT NULL CHECK(candidate_manifest_size=6849),
    accepted_batch_count INTEGER NOT NULL CHECK(accepted_batch_count=4),
    promoted_question_count INTEGER NOT NULL CHECK(promoted_question_count=48),
    formal_question_count INTEGER NOT NULL CHECK(formal_question_count=591)
)"""

_PROMOTED_TABLE_SQL = """CREATE TABLE task11_v121_promoted_questions_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal BETWEEN 1 AND 4),
    batch_id TEXT NOT NULL,
    batch_candidate_order INTEGER NOT NULL CHECK(batch_candidate_order>=0),
    formal_order INTEGER PRIMARY KEY CHECK(formal_order BETWEEN 544 AND 591),
    question_id TEXT NOT NULL UNIQUE,
    source_id TEXT NOT NULL,
    source_question_number TEXT NOT NULL,
    source_section TEXT NOT NULL,
    source_fragment_hash TEXT NOT NULL,
    normalized_text_sha256 TEXT NOT NULL,
    question_text_original TEXT NOT NULL,
    question_text_zh TEXT NOT NULL,
    translation_status TEXT NOT NULL CHECK(translation_status IN ('source_present','ai_proposed','verified','missing')),
    translation_evidence TEXT,
    solution_original TEXT NOT NULL,
    solution_verified TEXT NOT NULL,
    answer_status TEXT NOT NULL CHECK(answer_status IN ('source_provided','ai_solved_verified','missing_from_source')),
    explanation_text TEXT NOT NULL,
    explanation_status TEXT NOT NULL CHECK(explanation_status IN ('source_present','ai_proposed','verified','missing')),
    explanation_evidence TEXT,
    source_image_paths_json TEXT NOT NULL,
    source_image_sha256s_json TEXT NOT NULL,
    source_image_roles_json TEXT NOT NULL,
    primary_type TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    tag_status TEXT NOT NULL CHECK(tag_status IN ('source_provided','proposed','missing')),
    difficulty_level INTEGER CHECK(difficulty_level BETWEEN 1 AND 5 OR difficulty_level IS NULL),
    difficulty_status TEXT NOT NULL CHECK(difficulty_status IN ('source_provided','proposed','missing')),
    enrichment_status TEXT NOT NULL CHECK(enrichment_status IN ('complete','incomplete')),
    formal_image_paths_json TEXT NOT NULL,
    record_status TEXT NOT NULL CHECK(record_status='published'),
    selectable INTEGER NOT NULL CHECK(selectable=1),
    UNIQUE(batch_ordinal,batch_candidate_order),
    FOREIGN KEY(batch_ordinal,batch_id)
        REFERENCES task11_v121_batch_ledger_v1(batch_ordinal,batch_id)
)"""

_FORMAL_VIEW_SQL = """CREATE VIEW formal_complete_questions_v121 AS
SELECT * FROM formal_complete_questions_v120
UNION ALL
SELECT
    p.formal_order,
    p.question_id,
    'task11_v121_promoted' AS authority_kind,
    p.batch_id,
    p.batch_candidate_order AS candidate_order,
    p.source_id,
    p.source_question_number,
    p.source_section,
    p.source_fragment_hash,
    p.normalized_text_sha256,
    p.question_text_original,
    p.question_text_zh,
    CAST(NULL AS TEXT) AS question_text_zh_reviewed,
    p.translation_status,
    p.translation_evidence,
    p.solution_original,
    p.solution_verified,
    p.answer_status,
    p.explanation_text,
    p.explanation_status,
    p.explanation_evidence,
    p.source_image_paths_json,
    p.source_image_sha256s_json,
    p.source_image_roles_json,
    p.primary_type,
    p.tags_json,
    p.tag_status,
    p.difficulty_level,
    p.difficulty_status,
    p.enrichment_status,
    p.formal_image_paths_json,
    p.record_status,
    p.selectable
FROM task11_v121_promoted_questions_v1 AS p
ORDER BY formal_order"""

_METADATA_DELTA = {
    "release_version": "V1.21",
    "baseline_version": "V1.20",
    "baseline_sqlite_sha256": BASELINE_SHA256,
    "release_model": "append-only-multi-batch-promotion",
    "schema_version": "task11-v121-formal-v1",
    "formal_question_count": "591",
    "task11_baseline_release_digest": BASELINE_RELEASE_DIGEST,
    "task11_candidate_digest": CANDIDATE_DIGEST,
    "task11_candidate_sqlite_sha256": CANDIDATE_SHA256,
    "task11_candidate_manifest_sha256": CANDIDATE_MANIFEST_SHA256,
    "task11_accepted_batch_count": "4",
    "task11_promoted_questions": "48",
}


def _canonical_json_file_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8") + b"\n"


def _sha_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _normalize_sql(value: str) -> str:
    result = _ASCII_SPACE.sub(" ", value).strip(" ")
    return result[:-1].rstrip(" ") if result.endswith(";") else result


def _quoted(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _sqlite_value(value: object) -> object:
    if value is None or type(value) in {int, str}:
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if type(value) is bytes:
        return {"blob_hex": value.hex()}
    raise InputFormatError("SQLite contains an unsupported value")


def _sqlite_semantic_payload(path: Path, formal_view: str) -> dict[str, object]:
    uri = f"file:{path.resolve()}?mode=ro&immutable=1"
    with closing(sqlite3.connect(uri, uri=True)) as database:
        schema = [
            {
                "type": row[0], "name": row[1], "table_name": row[2],
                "sql": None if row[3] is None else _normalize_sql(row[3]),
            }
            for row in database.execute(
                "SELECT type,name,tbl_name,sql FROM sqlite_master "
                "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
            )
        ]
        tables = [
            row[0] for row in database.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        relations = []
        for name in tables + [formal_view]:
            info = tuple(database.execute(f"PRAGMA table_info({_quoted(name)})"))
            if not info:
                raise InputFormatError(f"SQLite relation is missing: {name}")
            columns = [row[1] for row in info]
            primary = [
                row[1] for row in sorted(
                    (row for row in info if row[5]), key=lambda row: row[5]
                )
            ]
            order_columns = ["formal_order"] if name == formal_view else primary or columns
            order = ",".join(_quoted(column) for column in order_columns)
            rows = [
                [_sqlite_value(item) for item in row]
                for row in database.execute(
                    f"SELECT * FROM {_quoted(name)} ORDER BY {order}"
                )
            ]
            relations.append({"name": name, "columns": columns, "rows": rows})
        user_version = database.execute("PRAGMA user_version").fetchone()[0]
    return {
        "schema_version": "task11-v121-sqlite-semantic-v1",
        "user_version": user_version,
        "schema_objects": schema,
        "relations": relations,
    }


def _reconstructs(value: object, expected: type) -> bool:
    if type(value) is not expected:
        return False
    try:
        return expected(**{
            field.name: getattr(value, field.name)
            for field in fields(expected) if field.init
        }) == value
    except (AttributeError, OSError, PipelineError, RuntimeError, TypeError, ValueError):
        return False


def _exact_keys(value: object, keys: tuple[str, ...]) -> bool:
    return type(value) is dict and tuple(sorted(value)) == tuple(sorted(keys))


def _is_int(value: object, expected: int | None = None) -> bool:
    return type(value) is int and value >= 0 and (expected is None or value == expected)


def _is_digest(value: object, expected: str | None = None) -> bool:
    return (
        type(value) is str and _SHA256.fullmatch(value) is not None
        and (expected is None or value == expected)
    )


def _safe_relative(value: object) -> bool:
    if type(value) is not str or not value or value == "." or "\x00" in value or "\\" in value:
        return False
    path = PurePosixPath(value)
    return (
        not path.is_absolute() and path.as_posix() == value
        and all(part not in {"", ".", ".."} for part in path.parts)
    )


def _has_symlink(path: Path, stop: Path) -> bool:
    try:
        current = path
        while True:
            if current.is_symlink():
                return True
            if current == stop or current.parent == current:
                return False
            current = current.parent
    except (OSError, RuntimeError):
        return True


def _report(states: dict[str, bool]) -> VerificationReport:
    checks = tuple(
        VerificationCheck(name, bool(states.get(name)), "PASS" if states.get(name) else "FAIL")
        for name in CHECK_NAMES
    )
    return VerificationReport(
        "PASS" if all(check.passed for check in checks) else "FAIL", checks
    )


def _read_json(path: Path) -> tuple[bytes, object] | None:
    if not path.is_file() or path.is_symlink():
        return None
    try:
        raw = path.read_bytes()
        return raw, json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, RecursionError) as error:
        raise InputFormatError("promotion JSON cannot establish verification context") from error
    except ValueError as error:
        raise InputFormatError("promotion JSON cannot establish verification context") from error


def _artifact_valid(value: object, kind: str, *, relative: bool = True) -> bool:
    keys = ("kind", "relative_path", "sha256", "size_bytes") if relative else (
        "kind", "sha256", "size_bytes",
    )
    return (
        _exact_keys(value, keys)
        and value["kind"] == kind
        and (not relative or _safe_relative(value["relative_path"]))
        and _is_digest(value["sha256"])
        and _is_int(value["size_bytes"])
    )


def _database_artifact_valid(value: object) -> bool:
    return (
        _exact_keys(
            value,
            ("kind", "relative_path", "sha256", "size_bytes", "semantic_sha256"),
        )
        and value["kind"] == "sqlite"
        and _safe_relative(value["relative_path"])
        and _is_digest(value["sha256"])
        and _is_int(value["size_bytes"])
        and _is_digest(value["semantic_sha256"])
    )


def _candidate_manifest(request: V121CandidateVerificationRequest) -> dict[str, object] | None:
    read = _read_json(request.candidate_dir / request.contract.manifest_filename)
    return read[1] if read is not None and type(read[1]) is dict else None


def _baseline_projection(candidate: dict[str, object]) -> dict[str, object]:
    baseline = candidate["baseline"]
    return {
        "release_version": "V1.20", "question_count": 543,
        "release_digest": BASELINE_RELEASE_DIGEST,
        "database_schema": "task10-v120-formal-v1",
        "sqlite": {"kind": "sqlite", "sha256": BASELINE_SHA256, "size_bytes": BASELINE_SIZE},
        "manifest": {
            "kind": "manifest", "sha256": BASELINE_MANIFEST_SHA256,
            "size_bytes": BASELINE_MANIFEST_SIZE,
        },
    }


def _candidate_projection() -> dict[str, object]:
    return {
        "generation": 4, "release_version": "V1.21", "release_status": "candidate",
        "database_schema": "task11-v121-candidate-v1",
        "candidate_digest": CANDIDATE_DIGEST,
        "sqlite": {"kind": "sqlite", "sha256": CANDIDATE_SHA256, "size_bytes": CANDIDATE_SIZE},
        "manifest": {"kind": "manifest", "sha256": CANDIDATE_MANIFEST_SHA256, "size_bytes": CANDIDATE_MANIFEST_SIZE},
    }


def _manifest_valid(
    value: object,
    candidate: dict[str, object],
    contract: V121PromotionContract,
) -> bool:
    keys = (
        "schema_version", "release_version", "release_status", "release_model",
        "database_schema", "baseline", "candidate", "batch_ledger",
        "batch_authority_artifacts", "counts", "database", "images",
        "artifacts", "rollback", "promotion", "verification",
    )
    if not _exact_keys(value, keys):
        return False
    counts = value["counts"]
    promotion = value["promotion"]
    verification = value["verification"]
    images = value["images"]
    artifacts = value["artifacts"]
    database = value["database"]
    rollback = value["rollback"]
    database_ref = (
        {
            key: database[key]
            for key in ("relative_path", "sha256", "size_bytes", "kind")
        }
        if _database_artifact_valid(database) else None
    )
    expected_artifacts = (
        [database_ref, rollback, *images]
        if database_ref is not None
        and _artifact_valid(rollback, "rollback")
        and type(images) is list
        and all(_artifact_valid(item, "image") for item in images)
        and images == sorted(images, key=lambda item: item["relative_path"].encode("utf-8"))
        else None
    )
    return all((
        value["schema_version"] == contract.release_manifest_schema,
        value["release_version"] == "V1.21",
        value["release_status"] == "published",
        value["release_model"] == "append-only-multi-batch-promotion",
        value["database_schema"] == contract.formal_database_schema,
        value["baseline"] == _baseline_projection(candidate),
        value["candidate"] == _candidate_projection(),
        value["batch_ledger"] == candidate["batch_ledger"],
        value["batch_authority_artifacts"] == candidate["batch_authority_artifacts"],
        counts == {"baseline_question_count": 543, "accepted_batch_count": 4,
                   "promoted_question_count": 48, "formal_question_count": 591},
        _database_artifact_valid(database)
        and database["relative_path"] == contract.database_filename,
        type(images) is list and all(_artifact_valid(item, "image") for item in images),
        type(candidate.get("images")) is list and images == candidate["images"],
        type(artifacts) is list and expected_artifacts is not None
        and artifacts == expected_artifacts,
        _artifact_valid(rollback, "rollback")
        and rollback["relative_path"] == contract.rollback_filename,
        _exact_keys(promotion, ("formal_target", "gate", "release_digest", "required_statement"))
        and promotion["formal_target"] == "releases/V1.21"
        and promotion["gate"] == "FINAL"
        and _is_digest(promotion["release_digest"])
        and promotion["required_statement"]
        == f"USER APPROVED RELEASE PROMOTION V1.21 {promotion['release_digest']}",
        verification == {"authority": "verify_v121_promotion",
                         "check_names": list(CHECK_NAMES), "required_status": "PASS"},
    ))


def _parse_sums(raw: bytes) -> tuple[tuple[str, str], ...] | None:
    try:
        text = raw.decode("utf-8")
    except UnicodeError:
        return None
    if not text.endswith("\n"):
        return None
    rows = []
    for line in text.splitlines():
        if len(line) < 67 or line[64:66] != "  ":
            return None
        digest, relative = line[:64], line[66:]
        if not _is_digest(digest) or not _safe_relative(relative):
            return None
        rows.append((relative, digest))
    if rows != sorted(rows, key=lambda item: item[0].encode("utf-8")):
        return None
    return tuple(rows)


def _file_matches(root: Path, value: dict[str, object]) -> bool:
    path = root / value["relative_path"]
    try:
        return (
            path.is_file() and not path.is_symlink()
            and path.stat().st_size == value["size_bytes"]
            and _sha_file(path) == value["sha256"]
        )
    except (OSError, RuntimeError, TypeError, ValueError):
        return False


def _promotion_payload(
    contract: V121PromotionContract,
    manifest: dict[str, object],
) -> dict[str, object]:
    return {
        "schema_version": contract.promotion_identity_schema,
        "release_version": "V1.21",
        "contract": {field.name: getattr(contract, field.name) for field in fields(contract)},
        "baseline": manifest["baseline"], "candidate": manifest["candidate"],
        "batch_ledger": manifest["batch_ledger"],
        "batch_authority_artifacts": manifest["batch_authority_artifacts"],
        "counts": manifest["counts"],
        "formal_sqlite_sha256": manifest["database"]["sha256"],
        "formal_sqlite_size_bytes": manifest["database"]["size_bytes"],
        "formal_sqlite_semantic_sha256": manifest["database"]["semantic_sha256"],
        "images": manifest["images"],
        "rollback_action": "remove_release_tree_if_release_digest_matches",
    }


def _schema_map(database: sqlite3.Connection) -> dict[str, tuple[str, str, str | None]]:
    return {
        row[1]: (
            row[0], row[2], None if row[3] is None else _normalize_sql(row[3]),
        )
        for row in database.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master "
            "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
        )
    }


def _relation_rows(database: sqlite3.Connection, name: str) -> tuple[tuple[object, ...], ...]:
    info = tuple(database.execute(f"PRAGMA table_info({_quoted(name)})"))
    if not info:
        raise sqlite3.DatabaseError(f"missing relation: {name}")
    columns = tuple(row[1] for row in info)
    primary = tuple(
        row[1] for row in sorted(
            (row for row in info if row[5]), key=lambda row: row[5]
        )
    )
    order_columns = (
        ("formal_order",) if "formal_order" in columns else primary or columns
    )
    order = ",".join(_quoted(column) for column in order_columns)
    return tuple(
        database.execute(f"SELECT * FROM {_quoted(name)} ORDER BY {order}")
    )


def _database_states(
    formal_path: Path,
    candidate_path: Path,
    contract: V121PromotionContract,
) -> dict[str, bool]:
    result = {
        name: False for name in (
            "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
            "sqlite_schema", "v120_preservation", "batch_ledger_closure",
            "promotion_projection", "formal_query", "count_closure",
        )
    }
    formal = candidate = None
    try:
        formal = sqlite3.connect(f"file:{formal_path.resolve()}?mode=ro&immutable=1", uri=True)
        candidate = sqlite3.connect(f"file:{candidate_path.resolve()}?mode=ro&immutable=1", uri=True)
        result["sqlite_readability"] = True
        result["sqlite_integrity"] = formal.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        result["sqlite_foreign_keys"] = tuple(formal.execute("PRAGMA foreign_key_check")) == ()
        candidate_schema = _schema_map(candidate)
        formal_schema = _schema_map(formal)
        expected_schema = dict(candidate_schema)
        expected_schema.update({
            contract.promotion_table: (
                "table", contract.promotion_table, _normalize_sql(_PROMOTION_TABLE_SQL),
            ),
            contract.promoted_table: (
                "table", contract.promoted_table, _normalize_sql(_PROMOTED_TABLE_SQL),
            ),
            contract.formal_view: (
                "view", contract.formal_view, _normalize_sql(_FORMAL_VIEW_SQL),
            ),
        })
        result["sqlite_schema"] = (
            formal_schema == expected_schema
            and formal.execute("PRAGMA user_version").fetchone() == (121,)
        )
        v120_formal = tuple(formal.execute("SELECT * FROM formal_complete_questions_v120 ORDER BY formal_order"))
        v120_candidate = tuple(candidate.execute("SELECT * FROM formal_complete_questions_v120 ORDER BY formal_order"))
        inherited_relations = tuple(
            row[0] for row in candidate.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view') "
                "AND name NOT LIKE 'sqlite_%' AND name!='release_metadata_v2' "
                "ORDER BY type,name"
            )
        )
        inherited_preserved = all(
            _relation_rows(formal, name) == _relation_rows(candidate, name)
            for name in inherited_relations
        )
        candidate_metadata = dict(candidate.execute(
            "SELECT key,value FROM release_metadata_v2"
        ))
        expected_metadata = dict(candidate_metadata)
        expected_metadata.update(_METADATA_DELTA)
        formal_metadata = dict(formal.execute(
            "SELECT key,value FROM release_metadata_v2"
        ))
        result["v120_preservation"] = (
            v120_formal == v120_candidate and len(v120_formal) == 543
            and inherited_preserved and formal_metadata == expected_metadata
        )
        ledger_formal = tuple(formal.execute("SELECT * FROM task11_v121_batch_ledger_v1 ORDER BY batch_ordinal"))
        ledger_candidate = tuple(candidate.execute("SELECT * FROM task11_v121_batch_ledger_v1 ORDER BY batch_ordinal"))
        result["batch_ledger_closure"] = (
            ledger_formal == ledger_candidate and len(ledger_formal) == 4
            and tuple(row[0] for row in ledger_formal) == (1, 2, 3, 4)
            and tuple(row[1] for row in ledger_formal) == (
                "JOY-M2-HKDSE-2015-PP-MS",
                "JOY-M2-HKDSE-2016-PP-MS",
                "JOY-M2-HKDSE-2017-PP-MS",
                "JOY-M2-HKDSE-2018-PP-MS",
            )
            and tuple(row[12] for row in ledger_formal) == (12, 12, 12, 12)
            and ledger_formal[-1][13:15] == (48, 591)
        )
        promoted = tuple(formal.execute(
            "SELECT * FROM task11_v121_promoted_questions_v1 ORDER BY formal_order"
        ))
        candidates = tuple(candidate.execute(
            "SELECT * FROM task11_v121_candidates_v1 ORDER BY aggregate_order"
        ))
        expected = tuple((*row[:30], "published", 1) for row in candidates)
        result["promotion_projection"] = promoted == expected and len(promoted) == 48
        rows = tuple(formal.execute(
            "SELECT * FROM formal_complete_questions_v121 ORDER BY formal_order"
        ))
        result["formal_query"] = (
            len(rows) == 591 and tuple(row[0] for row in rows) == tuple(range(1, 592))
            and rows[:543] == v120_formal
            and all(row[2] == "task11_v121_promoted" and row[-2:] == ("published", 1) for row in rows[543:])
        )
        promotion = tuple(formal.execute("SELECT * FROM task11_v121_promotion_v1"))
        expected_promotion = ((
            "V1.21", "task11-v121-formal-v1",
            "append-only-multi-batch-promotion", "published", "V1.20",
            BASELINE_SHA256, BASELINE_RELEASE_DIGEST, 543,
            CANDIDATE_DIGEST, CANDIDATE_SHA256, CANDIDATE_SIZE,
            CANDIDATE_MANIFEST_SHA256, CANDIDATE_MANIFEST_SIZE,
            4, 48, 591,
        ),)
        result["count_closure"] = (
            promotion == expected_promotion
            and len(promoted) == 48 and len(rows) == 591
        )
    except (OSError, sqlite3.Error, TypeError, ValueError):
        return result
    finally:
        if formal is not None:
            formal.close()
        if candidate is not None:
            candidate.close()
    return result


def verify_v121_promotion(
    request: V121PromotionVerificationRequest,
    config: PipelineConfig,
) -> VerificationReport:
    if not _reconstructs(request, V121PromotionVerificationRequest):
        raise PipelineError("request must be an exact valid V121PromotionVerificationRequest")
    if not _reconstructs(config, PipelineConfig):
        raise PipelineError("config must be an exact valid PipelineConfig")
    root = request.release_dir
    if not root.exists() and not root.is_symlink():
        raise InputMissingError("promotion directory does not exist")
    states = {name: False for name in CHECK_NAMES}
    try:
        resolved = root.resolve(strict=True)
    except (OSError, RuntimeError):
        return _report(states)
    if not resolved.is_dir() or root.is_symlink() or _has_symlink(root, config.repo_root):
        return _report(states)
    staging = config.staging_root.resolve(strict=False)
    formal_target = config.releases_root.resolve(strict=False) / "V1.21"
    boundary = resolved == formal_target or (
        resolved != staging and resolved.is_relative_to(staging)
    )
    states["release_directory"] = True
    states["publication_boundary"] = boundary
    states["promotion_contract"] = (
        type(request.contract) is V121PromotionContract
        and all(type(getattr(request.contract, key)) is type(value)
                and getattr(request.contract, key) == value
                for key, value in _CONTRACT_VALUES.items())
    )
    try:
        candidate_report = verify_v121_candidate(request.candidate, config)
        states["candidate_verification"] = (
            candidate_report.status == "PASS" and len(candidate_report.checks) == 24
            and all(check.passed for check in candidate_report.checks)
        )
    except PipelineError:
        states["candidate_verification"] = False
    candidate_root = request.candidate.candidate_dir
    candidate_database = candidate_root / request.candidate.contract.database_filename
    candidate_manifest_path = candidate_root / request.candidate.contract.manifest_filename
    candidate_manifest = _candidate_manifest(request.candidate)
    try:
        states["candidate_binding"] = (
            candidate_manifest is not None
            and candidate_database.is_file() and not candidate_database.is_symlink()
            and candidate_manifest_path.is_file() and not candidate_manifest_path.is_symlink()
            and _sha_file(candidate_database) == CANDIDATE_SHA256
            and candidate_database.stat().st_size == CANDIDATE_SIZE
            and _sha_file(candidate_manifest_path) == CANDIDATE_MANIFEST_SHA256
            and candidate_manifest_path.stat().st_size == CANDIDATE_MANIFEST_SIZE
            and candidate_manifest.get("candidate_digest") == CANDIDATE_DIGEST
            and len(request.candidate.approved_batches) == 4
        )
    except (OSError, RuntimeError, TypeError, ValueError):
        states["candidate_binding"] = False
    manifest_read = _read_json(resolved / request.contract.manifest_filename)
    rollback_read = _read_json(resolved / request.contract.rollback_filename)
    manifest = manifest_read[1] if manifest_read is not None else None
    rollback = rollback_read[1] if rollback_read is not None else None
    states["manifest_contract"] = (
        candidate_manifest is not None
        and _manifest_valid(manifest, candidate_manifest, request.contract)
        and manifest_read is not None
        and manifest_read[0] == _canonical_json_file_bytes(manifest)
    )
    expected_files: set[str] = set()
    if type(manifest) is dict and type(manifest.get("images")) is list:
        expected_files = {
            request.contract.database_filename, request.contract.manifest_filename,
            request.contract.sha256s_filename, request.contract.rollback_filename,
            *(item.get("relative_path") for item in manifest["images"] if type(item) is dict),
        }
    actual_files = {
        path.relative_to(resolved).as_posix()
        for path in resolved.rglob("*") if path.is_file() and not path.is_symlink()
    }
    no_unsafe = all(not path.is_symlink() for path in resolved.rglob("*"))
    states["filesystem_closure"] = expected_files == actual_files and no_unsafe
    sums_path = resolved / request.contract.sha256s_filename
    sums = _parse_sums(sums_path.read_bytes()) if sums_path.is_file() and not sums_path.is_symlink() else None
    expected_sum_paths = sorted(expected_files - {request.contract.sha256s_filename}, key=lambda value: value.encode("utf-8"))
    states["sha256sums_closure"] = (
        sums is not None and [row[0] for row in sums] == expected_sum_paths
        and all(
            (resolved / relative).is_file()
            and not (resolved / relative).is_symlink()
            and _sha_file(resolved / relative) == digest
            for relative, digest in sums
        )
    )
    if type(manifest) is dict:
        refs = [manifest.get("database"), manifest.get("rollback"), *manifest.get("images", [])]
        states["artifact_references"] = all(
            type(item) is dict and _file_matches(resolved, item) for item in refs
        )
    rollback_expected = None
    if type(manifest) is dict and type(manifest.get("promotion")) is dict:
        rollback_expected = {
            "schema_version": request.contract.rollback_schema,
            "release_version": "V1.21",
            "release_digest": manifest["promotion"].get("release_digest"),
            "action": "remove_release_tree_if_release_digest_matches",
            "protected_baseline": {
                "release_version": "V1.20", "question_count": 543,
                "sqlite_sha256": BASELINE_SHA256, "release_digest": BASELINE_RELEASE_DIGEST,
            },
            "candidate_digest": CANDIDATE_DIGEST,
            "release_artifacts": sorted(expected_files, key=lambda value: value.encode("utf-8")),
        }
    states["rollback_contract"] = (
        rollback_expected is not None and rollback == rollback_expected
        and rollback_read is not None and rollback_read[0] == _canonical_json_file_bytes(rollback)
    )
    formal_path = resolved / request.contract.database_filename
    states.update(_database_states(formal_path, candidate_database, request.contract))
    if candidate_manifest is not None and type(manifest) is dict:
        states["provenance_closure"] = (
            manifest.get("batch_ledger") == candidate_manifest.get("batch_ledger")
            and manifest.get("batch_authority_artifacts")
            == candidate_manifest.get("batch_authority_artifacts")
            and tuple(item.get("batch_id") for item in manifest.get("batch_ledger", []))
            == tuple(item[0] for item in (
                ("JOY-M2-HKDSE-2015-PP-MS",),
                ("JOY-M2-HKDSE-2016-PP-MS",),
                ("JOY-M2-HKDSE-2017-PP-MS",),
                ("JOY-M2-HKDSE-2018-PP-MS",),
            ))
        )
    if type(manifest) is dict and states["manifest_contract"] and formal_path.is_file():
        try:
            semantic = _sha_bytes(_canonical_json_file_bytes(
                _sqlite_semantic_payload(formal_path, request.contract.formal_view)
            ))
            payload = _promotion_payload(request.contract, manifest)
            digest = _sha_bytes(_canonical_json_file_bytes(payload))
            states["deterministic_identity"] = (
                semantic == manifest["database"]["semantic_sha256"]
                and digest == manifest["promotion"]["release_digest"]
            )
        except (OSError, InputFormatError, KeyError, TypeError, ValueError):
            states["deterministic_identity"] = False
    return _report(states)
