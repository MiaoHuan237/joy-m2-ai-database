"""Private deterministic parser for the approved Task 9B Mathpix subset."""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import PurePosixPath
import re
import unicodedata

from joy_m2.errors import PipelineError

from .adapter_models import MmdAdapterBlockedError, MmdAdapterIssue


_SHA256 = re.compile(r"[0-9a-f]{64}")
_DRIVE_OR_UNC = re.compile(r"[A-Za-z]:")
_EXAMPLE = re.compile(r"(例題|例题) ?([1-9]|10|11)")
_EXERCISE = re.compile(r"(?:Q([1-6])）|\\item\[Q([1-6])）\])(?:| ([^ ].*))")
_ANSWER_EXERCISE = re.compile(r"(?:Q([1-6])）|\\item\[Q([1-6])）\])")
_ITEM_PREFIX = re.compile(r"\\item\[[^\]\r\n]*\]")
_IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png"}
_SPAN_ROLES = {"question", "solution", "explanation", "image_token"}
_SPAN_LANGUAGES = {"en", "zh", "shared", "und"}


def _canonical_path(value: object, name: str) -> str:
    if type(value) is not str or not value:
        raise PipelineError(f"{name} must be an exact non-empty string")
    path = PurePosixPath(value)
    if (
        path.is_absolute()
        or value.startswith("//")
        or _DRIVE_OR_UNC.match(value) is not None
        or "\\" in value
        or unicodedata.normalize("NFC", value) != value
        or any(unicodedata.category(character) == "Cc" for character in value)
        or any(part in {"", ".", ".."} for part in path.parts)
        or path.as_posix() != value
    ):
        raise PipelineError(f"{name} must be a canonical NFC relative POSIX path")
    return value


def _exact_tuple(value: object, item_type: type, name: str):
    if type(value) not in {list, tuple}:
        raise PipelineError(f"{name} must be a list or tuple")
    result = tuple(value)
    if any(type(item) is not item_type for item in result):
        raise PipelineError(f"{name} contains an invalid value")
    return result


@dataclass(frozen=True)
class _SourceMember:
    relative_path: str
    sha256: str
    content: bytes

    def __post_init__(self) -> None:
        _canonical_path(self.relative_path, "relative_path")
        if type(self.sha256) is not str or _SHA256.fullmatch(self.sha256) is None:
            raise PipelineError("sha256 must be a lowercase SHA-256 digest")
        if type(self.content) is not bytes:
            raise PipelineError("content must be exact bytes")
        if hashlib.sha256(self.content).hexdigest() != self.sha256:
            raise PipelineError("sha256 must bind the exact member content")


@dataclass(frozen=True)
class _SourceSpan:
    member_path: str
    start_byte: int
    end_byte: int
    role: str
    language: str

    def __post_init__(self) -> None:
        _canonical_path(self.member_path, "member_path")
        if type(self.start_byte) is not int or self.start_byte < 0:
            raise PipelineError("start_byte must be an exact non-negative integer")
        if type(self.end_byte) is not int or self.end_byte <= self.start_byte:
            raise PipelineError("end_byte must be an exact integer after start_byte")
        if type(self.role) is not str or self.role not in _SPAN_ROLES:
            raise PipelineError("role must be an approved Source IR role")
        if type(self.language) is not str or self.language not in _SPAN_LANGUAGES:
            raise PipelineError("language must be an approved Source IR language")


