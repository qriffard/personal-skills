# Mode C — Rate a Recipe

Triggered when the user gives feedback on a cooked recipe.

## Trigger phrasings

- "the dal was a 4/5"
- "[recipe] was great"
- "never make that again"
- "we loved [recipe]"
- "[recipe] needs more salt next time"

## Rating scale

| Score | Meaning | Effect on future plans |
|---|---|---|
| 0 | Never make again | Excluded from all future plans |
| 1-2 | Disliked | Strongly deprioritized |
| 3 | Neutral / fine | Used normally |
| 4-5 | Loved | Prioritized; rotate in more often |
| null | Unrated | Used normally |

Map free-form feedback:
- "great" / "loved it" / "amazing" → 5
- "good" / "really nice" → 4
- "fine" / "ok" → 3
- "didn't love it" / "meh" → 2
- "didn't like it" → 1
- "never again" → 0

## Process

1. **Match the recipe.** Find `<data_root>/recipes/<slug>.json` by title fuzzy-match against `<data_root>/recipes/index.json`. If multiple matches, ask which.

`rating` and `usage` are **recipe-level** (top-level fields, shared across all versions) — rate the recipe regardless of which version was cooked.

2. **Update the recipe JSON:**

```json
"rating": {
  "score": 4,
  "notes": "user's exact comment if specific, else empty string",
  "date": "YYYY-MM-DD"
},
"usage": {
  "timesCooked": "<previous + 1 if just cooked>",
  "lastCooked": "YYYY-MM-DD if just cooked"
}
```

3. **Update `<data_root>/recipes/index.json`** — same fields on the matching entry.

4. **Git sync:**
```bash
cd ~/claude-code/meal-plan-web && git add data/recipes/ && git commit -m "Rate <slug>: <N>/5" && git push
```

5. **Confirm:** `Got it — <Title> rated <N>/5.`
   If 0: `I'll exclude it from future plans.`
   If 5 with notes: `Adding to the rotation — note saved: "<notes>".`
