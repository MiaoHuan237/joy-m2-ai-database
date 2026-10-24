"""Independent test-owned V124 formal fixture; never calls production builder/verifier helpers."""
from contextlib import closing
from dataclasses import fields
from functools import lru_cache
from pathlib import Path, PurePosixPath
import hashlib,json,math,re,shutil,sqlite3,sys
from joy_m2.errors import InputFormatError,PromotionError
from joy_m2.ingest.vector_ch12_delegated_models import ChapterVerificationRequest, chapter_contract
from joy_m2.ingest.v124_promotion_models import V124PromotionBuildRequest,V124PromotionContract

ROOT=Path(__file__).resolve().parents[2]
CANDIDATE_ROOT=ROOT/"data/staging/vector-ch12-v124-S08-delegated-20261024-000001/candidate-generation-000008"
def promotion_contract():
    return V124PromotionContract("V1.24","task14-v124-formal-manifest-v1","task14-v124-formal-v1",
        "task14-v124-promotion-identity-v1","task14-v124-formal-rollback-v1",124,
        "Joy_M2_Complete_Question_DB_V1_24.sqlite3","manifest.json","SHA256SUMS.txt","rollback.json",
        "images/sha256","task14_v124_promoted_questions_v1","task14_v124_promotion_v1","formal_complete_questions_v124")

@lru_cache(maxsize=1)
def selected_candidate():
    # Rehydrate historical evidence, never regenerate a live delegated decision.
    sys.path.insert(0,str(ROOT/"data/staging/vector-ch12-delegation-20261024-000001"))
    import load_historical_checkpoint
    return ChapterVerificationRequest(CANDIDATE_ROOT,load_historical_checkpoint.load(),chapter_contract())

def tree(root):
    return tuple((p.relative_to(root).as_posix(),hashlib.sha256(p.read_bytes()).hexdigest(),p.stat().st_size)
        for p in sorted(root.rglob("*")) if p.is_file())

def write_json(path,value):
    path.write_bytes(json.dumps(value,ensure_ascii=False,sort_keys=True,separators=(",",":"),allow_nan=False).encode()+b"\n")

def rewrite_sums(root,filename="SHA256SUMS.txt"):
    names=sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and p.name!=filename)
    (root/filename).write_bytes("".join(hashlib.sha256((root/n).read_bytes()).hexdigest()+"  "+n+"\n" for n in names).encode())

def rebind(root,contract):
    # Independent test serialization, useful to test coherent malicious changes.
    m=json.loads((root/"manifest.json").read_bytes())
    db=root/contract.database_filename
    m["database"].update(sha256=hashlib.sha256(db.read_bytes()).hexdigest(),size_bytes=db.stat().st_size,
        semantic_sha256=_sqlite_semantic_sha256(db,contract.formal_view))
    ref={k:m["database"][k] for k in ("relative_path","sha256","size_bytes","kind")}
    payload={"schema_version":contract.promotion_identity_schema,"release_version":"V1.24",
        "contract":{f.name:getattr(contract,f.name) for f in fields(contract)},
        "baseline":m["baseline"],"candidate":m["candidate"],"batch_ledger":m["batch_ledger"],
        "batch_authority_artifacts":m["batch_authority_artifacts"],"counts":m["counts"],
        "formal_sqlite_sha256":ref["sha256"],"formal_sqlite_size_bytes":ref["size_bytes"],
        "formal_sqlite_semantic_sha256":m["database"]["semantic_sha256"],"images":m["images"],
        "rollback_action":"remove_release_tree_if_release_digest_matches"}
    digest=_promotion_identity(payload)
    m["promotion"]["release_digest"]=digest
    m["promotion"]["required_statement"]="USER APPROVED RELEASE PROMOTION V1.24 "+digest
    rb=json.loads((root/"rollback.json").read_bytes());rb["release_digest"]=digest
    write_json(root/"rollback.json",rb)
    rref=_artifact("rollback.json",root/"rollback.json","rollback");m["rollback"]=rref
    m["artifacts"]=sorted([ref,rref,*m["images"]],key=lambda i:i["relative_path"].encode())
    write_json(root/"manifest.json",m);rewrite_sums(root)