@dataclass(frozen=True)
class _SourceImageRef:
    source_order: int
    token_span: _SourceSpan
    raw_target: str
    resolved_member: str | None

    def __post_init__(self) -> None:
        if type(self.source_order) is not int or self.source_order < 0:
            raise PipelineError("source_order must be an exact non-negative integer")
        if type(self.token_span) is not _SourceSpan or (
            self.token_span.role != "image_token"
            or self.token_span.language != "shared"
        ):
            raise PipelineError("token_span must be a shared image-token SourceSpan")
        if type(self.raw_target) is not str or not self.raw_target:
            raise PipelineError("raw_target must be an exact non-empty string")
        if self.resolved_member is not None:
            _canonical_path(self.resolved_member, "resolved_member")


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

    def __post_init__(self) -> None:
        if type(self.source_order) is not int or self.source_order < 0:
            raise PipelineError("source_order must be an exact non-negative integer")
        for name in ("source_question_number", "source_section"):
            value = getattr(self, name)
            if type(value) is not str or not value:
                raise PipelineError(f"{name} must be an exact non-empty string")
        if type(self.fragment_span) is not _SourceSpan:
            raise PipelineError("fragment_span must be an exact SourceSpan")
        if self.fragment_span.role != "question":
            raise PipelineError("fragment_span must have question role")

        text_spans = _exact_tuple(self.text_spans, _SourceSpan, "text_spans")
        solution_spans = _exact_tuple(
            self.solution_spans, _SourceSpan, "solution_spans"
        )
        explanation_spans = _exact_tuple(
            self.explanation_spans, _SourceSpan, "explanation_spans"
        )
        image_refs = _exact_tuple(self.image_refs, _SourceImageRef, "image_refs")
        if any(span.role != "question" for span in text_spans):
            raise PipelineError("text_spans must have question role")
        if any(span.role != "solution" for span in solution_spans):
            raise PipelineError("solution_spans must have solution role")
        if any(span.role != "explanation" for span in explanation_spans):
            raise PipelineError("explanation_spans must have explanation role")

        text_spans = tuple(
            sorted(text_spans, key=lambda span: (span.member_path, span.start_byte, span.end_byte))
        )
        solution_spans = tuple(
            sorted(
                solution_spans,
                key=lambda span: (span.member_path, span.start_byte, span.end_byte),
            )
        )
        explanation_spans = tuple(
            sorted(
                explanation_spans,
                key=lambda span: (span.member_path, span.start_byte, span.end_byte),
            )
        )
        image_refs = tuple(sorted(image_refs, key=lambda ref: ref.source_order))
        if tuple(ref.source_order for ref in image_refs) != tuple(range(len(image_refs))):
            raise PipelineError("image_refs source_order values must be contiguous")
        for spans, name in (
            (text_spans, "text_spans"),
            (solution_spans, "solution_spans"),
            (explanation_spans, "explanation_spans"),
        ):
            if len(set(spans)) != len(spans):
                raise PipelineError(f"{name} must not contain duplicates")
        if len(set(image_refs)) != len(image_refs):
            raise PipelineError("image_refs must not contain duplicates")

        object.__setattr__(self, "text_spans", text_spans)
        object.__setattr__(self, "solution_spans", solution_spans)
        object.__setattr__(self, "explanation_spans", explanation_spans)
        object.__setattr__(self, "image_refs", image_refs)


@dataclass(frozen=True)
class _SourceDocument:
    primary_member: str
    members: tuple[_SourceMember, ...]
    questions: tuple[_SourceQuestion, ...]

    def __post_init__(self) -> None:
        _canonical_path(self.primary_member, "primary_member")
        members = _exact_tuple(self.members, _SourceMember, "members")
        questions = _exact_tuple(self.questions, _SourceQuestion, "questions")
        members = tuple(sorted(members, key=lambda member: member.relative_path))
        questions = tuple(sorted(questions, key=lambda question: question.source_order))
        paths = tuple(member.relative_path for member in members)
        if len(set(paths)) != len(paths):
            raise PipelineError("members must have unique canonical paths")
        if self.primary_member not in paths:
            raise PipelineError("primary_member must resolve to a declared member")
        if tuple(question.source_order for question in questions) != tuple(
            range(len(questions))
        ):
            raise PipelineError("question source_order values must be contiguous")

        by_path = {member.relative_path: member for member in members}
        for question in questions:
            spans = (
                question.fragment_span,
                *question.text_spans,
                *question.solution_spans,
                *question.explanation_spans,
                *(reference.token_span for reference in question.image_refs),
            )
            for span in spans:
                member = by_path.get(span.member_path)
                if member is None or span.end_byte > len(member.content):
                    raise PipelineError("SourceSpan must be contained by a declared member")
            for span in (*question.text_spans, *(ref.token_span for ref in question.image_refs)):
                if (
                    span.member_path != question.fragment_span.member_path
                    or span.start_byte < question.fragment_span.start_byte
                    or span.end_byte > question.fragment_span.end_byte
                ):
                    raise PipelineError("question content spans must stay inside fragment_span")
            ordered_fragment_spans = sorted(
                (*question.text_spans, *(ref.token_span for ref in question.image_refs)),
                key=lambda span: (span.start_byte, span.end_byte),
            )
            if any(
                previous.end_byte > current.start_byte
                for previous, current in zip(
                    ordered_fragment_spans, ordered_fragment_spans[1:]
                )
            ):
                raise PipelineError("question content spans must not overlap")
            for reference in question.image_refs:
                if (
                    reference.resolved_member is not None
                    and reference.resolved_member not in by_path
                ):
                    raise PipelineError("resolved image member must be declared")

        object.__setattr__(self, "members", members)
        object.__setattr__(self, "questions", questions)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    )


