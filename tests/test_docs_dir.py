"""Tests for the ``docs_dir`` layout question and its legacy-compatibility shim.

The load-bearing guarantee is in ``test_flat_layout_paths_are_frozen``: the set
of files the flat layout renders may never change. Copier implements a
template-side file move as "delete the adopter's customized file, write a
pristine one at the new path" — it does not merge, does not conflict, and does
not warn, so a path change silently destroys an adopter's work log.

That guarantee used to be enforced by comparing the whole rendered tree
byte-for-byte against ``v0.7.0``, which also froze every word of prose. Measured
2026-08-13 against real Copier updates (``FlatConventionsMergeTests`` and
``FlatWorkLogMergeTests`` below): a *content* change costs an adopter at most one
visible merge conflict, and only where they had edited the same region. No
scenario lost adopter content. Content and paths are therefore enforced
separately — paths absolutely, content by what it actually costs.
"""

from __future__ import annotations

import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from agent_collab_treaty.cli import _legacy_layout_data
from agent_collab_treaty.validation import required_paths, resolve_docs_dir

REPO_ROOT = Path(__file__).resolve().parents[1]
BASELINE_REF = "v0.7.0"
SKIP_INTEGRATION = os.environ.get("TREATY_SKIP_INTEGRATION") == "1"

CONVENTIONS_TEMPLATE = "template/{{ docs_dir }}/treaty_conventions.md.jinja"
WORK_LOG_TEMPLATE = "template/{{ docs_dir }}/work_log.md"
FIRST_RUN_TEXT = "**Setting this up for the first time?**"

# Only a line-anchored marker is a real one: treaty_conventions.md documents
# `<<<<<<< before updating` in its own prose, so a substring check reports a
# conflict in every rendering.
CONFLICT_MARKER = re.compile(r"^<{7} |^>{7} ", re.M)


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )


def _commit(cwd: Path, message: str) -> None:
    _git("add", "-A", cwd=cwd)
    _git("-c", "user.email=t@e.st", "-c", "user.name=T", "commit", "-qm", message, cwd=cwd)


def _render(source: Path, ref: str, target: Path, **data: str) -> None:
    import copier

    copier.run_copy(
        src_path=str(source),
        dst_path=str(target),
        vcs_ref=ref,
        data=dict(data),
        defaults=True,
        quiet=True,
        overwrite=True,
    )


def _tree(root: Path) -> dict[str, str]:
    """Map every rendered file to its text, excluding Copier bookkeeping."""
    out: dict[str, str] = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root).as_posix()
        if rel == ".copier-answers.yml":
            continue
        out[rel] = path.read_text(encoding="utf-8")
    return out


class LegacyLayoutDataTests(unittest.TestCase):
    def test_pins_projects_with_no_recorded_docs_dir(self) -> None:
        self.assertEqual({"docs_dir": "."}, _legacy_layout_data({"_commit": "v0.7.0"}))

    def test_leaves_projects_that_already_answered_alone(self) -> None:
        self.assertEqual({}, _legacy_layout_data({"docs_dir": "treaty_docs"}))
        self.assertEqual({}, _legacy_layout_data({"docs_dir": "."}))

    def test_ignores_projects_with_no_answers_at_all(self) -> None:
        self.assertEqual({}, _legacy_layout_data({}))


class RequiredPathsTests(unittest.TestCase):
    def test_flat_layout_keeps_root_paths(self) -> None:
        self.assertIn("work_log.md", required_paths("."))
        self.assertIn("AGENTS.md", required_paths("."))

    def test_nested_layout_prefixes_only_the_docs(self) -> None:
        paths = required_paths("treaty_docs")
        self.assertIn("treaty_docs/work_log.md", paths)
        self.assertIn("treaty_docs/work_log_archive", paths)
        self.assertIn("AGENTS.md", paths)
        self.assertIn("project_overview.md", paths)

    def test_trailing_slash_is_tolerated(self) -> None:
        self.assertIn("treaty_docs/work_log.md", required_paths("treaty_docs/"))


class ResolveDocsDirTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_prefers_the_recorded_answer(self) -> None:
        (self.tmp / ".copier-answers.yml").write_text("docs_dir: treaty_docs\n")
        self.assertEqual("treaty_docs", resolve_docs_dir(self.tmp))

    def test_falls_back_to_flat_when_work_log_is_at_the_root(self) -> None:
        (self.tmp / "work_log.md").write_text("# Work Log\n")
        self.assertEqual(".", resolve_docs_dir(self.tmp))

    def test_detects_an_unrecorded_docs_folder(self) -> None:
        (self.tmp / "notes").mkdir()
        (self.tmp / "notes" / "work_log.md").write_text("# Work Log\n")
        self.assertEqual("notes", resolve_docs_dir(self.tmp))

    def test_defaults_to_flat_when_nothing_is_installed(self) -> None:
        self.assertEqual(".", resolve_docs_dir(self.tmp))


@unittest.skipIf(SKIP_INTEGRATION, "TREATY_SKIP_INTEGRATION=1")
class FlatRenderingCompatibilityTests(unittest.TestCase):
    """The flat rendering's *paths* must not drift from the last pre-docs_dir release."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_flat_layout_paths_are_frozen(self) -> None:
        """No file may move, appear, or disappear in the flat rendering. Ever.

        This one has no escape hatch and no acceptable reason to be updated.
        Copier applies a template-side path change as delete-plus-create, with
        no merge, no conflict, and no warning: the adopter's customized file is
        gone and a pristine one sits at the new path. Verified 2026-08-11, when
        a naive move wiped a customized work_log.md and left only `D
        work_log.md` in git status.

        If this fails, the fix is to revert the path change and express the
        layout as a Copier answer (`docs_dir`) instead — never to update the
        baseline.
        """
        baseline = self.tmp / "baseline"
        current = self.tmp / "current"
        _render(REPO_ROOT, BASELINE_REF, baseline)
        _render(REPO_ROOT, "HEAD", current, docs_dir=".")

        self.assertEqual(
            sorted(_tree(baseline)),
            sorted(_tree(current)),
            "docs_dir='.' changed which files are rendered; existing adopters "
            "would see files move, which Copier applies as delete-plus-create.",
        )

    def test_nested_layout_moves_only_the_working_docs(self) -> None:
        nested = self.tmp / "nested"
        _render(REPO_ROOT, "HEAD", nested, docs_dir="treaty_docs")
        rendered = set(_tree(nested))

        self.assertIn("AGENTS.md", rendered)
        self.assertIn("project_overview.md", rendered)
        for name in ("work_log.md", "next_steps.md", "treaty_conventions.md"):
            self.assertIn(f"treaty_docs/{name}", rendered)
            self.assertNotIn(name, rendered)
        self.assertIn("treaty_docs/work_log_archive/README.md", rendered)

    def test_nested_layout_rewrites_cross_document_links(self) -> None:
        nested = self.tmp / "nested"
        _render(REPO_ROOT, "HEAD", nested, docs_dir="treaty_docs")

        agents = (nested / "AGENTS.md").read_text(encoding="utf-8")
        self.assertIn("treaty_docs/work_log.md", agents)
        self.assertIn("treaty_docs/treaty_conventions.md", agents)

        conventions = (nested / "treaty_docs" / "treaty_conventions.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("../AGENTS.md", conventions)
        self.assertIn("../project_overview.md", conventions)

        # Docs that moved together keep plain same-directory links.
        archive = (
            nested / "treaty_docs" / "work_log_archive" / "README.md"
        ).read_text(encoding="utf-8")
        self.assertIn("../work_log.md", archive)

    def test_multi_segment_docs_dir_gets_a_depth_aware_root_prefix(self) -> None:
        """A nested-deeper docs_dir must still link back to the real repo root.

        Reported from the Windows sweep: root_prefix used to be a hardcoded
        '../', so `docs_dir=docs/agents` produced links that resolved one level
        short — to docs/AGENTS.md, which does not exist. README advertises
        exactly that value, so it has to work at any depth.
        """
        for docs_dir, expected in (
            ("treaty_docs", "../"),
            ("docs/agents", "../../"),
            ("a/b/c", "../../../"),
            ("trailing/slash/", "../../"),
        ):
            with self.subTest(docs_dir=docs_dir):
                target = self.tmp / f"seg_{docs_dir.strip('/').replace('/', '_')}"
                _render(REPO_ROOT, "HEAD", target, docs_dir=docs_dir)

                conventions = target / docs_dir.strip("/") / "treaty_conventions.md"
                text = conventions.read_text(encoding="utf-8")
                self.assertIn(f"]({expected}AGENTS.md)", text)
                self.assertIn(f"`{expected}project_overview.md`", text)

                # The link must actually resolve to the file on disk.
                self.assertTrue(
                    (conventions.parent / f"{expected}AGENTS.md").resolve().is_file(),
                    f"{expected}AGENTS.md does not resolve from {conventions.parent}",
                )


@unittest.skipIf(SKIP_INTEGRATION, "TREATY_SKIP_INTEGRATION=1")
class LegacyAdopterUpdateTests(unittest.TestCase):
    """End-to-end: a v0.7.0 adopter updating across the restructure."""

    def setUp(self) -> None:
        # Resolve symlinks (macOS /var -> /private/var) or Copier's repo-root
        # detection sees a "different" path than the one it was given.
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

        # Tag a throwaway clone so Copier sees a newer version to update to.
        self.template = self.tmp / "template"
        subprocess.run(
            ["git", "clone", "--quiet", "--no-local", str(REPO_ROOT), str(self.template)],
            check=True,
            capture_output=True,
        )
        _git("checkout", "-q", "--detach", "HEAD", cwd=self.template)
        _git("tag", "-f", "v99.0.0", cwd=self.template)

    def _build_adopter(self) -> Path:
        project = self.tmp / "adopter"
        _render(self.template, BASELINE_REF, project)
        _git("init", "-q", ".", cwd=project)
        _git("add", "-A", cwd=project)
        _git("-c", "user.email=t@e.st", "-c", "user.name=T", "commit", "-qm", "base", cwd=project)

        log = project / "work_log.md"
        log.write_text(
            log.read_text(encoding="utf-8").replace(
                "# Work Log",
                "# Work Log\n\n## 2026-08-10\n\n### Session (Opus 5)\n\n"
                "IRREPLACEABLE ADOPTER HISTORY.\n\n- Verification: pytest\n",
                1,
            ),
            encoding="utf-8",
        )
        agents = project / "AGENTS.md"
        agents.write_text(
            agents.read_text(encoding="utf-8") + "\n## Our Own Section\n\nLocal rule.\n",
            encoding="utf-8",
        )
        _git("add", "-A", cwd=project)
        _git("-c", "user.email=t@e.st", "-c", "user.name=T", "commit", "-qm", "custom", cwd=project)
        return project

    def test_update_preserves_layout_and_content(self) -> None:
        import copier

        from agent_collab_treaty.cli import _read_answers

        project = self._build_adopter()
        old_answers = _read_answers(project)
        self.assertNotIn("docs_dir", old_answers)

        copier.run_update(
            dst_path=str(project),
            data=_legacy_layout_data(old_answers),
            defaults=True,
            overwrite=True,
            quiet=True,
        )

        self.assertTrue((project / "work_log.md").exists(), "work log must not move")
        self.assertFalse((project / "treaty_docs").exists(), "nothing may be relocated")
        self.assertIn(
            "IRREPLACEABLE ADOPTER HISTORY",
            (project / "work_log.md").read_text(encoding="utf-8"),
        )
        self.assertIn(
            "Our Own Section", (project / "AGENTS.md").read_text(encoding="utf-8")
        )
        self.assertEqual(".", _read_answers(project).get("docs_dir"))

        status = _git("status", "--porcelain", cwd=project).stdout
        conflicted = [ln for ln in status.splitlines() if "U" in ln[:2]]
        self.assertEqual([], conflicted, f"update conflicted:\n{status}")


class _FlatContentChangeCase(unittest.TestCase):
    """Shared rig: publish a template with one prose edit, then update adopters.

    Each subclass edits exactly one file, never a path, and renders its adopters
    at v0.7.0 flat — the cohort the frozen rendering exists to protect. The
    template is built once per class because cloning and rendering dominate the
    runtime.
    """

    #: Subclasses mutate the cloned template in place, prose only.
    edit_template: staticmethod

    @classmethod
    def setUpClass(cls) -> None:
        if SKIP_INTEGRATION:
            raise unittest.SkipTest("TREATY_SKIP_INTEGRATION=1")
        # Resolve symlinks (macOS /var -> /private/var) or Copier's repo-root
        # detection sees a "different" path than the one it was given.
        cls.tmp = Path(tempfile.mkdtemp()).resolve()
        cls.addClassCleanup(shutil.rmtree, cls.tmp, ignore_errors=True)

        cls.template = cls.tmp / "template"
        subprocess.run(
            ["git", "clone", "--quiet", "--no-local", str(REPO_ROOT), str(cls.template)],
            check=True,
            capture_output=True,
        )
        _git("checkout", "-q", "--detach", "HEAD", cwd=cls.template)
        cls.edit_template(cls.template)
        _commit(cls.template, "upstream prose edit")
        _git("tag", "-f", "v99.0.0", cwd=cls.template)

    def adopter(self, name: str, customize=lambda project: None) -> Path:
        """A v0.7.0 flat adopter with real history, plus any extra edits."""
        project = self.tmp / name
        _render(self.template, BASELINE_REF, project)
        _git("init", "-q", ".", cwd=project)
        _commit(project, "treaty baseline")

        log = project / "work_log.md"
        log.write_text(
            log.read_text(encoding="utf-8").replace(
                "# Work Log",
                "# Work Log\n\n## 2026-08-10\n\n### Session (Opus 5)\n\n"
                "IRREPLACEABLE ADOPTER HISTORY.\n",
                1,
            ),
            encoding="utf-8",
        )
        customize(project)
        _commit(project, "customize")
        return project

    def update(self, project: Path) -> list[str]:
        """Run the real update; return the unmerged paths git reports."""
        import copier

        from agent_collab_treaty.cli import _read_answers

        copier.run_update(
            dst_path=str(project),
            data=_legacy_layout_data(_read_answers(project)),
            defaults=True,
            overwrite=True,
            quiet=True,
        )
        status = _git("status", "--porcelain", cwd=project).stdout
        return [line[3:] for line in status.splitlines() if "U" in line[:2]]

    def assertHistorySurvived(self, project: Path) -> None:
        """The non-negotiable outcome: a content change never costs content."""
        log = (project / "work_log.md").read_text(encoding="utf-8")
        self.assertIn(
            "IRREPLACEABLE ADOPTER HISTORY",
            log,
            "a template content change destroyed adopter work-log history",
        )
        self.assertFalse(
            (project / "treaty_docs").exists(), "a content change relocated the docs"
        )


def _add_conventions_prose(template: Path) -> None:
    path = template / CONVENTIONS_TEMPLATE
    text = path.read_text(encoding="utf-8")
    path.write_text(
        text.replace(
            "## Updating The Treaty\n",
            "## Updating The Treaty\n\nUPSTREAM ADDITION for the merge test.\n",
            1,
        ),
        encoding="utf-8",
    )


class FlatConventionsMergeTests(_FlatContentChangeCase):
    """Prose changes to the upstream-maintained conventions file.

    This is the file adopters are told not to edit, so in a three-way merge
    their copy equals the base and upstream prose applies cleanly. It is the
    cheapest file in the template to change, not the most expensive — the
    blanket byte-identity freeze had that backwards.
    """

    edit_template = staticmethod(_add_conventions_prose)

    def _edit_section(self, heading: str):
        def customize(project: Path) -> None:
            path = project / "treaty_conventions.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(
                text.replace(heading, f"{heading}\nADOPTER NOTE.\n", 1), encoding="utf-8"
            )

        return customize

    def test_lands_cleanly_when_the_adopter_left_conventions_alone(self) -> None:
        project = self.adopter("untouched")
        self.assertEqual([], self.update(project))

        conventions = (project / "treaty_conventions.md").read_text(encoding="utf-8")
        self.assertIn("UPSTREAM ADDITION", conventions)
        self.assertIsNone(CONFLICT_MARKER.search(conventions))
        self.assertHistorySurvived(project)

    def test_lands_cleanly_alongside_an_edit_to_a_different_section(self) -> None:
        project = self.adopter("other_section", self._edit_section("## Work Log Discipline\n"))
        self.assertEqual([], self.update(project))

        conventions = (project / "treaty_conventions.md").read_text(encoding="utf-8")
        self.assertIn("UPSTREAM ADDITION", conventions)
        self.assertIn("ADOPTER NOTE", conventions)
        self.assertHistorySurvived(project)

    def test_conflicts_only_where_the_adopter_edited_the_same_section(self) -> None:
        """The priced cost of a content change — visible, resolvable, contained."""
        project = self.adopter("same_section", self._edit_section("## Updating The Treaty\n"))
        self.assertEqual(["treaty_conventions.md"], self.update(project))

        conventions = (project / "treaty_conventions.md").read_text(encoding="utf-8")
        self.assertIsNotNone(CONFLICT_MARKER.search(conventions))
        self.assertIn("ADOPTER NOTE", conventions, "the conflict must retain both sides")
        self.assertHistorySurvived(project)


def _comment_out_first_run_text(template: Path) -> None:
    """The #23.2 fix: first-run-only guidance must not merge into a live log."""
    path = template / WORK_LOG_TEMPLATE
    text = path.read_text(encoding="utf-8")
    start = text.index(FIRST_RUN_TEXT)
    end = text.index("\n", text.index("\n", start) + 1)
    paragraph = text[start:end]
    path.write_text(text.replace(paragraph, f"<!--\n{paragraph}\n-->", 1), encoding="utf-8")


