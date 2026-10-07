# Mode A — Weekly Meal Plan

Generates a one-week plan (Sun → Sat) with recipes, batch bases, and prep tasks.

> **The flow has two phases. Do NOT write any recipe or JSON until the user has approved a rough plan.**
> Phase 1 = agree on a day-by-day skeleton (concepts only). Phase 2 = build the recipes and files.
> This mirrors how the planning conversation actually works: the user shapes the week first, then we commit it.

## Gates — the step is not done until its check passes

Every step below ends with a **gate**: a command whose output must be clean (or a check
you must state). Never move to the next step, and never show the user a result, with a
gate failing. Fix and re-run; the checks are cheap.

| Step | Gate |
|---|---|
| 1.4 Skeleton | `plate_check.py --day <ddd> <refs…>` passes for every night built from library recipes; new-recipe nights carry an estimate you'll confirm in 2.2 |
| 2.2 Each new / edited recipe | `nutrients.py --write <slug>` then `validate_recipe.py <slug>` → 0 errors |
| 2.5 Plan JSON | `validate_plan.py <weekStart>` → 0 errors; `plan_report.py <weekStart>` → exit 0 |
| 2.6 Independent review | a fresh reviewer agent returns `VERDICT: PASS` (`references/plan-review.md`) |
| 2.7 Publish | `sync.sh` succeeds (it re-validates) |

The user sees the plan only after 2.6 passes, as the `plan_report.py` table.

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

Present a **table**, one line per night, concept-level only — no recipe files yet. Every night names **its full plate** — main **+ veg + starch/legume** — or is explicitly a one-dish meal that already contains all three. **Protein first:** pick the plant main's `#high-protein` version or add a protein side (`tofu-bites-soy-ginger`, `tempeh-crumble-smoky`, `edamame-cucumber-herb-salad`, `lemony-white-bean-salad`, `skyr-herb-sauce`, `edamame-lime-salt`, …) before reaching for meat:

| Day | Main | Veg | Starch / legume | ≈ kcal · P · fiber |
|---|---|---|---|---|
| Sun | Grilled chicken | Peach/burrata/tomato salad | Grilled bread *(farmers market)* | 620 · 42 · 5 |
| Mon | Tofu · fennel · orange · quinoa bowl *(on hand, one-dish)* | — | — | 490 · 24 · 7 |
| … | … | … | … | … |
| Fri | Takeout | | | |
| Sat | Plancha — … | … | … | … |

**Gate — check every night's plate with the script, not by mental arithmetic** (from `<repo_root>`):

```bash
python3 scripts/plate_check.py --day mon red-lentil-dal#high-protein
python3 scripts/plate_check.py --day wed bbq-chicken-thai#lean edamame-cucumber-herb-salad jasmine-rice#brown-light
```

It sums per-serving nutrition over the plate, checks `rules.yaml → dinner_targets`
(kcal range, protein, protein share, fiber), checks the next-day lunchbox fit for Sun–Thu,
and lists higher-protein versions. **Every library night must exit 0 before you show the
table.** For a night that needs a recipe that doesn't exist yet, write an estimate from
similar library recipes and mark it *(estimate — confirmed in Phase 2)*. Put the numbers in
the table's last column. Honor the hard rules (below) while drafting. Show your protein count (e.g. "2 meat/fish: Sun + Wed ✓"). Mark which nights use on-hand items.

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
5. Lunches come from the previous night (covered by `servings`). **A Sun–Thu dinner's main must pack** (`lunchbox.fit` = `packs`/`separate`, see `rules.yaml → lunchbox_dinners`) — no tostadas, dressed leafy salads, scrambled eggs or bony fish the night before a school day.
5b. **Dinner targets** (`rules.yaml → dinner_targets`): per serving, whole plate incl. extras — kcal range, protein floor and share, fiber floor. Derived from both adults' daily targets in `Preferences.md`.
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
- **Nutrition is computed, never typed:** after writing the file run `python3 scripts/nutrients.py --write <slug>` (also fills delta versions). If it reports an unmatched ingredient, add that ingredient to `TABLE` in `scripts/nutrients.py` (per-100 g USDA values + unit weights; `sync.sh` commits the table) and re-run. Every caloric ingredient needs a `qty`.
- Set `role` and `lunchbox` (`fit` + `note`) — how it travels as next-day leftovers. Set all `restrictions` flags truthfully.
- If the plain version misses the protein floor on its plate, add a `high-protein` delta version (more tofu/eggs/legumes/skyr, less oil/starch) and pin it.
- Metric units only.
- Vegetable minimums: raw greens ≥ 120 g/adult, cooked veg ≥ 200 g/adult.