def _parse_issue(
    member: _SourceMember,
    field: str,
    reason: str,
    start_byte: int | None = None,
    end_byte: int | None = None,
) -> MmdAdapterIssue:
    locator = (
        f"{member.relative_path}#bytes={start_byte}:{end_byte}"
        if start_byte is not None and end_byte is not None and start_byte < end_byte
        else ""
    )
    return MmdAdapterIssue(
        "mmd_parse_failed",
        "blocking",
        None,
        locator,
        field,
        _canonical_json(
            {
                "end_byte": end_byte,
                "member": member.relative_path,
                "reason": reason,
                "start_byte": start_byte,
            }
        ),
    )


def _target_issue(
    member: _SourceMember,
    raw_target: str,
    reason: str,
    start_byte: int,
    end_byte: int,
) -> MmdAdapterIssue:
    return MmdAdapterIssue(
        "archive_member_unsafe",
        "blocking",
        None,
        f"{member.relative_path}#bytes={start_byte}:{end_byte}",
        "raw_target",
        _canonical_json(
            {
                "raw_target_sha256": hashlib.sha256(
                    raw_target.encode("utf-8")
                ).hexdigest(),
                "reason": reason,
            }
        ),
    )


def _physical_lines(content: bytes, start: int = 0, end: int | None = None):
    limit = len(content) if end is None else end
    position = start
    while position < limit:
        line_start = position
        while position < limit and content[position] not in {10, 13}:
            position += 1
        content_end = position
        if position < limit:
            if content[position] == 13 and position + 1 < limit and content[position + 1] == 10:
                position += 2
            else:
                position += 1
        yield (line_start, content_end, position, content[line_start:content_end].decode("utf-8"))


def _example_marker(text: str):
    match = _EXAMPLE.fullmatch(text)
    if match is None:
        return None
    return (match.group(1), match.group(2), len(text.encode("utf-8")))


def _exercise_marker(text: str, *, marker_only: bool = False):
    expression = _ANSWER_EXERCISE if marker_only else _EXERCISE
    match = expression.fullmatch(text)
    if match is None:
        return None
    digit = match.group(1) or match.group(2)
    token = f"Q{digit}"
    prefix = f"Q{digit}）" if match.group(1) else f"\\item[Q{digit}）]"
    return (token, len(prefix.encode("utf-8")))


def _looks_like_invalid_marker(text: str) -> bool:
    stripped = text.lstrip(" \t\v\f")
    return (
        stripped.startswith(("例題", "例题"))
        or re.match(r"(?:Q|Ｑ)(?:[0-9０-９（(])", stripped) is not None
        or stripped.startswith(("\\item[Q", "\\item[Ｑ"))
    )


def _is_han(character: str) -> bool:
    value = ord(character)
    return (
        0x3400 <= value <= 0x4DBF
        or 0x4E00 <= value <= 0x9FFF
        or 0xF900 <= value <= 0xFAFF
    )


def _is_latin(character: str) -> bool:
    return "A" <= character <= "Z" or "a" <= character <= "z"


def _char_byte_offsets(text: str, base: int) -> tuple[int, ...]:
    values = [base]
    for character in text:
        values.append(values[-1] + len(character.encode("utf-8")))
    return tuple(values)


def _prose_spans(
    member_path: str,
    text: str,
    base: int,
    excluded: tuple[tuple[int, int], ...],
) -> list[_SourceSpan]:
    offsets = _char_byte_offsets(text, base)
    excluded_chars: set[int] = set()
    for start_byte, end_byte in excluded:
        for index in range(len(text)):
            if offsets[index] >= start_byte and offsets[index + 1] <= end_byte:
                excluded_chars.add(index)
    available = [index for index in range(len(text)) if index not in excluded_chars]
    onsets = [index for index in available if _is_latin(text[index]) or _is_han(text[index])]
    first = onsets[0] if onsets else None
    first_han_after_latin = None
    first_language = None
    if first is not None:
        first_language = "zh" if _is_han(text[first]) else "en"
        if first_language == "en":
            first_han_after_latin = next(
                (index for index in onsets if index > first and _is_han(text[index])),
                None,
            )

    labels: dict[int, str] = {}
    for index in available:
        character = text[index]
        if first is None:
            labels[index] = "shared" if character in " \t" else "und"
        elif index < first and character in " \t":
            labels[index] = "shared"
        elif first_language == "zh":
            labels[index] = "zh"
        elif first_han_after_latin is not None and index >= first_han_after_latin:
            labels[index] = "zh"
        else:
            labels[index] = "en"

    spans: list[_SourceSpan] = []
    run_start = None
    run_language = None
    previous = None
    for index in available:
        language = labels[index]
        if (
            run_start is None
            or previous is None
            or index != previous + 1
            or language != run_language
        ):
            if run_start is not None and previous is not None:
                spans.append(
                    _SourceSpan(
                        member_path,
                        offsets[run_start],
                        offsets[previous + 1],
                        "question",
                        run_language,
                    )
                )
            run_start = index
            run_language = language
        previous = index
    if run_start is not None and previous is not None:
        spans.append(
            _SourceSpan(
                member_path,
                offsets[run_start],
                offsets[previous + 1],
                "question",
                run_language,
            )
        )
    return spans


