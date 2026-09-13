"""Independent read-only verification for Task 9D V1.19 promotion trees."""

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

from .promotion_models import V119PromotionContract, V119PromotionVerificationRequest
from .writer_models import V119VerificationRequest
from .writer_verification import verify_v119_candidate


BASELINE_SHA256 = "fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7"
CANDIDATE_SHA256 = "9d30cf444e9d6686128f884d5a3cf57f4e58ce544b7933d7a0a47ec0e8212d20"
CANDIDATE_MANIFEST_SHA256 = "b2e0b4607b49f5e1e097fd036dd0614c67128976e7d282f4e2783eb092be9634"
BATCH_ID = "TASK9B-REAL-0918-INTERVAL-REPRODUCTION-001"
PREFLIGHT_SHA256 = "4aa3ff8b419a0fcca57c805d5f10f252658cb30c00f6cf1b74c95ab3009333c9"
CHECK_NAMES = (
    "release_directory", "promotion_contract", "candidate_verification",
    "manifest_contract", "authority_binding", "filesystem_closure",
    "sha256sums_closure", "artifact_references", "rollback_contract",
    "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
    "sqlite_schema", "baseline_preservation", "promotion_projection",
    "formal_query", "count_closure", "publication_boundary",
)
_SHA256 = re.compile(r"[0-9a-f]{64}")
_ASCII_SPACE = re.compile(r"[ \t\r\n\f\v]+")

_PROMOTION_COLUMNS = (
    "release_version", "formal_database_schema", "release_model",
    "release_status", "baseline_release_version", "baseline_database_sha256",
    "baseline_question_count", "candidate_database_sha256",
    "candidate_manifest_sha256", "batch_id", "preflight_sha256",
    "import_approval_statement", "promoted_question_count", "formal_question_count",
)
_PROMOTED_COLUMNS = (
    "batch_id", "candidate_order", "formal_order", "question_id", "source_id",
    "source_question_number", "source_section", "source_fragment_hash",
    "normalized_text_sha256", "question_text_original", "question_text_zh",
    "translation_status", "translation_evidence", "solution_original",
    "solution_verified", "answer_status", "explanation_text",
    "explanation_status", "explanation_evidence", "source_image_paths_json",
    "source_image_sha256s_json", "source_image_roles_json", "primary_type",
    "tags_json", "tag_status", "difficulty_level", "difficulty_status",
    "enrichment_status", "formal_image_paths_json", "record_status", "selectable",
)
_FORMAL_COLUMNS = (
    "formal_order", "question_id", "authority_kind", "batch_id",
    "candidate_order", "source_id", "source_question_number", "source_section",
    "source_fragment_hash", "normalized_text_sha256", "question_text_original",
    "question_text_zh", "question_text_zh_reviewed", "translation_status",
    "translation_evidence", "solution_original", "solution_verified",
    "answer_status", "explanation_text", "explanation_status",
    "explanation_evidence", "source_image_paths_json", "source_image_sha256s_json",
    "source_image_roles_json", "primary_type", "tags_json", "tag_status",
    "difficulty_level", "difficulty_status", "enrichment_status",
    "formal_image_paths_json", "record_status", "selectable",
)

_PROMOTION_SQL = """CREATE TABLE task9_promotion_v1 (
    release_version TEXT PRIMARY KEY CHECK(release_version='V1.19'),
    formal_database_schema TEXT NOT NULL CHECK(formal_database_schema='task9-v119-formal-v1'),
    release_model TEXT NOT NULL CHECK(release_model='incremental-import-promotion'),
    release_status TEXT NOT NULL CHECK(release_status='published'),
    baseline_release_version TEXT NOT NULL CHECK(baseline_release_version='V1.18'),
    baseline_database_sha256 TEXT NOT NULL CHECK(length(baseline_database_sha256)=64 AND baseline_database_sha256 NOT GLOB '*[^0-9a-f]*'),
    baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count=497),
    candidate_database_sha256 TEXT NOT NULL CHECK(length(candidate_database_sha256)=64 AND candidate_database_sha256 NOT GLOB '*[^0-9a-f]*'),
    candidate_manifest_sha256 TEXT NOT NULL CHECK(length(candidate_manifest_sha256)=64 AND candidate_manifest_sha256 NOT GLOB '*[^0-9a-f]*'),
    batch_id TEXT NOT NULL UNIQUE,
    preflight_sha256 TEXT NOT NULL CHECK(length(preflight_sha256)=64 AND preflight_sha256 NOT GLOB '*[^0-9a-f]*'),
    import_approval_statement TEXT NOT NULL,
    promoted_question_count INTEGER NOT NULL CHECK(promoted_question_count=5),
    formal_question_count INTEGER NOT NULL CHECK(formal_question_count=baseline_question_count+promoted_question_count AND formal_question_count=502)
)"""

