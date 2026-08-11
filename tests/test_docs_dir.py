"""Tests for the ``docs_dir`` layout question and its legacy-compatibility shim.

The load-bearing guarantee is in ``test_flat_layout_is_byte_identical_to_v070``:
projects installed before ``docs_dir`` existed must see *no* file changes when
they update. Copier implements a template-side file move as "delete the
adopter's customized file, write a pristine one at the new path", so any drift
in the flat rendering is not a cosmetic diff — it is the failure mode that
silently destroys an adopter's work log.
"""

from __future__ import annotations

import os
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


def _git(*args: str, cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", *args], cwd=cwd, capture_output=True, text=True, check=True
    )


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
    """The flat rendering must not drift from the last pre-docs_dir release."""

    def setUp(self) -> None:
        self.tmp = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)

    def test_flat_layout_is_byte_identical_to_v070(self) -> None:
        baseline = self.tmp / "baseline"
        current = self.tmp / "current"
        _render(REPO_ROOT, BASELINE_REF, baseline)
        _render(REPO_ROOT, "HEAD", current, docs_dir=".")

        old, new = _tree(baseline), _tree(current)
        self.assertEqual(
            sorted(old),
            sorted(new),
            "docs_dir='.' changed which files are rendered; existing adopters "
            "would see files move, which Copier applies as delete-plus-create.",
        )
        for name in sorted(old):
            self.assertEqual(
                old[name],
                new[name],
                f"docs_dir='.' changed the contents of {name}; every existing "
                "adopter who customized it would get a merge conflict.",
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


if __name__ == "__main__":
    unittest.main()