def _raw_target_reason(raw_target: str) -> str | None:
    if raw_target.startswith(("//", "\\\\")) or _DRIVE_OR_UNC.match(raw_target):
        return "image_target_drive_or_unc"
    if raw_target.startswith("/"):
        return "image_target_absolute"
    if "\\" in raw_target:
        return "image_target_backslash"
    parts = raw_target.split("/")
    permitted_leading_dot = len(parts) >= 2 and parts[0] == "." and parts[1] == "images"
    checked_parts = parts[1:] if permitted_leading_dot else parts
    if ".." in checked_parts:
        return "image_target_traversal"
    tail = parts[2:] if permitted_leading_dot else checked_parts
    if permitted_leading_dot and (
        not tail or any(part in {"", "."} for part in tail)
    ):
        return "image_target_dot_or_empty_component"
    return None


def _target_needs_canonicalization(raw_target: str) -> bool:
    canonical = raw_target[2:]
    return (
        unicodedata.normalize("NFC", raw_target) != raw_target
        or any(unicodedata.category(character) == "Cc" for character in raw_target)
        or PurePosixPath(canonical).suffix not in _IMAGE_SUFFIXES
        or PurePosixPath(canonical).as_posix() != canonical
    )


def _scan_inline_atomics(
    member: _SourceMember,
    field: str,
    scan_text: str,
    scan_start: int,
    content_end: int,
    issues: list[MmdAdapterIssue],
    target_records: list[tuple[str, str, int, int]],
) -> list[tuple[int, int, str, str | None]]:
    offsets = _char_byte_offsets(scan_text, scan_start)
    atomic: list[tuple[int, int, str, str | None]] = []
    cursor = 0
    while cursor < len(scan_text):
        if scan_text.startswith("$$", cursor):
            start_byte = offsets[cursor]
            issues.append(
                _parse_issue(member, field, "unsupported_grammar", start_byte, content_end)
            )
            atomic.append((start_byte, content_end, "shared", None))
            cursor = len(scan_text)
            continue
        if scan_text.startswith("![", cursor):
            complete = re.match(r"!\[\]\(([^)]*)\)", scan_text[cursor:])
            if complete is None:
                start_byte = offsets[cursor]
                issues.append(
                    _parse_issue(member, field, "unsupported_grammar", start_byte, content_end)
                )
                cursor = len(scan_text)
                continue
            raw_target = complete.group(1)
            end_char = cursor + len(complete.group(0))
            start_byte = offsets[cursor]
            end_byte = offsets[end_char]
            target_records.append(
                (member.relative_path, raw_target, start_byte, end_byte)
            )
            reason = _raw_target_reason(raw_target)
            if reason is not None:
                issues.append(
                    _target_issue(member, raw_target, reason, start_byte, end_byte)
                )
                atomic.append((start_byte, end_byte, "shared", None))
            elif not raw_target.startswith("./images/"):
                issues.append(
                    _parse_issue(
                        member,
                        field,
                        "unsupported_grammar",
                        start_byte,
                        end_byte,
                    )
                )
                atomic.append((start_byte, end_byte, "shared", None))
            else:
                if _target_needs_canonicalization(raw_target):
                    atomic.append((start_byte, end_byte, "shared", None))
                else:
                    atomic.append((start_byte, end_byte, "image", raw_target))
            cursor = end_char
            continue
        if scan_text[cursor] == "$":
            opening_slashes = len(scan_text[:cursor]) - len(
                scan_text[:cursor].rstrip("\\")
            )
            if opening_slashes % 2:
                cursor += 1
                continue
            closing = cursor + 1
            while closing < len(scan_text):
                if scan_text[closing] == "$":
                    slash_count = len(scan_text[:closing]) - len(
                        scan_text[:closing].rstrip("\\")
                    )
                    if slash_count % 2 == 0:
                        break
                closing += 1
            if closing >= len(scan_text):
                issues.append(
                    _parse_issue(
                        member,
                        field,
                        "unclosed_token",
                        offsets[cursor],
                        content_end,
                    )
                )
                atomic.append((offsets[cursor], content_end, "shared", None))
                cursor = len(scan_text)
                continue
            atomic.append((offsets[cursor], offsets[closing + 1], "shared", None))
            cursor = closing + 1
            continue
        cursor += 1
    return atomic