_PROMOTED_SQL = """CREATE TABLE task9_promoted_questions_v1 (
    batch_id TEXT NOT NULL REFERENCES task9_promotion_v1(batch_id),
    candidate_order INTEGER NOT NULL CHECK(candidate_order BETWEEN 0 AND 4),
    formal_order INTEGER PRIMARY KEY CHECK(formal_order BETWEEN 498 AND 502),
    question_id TEXT NOT NULL UNIQUE,
    source_id TEXT NOT NULL,
    source_question_number TEXT NOT NULL,
    source_section TEXT NOT NULL,
    source_fragment_hash TEXT NOT NULL CHECK(length(source_fragment_hash)=64 AND source_fragment_hash NOT GLOB '*[^0-9a-f]*'),
    normalized_text_sha256 TEXT NOT NULL CHECK(length(normalized_text_sha256)=64 AND normalized_text_sha256 NOT GLOB '*[^0-9a-f]*'),
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
    UNIQUE(batch_id, candidate_order),
    CHECK(formal_order=498+candidate_order)
)"""

_FORMAL_VIEW_SQL = """CREATE VIEW formal_complete_questions_v119 AS
SELECT
    q.source_order AS formal_order,
    q.question_id AS question_id,
    'baseline_v118' AS authority_kind,
    CAST(NULL AS TEXT) AS batch_id,
    CAST(NULL AS INTEGER) AS candidate_order,
    q.source_id AS source_id,
    q.source_question_number AS source_question_number,
    q.source_section AS source_section,
    q.source_fragment_hash AS source_fragment_hash,
    CAST(NULL AS TEXT) AS normalized_text_sha256,
    q.question_text_original AS question_text_original,
    q.question_text_zh AS question_text_zh,
    q.question_text_zh_reviewed AS question_text_zh_reviewed,
    CAST(NULL AS TEXT) AS translation_status,
    CAST(NULL AS TEXT) AS translation_evidence,
    q.solution_original AS solution_original,
    q.solution_verified AS solution_verified,
    q.answer_status AS answer_status,
    CAST(NULL AS TEXT) AS explanation_text,
    CAST(NULL AS TEXT) AS explanation_status,
    CAST(NULL AS TEXT) AS explanation_evidence,
    q.image_paths_json AS source_image_paths_json,
    CAST(NULL AS TEXT) AS source_image_sha256s_json,
    CAST(NULL AS TEXT) AS source_image_roles_json,
    q.primary_type AS primary_type,
    q.tags_json AS tags_json,
    CAST(NULL AS TEXT) AS tag_status,
    q.difficulty_level AS difficulty_level,
    CAST(NULL AS TEXT) AS difficulty_status,
    CAST(NULL AS TEXT) AS enrichment_status,
    q.image_paths_json AS formal_image_paths_json,
    q.record_status AS record_status,
    q.selectable AS selectable
FROM complete_questions_v2 AS q
UNION ALL
SELECT
    p.formal_order,
    p.question_id,
    'task9_promoted' AS authority_kind,
    p.batch_id,
    p.candidate_order,
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
FROM task9_promoted_questions_v1 AS p
ORDER BY formal_order"""


def _normalize_sql(value: str) -> str:
    normalized = _ASCII_SPACE.sub(" ", value).strip(" ")
    if normalized.endswith(";"):
        normalized = normalized[:-1].rstrip(" ")
    return normalized


def _canonical_json_file_bytes(value: object) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False
    ).encode("utf-8") + b"\n"


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _relative_path(value: object) -> str:
    if type(value) is not str or not value or value == "." or "\x00" in value:
        raise InputFormatError("artifact path must be canonical and relative")
    path = PurePosixPath(value)
    if path.is_absolute() or "\\" in value or path.as_posix() != value or any(part in {"", ".", ".."} for part in path.parts):
        raise InputFormatError("artifact path must be canonical and relative")
    return value


