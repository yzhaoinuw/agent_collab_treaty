"""End-to-end `treaty update` tests that run the real Copier three-way merge.

Everything in ``test_cli.py`` patches ``copier.run_update``, so it verifies the
CLI's arguments and output formatting but never the merge itself. These tests
build a throwaway template repo, install a project from an early commit of it,
revise the template, and update — exercising the machinery this package exists
to get right.

The template is synthetic rather than this repo's own. That keeps the tests
independent of release history and of tags being present in a shallow CI
checkout, while still driving the same Copier code path. The one property that
is specific to *our* ``copier.yml`` — the declaration order the legacy
``test_command`` alias depends on — is asserted directly in
``CopierConfigContractTests``.
"""

from __future__ import annotations

import os
import subprocess
import tempfile
import textwrap
import unittest
from pathlib import Path

from typer.testing import CliRunner

from agent_collab_treaty.cli import app

REPO_ROOT = Path(__file__).resolve().parent.parent

#: These spawn real git and Copier runs, so they cost seconds rather than
#: milliseconds. Set TREATY_SKIP_INTEGRATION=1 for a fast inner loop.
SKIP = os.environ.get("TREATY_SKIP_INTEGRATION") == "1"


def git(cwd: Path, *args: str) -> str:
    """Run git in ``cwd`` with an identity that doesn't depend on user config."""
    proc = subprocess.run(
        [
            "git",
            "-c",
            "user.email=tests@example.invalid",
            "-c",
            "user.name=Treaty Tests",
            "-c",
            "commit.gpgsign=false",
            *args,
        ],
        cwd=cwd,
        capture_output=True,
        text=True,
        check=True,
    )
    return proc.stdout


def write_template(root: Path, agents_body: str, extra: dict[str, str] | None = None) -> None:
    """Write a minimal Copier template into ``root``."""
    (root / "template").mkdir(parents=True, exist_ok=True)
    (root / "copier.yml").write_text(
        textwrap.dedent(
            """\
            _subdirectory: template
            project_name:
              type: str
              default: "demo"
            """
        ),
        encoding="utf-8",
    )
    (root / "template" / "AGENTS.md.jinja").write_text(agents_body, encoding="utf-8")
    (root / "template" / ".copier-answers.yml.jinja").write_text(
        "# Changes here will be overwritten by Copier\n{{ _copier_answers|to_nice_yaml }}\n",
        encoding="utf-8",
    )
    for name, content in (extra or {}).items():
        path = root / "template" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")


def write_alias_template(root: Path, questions: str, agents: str) -> None:
    """Write a one-file template whose question block is supplied by the caller."""
    (root / "template").mkdir(parents=True, exist_ok=True)
    (root / "copier.yml").write_text(
        "_subdirectory: template\n" + textwrap.dedent(questions),
        encoding="utf-8",
    )
    (root / "template" / "AGENTS.md.jinja").write_text(agents, encoding="utf-8")
    (root / "template" / ".copier-answers.yml.jinja").write_text(
        "# Changes here will be overwritten by Copier\n{{ _copier_answers|to_nice_yaml }}\n",
        encoding="utf-8",
    )


def commit_all(root: Path, message: str, tag: str | None = None) -> None:
    git(root, "add", "-A")
    git(root, "commit", "-m", message)
    if tag:
        git(root, "tag", "-a", tag, "-m", message)


V1_AGENTS = textwrap.dedent(
    """\
    # Guidelines for {{ project_name }}

    ## Startup Rule

    Read this file first.

    ## Runtime Environment

    [fill me in]

    ## Conventions

    Short title line.
    """
)