def _validate_atomic_region(
    member: _SourceMember,
    lines: tuple[tuple[int, int, int, str], ...],
    start_byte: int,
    stop_byte: int,
    field: str,
    issues: list[MmdAdapterIssue],
    target_records: list[tuple[str, str, int, int]],
) -> None:
    region = tuple(
        line for line in lines if start_byte <= line[0] < stop_byte
    )
    index = 0
    while index < len(region):
        line_start, content_end, _line_end, text = region[index]
        if text == "$$":
            closing = next(
                (
                    candidate
                    for candidate in range(index + 1, len(region))
                    if region[candidate][3] == "$$"
                ),
                None,
            )
            if closing is None:
                issues.append(
                    _parse_issue(
                        member,
                        field,
                        "unclosed_token",
                        line_start,
                        stop_byte,
                    )
                )
                return
            index = closing + 1
            continue
        _scan_inline_atomics(
            member,
            field,
            text,
            line_start,
            min(content_end, stop_byte),
            issues,
            target_records,
        )
        index += 1


def _line_lex(
    member: _SourceMember,
    lines: tuple[tuple[int, int, int, str], ...],
    start_index: int,
    stop_byte: int,
    issues: list[MmdAdapterIssue],
    target_records: list[tuple[str, str, int, int]],
):
    text_spans: list[_SourceSpan] = []
    image_records: list[tuple[str, int, int]] = []
    itemize_depth = 0
    allow_outer_close = lines[start_index][3].startswith("\\item[Q")
    outer_close_consumed = False
    index = start_index
    immediately_after_marker = True
    immediately_after_reference = False
    while index < len(lines) and lines[index][0] < stop_byte:
        line_start, content_end, line_end, text = lines[index]
        line_end = min(line_end, stop_byte)
        content_end = min(content_end, stop_byte)

        if text == "$$":
            closing = None
            for candidate in range(index + 1, len(lines)):
                if lines[candidate][0] >= stop_byte:
                    break
                if lines[candidate][3] == "$$":
                    closing = candidate
                    break
            if closing is None:
                issues.append(
                    _parse_issue(member, "primary_member", "unclosed_token", line_start, stop_byte)
                )
                text_spans.append(
                    _SourceSpan(member.relative_path, line_start, stop_byte, "question", "shared")
                )
                return text_spans, image_records
            close_line_end = min(lines[closing][2], stop_byte)
            text_spans.append(
                _SourceSpan(
                    member.relative_path,
                    line_start,
                    close_line_end,
                    "question",
                    "shared",
                )
            )
            index = closing + 1
            immediately_after_marker = False
            immediately_after_reference = False
            continue

        structural_end = line_start
        marker = _example_marker(text)
        exercise = _exercise_marker(text)
        if marker is not None:
            structural_end = content_end
        elif exercise is not None:
            structural_end = line_start + exercise[1]
        elif text in {"\\begin{itemize}", "\\end{itemize}"}:
            if text == "\\begin{itemize}":
                next_index = index + 1
                while next_index < len(lines) and lines[next_index][3] == "":
                    next_index += 1
                starts_next_exercise = (
                    next_index < len(lines)
                    and lines[next_index][0] >= stop_byte
                    and _exercise_marker(lines[next_index][3]) is not None
                )
                if not starts_next_exercise:
                    itemize_depth += 1
            elif itemize_depth == 0:
                if allow_outer_close and not outer_close_consumed:
                    outer_close_consumed = True
                else:
                    issues.append(
                        _parse_issue(member, "primary_member", "unsupported_grammar", line_start, content_end)
                    )
            else:
                itemize_depth -= 1
            structural_end = content_end
        elif "\\begin{itemize}" in text or "\\end{itemize}" in text:
            issues.append(
                _parse_issue(member, "primary_member", "unsupported_grammar", line_start, content_end)
            )
            if "\\begin{itemize}" in text and "\\end{itemize}" not in text:
                itemize_depth += 1
        elif text == "參考" or text.startswith("參考 DSE"):
            structural_end = content_end
            immediately_after_reference = True
        elif text.startswith("DSE") and (immediately_after_marker or immediately_after_reference):
            structural_end = content_end
        else:
            item = _ITEM_PREFIX.match(text)
            if item is not None:
                structural_end = line_start + len(item.group(0).encode("utf-8"))

        if structural_end > line_start:
            text_spans.append(
                _SourceSpan(
                    member.relative_path,
                    line_start,
                    structural_end,
                    "question",
                    "shared",
                )
            )

        scan_start = structural_end
        scan_text = member.content[scan_start:content_end].decode("utf-8")
        atomic = _scan_inline_atomics(
            member,
            "primary_member",
            scan_text,
            scan_start,
            content_end,
            issues,
            target_records,
        )
        image_records.extend(
            (raw_target, start_byte, end_byte)
            for start_byte, end_byte, kind, raw_target in atomic
            if kind == "image" and raw_target is not None
        )

        excluded = tuple((start, end) for start, end, _kind, _target in atomic)
        text_spans.extend(_prose_spans(member.relative_path, scan_text, scan_start, excluded))
        for atomic_start, atomic_end, kind, raw_target in atomic:
            if kind == "image":
                continue
            text_spans.append(
                _SourceSpan(
                    member.relative_path,
                    atomic_start,
                    atomic_end,
                    "question",
                    "shared",
                )
            )
        if content_end < line_end:
            final_span = None
            if text:
                non_image = [span for span in text_spans if span.end_byte <= content_end]
                if non_image:
                    candidate = max(non_image, key=lambda span: span.end_byte)
                    if candidate.end_byte == content_end:
                        final_span = candidate
            if final_span is None:
                text_spans.append(
                    _SourceSpan(
                        member.relative_path,
                        content_end,
                        line_end,
                        "question",
                        "shared",
                    )
                )
            else:
                text_spans[text_spans.index(final_span)] = _SourceSpan(
                    final_span.member_path,
                    final_span.start_byte,
                    line_end,
                    final_span.role,
                    final_span.language,
                )
        immediately_after_marker = index == start_index
        if not (text == "參考" or text.startswith("參考 DSE")):
            immediately_after_reference = False
        index += 1

    if itemize_depth:
        begin = next(
            (line[0] for line in lines[start_index:] if line[3] == "\\begin{itemize}"),
            stop_byte,
        )
        issues.append(
            _parse_issue(member, "primary_member", "unsupported_grammar", begin, stop_byte)
        )
    return text_spans, image_records


