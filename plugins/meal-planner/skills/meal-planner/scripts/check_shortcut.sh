#!/bin/bash
# Check whether the "Add Tagged Reminder" Shortcut is installed.
# Exit 0 = installed; exit 2 = missing (caller should run the setup walkthrough);
# exit 1 = something else broke (no shortcuts CLI, etc.).
set -euo pipefail

if ! command -v shortcuts >/dev/null 2>&1; then
  echo "shortcuts CLI not found — this script requires macOS Sonoma+." >&2
  exit 1
fi

if shortcuts list | grep -Fxq "Add Tagged Reminder"; then
  echo "OK — 'Add Tagged Reminder' is installed."
  exit 0
fi

cat <<'EOF' >&2
MISSING — 'Add Tagged Reminder' Shortcut is not installed.

This Shortcut is required for Mode E (push groceries to Reminders with
real tag pills). One-time setup, ~2 minutes.

Open the Shortcuts app and create a new shortcut named exactly:

    Add Tagged Reminder

with three actions:

  1. Get Dictionary Value — Key: "name",  In: Shortcut Input
  2. Get Dictionary Value — Key: "tags",  In: Shortcut Input
  3. Add New Reminder
       Title: <Dictionary Value from action 1>
       List:  Grocery Shopping
       Tags (under "Show More"):
              <Dictionary Value from action 2>

Save with cmd+S. Then verify with:

    osascript -e 'tell application "Shortcuts Events" to run shortcut "Add Tagged Reminder" with input "{\"name\":\"Setup test\",\"tags\":\"setup-test,verify\"}"'

A new "Setup test" reminder should appear in the "Grocery Shopping" list
in Reminders.app, with two tag pills (#setup-test and #verify). Delete
that reminder when verified.

Full walkthrough in:
    ~/.claude/skills/meal-planner/references/groceries-to-reminders.md
EOF

exit 2
