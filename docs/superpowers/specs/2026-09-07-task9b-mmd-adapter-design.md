# Joy M2 AI Database — Task 9B Mathpix MMD Adapter Design

Project: Joy M2 AI Database
Task: Task 9B — Mathpix MMD / MMD.ZIP Source Adapter
Status: EXECUTABLE DESIGN AUTHORITY
Architecture: APPROVED
Executable authority: APPROVED
Implementation: NOT STARTED
Task 9A: CLOSED / PASS
Task 9C writer: OUT OF SCOPE
PDF: DEFERRED

## 1. Purpose and invariant

Task 9B converts one explicitly selected Mathpix MMD or MMD.ZIP source into a
deterministic canonical staging package that the frozen Task 9A preflight can
consume without knowing how that package was produced. A canonical package
created from handwritten JSON, MMD, or MMD.ZIP has the same Task 9A contract.

Task 9B produces staging evidence only. It does not approve an import, write a
database row, create V1.19, promote a release, or modify V1.18. Task 9A remains
the sole read-only preflight and duplicate/collision authority. A future Task
9C may write a V1.19 candidate only under separately approved user authority.

The architecture is:

```text
B1: safe source inventory + explicit selection
  ->
B2: deterministic Mathpix extraction -> private immutable Source IR
  ->
B3: explicit selection metadata -> canonical Task 9A package
  ->
existing Task 9A preflight_import(...)
```

Direct parser-to-database, parser-to-release, and parser-to-preflight flows
that skip the canonical package boundary are forbidden.

## 2. Public API and carriers

The only public adapter function is:

```python
def adapt_mmd_package(
    selection_manifest_path: Path,
    source_path: Path,
    output_dir: Path,
    config: PipelineConfig,
) -> AdaptedImportPackage:
    ...
```

The four parameters, their order, and the return type are exact. There is no
second answer-package input and no implicit source-root discovery.

### 2.1 `MmdSelection`

```python
@dataclass(frozen=True)
class MmdSelection:
    proposed_question_id: str
    kind: str
    number: str
    source_section: str
    language_layout: str
    answer_mapping: str
    answer_number: str | None
    expected_image_members: tuple[str, ...]
    primary_type: str
    tags: tuple[str, ...]
    tag_status: str
    difficulty_level: int | None
    difficulty_status: str
```

All non-optional strings are exact, non-empty `str` values. `kind` is exactly
`example | exercise`. `language_layout` is exactly
`english_then_chinese | interleaved_bilingual`. `answer_mapping` is exactly
`source_answer | missing_from_source`. `expected_image_members` and `tags`
accept only list/tuple input and are defensively canonicalized to tuples while
preserving declared semantic order. Image members are canonical package-root-
independent POSIX paths; absolute paths, dot segments, backslashes, empty
components, duplicate values, and suffixes other than exact lowercase `.jpg`,
`.jpeg`, or `.png` are invalid.

`tag_status` and `difficulty_status` reuse the frozen Task 9A values
`source_provided | proposed | missing`. Missing tags require an empty tuple;
non-missing tags require at least one non-empty string. Missing difficulty
requires `difficulty_level=None`; otherwise the level is an exact non-boolean
integer from 1 through 5. `primary_type` is explicit selection metadata and is
never inferred from the source text by the adapter.

Answer rules are:

- `source_answer` with `answer_number=None` selects the unique question-local
  solution in the primary MMD.
- `source_answer` with a non-empty `answer_number` requires a manifest-level
  `answer_member`; that number must match exactly one answer occurrence there.
- `missing_from_source` requires `answer_number=None`, empty solution fields,
  and Task 9A `answer_status="missing_from_source"`.
- A missing `answer_member` makes every non-empty `answer_number` invalid.

The selection does not determine explanation provenance. Answer and
explanation are independently parsed and represented.

### 2.2 `MmdAdapterManifest`

```python
@dataclass(frozen=True)
class MmdAdapterManifest:
    schema_version: str
    batch_id: str
    source_kind: str
    source_sha256: str
    primary_member: str
    answer_member: str | None
    source_id: str
    chapter: str
    expected_candidate_count: int
    selections: tuple[MmdSelection, ...]
```

`schema_version` is exactly `task9b-mmd-adapter-v1`. `source_kind` is exactly
`mmd | mmd_zip`. `source_sha256` is lowercase 64-character hexadecimal.
`batch_id`, `source_id`, and `chapter` are exact non-empty strings. The primary
and optional answer member use canonical NFC POSIX spelling and may not be
equal; each has the exact lowercase `.mmd` suffix. For plain MMD,
`primary_member` is the source filename and
`answer_member` must be `None`; resources resolve beneath `source_path.parent`.
For MMD.ZIP, both member names resolve from archive root. V1 permits at most
one answer member in the same archive and does not accept an independent
answer archive or arbitrary additional resource root.

`expected_candidate_count` is an exact non-boolean non-negative integer and
must equal `len(selections)`. `selections` accepts only list/tuple input,
canonicalizes to an independent tuple, and must contain exact `MmdSelection`
instances. Proposed IDs are unique. Their tuple order is the candidate semantic
order and may not be replaced by source discovery or filesystem order.

### 2.3 Selection-manifest file and decoding authority

`selection_manifest_path` names one strict UTF-8 JSON file. The file is neither
YAML, TOML, Markdown, nor pickle. Encoding guessing is forbidden, and a UTF-8
BOM is rejected. Its top level must be a JSON object whose exact key set is:

```text
schema_version, batch_id, source_kind, source_sha256, primary_member,
answer_member, source_id, chapter, expected_candidate_count, selections
```

Each `selections` array element must be a JSON object whose exact key set is:

```text
proposed_question_id, kind, number, source_section, language_layout,
answer_mapping, answer_number, expected_image_members, primary_type, tags,
tag_status, difficulty_level, difficulty_status
```

JSON arrays represent all tuple fields: top-level `selections` and each
selection's `expected_image_members` and `tags`. Missing and extra keys are
invalid. Physical JSON-object key order is not semantic authority: after exact
key-set validation, conversion follows the declared dataclass field order.
Array order is semantic and is preserved exactly.

Duplicate keys at any object depth are invalid. Decoding must use
`object_pairs_hook` or an equivalent pair-preserving mechanism and detect a
duplicate before constructing an ordinary mapping; last-value-wins decoding is
forbidden. The exact conversion boundary is:

```text
file bytes
  -> strict UTF-8 decode without BOM
  -> duplicate-key-aware JSON decode
  -> exact key-set and JSON runtime-type validation
  -> typed MmdAdapterManifest / MmdSelection conversion
  -> carrier and cross-field validation
  -> B1 source/archive processing
```

D0 ends after the typed carriers and every source-free invariant have been
validated. It may inspect the selection-manifest path and bytes, API argument
runtime types, the lexical `source_path.name` value without stat/resolve/open,
and configuration facts requiring no source content. It must not access source
filesystem state, read a ZIP member, parse MMD, compare the declared kind with
the actual artifact, or calculate the actual source digest. Only after D0 passes
may D1 access `source_path`, determine its actual kind, calculate its raw
SHA-256, and begin source/archive metadata validation. A D0 blocker therefore
prevents every source access.

Within selection-manifest decoding, a missing `selection_manifest_path` raises
`InputMissingError`. An existing non-regular path is `wrong_type` with expected
`regular_file`; an existing file that cannot be read is `invalid_value` with
expected `readable`.
Invalid UTF-8, BOM, invalid JSON syntax, a duplicate key, non-object top level,
missing/extra key, wrong JSON runtime type, invalid enum/value, or invalid
cross-field invariant produces `MmdAdapterBlockedError` with exactly one or
more `source_contract_mismatch` issues according to section 11. No default,
coercion, recovery parser, or best-effort conversion is permitted.

The semantic selection-manifest projection used by section 3 contains every
successfully typed field except `source_sha256`. It follows dataclass field
order and preserves the declared `selections`, `expected_image_members`, and
`tags` array orders; physical JSON-object key order remains excluded.

### 2.4 `AdaptedImportPackage`

```python
@dataclass(frozen=True)
class AdaptedImportPackage:
    package_root: Path
    manifest_path: Path
    manifest: BatchImportManifest
```

The carrier has exactly these fields. `package_root` and `manifest_path` are
`Path` instances, `manifest` is an exact frozen Task 9A
`BatchImportManifest`, and `manifest_path` equals
`package_root / "import_manifest.json"`. Runtime absolute paths exist only in
this return carrier for the caller to locate staging output; they never enter
canonical JSON, evidence, diagnostics, hashes, or approval identity.

### 2.5 Adapter diagnostics

```python
@dataclass(frozen=True)
class MmdAdapterIssue:
    code: str
    severity: str
    proposed_question_id: str | None
    source_locator: str
    field: str
    evidence: str
```

V1 severity is exactly `blocking`. Package-wide diagnostics use
`proposed_question_id=None`. Their `source_locator` is empty unless the matrix
in section 11 explicitly permits a safe canonical member byte interval for a
D3 lexical or parser diagnostic. Candidate-bound diagnostics use the exact
proposed ID.
Occurrence locators use:

```text
<canonical-member-path>#bytes=<start>:<end>
```

`evidence` is a canonical JSON object encoded as a string with UTF-8,
`ensure_ascii=False`, sorted object keys, compact separators, and
`allow_nan=False`. It contains no absolute path, cwd, temporary root, memory
identity, or runtime/session identifier.

```python
class MmdAdapterBlockedError(InputFormatError):
    issues: tuple[MmdAdapterIssue, ...]
```

The exception receives exact issues, stores an independent tuple in canonical
order, and uses a fixed non-data-bearing message. Its issue tuple is the
structured caller-visible failure envelope.

## 3. Input identity and deterministic authority

