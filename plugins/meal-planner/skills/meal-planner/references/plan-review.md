# Independent review — brief for the reviewer agent

The planner never grades its own work. Before a plan (or a plan edit, or a new recipe)
is shown to the user, launch a **fresh** agent with this file as its brief. It starts
cold, re-reads the files, runs the scripts itself and judges what the scripts can't.

## How to launch

Use the `Agent` tool (`subagent_type: general-purpose`), foreground, with a prompt like:

> You are the independent reviewer for the meal-planner skill. Read
> `<skill_dir>/references/plan-review.md` and follow it exactly.
> Repo: `<repo_root>`. Review target: **plan `<weekStart>`** (or: *recipes `<slug>…`*,
> or: *edit of `<weekStart>`, nights `<dates>`*). Do not modify any file.
> Reply with the verdict block only.

Then act on the verdict:
- **FAIL** → fix every blocking issue, re-run the gates (validators, `plan_report.py`),
  and launch a **new** reviewer (not the same one — it must start cold). Repeat.
- After **3 failed rounds**, stop and show the user the plan *with* the open issues and
  your proposed fixes. Never present a failing plan as done.
- **PASS** → present the plan; mention non-blocking notes in one line if useful.

## What the reviewer does

### 1. Run the mechanical gates (all must be clean)

From `<repo_root>`:

```bash
python3 scripts/validate_plan.py <weekStart>          # 0 errors
python3 scripts/plan_report.py <weekStart>            # exit 0
python3 scripts/validate_recipe.py <every slug in the plan>   # 0 errors
python3 scripts/build_indexes.py --check              # (after the planner rebuilt them)
python3 scripts/grocery_list.py <weekStart>           # read it: quantities sane?
```

Any error → **FAIL** (quote it).

### 2. Read the files and judge — each item is blocking unless marked *(note)*

Read the plan JSON, every recipe it references (resolve `mealSlug` via `data/meals.json`,
pinned `#versions`), `context/Preferences.md`, `context/Schedule.md`, `context/rules.yaml`.

**A. Plate coherence (every cooked night)**
- It is a real meal: main + vegetable + starch/legume, or a one-dish meal that truly
  contains all three. No plate is just a protein, just a salad, or two starches.
- Components belong together (cuisine and flavour): no hummus with pad thai, no two
  heavy sauces, no tzatziki *and* raita.
- Every dish the plan *mentions* (in `context[]`, prep tasks, notes) is a recipe in that
  night's `recipes[]`. `extras` are only things eaten as-is (fish, pita, lime wedges).
- Version pins make sense (`#high-protein` where the plain version misses the floor).

**B. Nutrition**
- Every night meets `dinner_targets` (the validator checks the numbers — you check they
  are *honest*): portions in recipes look like what the family actually eats; no protein
  side added only to pad the numbers (e.g. 300 g tofu as a garnish).
- Protein comes from varied, mostly plant sources across the week (not tofu 5 nights;
  legumes, eggs, dairy, tempeh, edamame in rotation). Meat/fish within the cap; fatty
  fish at least once when the cap allows *(note if missing)*.
- `plan_report.py`'s weekly average sits near `dinner_share` of each adult's day — flag
  if dinner is above ~45 % of daily kcal or below ~30 % of daily protein.

**C. Lunchbox chain (Sun–Thu dinners → Mon–Fri lunchboxes)**
- Each main packs (`packs` / `separate`), and the `separate` note is actionable.
- Nothing soggy, watery, rubbery, bony or messy for a 6-year-old and a toddler; nut-free;
  chili only on adult plates; no whole grapes / large round pieces for Léonie.
- Two lunchboxes in a row of the same thing *(note)*.

**D. Feasibility**
- Active time within `max_active_min` per night, or the extra time is moved to a dated
  prep task that actually exists.
- Prep tasks match the plan's own constraints (`context[]`: heat, no oven, stove only
  before X…), marinades start early enough, batch bases are scaled to every use.
- Fresh fish eaten within 2 days of purchase; Friday takeout; Saturday on the grill.
- Grocery list: no absurd quantities, no item bought twice under two names that could be
  one *(note)*, batch raw ingredients in `groceries` (not `extras`).

**E. Preferences & rules**
- Garlic / lamb / nuts-in-lunchbox, every dislike in `Preferences.md` (eggplant, bok
  choy, miso, seaweed, unlisted mushrooms, soba), vegan mayo, seasonal heroes from
  `Schedule.md`. Any user wish from this conversation is in the plan.

**F. Recipe review** (for new or edited recipes — also the target of a recipe-only review)
- Ingredients and quantities are realistic for the stated `serves`; nothing caloric left
  without a quantity; method steps match the ingredient list (nothing used but missing).
- Nutrition was written by `nutrients.py --write` (validator clean ⇒ it matches).
- `role` and `lunchbox.fit` are right for the dish (a dressed leafy salad is not `packs`).
- Restriction flags truthful; title follows the `Dish · key · key` style.

## Verdict format (reply with exactly this)

```
VERDICT: PASS | FAIL

Blocking:
1. <night / file> — <problem> → <concrete fix>
…

Notes:
- <non-blocking observation>
```

No blocking items ⇒ PASS. Be specific: name the night, the recipe slug, the number.