def _parse_sha256sums(raw: bytes) -> tuple[tuple[str, str], ...]:
    try:
        text = raw.decode("utf-8")
    except UnicodeError as error:
        raise InputFormatError("SHA256SUMS.txt must be UTF-8") from error
    if not text or not text.endswith("\n") or "\r" in text:
        raise InputFormatError("SHA256SUMS.txt must be non-empty LF-only text")
    result = []
    for line in text.splitlines():
        if len(line) < 67 or line[64:66] != "  ":
            raise InputFormatError("SHA256SUMS.txt line format is invalid")
        digest, relative = line[:64], line[66:]
        if _SHA256.fullmatch(digest) is None:
            raise InputFormatError("SHA256SUMS.txt digest is invalid")
        relative = _relative_path(relative)
        if relative == "SHA256SUMS.txt":
            raise InputFormatError("SHA256SUMS.txt cannot hash itself")
        result.append((relative, digest))
    ordered = tuple(sorted(result, key=lambda item: item[0].encode("utf-8")))
    if tuple(result) != ordered or len({item[0] for item in result}) != len(result):
        raise InputFormatError("SHA256SUMS.txt paths must be unique and sorted")
    return tuple(result)


def _quoted(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _sqlite_json_value(value: object) -> object:
    if value is None or type(value) in {int, str}:
        return value
    if type(value) is float and math.isfinite(value):
        return value
    if type(value) is bytes:
        return {"blob_hex": value.hex()}
    raise InputFormatError("SQLite contains an unsupported value")


def _sqlite_semantic_payload(path: Path, formal_view: str) -> dict[str, object]:
    with closing(
        sqlite3.connect(f"file:{path.resolve()}?mode=ro&immutable=1", uri=True)
    ) as database:
        schema_objects = [
            {"type": row[0], "name": row[1], "table_name": row[2], "sql": None if row[3] is None else _normalize_sql(row[3])}
            for row in database.execute("SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name")
        ]
        tables = [row[0] for row in database.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        relations = []
        for name in tables + [formal_view]:
            info = tuple(database.execute(f"PRAGMA table_info({_quoted(name)})"))
            if not info:
                raise InputFormatError(f"SQLite relation is missing: {name}")
            columns = [row[1] for row in info]
            primary = [row[1] for row in sorted((row for row in info if row[5]), key=lambda row: row[5])]
            order_columns = ["formal_order"] if name == formal_view else (primary or columns)
            order = ",".join(_quoted(column) for column in order_columns)
            rows = [[_sqlite_json_value(value) for value in row] for row in database.execute(f"SELECT * FROM {_quoted(name)} ORDER BY {order}")]
            relations.append({"name": name, "columns": columns, "rows": rows})
        user_version = database.execute("PRAGMA user_version").fetchone()[0]
    return {"schema_version": "task9-v119-sqlite-semantic-v1", "user_version": user_version, "schema_objects": schema_objects, "relations": relations}


def _sqlite_semantic_sha256(path: Path, formal_view: str) -> str:
    return _sha256_bytes(_canonical_json_file_bytes(_sqlite_semantic_payload(path, formal_view)))


def _reconstructs_exactly(value: object, expected: type) -> bool:
    if type(value) is not expected:
        return False
    try:
        return expected(**{field.name: getattr(value, field.name) for field in fields(expected) if field.init}) == value
    except (AttributeError, OSError, PipelineError, RuntimeError, TypeError, ValueError):
        return False


def _exact_keys(value: object, keys: tuple[str, ...]) -> bool:
    return type(value) is dict and set(value) == set(keys)


def _is_int(value: object, minimum: int | None = None) -> bool:
    return type(value) is int and (minimum is None or value >= minimum)


def _is_digest(value: object) -> bool:
    return type(value) is str and _SHA256.fullmatch(value) is not None


def _artifact_valid(value: object, kind: str) -> bool:
    return (
        _exact_keys(value, ("relative_path", "sha256", "size_bytes", "kind"))
        and value["kind"] == kind
        and _is_digest(value["sha256"])
        and _is_int(value["size_bytes"], 0)
        and _safe_relative(value["relative_path"])
    )


def _safe_relative(value: object) -> bool:
    try:
        _relative_path(value)
        return True
    except InputFormatError:
        return False


def _evidence_valid(value: object) -> bool:
    return (
        _exact_keys(value, ("relative_path", "sha256", "size_bytes", "kind"))
        and value["kind"] in {"candidate_json", "source", "answer", "teacher_notes", "common_errors"}
        and _safe_relative(value["relative_path"])
        and _is_digest(value["sha256"])
        and _is_int(value["size_bytes"], 0)
    )


def _manifest_contract_valid(value: object, contract: V119PromotionContract) -> bool:
    top = (
        "schema_version", "release_version", "release_status", "release_model",
        "database_schema", "baseline", "candidate", "import_approval", "counts",
        "database", "images", "artifacts", "verification", "promotion", "rollback",
    )
    if not _exact_keys(value, top):
        return False
    try:
        baseline = value["baseline"]
        candidate = value["candidate"]
        evidence = candidate["evidence"]
        approval = value["import_approval"]
        counts = value["counts"]
        database = value["database"]
        verification = value["verification"]
        promotion = value["promotion"]
        images = value["images"]
        artifacts = value["artifacts"]
        fixed = (
            value["schema_version"] == contract.release_manifest_schema,
            value["release_version"] == "V1.19",
            value["release_status"] == "published",
            value["release_model"] == "incremental-import-promotion",
            value["database_schema"] == contract.formal_database_schema,
        )
        return all(fixed) and (
            _exact_keys(baseline, ("release_version", "schema_version", "question_count", "sqlite"))
            and baseline["release_version"] == "V1.18"
            and baseline["schema_version"] == "complete-question-v1.0"
            and baseline["question_count"] == 497 and type(baseline["question_count"]) is int
            and _exact_keys(baseline["sqlite"], ("sha256", "size_bytes", "kind"))
            and baseline["sqlite"]["kind"] == "sqlite"
            and _is_digest(baseline["sqlite"]["sha256"])
            and _is_int(baseline["sqlite"]["size_bytes"], 0)
            and _exact_keys(candidate, ("release_version", "database_schema", "database", "manifest", "evidence"))
            and candidate["release_version"] == "V1.19"
            and candidate["database_schema"] == "task9-v119-candidate-v1"
            and all(
                _exact_keys(candidate[name], ("sha256", "size_bytes", "kind"))
                and candidate[name]["kind"] == kind
                and _is_digest(candidate[name]["sha256"])
                and _is_int(candidate[name]["size_bytes"], 0)
                for name, kind in (("database", "sqlite"), ("manifest", "manifest"))
            )
            and _exact_keys(evidence, ("candidate_records", "sources", "answers", "teacher_notes", "common_errors"))
            and all(type(evidence[name]) is list and all(_evidence_valid(item) for item in evidence[name]) for name in evidence)
            and _exact_keys(approval, ("batch_id", "preflight_sha256", "statement"))
            and type(approval["batch_id"]) is str and _is_digest(approval["preflight_sha256"])
            and type(approval["statement"]) is str
            and _exact_keys(counts, ("baseline_question_count", "promoted_question_count", "formal_question_count"))
            and counts["baseline_question_count"] == 497
            and counts["promoted_question_count"] == 5
            and counts["formal_question_count"] == 502
            and all(type(counts[name]) is int for name in counts)
            and _exact_keys(database, ("relative_path", "sha256", "semantic_sha256", "size_bytes", "kind"))
            and database["relative_path"] == contract.database_filename and database["kind"] == "sqlite"
            and _is_digest(database["sha256"]) and _is_digest(database["semantic_sha256"])
            and _is_int(database["size_bytes"], 0)
            and type(images) is list and all(_artifact_valid(item, "image") for item in images)
            and images == sorted(images, key=lambda item: item["relative_path"].encode("utf-8"))
            and type(artifacts) is list and all(type(item) is dict and item.get("kind") in {"sqlite", "rollback", "image"} and _artifact_valid(item, item["kind"]) for item in artifacts)
            and artifacts == sorted(artifacts, key=lambda item: item["relative_path"].encode("utf-8"))
            and artifacts == sorted(
                [
                    {
                        "relative_path": database["relative_path"],
                        "sha256": database["sha256"],
                        "size_bytes": database["size_bytes"],
                        "kind": "sqlite",
                    },
                    value["rollback"],
                    *images,
                ],
                key=lambda item: item["relative_path"].encode("utf-8"),
            )
            and _exact_keys(verification, ("authority", "check_names", "required_status"))
            and verification == {"authority": "verify_v119_promotion", "check_names": list(CHECK_NAMES), "required_status": "PASS"}
            and _exact_keys(promotion, ("gate", "release_digest", "required_statement", "formal_target"))
            and promotion["gate"] == "D" and _is_digest(promotion["release_digest"])
            and promotion["required_statement"] == f"USER APPROVED RELEASE PROMOTION V1.19 {promotion['release_digest']}"
            and promotion["formal_target"] == "releases/V1.19"
            and _artifact_valid(value["rollback"], "rollback")
        )
    except (KeyError, TypeError, ValueError):
        return False


def _read_json(path: Path, *, manifest: bool) -> object:
    try:
        raw = path.read_bytes()
        return json.loads(raw.decode("utf-8"))
    except (UnicodeError, ValueError, RecursionError) as error:
        if manifest:
            raise InputFormatError("promotion manifest must be valid UTF-8 JSON") from error
        return None
    except OSError:
        return None


def _load_candidate_manifest(candidate: V119VerificationRequest) -> dict[str, object] | None:
    value = _read_json(candidate.candidate_dir / candidate.contract.manifest_filename, manifest=False)
    return value if type(value) is dict else None


def _project_candidate_images(value: object) -> list[dict[str, object]] | None:
    if type(value) is not dict or type(value.get("images")) is not list:
        return None
    result = []
    for item in value["images"]:
        if (
            type(item) is not dict
            or item.get("kind") != "image"
            or not _safe_relative(item.get("relative_path"))
            or not _is_digest(item.get("sha256"))
            or not _is_int(item.get("size_bytes"), 0)
        ):
            return None
        result.append(
            {
                "relative_path": item["relative_path"],
                "sha256": item["sha256"],
                "size_bytes": item["size_bytes"],
                "kind": "image",
            }
        )
    return sorted(result, key=lambda item: item["relative_path"].encode("utf-8"))


def _canonical_json_file(path: Path, value: object) -> bool:
    try:
        return path.read_bytes() == _canonical_json_file_bytes(value)
    except (OSError, TypeError, ValueError):
        return False


def _relation_rows(database: sqlite3.Connection, name: str) -> tuple[tuple[object, ...], ...]:
    info = tuple(database.execute(f"PRAGMA table_info({_quoted(name)})"))
    if not info:
        raise sqlite3.DatabaseError(f"relation is missing: {name}")
    columns = [row[1] for row in info]
    primary = [
        row[1]
        for row in sorted((row for row in info if row[5]), key=lambda row: row[5])
    ]
    order = ",".join(_quoted(column) for column in (primary or columns))
    return tuple(database.execute(f"SELECT * FROM {_quoted(name)} ORDER BY {order}"))


def _file_matches(root: Path, artifact: dict[str, object]) -> bool:
    try:
        unresolved = root / artifact["relative_path"]
        if unresolved.is_symlink():
            return False
        path = unresolved.resolve(strict=True)
        return (
            path.is_relative_to(root.resolve(strict=True)) and path.is_file() and not path.is_symlink()
            and path.stat().st_size == artifact["size_bytes"]
            and _sha256_file(path) == artifact["sha256"]
        )
    except (OSError, KeyError, RuntimeError, TypeError, ValueError):
        return False


def _database_checks(
    path: Path,
    baseline_path: Path,
    candidate_path: Path,
    contract: V119PromotionContract,
) -> dict[str, bool]:
    result = {name: False for name in ("sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys", "sqlite_schema", "baseline_preservation", "promotion_projection", "formal_query", "count_closure")}
    formal = baseline = candidate = None
    try:
        formal = sqlite3.connect(f"file:{path.resolve()}?mode=ro&immutable=1", uri=True)
        baseline = sqlite3.connect(f"file:{baseline_path.resolve()}?mode=ro&immutable=1", uri=True)
        candidate = sqlite3.connect(f"file:{candidate_path.resolve()}?mode=ro&immutable=1", uri=True)
    except (OSError, sqlite3.Error):
        for connection in (candidate, baseline, formal):
            if connection is not None:
                connection.close()
        return result
    try:
        result["sqlite_readability"] = formal.execute("PRAGMA user_version").fetchone() == (119,)
        result["sqlite_integrity"] = formal.execute("PRAGMA integrity_check").fetchone() == ("ok",)
        result["sqlite_foreign_keys"] = formal.execute("PRAGMA foreign_key_check").fetchall() == []
        schema = {row[0]: row[1] for row in formal.execute("SELECT name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
        inherited = {row[0]: row[1] for row in candidate.execute("SELECT name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
        inherited_valid = all(name in schema and _normalize_sql(schema[name] or "") == _normalize_sql(sql or "") for name, sql in inherited.items())
        result["sqlite_schema"] = (
            inherited_valid
            and set(schema) == set(inherited) | {contract.promotion_table, contract.promoted_table, contract.formal_view}
            and tuple(row[1] for row in formal.execute(f"PRAGMA table_info({_quoted(contract.promotion_table)})")) == _PROMOTION_COLUMNS
            and tuple(row[1] for row in formal.execute(f"PRAGMA table_info({_quoted(contract.promoted_table)})")) == _PROMOTED_COLUMNS
            and tuple(row[1] for row in formal.execute(f"PRAGMA table_info({_quoted(contract.formal_view)})")) == _FORMAL_COLUMNS
            and _normalize_sql(schema.get(contract.promotion_table, "")) == _normalize_sql(_PROMOTION_SQL)
            and _normalize_sql(schema.get(contract.promoted_table, "")) == _normalize_sql(_PROMOTED_SQL)
            and _normalize_sql(schema.get(contract.formal_view, "")) == _normalize_sql(_FORMAL_VIEW_SQL)
        )
        baseline_rows = tuple(baseline.execute("SELECT * FROM complete_questions_v2 ORDER BY source_order"))
        formal_baseline_rows = tuple(formal.execute("SELECT * FROM complete_questions_v2 ORDER BY source_order"))
        baseline_schema = {row[0]: row[1] for row in baseline.execute("SELECT name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'")}
        baseline_relations = tuple(
            row[0]
            for row in baseline.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view') "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        )
        baseline_relation_preserved = all(
            name == "release_metadata_v2"
            or _relation_rows(formal, name) == _relation_rows(baseline, name)
            for name in baseline_relations
        )
        result["baseline_preservation"] = (
            baseline_rows == formal_baseline_rows
            and baseline_relation_preserved
            and all(
                name in schema
                and _normalize_sql(schema[name] or "") == _normalize_sql(sql or "")
                for name, sql in baseline_schema.items()
            )
        )
        candidate_rows = tuple(candidate.execute("SELECT * FROM task9_import_candidates_v1 ORDER BY candidate_order"))
        promoted = tuple(formal.execute("SELECT * FROM task9_promoted_questions_v1 ORDER BY candidate_order"))
        expected = tuple((row[0], row[1], 498 + row[1], row[2], *row[3:27], row[27], "published", 1) for row in candidate_rows)
        promotion_rows = tuple(formal.execute("SELECT * FROM task9_promotion_v1"))
        expected_promotion = (("V1.19", "task9-v119-formal-v1", "incremental-import-promotion", "published", "V1.18", BASELINE_SHA256, 497, CANDIDATE_SHA256, CANDIDATE_MANIFEST_SHA256, BATCH_ID, PREFLIGHT_SHA256, f"USER APPROVED IMPORT BATCH {BATCH_ID} {PREFLIGHT_SHA256} V1.19", 5, 502),)
        metadata = dict(formal.execute("SELECT key,value FROM release_metadata_v2"))
        expected_metadata = dict(candidate.execute("SELECT key,value FROM release_metadata_v2"))
        expected_metadata.update({
            "release_version": "V1.19",
            "baseline_version": "V1.18",
            "baseline_sqlite_sha256": BASELINE_SHA256,
            "release_model": "incremental-import-promotion",
            "schema_version": "task9-v119-formal-v1",
            "task9_batch_id": BATCH_ID,
            "task9_preflight_sha256": PREFLIGHT_SHA256,
            "task9_candidate_sqlite_sha256": CANDIDATE_SHA256,
            "task9_candidate_manifest_sha256": CANDIDATE_MANIFEST_SHA256,
            "task9_promoted_questions": "5",
            "formal_question_count": "502",
        })
        candidate_relations = tuple(
            row[0]
            for row in candidate.execute(
                "SELECT name FROM sqlite_master WHERE type IN ('table','view') "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
            if row[0] not in baseline_relations
        )
        candidate_relation_preserved = all(
            _relation_rows(formal, name) == _relation_rows(candidate, name)
            for name in candidate_relations
        )
        result["promotion_projection"] = (
            promoted == expected
            and promotion_rows == expected_promotion
            and candidate_relation_preserved
            and all(row[-2:] == ("published", 1) for row in promoted)
            and metadata == expected_metadata
        )
        formal_rows = tuple(formal.execute(f"SELECT * FROM {_quoted(contract.formal_view)} ORDER BY formal_order"))
        result["formal_query"] = len(formal_rows) == 502 and tuple(row[0] for row in formal_rows) == tuple(range(1, 503)) and len({row[1] for row in formal_rows}) == 502 and all(row[2] == "baseline_v118" for row in formal_rows[:497]) and all(row[2] == "task9_promoted" and row[12] is None and row[-2:] == ("published", 1) for row in formal_rows[497:])
        result["count_closure"] = len(baseline_rows) == 497 and len(candidate_rows) == 5 and len(promoted) == 5 and len(formal_rows) == 502
    except (OSError, sqlite3.Error, TypeError, ValueError):
        pass
    finally:
        formal.close()
        baseline.close()
        candidate.close()
    return result


def verify_v119_promotion(
    request: V119PromotionVerificationRequest,
    config: PipelineConfig,
) -> VerificationReport:
    if not _reconstructs_exactly(request, V119PromotionVerificationRequest):
        raise PipelineError("request must be an exact valid V119PromotionVerificationRequest")
    if not _reconstructs_exactly(config, PipelineConfig):
        raise PipelineError("config must be an exact valid PipelineConfig")
    root = request.release_dir.resolve(strict=False)
    if not root.exists():
        raise InputMissingError("promotion root does not exist")
    states = {name: False for name in CHECK_NAMES}
    staging = root.is_relative_to(config.staging_root) and root != config.staging_root
    formal = root == (config.releases_root / "V1.19").resolve(strict=False)
    states["release_directory"] = root.is_dir() and not root.is_symlink() and (staging or formal)
    states["publication_boundary"] = states["release_directory"]
    states["promotion_contract"] = _reconstructs_exactly(request.contract, V119PromotionContract)
    try:
        candidate_report = verify_v119_candidate(request.candidate, config)
        states["candidate_verification"] = candidate_report.status == "PASS" and all(check.passed for check in candidate_report.checks)
    except InputFormatError:
        raise
    except PipelineError:
        states["candidate_verification"] = False
    manifest_path = root / request.contract.manifest_filename
    if not manifest_path.is_file() or manifest_path.is_symlink():
        manifest = None
    else:
        manifest = _read_json(manifest_path, manifest=True)
    states["manifest_contract"] = (
        _manifest_contract_valid(manifest, request.contract)
        and _canonical_json_file(manifest_path, manifest)
    )
    candidate_manifest = _load_candidate_manifest(request.candidate)
    if states["manifest_contract"] and candidate_manifest is not None:
        try:
            evidence = manifest["candidate"]["evidence"]
            expected_evidence = {
                "candidate_records": candidate_manifest["candidate_record_evidence"],
                "sources": candidate_manifest["source_evidence"],
                "answers": candidate_manifest["answer_evidence"],
                "teacher_notes": candidate_manifest["teacher_notes_evidence"],
                "common_errors": candidate_manifest["common_errors_evidence"],
            }
            identity_payload = {
                "schema_version": request.contract.promotion_identity_schema,
                "release_version": "V1.19",
                "baseline_database_sha256": BASELINE_SHA256,
                "baseline_question_count": 497,
                "candidate_database_sha256": CANDIDATE_SHA256,
                "candidate_manifest_sha256": CANDIDATE_MANIFEST_SHA256,
                "batch_id": BATCH_ID,
                "preflight_sha256": PREFLIGHT_SHA256,
                "import_approval_statement": request.candidate.approval.statement,
                "promoted_question_count": 5,
                "formal_question_count": 502,
                "formal_sqlite_sha256": manifest["database"]["sha256"],
                "formal_sqlite_semantic_sha256": manifest["database"]["semantic_sha256"],
                "images": manifest["images"],
            }
            release_digest = _sha256_bytes(_canonical_json_file_bytes(identity_payload))
            baseline_ref = request.candidate.preflight_result.baseline_database
            candidate_database_path = (
                request.candidate.candidate_dir
                / request.candidate.contract.database_filename
            )
            candidate_manifest_path = (
                request.candidate.candidate_dir
                / request.candidate.contract.manifest_filename
            )
            projected_images = _project_candidate_images(candidate_manifest)
            states["authority_binding"] = (
                manifest["baseline"]["sqlite"]["sha256"] == BASELINE_SHA256
                and manifest["baseline"]["sqlite"]["size_bytes"] == baseline_ref.size_bytes
                and manifest["candidate"]["database"]["sha256"] == CANDIDATE_SHA256
                and manifest["candidate"]["database"]["size_bytes"] == candidate_database_path.stat().st_size
                and manifest["candidate"]["manifest"]["sha256"] == CANDIDATE_MANIFEST_SHA256
                and manifest["candidate"]["manifest"]["size_bytes"] == candidate_manifest_path.stat().st_size
                and manifest["import_approval"] == {"batch_id": BATCH_ID, "preflight_sha256": PREFLIGHT_SHA256, "statement": f"USER APPROVED IMPORT BATCH {BATCH_ID} {PREFLIGHT_SHA256} V1.19"}
                and evidence == expected_evidence
                and projected_images is not None
                and manifest["images"] == projected_images
                and manifest["promotion"]["release_digest"] == release_digest
            )
        except (OSError, KeyError, TypeError, ValueError):
            states["authority_binding"] = False
    expected_files = set()
    if states["manifest_contract"]:
        expected_files = {request.contract.database_filename, request.contract.manifest_filename, request.contract.sha256s_filename, request.contract.rollback_filename, *(item["relative_path"] for item in manifest["images"])}
    try:
        actual_files = set()
        actual_directories = set()
        safe = True
        for item in root.rglob("*"):
            if item.is_symlink():
                safe = False
                continue
            if item.is_file():
                actual_files.add(item.relative_to(root).as_posix())
            elif item.is_dir():
                actual_directories.add(item.relative_to(root).as_posix())
            else:
                safe = False
        expected_directories = set()
        for relative in expected_files:
            parent = PurePosixPath(relative).parent
            while parent != PurePosixPath("."):
                expected_directories.add(parent.as_posix())
                parent = parent.parent
        states["filesystem_closure"] = (
            safe
            and actual_files == expected_files
            and actual_directories == expected_directories
        )
    except OSError:
        states["filesystem_closure"] = False
    sums_path = root / request.contract.sha256s_filename
    try:
        sums = _parse_sha256sums(sums_path.read_bytes())
        states["sha256sums_closure"] = set(path for path, _ in sums) == expected_files - {request.contract.sha256s_filename} and all(_sha256_file(root / path) == digest for path, digest in sums)
    except (OSError, InputFormatError):
        states["sha256sums_closure"] = False
    if states["manifest_contract"]:
        states["artifact_references"] = all(_file_matches(root, item) for item in [manifest["database"], manifest["rollback"], *manifest["images"], *manifest["artifacts"]])
    rollback = _read_json(root / request.contract.rollback_filename, manifest=False)
    if states["manifest_contract"] and type(rollback) is dict:
        expected_paths = sorted(expected_files, key=lambda value: value.encode("utf-8"))
        states["rollback_contract"] = (
            _exact_keys(rollback, ("schema_version", "action", "release_version", "release_digest", "protected_baseline", "release_artifacts"))
            and rollback.get("schema_version") == request.contract.rollback_schema
            and rollback.get("action") == "remove_release_tree_if_release_digest_matches"
            and rollback.get("release_version") == "V1.19"
            and rollback.get("release_digest") == manifest["promotion"]["release_digest"]
            and rollback.get("protected_baseline") == {"release_version": "V1.18", "sqlite_sha256": BASELINE_SHA256, "question_count": 497}
            and rollback.get("release_artifacts") == expected_paths
            and _canonical_json_file(
                root / request.contract.rollback_filename, rollback
            )
        )
    database_path = root / request.contract.database_filename
    baseline_path = request.candidate.preflight_result.baseline_database.path
    candidate_path = request.candidate.candidate_dir / request.candidate.contract.database_filename
    if database_path.is_file() and not database_path.is_symlink():
        states.update(_database_checks(database_path, baseline_path, candidate_path, request.contract))
        if states["manifest_contract"]:
            try:
                states["artifact_references"] = states["artifact_references"] and manifest["database"]["sha256"] == _sha256_file(database_path) and manifest["database"]["size_bytes"] == database_path.stat().st_size and manifest["database"]["semantic_sha256"] == _sqlite_semantic_sha256(database_path, request.contract.formal_view)
            except (OSError, InputFormatError, sqlite3.Error):
                states["artifact_references"] = False
    checks = tuple(VerificationCheck(name, states[name], "PASS" if states[name] else "FAIL") for name in CHECK_NAMES)
    return VerificationReport("PASS" if all(check.passed for check in checks) else "FAIL", checks)
