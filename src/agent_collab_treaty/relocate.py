"""Move a project's treaty working docs between layouts.

Doing this by hand is four steps that must happen in the right order, and three
of them fail quietly when they go wrong:

* running the move before `treaty update` leaves the recorded answer disagreeing
  with the files on disk, so the *next* update renders its baseline at the old
  paths and conflicts;
* `AGENTS.md` keeps pointing at the old locations, and it is the one file every
  agent reads first;
* a deny-all `.gitignore` (``*`` plus an allowlist of ``!work_log.md``) stops
  matching once the files move, so anything added under the new folder later is
  silently untracked.

This module plans all of it up front, refuses to start when the ordering is
wrong, and reports what it cannot fix itself.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
import re
import subprocess

from .validation import ANSWERS_FILE, resolve_docs_dir

# Treaty docs that live in the docs folder and therefore move.
MOVABLE_NAMES = (
    "treaty_conventions.md",
    "next_steps.md",
    "work_log.md",
    "work_log_archive",
)

# Treaty docs that stay at the repo root and whose links need rewriting.
ROOT_DOC_NAMES = ("AGENTS.md", "project_overview.md")


@dataclass
class RelocationPlan:
    """Everything a relocation would do, computed before anything is written."""

    root: Path
    old_docs_dir: str
    new_docs_dir: str
    moves: list[tuple[Path, Path]] = field(default_factory=list)
    link_edits: list[tuple[Path, int]] = field(default_factory=list)
    outbound_edits: list[tuple[Path, int]] = field(default_factory=list)
    answers_update: bool = False
    blockers: list[str] = field(default_factory=list)
    external_refs: list[tuple[Path, int]] = field(default_factory=list)
    gitignore_risk: list[str] = field(default_factory=list)

    @property
    def is_noop(self) -> bool:
        return self.old_docs_dir == self.new_docs_dir


def docs_prefix(docs_dir: str) -> str:
    """Path prefix from the repo root into the docs folder ('' when flat)."""
    return "" if docs_dir in (".", "") else f"{docs_dir.strip('/')}/"


def root_prefix(docs_dir: str) -> str:
    """Path prefix from inside the docs folder back to the repo root."""
    if docs_dir in (".", ""):
        return ""
    return "../" * len(docs_dir.strip("/").split("/"))


def _git(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(root), *args], capture_output=True, text=True, check=False
    )


def _is_tracked(root: Path, path: Path) -> bool:
    rel = path.relative_to(root).as_posix()
    return _git(root, "ls-files", "--error-unmatch", rel).returncode == 0


def _tracked_files(root: Path) -> list[Path]:
    proc = _git(root, "ls-files")
    if proc.returncode != 0:
        return []
    return [root / line for line in proc.stdout.splitlines() if line]


def _retarget(text: str, old: str, new: str) -> tuple[str, int]:
    """Replace path references, ignoring ones already inside a longer path.

    The lookbehind is what stops ``work_log.md`` inside an already-correct
    ``treaty_docs/work_log.md`` from being rewritten a second time.
    """
    if old == new:
        return text, 0
    pattern = re.compile(r"(?<![A-Za-z0-9_./-])" + re.escape(old))
    return pattern.subn(new, text)


# Markdown link targets: `](target)` for inline links and images, and
# `[label]: target` for reference definitions.
_INLINE_TARGET = re.compile(
    r"(?P<pre>\]\(\s*<?)(?P<target>[^)<>\s]+)(?P<post>>?(?:\s+[\"'][^\"']*[\"'])?\s*\))"
)
_REFERENCE_TARGET = re.compile(
    r"(?m)^(?P<pre>\[[^\]]+\]:[ \t]+<?)(?P<target>[^\s<>]+)(?P<post>>?)"
)
_URL_SCHEME = re.compile(r"[A-Za-z][A-Za-z0-9+.-]*:")


def _relocated_target(
    target: str, root: Path, old_parent: Path, new_parent: Path, owned: set[Path]
) -> str | None:
    """Rewrite one project-relative link for a file that changed directory.

    Returns ``None`` to leave the link exactly as written. That is the answer
    for anything the move cannot invalidate — URLs, bare anchors, absolute
    paths, targets that escape the repo, and targets that do not resolve to a
    real file (already broken or historical, and not ours to guess at).

    Treaty-owned targets also return ``None``: docs that move in lockstep keep
    their relative path, and links to the root docs are the existing
    ``_retarget`` pass's job. Two passes rewriting one link would compound.
    """

    path_part, sep, fragment = target.partition("#")
    if not path_part or path_part.startswith("/"):
        return None
    # A percent-encoded path would have to be decoded to resolve and re-encoded
    # to write back; leaving it alone is the safe answer, not a silent mangle.
    if _URL_SCHEME.match(path_part) or "%" in path_part:
        return None

    old_target = Path(os.path.normpath(old_parent / path_part))
    if not old_target.is_relative_to(root) or not old_target.exists():
        return None
    if old_target in owned or any(
        old_target.is_relative_to(tree) for tree in owned if tree.is_dir()
    ):
        return None

    new_path = Path(os.path.relpath(old_target, new_parent)).as_posix()
    if path_part.endswith("/") and not new_path.endswith("/"):
        new_path += "/"
    if new_path == path_part:
        return None
    return f"{new_path}{sep}{fragment}"


def _rewrite_outbound(
    text: str, root: Path, old_parent: Path, new_parent: Path, owned: set[Path]
) -> tuple[str, int]:
    """Retarget every project-relative link in one moved document."""

    rewritten = 0

    def swap(match: re.Match) -> str:
        nonlocal rewritten
        new_target = _relocated_target(
            match.group("target"), root, old_parent, new_parent, owned
        )
        if new_target is None:
            return match.group(0)
        rewritten += 1
        return f"{match.group('pre')}{new_target}{match.group('post')}"

    for pattern in (_INLINE_TARGET, _REFERENCE_TARGET):
        text = pattern.sub(swap, text)
    return text, rewritten


def _moving_markdown_files(plan: RelocationPlan) -> list[tuple[Path, Path]]:
    """(old path, new path) for every Markdown file whose directory changes.

    Works before or after the move, so planning and applying share it: whichever
    side of a move is on disk is the one walked for directory contents.
    """

    pairs: list[tuple[Path, Path]] = []
    for source, destination in plan.moves:
        present = source if source.exists() else destination
        if present.is_dir():
            for path in sorted(present.rglob("*.md")):
                relative = path.relative_to(present)
                pairs.append((source / relative, destination / relative))
        elif present.suffix.lower() == ".md":
            pairs.append((source, destination))
    return pairs


def _owned_targets(root: Path, plan: RelocationPlan) -> set[Path]:
    """Paths whose links another pass already handles, or that move in lockstep."""

    owned = {root / name for name in ROOT_DOC_NAMES}
    owned |= {source for source, _ in plan.moves}
    return owned


def _plan_outbound_links(root: Path, plan: RelocationPlan) -> None:
    """Count project-relative links inside the moving docs that the move breaks.

    Reported separately from ``link_edits`` because these point *out* of the
    treaty set — at the project's own media, source, and docs. Until issue #24
    nothing rewrote them, so a link like ``media/README.md`` in a flat
    ``next_steps.md`` silently resolved to ``treaty_docs/media/README.md`` once
    the file moved, and both the dry run and `treaty validate` stayed quiet.
    """

    owned = _owned_targets(root, plan)
    for old_path, new_path in _moving_markdown_files(plan):
        if not old_path.is_file():
            continue
        text = old_path.read_text(encoding="utf-8")
        _, count = _rewrite_outbound(
            text, root, old_path.parent, new_path.parent, owned
        )
        if count:
            plan.outbound_edits.append((old_path, count))


def _doc_reference_pairs(old: str, new: str) -> list[tuple[str, str]]:
    """Old -> new reference strings for each movable doc, longest name first."""
    old_p, new_p = docs_prefix(old), docs_prefix(new)
    return [
        (f"{old_p}{name}", f"{new_p}{name}")
        for name in sorted(MOVABLE_NAMES, key=len, reverse=True)
    ]


def plan_relocation(root: Path, target: str) -> RelocationPlan:
    """Compute a full relocation plan without writing anything."""

    root = root.expanduser().resolve()
    current = resolve_docs_dir(root)
    target_clean = target.strip() or "."
    if target_clean != ".":
        target_clean = target_clean.strip("/")

    plan = RelocationPlan(root=root, old_docs_dir=current, new_docs_dir=target_clean)
    if plan.is_noop:
        return plan

    _check_ordering(root, plan)
    if _is_case_only_rename(root, plan):
        return plan
    _plan_moves(root, plan)
    _plan_link_edits(root, plan)
    _plan_outbound_links(root, plan)
    _plan_external_refs(root, plan)
    _plan_gitignore(root, plan)
    return plan


def _is_case_only_rename(root: Path, plan: RelocationPlan) -> bool:
    """Detect ``treaty_docs`` -> ``Treaty_Docs`` on a case-insensitive filesystem.

    There the two names are the same directory, so every destination looks
    occupied and the move planner emits one "already exists" blocker per doc —
    technically safe (nothing is touched) but it reads as four unrelated
    problems instead of the single unsupported operation it is. On a
    case-sensitive filesystem the names are genuinely different directories and
    the ordinary path handles it, so this only fires where it applies.
    """

    if plan.old_docs_dir.lower() != plan.new_docs_dir.lower():
        return False

    old_p, new_p = docs_prefix(plan.old_docs_dir), docs_prefix(plan.new_docs_dir)
    old_dir = root / old_p.rstrip("/") if old_p else root
    new_dir = root / new_p.rstrip("/") if new_p else root
    if not (old_dir.is_dir() and new_dir.is_dir()):
        return False
    try:
        if not old_dir.samefile(new_dir):
            return False
    except OSError:
        return False

    # Nothing will happen, so do not advertise an answers rewrite.
    plan.answers_update = False
    plan.blockers.append(
        f"{plan.old_docs_dir!r} and {plan.new_docs_dir!r} are the same directory "
        "on this filesystem, so this is a case-only rename and treaty relocate "
        "cannot do it in one step. Rename it yourself with two git moves "
        f"(git mv {plan.old_docs_dir} tmp-docs && git mv tmp-docs "
        f"{plan.new_docs_dir}), then update docs_dir in .copier-answers.yml to "
        "match."
    )
    return True


def _check_ordering(root: Path, plan: RelocationPlan) -> None:
    """Refuse to relocate a project whose template predates ``docs_dir``.

    Copier renders the update baseline from the *recorded* answers. A project
    with no ``docs_dir`` answer is pinned to a template version that hardcodes
    the flat paths, so moving the files first guarantees a conflict on the next
    update. Updating first records ``docs_dir: '.'`` and makes the move safe.
    """

    answers_path = root / ANSWERS_FILE
    if not answers_path.exists():
        # Hand-maintained project: no Copier baseline to disagree with.
        return

    try:
        import yaml

        data = yaml.safe_load(answers_path.read_text(encoding="utf-8"))
    except Exception:
        data = None

    if isinstance(data, dict) and "docs_dir" in data:
        plan.answers_update = True
        return

    plan.blockers.append(
        f"{ANSWERS_FILE} records no 'docs_dir', so this project is pinned to a "
        "template version that predates the setting. Run `treaty update` first "
        "— it records docs_dir and moves nothing — then relocate."
    )


def _plan_moves(root: Path, plan: RelocationPlan) -> None:
    old_p, new_p = docs_prefix(plan.old_docs_dir), docs_prefix(plan.new_docs_dir)
    for name in MOVABLE_NAMES:
        source = root / f"{old_p}{name}"
        if not source.exists():
            continue
        destination = root / f"{new_p}{name}"
        if destination.exists():
            plan.blockers.append(
                f"{destination.relative_to(root).as_posix()} already exists; "
                "move or remove it before relocating."
            )
            continue
        plan.moves.append((source, destination))

    if not plan.moves and not plan.blockers:
        plan.blockers.append(
            f"No treaty docs found under {plan.old_docs_dir!r}; nothing to relocate."
        )


def _plan_link_edits(root: Path, plan: RelocationPlan) -> None:
    """Count link rewrites in treaty-owned docs (root docs and the moved ones)."""

    pairs = _doc_reference_pairs(plan.old_docs_dir, plan.new_docs_dir)
    for name in ROOT_DOC_NAMES:
        path = root / name
        if not path.exists():
            continue
        text = path.read_text(encoding="utf-8")
        total = 0
        for old, new in pairs:
            text, count = _retarget(text, old, new)
            total += count
        if total:
            plan.link_edits.append((path, total))

    old_rp, new_rp = root_prefix(plan.old_docs_dir), root_prefix(plan.new_docs_dir)
    if old_rp != new_rp:
        old_p = docs_prefix(plan.old_docs_dir)
        for name in MOVABLE_NAMES:
            path = root / f"{old_p}{name}"
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8")
            total = 0
            for root_doc in ROOT_DOC_NAMES:
                text, count = _retarget(text, f"{old_rp}{root_doc}", f"{new_rp}{root_doc}")
                total += count
            if total:
                plan.link_edits.append((path, total))


def _plan_external_refs(root: Path, plan: RelocationPlan) -> None:
    """Find references in files the treaty does not own, to report not rewrite."""

    owned = {root / name for name in ROOT_DOC_NAMES}
    old_p = docs_prefix(plan.old_docs_dir)
    owned |= {root / f"{old_p}{name}" for name in MOVABLE_NAMES}
    # Directories in MOVABLE_NAMES (work_log_archive/) move wholesale, so files
    # inside them are treaty-owned too — and their same-folder links survive the
    # move untouched. Without this they would be reported as external refs.
    owned_trees = tuple(p for p in owned if p.is_dir())
    needles = [old for old, _ in _doc_reference_pairs(plan.old_docs_dir, plan.new_docs_dir)]

    for path in _tracked_files(root):
        if path in owned or not path.is_file():
            continue
        if any(path.is_relative_to(tree) for tree in owned_trees):
            continue
        if old_p and path.relative_to(root).as_posix().startswith(old_p):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        hits = sum(len(re.findall(r"(?<![A-Za-z0-9_./-])" + re.escape(n), text)) for n in needles)
        if hits:
            plan.external_refs.append((path, hits))


def _plan_gitignore(root: Path, plan: RelocationPlan) -> None:
    """Detect destinations git would ignore once the docs move there.

    A deny-all `.gitignore` with an allowlist of the flat doc names stops
    matching after a move, so new files under the folder vanish silently.
    """

    for _, destination in plan.moves:
        rel = destination.relative_to(root).as_posix()
        probe = f"{rel}/probe.md" if destination.name == "work_log_archive" else rel
        proc = _git(root, "check-ignore", "-v", probe)
        if proc.returncode == 0:
            rule = proc.stdout.strip().split("\t")[0] if proc.stdout.strip() else "a .gitignore rule"
            plan.gitignore_risk.append(f"{probe} would be ignored by {rule}")


def apply_relocation(plan: RelocationPlan) -> list[str]:
    """Perform the planned relocation. Returns a log of what was done."""

    if plan.blockers:
        raise ValueError("refusing to relocate: plan has blockers")

    root = plan.root
    actions: list[str] = []

    for source, destination in plan.moves:
        destination.parent.mkdir(parents=True, exist_ok=True)
        rel_src = source.relative_to(root).as_posix()
        rel_dst = destination.relative_to(root).as_posix()
        moved_with_git = False
        if _is_tracked(root, source):
            moved_with_git = _git(root, "mv", rel_src, rel_dst).returncode == 0
        if not moved_with_git:
            source.rename(destination)
        actions.append(f"moved {rel_src} -> {rel_dst}")

    pairs = _doc_reference_pairs(plan.old_docs_dir, plan.new_docs_dir)
    new_p = docs_prefix(plan.new_docs_dir)
    for name in ROOT_DOC_NAMES:
        path = root / name
        if not path.exists():
            continue
        text = original = path.read_text(encoding="utf-8")
        total = 0
        for old, new in pairs:
            text, count = _retarget(text, old, new)
            total += count
        if text != original:
            path.write_text(text, encoding="utf-8")
            actions.append(f"rewrote {total} doc link(s) in {name}")

    old_rp, new_rp = root_prefix(plan.old_docs_dir), root_prefix(plan.new_docs_dir)
    if old_rp != new_rp:
        for name in MOVABLE_NAMES:
            path = root / f"{new_p}{name}"
            if not path.is_file():
                continue
            text = original = path.read_text(encoding="utf-8")
            total = 0
            for root_doc in ROOT_DOC_NAMES:
                text, count = _retarget(text, f"{old_rp}{root_doc}", f"{new_rp}{root_doc}")
                total += count
            if text != original:
                path.write_text(text, encoding="utf-8")
                rel = path.relative_to(root).as_posix()
                actions.append(f"rewrote {total} root link(s) in {rel}")

    owned = _owned_targets(root, plan)
    for old_path, new_path in _moving_markdown_files(plan):
        if not new_path.is_file():
            continue
        text = new_path.read_text(encoding="utf-8")
        updated, count = _rewrite_outbound(
            text, root, old_path.parent, new_path.parent, owned
        )
        if count:
            new_path.write_text(updated, encoding="utf-8")
            rel = new_path.relative_to(root).as_posix()
            actions.append(f"rewrote {count} project link(s) in {rel}")

    # Drop the old docs folder once it is empty, so flattening does not leave a
    # stray directory behind. Anything the adopter put in there keeps it alive.
    old_p = docs_prefix(plan.old_docs_dir)
    if old_p:
        old_dir = root / old_p.rstrip("/")
        while old_dir != root and old_dir.is_dir() and not any(old_dir.iterdir()):
            old_dir.rmdir()
            actions.append(f"removed empty {old_dir.relative_to(root).as_posix()}/")
            old_dir = old_dir.parent

    if plan.answers_update:
        answers_path = root / ANSWERS_FILE
        text = answers_path.read_text(encoding="utf-8")
        updated, count = re.subn(
            r"^docs_dir:.*$",
            f"docs_dir: {plan.new_docs_dir}",
            text,
            count=1,
            flags=re.MULTILINE,
        )
        if count:
            answers_path.write_text(updated, encoding="utf-8")
            actions.append(f"recorded docs_dir: {plan.new_docs_dir} in {ANSWERS_FILE}")

    return actions


def format_plan(plan: RelocationPlan) -> list[str]:
    """Human-readable summary of a relocation plan."""

    if plan.is_noop:
        return [f"Treaty docs are already in {plan.new_docs_dir!r}; nothing to do."]

    lines = [f"Relocating treaty docs: {plan.old_docs_dir!r} -> {plan.new_docs_dir!r}"]

    if plan.moves:
        lines.append("Moves:")
        lines.extend(
            f"  - {s.relative_to(plan.root).as_posix()} -> {d.relative_to(plan.root).as_posix()}"
            for s, d in plan.moves
        )
    if plan.link_edits:
        lines.append("Link rewrites:")
        lines.extend(
            f"  - {p.relative_to(plan.root).as_posix()} ({n} reference(s))"
            for p, n in plan.link_edits
        )
    if plan.outbound_edits:
        lines.append("Project links inside the moved docs (retargeted for the new depth):")
        lines.extend(
            f"  - {p.relative_to(plan.root).as_posix()} ({n} link(s))"
            for p, n in plan.outbound_edits
        )
    if plan.answers_update:
        lines.append(
            f"Answers: docs_dir -> {plan.new_docs_dir} "
            f"(edited in place; {ANSWERS_FILE} stays at the repo root)"
        )

    if plan.gitignore_risk:
        lines.append("WARNING - git would ignore the new location:")
        lines.extend(f"  - {risk}" for risk in plan.gitignore_risk)
        lines.append(
            "  Allow the new folder in .gitignore (e.g. '!"
            f"{docs_prefix(plan.new_docs_dir)}' and '!{docs_prefix(plan.new_docs_dir)}**'), "
            "then re-check with git check-ignore -v."
        )

    if plan.external_refs:
        lines.append("References outside the treaty docs (not rewritten - yours to fix):")
        lines.extend(
            f"  - {p.relative_to(plan.root).as_posix()} ({n} reference(s))"
            for p, n in plan.external_refs
        )

    if plan.blockers:
        lines.append("Blocked:")
        lines.extend(f"  - {b}" for b in plan.blockers)

    return lines
