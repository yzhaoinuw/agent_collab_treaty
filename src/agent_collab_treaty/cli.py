"""CLI entry points for agent-collab-treaty."""

from __future__ import annotations

import shlex
import subprocess
from pathlib import Path, PurePosixPath
from typing import List, Optional

import typer

from .validation import (
    ANSWERS_FILE,
    STALE_BACKGROUND_PREFIX,
    answers_file_ignored,
    resolve_docs_dir,
)


def _git_output(dest: Path, *args: str) -> Optional[str]:
    """Run a read-only git command in ``dest``; return stdout or None on failure."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(dest), *args],
            capture_output=True,
            text=True,
            check=False,
        )
    except OSError:
        return None
    if proc.returncode != 0:
        return None
    return proc.stdout


def _is_unmerged(xy: str) -> bool:
    """True if a porcelain XY status code marks an unmerged (conflicted) path."""
    return "U" in xy or xy in ("AA", "DD")


def _classify_status(porcelain: str) -> tuple[list[str], list[str]]:
    """Split ``git status --porcelain`` output into (changed, unmerged) file lists."""
    changed: set[str] = set()
    unmerged: set[str] = set()
    for line in porcelain.splitlines():
        if len(line) < 4:
            continue
        xy = line[:2]
        path = line[3:]
        if " -> " in path:  # renamed: "old -> new"
            path = path.split(" -> ", 1)[1]
        if _is_unmerged(xy):
            unmerged.add(path)
        else:
            changed.add(path)
    return sorted(changed), sorted(unmerged)


def _update_status(dest: Path) -> tuple[list[str], list[str], list[str]]:
    """Split an updated tree into (changed, unmerged, line-ending-only) files.

    ``git status`` alone over-reports under ``core.autocrlf=true``: Copier
    rewrites files it touches, Git leaves them with CRLF endings, and status
    keeps flagging them although ``git add`` stages nothing (#31). ``git diff
    HEAD`` compares content after line-ending conversion, so a file counts as
    changed only when a commit would change it.
    """
    porcelain = _git_output(dest, "status", "--porcelain") or ""
    flagged, unmerged = _classify_status(porcelain)
    diffed = _git_output(dest, "diff", "--name-only", "HEAD")
    if diffed is None:
        return flagged, unmerged, []
    untracked = {line[3:] for line in porcelain.splitlines() if line.startswith("?? ")}
    content = (set(diffed.splitlines()) | untracked) - set(unmerged)
    changed = [path for path in flagged if path in content]
    eol_only = [path for path in flagged if path not in content]
    return changed, unmerged, eol_only


def _conflict_notes(unmerged: list[str]) -> list[str]:
    """File-specific advice for resolving conflicts, where a wrong pick is costly.

    Adopters rewrite the work log's intro text and then prepend entries right
    below it, so the template's intro and their newest entries land in the same
    conflict hunk. Taking the template side there deletes history: in one real
    adopter the "before updating" side held two whole session entries.
    """
    if not any(PurePosixPath(path).name == "work_log.md" for path in unmerged):
        return []
    return [
        "In work_log.md, the 'after updating' side is the template's intro "
        "text, and treaty_conventions.md already carries that guidance. Keep "
        "every dated entry from the 'before updating' side: dropping that side "
        "deletes history.",
    ]


def _next_steps_candidates(dest: Path) -> set[Path]:
    """Every next_steps.md that could be the treaty's, at either layout."""
    return {
        path.resolve()
        for path in (dest / "next_steps.md", *dest.glob("*/next_steps.md"))
        if path.is_file()
    }


def _drop_stale_background_line(dest: Path, existing: set[Path]) -> None:
    """Remove the template's self-contradicting line from a fresh next_steps.md.

    "Other sections below are background or paused" sits above the active
    thread examples it contradicts (#26). The template can't drop it: any edit
    to next_steps.md conflicts in nearly every adopter (measured 2026-10-22).
    Copier's ``_copier_operation`` is not visible to file content, so a
    copy-only render is not possible either. Deleting it in the new copy is the
    edit most adopters already made by hand, and their updates merge cleanly.
    A next_steps.md that existed before init was skipped by Copier; leave it.
    """
    path = (dest / resolve_docs_dir(dest) / "next_steps.md").resolve()
    if path in existing or not path.is_file():
        return
    lines = path.read_text(encoding="utf-8").split("\n")
    for index, line in enumerate(lines):
        if line.startswith(STALE_BACKGROUND_PREFIX):
            end = index + 2 if index + 1 < len(lines) and not lines[index + 1].strip() else index + 1
            del lines[index:end]
            path.write_text("\n".join(lines), encoding="utf-8")
            return


def _stage_command(paths: list[str]) -> str:
    """A commit command naming exactly ``paths``, not ``git add -A``.

    Adopters often keep unrelated untracked files (datasets, scratch work) out
    of the way with a temporary ``.git/info/exclude`` entry just for the
    update; ``git add -A`` would stage them once the entry is gone (#22).
    """
    return f"git add {' '.join(shlex.quote(path) for path in paths)} && git commit"


def _reject_files(dest: Path) -> set[str]:
    """Untracked ``*.rej`` files under ``dest``, as POSIX paths relative to it.

    Asked of ``git ls-files --others`` without ``--exclude-standard`` on purpose:
    that lists untracked files whatever ``status.showUntrackedFiles`` or the
    ignore rules say, and those two settings are exactly what hide a reject
    from Copier in the first place.
    """
    out = _git_output(dest, "ls-files", "--others", "-z", "--", "*.rej")
    if not out:
        return set()
    return {path for path in out.split("\0") if path}


#: Copier's update applies the adopter's own edits as a patch on top of the new
#: template with ``git apply --reject``, then finds the rejected hunks through
#: ``git status`` and turns each into inline conflict markers. Anything that
#: hides an untracked ``.rej`` from ``git status`` skips that step: the file is
#: left as the pristine template, the adopter's edits sit only in the ``.rej``,
#: and Copier reports success (issue #25).
_REJECT_PROBE = "AGENTS.md.rej"


def _reject_recovery_blockers(dest: Path) -> list[str]:
    """Settings in ``dest`` that would hide Copier's rejected hunks from it."""
    blockers: list[str] = []
    mode = (_git_output(dest, "config", "--get", "status.showUntrackedFiles") or "").strip()
    if mode.lower() in ("no", "false", "off", "0"):
        blockers.append(
            f"git config status.showUntrackedFiles={mode} is in effect (from the "
            "repo, your global config, or GIT_CONFIG_* environment variables). "
            "Unset it for the update. To keep unrelated untracked files out of "
            "the way, list them in .git/info/exclude instead."
        )
    ignored = subprocess.run(
        ["git", "-C", str(dest), "check-ignore", "--no-index", "-q", _REJECT_PROBE],
        capture_output=True,
        check=False,
    )
    if ignored.returncode == 0:
        blockers.append(
            "git ignores *.rej files here (see `git check-ignore -v --no-index "
            f"{_REJECT_PROBE}`). Add a `!*.rej` line after that rule in "
            ".gitignore; a narrow exception is enough, so a deny-all rule "
            "can stay."
        )
    return blockers


def _refuse_if_rejects_hidden(dest: Path) -> None:
    blockers = _reject_recovery_blockers(dest)
    if not blockers:
        return
    typer.echo(
        "Refusing to update: Copier finds merge conflicts through `git status`, "
        "and this project hides the files it needs to see. A conflicting file "
        "would be replaced by the template version, your edits left only in an "
        "untracked .rej file, and the update reported as a success.",
        err=True,
    )
    for blocker in blockers:
        typer.echo(f"  - {blocker}", err=True)
    raise typer.Exit(1)


def _rejected_targets(rejects: set[str]) -> list[str]:
    """The files whose patch was rejected, named by stripping ``.rej``."""
    return sorted(path[: -len(".rej")] for path in rejects)


def _read_answers(dest: Path) -> dict:
    """Load the Copier answers file for ``dest``; return {} if missing/unreadable."""
    answers_path = dest / ANSWERS_FILE
    if not answers_path.exists():
        return {}
    import yaml

    try:
        data = yaml.safe_load(answers_path.read_text(encoding="utf-8"))
    except (OSError, yaml.YAMLError):
        return {}
    return data if isinstance(data, dict) else {}


def _user_answers(answers: dict) -> dict:
    """Recorded template answers, excluding Copier's ``_``-prefixed bookkeeping keys."""
    return {k: v for k, v in answers.items() if not k.startswith("_")}


def _legacy_layout_data(answers: dict) -> dict[str, str]:
    """Pin projects installed before ``docs_dir`` existed to the flat root layout.

    Those projects have no recorded ``docs_dir``, so an unguarded update would
    hand them the new ``treaty_docs`` default and Copier would relocate every
    treaty doc. Copier implements that relocation as *delete the customized file
    and write a pristine one at the new path* — a silent loss of the adopter's
    entire work log. Answering ``.`` keeps their layout byte-identical, and the
    answer is recorded from then on, so this only has to fire once.
    """
    if not answers or "docs_dir" in answers:
        return {}
    return {"docs_dir": "."}


def _format_update_summary(
    old_answers: dict,
    new_answers: dict,
    changed: list[str],
    unmerged: list[str],
    rejected: Optional[list[str]] = None,
    eol_only: Optional[list[str]] = None,
) -> list[str]:
    """Build the human-readable post-update summary lines."""
    rejected = rejected or []
    eol_only = eol_only or []
    lines: list[str] = []

    old_v = old_answers.get("_commit")
    new_v = new_answers.get("_commit")
    if old_v or new_v:
        if old_v == new_v:
            lines.append(f"Template version: {new_v or 'unknown'} (unchanged)")
        else:
            lines.append(
                f"Template version: {old_v or 'unknown'} -> {new_v or 'unknown'}"
            )

    old_user = _user_answers(old_answers)
    new_user = _user_answers(new_answers)
    answer_diffs = [
        f"  - {key}: {old_user.get(key)!r} -> {new_user.get(key)!r}"
        for key in sorted(set(old_user) | set(new_user))
        if old_user.get(key) != new_user.get(key)
    ]
    if answer_diffs:
        lines.append("Answer changes:")
        lines.extend(answer_diffs)
    else:
        lines.append("Answers: unchanged")

    if changed:
        lines.append("Updated files:")
        lines.extend(f"  - {path}" for path in changed)
    if unmerged:
        lines.append("Conflicts (unresolved):")
        lines.extend(f"  - {path}" for path in unmerged)
    if rejected:
        lines.append("Rejected merges (your edits are only in the .rej file):")
        lines.extend(f"  - {path}  (see {path}.rej)" for path in rejected)
    if eol_only:
        lines.append(
            "Line endings rewritten, content unchanged (git status may list "
            "these; committing them changes nothing):"
        )
        lines.extend(f"  - {path}" for path in eol_only)
    if not changed and not unmerged and not rejected:
        lines.append("No file changes.")

    return lines


def _resolve_source(source: str) -> str:
    """Expand a local template source to an absolute path; pass URLs through.

    Copier records ``--source`` verbatim as ``_src_path``. A relative value like
    ``.`` is therefore re-resolved later *from the installed project*, where it
    points at the adopter's own repository instead of the template — so every
    subsequent `treaty diff` / `treaty update` runs git commands in the wrong
    repo. Absolutising it at install time keeps the recorded source meaningful
    from anywhere. Remote specs (``gh:``, ``git+``, ``https://``…) are not paths
    and are left untouched.
    """
    candidate = Path(source).expanduser()
    if candidate.exists():
        return str(candidate.resolve())
    return source


def _parse_data(pairs: Optional[List[str]]) -> dict[str, str]:
    """Parse `key=value` strings from --data into a dict for Copier."""
    if not pairs:
        return {}
    result: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise typer.BadParameter(f"--data expects key=value, got: {pair!r}")
        key, _, value = pair.partition("=")
        result[key.strip()] = value
    return result

app = typer.Typer(
    name="treaty",
    help="Install and maintain the Agent Collab Treaty in any project.",
    no_args_is_help=True,
    add_completion=False,
)

DEFAULT_TEMPLATE_SOURCE = "gh:yzhaoinuw/agent_collab_treaty"


def _version_lines(cwd: Path) -> list[str]:
    """Report the CLI version, plus the pinned template version when in a project."""
    from . import __version__

    lines = [f"treaty {__version__}"]

    answers = _read_answers(cwd)
    commit = answers.get("_commit")
    if commit:
        source = answers.get("_src_path")
        suffix = f" ({source})" if source else ""
        lines.append(f"template {commit}{suffix}")
    return lines


def _warn_if_cli_older(commit: object) -> None:
    from .versions import cli_older_than, skew_message

    if cli_older_than(commit):
        typer.echo(f"WARNING: {skew_message(commit)}", err=True)


def _version_callback(value: bool) -> None:
    if not value:
        return
    for line in _version_lines(Path.cwd()):
        typer.echo(line)
    raise typer.Exit()


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        help="Show the CLI version, and the pinned template version when run inside a project.",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Install and maintain the Agent Collab Treaty in any project."""


@app.command()
def init(
    destination: Path = typer.Argument(
        Path("."),
        help="Project directory to install the treaty into (defaults to the current directory).",
    ),
    source: str = typer.Option(
        DEFAULT_TEMPLATE_SOURCE,
        "--source",
        help="Override the template source (GitHub URL or local path). Defaults to the official treaty repo.",
    ),
    ref: Optional[str] = typer.Option(
        None,
        "--ref",
        help="Pin a specific git ref/branch/tag of the template source.",
    ),
    defaults: bool = typer.Option(
        False,
        "--defaults",
        help="Use default answers for all template questions (skip interactive prompts).",
    ),
    data: Optional[List[str]] = typer.Option(
        None,
        "--data",
        help="Pre-answer a template question: --data key=value (repeatable).",
    ),
) -> None:
    """Install the Agent Collab Treaty into a project."""
    import copier

    destination = destination.expanduser().resolve()
    destination.mkdir(parents=True, exist_ok=True)

    from .adoption import (
        INIT_SKIP_IF_EXISTS,
        format_adoption_notices,
        inspect_adoption_context,
    )

    adoption_notices = inspect_adoption_context(destination)
    for line in format_adoption_notices(adoption_notices):
        typer.echo(line, err=True)
    if any(notice.code == "noncanonical-treaty-paths" for notice in adoption_notices):
        typer.echo(
            "Resolve noncanonical treaty-looking paths, then rerun treaty init.",
            err=True,
        )
        raise typer.Exit(1)

    typer.echo(f"Installing the Agent Collab Treaty into {destination}")
    existing_next_steps = _next_steps_candidates(destination)
    copier.run_copy(
        src_path=_resolve_source(source),
        dst_path=str(destination),
        vcs_ref=ref,
        defaults=defaults,
        data=_parse_data(data),
        skip_if_exists=INIT_SKIP_IF_EXISTS,
    )
    _drop_stale_background_line(destination, existing_next_steps)

    if answers_file_ignored(destination):
        typer.echo(
            f"WARNING: git ignores {ANSWERS_FILE} in this project, so it cannot "
            "be committed. Future `treaty update` and `treaty diff` runs depend "
            "on it — remove the ignore rule from .gitignore and commit the file.",
            err=True,
        )


@app.command()
def update(
    destination: Path = typer.Argument(
        Path("."),
        help="Project directory to update (defaults to the current directory).",
    ),
    interactive: bool = typer.Option(
        False,
        "--interactive",
        help="Re-prompt for template answers instead of reusing the recorded ones.",
    ),
    data: Optional[List[str]] = typer.Option(
        None,
        "--data",
        metavar="KEY=VALUE",
        help=(
            "Answer a template question non-interactively; repeatable. Use it "
            "for questions that are new in the target version, which otherwise "
            "silently take the template default. Recorded answers are still "
            "reused for everything you do not name."
        ),
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help=(
            "Preview the update without writing any changes: run the merge in a "
            "disposable clone and report the planned answer changes, updated "
            "files, and conflicts. Exits non-zero if the merge would conflict, "
            "matching a real apply. The clone is of the project's *committed* "
            "state, so uncommitted edits are not previewed — but --data values "
            "are, since they are supplied on the command line."
        ),
    ),
    show_diff: bool = typer.Option(
        False,
        "--diff",
        help=(
            "With --dry-run, also print the full diff of every file the "
            "preview would change, so you can read what an update does before "
            "applying it. After a real update, use git diff."
        ),
    ),
    defaults: bool = typer.Option(
        False,
        "--defaults",
        hidden=True,
        help="Deprecated: recorded answers are now reused by default.",
    ),
) -> None:
    """Pull the latest treaty revisions into a project that was previously initialized.

    The target must be a git-tracked project (Copier needs git for three-way merges).
    Run `git init && git add . && git commit -m "treaty baseline"` if you haven't yet.

    Recorded answers are reused by default; pass --interactive to re-answer questions,
    or --data key=value to answer individual ones (repeatable) without a prompt.
    If the merge leaves any file with conflict markers, this command lists it and exits
    non-zero, so a conflicted update is never reported as a success. With --dry-run the
    same merge runs in a disposable clone of the project's committed state, and the same
    summary and exit policy apply without anything being written to the project.
    """
    import copier

    destination = destination.expanduser().resolve()
    if defaults:
        typer.echo(
            "Note: --defaults is deprecated; recorded answers are reused by default. "
            "Pass --interactive to re-answer questions.",
            err=True,
        )
    if show_diff and not dry_run:
        typer.echo(
            "--diff works with --dry-run. After a real update, review the "
            "changes with git diff.",
            err=True,
        )
        raise typer.Exit(2)
    use_defaults = not interactive
    overrides = _parse_data(data)
    _reject_layout_override(overrides)
    # Checked on the real project in both modes: a repo-local setting does not
    # survive into the dry run's clone, which is how a preview could predict a
    # conflict that the real update then silently skipped.
    _refuse_if_rejects_hidden(destination)

    if dry_run:
        _preview_update(destination, use_defaults, overrides, show_diff)
        return

    old_answers = _read_answers(destination)
    _warn_if_cli_older(old_answers.get("_commit"))
    rejects_before = _reject_files(destination)
    typer.echo(f"Updating the Agent Collab Treaty in {destination}")
    copier.run_update(
        dst_path=str(destination),
        data=_update_data(old_answers, overrides),
        defaults=use_defaults,
        overwrite=True,
    )
    new_answers = _read_answers(destination)
    if new_answers.get("_commit") != old_answers.get("_commit"):
        _warn_if_cli_older(new_answers.get("_commit"))

    changed, unmerged, eol_only = _update_status(destination)
    new_rejects = _reject_files(destination) - rejects_before
    rejected = _rejected_targets(new_rejects)
    changed = [path for path in changed if path not in new_rejects]
    for line in _format_update_summary(
        old_answers, new_answers, changed, unmerged, rejected, eol_only
    ):
        typer.echo(line)

    if rejected:
        typer.echo("", err=True)
        typer.echo(
            f"Update did NOT complete cleanly — {len(rejected)} file(s) were "
            "replaced by the template version, and your edits to them survive "
            "only in the .rej file(s) listed above. Do not commit this state.",
            err=True,
        )
        typer.echo(
            "Your pre-update content is still in HEAD. To back out, restore the "
            "tracked files and delete the rejects, then rerun:",
            err=True,
        )
        typer.echo(
            "    git checkout -- . && rm "
            + " ".join(sorted(new_rejects)),
            err=True,
        )
        raise typer.Exit(1)

    if unmerged:
        typer.echo("", err=True)
        typer.echo(
            f"Update did NOT complete cleanly — {len(unmerged)} file(s) have "
            "unresolved conflicts.",
            err=True,
        )
        for note in _conflict_notes(unmerged):
            typer.echo(note, err=True)
        typer.echo(
            "Resolve the conflict markers ('<<<<<<< before updating' / "
            "'>>>>>>> after updating'), then:",
            err=True,
        )
        # Every file the update touched, not only the conflicted ones: leaving
        # .copier-answers.yml out commits merged docs under the old version pin.
        typer.echo(
            f"    {_stage_command(unmerged + changed + eol_only)}", err=True
        )
        raise typer.Exit(1)

    if changed:
        typer.echo("")
        typer.echo("Review the changes, then:")
        typer.echo(f"    {_stage_command(changed + eol_only)}")
    for line in _flat_layout_hint(new_answers, after_update=True):
        typer.echo(line)


def _flat_layout_hint(answers: dict, *, after_update: bool) -> list[str]:
    """Point a flat-layout project at `treaty relocate`, once per update.

    `treaty update` never moves docs: Copier applies a move as delete-plus-create,
    so projects installed before v0.8.0 stay flat. Without this line nothing
    tells them the folder layout exists.
    """
    docs_dir = answers.get("docs_dir")
    if docs_dir is None or str(docs_dir).strip() not in (".", ""):
        return []
    if after_update:
        how = (
            "To move them, preview with `treaty relocate --dry-run`, then run "
            "`treaty relocate --force` to move them in the same commit as this update."
        )
    else:
        how = "To move them after updating, see `treaty relocate --dry-run`."
    return [
        "",
        "Your treaty docs are in the flat layout, at the repo root; new installs "
        "keep them in treaty_docs/. Staying flat is fine. " + how,
    ]


def _update_data(answers: dict, overrides: dict[str, str]) -> dict:
    """Answers to force for this update: the legacy layout pin, then --data.

    Order matters only in principle — ``docs_dir`` is the one key the pin sets
    and ``_reject_layout_override`` refuses it from --data — but it is written
    this way so a future pinned answer cannot be silently overridden either.
    """
    return {**_legacy_layout_data(answers), **overrides}


def _reject_layout_override(overrides: dict[str, str]) -> None:
    """Refuse `--data docs_dir=...`; that is `treaty relocate`'s job, not Copier's.

    Copier applies a layout change as "delete the adopter's customized file,
    write a pristine one at the new path" — no merge, no conflict, no warning.
    Letting --data through would hand adopters a one-flag way to do exactly the
    thing the whole docs_dir design exists to prevent.
    """
    if "docs_dir" not in overrides:
        return
    typer.echo(
        "--data docs_dir=... is not supported. Changing the layout through "
        "Copier deletes your customized docs and writes pristine ones at the "
        "new path, with no merge and no warning.",
        err=True,
    )
    typer.echo(
        f"Use `treaty relocate --to {overrides['docs_dir']}` instead — it moves "
        "the docs with git mv, rewrites their links, and records the answer.",
        err=True,
    )
    raise typer.Exit(1)


def _preview_update(
    destination: Path,
    use_defaults: bool,
    overrides: Optional[dict[str, str]] = None,
    show_diff: bool = False,
) -> None:
    """Run the real update in a disposable clone and report what it would do.

    Copier's ``pretend=True`` never materializes the merge, so the only honest
    preview is to perform it somewhere disposable. Cloning uses the project's
    committed state — the same state a real update would merge against.
    """
    import tempfile

    import copier

    typer.echo(
        f"Previewing treaty update for {destination} (no changes will be written)"
    )
    with tempfile.TemporaryDirectory() as tmp:
        # Resolve symlinks (macOS /var -> /private/var) or Copier's repo-root
        # detection sees a "different" path than the one it was given.
        preview = Path(tmp).resolve() / "preview"
        proc = subprocess.run(
            ["git", "clone", "--quiet", str(destination), str(preview)],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            typer.echo(
                "Could not clone the project to build the preview. The dry run "
                "works on committed state, so the project must be the root of a "
                "git repository with at least one commit.",
                err=True,
            )
            if proc.stderr.strip():
                typer.echo(proc.stderr.strip(), err=True)
            raise typer.Exit(1)

        if not (preview / ANSWERS_FILE).exists():
            if (destination / ANSWERS_FILE).exists():
                typer.echo(
                    f"{ANSWERS_FILE} exists but is not committed (is it "
                    "gitignored?). The preview — and every future treaty "
                    "update — needs it in the project's git history.",
                    err=True,
                )
            else:
                typer.echo(
                    f"No {ANSWERS_FILE} found in {destination}. "
                    "treaty update only works in a project installed with treaty init.",
                    err=True,
                )
            raise typer.Exit(1)

        old_answers = _read_answers(preview)
        _warn_if_cli_older(old_answers.get("_commit"))
        copier.run_update(
            dst_path=str(preview),
            data=_update_data(old_answers, overrides or {}),
            defaults=use_defaults,
            overwrite=True,
        )
        new_answers = _read_answers(preview)
        if new_answers.get("_commit") != old_answers.get("_commit"):
            _warn_if_cli_older(new_answers.get("_commit"))
        changed, unmerged, eol_only = _update_status(preview)
        # A fresh clone has no rejects of its own, so every one is new.
        new_rejects = _reject_files(preview)
        rejected = _rejected_targets(new_rejects)
        changed = [path for path in changed if path not in new_rejects]
        diff_text = _preview_diff(preview, changed + unmerged) if show_diff else ""

    for line in _format_update_summary(
        old_answers, new_answers, changed, unmerged, rejected, eol_only
    ):
        typer.echo(line)
    if diff_text:
        typer.echo("")
        typer.echo(diff_text.rstrip("\n"))

    if rejected:
        typer.echo("", err=True)
        typer.echo(
            f"Applying this update would replace {len(rejected)} file(s) with "
            "the template version and leave your edits only in .rej files.",
            err=True,
        )
        typer.echo("Preview only — no changes written.", err=True)
        raise typer.Exit(1)

    if unmerged:
        typer.echo("", err=True)
        typer.echo(
            f"Applying this update would leave {len(unmerged)} file(s) with "
            "unresolved conflicts.",
            err=True,
        )
        for note in _conflict_notes(unmerged):
            typer.echo(note, err=True)
        typer.echo("Preview only — no changes written.", err=True)
        raise typer.Exit(1)

    for line in _flat_layout_hint(new_answers, after_update=False):
        typer.echo(line)
    typer.echo("")
    typer.echo("Preview only — no changes written. Re-run without --dry-run to apply.")


def _preview_diff(preview: Path, paths: list[str]) -> str:
    """The unified diff of ``paths`` in the preview clone, new files included."""
    if not paths:
        return ""
    # Intent-to-add makes files the update created show up in `git diff`.
    subprocess.run(
        ["git", "-C", str(preview), "add", "--intent-to-add", "--", *paths],
        capture_output=True,
        check=False,
    )
    return _git_output(preview, "diff", "--no-color", "HEAD", "--", *paths) or ""


def _render_pristine(
    source: str,
    ref: Optional[str],
    answers: dict,
    target: Path,
) -> None:
    """Render the template into ``target`` using a project's recorded answers."""
    import copier

    copier.run_copy(
        src_path=source,
        dst_path=str(target),
        vcs_ref=ref,
        data={**_legacy_layout_data(answers), **_user_answers(answers)},
        defaults=True,
        quiet=True,
        overwrite=True,
    )


@app.command()
def diff(
    destination: Path = typer.Argument(
        Path("."),
        help="Project directory to compare (defaults to the current directory).",
    ),
    source: Optional[str] = typer.Option(
        None,
        "--source",
        help="Override the template source. Defaults to the one recorded at init.",
    ),
    ref: Optional[str] = typer.Option(
        None,
        "--ref",
        help="Compare against a specific template ref. Defaults to the pinned one.",
    ),
) -> None:
    """Show how far this project has drifted from the template version it is pinned to.

    Renders the pinned template into a temporary directory and compares it
    section by section, so you can see your conflict exposure before running
    `treaty update`. Nothing is written to the project.
    """
    import tempfile

    from .diff import compare_trees, format_report

    destination = destination.expanduser().resolve()
    answers = _read_answers(destination)
    if not answers:
        typer.echo(
            f"No {ANSWERS_FILE} found in {destination}. "
            "treaty diff only works in a project installed with treaty init.",
            err=True,
        )
        raise typer.Exit(1)

    template_source = _resolve_source(source) if source else answers.get("_src_path")
    if not template_source:
        typer.echo(
            f"{ANSWERS_FILE} records no template source; pass --source explicitly.",
            err=True,
        )
        raise typer.Exit(1)
    template_ref = ref or answers.get("_commit")

    with tempfile.TemporaryDirectory() as tmp:
        pristine = Path(tmp)
        _render_pristine(template_source, template_ref, answers, pristine)
        diffs = compare_trees(pristine, destination)

    for line in format_report(diffs, template_ref):
        typer.echo(line)


@app.command()
def relocate(
    destination: Path = typer.Argument(
        Path("."),
        help="Project directory to relocate (defaults to the current directory).",
    ),
    to: str = typer.Option(
        "treaty_docs",
        "--to",
        help="Folder to hold the working docs. Use '.' to flatten them back to the root.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Show the plan without moving anything.",
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help=(
            "Relocate with uncommitted changes. This is the normal step right after "
            "`treaty update`, whose changes are still uncommitted; otherwise "
            "commit first, so the relocation can be undone on its own."
        ),
    ),
) -> None:
    """Move this project's treaty working docs into (or out of) a subfolder.

    Moves `treaty_conventions.md`, `next_steps.md`, `work_log.md`, and
    `work_log_archive/`, rewrites the doc links in `AGENTS.md` and
    `project_overview.md`, and records the new `docs_dir` — in one pass, so the
    recorded answer and the files on disk never disagree. `AGENTS.md` and
    `project_overview.md` always stay at the repo root.

    Refuses to run on a project whose recorded answers predate `docs_dir`:
    relocating one of those before `treaty update` guarantees a conflict on the
    next update.
    """
    from .relocate import apply_relocation, format_plan, plan_relocation

    destination = destination.expanduser().resolve()

    if not force and not dry_run:
        porcelain = _git_output(destination, "status", "--porcelain")
        if porcelain is None:
            typer.echo(
                "Not a git repository (or git is unavailable). Relocation rewrites "
                "and moves files; run it in a git-tracked project so you can undo "
                "it, or pass --force to proceed anyway.",
                err=True,
            )
            raise typer.Exit(1)
        if porcelain.strip():
            typer.echo(
                "Working tree is not clean. If these are the changes `treaty update` "
                "just made, re-run with --force to relocate in the same commit. "
                "Otherwise commit or stash first, so the relocation is a single "
                "reviewable change.",
                err=True,
            )
            raise typer.Exit(1)

    plan = plan_relocation(destination, to)
    for line in format_plan(plan):
        typer.echo(line)

    if plan.is_noop:
        return

    if plan.blockers:
        raise typer.Exit(1)

    if dry_run:
        typer.echo("")
        typer.echo("Dry run — nothing was written. Re-run without --dry-run to apply.")
        return

    typer.echo("")
    for action in apply_relocation(plan):
        typer.echo(f"  {action}")

    typer.echo("")
    if plan.gitignore_risk:
        typer.echo(
            "Fix the .gitignore rules listed above before committing, or the "
            "moved docs will not stay tracked.",
            err=True,
        )
    leftover = _git_output(destination, "diff", "--name-only")
    if leftover is None:
        typer.echo("Not a git repository, so nothing was staged. Review the moved files.")
        return
    leftover_paths = leftover.splitlines()
    # Untracked files that relocate itself moved (say, an archive chunk from a
    # rotation not yet committed) are treaty docs, so name them too. Other
    # untracked files stay out: they may be data hidden by .git/info/exclude.
    moved_to = [d.relative_to(destination).as_posix() for _, d in plan.moves]
    untracked = _git_output(
        destination, "ls-files", "--others", "--exclude-standard", "--", *moved_to
    )
    if moved_to and untracked:
        leftover_paths += [p for p in untracked.splitlines() if p not in leftover_paths]
    typer.echo("The relocation is staged. Review it with git diff --cached, then:")
    typer.echo("    git commit")
    if leftover_paths:
        typer.echo("")
        typer.echo(
            "Changes from before the relocation are not staged. "
            "If they belong in this commit (for example, the update you just ran):"
        )
        typer.echo(f"    {_stage_command(leftover_paths)}")


@app.command()
def validate(
    path: Path = typer.Argument(
        Path("."),
        help="Project directory containing the treaty docs (defaults to the current directory).",
    ),
    warn_only: bool = typer.Option(
        False,
        "--warn-only",
        help="Print validation issues but exit successfully.",
    ),
    migration_hints: bool = typer.Option(
        False,
        "--migration-hints",
        help="Also print non-destructive hints for overlapping legacy project docs.",
    ),
) -> None:
    """Validate installed Agent Collab Treaty docs."""

    from .validation import format_issue, validate_project

    path = path.expanduser().resolve()
    issues = validate_project(path)
    if migration_hints:
        from .adoption import format_migration_hints, inspect_adoption_context

        for line in format_migration_hints(inspect_adoption_context(path)):
            typer.echo(line, err=True)

    for issue in issues:
        typer.echo(format_issue(issue, path), err=True)

    errors = [issue for issue in issues if issue.is_error]
    if not errors:
        warnings = len(issues)
        suffix = f" ({warnings} warning(s))" if warnings else ""
        typer.echo(f"Treaty validation passed{suffix}.")
        return

    if not warn_only:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