For MMD.ZIP, `source_sha256` is SHA-256 over the raw outer ZIP bytes. For plain
MMD it is SHA-256 over the raw MMD bytes. It validates that the selected input
is the expected artifact, but the outer archive digest is not semantic
authority. It is excluded from the source map, Task 9A manifest, Task 9A
preflight digest, and canonical package bytes.

The semantic selection-manifest projection contains every manifest field
except `source_sha256`, preserving the selection tuple order. Canonical
identity is based only on selected primary/answer member bytes, selected image
bytes, and this semantic projection (which contains the explicit metadata).
Repacking an otherwise identical ZIP with different physical member order or
container metadata changes input-validation SHA but not canonical output.

The following must produce byte-identical output:

```text
same logical selected member bytes
+ same semantic selection projection
```

Timestamps, random identifiers, temp roots, absolute paths, filesystem order,
ZIP physical order, and outer ZIP SHA are excluded.

## 4. Safe inventory and source handling

Task 9B performs metadata safety validation before any content read, bounded
integrity streaming before semantic parse/staging, and selective semantic
read/staging only after integrity succeeds. It never calls `extractall()` and
never extracts first and checks later.

After D0 passes, D1 applies the source-path input gate before classifying
content. A missing `source_path` raises `InputMissingError`; an existing
non-regular or unreadable source raises `InputFormatError`. Neither case emits
an `MmdAdapterIssue`. D0 never performs these filesystem checks or opens the
source. D1 then reads the top-level bytes and determines actual source kind by
this exact sequence:

1. `zipfile.is_zipfile(source_path)` true establishes actual `mmd_zip` identity
   and permits central-directory inventory. The outer filename suffix is not
   consulted.
2. Otherwise, raw bytes beginning with exact `b"PK"` are ZIP-shaped but not a
   structurally valid ZIP. They emit only D1 `archive_integrity_invalid` with
   reason `zip_structure`; declared-kind comparison is not also emitted for
   that fact.
3. Otherwise, raw bytes beginning with exact `b"%PDF-"` are the one recognized
   unsupported V1 top-level format and emit only D1
   `unsupported_source_format` with actual `pdf`. They are not treated as a
   declared-kind mismatch.
4. All other non-ZIP bytes are an actual plain-MMD candidate. Strict UTF-8 and
   MMD grammar remain D3 checks; invalid UTF-8 is not reclassified as an
   unsupported top-level format.

The resulting kind/structure decision is total:

| D1 observation | Declared kind | Single kind/structure outcome |
| --- | --- | --- |
| structurally valid ZIP | `mmd_zip` | continue ZIP inventory |
| structurally valid ZIP | `mmd` | `source_contract_mismatch` |
| non-ZIP, non-PDF bytes | `mmd` | continue as plain-MMD candidate |
| non-ZIP, non-PDF bytes | `mmd_zip` | `source_contract_mismatch` |
| false ZIP probe plus `b"PK"` prefix | either | `archive_integrity_invalid` |
| exact `b"%PDF-"` prefix | either | `unsupported_source_format` |

An approved actual `mmd` or `mmd_zip` kind that differs from declared
`source_kind` emits only `source_contract_mismatch` for that kind fact, with
reason `declared_source_kind_mismatch`. A raw `source_sha256` mismatch remains
an independently determinable D1 `source_contract_mismatch` with reason
`source_digest_mismatch`. D0 owns all suffix facts: the declared primary and
optional answer member must have the exact approved `.mmd` suffix, and for
declared plain MMD the lexical `primary_member` must equal `source_path.name`.
D1 never emits a second suffix issue, and no outer suffix overrides byte/
container identity.

### 4.1 Resource limits

All sizes use binary MiB and limits are inclusive:

| Authority | Limit |
| --- | ---: |
| Raw ZIP archive | 50 MiB |
| Member count | 256 |
| Total uncompressed bytes | 100 MiB |
| Generic regular member | 20 MiB |
| MMD member | 10 MiB |
| Image member | 20 MiB |
| Compression ratio | 100:1 |
| Allowed methods | STORED, DEFLATED |

The generic member limit is checked first and the type-specific limit second;
the stricter applicable value wins. Thus MMD is capped at 10 MiB and images at
20 MiB. Compression ratio is exactly
`uncompressed_size / max(compressed_size, 1)` and must be at most 100. Every
member, including ignored OS metadata, counts toward member count, total
uncompressed bytes, and ratio safety. Plain MMD is capped at 10 MiB; explicitly
selected adjacent images use the image and total limits.

### 4.2 ZIP/file matrix

| Entry | Decision |
| --- | --- |
| Directory | ALLOW for inventory only |
| Selected supported regular file | ALLOW after all validation |
| Symlink | REJECT |
| Device, FIFO, socket, or other special file | REJECT |
| Regular file with any Unix executable bit | REJECT |
| Nested archive | REJECT |
| Encrypted member | REJECT |
| Corrupt member or CRC | REJECT |
| Unsupported compression | REJECT |
| `__MACOSX/**` | IGNORE after safety validation |
| basename `.DS_Store` | IGNORE after safety validation |
| basename `._*` | IGNORE after safety validation |
| Any other hidden path component | REJECT |
| Unselected normal image | ALLOW inventory, IGNORE staging |
| Unselected second MMD | REJECT |

Ignored metadata is ignored only after path safety, collision detection,
regular non-executable type, encryption/compression, CRC, and all resource
limits pass. Unsafe metadata entries are rejected rather than hidden.

### 4.3 Three-phase ZIP read sequence

**B1-A — metadata preflight.** The adapter reads only the central directory and
metadata required to inventory every entry. It validates path spelling and
normalization, raw/NFC/casefold collisions, file type, executable bits,
encryption flag, compression method, declared compressed/uncompressed sizes,
member count, total declared uncompressed size, compression ratio, and nested
archive name/type authority. After those safety facts establish a canonical
inventory, B1-A verifies that the declared `primary_member` and every non-`None`
`answer_member` each exist exactly once as the selected canonical member. A
missing selected member emits D1 `selection_not_unique` under the exact section
11 package binding; it is not archive corruption and is never deferred to D4.
For V1, a regular member whose NFC basename
casefolds to a string ending in `.zip` is exactly a nested archive and is
classified before selected-member format checks. B1-A performs no semantic
parse and reads no member content. If this phase has blocking issues, it emits
all independently determinable B1-A issues in canonical order and stops before
CRC streaming.

**B1-B — bounded integrity streaming.** Only after B1-A passes, the adapter
opens and streams every regular member through the ZIP implementation to EOF,
including selected members, unselected ordinary images, and OS metadata that
will later be ignored. The stream is bounded by the declared and observed
member, total-uncompressed, ratio, and compression limits. This read exists
only to validate decompression and CRC; it is not semantic parsing, extraction,
or staging. A CRC/decompression/corrupt-stream failure emits
`archive_integrity_invalid`; after all safely determinable B1-B failures are
collected and sorted, processing stops before parsing or staging.

**B1-C — selective semantic read/stage.** Only after every B1-B stream passes
may the adapter retain/read for meaning the selected primary MMD, optional
selected answer MMD, and selected image bytes. OS metadata is then ignored.
Unselected ordinary images remain inventory-only and are not staged. No other
member is parsed or copied.

Thus “ignore” never means “skip integrity validation”: OS metadata and
unselected ordinary images pass B1-A and B1-B, then are omitted by B1-C. Plain
MMD input has no archive CRC phase but remains subject to its exact path, size,
digest, and UTF-8/parser gates.

### 4.4 Cross-platform paths

Backslashes, absolute paths, drive/UNC forms, parent traversal, empty/dot
segments, and normalized escape are rejected. Inventory derives an NFC POSIX
path for comparison and output while retaining the raw ZIP name privately for
member access. Two raw names that collide by NFC normalization or Unicode
casefold are rejected, as are duplicate raw member names. All emitted paths use
NFC POSIX spelling. No host directory enumeration order is authoritative.

For plain MMD, only the explicit primary file and exact referenced/selected
resources beneath `source_path.parent` are considered. The adapter does not
recursively discover arbitrary neighbouring files.

## 5. Private immutable Source IR

The IR is a private implementation contract, not public API and not a generic
Markdown AST:

```python
@dataclass(frozen=True)
class _SourceMember:
    relative_path: str
    sha256: str
    content: bytes

@dataclass(frozen=True)
class _SourceSpan:
    member_path: str
    start_byte: int
    end_byte: int
    role: str
    language: str

@dataclass(frozen=True)
class _SourceImageRef:
    source_order: int
    token_span: _SourceSpan
    raw_target: str
    resolved_member: str | None

@dataclass(frozen=True)
class _SourceQuestion:
    source_order: int
    source_question_number: str
    source_section: str
    fragment_span: _SourceSpan
    text_spans: tuple[_SourceSpan, ...]
    solution_spans: tuple[_SourceSpan, ...]
    explanation_spans: tuple[_SourceSpan, ...]
    image_refs: tuple[_SourceImageRef, ...]

@dataclass(frozen=True)
class _SourceDocument:
    primary_member: str
    members: tuple[_SourceMember, ...]
    questions: tuple[_SourceQuestion, ...]
```

Members are ordered by canonical POSIX path; questions by semantic source
order; spans and image references by occurrence order. Question `source_order`
is the zero-based contiguous index of the complete top-level question
occurrence in the primary MMD before manifest selection or reordering. An image
reference's `source_order` is its zero-based contiguous index among image-token
occurrences inside that question. Both fields are exact non-boolean integers.
Question arrays still follow manifest semantic order, so their carried
`source_order` values need not be increasing after an intentional manifest
reorder. Every span is the
half-open byte interval `[start_byte, end_byte)` in the original UTF-8 member
bytes. Span role is exactly `question | solution | explanation | image_token`;
language is exactly `en | zh | shared | und`. Offsets are exact non-boolean
non-negative integers with `start_byte < end_byte <= len(member.content)`.
Spans must resolve to a declared member and remain inside it.

