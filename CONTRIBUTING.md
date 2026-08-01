# Contributing

The front door for human contributors. Agents joining a session read [`AGENTS.md`](AGENTS.md) first — and humans should skim it too: it is the repo's working contract, and everything below links into it rather than repeating it.

## Reporting Issues & Support

Open a [GitHub issue](https://github.com/yzhaoinuw/agent_collab_treaty/issues) for bugs, confusing docs, or feature ideas. If `treaty update` left conflicts you think it shouldn't have, include the output of `treaty --version` and `treaty diff` — together they usually pinpoint the cause.

## Dev Setup

Python 3.10+, no other toolchain:

```bash
python -m venv .venv && .venv/bin/python -m pip install -e .
```

## Before You Open a PR

- Work on a branch and open a PR against `dev`. `dev` is staging; `main` is release. (Only the repo's resident boss agent commits to `dev` directly; every other contributor — human or agent — goes through a PR. See `AGENTS.md` § Agent Roles.)
- Run the CI-equivalent pre-flight (full checklist in `AGENTS.md` § Common Tasks):

  ```bash
  git diff --check
  python -m unittest discover -s tests -v     # ~13s; includes real Copier merges
  treaty --help && treaty --version && treaty validate .
  ```

- This repo dogfoods the treaty it ships: substantive changes prepend a `work_log.md` entry and update `next_steps.md`. The criteria live in `AGENTS.md` § When To Update Treaty Docs.

## Touching `template/`

The template is the product — what `treaty init` installs into other people's repos. Three rules prevent downstream pain (full list: `AGENTS.md` § Project-Specific Reminders):

- Keep the boundary: root docs are specific to this repo, template docs stay generic. Don't copy root treaty docs into `template/`.
- **Never rename a `##` heading** in template docs. A three-way merge reads a rename as delete + add, so every downstream adopter gets a conflict that cannot be auto-resolved.
- Smoke-test template edits by rendering into a scratch dir with `treaty init … --source . --ref HEAD`. Without `--ref HEAD`, Copier silently renders the source repo's last commit instead of your working tree.

## Releases (Maintainers)

Two GitHub Actions workflows handle publishing, both via [PyPI Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC), so no API tokens are stored in the repo:

- `.github/workflows/release.yml` — fires on a `v*` tag push, builds sdist + wheel, publishes to PyPI, creates a GitHub Release.
- `.github/workflows/test-publish.yml` — manual `workflow_dispatch`, publishes to TestPyPI for dry-runs.

Cutting a release (doc gate first — see `AGENTS.md` § Release / Tag Checklist):

```bash
gh workflow run test-publish.yml      # dry-run to TestPyPI first

# smoke-test the dry-run:
pipx install --index-url https://test.pypi.org/simple/ \
  --pip-args="--extra-index-url https://pypi.org/simple/" agent-collab-treaty

# then bump the version in pyproject.toml, __init__.py, and CITATION.cff, and:
git tag -a v0.1.0 -m "v0.1.0" && git push origin v0.1.0
```

<details>
<summary>One-time trusted-publisher setup (per maintainer)</summary>

1. **PyPI account** at https://pypi.org, and a *separate* **TestPyPI account** at https://test.pypi.org — they're fully independent services with different credentials.
2. **Register as a Pending Publisher on PyPI**: https://pypi.org/manage/account/publishing/ → "Add a new pending publisher" → project `agent-collab-treaty`, owner `yzhaoinuw`, repo `agent_collab_treaty`, workflow `release.yml`, environment `pypi`.
3. **Register on TestPyPI the same way**, except workflow `test-publish.yml` and environment `testpypi`.
4. **Create both GitHub environments**: repo Settings → Environments → `pypi` and `testpypi`. No secrets needed, since OIDC handles auth. Optionally add protection rules, e.g. require manual approval for `pypi`.

</details>

## License

MIT. By contributing you agree your contributions are licensed under the same terms.
