"""Validation helpers for installed Agent Collab Treaty docs."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path, PurePosixPath
import re
import subprocess
from typing import Iterable


ANSWERS_FILE = ".copier-answers.yml"

DATE_HEADING_RE = re.compile(r"^## (\d{4}-\d{2}-\d{2})\s*$")
SESSION_HEADING_RE = re.compile(r"^### (.+?)\s*$")
SESSION_METADATA_RE = re.compile(r"^### .+\([^()]+\)\s*$")
MARKDOWN_LINK_ANCHOR_RE = re.compile(r"\[[^\]]+\]\(#([^)]+)\)")

# Docs that always live at the repo root. AGENTS.md is fixed there by the
# AGENTS.md convention itself (agents resolve the *nearest* file up the tree, so
# a nested one would scope to the wrong subtree); project_overview.md is kept
# alongside it as the human-facing entry point.
ROOT_REQUIRED_NAMES = (
    "AGENTS.md",
    "project_overview.md",
)

# Docs that live under ``docs_dir`` — the repo root when that answer is "." .
DOCS_REQUIRED_NAMES = (
    "next_steps.md",
    "work_log.md",
    "work_log_archive",
)

# Flat-layout view, kept as the module-level default for callers that reason
# about treaty paths without a project in hand (see ``adoption``).
REQUIRED_PATHS = ROOT_REQUIRED_NAMES + DOCS_REQUIRED_NAMES


def resolve_docs_dir(root: Path) -> str:
    """Return the treaty docs folder for ``root`` ("." means the repo root).

    Prefers the recorded Copier answer. Projects maintained without Copier have
    no answer to read, so fall back to detecting an actual layout on disk and
    finally to the flat root, which is what every pre-``docs_dir`` project used.
    """

    recorded = _recorded_docs_dir(root)
    if recorded:
        return recorded

    if (root / "work_log.md").exists():
        return "."
    for candidate in sorted(p for p in root.iterdir() if p.is_dir()) if root.exists() else []:
        if (candidate / "work_log.md").exists():
            return candidate.name
    return "."


def _recorded_docs_dir(root: Path) -> str | None:
    """Read ``docs_dir`` out of the project's Copier answers file, if present."""

    answers = root / ANSWERS_FILE
    if not answers.exists():
        return None
    try:
        import yaml

        data = yaml.safe_load(answers.read_text(encoding="utf-8"))
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    value = data.get("docs_dir")
    return value if isinstance(value, str) and value else None


def required_paths(docs_dir: str) -> tuple[str, ...]:
    """Canonical treaty paths, relative to the project root, for one layout."""

    if docs_dir in (".", ""):
        return REQUIRED_PATHS
    prefix = docs_dir.rstrip("/")
    return ROOT_REQUIRED_NAMES + tuple(f"{prefix}/{name}" for name in DOCS_REQUIRED_NAMES)


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
    docs_dir = resolve_docs_dir(root)
    paths = required_paths(docs_dir)
    states = _inspect_required_paths(root, paths)
    issues.extend(_validate_required_paths(states))
    issues.extend(_validate_answers_file(root))
    issues.extend(_validate_docs_not_ignored(root, states))

    docs_prefix = "" if docs_dir in (".", "") else f"{docs_dir.rstrip('/')}/"

    work_log = states[f"{docs_prefix}work_log.md"].exact
    if work_log is not None:
        issues.extend(_validate_work_log(work_log, today))

    next_steps = states[f"{docs_prefix}next_steps.md"].exact
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


def answers_file_ignored(root: Path) -> bool:
    """True when git ignores the Copier answers file in ``root``."""

    try:
        proc = subprocess.run(
            ["git", "-C", str(root), "check-ignore", "-q", ANSWERS_FILE],
            capture_output=True,
            check=False,
        )
    except OSError:
        return False
    return proc.returncode == 0


def _validate_answers_file(root: Path) -> Iterable[ValidationIssue]:
    """Flag a Copier answers file that git ignores.

    An ignored answers file lets an adopter commit an apparently successful
    installation whose metadata never reaches the repository, silently breaking
    every future `treaty update` and `treaty diff` from a fresh clone. A
    *missing* file is legitimate — treaty docs can be maintained without Copier
    management — so only the present-but-ignored state is an error.
    """

    answers = root / ANSWERS_FILE
    if not answers.exists():
        return
    if answers_file_ignored(root):
        yield ValidationIssue(
            path=answers,
            line=1,
            code="answers-file-gitignored",
            message=(
                f"git ignores {ANSWERS_FILE}, so it cannot be committed and "
                "future `treaty update`/`treaty diff` runs will not find it in "
                "a fresh clone. Remove the ignore rule and commit the file."
            ),
        )


def _validate_docs_not_ignored(
    root: Path, states: dict[str, RequiredPathState]
) -> Iterable[ValidationIssue]:
    """Flag treaty docs that git ignores.

    Same failure as an ignored answers file, one level out: the docs look
    installed but never reach the repository. It bites hardest after the docs
    move into a folder, because a deny-all ``.gitignore`` that re-allows the
    flat filenames stops matching the new paths — already-tracked files survive,
    so nothing looks wrong until a later work-log rotation adds a file that is
    silently untracked.
    """

    # Two subtleties decide how this is asked:
    #  * `git check-ignore` exempts paths already in the index, so docs moved in
    #    with `git mv` would report clean. `--no-index` asks the rules directly.
    #  * Probing an arbitrary new filename would false-positive on any repo with
    #    a deliberate deny-all `.gitignore` plus an allowlist, since ignoring
    #    unknown files is exactly what those repos intend. So probe the treaty's
    #    own canonical paths, plus one representative future archive chunk —
    #    the file a work-log rotation will actually try to add.
    probes: list[tuple[str, Path]] = []
    for relative, state in states.items():
        if state.exact is None:
            continue
        probes.append((relative, state.exact))
        if state.exact.is_dir():
            probes.append(
                (f"{relative}/work_log_1970-01-01_to_1970-01-02.md", state.exact)
            )

    for probe, anchor in sorted(probes):
        try:
            proc = subprocess.run(
                ["git", "-C", str(root), "check-ignore", "--no-index", "-q", probe],
                capture_output=True,
                check=False,
            )
        except OSError:
            return
        if proc.returncode == 0:
            yield ValidationIssue(
                path=anchor,
                line=1,
                code="treaty-doc-gitignored",
                message=(
                    f"git ignores {probe}, so this treaty doc cannot be "
                    "committed. A deny-all .gitignore that re-allows the old "
                    "flat filenames does this once the docs move into a folder: "
                    "files already tracked survive, but the next work-log "
                    "rotation is silently untracked. Allow the docs directory "
                    "and re-check with git check-ignore -v --no-index."
                ),
            )


def _inspect_required_paths(
    root: Path, paths: Iterable[str]
) -> dict[str, RequiredPathState]:
    listings: dict[Path, tuple[Path, ...]] = {}

    def entries_of(directory: Path) -> tuple[Path, ...]:
        if directory not in listings:
            listings[directory] = (
                tuple(directory.iterdir()) if directory.is_dir() else ()
            )
        return listings[directory]

    states: dict[str, RequiredPathState] = {}
    for relative in paths:
        canonical = root / relative
        name = PurePosixPath(relative).name
        entries = entries_of(canonical.parent)
        matches = tuple(entry for entry in entries if entry.name.lower() == name.lower())
        exact = next((entry for entry in matches if entry.name == name), None)
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