An image reference whose target syntax and resource-root normalization are
valid but whose source member is absent is representable rather than an adapter
failure. Its `resolved_member` is `None`; the deterministic expected canonical
path is still derived from the normalized `raw_target`. A non-`None`
`resolved_member` must be the unique canonical source member selected by that
target. Missing bytes never create a `_SourceMember` and never receive a
fabricated digest.

The IR contains source truth only. Proposed IDs, tags, difficulty, AI content,
database identity, runtime paths, and release decisions do not belong in it.

## 6. Parser and complete-question grammar

V1 uses a fixture-driven deterministic line/state machine for only the
observed, approved Mathpix subset. It does not introduce a Markdown AST or
claim arbitrary Markdown support. Unknown or ambiguous syntax produces a
structured adapter blocker; it is never guessed silently.

The representative grammar recognizes:

- example marker lines matching exactly `例題` or `例题`, zero or one ASCII
  space, then the ASCII token `1` through `11`, with no other bytes;
- the exact exercise section marker line `應試練習`, followed by Q markers
  at line start matching `Q1）` through `Q6）` or `\\item[Q1）]` through
  `\\item[Q6）]`; a marker is followed either by the line terminator or by
  exactly one ASCII space and non-empty question prose on that same line;
- solution marker lines matching exactly `題解：` or `題解 ：`;
- a lexically complete Mathpix image envelope `![](<raw_target>)`; it becomes
  an approved image token only when `<raw_target>` passes the exact section 8
  target-safety and path grammar;
- nested `itemize`/`\\item` subparts, marks, bilingual blocks, and displayed
  LaTeX as content inside the current complete question.

Marker matching is performed on the decoded physical line after removing only
its line terminator; no surrounding whitespace, case, Unicode digit, or
punctuation normalization is allowed. An exercise marker is the exact prefix,
not the following same-line prose. The canonical
`source_question_number` is the captured ASCII integer (`"1"` ... `"11"`) for
an example and the exact token (`"Q1"` ... `"Q6"`) for an exercise. Selection
`number` and non-`None` `answer_number` compare to that canonical token, never
to a raw marker line. There is no case-folding, Unicode-numeric conversion, or
punctuation heuristic.

The primary occurrence's `source_section` is source-derived by one exact state
machine. Its exercise-section state starts as `NO_ACTIVE_SECTION`. An exact
top-level `應試練習` marker sets the state to `應試練習`; a repeated exact marker
resets it to the same single state. The next top-level example marker clears
that exercise scope, and EOF ends it. V1 recognizes no other top-level section
heading or transition: other lines neither create nor clear section state, and
there is no fuzzy synonym, generic Markdown-heading, filename, or chapter
fallback.

For an example, `source_section` is the marker keyword exactly as present in
source, either `例題` or `例题`, excluding the optional ASCII space and number;
the source spelling is preserved rather than normalized. An exercise Q marker
is valid only while the exact `應試練習` state is active, and its
`source_section` is that value. A Q marker in `NO_ACTIVE_SECTION` emits only D3
`mmd_parse_failed` with reason `missing_section`. If the parser cannot assign
exactly one section under these disjoint rules, it emits only D3
`mmd_parse_failed` with reason `ambiguous_section`; D4-D7 do not run. A uniquely
parsed occurrence whose selection declares a different `source_section` emits
D4 `source_contract_mismatch` with reason `source_occurrence_mismatch`.

The derived value is stored once on `_SourceQuestion` and then copied unchanged
to selection validation, `source/source-map.json`, the raw Task 9A candidate,
and every section-bearing locator/evidence projection. No later layer
recomputes it.

An example begins at its example marker. An exercise begins at its Q marker.
The next top-level example/exercise marker ends the current occurrence. A
same-member solution marker ends the question fragment immediately before the
marker and starts its answer body immediately after the marker line terminator;
the body ends immediately before the next top-level question marker or EOF.
The solution marker and answer body are excluded from `fragment_span`,
`question_text_original`, and `source_fragment_hash`. A second solution marker
inside one occurrence, or a source answer requested where no unique local
solution body exists, is `selection_not_unique`. The representative exercise
section has no source answers. Every `(a)/(b)/(c)/(i)/(ii)` subpart remains
inside its parent question.

For a separate `answer_member`, V1 recognizes an answer occurrence only as an
exact marker-only top-level example/exercise line from the grammar above,
followed by zero or more empty lines and then exactly one approved solution marker. Its
body begins after that solution marker and ends immediately before the next
top-level answer marker or EOF. The marker's canonical token is the occurrence
answer number. The selection's `answer_number` must equal exactly one such
token: zero or more than one match emits `selection_not_unique`. Other answer
heading spellings are unsupported grammar rather than guessed aliases.

The representative fixture exposes no independent source-explanation marker.
Consequently the V1 approved explanation-marker grammar is the empty set: the
entire non-empty answer body is `solution_spans`, and
`explanation_spans=()`. The same bytes are never double-labelled as solution
and explanation, and length or discursive wording never changes that rule. A
future explanation marker requires a separately reviewed Design revision.

`solution_original` concatenates its source-ordered solution spans after only
CRLF/CR-to-LF normalization. It does not include the top-level question marker
or the `題解` marker, does not trim boundary whitespace, and does not rewrite
LaTeX. An empty body is not a source answer and cannot produce
`answer_status="source_provided"`.

The selection manifest binds occurrences without using selection-array
position, filesystem order, runtime path, or proposed question ID. For each
selection, D4 first forms the set of parsed primary occurrences whose
`kind`, canonical `number`, and source-derived `source_section` all match
exactly. One exact match binds; more than one emits
`selection_not_unique/question_occurrence` with that exact match count.

When there is no exact match, `source_occurrence_mismatch` is reachable only by
this deterministic one-field counterfactual rule: consider occurrences that
match exactly two of those three fields and differ in exactly the remaining
field. If the union contains exactly one occurrence and exactly one field is
different, that occurrence is independently unique and D4 emits the one
`source_contract_mismatch` for the differing field. If the union is empty,
contains more than one occurrence, or no single differing field is unique,
D4 emits `selection_not_unique/question_occurrence` with `match_count=0` and
does not guess an occurrence. A source with zero parsed questions is therefore
an unambiguous zero-match case. Parser order never supplies the missing
identity and never overrides manifest semantic order; after binding, output
candidate order is the manifest selection tuple order.

## 7. Rendering, fragment identity, and provenance

### 7.1 Original and Chinese text

The V1 bilingual lexer is evidence-bound to the representative source and the
two approved `language_layout` values. It is not a general Unicode-language or
Markdown detector. It first recognizes the following atomic constructs before
classifying prose:

- a complete inline Mathpix token begins at an unescaped ASCII `$` that is not
  followed by `$` and ends at the next unescaped `$` on the same physical line;
  the delimiters and body form one `shared` span;
- a display block beginning on a line whose content is exactly `$$` and ending
  at the next line whose content is exactly `$$`, including both delimiters and
  intervening bytes, is one `shared` span;
- exact whole-line `\\begin{itemize}` / `\\end{itemize}` and the bracketed
  prefix of a `\\item[...]` line are structural `shared` spans; any following
  prose on that line is classified separately;
- a lexically complete image envelope is first checked by the section 8 target-
  safety rule; only a safe envelope matching `![](./images/<tail>)` becomes one
  `image_token` span with language `shared`, is not split by characters, and is
  also represented by `_SourceImageRef`;
- top-level question-marker prefixes, the `應試練習` marker, exact
  `參考`/`參考 DSE...` metadata lines, and a `DSE...` line immediately after a
  question marker or exact `參考` are structural `shared` spans. Prose after an
  exercise marker prefix is classified by the ordinary same-line rules.

LaTeX content, including variable names and Chinese text inside a recognized
math token, is never reclassified. Only a complete approved atomic construct
can become `shared` or `image_token`. An unclosed inline/display delimiter is
`mmd_parse_failed` with reason `unclosed_token`; a malformed atomic construct
or incomplete image token is `mmd_parse_failed` with reason
`unsupported_grammar`. These D3 parser blockers stop D4-D7, so the same bytes
can never become `und`, `language_mapping_ambiguous`, or an image-binding
diagnostic. After atomic constructs are removed from consideration, a
“Han onset” is precisely a decoded scalar in U+3400–U+4DBF, U+4E00–U+9FFF, or
U+F900–U+FAFF; a “Latin onset” is precisely ASCII `A`–`Z` or `a`–`z`. These
ranges are the fixed V1 boundary symbols observed in the source, not an
invitation to infer additional scripts.

Line entry and run ownership are exact:

- A physical line is processed left to right from its first byte after any
  structural prefix. Non-atomic ASCII horizontal whitespace before the first
  prose onset is `shared`. Once a prose run starts, every later non-atomic ASCII
  horizontal whitespace byte stays with the current prose language, including
  whitespace between language onsets, around an intervening atomic token, and
  immediately before the line terminator. If a line has no prose onset, its
  non-atomic whitespace is `shared`. An empty line, including its line
  terminator, is `shared`.
- Before a Han/Latin onset, digits and punctuation join the language chosen by
  that first onset. If no onset occurs outside atomic constructs, the remaining
  non-structural bytes are one `und` span.
- Once a prose run has a language, punctuation immediately following it stays
  with that run. Atomic shared constructs interrupt but do not reset the
  current prose language. A line terminator stays with the final non-image text
  span on that line. If the final construct is an image token and no later text
  span exists, the terminator is a separate `shared` text span; it is never
  absorbed into the image-token byte interval.
