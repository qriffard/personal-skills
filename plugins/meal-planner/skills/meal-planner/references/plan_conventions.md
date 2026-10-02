# WeekPlan Schema

Source of truth: `meal-plan-web/types/plan.ts`

Plan files live at `<data_root>/plans/<weekStart>.json` where `weekStart` is the Sunday date.  
Index file: `<data_root>/plans/index.json` — array of plan objects **without** `meals`, `reusableBases` and `prep`.

---

## JSON schema

```json
{
  "weekStart": "2026-06-01",
  "season": "spring",
  "cuisineRotation": "mediterranean",
  "context": [
    "Late spring: asparagus, snap peas, new potatoes in season",
    "Salmon front-loaded (Sunday buy → Tuesday eat) — day-2 freshness rule respected",
    "Weeknight cap: Mon–Thu all ≤ 20 min active"
  ],
  "generatedAt": "2026-05-28T10:00:00Z",

  "meals": [
    { "date": "2026-06-01", "recipes": ["green-lentil-dhal-spinach-poached-egg"], "servings": 6, "takeout": false },
    { "date": "2026-06-02", "recipes": ["crispy-chicken-thighs-asparagus-lemon-spring-onion", "green-salad"], "servings": 5, "takeout": false },
    { "date": "2026-06-06", "recipes": [], "servings": 0, "takeout": true }
  ],

  "reusableBases": [
    { "name": "Cooked lentils", "qty": 400, "unit": "g", "usedIn": ["green-lentil-dhal-spinach-poached-egg"] },
    { "name": "Lemon-herb dressing", "qty": 200, "unit": "ml", "usedIn": ["king-salmon-snap-peas-new-potatoes-lemon", "crispy-tofu-snap-peas-feta-herbs"] }
  ],

  "prep": [
    {
      "date": "2026-06-01",
      "label": "Sunday batch",
      "tasks": [
        { "text": "Hard-boil **6 eggs** — reserve for Thu/Fri lunchboxes.", "durationMin": 12 },
        { "text": "Make double batch lemon-herb dressing — use half Tue (salmon), half Wed (tofu).", "durationMin": 10 }
      ]
    },
    {
      "date": "2026-06-03",
      "label": "Tuesday evening",
      "tasks": [
        { "text": "Boil **700 g new potatoes** for tonight's salmon.", "durationMin": 20 }
      ]
    }
  ]
}
```

---

## Field rules

### `meals`

| Field | Notes |
|---|---|
| `date` | `YYYY-MM-DD`. One entry per dinner slot (Sun–Sat). Friday is always takeout. |
| `recipes` | Ordered array of recipe slugs (inline). First entry is the main; rest are sides. `[]` when `takeout` or when using `mealSlug`. A slug may pin a recipe version as `slug#versionId` (e.g. `tofu-snap-peas-sesame-ginger#high-protein`); no `#` = default version. |
| `mealSlug` | Optional. References a composed meal in `data/meals.json`. When set, its `recipes` provide the components — leave `recipes: []`. Counts as ONE slot; protein from the meal's hero recipe. |
| `title` | Optional. Label for a **no-recipe night** (e.g. `"Grilled whole fish"`) so the card has a name when there's no main recipe. |
| `extras` | Optional `Ingredient[]` — ad-hoc grocery items not tied to a recipe (the fish itself, a side salad, bread). **Absolute quantities** for the night (NOT scaled by `servings`). They flow into the computed grocery list like recipe ingredients. |
| `servings` | Total servings to make — applies to recipe components. `0` when `takeout: true`. |
| `takeout` | `true` → no recipes, no prep. |

A slot is exactly one of: `takeout: true` · `mealSlug: "..."` · inline `recipes: [...]` · a **no-recipe night** (`title` + `extras`, `recipes: []`). Any non-takeout slot may also add `extras` on top of its recipes (e.g. a recipe night plus "a baguette").

**No-recipe night example** — a grilled fish you'll improvise, but still need to shop for:
```json
{
  "date": "2026-06-20",
  "title": "Grilled whole fish",
  "recipes": [],
  "extras": [
    { "name": "Whole sea bream", "qty": 1200, "unit": "g", "note": "ask fishmonger to gut" },
    { "name": "Lemon", "qty": 2, "unit": "piece", "note": null },
    { "name": "Mixed salad greens", "qty": 200, "unit": "g", "note": null }
  ],
  "servings": 5,
  "takeout": false
}
```
`extras` items use the same shape as recipe ingredients (`name`, `qty`, `unit`, `note`) and the same clean-name rule (no ★, numeric `qty`).

### Composed meals (`data/meals.json`)

A single file holding all reusable named dinners. Many-to-many with recipes — one recipe can appear in many meals.

```json
[
  { "slug": "turkish-grilled-chicken-dinner",
    "title": "Turkish grilled chicken dinner",
    "recipes": ["chicken-thighs-middle-eastern", "saffron-rice-pilaf", "grilled-zucchini-plancha", "tzatziki-shallot"],
    "description": "Plancha chicken thighs with saffron rice, zucchini and garlic-free tzatziki." }
]
```

When the plan generator uses a meal, count it as **one** meat/fish/plant meal based on the hero (first) recipe — not one per component.

### `reusableBases`

- `usedIn` lists the slugs of every recipe that consumes this base.
- `qty` and `unit` reflect the **total batch** scaled for all meals that use it.

### `prep`

- `date` is when the task should be done — not a label string like `"Sunday May 31 morning"`.
- `label` is a human-readable group name. Use `null` for ungrouped tasks.
- `text` is markdown. Bold key quantities and timings.
- `durationMin` is the active or passive time for the task. Use `null` if instantaneous.
- Prep tasks are **kitchen tasks only** — no shopping errands. Shopping is computed separately by script from recipe ingredients.

### Shopping

The shopping list is **not stored in the plan**. It is computed at runtime by a script that:
1. Reads `meals[]` from the plan.
2. Loads each recipe's `ingredients[]`.
3. Aggregates quantities across all recipes for the week.
4. Groups by section and routes by store.
