"""CLI entry points for agent-collab-treaty."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import List, Optional

import typer

ANSWERS_FILE = ".copier-answers.yml"


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


def _format_update_summary(
    old_answers: dict,
    new_answers: dict,
    changed: list[str],
    unmerged: list[str],
) -> list[str]:
    """Build the human-readable post-update summary lines."""
    lines: list[str] = []

    old_v = old_answers.get("_commit")
    new_v = new_answers.get("_commit")
    if old_v or new_v:
        if old_v == new_v:
            lines.append(f"Template version: {new_v or 'unknown'} (unchanged)")
        else:
            lines.append(
                f"Template version: {old_v or 'unknown'} → {new_v or 'unknown'}"
            )

    old_user = _user_answers(old_answers)
    new_user = _user_answers(new_answers)
    answer_diffs = [
        f"  - {key}: {old_user.get(key)!r} → {new_user.get(key)!r}"
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
    if not changed and not unmerged:
        lines.append("No file changes.")

    return lines


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
    copier.run_copy(
        src_path=source,
        dst_path=str(destination),
        vcs_ref=ref,
        defaults=defaults,
        data=_parse_data(data),
        skip_if_exists=INIT_SKIP_IF_EXISTS,
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
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview the update (show the diff) without writing any changes.",
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

    Recorded answers are reused by default; pass --interactive to re-answer questions.
    If the merge leaves any file with conflict markers, this command lists it and exits
    non-zero, so a conflicted update is never reported as a success.
    """
    import copier

    destination = destination.expanduser().resolve()
    if defaults:
        typer.echo(
            "Note: --defaults is deprecated; recorded answers are reused by default. "
            "Pass --interactive to re-answer questions.",
            err=True,
        )
    use_defaults = not interactive

    if dry_run:
        typer.echo(
            f"Previewing treaty update for {destination} (no changes will be written)"
        )
        copier.run_update(
            dst_path=str(destination),
            defaults=use_defaults,
            overwrite=True,
            pretend=True,
        )
        typer.echo("Preview only — no changes written. Re-run without --dry-run to apply.")
        return

    old_answers = _read_answers(destination)
    typer.echo(f"Updating the Agent Collab Treaty in {destination}")
    copier.run_update(dst_path=str(destination), defaults=use_defaults, overwrite=True)
    new_answers = _read_answers(destination)

    changed, unmerged = _classify_status(
        _git_output(destination, "status", "--porcelain") or ""
    )
    for line in _format_update_summary(old_answers, new_answers, changed, unmerged):
        typer.echo(line)

    if unmerged:
        typer.echo("", err=True)
        typer.echo(
            f"Update did NOT complete cleanly — {len(unmerged)} file(s) have "
            "unresolved conflicts.",
            err=True,
        )
        typer.echo(
            "Resolve the conflict markers ('<<<<<<< before updating' / "
            "'>>>>>>> after updating'), then:",
            err=True,
        )
        typer.echo(f"    git add {' '.join(unmerged)} && git commit", err=True)
        raise typer.Exit(1)

    if changed:
        typer.echo("")
        typer.echo("Review the changes, then:")
        typer.echo("    git add -A && git commit")


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

    if not issues:
        typer.echo("Treaty validation passed.")
        return

    for issue in issues:
        typer.echo(format_issue(issue, path), err=True)

    if not warn_only:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
