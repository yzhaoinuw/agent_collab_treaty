from __future__ import annotations

import subprocess
import tempfile
import unittest
from datetime import date
from pathlib import Path

from agent_collab_treaty.validation import validate_project


def _git(cwd: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, check=True)


class TreatyValidationTests(unittest.TestCase):
    def test_valid_project_has_no_issues(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)

            issues = validate_project(root)

        self.assertEqual([], issues)

    def test_gitignored_answers_file_is_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            _git(root, "init", "-b", "main")
            (root / ".gitignore").write_text(".copier-answers.yml\n", encoding="utf-8")
            (root / ".copier-answers.yml").write_text("_commit: v0.6.0\n", encoding="utf-8")

            issues = validate_project(root)

        self.assertEqual(["answers-file-gitignored"], [issue.code for issue in issues])

    def test_trackable_answers_file_is_not_flagged(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            _git(root, "init", "-b", "main")
            (root / ".copier-answers.yml").write_text("_commit: v0.6.0\n", encoding="utf-8")

            issues = validate_project(root)

        self.assertEqual([], issues)

    def test_missing_answers_file_is_not_flagged_even_with_an_ignore_rule(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            _git(root, "init", "-b", "main")
            (root / ".gitignore").write_text(".copier-answers.yml\n", encoding="utf-8")

            issues = validate_project(root)

        self.assertEqual([], issues)

    def test_work_log_reports_missing_metadata_and_verification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "work_log.md").write_text(
                "\n".join(
                    [
                        "# Work Log",
                        "",
                        "## 2026-05-27",
                        "",
                        "### Missing metadata",
                        "",
                        "- Did a thing.",
                    ]
                ),
                encoding="utf-8",
            )

            issues = validate_project(root)

        codes = {issue.code for issue in issues}
        self.assertIn("work-log-missing-session-metadata", codes)
        self.assertIn("work-log-missing-verification", codes)

    def test_inline_verification_evidence_gets_a_specific_fix(self) -> None:
        """#15 follow-up: the words '- Verification:' were visibly present, so
        the generic 'should include a subsection' message read as wrong."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
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
                        "- Verification: inspected the calculation; ran git diff --check.",
                    ]
                ),
                encoding="utf-8",
            )

            issues = validate_project(root)

        self.assertEqual(["work-log-missing-verification"], [i.code for i in issues])
        self.assertEqual(8, issues[0].line, "should point at the inline line itself")
        self.assertIn("on its own line", issues[0].message)

    def test_wrong_case_work_log_reports_one_path_issue_only(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "work_log.md").unlink()
            (root / "Work_Log.md").write_text(
                "\n".join(
                    [
                        "# Work Log",
                        "",
                        "## 2026-05-27",
                        "",
                        "### Legacy heading",
                        "",
                        "- Did a thing.",
                    ]
                ),
                encoding="utf-8",
            )

            issues = validate_project(root)

        codes = [issue.code for issue in issues]
        self.assertEqual(["noncanonical-path-case"], codes)

    def test_wrong_case_required_path_reports_noncanonical_name(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "next_steps.md").unlink()
            (root / "Next_Steps.md").write_text("# Next Steps\n", encoding="utf-8")

            issues = validate_project(root)

        codes = [issue.code for issue in issues]
        self.assertIn("noncanonical-path-case", codes)
        self.assertNotIn("next-steps-missing-currently-hot", codes)

    def test_case_collision_reports_path_collision_when_supported(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "Work_Log.md").write_text("# Legacy Work Log\n", encoding="utf-8")
            work_log_matches = [
                path.name for path in root.iterdir() if path.name.lower() == "work_log.md"
            ]
            if len(work_log_matches) < 2:
                self.skipTest("Filesystem does not support case-only duplicate paths")

            issues = validate_project(root)

        self.assertIn("path-case-collision", {issue.code for issue in issues})

    def test_work_log_reports_rotation_needed(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            dates = [
                "2026-05-27",
                "2026-05-26",
                "2026-05-25",
                "2026-05-24",
                "2026-05-23",
                "2026-05-22",
            ]
            body = ["# Work Log", ""]
            for date in dates:
                body.extend(
                    [
                        f"## {date}",
                        "",
                        "### Entry (gpt-5)",
                        "",
                        "- Did a thing.",
                        "- Verification:",
                        "  - checked",
                        "",
                    ]
                )
            (root / "work_log.md").write_text("\n".join(body), encoding="utf-8")

            issues = validate_project(root)

        self.assertIn("work-log-rotation-needed", {issue.code for issue in issues})

    def test_work_log_reports_future_date(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "work_log.md").write_text(
                "\n".join(
                    [
                        "# Work Log",
                        "",
                        "## 2026-07-02",
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

            issues = validate_project(root, today=date(2026, 7, 1))

        self.assertIn("work-log-future-date", {issue.code for issue in issues})

    def test_work_log_todays_date_is_not_flagged_as_future(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "work_log.md").write_text(
                "\n".join(
                    [
                        "# Work Log",
                        "",
                        "## 2026-07-01",
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

            issues = validate_project(root, today=date(2026, 7, 1))

        self.assertNotIn("work-log-future-date", {issue.code for issue in issues})

    def test_next_steps_reports_broken_currently_hot_anchor(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "next_steps.md").write_text(
                "\n".join(
                    [
                        "# Next Steps",
                        "",
                        "## Currently Hot",
                        "",
                        "- **Missing** - see [Missing](#missing-thread).",
                    ]
                ),
                encoding="utf-8",
            )

            issues = validate_project(root)

        self.assertIn("next-steps-broken-hot-link", {issue.code for issue in issues})


class WarningTests(unittest.TestCase):
    """Warnings are reported by validate_project but never fail validation."""

    def test_claude_pointer_without_an_import_is_a_warning(self) -> None:
        """Issue #27: a request to read AGENTS.md is not an import of it."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "CLAUDE.md").write_text(
                "In a new chat, read AGENTS.md first.\n", encoding="utf-8"
            )

            issues = validate_project(root)

        self.assertEqual(["claude-pointer-missing-import"], [i.code for i in issues])
        self.assertFalse(issues[0].is_error)

    def test_claude_pointer_with_an_import_is_clean(self) -> None:
        for body in ("@AGENTS.md\n", "# Claude\n\n@./AGENTS.md\n", "See @AGENTS.md for the rules.\n"):
            with self.subTest(body=body), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                write_valid_project(root)
                (root / "CLAUDE.md").write_text(body, encoding="utf-8")

                self.assertEqual([], validate_project(root))

    def test_cli_older_than_the_pinned_template_is_a_warning(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / ".copier-answers.yml").write_text("_commit: v99.0.0\n", encoding="utf-8")

            issues = validate_project(root)

        self.assertEqual(["cli-older-than-template"], [i.code for i in issues])
        self.assertFalse(issues[0].is_error)
        self.assertIn("pip install -U agent-collab-treaty", issues[0].message)

    def test_cli_matching_or_newer_than_the_pin_is_clean(self) -> None:
        from agent_collab_treaty import __version__

        for commit in (f"v{__version__}", f"v{__version__}-4-gabc1234", "v0.1.0", "abc1234"):
            with self.subTest(commit=commit), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                write_valid_project(root)
                (root / ".copier-answers.yml").write_text(f"_commit: {commit}\n", encoding="utf-8")

                self.assertEqual([], validate_project(root))



