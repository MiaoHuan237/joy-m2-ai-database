"""Fixed V1.24 candidate DDL and genesis; version-neutral helpers reused."""
from joy_m2.errors import InputFormatError
from .v123_writer_profiles import (
    canonical_json_bytes, canonical_json_file_bytes, sha256_bytes, sha256_file,
    image_destination, is_sha256, normalized_sql, relative_path,
)

BASELINE_SHA256 = "28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd"
BASELINE_SIZE_BYTES = 10_928_128
BASELINE_MANIFEST_SHA256 = "54d192436e761c9bfe810510b77a902c5ae659bebdfbc4da8475aac271be8498"
BASELINE_MANIFEST_SIZE_BYTES = 6_728
BASELINE_RELEASE_DIGEST = "84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc"
GENESIS_DIGEST = "797ed06ca5833bac060c1603cada38a6f2aa9eb080a40d9dc892bba9a549773a"

CHECK_NAMES = (
    "candidate_directory", "candidate_contract", "baseline_authority",
    "batch_authority_artifacts", "parent_chain", "approval_binding",
    "preflight_reconstruction", "filesystem_closure", "sha256sums_closure",
    "artifact_references", "rollback_contract", "image_projection",
    "sqlite_readability", "sqlite_integrity", "sqlite_foreign_keys",
    "sqlite_schema", "v123_preservation", "batch_ledger",
    "candidate_projection", "effective_collision_closure", "count_closure",
    "candidate_digest", "deterministic_identity", "formal_boundary",
)

