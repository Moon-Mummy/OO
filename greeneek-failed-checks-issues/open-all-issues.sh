#!/usr/bin/env bash
set -euo pipefail

# Opens all 8 audited failed-check GitHub Issues on Mostafa-Taher-git/Greeneek.
# Usage:
#   bash greeneek-failed-checks-issues/open-all-issues.sh --dry-run
#   bash greeneek-failed-checks-issues/open-all-issues.sh

REPO="Mostafa-Taher-git/Greeneek"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PAYLOADS="$SCRIPT_DIR/issues-payloads.json"
DRY_RUN=0

if [[ "${1:-}" == "--dry-run" ]]; then
  DRY_RUN=1
fi

command -v gh >/dev/null 2>&1 || { echo "Error: gh CLI is required (https://cli.github.com/)." >&2; exit 1; }
command -v jq >/dev/null 2>&1 || { echo "Error: jq is required." >&2; exit 1; }

if [[ "$DRY_RUN" -eq 0 ]]; then
  gh auth status >/dev/null
fi

existing_titles="$(gh api --paginate "repos/$REPO/issues?state=open&per_page=100" --jq '.[].title' 2>/dev/null || true)"
count="$(jq 'length' "$PAYLOADS")"

echo "Preparing to process $count issue(s) for $REPO (dry_run=$DRY_RUN)..."

for (( i=0; i<count; i++ )); do
  title="$(jq -r ".[$i].title" "$PAYLOADS")"
  labels="$(jq -c ".[$i].labels" "$PAYLOADS")"
  body_len="$(jq -r ".[$i].body | length" "$PAYLOADS")"

  if grep -Fqx "$title" <<<"$existing_titles"; then
    echo "[$((i+1))/$count] SKIP (already open): $title"
    continue
  fi

  if [[ "$DRY_RUN" -eq 1 ]]; then
    echo "[$((i+1))/$count] DRY-RUN would create: $title (labels=$labels, body=${body_len} chars)"
  else
    url="$(jq -c ".[$i]" "$PAYLOADS" | gh api "repos/$REPO/issues" --method POST --input - --jq '.html_url')"
    echo "[$((i+1))/$count] CREATED: $url — $title"
    sleep 1
  fi
done

echo "Done."