NEXT_STEPS_WITH_BACKGROUND = """# Next Steps

## Currently Hot

- **Thread** - see [Thread](#thread-gpt-5).

{stale}## Thread (gpt-5)

Status: in progress

## Background / Paused

Sections below this line are older threads kept for context.

### Old thread (gpt-5)

Status: paused
"""


class AdopterCopyWarningTests(unittest.TestCase):
    """Template text the adopter must fix in their own copy, because the
    work_log.md / next_steps.md templates can't change upstream (2026-10-22)."""

    def codes(self, root: Path) -> list[str]:
        issues = validate_project(root)
        self.assertTrue(all(not i.is_error for i in issues), issues)
        return [i.code for i in issues]

    def test_first_run_paragraph_in_a_log_with_entries(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            log = root / "work_log.md"
            log.write_text(
                log.read_text().replace(
                    "# Work Log\n",
                    "# Work Log\n\n**Setting this up for the first time?** Leave this file empty.\n",
                ),
                encoding="utf-8",
            )
            issues = validate_project(root)

        self.assertEqual(["work-log-first-run-text"], [i.code for i in issues])
        self.assertEqual(3, issues[0].line)
        self.assertFalse(issues[0].is_error)

    def test_first_run_paragraph_in_an_empty_log_is_fine(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "work_log.md").write_text(
                "# Work Log\n\n**Setting this up for the first time?** Leave this file empty.\n",
                encoding="utf-8",
            )
            self.assertEqual([], self.codes(root))

    def test_stale_background_line_above_active_threads(self) -> None:
        """Issue #26: the line contradicts the layout it ships in."""
        stale = "Other sections below are background or paused; treat them as reference.\n\n"
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "next_steps.md").write_text(
                NEXT_STEPS_WITH_BACKGROUND.format(stale=stale), encoding="utf-8"
            )
            issues = validate_project(root)

        self.assertEqual(["next-steps-stale-background-line"], [i.code for i in issues])
        self.assertEqual(7, issues[0].line)

    def test_background_line_is_fine_without_threads_between(self) -> None:
        cases = {
            "no stale line": NEXT_STEPS_WITH_BACKGROUND.format(stale=""),
            # True as written: nothing sits between it and the divider.
            "right above the divider": (
                "# Next Steps\n\n## Currently Hot\n\n- none\n\n"
                "Other sections below are background or paused.\n\n"
                "## Background / Paused\n\n### Old\n"
            ),
            # No divider to judge against.
            "no divider": (
                "# Next Steps\n\n## Currently Hot\n\n- none\n\n"
                "Other sections below are background or paused.\n\n## Parked\n"
            ),
        }
        for name, body in cases.items():
            with self.subTest(name), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                write_valid_project(root)
                (root / "next_steps.md").write_text(body, encoding="utf-8")
                self.assertEqual([], self.codes(root))

    def test_currently_hot_thread_filed_under_background(self) -> None:
        """Issue #26: two agents, weeks apart, filed active threads as ###
        entries under Background / Paused."""
        body = NEXT_STEPS_WITH_BACKGROUND.format(stale="").replace(
            "- **Thread** - see [Thread](#thread-gpt-5).",
            "- **Thread** - see [Thread](#thread-gpt-5).\n- **Old** - see [Old](#old-thread-gpt-5).",
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "next_steps.md").write_text(body, encoding="utf-8")
            issues = validate_project(root)

        self.assertEqual(["next-steps-hot-thread-paused"], [i.code for i in issues])
        self.assertIn("#old-thread-gpt-5", issues[0].message)

    def test_placeholders_are_counted_once_per_file(self) -> None:
        """Issue #23: an update can add a section of placeholders to a doc the
        adopter finished long ago."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "project_overview.md").write_text(
                "# Project Overview\n\nA real summary.\n\n## Authored vs. Derived\n\n"
                "- [`path/to/source_of_truth`](path/to/source_of_truth) — [what it generates]\n",
                encoding="utf-8",
            )
            issues = validate_project(root)

        self.assertEqual(["unfilled-placeholder"], [i.code for i in issues])
        self.assertEqual(7, issues[0].line)
        self.assertIn("2 template placeholder(s)", issues[0].message)

    def test_brackets_that_are_not_placeholders(self) -> None:
        body = "\n".join(
            [
                "# Guidelines",
                "",
                "See [Documentation](#documentation) and [pre-commit](https://pre-commit.com).",
                "Reference-style [docs][ref] and an image ![logo](logo.png).",
                "",
                "[ref]: https://example.com",
                "",
                "- [ ] open task",
                "- [x] done task",
                "A footnote.[^1]",
                "Inline code: `rg -n '^## [0-9]{4}'` and `a[i]`.",
                "",
                "```",
                "matrix[row][col] = [fill me in]",
                "```",
                "<!-- [commented placeholder] -->",
            ]
        )
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            write_valid_project(root)
            (root / "AGENTS.md").write_text(body, encoding="utf-8")
            self.assertEqual([], self.codes(root))

    @unittest.skipIf(
        __import__("os").environ.get("TREATY_SKIP_INTEGRATION") == "1",
        "TREATY_SKIP_INTEGRATION=1",
    )
    def test_fresh_install_gets_warnings_and_no_errors(self) -> None:
        """A fresh init must still pass validate; the warnings are its to-do list."""
        import copier

        repo = Path(__file__).resolve().parents[1]
        for docs_dir in (".", "treaty_docs"):
            with self.subTest(docs_dir=docs_dir), tempfile.TemporaryDirectory() as tmp:
                root = Path(tmp)
                copier.run_copy(
                    str(repo), str(root), vcs_ref="HEAD", defaults=True,
                    data={"docs_dir": docs_dir}, quiet=True,
                )
                issues = validate_project(root)

                self.assertEqual([], [i for i in issues if i.is_error])
                self.assertEqual(
                    sorted(
                        [
                            "next-steps-stale-background-line",
                            "unfilled-placeholder",
                            "unfilled-placeholder",
                            "unfilled-placeholder",
                        ]
                    ),
                    sorted(i.code for i in issues),
                )

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
                "<!--",
                "### Commented heading without metadata",
                "-->",
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