TASK14_SCHEMA_SQL = (
    """CREATE TABLE task14_v124_batch_ledger_v1 (
    batch_ordinal INTEGER PRIMARY KEY CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL UNIQUE CHECK(length(batch_id) BETWEEN 1 AND 128),
    target_release_version TEXT NOT NULL CHECK(target_release_version = 'V1.24'),
    candidate_database_schema TEXT NOT NULL
        CHECK(candidate_database_schema = 'task14-v124-candidate-v1'),
    parent_candidate_digest TEXT NOT NULL
        CHECK(length(parent_candidate_digest) = 64
              AND parent_candidate_digest NOT GLOB '*[^0-9a-f]*'),
    preflight_sha256 TEXT NOT NULL UNIQUE
        CHECK(length(preflight_sha256) = 64
              AND preflight_sha256 NOT GLOB '*[^0-9a-f]*'),
    manifest_sha256 TEXT NOT NULL
        CHECK(length(manifest_sha256) = 64
              AND manifest_sha256 NOT GLOB '*[^0-9a-f]*'),
    approval_statement TEXT NOT NULL
        CHECK(approval_statement =
              'USER APPROVED IMPORT BATCH ' || batch_id || ' ' ||
              preflight_sha256 || ' V1.24 PARENT ' ||
              parent_candidate_digest),
    baseline_release_version TEXT NOT NULL CHECK(baseline_release_version = 'V1.23'),
    baseline_database_sha256 TEXT NOT NULL
        CHECK(baseline_database_sha256 =
              '28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd'),
    baseline_release_digest TEXT NOT NULL
        CHECK(baseline_release_digest =
              '84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc'),
    baseline_question_count INTEGER NOT NULL CHECK(baseline_question_count = 677),
    batch_candidate_count INTEGER NOT NULL CHECK(batch_candidate_count >= 0),
    cumulative_candidate_count INTEGER NOT NULL
        CHECK(cumulative_candidate_count >= batch_candidate_count),
    projected_question_count INTEGER NOT NULL
        CHECK(projected_question_count = 677 + cumulative_candidate_count),
    record_status TEXT NOT NULL CHECK(record_status = 'candidate'),
    UNIQUE(batch_ordinal, batch_id)
)""",
    """CREATE TABLE task14_v124_candidates_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL,
    batch_candidate_order INTEGER NOT NULL CHECK(batch_candidate_order >= 0),
    aggregate_order INTEGER NOT NULL CHECK(aggregate_order >= 678),
    proposed_question_id TEXT NOT NULL,
    source_id TEXT NOT NULL,
    source_question_number TEXT NOT NULL,
    source_section TEXT NOT NULL,
    source_fragment_hash TEXT NOT NULL,
    normalized_text_sha256 TEXT NOT NULL,
    question_text_original TEXT NOT NULL,
    question_text_zh TEXT NOT NULL,
    translation_status TEXT NOT NULL
        CHECK(translation_status IN ('source_present','ai_proposed','verified','missing')),
    translation_evidence TEXT,
    solution_original TEXT NOT NULL,
    solution_verified TEXT NOT NULL,
    answer_status TEXT NOT NULL
        CHECK(answer_status IN ('source_provided','ai_solved_verified','missing_from_source')),
    explanation_text TEXT NOT NULL,
    explanation_status TEXT NOT NULL
        CHECK(explanation_status IN ('source_present','ai_proposed','verified','missing')),
    explanation_evidence TEXT,
    image_paths_json TEXT NOT NULL,
    image_sha256s_json TEXT NOT NULL,
    image_roles_json TEXT NOT NULL,
    primary_type TEXT NOT NULL,
    tags_json TEXT NOT NULL,
    tag_status TEXT NOT NULL CHECK(tag_status IN ('source_provided','proposed','missing')),
    difficulty_level INTEGER CHECK(difficulty_level BETWEEN 1 AND 5
                                   OR difficulty_level IS NULL),
    difficulty_status TEXT NOT NULL
        CHECK(difficulty_status IN ('source_provided','proposed','missing')),
    enrichment_status TEXT NOT NULL
        CHECK(enrichment_status IN ('complete','incomplete')),
    candidate_image_paths_json TEXT NOT NULL,
    record_status TEXT NOT NULL CHECK(record_status = 'candidate'),
    selectable INTEGER NOT NULL CHECK(selectable = 0),
    PRIMARY KEY(batch_id, proposed_question_id),
    UNIQUE(proposed_question_id),
    UNIQUE(aggregate_order),
    UNIQUE(batch_ordinal, batch_candidate_order),
    UNIQUE(batch_ordinal, batch_id, proposed_question_id),
    FOREIGN KEY(batch_ordinal, batch_id)
        REFERENCES task14_v124_batch_ledger_v1(batch_ordinal, batch_id)
)""",
    """CREATE TABLE task14_v124_images_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL,
    proposed_question_id TEXT NOT NULL,
    image_order INTEGER NOT NULL CHECK(image_order >= 0),
    source_relative_path TEXT NOT NULL,
    candidate_relative_path TEXT NOT NULL,
    sha256 TEXT NOT NULL
        CHECK(length(sha256) = 64 AND sha256 NOT GLOB '*[^0-9a-f]*'),
    size_bytes INTEGER NOT NULL CHECK(size_bytes >= 0),
    kind TEXT NOT NULL CHECK(kind = 'image'),
    role TEXT NOT NULL,
    PRIMARY KEY(batch_id, proposed_question_id, image_order),
    FOREIGN KEY(batch_ordinal, batch_id, proposed_question_id)
        REFERENCES task14_v124_candidates_v1(
            batch_ordinal, batch_id, proposed_question_id
        )
)""",
    """CREATE TABLE task14_v124_taxonomy_v1 (
    batch_ordinal INTEGER NOT NULL CHECK(batch_ordinal >= 1),
    batch_id TEXT NOT NULL,
    taxonomy_kind TEXT NOT NULL CHECK(taxonomy_kind IN ('primary_type','tag')),
    value TEXT NOT NULL,
    sort_order INTEGER NOT NULL CHECK(sort_order >= 1),
    record_status TEXT NOT NULL CHECK(record_status = 'candidate'),
    PRIMARY KEY(batch_ordinal, batch_id, taxonomy_kind, value),
    UNIQUE(batch_ordinal, batch_id, taxonomy_kind, sort_order),
    FOREIGN KEY(batch_ordinal, batch_id)
        REFERENCES task14_v124_batch_ledger_v1(batch_ordinal, batch_id)
)""",
    """CREATE VIEW task14_candidate_questions_v124 AS
SELECT f.*
FROM formal_complete_questions_v123 AS f
UNION ALL
SELECT
    c.aggregate_order AS formal_order,
    c.proposed_question_id AS question_id,
    'task14_v124_candidate' AS authority_kind,
    c.batch_id AS batch_id,
    c.batch_candidate_order AS candidate_order,
    c.source_id,
    c.source_question_number,
    c.source_section,
    c.source_fragment_hash,
    c.normalized_text_sha256,
    c.question_text_original,
    c.question_text_zh,
    CAST(NULL AS TEXT) AS question_text_zh_reviewed,
    c.translation_status,
    c.translation_evidence,
    c.solution_original,
    c.solution_verified,
    c.answer_status,
    c.explanation_text,
    c.explanation_status,
    c.explanation_evidence,
    c.image_paths_json AS source_image_paths_json,
    c.image_sha256s_json AS source_image_sha256s_json,
    c.image_roles_json AS source_image_roles_json,
    c.primary_type,
    c.tags_json,
    c.tag_status,
    c.difficulty_level,
    c.difficulty_status,
    c.enrichment_status,
    c.candidate_image_paths_json AS formal_image_paths_json,
    c.record_status,
    c.selectable
FROM task14_v124_candidates_v1 AS c
ORDER BY formal_order""",
)


def _genesis_digest() -> str:
    """Reconstruct the fixed first-parent authority, never from artifacts."""
    projection = {
        "baseline_database_sha256": BASELINE_SHA256,
        "baseline_question_count": 677,
        "baseline_release_digest": BASELINE_RELEASE_DIGEST,
        "baseline_release_version": "V1.23", "candidate_count": 0,
        "schema": "task14-v124-genesis-v1", "target_release_version": "V1.24",
    }
    actual = sha256_bytes(canonical_json_file_bytes(projection))
    if actual != "797ed06ca5833bac060c1603cada38a6f2aa9eb080a40d9dc892bba9a549773a":
        raise InputFormatError("V1.24 genesis projection mismatch")
    return actual
