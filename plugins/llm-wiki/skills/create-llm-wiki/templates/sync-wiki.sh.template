#!/usr/bin/env bash
# Auto-sync this LLM Wiki: commit local changes, pull --rebase, push.
# Phase-aware (mirrors the config repo's cloud-sync), so it stays in sync across
# machines (laptop + VDI) without pulling/pushing on every single turn:
#   stop        (Stop hook, fires every turn) — sync only when something changed;
#               when the tree is clean, skip the network entirely.
#   end / <none> (SessionEnd, and the use-llm-wiki router) — always reconcile and
#               push; also catches a commit a previous push failed to deliver.
# Safe anytime: no-op when appropriate; never fails the session; on a real
# conflict it stops and tells you rather than clobbering.
set -uo pipefail
PHASE="${1:-manual}"

cd "${CLAUDE_PROJECT_DIR:-$PWD}" || exit 0
git rev-parse --git-dir >/dev/null 2>&1 || exit 0

# Stage + commit any local changes.
git add -A
if git diff --cached --quiet; then
  # Nothing to commit. On the per-turn 'stop' phase, skip the network so we don't
  # pull/push on every response. 'end'/default still reconcile (catch unpushed work).
  [ "$PHASE" = "stop" ] && exit 0
else
  git commit -q -m "wiki sync: $(date '+%Y-%m-%d %H:%M:%S')" || exit 0
fi

# No remote configured? The local commit is enough.
git remote get-url origin >/dev/null 2>&1 || exit 0

# Pull remote changes (from another machine) and replay ours on top.
if ! git pull --rebase -q 2>/dev/null; then
  git rebase --abort 2>/dev/null || true
  echo "wiki sync: could not reconcile with the remote (diverging edits or network). Your work is COMMITTED but NOT pushed. Run 'git pull --rebase' in $(pwd), resolve conflicts, then push." >&2
  exit 0
fi

git push -q || echo "wiki sync: push failed; committed locally, will retry next sync" >&2
exit 0
