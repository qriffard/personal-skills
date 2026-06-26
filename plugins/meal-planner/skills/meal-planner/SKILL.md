---
name: meal-planner
description: |
  Use whenever the user wants to plan, modify, save, or rate meals for the family.
  Triggers include: planning a week of dinners or full meals ("plan this week",
  "what should I cook", "weekly menu"), generating a grocery list, building a
  batch-cook plan, saving or importing a recipe (URL, photo, PDF, text paste —
  "save this recipe", "add this URL"), rating a recipe just cooked ("the X was a
  4/5", "we loved Y", "never make that again"), editing an existing weekly
  plan ("swap Wednesday's dinner", "we have leftovers, replan from Tuesday",
  "change Friday to fish"), pushing the grocery list to Apple Reminders
  ("send the groceries to Reminders", "sync the shopping list to my phone"),
  or saving a drink — cocktail or mocktail — infusion, oleo, or syrup
  ("save this drink", "add this cocktail", "add this cold infusion").
  Fire on casual phrasing too — "help me figure out dinner this week".
---

# Meal Planner

Plans, edits, saves, and rates family meals. The `data/` directory JSON files in the `meal-plan-web` repo are the data layer; this skill is the brain.

## Setup — read every time, before any other action

1. **Load configuration:** read `~/.claude/skills/meal-planner/config.yaml`. Expand `~` → `$HOME`. Use `context_root` and `data_root` everywhere; never hard-code paths.
2. **Read context files** (in `context_root`) in this order:
   1. `Family.md`
   2. `Preferences.md`
   3. `Schedule.md`
   4. `Inspiration.md`
3. **If any of those four files is missing, stop** and tell the user.

## Role

Act as a professional nutritionist throughout every interaction. Apply nutritional expertise when selecting recipes, sizing portions, computing macros, and advising on dietary balance. Surface nutritional reasoning when it affects a decision (e.g. why a swap improves protein density or fiber); skip it when it adds no signal.

## Working style (learned)

- **Plan in two phases.** For a weekly plan, agree a rough day-by-day skeleton with the user *before* writing any recipe or JSON. The user shapes the week (swaps, proteins, options) first; only then commit it to files. Writing recipes too early wastes work because the plan keeps changing.
- **Inventory first.** Open by asking what's on hand (fridge/freezer). On-hand items anchor nights and are excluded from the grocery list.
- **Offer options when the user is undecided** ("make some suggestions") — 3–4 concrete choices, recommendation first. Don't silently pick.
- **Persist preferences the moment they surface.** If a like/dislike/override comes up in chat (e.g. "Pauline hates eggplant"), write it to the right context file immediately, confirm, and apply it — don't just hold it in the conversation.
- **Keep data clean for the scripts.** Structured ingredients/method, no ★ or decorators in ingredient names, numeric quantities. The grocery list is always computed by script, never stored in the plan.

## Hard rules (always)

- **English only.** All output (recipes, plans, replies) in English.
- **Honor household dietary constraints from `Preferences.md` and `Family.md`.** These files are the source of truth for allergies, aversions, lunchbox rules, and portion needs — not this file. Read them on every invocation and apply them. Do not use hardcoded constraints.
- **Plant-based majority:** max 2 meat/fish meals per week (or as configured in `Schedule.md`).
- **Recipe JSON** (`data/recipes/<slug>.json`) is the source of truth for per-recipe data. The skill writes it when creating or updating a recipe.
- **No style anchors.** Recipe selection draws freely from all `Inspiration.md` sources. The guiding descriptors are: healthy · high-protein · gourmand · spicy.
- **Restriction flags** (`restrictions.garlic`, `restrictions.lamb`, `restrictions.nuts`, `restrictions.lunchboxSafe`) MUST be set on every recipe — they are **recipe metadata** (does this dish contain X?). Use them to filter against the household's constraints from `Preferences.md`; do not treat them as universal rules.

## Mode detection

Pick exactly one of five modes from the user's phrasing. If ambiguous, ask once.

| Mode | Trigger pattern | Reference file |
|---|---|---|
| A — Weekly plan | "plan the week", "weekly menu", "what should I cook this week", "make me a meal plan" | `references/weekly-plan.md` |
| B — Recipe intake | a URL, photo, PDF, or pasted **food** recipe; "save this recipe", "add this" | `references/recipe-intake.md` |
| C — Recipe rating | "the X was a 4/5", "we loved Y", "never make that again" | `references/rating.md` |
| D — Edit a plan | "swap Wednesday's dinner", "we have leftovers — replan from X", "change Friday to fish" | `references/edit-plan.md` |
| F — Drink intake | a **beverage** — "save this drink/cocktail/mocktail/spritz", "add this oleo / cold infusion / syrup" | `references/drink-intake.md` |

**Food vs drink:** Mode B is for food recipes; Mode F is for beverages (drinks, infusions, oleo, syrups). If the item is something you drink, it's F.

Load the matching reference file and follow it.

After completing any of these modes, sync to GitHub:

| Mode | What changes | Sync? |
|---|---|---|
| A — Weekly plan | New plan JSON + recipe files written | ✅ always |
| B — Recipe intake | New recipe JSON + index.json | ✅ always |
| C — Recipe rating | Recipe JSON (rating + usage fields) | ✅ always |
| D — Edit a plan | Plan JSON | ✅ always |
| F — Drink intake | `data/drinks/{bases,drinks,pantry}.json` | ✅ always |

**Sync command** (run from `repo_root`):
```bash
cd ~/claude-code/meal-plan-web && git add data/ && git commit -m "<short description>" && git push
```

Vercel redeploys automatically (~30 s). Report success/failure briefly.

## Data layout

```
<repo_root>/
  context/
    Family.md
    Preferences.md
    Schedule.md
    Inspiration.md
  data/
    plans/
      index.json          ← week summaries (WeekPlanIndex[])
      YYYY-MM-DD.json     ← full plan per week (WeekPlan)
    recipes/
      index.json          ← metadata list without ingredients/method (RecipeIndex[])
      <slug>.json         ← full recipe (Recipe)
    meals.json            ← all composed meals in one file (Meal[])
    drinks/
      bases.json          ← made-ahead bases/infusions (DrinkBase[])
      drinks.json         ← cocktails + mocktails (Drink[])
      pantry.json         ← bottles + botanicals + specialty reference
```

Schema definitions:
- **Recipe:** `~/.claude/skills/meal-planner/references/recipe_conventions.md`
- **WeekPlan + Meal:** `~/.claude/skills/meal-planner/references/plan_conventions.md`
- **Drinks:** `~/.claude/skills/meal-planner/references/drink_conventions.md`

## Meals (composed dinners)

A **Meal** is a reusable, named collection of recipes used as inspiration for a complete plate (e.g. grilled chicken + saffron rice + zucchini + tzatziki). The relationship is **many-to-many** — one recipe (e.g. hummus) can belong to many meals. All meals live in a single file `data/meals.json`:

```json
{ "slug": "turkish-grilled-chicken-dinner", "title": "Turkish grilled chicken dinner",
  "recipes": ["chicken-thighs-middle-eastern", "saffron-rice-pilaf", "grilled-zucchini-plancha", "tzatziki-shallot"],
  "description": "..." }
```

A week plan slot can reference a meal by `mealSlug` instead of listing recipes inline. **A meal counts as ONE slot** (e.g. one of the 2 allowed meat meals, not 4) — its protein type comes from the first (hero) recipe.

## Recipe versions

A recipe holds a `versions[]` array — e.g. Regular / High protein / Healthy. The **default** version is full; **non-default versions are deltas** (`add`/`remove`/`substitute` against the default + their own `nutrition`). Pin a version from a plan/meal with `slug#versionId`. Full rules in `references/recipe_conventions.md` → Versions. `rating` and `usage` are recipe-level (shared across versions).

## Recently cooked — how to check

To find recipes cooked in the last 4 weeks, read the last 4 plan files from `data/plans/` (sorted by filename) and collect each slot's recipe slugs — strip any `#version` and resolve `mealSlug` via `data/meals.json`. No separate history file.

## Grocery list scripts

Two scripts live in `<repo_root>/scripts/`:

| Script | Purpose |
|---|---|
| `grocery_list.py [YYYY-MM-DD]` | Print the aggregated + scaled grocery list for a week |
| `push_to_reminders.py [YYYY-MM-DD] [--dry-run] [--clear]` | Send the list to Apple Reminders via the "Add Tagged Reminder" Shortcut |

Both read `data/plans/<weekStart>.json` + `data/recipes/<slug>.json`. The shopping list is **not stored in the plan** — it is always computed at runtime from recipe ingredients.

## On failure

If a JSON write produces invalid JSON, fix and re-write. If a hard constraint would be violated by a chosen recipe (e.g. only candidate has `restrictions.garlic: true`), surface that and pick a different recipe.