BASELINE_SHA256 = "28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd"
BASELINE_RELEASE_DIGEST = "84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc"
BASELINE_SIZE = 10_928_128
BASELINE_MANIFEST_SHA256 = "54d192436e761c9bfe810510b77a902c5ae659bebdfbc4da8475aac271be8498"
BASELINE_MANIFEST_SIZE = 6_728
CANDIDATE_DIGEST = "3f14589da452207d0088cd44689aded7ffbadea0768a85d808a67ae526a5f3ab"
CANDIDATE_SHA256 = "93acb2b4c333c4cb881c327389569898ab110ab2f436f00f1d40586e0ed4f8a0"
CANDIDATE_MANIFEST_SHA256 = "34cd37e27370a72e332d7047d9699d3910d853e1276132ce33ec26df4786de94"
CANDIDATE_SIZE = 11_378_688
CANDIDATE_MANIFEST_SIZE = 676_520

PROMOTION_TABLE_SQL = """CREATE TABLE task14_v124_promotion_v1 (
    release_version TEXT PRIMARY KEY CHECK(release_version='V1.24'),
    formal_database_schema TEXT NOT NULL CHECK(formal_database_schema='task14-v124-formal-v1'),
    release_model TEXT NOT NULL CHECK(release_model='append-only-multi-batch-promotion'),
    release_status TEXT NOT NULL CHECK(release_status='published'),
    baseline_release_version TEXT NOT NULL CHECK(baseline_release_version='V1.23'),
    baseline_database_sha256 TEXT NOT NULL CHECK(baseline_database_sha256='28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd'),
    baseline_release_digest TEXT NOT NULL CHECK(baseline_release_digest='84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc'),
    baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count=677),
    candidate_digest TEXT NOT NULL CHECK(candidate_digest='3f14589da452207d0088cd44689aded7ffbadea0768a85d808a67ae526a5f3ab'),
    candidate_database_sha256 TEXT NOT NULL CHECK(candidate_database_sha256='93acb2b4c333c4cb881c327389569898ab110ab2f436f00f1d40586e0ed4f8a0'),
    candidate_database_size INTEGER NOT NULL CHECK(candidate_database_size=11378688),
    candidate_manifest_sha256 TEXT NOT NULL CHECK(candidate_manifest_sha256='34cd37e27370a72e332d7047d9699d3910d853e1276132ce33ec26df4786de94'),
    candidate_manifest_size INTEGER NOT NULL CHECK(candidate_manifest_size=676520),
    accepted_batch_count INTEGER NOT NULL CHECK(accepted_batch_count=8),
    promoted_question_count INTEGER NOT NULL CHECK(promoted_question_count=114),
    formal_question_count INTEGER NOT NULL CHECK(formal_question_count=791)
)"""

PROMOTED_TABLE_SQL = """CREATE TABLE task14_v124_promoted_questions_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal BETWEEN 1 AND 8),
    batch_id TEXT NOT NULL,
    batch_candidate_order INTEGER NOT NULL CHECK(batch_candidate_order>=0),
    formal_order INTEGER PRIMARY KEY CHECK(formal_order BETWEEN 678 AND 791),
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
        REFERENCES task14_v124_batch_ledger_v1(batch_ordinal,batch_id)
)"""

FORMAL_VIEW_SQL = """CREATE VIEW formal_complete_questions_v124 AS
SELECT * FROM formal_complete_questions_v123
UNION ALL
SELECT
    p.formal_order,
    p.question_id,
    'task14_v124_promoted' AS authority_kind,
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
FROM task14_v124_promoted_questions_v1 AS p
ORDER BY formal_order"""

_ASCII_SPACE = re.compile(r"[ \t\r\n\f\v]+")

def _normalize_sql(value: str) -> str:
    normalized = _ASCII_SPACE.sub(" ", value).strip(" ")
    if normalized.endswith(";"):
        normalized = normalized[:-1].rstrip(" ")
    return normalized



def _canonical_json_file_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8") + b"\n"



def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()



def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()



