# Mode B — Recipe Intake

Triggered when the user provides a recipe in any format (URL, pasted text, photo, PDF).

## 1. Detect the format

| Input | Detection | Tool |
|---|---|---|
| URL alone | message is `https?://...` or contains a single URL | `WebFetch` |
| Pasted text | multi-line text with section headers like "Ingredients" / "Method" | parse as-is |
| Photo | image attachment (jpg/png/heic) | vision (built-in image reading) |
| PDF | `.pdf` attachment | `Read` tool with `pages:` |

## 2. Extract the recipe

### URL
Use `WebFetch` and extract: title, ingredients (with quantities and units), method steps, servings, total time, source name and author. Ignore ads, comments, and intro stories.

### Pasted text / Photo / PDF
Parse directly. Look for title, ingredients, method.

## 2a. Splitting composed meals

When the source describes a **composed meal** (a restaurant plate, a video recipe that combines protein + grain + sauce), split it into **separate recipe files** — one per reusable component:

- A plate of chicken + rice pilaf + tzatziki → three files: `chicken-...`, `rice-...`, `tzatziki` (with `role: "condiment"`)
- A taco plate with salsa and guacamole → at least three files
- Only keep everything in one file when the components are genuinely inseparable (e.g. a slow-cooked stew where everything cooks together)

Assign the correct `role` to each component (`main`, `base`, `side`, `sauce`, `condiment`, `dip`, etc.) so they compose correctly on meal cards.

## 3. Compute all fields

**Slug** — lowercase ASCII, hyphenated, 3-6 words. Pattern: `<protein>-<key-veg>-<grain>` or `<technique>-<protein>-<flavor>`. The slug becomes the filename — do not store it inside the JSON.

**`role`** (optional) — the recipe's role on a plate, drives its label in a composed meal: `main` · `side` · `salad` · `base` · `sauce` · `dressing` · `condiment` · `dip` · `bread` · `drink`. Set it for anything that's naturally a component (a tzatziki = `condiment`, a vinaigrette = `dressing`, a rice pilaf = `base`). Standalone mains can omit it (meal cards fall back to positional Main/Side).

**`classification`**
- `proteinType`: `"meat"` | `"fish"` | `"plant-based"`
- `seasons`: array — match ingredients to season(s); use current season from `Schedule.md` as default
- `cuisine`: array — e.g. `["mediterranean"]`, `["japanese"]`
- `technique`: array — e.g. `["grill"]`, `["one-pan"]`, `["batch-cook"]`
- `dietary`: array — e.g. `["dairy-free"]`, `["gluten-free"]`

**`sources`** — an **array** of source objects (a recipe can have several). Each:
- `type`: `"web"` | `"book"` | `"notes"` | `"original"`
- `author`, `url` (web), `book` + `page` (book) — null where N/A.
- **Always capture the page `url` for web imports.**
- **Consolidate, don't duplicate:** if a recipe for the same dish already exists, add the new source to that recipe's `sources[]` rather than creating a second file.

**`restrictions`** — scan ingredients carefully:
- `garlic`: scan for `garlic`, `garlic powder`, `ail`. If found: **do not save**. Tell the user and offer to adapt (substitute shallot). Only save with `garlic: false`.
- `lamb`: scan for `lamb`, `mutton`, `agneau`. If found: **do not save**.
- `nuts`: scan for `almond`, `cashew`, `walnut`, `pecan`, `pistachio`, `hazelnut`, `pine nut`, `peanut`. If found: `nuts: true`, `lunchboxSafe: false`.
- `lunchboxSafe`: `true` unless `nuts: true` or other choking/allergen risk for kids.

**`nutrition`** — compute from USDA FoodData Central. Values are **per serving** (total ÷ `serves`):
```json
{ "kcal": N, "protein": N, "carbs": N, "fat": N, "fiber": N }
```

**`ingredients`** — structured array, NOT markdown:
```json
[
  {
    "label": null,
    "items": [
      { "name": "Firm tofu", "qty": 600, "unit": "g", "note": "pressed 30 min" },
      { "name": "Snap peas", "qty": 350, "unit": "g", "note": null }
    ]
  },
  {
    "label": "Dressing",
    "items": [
      { "name": "Lemon juice", "qty": 2, "unit": "tbsp", "note": null }
    ]
  }
]
```

Rules:
- `qty` is always a number. Never a string like `"2-3"`. Use `null` for "to taste".
- `unit` examples: `g`, `ml`, `tbsp`, `tsp`, `piece`, `bunch`. Use `null` for unitless counts.
- `note` is markdown — use for prep state, optional flags, substitutions.
- **No ★ or other decorators in ingredient `name` fields.** The ★ seasonal marker belongs in plan `context[]` only — it breaks grocery list aggregation if embedded in names.

**Vegetable portioning minimums:**
- Raw leafy greens: ≥ 120 g per adult per serving.
- Cooked / roasted vegetables: ≥ 200 g per adult per serving.
- Scale up if the source falls below these, then recompute nutrition.

**`method`** — structured array, NOT markdown:
```json
[
  {
    "label": null,
    "steps": [
      { "text": "Press tofu under a heavy pan for **30 min**.", "durationMin": 30 },
      { "text": "Heat oil over high heat. Fry tofu until golden on all sides.", "durationMin": 10 }
    ]
  },
  {
    "label": "Finish",
    "steps": [
      { "text": "Add snap peas, toss **2 min**. Off heat, add dressing and feta.", "durationMin": 2 }
    ]
  }
]
```

Rules:
- `text` is markdown — bold key actions, use backticks for temperatures (`55–57 °C`).
- `durationMin` is the active or passive time for the step. `null` if instantaneous.
- Group steps by phase (Prep, Marinate, Grill, Finish, etc.) using `label`. Use `null` for ungrouped.

**`versions`** — wrap `serves`, `activeTimeMin`, `totalTimeMin`, `nutrition`, `ingredients` and `method` inside a single default version when saving a new recipe:
```json
"versions": [ { "id": "regular", "label": "Regular", "default": true, "serves": N, "activeTimeMin": N, "totalTimeMin": N, "nutrition": {...}, "ingredients": [...], "method": [...] } ]
```
Add more versions (e.g. `high-protein`, `healthy`) only when the user asks. A non-default version is a **delta** — a `changes[]` list (`add`/`remove`/`substitute` by ingredient name) + its own `nutrition` + optional `methodNotes[]`. Don't repeat the full ingredient/method list. See `recipe_conventions.md` → Versions.

**`rating`** — always initialize as:
```json
{ "score": null, "notes": "", "date": null }
```

**`usage`** — always initialize as:
```json
{ "timesCooked": 0, "lastCooked": null }
```

**`createdBy`** — always set to:
```json
{ "kind": "ai" }
```
This marks the recipe as generated by Commis. Never omit it. If you are editing an existing recipe that already has `createdBy`, preserve the existing value.

## 4. Write the file

Write to `<data_root>/recipes/<slug>.json` using the full schema from `references/recipe_conventions.md`.

Update `<data_root>/recipes/index.json` — append the entry **without** `ingredients` and `method`, but **with** `slug` added.

## 5. Git sync

```bash
cd ~/claude-code/meal-plan-web && git add data/recipes/ && git commit -m "Add recipe: <slug>" && git push
```

## 6. Confirm

Reply: `Saved: <slug> — <kcal> kcal · <protein>g protein per serving.`

If rejected for hard-constraint violations (garlic / lamb), tell the user clearly and offer to save a modified version.
