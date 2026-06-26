# Groceries → Apple Reminders

The grocery list is **computed, never stored** in the plan. Two scripts in `<repo_root>/scripts/`:

```bash
python3 scripts/grocery_list.py <weekStart>                 # print the list
python3 scripts/push_to_reminders.py <weekStart> [--dry-run] [--clear]
```

`<weekStart>` defaults to the latest plan if omitted.

## How the list is built

`grocery_list.py` (and `push_to_reminders.py`, which imports it):

1. Reads `<data_root>/plans/<weekStart>.json` → `meals[]`.
2. Resolves each slot to recipe refs: `takeout` → none; `mealSlug` → the meal's recipes (`data/meals.json`); else inline `recipes[]`.
3. For each ref `slug` or `slug#versionId`: loads the recipe, **resolves the version** (default or pinned; deltas applied, removed items dropped), scales ingredients by `servings / version.serves`.
4. Adds the slot's `extras[]` (no-recipe items) at absolute quantity.
5. Normalises names, merges same ingredient + unit, drops on-hand / pantry staples, converts lemon juice → whole lemons, herb pieces → bunches, etc.

`push_to_reminders.py` then classifies each item by store (`tj` / `clement-st`) and category and sends it through the **"Add Tagged Reminder"** Shortcut into the "Grocery Shopping" list. `--clear` wipes incomplete items first; `--dry-run` prints without sending.

**Always remind the user to subtract on-hand items** — the script can't know what's already in their fridge.

## Shortcut setup

The "Add Tagged Reminder" Shortcut (one per item: `name` + comma-separated `tags`) is unchanged — see the archived click-by-click setup if it needs rebuilding.
