# Drinks Schema

Source of truth: `meal-plan-web/types/drink.ts`. The Drinks system is **separate** from food recipes — its own files, slugs, and fields (ml measures, glass, steep time).

All drinks data lives in three single files under `<data_root>/drinks/`:

| File | Shape | Contents |
|---|---|---|
| `bases.json` | `DrinkBase[]` | Made-ahead components — oleo saccharum, cold infusions, syrups. First-class & reusable. |
| `drinks.json` | `Drink[]` | Assembled, served drinks that reference bases + bottles. |
| `pantry.json` | `{ bottles[], botanicals[], specialty[] }` | Reference tables. |

Each base/drink carries its own `slug` (lowercase, hyphenated, from the name — e.g. "Ghia Ginger Buck" → `ghia-ginger-buck`).

## DrinkComponent (an ingredient line)

```json
{ "name": "Oleo saccharum", "qty": 20, "unit": "ml", "note": null, "baseSlug": "citrus-oleo-saccharum" }
```

- `qty` is a number or `null` (garnish / to taste). `unit`: `ml`, `g`, `piece`, `pods`, `dash`, `pinch`, … or `null`.
- **`baseSlug`** — set when the line *is* one of the bases in `bases.json` (e.g. oleo saccharum, a cold infusion). This links the drink to the base and powers the "used in N drinks" backlink. Match by name; if the referenced base doesn't exist yet, create it too (see intake).

## DrinkBase

```json
{
  "slug": "ginger-cold-infusion",
  "name": "Ginger Cold Infusion",
  "kind": "infusion",            // "oleo" | "infusion" | "syrup" | "other"
  "yield": "500 ml",
  "timeLabel": "Steep 6–8h",
  "ingredients": [ DrinkComponent, … ],
  "method": [ "markdown step", … ],
  "notes":  [ "markdown note", … ]
}
```

## Drink

```json
{
  "slug": "ghia-ginger-buck",
  "name": "Ghia Ginger Buck",
  "alcoholic": false,            // false = mocktail (NA) · true = cocktail
  "glass": "tall over ice",
  "timeMin": 5,
  "keeper": true,                // optional — a tried-and-true favourite (★)
  "bottles": ["Ghia"],           // bottle names used, for filtering
  "ingredients": [ DrinkComponent, … ],
  "method": [ "markdown step", … ],
  "notes":  [ "markdown note", … ]
}
```

Both **cocktails** (`alcoholic: true`) and **mocktails** (`alcoholic: false`) live in `drinks.json` together; the Drinks page filters between them. Bases/infusions are NA components regardless.

`method` and `notes` are arrays of markdown strings (bold timings, etc.). Keep ingredient names clean (no decorators).

## Pantry

```json
{
  "bottles":    [ { "name": "...", "profile": "...", "useAs": "..." } ],
  "botanicals": [ { "name": "...", "profile": "...", "technique": "..." } ],
  "specialty":  [ { "name": "...", "profile": "...", "use": "..." } ]
}
```