class UpdateIntegrationTests(unittest.TestCase):
    """Drive `treaty update` against a real Copier template across two versions."""

    def setUp(self) -> None:
        self.runner = CliRunner()
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmp.name)
        self.template = self.tmp / "template_repo"
        self.template.mkdir()
        git(self.template, "init", "-b", "main")
        write_template(self.template, V1_AGENTS)
        commit_all(self.template, "template v1", tag="v1.0.0")

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def install(self, name: str = "project") -> Path:
        """Install a project from template v1 and commit it as a git baseline."""
        dest = self.tmp / name
        result = self.runner.invoke(
            app,
            ["init", str(dest), "--source", str(self.template), "--ref", "v1.0.0", "--defaults"],
        )
        self.assertEqual(0, result.exit_code, result.output)
        git(dest, "init", "-b", "main")
        commit_all(dest, "treaty baseline")
        return dest

    def revise_template(self, agents_body: str, extra: dict[str, str] | None = None) -> None:
        write_template(self.template, agents_body, extra)
        commit_all(self.template, "template v2", tag="v2.0.0")

    def update(self, dest: Path):
        return self.runner.invoke(app, ["update", str(dest)])

    # ---------------------------------------------------------------- tests

    @unittest.skipIf(SKIP, "TREATY_SKIP_INTEGRATION=1")
    def test_clean_update_applies_upstream_edits_and_exits_zero(self) -> None:
        dest = self.install()
        self.revise_template(V1_AGENTS.replace("Read this file first.", "Read this file first, always."))

        result = self.update(dest)

        self.assertEqual(0, result.exit_code, result.output)
        self.assertIn("Read this file first, always.", (dest / "AGENTS.md").read_text())
        self.assertIn("Updated files:", result.output)

    @unittest.skipIf(SKIP, "TREATY_SKIP_INTEGRATION=1")
    def test_local_edits_outside_the_changed_region_survive(self) -> None:
        dest = self.install()
        agents = dest / "AGENTS.md"
        agents.write_text(
            agents.read_text().replace("[fill me in]", "conda activate demo"), encoding="utf-8"
        )
        commit_all(dest, "fill in the runtime")

        self.revise_template(V1_AGENTS.replace("Short title line.", "Short title line, imperative mood."))
        result = self.update(dest)

        self.assertEqual(0, result.exit_code, result.output)
        merged = agents.read_text()
        self.assertIn("conda activate demo", merged)  # local edit kept
        self.assertIn("imperative mood", merged)  # upstream edit folded in
        self.assertNotIn("<<<<<<<", merged)

    @unittest.skipIf(SKIP, "TREATY_SKIP_INTEGRATION=1")
    def test_overlapping_edit_conflicts_names_the_file_and_exits_nonzero(self) -> None:
        dest = self.install()
        agents = dest / "AGENTS.md"
        agents.write_text(
            agents.read_text().replace("Read this file first.", "Read me before anything else."),
            encoding="utf-8",
        )
        commit_all(dest, "reword the startup rule")

        self.revise_template(V1_AGENTS.replace("Read this file first.", "Read this file before any other."))
        result = self.update(dest)

        self.assertEqual(1, result.exit_code, result.output)
        self.assertIn("Conflicts (unresolved):", result.output)
        self.assertIn("AGENTS.md", result.output)
        self.assertIn("did NOT complete cleanly", result.output)
        self.assertIn("<<<<<<<", agents.read_text())

    @unittest.skipIf(SKIP, "TREATY_SKIP_INTEGRATION=1")
    def test_file_added_upstream_lands_in_an_older_project(self) -> None:
        dest = self.install()
        self.assertFalse((dest / "treaty_conventions.md").exists())

        self.revise_template(V1_AGENTS, extra={"treaty_conventions.md": "# Conventions\n\nMechanics.\n"})
        result = self.update(dest)

        self.assertEqual(0, result.exit_code, result.output)
        self.assertTrue((dest / "treaty_conventions.md").exists())

    @unittest.skipIf(SKIP, "TREATY_SKIP_INTEGRATION=1")
    def test_recorded_answers_are_reused_without_reprompting(self) -> None:
        dest = self.tmp / "answered"
        result = self.runner.invoke(
            app,
            [
                "init", str(dest),
                "--source", str(self.template),
                "--ref", "v1.0.0",
                "--defaults",
                "--data", "project_name=Vessel Analysis",
            ],
        )
        self.assertEqual(0, result.exit_code, result.output)
        git(dest, "init", "-b", "main")
        commit_all(dest, "treaty baseline")

        self.revise_template(V1_AGENTS.replace("Short title line.", "Short title line, please."))
        result = self.update(dest)

        self.assertEqual(0, result.exit_code, result.output)
        self.assertIn("Vessel Analysis", (dest / "AGENTS.md").read_text())
        self.assertIn("Answers: unchanged", result.output)

    @unittest.skipIf(SKIP, "TREATY_SKIP_INTEGRATION=1")
    def test_hidden_alias_question_migrates_a_recorded_answer(self) -> None:
        """The rename pattern v0.5.0 used for test_command -> verification_command.

        A `when: false` question keeps the old key readable while a new question
        inherits its recorded value — but only because the legacy key is
        declared *after* its replacement. This walks a project installed under
        the old name through an update that renames it.
        """
        alias_template = self.tmp / "alias_template"
        alias_template.mkdir()
        git(alias_template, "init", "-b", "main")

        # v1: the question is called test_command.
        write_alias_template(
            alias_template,
            questions="""\
            test_command:
              type: str
              default: ""
            """,
            agents="# Guidelines\n\n## Common Tasks\n\nRun `{{ test_command }}` to verify.\n",
        )
        commit_all(alias_template, "alias template v1", tag="v1.0.0")

        dest = self.tmp / "migrating"
        result = self.runner.invoke(
            app,
            [
                "init", str(dest),
                "--source", str(alias_template),
                "--ref", "v1.0.0",
                "--defaults",
                "--data", "test_command=pytest -q",
            ],
        )
        self.assertEqual(0, result.exit_code, result.output)
        self.assertIn("test_command: pytest -q", (dest / ".copier-answers.yml").read_text())
        git(dest, "init", "-b", "main")
        commit_all(dest, "treaty baseline")

        # v2: renamed, with the legacy key kept hidden and declared last.
        write_alias_template(
            alias_template,
            questions="""\
            verification_command:
              type: str
              default: "{{ test_command | default('', true) }}"
            test_command:
              type: str
              when: false
              default: ""
            """,
            agents="# Guidelines\n\n## Common Tasks\n\nVerify with `{{ verification_command }}`.\n",
        )
        commit_all(alias_template, "alias template v2", tag="v2.0.0")

        result = self.update(dest)

        self.assertEqual(0, result.exit_code, result.output)
        answers = (dest / ".copier-answers.yml").read_text()
        self.assertIn("verification_command: pytest -q", answers)
        self.assertNotIn("test_command:", answers)
        self.assertIn("Verify with `pytest -q`.", (dest / "AGENTS.md").read_text())

    @unittest.skipIf(SKIP, "TREATY_SKIP_INTEGRATION=1")
    def test_dry_run_predicts_conflicts_and_new_files_without_mutating(self) -> None:
        """Issues #16/#18: the preview must show the merge plan, not just run quietly."""
        dest = self.install()
        agents = dest / "AGENTS.md"
        agents.write_text(
            agents.read_text().replace("Read this file first.", "Read me before anything else."),
            encoding="utf-8",
        )
        commit_all(dest, "reword the startup rule")

        self.revise_template(
            V1_AGENTS.replace("Read this file first.", "Read this file before any other."),
            extra={"treaty_conventions.md": "# Conventions\n\nMechanics.\n"},
        )

        status_before = git(dest, "status", "--porcelain")
        head_before = git(dest, "rev-parse", "HEAD")
        agents_before = agents.read_bytes()

        result = self.runner.invoke(app, ["update", str(dest), "--dry-run"])

        self.assertEqual(1, result.exit_code, result.output)
        self.assertIn("Template version: v1.0.0 → v2.0.0", result.output)
        self.assertIn("Conflicts (unresolved):", result.output)
        self.assertIn("AGENTS.md", result.output)
        self.assertIn("treaty_conventions.md", result.output)
        self.assertIn("would leave 1 file(s)", result.output)
        # The project itself is byte-for-byte untouched.
        self.assertEqual(agents_before, agents.read_bytes())
        self.assertEqual(status_before, git(dest, "status", "--porcelain"))
        self.assertEqual(head_before, git(dest, "rev-parse", "HEAD"))
        self.assertFalse((dest / "treaty_conventions.md").exists())

    @unittest.skipIf(SKIP, "TREATY_SKIP_INTEGRATION=1")
    def test_dry_run_on_a_clean_update_reports_the_plan_and_exits_zero(self) -> None:
        dest = self.install()
        self.revise_template(
            V1_AGENTS.replace("Read this file first.", "Read this file first, always.")
        )

        result = self.runner.invoke(app, ["update", str(dest), "--dry-run"])

        self.assertEqual(0, result.exit_code, result.output)
        self.assertIn("Template version: v1.0.0 → v2.0.0", result.output)
        self.assertIn("Updated files:", result.output)
        self.assertIn("AGENTS.md", result.output)
        self.assertIn("Re-run without --dry-run to apply", result.output)
        self.assertNotIn("first, always.", (dest / "AGENTS.md").read_text())

    @unittest.skipIf(SKIP, "TREATY_SKIP_INTEGRATION=1")
    def test_dry_run_names_an_answers_file_that_git_ignores(self) -> None:
        """Issue #15's trap: metadata that exists on disk but can never be committed."""
        dest = self.tmp / "ignored_metadata"
        result = self.runner.invoke(
            app,
            ["init", str(dest), "--source", str(self.template), "--ref", "v1.0.0", "--defaults"],
        )
        self.assertEqual(0, result.exit_code, result.output)
        (dest / ".gitignore").write_text(".copier-answers.yml\n", encoding="utf-8")
        git(dest, "init", "-b", "main")
        commit_all(dest, "treaty baseline without the answers file")

        result = self.runner.invoke(app, ["update", str(dest), "--dry-run"])

        self.assertEqual(1, result.exit_code, result.output)
        self.assertIn("not committed", result.output)
        self.assertIn(".copier-answers.yml", result.output)

    @unittest.skipIf(SKIP, "TREATY_SKIP_INTEGRATION=1")
    def test_alias_declared_before_its_replacement_loses_the_answer(self) -> None:
        """The failure mode the declaration order protects against.

        Copier clears a `when: false` question's recorded answer as it walks
        past it, so a legacy key declared *first* is already gone by the time
        the replacement's default is rendered. This pins that behavior, so if a
        future Copier release changes it, we find out here rather than from an
        adopter whose answer silently vanished.
        """
        broken = self.tmp / "broken_template"
        broken.mkdir()
        git(broken, "init", "-b", "main")

        write_alias_template(
            broken,
            questions="""\
            test_command:
              type: str
              default: ""
            """,
            agents="# Guidelines\n\n## Common Tasks\n\nRun `{{ test_command }}` to verify.\n",
        )
        commit_all(broken, "v1", tag="v1.0.0")

        dest = self.tmp / "broken_project"
        self.runner.invoke(
            app,
            [
                "init", str(dest), "--source", str(broken),
                "--ref", "v1.0.0", "--defaults", "--data", "test_command=pytest -q",
            ],
        )
        git(dest, "init", "-b", "main")
        commit_all(dest, "treaty baseline")

        # Same rename, but with the legacy key declared FIRST.
        write_alias_template(
            broken,
            questions="""\
            test_command:
              type: str
              when: false
              default: ""
            verification_command:
              type: str
              default: "{{ test_command | default('', true) }}"
            """,
            agents="# Guidelines\n\n## Common Tasks\n\nVerify with `{{ verification_command }}`.\n",
        )
        commit_all(broken, "v2 with the order reversed", tag="v2.0.0")

        self.update(dest)

        answers = (dest / ".copier-answers.yml").read_text()
        self.assertIn(
            "verification_command: ''",
            answers,
            "Copier no longer clears a hidden question's answer before later "
            "defaults render. If this fails, the declaration-order constraint "
            "in copier.yml may no longer be needed — re-check before relying on it.",
        )


