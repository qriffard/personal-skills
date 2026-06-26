# Designing for mixed expert + executive audiences

A reference loaded on demand. Use when the user has named the audience as mixed, when the artifact will be both presented and circulated, or when one audience layer's needs seem to conflict with another.

## The tension

- **Executives** want one takeaway in ≤5 seconds. They will skim the title, glance at the hero, and decide whether to read further. They distrust complexity that doesn't pay off.
- **Experts** want to verify. They want distributions, sample sizes, sources, uncertainty, methodology. They distrust simplicity that hides the assumptions.

Designing for one breaks the other — *unless* you layer the artifact.

## The layered artifact

A single chart or dashboard can serve both if it is built in three concentric layers:

```
[ TITLE ]      ← Action title states the finding.            (executive layer)
[ HERO  ]      ← One chart with one accent. 5-second read.   (executive layer)
[ BODY  ]      ← Small multiples / distributions / detail.   (expert layer)
[ FOOTER]      ← Source, date, sample size, denominator,
                 methodology note, uncertainty disclosure.   (expert layer)
```

The executive reads top-to-bottom and stops as soon as they have what they need. The expert reads top-to-bottom too, but doesn't stop. Both find what they want without separate versions.

Critically: **the executive layer must be readable in isolation** (e.g., when pasted into Slack with no caption). The title + the highlighted mark together must convey the finding even with no other context.

## Concrete techniques

### Title and subtitle as a two-layer pair

- **Title** — the finding, in plain language, as a complete sentence.
  *"Customer churn has risen 3.2 pts since the price change in March"*
- **Subtitle** — the methodological qualifier the expert needs.
  *"Monthly cohort churn, defined as cancellations within 30 days of billing; 95% CI shown"*

The executive reads the title and decides whether to read more. The expert reads the subtitle and knows what they're looking at.

### Pair rate with count

Executives feel counts ("74 million people"). Experts trust rates ("1.2 per 1,000 adults"). Showing both, in adjacent text, lets each find what they trust:

> *Customer churn rose to **1.2%** of monthly active users in Q2, representing **840 accounts** lost.*

In a chart, you can render the rate as the bar and the count as a label at the end of the bar. Both visible at a glance, neither competes.

### Annotate the takeaway, but also annotate the assumption

Two annotations per chart, not one:

1. **The finding annotation** — directly on the data point that matters. *"Q2 inflection — first decline since 2019"*
2. **The assumption annotation** — in the corner or footer. *"Excludes 312 accounts flagged for fraud; methodology in §3 of report"*

Executives read the first, experts read both. Don't merge them into one — they answer different questions.

### Use the action title for what is known; use the chart for the uncertainty

Common mistake: hedge the title because the data is noisy. Don't.

- **Title:** State the finding plainly. *"Conversion rate is flat year-over-year"*
- **Chart:** Show the uncertainty band so the expert sees the noise. *"95% CI ±0.8 pts"*

These are two independent channels of communication. The title is the *what* (your assessment). The chart is the *how confident* (the data's signal-to-noise).

### Strip secondary detail from the hero — push it to the body

If the dashboard has a single hero chart and supporting panels:

- **Hero:** the chart that answers the Big Idea. One series highlighted, others gray. No legend. Title is the takeaway. Generally 1.5–2× the size of the supporting panels.
- **Supporting panels:** small multiples that decompose the hero (by region, segment, cohort). Same scales. Same color logic. They exist to answer "where is the effect coming from?"
- **Footer / appendix:** distribution plots, tables, source citations, methodology notes.

The executive reads the hero and stops. The expert continues into the supporting panels and footer. Same artifact.

### Color logic that satisfies both

- **Grey** = the rest. Most of the artifact.
- **One accent color** = the thing the title points at. Used identically across every panel (e.g., "our company" stays the same blue in every chart).
- **A second muted accent** allowed when an explicit comparison is being made (e.g., "us vs. competitor"; "before vs. after"). Never more than two.

Categorical palettes (>2 colors) are an expert-layer tool — confine them to the supporting panels where they label series in small multiples, not the hero.

### Sample size, always shown — but unobtrusively

Experts will ask "what's n?" Show it. But don't put it in the title.

- Inline as a subtitle annotation: *"n=4,217 monthly cohorts"*
- Or in the footer: *"Source: Internal billing system, May 2026. n=4,217."*

A chart of percentages with no n is a chart the expert will not trust. A chart of percentages with n in the title is a chart the executive's eye trips on.

### Show uncertainty in a form executives can read

Confidence intervals are expert-native. For executive readability:

- **Bands**, not vertical error bars — bands are easier to gestalt-read.
- **Faded color**, not crosshatch — chartjunk-free.
- **One band per series**, not nested 50/80/95% bands except in forecasting reports.
- A single line in the subtitle telling the executive what to do with the band: *"shaded region is the 95% confidence interval"*

### Reverse the storyboard

After building, do the **horizontal logic test** Knaflic prescribes:

- Read **only the chart titles** (and slide titles in a deck) top to bottom.
- Together they should narrate the story.
- If they read as a list of labels ("Q2 revenue", "Q2 churn", "Q2 NPS"), you have descriptive titles instead of action titles. Rewrite.

The horizontal-logic test is the single most reliable check that an executive will get the story without reading any of the charts.

## When the audiences truly diverge

Sometimes you can't serve both with one artifact. Signs:

- The executive needs a one-page summary; the expert needs 30 pages of detail.
- The executive will see this in a 60-second meeting; the expert will study it for an hour.
- Politically sensitive context — the expert needs to see disagreements; the executive does not.

In those cases, ship two artifacts that reference each other:

- **The executive brief** — single page, hero chart, action title, three bullets. Footer cites the technical appendix.
- **The technical appendix** — full small multiples, distributions, robustness checks, methodology, raw data link.

Both are needed; neither replaces the other. The brief is not "dumbed down" — it is *focused*. The appendix is not "the real version" — it is *the audit trail*.

## Things to refuse for this audience

- A 12-panel dashboard with no hero. *"What am I supposed to look at?"*
- An action title that hedges. *"Spending may possibly be slightly above budget pending further analysis."* This is title-as-CYA. Either you know or you don't; if you know, state it; if you don't, show the data and ask the question.
- A chart with three accent colors because brand guidelines required them. Brand colors used badly cost more credibility than they buy.
- A chart with no source. For executive audiences this is a trust killer the moment one number is questioned.
- "Drill-down" interactivity as a substitute for a clear hero. Executives don't drill. They scan.

## Quotable principles for this audience

- Tufte: *"Why not assume that if you understand it, most other readers will, too?"* — applies to the expert layer.
- Knaflic: *"Identify the single most important thing you want your audience to know and design around it."* — applies to the executive layer.
- Andrews: *"Information has not done its job until it impacts the story running in a person's mind."* — applies to both: the story must land.
- Cairo: *"Charts alone rarely prove anything; they enable conversations."* — invitation to layer the artifact so both audiences can pick up the conversation where they need to.
