# Chart selection — decision rules

A reference loaded on demand. Use this when the user has not specified a chart type, when they have specified one and it seems wrong for the data, or when they ask which chart to use.

## Step 1 — Form follows function

Before picking a chart type, name the **question** the chart answers. Examples:

- "How does X compare across Y?" → comparison
- "How is X distributed?" → distribution
- "How does X change over time?" → trend
- "How are X and Y related?" → relationship
- "What share does each part of X represent?" → composition
- "Where is X concentrated?" → geographic
- "What is the value of X?" → single number

The question dictates the form. Picking the chart before naming the question is the most common amateur mistake.

## Step 2 — Quick lookup

| Question | Default form | Alternative |
|---|---|---|
| Single value / 1–2 numbers | **Big text** with a caption | Headline + small change indicator |
| ≤20 numbers, mixed | **Formatted table** | Heatmap if there's a magnitude pattern |
| Comparison across ≤12 categories | **Horizontal bar**, sorted by value | Lollipop if many bars are similar lengths |
| Comparison across >12 categories | **Sorted dot plot** (Cleveland) | Faceted small bars |
| Two timepoints, many categories | **Slopegraph** | Side-by-side bars (worse for many categories) |
| Continuous over time, 1–5 series | **Line chart** | Area chart for cumulative; ribbon for ±range |
| Continuous over time, >5 series | **Small multiples** (one per series, shared axes) | Highlight chart (one bold, rest gray) |
| Two continuous variables, ≤500 points | **Scatter** + rug + trendline if useful | Bubble if a third variable matters |
| Two continuous variables, >2000 points | **Hexbin / density / 2D histogram** | Datashader for very large N |
| Distribution, one variable | **Histogram** or **dot strip** | Box plot for groups, violin for shape |
| Distribution comparison across groups | **Faceted histograms** or **dot strip** | Box / violin; ridgeline for many groups |
| Part-to-whole, ≤4 parts | **Stacked horizontal bar** | Treemap only for hierarchical parts |
| Part-to-whole, >4 parts | **Sorted horizontal bar of shares** | Never pie |
| Geographic by region | **Choropleth of rates** (never raw counts) | Cartogram weighted by population |
| Geographic point events | **Symbol map** (size = magnitude) | Hex / kernel density for many points |
| Flows / transitions | **Sankey** (limit ≤6 nodes per side) | Chord; alluvial for categorical flows |
| Network of entities | **Node-link** with sensible layout | Adjacency matrix for dense graphs |
| Multivariate (≥4 variables) | **Small multiples** or **parallel coordinates** | Scatterplot matrix for ≤6 variables |
| Hierarchy / proportion + nesting | **Treemap** | Sunburst if depth matters; icicle for code/file trees |
| Sequence / process | **Step chart** or **timeline** | Gantt for tasks; bump chart for ranks |

## Step 3 — Test the choice

After picking a form, run these tests:

- **Encoding fidelity.** Does the visual property scale with the data? (length for bars, position for points.)
- **Decoding test.** Can a reader recover the magnitude with an acceptable error? If the answer is no for the precision the decision requires, climb the perceptual hierarchy (replace area with length, or color with position).
- **Comparison directness.** Are the things to compare adjacent? (Side-by-side bars beat scattered bars; small multiples with shared axes beat overlapping lines for >5 series.)
- **The "compared to what?" check.** Is the baseline visible? Add a reference line if not.

## Step 4 — When two forms are both plausible

Use this tiebreaker order, derived from the four authors:

1. **More precise encoding wins** (position > length > area > color).
2. **Fewer cognitive jumps wins.** Direct labels > legend lookups > footnote lookups.
3. **More familiar form wins** for executive audiences. A novel chart spends trust the data may not earn back.
4. **Higher data density wins** for expert audiences, as long as readability holds.
5. **The form that lets you show uncertainty wins.** Bands beat naked lines.

## Common cases worked out

### "I have 4 KPIs to show on a slide."
Don't draw four sparklines on a 2×2 grid. Use big numbers with a small change indicator (`+3.2%` in green if up matters, red if down matters), each with a tiny inline sparkline showing the trend. Aligned in one row. Anything more is filler.

### "Revenue across 8 product lines for last quarter."
Horizontal bar chart, sorted descending by revenue, zero baseline, no gridlines, labels at the end of each bar. Title: the actual finding ("Two products contributed 60% of Q4 revenue"). Not a pie. Not a treemap unless there's nesting.

### "Engagement metric over 24 months."
Line chart. Whether or not the y-axis includes zero depends on whether the *change* matters (don't include zero) or the *absolute level* matters (include zero or a natural baseline). Annotate any inflection points. Source + sample size in footer.

### "Geographic distribution of customers."
Almost never raw counts on a choropleth — they'll mirror population. Show customers per 1,000 residents, or per capita revenue. If you must show count, use proportional symbols at city/region centroids, not a filled map.

### "A regression result with confidence intervals."
A coefficient plot (forest plot): one point per coefficient, horizontal error bars for CI, ordered by magnitude or by alphabetical name. Zero reference line. Never a table for >5 coefficients.

### "Distribution of latency."
Never a single mean. At minimum p50/p95/p99 as a small text table, plus a density or CDF plot. For comparison across services, faceted CDFs with shared x-axis (log) and a vertical reference at the SLO.

### "Quarterly progress toward a target."
Line chart with the target as a horizontal reference line, current value labeled, color the line gray and the most recent point in the accent color, title states whether you are on track.

## Things to refuse

- **Pie / donut for any precise comparison.** Replace with sorted horizontal bar.
- **3D for 2D data.** Never. Drop the dimension.
- **Dual y-axes.** Replace with indexed series (=100 at t₀) on a single axis, or two stacked panels sharing the x-axis.
- **Rainbow color scales for ordered data.** Use viridis, plasma, or a single-hue saturation ramp.
- **A bar chart whose y-axis doesn't include zero.** It misencodes length.
- **A choropleth of raw counts.** Always normalize.
- **A bubble chart where bubble *diameter* is proportional to the value.** Always area-proportional.
- **More than ~5 overlapping lines.** Switch to small multiples or highlight one line and gray the rest.