class CopierConfigContractTests(unittest.TestCase):
    """Guard the properties of our own copier.yml that the migration relies on."""

    def setUp(self) -> None:
        import yaml

        self.raw = (REPO_ROOT / "copier.yml").read_text(encoding="utf-8")
        self.config = yaml.safe_load(self.raw)

    def test_legacy_test_command_is_hidden_and_declared_after_its_replacement(self) -> None:
        keys = [k for k in self.config if not k.startswith("_")]
        self.assertIn("test_command", keys)
        self.assertIn("verification_command", keys)
        self.assertFalse(
            self.config["test_command"]["when"],
            "test_command must stay hidden; it exists only to carry pre-v0.5.0 answers forward.",
        )
        self.assertGreater(
            keys.index("test_command"),
            keys.index("verification_command"),
            "Copier renders question defaults in declaration order and clears a "
            "`when: false` answer as it passes it. If test_command is declared "
            "first, verification_command's default reads an already-cleared value "
            "and every adopter's migration is silently dropped.",
        )

    def test_verification_command_inherits_the_legacy_answer(self) -> None:
        self.assertIn("test_command", self.config["verification_command"]["default"])

    def test_opt_out_questions_default_to_true(self) -> None:
        for key in ("has_releases", "uses_precommit", "include_git_ownership_note"):
            with self.subTest(question=key):
                self.assertIs(
                    True,
                    self.config[key]["default"],
                    f"{key} must default to true so existing code repos see no change.",
                )


if __name__ == "__main__":
    unittest.main()