- On a line whose first prose onset is Latin, the first later Han onset outside
  an atomic construct is the sole same-line `en -> zh` boundary. Bytes through
  the spaces/punctuation preceding that Han scalar remain `en`; that Han scalar
  and all later prose bytes on the line are `zh`. Thus observed `and 及` splits
  as `en="and "`, `zh="及"`, and `Using the fact that 利用這事實` splits as
  `en="Using the fact that "`, `zh="利用這事實"`. A second direction change is
  not inferred; Latin letters after the Han onset remain part of the `zh` run.
- A line whose first prose onset is Han is `zh` for all its prose bytes; Latin
  symbols later on that Chinese line do not create an English run.

For `english_then_chinese`, the question starts in an `await_en` state after
the shared question/reference prefix. The first prose line must have a Latin
onset and enters `en`. The first later prose line with a Han onset, or the first
same-line Han boundary, irreversibly enters `zh`; all later prose lines must
have a Han onset and are `zh`. Missing either phase or encountering a new
Latin-onset prose line after the transition emits
`language_mapping_ambiguous`.

For `interleaved_bilingual`, each physical line enters independently and uses
the line/run rules above. At least one `en` and one `zh` span must exist, and a
Latin-onset line, Han-onset line, or the approved single `en -> zh` same-line
form is accepted in any source order. A non-structural `und` span or any
language transition outside those approved forms makes the mapping ambiguous.
Atomic grammar failures have already stopped at D3 and are not D6 language
failures. No third layout or fallback classifier exists.

Across the included renderable question-text region, source-ordered text spans
plus separately modeled image-token spans form a non-overlapping, byte-complete
partition. Every included source byte belongs to exactly one span; there are no
gaps at language transitions, no double-owned punctuation or whitespace, and
no discarded trailing whitespace. Bytes excluded by the question/solution
boundary are outside this partition. The same partition rule applies to both
approved layouts.

`question_text_original` is the complete question fragment rendered in source
order. The only transformation is CRLF or CR to LF. The adapter does not trim,
collapse whitespace, rewrite LaTeX, reorder bilingual spans, translate,
correct mathematics, summarize, or polish. Heading, number, subparts, marks,
and original image tokens remain. Solution, explanation, marking rubric, and
AI content are excluded.

`question_text_zh` traverses the source-ordered union of `text_spans` and image
token spans and selects `zh` plus `shared`. Contiguous selected spans concatenate
their exact newline-normalized bytes; exactly one LF joins selected regions
separated by an omitted `en` span. It neither creates a leading/trailing LF nor
duplicates an existing selected LF. Source characters, structural markup,
image tokens, and LaTeX wrappers remain unchanged. If no `zh` prose span is
present, the exact result is empty text, `translation_status="missing"`, and
`translation_evidence=None` even if shared spans exist. Otherwise status is
`source_present` and evidence is the stable locator covering the ordered `zh`
source spans. These rules uniquely determine `text_spans`, both renderings,
source-map spans, and their canonical bytes from the same source bytes and
declared layout.

### 7.2 Fragment digest and locator

`source_fragment_hash` is SHA-256 over the exact original UTF-8 bytes of the
question fragment. No newline or Unicode normalization occurs before hashing.
The fragment starts at the semantic question marker and ends immediately
before its solution marker, the next question marker, or EOF. It includes
heading, question number, full bilingual text, all subparts, marks, and image
tokens; it excludes solution, marking rubric, and AI content.

Locators use canonical member paths and byte offsets, never package roots:

```text
<canonical-member-path>#bytes=<start>:<end>
```

Task 9A source evidence uses its frozen wrapper:

```text
source:<canonical-package-relative-source-path>#<stable-locator>
```

### 7.3 Answer and explanation independence

`answer_mapping` selects source-answer availability only. A successful source
solution maps exact source text to `solution_original`, leaves
`solution_verified` empty, and emits `answer_status="source_provided"`.
Missing source answer leaves both solution fields empty and emits
`missing_from_source`. Task 9B never generates an AI answer and never imports
historical V1.18 AI solutions for the six exercises.

The V1 parser has no approved independent source-explanation marker, so its
current representative and separate-member answer bodies are solution-only.
It therefore emits empty `explanation_text`, `explanation_status="missing"`,
and `explanation_evidence=None`. If a future approved source grammar adds a
distinct explanation construct, only its non-overlapping source spans may emit
`source_present` with a stable source locator.

Task 9B V1 performs no AI generation or verification, and its exact public
manifest has no AI explanation or review input field. Its emission subset is
exactly `source_present | missing`; it cannot emit `ai_proposed` or `verified`.
Those two values remain valid frozen Task 9A vocabulary only for a future,
separately authorized post-adapter enrichment carrier. They are not current
adapter input or output-generation authority. The existence or length of a
solution never grants explanation authority.

### 7.4 Tags, difficulty, and enrichment

`primary_type`, tags, and difficulty come from explicit selection metadata.
`source_provided` is valid only when corresponding source evidence exists;
otherwise user/AI suggestions remain `proposed`. Missing values retain the
frozen missing representation.

Task 9B derives only the existing Task 9A enrichment vocabulary:

```python
complete = (
    translation_status != "missing"
    and explanation_status != "missing"
    and tag_status != "missing"
    and difficulty_status != "missing"
)
```

The status is `complete` when true and `incomplete` otherwise. Answer status is
reported independently and does not participate in this presence formula. In
Task 9B V1, explanation presence can be satisfied only by an approved distinct
source explanation; no unavailable AI/review payload may make it complete.

## 8. Image authority

Each present image binding is explicit: source image token -> selected source
member -> canonical output path. Raw bytes are copied byte-for-byte. Resize,
recompression, OCR, conversion, and byte rewriting are forbidden. A
syntactically valid reference whose normalized expected resource is absent has
`resolved_member=None`; it retains the deterministic canonical output path but
has no staged bytes or digest.

Image ordering is candidate semantic order followed by question-local source
reference order. The first occurrence establishes staging order. Reuse by
multiple questions stages one canonical file. Different source paths remain
different canonical paths even when bytes match, preserving Task 9A collision
authority. For the exact V1 token `![](./images/<tail>)`, `<tail>` must itself
be a non-empty safe canonical NFC POSIX relative path under `images/`. Remove
only the literal leading `./`; the source lookup member is
`images/<tail>` relative to the archive root or `source_path.parent`, and the
canonical package path is exactly:

```text
images/<tail>
```

No basename-only fallback, recursive search, percent-decoding, URL decoding,
or case correction occurs. `expected_image_members` contains this exact
`images/<tail>` source-member spelling. The same derivation produces
`canonical_path` whether or not that member exists.

Task 9B blocks ambiguous or unsafe resolution, but does not absorb Task 9A
facts that a canonical package can represent. Task 9A remains responsible for
`missing_image`, `orphan_image`, `collision_image_sha256`, and
`file_integrity_mismatch`.

For a valid absent source image, the raw Task 9A candidate still lists its
`canonical_path` in `image_paths` and the matching approved `question` role in
`image_roles`. The Task 9A `image_files` manifest group does not declare that
nonexistent path or a fabricated SHA. Task 9A therefore emits its frozen
`missing_image` issue. This is expected canonical representation, not a Task
9B blocker.

`image_binding_invalid` is limited to a path-safe reference whose semantic
binding cannot be formed uniquely: ambiguous reference mapping, conflict
between the selected member and explicit manifest binding, multiple matches,
inability to derive exactly one canonical expected path despite a safe target,
or invalid role/binding metadata. A syntactically valid but absent image is not
this code.

Archive member-name threats, nested archives, and unsafe member types are D1
`archive_member_unsafe` facts. A raw image target embedded in MMD cannot be
known during metadata-only D1. After D2 integrity succeeds, D3 performs the
earliest lexical target-safety check while recognizing a complete image
envelope, before question selection or image binding. The one literal leading
`./` in the approved `./images/<tail>` grammar is permitted and removed before
component checks; a dot component anywhere in `<tail>` is not permitted.

For each complete envelope, D3 applies this ordered, single-reason safety list:
Windows drive or UNC form, POSIX absolute form, backslash, `..` traversal
component, dot or empty tail component (including a leading/trailing separator),
normalization escape from `images/`, NFC collision, casefold collision, then any
remaining failure to form the approved NFC POSIX canonical path. The exact
reasons are respectively `image_target_drive_or_unc`, `image_target_absolute`,
`image_target_backslash`, `image_target_traversal`,
`image_target_dot_or_empty_component`, `image_target_normalized_escape`,
`image_target_nfc_collision`, `image_target_casefold_collision`, and
`image_target_canonicalization`. A target matching more than one threat emits
only the first reason in this list. Collision checks compare every complete
image target and the safe canonical archive/resource inventory before semantic
selection; physical discovery order is irrelevant. A NUL/control value is not
a new path category: when it prevents that exact canonical path, it uses the
final `image_target_canonicalization` reason.

A complete envelope with any such threat emits only D3
`archive_member_unsafe`; D4-D7 do not run. An incomplete image token, or a
complete envelope whose target is path-safe but does not match the exact
`./images/<tail>` grammar, is D3 `mmd_parse_failed` with reason
`unsupported_grammar`. A safe approved target with an absent member remains the
representable Task 9A `missing_image` case, while a safe present/expected target
with conflicting semantic binding belongs only to D7 `image_binding_invalid`.
D7 receives only a safe canonical target and never rechecks path threats.

## 9. Canonical source map

`source/source-map.json` is deterministic source-locator/mapping evidence. It
is not raw primary source or raw answer source and cannot replace either. It is
declared in Task 9A `source_files` with `kind="source"`, so it participates in
manifest and preflight digest authority.

Top-level exact keys are:

```text
schema_version, batch_id, source_id, primary_member, members, questions
```

`schema_version` is exactly `task9b-source-map-v1`.

Each `members` entry has exactly:

```text
source_member, staged_path, sha256, size_bytes, role
```

