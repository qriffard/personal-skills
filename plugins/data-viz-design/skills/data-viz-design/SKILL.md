---
name: data-viz-design
description: Produce publication-grade plots and dashboards for mixed expert / executive audiences. Use this skill whenever the user asks to create, design, redraw, declutter, or critique a chart, plot, figure, dashboard, infographic, or data visualization — even when the user does not name a specific chart type. Also use when the user is choosing between chart types, picking a color palette, designing a slide for stakeholders, building a Streamlit / Dash / Plotly app, or asking how to present data to executives. Distilled from Tufte's *Visual Display of Quantitative Information*, Knaflic's *Storytelling with Data*, Cairo's *How Charts Lie*, and Andrews's *Info We Trust*.
---

# Designing Data Visualizations for Mixed Expert + Executive Audiences

## What this skill is for

A working method, plus an enforced set of principles, for producing charts and dashboards that hold up under both **executive skim** ("what's the takeaway in 5 seconds?") and **expert inspection** ("show me the distribution, the source, the uncertainty"). Generated for any plotting stack (matplotlib, seaborn, plotly, altair, Streamlit, Dash) but library-agnostic where it matters.

The skill enforces a workflow. It is not a passive style guide.

## The workflow — six stages

Walk through these in order. Skipping the early stages is the single biggest cause of bad data viz.

### 1. Context (before you open a plotting tool)

Answer four questions in writing — even one sentence each is enough. Refuse to render anything until they are answered.

1. **Who is the single primary audience?** "Stakeholders" is not an answer. Name one decision-maker or the smallest archetype: *"the VP of Ops, who needs to choose whether to hire 2 FTEs."*
2. **What must they decide or do?** A chart with no decision is a data dump. If there is no action, state that explicitly ("informational, no decision expected").
3. **What is the Big Idea?** One complete sentence, in plain language, that (a) states your point of view, (b) conveys what's at stake, (c) is something you would say out loud. Example: *"The pilot improved students' science perceptions — please approve continuation."*
4. **Compared to what?** Every quantitative claim needs a baseline (prior period, peer group, target, control). If you cannot name one, the chart cannot tell a story.

If the user did not supply this context, **ask before drawing**. Skip the asking only when the user has explicitly said "just draw it" or when the context is unambiguous from the data itself.

### 2. Choose the visual form

Pick the **simplest** form that supports the decision. Use the decision rules in `references/chart-selection.md`. The 80% cheatsheet:

| If the data is… | Default form |
|---|---|
| 1–2 numbers, no comparison | Big text / callout, not a chart |
| ≤ ~20 numbers, mixed types | Formatted table (Tufte: tables beat thin charts) |
| Categorical comparison (≤12 categories) | Horizontal bar, sorted by value, zero baseline |
| Continuous over time | Line chart (zero baseline optional) |
| Two timepoints, many categories | Slopegraph |
| Two continuous variables | Scatter with rug / marginal distributions |
| Many categories × many variables | Small multiples (Tufte's most-used pattern) |
| Part-to-whole, ≤4 parts | Stacked horizontal bar (NOT pie) |
| Geographic by region | Choropleth of **rates**, never raw counts; consider a cartogram |
| Distribution | Histogram, dot-strip, or box plot — show the spread |

**Never** generate: pie charts, donut charts, 3D anything, dual y-axes (except indexed series at base=100), rainbow palettes, area-as-1D-encoding, decorative "ducks." See `references/anti-patterns.md` for full list with reasoning.

### 3. Draft

Get a complete, ugly version on the page before polishing. The draft must include:

- The data, encoded correctly (length for bars, position for points/lines, area only for gist-not-precision)
- Real axis labels with units
- A working title (will be rewritten in stage 5)
- Source citation slot (even if empty)

Use the perceptual hierarchy when choosing encodings: **position > length > angle > area > color hue**. The lower in the hierarchy you go, the less precise the reader's decoding will be.

### 4. Declutter — apply the data-ink test

For every visual element on the page, ask: *if I erased this, would the reader lose information?* If no, erase it. Specifically:

- Remove chart borders.
- Remove gridlines, or make them thin pale gray. Dark grids are chartjunk.
- Remove tick marks at every integer; keep ~4–6 informative ticks per axis.
- Strip trailing zeros (`300.00` → `300`); abbreviate months.
- Trim axis spines to the data range (Tufte's *range-frame*) when it doesn't confuse the zero baseline of a bar chart.
- Remove the legend if you can label series directly on the chart (Gestalt: proximity).
- Use grayscale by default. Color is a spotlight, not wallpaper — spend it on the one thing the reader must see.

When in doubt, run the **"where are your eyes drawn?"** test. Close your eyes, glance at the chart, note where they land. If they land on a gridline or a logo before the data, the design has failed.

### 5. Focus attention + write the action title

This is what separates a chart from a slide that *moves a decision*.

- **Title is an action title, not a label.** *"Estimated 2026 spending is 8% above budget"* beats *"2026 Budget."* The title states the finding; the chart proves it.
- **Annotate on the chart.** Outliers, regime changes, events, the specific bar that matters — call them out in plain text next to the mark. Direct labels beat legends and footnotes.
- **One accent color, used consistently.** Grey the rest. A chart with three highlights has zero highlights.
- **Pre-attentive attributes** (color, size, position, enclosure) do the focusing — not arrows scattered everywhere.

For the executive layer of the audience, the title + the one highlighted mark must carry the message even if they read nothing else. For the expert layer, the full distribution / source / uncertainty must be reachable on the same artifact.

### 6. Verify before shipping

Run this checklist. Do not claim the chart is done until each item passes or has been explicitly accepted.

- [ ] **Big Idea test:** Cover the chart, recite the takeaway. Uncover. Does the chart prove it?
- [ ] **3-second test:** Glance away, glance back. The first thing you see should be the message.
- [ ] **Lie Factor:** `(visual effect size) / (data effect size)` between 0.95 and 1.05. (See `references/principles.md` for the exact formula and examples.)
- [ ] **Zero baseline** is present on every bar chart. Always.
- [ ] **No dual axes** unless explicitly indexed series on a single axis (e.g., =100 at t₀).
- [ ] **Uncertainty shown** if the data has any — error bars, CI bands, fan charts, or a footnote stating "point estimate."
- [ ] **Denominator visible** if showing rates, counts on maps, or percentages.
- [ ] **Source + date + sample type** cited in small grey type at the bottom.
- [ ] **Colorblind-safe.** Avoid red/green pairs. Test with a simulator or use a known-safe palette (blue/orange, viridis, ColorBrewer).
- [ ] **Reverse storyboard:** Read only the chart title (and slide titles if this is a deck). Do they tell the story by themselves?

## Library / output guidance

When the user specifies a stack, load the matching reference file:

- Static Python (matplotlib / seaborn) → `references/matplotlib.md`
- Interactive Python (plotly / altair / bokeh) → `references/plotly.md`
- Multi-panel apps (Streamlit / Dash) → `references/dashboards.md`

If unspecified, ask — or default to matplotlib for static, Plotly for interactive. Do not default to seaborn's `whitegrid` style; it violates the data-ink ratio by drawing a heavy grid.

## When the user asks you to critique an existing chart

Use the same checklist as stage 6, plus the failure taxonomy in `references/anti-patterns.md`. For each violation, name it, explain *why* it misleads (cite the underlying principle), and propose the smallest fix. Don't pile on — the goal is to ship a better chart, not win an argument.

## When the user asks for "a dashboard"

A dashboard is not a chart grid. It is a hierarchy. Apply Andrews's museum metaphor (see `references/dashboards.md`):

- **Lobby (top of page)** — the single hero chart or KPI strip that answers the primary question. Designed for a 5-second read.
- **Galleries (middle)** — 2–4 supporting charts that decompose the hero. Designed for a 30-second read.
- **Artifacts (bottom or expandable)** — tables, distributions, source data. Designed for the expert who wants to verify.

Decide the hero before any other chart. The hero answers the Big Idea. Everything else exists to support, qualify, or drill into it.

## Mixed expert + executive audiences

The hardest case, and the user's stated audience. The strategies:

- **Layer the artifact.** Title + hero conveys the takeaway for execs. Small multiples + uncertainty bands + source footer satisfy experts. Same page.
- **Don't dumb down the data; clarify its presentation.** Tufte: *"Why not assume that if you understand it, most other readers will, too?"*
- **Pair rate + count.** Executives feel counts ("74 million people"); analysts trust rates ("1%"). Show both when both matter.
- **Annotate the takeaway in words on the chart**, so the chart still works when it's pasted into Slack with no caption.

Full strategies in `references/audience-tailoring.md`.

## Reference files (load on demand)

- `references/principles.md` — Deep principles from each author, with formulas (Lie Factor), trust signals, Gestalt list, pre-attentive attributes.
- `references/chart-selection.md` — Detailed decision tree: which chart, when, with code-level guidance.
- `references/anti-patterns.md` — Every chart anti-pattern with the mechanism that makes it mislead, and the fix.
- `references/matplotlib.md` — Tufte-style matplotlib defaults, range-frames, small multiples, action titles.
- `references/plotly.md` — Plotly / altair patterns for interactive charts.
- `references/dashboards.md` — Streamlit / Dash composition: hero, galleries, artifacts.
- `references/audience-tailoring.md` — Strategies for mixed expert / executive audiences, including titles, annotations, layered detail.

## A note on style

Do not produce charts that *look* like default library output. Default `matplotlib` plots, default `plt.bar()` with a blue rectangle and a tick at every integer, are immediately readable as "thrown together." Care is a trust signal (Andrews). Spend a minute removing the chrome you don't need.

Also: do not produce charts that look *over-designed* — gradients, glow, animated transitions for static reports, illustrated icons in the legend. Decoration that doesn't carry data is a "duck" (Tufte). Beauty is welcome; ornamentation is not.

The right look is *spare, dense, and labeled*.