class FlatWorkLogMergeTests(_FlatContentChangeCase):
    """Prose changes to a file every adopter edits heavily.

    The expensive end of the scale: the adopter's own entries sit directly below
    the header being changed. Even here the cost is one conflict, and only for
    an adopter who had edited that exact paragraph.
    """

    edit_template = staticmethod(_comment_out_first_run_text)

    def test_merges_into_a_log_with_real_history(self) -> None:
        project = self.adopter("live_log")
        self.assertEqual([], self.update(project))

        log = (project / "work_log.md").read_text(encoding="utf-8")
        self.assertIn(f"<!--\n{FIRST_RUN_TEXT}", log)
        self.assertIsNone(CONFLICT_MARKER.search(log))
        self.assertHistorySurvived(project)

    def test_conflicts_for_an_adopter_who_had_deleted_the_paragraph(self) -> None:
        """Exactly what issue #23 did by hand after their v0.3.3 -> v0.9.0 jump."""

        def drop_paragraph(project: Path) -> None:
            path = project / "work_log.md"
            text = path.read_text(encoding="utf-8")
            start = text.index(FIRST_RUN_TEXT)
            end = text.index("\n", text.index("\n", start) + 1)
            path.write_text(text[:start] + text[end:].lstrip("\n"), encoding="utf-8")

        project = self.adopter("deleted_paragraph", drop_paragraph)
        self.assertEqual(["work_log.md"], self.update(project))

        log = (project / "work_log.md").read_text(encoding="utf-8")
        self.assertIsNotNone(CONFLICT_MARKER.search(log))
        self.assertHistorySurvived(project)


if __name__ == "__main__":
    unittest.main()