Role is exactly `primary | answer`. Members are ordered by semantic role:
primary first, followed by the optional answer member. V1 has no third member
role, so this order is total and does not depend on path spelling.

Each question has exactly:

```text
proposed_question_id, source_order, source_question_number, source_section,
fragment, text_spans, solution_spans, explanation_spans, image_references
```

A generic span is exactly:

```text
member, start_byte, end_byte
```

A text span adds exactly `language`. An image reference has exactly:

```text
source_order, token_span, raw_target, selected_member, canonical_path,
sha256, role
```

Its runtime/JSON types are exact:

```text
source_order: int (not bool)
token_span: exact span object
raw_target: str
selected_member: str | null
canonical_path: str
sha256: str | null
role: str
```

For a present image, `selected_member` is its canonical source member and
`sha256` is the lowercase digest of exact bytes. For a valid absent image,
`selected_member=null` and `sha256=null`, while `canonical_path` remains the
deterministic expected package path. Image role is exactly `question` in V1.
Question arrays follow manifest semantic order; span and image arrays follow
source occurrence order. The outer ZIP SHA must not appear.

Serialization is exactly:

```python
json.dumps(
    payload,
    ensure_ascii=False,
    sort_keys=True,
    separators=(",", ":"),
    allow_nan=False,
).encode("utf-8")
```

No trailing LF is appended to source-map bytes.

For a separate answer member, the map binds its raw member path and digest to
exact solution byte spans and candidate IDs. V1 creates no explanation span
from an undifferentiated solution body; the raw answer bytes remain
independently declared answer evidence.

## 10. Canonical package and Task 9A mapping

The exact layout is:

```text
import_manifest.json
records/candidates.json
source/original.mmd.txt
source/source-map.json
answers/answer.mmd.txt        # only for a selected separate answer member
images/<resolved-canonical-source-relative-path>
```

Raw MMD and image files preserve bytes exactly. `records/candidates.json`,
`source/source-map.json`, and `import_manifest.json` use their approved
canonical JSON serialization. Every package file is declared once in exactly
one Task 9A file group; there are no undeclared auxiliary files.

### 10.1 Exact 18-field `BatchImportManifest` mapping

| Task 9A field | Task 9B authority |
| --- | --- |
| `schema_version` | fixed `task9-import-manifest-v1` |
| `batch_id` | explicit `MmdAdapterManifest.batch_id` |
| `project` | fixed `Joy M2 AI Database` |
| `module` | fixed `M2` |
| `chapter` | explicit manifest chapter |
| `target_release_version` | fixed `V1.19` |
| `candidate_records` | one entry for `records/candidates.json` |
| `source_files` | `source/original.mmd.txt`, then `source/source-map.json` |
| `answer_files` | empty, or one raw `answers/answer.mmd.txt` entry |
| `image_files` | present selected canonical images in first-reference order; representable missing paths are omitted |
| `teacher_notes_files` | empty tuple |
| `common_errors_files` | empty tuple |
| `language_policy` | fixed `preserve_source_and_store_reviewed_chinese_separately` |
| `split_policy` | fixed `one_complete_question_per_record` |
| `difficulty_policy` | fixed `joy_level_1_5` |
| `tag_policy` | fixed `controlled_primary_type_and_tags` |
| `answer_policy` | fixed `preserve_source_answer_identity` |
| `explanation_policy` | fixed `source_or_independently_verified_with_identity` |

All six file arrays contain exact `ImportFileEvidence` path, SHA, size, and
kind values derived from final staged bytes. Task 9B neither adds a policy nor
changes a frozen Task 9A value.

Same-member answer:

```text
source_files = (source/original.mmd.txt, source/source-map.json)
answer_files = ()
```

Primary raw bytes are staged once. V1 solution spans map to that member; the
representative grammar has no independent explanation spans.

Separate selected answer member:

```text
source_files = (source/original.mmd.txt, source/source-map.json)
answer_files = (answers/answer.mmd.txt,)
```

Answer raw bytes are staged once. The source map binds its exact solution spans
to candidates. V1 does not derive explanation provenance from that solution.

Missing answer retains the same source-files tuple, an empty answer-files
tuple, empty solution fields, and `missing_from_source`.

### 10.2 Exact raw candidate mapping

| Task 9A raw candidate field | Task 9B source |
| --- | --- |
| `proposed_question_id` | explicit selection |
| `source_id` | explicit adapter manifest |
| `source_question_number` | uniquely validated source occurrence |
| `source_section` | explicit selection validated against source |
| `source_fragment_hash` | exact raw question-fragment bytes |
| `question_text_original` | deterministic complete-fragment rendering |
| `question_text_zh` | source `zh + shared` projection or empty |
| `translation_status` | `source_present` when Chinese source exists, otherwise `missing` |
| `translation_evidence` | raw-source locator or `None` |
| `solution_original` | exact source solution rendering or empty |
| `solution_verified` | empty in V1 |
| `answer_status` | `source_provided` or `missing_from_source` |
| `explanation_text` | approved distinct source explanation rendering or empty; empty for the representative V1 grammar |
| `explanation_status` | Task 9B V1 emission subset `source_present | missing`; representative output is `missing` |
| `explanation_evidence` | source locator only with `source_present`, otherwise `None`; no V1 AI/review evidence |
| `image_paths` | canonical expected paths in source-reference order, including representable missing images |
| `image_roles` | matching tuple of `question` |
| `primary_type` | explicit selection |
| `tags` | explicit selection tuple |
| `tag_status` | explicit validated selection status |
| `difficulty_level` | explicit selection value or `None` |
| `difficulty_status` | explicit validated selection status |
| `enrichment_status` | deterministic formula in section 7.4 |

Task 9A derives `normalized_text_sha256` and `image_sha256s`; Task 9B does not
write those two derived fields into raw candidate JSON. Candidate JSON contains
every other frozen caller-supplied field and no extra key.

The three JSON files have exact byte conventions:

- `records/candidates.json` uses UTF-8 canonical JSON with sorted object keys,
  compact separators, `ensure_ascii=False`, `allow_nan=False`, followed by one
  LF byte;
- `import_manifest.json` preserves the exact Task 9A
  `BatchImportManifest` field order shown above, and every file-evidence object
  preserves the exact `ImportFileEvidence` order
  `(relative_path, sha256, size_bytes, kind)`. It uses compact separators,
  `ensure_ascii=False`, `allow_nan=False`, and one trailing LF, but **does not**
  sort object keys because the existing Task 9A loader validates those ordered
  fields;
- `source/source-map.json` uses the sorted-key canonical serializer without a
  trailing LF, as frozen in section 9.

### 10.3 Metadata and provenance authority

| Value | Authority class | Rule |
| --- | --- | --- |
| `project`, `module`, target version, six policies | FIXED-AUTHORITY | exact Task 9A constants |
| `batch_id`, `source_id`, `chapter` | USER-CONFIGURED | explicit non-empty manifest values |
| proposed ID, type, tags/status, difficulty/status | USER-CONFIGURED | explicit selection values validated against Task 9A contract |
| source number/section occurrence | SOURCE-DERIVED | parser result must agree with explicit selection |
| original/Chinese source text and raw solution; any future distinct source explanation | SOURCE-DERIVED | exact approved non-overlapping spans only |
| fragment/member/image SHA and staged sizes | DETERMINISTIC-DERIVED | calculated from exact bytes |
| canonical paths, source map, enrichment status | DETERMINISTIC-DERIVED | exact rules in this Design |
| future externally supplied explanation/review payload | FUTURE-ONLY | no Task 9B V1 carrier or emission authority |

There is no default authority class. Every emitted field follows one row in
this table and the exact candidate mapping above.

## 11. Diagnostics and error layers

Processing and diagnostic collection use these exact dependent stages:

```text
D0 selection-manifest decode/schema/carrier contract
D1 source kind, raw digest, archive metadata, path/type safety, declared limits,
   and selected-member existence
D2 bounded archive CRC/decompression streaming
D3 primary/answer MMD decoding, atomic/path safety, and complete-question parse
D4 explicit question/answer selection and source-agreement binding
D5 expected candidate count
D6 bilingual language mapping
D7 image-reference binding
```

D0 uses no source content. If it blocks, D1 never touches `source_path`. D1 is
the first source-access stage and follows the exact section 4 source-kind
algorithm before comparing actual kind/digest, inventorying archive metadata,
and checking selected-member existence. The PDF signature case alone emits
`unsupported_source_format`; a structurally invalid ZIP-shaped input emits
`archive_integrity_invalid`; an approved actual kind that contradicts the
declaration emits `source_contract_mismatch`. These owners are mutually
exclusive for the kind/structure fact. A D1 blocker stops D2-D7. Unless a row
below states an earlier stop, a blocker at Dx completes and sorts independently
determinable Dx issues and stops every dependent stage Dx+1 through D7.

If a stage emits any blocking issue, it first completes all other independently
determinable checks in that same stage, sorts those issues, and then stops every
later stage that depends on its result. Within a stage the rule is emit-all,
not first-error-only, except when another read would itself be unsafe or the
failed input cannot establish the context needed for that check. Downstream
consequences are not emitted as secondary noise.

Every evidence value is canonical JSON with the exact key set in this matrix.
`reason` is one of the listed machine tokens, never free text. D0
`source_contract_mismatch` evidence follows the complete construction rules in
section 11.1. Unless that subsection or a matrix row fixes a more specific
projection, `expected` and `actual` are JSON scalar, array, or `null` values
appropriate to the reason; they never contain an absolute path, cwd, temp root,
exception string, or runtime identity. A path-valued invalid `actual` is
represented by the lowercase SHA-256 of its exact UTF-8 field bytes rather than
copied into evidence. A `member` value is a safe canonical archive-relative
path or `null`, never a host or unsafe raw path. All rows have severity
`blocking` and stop after completing their own stage.