def _parse_answers(member: _SourceMember, issues: list[MmdAdapterIssue]):
    try:
        member.content.decode("utf-8")
    except UnicodeDecodeError:
        issues.append(_parse_issue(member, "answer_member", "invalid_utf8"))
        return {}
    lines = tuple(_physical_lines(member.content))
    occurrences: list[tuple[str, int, int]] = []
    index = 0
    while index < len(lines):
        start, content_end, line_end, text = lines[index]
        if text == "":
            index += 1
            continue
        marker = _example_marker(text)
        exercise = _exercise_marker(text, marker_only=True)
        if marker is not None:
            number = marker[1]
        elif exercise is not None:
            number = exercise[0]
        else:
            issues.append(
                _parse_issue(member, "answer_member", "unsupported_grammar", start, content_end)
            )
            return {}
        index += 1
        while index < len(lines) and lines[index][3] == "":
            index += 1
        if index >= len(lines) or lines[index][3] not in {"題解：", "題解 ："}:
            end = lines[index][1] if index < len(lines) else content_end
            issues.append(
                _parse_issue(member, "answer_member", "broken_boundary", start, end)
            )
            continue
        body_start = lines[index][2]
        index += 1
        body_end = len(member.content)
        probe = index
        in_display_math = False
        while probe < len(lines):
            candidate = lines[probe][3]
            if candidate == "$$":
                in_display_math = not in_display_math
                probe += 1
                continue
            if not in_display_math and (
                _example_marker(candidate) is not None
                or _exercise_marker(candidate, marker_only=True) is not None
            ):
                body_end = lines[probe][0]
                break
            probe += 1
        occurrences.append((number, body_start, body_end))
        index = probe
    result: dict[str, list[tuple[int, int]]] = {}
    for number, start, end in occurrences:
        result.setdefault(number, []).append((start, end))
    return result


def _parse_source_document(
    primary_member: _SourceMember,
    answer_member: _SourceMember | None = None,
) -> _SourceDocument:
    document, _target_records = _parse_source_document_with_inventory(
        primary_member,
        answer_member,
        (),
        (),
    )
    return document


