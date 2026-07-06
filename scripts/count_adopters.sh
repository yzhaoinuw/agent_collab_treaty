#!/usr/bin/env bash
# Count public GitHub repositories that have adopted the Agent Collab Treaty.
#
# Uses GitHub code search (via the gh CLI) to find repos that reference the
# treaty by its badge image URLs or its canonical repo link, filters out our
# own org and known crawlers, dedupes, and prints the adopter list + total.
#
# Runs on demand on your machine using your existing `gh` auth. No servers,
# no hosting, no cost. The same script is reused by the weekly GitHub Action
# that refreshes the adopters badge in README.md.
#
# Caveat: GitHub code search only indexes a subset of public repos (default
# branch, with lag), so the total is a floor, not an exact census.

set -euo pipefail

# Distinctive strings that effectively only appear in adopting repos.
#  - the canonical repo link (used by both badge variants + .copier-answers.yml)
#  - each badge image URL, in case a repo links the badge elsewhere
QUERIES=(
  'yzhaoinuw/agent_collab_treaty'
  'img.shields.io/badge/Agent_Collab_Treaty-adopted'
  'agent_collab_treaty/main/assets/treaty-adopted.svg'
)

# Owners/repos excluded from the adopter count:
#  - yzhaoinuw/agent_collab_treaty : the treaty repo itself (you don't adopt your own treaty)
#  - szabgab/pydigger              : a PyPI metadata crawler, not a real adopter
# Our own dogfood repos (other yzhaoinuw/* repos) ARE counted as adopters.
EXCLUDE_REGEX='^(yzhaoinuw/agent_collab_treaty$|szabgab/pydigger)'

if ! command -v gh >/dev/null 2>&1; then
  echo "error: gh CLI not found. Install it from https://cli.github.com/" >&2
  exit 1
fi

if ! gh auth status >/dev/null 2>&1; then
  echo "error: gh is not authenticated. Run: gh auth login" >&2
  exit 1
fi

tmp="$(mktemp)"
err="$(mktemp)"
trap 'rm -f "$tmp" "$err"' EXIT

# Shape of a valid GitHub "owner/repo" full name. Anything else that lands in
# the results (e.g. a rate-limit error body that gh may print on stdout) is
# discarded so it can never be miscounted as an adopter.
REPO_REGEX='^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$'

# Keep repo names (stdout) and errors (stderr) separate. A non-zero exit or a
# rate-limit response must NOT silently become "0 adopters" or, as happened
# once, a bogus "1 adopter" from a 429 JSON body leaking onto stdout.
search_failed=0
for q in "${QUERIES[@]}"; do
  if ! gh api --paginate -X GET search/code -f q="$q" -f per_page=100 \
        --jq '.items[].repository.full_name' >>"$tmp" 2>>"$err"; then
    search_failed=1
  fi
done

# Bail out on any failure or rate limit instead of reporting a number the badge
# updater would trust. An empty ADOPTER_COUNT plus a non-zero exit tells the
# caller to leave the displayed count unchanged.
if [ "$search_failed" -ne 0 ] || grep -qiE 'rate limit|"status":"(403|429)"|secondary rate' "$err"; then
  echo "error: GitHub code search failed or was rate-limited; not reporting a count." >&2
  sed 's/^/  gh: /' "$err" >&2 || true
  echo "ADOPTER_COUNT="
  exit 1
fi

# Count only real "owner/repo" lines, then dedupe and drop excluded repos.
adopters="$(grep -E "$REPO_REGEX" "$tmp" | sort -u | grep -Ev "$EXCLUDE_REGEX" || true)"
count="$(printf '%s\n' "$adopters" | grep -c . || true)"

echo "Agent Collab Treaty — public adopters"
echo "─────────────────────────────────────"
if [ "$count" -gt 0 ]; then
  printf '%s\n' "$adopters" | sed 's/^/  /'
else
  echo "  (none found yet)"
fi
echo
echo "Total adopters: $count"
echo "(excludes the treaty repo itself and the pydigger crawler; GitHub code-search index, so a floor)"

# Machine-readable line consumed by the weekly badge-updater Action.
echo "ADOPTER_COUNT=$count"
