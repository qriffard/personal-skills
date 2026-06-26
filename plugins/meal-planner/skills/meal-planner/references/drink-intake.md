# Mode F — Drink Intake

Captures a drink (cocktail or mocktail), base, or infusion into the Drinks system (`<data_root>/drinks/`).

## Trigger phrasings

- "save this drink / cocktail / mocktail / spritz"
- "add a base/infusion" / "save this oleo / cold infusion / syrup"
- a pasted drink recipe, a URL, or a photo of one
- "I made a new Ghia spritz — save it"

**Disambiguate from Mode B (food recipe):** if the item is a beverage — a drink, cocktail, spritz, infusion, oleo, syrup, shrub — it's Mode F. Food → Mode B.

## 1. Base or Drink?

| It's a… | When | File |
|---|---|---|
| **Base** | made ahead, has a yield + steep/rest time, used *inside* drinks (oleo, cold infusion, syrup) | `drinks/bases.json` |
| **Drink** | an assembled, served glass with a build + garnish, references bases/bottles | `drinks/drinks.json` |

If unsure, ask once.

## 2. Parse into the schema

Follow `references/drink_conventions.md`. Compute:

- **`slug`** — lowercase, hyphenated, from the name. Unique within its file.
- **`ingredients`** — one `DrinkComponent` per line. Parse `qty` (number) + `unit` (`ml`, `g`, `piece`, `pods`, `dash`, `pinch`). Garnishes → `qty: null`, `note: "to garnish"`.
- **Base linking (drinks):** for each ingredient that is itself a base, set `baseSlug` to that base's slug. Match the name against `drinks/bases.json`. **If the referenced base doesn't exist yet, offer to create it too** (a drink that calls for "elderflower cold infusion" needs that base to exist for the link to work).
- **`method` / `notes`** — arrays of markdown strings; bold key timings.
- **Drink extras:** `alcoholic` (`true` = cocktail, `false` = mocktail — infer from ingredients, e.g. real spirits → cocktail; ask if unclear), `glass`, `timeMin`, `bottles[]` (bottle names used), `keeper: true` if the user calls it a favourite/keeper.
- **Base extras:** `kind` (`oleo`/`infusion`/`syrup`/`other`), `yield`, `timeLabel` (e.g. "Steep 4–8h").

## 3. Write the file

Append the new object to the right array (`bases.json` or `drinks.json`). Keep the file valid JSON, 2-space indent.

If new bottles or botanicals are mentioned that aren't in `pantry.json`, offer to add them to the pantry tables.

## 4. Git sync

```bash
cd ~/claude-code/meal-plan-web && git add data/drinks/ && git commit -m "Add drink: <slug>" && git push
```

Vercel redeploys (~30 s). The drink appears at `/drinks/<slug>`; a base shows its "used in N drinks" backlinks automatically.

## 5. Confirm

Reply: `Saved: <Name> — <N> ingredients.` For a base, mention which existing drinks reference it (if any).
