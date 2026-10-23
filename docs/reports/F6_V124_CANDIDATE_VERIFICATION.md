# V1.24 shared candidate dependency — scoped verification

2026-10-23. Native/Inline, under the approved F6/V1.24 Design and Plan and the
chapter12 execution authorization. This report covers the shared version layer
only: Plan Tasks1,2,5,6A,6B,7,8 and the focused/review portion of9. F6 source
Tasks3/4 and real F6 operations10/11 are not performed or claimed complete.

Formal baseline V1.23 remains677 records. SQLite SHA256
`28e44bda233b7d6acdb96a4fecf46df4cb75a50730694e0b249e9d38d3a584cd`;
manifest SHA256 `54d192436e761c9bfe810510b77a902c5ae659bebdfbc4da8475aac271be8498`;
release digest `84ebbd9d9f0d5fbef97f20ae98f8cdfa16c55d56eac7a826cfde3cc47fe9a2fc`.
V1.24 genesis is `797ed06ca5833bac060c1603cada38a6f2aa9eb080a40d9dc892bba9a549773a`.
No real V1.24 candidate or release has been built.

## Executable dependency

Six fixed sibling modules are implemented: models, strict manifest loader,
writer_profiles, effective-state preflight, atomic writer and independent verifier.
Commits3962bc5→73ba362 implement the ordered first/parent/multi-batch stages.
Only version-neutral helpers are reused; historical modules and root exports are
unchanged. Test-owned literal SQL/JSON builds an independent first-generation
oracle before testing the production builder. Synthetic source approvals use
TASK10-A/B/C only, never actual source batch identities.

Fresh command (PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:., configured Python -B):

```text
-m unittest -q tests.unit.test_v124_models tests.integration.test_v124_preflight tests.integration.test_v124_candidate tests.regression.test_v124_historical_replay
Ran124 tests in105.975s — OK; no skip or expected failure.
```

The historical replay module checks frozen releases, actual historical V1.23
receipt verification and no-publication boundary read-only. Genuine first and
verified-parent preflight/writer/verifier are available for chapter C synthetic
integration. Full maintained regression is intentionally deferred to the single
combined chapter engineering exit, not represented by this focused result.

## Independent implementation review

Separate read-only reviewer `/root/v124_shared_dependency_review` inspected the
approved contracts, six-file diff, test-owned oracle, and synthetic fault paths.
Initial review: C0/I2/M1. Both Important findings were independently reproduced:
forged READY bypassing multi-reference ambiguity and unknown taxonomy. Four
behavioral negative tests failed before fixes and passed after independent
writer/verifier closure checks. A valid three-record shared-image control and
next-batch multi-owner rejection preserve the original classification semantics.
Post-verification source/private changes and late destination race are now tested.

Final separate re-review: Critical0 / Important0 / openMinor0. Reviewer directly
ran the saved shared-image control and other focused hostile cases, without
builder-generated expected output. Earlier fixture mistakes (manifest whitespace
and derived image SHA field) were corrected in tests, not by weakening contracts.

Reviewer declined whole-task/full-suite certification, complete historical TDD
replay, Chapter/F6 source authority and real receipt/lock operations. Main ruling:
these are not claimed by this report; combined regression and chapter review
remain mandatory before real chapter proposal delivery. No actual writer use,
F6 import, source approval, promotion or scheduler change is authorized here.

User AGENTS bytes remain SHA256
`75ffa9680b18a0875fde8d36a8ca3e0ebda0603f10e8dc788e71ea8353d0311d`.
Ignored ledgers retain task RED/GREEN evidence. Local commits are not a backup
of ignored source/candidate data; remote synchronization not yet attempted in
this execution.