| Code | Stage / exact trigger | Binding and locator | Exact `field` | Exact evidence object |
| --- | --- | --- | --- | --- |
| `source_contract_mismatch` | D0: selection bytes fail strict UTF-8/no-BOM, JSON syntax, duplicate-key, exact schema/type/value, or carrier/internal cross-field validation; D1: an approved actual `mmd`/`mmd_zip` kind contradicts declared `source_kind`, or actual raw SHA-256 differs from `source_sha256`; D4: a uniquely selected source occurrence contradicts explicit `kind`, `number`, or exact source-derived `source_section` | D0/D1 package: `proposed_question_id=None`, `source_locator=""`; D4 candidate: exact proposed ID and matched occurrence locator | D0 logical JSON path: `$`, `$.<field>`, or `$.selections[n].<field>`; D1 exactly `$.source_kind` or `$.source_sha256`; D4 one of `kind`, `number`, `source_section` | exactly `{"actual":...,"expected":...,"reason":...}`; reason exactly `invalid_utf8 | utf8_bom | invalid_json | duplicate_key | non_object | missing_key | extra_key | wrong_type | invalid_value | cross_field_violation | declared_source_kind_mismatch | source_digest_mismatch | source_occurrence_mismatch` |
| `unsupported_source_format` | D1: after a false ZIP structural probe, exact raw prefix `b"%PDF-"` identifies the one recognized unsupported V1 top-level format; approved actual-kind disagreement instead uses `source_contract_mismatch`, ZIP-shaped structural failure uses `archive_integrity_invalid`, manifest member suffixes remain D0 facts, and a selected nested archive uses `archive_member_unsafe` | package, `None`, empty locator | exactly `source_kind` | exactly `{"actual":"pdf","expected":["mmd","mmd_zip"],"reason":"top_level_format"}` |
| `archive_integrity_invalid` | D1: `zipfile.is_zipfile` is false while raw bytes begin `b"PK"`, or an established ZIP has unreadable/corrupt structure, encryption, unsupported compression, or declared member/count/size/ratio limit; D2: observed bound, decompression, or CRC failure | package, `None`, empty locator | exactly `archive` | exactly `{"actual":...,"limit":...,"member":...,"reason":...}`; reason exactly `zip_structure | encrypted | compression | member_count | archive_size | member_size | mmd_size | image_size | total_uncompressed | compression_ratio | decompression | crc` |
| `archive_member_unsafe` | D1: archive/member metadata has an absolute/backslash/drive/UNC/traversal/dot/empty component, normalization escape, duplicate/NFC/casefold collision, disallowed hidden member, symlink/special/executable type, unselected second MMD, or nested archive; D3: a lexically complete image envelope hits the ordered raw-target safety list in section 8 | D1 package: `proposed_question_id=None`, empty locator; D3 package: `proposed_question_id=None` and the safe canonical containing-member/image-envelope byte locator (selection has not run) | D1 exactly `archive_member`; D3 exactly `raw_target` | D1 exactly `{"member_name_sha256":...,"reason":...}`, with the digest over the ZIP-decoded raw member-name string encoded as UTF-8 and reason exactly `absolute | backslash | drive_or_unc | traversal | dot_or_empty_component | normalized_escape | duplicate | nfc_collision | casefold_collision | hidden | symlink | special | executable | second_mmd | nested_archive`; D3 exactly `{"raw_target_sha256":...,"reason":...}`, with the digest over exact UTF-8 target bytes and reason exactly `image_target_drive_or_unc | image_target_absolute | image_target_backslash | image_target_traversal | image_target_dot_or_empty_component | image_target_normalized_escape | image_target_nfc_collision | image_target_casefold_collision | image_target_canonicalization` |
| `mmd_parse_failed` | D3: selected MMD invalid UTF-8, unclosed inline/display token, malformed atomic construct or incomplete image token, unsupported V1 grammar, invalid span, broken question/answer boundary, or missing/ambiguous exercise section; a complete but unsafe image target instead uses D3 `archive_member_unsafe` | package, `None`; canonical member/byte locator when a safe interval exists, otherwise empty locator | exactly `primary_member` or `answer_member` | exactly `{"end_byte":...,"member":...,"reason":...,"start_byte":...}`; offsets are exact ints or `null`; reason exactly `invalid_utf8 | unclosed_token | unsupported_grammar | invalid_span | broken_boundary | missing_section | ambiguous_section` |
| `selection_not_unique` | D1: for MMD.ZIP, a declared `primary_member` or non-`None` `answer_member` is absent from the completed safe canonical inventory; D4: a typed selection's primary question, local solution, or separate answer occurrence has zero or more than one match | D1 package: `proposed_question_id=None`, `source_locator=""`; D4 candidate: exact proposed ID and unique surrounding question locator when available, otherwise empty locator | D1 exactly `primary_member` or `answer_member`; D4 exactly `selection`, `answer_mapping`, or `answer_number` | D1 exactly `{"member":...,"reason":"selected_member_missing"}` using the canonical safe declared member; D4 exactly `{"canonical_number":...,"match_count":...,"reason":...}` with reason exactly `question_occurrence | local_solution | answer_occurrence` |
| `candidate_count_mismatch` | D5: after every selection binds uniquely, the number of complete top-level question occurrences parsed from the selected primary member differs from `expected_candidate_count` | package, `None`, empty locator | exactly `expected_candidate_count` | exactly `{"actual":...,"expected":...,"reason":"candidate_count"}` |
| `language_mapping_ambiguous` | D6: after D3 atomic parsing succeeds, the exact section 7.1 state machine cannot satisfy the declared layout | candidate, exact proposed ID and smallest offending question byte locator | exactly `language_layout` | exactly `{"end_byte":...,"layout":...,"reason":...,"start_byte":...}`; reason exactly `missing_en | missing_zh | invalid_transition | und_prose` |
| `image_binding_invalid` | D7: a path-safe reference has ambiguous semantic mapping, conflicts with explicit selection, has multiple matches, cannot yield exactly one canonical expected path, or has invalid role/binding metadata; a valid absent member and every unsafe raw target are not triggers | candidate, exact proposed ID and image-token locator | exactly `expected_image_members` | exactly `{"matches":...,"raw_target":...,"reason":...}` where `matches` is the canonically sorted safe member array; reason exactly `ambiguous_reference | selection_conflict | multiple_matches | canonical_path_unavailable | invalid_role` |

### 11.1 Exact D0 `source_contract_mismatch` evidence

D0 evidence is always the canonical encoding of exactly:

```json
{"actual":...,"expected":...,"reason":"..."}
```

No raw undecodable byte, parser/decoder exception text, traceback, host path,
cwd, temporary root, memory identity, platform name, locale, or runtime version
may enter `actual` or `expected`. The following JSON type tokens are exact:
`array`, `boolean`, `integer`, `null`, `number`, `object`, and `string`. The
token decision uses this exact ordered ladder:

1. `value is None` -> `null`;
2. `type(value) is bool` -> `boolean`;
3. `type(value) is int` -> `integer`;
4. `type(value) is float` -> `number`;
5. exact `str`, `list`, or `dict` -> `string`, `array`, or `object`.

No `isinstance` widening is allowed. Consequently JSON `1` is `integer`, while
`1.0`, `1e0`, and `-0.0` are all `number`, and `true` is `boolean`. `NaN`,
`Infinity`, and `-Infinity` are rejected by strict decoding as `invalid_json`;
they never reach type/value validation.

Logical fields are deterministic JSON paths. The root is `$`, and an array
element appends a zero-based decimal `[n]`. Each decoded object key is projected
before it is appended. A path-like key is one for which the existing evidence
path detector is true: `PurePosixPath(key).is_absolute()`, `key` starts with two
backslashes (`key.startswith("\\\\")`), or ASCII regex `[A-Za-z]:[\\/]`
matches at the start. Such a key
appends the opaque segment `[~key-sha256:<digest>]`, where `<digest>` is the
lowercase SHA-256 of the exact key UTF-8 bytes. Otherwise a key matching ASCII
`[A-Za-z_][A-Za-z0-9_]*` appends `.key`, and every other key appends `[` plus its
canonical JSON string encoding plus `]`. The same rule applies recursively to
unknown nested objects and identically to `extra_key` and `duplicate_key`.
Valid-schema paths consequently use `$.field`, `$.selections[n]`,
`$.selections[n].field`, and the latter followed by `[m]` for a tuple item. No
logical path includes raw path-like key text, `selection_manifest_path`,
`source_path`, or a derived filesystem path.

Raw decode and schema reasons use these exact values:

| `reason` | Exact `field` | Exact `actual` | Exact `expected` |
| --- | --- | --- | --- |
| `wrong_type` for an existing non-regular selection-manifest path | `$` | `"non_regular_file"` | `"regular_file"` |
| `invalid_value` for an existing unreadable regular selection-manifest file | `$` | `"unreadable_file"` | `"readable"` |
| `invalid_utf8` | `$` | `"undecodable_utf8"` | `"strict_utf8"` |
| `utf8_bom` | `$` | `"utf8_bom"` | `"no_bom"` |
| `invalid_json` | `$` | `"invalid_json_syntax"` | `"json_object"` |
| `duplicate_key` | logical path of the repeated key | `"duplicate"` | `"unique"` |
| `non_object` | `$` | exact decoded JSON type token | `"object"` |
| `missing_key` | logical path of the absent key | `"missing"` | `"present"` |
| `extra_key` | logical path of the present extra key | `"present"` | `"absent"` |
| `wrong_type` | logical path of the value | exact decoded JSON type token | exact expected type token or union below |

