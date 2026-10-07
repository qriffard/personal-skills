# Mode A — Weekly Meal Plan

Generates a one-week plan (Sun → Sat) with recipes, batch bases, and prep tasks.

> **The flow has two phases. Do NOT write any recipe or JSON until the user has approved a rough plan.**
> Phase 1 = agree on a day-by-day skeleton (concepts only). Phase 2 = build the recipes and files.
> This mirrors how the planning conversation actually works: the user shapes the week first, then we commit it.

---

## Phase 1 — Rough plan (conversation, no files written)

### 1.1 Ask what's on hand, then wishes

Two short questions, in order. Wait for answers.

> What's in the fridge / freezer you want to use up this week?

> Any specific dishes, cuisines, or proteins you want — or anything to avoid?

On-hand items are **load-bearing**: they anchor specific nights and get **excluded from the grocery list** later. A named wish must appear in the plan.

### 1.2 Read context (in order)

1. `<context_root>/Family.md`
2. `<context_root>/Preferences.md` — hard constraints + taste dislikes
3. `<context_root>/Schedule.md` — week structure, hard rules, shopping cadence, seasonality
4. `<context_root>/Inspiration.md` — sources
4b. `<context_root>/rules.yaml` — the checkable rules (exclusions, caps, weekday rules)
5. `<data_root>/plans/` — last 4 plan files (resolve each slot's recipes, including `mealSlug` → `data/meals.json`) to avoid repeats
6. `<data_root>/recipes/index.json` — library with ratings · `<data_root>/meals.json` — composed meals

If any of files 1–4b is missing, **stop** and tell the user.

### 1.3 Check seasonality before proposing

Read the "Right now" block in `Schedule.md` and its `> _Updated: YYYY-MM_` marker. If it's stale (not current month or the month before), refresh from the web and overwrite it. **Out-of-season hero vegetables are a common miss** (e.g. asparagus in June) — surface 3–5 in-season hero ingredients and build around those.

### 1.4 Propose a rough day-by-day plan

Present a **table**, one line per night, concept-level only — no recipe files yet. Every night names **its full plate** — main **+ veg + starch/legume** — or is explicitly a one-dish meal that already contains all three:

| Day | Main | Veg | Starch / legume | ≈ kcal · P · fiber |
|---|---|---|---|---|
| Sun | Grilled chicken | Peach/burrata/tomato salad | Grilled bread *(farmers market)* | 620 · 42 · 5 |
| Mon | Tofu · fennel · orange · quinoa bowl *(on hand, one-dish)* | — | — | 490 · 24 · 7 |
| … | … | … | … | … |
| Fri | Takeout | | | |
| Sat | Plancha — … | … | … | … |

Estimate per-serving totals from library `nutrition` (or USDA for new ideas) and compare to `rules.yaml → dinner_min`. **Fix a night below the floor before showing the table** — don't leave it for the user to spot. Honor the hard rules (below) while drafting. Show your protein count (e.g. "2 meat/fish: Sun + Wed ✓"). Mark which nights use on-hand items.

### 1.5 Iterate until approved — this is the heart of the mode

Expect several rounds. The user will swap days, change proteins, reject ideas, and ask for options. Specifically:

- **When the user is undecided, offer 3–4 concrete options**, not one silent pick ("make some suggestions"). Lead with a recommendation.
- **When a new preference or constraint surfaces mid-conversation** (e.g. "Pauline hates eggplant", "she's fine with garlicky sausage"), **write it to the relevant context file immediately** (`Preferences.md` usually), confirm it, and apply it. Don't just hold it in the chat — it must persist for future weeks. See [[how-to-update-context]] below.
- **Proactively flag a hard-constraint risk** (e.g. garlic in linguiça/tzatziki) and offer to adapt — but accept the user's override if they say it's fine.
- A **composed dinner** (main + sides) is normal — keep it as one night with multiple components.
- Re-check the protein cap after every swap.

Only when the user signals the skeleton is good do you move to Phase 2.

### Hard rules to honor while drafting

These mirror `rules.yaml` (checked by `validate_plan.py`) plus the judgement-only rules from `Schedule.md`:

1. Active-time caps per night from `rules.yaml → max_active_min` (Mon ≤ 15 assembly-leaning, Tue–Thu ≤ 20).
2. Sunday lunch ≤ 5 min, assembly only (music lesson 12:30).
3. **Saturday dinner = gas grill** (`rules.yaml → weekday_rules.sat.technique_any`). **Friday = takeout.**
4. Sunday dinner sized for Monday-lunch leftovers (set `servings`).
5. Lunches come from the previous night (covered by `servings`, no separate lunchbox planning).
6. Fresh fish eaten within 2 days of purchase — front-load fish (Sun/Mon/Tue).
7. **Honor household dietary constraints** — `rules.yaml → exclude_if` plus `Preferences.md` nuance (lunchbox rules, dislikes). Meat/fish cap from `rules.yaml` unless the user relaxes it for this week (say so in `context[]`).

---

## Phase 2 — Build it (write files)

### 2.1 Resolve each night to recipes

For every night, decide the components and where each recipe comes from, in priority order:

1. Library recipe (`recipes/index.json`) rated 4–5, not cooked in last 4 weeks
2. Library recipe rated 3 or unrated, not cooked in last 4 weeks
3. New recipe from an `Inspiration.md` source
4. Original recipe (`source.type: "original"`)

**Exclude:** `rating.score: 0`, cooked within `repeat_window_weeks`, any recipe with a flag listed in `rules.yaml → exclude_if` (e.g. `restrictions.garlic: true`).

**Composed dinners → one recipe per component.** "Grilled chicken + saffron rice + zucchini + tzatziki" is **four** recipe files, not one. Split them so each is reusable and the grocery list aggregates correctly.

**Every component approved in Phase 1 becomes a recipe in the slot's `recipes[]`** — including plain sides (rice, a cucumber salad). Never park a side in `extras` or mention it only in `context[]`: the app renders `recipes[]` only, so it disappears from the plan (this is how Wed 2026-10-07 shipped as a lone chicken).

**Seasonal adaptation of a reused recipe:** if a library recipe's hero veg is out of season, swap it for an in-season one and update the recipe file before using it. A `seasons: ["spring"]` tag does not block summer use once adapted.

**No-recipe nights (improvised dishes).** A night can be a dish with no formal recipe — e.g. "grilled whole fish" you'll wing on the plancha. Do NOT leave the slot empty (the fish would vanish from the grocery list). Instead give the slot a `title` and an `extras[]` list of what to buy (absolute quantities), with `recipes: []`. The grocery script aggregates `extras` exactly like recipe ingredients. See `plan_conventions.md` → "No-recipe night example". Use this whenever the user describes a night by its protein/technique rather than a recipe.

**Reusable meals & version pinning.** If a night is a saved composed dinner, reference it with `mealSlug` (counts as one slot; protein from its hero recipe). To cook a specific variant of a recipe, pin it with `slug#versionId` (e.g. `crispy-tofu#high-protein`) — grocery and macros follow the pin. Default version if no `#`.

**Recently-cooked comparison.** When checking the last-4-weeks window, compare by **slug** — strip any `#version`, and resolve a `mealSlug` to its component recipe slugs (read `data/meals.json`).

### 2.2 Write any new recipe files

Follow `references/recipe_conventions.md` exactly. Key reminders from past misses:

- Structured `ingredients[]` and `method[]` — never markdown blobs.
- **No ★ or decorators in ingredient `name` fields** — it breaks grocery aggregation. Hero markers belong in plan `context[]`.
- `qty` is always a number; `null` for "to taste". Clean, canonical ingredient names (the grocery script normalises, but don't fight it).
- Compute `nutrition` per serving from USDA. Set all `restrictions` flags truthfully.
- Metric units only.
- Vegetable minimums: raw greens ≥ 120 g/adult, cooked veg ≥ 200 g/adult.

Write to `<data_root>/recipes/<slug>.json`, then run `python3 scripts/validate_recipe.py <slug>…` from `<repo_root>` and fix until clean. Don't touch `recipes/index.json` — `sync.sh` rebuilds it.

### 2.3 Save a reusable composed dinner as a Meal (optional)

If a composed dinner is one the family will want again, add it to `<data_root>/meals.json` (see `plan_conventions.md`) and reference it from the slot via `mealSlug`. A meal counts as **one** slot. Skip this for one-off combos — just list the components inline in the slot's `recipes[]`.

### 2.4 Batch bases + servings + prep

- **Reusable bases:** 2–3 per week (grain, sauce, roasted veg), scaled across every meal that uses them. Goal: weeknights are assembly + 1 fresh element.
- **Servings:** recipe `serves` + 2 adult portions for next-day lunch; Sunday extra for Monday's 2 adults + 2 kids; takeout `servings: 0`.
- **Prep:** dated `PrepGroup`s, kitchen tasks only — no shopping errands. Mark farmers-market pickups on Sunday.

### 2.5 Assemble the plan JSON

Write `<data_root>/plans/<weekStart>.json` per `plan_conventions.md`. Each slot is one of: `takeout` · `mealSlug` · inline `recipes[]` · no-recipe night. Put hero-ingredient notes and planning rationale in `context[]` (including any rule the user relaxed this week).

**Validate loop — before you show the user anything:** run `python3 scripts/validate_plan.py <weekStart>` from `<repo_root>`. Fix every error and re-run until it passes; **the user never sees a plan that fails.** For each warning, either fix it or tell the user why it stands (e.g. a repeat they asked for).

- *Unbalanced dinner* (`dinner_min`) → add the missing side as a recipe, or pin a high-protein version. Only set `override` if the user explicitly accepts a light night.
- Then **self-review the written JSON, not your memory of the plan.** Print one line per slot from the file — recipe titles, summed kcal · protein · fiber, active minutes — and check it against the approved skeleton: every component present, no side living only in `extras`/`context[]`, prep tasks don't contradict `context[]` (e.g. "no stove after 10 am" vs an evening simmer), each school-night dinner packs as a lunchbox. Show this table to the user as the final plan.

### 2.6 Update usage

For each recipe cooked this week, bump `usage.timesCooked` and set `usage.lastCooked` (`sync.sh` carries it into the index).

### 2.7 Sync

```bash
<repo_root>/scripts/sync.sh "Add week YYYY-MM-DD: <dishes>"
```
Ships the plan, recipes, rebuilt indexes and any `context/` edits. Report the one-line result.

### 2.8 Grocery list + Reminders

The shopping list is **computed, never stored** (run from `<repo_root>`):
```bash
python3 scripts/grocery_list.py <weekStart>        # review
python3 scripts/push_to_reminders.py <weekStart>   # send (add --clear to wipe stale)
```
**Remind the user to subtract on-hand items** (from 1.1) — the script can't know what's already in their fridge. Then offer to push to Reminders.

---

## how-to-update-context

When a preference surfaces in conversation that isn't in the context files:

- **Dislike / aversion** → add under the person's **Taste** list in `Preferences.md` (e.g. `- ❌ Eggplant — dislikes it; never use`).
- **Allow/override of a default** → note it where the default lives.
- **Schedule / cadence change** → `Schedule.md`.
- Confirm the edit in one line ("Added eggplant to Pauline's dislikes"), commit it with the plan, and apply it immediately to the current week.

---

## Quality checklist

- [ ] Asked on-hand inventory + wishes first
- [ ] Rough plan approved **before** any file was written
- [ ] Any newly-surfaced preference saved to a context file
- [ ] Seasonality fresh; out-of-season heroes swapped
- [ ] No recipe repeated from last 4 weeks; rating 0 excluded
- [ ] Household dietary constraints from `Preferences.md` applied (allergies, aversions, lunchbox rules)
- [ ] Mon–Fri ≤ 20 min · Sun lunch assembly · Fri takeout · Sat grill
- [ ] ≤ 2 meat/fish (unless user relaxed); meal counts as one slot
- [ ] Every night = main + veg + starch/legume (or a one-dish meal), estimated in Phase 1
- [ ] Composed dinners split into component recipes; reusable ones saved as Meals
- [ ] No dish only in `extras` or `context[]` — every component is in `recipes[]`
- [ ] Final plan shown as a per-slot table read back from the written JSON
- [ ] No ★ in ingredient names
- [ ] `validate_recipe.py` clean on new/edited recipes · `validate_plan.py` clean on the plan
- [ ] Batch bases scaled · servings sized for leftovers · prep dated, kitchen-only
- [ ] usage updated · published with `sync.sh`
- [ ] Grocery list generated; reminded user to subtract on-hand items