Write to `<data_root>/recipes/<slug>.json`, then **gate** (from `<repo_root>`):

```bash
python3 scripts/nutrients.py --write <slug>…
python3 scripts/validate_recipe.py <slug>…        # 0 errors
```

Then re-run `plate_check.py` for the night(s) that use it — an estimate from Phase 1 is
replaced by the real number here; if the night now misses a target, fix it before going on.
Don't touch `recipes/index.json` — `sync.sh` rebuilds it.

### 2.3 Save a reusable composed dinner as a Meal (optional)

If a composed dinner is one the family will want again, add it to `<data_root>/meals.json` (see `plan_conventions.md`) and reference it from the slot via `mealSlug`. A meal counts as **one** slot. Skip this for one-off combos — just list the components inline in the slot's `recipes[]`.

### 2.4 Batch bases + servings + prep

- **Reusable bases:** 2–3 per week (grain, sauce, roasted veg), scaled across every meal that uses them. Goal: weeknights are assembly + 1 fresh element.
- **Servings:** recipe `serves` + 2 adult portions for next-day lunch; Sunday extra for Monday's 2 adults + 2 kids; takeout `servings: 0`.
- **Prep:** dated `PrepGroup`s, kitchen tasks only — no shopping errands. Mark farmers-market pickups on Sunday.

### 2.5 Assemble the plan JSON

Write `<data_root>/plans/<weekStart>.json` per `plan_conventions.md`. Each slot is one of: `takeout` · `mealSlug` · inline `recipes[]` · no-recipe night. Put hero-ingredient notes and planning rationale in `context[]` (including any rule the user relaxed this week). Slot `extras` are only things **eaten at that dinner** (they count in its nutrition); raw ingredients for batch bases, Sunday lunch and lunchbox snacks go in the plan's top-level `groceries`.

**Gate — before you show the user anything** (from `<repo_root>`):

```bash
python3 scripts/build_indexes.py
python3 scripts/validate_plan.py <weekStart>     # 0 errors
python3 scripts/plan_report.py <weekStart>       # exit 0 — read it
```

Fix every error and re-run until clean; **the user never sees a plan that fails.**

- *Off nutrition target* → add the missing side **as a recipe**, pin a `#high-protein` / `#lean` version, or trim the starch/oil. `override` only if the user explicitly accepts it for that night.
- *Lunchbox doesn't pack* → move that main to Fri/Sat, or pick another main.
- Warnings: fix, or say why it stands (e.g. a repeat they asked for). Active time over the cap → move the work into a dated prep task.
- Read `plan_report.py` critically against the approved skeleton: every component present, weekly average near `dinner_share` of each adult's day, the lunchbox column all packable, prep consistent with `context[]`.

### 2.6 Independent review

Launch a **fresh reviewer agent** with `references/plan-review.md` (how-to-launch is in
that file). It re-reads the files, re-runs the scripts and judges plate coherence,
nutrition honesty, the lunchbox chain, feasibility and preferences. **FAIL → fix → new
reviewer**, until `VERDICT: PASS` (after 3 failed rounds, show the user the open issues
instead of pretending it's done).

**Present the plan** as the `plan_report.py` table (+ the prep and the reviewer's
non-blocking notes in a line). That table is read from the files — it is exactly what the
app and the grocery list will use.

### 2.7 Update usage

For each recipe cooked this week, bump `usage.timesCooked` and set `usage.lastCooked` (`sync.sh` carries it into the index).

### 2.8 Sync

```bash
<repo_root>/scripts/sync.sh "Add week YYYY-MM-DD: <dishes>"
```
Ships the plan, recipes, rebuilt indexes and any `context/` edits. Report the one-line result.

### 2.9 Grocery list + Reminders

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
- [ ] Every night = main + veg + starch/legume (or a one-dish meal); `plate_check.py` passed in Phase 1
- [ ] Protein from plant sources first (`#high-protein` versions, protein sides); meat/fish ≤ cap
- [ ] Sun–Thu mains pack for the next day's lunchbox
- [ ] Composed dinners split into component recipes; reusable ones saved as Meals
- [ ] No dish only in `extras` or `context[]` — every component is in `recipes[]`
- [ ] Final plan shown as the `plan_report.py` table
- [ ] No ★ in ingredient names
- [ ] New/edited recipes: `nutrients.py --write` + `validate_recipe.py` clean
- [ ] `validate_plan.py` + `plan_report.py` clean · reviewer agent `VERDICT: PASS`
- [ ] Batch bases scaled · servings sized for leftovers · prep dated, kitchen-only
- [ ] usage updated · published with `sync.sh`
- [ ] Grocery list generated; reminded user to subtract on-hand items