The two pre-read file rows above override decoded-value projections and expose
no path. For decoded JSON, the `wrong_type` expected projection is exact. The
top-level manifest is `object`; each `selections[n]` is `object`; `selections`,
`expected_image_members`, and `tags` are `array`; `expected_candidate_count` is
`integer`; and every remaining non-null scalar field is `string`.
`answer_member` and `answer_number` override that scalar rule with
`["string","null"]`, and
`difficulty_level` uses `["integer","null"]`, precisely in the shown order.
Array item paths under `expected_image_members` and `tags` expect `string`.

For `invalid_value`, a correctly typed enum or exact-constant field places its
actual decoded JSON scalar in `actual`; its exact approved constant or ordered
allowed-value array is `expected`. The sole safe-scalar substitution is exact:
if that invalid string is an absolute POSIX path, starts with two backslashes,
or begins with a drive letter plus slash or backslash, `actual` is instead the
lowercase SHA-256 of its exact UTF-8 bytes. This applies before evidence
serialization and prevents a manifest-supplied host path from entering the
public envelope.

| Field family | Exact `expected` |
| --- | --- |
| `$.schema_version` | `"task9b-mmd-adapter-v1"` |
| `$.source_kind` | `["mmd","mmd_zip"]` |
| `$.selections[n].kind` | `["example","exercise"]` |
| `$.selections[n].language_layout` | `["english_then_chinese","interleaved_bilingual"]` |
| `$.selections[n].answer_mapping` | `["source_answer","missing_from_source"]` |
| `$.selections[n].tag_status` or `$.selections[n].difficulty_status` | `["source_provided","proposed","missing"]` |

Every other `invalid_value` projection is exact:

- empty `batch_id`, `source_id`, `chapter`, `proposed_question_id`, `number`,
  `source_section`, `answer_number`, `primary_type`, or tag item uses
  `actual=""`, `expected="non_empty_string"`;
- an invalid `source_sha256` string uses as `actual` the lowercase SHA-256 of
  its exact UTF-8 string bytes and `expected="lowercase_hex_64"`;
- an invalid `primary_member` or non-null `answer_member` string uses as
  `actual` the lowercase SHA-256 of its exact UTF-8 string bytes and
  `expected="canonical_nfc_posix_mmd_member"`;
- an invalid `expected_image_members[m]` string uses as `actual` the lowercase
  SHA-256 of its exact UTF-8 string bytes and
  `expected="canonical_nfc_posix_images_member"`;
- only an `expected_image_members[m]` value that first passes its exact runtime
  type and all individual canonical path/root/suffix validation participates in
  duplicate uniqueness. Each later occurrence of such a valid member emits one
  issue bound to `$.selections[n].expected_image_members`; `actual` is the
  lowercase SHA-256 of the duplicate value's exact UTF-8 bytes and
  `expected="unique_items"`;
- a negative `expected_candidate_count` preserves the exact decoded integer in
  `actual` and uses `expected="non_negative_integer"`;
- a correctly typed `difficulty_level` outside 1 through 5 preserves the exact
  decoded integer in `actual` and uses `expected="integer_1_to_5"`.

Each correctly typed invalid scalar or tuple item emits at most one
`invalid_value` issue even if it violates more than one spelling constraint.
Canonical path/root/suffix checks are one field-value fact; they do not create
duplicate issues with the same reason. Invalid member occurrences never enter
the duplicate seen-set. Thus `["bad.gif","bad.gif"]` emits exactly two
element-bound `invalid_value` issues and no container-bound duplicate issue.

For `cross_field_violation`, only the following exact projections exist:

| Violated invariant and exact `field` | Exact `actual` | Exact `expected` |
| --- | --- | --- |
| declared plain MMD has non-null `$.answer_member` | `"present"` | `"null_when_source_kind_mmd"` |
| declared plain MMD `$.primary_member` differs from lexical `source_path.name` | lowercase SHA-256 of declared member UTF-8 bytes | lowercase SHA-256 of lexical filename UTF-8 bytes |
| `$.answer_member` equals `$.primary_member` | `"same_as_primary_member"` | `"different_from_primary_member"` |
| `$.expected_candidate_count` differs from `len(selections)` | exact declared integer | exact array length integer |
| later duplicate `$.selections[n].proposed_question_id` | lowercase SHA-256 of the exact ID UTF-8 bytes | `"unique_proposed_question_id"` |
| `missing_from_source` has non-null `$.selections[n].answer_number` | `"present"` | `"null_when_missing_from_source"` |
| any non-null `$.selections[n].answer_number` while manifest `answer_member` is null | `"present"` | `"null_without_answer_member"` |
| `tag_status="missing"` has non-empty `$.selections[n].tags` | exact array length integer | `0` |
| non-missing `tag_status` has empty `$.selections[n].tags` | `0` | `"positive_length"` |
| `difficulty_status="missing"` has non-null `$.selections[n].difficulty_level` | exact level integer | `null` |
| non-missing `difficulty_status` has null `$.selections[n].difficulty_level` | `null` | `"integer_1_to_5"` |

D0 collection is also exact. An undecodable UTF-8 input, BOM, invalid JSON
syntax, or non-object root emits its single context-establishing issue and
stops. A syntactically valid document with duplicate keys emits one
`duplicate_key` issue for every repeated occurrence after the first, in lexical
detection order, and does not construct the ambiguous object or add derived
schema issues. Otherwise D0 emits every independently determinable missing,
extra, wrong-type, invalid-value, and cross-field issue. It never performs a
value check after a wrong type, and performs a cross-field check only when all
of that invariant's inputs have the required types and valid individual values.
All collected issues then use the unchanged five-field stable sort below;
identical duplicate-key issues retain lexical detection order. These rules add
no diagnostic code or reason, and do not change D0's stop before D1.
Consequently, `missing_from_source` with a non-null `answer_number` and a null
manifest `answer_member` emits both independently applicable cross-field rows;
their distinct canonical evidence strings determine their order through the
unchanged sort key.

Representable missing/orphan/image-byte-collision facts are emitted into the
canonical package for Task 9A classification rather than converted to a Task
9B code. All nine codes remain independent from the frozen Task 9A 16-code
`ImportIssue` taxonomy.

Required precedence is exact:

- a missing `selection_manifest_path` raises `InputMissingError`, emits no
  issue, and leaves `source_path` untouched;
- a present but invalid selection manifest produces only determinable D0
  `source_contract_mismatch` issues; `source_path` remains untouched and D4
  cannot add `selection_not_unique`;
- declared `mmd_zip` with actual plain-MMD bytes, or declared `mmd` with an
  established ZIP, produces the D1 `source_contract_mismatch` reason
  `declared_source_kind_mismatch`; exact PDF bytes instead produce only
  `unsupported_source_format`, while ZIP-shaped structurally invalid bytes
  produce only `archive_integrity_invalid` reason `zip_structure`;
- a missing declared primary or answer member produces only the D1 package-bound
  `selection_not_unique` reason `selected_member_missing`; D2-D7 do not run and
  no partial primary parse is permitted;
- an unsafe archive member or path produces `archive_member_unsafe`; D2/D7 do
  not run, so `archive_integrity_invalid` and `image_binding_invalid` are not
  derived from that member;
- a complete image token with an unsafe raw target is discovered only after D2
  passes and produces D3 `archive_member_unsafe`; the parser finishes safely
  determinable D3 checks, then D4-D7 stop, so neither `mmd_parse_failed` nor
  `image_binding_invalid` is produced for that target;
- an unclosed or malformed atomic construct produces only D3
  `mmd_parse_failed`; D6 does not run and cannot add
  `language_mapping_ambiguous`;
- an exercise Q marker outside active `應試練習` scope produces only D3
  `mmd_parse_failed` reason `missing_section`; a uniquely parsed section that
  disagrees with the manifest instead produces D4 `source_contract_mismatch`
  reason `source_occurrence_mismatch`;
- a selected nested archive produces only `archive_member_unsafe` for that
  fact, not `unsupported_source_format` or `archive_integrity_invalid`, unless
  the top-level source itself independently has an unsupported source format;
- any D4 selection failure prevents D5, so no consequential
  `candidate_count_mismatch` is emitted;
- a safe canonical image target whose member is absent produces no Task 9B
  issue and is preserved for Task 9A `missing_image`.

Issues use a stable Python sort by exactly:

```python
(
    issue.source_locator,
    issue.proposed_question_id or "",
    issue.code,
    issue.field,
    issue.evidence,
)
```

Equal-key entries retain input order. No filesystem, dict, set, or absolute
path order participates.

Early contract layers are exact:

- missing source or selection manifest: `InputMissingError`;
- existing non-regular or unreadable source: `InputFormatError`;
- output outside the approved staging boundary: `ConfigurationError`;
- pre-existing output target: `OutputConflictError`;
- one or more structured adapter diagnostics:
  `MmdAdapterBlockedError(InputFormatError)`.

Any Task 9B issue blocks canonical build. No partial package is published; a
temporary sibling may be used privately and must be removed on failure.

## 12. Staging and write boundary

`output_dir` must be a new descendant of the configured disposable Task 9
staging root. Task 9B may atomically publish only the canonical layout in
section 10. It may not write under `releases/`, `data/baselines/`, `legacy/`,
the V1.18 tree, any formal image tree, or a promotion destination.

Staging writes do not constitute a database import. V1.18 SQLite remains
immutable, V1.19 database artifacts remain absent, and imported question count
remains zero throughout Task 9B.

## 13. Representative source authority

The representative analyzed source is the external package named
`数学M2王-向量及其应用.mmd.zip`, identified by SHA-256:

```text
59cef92aefc0f9b2d66db199b8cb7c72306bb61c1ff9554f3ca57da16b51ff52
```

Its approved structural inventory is one directory entry, eight STORED JPEG
members, and one STORED MMD member. The MMD member is 88,140 bytes, UTF-8,
LF-only, 1,997 lines, and has SHA-256:

```text
649f9df7bf2c63232c4e96d8cd07977822b5cdadc49f718038806a7542b71a97
```

