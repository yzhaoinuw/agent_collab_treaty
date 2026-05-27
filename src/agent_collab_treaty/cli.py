"""CLI entry points for agent-collab-treaty."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

import typer


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

    typer.echo(f"Installing the Agent Collab Treaty into {destination}")
    copier.run_copy(
        src_path=source,
        dst_path=str(destination),
        vcs_ref=ref,
        defaults=defaults,
        data=_parse_data(data),
    )


@app.command()
def update(
    destination: Path = typer.Argument(
        Path("."),
        help="Project directory to update (defaults to the current directory).",
    ),
    defaults: bool = typer.Option(
        False,
        "--defaults",
        help="Use previously answered values; skip interactive prompts.",
    ),
) -> None:
    """Pull the latest treaty revisions into a project that was previously initialized.

    The target must be a git-tracked project (Copier needs git for three-way merges).
    Run `git init && git add . && git commit -m "treaty baseline"` if you haven't yet.
    """
    import copier

    destination = destination.expanduser().resolve()
    typer.echo(f"Updating the Agent Collab Treaty in {destination}")
    copier.run_update(dst_path=str(destination), defaults=defaults, overwrite=True)


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
) -> None:
    """Validate installed Agent Collab Treaty docs."""

    from .validation import format_issue, validate_project

    path = path.expanduser().resolve()
    issues = validate_project(path)

    if not issues:
        typer.echo("Treaty validation passed.")
        return

    for issue in issues:
        typer.echo(format_issue(issue, path), err=True)

    if not warn_only:
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
