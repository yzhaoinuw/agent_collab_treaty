"""Adoption preflight helpers for existing projects."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .validation import REQUIRED_PATHS


OVERLAPPING_DOC_NAMES = (
    "TODO.md",
    "TODOS.md",
    "ROADMAP.md",
    "NOTES.md",
    "PLAN.md",
    "PLANS.md",
    "PLANNING.md",
    "WORKLOG.md",
    "SESSION_LOG.md",
    "CLAUDE.md",
    "CODEX.md",
    "GEMINI.md",
    ".aider.conf.yml",
    ".cursorrules",
)

INIT_SKIP_IF_EXISTS = (
    ".copier-answers.yml",
    "AGENTS.md",
    "project_overview.md",
    "next_steps.md",
    "work_log.md",
    "work_log_archive/README.md",
    "CLAUDE.md",
    ".cursor/rules/treaty.mdc",
    ".windsurf/rules/treaty.md",
    ".aider.conf.yml",
)


@dataclass(frozen=True)
class AdoptionNotice:
    """One non-destructive adoption preflight notice."""

    code: str
    paths: tuple[str, ...]
    message: str


def inspect_adoption_context(root: Path) -> list[AdoptionNotice]:
    """Return concise notices about docs that may overlap with treaty init."""

    root = root.expanduser().resolve()
    entries = tuple(root.iterdir()) if root.exists() else ()
    notices: list[AdoptionNotice] = []

    entry_names = {entry.name for entry in entries}
    canonical_existing = tuple(relative for relative in REQUIRED_PATHS if relative in entry_names)
    if canonical_existing:
        notices.append(
            AdoptionNotice(
                code="existing-treaty-paths",
                paths=canonical_existing,
                message=(
                    "Existing canonical treaty paths found; init will not migrate or "
                    "archive them automatically."
                ),
            )
        )

    noncanonical_matches: list[str] = []
    required_lower = {relative.lower(): relative for relative in REQUIRED_PATHS}
    for entry in entries:
        canonical = required_lower.get(entry.name.lower())
        if canonical is not None and entry.name != canonical:
            noncanonical_matches.append(f"{entry.name} -> {canonical}")
    if noncanonical_matches:
        notices.append(
            AdoptionNotice(
                code="noncanonical-treaty-paths",
                paths=tuple(noncanonical_matches),
                message=(
                    "Case-mismatched treaty-looking paths found; keep them as history "
                    "or rename/migrate them yourself before relying on validation."
                ),
            )
        )

    overlapping_lower = {name.lower() for name in OVERLAPPING_DOC_NAMES}
    required_names_lower = {Path(relative).name.lower() for relative in REQUIRED_PATHS}
    overlapping = tuple(
        entry.name
        for entry in entries
        if entry.name.lower() in overlapping_lower
        and entry.name.lower() not in required_names_lower
    )
    if overlapping:
        notices.append(
            AdoptionNotice(
                code="overlapping-project-docs",
                paths=overlapping,
                message=(
                    "Existing project or agent docs may overlap with treaty planning "
                    "or logging; they are preserved as-is."
                ),
            )
        )

    return notices


def format_adoption_notices(notices: list[AdoptionNotice]) -> list[str]:
    """Format preflight notices for CLI output."""

    if not notices:
        return []

    lines = [
        "Adoption preflight: found existing docs that may overlap with the treaty.",
        (
            "No files will be moved, archived, rewritten, or deleted automatically; "
            "matching treaty template paths will be skipped."
        ),
    ]
    for notice in notices:
        lines.append(f"- {notice.code}: {', '.join(notice.paths)}")
        lines.append(f"  {notice.message}")
    return lines


def format_migration_hints(notices: list[AdoptionNotice]) -> list[str]:
    """Format non-destructive migration hints for validation output."""

    migration_notices = [
        notice
        for notice in notices
        if notice.code in {"noncanonical-treaty-paths", "overlapping-project-docs"}
    ]
    if not migration_notices:
        return []

    lines = [
        "Migration hints: found existing docs that may overlap with treaty adoption.",
        "treaty validate does not move, archive, rewrite, or delete files.",
    ]
    for notice in migration_notices:
        lines.append(f"- {notice.code}: {', '.join(notice.paths)}")
        lines.append(f"  {notice.message}")
    return lines