The semantic fixture authority is 17 complete questions in source order:
examples 1–11 followed by exercises Q1–Q6. The eleven examples contain source
solutions; the six exercises have no source answer and must remain
`missing_from_source`. Historical V1.18 AI-verified exercise answers are not
Task 9B input and must not be reused.

Eight image references are observed. Four chapter illustrations are not
selected as candidate images. Example 11 and exercises Q1–Q3 each bind one
question image. The fixture covers both bilingual layouts, nested subparts,
source solutions, the V1 explanation-missing rule, missing answers, image
binding, locators, raw fragment digests, and semantic ordering.

This external artifact remains outside the repository. A later B1 checkpoint
will create reviewed, minimal test material only beneath the approved fixture
scope; this Design checkpoint does not create fixtures or copy source content.

## 14. Implementation and fixture scope

Task 9B implementation authority is closed to these paths and categories.

**NEW** maintained files:

```text
src/joy_m2/ingest/adapter_models.py
src/joy_m2/ingest/archive.py
src/joy_m2/ingest/mmd_parser.py
src/joy_m2/ingest/adapter.py
```

**MODIFIED** maintained production files: none. In particular, frozen Task 9A
models, manifest loader, preflight implementation, and public behavior are not
modified.

**TEST** files:

```text
tests/unit/test_mmd_adapter_models.py
tests/unit/test_mmd_archive.py
tests/unit/test_mmd_parser.py
tests/integration/test_mmd_adapter.py
```

**FIXTURE** authority is restricted to:

```text
tests/fixtures/task9b/representative/**
tests/fixtures/task9b/golden/**
tests/fixtures/task9b/security/**
```

`representative` holds reviewed minimal MMD/image/selection material;
`golden` holds an independently authored semantic-equivalent Task 9A package;
`security` holds minimal unsafe archive members required by explicit negative
controls. Fixtures may not contain formal database artifacts, the entire
external source archive, or unreviewed question corpora.

**DOC** scope for this checkpoint is exactly this Design document. An
implementation plan is a later,
separately reviewed artifact. No plugin framework, generic ingestion system,
generic Markdown subsystem, object store, UI, or new dependency is authorized.

## 15. RED-first delivery sequence

No production code may be written before its valid RED. The sequence is:

1. **B0 — Design authority committed.** This Design passes independent review
   and is committed alone.
2. **B1 — Representative fixture checkpoint.** Minimal reviewed fixtures are
   created, independently reviewed, and committed before behavior tests depend
   on them.
3. **B2 — Public contract RED.** Model tests first prove missing exact public
   carriers and validation. After valid RED, implement only
   `adapter_models.py` and restore focused GREEN. Then establish an API-
   existence RED and add only a no-behavior adapter scaffold whose call still
   raises `NotImplementedError`.
4. **Behavior RED gate.** Before any archive, parser, mapping, or package
   behavior, establish and validate all three behavior groups: archive safety;
   parser/complete-question mapping; canonical package/integration/golden
   equivalence. Each failure must be the deliberate no-behavior boundary, not
   an import, fixture, environment, or test-construction error.
5. **B3 — Inventory/safety GREEN.** Implement only safe inventory/path/limit
   behavior and its nine-code projections needed by this group.
6. **B4 — Parser/Source IR GREEN.** Implement only the approved Mathpix subset,
   immutable IR, complete-question spans, rendering, and fragment identity.
7. **B5 — Mapping/provenance GREEN.** Implement explicit selection, answer and
   explanation independence, bilingual mapping, images, metadata, and
   enrichment status.
8. **B6 — Canonical package GREEN.** Implement deterministic JSON, file groups,
   source map, byte-preserving staging, atomic publication, and cleanup.
9. **B7 — Task 9A equivalence GREEN.** Run adapter and independent golden
   package through unchanged Task 9A and close every equivalence dimension.
10. **B8 — Determinism/security gates.** Repeat under different roots, temp
    paths, ZIP physical orders, and container metadata; run every safety
    negative control and full maintained/frozen gates.
11. **B9 — Final independent review.** Review implementation, provenance,
    deterministic bytes, security, scope, and frozen boundaries before the
    implementation commit.

Every checkpoint records collected/PASS/FAIL/ERROR/exit code for its focused
tests, keeps Task 9A `41/41 PASS`, and stops on dependency, scope, or authority
drift. Tests are never weakened to fit implementation.

## 16. Golden equivalence and determinism gates

The expected canonical package is independently authored and reviewed; it may
not be generated by production adapter helpers. Adapter and expected package,
when independently passed to frozen Task 9A, must produce identical:

- candidates;
- issues;
- counts and final status;
- duplicate classifications;
- adaptations;
- report;
- `preflight_sha256`.

Additional byte gates cover repeat runs, different absolute roots, different
temporary roots, ZIP physical member order, and irrelevant ZIP metadata.
Selected member bytes, images, source map, candidate JSON, manifest evidence,
and complete package tree must be deterministic. Changing semantic manifest
order changes semantic identity and output; changing only discovery or ZIP
physical order does not.

Security tests independently cover every rejected path/type, collision,
archive integrity condition, limit, compression method, metadata rule, second
MMD, and ambiguous selection. Removing one check must fail its corresponding
negative control. Separate controls also lock: the actual-kind decisions for
plain, valid ZIP, ZIP-shaped corruption, and PDF; missing primary and answer
members; missing versus present-invalid selection manifests with source-access
spies; each section 8 raw-target reason; an out-of-scope exercise Q; and a
uniquely parsed section that disagrees with its selection.

## 17. Regression and frozen gates

Every Task 9B checkpoint keeps the existing Task 9A integration suite at
`41/41 PASS`. Final gates also include all maintained regressions required by
current project authority and the V1.18 independent validator.

The frozen database gate is exact:

```text
V1.18 SQLite SHA-256:
fd9fe44f1d4bebb3e6dc94ef9d0ef28afde217920c09682e3b4840a97522f5a7

complete questions: 497
V1.19 database artifacts: absent
formal imported questions: 0
writer: absent
promotion: not started
```

The adapter must not search for, read, or re-hash a historical V1.16 ZIP.
Existing historical constants and maintained/frozen authority hierarchy remain
unchanged.

## 18. Exit gate

Task 9B is complete only after all of the following are true:

- this Design is independently reviewed, approved, and committed;
- a detailed implementation plan is separately approved;
- representative fixtures are independently reviewed and committed;
- public carrier and API tests are GREEN;
- strict selection-manifest decoding, duplicate-key rejection, and typed
  conversion are GREEN;
- all nine diagnostic codes and deterministic ordering are GREEN;
- diagnostic stage precedence and within-stage multiplicity are GREEN;
- ZIP/file safety and resource limits are GREEN;
- metadata preflight, all-member bounded CRC streaming, and selective staging
  are independently GREEN;
- parser and 17-question complete mapping are GREEN;
- translation, answer, explanation, image, tag, and difficulty provenance are
  GREEN;
- both bilingual layouts, same-line mixed runs, exact answer boundaries, and
  representable missing images are GREEN;
- canonical package bytes and source-map bytes are deterministic;
- independently authored golden equivalence is GREEN;
- Task 9A remains `41/41 PASS`;
- the V1.18 SHA and 497-question count remain unchanged;
- no V1.19 database or formal import exists;
- final independent implementation review passes;
- the approved implementation files are committed in a dedicated checkpoint.

Completion of Task 9B grants no Task 9C writer or promotion authority.

## 19. Non-goals and downstream boundary

Task 9B V1 explicitly excludes:

- independent answer archives or multiple answer members;
- PDF ingestion and OCR;
- runtime AI answer or explanation generation;
- arbitrary Markdown compatibility;
- generic ingestion/plugin frameworks;
- database writers and V1.19 creation;
- import approval, release promotion, and automatic approval;
- workflow UI and API/application work;
- M1 material;
- rewriting or correcting source mathematics.

The user workflow remains:

```text
MMD or MMD.ZIP + explicit selection manifest
  -> Task 9B adapter
  -> canonical Task 9A package
  -> Task 9A read-only preflight
  -> user review of detected/new/duplicate/rejected/issues
  -> explicit approval
  -> future separately authorized Task 9C writer
```

Enrichment uses only candidate-local source content, relevant taxonomy subsets,
and approved compact context. The complete 497-question database is never sent
to an AI enrichment step. Duplicate and collision checks remain Task 9A local
read-only baseline work.

## 20. Final decision register

| Decision | Final authority | V1 classification |
| --- | --- | --- |
| Answer-package scope | primary answer or one explicitly selected same-ZIP answer member; independent archive excluded | REQUIRED FOR V1 |
| Outer ZIP identity | input validation only; excluded from semantic/digest authority | REQUIRED FOR V1 |
| Source IR | exact private frozen member/span/image/question/document carriers | REQUIRED FOR V1 |
| Adapter diagnostics | exact immutable carrier, nine codes, canonical evidence and ordering | REQUIRED FOR V1 |
| Resource limits | 50/100/20/10 MiB, 256 members, 100:1, STORED/DEFLATED | REQUIRED FOR V1 |
| OS/file policy | explicit allow/ignore/reject matrix with safety-before-ignore | REQUIRED FOR V1 |
| Bilingual/source-map | source-order rendering, raw fragment hash, exact canonical map | REQUIRED FOR V1 |
| Task 9A mapping | exact enrichment formula and raw source/answer/map file-group semantics | REQUIRED FOR V1 |

Answer semantics are final: answer selection never implies explanation
provenance; raw answer evidence is not replaced by derived mapping metadata.
All eight executable authority decisions are approved. There is no unresolved
V1 contract decision.

Deferred work is limited to independent answer archives, broader Mathpix or
Markdown grammar, PDF/OCR, and runtime AI enrichment. Database writing,
V1.19 creation, formal import, and promotion are outside Task 9B.
