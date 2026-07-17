from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from agent_collab_treaty.cli import (
    _classify_status,
    _format_update_summary,
    app,
)


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
        self.assertIn("Template version: v0.3.2 → v0.3.3", result.output)
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

    def test_update_dry_run_pretends_without_writing(self) -> None:
        with patch("copier.run_update") as run_update:
            result = self.runner.invoke(app, ["update", "/some/dest", "--dry-run"])

        self.assertEqual(0, result.exit_code)
        self.assertTrue(run_update.call_args.kwargs["pretend"])
        self.assertIn("Preview only", result.output)

    def test_classify_status_splits_changed_and_unmerged(self) -> None:
        porcelain = "UU AGENTS.md\n M work_log.md\n?? new.txt\nAA both.md\n"
        changed, unmerged = _classify_status(porcelain)
        self.assertEqual(["new.txt", "work_log.md"], changed)
        self.assertEqual(["AGENTS.md", "both.md"], unmerged)

    def test_format_update_summary_reports_answer_changes(self) -> None:
        old = {"_commit": "v0.3.2", "include_treaty_badge": False}
        new = {"_commit": "v0.3.3", "include_treaty_badge": True}
        lines = "\n".join(_format_update_summary(old, new, ["AGENTS.md"], []))
        self.assertIn("Template version: v0.3.2 → v0.3.3", lines)
        self.assertIn("Answer changes:", lines)
        self.assertIn("include_treaty_badge: False → True", lines)

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