def _parse_source_document_with_inventory(
    primary_member: _SourceMember,
    answer_member: _SourceMember | None,
    source_inventory: tuple[str, ...],
    image_members: tuple[_SourceMember, ...],
) -> tuple[_SourceDocument, tuple[tuple[str, str, int, int], ...]]:
    if type(primary_member) is not _SourceMember:
        raise PipelineError("primary_member must be an exact _SourceMember")
    if answer_member is not None and type(answer_member) is not _SourceMember:
        raise PipelineError("answer_member must be an exact _SourceMember or None")
    if type(source_inventory) is not tuple or any(
        type(member) is not str for member in source_inventory
    ):
        raise PipelineError("source_inventory must be an exact tuple of strings")
    if type(image_members) is not tuple or any(
        type(member) is not _SourceMember for member in image_members
    ):
        raise PipelineError("image_members must be an exact tuple of SourceMember values")

    issues: list[MmdAdapterIssue] = []
    for member, field in (
        (primary_member, "primary_member"),
        (answer_member, "answer_member"),
    ):
        if member is None:
            continue
        try:
            member.content.decode("utf-8")
        except UnicodeDecodeError:
            issues.append(_parse_issue(member, field, "invalid_utf8"))
    if issues:
        raise MmdAdapterBlockedError(tuple(issues))

    lines = tuple(_physical_lines(primary_member.content))
    occurrences: list[dict[str, object]] = []
    active_section = False
    in_display_math = False
    current: dict[str, object] | None = None
    for line_index, (start, content_end, line_end, text) in enumerate(lines):
        if text == "$$":
            in_display_math = not in_display_math
            continue
        if in_display_math:
            continue
        if text == "應試練習":
            active_section = True
            continue
        example = _example_marker(text)
        exercise = _exercise_marker(text)
        if example is not None:
            active_section = False
            if current is not None:
                current["end"] = start
            current = {
                "start": start,
                "end": len(primary_member.content),
                "line_index": line_index,
                "number": example[1],
                "section": example[0],
                "solution_markers": [],
            }
            occurrences.append(current)
            continue
        if exercise is not None:
            if not active_section:
                issues.append(
                    _parse_issue(
                        primary_member,
                        "primary_member",
                        "missing_section",
                        start,
                        start + exercise[1],
                    )
                )
                continue
            if current is not None:
                current["end"] = start
            current = {
                "start": start,
                "end": len(primary_member.content),
                "line_index": line_index,
                "number": exercise[0],
                "section": "應試練習",
                "solution_markers": [],
            }
            occurrences.append(current)
            continue
        if text in {"題解：", "題解 ："}:
            if current is None:
                issues.append(
                    _parse_issue(
                        primary_member,
                        "primary_member",
                        "broken_boundary",
                        start,
                        content_end,
                    )
                )
            else:
                current["solution_markers"].append((start, line_end))
            continue
        if _looks_like_invalid_marker(text):
            issues.append(
                _parse_issue(
                    primary_member,
                    "primary_member",
                    "unsupported_grammar",
                    start,
                    content_end,
                )
            )

    answers = _parse_answers(answer_member, issues) if answer_member is not None else {}
    questions: list[_SourceQuestion] = []
    target_records: list[tuple[str, str, int, int]] = []
    image_records_by_question: list[list[tuple[str, int, int]]] = []
    text_spans_by_question: list[list[_SourceSpan]] = []
    for order, occurrence in enumerate(occurrences):
        start = int(occurrence["start"])
        boundary = int(occurrence["end"])
        local_markers = list(occurrence["solution_markers"])
        fragment_end = int(local_markers[0][0]) if local_markers else boundary
        text_spans, image_records = _line_lex(
            primary_member,
            lines,
            int(occurrence["line_index"]),
            fragment_end,
            issues,
            target_records,
        )
        text_spans_by_question.append(text_spans)
        image_records_by_question.append(image_records)

        solution_spans: list[_SourceSpan] = []
        if local_markers:
            for index, (_marker_start, body_start) in enumerate(local_markers):
                body_end = (
                    int(local_markers[index + 1][0])
                    if index + 1 < len(local_markers)
                    else boundary
                )
                _validate_atomic_region(
                    primary_member,
                    lines,
                    int(body_start),
                    body_end,
                    "primary_member",
                    issues,
                    target_records,
                )
                if int(body_start) < body_end:
                    solution_spans.append(
                        _SourceSpan(
                            primary_member.relative_path,
                            int(body_start),
                            body_end,
                            "solution",
                            "und",
                        )
                    )
        elif answer_member is not None:
            matches = answers.get(str(occurrence["number"]), [])
            if len(matches) == 1 and matches[0][0] < matches[0][1]:
                solution_spans.append(
                    _SourceSpan(
                        answer_member.relative_path,
                        matches[0][0],
                        matches[0][1],
                        "solution",
                        "und",
                    )
                )

        questions.append(
            _SourceQuestion(
                order,
                str(occurrence["number"]),
                str(occurrence["section"]),
                _SourceSpan(
                    primary_member.relative_path,
                    start,
                    fragment_end,
                    "question",
                    "und",
                ),
                text_spans,
                solution_spans,
                (),
                (),
            )
        )

    if answer_member is not None:
        answer_lines = tuple(_physical_lines(answer_member.content))
        for body_start, body_end in sorted(
            span for spans in answers.values() for span in spans
        ):
            _validate_atomic_region(
                answer_member,
                answer_lines,
                body_start,
                body_end,
                "answer_member",
                issues,
                target_records,
            )

    # Collision diagnostics are bound to the first occurrence in each complete
    # colliding group, independent of physical discovery order elsewhere.
    normalized_groups: dict[
        str,
        tuple[list[tuple[str, str, int, int]], set[str]],
    ] = {}
    casefold_groups: dict[
        str,
        tuple[list[tuple[str, str, int, int]], set[str]],
    ] = {}
    for record in target_records:
        raw_target = record[1]
        if _raw_target_reason(raw_target) is not None or not raw_target.startswith("./images/"):
            continue
        source_path = raw_target[2:]
        normalized = unicodedata.normalize("NFC", source_path)
        normalized_targets, normalized_spellings = normalized_groups.setdefault(
            normalized,
            ([], set()),
        )
        normalized_targets.append(record)
        normalized_spellings.add(source_path)
        casefold_targets, casefold_spellings = casefold_groups.setdefault(
            normalized.casefold(),
            ([], set()),
        )
        casefold_targets.append(record)
        casefold_spellings.add(normalized)
    for source_path in source_inventory:
        normalized = unicodedata.normalize("NFC", source_path)
        normalized_groups.setdefault(normalized, ([], set()))[1].add(source_path)
        casefold_groups.setdefault(normalized.casefold(), ([], set()))[1].add(normalized)
    collision_records: set[tuple[str, str, int, int]] = set()
    member_by_path = {primary_member.relative_path: primary_member}
    if answer_member is not None:
        member_by_path[answer_member.relative_path] = answer_member
    for records, spellings in normalized_groups.values():
        if records and len(spellings) > 1:
            record = records[0]
            issues.append(
                _target_issue(
                    member_by_path[record[0]],
                    record[1],
                    "image_target_nfc_collision",
                    record[2],
                    record[3],
                )
            )
            collision_records.update(records)
    for records, spellings in casefold_groups.values():
        if (
            records
            and len(spellings) > 1
            and not any(record in collision_records for record in records)
        ):
            record = records[0]
            issues.append(
                _target_issue(
                    member_by_path[record[0]],
                    record[1],
                    "image_target_casefold_collision",
                    record[2],
                    record[3],
                )
            )
            collision_records.update(records)
    for member_path, raw_target, start, end in target_records:
        record = (member_path, raw_target, start, end)
        if (
            record not in collision_records
            and _raw_target_reason(raw_target) is None
            and raw_target.startswith("./images/")
            and _target_needs_canonicalization(raw_target)
        ):
            issues.append(
                _target_issue(
                    member_by_path[member_path],
                    raw_target,
                    "image_target_canonicalization",
                    start,
                    end,
                )
            )

    if issues:
        raise MmdAdapterBlockedError(tuple(issues))

    image_paths = {member.relative_path for member in image_members}
    finalized: list[_SourceQuestion] = []
    for question, image_records in zip(questions, image_records_by_question):
        refs = tuple(
            _SourceImageRef(
                index,
                _SourceSpan(
                    primary_member.relative_path,
                    start,
                    end,
                    "image_token",
                    "shared",
                ),
                raw_target,
                raw_target[2:] if raw_target[2:] in image_paths else None,
            )
            for index, (raw_target, start, end) in enumerate(image_records)
        )
        finalized.append(
            _SourceQuestion(
                question.source_order,
                question.source_question_number,
                question.source_section,
                question.fragment_span,
                question.text_spans,
                question.solution_spans,
                question.explanation_spans,
                refs,
            )
        )

    members = [primary_member]
    if answer_member is not None:
        members.append(answer_member)
    members.extend(image_members)
    return (
        _SourceDocument(primary_member.relative_path, members, finalized),
        tuple(target_records),
    )
