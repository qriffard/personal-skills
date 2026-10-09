# Mode D — Edit an Existing Plan

Triggered when the user wants to modify the current week's plan without regenerating from scratch.

## Trigger phrasings

- "swap Wednesday's dinner"
- "we have leftovers, replan from Tuesday"
- "change Friday to fish"
- "drop tomorrow's dinner — we're going out"
- "guests Saturday — make it a meat night"
- "make Tuesday the high-protein version"

## Process

1. **Locate the active plan.** Find the most recent file in `<data_root>/plans/` using `index.json`. Confirm with user: `Editing week <weekStart>?`

2. **Identify the edit type** and update that slot in `meals[]`. A slot is one of: `takeout` · `mealSlug` · inline `recipes[]` · no-recipe night (`title` + `extras`). See `plan_conventions.md`.

   | Edit | Action |
   |---|---|
   | Swap the main | Replace `meals[i].recipes[0]` with the new slug. If the recipe doesn't exist, run Mode B inline first. Re-check the sides still fit the new main — a plate must stay main + veg + starch/legume. |
   | Swap/add a side | Edit the rest of `meals[i].recipes`. |
   | Use a saved meal | Set `meals[i].mealSlug` and clear `recipes` to `[]`. |
   | Pin a version | Append `#versionId` to a slug in `recipes[]` (e.g. `crispy-tofu#high-protein`). |
   | No-recipe night | Set `recipes: []`, add `title` + `extras[]` (items to buy). |
   | Drop a meal (eating out) | `takeout: true`, `recipes: []`, `mealSlug: null`, remove `extras`, `servings: 0`. |
   | Replan from day X | Re-pick all meals from `meals[i]` onward, respecting hard constraints + recent-meals. |

3. **Recompute affected sections:**
   - Update `meals[]` in the plan JSON.
   - Update `reusableBases` if the swap breaks a shared base.
   - Update `prep` if the swap changes what needs to be prepped.
   - Update `usage` on any newly-added recipe (and decrement the one removed if it was only there this week — optional, low stakes).

4. **Gates, then sync** (from `<repo_root>`):
   - Check the new plate first: `python3 scripts/plate_check.py --day <ddd> <refs…>` → exit 0.
   - Any new/edited recipe: `nutrients.py --write <slug>` + `validate_recipe.py <slug>` → 0 errors.
   - `build_indexes.py`, `validate_plan.py <weekStart>` → 0 errors, `plan_report.py <weekStart>` → exit 0. Off target → add the missing side **as a recipe** or pin a `#high-protein` version, never an `extras` item.
   - Launch a fresh reviewer agent (`references/plan-review.md`, target: *edit of `<weekStart>`, nights `<dates>`* — it also checks the lunchbox chain around them) → `VERDICT: PASS`.
   - Show the edited nights' rows from `plan_report.py`.
```bash
python3 scripts/validate_plan.py <weekStart>      # fix until clean
scripts/sync.sh "Edit week <weekStart>: <brief description>"
```

5. **Regenerate the grocery list** (it's computed, not stored) and offer to re-push:
```bash
python3 scripts/grocery_list.py <weekStart>
python3 scripts/push_to_reminders.py <weekStart> --clear   # --clear wipes the stale list
```

6. **Confirm:** `Updated week <weekStart>.`

## Hard rules during edits

- New picks must pass `rules.yaml` (exclusions, meat cap + one fish night, weekday rules) — `validate_plan.py` checks it. Lunchbox nights stay nut-free.
- New picks must respect `repeat_window_weeks` unless the user explicitly overrides. Compare by **slug**, ignoring any `#version` and resolving `mealSlug` to its component recipes.
- Dropping a meal never removes the lunchbox source for the next school day without surfacing it to the user first.
- A swapped-in Sun–Thu main must pack for the next day (`lunchbox.fit`); a swap that drops a side must replace it so the plate still meets `dinner_targets`.
