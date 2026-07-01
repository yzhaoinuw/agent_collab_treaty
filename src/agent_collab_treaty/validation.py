"""Validation helpers for installed Agent Collab Treaty docs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path
import re
from typing import Iterable


DATE_HEADING_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2})\s*$")
SESSION_HEADING_RE = re.compile(r"^### (.+?)\s*$")
SESSION_METADATA_RE = re.compile(r"^### .+\([^()]+\)\s*$")
MARKDOWN_LINK_ANCHOR_RE = re.compile(r"\[[^\]]+\]\(#([^)]+)\)")

REQUIRED_PATHS = (
    "AGENTS.md",
    "project_overview.md",
    "next_steps.md",
    "work_log.md",
    "work_log_archive",
)


@dataclass(frozen=True)
class ValidationIssue:
    """One treaty validation issue with a stable code and source location."""

    path: Path
    line: int
    code: str
    message: str


@dataclass(frozen=True)
class RequiredPathState:
    """Actual filesystem matches for one canonical treaty path."""

    canonical: Path
    exact: Path | None
    case_insensitive_matches: tuple[Path, ...]


def validate_project(root: Path, today: date | None = None) -> list[ValidationIssue]:
    """Validate standard treaty files under root.

    ``today`` is the local reference date for the future-date check; it defaults
    to ``date.today()`` and is injectable so tests stay deterministic.
    """

    root = root.expanduser().resolve()
    if today is None:
        today = date.today()
    issues: list[ValidationIssue] = []
    required_paths = _inspect_required_paths(root)
    issues.extend(_validate_required_paths(required_paths))

    work_log = required_paths["work_log.md"].exact
    if work_log is not None:
        issues.extend(_validate_work_log(work_log, today))

    next_steps = required_paths["next_steps.md"].exact
    if next_steps is not None:
        issues.extend(_validate_next_steps(next_steps))

    return issues


def format_issue(issue: ValidationIssue, root: Path) -> str:
    """Return a file:line issue string for CLI output."""

    root = root.expanduser().resolve()
    try:
        path = issue.path.resolve().relative_to(root)
    except ValueError:
        path = issue.path
    return f"{path}:{issue.line}: {issue.code}: {issue.message}"


def _inspect_required_paths(root: Path) -> dict[str, RequiredPathState]:
    entries = tuple(root.iterdir()) if root.exists() else ()
    states: dict[str, RequiredPathState] = {}

    for relative in REQUIRED_PATHS:
        canonical = root / relative
        matches = tuple(entry for entry in entries if entry.name.lower() == relative.lower())
        exact = next((entry for entry in matches if entry.name == relative), None)
        states[relative] = RequiredPathState(
            canonical=canonical,
            exact=exact,
            case_insensitive_matches=matches,
        )

    return states


def _validate_required_paths(
    states: dict[str, RequiredPathState],
) -> Iterable[ValidationIssue]:
    for relative, state in states.items():
        if not state.case_insensitive_matches:
            yield ValidationIssue(
                path=state.canonical,
                line=1,
                code="missing-required-file",
                message=f"Required treaty path is missing: {relative}",
            )
            continue

        if len(state.case_insensitive_matches) > 1:
            found = ", ".join(path.name for path in state.case_insensitive_matches)
            yield ValidationIssue(
                path=state.exact or state.case_insensitive_matches[0],
                line=1,
                code="path-case-collision",
                message=(
                    f"Multiple treaty paths match {relative!r} by case-insensitive name: "
                    f"{found}. Keep one canonical path named {relative!r}."
                ),
            )
            continue

        if state.exact is None:
            found = state.case_insensitive_matches[0]
            yield ValidationIssue(
                path=found,
                line=1,
                code="noncanonical-path-case",
                message=(
                    f"Found {found.name!r}, but the canonical treaty path is {relative!r}. "
                    "Rename or migrate it before validating treaty content."
                ),
            )


def _validate_work_log(path: Path, today: date) -> Iterable[ValidationIssue]:
    lines = _read_lines(path)
    content = list(_without_html_comments(lines))

    date_headings: list[tuple[int, str]] = []
    session_headings: list[tuple[int, str, int]] = []

    for content_index, (line_number, line) in enumerate(content):
        date_match = DATE_HEADING_RE.match(line)
        if date_match:
            date_headings.append((line_number, date_match.group(1)))
            continue

        session_match = SESSION_HEADING_RE.match(line)
        if session_match:
            session_headings.append((line_number, line, content_index))
            if not SESSION_METADATA_RE.match(line):
                yield ValidationIssue(
                    path=path,
                    line=line_number,
                    code="work-log-missing-session-metadata",
                    message="Session heading should end with '(model + version, effort/thinking mode, token budget if known)'.",
                )

    seen_dates: set[str] = set()
    for line_number, date_value in date_headings:
        if date_value in seen_dates:
            yield ValidationIssue(
                path=path,
                line=line_number,
                code="work-log-duplicate-date",
                message=f"Duplicate date heading {date_value}; add another session under the first date heading instead.",
            )
        seen_dates.add(date_value)

        try:
            parsed = date.fromisoformat(date_value)
        except ValueError:
            continue
        if parsed > today:
            yield ValidationIssue(
                path=path,
                line=line_number,
                code="work-log-future-date",
                message=(
                    f"Work-log date {date_value} is in the future (local today is "
                    f"{today.isoformat()}); verify the workstation date before dating an entry."
                ),
            )

    if len(date_headings) > 5:
        line_number, date_value = date_headings[5]
        yield ValidationIssue(
            path=path,
            line=line_number,
            code="work-log-rotation-needed",
            message=f"Live work_log.md has more than 5 unique dates; rotate starting at {date_value}.",
        )

    for index, (line_number, _, content_index) in enumerate(session_headings):
        next_content_index = (
            session_headings[index + 1][2]
            if index + 1 < len(session_headings)
            else len(content)
        )
        segment = [line for _, line in content[content_index + 1 : next_content_index]]
        if not any(_is_verification_heading(line) for line in segment):
            yield ValidationIssue(
                path=path,
                line=line_number,
                code="work-log-missing-verification",
                message="Session entry should include a '- Verification:' subsection.",
            )


def _validate_next_steps(path: Path) -> Iterable[ValidationIssue]:
    lines = _read_lines(path)
    content = list(_without_html_comments(lines))
    anchors = _heading_anchors(content)

    current_hot_start: int | None = None
    current_hot_end = len(content)
    for index, (_, line) in enumerate(content):
        if line.strip() == "## Currently Hot":
            current_hot_start = index
            continue
        if current_hot_start is not None and index > current_hot_start and line.startswith("## "):
            current_hot_end = index
            break

    if current_hot_start is None:
        yield ValidationIssue(
            path=path,
            line=1,
            code="next-steps-missing-currently-hot",
            message="next_steps.md should include a '## Currently Hot' section.",
        )
        return

    for line_number, line in content[current_hot_start:current_hot_end]:
        for anchor in MARKDOWN_LINK_ANCHOR_RE.findall(line):
            if anchor not in anchors:
                yield ValidationIssue(
                    path=path,
                    line=line_number,
                    code="next-steps-broken-hot-link",
                    message=f"Currently Hot link points to missing anchor: #{anchor}",
                )


def _heading_anchors(lines: Iterable[tuple[int, str]]) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    for _, line in lines:
        if not line.startswith("#"):
            continue
        match = re.match(r"^#{2,6}\s+(.+?)\s*$", line)
        if not match:
            continue
        base = _github_anchor(match.group(1))
        count = counts.get(base, 0)
        counts[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")
    return anchors


def _is_verification_heading(line: str) -> bool:
    stripped = line.strip()
    return stripped == "- Verification:" or (
        stripped.startswith("- Verification ") and stripped.endswith(":")
    )


def _github_anchor(text: str) -> str:
    text = text.replace("`", "").lower()
    text = re.sub(r"[^a-z0-9 \-]", "", text)
    text = re.sub(r"\s+", "-", text.strip())
    text = re.sub(r"-+", "-", text)
    return text


def _without_html_comments(lines: Iterable[str]) -> Iterable[tuple[int, str]]:
    in_comment = False
    for line_number, line in enumerate(lines, start=1):
        if in_comment:
            if "-->" in line:
                in_comment = False
            continue

        if "<!--" in line:
            before, _, after = line.partition("<!--")
            if before.strip():
                yield line_number, before
            if "-->" not in after:
                in_comment = True
            continue

        yield line_number, line


def _read_lines(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()
