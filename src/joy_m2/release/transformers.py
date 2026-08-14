"""Deterministic V1.17 historical release transformation."""

from __future__ import annotations

from ..errors import PipelineError
from ..models import (
    AuditResult,
    PublicationEvidence,
    ReleaseCompatibility,
    V117ReleaseBatch,
    V117ReleaseDecision,
    V117ReleaseRecord,
)


def transform_v117_release(
    result: AuditResult,
    decision: V117ReleaseDecision,
) -> V117ReleaseBatch:
    """Replay the frozen V1.17 release decision over a passed audit result."""

    if type(result) is not AuditResult:
        raise PipelineError("result must be an AuditResult")
    audited_batch = result.require_passed()
    if type(decision) is not V117ReleaseDecision:
        raise PipelineError("decision must be a V117ReleaseDecision")
    if result.report.release_version != "V1.17":
        raise PipelineError("result must use the V1.17 audit profile")
    if not audited_batch.records:
        raise PipelineError("V1.17 release transformation requires audited records")
    if any(
        record.task4_compatibility is None
        or record.release_compatibility is not None
        for record in audited_batch.records
    ):
        raise PipelineError("V1.17 release transformation requires only V1.17 records")

    records = tuple(
        V117ReleaseRecord(
            audited_record=record,
            publication_evidence=PublicationEvidence(
                record_status=decision.record_status,
                joy_approval=decision.joy_approval,
                approved_at=decision.approved_at,
            ),
            release_compatibility=ReleaseCompatibility(
                formal_release_version=decision.formal_release_version,
                selectable=decision.selectable,
                source_order=source_order,
            ),
            schema_version=decision.schema_version,
        )
        for source_order, record in enumerate(audited_batch.records, start=1)
    )
    return V117ReleaseBatch(records=records)
