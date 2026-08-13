from __future__ import annotations

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from agent_collab_treaty.cli import (
    _classify_status,
    _format_update_summary,
    _render_pristine,
    app,
)


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, check=True)


class TreatyCliTests(unittest.TestCase):
    def setUp(self) -> None:
        self.runner = CliRunner()

    def test_init_blocks_before_copy_for_noncanonical_treaty_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "Work_Log.md").write_text("# Legacy Work Log\n", encoding="utf-8")

            with patch("copier.run_copy") as run_copy:
                result = self.runner.invoke(
                    app,
                    ["init", str(root), "--source", ".", "--defaults"],
                )

            self.assertEqual(1, result.exit_code)
            self.assertIn("noncanonical-treaty-paths", result.output)
            self.assertIn("Resolve noncanonical treaty-looking paths", result.output)
            self.assertFalse((root / "AGENTS.md").exists())
            run_copy.assert_not_called()

    def test_init_warns_for_overlapping_docs_and_preserves_existing_paths(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "TODO.md").write_text("# TODO\n", encoding="utf-8")

            with patch("copier.run_copy") as run_copy:
                result = self.runner.invoke(
                    app,
                    ["init", str(root), "--source", ".", "--defaults"],
                )

            self.assertEqual(0, result.exit_code)
            self.assertIn("overlapping-project-docs", result.output)
            kwargs = run_copy.call_args.kwargs
            self.assertIn("work_log.md", kwargs["skip_if_exists"])
            self.assertIn("AGENTS.md", kwargs["skip_if_exists"])

    def test_update_exits_nonzero_and_names_conflicts(self) -> None:
        old = {"_commit": "v0.3.2", "include_treaty_badge": True}
        new = {"_commit": "v0.3.3", "include_treaty_badge": True}
        with patch("copier.run_update") as run_update, patch(
            "agent_collab_treaty.cli._read_answers", side_effect=[old, new]
        ), patch(
            "agent_collab_treaty.cli._git_output",
            return_value="UU AGENTS.md\n M work_log.md\n",
        ):
            result = self.runner.invoke(app, ["update", "/some/dest"])

        run_update.assert_called_once()
        self.assertEqual(1, result.exit_code)
        self.assertIn("Conflicts (unresolved):", result.output)
        self.assertIn("AGENTS.md", result.output)
        self.assertIn("did NOT complete cleanly", result.output)
        self.assertIn("git add AGENTS.md", result.output)

    def test_update_clean_reports_summary_and_exits_zero(self) -> None:
        old = {"_commit": "v0.3.2", "include_treaty_badge": True}
        new = {"_commit": "v0.3.3", "include_treaty_badge": True}
        with patch("copier.run_update"), patch(
            "agent_collab_treaty.cli._read_answers", side_effect=[old, new]
        ), patch(
            "agent_collab_treaty.cli._git_output",
            return_value=" M AGENTS.md\n M .copier-answers.yml\n",
        ):
            result = self.runner.invoke(app, ["update", "/some/dest"])

        self.assertEqual(0, result.exit_code)
        self.assertIn("Template version: v0.3.2 -> v0.3.3", result.output)
        self.assertIn("Updated files:", result.output)
        self.assertIn("git add -A && git commit", result.output)
        self.assertNotIn("Conflicts", result.output)

    def test_update_preserves_answers_by_default_and_reanswers_on_interactive(
        self,
    ) -> None:
        answers = {"_commit": "v0.3.3"}
        with patch("copier.run_update") as run_update, patch(
            "agent_collab_treaty.cli._read_answers", return_value=answers
        ), patch("agent_collab_treaty.cli._git_output", return_value=""):
            self.runner.invoke(app, ["update", "/some/dest"])
            self.assertTrue(run_update.call_args.kwargs["defaults"])

            run_update.reset_mock()
            self.runner.invoke(app, ["update", "/some/dest", "--interactive"])
            self.assertFalse(run_update.call_args.kwargs["defaults"])

    def test_update_dry_run_outside_a_git_repo_explains_and_exits_nonzero(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch("copier.run_update") as run_update:
                result = self.runner.invoke(app, ["update", tmp, "--dry-run"])

        self.assertEqual(1, result.exit_code)
        self.assertIn("Could not clone the project", result.output)
        run_update.assert_not_called()

    def test_init_warns_when_git_ignores_the_answers_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git(root, "init", "-b", "main")
            (root / ".gitignore").write_text(".copier-answers.yml\n", encoding="utf-8")

            with patch("copier.run_copy"):
                result = self.runner.invoke(
                    app, ["init", str(root), "--source", ".", "--defaults"]
                )

        self.assertEqual(0, result.exit_code)
        self.assertIn("git ignores .copier-answers.yml", result.output)

    def test_init_does_not_warn_when_the_answers_file_is_trackable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            _git(root, "init", "-b", "main")

            with patch("copier.run_copy"):
                result = self.runner.invoke(
                    app, ["init", str(root), "--source", ".", "--defaults"]
                )

        self.assertEqual(0, result.exit_code)
        self.assertNotIn("git ignores", result.output)

    def test_classify_status_splits_changed_and_unmerged(self) -> None:
        porcelain = "UU AGENTS.md\n M work_log.md\n?? new.txt\nAA both.md\n"
        changed, unmerged = _classify_status(porcelain)
        self.assertEqual(["new.txt", "work_log.md"], changed)
        self.assertEqual(["AGENTS.md", "both.md"], unmerged)

    def test_format_update_summary_reports_answer_changes(self) -> None:
        old = {"_commit": "v0.3.2", "include_treaty_badge": False}
        new = {"_commit": "v0.3.3", "include_treaty_badge": True}
        lines = "\n".join(_format_update_summary(old, new, ["AGENTS.md"], []))
        self.assertIn("Template version: v0.3.2 -> v0.3.3", lines)
        self.assertIn("Answer changes:", lines)
        self.assertIn("include_treaty_badge: False -> True", lines)

    def test_version_reports_cli_and_pinned_template_versions(self) -> None:
        from agent_collab_treaty import __version__

        answers = {
            "_commit": "v0.4.1",
            "_src_path": "gh:yzhaoinuw/agent_collab_treaty",
            "integration_branch": "main",
        }
        with patch("agent_collab_treaty.cli._read_answers", return_value=answers):
            result = self.runner.invoke(app, ["--version"])

        self.assertEqual(0, result.exit_code)
        self.assertIn(f"treaty {__version__}", result.output)
        self.assertIn("template v0.4.1 (gh:yzhaoinuw/agent_collab_treaty)", result.output)

    def test_version_outside_a_project_reports_cli_version_only(self) -> None:
        from agent_collab_treaty import __version__

        with patch("agent_collab_treaty.cli._read_answers", return_value={}):
            result = self.runner.invoke(app, ["--version"])

        self.assertEqual(0, result.exit_code)
        self.assertIn(f"treaty {__version__}", result.output)
        self.assertNotIn("template", result.output)

    def test_version_flag_does_not_require_a_subcommand(self) -> None:
        with tempfile.TemporaryDirectory() as tmp, patch("copier.run_copy") as run_copy:
            result = self.runner.invoke(app, ["--version"], env={"PWD": tmp})

        self.assertEqual(0, result.exit_code)
        run_copy.assert_not_called()

    def test_diff_reports_drift_against_the_pinned_template_version(self) -> None:
        def fake_render(source, ref, answers, target) -> None:
            (target / "AGENTS.md").write_text(
                "## Startup Rule\n\nRead this first.\n\n## Release / Tag Checklist\n\nGate the tag.\n",
                encoding="utf-8",
            )

        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "AGENTS.md").write_text(
                "## Startup Rule\n\nRead this first.\n\n## Story Bible\n\nOurs.\n",
                encoding="utf-8",
            )
            answers = {
                "_commit": "v0.4.1",
                "_src_path": "gh:yzhaoinuw/agent_collab_treaty",
                "integration_branch": "main",
            }
            with patch(
                "agent_collab_treaty.cli._read_answers", return_value=answers
            ), patch(
                "agent_collab_treaty.cli._render_pristine", side_effect=fake_render
            ) as render:
                result = self.runner.invoke(app, ["diff", str(root)])

        self.assertEqual(0, result.exit_code)
        self.assertEqual("gh:yzhaoinuw/agent_collab_treaty", render.call_args.args[0])
        self.assertEqual("v0.4.1", render.call_args.args[1])
        self.assertIn("template version v0.4.1", result.output)
        self.assertIn("! removed: '## Release / Tag Checklist'", result.output)
        self.assertIn("Conflict exposure: 1 section(s)", result.output)
        self.assertIn("Nothing was written.", result.output)

    def test_render_pristine_replays_answers_without_copier_bookkeeping(self) -> None:
        answers = {
            "_commit": "v0.4.1",
            "_src_path": "gh:yzhaoinuw/agent_collab_treaty",
            "integration_branch": "dev",
        }
        with patch("copier.run_copy") as run_copy:
            _render_pristine("gh:yzhaoinuw/agent_collab_treaty", "v0.4.1", answers, Path("/tmp/x"))

        kwargs = run_copy.call_args.kwargs
        # docs_dir is pinned flat: a project installed before that question
        # existed is flat on disk, so the pristine render has to be flat too or
        # `treaty diff` would report the whole treaty as drift.
        self.assertEqual(
            {"docs_dir": ".", "integration_branch": "dev"}, kwargs["data"]
        )
        self.assertEqual("v0.4.1", kwargs["vcs_ref"])
        self.assertTrue(kwargs["defaults"])

    def test_render_pristine_keeps_a_recorded_docs_dir(self) -> None:
        answers = {
            "_commit": "v0.8.0",
            "_src_path": "gh:yzhaoinuw/agent_collab_treaty",
            "docs_dir": "treaty_docs",
        }
        with patch("copier.run_copy") as run_copy:
            _render_pristine("gh:yzhaoinuw/agent_collab_treaty", "v0.8.0", answers, Path("/tmp/x"))

        self.assertEqual({"docs_dir": "treaty_docs"}, run_copy.call_args.kwargs["data"])

    def test_diff_requires_an_installed_project(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with patch("agent_collab_treaty.cli._render_pristine") as render:
                result = self.runner.invoke(app, ["diff", tmp])

        self.assertEqual(1, result.exit_code)
        self.assertIn("treaty init", result.output)
        render.assert_not_called()

    def test_validate_migration_hints_reports_overlapping_docs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "TODO.md").write_text("# TODO\n", encoding="utf-8")

            default_result = self.runner.invoke(app, ["validate", str(root)])
            hinted_result = self.runner.invoke(
                app,
                ["validate", str(root), "--migration-hints"],
            )

        self.assertEqual(0, default_result.exit_code)
        self.assertNotIn("TODO.md", default_result.output)
        self.assertEqual(0, hinted_result.exit_code)
        self.assertIn("Migration hints", hinted_result.output)
        self.assertIn("TODO.md", hinted_result.output)

def write_valid_project(root: Path) -> None:
    (root / "work_log_archive").mkdir()
    (root / "AGENTS.md").write_text("# Guidelines\n", encoding="utf-8")
    (root / "project_overview.md").write_text("# Project Overview\n", encoding="utf-8")
    (root / "next_steps.md").write_text(
        "\n".join(
            [
                "# Next Steps",
                "",
                "## Currently Hot",
                "",
                "- **Thread** - see [Thread](#thread-gpt-5).",
                "",
                "## Thread (gpt-5)",
                "",
                "Status: proposed",
            ]
        ),
        encoding="utf-8",
    )
    (root / "work_log.md").write_text(
        "\n".join(
            [
                "# Work Log",
                "",
                "## 2026-05-27",
                "",
                "### Entry (gpt-5)",
                "",
                "- Did a thing.",
                "- Verification:",
                "  - checked",
            ]
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    unittest.main()
