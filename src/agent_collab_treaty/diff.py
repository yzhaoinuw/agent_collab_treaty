"""Section-level drift between an installed treaty and its pristine render.

``treaty diff`` renders the template version a project is pinned to into a
temporary directory and compares it section by section with what's on disk.
The point is to show conflict exposure *before* ``treaty update`` runs: a
section the adopter deleted or renamed is where an upstream revision turns
into an unresolvable conflict, while an added section always merges cleanly.
"""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Sequence

SECTION_HEADING_RE = re.compile(r"^(## .+?)\s*$", re.MULTILINE)

#: Bodies at least this similar mark a removed/added heading pair as a rename.
RENAME_SIMILARITY = 0.6

PREAMBLE_KEY = "(preamble)"

#: Files whose content is the adopter's own from day one. Their sections drift
#: by design, so reporting them as risk would bury the signal.
ADOPTER_OWNED = frozenset({"work_log.md", "next_steps.md"})


@dataclass(frozen=True)
class Rename:
    """A removed heading whose body survived under a new heading."""

    old: str
    new: str
    similarity: float


@dataclass
class FileDiff:
    """Section-level comparison of one rendered file against its local copy."""

    path: str
    untouched: list[str] = field(default_factory=list)
    modified: list[str] = field(default_factory=list)
    removed: list[str] = field(default_factory=list)
    added: list[str] = field(default_factory=list)
    renamed: list[Rename] = field(default_factory=list)
    missing_locally: bool = False
    adopter_owned: bool = False

    @property
    def at_risk(self) -> int:
        """Sections where an upstream revision would land as a conflict."""
        if self.adopter_owned:
            return 0
        return len(self.modified) + len(self.removed) + len(self.renamed)


def split_sections(text: str) -> dict[str, str]:
    """Split Markdown into ``{'## Heading': body}``, keyed in document order.

    Anything before the first ``##`` heading is collected under
    :data:`PREAMBLE_KEY`. Repeated headings keep only the first occurrence,
    which matches how a three-way merge anchors on them.
    """

    sections: dict[str, str] = {}
    matches = list(SECTION_HEADING_RE.finditer(text))

    preamble = text[: matches[0].start()] if matches else text
    if preamble.strip():
        sections[PREAMBLE_KEY] = preamble.strip()

    for index, match in enumerate(matches):
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        heading = match.group(1)
        if heading in sections:
            continue
        sections[heading] = text[match.end() : end].strip()

    return sections


def detect_renames(
    removed: Sequence[str],
    added: Sequence[str],
    pristine: dict[str, str],
    local: dict[str, str],
    threshold: float = RENAME_SIMILARITY,
) -> list[Rename]:
    """Pair removed and added headings whose bodies are near-identical.

    A renamed heading reads to a three-way merge as a delete plus an unrelated
    add, so it is worth calling out separately from either.
    """

    renames: list[Rename] = []
    unclaimed = list(added)

    for old in removed:
        best: tuple[float, str] | None = None
        for new in unclaimed:
            ratio = difflib.SequenceMatcher(
                None, pristine.get(old, ""), local.get(new, "")
            ).ratio()
            if ratio >= threshold and (best is None or ratio > best[0]):
                best = (ratio, new)
        if best is not None:
            renames.append(Rename(old=old, new=best[1], similarity=best[0]))
            unclaimed.remove(best[1])

    return renames


def compare_file(path: str, pristine_text: str, local_text: str | None) -> FileDiff:
    """Classify one file's sections as untouched, modified, removed, or added."""

    result = FileDiff(path=path, adopter_owned=path in ADOPTER_OWNED)
    if local_text is None:
        result.missing_locally = True
        return result

    pristine = split_sections(pristine_text)
    local = split_sections(local_text)

    for heading, body in pristine.items():
        if heading not in local:
            result.removed.append(heading)
        elif local[heading] == body:
            result.untouched.append(heading)
        else:
            result.modified.append(heading)

    result.added = [heading for heading in local if heading not in pristine]
    result.renamed = detect_renames(result.removed, result.added, pristine, local)

    renamed_old = {rename.old for rename in result.renamed}
    renamed_new = {rename.new for rename in result.renamed}
    result.removed = [h for h in result.removed if h not in renamed_old]
    result.added = [h for h in result.added if h not in renamed_new]

    return result


def compare_trees(pristine_root: Path, local_root: Path) -> list[FileDiff]:
    """Compare every Markdown file in a pristine render against a project."""

    diffs: list[FileDiff] = []
    for rendered in sorted(pristine_root.rglob("*.md")):
        relative = rendered.relative_to(pristine_root).as_posix()
        local = local_root / relative
        diffs.append(
            compare_file(
                relative,
                _read(rendered),
                _read(local) if local.is_file() else None,
            )
        )
    return diffs


def format_report(diffs: Iterable[FileDiff], template_version: str | None) -> list[str]:
    """Render the human-readable ``treaty diff`` output."""

    diffs = list(diffs)
    lines = [
        f"Comparing this project against a clean render of template version "
        f"{template_version or 'unknown'}.",
        "",
    ]

    for diff in diffs:
        lines.append(diff.path)
        if diff.missing_locally:
            lines.append("  missing locally — treaty update will add it")
            lines.append("")
            continue

        counts = (
            f"  untouched {len(diff.untouched)}"
            f"   modified {len(diff.modified)}"
            f"   removed {len(diff.removed)}"
            f"   added {len(diff.added)}"
        )
        if diff.renamed:
            counts += f"   renamed {len(diff.renamed)}"
        lines.append(counts)

        if diff.adopter_owned:
            lines.append("  (your content by design — drift here is expected)")
            lines.append("")
            continue

        for rename in diff.renamed:
            lines.append(
                f"  ! renamed: {rename.old!r} -> {rename.new!r} "
                "— restore the upstream heading and keep your body; a rename "
                "cannot be auto-merged"
            )
        for heading in diff.removed:
            lines.append(
                f"  ! removed: {heading!r} — upstream edits arrive with nothing "
                "local to merge into"
            )
        for heading in diff.modified:
            lines.append(f"  ~ modified: {heading!r}")
        lines.append("")

    at_risk = sum(diff.at_risk for diff in diffs)
    files_at_risk = sum(1 for diff in diffs if diff.at_risk)
    lines.append(
        f"Conflict exposure: {at_risk} section(s) across {files_at_risk} file(s) "
        "would conflict if upstream revises them."
    )
    if any(diff.renamed for diff in diffs):
        lines.append(
            "Renamed headings are the costliest drift — see 'Customizing These "
            "Docs' in treaty_conventions.md."
        )
    lines.append("Nothing was written. Run 'treaty update --dry-run' to preview a merge.")
    return lines


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")
