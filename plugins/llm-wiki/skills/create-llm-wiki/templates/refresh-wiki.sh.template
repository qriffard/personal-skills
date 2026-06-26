#!/usr/bin/env bash
# SessionStart: pull the latest wiki from the remote BEFORE you start editing, so
# work from another machine (e.g. your VDI) doesn't diverge. Conflict-safe: only
# pulls when the working tree is clean, and on trouble it warns without touching
# your edits.
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-$PWD}" || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0
git remote get-url origin >/dev/null 2>&1 || exit 0

# Don't auto-rebase over uncommitted work — let the next sync commit it first.
if ! git diff --quiet || ! git diff --cached --quiet; then
  echo "wiki: uncommitted local changes — skipped startup pull. They'll commit on the next sync; pull after that." >&2
  exit 0
fi

if ! git pull --rebase -q 2>/dev/null; then
  git rebase --abort 2>/dev/null || true
  echo "wiki: couldn't pull latest from the remote (conflict or network). Resolve with 'git pull --rebase' before editing." >&2
fi
exit 0
