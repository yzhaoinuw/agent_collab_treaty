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
trap 'rm -f "$tmp"' EXIT

for q in "${QUERIES[@]}"; do
  gh api --paginate -X GET search/code -f q="$q" -f per_page=100 \
    --jq '.items[].repository.full_name' 2>/dev/null >>"$tmp" || true
done

adopters="$(sort -u "$tmp" | grep -Ev "$EXCLUDE_REGEX" || true)"
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
