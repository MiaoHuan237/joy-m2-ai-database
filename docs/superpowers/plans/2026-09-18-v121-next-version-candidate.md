# V1.21 Next-Version Candidate Authority Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement a deterministic V1.21 multi-batch staging candidate lifecycle over immutable formal V1.20/543 and carry the already-approved 2015 HKDSE transcription to authoritative preflight.

**Architecture:** Add exact V1.21 public carriers and versioned canonical, preflight, writer, and verifier modules beside unchanged V1.20 modules. Build each candidate by copying formal V1.20 into private staging, adding only V1.21 candidate structures, independently verifying, and atomically publishing.

**Tech Stack:** Python 3.12, stdlib dataclasses/hashlib/json/pathlib/sqlite3/tempfile, existing PipelineConfig/evidence carriers, unittest.

**Spec:** `docs/superpowers/specs/2026-09-18-v121-next-version-candidate-design.md`

## Global constraints

- Formal V1.18/V1.19/V1.20 are immutable.
- Baseline is exactly V1.20/543, SQLite SHA `b3e4911259fbc4063e788f418f6e52a53017ff079895bce679837914a5539292`, release digest `1eb046cd247c362ab6b6052ca7fecddea914340dd7421bf136012a9a086c9fcf`.
- Target is exactly V1.21; no V1.22/generic framework.
- No production behavior before its valid RED.
- No `releases/V1.21/`, promotion, CLI, dependency, or project script.
- Reuse the approved 2015 transcription; do not rerun OCR or change text/MS.

### Task 1: Public carriers and strict manifest

**Files:**
- Create: `tests/unit/test_v121_models.py`
- Create: `src/joy_m2/ingest/v121_models.py`
- Create: `src/joy_m2/ingest/v121_manifest.py`
- Modify: `src/joy_m2/ingest/__init__.py`

**Interfaces:**
- Produces the 13 exact V1.21 dataclasses, `load_v121_import_manifest()`, and the exact fixed contract/genesis.

- [ ] Write tests for exact fields/order/types/no-default/frozen semantics, nested exact types, tuple copying, fixed literals, invalid envelopes, approval text, count closure, and deterministic non-V1.20 genesis.
- [ ] Run `python -m unittest -v tests.unit.test_v121_models`; require importable tests and feature-missing RED.
- [ ] Implement only carriers and strict loader.
- [ ] Re-run focused tests to GREEN and run `tests.unit.test_v120_models` unchanged.
- [ ] Commit exact Task 1 files.

### Task 2: Approved HKDSE transcription to V1.21 canonical package

**Files:**
- Create: `tests/integration/test_v121_hkdse_bridge.py`
- Modify: `src/joy_m2/ingest/hkdse_pdf_adapter.py`
- Modify: `src/joy_m2/ingest/__init__.py`

**Interfaces:**
- Produces `adapt_verified_hkdse_pdf_transcription_v121(...) -> V121AdaptedImportPackage`.

- [ ] Write tests locking verified-only input, exact V1.21 manifest, five-file layout, candidate/source/MS byte preservation, path independence, atomic no-replace behavior, and unchanged V1.20 bridge bytes.
- [ ] Run bridge tests and require behavior RED before production modification.
- [ ] Implement the narrow V1.21 bridge using existing source-preserving payload helpers.
- [ ] Run V1.21 bridge and full Task 10B suites to GREEN.
- [ ] Commit exact Task 2 files.

### Task 3: Read-only authoritative V1.21 preflight

**Files:**
- Create: `tests/integration/test_v121_preflight.py`
- Create: `src/joy_m2/ingest/v121_preflight.py`

**Interfaces:**
- Produces `preflight_v121_import(request, config) -> V121ImportPreflightResult`.

- [ ] Write RED tests for exact V1.20 baseline identity/count/view, wrong SHA/size/schema/count rejection, deterministic genesis, canonical package binding, existing sixteen-code collision taxonomy, duplicate against formal V1.20, parent-candidate duplicate, first/second batch count closure, and zero writes.
- [ ] Run focused tests and require behavior RED.
- [ ] Implement minimum read-only package loading, V1.20 indexing, parent verification/state extension, classification, report, and digest.
- [ ] Re-run focused tests to GREEN and confirm V1.20 preflight replay unchanged.
- [ ] Commit exact Task 3 files.

### Task 4: Approval, writer, and independent verifier

**Files:**
- Create: `tests/integration/test_v121_candidate.py`
- Create: `src/joy_m2/ingest/v121_writer_profiles.py`
- Create: `src/joy_m2/ingest/v121_writer.py`
- Create: `src/joy_m2/ingest/v121_verification.py`
- Modify: `src/joy_m2/ingest/__init__.py`

**Interfaces:**
- Produces `approve_v121_import`, `build_v121_candidate`, and `verify_v121_candidate`.

- [ ] Write RED tests for exact approval, stale preflight and approval rejection, first and second generation, full-prefix rebuild, failed append parent preservation, deterministic roots, exact artifact/SHA/rollback closure, V1.20 prefix preservation, and no formal V1.21 path.
- [ ] Run focused tests and require behavior RED.
- [ ] Implement fixed V1.21 DDL/profile constants, approval closure, private-root builder, deterministic SQLite normalization, atomic publication, and independent verifier.
- [ ] Re-run focused tests to GREEN; independently replay two equivalent roots.
- [ ] Commit exact Task 4 files.

### Task 5: Historical replay, regression, review, and documentation

**Files:**
- Create: `tests/regression/test_v121_historical_replay.py`
- Create: `docs/reports/V121_CANDIDATE_AUTHORITY_VERIFICATION.md`
- Modify: `PROJECT_STATE.md`

**Interfaces:**
- Proves V1.19/V1.20 history and all formal releases remain unchanged.

- [ ] Write and run historical replay tests for V1.20 manifest/preflight/approval/candidate identity and absence of `releases/V1.21/`.
- [ ] Run all V1.21 focused tests and the explicit maintained suite with zero skip/expected failure.
- [ ] Run Task 9A, 9B, 9C, 9D, 10A, 10B, 10C, V1.18 validator, V1.19 verifier, and V1.20 formal verifier.
- [ ] Re-hash and recount V1.18/497, V1.19/502, V1.20/543.
- [ ] Perform independent line-by-line review; remediate every Critical/Important finding with RED then GREEN.
- [ ] Record exact commands/counts/hashes in the verification report and synchronize PROJECT_STATE.
- [ ] Run `git diff --check`, commit docs/regression closure, and ordinary push.

### Task 6: First real 2015 operational preflight

**Files:**
- Ignored output only: `data/staging/task11-v121-hkdse-2015/**`

**Interfaces:**
- Consumes the exact approved transcription digest `41e284c25e41759f72debd192e58c00288d14a355e704978d80587c201e970fc`.
- Produces a V1.21 canonical package and authoritative preflight against genesis.

- [ ] Reconstruct and validate the exact transcription approval without OCR or content changes.
- [ ] If taxonomy is non-canonical, perform taxonomy-only remediation and stop at the existing approval gate if its digest changes.
- [ ] Generate the V1.21 package twice in independent roots and require byte identity.
- [ ] Run preflight twice against exact formal V1.20 and genesis; require identical result/digest.
- [ ] Re-verify formal V1.18/V1.19/V1.20 hashes/counts and all focused gates.
- [ ] If READY, report exact metrics and stop at `USER DECISION REQUIRED — REAL BATCH IMPORT`; do not approve, write candidate, or promote.

