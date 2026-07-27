#!/usr/bin/env bash
# Count public GitHub repositories that have adopted the Agent Collab Treaty.
#
# Two independent sources are unioned:
#
#   1. Owner scan  — lists OWNER's public non-fork repos via the repos API and
#      reads the candidate files directly. Authoritative for OWNER/*.
#   2. Code search — the only way to discover third-party adopters, but it can
#      only find repos GitHub has admitted to its code-search index.
#
# Why both: code search alone undercounts badly. Measured 2026-07-26, it found
# 6 of our 13 adopting repos. The 7 it missed are not in the index at all —
# ordinary words known to be in their READMEs return zero hits when scoped to
# those repos, while indexed repos return 8-34. Every missed repo was created
# 2026-03 or later and every found one 2025-07 or earlier; stars are not the
# discriminator (two zero-star repos are indexed). Nothing on our side fixes
# that, so we read our own repos directly instead of asking the index about them.
#
# Third-party adopters remain a floor: for repos we do not own, the index is
# the only source available, and it will miss the same class of repo.
#
# Runs on demand on your machine using your existing `gh` auth. No servers,
# no hosting, no cost. The same script is reused by the weekly GitHub Action
# that refreshes the adopters badge in README.md.

set -euo pipefail

OWNER='yzhaoinuw'
TREATY_REPO="$OWNER/agent_collab_treaty"

# Distinctive strings that effectively only appear in adopting repos.
#  - the canonical repo link (used by both badge variants + .copier-answers.yml)
#  - each badge image URL, in case a repo links the badge elsewhere
QUERIES=(
  'yzhaoinuw/agent_collab_treaty'
  'img.shields.io/badge/Agent_Collab_Treaty-adopted'
  'agent_collab_treaty/main/assets/treaty-adopted.svg'
)

# Same three strings as an ERE, for reading files directly in the owner scan.
# Keep in sync with QUERIES above.
MARKER_REGEX='yzhaoinuw/agent_collab_treaty|img\.shields\.io/badge/Agent_Collab_Treaty-adopted|agent_collab_treaty/main/assets/treaty-adopted\.svg'

# Root-level files an adopting repo can carry the marker in. README.md holds
# the badge; .copier-answers.yml is written by `treaty init`; AGENTS.md is the
# treaty's entry doc. A repo adopted by hand may have only some of these.
MARKER_FILES='README.md .copier-answers.yml AGENTS.md'

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
owned="$(mktemp)"
trap 'rm -f "$tmp" "$err" "$owned"' EXIT

# Shape of a valid GitHub "owner/repo" full name. Anything else that lands in
# the results (e.g. a rate-limit error body that gh may print on stdout) is
# discarded so it can never be miscounted as an adopter.
REPO_REGEX='^[A-Za-z0-9._-]+/[A-Za-z0-9._-]+$'

# ---------------------------------------------------------------------------
# Source 1: owner scan (index-independent, authoritative for OWNER/*)
# ---------------------------------------------------------------------------
# Forks are skipped: inheriting a README from an upstream fork is not adoption,
# and code search excludes forks too, so the two sources agree on that.
owner_failed=0
if ! gh api --paginate "users/$OWNER/repos?type=owner&per_page=100" \
      --jq '.[] | select(.fork == false and .private == false) | .full_name' \
      >"$owned" 2>>"$err"; then
  owner_failed=1
fi

if [ "$owner_failed" -eq 0 ]; then
  while read -r repo; do
    [ -n "$repo" ] || continue
    if [ "$repo" = "$TREATY_REPO" ]; then
      continue
    fi

    # One listing call tells us which marker files exist, so a later read that
    # fails is a real error rather than an ordinary "file not present". An
    # empty repo 404s here and is correctly treated as having no markers.
    # Reads are given /dev/null so they cannot consume the repo list on stdin.
    root="$(gh api "repos/$repo/contents" --jq '.[].name' 2>/dev/null </dev/null || true)"

    for f in $MARKER_FILES; do
      printf '%s\n' "$root" | grep -qxF "$f" || continue

      if ! body="$(gh api "repos/$repo/contents/$f" \
                     -H 'Accept: application/vnd.github.raw' 2>>"$err" </dev/null)"; then
        echo "error: could not read $repo/$f (listed but unreadable)" >>"$err"
        owner_failed=1
        continue
      fi

      if printf '%s' "$body" | grep -qE "$MARKER_REGEX"; then
        echo "$repo" >>"$tmp"
        break
      fi
    done
  done <"$owned"
fi

# ---------------------------------------------------------------------------
# Source 2: code search (third-party discovery)
# ---------------------------------------------------------------------------
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
# caller to leave the displayed count unchanged. Code-search failure stays
# fatal even though the owner scan may have succeeded: a partial count would
# drop any third-party adopter and shrink the badge, which is exactly the
# regression this guard exists to prevent.
if [ "$owner_failed" -ne 0 ] || [ "$search_failed" -ne 0 ] \
   || grep -qiE 'rate limit|"status":"(403|429)"|secondary rate' "$err"; then
  echo "error: adopter lookup failed or was rate-limited; not reporting a count." >&2
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
  # Flag third-party repos: those are the ones found only via code search, so
  # they are the part of the total still subject to the index gap.
  printf '%s\n' "$adopters" | while read -r repo; do
    [ -n "$repo" ] || continue
    case "$repo" in
      "$OWNER"/*) printf '  %s\n' "$repo" ;;
      *)          printf '  %s (third party)\n' "$repo" ;;
    esac
  done
else
  echo "  (none found yet)"
fi
echo
echo "Total adopters: $count"
echo "(excludes the treaty repo itself and the pydigger crawler; $OWNER/* read directly,"
echo " third-party adopters via the GitHub code-search index, so that part is a floor)"

# Machine-readable line consumed by the weekly badge-updater Action.
echo "ADOPTER_COUNT=$count"
