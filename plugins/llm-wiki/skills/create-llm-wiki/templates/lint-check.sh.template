#!/usr/bin/env bash
# SessionStart hook: nudge when a lint (health-check) pass is overdue.
# Counts `ingest` log entries since the last `lint` entry; if past the
# threshold it prints a notice, which Claude Code adds to the session context.
# A lint is a reasoning pass — this hook only DETECTS and REMINDS; Claude runs
# the actual pass per CLAUDE.md → Operations → Lint.
set -uo pipefail

cd "${CLAUDE_PROJECT_DIR:-$PWD}" || exit 0
[ -f log.md ] || exit 0

THRESHOLD=10

# Log entries look like:  ## [YYYY-MM-DD] ingest | ...   /   ## [YYYY-MM-DD] lint | ...
last_lint=$(grep -n '^## \[.*\] lint ' log.md | tail -1 | cut -d: -f1)
if [ -n "${last_lint:-}" ]; then
  ingests=$(tail -n +"$((last_lint + 1))" log.md | grep -c '^## \[.*\] ingest ')
else
  ingests=$(grep -c '^## \[.*\] ingest ' log.md)
fi

if [ "${ingests:-0}" -ge "$THRESHOLD" ]; then
  echo "⚠️ Lint due: ${ingests} ingests since the last health check. Run a lint pass (CLAUDE.md → Operations → Lint) before continuing, then log it as a 'lint' entry."
fi

exit 0