def _quoted(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'



def _sqlite_json_value(value: object) -> object:
    if value is None or type(value) in {int, str}:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise InputFormatError("SQLite contains a non-finite number")
        return value
    if type(value) is bytes:
        return {"blob_hex": value.hex()}
    raise InputFormatError("SQLite contains an unsupported value")



def _sqlite_semantic_payload(path: Path, formal_view: str) -> dict[str, object]:
    uri = path.resolve().as_uri() + "?mode=ro&immutable=1"
    with closing(sqlite3.connect(uri, uri=True)) as database:
        schema_objects = [
            {
                "type": row[0],
                "name": row[1],
                "table_name": row[2],
                "sql": None if row[3] is None else _normalize_sql(row[3]),
            }
            for row in database.execute(
                "SELECT type,name,tbl_name,sql FROM sqlite_master "
                "WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
            )
        ]
        table_names = [
            row[0]
            for row in database.execute(
                "SELECT name FROM sqlite_master WHERE type='table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        relations = []
        for name in table_names + [formal_view]:
            info = tuple(database.execute(f"PRAGMA table_info({_quoted(name)})"))
            if not info:
                raise InputFormatError(f"SQLite relation is missing: {name}")
            columns = [row[1] for row in info]
            if name == formal_view:
                order_columns = ["formal_order"]
            else:
                primary = [row[1] for row in sorted((row for row in info if row[5]), key=lambda row: row[5])]
                order_columns = primary or columns
            order = ",".join(_quoted(column) for column in order_columns)
            rows = [
                [_sqlite_json_value(value) for value in row]
                for row in database.execute(
                    f"SELECT * FROM {_quoted(name)} ORDER BY {order}"
                )
            ]
            relations.append({"name": name, "columns": columns, "rows": rows})
        user_version = database.execute("PRAGMA user_version").fetchone()[0]
    return {
        "schema_version": "task14-v124-sqlite-semantic-v1",
        "user_version": user_version,
        "schema_objects": schema_objects,
        "relations": relations,
    }



def _sqlite_semantic_sha256(path: Path, formal_view: str) -> str:
    return _sha256_bytes(_canonical_json_file_bytes(_sqlite_semantic_payload(path, formal_view)))



def _promotion_identity(payload: dict[str, object]) -> str:
    return _sha256_bytes(_canonical_json_file_bytes(payload))



def _candidate_manifest(request: ChapterVerificationRequest) -> tuple[dict[str, object], bytes]:
    path = request.candidate_dir / request.contract.manifest_filename
    if not path.is_file() or path.is_symlink():
        raise PromotionError("candidate manifest is missing")
    try:
        raw = path.read_bytes()
        payload = json.loads(raw.decode("utf-8"))
    except (OSError, UnicodeError, ValueError, RecursionError) as error:
        raise PromotionError("candidate manifest is unreadable") from error
    if type(payload) is not dict:
        raise PromotionError("candidate manifest is invalid")
    return payload, raw



def _populate_database(path: Path, request: V124PromotionBuildRequest) -> None:
    with closing(sqlite3.connect(path)) as database:
        database.execute("PRAGMA foreign_keys=ON")
        database.execute("BEGIN IMMEDIATE")
        try:
            database.execute(PROMOTION_TABLE_SQL)
            database.execute(PROMOTED_TABLE_SQL)
            database.execute(
                "INSERT INTO task14_v124_promotion_v1 VALUES ("
                + ",".join("?" for _ in range(16)) + ")",
                (
                    "V1.24", request.contract.formal_database_schema,
                    "append-only-multi-batch-promotion", "published", "V1.23",
                    BASELINE_SHA256, BASELINE_RELEASE_DIGEST, 677,
                    CANDIDATE_DIGEST, CANDIDATE_SHA256, CANDIDATE_SIZE,
                    CANDIDATE_MANIFEST_SHA256, CANDIDATE_MANIFEST_SIZE,
                    8, 114, 791,
                ),
            )
            rows = tuple(
                database.execute(
                    "SELECT * FROM task14_v124_candidates_v1 ORDER BY aggregate_order"
                )
            )
            if len(rows) != 114 or tuple(row[3] for row in rows) != tuple(range(678, 792)):
                raise PromotionError("candidate row closure is invalid")
            baseline_ids = {
                row[0] for row in database.execute(
                    "SELECT question_id FROM formal_complete_questions_v123"
                )
            }
            if any(row[4] in baseline_ids for row in rows):
                raise PromotionError("candidate question ID collides with V1.23")
            for row in rows:
                database.execute(
                    "INSERT INTO task14_v124_promoted_questions_v1 VALUES ("
                    + ",".join("?" for _ in range(32))
                    + ")",
                    (*row[:30], "published", 1),
                )
            database.execute(FORMAL_VIEW_SQL)
            metadata = {
                "release_version": "V1.24",
                "baseline_version": "V1.23",
                "baseline_sqlite_sha256": BASELINE_SHA256,
                "release_model": "append-only-multi-batch-promotion",
                "schema_version": request.contract.formal_database_schema,
                "formal_question_count": "791",
                "task14_baseline_release_digest": BASELINE_RELEASE_DIGEST,
                "task14_candidate_digest": CANDIDATE_DIGEST,
                "task14_candidate_sqlite_sha256": CANDIDATE_SHA256,
                "task14_candidate_manifest_sha256": CANDIDATE_MANIFEST_SHA256,
                "task14_accepted_batch_count": "8",
                "task14_promoted_questions": "114",
            }
            for key, value in metadata.items():
                database.execute(
                    "INSERT INTO release_metadata_v2(key,value) VALUES (?,?) "
                    "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                    (key, value),
                )
            database.execute("PRAGMA user_version=124")
            database.commit()
        except Exception:
            database.rollback()
            raise



def _artifact(relative_path: str, path: Path, kind: str) -> dict[str, object]:
    return {
        "relative_path": relative_path,
        "sha256": _sha256_file(path),
        "size_bytes": path.stat().st_size,
        "kind": kind,
    }



def _copy_images(
    candidate_root: Path,
    target_root: Path,
    candidate_manifest: dict[str, object],
) -> list[dict[str, object]]:
    safe_candidate_root = candidate_root.resolve(strict=True)
    declared = candidate_manifest.get("images")
    if type(declared) is not list:
        raise PromotionError("candidate image closure is invalid")
    result = []
    for item in declared:
        if type(item) is not dict:
            raise PromotionError("candidate image entry is invalid")
        relative = _relative_path(item.get("relative_path"))
        source = (safe_candidate_root / relative).resolve(strict=False)
        if (
            not source.is_relative_to(safe_candidate_root)
            or not source.is_file()
            or source.is_symlink()
        ):
            raise PromotionError("candidate image is missing or unsafe")
        target = target_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        projected = _artifact(relative, target, "image")
        if (
            projected["sha256"] != item.get("sha256")
            or projected["size_bytes"] != item.get("size_bytes")
        ):
            raise PromotionError("candidate image bytes do not match authority")
        result.append(projected)
    result.sort(key=lambda item: item["relative_path"].encode("utf-8"))
    return result



def _relative_path(value: object) -> str:
    if type(value) is not str or not value or value == "." or "\x00" in value:
        raise InputFormatError("artifact path must be a non-empty canonical relative path")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or "\\" in value
        or path.as_posix() != value
        or any(part in {"", ".", ".."} for part in path.parts)
    ):
        raise InputFormatError("artifact path must be a canonical relative path")
    return value



def _promotion_payload(
    request: V124PromotionBuildRequest,
    database_artifact: dict[str, object],
    semantic_sha256: str,
    images: list[dict[str, object]],
) -> dict[str, object]:
    manifest, _ = _candidate_manifest(request.candidate)
    contract = {
        field.name: getattr(request.contract, field.name)
        for field in fields(V124PromotionContract)
    }
    return {
        "schema_version": request.contract.promotion_identity_schema,
        "release_version": "V1.24",
        "contract": contract,
        "baseline": _baseline_projection(manifest),
        "candidate": _candidate_projection(manifest),
        "batch_ledger": manifest["batch_ledger"],
        "batch_authority_artifacts": manifest["batch_authority_artifacts"],
        "counts": {
            "baseline_question_count": 677,
            "accepted_batch_count": 8,
            "promoted_question_count": 114,
            "formal_question_count": 791,
        },
        "formal_sqlite_sha256": database_artifact["sha256"],
        "formal_sqlite_size_bytes": database_artifact["size_bytes"],
        "formal_sqlite_semantic_sha256": semantic_sha256,
        "images": images,
        "rollback_action": "remove_release_tree_if_release_digest_matches",
    }



def _baseline_projection(manifest: dict[str, object]) -> dict[str, object]:
    value = manifest["baseline"]
    return {
        "release_version": "V1.23",
        "question_count": 677,
        "release_digest": BASELINE_RELEASE_DIGEST,
        "database_schema": "task13-v123-formal-v1",
        "sqlite": {
            "kind": "sqlite", "sha256": BASELINE_SHA256, "size_bytes": BASELINE_SIZE,
        },
        "manifest": {
            "kind": "manifest",
            "sha256": BASELINE_MANIFEST_SHA256,
            "size_bytes": BASELINE_MANIFEST_SIZE,
        },
    }



def _candidate_projection(manifest: dict[str, object]) -> dict[str, object]:
    return {
        "generation": 8,
        "release_version": "V1.24",
        "release_status": "candidate",
        "database_schema": "task14-v124-ch12-candidate-v1",
        "candidate_digest": CANDIDATE_DIGEST,
        "sqlite": {"kind": "sqlite", "sha256": CANDIDATE_SHA256, "size_bytes": CANDIDATE_SIZE},
        "manifest": {
            "kind": "manifest", "sha256": CANDIDATE_MANIFEST_SHA256,
            "size_bytes": CANDIDATE_MANIFEST_SIZE,
        },
    }



def _write_release_artifacts(
    root: Path,
    request: V124PromotionBuildRequest,
    candidate_manifest: dict[str, object],
) -> str:
    contract = request.contract
    database_path = root / contract.database_filename
    database_artifact = _artifact(contract.database_filename, database_path, "sqlite")
    semantic = _sqlite_semantic_sha256(database_path, contract.formal_view)
    images = _copy_images(request.candidate.candidate_dir, root, candidate_manifest)
    release_digest = _promotion_identity(
        _promotion_payload(request, database_artifact, semantic, images)
    )
    paths = sorted(
        [
            contract.database_filename,
            contract.manifest_filename,
            contract.sha256s_filename,
            contract.rollback_filename,
            *(item["relative_path"] for item in images),
        ],
        key=lambda value: value.encode("utf-8"),
    )
    rollback = {
        "schema_version": contract.rollback_schema,
        "action": "remove_release_tree_if_release_digest_matches",
        "release_version": "V1.24",
        "release_digest": release_digest,
        "protected_baseline": {
            "release_version": "V1.23",
            "sqlite_sha256": BASELINE_SHA256,
            "question_count": 677,
            "release_digest": BASELINE_RELEASE_DIGEST,
        },
        "candidate_digest": CANDIDATE_DIGEST,
        "release_artifacts": paths,
    }
    rollback_path = root / contract.rollback_filename
    rollback_path.write_bytes(_canonical_json_file_bytes(rollback))
    rollback_artifact = _artifact(contract.rollback_filename, rollback_path, "rollback")
    manifest = {
        "schema_version": contract.release_manifest_schema,
        "release_version": "V1.24",
        "release_status": "published",
        "release_model": "append-only-multi-batch-promotion",
        "database_schema": contract.formal_database_schema,
        "baseline": _baseline_projection(candidate_manifest),
        "candidate": _candidate_projection(candidate_manifest),
        "batch_ledger": candidate_manifest["batch_ledger"],
        "batch_authority_artifacts": candidate_manifest["batch_authority_artifacts"],
        "counts": {
            "baseline_question_count": 677,
            "accepted_batch_count": 8,
            "promoted_question_count": 114,
            "formal_question_count": 791,
        },
        "database": {
            **database_artifact,
            "semantic_sha256": semantic,
        },
        "images": images,
        "artifacts": sorted(
            [database_artifact, rollback_artifact, *images],
            key=lambda item: item["relative_path"].encode("utf-8"),
        ),
        "verification": {
            "authority": "verify_v124_promotion",
            "check_names": [
                "release_directory", "promotion_contract", "candidate_verification",
                "candidate_binding", "manifest_contract", "filesystem_closure",
                "sha256sums_closure", "artifact_references", "rollback_contract",
                "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
                "sqlite_schema", "v123_preservation", "batch_ledger_closure",
                "promotion_projection", "formal_query", "count_closure",
                "provenance_closure", "deterministic_identity",
                "publication_boundary", "image_projection",
            ],
            "required_status": "PASS",
        },
        "promotion": {
            "gate": "FINAL",
            "release_digest": release_digest,
            "required_statement": f"USER APPROVED RELEASE PROMOTION V1.24 {release_digest}",
            "formal_target": "releases/V1.24",
        },
        "rollback": rollback_artifact,
    }
    manifest_path = root / contract.manifest_filename
    manifest_path.write_bytes(_canonical_json_file_bytes(manifest))
    closure = []
    for item in sorted(
        [database_artifact["relative_path"], contract.manifest_filename, contract.rollback_filename, *(image["relative_path"] for image in images)],
        key=lambda value: value.encode("utf-8"),
    ):
        closure.append(f"{_sha256_file(root / item)}  {item}\n")
    (root / contract.sha256s_filename).write_bytes("".join(closure).encode("utf-8"))
    return release_digest



def fixture_release(output, candidate, contract):
    output.mkdir(parents=True)
    shutil.copyfile(candidate.candidate_dir / candidate.contract.database_filename,
                    output / contract.database_filename)
    request = V124PromotionBuildRequest(candidate, output, contract)
    _populate_database(output / contract.database_filename, request)
    manifest = json.loads((candidate.candidate_dir / candidate.contract.manifest_filename).read_text())
    _write_release_artifacts(output, request, manifest)
    with sqlite3.connect((output / contract.database_filename).as_uri()+"?mode=ro", uri=True) as db:
        assert db.execute("SELECT COUNT(*) FROM formal_complete_questions_v124").fetchone() == (791,)
        assert db.execute("SELECT COUNT(*) FROM formal_complete_questions_v123").fetchone() == (677,)
        assert db.execute("SELECT COUNT(*) FROM task14_v124_promoted_questions_v1 WHERE record_status='published' AND selectable=1").fetchone() == (114,)
    return output
