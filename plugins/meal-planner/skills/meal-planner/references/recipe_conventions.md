# Recipe Schema

Source of truth: `meal-plan-web/types/recipe.ts`

Recipe files live at `<data_root>/recipes/<slug>.json`.  
The slug is the filename without `.json` — it is **not** stored inside the file.

Index file: `<data_root>/recipes/index.json` — array of recipe objects **without** `ingredients` and `method`.

---

## JSON schema

```json
{
  "title": "Crispy tofu · snap peas · feta · herbs",
  "role": "main",

  "classification": {
    "proteinType": "plant-based",
    "seasons": ["spring", "summer"],
    "cuisine": ["mediterranean"],
    "technique": ["one-pan"],
    "dietary": ["gluten-free"]
  },

  "sources": [
    { "type": "original", "author": null, "url": null, "book": null, "page": null }
  ],

  "activeTimeMin": 20,
  "totalTimeMin": 25,
  "serves": 4,
  "complexity": "beginner",

  "restrictions": {
    "garlic": false,
    "lamb": false,
    "nuts": false,
    "lunchboxSafe": true
  },

  "nutrition": {
    "kcal": 420,
    "protein": 22,
    "carbs": 18,
    "fat": 28,
    "fiber": 5
  },

  "ingredients": [
    {
      "label": null,
      "items": [
        { "name": "Firm tofu", "qty": 600, "unit": "g", "note": "pressed 30 min" },
        { "name": "Snap peas", "qty": 350, "unit": "g", "note": null },
        { "name": "Feta", "qty": 120, "unit": "g", "note": "crumbled" }
      ]
    },
    {
      "label": "Dressing",
      "items": [
        { "name": "Lemon juice", "qty": 2, "unit": "tbsp", "note": null },
        { "name": "Olive oil", "qty": 3, "unit": "tbsp", "note": null }
      ]
    }
  ],

  "method": [
    {
      "label": null,
      "steps": [
        { "text": "Press tofu under a heavy pan for **30 min**, then cut into 2 cm cubes.", "durationMin": 30 },
        { "text": "Heat oil in a non-stick pan over high heat. Fry tofu until golden on all sides.", "durationMin": 10 }
      ]
    },
    {
      "label": "Finish",
      "steps": [
        { "text": "Add snap peas, toss 2 min. Off heat, add dressing and feta.", "durationMin": 2 }
      ]
    }
  ],

  "rating": {
    "score": null,
    "notes": "",
    "date": null
  },

  "usage": {
    "timesCooked": 0,
    "lastCooked": null
  },

  "createdBy": { "kind": "ai" }
}
```

---

## Versions

A recipe holds a `versions[]` array (≥1, exactly one `default: true`). Shared across versions (top level): `title`, `role`, `classification`, `sources`, `complexity`, `restrictions`, `rating`, `usage`.

**The default version is full** — it carries `serves`, `activeTimeMin`, `totalTimeMin`, `nutrition`, `ingredients[]`, `method[]`.

**Non-default versions are DELTAS** against the default — author only what changes:

```json
"versions": [
  { "id": "regular", "label": "Regular", "default": true,
    "serves": 4, "activeTimeMin": 15, "totalTimeMin": 15,
    "nutrition": { "kcal": 380, "protein": 22, "carbs": 38, "fat": 14, "fiber": 4 },
    "ingredients": [ ... ], "method": [ ... ] },

  { "id": "high-protein", "label": "High protein",
    "nutrition": { "kcal": 450, "protein": 34, "carbs": 36, "fat": 18, "fiber": 6 },
    "changes": [
      { "op": "substitute", "name": "Extra-firm tofu",
        "item": { "name": "Extra-firm tofu", "qty": 800, "unit": "g", "note": "..." } },
      { "op": "add",
        "item": { "name": "Frozen shelled edamame", "qty": 200, "unit": "g", "note": "thawed" } },
      { "op": "remove", "name": "Neutral oil" }
    ],
    "methodNotes": [ "Add the **edamame** with the snap peas." ] }
]
```

**Delta version rules:**
- `changes[]` ops: `add` (needs `item`, optional `group` label), `remove` (needs `name`), `substitute` (needs `name` to match + replacement `item`). Matching is by ingredient `name`, case-insensitive.
- `nutrition` is **required** on a delta version — macros can't be reliably recomputed from a delta. Enter the version's per-serving macros.
- `methodNotes[]` (markdown) capture method tweaks — shown as a callout above the shared method. The base `method` is reused; don't repeat it.
- `serves`/`activeTimeMin`/`totalTimeMin` are optional overrides; omit to inherit the default's.
- The app resolves the delta → effective ingredients and shows the diff (added / removed / substituted) to educate. The grocery list and scaling use the resolved list (removed items are not bought).

**Pinning a version** from a plan/meal: write the recipe reference as `slug#versionId` (e.g. `tofu-snap-peas-sesame-ginger#high-protein`). No `#` → default. Grocery, macros and the recipe link all follow the pin.

## Field rules

### `role` (optional)

The role the recipe plays on a plate — drives its label inside a composed meal. One of:
`main` · `side` · `salad` · `base` (grain/starch) · `sauce` · `dressing` · `condiment` · `dip` · `bread` · `drink`.

Set it whenever a recipe is naturally a component (a dressing, a sauce, a dip, a side). Standalone mains can leave it unset — a meal card falls back to positional **Main** (first recipe) / **Side** (the rest). The role is intrinsic to the recipe (a vinaigrette is always a dressing), reused across every meal that includes it.

### `classification`

| Field | Type | Notes |
|---|---|---|
| `proteinType` | `"meat" \| "fish" \| "plant-based"` | Required |
| `seasons` | array | At least one. A recipe can span multiple seasons. |
| `cuisine` | array | Free string. Examples: `mediterranean`, `japanese`, `french`, `middle-eastern`, `southeast-asian`, `mexican` |
| `technique` | array | Examples: `grill`, `plancha`, `batch-cook`, `one-pan`, `bbq` |
| `dietary` | array | Examples: `dairy-free`, `gluten-free`, `vegan` |

### `sources`

An **array** — a recipe consolidated from several places carries them all. Per source:

| `type` | `url` | `book` + `page` | `author` |
|---|---|---|---|
| `"web"` | required | null | optional |
| `"book"` | null | required | required |
| `"notes"` | null | null | optional |
| `"original"` | null | null | null |

When importing a recipe whose dish already exists, **add the new source to the existing recipe's `sources[]`** rather than creating a duplicate file.

### `restrictions`

These are **recipe metadata flags** — they record what the recipe contains so households can filter against their own constraints. They are not universal rules.

- `garlic: true` → recipe contains garlic. If the current household has a garlic constraint (check `Preferences.md`), exclude this recipe. When writing a new recipe for a garlic-restricted household, substitute shallot and set `garlic: false`.
- `lamb: true` → recipe contains lamb or goat. Filter out for households with a lamb aversion.
- `nuts: true` → recipe contains nuts; **`lunchboxSafe` must be `false`**.

All four fields (`garlic`, `lamb`, `nuts`, `lunchboxSafe`) must be set explicitly on every recipe.

### `nutrition`

All values are **per serving** (i.e. for `serves: 4`, this is 1/4 of the total recipe). Compute from USDA FoodData Central. All fields nullable if unknown.

### `ingredients`

- `qty` is a number (never a string like `"2-3"`). Use `null` for "to taste".
- `unit` examples: `g`, `ml`, `tbsp`, `tsp`, `piece`, `bunch`, `clove`. Use `null` for unitless counts.
- `note` is markdown. Use for prep state ("pressed 30 min"), optional flags, or substitutions.

### `method`

- `label` groups steps by phase (e.g. "Marinade", "Grill", "Finish"). Use `null` for ungrouped.
- `text` is markdown. Bold key actions, use backticks for temperatures.
- `durationMin` is the time for that step (or the waiting time if passive). Use `null` if instantaneous.

### `rating`

- `score`: 1–5 integer or `null` (unrated).
- `score: 0` means **never cook again** — exclude from all future plans.

### `usage`

Updated by the skill each time the recipe is cooked. Never set manually.

### `createdBy`

Always set `"createdBy": { "kind": "ai" }` on every recipe file the skill writes.
Recipes added via the web app carry `{ "kind": "user", "userId": "..." }` instead — never overwrite that field when editing an existing recipe.
